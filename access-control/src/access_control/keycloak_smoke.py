from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

from .config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID


KEYCLOAK_BASE_URL = os.environ.get("KEYCLOAK_BASE_URL", "http://keycloak:8080").rstrip("/")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "access-control-mvp")
BACKOFFICE_CLIENT_ID = os.environ.get("KEYCLOAK_BACKOFFICE_CLIENT_ID", "backoffice")
BACKOFFICE_CLIENT_SECRET = os.environ.get("KEYCLOAK_BACKOFFICE_CLIENT_SECRET", "change-me-backoffice-secret")
BACKOFFICE_REDIRECT_URI = os.environ.get("KEYCLOAK_BACKOFFICE_REDIRECT_URI", "http://localhost:9999/callback")
KC_BOOTSTRAP_ADMIN_USERNAME = os.environ.get("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
KC_BOOTSTRAP_ADMIN_PASSWORD = os.environ.get("KC_BOOTSTRAP_ADMIN_PASSWORD", "change-me-admin-password")
SERVICE_CLIENT_ID = os.environ.get("KEYCLOAK_SERVICE_CLIENT_ID", DEFAULT_SERVICE_ID)
SUPER_ADMIN_USERNAME = os.environ.get("KEYCLOAK_SUPER_ADMIN_USERNAME", "mvp-super-admin")
SUPER_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_SUPER_ADMIN_PASSWORD", "change-me-super-admin-password")
SMOKE_USERNAME = os.environ.get("KEYCLOAK_SMOKE_USERNAME", "mvp-member")
SMOKE_PASSWORD = os.environ.get("KEYCLOAK_SMOKE_PASSWORD", "change-me-member-password")
SMOKE_EMAIL = os.environ.get("KEYCLOAK_SMOKE_EMAIL", "mvp-member@example.test")
IAM_API_BASE_URL = os.environ.get("IAM_API_BASE_URL", "http://iam-api:8000").rstrip("/")
DEMO_BASE_URL = os.environ.get("DEMO_BASE_URL", "http://access-check-demo-service:8001").rstrip("/")
BOOTSTRAP_SUPER_ADMIN_SUBJECT = os.environ.get("BOOTSTRAP_SUPER_ADMIN_SUBJECT", "bootstrap-super-admin-subject")
KEYCLOAK_BOOTSTRAP_OUTPUT = os.environ.get("KEYCLOAK_BOOTSTRAP_OUTPUT")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def main() -> None:
    wait_for_runtime()
    admin_token_response = login_with_authorization_code(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD)
    keycloak_admin_token = keycloak_admin_access_token()
    remove_direct_service_role_mapping(keycloak_admin_token, SMOKE_USERNAME)
    admin_id_claims = decode_claims(admin_token_response["id_token"])
    admin_subject = required_claim(admin_id_claims, "sub")
    if admin_subject != expected_bootstrap_super_admin_subject():
        raise RuntimeError("Keycloak super-admin subject does not match the bootstrapped IAM account subject")

    token_response = login_with_authorization_code(SMOKE_USERNAME, SMOKE_PASSWORD)
    id_claims = decode_claims(token_response["id_token"])
    subject = required_claim(id_claims, "sub")
    email = required_claim(id_claims, "email")
    if email.lower() != SMOKE_EMAIL.lower() or id_claims.get("email_verified") is not True:
        raise RuntimeError("Keycloak token did not carry the expected verified smoke-test email")
    account = ensure_local_member_account(
        subject,
        email,
        admin_token_response["access_token"],
        token_response["access_token"],
    )
    stale_token_response = issue_token_with_stale_service_role_claim(keycloak_admin_token)
    stale_access_token = stale_token_response["access_token"]
    stale_access_token_claims = decode_claims(stale_access_token)
    if not has_demo_service_role_claim(stale_access_token_claims):
        raise RuntimeError("Keycloak access token did not carry the expected stale demo service-role claim")
    request_json(
        "PUT",
        f"{IAM_API_BASE_URL}/iam/accounts/{account['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=admin_token_response["access_token"],
        expected={200},
    )
    demo_status, demo_body = request_json(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": f"Bearer {stale_access_token}"},
        expected={200},
    )
    request_json(
        "DELETE",
        f"{IAM_API_BASE_URL}/iam/accounts/{account['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=admin_token_response["access_token"],
        expected={200},
    )
    try:
        stale_denied_status, stale_denied_body = request_json(
            "GET",
            f"{DEMO_BASE_URL}/access-check-demo",
            headers={"Authorization": f"Bearer {stale_access_token}"},
            expected={403},
        )
        if stale_denied_body.get("authorized") is not False or stale_denied_body.get("result") != "KO":
            raise RuntimeError(f"Stale service-role claim returned unexpected denial body: {stale_denied_body}")
    finally:
        request_json(
            "PUT",
            f"{IAM_API_BASE_URL}/iam/accounts/{account['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
            actor_token=admin_token_response["access_token"],
            expected={200},
        )
    bad_status, bad_body = request_json(
        "GET",
        f"{DEMO_BASE_URL}/access-check-demo",
        headers={"Authorization": "Bearer not-a-valid-token"},
        expected={401},
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "keycloakSubject": subject,
                "accountId": account["accountId"],
                "authorizedDemoStatus": demo_status,
                "authorizedDemoBody": demo_body,
                "staleTokenHadServiceRoleClaim": True,
                "staleTokenAfterRoleRemovalStatus": stale_denied_status,
                "staleTokenAfterRoleRemovalBody": stale_denied_body,
                "invalidTokenStatus": bad_status,
                "invalidTokenBody": bad_body,
            },
            sort_keys=True,
        )
    )


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


def expected_bootstrap_super_admin_subject() -> str:
    if KEYCLOAK_BOOTSTRAP_OUTPUT:
        path = Path(KEYCLOAK_BOOTSTRAP_OUTPUT)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("superAdminSubject"), str):
                return payload["superAdminSubject"]
    return BOOTSTRAP_SUPER_ADMIN_SUBJECT


def login_with_authorization_code(username: str, password: str) -> dict[str, Any]:
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
    })}"
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()), NoRedirect)
    login_page = opener.open(auth_url, timeout=10).read().decode("utf-8")
    login_action = parse_login_action(login_page)
    form = urllib.parse.urlencode({"username": username, "password": password, "credentialId": ""}).encode("utf-8")
    request = urllib.request.Request(
        login_action,
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        opener.open(request, timeout=10)
    except urllib.error.HTTPError as exc:
        if exc.code not in {302, 303}:
            raise
        location = exc.headers.get("Location", "")
    else:
        raise RuntimeError("Keycloak login did not redirect with an authorization code")
    parsed = urllib.parse.urlparse(location)
    params = urllib.parse.parse_qs(parsed.query)
    if params.get("state", [""])[0] != state:
        returned_state = params.get("state", [""])[0]
        raise RuntimeError(f"Keycloak returned an unexpected OAuth state: {returned_state!r} in {location}")
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
    if not isinstance(token_body.get("access_token"), str) or not isinstance(token_body.get("id_token"), str):
        raise RuntimeError("Keycloak token response is missing expected tokens")
    id_claims = decode_claims(token_body["id_token"])
    if id_claims.get("nonce") != nonce:
        raise RuntimeError("Keycloak ID token nonce mismatch")
    return token_body


def issue_token_with_stale_service_role_claim(keycloak_admin_token: str) -> dict[str, Any]:
    add_direct_service_role_mapping(keycloak_admin_token, SMOKE_USERNAME)
    try:
        token_response = login_with_authorization_code(SMOKE_USERNAME, SMOKE_PASSWORD)
    finally:
        remove_direct_service_role_mapping(keycloak_admin_token, SMOKE_USERNAME)
    return token_response


def has_demo_service_role_claim(claims: dict[str, Any]) -> bool:
    resource_access = claims.get("resource_access")
    if not isinstance(resource_access, dict):
        return False
    service_access = resource_access.get(SERVICE_CLIENT_ID)
    if not isinstance(service_access, dict):
        return False
    roles = service_access.get("roles")
    return isinstance(roles, list) and service_role_name() in roles


def service_role_name() -> str:
    prefix = f"{SERVICE_CLIENT_ID}:"
    if DEFAULT_SERVICE_ROLE_ID.startswith(prefix):
        return DEFAULT_SERVICE_ROLE_ID.removeprefix(prefix)
    return DEFAULT_SERVICE_ROLE_ID.rsplit(":", 1)[-1]


def ensure_local_member_account(
    subject: str,
    email: str,
    admin_access_token: str,
    user_access_token: str,
) -> dict[str, Any]:
    account = find_account_by_email(email, admin_access_token)
    if account is None:
        _, account = request_json(
            "POST",
            f"{IAM_API_BASE_URL}/iam/accounts",
            actor_token=admin_access_token,
            body={"email": email, "organization": "MVP Organization", "name": "MVP Member", "accountType": "member"},
            expected={200},
        )
    request_json(
        "PUT",
        f"{IAM_API_BASE_URL}/iam/accounts/{account['accountId']}/service-roles/{DEFAULT_SERVICE_ROLE_ID}",
        actor_token=admin_access_token,
        expected={200},
    )
    _, activated = request_json(
        "POST",
        f"{IAM_API_BASE_URL}/iam/onboarding/activate",
        actor_token=user_access_token,
        body={},
        expected={200},
    )
    return activated


def find_account_by_email(email: str, admin_access_token: str) -> dict[str, Any] | None:
    _, response = request_json("GET", f"{IAM_API_BASE_URL}/iam/accounts", actor_token=admin_access_token, expected={200})
    for account in response.get("accounts", []):
        if isinstance(account, dict) and str(account.get("email", "")).lower() == email.lower():
            return account
    return None


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
    if not isinstance(token, str) or not token:
        raise RuntimeError("Unable to obtain Keycloak admin token")
    return token


def add_direct_service_role_mapping(admin_token: str, username: str) -> None:
    change_direct_service_role_mapping("POST", admin_token, username)


def remove_direct_service_role_mapping(admin_token: str, username: str) -> None:
    change_direct_service_role_mapping("DELETE", admin_token, username)


def change_direct_service_role_mapping(method: str, admin_token: str, username: str) -> None:
    user = find_keycloak_user(admin_token, username)
    service_client = find_keycloak_client(admin_token, SERVICE_CLIENT_ID)
    role = keycloak_api_get(
        admin_token,
        f"clients/{service_client['id']}/roles/{urllib.parse.quote(service_role_name())}",
    )
    if not isinstance(role, dict):
        raise RuntimeError("Unexpected Keycloak service-role response")
    keycloak_api_json(
        method,
        admin_token,
        f"users/{user['id']}/role-mappings/clients/{service_client['id']}",
        [role],
        expected={200, 204},
    )


def find_keycloak_user(admin_token: str, username: str) -> dict[str, Any]:
    users = keycloak_api_get(admin_token, f"users?username={urllib.parse.quote(username)}")
    if not isinstance(users, list):
        raise RuntimeError("Unexpected Keycloak users response")
    matches = [user for user in users if isinstance(user, dict) and user.get("username") == username]
    if len(matches) != 1 or not isinstance(matches[0].get("id"), str):
        raise RuntimeError(f"Unable to resolve Keycloak user: {username}")
    return matches[0]


def find_keycloak_client(admin_token: str, client_id: str) -> dict[str, Any]:
    clients = keycloak_api_get(admin_token, f"clients?clientId={urllib.parse.quote(client_id)}")
    if not isinstance(clients, list):
        raise RuntimeError("Unexpected Keycloak clients response")
    matches = [client for client in clients if isinstance(client, dict) and client.get("clientId") == client_id]
    if len(matches) != 1 or not isinstance(matches[0].get("id"), str):
        raise RuntimeError(f"Unable to resolve Keycloak client: {client_id}")
    return matches[0]


def keycloak_api_get(admin_token: str, path: str) -> Any:
    request = urllib.request.Request(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/{path}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def keycloak_api_json(
    method: str,
    admin_token: str,
    path: str,
    body: Any,
    *,
    expected: set[int],
) -> None:
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/{path}",
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        error_body = exc.read().decode("utf-8")
        if status not in expected:
            raise RuntimeError(f"Unexpected Keycloak HTTP status {status} for {method} {path}: {error_body}") from exc
    if status not in expected:
        raise RuntimeError(f"Unexpected Keycloak HTTP status {status} for {method} {path}")


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
    data = None
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if actor_token:
        request_headers["Authorization"] = f"Bearer {actor_token}"
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        status = exc.code
    if status not in expected:
        raise RuntimeError(f"Unexpected HTTP status {status} for {method} {url}: {payload}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected JSON body for {method} {url}")
    return status, payload


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected JSON body from {url}")
    return body


def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected token response from {url}")
    return body


def parse_login_action(page: str) -> str:
    match = re.search(r'action="([^"]+)"', page)
    if not match:
        raise RuntimeError("Unable to find Keycloak login form action")
    return html.unescape(match.group(1))


def decode_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise RuntimeError("Token does not have three JWT parts")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    body = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError("Token payload is not a JSON object")
    return body


def required_claim(claims: dict[str, Any], name: str) -> str:
    value = claims.get(name)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Token is missing required claim: {name}")
    return value


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


if __name__ == "__main__":
    main()
