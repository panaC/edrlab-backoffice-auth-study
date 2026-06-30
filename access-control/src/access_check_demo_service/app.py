from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from access_control.config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID
from access_control.http_util import correlation_id, json_response
from access_control.technical_logging import elapsed_ms, technical_log
from access_control.tokens import ServiceTokenProvider, TokenValidationError, service_token_provider_from_env


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "AccessCheckDemo/0.1"

    def log_message(self, format: str, *args: object) -> None:
        # Use structured technical_log events instead of BaseHTTPRequestHandler text access logs.
        return

    @property
    def service_token_provider(self) -> ServiceTokenProvider:
        provider = getattr(self.server, "service_token_provider", None)
        if provider is None:
            provider = service_token_provider_from_env()
            self.server.service_token_provider = provider  # type: ignore[attr-defined]
        return provider

    def do_GET(self) -> None:
        started = time.perf_counter()
        parsed = urlparse(self.path)
        path = parsed.path
        corr = correlation_id(self.headers.get("X-Correlation-Id"))
        status = 500
        response_delivered = False
        try:
            status, body = self._handle_access_check(path, corr)
            response_delivered = self._json_response(status, body, corr)
        finally:
            technical_log(
                "http_request_completed",
                component="access-check-demo-service",
                correlationId=corr,
                method="GET",
                path=path,
                status=status,
                elapsedMs=elapsed_ms(started, time.perf_counter()),
                responseDelivered=response_delivered,
            )

    def _handle_access_check(self, path: str, corr: str) -> tuple[int, dict[str, object]]:
        if path == "/healthz":
            return 200, {"status": "ok"}
        if path not in {"/", "/access-check-demo"}:
            return 404, {"result": "KO", "authorized": False}

        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return 401, {"result": "KO", "authorized": False}

        subject_token = authorization.removeprefix("Bearer ").strip()
        try:
            decision = self._call_iam_api(subject_token, corr)
        except (TimeoutError, TokenValidationError):
            return 503, {"result": "KO", "authorized": False}

        if decision.get("decision") == "allow":
            return 200, {"result": "OK", "authorized": True}
        if decision.get("decision") == "authentication_failed":
            return 401, {"result": "KO", "authorized": False}
        if decision.get("decision") == "deny":
            return 403, {"result": "KO", "authorized": False}
        return 503, {"result": "KO", "authorized": False}

    def _json_response(self, status: int, body: dict[str, object], corr: str) -> bool:
        try:
            json_response(self, status, body, corr)
            return True
        except (BrokenPipeError, ConnectionResetError):
            technical_log(
                "client_disconnected_before_response",
                component="access-check-demo-service",
                correlationId=corr,
                method="GET",
                path=urlparse(self.path).path,
                intendedStatus=status,
            )
            return False

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
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                    self._log_iam_call(corr, attempt + 1, response.status, body.get("decision"), started)
                    return body
            except urllib.error.HTTPError as exc:
                error_code = self._iam_error_code(exc)
                decision = "deny"
                if exc.code == 401 and error_code != "invalid_service_token":
                    decision = "authentication_failed"
                    self._log_iam_call(corr, attempt + 1, exc.code, decision, started, error_code)
                    return {"decision": decision}
                if exc.code in {401, 503}:
                    decision = "indeterminate"
                self._log_iam_call(corr, attempt + 1, exc.code, decision, started, error_code)
                return {"decision": decision}
            except (urllib.error.URLError, TimeoutError) as exc:
                self._log_iam_call(corr, attempt + 1, None, "unavailable", started, errorType=type(exc).__name__)
                if attempt >= attempts - 1:
                    raise TimeoutError("IAM API unavailable")
                time.sleep(random.uniform(0.025, 0.1))
        raise TimeoutError("IAM API unavailable")

    def _log_iam_call(
        self,
        corr: str,
        attempt: int,
        status: int | None,
        decision: object,
        started: float,
        error_code: str | None = None,
        *,
        errorType: str | None = None,
    ) -> None:
        technical_log(
            "iam_authorization_check_call_completed",
            component="access-check-demo-service",
            correlationId=corr,
            dependency="iam-api",
            attempt=attempt,
            status=status,
            decision=decision if isinstance(decision, str) else None,
            errorCode=error_code,
            errorType=errorType,
            elapsedMs=elapsed_ms(started, time.perf_counter()),
        )

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
