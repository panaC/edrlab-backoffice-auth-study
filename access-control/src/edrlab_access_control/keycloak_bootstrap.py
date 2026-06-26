from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import DEFAULT_SERVICE_ID


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


KEYCLOAK_BASE_URL = env("KEYCLOAK_BASE_URL", "http://keycloak:8080").rstrip("/")
KEYCLOAK_REALM = env("KEYCLOAK_REALM", "edrlab-backoffice-mvp")
KC_BOOTSTRAP_ADMIN_USERNAME = env("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
KC_BOOTSTRAP_ADMIN_PASSWORD = env("KC_BOOTSTRAP_ADMIN_PASSWORD", "change-me-admin-password")
BACKOFFICE_CLIENT_ID = env("KEYCLOAK_BACKOFFICE_CLIENT_ID", "edrlab-backoffice")
BACKOFFICE_CLIENT_SECRET = env("KEYCLOAK_BACKOFFICE_CLIENT_SECRET", "change-me-backoffice-secret")
SERVICE_CLIENT_ID = env("KEYCLOAK_SERVICE_CLIENT_ID", DEFAULT_SERVICE_ID)
SERVICE_CLIENT_SECRET = env("KEYCLOAK_SERVICE_CLIENT_SECRET", "change-me-demo-service-secret")
SUPER_ADMIN_USERNAME = env("KEYCLOAK_SUPER_ADMIN_USERNAME", "mvp-super-admin")
SUPER_ADMIN_EMAIL = env("BOOTSTRAP_SUPER_ADMIN_EMAIL", "super-admin@example.test")
SUPER_ADMIN_PASSWORD = env("KEYCLOAK_SUPER_ADMIN_PASSWORD", "change-me-super-admin-password")
KEYCLOAK_BOOTSTRAP_OUTPUT = os.environ.get("KEYCLOAK_BOOTSTRAP_OUTPUT")
SMOKE_USERNAME = env("KEYCLOAK_SMOKE_USERNAME", "mvp-member")
SMOKE_EMAIL = env("KEYCLOAK_SMOKE_EMAIL", "mvp-member@example.test")
SMOKE_PASSWORD = env("KEYCLOAK_SMOKE_PASSWORD", "change-me-member-password")
BACKOFFICE_REDIRECT_URI = env("KEYCLOAK_BACKOFFICE_REDIRECT_URI", "http://localhost:9999/callback")


def main() -> None:
    wait_for_keycloak()
    token = admin_token()
    ensure_realm(token)
    backoffice_uuid = ensure_client(token, backoffice_client_payload())
    ensure_client(token, service_client_payload())
    ensure_audience_mapper(token, backoffice_uuid)
    super_admin = ensure_user(token, SUPER_ADMIN_USERNAME, SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD, "Initial", "Super Admin")
    ensure_user(token, SMOKE_USERNAME, SMOKE_EMAIL, SMOKE_PASSWORD, "MVP", "Member")
    write_bootstrap_output(super_admin)
    print(
        json.dumps(
            {
                "status": "ok",
                "realm": KEYCLOAK_REALM,
                "superAdminSubject": super_admin["id"],
                "superAdminUser": SUPER_ADMIN_USERNAME,
                "smokeUser": SMOKE_USERNAME,
            },
            sort_keys=True,
        )
    )


def wait_for_keycloak() -> None:
    url = f"{KEYCLOAK_BASE_URL}/realms/master/.well-known/openid-configuration"
    for _ in range(90):
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except OSError:
            time.sleep(2)
    raise RuntimeError(f"Keycloak is not reachable at {url}")


def admin_token() -> str:
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


def ensure_realm(token: str) -> None:
    payload = {
        "realm": KEYCLOAK_REALM,
        "enabled": True,
        "displayName": "EDRLab Backoffice MVP",
        "eventsEnabled": True,
        "eventsExpiration": 3600,
        "enabledEventTypes": ["LOGIN", "LOGIN_ERROR", "LOGOUT", "CODE_TO_TOKEN", "CLIENT_LOGIN"],
        "adminEventsEnabled": True,
        "adminEventsDetailsEnabled": True,
    }
    if api_get(token, f"realms/{KEYCLOAK_REALM}", ok_missing=True) is None:
        api_json("POST", token, "realms", payload, expected={201, 204})
    else:
        api_json("PUT", token, f"realms/{KEYCLOAK_REALM}", payload, expected={200, 204})


def backoffice_client_payload() -> dict[str, Any]:
    return {
        "clientId": BACKOFFICE_CLIENT_ID,
        "name": "EDRLab Backoffice MVP",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "clientAuthenticatorType": "client-secret",
        "secret": BACKOFFICE_CLIENT_SECRET,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
        "bearerOnly": False,
        "consentRequired": False,
        "redirectUris": [BACKOFFICE_REDIRECT_URI],
        "webOrigins": ["+"],
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": BACKOFFICE_REDIRECT_URI,
        },
    }


def service_client_payload() -> dict[str, Any]:
    return {
        "clientId": SERVICE_CLIENT_ID,
        "name": "Access Check Demo Service",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "clientAuthenticatorType": "client-secret",
        "secret": SERVICE_CLIENT_SECRET,
        "standardFlowEnabled": False,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": True,
        "bearerOnly": False,
        "consentRequired": False,
    }


def ensure_client(token: str, payload: dict[str, Any]) -> str:
    client_id = payload["clientId"]
    existing = find_client(token, client_id)
    if existing is None:
        api_json("POST", token, f"realms/{KEYCLOAK_REALM}/clients", payload, expected={201, 204})
        existing = find_client(token, client_id)
    else:
        api_json("PUT", token, f"realms/{KEYCLOAK_REALM}/clients/{existing['id']}", payload, expected={200, 204})
    if not existing or not isinstance(existing.get("id"), str):
        raise RuntimeError(f"Unable to resolve Keycloak client: {client_id}")
    return existing["id"]


def ensure_audience_mapper(token: str, backoffice_uuid: str) -> None:
    mapper = {
        "name": f"audience-{SERVICE_CLIENT_ID}",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-audience-mapper",
        "consentRequired": False,
        "config": {
            "included.client.audience": SERVICE_CLIENT_ID,
            "id.token.claim": "false",
            "access.token.claim": "true",
        },
    }
    path = f"realms/{KEYCLOAK_REALM}/clients/{backoffice_uuid}/protocol-mappers/models"
    existing = api_get(token, path)
    if not isinstance(existing, list):
        raise RuntimeError("Unexpected protocol mapper response")
    match = next((item for item in existing if item.get("name") == mapper["name"]), None)
    if match and isinstance(match.get("id"), str):
        api_json("PUT", token, f"{path}/{match['id']}", {**mapper, "id": match["id"]}, expected={200, 204})
    else:
        api_json("POST", token, path, mapper, expected={201, 204})


def ensure_user(
    token: str,
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> dict[str, Any]:
    payload = {
        "username": username,
        "enabled": True,
        "email": email,
        "emailVerified": True,
        "firstName": first_name,
        "lastName": last_name,
        "requiredActions": [],
    }
    user = find_user(token, username)
    if user is None:
        api_json("POST", token, f"realms/{KEYCLOAK_REALM}/users", payload, expected={201, 204})
        user = find_user(token, username)
    else:
        api_json("PUT", token, f"realms/{KEYCLOAK_REALM}/users/{user['id']}", payload, expected={200, 204})
    if not user or not isinstance(user.get("id"), str):
        raise RuntimeError(f"Unable to resolve Keycloak user: {username}")
    api_json(
        "PUT",
        token,
        f"realms/{KEYCLOAK_REALM}/users/{user['id']}/reset-password",
        {"type": "password", "value": password, "temporary": False},
        expected={200, 204},
    )
    return user


def write_bootstrap_output(super_admin: dict[str, Any]) -> None:
    if not KEYCLOAK_BOOTSTRAP_OUTPUT:
        return
    path = Path(KEYCLOAK_BOOTSTRAP_OUTPUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"superAdminSubject": super_admin["id"]}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def find_client(token: str, client_id: str) -> dict[str, Any] | None:
    encoded = urllib.parse.quote(client_id)
    response = api_get(token, f"realms/{KEYCLOAK_REALM}/clients?clientId={encoded}")
    if isinstance(response, list) and response:
        return response[0]
    return None


def find_user(token: str, username: str) -> dict[str, Any] | None:
    encoded = urllib.parse.quote(username)
    response = api_get(token, f"realms/{KEYCLOAK_REALM}/users?username={encoded}&exact=true")
    if isinstance(response, list) and response:
        return response[0]
    return None


def api_get(token: str, path: str, *, ok_missing: bool = False) -> Any:
    request = urllib.request.Request(
        f"{KEYCLOAK_BASE_URL}/admin/{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 204:
                return {}
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if ok_missing and exc.code == 404:
            return None
        raise


def api_json(method: str, token: str, path: str, payload: dict[str, Any], *, expected: set[int]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{KEYCLOAK_BASE_URL}/admin/{path}",
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status not in expected:
                raise RuntimeError(f"Unexpected Keycloak status {response.status} for {method} {path}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Unexpected Keycloak status {exc.code} for {method} {path}: {detail}") from exc


def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
