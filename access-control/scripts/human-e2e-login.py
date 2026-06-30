#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / "access-control" / ".env.local"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a browser Authorization Code + PKCE login for human e2e testing."
    )
    parser.add_argument(
        "--env-file",
        default=str(ENV_FILE),
        help="Path to the local access-control env file. Defaults to access-control/.env.local.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for the token JSON. Treat the output as sensitive local test evidence.",
    )
    args = parser.parse_args()

    env = dict(os.environ)
    env.update(read_env_file(Path(args.env_file)))

    keycloak_base_url = env.get("KEYCLOAK_PUBLIC_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    realm = env.get("KEYCLOAK_REALM", "access-control-mvp")
    client_id = env.get("KEYCLOAK_BACKOFFICE_CLIENT_ID", "backoffice")
    client_secret = env.get("KEYCLOAK_BACKOFFICE_CLIENT_SECRET", "change-me-backoffice-secret")
    redirect_uri = env.get("KEYCLOAK_BACKOFFICE_REDIRECT_URI", "http://localhost:9999/callback")

    discovery = get_json(f"{keycloak_base_url}/realms/{realm}/.well-known/openid-configuration")
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)

    auth_url = f"{discovery['authorization_endpoint']}?{urllib.parse.urlencode({
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
    })}"

    callback = wait_for_callback(redirect_uri, auth_url)
    if callback.get("state") != state:
        raise SystemExit("OAuth state mismatch; discard this login attempt.")
    code = callback.get("code")
    if not code:
        raise SystemExit("No authorization code was returned by Keycloak.")

    token_response = post_form(
        discovery["token_endpoint"],
        {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": verifier,
        },
    )
    id_token = token_response.get("id_token")
    claims = decode_claims(id_token) if isinstance(id_token, str) else {}
    if claims.get("nonce") != nonce:
        raise SystemExit("OIDC nonce mismatch; discard this login attempt.")

    result = {
        "subject": claims.get("sub"),
        "email": claims.get("email"),
        "emailVerified": claims.get("email_verified"),
        "preferredUsername": claims.get("preferred_username"),
        "accessToken": token_response.get("access_token"),
        "refreshToken": token_response.get("refresh_token"),
        "idToken": id_token,
        "expiresIn": token_response.get("expires_in"),
        "logoutUrl": logout_url(discovery, id_token, redirect_uri),
    }

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote token JSON to {args.output}", file=sys.stderr)
    else:
        print(payload)


def wait_for_callback(redirect_uri: str, auth_url: str) -> dict[str, str]:
    parsed = urllib.parse.urlparse(redirect_uri)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise SystemExit("The human e2e helper only supports localhost redirect URIs.")
    if not parsed.port:
        raise SystemExit("The redirect URI must include an explicit localhost port.")

    callback: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            request = urllib.parse.urlparse(self.path)
            if request.path != parsed.path:
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(request.query)
            callback.update({key: values[0] for key, values in params.items() if values})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Keycloak login captured. You can return to the terminal.")

    with ThreadingHTTPServer((parsed.hostname or "127.0.0.1", parsed.port), CallbackHandler) as server:
        print("Open this URL in your browser and complete the Keycloak login:\n", file=sys.stderr)
        print(auth_url, file=sys.stderr)
        print("\nWaiting for the localhost callback...", file=sys.stderr)
        server.handle_request()

    return callback


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected JSON response from {url}")
    return payload


def post_form(url: str, form: dict[str, str]) -> dict[str, Any]:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected token response from {url}")
    return payload


def decode_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    return decoded if isinstance(decoded, dict) else {}


def logout_url(discovery: dict[str, Any], id_token: object, redirect_uri: str) -> str | None:
    endpoint = discovery.get("end_session_endpoint")
    if not isinstance(endpoint, str) or not isinstance(id_token, str):
        return None
    return f"{endpoint}?{urllib.parse.urlencode({
        'id_token_hint': id_token,
        'post_logout_redirect_uri': redirect_uri,
    })}"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


if __name__ == "__main__":
    main()
