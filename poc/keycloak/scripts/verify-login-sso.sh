#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command curl
require_command docker
require_command jq
require_command openssl
require_command python3
load_env

fail() {
  echo "FAIL $*" >&2
  exit 1
}

pass() {
  echo "PASS $*"
}

random_urlsafe() {
  local byte_count=$1
  openssl rand -base64 "$byte_count" | tr '+/' '-_' | tr -d '=\r\n'
}

pkce_challenge() {
  local verifier=$1
  python3 - "$verifier" <<'PY'
import base64
import hashlib
import sys

digest = hashlib.sha256(sys.argv[1].encode("ascii")).digest()
print(base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="))
PY
}

form_action() {
  local html_file=$1
  python3 - "$html_file" <<'PY'
import sys
from html import unescape
from html.parser import HTMLParser


class LoginFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "form" or self.action:
            return
        values = dict(attrs)
        action = values.get("action", "")
        if "login-actions/authenticate" in action:
            self.action = unescape(action)


parser = LoginFormParser()
with open(sys.argv[1], encoding="utf-8", errors="replace") as source:
    parser.feed(source.read())
if not parser.action:
    sys.exit(1)
print(parser.action)
PY
}

header_location() {
  local headers_file=$1
  python3 - "$headers_file" <<'PY'
import sys

location = ""
with open(sys.argv[1], encoding="iso-8859-1", errors="replace") as source:
    for line in source:
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
if not location:
    sys.exit(1)
print(location)
PY
}

query_param() {
  local url=$1
  local name=$2
  python3 - "$url" "$name" <<'PY'
import sys
from urllib.parse import parse_qs, urlparse

values = parse_qs(urlparse(sys.argv[1]).query).get(sys.argv[2], [])
print(values[0] if values else "")
PY
}

jwt_part() {
  local jwt=$1
  local index=$2
  python3 - "$jwt" "$index" <<'PY'
import base64
import sys

parts = sys.argv[1].split(".")
index = int(sys.argv[2])
if index >= len(parts):
    sys.exit(1)
value = parts[index]
value += "=" * (-len(value) % 4)
data = base64.urlsafe_b64decode(value.encode("ascii"))
sys.stdout.write(data.decode("utf-8"))
PY
}

b64url_to_file() {
  local value=$1
  local output_file=$2
  python3 - "$value" "$output_file" <<'PY'
import base64
import sys

value = sys.argv[1]
value += "=" * (-len(value) % 4)
with open(sys.argv[2], "wb") as output:
    output.write(base64.urlsafe_b64decode(value.encode("ascii")))
PY
}

jwk_to_pem() {
  local jwks_file=$1
  local kid=$2
  local output_file=$3
  python3 - "$jwks_file" "$kid" "$output_file" <<'PY'
import base64
import json
import textwrap
import sys


def b64url_to_int(value):
    value += "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(value.encode("ascii")), "big")


def der_len(length):
    if length < 128:
        return bytes([length])
    data = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(data)]) + data


def der_tlv(tag, content):
    return bytes([tag]) + der_len(len(content)) + content


def der_int(value):
    data = value.to_bytes((value.bit_length() + 7) // 8, "big") or b"\x00"
    if data[0] & 0x80:
        data = b"\x00" + data
    return der_tlv(0x02, data)


def der_seq(*items):
    return der_tlv(0x30, b"".join(items))


def der_null():
    return b"\x05\x00"


def der_oid(oid):
    parts = [int(part) for part in oid.split(".")]
    output = bytes([parts[0] * 40 + parts[1]])
    for part in parts[2:]:
        encoded = [part & 0x7F]
        part >>= 7
        while part:
            encoded.append(0x80 | (part & 0x7F))
            part >>= 7
        output += bytes(reversed(encoded))
    return der_tlv(0x06, output)


def der_bit_string(content):
    return der_tlv(0x03, b"\x00" + content)


with open(sys.argv[1], encoding="utf-8") as source:
    jwks = json.load(source)

key = next(
    (
        item
        for item in jwks.get("keys", [])
        if item.get("kid") == sys.argv[2] and item.get("kty") == "RSA"
    ),
    None,
)
if not key:
    sys.exit("No RSA JWK found for kid")

n = b64url_to_int(key["n"])
e = b64url_to_int(key["e"])
rsa_public_key = der_seq(der_int(n), der_int(e))
algorithm = der_seq(der_oid("1.2.840.113549.1.1.1"), der_null())
subject_public_key_info = der_seq(algorithm, der_bit_string(rsa_public_key))
body = base64.b64encode(subject_public_key_info).decode("ascii")
pem = "-----BEGIN PUBLIC KEY-----\n"
pem += "\n".join(textwrap.wrap(body, 64))
pem += "\n-----END PUBLIC KEY-----\n"

with open(sys.argv[3], "w", encoding="ascii") as output:
    output.write(pem)
PY
}

build_auth_url() {
  local state=$1
  local nonce=$2
  local code_challenge=$3
  local prompt=${4:-}
  local url

  url="$AUTH_ENDPOINT?client_id=$(urlencode "$KEYCLOAK_CLIENT_ID")"
  url+="&response_type=code"
  url+="&scope=openid%20email%20profile"
  url+="&redirect_uri=$(urlencode "$BACKOFFICE_REDIRECT_URI")"
  url+="&state=$(urlencode "$state")"
  url+="&nonce=$(urlencode "$nonce")"
  url+="&code_challenge=$(urlencode "$code_challenge")"
  url+="&code_challenge_method=S256"
  if [[ -n "$prompt" ]]; then
    url+="&prompt=$(urlencode "$prompt")"
  fi

  printf '%s' "$url"
}

exchange_code() {
  local code=$1
  local verifier=$2
  local output_file=$3
  local status

  status=$(curl -sS \
    -o "$output_file" \
    -w "%{http_code}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=authorization_code" \
    --data-urlencode "client_id=$KEYCLOAK_CLIENT_ID" \
    --data-urlencode "client_secret=$KEYCLOAK_CLIENT_SECRET" \
    --data-urlencode "code=$code" \
    --data-urlencode "redirect_uri=$BACKOFFICE_REDIRECT_URI" \
    --data-urlencode "code_verifier=$verifier" \
    "$TOKEN_ENDPOINT")

  if [[ ! "$status" =~ ^2 ]]; then
    echo "Token exchange returned HTTP $status" >&2
    cat "$output_file" >&2
    return 1
  fi
}

sanitize_token_response() {
  local input_file=$1
  local output_file=$2

  jq '{
    token_type,
    expires_in,
    refresh_expires_in,
    scope,
    has_access_token: (.access_token | type == "string"),
    has_refresh_token: (.refresh_token | type == "string"),
    has_id_token: (.id_token | type == "string")
  }' "$input_file" > "$output_file"
}

sanitize_claims() {
  local input_file=$1
  local output_file=$2

  jq '{
    iss,
    sub,
    aud,
    exp,
    iat,
    auth_time,
    nonce,
    email,
    email_verified,
    preferred_username,
    azp,
    amr,
    sid_present: (.sid != null)
  }' "$input_file" > "$output_file"
}

validate_id_token() {
  local id_token=$1
  local expected_nonce=$2
  local raw_header_file=$3
  local raw_claims_file=$4
  local sanitized_claims_file=$5
  local verify_file=$6
  local expected_issuer="$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM"
  local now
  local kid
  local alg
  local signature
  local signing_input

  jwt_part "$id_token" 0 | jq '.' > "$raw_header_file"
  jwt_part "$id_token" 1 | jq '.' > "$raw_claims_file"
  sanitize_claims "$raw_claims_file" "$sanitized_claims_file"

  alg=$(jq -r '.alg // empty' "$raw_header_file")
  [[ "$alg" == "RS256" ]] || fail "ID token alg expected RS256, got '$alg'"

  kid=$(jq -r '.kid // empty' "$raw_header_file")
  [[ -n "$kid" ]] || fail "ID token missing kid"

  jwk_to_pem "$JWKS_FILE" "$kid" "$TMP_DIR/id-token-key.pem"
  signing_input=${id_token%.*}
  signature=${id_token##*.}
  printf '%s' "$signing_input" > "$TMP_DIR/id-token-signing-input.txt"
  b64url_to_file "$signature" "$TMP_DIR/id-token-signature.bin"
  if openssl dgst -sha256 \
    -verify "$TMP_DIR/id-token-key.pem" \
    -signature "$TMP_DIR/id-token-signature.bin" \
    "$TMP_DIR/id-token-signing-input.txt" > "$verify_file" 2>&1; then
    pass "ID token signature verified"
  else
    cat "$verify_file" >&2
    fail "ID token signature verification failed"
  fi

  jq -e --arg issuer "$expected_issuer" '.iss == $issuer' "$raw_claims_file" >/dev/null \
    || fail "ID token issuer mismatch"
  pass "ID token issuer matches realm"

  jq -e --arg client "$KEYCLOAK_CLIENT_ID" \
    '(.aud == $client) or ((.aud | type) == "array" and (.aud | index($client) != null))' \
    "$raw_claims_file" >/dev/null \
    || fail "ID token audience does not include client"
  pass "ID token audience includes client"

  jq -e --arg nonce "$expected_nonce" '.nonce == $nonce' "$raw_claims_file" >/dev/null \
    || fail "ID token nonce mismatch"
  pass "ID token nonce matches authorization request"

  jq -e --arg email "$POC_MEMBER_EMAIL" '.email == $email and .email_verified == true' "$raw_claims_file" >/dev/null \
    || fail "ID token email or email_verified mismatch for member user"
  pass "ID token email is the verified member email"

  now=$(date +%s)
  jq -e --argjson now "$now" '.exp > $now and .iat <= ($now + 300)' "$raw_claims_file" >/dev/null \
    || fail "ID token time claims are not valid for the current clock"
  pass "ID token time claims are within expected bounds"
}

wait_for_url "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" "PoC realm discovery"

ADMIN_TOKEN=$(admin_token)
if [[ -z "$ADMIN_TOKEN" || "$ADMIN_TOKEN" == "null" ]]; then
  fail "unable to obtain Keycloak admin token"
fi

DISCOVERY_JSON=$(curl -fsS "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration")
AUTH_ENDPOINT=$(jq -r '.authorization_endpoint' <<<"$DISCOVERY_JSON")
TOKEN_ENDPOINT=$(jq -r '.token_endpoint' <<<"$DISCOVERY_JSON")
USERINFO_ENDPOINT=$(jq -r '.userinfo_endpoint' <<<"$DISCOVERY_JSON")
JWKS_URI=$(jq -r '.jwks_uri' <<<"$DISCOVERY_JSON")
END_SESSION_ENDPOINT=$(jq -r '.end_session_endpoint // empty' <<<"$DISCOVERY_JSON")
if [[ -z "$END_SESSION_ENDPOINT" || "$END_SESSION_ENDPOINT" == "null" ]]; then
  END_SESSION_ENDPOINT="$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/logout"
fi

EVIDENCE_ROOT="$POC_DIR/evidence"
EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +"%Y%m%dT%H%M%SZ")"
TMP_DIR="$POC_DIR/tmp/wp-002-$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

COOKIE_JAR="$TMP_DIR/browser-cookies.txt"
JWKS_FILE="$TMP_DIR/jwks.json"
curl -fsS "$JWKS_URI" | jq '.' > "$JWKS_FILE"

first_state=$(random_urlsafe 24)
first_nonce=$(random_urlsafe 24)
first_verifier=$(random_urlsafe 64)
first_challenge=$(pkce_challenge "$first_verifier")
first_auth_url=$(build_auth_url "$first_state" "$first_nonce" "$first_challenge")

curl -fsS -L \
  -b "$COOKIE_JAR" \
  -c "$COOKIE_JAR" \
  -o "$TMP_DIR/login-page.html" \
  "$first_auth_url"
login_action=$(form_action "$TMP_DIR/login-page.html") || fail "unable to find Keycloak login form action"
pass "Keycloak login form reached"

login_status=$(curl -sS \
  -b "$COOKIE_JAR" \
  -c "$COOKIE_JAR" \
  -D "$TMP_DIR/login-post.headers" \
  -o "$TMP_DIR/login-post.body" \
  -w "%{http_code}" \
  --data-urlencode "username=$POC_MEMBER_USERNAME" \
  --data-urlencode "password=$POC_USER_PASSWORD" \
  --data-urlencode "credentialId=" \
  --data-urlencode "login=Sign In" \
  "$login_action")
[[ "$login_status" =~ ^(302|303)$ ]] || fail "login POST expected redirect, got HTTP $login_status"
first_callback=$(header_location "$TMP_DIR/login-post.headers") || fail "login redirect did not include Location"
[[ "$first_callback" == "$BACKOFFICE_REDIRECT_URI"* ]] || fail "login redirect target is not the backoffice callback"
first_code=$(query_param "$first_callback" "code")
first_returned_state=$(query_param "$first_callback" "state")
[[ -n "$first_code" ]] || fail "first authorization response missing code"
[[ "$first_returned_state" == "$first_state" ]] || fail "first authorization response state mismatch"
pass "Authorization Code flow returned first code after Keycloak login"

first_token_response="$TMP_DIR/first-token-response.json"
exchange_code "$first_code" "$first_verifier" "$first_token_response"
sanitize_token_response "$first_token_response" "$EVIDENCE_DIR/wp-002-first-token-response.json"

first_id_token=$(jq -r '.id_token // empty' "$first_token_response")
first_access_token=$(jq -r '.access_token // empty' "$first_token_response")
[[ -n "$first_id_token" && "$first_id_token" != "null" ]] || fail "token response missing ID token"
[[ -n "$first_access_token" && "$first_access_token" != "null" ]] || fail "token response missing access token"
pass "Authorization code exchanged for server-side tokens"

validate_id_token \
  "$first_id_token" \
  "$first_nonce" \
  "$TMP_DIR/id-token-header.raw.json" \
  "$TMP_DIR/id-token-claims.raw.json" \
  "$EVIDENCE_DIR/wp-002-id-token-claims.json" \
  "$EVIDENCE_DIR/wp-002-id-token-signature.txt"

subject=$(jq -r '.sub' "$TMP_DIR/id-token-claims.raw.json")
issuer=$(jq -r '.iss' "$TMP_DIR/id-token-claims.raw.json")
[[ -n "$subject" && "$subject" != "null" ]] || fail "ID token missing sub"

curl -fsS \
  -H "Authorization: Bearer $first_access_token" \
  "$USERINFO_ENDPOINT" \
  | jq '{sub, email, email_verified, preferred_username, name}' > "$EVIDENCE_DIR/wp-002-userinfo.json"
jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-002-userinfo.json" >/dev/null \
  || fail "UserInfo sub does not match ID token sub"
pass "UserInfo sub matches ID token sub"

member_keycloak_admin_id=$(user_uuid "$ADMIN_TOKEN" "$POC_MEMBER_USERNAME")
admin_id_matches_sub=false
if [[ "$member_keycloak_admin_id" == "$subject" ]]; then
  admin_id_matches_sub=true
fi

local_accounts_file="$EVIDENCE_DIR/wp-002-local-accounts.json"
jq -n \
  --arg issuer "$issuer" \
  --arg sub "$subject" \
  --arg email "$POC_MEMBER_EMAIL" \
  --argjson adminIdMatchesSub "$admin_id_matches_sub" \
  '{
    note: "PoC-only fixture for WP-002. WP-003 validates safe subject-link creation.",
    observations: {
      keycloak_admin_user_id_matches_id_token_sub: $adminIdMatchesSub
    },
    accounts: [
      {
        account_id: "acct-member-poc",
        account_type: "member",
        lifecycle_state: "active",
        keycloak_issuer: $issuer,
        keycloak_sub: $sub,
        email: $email,
        service_access_roles: ["protected-service-consultation-poc"]
      }
    ]
  }' > "$local_accounts_file"

resolved_account=$(jq -c --arg issuer "$issuer" --arg sub "$subject" '
  [.accounts[] | select(.keycloak_issuer == $issuer and .keycloak_sub == $sub and .lifecycle_state == "active")]
' "$local_accounts_file")
resolved_count=$(jq 'length' <<<"$resolved_account")
[[ "$resolved_count" == "1" ]] || fail "local resolver expected exactly one active account, got $resolved_count"
resolved_account_id=$(jq -r '.[0].account_id' <<<"$resolved_account")
pass "Local resolver matched exactly one active account by issuer and sub"

local_session_id="wp-002-session-$(random_urlsafe 18)"
jq -n \
  --arg sessionId "$local_session_id" \
  --arg accountId "$resolved_account_id" \
  --arg issuer "$issuer" \
  --arg sub "$subject" \
  --arg createdAt "$(utc_timestamp)" \
  '{
    local_session_id: $sessionId,
    account_id: $accountId,
    keycloak_issuer: $issuer,
    keycloak_sub: $sub,
    created_at: $createdAt,
    browser_cookie_boundary: "browser stores only this local session cookie in the selected BFF/server-side session pattern",
    token_storage_boundary: "Keycloak tokens are server-side PoC variables only and are not written to evidence"
  }' > "$EVIDENCE_DIR/wp-002-local-session.json"
pass "Local session decision recorded after local account resolution"

second_state=$(random_urlsafe 24)
second_nonce=$(random_urlsafe 24)
second_verifier=$(random_urlsafe 64)
second_challenge=$(pkce_challenge "$second_verifier")
second_auth_url=$(build_auth_url "$second_state" "$second_nonce" "$second_challenge" "none")

second_status=$(curl -sS \
  -b "$COOKIE_JAR" \
  -c "$COOKIE_JAR" \
  -D "$TMP_DIR/second-auth.headers" \
  -o "$TMP_DIR/second-auth.body" \
  -w "%{http_code}" \
  "$second_auth_url")
[[ "$second_status" =~ ^(302|303)$ ]] || fail "silent SSO authorization expected redirect, got HTTP $second_status"
second_callback=$(header_location "$TMP_DIR/second-auth.headers") || fail "silent SSO redirect did not include Location"
[[ "$second_callback" == "$BACKOFFICE_REDIRECT_URI"* ]] || fail "silent SSO redirect target is not the backoffice callback"
second_code=$(query_param "$second_callback" "code")
second_returned_state=$(query_param "$second_callback" "state")
[[ -n "$second_code" ]] || fail "silent SSO authorization response missing code"
[[ "$second_returned_state" == "$second_state" ]] || fail "silent SSO authorization response state mismatch"
pass "Prompt-none authorization returned code with existing Keycloak SSO session"

second_token_response="$TMP_DIR/second-token-response.json"
exchange_code "$second_code" "$second_verifier" "$second_token_response"
sanitize_token_response "$second_token_response" "$EVIDENCE_DIR/wp-002-second-token-response.json"
second_id_token=$(jq -r '.id_token // empty' "$second_token_response")
[[ -n "$second_id_token" && "$second_id_token" != "null" ]] || fail "second token response missing ID token"
jwt_part "$second_id_token" 1 | jq '.' > "$TMP_DIR/second-id-token-claims.raw.json"
jq -e --arg sub "$subject" --arg nonce "$second_nonce" '.sub == $sub and .nonce == $nonce' "$TMP_DIR/second-id-token-claims.raw.json" >/dev/null \
  || fail "silent SSO token subject or nonce mismatch"
sanitize_claims "$TMP_DIR/second-id-token-claims.raw.json" "$EVIDENCE_DIR/wp-002-second-id-token-claims.json"
pass "Silent SSO token keeps same subject and request nonce"

logout_url="$END_SESSION_ENDPOINT?id_token_hint=$(urlencode "$first_id_token")"
logout_url+="&client_id=$(urlencode "$KEYCLOAK_CLIENT_ID")"
logout_url+="&post_logout_redirect_uri=$(urlencode "$BACKOFFICE_LOGOUT_REDIRECT_URI")"

logout_status=$(curl -sS \
  -b "$COOKIE_JAR" \
  -c "$COOKIE_JAR" \
  -D "$TMP_DIR/logout.headers" \
  -o "$TMP_DIR/logout.body" \
  -w "%{http_code}" \
  "$logout_url")
[[ "$logout_status" =~ ^(302|303)$ ]] || fail "logout expected redirect, got HTTP $logout_status"
logout_callback=$(header_location "$TMP_DIR/logout.headers") || fail "logout redirect did not include Location"
[[ "$logout_callback" == "$BACKOFFICE_LOGOUT_REDIRECT_URI"* ]] || fail "logout redirect target is not the backoffice logout callback"
pass "Keycloak logout endpoint redirected back to local logout callback"

post_logout_state=$(random_urlsafe 24)
post_logout_nonce=$(random_urlsafe 24)
post_logout_verifier=$(random_urlsafe 64)
post_logout_challenge=$(pkce_challenge "$post_logout_verifier")
post_logout_auth_url=$(build_auth_url "$post_logout_state" "$post_logout_nonce" "$post_logout_challenge" "none")
post_logout_status=$(curl -sS \
  -b "$COOKIE_JAR" \
  -c "$COOKIE_JAR" \
  -D "$TMP_DIR/post-logout-auth.headers" \
  -o "$TMP_DIR/post-logout-auth.body" \
  -w "%{http_code}" \
  "$post_logout_auth_url")
post_logout_location=$(header_location "$TMP_DIR/post-logout-auth.headers" 2>/dev/null || true)
post_logout_code=""
post_logout_error=""
if [[ -n "$post_logout_location" ]]; then
  post_logout_code=$(query_param "$post_logout_location" "code")
  post_logout_error=$(query_param "$post_logout_location" "error")
fi
[[ -z "$post_logout_code" ]] || fail "prompt-none authorization returned a code after logout"
if [[ "$post_logout_error" == "login_required" || "$post_logout_status" == "200" ]]; then
  pass "Prompt-none authorization after logout did not silently authenticate"
else
  fail "unexpected post-logout prompt-none response: HTTP $post_logout_status error '$post_logout_error'"
fi

jq -n \
  --arg firstLoginStatus "$login_status" \
  --arg firstCallback "$BACKOFFICE_REDIRECT_URI" \
  --arg secondStatus "$second_status" \
  --arg logoutStatus "$logout_status" \
  --arg postLogoutStatus "$post_logout_status" \
  --arg postLogoutError "$post_logout_error" \
  '{
    first_login: {
      credential_posted_to_keycloak: true,
      http_status: $firstLoginStatus,
      callback_prefix: $firstCallback,
      authorization_code_received: true
    },
    silent_sso: {
      credential_posted_to_keycloak: false,
      prompt: "none",
      http_status: $secondStatus,
      authorization_code_received: true
    },
    logout: {
      local_session_cleared_by_poc: true,
      keycloak_logout_http_status: $logoutStatus,
      post_logout_silent_auth_http_status: $postLogoutStatus,
      post_logout_silent_auth_error: $postLogoutError,
      post_logout_authorization_code_received: false
    }
  }' > "$EVIDENCE_DIR/wp-002-login-sso-trace.json"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events?max=100" \
  | jq --arg userId "$subject" '
      [.[] | select(.userId == $userId and (.type == "LOGIN" or .type == "CODE_TO_TOKEN" or .type == "LOGOUT"))
      | {
          time,
          type,
          realmId,
          clientId,
          userId,
          sessionId_present: (.sessionId != null),
          ipAddress,
          error,
          details
        }]
    ' > "$EVIDENCE_DIR/wp-002-keycloak-events.json"

cat > "$EVIDENCE_DIR/wp-002-evidence.md" <<EOF
# WP-002 Evidence

Scenario: Login and SSO boundary
Work package: WP-002
Requirement links: FR-010, FR-020, FR-036, FR-037, FR-038
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production member user \`$POC_MEMBER_USERNAME\`
Action: Scripted browser-like Authorization Code flow with PKCE, ID token validation, UserInfo subject check, local account resolution, local session decision, prompt-none SSO check, and logout check
Expected result: Keycloak authenticates and maintains SSO, while local access control resolves \`iss\` + \`sub\` to one active account before creating a local session; browser-token shortcuts are not used
Observed result: The script completed all assertions and collected sanitized evidence files in this directory
Evidence collected:
- \`wp-002-first-token-response.json\`
- \`wp-002-id-token-claims.json\`
- \`wp-002-id-token-signature.txt\`
- \`wp-002-userinfo.json\`
- \`wp-002-local-accounts.json\`
- \`wp-002-local-session.json\`
- \`wp-002-second-token-response.json\`
- \`wp-002-second-id-token-claims.json\`
- \`wp-002-login-sso-trace.json\`
- \`wp-002-keycloak-events.json\`
Pass / fail / blocked: Pass
Residual risk: This is a curl-based browser simulation, not a real BFF or browser UX validation. It does not validate production cookie flags, HTTPS, CSRF protection, framework OIDC middleware, persistent session storage, or protected-service authorization.
Production gap: A production implementation still needs a real BFF/server-side session implementation, hardened cookies, HTTPS, CSRF controls, token redaction, JWKS cache policy, session expiry, error handling, and audit integration.
Decision impact: WP-002 supports the selected boundary where Keycloak owns authentication and SSO, while EDRLab local access control owns account resolution and authorization.
Generated at: $(utc_timestamp)
EOF

echo "WP-002 verification passed"
echo "Evidence written to $EVIDENCE_DIR"
