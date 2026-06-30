from __future__ import annotations

import copy
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any, Callable, TypeVar

from . import config
from .config import DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID


T = TypeVar("T")

SCHEMA_VERSION = "iam-schema-v1"
ACCOUNT_TYPE_ROLE_BY_TYPE = {
    "member": "account-type-member",
    "admin": "account-type-admin",
    "super-admin": "account-type-super-admin",
}
ACCOUNT_TYPE_BY_ROLE = {value: key for key, value in ACCOUNT_TYPE_ROLE_BY_TYPE.items()}
IAM_ATTRS = {
    "iam.account_id",
    "iam.lifecycle",
    "iam.linked_subject",
    "iam.organization",
    "iam.assigned_service_roles",
    "iam.schema_version",
    "iam.last_control_plane_mutation_at",
}
MEMBER_ONBOARDING_ACTIONS = ("VERIFY_EMAIL", "UPDATE_PASSWORD")
PRIVILEGED_ONBOARDING_ACTIONS = ("VERIFY_EMAIL", "UPDATE_PASSWORD", "CONFIGURE_TOTP")


class KeycloakStateStore:
    def __init__(
        self,
        client: KeycloakAdminClient,
        *,
        backoffice_client_id: str,
        service_client_ids: list[str],
        send_onboarding_action_emails: bool = False,
        onboarding_action_email_redirect_uri: str | None = None,
        onboarding_action_email_lifespan_seconds: int | None = None,
    ) -> None:
        self.client = client
        self.backoffice_client_id = backoffice_client_id
        self.service_client_ids = service_client_ids
        self.send_onboarding_action_emails = send_onboarding_action_emails
        self.onboarding_action_email_redirect_uri = onboarding_action_email_redirect_uri
        self.onboarding_action_email_lifespan_seconds = onboarding_action_email_lifespan_seconds
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls) -> KeycloakStateStore:
        return cls(
            KeycloakAdminClient.from_env(),
            backoffice_client_id=config.oidc_client_id(),
            service_client_ids=[config.service_client_id()],
            send_onboarding_action_emails=config.keycloak_onboarding_action_emails_enabled(),
            onboarding_action_email_redirect_uri=config.keycloak_backoffice_redirect_uri(),
            onboarding_action_email_lifespan_seconds=config.keycloak_onboarding_action_email_lifespan_seconds(),
        )

    def load(self) -> dict[str, Any]:
        service_roles = self._load_service_roles()
        accounts: dict[str, dict[str, Any]] = {}
        for user in self.client.list_users():
            account = self._account_from_user(user, service_roles)
            if not account:
                continue
            accounts[account["accountId"]] = account
        return {"accounts": accounts, "serviceRoles": service_roles}

    def transact(self, callback: Callable[[dict[str, Any]], T]) -> T:
        with self._lock:
            original = self.load()
            state = copy.deepcopy(original)
            result = callback(state)
            self.save(state, original)
            return result

    def save(self, state: dict[str, Any], original: dict[str, Any] | None = None) -> None:
        original = original or self.load()
        self._ensure_schema_roles()
        self._apply_service_role_changes(original.get("serviceRoles", {}), state.get("serviceRoles", {}))
        self._apply_account_changes(original.get("accounts", {}), state.get("accounts", {}))

    def _ensure_schema_roles(self) -> None:
        for account_type, role_name in ACCOUNT_TYPE_ROLE_BY_TYPE.items():
            self.client.ensure_client_role(
                self.backoffice_client_id,
                role_name,
                f"MVP Organization {account_type} account type.",
                {"iam.schema_version": [SCHEMA_VERSION]},
            )

    def _load_service_roles(self) -> dict[str, dict[str, Any]]:
        roles: dict[str, dict[str, Any]] = {}
        for service_client_id in self.service_client_ids:
            for role in self.client.list_client_roles(service_client_id):
                role_name = _string(role.get("name"))
                if not role_name:
                    continue
                attrs = _attributes(role)
                role_id = _attr(attrs, "iam.role_id") or f"{service_client_id}:{role_name}"
                status = _attr(attrs, "iam.role_status") or "active"
                roles[role_id] = {
                    "roleId": role_id,
                    "serviceId": service_client_id,
                    "status": status,
                    "description": _string(role.get("description")),
                    "schemaVersion": _attr(attrs, "iam.schema_version") or SCHEMA_VERSION,
                }
        return roles

    def _account_from_user(
        self,
        user: dict[str, Any],
        service_roles: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        attrs = _attributes(user)
        account_id = _attr(attrs, "iam.account_id")
        if not account_id:
            return None
        user_id = _required_string(user, "id")
        account_type, account_type_violations, account_type_roles = self._account_type_for_user(user_id)
        direct_service_role_ids = self._service_roles_for_user(user_id)
        assigned_service_role_ids, assigned_service_role_violations = _assigned_service_roles(attrs)
        lifecycle = _attr(attrs, "iam.lifecycle") or ""
        violations = [*account_type_violations, *assigned_service_role_violations]
        enabled = user.get("enabled") is True
        if lifecycle in {"disabled", "archived"} and enabled:
            violations.append("disabled_or_archived_user_enabled")
        if lifecycle in {"invited", "active"} and not enabled:
            violations.append("invited_or_active_user_disabled")
        if direct_service_role_ids:
            violations.append("direct_service_role_mapping_drift")
        if account_type in {"admin", "super-admin"} and assigned_service_role_ids:
            violations.append("privileged_account_has_service_roles")
        missing_roles = [role_id for role_id in assigned_service_role_ids if role_id not in service_roles]
        if missing_roles:
            violations.append("assigned_service_role_missing")

        account: dict[str, Any] = {
            "accountId": account_id,
            "email": _string(user.get("email")),
            "organization": _attr(attrs, "iam.organization") or "",
            "name": _display_name(user),
            "accountType": account_type,
            "lifecycle": lifecycle,
            "linkedSubject": _attr(attrs, "iam.linked_subject"),
            "serviceRoles": assigned_service_role_ids,
            "schemaVersion": _attr(attrs, "iam.schema_version") or SCHEMA_VERSION,
            "_keycloakUserId": user_id,
            "_keycloakAccountTypeRoles": sorted(account_type_roles),
            "_directServiceRoles": direct_service_role_ids,
        }
        if violations:
            account["_invariantViolations"] = sorted(set(violations))
        return account

    def _account_type_for_user(self, user_id: str) -> tuple[str, list[str], list[str]]:
        roles = self.client.get_user_client_roles(user_id, self.backoffice_client_id)
        role_names = sorted(
            name
            for role in roles
            if (name := _string(role.get("name"))) in ACCOUNT_TYPE_BY_ROLE
        )
        if len(role_names) != 1:
            return "", ["invalid_account_type_role_count"], role_names
        return ACCOUNT_TYPE_BY_ROLE[role_names[0]], [], role_names

    def _service_roles_for_user(self, user_id: str) -> list[str]:
        role_ids: list[str] = []
        for service_client_id in self.service_client_ids:
            for role in self.client.get_user_client_roles(user_id, service_client_id):
                role_name = _string(role.get("name"))
                if not role_name:
                    continue
                attrs = _attributes(role)
                role_ids.append(_attr(attrs, "iam.role_id") or f"{service_client_id}:{role_name}")
        return sorted(set(role_ids))

    def _apply_service_role_changes(
        self,
        original_roles: dict[str, dict[str, Any]],
        target_roles: dict[str, dict[str, Any]],
    ) -> None:
        removed = set(original_roles) - set(target_roles)
        if removed:
            raise RuntimeError(f"Keycloak IAM state does not support service-role deletion: {sorted(removed)}")
        for role_id, role in target_roles.items():
            original = original_roles.get(role_id)
            if original == role:
                continue
            service_id = _required_string(role, "serviceId")
            role_name = _role_name_from_role_id(role_id, service_id)
            self.client.ensure_client_role(
                service_id,
                role_name,
                _string(role.get("description")),
                {
                    "iam.role_id": [role_id],
                    "iam.role_status": [_required_string(role, "status")],
                    "iam.schema_version": [_string(role.get("schemaVersion")) or SCHEMA_VERSION],
                    "iam.last_control_plane_mutation_at": [_now()],
                },
            )

    def _apply_account_changes(
        self,
        original_accounts: dict[str, dict[str, Any]],
        target_accounts: dict[str, dict[str, Any]],
    ) -> None:
        removed = set(original_accounts) - set(target_accounts)
        if removed:
            raise RuntimeError(f"Keycloak IAM state does not support account deletion: {sorted(removed)}")
        service_roles = self._load_service_roles()
        for account_id, account in target_accounts.items():
            original = original_accounts.get(account_id)
            if original == account:
                continue
            user = self._resolve_user_for_account(account, original)
            user_id = _required_string(user, "id")
            is_new_account = original is None
            self._write_user_profile(user, account)
            self._write_account_type_role(user_id, _required_string(account, "accountType"), is_new_account)
            self._write_service_role_assignments(user_id, account, service_roles)
            if is_new_account:
                self._send_onboarding_action_email(user_id, account)

    def _resolve_user_for_account(
        self,
        account: dict[str, Any],
        original: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if original and isinstance(original.get("_keycloakUserId"), str):
            user = self.client.get_user(original["_keycloakUserId"])
            if user:
                return user
        account_id = _required_string(account, "accountId")
        user = self.client.find_user_by_attribute("iam.account_id", account_id)
        if user:
            return user
        linked_subject = account.get("linkedSubject")
        if isinstance(linked_subject, str) and linked_subject:
            user = self.client.get_user(linked_subject)
            if user:
                return user
        email = _required_string(account, "email")
        user = self.client.find_user_by_email(email)
        if user:
            return user
        user_id = self.client.create_user(
            {
                "username": email,
                "enabled": _enabled_for_lifecycle(_required_string(account, "lifecycle")),
                "email": email,
                "emailVerified": False,
                "firstName": _required_string(account, "name"),
                "lastName": "",
                "requiredActions": list(_onboarding_required_actions(_required_string(account, "accountType"))),
                "attributes": {},
            }
        )
        user = self.client.get_user(user_id)
        if not user:
            raise RuntimeError(f"Unable to resolve created Keycloak user for account {account_id}")
        return user

    def _write_user_profile(self, user: dict[str, Any], account: dict[str, Any]) -> None:
        attrs = _attributes(user)
        for attr_name in IAM_ATTRS:
            if attr_name not in attrs:
                continue
            attrs[attr_name] = list(attrs[attr_name])
        _set_attr(attrs, "iam.account_id", _required_string(account, "accountId"))
        _set_attr(attrs, "iam.lifecycle", _required_string(account, "lifecycle"))
        _set_attr(attrs, "iam.linked_subject", account.get("linkedSubject"))
        _set_attr(attrs, "iam.organization", _required_string(account, "organization"))
        _set_attr(attrs, "iam.assigned_service_roles", _assigned_service_roles_json(account.get("serviceRoles")))
        _set_attr(attrs, "iam.schema_version", _string(account.get("schemaVersion")) or SCHEMA_VERSION)
        _set_attr(attrs, "iam.last_control_plane_mutation_at", _now())
        first_name, last_name = _name_parts(_required_string(account, "name"), user)
        required_actions = _string_list(user.get("requiredActions"))
        if (
            account.get("lifecycle") == "invited"
            and not account.get("linkedSubject")
            and user.get("emailVerified") is not True
        ):
            required_actions = _merged_unique(required_actions, _onboarding_required_actions(_required_string(account, "accountType")))
        payload = {
            "id": user["id"],
            "username": user.get("username") or account["email"],
            "enabled": _enabled_for_lifecycle(account["lifecycle"]),
            "email": account["email"],
            "emailVerified": user.get("emailVerified") is True,
            "firstName": first_name,
            "lastName": last_name,
            "requiredActions": required_actions,
            "attributes": attrs,
        }
        self.client.update_user(str(user["id"]), payload)

    def _send_onboarding_action_email(self, user_id: str, account: dict[str, Any]) -> None:
        if not self.send_onboarding_action_emails:
            return
        if account.get("lifecycle") != "invited" or account.get("linkedSubject"):
            return
        actions = list(_onboarding_required_actions(_required_string(account, "accountType")))
        if not actions:
            return
        self.client.execute_actions_email(
            user_id,
            actions,
            client_id=self.backoffice_client_id,
            redirect_uri=self.onboarding_action_email_redirect_uri,
            lifespan_seconds=self.onboarding_action_email_lifespan_seconds,
        )

    def _write_account_type_role(self, user_id: str, account_type: str, is_new_account: bool) -> None:
        desired = ACCOUNT_TYPE_ROLE_BY_TYPE.get(account_type)
        if not desired:
            raise RuntimeError(f"Invalid account type for Keycloak write: {account_type}")
        current_roles = {
            _string(role.get("name"))
            for role in self.client.get_user_client_roles(user_id, self.backoffice_client_id)
        }
        current_account_roles = {role for role in current_roles if role in ACCOUNT_TYPE_BY_ROLE}
        if current_account_roles == {desired}:
            return
        if current_account_roles and not is_new_account:
            raise RuntimeError("Refusing to repair drifted Keycloak account-type roles during a business mutation")
        to_remove = sorted(current_account_roles - {desired})
        if to_remove:
            self.client.remove_user_client_roles(user_id, self.backoffice_client_id, to_remove)
        if desired not in current_account_roles:
            self.client.add_user_client_roles(user_id, self.backoffice_client_id, [desired])

    def _write_service_role_assignments(
        self,
        user_id: str,
        account: dict[str, Any],
        service_roles: dict[str, dict[str, Any]],
    ) -> None:
        for role_id in account.get("serviceRoles", []):
            role = service_roles.get(role_id)
            if not role:
                raise RuntimeError(f"Cannot assign unknown Keycloak service role: {role_id}")
            service_id = _required_string(role, "serviceId")
            if service_id not in self.service_client_ids:
                raise RuntimeError(f"Cannot assign unsupported Keycloak service role: {role_id}")

        for service_id in self.service_client_ids:
            current_roles = self.client.get_user_client_roles(user_id, service_id)
            current_names = {
                _string(role.get("name"))
                for role in current_roles
                if _attr(_attributes(role), "iam.role_id") or _string(role.get("name"))
            }
            if current_names:
                self.client.remove_user_client_roles(user_id, service_id, sorted(current_names))


class KeycloakAdminClient:
    def __init__(
        self,
        *,
        base_url: str,
        realm: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds
        self._cached_token: str | None = None
        self._expires_at = 0.0
        self._client_uuid_cache: dict[str, str] = {}

    @classmethod
    def from_env(cls) -> KeycloakAdminClient:
        return cls(
            base_url=config.keycloak_base_url(),
            realm=config.keycloak_realm(),
            token_url=config.keycloak_admin_token_url(),
            client_id=config.keycloak_admin_client_id(),
            client_secret=config.keycloak_admin_client_secret(),
            timeout_seconds=max(5.0, config.oidc_timeout_seconds()),
        )

    def list_users(self) -> list[dict[str, Any]]:
        response = self._request_json("GET", "users?max=1000&briefRepresentation=false")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected Keycloak users response")
        users: list[dict[str, Any]] = []
        for item in response:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            users.append(self.get_user(item["id"]) or item)
        return users

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        try:
            response = self._request_json("GET", f"users/{urllib.parse.quote(user_id)}")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected Keycloak user response")
        return response

    def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        encoded = urllib.parse.quote(email)
        response = self._request_json("GET", f"users?email={encoded}&exact=true&max=2&briefRepresentation=false")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected Keycloak user search response")
        matches = [item for item in response if isinstance(item, dict) and _string(item.get("email")).lower() == email.lower()]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple Keycloak users share email {email}")
        if not matches:
            return None
        user_id = _required_string(matches[0], "id")
        return self.get_user(user_id)

    def find_user_by_attribute(self, attr_name: str, value: str) -> dict[str, Any] | None:
        query = urllib.parse.quote(f"{attr_name}:{value}")
        response = self._request_json("GET", f"users?q={query}&max=2&briefRepresentation=false")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected Keycloak attribute search response")
        matches = [
            item
            for item in response
            if isinstance(item, dict) and _attr(_attributes(item), attr_name) == value
        ]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple Keycloak users share {attr_name}={value}")
        if not matches:
            return None
        user_id = _required_string(matches[0], "id")
        return self.get_user(user_id)

    def create_user(self, payload: dict[str, Any]) -> str:
        response_headers = self._request_no_json("POST", "users", payload, expected={201, 204})
        location = response_headers.get("Location", "")
        user_id = location.rstrip("/").rsplit("/", 1)[-1] if location else ""
        if user_id:
            return user_id
        email = _required_string(payload, "email")
        user = self.find_user_by_email(email)
        if user and isinstance(user.get("id"), str):
            return user["id"]
        raise RuntimeError(f"Unable to resolve created Keycloak user for {email}")

    def update_user(self, user_id: str, payload: dict[str, Any]) -> None:
        self._request_no_json("PUT", f"users/{urllib.parse.quote(user_id)}", payload, expected={200, 204})

    def execute_actions_email(
        self,
        user_id: str,
        actions: list[str],
        *,
        client_id: str,
        redirect_uri: str | None,
        lifespan_seconds: int | None,
    ) -> None:
        query: dict[str, str] = {"client_id": client_id}
        if redirect_uri:
            query["redirect_uri"] = redirect_uri
        if lifespan_seconds is not None:
            query["lifespan"] = str(lifespan_seconds)
        encoded_query = urllib.parse.urlencode(query)
        self._request_no_json(
            "PUT",
            f"users/{urllib.parse.quote(user_id)}/execute-actions-email?{encoded_query}",
            actions,
            expected={200, 204},
        )

    def list_client_roles(self, client_id: str) -> list[dict[str, Any]]:
        client_uuid = self._client_uuid(client_id)
        response = self._request_json("GET", f"clients/{client_uuid}/roles")
        if not isinstance(response, list):
            raise RuntimeError("Unexpected Keycloak client roles response")
        roles: list[dict[str, Any]] = []
        for item in response:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            roles.append(self._client_role(client_id, item["name"]))
        return roles

    def ensure_client_role(
        self,
        client_id: str,
        role_name: str,
        description: str,
        attributes: dict[str, list[str]],
    ) -> dict[str, Any]:
        client_uuid = self._client_uuid(client_id)
        encoded_role = urllib.parse.quote(role_name)
        payload = {
            "name": role_name,
            "description": description,
            "clientRole": True,
            "attributes": attributes,
        }
        try:
            response = self._request_json("GET", f"clients/{client_uuid}/roles/{encoded_role}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            self._request_no_json("POST", f"clients/{client_uuid}/roles", payload, expected={201, 204})
            response = self._request_json("GET", f"clients/{client_uuid}/roles/{encoded_role}")
        if not isinstance(response, dict):
            raise RuntimeError("Unexpected Keycloak role response")
        merged = {**response, "description": description, "attributes": {**_attributes(response), **attributes}}
        self._request_no_json("PUT", f"clients/{client_uuid}/roles/{encoded_role}", merged, expected={200, 204})
        refreshed = self._request_json("GET", f"clients/{client_uuid}/roles/{encoded_role}")
        if not isinstance(refreshed, dict):
            raise RuntimeError("Unexpected Keycloak role response")
        return refreshed

    def get_user_client_roles(self, user_id: str, client_id: str) -> list[dict[str, Any]]:
        client_uuid = self._client_uuid(client_id)
        response = self._request_json(
            "GET",
            f"users/{urllib.parse.quote(user_id)}/role-mappings/clients/{client_uuid}",
        )
        if not isinstance(response, list):
            raise RuntimeError("Unexpected Keycloak user role mapping response")
        roles: list[dict[str, Any]] = []
        for item in response:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            roles.append(self._client_role(client_id, item["name"]))
        return roles

    def add_user_client_roles(self, user_id: str, client_id: str, role_names: list[str]) -> None:
        if not role_names:
            return
        roles = [self._client_role(client_id, role_name) for role_name in role_names]
        self._change_user_client_roles("POST", user_id, client_id, roles)

    def remove_user_client_roles(self, user_id: str, client_id: str, role_names: list[str]) -> None:
        if not role_names:
            return
        roles = [self._client_role(client_id, role_name) for role_name in role_names]
        self._change_user_client_roles("DELETE", user_id, client_id, roles)

    def _change_user_client_roles(
        self,
        method: str,
        user_id: str,
        client_id: str,
        roles: list[dict[str, Any]],
    ) -> None:
        client_uuid = self._client_uuid(client_id)
        self._request_no_json(
            method,
            f"users/{urllib.parse.quote(user_id)}/role-mappings/clients/{client_uuid}",
            roles,
            expected={200, 204},
        )

    def _client_role(self, client_id: str, role_name: str) -> dict[str, Any]:
        client_uuid = self._client_uuid(client_id)
        encoded_role = urllib.parse.quote(role_name)
        response = self._request_json("GET", f"clients/{client_uuid}/roles/{encoded_role}")
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected Keycloak role response for {client_id}/{role_name}")
        return response

    def _client_uuid(self, client_id: str) -> str:
        if client_id in self._client_uuid_cache:
            return self._client_uuid_cache[client_id]
        encoded = urllib.parse.quote(client_id)
        response = self._request_json("GET", f"clients?clientId={encoded}")
        if not isinstance(response, list) or not response or not isinstance(response[0], dict):
            raise RuntimeError(f"Unable to resolve Keycloak client {client_id}")
        client_uuid = _required_string(response[0], "id")
        self._client_uuid_cache[client_id] = client_uuid
        return client_uuid

    def _request_json(self, method: str, path: str, payload: Any | None = None) -> Any:
        headers = self._request_no_json(method, path, payload, expected={200, 201, 204})
        body = headers.get("_body", "")
        if not body:
            return {}
        return json.loads(body)

    def _request_no_json(
        self,
        method: str,
        path: str,
        payload: Any | None = None,
        *,
        expected: set[int],
    ) -> dict[str, str]:
        data = None
        headers = {"Authorization": f"Bearer {self._token()}"}
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}/admin/realms/{self.realm}/{path}",
            data=data,
            method=method,
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status not in expected:
                raise RuntimeError(f"Unexpected Keycloak status {response.status} for {method} {path}")
            body = response.read().decode("utf-8") if response.status != 204 else ""
            result = {key: value for key, value in response.headers.items()}
            result["_body"] = body
            return result

    def _token(self) -> str:
        now = time.time()
        if self._cached_token and now < self._expires_at - 10:
            return self._cached_token
        data = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.token_url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        token = _string(body.get("access_token"))
        expires_in = body.get("expires_in")
        if not token or not isinstance(expires_in, int):
            raise RuntimeError("Keycloak admin token response is invalid")
        self._cached_token = token
        self._expires_at = now + expires_in
        return token


def _attributes(representation: dict[str, Any]) -> dict[str, list[str]]:
    attrs = representation.get("attributes")
    if not isinstance(attrs, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, value in attrs.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, list):
            normalized[key] = [str(item) for item in value if item is not None]
        elif value is not None:
            normalized[key] = [str(value)]
    return normalized


def _attr(attrs: dict[str, list[str]], name: str) -> str | None:
    value = attrs.get(name)
    if not value:
        return None
    first = value[0].strip()
    return first or None


def _set_attr(attrs: dict[str, list[str]], name: str, value: Any) -> None:
    if isinstance(value, str) and value.strip():
        attrs[name] = [value.strip()]
    else:
        attrs.pop(name, None)


def _assigned_service_roles(attrs: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    raw = _attr(attrs, "iam.assigned_service_roles")
    if raw is None:
        return [], []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return [], ["invalid_assigned_service_roles"]
    if not isinstance(parsed, list):
        return [], ["invalid_assigned_service_roles"]
    role_ids: list[str] = []
    for item in parsed:
        if not isinstance(item, str) or not item.strip():
            return [], ["invalid_assigned_service_roles"]
        role_ids.append(item.strip())
    return sorted(set(role_ids)), []


def _assigned_service_roles_json(value: Any) -> str:
    if not isinstance(value, list):
        return "[]"
    role_ids = sorted(item.strip() for item in value if isinstance(item, str) and item.strip())
    return json.dumps(role_ids, separators=(",", ":"))


def _onboarding_required_actions(account_type: str) -> tuple[str, ...]:
    if account_type in {"admin", "super-admin"}:
        return PRIVILEGED_ONBOARDING_ACTIONS
    return MEMBER_ONBOARDING_ACTIONS


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _merged_unique(existing: list[str], additions: tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys([*existing, *additions]))


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _required_string(values: dict[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Missing required Keycloak IAM value: {key}")
    return value.strip()


def _display_name(user: dict[str, Any]) -> str:
    parts = [
        _string(user.get("firstName")).strip(),
        _string(user.get("lastName")).strip(),
    ]
    name = " ".join(part for part in parts if part)
    return name or _string(user.get("username")) or _string(user.get("email"))


def _name_parts(name: str, existing_user: dict[str, Any]) -> tuple[str, str]:
    parts = name.strip().rsplit(" ", 1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    existing_last = _string(existing_user.get("lastName")).strip()
    return name.strip(), existing_last or "User"


def _role_name_from_role_id(role_id: str, service_id: str) -> str:
    prefix = f"{service_id}:"
    if role_id.startswith(prefix):
        return role_id.removeprefix(prefix)
    if ":" in role_id:
        return role_id.rsplit(":", 1)[1]
    return role_id


def _enabled_for_lifecycle(lifecycle: str) -> bool:
    if lifecycle in {"invited", "active"}:
        return True
    if lifecycle in {"disabled", "archived"}:
        return False
    raise RuntimeError(f"Invalid lifecycle for Keycloak write: {lifecycle}")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
