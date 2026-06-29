from __future__ import annotations

import json
import os


DEFAULT_STATE_PATH = "/app/runtime/state/state.json"
DEFAULT_AUDIT_PATH = "/app/runtime/audit/audit.jsonl"
DEFAULT_SERVICE_ROLE_ID = "access-check-demo:consult"
DEFAULT_SERVICE_ID = "access-check-demo-service"
DEFAULT_PRIVILEGED_ACR = "iam-privileged"
DEFAULT_KEYCLOAK_REALM = "access-control-mvp"
DEFAULT_BACKOFFICE_CLIENT_ID = "backoffice"


def state_path() -> str:
    return os.environ.get("IAM_STATE_PATH", DEFAULT_STATE_PATH)


def state_backend() -> str:
    return os.environ.get("IAM_STATE_BACKEND", "file").strip().lower()


def audit_path() -> str:
    return os.environ.get("IAM_AUDIT_PATH", DEFAULT_AUDIT_PATH)


def service_token() -> str:
    return os.environ.get("IAM_SERVICE_TOKEN", "change-me-service-token")


def privileged_acr() -> str:
    return os.environ.get("IAM_PRIVILEGED_ACR", DEFAULT_PRIVILEGED_ACR)


def subject_token_mode() -> str:
    return os.environ.get("IAM_SUBJECT_TOKEN_MODE", "dev").strip().lower()


def service_auth_mode() -> str:
    return os.environ.get("IAM_SERVICE_AUTH_MODE", "shared-token").strip().lower()


def allow_dev_actor_header() -> bool:
    value = os.environ.get("IAM_ALLOW_DEV_ACTOR_HEADER", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def oidc_timeout_seconds() -> float:
    return int(os.environ.get("OIDC_TIMEOUT_MS", "1000")) / 1000


def keycloak_realm() -> str:
    return os.environ.get("KEYCLOAK_REALM", DEFAULT_KEYCLOAK_REALM)


def keycloak_base_url() -> str:
    return os.environ.get("KEYCLOAK_BASE_URL", "http://keycloak:8080").rstrip("/")


def oidc_issuer() -> str:
    return os.environ.get("OIDC_ISSUER", f"{keycloak_base_url()}/realms/{keycloak_realm()}").rstrip("/")


def oidc_introspection_url() -> str:
    return os.environ.get(
        "OIDC_INTROSPECTION_URL",
        f"{oidc_issuer()}/protocol/openid-connect/token/introspect",
    )


def oidc_client_id() -> str:
    return os.environ.get("OIDC_CLIENT_ID", DEFAULT_BACKOFFICE_CLIENT_ID)


def oidc_client_secret() -> str:
    return os.environ.get("OIDC_CLIENT_SECRET", "change-me-backoffice-secret")


def oidc_expected_audience() -> str:
    return os.environ.get("OIDC_EXPECTED_AUDIENCE", DEFAULT_SERVICE_ID)


def service_introspection_url() -> str:
    return os.environ.get("IAM_SERVICE_INTROSPECTION_URL", oidc_introspection_url())


def service_client_id() -> str:
    return os.environ.get("IAM_SERVICE_CLIENT_ID", DEFAULT_SERVICE_ID)


def service_client_secret() -> str:
    return os.environ.get("IAM_SERVICE_CLIENT_SECRET", "change-me-demo-service-secret")


def service_token_url() -> str:
    return os.environ.get("IAM_SERVICE_TOKEN_URL", f"{oidc_issuer()}/protocol/openid-connect/token")


def keycloak_admin_client_id() -> str:
    return os.environ.get("KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_ID", "iam-control-plane")


def keycloak_admin_client_secret() -> str:
    return os.environ.get("KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_SECRET", "change-me-iam-control-plane-secret")


def keycloak_admin_token_url() -> str:
    return os.environ.get("KEYCLOAK_ADMIN_TOKEN_URL", f"{oidc_issuer()}/protocol/openid-connect/token")


def bootstrap_config() -> dict[str, str]:
    subject = os.environ.get("BOOTSTRAP_SUPER_ADMIN_SUBJECT", "bootstrap-super-admin-subject")
    subject_file = os.environ.get("BOOTSTRAP_SUPER_ADMIN_SUBJECT_FILE")
    if subject_file and os.path.exists(subject_file):
        with open(subject_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and isinstance(payload.get("superAdminSubject"), str):
            subject = payload["superAdminSubject"]
    return {
        "email": os.environ.get("BOOTSTRAP_SUPER_ADMIN_EMAIL", "super-admin@example.test"),
        "name": os.environ.get("BOOTSTRAP_SUPER_ADMIN_NAME", "Initial Super Admin"),
        "organization": os.environ.get("BOOTSTRAP_SUPER_ADMIN_ORGANIZATION", "MVP Organization"),
        "subject": subject,
    }
