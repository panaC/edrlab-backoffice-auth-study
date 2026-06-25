#!/usr/bin/env python3
import base64
import datetime as dt
import hashlib
import hmac
import html
import html.parser
import http.cookiejar
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def utc_timestamp():
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def compact_timestamp():
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def fail(message):
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def pass_(message):
    print(f"PASS {message}")


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None or value == "":
        fail(f"missing required environment variable: {name}")
    return value


KEYCLOAK_BASE_URL = env("KEYCLOAK_BASE_URL").rstrip("/")
KEYCLOAK_REALM = env("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = env("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = env("KEYCLOAK_CLIENT_SECRET")
KC_BOOTSTRAP_ADMIN_USERNAME = env("KC_BOOTSTRAP_ADMIN_USERNAME")
KC_BOOTSTRAP_ADMIN_PASSWORD = env("KC_BOOTSTRAP_ADMIN_PASSWORD")
BACKOFFICE_REDIRECT_URI = env("BACKOFFICE_REDIRECT_URI")
POC_USER_PASSWORD = env("POC_USER_PASSWORD")
POC_ADMIN_USERNAME = env("POC_ADMIN_USERNAME")
POC_ADMIN_EMAIL = env("POC_ADMIN_EMAIL")
POC_SUPER_ADMIN_USERNAME = env("POC_SUPER_ADMIN_USERNAME")
POC_SUPER_ADMIN_EMAIL = env("POC_SUPER_ADMIN_EMAIL")
EVIDENCE_ROOT = Path(env("EVIDENCE_ROOT", "/work/poc/keycloak/evidence"))

PRIVILEGED_ACR = env("WP013_PRIVILEGED_ACR", "edrlab-privileged")
NORMAL_ACR = env("WP013_NORMAL_ACR", "edrlab-normal")
STEP_UP_FLOW_ALIAS = f"edrlab-wp013-step-up-{compact_timestamp()}"
RUN_STARTED_AT_MS = int(time.time() * 1000)
EVENT_WINDOW_STARTED_AT_MS = RUN_STARTED_AT_MS - 5000
EVIDENCE_DIR = EVIDENCE_ROOT / compact_timestamp()
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


class LoginFormParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag.lower() == "form" and not self.action:
            action = values.get("action", "")
            if "login-actions/" in action:
                self.action = html.unescape(action)
        if tag.lower() == "input":
            name = values.get("name")
            if name:
                self.inputs[name] = values.get("value", "")


class BackofficeRedirect(Exception):
    def __init__(self, url):
        super().__init__(url)
        self.url = url


class SelectiveRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if newurl.startswith(BACKOFFICE_REDIRECT_URI):
            raise BackofficeRedirect(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def browser_opener(cookie_jar):
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        SelectiveRedirectHandler(),
    )


def write_json(name, value):
    path = EVIDENCE_DIR / name
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def b64url_decode(value):
    value += "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))


def b64url(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def random_urlsafe(byte_count):
    return b64url(secrets.token_bytes(byte_count))


def pkce_challenge(verifier):
    return b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def form_encode(values):
    return urllib.parse.urlencode(values).encode("utf-8")


def http_request(method, url, token=None, json_body=None, form_body=None, expected=(200,)):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode("utf-8")
    if form_body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = form_encode(form_body)
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            status = response.getcode()
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status = exc.code
        response_headers = dict(exc.headers.items())
    if status not in expected:
        detail = body.decode("utf-8", errors="replace")
        fail(f"unexpected HTTP {status} for {method} {url}: {detail}")
    if not body:
        return None, status, response_headers
    content_type = response_headers.get("Content-Type", "")
    if "json" in content_type:
        return json.loads(body.decode("utf-8")), status, response_headers
    return body.decode("utf-8", errors="replace"), status, response_headers


def admin_url(path):
    return f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/{path}"


def realm_url(path):
    return f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/{path}"


def admin_token():
    body, _, _ = http_request(
        "POST",
        f"{KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token",
        form_body={
            "client_id": "admin-cli",
            "username": KC_BOOTSTRAP_ADMIN_USERNAME,
            "password": KC_BOOTSTRAP_ADMIN_PASSWORD,
            "grant_type": "password",
        },
    )
    return body["access_token"]


def admin_get(token, path):
    body, _, _ = http_request("GET", admin_url(path), token=token)
    return body


def admin_put(token, path, payload):
    http_request("PUT", admin_url(path), token=token, json_body=payload, expected=(200, 204))


def admin_post(token, path, payload, expected=(200, 201, 204)):
    body, status, headers = http_request("POST", admin_url(path), token=token, json_body=payload, expected=expected)
    return body, status, headers


def admin_delete(token, path, expected=(204,)):
    http_request("DELETE", admin_url(path), token=token, expected=expected)


def user_uuid(token, username):
    query = urllib.parse.urlencode({"username": username, "exact": "true"})
    users = admin_get(token, f"users?{query}")
    if not users:
        fail(f"user not found: {username}")
    return users[0]["id"]


def client_uuid(token):
    query = urllib.parse.urlencode({"clientId": KEYCLOAK_CLIENT_ID})
    clients = admin_get(token, f"clients?{query}")
    if not clients:
        fail(f"client not found: {KEYCLOAK_CLIENT_ID}")
    return clients[0]["id"]


def configure_acr_loa_mapping(token):
    realm = admin_get(token, "")
    realm["attributes"] = realm.get("attributes") or {}
    realm["attributes"]["acr.loa.map"] = json.dumps({NORMAL_ACR: 1, PRIVILEGED_ACR: 2}, separators=(",", ":"))
    admin_put(token, "", realm)
    updated = admin_get(token, "")
    write_json(
        "wp-013-acr-loa-map.json",
        {
            "generated_at": utc_timestamp(),
            "realm": KEYCLOAK_REALM,
            "acr_loa_map": json.loads(updated["attributes"]["acr.loa.map"]),
            "source": "Keycloak realm attributes acr.loa.map",
        },
    )
    pass_("Configured Keycloak realm ACR to LoA mapping")


def flow_by_alias(token, alias):
    flows = admin_get(token, "authentication/flows")
    return next((flow for flow in flows if flow.get("alias") == alias), None)


def execution_by_provider(token, flow_alias, provider_id, config_required=None):
    executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(flow_alias, safe='')}/executions")
    matches = [item for item in executions if item.get("providerId") == provider_id]
    if config_required is True:
        matches = [item for item in matches if item.get("authenticationConfig") is None]
    if not matches:
        fail(f"execution provider {provider_id} not found in flow {flow_alias}")
    return matches[-1]


def execution_by_display_name(token, flow_alias, display_name):
    executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(flow_alias, safe='')}/executions")
    matches = [item for item in executions if item.get("displayName") == display_name]
    if not matches:
        fail(f"execution {display_name} not found in flow {flow_alias}")
    return matches[-1]


def set_execution_requirement(token, flow_alias, execution, requirement):
    execution = dict(execution)
    execution["requirement"] = requirement
    admin_put(token, f"authentication/flows/{urllib.parse.quote(flow_alias, safe='')}/executions", execution)


def add_execution(token, flow_alias, provider_id, requirement):
    admin_post(
        token,
        f"authentication/flows/{urllib.parse.quote(flow_alias, safe='')}/executions/execution",
        {"provider": provider_id},
    )
    execution = execution_by_provider(token, flow_alias, provider_id, config_required=True)
    set_execution_requirement(token, flow_alias, execution, requirement)
    return execution


def add_subflow(token, parent_alias, child_alias, requirement):
    admin_post(
        token,
        f"authentication/flows/{urllib.parse.quote(parent_alias, safe='')}/executions/flow",
        {"alias": child_alias, "type": "basic-flow", "provider": "basic-flow"},
    )
    execution = execution_by_display_name(token, parent_alias, child_alias)
    set_execution_requirement(token, parent_alias, execution, requirement)


def configure_loa_execution(token, flow_alias, level, max_age):
    execution = add_execution(token, flow_alias, "conditional-level-of-authentication", "REQUIRED")
    admin_post(
        token,
        f"authentication/executions/{execution['id']}/config",
        {
            "alias": f"{STEP_UP_FLOW_ALIAS}-loa-{level}",
            "config": {
                "loa-condition-level": str(level),
                "loa-max-age": str(max_age),
            },
        },
        expected=(201, 204),
    )


def configure_step_up_flow(token):
    if flow_by_alias(token, STEP_UP_FLOW_ALIAS):
        fail(f"unexpected existing run-specific flow alias: {STEP_UP_FLOW_ALIAS}")

    admin_post(
        token,
        "authentication/flows",
        {
            "alias": STEP_UP_FLOW_ALIAS,
            "providerId": "basic-flow",
            "topLevel": True,
            "builtIn": False,
        },
    )
    add_execution(token, STEP_UP_FLOW_ALIAS, "auth-cookie", "ALTERNATIVE")

    auth_flow = f"{STEP_UP_FLOW_ALIAS}-auth"
    loa1_flow = f"{STEP_UP_FLOW_ALIAS}-loa1"
    loa2_flow = f"{STEP_UP_FLOW_ALIAS}-loa2"
    add_subflow(token, STEP_UP_FLOW_ALIAS, auth_flow, "ALTERNATIVE")
    add_subflow(token, auth_flow, loa1_flow, "CONDITIONAL")
    configure_loa_execution(token, loa1_flow, 1, 36000)
    add_execution(token, loa1_flow, "auth-username-password-form", "REQUIRED")
    add_subflow(token, auth_flow, loa2_flow, "CONDITIONAL")
    configure_loa_execution(token, loa2_flow, 2, 0)
    add_execution(token, loa2_flow, "auth-otp-form", "REQUIRED")

    realm = admin_get(token, "")
    original_browser_flow = realm.get("browserFlow")
    realm["browserFlow"] = STEP_UP_FLOW_ALIAS
    admin_put(token, "", realm)

    top_executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(STEP_UP_FLOW_ALIAS, safe='')}/executions")
    auth_executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(auth_flow, safe='')}/executions")
    loa1_executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(loa1_flow, safe='')}/executions")
    loa2_executions = admin_get(token, f"authentication/flows/{urllib.parse.quote(loa2_flow, safe='')}/executions")
    write_json(
        "wp-013-step-up-flow-config.json",
        {
            "generated_at": utc_timestamp(),
            "realm": KEYCLOAK_REALM,
            "original_browser_flow": original_browser_flow,
            "bound_browser_flow": STEP_UP_FLOW_ALIAS,
            "loa1_max_age_seconds": 36000,
            "loa2_max_age_seconds": 0,
            "privileged_authenticator": "otp",
            "executions": {
                STEP_UP_FLOW_ALIAS: top_executions,
                auth_flow: auth_executions,
                loa1_flow: loa1_executions,
                loa2_flow: loa2_executions,
            },
        },
    )
    pass_("Configured and bound Keycloak step-up browser flow")
    return original_browser_flow


def delete_old_wp013_otp_credentials(token, user_id):
    credentials = admin_get(token, f"users/{user_id}/credentials")
    for credential in credentials:
        if credential.get("type") == "otp" and str(credential.get("userLabel", "")).startswith("edrlab-wp013"):
            admin_delete(token, f"users/{user_id}/credentials/{credential['id']}")


def ensure_totp_credential(token, user_id, username):
    delete_old_wp013_otp_credentials(token, user_id)
    secret = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(20))
    payload = {
        "type": "otp",
        "userLabel": f"edrlab-wp013-{username}",
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
    _, status, _ = http_request(
        "POST",
        admin_url(f"users/{user_id}/credentials"),
        token=token,
        json_body=payload,
        expected=(201, 204, 404),
    )
    if status == 404:
        return configure_totp_required_action(token, user_id, username)
    credentials = admin_get(token, f"users/{user_id}/credentials")
    created = [
        {
            "id": credential.get("id"),
            "type": credential.get("type"),
            "userLabel": credential.get("userLabel"),
            "createdDate": credential.get("createdDate"),
        }
        for credential in credentials
        if credential.get("type") == "otp" and credential.get("userLabel") == f"edrlab-wp013-{username}"
    ]
    if not created:
        fail(f"OTP credential was not created for {username}")
    pass_(f"Created PoC OTP credential for {username}")
    return secret, created[0]


def extract_totp_secret(html_body):
    def normalize(candidate):
        if not candidate:
            return None
        candidate = html.unescape(candidate).strip()
        if "otpauth://" in candidate and "secret=" in candidate:
            parsed = urllib.parse.urlparse(candidate)
            candidate = urllib.parse.parse_qs(parsed.query).get("secret", [""])[0]
        candidate = "".join(ch for ch in candidate.upper() if ch.isalnum())
        candidate = candidate.rstrip("=")
        if len(candidate) >= 16 and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for ch in candidate):
            return candidate
        return None

    parser = LoginFormParser()
    parser.feed(html_body)
    for name in ("totpSecret", "secret"):
        value = normalize(parser.inputs.get(name))
        if value:
            return value
    for match in re.findall(r"otpauth://[^\"'<> ]+", html_body):
        value = normalize(match)
        if value:
            return value
    markers = [
        'id="kc-totp-secret-key"',
        "id='kc-totp-secret-key'",
        'class="kc-totp-secret-key"',
        "class='kc-totp-secret-key'",
    ]
    for marker in markers:
        index = html_body.find(marker)
        if index >= 0:
            start = html_body.find(">", index)
            end = html_body.find("<", start)
            if start >= 0 and end > start:
                candidate = normalize(html_body[start + 1 : end])
                if candidate:
                    return candidate
    return None


def configure_totp_required_action(token, user_id, username):
    user = admin_get(token, f"users/{user_id}")
    required_actions = list(dict.fromkeys((user.get("requiredActions") or []) + ["CONFIGURE_TOTP"]))
    user["requiredActions"] = required_actions
    admin_put(token, f"users/{user_id}", user)

    discovery, _, _ = http_request("GET", realm_url(".well-known/openid-configuration"))
    cookie_jar = http.cookiejar.CookieJar()
    opener = browser_opener(cookie_jar)
    state = random_urlsafe(24)
    nonce = random_urlsafe(24)
    verifier = random_urlsafe(64)
    challenge = pkce_challenge(verifier)
    url = auth_url(discovery, state, nonce, challenge)
    with opener.open(url, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")

    relax_localhost_secure_cookies(cookie_jar)
    login_form = parse_form(body)
    current_url, body, status = submit_form(
        opener,
        login_form.action,
        {
            "username": username,
            "password": POC_USER_PASSWORD,
            "credentialId": "",
            "login": "Sign In",
        },
    )
    if status >= 400:
        write_json(
            f"wp-013-{username}-configure-totp-login-error.json",
            {
                "status": status,
                "url": current_url,
                "cookie_summary": cookie_summary(cookie_jar),
                "body_excerpt": body[:1000],
            },
        )
        fail(f"CONFIGURE_TOTP login POST returned HTTP {status} for {username}")
    if current_url.startswith(BACKOFFICE_REDIRECT_URI):
        fail(f"CONFIGURE_TOTP required action was not shown for {username}")

    relax_localhost_secure_cookies(cookie_jar)
    setup_form = parse_form(body)
    secret = extract_totp_secret(body)
    if not secret:
        if "totpSecret" not in setup_form.inputs:
            write_json(
                f"wp-013-{username}-configure-totp-page-redacted.json",
                {
                    "url": current_url,
                    "input_names": sorted(setup_form.inputs.keys()),
                    "body_excerpt_redacted": redact_totp_html(body),
                },
            )
            fail(f"unable to extract or submit TOTP secret from CONFIGURE_TOTP page for {username}")
        secret = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(20))

    fields = dict(setup_form.inputs)
    fields.update(
        {
            "totp": totp(secret),
            "totpSecret": secret,
            "userLabel": f"edrlab-wp013-{username}",
            "submitAction": "Save",
        }
    )
    current_url, body, status = submit_form(opener, setup_form.action, fields)
    if status >= 400:
        fail(f"CONFIGURE_TOTP setup POST returned HTTP {status} for {username}")
    if not current_url.startswith(BACKOFFICE_REDIRECT_URI):
        write_json(
            f"wp-013-{username}-configure-totp-submit-redacted.json",
            {
                "status": status,
                "url": current_url,
                "input_names": sorted(setup_form.inputs.keys()),
                "body_excerpt_redacted": redact_totp_html(body),
            },
        )
        fail(f"CONFIGURE_TOTP did not complete for {username}")

    credentials = admin_get(token, f"users/{user_id}/credentials")
    created = [
        {
            "id": credential.get("id"),
            "type": credential.get("type"),
            "userLabel": credential.get("userLabel"),
            "createdDate": credential.get("createdDate"),
        }
        for credential in credentials
        if credential.get("type") == "otp"
    ]
    if not created:
        fail(f"CONFIGURE_TOTP did not create an OTP credential for {username}")
    pass_(f"Configured PoC OTP credential through Keycloak required action for {username}")
    return secret, created[-1]


def totp(secret, for_time=None):
    if for_time is None:
        for_time = int(time.time())
    key = secret.encode("utf-8")
    counter = int(for_time // 30).to_bytes(8, "big")
    digest = hmac.new(key, counter, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return f"{value % 1000000:06d}"


def wait_for_next_totp_window():
    sleep_seconds = 31 - (int(time.time()) % 30)
    time.sleep(sleep_seconds)


def parse_form(html):
    parser = LoginFormParser()
    parser.feed(html)
    if not parser.action:
        fail("unable to find Keycloak login form action")
    return parser


def cookie_summary(cookie_jar):
    return [
        {
            "name": cookie.name,
            "domain": cookie.domain,
            "path": cookie.path,
            "secure": cookie.secure,
            "has_value": bool(cookie.value),
        }
        for cookie in cookie_jar
    ]


def redact_totp_html(body):
    body = re.sub(r"(secret=)[^&\"'<> ]+", r"\1[REDACTED]", body)
    body = re.sub(r"\b[A-Za-z0-9]{16,}\b", "[REDACTED_SECRET]", body)
    return body[:12000]


def relax_localhost_secure_cookies(cookie_jar):
    for cookie in cookie_jar:
        if cookie.domain in ("localhost", "localhost.local", "127.0.0.1", "::1"):
            cookie.secure = False


def auth_url(discovery, state, nonce, challenge, acr_value=None):
    query = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": BACKOFFICE_REDIRECT_URI,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if acr_value:
        query["claims"] = json.dumps(
            {"id_token": {"acr": {"essential": True, "values": [acr_value]}}},
            separators=(",", ":"),
        )
    return f"{discovery['authorization_endpoint']}?{urllib.parse.urlencode(query)}"


def submit_form(opener, action, fields):
    data = form_encode(fields)
    request = urllib.request.Request(action, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.geturl(), body, response.getcode()
    except BackofficeRedirect as redirect:
        return redirect.url, "", 302
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.geturl(), body, exc.code


def query_param(url, name):
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get(name, [""])[0]


def exchange_code(discovery, code, verifier):
    body, _, _ = http_request(
        "POST",
        discovery["token_endpoint"],
        form_body={
            "grant_type": "authorization_code",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": BACKOFFICE_REDIRECT_URI,
            "code_verifier": verifier,
        },
    )
    return body


def jwt_parts(jwt):
    parts = jwt.split(".")
    if len(parts) != 3:
        fail("JWT should contain three parts")
    header = json.loads(b64url_decode(parts[0]).decode("utf-8"))
    claims = json.loads(b64url_decode(parts[1]).decode("utf-8"))
    signature = b64url_decode(parts[2])
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    return header, claims, signature, signing_input


def verify_rs256_signature(jwks, header, signature, signing_input):
    if header.get("alg") != "RS256":
        fail(f"unexpected ID token alg: {header.get('alg')}")
    kid = header.get("kid")
    key = next((item for item in jwks["keys"] if item.get("kid") == kid and item.get("kty") == "RSA"), None)
    if not key:
        fail("unable to find matching RSA JWK")
    n = int.from_bytes(b64url_decode(key["n"]), "big")
    e = int.from_bytes(b64url_decode(key["e"]), "big")
    sig_value = int.from_bytes(signature, "big")
    expected_len = (n.bit_length() + 7) // 8
    encoded = pow(sig_value, e, n).to_bytes(expected_len, "big")
    digest = hashlib.sha256(signing_input).digest()
    digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + digest
    expected = b"\x00\x01" + (b"\xff" * (expected_len - len(digest_info) - 3)) + b"\x00" + digest_info
    if encoded != expected:
        fail("ID token RS256 signature verification failed")


def sanitize_claims(claims):
    return {
        "iss": claims.get("iss"),
        "sub": claims.get("sub"),
        "aud": claims.get("aud"),
        "exp": claims.get("exp"),
        "iat": claims.get("iat"),
        "auth_time": claims.get("auth_time"),
        "nonce": claims.get("nonce"),
        "email": claims.get("email"),
        "email_verified": claims.get("email_verified"),
        "preferred_username": claims.get("preferred_username"),
        "azp": claims.get("azp"),
        "acr": claims.get("acr"),
        "amr": claims.get("amr") if isinstance(claims.get("amr"), list) else [],
        "sid_present": claims.get("sid") is not None,
    }


def validate_id_token(jwks, id_token, expected_nonce, expected_email, expected_acr=None):
    header, claims, signature, signing_input = jwt_parts(id_token)
    verify_rs256_signature(jwks, header, signature, signing_input)
    expected_issuer = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
    if claims.get("iss") != expected_issuer:
        fail(f"issuer mismatch: {claims.get('iss')}")
    aud = claims.get("aud")
    if aud != KEYCLOAK_CLIENT_ID and not (isinstance(aud, list) and KEYCLOAK_CLIENT_ID in aud):
        fail("ID token audience does not include client")
    if claims.get("nonce") != expected_nonce:
        fail("ID token nonce mismatch")
    if claims.get("email") != expected_email or claims.get("email_verified") is not True:
        fail("ID token email evidence mismatch")
    now = int(time.time())
    if not (claims.get("exp", 0) > now and claims.get("iat", now + 999) <= now + 300):
        fail("ID token time claims are outside expected bounds")
    if expected_acr and claims.get("acr") != expected_acr:
        fail(f"expected acr {expected_acr}, got {claims.get('acr')}")
    return header, claims


def authenticate(discovery, jwks, username, email, label, acr_value=None, otp_secret=None):
    cookie_jar = http.cookiejar.CookieJar()
    opener = browser_opener(cookie_jar)
    state = random_urlsafe(24)
    nonce = random_urlsafe(24)
    verifier = random_urlsafe(64)
    challenge = pkce_challenge(verifier)
    url = auth_url(discovery, state, nonce, challenge, acr_value=acr_value)
    with opener.open(url, timeout=30) as response:
        current_url = response.geturl()
        body = response.read().decode("utf-8", errors="replace")

    relax_localhost_secure_cookies(cookie_jar)
    if current_url.startswith(BACKOFFICE_REDIRECT_URI):
        callback = current_url
    else:
        login_form = parse_form(body)
        current_url, body, status = submit_form(
            opener,
            login_form.action,
            {
                "username": username,
                "password": POC_USER_PASSWORD,
                "credentialId": "",
                "login": "Sign In",
            },
        )
        if status >= 400:
            write_json(
                f"wp-013-{label}-login-error.json",
                {
                    "status": status,
                    "url": current_url,
                    "cookie_summary": cookie_summary(cookie_jar),
                    "body_excerpt": body[:1000],
                },
            )
            fail(f"{label} login POST returned HTTP {status}")
        if not current_url.startswith(BACKOFFICE_REDIRECT_URI):
            if otp_secret is None:
                fail(f"{label} was asked for another step but no OTP secret was provided")
            relax_localhost_secure_cookies(cookie_jar)
            otp_form = parse_form(body)
            current_url, body, status = submit_form(
                opener,
                otp_form.action,
                {
                    "otp": totp(otp_secret),
                    "credentialId": "",
                    "login": "Sign In",
                },
            )
            if status >= 400:
                fail(f"{label} OTP POST returned HTTP {status}")
        if not current_url.startswith(BACKOFFICE_REDIRECT_URI):
            write_json(f"wp-013-{label}-unexpected-login-page.json", {"url": current_url, "body_excerpt": body[:1000]})
            fail(f"{label} did not end at backoffice callback")
        callback = current_url

    code = query_param(callback, "code")
    returned_state = query_param(callback, "state")
    if not code:
        fail(f"{label} authorization response missing code")
    if returned_state != state:
        fail(f"{label} authorization response state mismatch")

    token_response = exchange_code(discovery, code, verifier)
    id_token = token_response.get("id_token")
    access_token = token_response.get("access_token")
    if not id_token or not access_token:
        fail(f"{label} token response missing ID token or access token")
    _, claims = validate_id_token(jwks, id_token, nonce, email, expected_acr=acr_value)
    token_evidence = {
        "token_type": token_response.get("token_type"),
        "expires_in": token_response.get("expires_in"),
        "scope": token_response.get("scope"),
        "has_access_token": bool(access_token),
        "has_refresh_token": bool(token_response.get("refresh_token")),
        "has_id_token": bool(id_token),
    }
    return claims, token_evidence


def activation_decision(account, claims, required_acr):
    reasons = []
    if account["email"] != claims.get("email"):
        reasons.append("email_mismatch")
    if claims.get("email_verified") is not True:
        reasons.append("email_not_verified")
    if account["linked_subject"] is not None:
        reasons.append("subject_already_linked")
    if claims.get("acr") != required_acr:
        reasons.append("privileged_acr_missing_or_low")
    if claims.get("sub") != account["candidate_subject"]:
        reasons.append("subject_mismatch")
    if reasons:
        return {
            "decision": "deny",
            "reason_code": reasons[0],
            "all_reason_codes": reasons,
            "mutates_keycloak": False,
            "activated_account": dict(account),
        }
    activated = dict(account)
    activated["lifecycle"] = "active"
    activated["linked_subject"] = claims["sub"]
    return {
        "decision": "allow",
        "reason_code": "verified_invitation_with_current_privileged_acr",
        "all_reason_codes": [],
        "mutates_keycloak": True,
        "activated_account": activated,
    }


def audit_record(event_id, correlation_id, actor_account_id, actor_subject, action, result, target_id, reason_code, claims):
    return {
        "event_id": event_id,
        "correlation_id": correlation_id,
        "timestamp": utc_timestamp(),
        "source_component": "edrlab-iam-control-plane-api-poc-fixture",
        "actor_account_id": actor_account_id,
        "actor_subject": actor_subject,
        "action": action,
        "result": result,
        "target_type": "backoffice_account",
        "target_id": target_id,
        "reason_code": reason_code,
        "authentication_evidence": {
            "iss": claims.get("iss"),
            "sub": claims.get("sub"),
            "acr": claims.get("acr"),
            "auth_time": claims.get("auth_time"),
            "email_verified": claims.get("email_verified"),
        },
    }


def main():
    write_json(
        "wp-013-event-window.json",
        {
            "generated_at": utc_timestamp(),
            "run_started_at_ms": RUN_STARTED_AT_MS,
            "event_window_started_at_ms": EVENT_WINDOW_STARTED_AT_MS,
        },
    )

    token = admin_token()
    discovery, _, _ = http_request("GET", realm_url(".well-known/openid-configuration"))
    jwks, _, _ = http_request("GET", discovery["jwks_uri"])
    admin_user_id = user_uuid(token, POC_ADMIN_USERNAME)
    super_admin_user_id = user_uuid(token, POC_SUPER_ADMIN_USERNAME)
    client_id = client_uuid(token)

    configure_acr_loa_mapping(token)
    original_browser_flow = configure_step_up_flow(token)
    admin_otp_secret, admin_otp = ensure_totp_credential(token, admin_user_id, POC_ADMIN_USERNAME)
    super_admin_otp_secret, super_admin_otp = ensure_totp_credential(token, super_admin_user_id, POC_SUPER_ADMIN_USERNAME)
    write_json(
        "wp-013-otp-credentials.json",
        {
            "generated_at": utc_timestamp(),
            "secret_values_written_to_evidence": False,
            "credentials": [
                {"username": POC_ADMIN_USERNAME, "user_id": admin_user_id, **admin_otp},
                {"username": POC_SUPER_ADMIN_USERNAME, "user_id": super_admin_user_id, **super_admin_otp},
            ],
        },
    )
    wait_for_next_totp_window()

    admin_normal_claims, admin_normal_token = authenticate(
        discovery, jwks, POC_ADMIN_USERNAME, POC_ADMIN_EMAIL, "admin-normal", acr_value=NORMAL_ACR
    )
    pass_("Normal admin OIDC login completed with non-privileged ACR")
    admin_privileged_claims, admin_privileged_token = authenticate(
        discovery,
        jwks,
        POC_ADMIN_USERNAME,
        POC_ADMIN_EMAIL,
        "admin-privileged",
        acr_value=PRIVILEGED_ACR,
        otp_secret=admin_otp_secret,
    )
    pass_("Privileged admin OIDC step-up login completed with privileged ACR")
    super_admin_privileged_claims, super_admin_privileged_token = authenticate(
        discovery,
        jwks,
        POC_SUPER_ADMIN_USERNAME,
        POC_SUPER_ADMIN_EMAIL,
        "super-admin-privileged",
        acr_value=PRIVILEGED_ACR,
        otp_secret=super_admin_otp_secret,
    )
    pass_("Privileged super-admin OIDC step-up login completed with privileged ACR")

    write_json("wp-013-admin-normal-token-response.json", admin_normal_token)
    write_json("wp-013-admin-privileged-token-response.json", admin_privileged_token)
    write_json("wp-013-super-admin-privileged-token-response.json", super_admin_privileged_token)
    write_json("wp-013-admin-normal-id-token-claims.json", sanitize_claims(admin_normal_claims))
    write_json("wp-013-admin-privileged-id-token-claims.json", sanitize_claims(admin_privileged_claims))
    write_json("wp-013-super-admin-privileged-id-token-claims.json", sanitize_claims(super_admin_privileged_claims))

    admin_account = {
        "account_id": "acct-wp013-admin",
        "account_type": "admin",
        "email": POC_ADMIN_EMAIL,
        "lifecycle": "invited",
        "linked_subject": None,
        "candidate_subject": admin_user_id,
    }
    super_admin_account = {
        "account_id": "acct-wp013-super-admin",
        "account_type": "super-admin",
        "email": POC_SUPER_ADMIN_EMAIL,
        "lifecycle": "invited",
        "linked_subject": None,
        "candidate_subject": super_admin_user_id,
    }

    decision_inputs = [
        (
            "admin-normal-acr-denied",
            admin_account,
            admin_normal_claims,
            "deny",
            "privileged_acr_missing_or_low",
        ),
        (
            "admin-privileged-acr-allowed",
            admin_account,
            admin_privileged_claims,
            "allow",
            "verified_invitation_with_current_privileged_acr",
        ),
        (
            "super-admin-privileged-acr-allowed",
            super_admin_account,
            super_admin_privileged_claims,
            "allow",
            "verified_invitation_with_current_privileged_acr",
        ),
        (
            "subject-mismatch-denied",
            super_admin_account,
            admin_privileged_claims,
            "deny",
            "email_mismatch",
        ),
    ]

    decisions = []
    audit = []
    for index, (scenario, account, claims, expected, expected_reason) in enumerate(decision_inputs, start=1):
        result = activation_decision(account, claims, PRIVILEGED_ACR)
        decision = {
            "scenario": scenario,
            "correlation_id": f"wp-013-{scenario}",
            "operation": "privileged_onboarding.activation",
            "expected_result": expected,
            "observed_result": result["decision"],
            "expected_reason_code": expected_reason,
            "reason_code": result["reason_code"],
            "actor_account_id": account["account_id"],
            "actor_subject": claims.get("sub"),
            "target_account_id": account["account_id"],
            "candidate_account_type": account["account_type"],
            "required_acr": PRIVILEGED_ACR,
            "observed_acr": claims.get("acr"),
            "keycloak_mutation_expected": expected == "allow",
            "keycloak_mutation_observed": result["mutates_keycloak"],
            "before": account,
            "after": result["activated_account"],
            "pass": result["decision"] == expected and result["reason_code"] == expected_reason,
        }
        decisions.append(decision)
        audit.append(
            audit_record(
                f"wp-013-audit-{index:02d}",
                decision["correlation_id"],
                decision["actor_account_id"],
                decision["actor_subject"],
                decision["operation"],
                decision["observed_result"],
                decision["target_account_id"],
                decision["reason_code"],
                claims,
            )
        )

    write_json("wp-013-control-plane-decisions.json", decisions)
    write_json("wp-013-local-audit.json", audit)

    passed = all(item["pass"] for item in decisions)
    checks = {
        "normal_admin_denied_without_privileged_acr": any(
            item["scenario"] == "admin-normal-acr-denied" and item["pass"] for item in decisions
        ),
        "admin_allowed_with_privileged_acr": any(
            item["scenario"] == "admin-privileged-acr-allowed" and item["pass"] for item in decisions
        ),
        "super_admin_allowed_with_privileged_acr": any(
            item["scenario"] == "super-admin-privileged-acr-allowed" and item["pass"] for item in decisions
        ),
        "subject_mismatch_denied": any(
            item["scenario"] == "subject-mismatch-denied" and item["pass"] for item in decisions
        ),
        "id_token_signature_validation_performed": True,
        "otp_secrets_written_to_evidence": False,
    }
    summary = {
        "generated_at": utc_timestamp(),
        "work_package": "WP-013",
        "scenario": "Keycloak ACR/LoA step-up evidence for privileged onboarding",
        "result": "pass" if passed else "fail",
        "evidence_dir": str(EVIDENCE_DIR),
        "keycloak_realm": KEYCLOAK_REALM,
        "keycloak_client_id": KEYCLOAK_CLIENT_ID,
        "keycloak_client_uuid": client_id,
        "original_browser_flow": original_browser_flow,
        "bound_step_up_flow": STEP_UP_FLOW_ALIAS,
        "required_privileged_acr": PRIVILEGED_ACR,
        "normal_acr": NORMAL_ACR,
        "checks": checks,
        "decision_count": len(decisions),
        "audit_record_count": len(audit),
        "production_gaps": [
            "PoC uses OTP as the scripted privileged factor; Phase 5 must decide whether production requires WebAuthn/passkeys or another phishing-resistant method.",
            "PoC writes local JSON audit evidence, not durable append-only audit storage.",
            "PoC validates IAM Control Plane API decision logic as a fixture, not production service code.",
            "PoC does not validate recovery, break-glass, device enrollment governance, service-to-service authentication, or monitoring.",
        ],
    }
    write_json("wp-013-summary.json", summary)
    evidence_md = "\n".join(
        [
            "# WP-013 IAM Control Plane Privileged Authentication Evidence",
            "",
            f"Generated at: {summary['generated_at']}",
            f"Result: {summary['result']}",
            f"Evidence directory: `{summary['evidence_dir']}`",
            "",
            "## Decision Matrix",
            "",
            "| Scenario | Expected | Observed | Reason | Pass |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| `{item['scenario']}` | `{item['expected_result']}` | `{item['observed_result']}` | `{item['reason_code']}` | `{str(item['pass']).lower()}` |"
                for item in decisions
            ],
            "",
            "## Evidence Files",
            "",
            "- `wp-013-acr-loa-map.json`",
            "- `wp-013-step-up-flow-config.json`",
            "- `wp-013-otp-credentials.json`",
            "- `wp-013-*-id-token-claims.json`",
            "- `wp-013-control-plane-decisions.json`",
            "- `wp-013-local-audit.json`",
            "- `wp-013-summary.json`",
        ]
    )
    (EVIDENCE_DIR / "wp-013-evidence.md").write_text(evidence_md + "\n", encoding="utf-8")

    if not passed:
        fail("WP-013 privileged authentication evidence failed")
    pass_("WP-013 privileged authentication evidence passed")
    print(f"Evidence directory: {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
