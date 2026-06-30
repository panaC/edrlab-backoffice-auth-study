from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import html.parser
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Callable

from .config import DEFAULT_PRIVILEGED_ACR, DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID


KEYCLOAK_BASE_URL = os.environ.get("KEYCLOAK_BASE_URL", "http://keycloak:8080").rstrip("/")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "access-control-mvp")
KC_BOOTSTRAP_ADMIN_USERNAME = os.environ.get("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
KC_BOOTSTRAP_ADMIN_PASSWORD = os.environ.get("KC_BOOTSTRAP_ADMIN_PASSWORD", "change-me-admin-password")
BACKOFFICE_CLIENT_ID = os.environ.get("KEYCLOAK_BACKOFFICE_CLIENT_ID", "backoffice")
BACKOFFICE_CLIENT_SECRET = os.environ.get("KEYCLOAK_BACKOFFICE_CLIENT_SECRET", "change-me-backoffice-secret")
BACKOFFICE_REDIRECT_URI = os.environ.get("KEYCLOAK_BACKOFFICE_REDIRECT_URI", "http://localhost:9999/callback")
SUPER_ADMIN_USERNAME = os.environ.get("KEYCLOAK_SUPER_ADMIN_USERNAME", "mvp-super-admin")
SUPER_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_SUPER_ADMIN_PASSWORD", "change-me-super-admin-password")
BOOTSTRAP_SUPER_ADMIN_EMAIL = os.environ.get("BOOTSTRAP_SUPER_ADMIN_EMAIL", "super-admin@example.test")
IAM_API_BASE_URL = os.environ.get("IAM_API_BASE_URL", "http://iam-api:8000").rstrip("/")
DEMO_BASE_URL = os.environ.get("DEMO_BASE_URL", "http://access-check-demo-service:8001").rstrip("/")
EVIDENCE_ROOT = Path(os.environ.get("HUMAN_E2E_EVIDENCE_ROOT", "/app/evidence"))
LOCAL_TEST_PASSWORD = os.environ.get("HUMAN_E2E_FIXTURE_PASSWORD", "change-me-human-e2e-password")
NORMAL_ACR = os.environ.get("IAM_NORMAL_ACR", "iam-normal")
PRIVILEGED_ACR = os.environ.get("IAM_PRIVILEGED_ACR", DEFAULT_PRIVILEGED_ACR)
OTP_LABEL_PREFIX = "iam-human-e2e"
ONBOARDING_ACTION_EMAILS_ENABLED = os.environ.get("KEYCLOAK_ONBOARDING_ACTION_EMAILS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
KEYCLOAK_SMTP_HOST = os.environ.get("KEYCLOAK_SMTP_HOST", "mailpit")
KEYCLOAK_SMTP_PORT = os.environ.get("KEYCLOAK_SMTP_PORT", "1025")
KEYCLOAK_SMTP_FROM = os.environ.get("KEYCLOAK_SMTP_FROM", "no-reply@example.test")
MAILPIT_API_BASE_URL = os.environ.get("MAILPIT_API_BASE_URL", "http://mailpit:8025").rstrip("/")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class LoginFormParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.action: str | None = None
        self.inputs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag.lower() == "form" and self.action is None:
            action = values.get("action", "")
            if action:
                self.action = html.unescape(action)
        if tag.lower() == "input":
            name = values.get("name")
            if name:
                self.inputs[name] = values.get("value", "")


class Evidence:
    def __init__(self, evidence_dir: Path, *, interactive: bool) -> None:
        self.evidence_dir = evidence_dir
        self.interactive = interactive
        self.log_path = evidence_dir / "human-e2e-output.log"
        self.summary_path = evidence_dir / "summary.json"
        self.results: list[dict[str, Any]] = []
        evidence_dir.mkdir(parents=True, exist_ok=True)

    def write(self, message: str = "") -> None:
        line = mask(message)
        print(line, flush=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def section(self, title: str) -> None:
        self.write("")
        self.write(f"## {title}")

    def result(self, case_id: str, status: str, detail: str, **extra: Any) -> None:
        item = {"caseId": case_id, "status": status, "detail": detail, **extra}
        self.results.append(item)
        self.write(f"[{status}] {case_id}: {detail}")

    def payload(self, label: str, payload: Any) -> None:
        body = json.dumps(redact(payload), indent=2, sort_keys=True)
        self.write(f"{label}:\n{body}")

    def pause(self) -> None:
        if not self.interactive:
            return
        self.write("Press Enter to continue...")
        input()

    def finalize(self) -> None:
        summary = {
            "status": "failed" if any(item["status"] == "FAIL" for item in self.results) else "complete",
            "finishedAt": now(),
            "evidenceDir": str(self.evidence_dir),
            "logPath": str(self.log_path),
            "results": self.results,
        }
        self.summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.write("")
        self.write("## Evidence")
        self.write(f"Log: {self.log_path}")
        self.write(f"Summary: {self.summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive human e2e runner for the access-control MVP.")
    parser.add_argument("--yes", action="store_true", help="Run without pausing between test cases.")
    parser.add_argument(
        "--email-onboarding",
        action="store_true",
        help="Also run the SMTP-backed Keycloak action-email onboarding test.",
    )
    args = parser.parse_args()

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    evidence = Evidence(EVIDENCE_ROOT / f"human-e2e-script-{run_id}", interactive=not args.yes and sys.stdin.isatty())
    state: dict[str, Any] = {"runId": run_id}
    evidence.write("Human E2E script started.")
    evidence.write(f"Run ID: {run_id}")
    evidence.write(f"Keycloak: {KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}")
    evidence.write(f"IAM API: {IAM_API_BASE_URL}")
    evidence.write(f"Demo service: {DEMO_BASE_URL}")
    if args.email_onboarding:
        wait_for_mailpit()
        configure_realm_smtp(keycloak_admin_access_token())

    cases: list[tuple[str, str, Callable[[Evidence, dict[str, Any]], None]]] = [
        ("E2E-001", "Runtime bootstrap and health", e2e_001_runtime),
        ("E2E-002", "Super-admin login and self profile", e2e_002_super_admin),
        ("E2E-003", "Super-admin creates admin account", e2e_003_create_admin),
        ("E2E-004", "Admin identity fixture and onboarding", e2e_004_admin_onboarding),
        ("E2E-005", "Admin creates member", e2e_005_admin_creates_member),
        ("E2E-006", "Member onboarding and self profile", e2e_006_member_onboarding),
        ("E2E-007", "Protected demo service deny/allow/remove/deny", e2e_007_demo_service),
        ("E2E-008", "Admin lifecycle management stops access", e2e_008_lifecycle),
        ("E2E-009", "Super-admin service-role catalog operation", e2e_009_catalog),
        ("E2E-010", "Super-admin audit consultation", e2e_010_audit),
        ("E2E-011", "Logout and actor isolation", e2e_011_logout),
    ]
    if args.email_onboarding:
        cases.append(("E2E-012", "SMTP action-email onboarding", e2e_012_email_onboarding))
    try:
        for case_id, title, callback in cases:
            evidence.section(f"{case_id} {title}")
            try:
                callback(evidence, state)
            except SkipCase as exc:
                evidence.result(case_id, "SKIP", str(exc))
            except Exception as exc:
                evidence.result(case_id, "FAIL", str(exc))
            evidence.pause()
    finally:
        evidence.finalize()
    if any(item["status"] == "FAIL" for item in evidence.results):
        raise SystemExit(1)


def e2e_001_runtime(evidence: Evidence, state: dict[str, Any]) -> None:
    wait_for_runtime()
    health_status, health = request_json("GET", f"{IAM_API_BASE_URL}/healthz", expected={200})
    demo_status, demo = request_json("GET", f"{DEMO_BASE_URL}/access-check-demo", expected={401})
    assert_equal(health.get("status"), "ok", "IAM health must be ok")
    assert_equal(demo.get("result"), "KO", "Unauthenticated demo result must be KO")
    evidence.payload("health", {"status": health_status, "body": health})
    evidence.payload("unauthenticatedDemo", {"status": demo_status, "body": demo})
    evidence.result("E2E-001", "PASS", "Runtime endpoints are reachable and fail closed without a bearer token.")


def e2e_002_super_admin(evidence: Evidence, state: dict[str, Any]) -> None:
    token_response = login_with_authorization_code(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, acr_value=NORMAL_ACR)
    state["superAdminToken"] = token_response["access_token"]
    state["superAdminIdToken"] = token_response["id_token"]
    claims = decode_claims(token_response["id_token"])
    assert_equal(str(claims.get("email", "")).lower(), BOOTSTRAP_SUPER_ADMIN_EMAIL.lower(), "Unexpected super-admin email")
    _, me = request_json("GET", f"{IAM_API_BASE_URL}/iam/me", actor_token=state["superAdminToken"], expected={200})
    _, services = request_json("GET", f"{IAM_API_BASE_URL}/iam/me/services", actor_token=state["superAdminToken"], expected={200})
    assert_equal(me.get("accountType"), "super-admin", "Expected super-admin account type")
    assert_equal(me.get("lifecycle"), "active", "Expected active super-admin")
    evidence.payload("superAdminMe", me)
    evidence.payload("superAdminServices", services)
    evidence.result("E2E-002", "PASS", "Super-admin authenticated through Keycloak and resolved to IAM.")


def e2e_003_create_admin(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "superAdminToken")
    state["adminUsername"] = f"human-admin-{state['runId']}"
    state["adminEmail"] = f"{state['adminUsername']}@example.test"
    _, account = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts",
        actor_token=state["superAdminToken"],
        body={
            "email": state["adminEmail"],
            "organization": "MVP Organization",
            "name": "Human E2E Admin",
            "accountType": "admin",
        },
        expected={200},
    )
    state["adminAccountId"] = account["accountId"]
    assert_equal(account.get("accountType"), "admin", "Created account must be admin")
    assert_equal(account.get("lifecycle"), "invited", "Created admin must start invited")
    evidence.payload("adminAccount", account)
    evidence.result("E2E-003", "PASS", "Super-admin created an invited admin account through IAM.")


def e2e_004_admin_onboarding(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "adminEmail")
    keycloak_admin_token = keycloak_admin_access_token()
    admin_user = ensure_keycloak_user(keycloak_admin_token, state["adminUsername"], state["adminEmail"], LOCAL_TEST_PASSWORD)
    state["adminUsername"] = admin_user["username"]
    otp_secret, otp_credential = ensure_totp_credential(keycloak_admin_token, admin_user["id"], state["adminUsername"])
    token_response = login_with_authorization_code(
        state["adminUsername"],
        LOCAL_TEST_PASSWORD,
        acr_value=PRIVILEGED_ACR,
        otp_secret=otp_secret,
    )
    id_claims = decode_claims(token_response["id_token"])
    assert_equal(id_claims.get("acr"), PRIVILEGED_ACR, "Privileged login must return the required ACR")
    state["adminToken"] = token_response["access_token"]
    status, body = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/onboarding/activate",
        actor_token=state["adminToken"],
        body={},
        expected={200, 403},
    )
    evidence.payload(
        "adminPrivilegedAuthentication",
        {
            "requiredAcr": PRIVILEGED_ACR,
            "observedAcr": id_claims.get("acr"),
            "otpCredential": otp_credential,
            "otpSeedValueInEvidence": False,
        },
    )
    evidence.payload("adminActivation", {"status": status, "body": body})
    if status == 403 and body.get("code") == "missing_privileged_acr":
        state.pop("adminToken", None)
        raise RuntimeError(
            "Admin onboarding was rejected because the token lacks privileged ACR evidence. "
            "Expected Keycloak OTP step-up to produce the configured privileged ACR."
        )
    assert_equal(status, 200, "Admin onboarding must succeed")
    assert_equal(body.get("accountId"), state["adminAccountId"], "Activated admin account mismatch")
    assert_equal(body.get("lifecycle"), "active", "Activated admin must be active")
    state["adminActive"] = True
    evidence.result("E2E-004", "PASS", "Admin identity fixture authenticated and activated through onboarding.")


def e2e_005_admin_creates_member(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "adminActive")
    require_state(state, "adminToken")
    state["memberUsername"] = f"human-member-{state['runId']}"
    state["memberEmail"] = f"{state['memberUsername']}@example.test"
    _, account = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts",
        actor_token=state["adminToken"],
        body={
            "email": state["memberEmail"],
            "organization": "MVP Organization",
            "name": "Human E2E Member",
            "accountType": "member",
        },
        expected={200},
    )
    state["memberAccountId"] = account["accountId"]
    denied_status, denied = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts",
        actor_token=state["adminToken"],
        body={
            "email": f"blocked-admin-{state['runId']}@example.test",
            "organization": "MVP Organization",
            "name": "Blocked Admin",
            "accountType": "admin",
        },
        expected={403},
    )
    evidence.payload("memberAccount", account)
    evidence.payload("adminCreateAdminDenied", {"status": denied_status, "body": denied})
    evidence.result("E2E-005", "PASS", "Admin created a member and was denied privileged account creation.")


def e2e_006_member_onboarding(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "memberEmail")
    keycloak_admin_token = keycloak_admin_access_token()
    member_user = ensure_keycloak_user(keycloak_admin_token, state["memberUsername"], state["memberEmail"], LOCAL_TEST_PASSWORD)
    state["memberUsername"] = member_user["username"]
    token_response = login_with_authorization_code(state["memberUsername"], LOCAL_TEST_PASSWORD, acr_value=NORMAL_ACR)
    state["memberToken"] = token_response["access_token"]
    state["memberIdToken"] = token_response["id_token"]
    _, activated = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/onboarding/activate",
        actor_token=state["memberToken"],
        body={},
        expected={200},
    )
    _, me = request_json("GET", f"{IAM_API_BASE_URL}/iam/me", actor_token=state["memberToken"], expected={200})
    _, services = request_json("GET", f"{IAM_API_BASE_URL}/iam/me/services", actor_token=state["memberToken"], expected={200})
    denied_status, denied = request_json("GET", f"{IAM_API_BASE_URL}/iam/accounts", actor_token=state["memberToken"], expected={403})
    assert_equal(activated.get("accountId"), state["memberAccountId"], "Activated member account mismatch")
    evidence.payload("memberActivation", activated)
    evidence.payload("memberMe", me)
    evidence.payload("memberServicesBeforeRole", services)
    evidence.payload("memberListAccountsDenied", {"status": denied_status, "body": denied})
    evidence.result("E2E-006", "PASS", "Member activated, read self profile, and was denied account management.")


def e2e_007_demo_service(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "memberToken")
    before_status, before = request_json_with_retry(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": f"Bearer {state['memberToken']}"},
        expected={403},
    )
    _, assigned = request_json(
        "PUT",
        f"{IAM_API_BASE_URL}/iam/accounts/{state['memberAccountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=state["adminToken"],
        expected={200},
    )
    allow_status, allow = request_json_with_retry(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": f"Bearer {state['memberToken']}"},
        expected={200},
    )
    _, removed = request_json(
        "DELETE",
        f"{IAM_API_BASE_URL}/iam/accounts/{state['memberAccountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=state["adminToken"],
        expected={200},
    )
    after_status, after = request_json_with_retry(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": f"Bearer {state['memberToken']}"},
        expected={403},
    )
    evidence.payload("demoBeforeRole", {"status": before_status, "body": before})
    evidence.payload("roleAssigned", assigned)
    evidence.payload("demoAfterRole", {"status": allow_status, "body": allow})
    evidence.payload("roleRemoved", removed)
    evidence.payload("demoAfterRemoval", {"status": after_status, "body": after})
    evidence.result("E2E-007", "PASS", "Demo service denied, allowed after assignment, and denied after removal.")


def e2e_008_lifecycle(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "memberToken")
    request_json(
        "PUT",
        f"{IAM_API_BASE_URL}/iam/accounts/{state['memberAccountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=state["adminToken"],
        expected={200},
    )
    _, disabled = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts/{state['memberAccountId']}/disable",
        actor_token=state["adminToken"],
        expected={200},
    )
    denied_status, denied = request_json(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": f"Bearer {state['memberToken']}"},
        expected={401, 403},
    )
    _, restored = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts/{state['memberAccountId']}/restore",
        actor_token=state["adminToken"],
        expected={200},
    )
    evidence.payload("memberDisabled", disabled)
    evidence.payload("demoAfterDisable", {"status": denied_status, "body": denied})
    evidence.payload("memberRestored", restored)
    evidence.result("E2E-008", "PASS", "Member disablement stopped protected-service access and restore succeeded.")


def e2e_009_catalog(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "adminActive")
    require_state(state, "adminToken")
    _, roles = request_json("GET", f"{IAM_API_BASE_URL}/iam/service-roles", actor_token=state["adminToken"], expected={200})
    role_id = f"access-check-demo:human-{state['runId'].lower()}"
    admin_status, admin_denied = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/service-roles",
        actor_token=state["adminToken"],
        body={"roleId": role_id, "serviceId": DEFAULT_SERVICE_ID, "description": "Human E2E role"},
        expected={403},
    )
    _, created = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/service-roles",
        actor_token=state["superAdminToken"],
        body={"roleId": role_id, "serviceId": DEFAULT_SERVICE_ID, "description": "Human E2E role"},
        expected={200},
    )
    _, disabled = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/service-roles/{role_id}/disable",
        actor_token=state["superAdminToken"],
        expected={200},
    )
    _, archived = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/service-roles/{role_id}/archive",
        actor_token=state["superAdminToken"],
        expected={200},
    )
    evidence.payload("adminServiceRoles", roles)
    evidence.payload("adminCreateServiceRoleDenied", {"status": admin_status, "body": admin_denied})
    evidence.payload("superAdminCreatedServiceRole", created)
    evidence.payload("superAdminArchivedServiceRole", archived)
    assert_equal(disabled.get("status"), "disabled", "Cleanup role must first be disabled")
    assert_equal(archived.get("status"), "archived", "Cleanup role must be archived")
    evidence.result("E2E-009", "PASS", "Admin read catalog, admin mutation was denied, super-admin mutation succeeded, and the test role was archived.")


def e2e_010_audit(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "adminActive")
    require_state(state, "adminToken")
    admin_status, admin_denied = request_json(
        "GET", f"{IAM_API_BASE_URL}/iam/audit/events", actor_token=state["adminToken"], expected={403}
    )
    _, audit = request_json("GET", f"{IAM_API_BASE_URL}/iam/audit/events", actor_token=state["superAdminToken"], expected={200})
    operations = [event.get("operation") for event in audit.get("events", []) if isinstance(event, dict)]
    evidence.payload("adminAuditDenied", {"status": admin_status, "body": admin_denied})
    evidence.payload("superAdminAuditOperations", operations[-20:])
    evidence.result("E2E-010", "PASS", "Audit consultation was denied to admin and allowed to super-admin.")


def e2e_011_logout(evidence: Evidence, state: dict[str, Any]) -> None:
    no_token_status, no_token = request_json("GET", f"{IAM_API_BASE_URL}/iam/me", expected={401})
    logout_result = None
    if isinstance(state.get("memberIdToken"), str):
        logout_result = keycloak_logout(state["memberIdToken"])
    evidence.payload("noTokenMeDenied", {"status": no_token_status, "body": no_token})
    evidence.payload("keycloakLogout", logout_result or {"status": "not_executed"})
    evidence.result("E2E-011", "PASS", "No-token IAM request was denied and Keycloak logout was exercised when possible.")


def e2e_012_email_onboarding(evidence: Evidence, state: dict[str, Any]) -> None:
    require_state(state, "superAdminToken")
    if not ONBOARDING_ACTION_EMAILS_ENABLED:
        raise SkipCase("KEYCLOAK_ONBOARDING_ACTION_EMAILS is not enabled for the IAM API runtime.")
    wait_for_mailpit()
    admin_token = keycloak_admin_access_token()
    configure_realm_smtp(admin_token)
    clear_mailpit_messages()

    username = f"email-member-{state['runId']}".lower()
    email = f"{username}@example.test"
    password = f"{LOCAL_TEST_PASSWORD}-email"
    _, account = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/accounts",
        actor_token=state["superAdminToken"],
        body={
            "email": email,
            "organization": "MVP Organization",
            "name": "Email Onboarding Member",
            "accountType": "member",
        },
        expected={200},
    )
    message = wait_for_mailpit_message(email)
    action_link = extract_keycloak_action_link(message)
    complete_member_action_email(action_link, password)
    token_response = login_with_authorization_code(email, password, acr_value=NORMAL_ACR)
    _, activated = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/onboarding/activate",
        actor_token=token_response["access_token"],
        body={},
        expected={200},
    )

    assert_equal(activated.get("accountId"), account.get("accountId"), "Email-onboarded account mismatch")
    assert_equal(activated.get("lifecycle"), "active", "Email-onboarded member must become active")
    assert_equal(activated.get("hasLinkedSubject"), True, "Email-onboarded member must have a linked subject")
    evidence.payload(
        "emailOnboarding",
        {
            "account": account,
            "mailpitMessage": summarize_mailpit_message(message),
            "activation": activated,
        },
    )
    evidence.result("E2E-012", "PASS", "Keycloak action email was captured, completed, and activated through IAM onboarding.")


class SkipCase(Exception):
    pass


def require_state(state: dict[str, Any], key: str) -> None:
    if key not in state:
        raise SkipCase(f"Missing prerequisite state: {key}")


def wait_for_runtime() -> None:
    urls = [
        f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration",
        f"{IAM_API_BASE_URL}/healthz",
        f"{DEMO_BASE_URL}/healthz",
    ]
    for url in urls:
        for _ in range(90):
            try:
                with urllib.request.urlopen(url, timeout=2):
                    break
            except OSError:
                time.sleep(2)
        else:
            raise RuntimeError(f"Runtime endpoint is not reachable: {url}")


def login_with_authorization_code(
    username: str,
    password: str,
    *,
    acr_value: str | None = NORMAL_ACR,
    otp_secret: str | None = None,
) -> dict[str, Any]:
    discovery = get_json(f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration")
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    query = {
        'client_id': BACKOFFICE_CLIENT_ID,
        'redirect_uri': BACKOFFICE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
    }
    if acr_value:
        query["claims"] = json.dumps(
            {"id_token": {"acr": {"essential": True, "values": [acr_value]}}},
            separators=(",", ":"),
        )
    auth_url = f"{discovery['authorization_endpoint']}?{urllib.parse.urlencode(query)}"
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()), NoRedirect)
    login_page = opener.open(auth_url, timeout=10).read().decode("utf-8")
    login_form = parse_login_form(login_page, context="initial login page")
    location, body = submit_form(
        opener,
        login_form.action,
        {
            "username": username,
            "password": password,
            "credentialId": "",
            "login": "Sign In",
        },
    )
    if not location.startswith(BACKOFFICE_REDIRECT_URI):
        if otp_secret is None:
            raise RuntimeError("Keycloak requested an extra authentication step but no OTP secret is available")
        body = load_page(opener, location) if location and not body else body
        otp_form = parse_login_form(body, context="OTP challenge page")
        location, body = submit_form(
            opener,
            otp_form.action,
            {
                **otp_form.inputs,
                "otp": totp(otp_secret),
                "credentialId": "",
                "login": "Sign In",
            },
        )
    if not location.startswith(BACKOFFICE_REDIRECT_URI):
        raise RuntimeError(
            "Keycloak login did not redirect with an authorization code; "
            f"url={location}; message={extract_page_text(body)[:250]}; form={extract_form_snippet(body)[:1000]}"
        )
    parsed = urllib.parse.urlparse(location)
    params = urllib.parse.parse_qs(parsed.query)
    if params.get("state", [""])[0] != state:
        raise RuntimeError("Keycloak returned an unexpected OAuth state")
    code = params.get("code", [""])[0]
    if not code:
        raise RuntimeError("Keycloak login did not return an authorization code")
    token_body = post_form(
        discovery["token_endpoint"],
        {
            "grant_type": "authorization_code",
            "client_id": BACKOFFICE_CLIENT_ID,
            "client_secret": BACKOFFICE_CLIENT_SECRET,
            "redirect_uri": BACKOFFICE_REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
    )
    id_claims = decode_claims(token_body["id_token"])
    if id_claims.get("nonce") != nonce:
        raise RuntimeError("Keycloak ID token nonce mismatch")
    if acr_value and id_claims.get("acr") != acr_value:
        raise RuntimeError(f"Keycloak ID token ACR mismatch: expected {acr_value!r}, got {id_claims.get('acr')!r}")
    return token_body


def keycloak_admin_access_token() -> str:
    body = post_form(
        f"{KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token",
        {
            "client_id": "admin-cli",
            "username": KC_BOOTSTRAP_ADMIN_USERNAME,
            "password": KC_BOOTSTRAP_ADMIN_PASSWORD,
            "grant_type": "password",
        },
    )
    token = body.get("access_token")
    if not isinstance(token, str):
        raise RuntimeError("Unable to obtain Keycloak admin token")
    return token


def configure_realm_smtp(admin_token: str) -> None:
    realm = keycloak_api_get(admin_token, "")
    if not isinstance(realm, dict):
        raise RuntimeError("Unexpected Keycloak realm response")
    smtp = {
        **(realm.get("smtpServer") if isinstance(realm.get("smtpServer"), dict) else {}),
        "host": KEYCLOAK_SMTP_HOST,
        "port": str(KEYCLOAK_SMTP_PORT),
        "from": KEYCLOAK_SMTP_FROM,
        "auth": "false",
        "ssl": "false",
        "starttls": "false",
    }
    payload = {**realm, "smtpServer": smtp}
    keycloak_api_json("PUT", admin_token, "", payload, expected={200, 204})


def wait_for_mailpit() -> None:
    for _ in range(30):
        try:
            mailpit_request_json("GET", "/api/v1/messages", expected={200})
            return
        except OSError:
            time.sleep(1)
        except urllib.error.URLError:
            time.sleep(1)
    raise RuntimeError(f"Mailpit API is not reachable at {MAILPIT_API_BASE_URL}")


def clear_mailpit_messages() -> None:
    mailpit_request_json("DELETE", "/api/v1/messages", expected={200, 204})


def wait_for_mailpit_message(email: str) -> dict[str, Any]:
    for _ in range(30):
        messages = mailpit_request_json("GET", "/api/v1/messages", expected={200})
        for summary in _mailpit_message_summaries(messages):
            if email.lower() not in _mailpit_recipients(summary):
                continue
            message_id = _mailpit_message_id(summary)
            if message_id:
                detail = mailpit_request_json("GET", f"/api/v1/message/{urllib.parse.quote(message_id)}", expected={200})
                if isinstance(detail, dict):
                    return detail
            if isinstance(summary, dict):
                return summary
        time.sleep(1)
    raise RuntimeError(f"No Keycloak action email was captured for {email}")


def extract_keycloak_action_link(message: dict[str, Any]) -> str:
    body_parts = []
    for key in ("HTML", "Text", "HTMLBody", "TextBody", "Body"):
        value = message.get(key)
        if isinstance(value, str):
            body_parts.append(value)
    body = "\n".join(body_parts)
    for match in re.findall(r"https?://[^\"'<>\\\s]+", body):
        link = html.unescape(match).rstrip(").,;")
        if "/login-actions/action-token" in link:
            return normalize_keycloak_link(link)
    raise RuntimeError(f"Unable to find Keycloak action-token link in captured email: {summarize_mailpit_message(message)}")


def complete_member_action_email(action_link: str, password: str) -> None:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()), NoRedirect)
    location, body = open_keycloak_url(opener, action_link)
    for _ in range(8):
        if location.startswith(BACKOFFICE_REDIRECT_URI):
            return
        if location and not body:
            location, body = open_keycloak_url(opener, location)
            if location.startswith(BACKOFFICE_REDIRECT_URI):
                return
        if "account updated" in extract_page_text(body).lower():
            return
        try:
            form = parse_login_form(body, context=f"action-email page at {location}: {extract_page_text(body)[:300]}")
        except RuntimeError:
            next_link = extract_first_href(body)
            if not next_link:
                raise
            location, body = open_keycloak_url(opener, next_link)
            continue
        fields = action_email_form_fields(form, password)
        location, body = submit_form(opener, form.action, fields)
    raise RuntimeError(f"Keycloak action-email flow did not finish; last url={location}; text={extract_page_text(body)[:300]}")


def action_email_form_fields(form: LoginFormParser, password: str) -> dict[str, str]:
    fields = dict(form.inputs)
    has_password_field = False
    for name in list(fields):
        lowered = name.lower()
        if "password" in lowered and "confirm" not in lowered:
            fields[name] = password
            has_password_field = True
        if "password" in lowered and "confirm" in lowered:
            fields[name] = password
    if has_password_field:
        fields.setdefault("password-new", password)
        fields.setdefault("password-confirm", password)
    fields.setdefault("submitAction", "Save")
    return fields


def open_keycloak_url(opener: urllib.request.OpenerDirector, url: str) -> tuple[str, str]:
    request = urllib.request.Request(normalize_keycloak_link(url))
    try:
        with opener.open(request, timeout=10) as response:
            return response.geturl(), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in {302, 303}:
            return exc.headers.get("Location", ""), ""
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Keycloak action link returned HTTP {exc.code}: {detail[:500]}") from exc


def normalize_keycloak_link(link: str) -> str:
    if link.startswith("/"):
        return urllib.parse.urljoin(f"{KEYCLOAK_BASE_URL}/", link.lstrip("/"))
    parsed = urllib.parse.urlparse(link)
    if parsed.hostname in {"127.0.0.1", "localhost"}:
        base = urllib.parse.urlparse(KEYCLOAK_BASE_URL)
        parsed = parsed._replace(scheme=base.scheme, netloc=base.netloc)
    return urllib.parse.urlunparse(parsed)


def extract_first_href(page: str) -> str | None:
    for match in re.findall(r"href=[\"']([^\"']+)[\"']", page, flags=re.IGNORECASE):
        link = html.unescape(match)
        if "/login-actions/" in link:
            return normalize_keycloak_link(link)
    return None


def summarize_mailpit_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": message.get("ID") or message.get("Id") or message.get("id"),
        "subject": message.get("Subject") or message.get("subject"),
        "to": _mailpit_recipients(message),
    }


def _mailpit_message_summaries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        return [item for item in payload["messages"] if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("Messages"), list):
        return [item for item in payload["Messages"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _mailpit_message_id(message: dict[str, Any]) -> str | None:
    for key in ("ID", "Id", "id"):
        value = message.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _mailpit_recipients(message: dict[str, Any]) -> list[str]:
    recipients: list[str] = []
    for key in ("To", "to"):
        value = message.get(key)
        if isinstance(value, str):
            recipients.append(value.lower())
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    recipients.append(item.lower())
                if isinstance(item, dict):
                    address = item.get("Address") or item.get("address") or item.get("Email") or item.get("email")
                    if isinstance(address, str):
                        recipients.append(address.lower())
    return recipients


def mailpit_request_json(method: str, path: str, *, expected: set[int]) -> Any:
    request = urllib.request.Request(
        f"{MAILPIT_API_BASE_URL}{path}",
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
        if status not in expected:
            detail = raw.decode("utf-8", errors="replace")
            raise RuntimeError(f"Unexpected Mailpit HTTP {status} for {method} {path}: {detail}") from exc
    if status not in expected:
        raise RuntimeError(f"Unexpected Mailpit HTTP {status} for {method} {path}")
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def ensure_keycloak_user(admin_token: str, username: str, email: str, password: str) -> dict[str, Any]:
    user = find_keycloak_user(admin_token, username)
    email_user = find_keycloak_user_by_email(admin_token, email)
    if user is not None and email_user is not None and user.get("id") != email_user.get("id"):
        raise RuntimeError(f"Keycloak fixture user {username} conflicts with existing email {email}")
    if user is None:
        user = email_user
    payload = {
        "username": username,
        "enabled": True,
        "email": email,
        "emailVerified": True,
        "firstName": "Human",
        "lastName": "E2E",
        "requiredActions": [],
    }
    if user is None:
        keycloak_api_json("POST", admin_token, "users", payload, expected={201, 204})
        user = find_keycloak_user(admin_token, username)
    elif isinstance(user.get("id"), str):
        full = keycloak_api_get(admin_token, f"users/{user['id']}")
        if not isinstance(full, dict):
            raise RuntimeError(f"Unexpected Keycloak user response: {username}")
        merged = dict(full)
        update_payload = dict(payload)
        update_payload["username"] = full.get("username", username)
        merged.update(update_payload)
        keycloak_api_json("PUT", admin_token, f"users/{user['id']}", merged, expected={200, 204})
        refreshed = keycloak_api_get(admin_token, f"users/{user['id']}")
        if isinstance(refreshed, dict):
            user = refreshed
    if user is None or not isinstance(user.get("id"), str):
        raise RuntimeError(f"Unable to resolve Keycloak fixture user: {username}")
    keycloak_api_json(
        "PUT",
        admin_token,
        f"users/{user['id']}/reset-password",
        {"type": "password", "value": password, "temporary": False},
        expected={200, 204},
    )
    if not isinstance(user.get("username"), str):
        raise RuntimeError(f"Keycloak fixture user is missing username: {username}")
    return user


def ensure_totp_credential(admin_token: str, user_id: str, username: str) -> tuple[str, dict[str, Any]]:
    credentials = keycloak_api_get(admin_token, f"users/{user_id}/credentials")
    if not isinstance(credentials, list):
        raise RuntimeError("Unexpected Keycloak credential response")
    for credential in credentials:
        if not isinstance(credential, dict):
            continue
        if credential.get("type") == "otp" and str(credential.get("userLabel", "")).startswith(OTP_LABEL_PREFIX):
            credential_id = credential.get("id")
            if isinstance(credential_id, str):
                keycloak_api_delete(admin_token, f"users/{user_id}/credentials/{credential_id}", expected={204})
    secret = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(20))
    label = f"{OTP_LABEL_PREFIX}-{username}"
    status = keycloak_api_json_status(
        "POST",
        admin_token,
        f"users/{user_id}/credentials",
        totp_credential_payload(label, secret),
        expected={201, 204, 404},
    )
    if status == 404:
        provisioned = ensure_totp_credential_through_user_update(admin_token, user_id, label, secret)
        if provisioned is not None:
            return f"raw:{secret}", provisioned
        return configure_totp_required_action(admin_token, user_id, username)
    created = keycloak_api_get(admin_token, f"users/{user_id}/credentials")
    if not isinstance(created, list):
        raise RuntimeError("Unexpected Keycloak credential verification response")
    matches = [
        {
            "id": credential.get("id"),
            "type": credential.get("type"),
            "userLabel": credential.get("userLabel"),
            "createdDate": credential.get("createdDate"),
        }
        for credential in created
        if isinstance(credential, dict) and credential.get("type") == "otp" and credential.get("userLabel") == label
    ]
    if not matches:
        raise RuntimeError(f"OTP credential was not created for {username}")
    return f"raw:{secret}", matches[0]


def ensure_totp_credential_through_user_update(
    admin_token: str,
    user_id: str,
    label: str,
    secret: str,
) -> dict[str, Any] | None:
    user = keycloak_api_get(admin_token, f"users/{user_id}")
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected Keycloak user response for OTP credential update")
    payload = {**user, "credentials": [totp_credential_payload(label, secret)]}
    keycloak_api_json("PUT", admin_token, f"users/{user_id}", payload, expected={200, 204})
    created = keycloak_api_get(admin_token, f"users/{user_id}/credentials")
    if not isinstance(created, list):
        raise RuntimeError("Unexpected Keycloak credential verification response")
    matches = [
        {
            "id": credential.get("id"),
            "type": credential.get("type"),
            "userLabel": credential.get("userLabel"),
            "createdDate": credential.get("createdDate"),
        }
        for credential in created
        if isinstance(credential, dict) and credential.get("type") == "otp" and credential.get("userLabel") == label
    ]
    return matches[0] if matches else None


def totp_credential_payload(label: str, secret: str) -> dict[str, str]:
    return {
        "type": "otp",
        "userLabel": label,
        "credentialData": json.dumps(
            {
                "subType": "totp",
                "digits": 6,
                "counter": 0,
                "period": 30,
                "algorithm": "HmacSHA1",
            },
            separators=(",", ":"),
        ),
        "secretData": json.dumps({"value": secret}, separators=(",", ":")),
    }


def configure_totp_required_action(admin_token: str, user_id: str, username: str) -> tuple[str, dict[str, Any]]:
    user = keycloak_api_get(admin_token, f"users/{user_id}")
    if not isinstance(user, dict):
        raise RuntimeError(f"Unexpected Keycloak user response for {username}")
    required_actions = list(dict.fromkeys([*_string_list(user.get("requiredActions")), "CONFIGURE_TOTP"]))
    keycloak_api_json("PUT", admin_token, f"users/{user_id}", {**user, "requiredActions": required_actions}, expected={200, 204})

    discovery = get_json(f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration")
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    auth_url = f"{discovery['authorization_endpoint']}?{urllib.parse.urlencode({
        'client_id': BACKOFFICE_CLIENT_ID,
        'redirect_uri': BACKOFFICE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'claims': json.dumps({'id_token': {'acr': {'essential': True, 'values': [NORMAL_ACR]}}}, separators=(',', ':')),
    })}"
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()), NoRedirect)
    login_page = opener.open(auth_url, timeout=10).read().decode("utf-8", errors="replace")
    login_form = parse_login_form(login_page, context="CONFIGURE_TOTP login page")
    location, body = submit_form(
        opener,
        login_form.action,
        {
            "username": username,
            "password": LOCAL_TEST_PASSWORD,
            "credentialId": "",
            "login": "Sign In",
        },
    )
    if location.startswith(BACKOFFICE_REDIRECT_URI):
        raise RuntimeError(f"CONFIGURE_TOTP required action was not shown for {username}")
    body = load_page(opener, location) if location and not body else body
    setup_form = parse_login_form(body, context=f"CONFIGURE_TOTP setup page at {location}: {body[:500]}")
    secret = extract_totp_secret(body)
    if not secret:
        raise RuntimeError(
            f"Unable to extract TOTP secret from CONFIGURE_TOTP page for {username}; "
            f"inputs={sorted(setup_form.inputs.keys())}; form={extract_form_snippet(body)[:1600]}; "
            f"images={extract_image_snippet(body)[:1000]}; "
            f"text={extract_page_text(body)[:400]}"
        )
    setup_fields = dict(setup_form.inputs)
    setup_fields.update(
        {
            "totp": totp(secret),
            "userLabel": f"{OTP_LABEL_PREFIX}-{username}",
            "submitAction": "Save",
        }
    )
    if not setup_fields.get("totpSecret"):
        setup_fields["totpSecret"] = secret
    location, body = submit_form(
        opener,
        setup_form.action,
        setup_fields,
    )
    if not location.startswith(BACKOFFICE_REDIRECT_URI):
        raise RuntimeError(
            f"CONFIGURE_TOTP did not complete for {username}; "
            f"url={location}; inputs={sorted(setup_form.inputs.keys())}; "
            f"message={extract_page_text(body)[:250]}; "
            f"form={extract_form_snippet(body)[:1200]}"
        )

    created = keycloak_api_get(admin_token, f"users/{user_id}/credentials")
    if not isinstance(created, list):
        raise RuntimeError("Unexpected Keycloak credential verification response")
    matches = [
        {
            "id": credential.get("id"),
            "type": credential.get("type"),
            "userLabel": credential.get("userLabel"),
            "createdDate": credential.get("createdDate"),
        }
        for credential in created
        if isinstance(credential, dict)
        and credential.get("type") == "otp"
        and credential.get("userLabel") == f"{OTP_LABEL_PREFIX}-{username}"
    ]
    if not matches:
        raise RuntimeError(f"CONFIGURE_TOTP did not create an OTP credential for {username}")
    return secret, matches[0]


def extract_totp_secret(page: str) -> str | None:
    def normalize(candidate: str | None) -> str | None:
        if not candidate:
            return None
        candidate = html.unescape(candidate).strip()
        candidate = urllib.parse.unquote(candidate)
        if "otpauth://" in candidate and "secret=" in candidate:
            parsed = urllib.parse.urlparse(candidate)
            candidate = urllib.parse.parse_qs(parsed.query).get("secret", [""])[0]
        candidate = "".join(ch for ch in candidate.upper() if ch.isalnum()).rstrip("=")
        if len(candidate) >= 16 and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for ch in candidate):
            return candidate
        return None

    parser = LoginFormParser()
    parser.feed(page)
    for match in re.findall(r"<[^>]*(?:id|class)=[\"'][^\"']*kc-totp-secret-key[^\"']*[\"'][^>]*>(.*?)</[^>]+>", page, re.IGNORECASE | re.DOTALL):
        value = normalize(re.sub(r"<[^>]+>", " ", match))
        if value:
            return value
    for match in re.findall(r"otpauth://[^\"'<> ]+", page):
        value = normalize(match)
        if value:
            return value
    for match in re.findall(r"(?:secret|totpSecret)=([^&\"'<> ]+)", page, re.IGNORECASE):
        value = normalize(match)
        if value:
            return value
    for name in ("totpSecret", "secret"):
        value = normalize(parser.inputs.get(name))
        if value:
            return value
    for name in ("totpSecret", "secret"):
        value = parser.inputs.get(name)
        if value:
            return html.unescape(value).strip()
    return None


def redact_totp_page(page: str) -> str:
    redacted = re.sub(r"otpauth://[^\"'<> ]+", "otpauth://<redacted>", page)
    redacted = re.sub(r"([?&]secret=)[A-Z2-7=]+", r"\1<redacted>", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r'(name=["\']totpSecret["\'][^>]*value=["\'])[^"\']+', r"\1<redacted>", redacted)
    redacted = re.sub(r'(id=["\']kc-totp-secret-key["\'][^>]*>)[^<]+', r"\1<redacted>", redacted)
    return " ".join(redacted.split())


def extract_page_text(page: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", page, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())


def extract_form_snippet(page: str) -> str:
    redacted = redact_totp_page(page)
    index = redacted.find("<form")
    if index < 0:
        return redacted[:1200]
    end = redacted.find("</form>", index)
    if end < 0:
        return redacted[index : index + 1200]
    return redacted[index : end + len("</form>")]


def extract_image_snippet(page: str) -> str:
    redacted = redact_totp_page(page)
    images = re.findall(r"<img\b[^>]+>", redacted, flags=re.IGNORECASE)
    return " ".join(images)


def find_keycloak_user(admin_token: str, username: str) -> dict[str, Any] | None:
    users = keycloak_api_get(admin_token, f"users?username={urllib.parse.quote(username)}")
    if not isinstance(users, list):
        raise RuntimeError("Unexpected Keycloak user search response")
    matches = [user for user in users if isinstance(user, dict) and user.get("username") == username]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple Keycloak users match username: {username}")
    return matches[0] if matches else None


def find_keycloak_user_by_email(admin_token: str, email: str) -> dict[str, Any] | None:
    users = keycloak_api_get(admin_token, f"users?email={urllib.parse.quote(email)}")
    if not isinstance(users, list):
        raise RuntimeError("Unexpected Keycloak email search response")
    matches = [user for user in users if isinstance(user, dict) and str(user.get("email", "")).lower() == email.lower()]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple Keycloak users match email: {email}")
    return matches[0] if matches else None


def keycloak_logout(id_token: str) -> dict[str, Any]:
    discovery = get_json(f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration")
    endpoint = discovery.get("end_session_endpoint")
    if not isinstance(endpoint, str):
        return {"status": "skipped", "reason": "missing_end_session_endpoint"}
    url = f"{endpoint}?{urllib.parse.urlencode({'id_token_hint': id_token})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return {"status": response.status}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code}


def keycloak_api_get(admin_token: str, path: str) -> Any:
    request = urllib.request.Request(
        keycloak_admin_url(path),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def keycloak_api_json(method: str, admin_token: str, path: str, body: Any, *, expected: set[int]) -> None:
    keycloak_api_json_status(method, admin_token, path, body, expected=expected)


def keycloak_api_json_status(method: str, admin_token: str, path: str, body: Any, *, expected: set[int]) -> int:
    request = urllib.request.Request(
        keycloak_admin_url(path),
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        method=method,
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        detail = exc.read().decode("utf-8")
        if status not in expected:
            raise RuntimeError(f"Unexpected Keycloak HTTP {status} for {method} {path}: {detail}") from exc
    if status not in expected:
        raise RuntimeError(f"Unexpected Keycloak HTTP {status} for {method} {path}")
    return status


def keycloak_api_delete(admin_token: str, path: str, *, expected: set[int]) -> None:
    request = urllib.request.Request(
        keycloak_admin_url(path),
        method="DELETE",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        detail = exc.read().decode("utf-8")
        if status not in expected:
            raise RuntimeError(f"Unexpected Keycloak HTTP {status} for DELETE {path}: {detail}") from exc
    if status not in expected:
        raise RuntimeError(f"Unexpected Keycloak HTTP {status} for DELETE {path}")


def keycloak_admin_url(path: str) -> str:
    base = f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}"
    stripped = path.strip("/")
    return f"{base}/{stripped}" if stripped else base


def request_json(
    method: str,
    url: str,
    *,
    actor_token: str | None = None,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    expected: set[int],
) -> tuple[int, dict[str, Any]]:
    request_headers = dict(headers or {})
    if actor_token:
        request_headers["Authorization"] = f"Bearer {actor_token}"
    data = None
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = parse_json_body(response.read())
            status = response.status
    except urllib.error.HTTPError as exc:
        payload = parse_json_body(exc.read())
        status = exc.code
    if status not in expected:
        raise RuntimeError(f"Unexpected HTTP {status} for {method} {url}: {payload}")
    return status, payload


def request_json_with_retry(
    method: str,
    url: str,
    *,
    actor_token: str | None = None,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    expected: set[int],
    attempts: int = 3,
) -> tuple[int, dict[str, Any]]:
    last_error: RuntimeError | None = None
    for attempt in range(attempts):
        try:
            status, payload = request_json(
                method,
                url,
                actor_token=actor_token,
                headers=headers,
                body=body,
                expected=expected | {503},
            )
            if status in expected:
                return status, payload
            last_error = RuntimeError(f"Transient HTTP {status} for {method} {url}: {payload}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(1)
    if last_error:
        raise last_error
    raise RuntimeError(f"Request retry failed unexpectedly for {method} {url}")


def parse_json_body(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {}
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Expected JSON object response")
    return payload


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected JSON body from {url}")
    return payload


def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(form).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected token response from {url}")
    return payload


def parse_login_form(page: str, *, context: str = "Keycloak page") -> LoginFormParser:
    parser = LoginFormParser()
    parser.feed(page)
    if not parser.action:
        raise RuntimeError(f"Unable to find Keycloak login form action on {context}")
    return parser


def submit_form(opener: urllib.request.OpenerDirector, action: str, fields: dict[str, str]) -> tuple[str, str]:
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with opener.open(request, timeout=10) as response:
            return response.geturl(), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in {302, 303}:
            return exc.headers.get("Location", ""), ""
        if exc.code >= 400:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Keycloak form POST returned HTTP {exc.code}: {detail[:500]}") from exc
        return exc.geturl(), exc.read().decode("utf-8", errors="replace")


def load_page(opener: urllib.request.OpenerDirector, url: str) -> str:
    with opener.open(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def decode_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise RuntimeError("Token does not have three JWT parts")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    body = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError("Token payload is not a JSON object")
    return body


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{message}: expected {expected!r}, got {actual!r}")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def totp(secret: str, for_time: int | None = None) -> str:
    timestamp = int(time.time() if for_time is None else for_time)
    counter = timestamp // 30
    key = totp_key(secret)
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return f"{code % 1_000_000:06d}"


def totp_key(secret: str) -> bytes:
    if secret.startswith("raw:"):
        return secret.removeprefix("raw:").encode("utf-8")
    normalized = "".join(ch for ch in secret.upper() if ch.isalnum()).rstrip("=")
    if len(normalized) >= 16 and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for ch in normalized):
        return base64.b32decode(normalized + "=" * (-len(normalized) % 8))
    compact = "".join(ch for ch in secret.strip() if not ch.isspace())
    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            return decoder(compact + "=" * (-len(compact) % 4))
        except (ValueError, TypeError):
            continue
    return secret.encode("utf-8")


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("<redacted>" if sensitive_key(key) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and value.count(".") == 2 and len(value) > 80:
        return "<redacted-jwt>"
    return value


def mask(message: str) -> str:
    masked = message
    for secret in (
        KC_BOOTSTRAP_ADMIN_PASSWORD,
        BACKOFFICE_CLIENT_SECRET,
        SUPER_ADMIN_PASSWORD,
        LOCAL_TEST_PASSWORD,
    ):
        if secret:
            masked = masked.replace(secret, "<redacted>")
    return masked


def sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in ("token", "secret", "password", "authorization", "logouturl"))


if __name__ == "__main__":
    main()
