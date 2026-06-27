from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID


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
CONTROL_PLANE_CLIENT_ID = env("KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_ID", "edrlab-iam-control-plane")
CONTROL_PLANE_CLIENT_SECRET = env("KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_SECRET", "change-me-iam-control-plane-secret")
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
    ensure_user_profile(token)
    backoffice_uuid = ensure_client(token, backoffice_client_payload())
    service_uuid = ensure_client(token, service_client_payload())
    control_plane_uuid = ensure_client(token, control_plane_client_payload())
    ensure_control_plane_admin_roles(token, control_plane_uuid)
    ensure_account_type_roles(token, backoffice_uuid)
    ensure_service_role(token, service_uuid, "consult", "Initial MVP access-check demo consultation role.")
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


def ensure_user_profile(token: str) -> None:
    profile = api_get(token, f"realms/{KEYCLOAK_REALM}/users/profile")
    if not isinstance(profile, dict):
        raise RuntimeError("Unexpected Keycloak user-profile response")
    attributes = profile.get("attributes")
    if not isinstance(attributes, list):
        attributes = []
    by_name = {attribute.get("name"): attribute for attribute in attributes if isinstance(attribute, dict)}
    for attribute_name in (
        "edrlab.account_id",
        "edrlab.lifecycle",
        "edrlab.linked_subject",
        "edrlab.organization",
        "edrlab.schema_version",
        "edrlab.last_control_plane_mutation_at",
    ):
        definition = by_name.get(attribute_name)
        if definition is None:
            definition = {"name": attribute_name}
            attributes.append(definition)
        definition.update(
            {
                "displayName": attribute_name,
                "multivalued": False,
                "permissions": {"view": ["admin"], "edit": ["admin"]},
            }
        )
    profile["attributes"] = attributes
    api_json("PUT", token, f"realms/{KEYCLOAK_REALM}/users/profile", profile, expected={200})


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


def control_plane_client_payload() -> dict[str, Any]:
    return {
        "clientId": CONTROL_PLANE_CLIENT_ID,
        "name": "EDRLab IAM Control Plane API",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "clientAuthenticatorType": "client-secret",
        "secret": CONTROL_PLANE_CLIENT_SECRET,
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


def ensure_control_plane_admin_roles(token: str, control_plane_uuid: str) -> None:
    service_account = api_get(token, f"realms/{KEYCLOAK_REALM}/clients/{control_plane_uuid}/service-account-user")
    if not isinstance(service_account, dict) or not isinstance(service_account.get("id"), str):
        raise RuntimeError("Unable to resolve IAM Control Plane service account")
    realm_management = find_client(token, "realm-management")
    if not realm_management or not isinstance(realm_management.get("id"), str):
        raise RuntimeError("Unable to resolve realm-management client")
    realm_management_uuid = realm_management["id"]
    needed = {"manage-users", "view-users", "query-users", "manage-clients", "view-clients"}
    available = api_get(token, f"realms/{KEYCLOAK_REALM}/clients/{realm_management_uuid}/roles")
    if not isinstance(available, list):
        raise RuntimeError("Unexpected realm-management role response")
    roles_by_name = {role.get("name"): role for role in available if isinstance(role, dict)}
    missing = needed - set(roles_by_name)
    if missing:
        raise RuntimeError(f"Missing expected realm-management roles: {sorted(missing)}")
    assigned = api_get(
        token,
        f"realms/{KEYCLOAK_REALM}/users/{service_account['id']}/role-mappings/clients/{realm_management_uuid}",
    )
    if not isinstance(assigned, list):
        raise RuntimeError("Unexpected service-account role mapping response")
    assigned_names = {role.get("name") for role in assigned if isinstance(role, dict)}
    to_add = [roles_by_name[name] for name in sorted(needed - assigned_names)]
    if to_add:
        api_json(
            "POST",
            token,
            f"realms/{KEYCLOAK_REALM}/users/{service_account['id']}/role-mappings/clients/{realm_management_uuid}",
            to_add,
            expected={200, 204},
        )


def ensure_account_type_roles(token: str, backoffice_uuid: str) -> None:
    ensure_client_role(token, backoffice_uuid, "account-type-member", "EDRLab member account type.", {"edrlab.schema_version": ["iam-schema-v1"]})
    ensure_client_role(token, backoffice_uuid, "account-type-admin", "EDRLab admin account type.", {"edrlab.schema_version": ["iam-schema-v1"]})
    ensure_client_role(token, backoffice_uuid, "account-type-super-admin", "EDRLab super-admin account type.", {"edrlab.schema_version": ["iam-schema-v1"]})


def ensure_service_role(token: str, service_uuid: str, role_name: str, description: str) -> None:
    ensure_client_role(
        token,
        service_uuid,
        role_name,
        description,
        {
            "edrlab.role_id": [DEFAULT_SERVICE_ROLE_ID],
            "edrlab.role_status": ["active"],
            "edrlab.schema_version": ["iam-schema-v1"],
        },
    )


def ensure_client_role(
    token: str,
    client_uuid: str,
    role_name: str,
    description: str,
    attributes: dict[str, list[str]],
) -> None:
    encoded_role = urllib.parse.quote(role_name)
    path = f"realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{encoded_role}"
    existing = api_get(token, path, ok_missing=True)
    payload = {
        "name": role_name,
        "description": description,
        "clientRole": True,
        "attributes": attributes,
    }
    if existing is None:
        api_json("POST", token, f"realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles", payload, expected={201, 204})
        return
    if not isinstance(existing, dict):
        raise RuntimeError("Unexpected client-role response")
    merged_attributes = dict(existing.get("attributes") if isinstance(existing.get("attributes"), dict) else {})
    merged_attributes.update(attributes)
    api_json(
        "PUT",
        token,
        path,
        {**existing, "description": description, "attributes": merged_attributes},
        expected={200, 204},
    )


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
        full_user = api_get(token, f"realms/{KEYCLOAK_REALM}/users/{user['id']}")
        if isinstance(full_user, dict) and isinstance(full_user.get("attributes"), dict):
            payload["attributes"] = full_user["attributes"]
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


def api_json(method: str, token: str, path: str, payload: Any, *, expected: set[int]) -> None:
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
