from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from edrlab_access_control.audit import AuditWriter
from edrlab_access_control.config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID
from edrlab_access_control.demo_service import DemoHandler
from edrlab_access_control.iam_api import IamServer
from edrlab_access_control.service import AccessControlService, ApiError
from edrlab_access_control.store import FileStateStore
from edrlab_access_control.tokens import (
    OidcIntrospectionSubjectTokenValidator,
    OidcServiceTokenAuthenticator,
    SharedSecretServiceAuthenticator,
    SubjectEvidence,
    SubjectTokenValidator,
    TokenValidationError,
)


class StaticSubjectTokenValidator(SubjectTokenValidator):
    def __init__(self, evidence_by_token: dict[str, SubjectEvidence]) -> None:
        self.evidence_by_token = evidence_by_token

    def validate(self, token: str) -> SubjectEvidence:
        evidence = self.evidence_by_token.get(token)
        if evidence is None:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is invalid.")
        return evidence


class MvpSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.state_path = root / "state.json"
        self.audit_path = root / "audit.jsonl"
        self.subject_tokens: dict[str, SubjectEvidence] = {
            "dev-sub:member-sub": SubjectEvidence(subject="member-sub"),
            "dev-sub:missing-subject": SubjectEvidence(subject="missing-subject"),
        }
        self.service = AccessControlService(
            FileStateStore(self.state_path),
            AuditWriter(self.audit_path),
            StaticSubjectTokenValidator(self.subject_tokens),
        )
        self.bootstrap = self.service.bootstrap_first_super_admin(
            email="super-admin@example.test",
            name="Initial Super Admin",
            organization="EDRLab",
            subject="super-sub",
        )
        self.super_admin_id = self.bootstrap["accountId"]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bootstrap_is_idempotent_and_audited(self) -> None:
        second = self.service.bootstrap_first_super_admin(
            email="ignored@example.test",
            name="Ignored",
            organization="Ignored",
            subject="ignored-sub",
        )
        self.assertEqual(second["status"], "no_change")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        super_admins = [
            account
            for account in state["accounts"].values()
            if account["accountType"] == "super-admin"
        ]
        self.assertEqual(len(super_admins), 1)
        self.assertTrue(any("bootstrap.super_admin" in line for line in self._audit_lines()))

    def test_admin_cannot_create_admin_or_super_admin(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "admin@example.test",
                "organization": "EDRLab",
                "name": "Admin",
                "accountType": "admin",
            },
            "corr-admin",
        )
        self._add_subject_token("admin-token", "admin-sub", "admin@example.test", acr="edrlab-privileged")
        self.service.activate_onboarding_from_bearer(
            "Bearer admin-token",
            {},
            "corr-admin-activate",
        )
        with self.assertRaises(ApiError) as admin_attempt:
            self.service.create_account(
                admin["accountId"],
                {
                    "email": "other-admin@example.test",
                    "organization": "EDRLab",
                    "name": "Other Admin",
                    "accountType": "admin",
                },
                "corr-admin-deny",
            )
        self.assertEqual(admin_attempt.exception.status, 403)

        with self.assertRaises(ApiError) as super_admin_attempt:
            self.service.create_account(
                self.super_admin_id,
                {
                    "email": "new-super@example.test",
                    "organization": "EDRLab",
                    "name": "New Super",
                    "accountType": "super-admin",
                },
                "corr-super-deny",
            )
        self.assertEqual(super_admin_attempt.exception.status, 422)

    def test_privileged_onboarding_requires_privileged_acr(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "priv-admin@example.test",
                "organization": "EDRLab",
                "name": "Priv Admin",
                "accountType": "admin",
            },
            "corr-create-priv-admin",
        )
        with self.assertRaises(ApiError) as missing_acr:
            self._add_subject_token("priv-admin-normal-token", "priv-admin-sub", "priv-admin@example.test", acr="edrlab-normal")
            self.service.activate_onboarding_from_bearer(
                "Bearer priv-admin-normal-token",
                {},
                "corr-deny-priv-admin",
            )
        self.assertEqual(missing_acr.exception.status, 403)
        self._add_subject_token("priv-admin-token", "priv-admin-sub", "priv-admin@example.test", acr="edrlab-privileged")
        activated = self.service.activate_onboarding_from_bearer(
            "Bearer priv-admin-token",
            {},
            "corr-allow-priv-admin",
        )
        self.assertEqual(activated["accountId"], admin["accountId"])
        self.assertEqual(activated["lifecycle"], "active")

    def test_member_access_stops_after_role_removal_and_disablement(self) -> None:
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "member@example.test",
                "organization": "EDRLab",
                "name": "Member",
                "accountType": "member",
            },
            "corr-create-member",
        )
        self.service.assign_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-assign-role",
        )
        self._add_subject_token("member-token", "member-sub", "member@example.test")
        self.service.activate_onboarding_from_bearer(
            "Bearer member-token",
            {},
            "corr-activate-member",
        )
        allow = self.service.authorization_check(
            {
                "subjectToken": "dev-sub:member-sub",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-allow",
        )
        self.assertEqual(allow["decision"], "allow")

        self.service.remove_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-remove-role",
        )
        deny_after_remove = self.service.authorization_check(
            {
                "subjectToken": "dev-sub:member-sub",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-deny-after-remove",
        )
        self.assertEqual(deny_after_remove["decision"], "deny")

        self.service.assign_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-reassign-role",
        )
        self.service.lifecycle(self.super_admin_id, member["accountId"], "disable", "corr-disable")
        deny_after_disable = self.service.authorization_check(
            {
                "subjectToken": "dev-sub:member-sub",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-deny-after-disable",
        )
        self.assertEqual(deny_after_disable["decision"], "deny")

    def test_admin_gets_effective_service_access_without_assignment(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "services-admin@example.test",
                "organization": "EDRLab",
                "name": "Services Admin",
                "accountType": "admin",
            },
            "corr-create-services-admin",
        )
        self._add_subject_token("services-admin-token", "services-admin-sub", "services-admin@example.test", acr="edrlab-privileged")
        self.service.activate_onboarding_from_bearer(
            "Bearer services-admin-token",
            {},
            "corr-activate-services-admin",
        )
        services = self.service.get_effective_services(admin["accountId"], "corr-services")
        self.assertEqual(services, [{"serviceId": DEFAULT_SERVICE_ID, "roleId": DEFAULT_SERVICE_ROLE_ID}])

    def test_audit_lines_are_single_json_objects_without_subject_tokens(self) -> None:
        self.service.authorization_check(
            {
                "subjectToken": "dev-sub:missing-subject",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-deny-missing-subject",
        )
        lines = self._audit_lines()
        self.assertGreater(len(lines), 0)
        for line in lines:
            parsed = json.loads(line)
            self.assertIsInstance(parsed, dict)
            self.assertNotIn("dev-sub:missing-subject", line)
            self.assertNotIn("subjectToken", line)

    def _audit_lines(self) -> list[str]:
        return [
            line.strip()
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _add_subject_token(
        self,
        token: str,
        subject: str,
        email: str,
        *,
        email_verified: bool = True,
        acr: str | None = None,
    ) -> None:
        self.subject_tokens[token] = SubjectEvidence(
            subject=subject,
            email=email,
            email_verified=email_verified,
            acr=acr,
        )


class StubIamHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else ""
        self.server.requests.append(  # type: ignore[attr-defined]
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "body": body,
            }
        )
        payload = json.dumps(self.server.body).encode("utf-8")  # type: ignore[attr-defined]
        self.send_response(self.server.status)  # type: ignore[attr-defined]
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class StubIntrospectionHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        form = urllib.parse.parse_qs(raw_body)
        token = form.get("token", [""])[0]
        self.server.requests.append(  # type: ignore[attr-defined]
            {
                "authorization": self.headers.get("Authorization"),
                "token": token,
            }
        )
        body = self.server.responses.get(token, {"active": False})  # type: ignore[attr-defined]
        payload = json.dumps(body).encode("utf-8")
        self.send_response(self.server.status)  # type: ignore[attr-defined]
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class IamHttpAuthenticationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.old_dev_header = os.environ.get("IAM_ALLOW_DEV_ACTOR_HEADER")
        os.environ.pop("IAM_ALLOW_DEV_ACTOR_HEADER", None)
        self.subject_tokens: dict[str, SubjectEvidence] = {
            "dev-sub:member-sub": SubjectEvidence(
                subject="member-sub",
                email="member@example.test",
                email_verified=True,
            ),
            "dev-sub:super-sub": SubjectEvidence(subject="super-sub"),
        }
        self.service = AccessControlService(
            FileStateStore(root / "state.json"),
            AuditWriter(root / "audit.jsonl"),
            StaticSubjectTokenValidator(self.subject_tokens),
        )
        bootstrap = self.service.bootstrap_first_super_admin(
            email="super-admin@example.test",
            name="Initial Super Admin",
            organization="EDRLab",
            subject="super-sub",
        )
        self.super_admin_id = bootstrap["accountId"]
        self.member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "member@example.test",
                "organization": "EDRLab",
                "name": "Member",
                "accountType": "member",
            },
            "corr-create-member",
        )
        self.service.activate_onboarding_from_bearer(
            "Bearer dev-sub:member-sub",
            {},
            "corr-activate-member",
        )
        self.server = IamServer(
            ("127.0.0.1", 0),
            self.service,
            SharedSecretServiceAuthenticator("service-token"),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.old_dev_header is None:
            os.environ.pop("IAM_ALLOW_DEV_ACTOR_HEADER", None)
        else:
            os.environ["IAM_ALLOW_DEV_ACTOR_HEADER"] = self.old_dev_header
        self.tmp.cleanup()

    def test_admin_header_without_bearer_is_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request(
                "GET",
                "/iam/accounts",
                headers={"X-Actor-Account-Id": self.super_admin_id},
            )
        self.assertEqual(raised.exception.code, 401)

    def test_member_bearer_cannot_impersonate_super_admin_with_header(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request(
                "POST",
                "/iam/accounts",
                headers={
                    "Authorization": "Bearer dev-sub:member-sub",
                    "X-Actor-Account-Id": self.super_admin_id,
                },
                body={
                    "email": "new-member@example.test",
                    "organization": "EDRLab",
                    "name": "New Member",
                    "accountType": "member",
                },
            )
        self.assertEqual(raised.exception.code, 403)

    def test_super_admin_bearer_can_use_admin_endpoint(self) -> None:
        status, body = self._json_request(
            "POST",
            "/iam/accounts",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "email": "new-member@example.test",
                "organization": "EDRLab",
                "name": "New Member",
                "accountType": "member",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["accountType"], "member")

    def test_onboarding_requires_bearer(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request("POST", "/iam/onboarding/activate", body={})
        self.assertEqual(raised.exception.code, 401)

    def test_onboarding_rejects_client_supplied_identity_claims(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request(
                "POST",
                "/iam/onboarding/activate",
                headers={"Authorization": "Bearer dev-sub:member-sub"},
                body={
                    "subject": "forged-sub",
                    "email": "forged@example.test",
                    "emailVerified": True,
                    "acr": "edrlab-privileged",
                },
            )
        self.assertEqual(raised.exception.code, 422)

    def test_onboarding_activates_from_bearer_evidence(self) -> None:
        self.service.create_account(
            self.super_admin_id,
            {
                "email": "new-member@example.test",
                "organization": "EDRLab",
                "name": "New Member",
                "accountType": "member",
            },
            "corr-create-new-member",
        )
        self.subject_tokens["new-member-token"] = SubjectEvidence(
            subject="new-member-sub",
            email="new-member@example.test",
            email_verified=True,
        )

        status, body = self._json_request(
            "POST",
            "/iam/onboarding/activate",
            headers={"Authorization": "Bearer new-member-token"},
            body={},
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["lifecycle"], "active")
        self.assertTrue(body["hasLinkedSubject"])

    def _json_request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: dict[str, object] | None = None,
    ) -> tuple[int, dict[str, object]]:
        request_headers = dict(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=request_headers,
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload


class OidcTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servers: list[ThreadingHTTPServer] = []
        self.issuer = "http://issuer.example.test/realms/mvp"
        self.audience = DEFAULT_SERVICE_ID

    def tearDown(self) -> None:
        for server in self.servers:
            server.shutdown()
            server.server_close()

    def test_oidc_subject_token_requires_issuer_audience_expiry_and_subject(self) -> None:
        _, url = self._serve_introspection(
            {
                "valid-token": self._active_response(sub="kc-sub"),
                "wrong-issuer": self._active_response(sub="kc-sub", iss="http://wrong.example.test/realms/mvp"),
                "wrong-audience": self._active_response(sub="kc-sub", aud="other-service"),
                "expired": self._active_response(sub="kc-sub", exp=int(time.time()) - 1),
                "inactive": {"active": False},
            }
        )
        validator = self._validator(url)

        self.assertEqual(validator.validate("valid-token").subject, "kc-sub")
        for token in ("wrong-issuer", "wrong-audience", "expired", "inactive"):
            with self.subTest(token=token):
                with self.assertRaises(TokenValidationError) as raised:
                    validator.validate(token)
                self.assertEqual(raised.exception.status, 401)

    def test_raw_oidc_claims_do_not_grant_local_service_access(self) -> None:
        _, url = self._serve_introspection(
            {
                "misleading-token": {
                    **self._active_response(sub="member-sub"),
                    "email": "member@example.test",
                    "email_verified": True,
                    "edrlab_account_type": "super-admin",
                    "realm_access": {"roles": [DEFAULT_SERVICE_ROLE_ID]},
                }
            }
        )
        service = self._service_with_validator(url)
        member = service.create_account(
            service.bootstrap_first_super_admin(
                email="super-admin@example.test",
                name="Initial Super Admin",
                organization="EDRLab",
                subject="super-sub",
            )["accountId"],
            {
                "email": "member@example.test",
                "organization": "EDRLab",
                "name": "Member",
                "accountType": "member",
            },
            "corr-create-member",
        )
        service.activate_onboarding_from_bearer(
            "Bearer misleading-token",
            {},
            "corr-activate-member",
        )

        decision = service.authorization_check(
            {
                "subjectToken": "misleading-token",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-claim-deny",
        )

        self.assertEqual(member["accountType"], "member")
        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["reason"], "not_authorized")

    def test_oidc_service_token_requires_expected_client(self) -> None:
        _, url = self._serve_introspection(
            {
                "service-token": self._active_response(sub="service-account", client_id=DEFAULT_SERVICE_ID),
                "wrong-client": self._active_response(sub="service-account", client_id="other-client"),
            }
        )
        authenticator = OidcServiceTokenAuthenticator(
            f"{url}/introspect",
            DEFAULT_SERVICE_ID,
            "secret",
            DEFAULT_SERVICE_ID,
            self.issuer,
            1,
        )

        authenticator.require_authorized("Bearer service-token")
        with self.assertRaises(TokenValidationError) as raised:
            authenticator.require_authorized("Bearer wrong-client")
        self.assertEqual(raised.exception.status, 401)

    def _service_with_validator(self, url: str) -> AccessControlService:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        return AccessControlService(
            FileStateStore(root / "state.json"),
            AuditWriter(root / "audit.jsonl"),
            self._validator(url),
        )

    def _validator(self, url: str) -> OidcIntrospectionSubjectTokenValidator:
        return OidcIntrospectionSubjectTokenValidator(
            f"{url}/introspect",
            "client-id",
            "client-secret",
            self.issuer,
            self.audience,
            1,
        )

    def _active_response(
        self,
        *,
        sub: str,
        iss: str | None = None,
        aud: str | list[str] | None = None,
        exp: int | None = None,
        client_id: str = "edrlab-backoffice",
    ) -> dict[str, object]:
        return {
            "active": True,
            "iss": iss or self.issuer,
            "aud": aud or [self.audience],
            "exp": exp or int(time.time()) + 60,
            "sub": sub,
            "client_id": client_id,
        }

    def _serve_introspection(self, responses: dict[str, dict[str, object]]) -> tuple[ThreadingHTTPServer, str]:
        server = ThreadingHTTPServer(("127.0.0.1", 0), StubIntrospectionHandler)
        server.responses = responses  # type: ignore[attr-defined]
        server.status = 200  # type: ignore[attr-defined]
        server.requests = []  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append(server)
        return server, f"http://127.0.0.1:{server.server_port}"


class HttpContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servers: list[ThreadingHTTPServer] = []
        self.old_env = {
            "IAM_API_URL": os.environ.get("IAM_API_URL"),
            "IAM_SERVICE_TOKEN": os.environ.get("IAM_SERVICE_TOKEN"),
            "IAM_SERVICE_AUTH_MODE": os.environ.get("IAM_SERVICE_AUTH_MODE"),
            "IAM_SERVICE_TOKEN_URL": os.environ.get("IAM_SERVICE_TOKEN_URL"),
            "IAM_SERVICE_CLIENT_ID": os.environ.get("IAM_SERVICE_CLIENT_ID"),
            "IAM_SERVICE_CLIENT_SECRET": os.environ.get("IAM_SERVICE_CLIENT_SECRET"),
        }

    def tearDown(self) -> None:
        for server in self.servers:
            server.shutdown()
            server.server_close()
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_demo_maps_iam_authentication_failure_to_401_ko(self) -> None:
        iam_server, iam_url = self._serve(
            StubIamHandler,
            status=401,
            body={"code": "invalid_subject_token"},
        )
        os.environ["IAM_API_URL"] = f"{iam_url}/iam/authorization/check"
        os.environ["IAM_SERVICE_TOKEN"] = "test-service-token"
        _, demo_url = self._serve(DemoHandler)

        request = urllib.request.Request(
            f"{demo_url}/access-check-demo",
            headers={"Authorization": "Bearer invalid-token"},
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)

        response = raised.exception
        self.assertEqual(response.code, 401)
        self.assertEqual(json.loads(response.read().decode("utf-8")), {"authorized": False, "result": "KO"})
        self.assertEqual(iam_server.requests[0]["path"], "/iam/authorization/check")  # type: ignore[attr-defined]

    def test_demo_maps_service_authentication_failure_to_503_ko(self) -> None:
        _, iam_url = self._serve(
            StubIamHandler,
            status=401,
            body={"code": "invalid_service_token"},
        )
        os.environ["IAM_API_URL"] = f"{iam_url}/iam/authorization/check"
        os.environ["IAM_SERVICE_TOKEN"] = "wrong-service-token"
        _, demo_url = self._serve(DemoHandler)

        request = urllib.request.Request(
            f"{demo_url}/access-check-demo",
            headers={"Authorization": "Bearer dev-sub:any-subject"},
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)

        response = raised.exception
        self.assertEqual(response.code, 503)
        self.assertEqual(json.loads(response.read().decode("utf-8")), {"authorized": False, "result": "KO"})

    def test_demo_uses_oidc_client_credentials_for_service_authentication(self) -> None:
        iam_server, iam_url = self._serve(
            StubIamHandler,
            status=200,
            body={"decision": "allow"},
        )
        _, token_url = self._serve(
            StubIamHandler,
            status=200,
            body={"access_token": "service-access-token", "expires_in": 60},
        )
        os.environ["IAM_API_URL"] = f"{iam_url}/iam/authorization/check"
        os.environ["IAM_SERVICE_AUTH_MODE"] = "oidc"
        os.environ["IAM_SERVICE_TOKEN_URL"] = f"{token_url}/token"
        os.environ["IAM_SERVICE_CLIENT_ID"] = "access-check-demo-service"
        os.environ["IAM_SERVICE_CLIENT_SECRET"] = "demo-secret"
        _, demo_url = self._serve(DemoHandler)

        request = urllib.request.Request(
            f"{demo_url}/access-check-demo",
            headers={"Authorization": "Bearer dev-sub:any-subject"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertEqual(body, {"authorized": True, "result": "OK"})
        self.assertEqual(iam_server.requests[0]["authorization"], "Bearer service-access-token")  # type: ignore[attr-defined]

    def _serve(
        self,
        handler: type[BaseHTTPRequestHandler],
        **attributes: object,
    ) -> tuple[ThreadingHTTPServer, str]:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        for key, value in attributes.items():
            setattr(server, key, value)
        if not hasattr(server, "requests"):
            server.requests = []  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append(server)
        return server, f"http://127.0.0.1:{server.server_port}"


if __name__ == "__main__":
    unittest.main()
