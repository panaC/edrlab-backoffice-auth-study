from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID
from .http_util import correlation_id, json_response
from .tokens import ServiceTokenProvider, TokenValidationError, service_token_provider_from_env


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "AccessCheckDemo/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    @property
    def service_token_provider(self) -> ServiceTokenProvider:
        provider = getattr(self.server, "service_token_provider", None)
        if provider is None:
            provider = service_token_provider_from_env()
            self.server.service_token_provider = provider  # type: ignore[attr-defined]
        return provider

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        corr = correlation_id(self.headers.get("X-Correlation-Id"))
        if parsed.path == "/healthz":
            json_response(self, 200, {"status": "ok"}, corr)
            return
        if parsed.path not in {"/", "/access-check-demo"}:
            json_response(self, 404, {"result": "KO", "authorized": False}, corr)
            return

        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            json_response(self, 401, {"result": "KO", "authorized": False}, corr)
            return

        subject_token = authorization.removeprefix("Bearer ").strip()
        try:
            decision = self._call_iam_api(subject_token, corr)
        except (TimeoutError, TokenValidationError):
            json_response(self, 503, {"result": "KO", "authorized": False}, corr)
            return

        if decision.get("decision") == "allow":
            json_response(self, 200, {"result": "OK", "authorized": True}, corr)
            return
        if decision.get("decision") == "authentication_failed":
            json_response(self, 401, {"result": "KO", "authorized": False}, corr)
            return
        if decision.get("decision") == "deny":
            json_response(self, 403, {"result": "KO", "authorized": False}, corr)
            return
        json_response(self, 503, {"result": "KO", "authorized": False}, corr)

    def _call_iam_api(self, subject_token: str, corr: str) -> dict[str, object]:
        timeout_seconds = int(os.environ.get("IAM_CALL_TIMEOUT_MS", "500")) / 1000
        retry_count = int(os.environ.get("IAM_CALL_RETRY_COUNT", "1"))
        body = {
            "subjectToken": subject_token,
            "serviceId": DEFAULT_SERVICE_ID,
            "requiredRole": DEFAULT_SERVICE_ROLE_ID,
        }
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            os.environ.get("IAM_API_URL", "http://127.0.0.1:8000/iam/authorization/check"),
            data=data,
            method="POST",
            headers={
                "Authorization": self.service_token_provider.authorization_header(),
                "Content-Type": "application/json",
                "X-Correlation-Id": corr,
            },
        )

        attempts = retry_count + 1
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error_code = self._iam_error_code(exc)
                if exc.code == 401 and error_code != "invalid_service_token":
                    return {"decision": "authentication_failed"}
                if exc.code in {401, 503}:
                    return {"decision": "indeterminate"}
                return {"decision": "deny"}
            except (urllib.error.URLError, TimeoutError):
                if attempt >= attempts - 1:
                    raise TimeoutError("IAM API unavailable")
                time.sleep(random.uniform(0.025, 0.1))
        raise TimeoutError("IAM API unavailable")

    def _iam_error_code(self, exc: urllib.error.HTTPError) -> str | None:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if isinstance(body, dict) and isinstance(body.get("code"), str):
            return body["code"]
        return None


def main() -> None:
    host = os.environ.get("DEMO_HOST", "127.0.0.1")
    port = int(os.environ.get("DEMO_PORT", "8001"))
    ThreadingHTTPServer((host, port), DemoHandler).serve_forever()


if __name__ == "__main__":
    main()
