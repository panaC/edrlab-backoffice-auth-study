from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from . import config


class TokenValidationError(Exception):
    def __init__(self, status: int, code: str, title: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail


@dataclass(frozen=True)
class SubjectEvidence:
    subject: str
    issuer: str | None = None
    audience: tuple[str, ...] = ()
    client_id: str | None = None
    email: str | None = None
    email_verified: bool | None = None
    acr: str | None = None


class SubjectTokenValidator:
    def validate(self, token: str) -> SubjectEvidence:
        raise NotImplementedError


class DevSubjectTokenValidator(SubjectTokenValidator):
    def validate(self, token: str) -> SubjectEvidence:
        if not token.startswith("dev-sub:"):
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is invalid for this runtime.")
        subject = token.removeprefix("dev-sub:").strip()
        if not subject:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is empty.")
        return SubjectEvidence(subject=subject)


class OidcIntrospectionSubjectTokenValidator(SubjectTokenValidator):
    def __init__(
        self,
        introspection_url: str,
        client_id: str,
        client_secret: str,
        expected_issuer: str,
        expected_audience: str,
        timeout_seconds: float,
    ) -> None:
        self.introspection_url = introspection_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.expected_issuer = expected_issuer.rstrip("/")
        self.expected_audience = expected_audience
        self.timeout_seconds = timeout_seconds

    def validate(self, token: str) -> SubjectEvidence:
        response = self._introspect(token)
        self._require_active(response)
        issuer = _string(response.get("iss"))
        if issuer != self.expected_issuer:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token issuer is invalid.")
        if not _contains_claim(response.get("aud"), self.expected_audience):
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token audience is invalid.")
        if not _is_unexpired(response.get("exp")):
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is expired or missing expiry.")
        subject = _string(response.get("sub"))
        if not subject:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is missing a subject.")
        token_client = _string(response.get("client_id")) or _string(response.get("azp"))
        if token_client != self.client_id:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token client is invalid.")
        return SubjectEvidence(
            subject=subject,
            issuer=issuer,
            audience=tuple(_claim_values(response.get("aud"))),
            client_id=token_client,
            email=_string(response.get("email")),
            email_verified=response.get("email_verified") if isinstance(response.get("email_verified"), bool) else None,
            acr=_string(response.get("acr")),
        )

    def _introspect(self, token: str) -> dict[str, Any]:
        return _post_introspection(
            self.introspection_url,
            self.client_id,
            self.client_secret,
            {"token": token, "token_type_hint": "access_token"},
            self.timeout_seconds,
        )

    def _require_active(self, response: dict[str, Any]) -> None:
        if response.get("active") is not True:
            raise TokenValidationError(401, "invalid_subject_token", "Unauthorized", "Subject token is inactive or invalid.")


class ServiceAuthenticator:
    def require_authorized(self, authorization_header: str) -> None:
        raise NotImplementedError


class SharedSecretServiceAuthenticator(ServiceAuthenticator):
    def __init__(self, expected_token: str) -> None:
        self.expected_token = expected_token

    def require_authorized(self, authorization_header: str) -> None:
        if authorization_header != f"Bearer {self.expected_token}":
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Invalid service authentication.")


class OidcServiceTokenAuthenticator(ServiceAuthenticator):
    def __init__(
        self,
        introspection_url: str,
        client_id: str,
        client_secret: str,
        expected_service_client_id: str,
        expected_issuer: str,
        expected_audience: str,
        timeout_seconds: float,
    ) -> None:
        self.introspection_url = introspection_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.expected_service_client_id = expected_service_client_id
        self.expected_issuer = expected_issuer.rstrip("/")
        self.expected_audience = expected_audience
        self.timeout_seconds = timeout_seconds

    def require_authorized(self, authorization_header: str) -> None:
        token = _bearer_token(authorization_header)
        response = _post_introspection(
            self.introspection_url,
            self.client_id,
            self.client_secret,
            {"token": token, "token_type_hint": "access_token"},
            self.timeout_seconds,
        )
        if response.get("active") is not True:
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token is inactive or invalid.")
        issuer = _string(response.get("iss"))
        if issuer != self.expected_issuer:
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token issuer is invalid.")
        if not _contains_claim(response.get("aud"), self.expected_audience):
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token audience is invalid.")
        if not _is_unexpired(response.get("exp")):
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token is expired or missing expiry.")
        subject = _string(response.get("sub"))
        if not subject:
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token is missing a subject.")
        token_client = _string(response.get("client_id")) or _string(response.get("azp"))
        if token_client != self.expected_service_client_id:
            raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Service token client is invalid.")


class ServiceTokenProvider:
    def authorization_header(self) -> str:
        raise NotImplementedError


class SharedSecretServiceTokenProvider(ServiceTokenProvider):
    def __init__(self, token: str) -> None:
        self.token = token

    def authorization_header(self) -> str:
        return f"Bearer {self.token}"


class OidcClientCredentialsServiceTokenProvider(ServiceTokenProvider):
    def __init__(self, token_url: str, client_id: str, client_secret: str, timeout_seconds: float) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds
        self._cached_token: str | None = None
        self._expires_at = 0.0

    def authorization_header(self) -> str:
        now = time.time()
        if self._cached_token and now < self._expires_at - 10:
            return f"Bearer {self._cached_token}"
        token, expires_in = self._request_token()
        self._cached_token = token
        self._expires_at = now + expires_in
        return f"Bearer {token}"

    def _request_token(self) -> tuple[str, int]:
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
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise TokenValidationError(503, "service_token_unavailable", "Service Unavailable", "Service authentication token is unavailable.") from exc
        token = _string(body.get("access_token"))
        expires_in = body.get("expires_in")
        if not token or not isinstance(expires_in, int):
            raise TokenValidationError(503, "service_token_unavailable", "Service Unavailable", "Service authentication token response is invalid.")
        return token, expires_in


def subject_token_validator_from_env() -> SubjectTokenValidator:
    if config.subject_token_mode() == "oidc":
        return OidcIntrospectionSubjectTokenValidator(
            config.oidc_introspection_url(),
            config.oidc_client_id(),
            config.oidc_client_secret(),
            config.oidc_issuer(),
            config.oidc_expected_audience(),
            config.oidc_timeout_seconds(),
        )
    return DevSubjectTokenValidator()


def service_authenticator_from_env() -> ServiceAuthenticator:
    if config.service_auth_mode() == "oidc":
        return OidcServiceTokenAuthenticator(
            config.service_introspection_url(),
            config.service_client_id(),
            config.service_client_secret(),
            config.service_client_id(),
            config.oidc_issuer(),
            config.keycloak_admin_client_id(),
            config.oidc_timeout_seconds(),
        )
    return SharedSecretServiceAuthenticator(config.service_token())


def service_token_provider_from_env() -> ServiceTokenProvider:
    if config.service_auth_mode() == "oidc":
        return OidcClientCredentialsServiceTokenProvider(
            config.service_token_url(),
            config.service_client_id(),
            config.service_client_secret(),
            config.oidc_timeout_seconds(),
        )
    return SharedSecretServiceTokenProvider(config.service_token())


def _post_introspection(
    url: str,
    client_id: str,
    client_secret: str,
    form: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    data = urllib.parse.urlencode(form).encode("utf-8")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in {400, 401, 403}:
            raise TokenValidationError(401, "invalid_token_introspection", "Unauthorized", "Token introspection was rejected.") from exc
        raise TokenValidationError(503, "token_introspection_unavailable", "Service Unavailable", "Token introspection is unavailable.") from exc
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise TokenValidationError(503, "token_introspection_unavailable", "Service Unavailable", "Token introspection is unavailable.") from exc
    if not isinstance(body, dict):
        raise TokenValidationError(503, "token_introspection_unavailable", "Service Unavailable", "Token introspection response is invalid.")
    return body


def _bearer_token(authorization_header: str) -> str:
    if not authorization_header.startswith("Bearer "):
        raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Missing bearer service token.")
    token = authorization_header.removeprefix("Bearer ").strip()
    if not token:
        raise TokenValidationError(401, "invalid_service_token", "Unauthorized", "Empty bearer service token.")
    return token


def _claim_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _contains_claim(value: Any, expected: str) -> bool:
    return expected in _claim_values(value)


def _is_unexpired(value: Any) -> bool:
    return isinstance(value, int) and value > int(time.time())


def _string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
