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
  sanitize_token_response "$token_response" "$EVIDENCE_DIR/wp-007-member-token-response.json"

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
    "$EVIDENCE_DIR/wp-007-member-id-token-claims.json" \
    "$EVIDENCE_DIR/wp-007-member-id-token-signature.txt"

  subject=$(jq -r '.sub' "$TMP_DIR/member-id-token-claims.raw.json")
  issuer=$(jq -r '.iss' "$TMP_DIR/member-id-token-claims.raw.json")
  [[ -n "$subject" && "$subject" != "null" ]] || fail "member ID token missing sub"

  curl -fsS \
    -H "Authorization: Bearer $access_token" \
    "$USERINFO_ENDPOINT" \
    | jq '{sub, email, email_verified, preferred_username, name}' > "$EVIDENCE_DIR/wp-007-member-userinfo.json"
  jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-007-member-userinfo.json" >/dev/null \
    || fail "member UserInfo sub does not match ID token sub"
  pass "UserInfo sub matches ID token sub for member identity"

  jq -n \
    --arg keycloakUsername "$POC_MEMBER_USERNAME" \
    --arg email "$POC_MEMBER_EMAIL" \
    --arg issuer "$issuer" \
    --arg sub "$subject" \
    '{
      keycloak_username: $keycloakUsername,
      local_account_id: "acct-wp007-member",
      account_type: "member",
      lifecycle_state: "active",
      iss: $issuer,
      sub: $sub,
      email: $email,
      email_verified: true
    }' > "$TMP_DIR/member-authenticated-identity.json"
}

write_keycloak_admin_event_probe() {
  local member_user_id
  local member_user_file="$TMP_DIR/member-user-before-admin-probe.json"
  local admin_update_payload
  local generated_at

  generated_at=$(utc_timestamp)
  member_user_id=$(user_uuid "$ADMIN_TOKEN" "$POC_MEMBER_USERNAME")
  [[ -n "$member_user_id" ]] || fail "member user not found for admin event probe"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$member_user_id" > "$member_user_file"
  admin_update_payload=$(jq -c \
    --arg generatedAt "$generated_at" \
    '{
      username,
      enabled,
      email,
      emailVerified,
      firstName,
      lastName,
      requiredActions: (.requiredActions // []),
      attributes: ((.attributes // {}) + {wp_007_admin_event_probe: [$generatedAt]})
    }' "$member_user_file")

  api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$member_user_id" "$admin_update_payload" '^(200|204)$' >/dev/null
  pass "Keycloak admin event probe updated non-production member user attribute"

  jq -n \
    --arg generatedAt "$generated_at" \
    --arg userId "$member_user_id" \
    --arg username "$POC_MEMBER_USERNAME" \
    '{
      generated_at: $generatedAt,
      note: "PoC-only Keycloak admin-event probe. The update touches a non-authoritative user attribute in the throwaway realm so the script can collect a run-scoped Keycloak admin event as supplemental evidence.",
      keycloak_user_id: $userId,
      keycloak_username: $username,
      operation: "PUT /admin/realms/{realm}/users/{user-id}",
      changed_attribute: "wp_007_admin_event_probe",
      expected_admin_event: {
        operationType: "UPDATE",
        resourcePath_contains: $userId
      }
    }' > "$EVIDENCE_DIR/wp-007-keycloak-admin-event-probe.json"
}

collect_keycloak_event_evidence() {
  local member_subject
  local member_user_id
  local user_event_count
  local login_count
  local token_count
  local admin_event_count

  member_subject=$(jq -r '.sub' "$TMP_DIR/member-authenticated-identity.json")
  member_user_id=$(jq -r '.keycloak_user_id' "$EVIDENCE_DIR/wp-007-keycloak-admin-event-probe.json")

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
      ' > "$EVIDENCE_DIR/wp-007-keycloak-events.json"

  user_event_count=$(jq 'length' "$EVIDENCE_DIR/wp-007-keycloak-events.json")
  login_count=$(jq '[.[] | select(.type == "LOGIN")] | length' "$EVIDENCE_DIR/wp-007-keycloak-events.json")
  token_count=$(jq '[.[] | select(.type == "CODE_TO_TOKEN")] | length' "$EVIDENCE_DIR/wp-007-keycloak-events.json")
  [[ "$user_event_count" -ge 2 ]] || fail "expected run-scoped Keycloak user events for member subject"
  [[ "$login_count" -ge 1 ]] || fail "expected run-scoped Keycloak LOGIN event for member subject"
  [[ "$token_count" -ge 1 ]] || fail "expected run-scoped Keycloak CODE_TO_TOKEN event for member subject"
  pass "Run-scoped Keycloak LOGIN and CODE_TO_TOKEN events collected for member subject"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/admin-events?max=100" \
    | jq \
        --arg userId "$member_user_id" \
        --argjson eventWindowStartedAtMs "$event_window_started_at_ms" \
        '
        [.[] | select(
            .time >= $eventWindowStartedAtMs
            and ((.resourcePath // "") | contains($userId))
          )
        | {
            time,
            realmId,
            operationType,
            resourceType,
            resourcePath,
            representation_present: (.representation != null),
            error,
            authDetails: {
              realmId: .authDetails.realmId,
              clientId: .authDetails.clientId,
              userId_present: (.authDetails.userId != null),
              ipAddress: .authDetails.ipAddress
            }
          }]
      ' > "$EVIDENCE_DIR/wp-007-keycloak-admin-events.json"

  admin_event_count=$(jq '[.[] | select(.operationType == "UPDATE")] | length' "$EVIDENCE_DIR/wp-007-keycloak-admin-events.json")
  [[ "$admin_event_count" -ge 1 ]] || fail "expected run-scoped Keycloak admin UPDATE event for probe"
  pass "Run-scoped Keycloak admin UPDATE event collected for probe"
}

write_local_audit_correlation_evidence() {
  local identity_file="$TMP_DIR/member-authenticated-identity.json"
  local local_audit_file="$EVIDENCE_DIR/wp-007-local-audit.json"
  local correlation_file="$EVIDENCE_DIR/wp-007-audit-correlation-map.json"
  local gaps_file="$EVIDENCE_DIR/wp-007-audit-gaps.json"
  local summary_file="$EVIDENCE_DIR/wp-007-audit-correlation-summary.json"
  local generated_at
  local required_field
  local local_record_count
  local local_only_count
  local user_event_count
  local admin_event_count

  generated_at=$(utc_timestamp)

  jq -n \
    --arg generatedAt "$generated_at" \
    --slurpfile identity "$identity_file" \
    '[
      {
        event_id: "wp-007-authenticated-subject-resolved",
        correlation_id: "wp-007-auth-session",
        timestamp: $generatedAt,
        source_component: "local-access-control-poc",
        actor_account_id: $identity[0].local_account_id,
        actor_keycloak_sub: $identity[0].sub,
        action: "authenticated_subject_resolved",
        result: "allow",
        target_type: "backoffice_session",
        target_id: "local-session-wp007-member",
        reason_code: "linked_active_account_resolved",
        keycloak_event_reference: {
          relationship: "supplemental_authentication_evidence",
          file: "wp-007-keycloak-events.json",
          expected_types: ["LOGIN", "CODE_TO_TOKEN"]
        }
      },
      {
        event_id: "wp-007-authorization-check-allow",
        correlation_id: "wp-007-protected-service-allow",
        timestamp: $generatedAt,
        source_component: "local-access-control-poc",
        actor_account_id: $identity[0].local_account_id,
        actor_keycloak_sub: $identity[0].sub,
        action: "authorization_check",
        result: "allow",
        target_type: "protected_backend_service",
        target_id: "catalog-service-poc",
        requested_action: "consult",
        reason_code: "service_access_granted",
        keycloak_event_reference: {
          relationship: "same_authenticated_subject_only",
          file: "wp-007-keycloak-events.json",
          note: "Keycloak authenticates the subject but does not decide this local protected-service authorization result."
        }
      },
      {
        event_id: "wp-007-authorization-check-deny",
        correlation_id: "wp-007-protected-service-deny",
        timestamp: $generatedAt,
        source_component: "local-access-control-poc",
        actor_account_id: $identity[0].local_account_id,
        actor_keycloak_sub: $identity[0].sub,
        action: "authorization_check",
        result: "deny",
        target_type: "protected_backend_service",
        target_id: "catalog-service-poc",
        requested_action: "consult",
        reason_code: "missing_local_service_access_role",
        keycloak_event_reference: {
          relationship: "local_only_expected_gap",
          file: "wp-007-keycloak-events.json",
          note: "No Keycloak event is expected to prove the local role-denial reason."
        }
      },
      {
        event_id: "wp-007-audit-read-denied",
        correlation_id: "wp-007-audit-read-denied",
        timestamp: $generatedAt,
        source_component: "local-access-control-poc",
        actor_account_id: $identity[0].local_account_id,
        actor_keycloak_sub: $identity[0].sub,
        action: "audit_read",
        result: "deny",
        target_type: "audit_record",
        target_id: "audit-log-poc",
        reason_code: "local_account_type_not_authorized",
        keycloak_event_reference: {
          relationship: "local_only_expected_gap",
          file: "wp-007-keycloak-events.json",
          note: "No Keycloak event is expected to prove the local audit-read authorization decision."
        }
      }
    ]' > "$local_audit_file"

  for required_field in \
    event_id \
    correlation_id \
    timestamp \
    source_component \
    actor_account_id \
    actor_keycloak_sub \
    action \
    result \
    target_type \
    target_id \
    reason_code; do
    jq -e --arg field "$required_field" \
      'all(.[]; has($field) and (.[$field] != null) and ((.[$field] | tostring) | length > 0))' \
      "$local_audit_file" >/dev/null \
      || fail "local audit records are missing required field: $required_field"
  done
  pass "Local audit examples contain the accepted minimum audit schema fields"

  jq -e 'all(.[]; (.correlation_id | startswith("wp-007-")))' "$local_audit_file" >/dev/null \
    || fail "local audit records do not all carry WP-007 correlation IDs"
  pass "Local audit examples carry correlation IDs"

  local_record_count=$(jq 'length' "$local_audit_file")
  [[ "$local_record_count" == "4" ]] || fail "expected four local audit examples, got $local_record_count"

  jq -n \
    --arg generatedAt "$generated_at" \
    --slurpfile identity "$identity_file" \
    --slurpfile localAudit "$local_audit_file" \
    --slurpfile keycloakEvents "$EVIDENCE_DIR/wp-007-keycloak-events.json" \
    --slurpfile keycloakAdminEvents "$EVIDENCE_DIR/wp-007-keycloak-admin-events.json" \
    '{
      generated_at: $generatedAt,
      work_package: "WP-007",
      rule_under_test: "Local audit is authoritative for EDRLab account, authorization, and audit-read decisions. Keycloak events are supplemental authentication or technical-administration evidence.",
      authenticated_identity: $identity[0],
      local_audit_authority: {
        authoritative_record_file: "wp-007-local-audit.json",
        required_schema_fields: [
          "event_id",
          "correlation_id",
          "timestamp",
          "source_component",
          "actor_account_id",
          "actor_keycloak_sub",
          "action",
          "result",
          "target_type",
          "target_id",
          "reason_code"
        ],
        pass: true
      },
      keycloak_supplemental_evidence: {
        user_event_file: "wp-007-keycloak-events.json",
        user_event_types_observed: ($keycloakEvents[0] | map(.type) | unique),
        admin_event_file: "wp-007-keycloak-admin-events.json",
        admin_event_operations_observed: ($keycloakAdminEvents[0] | map(.operationType) | unique),
        admin_event_probe_file: "wp-007-keycloak-admin-event-probe.json"
      },
      correlations: [
        {
          correlation_id: "wp-007-auth-session",
          local_event_id: "wp-007-authenticated-subject-resolved",
          matching_keycloak_user_event_types: ($keycloakEvents[0] | map(.type) | unique),
          keycloak_relationship: "supplemental authentication evidence",
          local_audit_remains_authoritative: true
        },
        {
          correlation_id: "wp-007-protected-service-allow",
          local_event_id: "wp-007-authorization-check-allow",
          matching_keycloak_user_event_types: ($keycloakEvents[0] | map(.type) | unique),
          keycloak_relationship: "same authenticated subject, not the authorization decision source",
          local_audit_remains_authoritative: true
        },
        {
          correlation_id: "wp-007-protected-service-deny",
          local_event_id: "wp-007-authorization-check-deny",
          matching_keycloak_user_event_types: ($keycloakEvents[0] | map(.type) | unique),
          keycloak_relationship: "authentication context only; local role-denial reason is local-only",
          local_audit_remains_authoritative: true
        },
        {
          correlation_id: "wp-007-audit-read-denied",
          local_event_id: "wp-007-audit-read-denied",
          matching_keycloak_user_event_types: ($keycloakEvents[0] | map(.type) | unique),
          keycloak_relationship: "authentication context only; local audit-read denial is local-only",
          local_audit_remains_authoritative: true
        },
        {
          correlation_id: "wp-007-keycloak-admin-event-probe",
          local_event_id: null,
          matching_keycloak_admin_event_operations: ($keycloakAdminEvents[0] | map(.operationType) | unique),
          keycloak_relationship: "technical Keycloak administration event, not an EDRLab local authorization or audit authority event",
          local_audit_remains_authoritative: true
        }
      ]
    }' > "$correlation_file"

  jq -n \
    --arg generatedAt "$generated_at" \
    '[
      {
        gap_id: "wp-007-gap-local-authorization-decisions",
        generated_at: $generatedAt,
        expected: true,
        description: "Keycloak user events prove authentication activity, but they do not prove local protected-service allow or deny reasons.",
        local_authoritative_files: ["wp-007-local-audit.json", "wp-007-audit-correlation-map.json"],
        supplemental_keycloak_files: ["wp-007-keycloak-events.json"]
      },
      {
        gap_id: "wp-007-gap-local-audit-read-decisions",
        generated_at: $generatedAt,
        expected: true,
        description: "Keycloak events do not prove whether a local EDRLab account is allowed to read or export EDRLab audit records.",
        local_authoritative_files: ["wp-007-local-audit.json"],
        supplemental_keycloak_files: ["wp-007-keycloak-events.json"]
      },
      {
        gap_id: "wp-007-gap-persistence-integrity-retention",
        generated_at: $generatedAt,
        expected: true,
        description: "This PoC writes JSON evidence only. It does not prove production append-only persistence, tamper resistance, retention, export, backup, or restore behavior.",
        local_authoritative_files: ["wp-007-local-audit.json"],
        supplemental_keycloak_files: ["wp-007-keycloak-admin-events.json"]
      },
      {
        gap_id: "wp-007-gap-keycloak-technical-admin-scope",
        generated_at: $generatedAt,
        expected: true,
        description: "The Keycloak admin UPDATE event proves provider-side technical administration event capture for the probe, not EDRLab account lifecycle, service-access-role, protected-service authorization, or audit-read authority.",
        local_authoritative_files: ["wp-007-audit-correlation-map.json"],
        supplemental_keycloak_files: ["wp-007-keycloak-admin-events.json"]
      }
    ]' > "$gaps_file"

  local_only_count=$(jq '[.[] | select(.keycloak_event_reference.relationship == "local_only_expected_gap")] | length' "$local_audit_file")
  user_event_count=$(jq 'length' "$EVIDENCE_DIR/wp-007-keycloak-events.json")
  admin_event_count=$(jq 'length' "$EVIDENCE_DIR/wp-007-keycloak-admin-events.json")

  jq -n \
    --arg generatedAt "$generated_at" \
    --argjson localRecordCount "$local_record_count" \
    --argjson localOnlyCount "$local_only_count" \
    --argjson userEventCount "$user_event_count" \
    --argjson adminEventCount "$admin_event_count" \
    --slurpfile gaps "$gaps_file" \
    '{
      generated_at: $generatedAt,
      work_package: "WP-007",
      result: (
        if $localRecordCount == 4
          and $localOnlyCount >= 2
          and $userEventCount >= 2
          and $adminEventCount >= 1
          and (($gaps[0] | length) >= 4)
        then "pass" else "fail" end
      ),
      local_audit: {
        record_count: $localRecordCount,
        records_with_local_only_expected_gap: $localOnlyCount,
        minimum_schema_verified: true,
        correlation_ids_verified: true
      },
      keycloak_supplemental_evidence: {
        user_event_count: $userEventCount,
        admin_event_count: $adminEventCount
      },
      audit_gaps: {
        expected_gap_count: ($gaps[0] | length),
        persistence_integrity_retention_not_proven: true
      },
      note: "Pass means WP-007 produced minimum-schema local audit examples, correlated them with run-scoped Keycloak authentication and admin-event evidence, and recorded expected gaps where Keycloak cannot prove local EDRLab authorization or audit decisions."
    }' > "$summary_file"

  jq -e '.result == "pass"' "$summary_file" >/dev/null \
    || fail "WP-007 audit-correlation summary did not pass"
  pass "WP-007 audit-correlation summary passed"
}

wait_for_url "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" "PoC realm discovery"

ADMIN_TOKEN=$(admin_token)
if [[ -z "$ADMIN_TOKEN" || "$ADMIN_TOKEN" == "null" ]]; then
  fail "unable to obtain Keycloak admin token"
fi

events_config=$(api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events/config")
jq -e '.eventsEnabled == true and .adminEventsEnabled == true and .adminEventsDetailsEnabled == true' <<<"$events_config" >/dev/null \
  || fail "Keycloak user/admin events are not enabled as required for WP-007"
pass "Keycloak user and admin events are enabled"

DISCOVERY_JSON=$(curl -fsS "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration")
AUTH_ENDPOINT=$(jq -r '.authorization_endpoint' <<<"$DISCOVERY_JSON")
TOKEN_ENDPOINT=$(jq -r '.token_endpoint' <<<"$DISCOVERY_JSON")
USERINFO_ENDPOINT=$(jq -r '.userinfo_endpoint' <<<"$DISCOVERY_JSON")
JWKS_URI=$(jq -r '.jwks_uri' <<<"$DISCOVERY_JSON")

EVIDENCE_ROOT="$POC_DIR/evidence"
EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +"%Y%m%dT%H%M%SZ")"
TMP_DIR="$POC_DIR/tmp/wp-007-$(date -u +"%Y%m%dT%H%M%SZ")"
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
  }' > "$EVIDENCE_DIR/wp-007-event-window.json"

authenticate_member_user
write_keycloak_admin_event_probe
collect_keycloak_event_evidence
write_local_audit_correlation_evidence

cat > "$EVIDENCE_DIR/wp-007-evidence.md" <<EOF
# WP-007 Evidence

Scenario: Audit correlation
Work package: WP-007
Requirement links: FR-027, FR-028, FR-035, FR-036, FR-038
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production member user \`$POC_MEMBER_USERNAME\`, Keycloak user/admin events enabled, and PoC-only local audit fixtures
Action: Scripted Authorization Code flow with PKCE for the member identity, ID token validation, UserInfo subject check, PoC-only Keycloak admin-event probe, Keycloak event collection, local minimum-schema audit examples, correlation map, and expected audit-gap record
Expected result: Local audit examples contain the accepted minimum schema and correlation IDs; Keycloak \`LOGIN\` and \`CODE_TO_TOKEN\` events are collected as supplemental authentication evidence; a Keycloak admin \`UPDATE\` event is collected as supplemental technical-administration evidence; local protected-service and audit-read decisions remain local-only authoritative audit records with explicit gaps
Observed result: The script completed all assertions and recorded \`$(jq -r '.result' "$EVIDENCE_DIR/wp-007-audit-correlation-summary.json")\` in \`wp-007-audit-correlation-summary.json\`
Evidence collected:
- \`wp-007-member-token-response.json\`
- \`wp-007-member-id-token-claims.json\`
- \`wp-007-member-id-token-signature.txt\`
- \`wp-007-member-userinfo.json\`
- \`wp-007-keycloak-admin-event-probe.json\`
- \`wp-007-event-window.json\`
- \`wp-007-keycloak-events.json\`
- \`wp-007-keycloak-admin-events.json\`
- \`wp-007-local-audit.json\`
- \`wp-007-audit-correlation-map.json\`
- \`wp-007-audit-gaps.json\`
- \`wp-007-audit-correlation-summary.json\`
Pass / fail / blocked: $(jq -r '.result' "$EVIDENCE_DIR/wp-007-audit-correlation-summary.json")
Residual risk: The local audit records are fixture-based JSON evidence, not production append-only audit persistence, tamper resistance, retention, export, backup, restore, or privacy policy.
Production gap: A production path still needs a durable local audit store, write-path integration for every audited operation, correlation propagation, redaction policy, export controls, retention review, operational monitoring, and reconciliation rules for provider-side event gaps.
Decision impact: WP-007 supports the accepted Phase 4 audit boundary: Keycloak events can supplement authentication and technical-administration evidence, while local EDRLab audit remains authoritative for account, protected-service authorization, and audit-read decisions.
Generated at: $(utc_timestamp)
EOF

echo "WP-007 verification passed"
echo "Evidence written to $EVIDENCE_DIR"
