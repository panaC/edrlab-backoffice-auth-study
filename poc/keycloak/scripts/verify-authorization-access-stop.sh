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

epoch_millis() {
  python3 - <<'PY'
import time

print(int(time.time() * 1000))
PY
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
  local url

  url="$AUTH_ENDPOINT?client_id=$(urlencode "$KEYCLOAK_CLIENT_ID")"
  url+="&response_type=code"
  url+="&scope=openid%20email%20profile"
  url+="&redirect_uri=$(urlencode "$BACKOFFICE_REDIRECT_URI")"
  url+="&state=$(urlencode "$state")"
  url+="&nonce=$(urlencode "$nonce")"
  url+="&code_challenge=$(urlencode "$code_challenge")"
  url+="&code_challenge_method=S256"

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
    acr,
    amr,
    sid_present: (.sid != null)
  }' "$input_file" > "$output_file"
}

validate_id_token() {
  local id_token=$1
  local expected_nonce=$2
  local expected_email=$3
  local raw_header_file=$4
  local raw_claims_file=$5
  local sanitized_claims_file=$6
  local verify_file=$7
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
    pass "ID token signature verified for $expected_email"
  else
    cat "$verify_file" >&2
    fail "ID token signature verification failed for $expected_email"
  fi

  jq -e --arg issuer "$expected_issuer" '.iss == $issuer' "$raw_claims_file" >/dev/null \
    || fail "ID token issuer mismatch for $expected_email"
  pass "ID token issuer matches realm for $expected_email"

  jq -e --arg client "$KEYCLOAK_CLIENT_ID" \
    '(.aud == $client) or ((.aud | type) == "array" and (.aud | index($client) != null))' \
    "$raw_claims_file" >/dev/null \
    || fail "ID token audience does not include client for $expected_email"
  pass "ID token audience includes client for $expected_email"

  jq -e --arg nonce "$expected_nonce" '.nonce == $nonce' "$raw_claims_file" >/dev/null \
    || fail "ID token nonce mismatch for $expected_email"
  pass "ID token nonce matches authorization request for $expected_email"

  jq -e --arg email "$expected_email" '.email == $email and .email_verified == true' "$raw_claims_file" >/dev/null \
    || fail "ID token email or email_verified mismatch for $expected_email"
  pass "ID token email evidence is verified for $expected_email"

  now=$(date +%s)
  jq -e --argjson now "$now" '.exp > $now and .iat <= ($now + 300)' "$raw_claims_file" >/dev/null \
    || fail "ID token time claims are not valid for the current clock for $expected_email"
  pass "ID token time claims are within expected bounds for $expected_email"
}

authenticate_member_user() {
  local cookie_jar="$TMP_DIR/member-browser-cookies.txt"
  local state
  local nonce
  local verifier
  local challenge
  local auth_url
  local login_action
  local login_status
  local callback
  local code
  local returned_state
  local token_response
  local id_token
  local access_token
  local subject
  local issuer

  state=$(random_urlsafe 24)
  nonce=$(random_urlsafe 24)
  verifier=$(random_urlsafe 64)
  challenge=$(pkce_challenge "$verifier")
  auth_url=$(build_auth_url "$state" "$nonce" "$challenge")

  curl -fsS -L \
    -b "$cookie_jar" \
    -c "$cookie_jar" \
    -o "$TMP_DIR/member-login-page.html" \
    "$auth_url"
  login_action=$(form_action "$TMP_DIR/member-login-page.html") \
    || fail "unable to find Keycloak login form action for member identity"
  pass "Keycloak login form reached for member identity"

  login_status=$(curl -sS \
    -b "$cookie_jar" \
    -c "$cookie_jar" \
    -D "$TMP_DIR/member-login-post.headers" \
    -o "$TMP_DIR/member-login-post.body" \
    -w "%{http_code}" \
    --data-urlencode "username=$POC_MEMBER_USERNAME" \
    --data-urlencode "password=$POC_USER_PASSWORD" \
    --data-urlencode "credentialId=" \
    --data-urlencode "login=Sign In" \
    "$login_action")
  [[ "$login_status" =~ ^(302|303)$ ]] || fail "member login POST expected redirect, got HTTP $login_status"
  callback=$(header_location "$TMP_DIR/member-login-post.headers") \
    || fail "member login redirect did not include Location"
  [[ "$callback" == "$BACKOFFICE_REDIRECT_URI"* ]] || fail "member login redirect target is not the backoffice callback"
  code=$(query_param "$callback" "code")
  returned_state=$(query_param "$callback" "state")
  [[ -n "$code" ]] || fail "member authorization response missing code"
  [[ "$returned_state" == "$state" ]] || fail "member authorization response state mismatch"
  pass "Authorization Code flow returned code for member identity"

  token_response="$TMP_DIR/member-token-response.json"
  exchange_code "$code" "$verifier" "$token_response"
  sanitize_token_response "$token_response" "$EVIDENCE_DIR/wp-006-member-token-response.json"

  id_token=$(jq -r '.id_token // empty' "$token_response")
  access_token=$(jq -r '.access_token // empty' "$token_response")
  [[ -n "$id_token" && "$id_token" != "null" ]] || fail "member token response missing ID token"
  [[ -n "$access_token" && "$access_token" != "null" ]] || fail "member token response missing access token"
  pass "Authorization code exchanged for server-side tokens for member identity"

  validate_id_token \
    "$id_token" \
    "$nonce" \
    "$POC_MEMBER_EMAIL" \
    "$TMP_DIR/member-id-token-header.raw.json" \
    "$TMP_DIR/member-id-token-claims.raw.json" \
    "$EVIDENCE_DIR/wp-006-member-id-token-claims.json" \
    "$EVIDENCE_DIR/wp-006-member-id-token-signature.txt"

  subject=$(jq -r '.sub' "$TMP_DIR/member-id-token-claims.raw.json")
  issuer=$(jq -r '.iss' "$TMP_DIR/member-id-token-claims.raw.json")
  [[ -n "$subject" && "$subject" != "null" ]] || fail "member ID token missing sub"

  curl -fsS \
    -H "Authorization: Bearer $access_token" \
    "$USERINFO_ENDPOINT" \
    | jq '{sub, email, email_verified, preferred_username, name}' > "$EVIDENCE_DIR/wp-006-member-userinfo.json"
  jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-006-member-userinfo.json" >/dev/null \
    || fail "member UserInfo sub does not match ID token sub"
  pass "UserInfo sub matches ID token sub for member identity"

  jq -n \
    --arg keycloakUsername "$POC_MEMBER_USERNAME" \
    --arg email "$POC_MEMBER_EMAIL" \
    --arg issuer "$issuer" \
    --arg sub "$subject" \
    '{
      keycloak_username: $keycloakUsername,
      iss: $issuer,
      sub: $sub,
      email: $email,
      email_verified: true
    }' > "$TMP_DIR/member-authenticated-identity.json"
}

write_local_authorization_evidence() {
  local identity_file="$TMP_DIR/member-authenticated-identity.json"
  local inputs_file="$EVIDENCE_DIR/wp-006-local-authorization-inputs.json"
  local requests_file="$EVIDENCE_DIR/wp-006-authorization-check-requests.json"
  local responses_file="$EVIDENCE_DIR/wp-006-authorization-check-responses.json"
  local decisions_file="$EVIDENCE_DIR/wp-006-authorization-check-decisions.json"
  local transitions_file="$EVIDENCE_DIR/wp-006-local-state-transitions.json"
  local audit_file="$EVIDENCE_DIR/wp-006-local-audit.json"
  local summary_file="$EVIDENCE_DIR/wp-006-authorization-access-stop-summary.json"
  local generated_at

  generated_at=$(utc_timestamp)

  jq -n \
    --arg generatedAt "$generated_at" \
    --slurpfile identity "$identity_file" \
    '{
      note: "PoC-only local authorization/check fixtures for WP-006. This is not production middleware, a BFF, protected-service code, persistent storage, or audit persistence.",
      rule_under_test: "A protected service asks the local access-control side for a fresh authorization decision using trusted local account context. The decision is made from current local account state and current local service-access-role state, not from Keycloak roles, groups, or token claims.",
      authorization_contract: {
        endpoint: "POST /authorization/check",
        caller: "protected-service-poc-or-backoffice-bff-poc",
        required_request_context: [
          "correlation_id",
          "local_account_id",
          "keycloak_issuer",
          "keycloak_sub",
          "target protected service",
          "action"
        ],
        response_shape: {
          allow: "boolean",
          reason_code: "string",
          evaluated_local_state_version: "integer",
          positive_authorization_cache_used: "boolean"
        },
        cache_rule: "No positive authorization cache is allowed in the validation path; every scenario below is evaluated against current local state."
      },
      authenticated_identity: $identity[0],
      scenarios: [
        {
          scenario: "allow-active-member-with-service-role",
          group: "baseline-authorization",
          expected_result: "allow",
          expected_reason_code: "service_access_granted",
          local_state_version: 1,
          authorization_service_available: true,
          request: {
            correlation_id: "wp-006-allow-active-member-with-service-role",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "active",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "deny-unresolved-local-subject",
          group: "fail-closed",
          expected_result: "deny",
          expected_reason_code: "unresolved_local_subject",
          local_state_version: 1,
          authorization_service_available: true,
          request: {
            correlation_id: "wp-006-deny-unresolved-local-subject",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-missing",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: null,
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "deny-authorization-check-unavailable",
          group: "fail-closed",
          expected_result: "deny",
          expected_reason_code: "authorization_result_unavailable",
          local_state_version: 1,
          authorization_service_available: false,
          request: {
            correlation_id: "wp-006-deny-authorization-check-unavailable",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "active",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "deny-disabled-account",
          group: "baseline-denial",
          expected_result: "deny",
          expected_reason_code: "local_account_not_active",
          local_state_version: 1,
          authorization_service_available: true,
          request: {
            correlation_id: "wp-006-deny-disabled-account",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member-disabled",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member-disabled",
            account_type: "member",
            lifecycle_state: "disabled",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "deny-active-member-missing-service-role",
          group: "baseline-denial",
          expected_result: "deny",
          expected_reason_code: "missing_local_service_access_role",
          local_state_version: 1,
          authorization_service_available: true,
          request: {
            correlation_id: "wp-006-deny-active-member-missing-service-role",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member-without-role",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member-without-role",
            account_type: "member",
            lifecycle_state: "active",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: []
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "access-stop-after-account-disable",
          group: "access-stop",
          expected_result: "deny",
          expected_reason_code: "local_account_not_active",
          local_state_version: 2,
          authorization_service_available: true,
          prior_positive_authorization: {
            scenario: "allow-active-member-with-service-role",
            local_state_version: 1,
            observed_result: "allow"
          },
          state_change: {
            change_id: "wp-006-disable-member",
            state_version_before: 1,
            state_version_after: 2,
            operation: "disable active member account",
            applied_before_check: true
          },
          request: {
            correlation_id: "wp-006-access-stop-after-account-disable",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "disabled",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "access-stop-after-account-archive",
          group: "access-stop",
          expected_result: "deny",
          expected_reason_code: "local_account_not_active",
          local_state_version: 3,
          authorization_service_available: true,
          prior_positive_authorization: {
            scenario: "allow-active-member-with-service-role",
            local_state_version: 1,
            observed_result: "allow"
          },
          state_change: {
            change_id: "wp-006-archive-member",
            state_version_before: 1,
            state_version_after: 3,
            operation: "disable active member account, then archive the disabled account before the next protected-service check",
            applied_before_check: true
          },
          request: {
            correlation_id: "wp-006-access-stop-after-account-archive",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "archived",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "access-stop-after-member-role-removal",
          group: "access-stop",
          expected_result: "deny",
          expected_reason_code: "missing_local_service_access_role",
          local_state_version: 4,
          authorization_service_available: true,
          prior_positive_authorization: {
            scenario: "allow-active-member-with-service-role",
            local_state_version: 1,
            observed_result: "allow"
          },
          state_change: {
            change_id: "wp-006-remove-member-service-role",
            state_version_before: 1,
            state_version_after: 4,
            operation: "remove member service-access-role assignment",
            applied_before_check: true
          },
          request: {
            correlation_id: "wp-006-access-stop-after-member-role-removal",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "active",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: []
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "active",
              covers_services: ["catalog-service-poc"]
            }
          ]
        },
        {
          scenario: "access-stop-after-service-role-disable",
          group: "access-stop",
          expected_result: "deny",
          expected_reason_code: "service_access_role_not_active",
          local_state_version: 5,
          authorization_service_available: true,
          prior_positive_authorization: {
            scenario: "allow-active-member-with-service-role",
            local_state_version: 1,
            observed_result: "allow"
          },
          state_change: {
            change_id: "wp-006-disable-service-access-role",
            state_version_before: 1,
            state_version_after: 5,
            operation: "disable service-access-role catalog entry",
            applied_before_check: true
          },
          request: {
            correlation_id: "wp-006-access-stop-after-service-role-disable",
            method: "POST",
            path: "/authorization/check",
            source_component: "catalog-service-poc",
            requested_at: $generatedAt,
            actor: {
              local_account_id: "acct-wp006-member",
              keycloak_issuer: $identity[0].iss,
              keycloak_sub: $identity[0].sub
            },
            target: {
              service_id: "catalog-service-poc",
              action: "consult"
            }
          },
          local_account: {
            account_id: "acct-wp006-member",
            account_type: "member",
            lifecycle_state: "active",
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          },
          service_role_catalog: [
            {
              role_id: "protected-service-consultation-poc",
              lifecycle_state: "disabled",
              covers_services: ["catalog-service-poc"]
            }
          ]
        }
      ]
    }' > "$inputs_file"

  jq \
    --arg checkedAt "$(utc_timestamp)" \
    '
    def subject_matches($identity; $account; $request):
      ($account != null)
      and ($account.keycloak_issuer == $identity.iss)
      and ($account.keycloak_sub == $identity.sub)
      and ($account.account_id == $request.actor.local_account_id)
      and ($account.keycloak_issuer == $request.actor.keycloak_issuer)
      and ($account.keycloak_sub == $request.actor.keycloak_sub);

    def role_entries($catalog; $account; $service):
      [
        ($account.service_access_roles // [])[] as $roleId
        | $catalog[]?
        | select(.role_id == $roleId and ((.covers_services // []) | index($service) != null))
      ];

    def any_active_role_covers($catalog; $service):
      any($catalog[]?; .lifecycle_state == "active" and ((.covers_services // []) | index($service) != null));

    def member_has_active_service_access($catalog; $account; $service):
      any(role_entries($catalog; $account; $service)[]?; .lifecycle_state == "active");

    def inactive_assigned_role_covers($catalog; $account; $service):
      any(role_entries($catalog; $account; $service)[]?; .lifecycle_state != "active");

    def build_response($root; $scenario; $result; $reason; $httpStatus):
      {
        scenario: $scenario.scenario,
        group: $scenario.group,
        expected_result: $scenario.expected_result,
        observed_result: $result,
        expected_reason_code: $scenario.expected_reason_code,
        reason_code: $reason,
        pass: ($scenario.expected_result == $result and $scenario.expected_reason_code == $reason),
        checked_at: $checkedAt,
        authorization_check_request: $scenario.request,
        authorization_check_response: {
          http_status: $httpStatus,
          body: {
            allow: ($result == "allow"),
            reason_code: $reason,
            decision_source: "local-access-control-poc",
            evaluated_local_state_version: $scenario.local_state_version,
            positive_authorization_cache_used: false,
            no_positive_authorization_cache_allowed: true
          }
        },
        protected_service_effective_decision: $result,
        local_account: $scenario.local_account,
        service_role_catalog: $scenario.service_role_catalog,
        local_decision_authority: {
          account_type: ($scenario.local_account.account_type // null),
          lifecycle_state: ($scenario.local_account.lifecycle_state // null),
          service_access_roles: ($scenario.local_account.service_access_roles // []),
          service_role_catalog_lifecycle: ($scenario.service_role_catalog | map({role_id, lifecycle_state, covers_services}))
        },
        prior_positive_authorization: ($scenario.prior_positive_authorization // null),
        state_change: ($scenario.state_change // null),
        no_positive_cache_evidence: (
          if ($scenario.prior_positive_authorization // null) == null then
            {
              applies: false,
              positive_authorization_cache_used: false
            }
          else
            {
              applies: true,
              previous_result: $scenario.prior_positive_authorization.observed_result,
              previous_local_state_version: $scenario.prior_positive_authorization.local_state_version,
              fresh_local_state_version: $scenario.local_state_version,
              state_change_applied_before_check: ($scenario.state_change.applied_before_check == true),
              next_fresh_check_denied: ($result == "deny"),
              positive_authorization_cache_used: false,
              pass: (
                $scenario.prior_positive_authorization.observed_result == "allow"
                and $scenario.local_state_version > $scenario.prior_positive_authorization.local_state_version
                and ($scenario.state_change.applied_before_check == true)
                and $result == "deny"
              )
            }
          end
        ),
        keycloak_identity_used_for_resolution_only: {
          iss: $root.authenticated_identity.iss,
          sub: $root.authenticated_identity.sub,
          email: $root.authenticated_identity.email
        }
      };

    . as $root
    | $root.scenarios
    | map(
        . as $scenario
        | $root.authenticated_identity as $identity
        | ($scenario.local_account // null) as $account
        | $scenario.service_role_catalog as $catalog
        | $scenario.request.target.service_id as $service
        | if $scenario.authorization_service_available != true then
            build_response($root; $scenario; "deny"; "authorization_result_unavailable"; 503)
          elif (subject_matches($identity; $account; $scenario.request) | not) then
            build_response($root; $scenario; "deny"; "unresolved_local_subject"; 200)
          elif $account.lifecycle_state != "active" then
            build_response($root; $scenario; "deny"; "local_account_not_active"; 200)
          elif ($account.account_type == "admin" or $account.account_type == "super-admin") then
            if any_active_role_covers($catalog; $service) then
              build_response($root; $scenario; "allow"; "service_access_granted"; 200)
            else
              build_response($root; $scenario; "deny"; "no_active_service_role_covers_target"; 200)
            end
          elif $account.account_type == "member" then
            if member_has_active_service_access($catalog; $account; $service) then
              build_response($root; $scenario; "allow"; "service_access_granted"; 200)
            elif (($account.service_access_roles // []) | length) == 0 then
              build_response($root; $scenario; "deny"; "missing_local_service_access_role"; 200)
            elif inactive_assigned_role_covers($catalog; $account; $service) then
              build_response($root; $scenario; "deny"; "service_access_role_not_active"; 200)
            else
              build_response($root; $scenario; "deny"; "service_access_role_does_not_cover_service"; 200)
            end
          else
            build_response($root; $scenario; "deny"; "unsupported_account_type"; 200)
          end
      )
    ' "$inputs_file" > "$decisions_file"

  jq -e 'all(.[]; .pass == true)' "$decisions_file" >/dev/null \
    || fail "one or more authorization/check decisions did not match the expected result"
  pass "All WP-006 authorization/check decisions matched expected outcomes"

  local allowed_count
  local denied_count
  local access_stop_count
  allowed_count=$(jq '[.[] | select(.observed_result == "allow")] | length' "$decisions_file")
  denied_count=$(jq '[.[] | select(.observed_result == "deny")] | length' "$decisions_file")
  access_stop_count=$(jq '[.[] | select(.group == "access-stop")] | length' "$decisions_file")
  [[ "$allowed_count" == "1" ]] || fail "expected exactly one baseline allow, got $allowed_count"
  [[ "$denied_count" == "8" ]] || fail "expected eight deny decisions, got $denied_count"
  [[ "$access_stop_count" == "4" ]] || fail "expected four access-stop scenarios, got $access_stop_count"
  pass "Authorization/check allow, deny, inactive, missing-role, and access-stop scenarios were all exercised"

  jq -e '
    all(.[] | select(.group == "access-stop");
      .observed_result == "deny"
      and .no_positive_cache_evidence.applies == true
      and .no_positive_cache_evidence.pass == true
      and .authorization_check_response.body.positive_authorization_cache_used == false
    )
  ' "$decisions_file" >/dev/null \
    || fail "one or more access-stop scenarios did not prove next-fresh-check denial without a positive cache"
  pass "Access-stop scenarios denied on the next fresh check with no positive authorization cache"

  jq '[.[] | {scenario, request: .authorization_check_request}]' "$decisions_file" > "$requests_file"
  jq '[.[] | {
    scenario,
    response: .authorization_check_response,
    protected_service_effective_decision,
    reason_code,
    no_positive_cache_evidence
  }]' "$decisions_file" > "$responses_file"
  jq '[.[] | select(.state_change != null) | {
    scenario,
    prior_positive_authorization,
    state_change,
    resulting_local_state_version: .authorization_check_response.body.evaluated_local_state_version,
    observed_result,
    reason_code
  }]' "$decisions_file" > "$transitions_file"

  jq \
    --arg timestamp "$(utc_timestamp)" \
    '
    map(
      {
        event_id: ("wp-006-" + .scenario),
        correlation_id: .authorization_check_request.correlation_id,
        timestamp: $timestamp,
        source_component: "local-access-control-poc",
        actor_account_id: .authorization_check_request.actor.local_account_id,
        actor_keycloak_sub: .authorization_check_request.actor.keycloak_sub,
        action: "authorization_check",
        result: .observed_result,
        target_type: "protected_backend_service",
        target_id: .authorization_check_request.target.service_id,
        requested_action: .authorization_check_request.target.action,
        reason_code,
        local_state_version: .authorization_check_response.body.evaluated_local_state_version,
        positive_authorization_cache_used: .authorization_check_response.body.positive_authorization_cache_used,
        keycloak_event_reference: "supplemental; see wp-006-keycloak-events.json"
      }
    )
    ' "$decisions_file" > "$audit_file"

  jq -n \
    --arg generatedAt "$(utc_timestamp)" \
    --slurpfile decisions "$decisions_file" \
    '{
      generated_at: $generatedAt,
      work_package: "WP-006",
      result: (
        if (
          all($decisions[0][]; .pass == true)
          and all($decisions[0][] | select(.group == "access-stop"); .no_positive_cache_evidence.pass == true)
        ) then "pass" else "fail" end
      ),
      scenario_counts: {
        total: ($decisions[0] | length),
        allow: ($decisions[0] | map(select(.observed_result == "allow")) | length),
        deny: ($decisions[0] | map(select(.observed_result == "deny")) | length),
        access_stop: ($decisions[0] | map(select(.group == "access-stop")) | length)
      },
      access_stop_result: {
        next_fresh_check_denied_after_local_changes: all($decisions[0][] | select(.group == "access-stop"); .observed_result == "deny"),
        positive_authorization_cache_used: false,
        no_positive_cache_evidence_passed: all($decisions[0][] | select(.group == "access-stop"); .no_positive_cache_evidence.pass == true)
      },
      note: "Pass means the local authorization/check fixture allowed the active member with a current local role, denied fail-closed and non-authorized cases, and denied every next fresh check after local account or role state changed."
    }' > "$summary_file"
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

EVIDENCE_ROOT="$POC_DIR/evidence"
EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +"%Y%m%dT%H%M%SZ")"
TMP_DIR="$POC_DIR/tmp/wp-006-$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

JWKS_FILE="$TMP_DIR/jwks.json"
curl -fsS "$JWKS_URI" | jq '.' > "$JWKS_FILE"

run_started_at_ms=$(epoch_millis)
event_window_started_at_ms=$((run_started_at_ms - 5000))
jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --argjson runStartedAtMs "$run_started_at_ms" \
  --argjson eventWindowStartedAtMs "$event_window_started_at_ms" \
  --arg note "Keycloak event evidence is filtered to events at or after event_window_started_at_ms to avoid mixing prior PoC runs." \
  '{
    generated_at: $generatedAt,
    run_started_at_ms: $runStartedAtMs,
    event_window_started_at_ms: $eventWindowStartedAtMs,
    note: $note
  }' > "$EVIDENCE_DIR/wp-006-event-window.json"

authenticate_member_user
write_local_authorization_evidence

member_subject=$(jq -r '.sub' "$TMP_DIR/member-authenticated-identity.json")
api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events?max=100" \
  | jq \
      --arg subject "$member_subject" \
      --argjson eventWindowStartedAtMs "$event_window_started_at_ms" \
      '
      [.[] | select(
          .time >= $eventWindowStartedAtMs
          and .userId == $subject
          and (.type == "LOGIN" or .type == "CODE_TO_TOKEN")
        )
      | {
          time,
          type,
          realmId,
          clientId,
          userId,
          sessionId_present: (.sessionId != null),
          ipAddress,
          error,
          details: {
            auth_method: .details.auth_method,
            auth_type: .details.auth_type,
            response_type: .details.response_type,
            response_mode: .details.response_mode,
            grant_type: .details.grant_type,
            scope: .details.scope,
            client_auth_method: .details.client_auth_method,
            redirect_uri_present: (.details.redirect_uri != null),
            username_present: (.details.username != null),
            code_id_present: (.details.code_id != null),
            token_id_present: (.details.token_id != null),
            refresh_token_id_present: (.details.refresh_token_id != null)
          }
        }]
    ' > "$EVIDENCE_DIR/wp-006-keycloak-events.json"

for event_type in LOGIN CODE_TO_TOKEN; do
  event_count=$(jq \
    --arg subject "$member_subject" \
    --arg eventType "$event_type" \
    '[.[] | select(.userId == $subject and .type == $eventType)] | length' \
    "$EVIDENCE_DIR/wp-006-keycloak-events.json")
  [[ "$event_count" -ge 1 ]] \
    || fail "expected run-scoped Keycloak $event_type event for member subject $member_subject"
done
pass "Run-scoped Keycloak LOGIN and CODE_TO_TOKEN events collected for member subject"

cat > "$EVIDENCE_DIR/wp-006-evidence.md" <<EOF
# WP-006 Evidence

Scenario: Authorization and access stop
Work package: WP-006
Requirement links: FR-015, FR-016, FR-020, FR-021, FR-022, FR-032, FR-036, FR-038
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production member user \`$POC_MEMBER_USERNAME\`, and PoC-only local authorization/check fixtures
Action: Scripted Authorization Code flow with PKCE for the member identity, ID token validation, UserInfo subject check, then PoC-only local authorization/check evaluation for allow, deny, inactive account, missing role, fail-closed, and next-fresh-check access-stop cases
Expected result: Active linked member with an active covering local service-access role is allowed; unresolved identity, unavailable authorization result, inactive account, missing local role, account disablement, account archival, member role removal, and service-role disablement deny; every access-stop case evaluates the changed local state without using a positive authorization cache
Observed result: The script completed all assertions and recorded \`$(jq -r '.result' "$EVIDENCE_DIR/wp-006-authorization-access-stop-summary.json")\` in \`wp-006-authorization-access-stop-summary.json\`
Evidence collected:
- \`wp-006-member-token-response.json\`
- \`wp-006-member-id-token-claims.json\`
- \`wp-006-member-id-token-signature.txt\`
- \`wp-006-member-userinfo.json\`
- \`wp-006-local-authorization-inputs.json\`
- \`wp-006-authorization-check-requests.json\`
- \`wp-006-authorization-check-responses.json\`
- \`wp-006-authorization-check-decisions.json\`
- \`wp-006-local-state-transitions.json\`
- \`wp-006-local-audit.json\`
- \`wp-006-authorization-access-stop-summary.json\`
- \`wp-006-event-window.json\`
- \`wp-006-keycloak-events.json\`
Pass / fail / blocked: $(jq -r '.result' "$EVIDENCE_DIR/wp-006-authorization-access-stop-summary.json")
Residual risk: The local authorization/check evaluator is fixture-based PoC evidence, not production middleware, BFF code, protected-service code, persistent storage, distributed cache behavior, or audit persistence.
Production gap: A production path still needs a real local account store, transactionally updated service-access-role state, protected-service or BFF integration, dependency-failure handling, audit persistence, and automated tests that enforce fresh local checks or explicitly reviewed cache behavior.
Decision impact: WP-006 supports the accepted Phase 4 access-stop target: Keycloak authenticates the subject, while local access-control makes current-state protected-service decisions and denies on the next fresh check after local account or role changes.
Generated at: $(utc_timestamp)
EOF

echo "WP-006 verification passed"
echo "Evidence written to $EVIDENCE_DIR"
