from __future__ import annotations

import uuid
from typing import Any

from .audit import AuditWriter, build_event
from .config import DEFAULT_PRIVILEGED_ACR, DEFAULT_SERVICE_ID, DEFAULT_SERVICE_ROLE_ID, privileged_acr
from .store import FileStateStore
from .tokens import SubjectTokenValidator, TokenValidationError, subject_token_validator_from_env


ACCOUNT_TYPES = {"member", "admin", "super-admin"}
LIFECYCLES = {"invited", "active", "disabled", "archived"}
ROLE_STATUSES = {"active", "disabled", "archived"}
PROTECTED_PROFILE_FIELDS = {
    "accountId",
    "accountType",
    "lifecycle",
    "linkedSubject",
    "serviceRoles",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, title: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail


class AccessControlService:
    def __init__(
        self,
        store: FileStateStore,
        audit: AuditWriter,
        subject_token_validator: SubjectTokenValidator | None = None,
    ) -> None:
        self.store = store
        self.audit = audit
        self.subject_token_validator = subject_token_validator or subject_token_validator_from_env()

    def bootstrap_first_super_admin(
        self,
        *,
        email: str,
        name: str,
        organization: str,
        subject: str,
    ) -> dict[str, Any]:
        correlation_id = f"bootstrap_{uuid.uuid4().hex}"

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            self._ensure_default_role(state, correlation_id)
            existing = [
                account
                for account in state["accounts"].values()
                if account.get("accountType") == "super-admin" and account.get("lifecycle") == "active"
            ]
            if existing:
                account = existing[0]
                self._audit(
                    "bootstrap.super_admin",
                    "account",
                    account["accountId"],
                    "no_change",
                    correlation_id,
                    "bootstrap-process",
                    "valid_super_admin_exists",
                )
                return {"status": "no_change", "accountId": account["accountId"]}

            account_id = "acc_bootstrap_super_admin"
            account = {
                "accountId": account_id,
                "email": email,
                "organization": organization,
                "name": name,
                "accountType": "super-admin",
                "lifecycle": "active",
                "linkedSubject": subject,
                "serviceRoles": [],
                "schemaVersion": "iam-schema-v1",
            }
            state["accounts"][account_id] = account
            self._audit(
                "bootstrap.super_admin",
                "account",
                account_id,
                "changed",
                correlation_id,
                "bootstrap-process",
                "created_first_super_admin",
            )
            return {"status": "created", "accountId": account_id}

        return self.store.transact(mutate)

    def resolve_actor_id_from_bearer(self, authorization_header: str, correlation_id: str) -> str:
        subject_token = self._bearer_subject_token(authorization_header)
        subject = self._parse_subject_token(subject_token)
        state = self.store.load()
        accounts = [
            account
            for account in state["accounts"].values()
            if account.get("linkedSubject") == subject
        ]
        if len(accounts) != 1:
            raise ApiError(403, "actor_not_resolved", "Forbidden", "Authenticated subject is not linked to one active account.")
        actor = accounts[0]
        self._assert_account_invariants(actor)
        if actor["lifecycle"] != "active":
            raise ApiError(403, "actor_inactive", "Forbidden", "Actor account is not active.")
        return str(actor["accountId"])

    def get_me(self, actor_id: str | None, correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        return self._public_account(actor)

    def get_effective_services(self, actor_id: str | None, correlation_id: str) -> list[dict[str, str]]:
        actor = self._require_actor(actor_id)
        state = self.store.load()
        return self._effective_services(state, actor)

    def list_accounts(self, actor_id: str | None, correlation_id: str) -> list[dict[str, Any]]:
        actor = self._require_actor(actor_id)
        state = self.store.load()
        return [
            self._public_account(account)
            for account in state["accounts"].values()
            if self._can_manage(actor, account)
        ]

    def get_account(self, actor_id: str | None, account_id: str, correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        account = self._require_account(account_id)
        if not self._can_manage(actor, account):
            raise ApiError(404, "not_found", "Not Found", "Account is not visible in the actor scope.")
        return self._public_account(account)

    def create_account(self, actor_id: str | None, payload: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        target_type = payload.get("accountType")
        if target_type not in {"member", "admin"}:
            raise ApiError(422, "invalid_account_type", "Unprocessable Entity", "Only member or admin creation is allowed.")
        if actor["accountType"] == "admin" and target_type != "member":
            raise ApiError(403, "forbidden", "Forbidden", "Admins may create member accounts only.")
        if actor["accountType"] != "super-admin" and actor["accountType"] != "admin":
            raise ApiError(403, "forbidden", "Forbidden", "Actor cannot create accounts.")

        email = self._required_string(payload, "email")
        organization = self._required_string(payload, "organization")
        name = self._required_string(payload, "name")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            duplicate = [
                account
                for account in state["accounts"].values()
                if account.get("email", "").lower() == email.lower()
                and account.get("lifecycle") != "archived"
            ]
            if duplicate:
                raise ApiError(409, "duplicate_account_email", "Conflict", "A non-archived account already uses this email.")
            account_id = f"acc_{uuid.uuid4().hex[:16]}"
            account = {
                "accountId": account_id,
                "email": email,
                "organization": organization,
                "name": name,
                "accountType": target_type,
                "lifecycle": "invited",
                "linkedSubject": None,
                "serviceRoles": [],
                "schemaVersion": "iam-schema-v1",
            }
            state["accounts"][account_id] = account
            self._audit(
                "account.create",
                "account",
                account_id,
                "changed",
                correlation_id,
                actor["accountType"],
                "created_invited_account",
                actor["accountId"],
            )
            return self._public_account(account)

        return self.store.transact(mutate)

    def update_profile(
        self,
        actor_id: str | None,
        account_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        if PROTECTED_PROFILE_FIELDS.intersection(payload):
            raise ApiError(422, "protected_field", "Unprocessable Entity", "Protected account fields cannot be changed here.")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            account = self._require_account_from_state(state, account_id)
            if not self._can_manage(actor, account):
                raise ApiError(404, "not_found", "Not Found", "Account is not visible in the actor scope.")
            for field in ("email", "organization", "name"):
                if field in payload:
                    account[field] = self._required_string(payload, field)
            self._audit(
                "account.profile.update",
                "account",
                account_id,
                "changed",
                correlation_id,
                actor["accountType"],
                "profile_updated",
                actor["accountId"],
            )
            return self._public_account(account)

        return self.store.transact(mutate)

    def lifecycle(self, actor_id: str | None, account_id: str, action: str, correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            account = self._require_account_from_state(state, account_id)
            if not self._can_manage(actor, account):
                raise ApiError(404, "not_found", "Not Found", "Account is not visible in the actor scope.")
            old = account["lifecycle"]
            new = self._next_lifecycle(old, action)
            outcome = "no_change" if old == new else "changed"
            account["lifecycle"] = new
            self._audit(
                f"account.{action}",
                "account",
                account_id,
                outcome,
                correlation_id,
                actor["accountType"],
                f"{old}_to_{new}",
                actor["accountId"],
            )
            return self._public_account(account)

        return self.store.transact(mutate)

    def activate_onboarding(self, payload: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        subject = self._required_string(payload, "subject")
        email = self._required_string(payload, "email")
        email_verified = payload.get("emailVerified") is True
        acr = payload.get("acr")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            active_same_subject = [
                account
                for account in state["accounts"].values()
                if account.get("linkedSubject") == subject and account.get("email", "").lower() == email.lower()
            ]
            if active_same_subject:
                account = active_same_subject[0]
                self._audit(
                    "onboarding.activate",
                    "account",
                    account["accountId"],
                    "no_change",
                    correlation_id,
                    "authenticated-subject",
                    "already_active_same_subject",
                )
                return self._public_account(account)

            candidates = [
                account
                for account in state["accounts"].values()
                if account.get("email", "").lower() == email.lower()
                and account.get("lifecycle") == "invited"
                and not account.get("linkedSubject")
            ]
            if len(candidates) != 1:
                self._audit(
                    "onboarding.activate",
                    "account",
                    "unresolved",
                    "rejected",
                    correlation_id,
                    "authenticated-subject",
                    "unsafe_match_count",
                )
                raise ApiError(409, "unsafe_onboarding_match", "Conflict", "Onboarding did not resolve exactly one invited account.")
            account = candidates[0]
            if not email_verified:
                self._audit(
                    "onboarding.activate",
                    "account",
                    account["accountId"],
                    "rejected",
                    correlation_id,
                    "authenticated-subject",
                    "email_not_verified",
                )
                raise ApiError(403, "email_not_verified", "Forbidden", "Onboarding requires a verified email.")
            if account["accountType"] in {"admin", "super-admin"} and acr != privileged_acr():
                self._audit(
                    "onboarding.activate",
                    "account",
                    account["accountId"],
                    "rejected",
                    correlation_id,
                    "authenticated-subject",
                    "missing_privileged_acr",
                )
                raise ApiError(403, "missing_privileged_acr", "Forbidden", "Privileged onboarding requires privileged authentication evidence.")
            account["linkedSubject"] = subject
            account["lifecycle"] = "active"
            self._audit(
                "onboarding.activate",
                "account",
                account["accountId"],
                "changed",
                correlation_id,
                "authenticated-subject",
                "safe_activation",
            )
            return self._public_account(account)

        return self.store.transact(mutate)

    def list_service_roles(self, actor_id: str | None, correlation_id: str) -> list[dict[str, Any]]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] not in {"admin", "super-admin"}:
            raise ApiError(403, "forbidden", "Forbidden", "Actor cannot list service roles.")
        return list(self.store.load()["serviceRoles"].values())

    def get_service_role(self, actor_id: str | None, role_id: str, correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] not in {"admin", "super-admin"}:
            raise ApiError(403, "forbidden", "Forbidden", "Actor cannot read service roles.")
        role = self.store.load()["serviceRoles"].get(role_id)
        if not role:
            raise ApiError(404, "not_found", "Not Found", "Service role not found.")
        return role

    def create_service_role(self, actor_id: str | None, payload: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] != "super-admin":
            raise ApiError(403, "forbidden", "Forbidden", "Only super-admins can create service roles.")
        role_id = self._required_string(payload, "roleId")
        service_id = self._required_string(payload, "serviceId")
        description = str(payload.get("description", ""))

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            if role_id in state["serviceRoles"]:
                raise ApiError(409, "role_exists", "Conflict", "Service role already exists.")
            role = {
                "roleId": role_id,
                "serviceId": service_id,
                "status": "active",
                "description": description,
                "schemaVersion": "iam-schema-v1",
            }
            state["serviceRoles"][role_id] = role
            self._audit(
                "service_role.create",
                "service-role",
                role_id,
                "changed",
                correlation_id,
                actor["accountType"],
                "created_service_role",
                actor["accountId"],
            )
            return role

        return self.store.transact(mutate)

    def service_role_lifecycle(
        self,
        actor_id: str | None,
        role_id: str,
        action: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] != "super-admin":
            raise ApiError(403, "forbidden", "Forbidden", "Only super-admins can change service-role lifecycle.")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            role = state["serviceRoles"].get(role_id)
            if not role:
                raise ApiError(404, "not_found", "Not Found", "Service role not found.")
            old = role["status"]
            if action == "disable":
                new = "disabled" if old == "active" else old
            elif action == "archive":
                if old == "active":
                    raise ApiError(422, "invalid_transition", "Unprocessable Entity", "Disable a service role before archival.")
                new = "archived"
            else:
                raise ApiError(404, "not_found", "Not Found", "Unsupported lifecycle action.")
            role["status"] = new
            self._audit(
                f"service_role.{action}",
                "service-role",
                role_id,
                "no_change" if old == new else "changed",
                correlation_id,
                actor["accountType"],
                f"{old}_to_{new}",
                actor["accountId"],
            )
            return role

        return self.store.transact(mutate)

    def assign_service_role(
        self,
        actor_id: str | None,
        account_id: str,
        role_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        return self._change_assignment(actor_id, account_id, role_id, correlation_id, assign=True)

    def remove_service_role(
        self,
        actor_id: str | None,
        account_id: str,
        role_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        return self._change_assignment(actor_id, account_id, role_id, correlation_id, assign=False)

    def authorization_check(self, payload: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        subject_token = self._required_string(payload, "subjectToken")
        service_id = self._required_string(payload, "serviceId")
        required_role = self._required_string(payload, "requiredRole")
        subject = self._parse_subject_token(subject_token)
        state = self.store.load()
        try:
            role = state["serviceRoles"].get(required_role)
            if not role or role.get("serviceId") != service_id or role.get("status") != "active":
                return self._deny(correlation_id, service_id, required_role, "role_not_active")
            accounts = [
                account
                for account in state["accounts"].values()
                if account.get("linkedSubject") == subject
            ]
            if len(accounts) != 1:
                return self._deny(correlation_id, service_id, required_role, "linked_account_not_found")
            account = accounts[0]
            self._assert_account_invariants(account)
            if account["lifecycle"] != "active":
                return self._deny(correlation_id, service_id, required_role, "account_not_active", account)
            if account["accountType"] in {"admin", "super-admin"}:
                return self._allow(correlation_id, service_id, required_role, account)
            if required_role in account.get("serviceRoles", []):
                return self._allow(correlation_id, service_id, required_role, account)
            return self._deny(correlation_id, service_id, required_role, "not_authorized", account)
        except ApiError:
            self._audit(
                "authorization.check.indeterminate",
                "service",
                service_id,
                "rejected",
                correlation_id,
                "protected-service",
                "invariant_violation",
                client_id=DEFAULT_SERVICE_ID,
            )
            raise ApiError(503, "indeterminate", "Service Unavailable", "Authorization state cannot be safely determined.")

    def read_audit_events(self, actor_id: str | None, correlation_id: str) -> list[dict[str, Any]]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] != "super-admin":
            raise ApiError(403, "forbidden", "Forbidden", "Only super-admins can read audit events.")
        events = self.audit.read_events()
        self._audit(
            "audit.read",
            "audit",
            "events",
            "no_change",
            correlation_id,
            actor["accountType"],
            "audit_list_read",
            actor["accountId"],
        )
        return events

    def read_audit_event(self, actor_id: str | None, event_id: str, correlation_id: str) -> dict[str, Any]:
        events = self.read_audit_events(actor_id, correlation_id)
        for event in events:
            if event.get("eventId") == event_id:
                return event
        raise ApiError(404, "not_found", "Not Found", "Audit event not found.")

    def _change_assignment(
        self,
        actor_id: str | None,
        account_id: str,
        role_id: str,
        correlation_id: str,
        *,
        assign: bool,
    ) -> dict[str, Any]:
        actor = self._require_actor(actor_id)
        if actor["accountType"] not in {"admin", "super-admin"}:
            raise ApiError(403, "forbidden", "Forbidden", "Actor cannot change role assignments.")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            account = self._require_account_from_state(state, account_id)
            if not self._can_manage(actor, account) or account["accountType"] != "member":
                raise ApiError(403, "forbidden", "Forbidden", "Service roles can be assigned only to managed member accounts.")
            role = state["serviceRoles"].get(role_id)
            if not role or role.get("status") != "active":
                raise ApiError(422, "role_not_active", "Unprocessable Entity", "Only active service roles may be assigned.")
            roles = set(account.get("serviceRoles", []))
            before = set(roles)
            if assign:
                roles.add(role_id)
            else:
                roles.discard(role_id)
            account["serviceRoles"] = sorted(roles)
            changed = before != roles
            operation = "service_role.assign" if assign else "service_role.remove"
            self._audit(
                operation,
                "account",
                account_id,
                "changed" if changed else "no_change",
                correlation_id,
                actor["accountType"],
                role_id,
                actor["accountId"],
            )
            return self._public_account(account)

        return self.store.transact(mutate)

    def _ensure_default_role(self, state: dict[str, Any], correlation_id: str) -> None:
        role = state["serviceRoles"].get(DEFAULT_SERVICE_ROLE_ID)
        if role:
            return
        state["serviceRoles"][DEFAULT_SERVICE_ROLE_ID] = {
            "roleId": DEFAULT_SERVICE_ROLE_ID,
            "serviceId": DEFAULT_SERVICE_ID,
            "status": "active",
            "description": "Initial MVP access-check demo consultation role.",
            "schemaVersion": "iam-schema-v1",
        }
        self._audit(
            "service_role.bootstrap",
            "service-role",
            DEFAULT_SERVICE_ROLE_ID,
            "changed",
            correlation_id,
            "bootstrap-process",
            "created_initial_service_role",
        )

    def _deny(
        self,
        correlation_id: str,
        service_id: str,
        required_role: str,
        reason: str,
        account: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._audit(
            "authorization.check.denied",
            "service",
            service_id,
            "rejected",
            correlation_id,
            "protected-service",
            reason,
            client_id=DEFAULT_SERVICE_ID,
        )
        return {
            "decision": "deny",
            "reason": reason,
            "serviceId": service_id,
            "requiredRole": required_role,
            "correlationId": correlation_id,
        }

    def _allow(
        self,
        correlation_id: str,
        service_id: str,
        required_role: str,
        account: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "decision": "allow",
            "accountId": account["accountId"],
            "serviceId": service_id,
            "requiredRole": required_role,
            "correlationId": correlation_id,
        }

    def _audit(
        self,
        operation: str,
        target_type: str,
        target_id: str,
        outcome: str,
        correlation_id: str,
        actor_type: str,
        reason_code: str | None = None,
        actor_account_id: str | None = None,
        *,
        client_id: str | None = None,
    ) -> None:
        self.audit.append(
            build_event(
                operation=operation,
                target_type=target_type,
                target_id=target_id,
                outcome=outcome,
                correlation_id=correlation_id,
                actor_type=actor_type,
                reason_code=reason_code,
                actor_account_id=actor_account_id,
                client_id=client_id,
            )
        )

    def _require_actor(self, actor_id: str | None) -> dict[str, Any]:
        if not actor_id:
            raise ApiError(401, "missing_actor", "Unauthorized", "Missing actor account identifier.")
        actor = self._require_account(actor_id)
        self._assert_account_invariants(actor)
        if actor["lifecycle"] != "active":
            raise ApiError(403, "actor_inactive", "Forbidden", "Actor account is not active.")
        return actor

    def _require_account(self, account_id: str) -> dict[str, Any]:
        return self._require_account_from_state(self.store.load(), account_id)

    def _require_account_from_state(self, state: dict[str, Any], account_id: str) -> dict[str, Any]:
        account = state["accounts"].get(account_id)
        if not account:
            raise ApiError(404, "not_found", "Not Found", "Account not found.")
        return account

    def _assert_account_invariants(self, account: dict[str, Any]) -> None:
        if account.get("accountType") not in ACCOUNT_TYPES:
            raise ApiError(503, "invalid_account_type", "Service Unavailable", "Invalid account type state.")
        if account.get("lifecycle") not in LIFECYCLES:
            raise ApiError(503, "invalid_lifecycle", "Service Unavailable", "Invalid lifecycle state.")
        if not account.get("accountId"):
            raise ApiError(503, "missing_account_id", "Service Unavailable", "Missing stable account identifier.")

    def _can_manage(self, actor: dict[str, Any], target: dict[str, Any]) -> bool:
        if actor["accountType"] == "admin":
            return target.get("accountType") == "member"
        if actor["accountType"] == "super-admin":
            return target.get("accountType") in {"admin", "member"}
        return actor["accountId"] == target.get("accountId")

    def _next_lifecycle(self, current: str, action: str) -> str:
        if action == "disable":
            if current == "active":
                return "disabled"
            if current == "disabled":
                return "disabled"
            raise ApiError(422, "invalid_transition", "Unprocessable Entity", "Only active accounts can be disabled.")
        if action == "restore":
            if current == "disabled":
                return "active"
            if current == "active":
                return "active"
            raise ApiError(422, "invalid_transition", "Unprocessable Entity", "Only disabled accounts can be restored.")
        if action == "archive":
            if current == "disabled":
                return "archived"
            if current == "archived":
                return "archived"
            raise ApiError(422, "invalid_transition", "Unprocessable Entity", "Only disabled accounts can be archived.")
        raise ApiError(404, "not_found", "Not Found", "Unsupported lifecycle action.")

    def _effective_services(self, state: dict[str, Any], account: dict[str, Any]) -> list[dict[str, str]]:
        if account["lifecycle"] != "active":
            return []
        active_roles = {
            role_id: role
            for role_id, role in state["serviceRoles"].items()
            if role.get("status") == "active"
        }
        if account["accountType"] in {"admin", "super-admin"}:
            role_ids = sorted(active_roles)
        else:
            role_ids = sorted(set(account.get("serviceRoles", [])).intersection(active_roles))
        return [
            {"serviceId": active_roles[role_id]["serviceId"], "roleId": role_id}
            for role_id in role_ids
        ]

    def _parse_subject_token(self, subject_token: str) -> str:
        try:
            return self.subject_token_validator.validate(subject_token).subject
        except TokenValidationError as exc:
            raise ApiError(exc.status, exc.code, exc.title, exc.detail) from exc

    def _bearer_subject_token(self, authorization_header: str) -> str:
        if not authorization_header.startswith("Bearer "):
            raise ApiError(401, "missing_bearer_token", "Unauthorized", "Missing bearer user token.")
        token = authorization_header.removeprefix("Bearer ").strip()
        if not token:
            raise ApiError(401, "missing_bearer_token", "Unauthorized", "Empty bearer user token.")
        return token

    def _public_account(self, account: dict[str, Any]) -> dict[str, Any]:
        return {
            "accountId": account["accountId"],
            "email": account["email"],
            "organization": account["organization"],
            "name": account["name"],
            "accountType": account["accountType"],
            "lifecycle": account["lifecycle"],
            "hasLinkedSubject": bool(account.get("linkedSubject")),
            "serviceRoles": list(account.get("serviceRoles", [])),
        }

    def _required_string(self, payload: dict[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ApiError(422, "validation_error", "Unprocessable Entity", f"{field} is required.")
        return value.strip()
