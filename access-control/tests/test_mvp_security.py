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

from access_check_demo_service.app import DemoHandler
from access_control.audit import AuditWriter
from access_control import keycloak_bootstrap
from access_control.config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID
from access_control.iam_api import IamServer
from access_control.keycloak_store import KeycloakStateStore
from access_control.service import AccessControlService, ApiError
from access_control.store import FileStateStore
from access_control.tokens import (
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


class FailingStateStore:
    def load(self) -> dict[str, object]:
        raise RuntimeError("Unexpected Keycloak users response")

    def transact(self, callback: object) -> object:
        raise RuntimeError("Unexpected Keycloak users response")


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
            organization="MVP Organization",
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
                "organization": "MVP Organization",
                "name": "Admin",
                "accountType": "admin",
            },
            "corr-admin",
        )
        self._add_subject_token("admin-token", "admin-sub", "admin@example.test", acr="iam-privileged")
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
                    "organization": "MVP Organization",
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
                    "organization": "MVP Organization",
                    "name": "New Super",
                    "accountType": "super-admin",
                },
                "corr-super-deny",
            )
        self.assertEqual(super_admin_attempt.exception.status, 422)

    def test_rejected_business_rule_mutations_are_audited(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "audited-admin@example.test",
                "organization": "MVP Organization",
                "name": "Audited Admin",
                "accountType": "admin",
            },
            "corr-create-audited-admin",
        )
        self._add_subject_token("audited-admin-token", "audited-admin-sub", "audited-admin@example.test", acr="iam-privileged")
        self.service.activate_onboarding_from_bearer(
            "Bearer audited-admin-token",
            {},
            "corr-activate-audited-admin",
        )
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "audited-member@example.test",
                "organization": "MVP Organization",
                "name": "Audited Member",
                "accountType": "member",
            },
            "corr-create-audited-member",
        )
        self._add_subject_token("audited-member-token", "audited-member-sub", "audited-member@example.test")
        self.service.activate_onboarding_from_bearer(
            "Bearer audited-member-token",
            {},
            "corr-activate-audited-member",
        )

        with self.assertRaises(ApiError):
            self.service.create_account(
                admin["accountId"],
                {
                    "email": "forbidden-admin@example.test",
                    "organization": "MVP Organization",
                    "name": "Forbidden Admin",
                    "accountType": "admin",
                },
                "corr-rejected-account-create",
            )
        with self.assertRaises(ApiError):
            self.service.lifecycle(
                self.super_admin_id,
                member["accountId"],
                "archive",
                "corr-rejected-lifecycle",
            )
        self.service.service_role_lifecycle(
            self.super_admin_id,
            DEFAULT_SERVICE_ROLE_ID,
            "disable",
            "corr-disable-default-role",
        )
        with self.assertRaises(ApiError):
            self.service.assign_service_role(
                self.super_admin_id,
                member["accountId"],
                DEFAULT_SERVICE_ROLE_ID,
                "corr-rejected-role-assignment",
            )

        self._assert_rejected_audit_event(
            "account.create",
            "unresolved",
            "corr-rejected-account-create",
            "forbidden",
        )
        self._assert_rejected_audit_event(
            "account.archive",
            member["accountId"],
            "corr-rejected-lifecycle",
            "invalid_transition",
        )
        self._assert_rejected_audit_event(
            "service_role.assign",
            member["accountId"],
            "corr-rejected-role-assignment",
            "role_not_active",
        )

    def test_privileged_onboarding_requires_privileged_acr(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "priv-admin@example.test",
                "organization": "MVP Organization",
                "name": "Priv Admin",
                "accountType": "admin",
            },
            "corr-create-priv-admin",
        )
        with self.assertRaises(ApiError) as missing_acr:
            self._add_subject_token("priv-admin-normal-token", "priv-admin-sub", "priv-admin@example.test", acr="iam-normal")
            self.service.activate_onboarding_from_bearer(
                "Bearer priv-admin-normal-token",
                {},
                "corr-deny-priv-admin",
            )
        self.assertEqual(missing_acr.exception.status, 403)
        self._add_subject_token("priv-admin-token", "priv-admin-sub", "priv-admin@example.test", acr="iam-privileged")
        activated = self.service.activate_onboarding_from_bearer(
            "Bearer priv-admin-token",
            {},
            "corr-allow-priv-admin",
        )
        self.assertEqual(activated["accountId"], admin["accountId"])
        self.assertEqual(activated["lifecycle"], "active")

    def test_repeat_onboarding_activation_is_idempotent_and_audited(self) -> None:
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "repeat-onboarding@example.test",
                "organization": "MVP Organization",
                "name": "Repeat Onboarding",
                "accountType": "member",
            },
            "corr-create-repeat-onboarding",
        )
        self._add_subject_token(
            "repeat-onboarding-token",
            "repeat-onboarding-sub",
            "repeat-onboarding@example.test",
        )

        first = self.service.activate_onboarding_from_bearer(
            "Bearer repeat-onboarding-token",
            {},
            "corr-first-repeat-onboarding",
        )
        second = self.service.activate_onboarding_from_bearer(
            "Bearer repeat-onboarding-token",
            {},
            "corr-second-repeat-onboarding",
        )

        self.assertEqual(first["accountId"], member["accountId"])
        self.assertEqual(first["lifecycle"], "active")
        self.assertTrue(first["hasLinkedSubject"])
        self.assertEqual(second["accountId"], member["accountId"])
        self.assertEqual(second["lifecycle"], "active")
        self.assertTrue(second["hasLinkedSubject"])
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        stored = state["accounts"][member["accountId"]]
        self.assertEqual(stored["lifecycle"], "active")
        self.assertEqual(stored["linkedSubject"], "repeat-onboarding-sub")

        self._assert_audit_event(
            "onboarding.activate",
            member["accountId"],
            "corr-first-repeat-onboarding",
            "changed",
            "safe_activation",
        )
        self._assert_audit_event(
            "onboarding.activate",
            member["accountId"],
            "corr-second-repeat-onboarding",
            "no_change",
            "already_active_same_subject",
        )

    def test_different_subject_onboarding_cannot_rebind_link_and_is_audited(self) -> None:
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "subject-rebind@example.test",
                "organization": "MVP Organization",
                "name": "Subject Rebind",
                "accountType": "member",
            },
            "corr-create-subject-rebind",
        )
        self._add_subject_token(
            "subject-rebind-first-token",
            "subject-rebind-first-sub",
            "subject-rebind@example.test",
        )
        self._add_subject_token(
            "subject-rebind-second-token",
            "subject-rebind-second-sub",
            "subject-rebind@example.test",
        )

        activated = self.service.activate_onboarding_from_bearer(
            "Bearer subject-rebind-first-token",
            {},
            "corr-first-subject-rebind",
        )
        with self.assertRaises(ApiError) as rejected:
            self.service.activate_onboarding_from_bearer(
                "Bearer subject-rebind-second-token",
                {},
                "corr-second-subject-rebind",
            )

        self.assertEqual(activated["accountId"], member["accountId"])
        self.assertEqual(rejected.exception.status, 409)
        self.assertEqual(rejected.exception.code, "unsafe_onboarding_match")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        stored = state["accounts"][member["accountId"]]
        self.assertEqual(stored["lifecycle"], "active")
        self.assertEqual(stored["linkedSubject"], "subject-rebind-first-sub")
        self._assert_audit_event(
            "onboarding.activate",
            member["accountId"],
            "corr-first-subject-rebind",
            "changed",
            "safe_activation",
        )
        self._assert_audit_event(
            "onboarding.activate",
            "unresolved",
            "corr-second-subject-rebind",
            "rejected",
            "unsafe_match_count",
        )
        for line in self._audit_lines():
            self.assertNotIn("subject-rebind-second-token", line)

    def test_onboarding_repeat_requires_account_to_still_be_active(self) -> None:
        for lifecycle_action, expected_lifecycle in (("disable", "disabled"), ("archive", "archived")):
            with self.subTest(expected_lifecycle=expected_lifecycle):
                member = self.service.create_account(
                    self.super_admin_id,
                    {
                        "email": f"{expected_lifecycle}-repeat@example.test",
                        "organization": "MVP Organization",
                        "name": f"{expected_lifecycle.title()} Repeat",
                        "accountType": "member",
                    },
                    f"corr-create-{expected_lifecycle}-repeat",
                )
                token = f"{expected_lifecycle}-repeat-token"
                subject = f"{expected_lifecycle}-repeat-sub"
                self._add_subject_token(token, subject, member["email"])
                self.service.activate_onboarding_from_bearer(
                    f"Bearer {token}",
                    {},
                    f"corr-activate-{expected_lifecycle}-repeat",
                )
                self.service.lifecycle(
                    self.super_admin_id,
                    member["accountId"],
                    "disable",
                    f"corr-disable-{expected_lifecycle}-repeat",
                )
                if lifecycle_action == "archive":
                    self.service.lifecycle(
                        self.super_admin_id,
                        member["accountId"],
                        "archive",
                        "corr-archive-repeat",
                    )

                with self.assertRaises(ApiError) as repeat:
                    self.service.activate_onboarding_from_bearer(
                        f"Bearer {token}",
                        {},
                        f"corr-repeat-{expected_lifecycle}",
                    )

                self.assertEqual(repeat.exception.status, 409)
                self.assertEqual(repeat.exception.code, "unsafe_onboarding_match")
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.assertEqual(state["accounts"][member["accountId"]]["lifecycle"], expected_lifecycle)

    def test_member_access_stops_after_role_removal_and_disablement(self) -> None:
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "member@example.test",
                "organization": "MVP Organization",
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

    def test_authorization_check_denies_unknown_service_or_role_ids(self) -> None:
        cases = (
            (
                "unknown-service",
                "unknown-service:consult",
                "corr-deny-unknown-service",
            ),
            (
                DEFAULT_SERVICE_ID,
                f"{DEFAULT_SERVICE_ID}:unknown-role",
                "corr-deny-unknown-role",
            ),
        )
        for service_id, required_role, correlation_id in cases:
            with self.subTest(service_id=service_id, required_role=required_role):
                decision = self.service.authorization_check(
                    {
                        "subjectToken": "dev-sub:member-sub",
                        "serviceId": service_id,
                        "requiredRole": required_role,
                    },
                    correlation_id,
                )

                self.assertEqual(decision["decision"], "deny")
                self.assertEqual(decision["reason"], "role_not_active")
                self._assert_audit_event(
                    "authorization.check.denied",
                    service_id,
                    correlation_id,
                    "rejected",
                    "role_not_active",
                )

    def test_authorization_check_denies_inactive_and_archived_accounts(self) -> None:
        for action, expected_lifecycle in (("disable", "disabled"), ("archive", "archived")):
            with self.subTest(expected_lifecycle=expected_lifecycle):
                member = self.service.create_account(
                    self.super_admin_id,
                    {
                        "email": f"{expected_lifecycle}-authz@example.test",
                        "organization": "MVP Organization",
                        "name": f"{expected_lifecycle.title()} Authz",
                        "accountType": "member",
                    },
                    f"corr-create-{expected_lifecycle}-authz",
                )
                self.service.assign_service_role(
                    self.super_admin_id,
                    member["accountId"],
                    DEFAULT_SERVICE_ROLE_ID,
                    f"corr-assign-{expected_lifecycle}-authz",
                )
                subject = f"{expected_lifecycle}-authz-sub"
                token = f"{expected_lifecycle}-authz-token"
                self._add_subject_token(token, subject, member["email"])
                self.service.activate_onboarding_from_bearer(
                    f"Bearer {token}",
                    {},
                    f"corr-activate-{expected_lifecycle}-authz",
                )
                self.service.lifecycle(
                    self.super_admin_id,
                    member["accountId"],
                    "disable",
                    f"corr-disable-{expected_lifecycle}-authz",
                )
                if action == "archive":
                    self.service.lifecycle(
                        self.super_admin_id,
                        member["accountId"],
                        "archive",
                        f"corr-archive-{expected_lifecycle}-authz",
                    )

                decision = self.service.authorization_check(
                    {
                        "subjectToken": token,
                        "serviceId": DEFAULT_SERVICE_ID,
                        "requiredRole": DEFAULT_SERVICE_ROLE_ID,
                    },
                    f"corr-deny-{expected_lifecycle}-authz",
                )

                self.assertEqual(decision["decision"], "deny")
                self.assertEqual(decision["reason"], "account_not_active")
                self._assert_audit_event(
                    "authorization.check.denied",
                    DEFAULT_SERVICE_ID,
                    f"corr-deny-{expected_lifecycle}-authz",
                    "rejected",
                    "account_not_active",
                )

    def test_authorization_check_denies_disabled_and_archived_service_roles(self) -> None:
        for action, expected_status in (("disable", "disabled"), ("archive", "archived")):
            with self.subTest(expected_status=expected_status):
                if action == "archive":
                    self.service.service_role_lifecycle(
                        self.super_admin_id,
                        DEFAULT_SERVICE_ROLE_ID,
                        "disable",
                        "corr-disable-role-before-archive",
                    )
                self.service.service_role_lifecycle(
                    self.super_admin_id,
                    DEFAULT_SERVICE_ROLE_ID,
                    action,
                    f"corr-{action}-role",
                )

                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                role = state["serviceRoles"][DEFAULT_SERVICE_ROLE_ID]
                self.assertEqual(role["status"], expected_status)
                decision = self.service.authorization_check(
                    {
                        "subjectToken": "dev-sub:member-sub",
                        "serviceId": DEFAULT_SERVICE_ID,
                        "requiredRole": DEFAULT_SERVICE_ROLE_ID,
                    },
                    f"corr-deny-{expected_status}-role",
                )

                self.assertEqual(decision["decision"], "deny")
                self.assertEqual(decision["reason"], "role_not_active")
                self._assert_audit_event(
                    "authorization.check.denied",
                    DEFAULT_SERVICE_ID,
                    f"corr-deny-{expected_status}-role",
                    "rejected",
                    "role_not_active",
                )

    def test_role_removal_allows_inactive_role_cleanup_and_idempotent_retry(self) -> None:
        member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "inactive-role-cleanup@example.test",
                "organization": "MVP Organization",
                "name": "Inactive Role Cleanup",
                "accountType": "member",
            },
            "corr-create-inactive-role-cleanup",
        )
        self.service.assign_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-assign-inactive-role-cleanup",
        )
        self.service.service_role_lifecycle(
            self.super_admin_id,
            DEFAULT_SERVICE_ROLE_ID,
            "disable",
            "corr-disable-inactive-role-cleanup",
        )

        removed = self.service.remove_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-remove-inactive-role-cleanup",
        )
        self.assertNotIn(DEFAULT_SERVICE_ROLE_ID, removed["serviceRoles"])

        retried = self.service.remove_service_role(
            self.super_admin_id,
            member["accountId"],
            DEFAULT_SERVICE_ROLE_ID,
            "corr-retry-inactive-role-cleanup",
        )
        self.assertNotIn(DEFAULT_SERVICE_ROLE_ID, retried["serviceRoles"])
        events = [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(
            any(
                event["operation"] == "service_role.remove"
                and event["targetId"] == member["accountId"]
                and event["outcome"] == "changed"
                and event["correlationId"] == "corr-remove-inactive-role-cleanup"
                for event in events
            )
        )
        self.assertTrue(
            any(
                event["operation"] == "service_role.remove"
                and event["targetId"] == member["accountId"]
                and event["outcome"] == "no_change"
                and event["correlationId"] == "corr-retry-inactive-role-cleanup"
                for event in events
            )
        )

    def test_admin_gets_effective_service_access_without_assignment(self) -> None:
        admin = self.service.create_account(
            self.super_admin_id,
            {
                "email": "services-admin@example.test",
                "organization": "MVP Organization",
                "name": "Services Admin",
                "accountType": "admin",
            },
            "corr-create-services-admin",
        )
        self._add_subject_token("services-admin-token", "services-admin-sub", "services-admin@example.test", acr="iam-privileged")
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

    def _audit_events(self) -> list[dict[str, object]]:
        return [json.loads(line) for line in self._audit_lines()]

    def _assert_audit_event(
        self,
        operation: str,
        target_id: str,
        correlation_id: str,
        outcome: str,
        reason_code: str,
    ) -> None:
        self.assertTrue(
            any(
                event.get("operation") == operation
                and event.get("targetId") == target_id
                and event.get("outcome") == outcome
                and event.get("correlationId") == correlation_id
                and event.get("reasonCode") == reason_code
                for event in self._audit_events()
            ),
            f"missing audit event for {operation} {correlation_id}",
        )

    def _assert_rejected_audit_event(
        self,
        operation: str,
        target_id: str,
        correlation_id: str,
        reason_code: str,
    ) -> None:
        self.assertTrue(
            any(
                event.get("operation") == operation
                and event.get("targetId") == target_id
                and event.get("outcome") == "rejected"
                and event.get("correlationId") == correlation_id
                and event.get("reasonCode") == reason_code
                for event in self._audit_events()
            ),
            f"missing rejected audit event for {operation} {correlation_id}",
        )

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
        self.audit_path = root / "audit.jsonl"
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
            AuditWriter(self.audit_path),
            StaticSubjectTokenValidator(self.subject_tokens),
        )
        bootstrap = self.service.bootstrap_first_super_admin(
            email="super-admin@example.test",
            name="Initial Super Admin",
            organization="MVP Organization",
            subject="super-sub",
        )
        self.super_admin_id = bootstrap["accountId"]
        self.member = self.service.create_account(
            self.super_admin_id,
            {
                "email": "member@example.test",
                "organization": "MVP Organization",
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
                    "organization": "MVP Organization",
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
                "organization": "MVP Organization",
                "name": "New Member",
                "accountType": "member",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["accountType"], "member")

    def test_super_admin_bearer_can_patch_service_role(self) -> None:
        status, body = self._json_request(
            "PATCH",
            f"/iam/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
            headers={
                "Authorization": "Bearer dev-sub:super-sub",
                "X-Correlation-Id": "corr-update-service-role",
            },
            body={"description": "Updated MVP access-check demo consultation role."},
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["roleId"], DEFAULT_SERVICE_ROLE_ID)
        self.assertEqual(body["serviceId"], DEFAULT_SERVICE_ID)
        self.assertEqual(body["description"], "Updated MVP access-check demo consultation role.")
        events = [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(
            any(
                event["operation"] == "service_role.update"
                and event["targetId"] == DEFAULT_SERVICE_ROLE_ID
                and event["correlationId"] == "corr-update-service-role"
                for event in events
            )
        )

    def test_admin_account_endpoints_reject_protected_body_fields(self) -> None:
        protected_account_fields: dict[str, object] = {
            "accountId": "acc_client_supplied",
            "hasLinkedSubject": True,
            "lifecycle": "active",
            "linkedSubject": "forged-sub",
            "schemaVersion": "iam-schema-v999",
            "serviceRoles": [DEFAULT_SERVICE_ROLE_ID],
        }
        initial_account_ids = set(self._state()["accounts"])

        for field, value in protected_account_fields.items():
            with self.subTest(endpoint="create", field=field):
                correlation_id = f"corr-protected-account-create-{field}"
                self._assert_problem(
                    "POST",
                    "/iam/accounts",
                    headers={
                        "Authorization": "Bearer dev-sub:super-sub",
                        "X-Correlation-Id": correlation_id,
                    },
                    body={
                        "email": f"protected-create-{field.lower()}@example.test",
                        "organization": "MVP Organization",
                        "name": "Protected Create",
                        "accountType": "member",
                        field: value,
                    },
                    status=422,
                    code="protected_field",
                )
                self.assertEqual(set(self._state()["accounts"]), initial_account_ids)
                self._assert_rejected_audit_event("account.create", "unresolved", correlation_id, "protected_field")

        before_member = dict(self._account_state(self.member["accountId"]))
        for field, value in {
            **protected_account_fields,
            "accountType": "super-admin",
        }.items():
            with self.subTest(endpoint="profile", field=field):
                correlation_id = f"corr-protected-profile-{field}"
                self._assert_problem(
                    "PATCH",
                    f"/iam/accounts/{self.member['accountId']}/profile",
                    headers={
                        "Authorization": "Bearer dev-sub:super-sub",
                        "X-Correlation-Id": correlation_id,
                    },
                    body={"name": "Ignored Protected Profile", field: value},
                    status=422,
                    code="protected_field",
                )
                self.assertEqual(self._account_state(self.member["accountId"]), before_member)
                self._assert_rejected_audit_event(
                    "account.profile.update",
                    self.member["accountId"],
                    correlation_id,
                    "protected_field",
                )

    def test_path_driven_account_mutations_do_not_trust_body_targets(self) -> None:
        other = self.service.create_account(
            self.super_admin_id,
            {
                "email": "other-target@example.test",
                "organization": "MVP Organization",
                "name": "Other Target",
                "accountType": "member",
            },
            "corr-create-other-target",
        )
        other_before = dict(self._account_state(other["accountId"]))

        status, disabled = self._json_request(
            "POST",
            f"/iam/accounts/{self.member['accountId']}/disable",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "accountId": other["accountId"],
                "accountType": "super-admin",
                "lifecycle": "archived",
                "linkedSubject": "forged-sub",
                "serviceRoles": [DEFAULT_SERVICE_ROLE_ID],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(disabled["accountId"], self.member["accountId"])
        self.assertEqual(disabled["lifecycle"], "disabled")
        self.assertEqual(self._account_state(other["accountId"]), other_before)
        target_state = self._account_state(self.member["accountId"])
        self.assertEqual(target_state["accountType"], "member")
        self.assertEqual(target_state["linkedSubject"], "member-sub")
        self.assertEqual(target_state["serviceRoles"], [])

        status, restored = self._json_request(
            "POST",
            f"/iam/accounts/{self.member['accountId']}/restore",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "accountId": other["accountId"],
                "accountType": "super-admin",
                "lifecycle": "archived",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(restored["accountId"], self.member["accountId"])
        self.assertEqual(restored["lifecycle"], "active")
        self.assertEqual(self._account_state(other["accountId"]), other_before)

        alternate_role_id = "access-check-demo:alternate"
        self.service.create_service_role(
            self.super_admin_id,
            {
                "roleId": alternate_role_id,
                "serviceId": DEFAULT_SERVICE_ID,
                "description": "Alternate test role.",
            },
            "corr-create-alternate-role",
        )

        status, assigned = self._json_request(
            "PUT",
            f"/iam/accounts/{self.member['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "accountId": other["accountId"],
                "roleId": alternate_role_id,
                "accountType": "super-admin",
                "serviceRoles": [alternate_role_id],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(assigned["accountId"], self.member["accountId"])
        self.assertEqual(assigned["serviceRoles"], [DEFAULT_SERVICE_ROLE_ID])
        self.assertEqual(self._account_state(other["accountId"]), other_before)

        status, removed = self._json_request(
            "DELETE",
            f"/iam/accounts/{self.member['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "accountId": other["accountId"],
                "roleId": alternate_role_id,
                "serviceRoles": [alternate_role_id],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(removed["accountId"], self.member["accountId"])
        self.assertEqual(removed["serviceRoles"], [])
        self.assertEqual(self._account_state(other["accountId"]), other_before)

        self._json_request(
            "POST",
            f"/iam/accounts/{self.member['accountId']}/disable",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={"accountId": other["accountId"], "lifecycle": "active"},
        )
        status, archived = self._json_request(
            "POST",
            f"/iam/accounts/{self.member['accountId']}/archive",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "accountId": other["accountId"],
                "accountType": "super-admin",
                "lifecycle": "active",
                "linkedSubject": "forged-sub",
                "serviceRoles": [alternate_role_id],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(archived["accountId"], self.member["accountId"])
        self.assertEqual(archived["lifecycle"], "archived")
        self.assertEqual(self._account_state(other["accountId"]), other_before)
        archived_state = self._account_state(self.member["accountId"])
        self.assertEqual(archived_state["accountType"], "member")
        self.assertEqual(archived_state["linkedSubject"], "member-sub")
        self.assertEqual(archived_state["serviceRoles"], [])

    def test_service_role_endpoints_reject_protected_body_fields(self) -> None:
        for field, value in {"schemaVersion": "iam-schema-v999", "status": "archived"}.items():
            with self.subTest(endpoint="create", field=field):
                role_id = f"access-check-demo:protected-{field.lower()}"
                correlation_id = f"corr-protected-service-role-create-{field}"
                self._assert_problem(
                    "POST",
                    "/iam/service-roles",
                    headers={
                        "Authorization": "Bearer dev-sub:super-sub",
                        "X-Correlation-Id": correlation_id,
                    },
                    body={
                        "roleId": role_id,
                        "serviceId": DEFAULT_SERVICE_ID,
                        "description": "Protected create attempt.",
                        field: value,
                    },
                    status=422,
                    code="protected_field",
                )
                self.assertNotIn(role_id, self._state()["serviceRoles"])
                self._assert_rejected_audit_event(
                    "service_role.create",
                    role_id,
                    correlation_id,
                    "protected_field",
                )

        before_role = dict(self._service_role_state(DEFAULT_SERVICE_ROLE_ID))
        protected_update_fields: dict[str, object] = {
            "roleId": "access-check-demo:changed",
            "schemaVersion": "iam-schema-v999",
            "serviceId": "changed-service",
            "status": "archived",
        }
        for field, value in protected_update_fields.items():
            with self.subTest(endpoint="update", field=field):
                correlation_id = f"corr-protected-service-role-update-{field}"
                self._assert_problem(
                    "PATCH",
                    f"/iam/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
                    headers={
                        "Authorization": "Bearer dev-sub:super-sub",
                        "X-Correlation-Id": correlation_id,
                    },
                    body={"description": "Ignored protected service role update.", field: value},
                    status=422,
                    code="protected_field",
                )
                self.assertEqual(self._service_role_state(DEFAULT_SERVICE_ROLE_ID), before_role)
                self._assert_rejected_audit_event(
                    "service_role.update",
                    DEFAULT_SERVICE_ROLE_ID,
                    correlation_id,
                    "protected_field",
                )

    def test_path_driven_service_role_lifecycle_does_not_trust_body_state(self) -> None:
        before_role = dict(self._service_role_state(DEFAULT_SERVICE_ROLE_ID))

        status, disabled = self._json_request(
            "POST",
            f"/iam/service-roles/{DEFAULT_SERVICE_ROLE_ID}/disable",
            headers={"Authorization": "Bearer dev-sub:super-sub"},
            body={
                "roleId": "access-check-demo:changed",
                "schemaVersion": "iam-schema-v999",
                "serviceId": "changed-service",
                "status": "archived",
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(disabled["roleId"], DEFAULT_SERVICE_ROLE_ID)
        self.assertEqual(disabled["serviceId"], before_role["serviceId"])
        self.assertEqual(disabled["schemaVersion"], before_role["schemaVersion"])
        self.assertEqual(disabled["status"], "disabled")

    def test_member_bearer_can_use_self_endpoints(self) -> None:
        status, body = self._json_request(
            "GET",
            "/iam/me",
            headers={"Authorization": "Bearer dev-sub:member-sub"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["accountId"], self.member["accountId"])

        status, body = self._json_request(
            "GET",
            "/iam/me/services",
            headers={"Authorization": "Bearer dev-sub:member-sub"},
        )
        self.assertEqual(status, 200)
        self.assertIn("services", body)

    def test_member_bearer_cannot_use_account_management_endpoints_on_self(self) -> None:
        cases: list[tuple[str, str, dict[str, object] | None]] = [
            ("GET", "/iam/accounts", None),
            ("GET", f"/iam/accounts/{self.member['accountId']}", None),
            ("PATCH", f"/iam/accounts/{self.member['accountId']}/profile", {"name": "Changed"}),
            ("POST", f"/iam/accounts/{self.member['accountId']}/disable", None),
            ("POST", f"/iam/accounts/{self.member['accountId']}/restore", None),
            ("POST", f"/iam/accounts/{self.member['accountId']}/archive", None),
        ]
        for method, path, body in cases:
            with self.subTest(method=method, path=path):
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    self._json_request(
                        method,
                        path,
                        headers={"Authorization": "Bearer dev-sub:member-sub"},
                        body=body,
                    )
                self.assertEqual(raised.exception.code, 403)

        _, profile = self._json_request(
            "GET",
            "/iam/me",
            headers={"Authorization": "Bearer dev-sub:member-sub"},
        )
        self.assertEqual(profile["name"], "Member")

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
                    "acr": "iam-privileged",
                },
            )
        self.assertEqual(raised.exception.code, 422)

    def test_non_object_json_body_returns_validation_error(self) -> None:
        cases: list[tuple[str, str, dict[str, str], object]] = [
            (
                "POST",
                "/iam/accounts",
                {"Authorization": "Bearer dev-sub:super-sub"},
                [],
            ),
            (
                "POST",
                "/iam/authorization/check",
                {"Authorization": "Bearer service-token"},
                "not-an-object",
            ),
        ]
        for method, path, headers, body in cases:
            with self.subTest(path=path, body=body):
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    self._json_request(
                        method,
                        path,
                        headers=headers,
                        body=body,
                    )
                response = raised.exception
                problem = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.code, 422)
                self.assertEqual(problem["status"], 422)
                self.assertEqual(problem["code"], "validation_error")
                self.assertEqual(problem["detail"], "Request body must be a JSON object.")

    def test_onboarding_activates_from_bearer_evidence(self) -> None:
        self.service.create_account(
            self.super_admin_id,
            {
                "email": "new-member@example.test",
                "organization": "MVP Organization",
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

    def test_unexpected_keycloak_state_error_is_audited(self) -> None:
        self.service.store = FailingStateStore()  # type: ignore[assignment]

        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request(
                "GET",
                "/iam/accounts",
                headers={
                    "Authorization": "Bearer dev-sub:super-sub",
                    "X-Correlation-Id": "corr-keycloak-failure",
                },
            )

        self.assertEqual(raised.exception.code, 503)
        events = [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event = events[-1]
        self.assertEqual(event["operation"], "iam.request.indeterminate")
        self.assertEqual(event["targetType"], "request")
        self.assertEqual(event["targetId"], "GET /iam/accounts")
        self.assertEqual(event["outcome"], "rejected")
        self.assertEqual(event["actorType"], "iam-api")
        self.assertEqual(event["reasonCode"], "keycloak_indeterminate")
        self.assertEqual(event["correlationId"], "corr-keycloak-failure")

    def _state(self) -> dict[str, object]:
        return self.service.store.load()

    def _account_state(self, account_id: str) -> dict[str, object]:
        return self._state()["accounts"][account_id]  # type: ignore[index]

    def _service_role_state(self, role_id: str) -> dict[str, object]:
        return self._state()["serviceRoles"][role_id]  # type: ignore[index]

    def _audit_events(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _assert_rejected_audit_event(
        self,
        operation: str,
        target_id: object,
        correlation_id: str,
        reason_code: str,
    ) -> None:
        self.assertTrue(
            any(
                event.get("operation") == operation
                and event.get("targetId") == target_id
                and event.get("outcome") == "rejected"
                and event.get("correlationId") == correlation_id
                and event.get("reasonCode") == reason_code
                for event in self._audit_events()
            ),
            f"missing rejected audit event for {operation} {correlation_id}",
        )

    def _assert_problem(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: object | None = None,
        status: int,
        code: str,
    ) -> dict[str, object]:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._json_request(method, path, headers=headers, body=body)
        response = raised.exception
        problem = json.loads(response.read().decode("utf-8"))
        self.assertEqual(response.code, status)
        self.assertEqual(problem["status"], status)
        self.assertEqual(problem["code"], code)
        return problem

    def _json_request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: object | None = None,
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
                "wrong-client": self._active_response(sub="kc-sub", client_id="other-backoffice"),
                "expired": self._active_response(sub="kc-sub", exp=int(time.time()) - 1),
                "inactive": {"active": False},
            }
        )
        validator = self._validator(url)

        self.assertEqual(validator.validate("valid-token").subject, "kc-sub")
        for token in ("wrong-issuer", "wrong-audience", "wrong-client", "expired", "inactive"):
            with self.subTest(token=token):
                with self.assertRaises(TokenValidationError) as raised:
                    validator.validate(token)
                self.assertEqual(raised.exception.status, 401)

    def test_oidc_subject_token_accepts_azp_as_token_client(self) -> None:
        _, url = self._serve_introspection(
            {
                "azp-token": {
                    **self._active_response(sub="kc-sub", client_id=None),
                    "azp": "backoffice",
                }
            }
        )

        self.assertEqual(self._validator(url).validate("azp-token").client_id, "backoffice")

    def test_raw_oidc_claims_do_not_grant_local_service_access(self) -> None:
        _, url = self._serve_introspection(
            {
                "misleading-token": {
                    **self._active_response(sub="member-sub"),
                    "email": "member@example.test",
                    "email_verified": True,
                    "iam_account_type": "super-admin",
                    "realm_access": {"roles": [DEFAULT_SERVICE_ROLE_ID]},
                }
            }
        )
        service = self._service_with_validator(url)
        member = service.create_account(
            service.bootstrap_first_super_admin(
                email="super-admin@example.test",
                name="Initial Super Admin",
                organization="MVP Organization",
                subject="super-sub",
            )["accountId"],
            {
                "email": "member@example.test",
                "organization": "MVP Organization",
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

    def test_admin_looking_token_for_inactive_account_fails_closed(self) -> None:
        _, url = self._serve_introspection(
            {
                "inactive-admin-looking-token": {
                    **self._active_response(sub="admin-sub"),
                    "acr": "iam-privileged",
                    "email": "inactive-admin@example.test",
                    "email_verified": True,
                    "iam_account_type": "super-admin",
                    "realm_access": {"roles": [DEFAULT_SERVICE_ROLE_ID]},
                }
            }
        )
        service = self._service_with_validator(url)
        super_admin_id = service.bootstrap_first_super_admin(
            email="super-admin@example.test",
            name="Initial Super Admin",
            organization="MVP Organization",
            subject="super-sub",
        )["accountId"]
        admin = service.create_account(
            super_admin_id,
            {
                "email": "inactive-admin@example.test",
                "organization": "MVP Organization",
                "name": "Inactive Admin",
                "accountType": "admin",
            },
            "corr-create-inactive-admin",
        )
        service.activate_onboarding_from_bearer(
            "Bearer inactive-admin-looking-token",
            {},
            "corr-activate-inactive-admin",
        )
        service.lifecycle(super_admin_id, admin["accountId"], "disable", "corr-disable-inactive-admin")

        decision = service.authorization_check(
            {
                "subjectToken": "inactive-admin-looking-token",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-inactive-admin-looking-deny",
        )

        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["reason"], "account_not_active")

    def test_oidc_service_token_requires_contract_claims(self) -> None:
        missing_issuer = self._active_response(sub="service-account", client_id=DEFAULT_SERVICE_ID)
        missing_issuer.pop("iss")
        missing_audience = self._active_response(sub="service-account", client_id=DEFAULT_SERVICE_ID)
        missing_audience.pop("aud")
        missing_subject = self._active_response(sub="service-account", client_id=DEFAULT_SERVICE_ID)
        missing_subject.pop("sub")
        _, url = self._serve_introspection(
            {
                "service-token": self._active_response(sub="service-account", client_id=DEFAULT_SERVICE_ID),
                "wrong-issuer": self._active_response(
                    sub="service-account",
                    iss="http://wrong.example.test/realms/mvp",
                    client_id=DEFAULT_SERVICE_ID,
                ),
                "missing-issuer": missing_issuer,
                "wrong-audience": self._active_response(
                    sub="service-account",
                    aud="other-service",
                    client_id=DEFAULT_SERVICE_ID,
                ),
                "missing-audience": missing_audience,
                "missing-subject": missing_subject,
                "wrong-client": self._active_response(sub="service-account", client_id="other-client"),
                "expired": self._active_response(
                    sub="service-account",
                    exp=int(time.time()) - 1,
                    client_id=DEFAULT_SERVICE_ID,
                ),
                "inactive": {"active": False},
            }
        )
        authenticator = OidcServiceTokenAuthenticator(
            f"{url}/introspect",
            DEFAULT_SERVICE_ID,
            "secret",
            DEFAULT_SERVICE_ID,
            self.issuer,
            self.audience,
            1,
        )

        authenticator.require_authorized("Bearer service-token")
        for token in (
            "wrong-issuer",
            "missing-issuer",
            "wrong-audience",
            "missing-audience",
            "missing-subject",
            "wrong-client",
            "expired",
            "inactive",
        ):
            with self.subTest(token=token):
                with self.assertRaises(TokenValidationError) as raised:
                    authenticator.require_authorized(f"Bearer {token}")
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
            "backoffice",
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
        client_id: str | None = "backoffice",
    ) -> dict[str, object]:
        response: dict[str, object] = {
            "active": True,
            "iss": iss or self.issuer,
            "aud": aud or [self.audience],
            "exp": exp or int(time.time()) + 60,
            "sub": sub,
        }
        if client_id is not None:
            response["client_id"] = client_id
        return response

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


class KeycloakBootstrapIdempotenceTests(unittest.TestCase):
    def test_user_profile_policy_declares_iam_attributes_and_disables_unmanaged_attributes(self) -> None:
        profile = {
            "attributes": [
                {
                    "name": "email",
                    "displayName": "Email",
                    "permissions": {"view": ["admin", "user"], "edit": ["admin", "user"]},
                }
            ],
            "unmanagedAttributePolicy": "ENABLED",
        }

        keycloak_bootstrap.apply_iam_user_profile_policy(profile)

        self.assertEqual(profile["unmanagedAttributePolicy"], "DISABLED")
        by_name = {
            attribute["name"]: attribute
            for attribute in profile["attributes"]
            if isinstance(attribute, dict)
        }
        self.assertEqual(by_name["email"]["displayName"], "Email")
        for attribute_name in keycloak_bootstrap.IAM_USER_ATTRIBUTES:
            self.assertEqual(by_name[attribute_name]["displayName"], attribute_name)
            self.assertFalse(by_name[attribute_name]["multivalued"])
            self.assertEqual(by_name[attribute_name]["permissions"], {"view": ["admin"], "edit": ["admin"]})

    def test_user_profile_verification_rejects_enabled_unmanaged_attributes(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unmanaged user-profile attributes are not disabled"):
            keycloak_bootstrap.verify_unmanaged_attributes_disabled({"unmanagedAttributePolicy": "ENABLED"})

    def test_user_profile_verification_accepts_missing_default_unmanaged_policy(self) -> None:
        profile = {"attributes": []}

        keycloak_bootstrap.apply_iam_user_profile_policy(profile)
        keycloak_bootstrap.verify_unmanaged_attributes_disabled(profile)

        self.assertNotIn("unmanagedAttributePolicy", profile)

    def test_client_merge_preserves_existing_unowned_configuration(self) -> None:
        existing = {
            "id": "client-uuid",
            "clientId": "backoffice",
            "name": "Custom Existing Name",
            "redirectUris": ["https://admin.example.test/callback"],
            "webOrigins": ["https://admin.example.test"],
            "attributes": {
                "custom.attribute": "keep",
                "post.logout.redirect.uris": "https://admin.example.test/logout",
            },
            "optionalClientScopes": ["profile"],
        }
        desired = {
            "clientId": "backoffice",
            "name": "Access-Control Backoffice MVP",
            "enabled": True,
            "protocol": "openid-connect",
            "redirectUris": ["http://localhost:9999/callback"],
            "webOrigins": ["+"],
            "attributes": {
                "pkce.code.challenge.method": "S256",
                "post.logout.redirect.uris": "http://localhost:9999/callback",
            },
        }

        merged = keycloak_bootstrap.merge_client_representation(existing, desired)

        self.assertEqual(merged["id"], "client-uuid")
        self.assertEqual(merged["optionalClientScopes"], ["profile"])
        self.assertEqual(
            merged["redirectUris"],
            ["https://admin.example.test/callback", "http://localhost:9999/callback"],
        )
        self.assertEqual(merged["webOrigins"], ["https://admin.example.test", "+"])
        self.assertEqual(merged["attributes"]["custom.attribute"], "keep")
        self.assertEqual(merged["attributes"]["pkce.code.challenge.method"], "S256")
        self.assertEqual(merged["attributes"]["post.logout.redirect.uris"], "http://localhost:9999/callback")

    def test_fixture_user_merge_preserves_iam_managed_user(self) -> None:
        existing = {
            "id": "super-sub",
            "username": "mvp-super-admin",
            "enabled": False,
            "email": "renamed-super-admin@example.test",
            "emailVerified": False,
            "firstName": "Renamed",
            "lastName": "Admin",
            "requiredActions": ["UPDATE_PASSWORD"],
            "attributes": {
                "iam.account_id": ["acc_bootstrap_super_admin"],
                "iam.lifecycle": ["disabled"],
                "iam.linked_subject": ["super-sub"],
                "iam.organization": ["MVP Organization"],
                "iam.assigned_service_roles": ["[]"],
                "iam.schema_version": ["iam-schema-v1"],
            },
        }
        desired = keycloak_bootstrap.fixture_user_payload(
            "mvp-super-admin",
            "super-admin@example.test",
            "Initial",
            "Super Admin",
        )

        merged = keycloak_bootstrap.merge_fixture_user_representation(existing, desired)

        self.assertEqual(merged, existing)

    def test_fixture_user_merge_updates_unmanaged_fixture_without_dropping_attributes(self) -> None:
        existing = {
            "id": "fixture-user",
            "username": "mvp-member",
            "enabled": False,
            "email": "old@example.test",
            "emailVerified": False,
            "firstName": "Old",
            "lastName": "Name",
            "requiredActions": ["VERIFY_EMAIL"],
            "attributes": {"custom.attribute": ["keep"]},
        }
        desired = keycloak_bootstrap.fixture_user_payload(
            "mvp-member",
            "mvp-member@example.test",
            "MVP",
            "Member",
        )

        merged = keycloak_bootstrap.merge_fixture_user_representation(existing, desired)

        self.assertEqual(merged["email"], "mvp-member@example.test")
        self.assertTrue(merged["enabled"])
        self.assertTrue(merged["emailVerified"])
        self.assertEqual(merged["requiredActions"], [])
        self.assertEqual(merged["attributes"], {"custom.attribute": ["keep"]})


class FakeKeycloakAdminClient:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, object]] = {}
        self.roles: dict[str, dict[str, dict[str, object]]] = {}
        self.assignments: dict[str, dict[str, set[str]]] = {}
        self.action_emails: list[dict[str, object]] = []
        self.next_user = 1

    def add_user(
        self,
        user_id: str,
        email: str,
        attributes: dict[str, list[str]],
        assignments: dict[str, set[str]],
        *,
        enabled: bool = True,
        first_name: str = "Test",
        last_name: str = "User",
    ) -> None:
        self.users[user_id] = {
            "id": user_id,
            "username": email,
            "enabled": enabled,
            "email": email,
            "emailVerified": True,
            "firstName": first_name,
            "lastName": last_name,
            "requiredActions": [],
            "attributes": attributes,
        }
        self.assignments[user_id] = {client_id: set(names) for client_id, names in assignments.items()}

    def list_users(self) -> list[dict[str, object]]:
        return [self._copy_user(user) for user in self.users.values()]

    def get_user(self, user_id: str) -> dict[str, object] | None:
        user = self.users.get(user_id)
        return self._copy_user(user) if user else None

    def find_user_by_email(self, email: str) -> dict[str, object] | None:
        for user in self.users.values():
            if str(user.get("email", "")).lower() == email.lower():
                return self._copy_user(user)
        return None

    def find_user_by_attribute(self, attr_name: str, value: str) -> dict[str, object] | None:
        for user in self.users.values():
            attrs = user.get("attributes")
            if isinstance(attrs, dict) and attrs.get(attr_name) == [value]:
                return self._copy_user(user)
        return None

    def create_user(self, payload: dict[str, object]) -> str:
        user_id = f"kc-user-{self.next_user}"
        self.next_user += 1
        self.users[user_id] = {**payload, "id": user_id}
        self.assignments[user_id] = {}
        return user_id

    def update_user(self, user_id: str, payload: dict[str, object]) -> None:
        self.users[user_id] = {**payload, "id": user_id}

    def execute_actions_email(
        self,
        user_id: str,
        actions: list[str],
        *,
        client_id: str,
        redirect_uri: str | None,
        lifespan_seconds: int | None,
    ) -> None:
        self.action_emails.append(
            {
                "userId": user_id,
                "actions": list(actions),
                "clientId": client_id,
                "redirectUri": redirect_uri,
                "lifespanSeconds": lifespan_seconds,
            }
        )

    def list_client_roles(self, client_id: str) -> list[dict[str, object]]:
        return [dict(role) for role in self.roles.get(client_id, {}).values()]

    def ensure_client_role(
        self,
        client_id: str,
        role_name: str,
        description: str,
        attributes: dict[str, list[str]],
    ) -> dict[str, object]:
        client_roles = self.roles.setdefault(client_id, {})
        existing = client_roles.get(role_name, {})
        merged_attributes = dict(existing.get("attributes") if isinstance(existing.get("attributes"), dict) else {})
        merged_attributes.update(attributes)
        role = {
            "id": f"{client_id}:{role_name}",
            "name": role_name,
            "description": description,
            "clientRole": True,
            "attributes": merged_attributes,
        }
        client_roles[role_name] = role
        return dict(role)

    def get_user_client_roles(self, user_id: str, client_id: str) -> list[dict[str, object]]:
        names = self.assignments.get(user_id, {}).get(client_id, set())
        return [
            dict(self.roles.get(client_id, {}).get(name, {"name": name, "attributes": {}}))
            for name in sorted(names)
        ]

    def add_user_client_roles(self, user_id: str, client_id: str, role_names: list[str]) -> None:
        self.assignments.setdefault(user_id, {}).setdefault(client_id, set()).update(role_names)

    def remove_user_client_roles(self, user_id: str, client_id: str, role_names: list[str]) -> None:
        self.assignments.setdefault(user_id, {}).setdefault(client_id, set()).difference_update(role_names)

    def _copy_user(self, user: dict[str, object]) -> dict[str, object]:
        copied = dict(user)
        attrs = copied.get("attributes")
        if isinstance(attrs, dict):
            copied["attributes"] = {str(key): list(value) for key, value in attrs.items()}
        return copied


class KeycloakStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.client = FakeKeycloakAdminClient()
        self.store = KeycloakStateStore(
            self.client,  # type: ignore[arg-type]
            backoffice_client_id="backoffice",
            service_client_ids=[DEFAULT_SERVICE_ID],
        )
        self.client.ensure_client_role(
            DEFAULT_SERVICE_ID,
            "consult",
            "Initial MVP access-check demo consultation role.",
            {
                "iam.role_id": [DEFAULT_SERVICE_ROLE_ID],
                "iam.role_status": ["active"],
                "iam.schema_version": ["iam-schema-v1"],
            },
        )
        self.client.add_user(
            "super-sub",
            "super-admin@example.test",
            {
                "iam.account_id": ["acc-super"],
                "iam.lifecycle": ["active"],
                "iam.linked_subject": ["super-sub"],
                "iam.organization": ["MVP Organization"],
                "iam.assigned_service_roles": ["[]"],
                "iam.schema_version": ["iam-schema-v1"],
            },
            {"backoffice": {"account-type-super-admin"}},
            first_name="Super",
            last_name="Admin",
        )
        self.subject_tokens = {
            "super-token": SubjectEvidence(subject="super-sub"),
            "member-token": SubjectEvidence(
                subject="member-sub",
                email="member@example.test",
                email_verified=True,
            ),
        }
        self.audit_path = Path(self.tmp.name) / "audit.jsonl"
        self.service = AccessControlService(
            self.store,
            AuditWriter(self.audit_path),
            StaticSubjectTokenValidator(self.subject_tokens),
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_control_plane_mutations_are_written_to_keycloak_state(self) -> None:
        created = self.service.create_account(
            "acc-super",
            {
                "email": "member@example.test",
                "organization": "MVP Organization",
                "name": "MVP Member",
                "accountType": "member",
            },
            "corr-create",
        )
        account_id = created["accountId"]
        user = self.client.find_user_by_attribute("iam.account_id", account_id)
        self.assertIsNotNone(user)
        assert user is not None
        self.assertEqual(user["attributes"]["iam.lifecycle"], ["invited"])
        self.assertEqual(json.loads(user["attributes"]["iam.assigned_service_roles"][0]), [])
        self.assertIn("account-type-member", self.client.assignments[user["id"]]["backoffice"])

        self.service.assign_service_role("acc-super", account_id, DEFAULT_SERVICE_ROLE_ID, "corr-assign")
        user = self.client.find_user_by_attribute("iam.account_id", account_id)
        assert user is not None
        self.assertEqual(
            json.loads(user["attributes"]["iam.assigned_service_roles"][0]),
            [DEFAULT_SERVICE_ROLE_ID],
        )
        self.assertNotIn("consult", self.client.assignments[user["id"]].get(DEFAULT_SERVICE_ID, set()))

        activated = self.service.activate_onboarding_from_bearer("Bearer member-token", {}, "corr-activate")
        user = self.client.find_user_by_attribute("iam.account_id", account_id)
        assert user is not None
        self.assertEqual(activated["lifecycle"], "active")
        self.assertEqual(user["attributes"]["iam.lifecycle"], ["active"])
        self.assertEqual(user["attributes"]["iam.linked_subject"], ["member-sub"])

        decision = self.service.authorization_check(
            {
                "subjectToken": "member-token",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-check",
        )
        self.assertEqual(decision["decision"], "allow")

    def test_new_invited_member_is_prepared_for_keycloak_onboarding(self) -> None:
        created = self.service.create_account(
            "acc-super",
            {
                "email": "prepared-member@example.test",
                "organization": "MVP Organization",
                "name": "Prepared Member",
                "accountType": "member",
            },
            "corr-create-prepared-member",
        )

        user = self.client.find_user_by_attribute("iam.account_id", created["accountId"])
        self.assertIsNotNone(user)
        assert user is not None
        self.assertEqual(user["requiredActions"], ["VERIFY_EMAIL", "UPDATE_PASSWORD"])
        self.assertFalse(user["emailVerified"])
        self.assertEqual(self.client.action_emails, [])

    def test_new_invited_admin_sends_privileged_onboarding_actions_when_enabled(self) -> None:
        store = KeycloakStateStore(
            self.client,  # type: ignore[arg-type]
            backoffice_client_id="backoffice",
            service_client_ids=[DEFAULT_SERVICE_ID],
            send_onboarding_action_emails=True,
            onboarding_action_email_redirect_uri="http://localhost:9999/callback",
            onboarding_action_email_lifespan_seconds=900,
        )
        service = AccessControlService(
            store,
            AuditWriter(self.audit_path),
            StaticSubjectTokenValidator(self.subject_tokens),
        )

        created = service.create_account(
            "acc-super",
            {
                "email": "prepared-admin@example.test",
                "organization": "MVP Organization",
                "name": "Prepared Admin",
                "accountType": "admin",
            },
            "corr-create-prepared-admin",
        )

        user = self.client.find_user_by_attribute("iam.account_id", created["accountId"])
        self.assertIsNotNone(user)
        assert user is not None
        self.assertEqual(user["requiredActions"], ["VERIFY_EMAIL", "UPDATE_PASSWORD", "CONFIGURE_TOTP"])
        self.assertEqual(
            self.client.action_emails,
            [
                {
                    "userId": user["id"],
                    "actions": ["VERIFY_EMAIL", "UPDATE_PASSWORD", "CONFIGURE_TOTP"],
                    "clientId": "backoffice",
                    "redirectUri": "http://localhost:9999/callback",
                    "lifespanSeconds": 900,
                }
            ],
        )

    def test_keycloak_account_type_drift_blocks_actor_resolution(self) -> None:
        self.client.assignments["super-sub"]["backoffice"].add("account-type-admin")

        with self.assertRaises(ApiError) as raised:
            self.service.resolve_actor_id_from_bearer("Bearer super-token", "corr-drift")

        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(raised.exception.code, "iam_state_drift")

    def test_direct_keycloak_service_role_addition_is_drift_and_denied(self) -> None:
        self.client.add_user(
            "drift-member-sub",
            "drift-member@example.test",
            {
                "iam.account_id": ["acc-drift-member"],
                "iam.lifecycle": ["active"],
                "iam.linked_subject": ["drift-member-sub"],
                "iam.organization": ["MVP Organization"],
                "iam.assigned_service_roles": ["[]"],
                "iam.schema_version": ["iam-schema-v1"],
            },
            {
                "backoffice": {"account-type-member"},
                DEFAULT_SERVICE_ID: {"consult"},
            },
            first_name="Drift",
            last_name="Member",
        )
        self.subject_tokens["drift-member-token"] = SubjectEvidence(subject="drift-member-sub")

        decision = self.service.authorization_check(
            {
                "subjectToken": "drift-member-token",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-direct-role-drift",
        )

        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["reason"], "drift_detected")

    def test_direct_keycloak_service_role_mapping_is_drift_even_when_canonical_assignment_exists(self) -> None:
        self.client.add_user(
            "assigned-plus-direct-sub",
            "assigned-plus-direct@example.test",
            {
                "iam.account_id": ["acc-assigned-plus-direct"],
                "iam.lifecycle": ["active"],
                "iam.linked_subject": ["assigned-plus-direct-sub"],
                "iam.organization": ["MVP Organization"],
                "iam.assigned_service_roles": [json.dumps([DEFAULT_SERVICE_ROLE_ID])],
                "iam.schema_version": ["iam-schema-v1"],
            },
            {
                "backoffice": {"account-type-member"},
                DEFAULT_SERVICE_ID: {"consult"},
            },
            first_name="Assigned",
            last_name="Direct",
        )
        self.subject_tokens["assigned-plus-direct-token"] = SubjectEvidence(subject="assigned-plus-direct-sub")

        decision = self.service.authorization_check(
            {
                "subjectToken": "assigned-plus-direct-token",
                "serviceId": DEFAULT_SERVICE_ID,
                "requiredRole": DEFAULT_SERVICE_ROLE_ID,
            },
            "corr-direct-role-plus-canonical-drift",
        )

        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["reason"], "drift_detected")

    def test_direct_keycloak_lifecycle_change_is_drift_and_audited(self) -> None:
        cases = (
            ("active-user-disabled", "active", False),
            ("disabled-user-enabled", "disabled", True),
        )
        for subject, lifecycle, enabled in cases:
            with self.subTest(lifecycle=lifecycle, enabled=enabled):
                correlation_id = f"corr-lifecycle-drift-{subject}"
                account_id = f"acc-{subject}"
                self.client.add_user(
                    subject,
                    f"{subject}@example.test",
                    {
                        "iam.account_id": [account_id],
                        "iam.lifecycle": [lifecycle],
                        "iam.linked_subject": [subject],
                        "iam.organization": ["MVP Organization"],
                        "iam.assigned_service_roles": [json.dumps([DEFAULT_SERVICE_ROLE_ID])],
                        "iam.schema_version": ["iam-schema-v1"],
                    },
                    {"backoffice": {"account-type-member"}},
                    enabled=enabled,
                    first_name="Lifecycle",
                    last_name="Drift",
                )
                token = f"{subject}-token"
                self.subject_tokens[token] = SubjectEvidence(subject=subject)

                decision = self.service.authorization_check(
                    {
                        "subjectToken": token,
                        "serviceId": DEFAULT_SERVICE_ID,
                        "requiredRole": DEFAULT_SERVICE_ROLE_ID,
                    },
                    correlation_id,
                )

                self.assertEqual(decision["decision"], "deny")
                self.assertEqual(decision["reason"], "drift_detected")
                self.assertTrue(
                    any(
                        event.get("operation") == "authorization.check.denied"
                        and event.get("outcome") == "rejected"
                        and event.get("correlationId") == correlation_id
                        and event.get("reasonCode") == "drift_detected"
                        for event in self._audit_events()
                    ),
                    f"missing lifecycle drift audit event for {correlation_id}",
                )

    def _audit_events(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
