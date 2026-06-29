from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .audit import AuditWriter
from .config import allow_dev_actor_header
from .config import audit_path
from .http_util import JsonBodyValidationError, correlation_id, json_response, problem_response, read_json
from .service import AccessControlService, ApiError
from .store import state_store_from_env
from .tokens import ServiceAuthenticator, TokenValidationError, service_authenticator_from_env


ACCOUNT_PATH = re.compile(r"^/iam/accounts/([^/]+)$")
PROFILE_PATH = re.compile(r"^/iam/accounts/([^/]+)/profile$")
LIFECYCLE_PATH = re.compile(r"^/iam/accounts/([^/]+)/(disable|restore|archive)$")
ASSIGNMENT_PATH = re.compile(r"^/iam/accounts/([^/]+)/service-roles/(.+)$")
ROLE_PATH = re.compile(r"^/iam/service-roles/(.+)$")
ROLE_LIFECYCLE_PATH = re.compile(r"^/iam/service-roles/(.+)/(disable|archive)$")
AUDIT_EVENT_PATH = re.compile(r"^/iam/audit/events/([^/]+)$")


class IamHandler(BaseHTTPRequestHandler):
    server_version = "IamControlPlane/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    @property
    def service(self) -> AccessControlService:
        return self.server.service  # type: ignore[attr-defined]

    @property
    def service_authenticator(self) -> ServiceAuthenticator:
        return self.server.service_authenticator  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def do_PATCH(self) -> None:
        self._handle("PATCH")

    def do_PUT(self) -> None:
        self._handle("PUT")

    def do_DELETE(self) -> None:
        self._handle("DELETE")

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        corr = correlation_id(self.headers.get("X-Correlation-Id"))
        try:
            result = self._dispatch(method, path, corr)
            status = result.pop("_status", 200) if isinstance(result, dict) else 200
            json_response(self, status, result, corr)
        except ApiError as exc:
            problem_response(self, exc.status, exc.code, exc.title, exc.detail, corr)
        except JsonBodyValidationError:
            problem_response(
                self,
                422,
                "validation_error",
                "Unprocessable Entity",
                "Request body must be a JSON object.",
                corr,
            )
        except json.JSONDecodeError:
            problem_response(self, 400, "invalid_json", "Invalid JSON", "Request body is not valid JSON.", corr)
        except Exception as exc:
            try:
                self.service.audit_indeterminate_request(method, path, corr, exc)
            except Exception:
                pass
            problem_response(
                self,
                503,
                "internal_error",
                "Service Unavailable",
                "The IAM Control Plane API could not safely handle the request.",
                corr,
            )

    def _dispatch(self, method: str, path: str, corr: str) -> dict[str, object]:
        if method == "GET" and path == "/healthz":
            return {"status": "ok"}
        if method == "GET" and path == "/iam/me":
            actor_id = self._require_actor_id(corr)
            return self.service.get_me(actor_id, corr)
        if method == "GET" and path == "/iam/me/services":
            actor_id = self._require_actor_id(corr)
            return {"services": self.service.get_effective_services(actor_id, corr)}
        if method == "GET" and path == "/iam/accounts":
            actor_id = self._require_actor_id(corr)
            return {"accounts": self.service.list_accounts(actor_id, corr)}
        if method == "POST" and path == "/iam/accounts":
            actor_id = self._require_actor_id(corr)
            return self.service.create_account(actor_id, read_json(self), corr)

        if match := ACCOUNT_PATH.match(path):
            if method == "GET":
                actor_id = self._require_actor_id(corr)
                return self.service.get_account(actor_id, match.group(1), corr)
        if match := PROFILE_PATH.match(path):
            if method == "PATCH":
                actor_id = self._require_actor_id(corr)
                return self.service.update_profile(actor_id, match.group(1), read_json(self), corr)
        if match := LIFECYCLE_PATH.match(path):
            if method == "POST":
                actor_id = self._require_actor_id(corr)
                return self.service.lifecycle(actor_id, match.group(1), match.group(2), corr)

        if method == "POST" and path == "/iam/onboarding/activate":
            return self.service.activate_onboarding_from_bearer(
                self.headers.get("Authorization", ""),
                read_json(self),
                corr,
            )

        if method == "GET" and path == "/iam/service-roles":
            actor_id = self._require_actor_id(corr)
            return {"serviceRoles": self.service.list_service_roles(actor_id, corr)}
        if method == "POST" and path == "/iam/service-roles":
            actor_id = self._require_actor_id(corr)
            return self.service.create_service_role(actor_id, read_json(self), corr)
        if match := ROLE_PATH.match(path):
            if method == "GET":
                actor_id = self._require_actor_id(corr)
                return self.service.get_service_role(actor_id, match.group(1), corr)
            if method == "PATCH":
                actor_id = self._require_actor_id(corr)
                return self.service.update_service_role(actor_id, match.group(1), read_json(self), corr)
        if match := ROLE_LIFECYCLE_PATH.match(path):
            if method == "POST":
                actor_id = self._require_actor_id(corr)
                return self.service.service_role_lifecycle(actor_id, match.group(1), match.group(2), corr)

        if match := ASSIGNMENT_PATH.match(path):
            if method == "PUT":
                actor_id = self._require_actor_id(corr)
                return self.service.assign_service_role(actor_id, match.group(1), match.group(2), corr)
            if method == "DELETE":
                actor_id = self._require_actor_id(corr)
                return self.service.remove_service_role(actor_id, match.group(1), match.group(2), corr)

        if method == "POST" and path == "/iam/authorization/check":
            self._require_service_authentication()
            return self.service.authorization_check(read_json(self), corr)

        if method == "GET" and path == "/iam/audit/events":
            actor_id = self._require_actor_id(corr)
            return {"events": self.service.read_audit_events(actor_id, corr)}
        if match := AUDIT_EVENT_PATH.match(path):
            if method == "GET":
                actor_id = self._require_actor_id(corr)
                return self.service.read_audit_event(actor_id, match.group(1), corr)

        raise ApiError(404, "not_found", "Not Found", "The requested endpoint does not exist.")

    def _require_actor_id(self, corr: str) -> str:
        if allow_dev_actor_header():
            actor_id = self.headers.get("X-Actor-Account-Id")
            if actor_id:
                return actor_id
        return self.service.resolve_actor_id_from_bearer(self.headers.get("Authorization", ""), corr)

    def _require_service_authentication(self) -> None:
        try:
            self.service_authenticator.require_authorized(self.headers.get("Authorization", ""))
        except TokenValidationError as exc:
            raise ApiError(exc.status, exc.code, exc.title, exc.detail) from exc


class IamServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        service: AccessControlService,
        service_authenticator: ServiceAuthenticator,
    ) -> None:
        super().__init__(server_address, IamHandler)
        self.service = service
        self.service_authenticator = service_authenticator


def main() -> None:
    service = AccessControlService(state_store_from_env(), AuditWriter(audit_path()))
    host = os.environ.get("IAM_HOST", "127.0.0.1")
    port = int(os.environ.get("IAM_PORT", "8000"))
    IamServer((host, port), service, service_authenticator_from_env()).serve_forever()


if __name__ == "__main__":
    main()
