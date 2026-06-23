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
    amr,
    sid_present: (.sid != null)
  }' "$input_file" > "$output_file"
}

validate_id_token() {
  local id_token=$1
  local expected_nonce=$2
  local expected_email=$3
  local expected_email_verified=$4
  local raw_header_file=$5
  local raw_claims_file=$6
  local sanitized_claims_file=$7
  local verify_file=$8
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

  jq -e \
    --arg email "$expected_email" \
    --argjson expectedVerified "$expected_email_verified" \
    '.email == $email and .email_verified == $expectedVerified' \
    "$raw_claims_file" >/dev/null \
    || fail "ID token email or email_verified mismatch for $expected_email"
  pass "ID token email evidence matches expected verification state for $expected_email"

  now=$(date +%s)
  jq -e --argjson now "$now" '.exp > $now and .iat <= ($now + 300)' "$raw_claims_file" >/dev/null \
    || fail "ID token time claims are not valid for the current clock for $expected_email"
  pass "ID token time claims are within expected bounds for $expected_email"
}

authenticate_user() {
  local username=$1
  local email=$2
  local expected_email_verified=$3
  local prefix=$4
  local label=$5
  local cookie_jar="$TMP_DIR/$prefix-browser-cookies.txt"
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
  local keycloak_admin_id
  local admin_id_matches_sub=false

  state=$(random_urlsafe 24)
  nonce=$(random_urlsafe 24)
  verifier=$(random_urlsafe 64)
  challenge=$(pkce_challenge "$verifier")
  auth_url=$(build_auth_url "$state" "$nonce" "$challenge")

  curl -fsS -L \
    -b "$cookie_jar" \
    -c "$cookie_jar" \
    -o "$TMP_DIR/$prefix-login-page.html" \
    "$auth_url"
  login_action=$(form_action "$TMP_DIR/$prefix-login-page.html") \
    || fail "unable to find Keycloak login form action for $label"
  pass "Keycloak login form reached for $label"

  login_status=$(curl -sS \
    -b "$cookie_jar" \
    -c "$cookie_jar" \
    -D "$TMP_DIR/$prefix-login-post.headers" \
    -o "$TMP_DIR/$prefix-login-post.body" \
    -w "%{http_code}" \
    --data-urlencode "username=$username" \
    --data-urlencode "password=$POC_USER_PASSWORD" \
    --data-urlencode "credentialId=" \
    --data-urlencode "login=Sign In" \
    "$login_action")
  [[ "$login_status" =~ ^(302|303)$ ]] || fail "$label login POST expected redirect, got HTTP $login_status"
  callback=$(header_location "$TMP_DIR/$prefix-login-post.headers") \
    || fail "$label login redirect did not include Location"
  [[ "$callback" == "$BACKOFFICE_REDIRECT_URI"* ]] || fail "$label login redirect target is not the backoffice callback"
  code=$(query_param "$callback" "code")
  returned_state=$(query_param "$callback" "state")
  [[ -n "$code" ]] || fail "$label authorization response missing code"
  [[ "$returned_state" == "$state" ]] || fail "$label authorization response state mismatch"
  pass "Authorization Code flow returned code for $label"

  token_response="$TMP_DIR/$prefix-token-response.json"
  exchange_code "$code" "$verifier" "$token_response"
  sanitize_token_response "$token_response" "$EVIDENCE_DIR/wp-003-$prefix-token-response.json"

  id_token=$(jq -r '.id_token // empty' "$token_response")
  access_token=$(jq -r '.access_token // empty' "$token_response")
  [[ -n "$id_token" && "$id_token" != "null" ]] || fail "$label token response missing ID token"
  [[ -n "$access_token" && "$access_token" != "null" ]] || fail "$label token response missing access token"
  pass "Authorization code exchanged for server-side tokens for $label"

  validate_id_token \
    "$id_token" \
    "$nonce" \
    "$email" \
    "$expected_email_verified" \
    "$TMP_DIR/$prefix-id-token-header.raw.json" \
    "$TMP_DIR/$prefix-id-token-claims.raw.json" \
    "$EVIDENCE_DIR/wp-003-$prefix-id-token-claims.json" \
    "$EVIDENCE_DIR/wp-003-$prefix-id-token-signature.txt"

  subject=$(jq -r '.sub' "$TMP_DIR/$prefix-id-token-claims.raw.json")
  issuer=$(jq -r '.iss' "$TMP_DIR/$prefix-id-token-claims.raw.json")
  [[ -n "$subject" && "$subject" != "null" ]] || fail "$label ID token missing sub"

  curl -fsS \
    -H "Authorization: Bearer $access_token" \
    "$USERINFO_ENDPOINT" \
    | jq '{sub, email, email_verified, preferred_username, name}' > "$EVIDENCE_DIR/wp-003-$prefix-userinfo.json"
  jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-003-$prefix-userinfo.json" >/dev/null \
    || fail "$label UserInfo sub does not match ID token sub"
  pass "UserInfo sub matches ID token sub for $label"

  keycloak_admin_id=$(user_uuid "$ADMIN_TOKEN" "$username")
  if [[ "$keycloak_admin_id" == "$subject" ]]; then
    admin_id_matches_sub=true
  fi

  jq -n \
    --arg label "$label" \
    --arg username "$username" \
    --arg email "$email" \
    --arg issuer "$issuer" \
    --arg sub "$subject" \
    --argjson emailVerified "$expected_email_verified" \
    --argjson adminIdMatchesSub "$admin_id_matches_sub" \
    '{
      label: $label,
      keycloak_username: $username,
      iss: $issuer,
      sub: $sub,
      email: $email,
      email_verified: $emailVerified,
      keycloak_admin_user_id_matches_id_token_sub: $adminIdMatchesSub
    }' > "$TMP_DIR/$prefix-authenticated-identity.json"
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
TMP_DIR="$POC_DIR/tmp/wp-003-$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

JWKS_FILE="$TMP_DIR/jwks.json"
curl -fsS "$JWKS_URI" | jq '.' > "$JWKS_FILE"

event_window_file="$EVIDENCE_DIR/wp-003-event-window.json"
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
  }' > "$event_window_file"

authenticate_user "$POC_MEMBER_USERNAME" "$POC_MEMBER_EMAIL" true "safe-member" "safe invited member identity"
authenticate_user "$POC_UNSAFE_USERNAME" "$POC_UNSAFE_EMAIL" false "unverified-user" "unverified unsafe identity"

safe_identity_file="$TMP_DIR/safe-member-authenticated-identity.json"
unverified_identity_file="$TMP_DIR/unverified-user-authenticated-identity.json"
inputs_file="$EVIDENCE_DIR/wp-003-local-onboarding-inputs.json"
decisions_file="$EVIDENCE_DIR/wp-003-onboarding-decisions.json"
audit_file="$EVIDENCE_DIR/wp-003-local-audit.json"

jq -n \
  --slurpfile safeIdentity "$safe_identity_file" \
  --slurpfile unverifiedIdentity "$unverified_identity_file" \
  '{
    note: "PoC-only local onboarding fixtures for WP-003. This is not production application code or a persistent store.",
    rule_under_test: "Link and activate only when one invited local account has no subject link and matches a verified authenticated email.",
    scenarios: [
      {
        scenario: "safe-invited-member",
        expected_result: "allow",
        identity: $safeIdentity[0],
        local_accounts: [
          {
            account_id: "acct-wp003-safe-member",
            account_type: "member",
            lifecycle_state: "invited",
            email: $safeIdentity[0].email,
            organization: "PoC Organization",
            name: "Safe Member PoC",
            keycloak_issuer: null,
            keycloak_sub: null,
            service_access_roles: ["protected-service-consultation-poc"]
          }
        ]
      },
      {
        scenario: "no-local-invitation",
        expected_result: "deny",
        identity: $safeIdentity[0],
        local_accounts: [
          {
            account_id: "acct-wp003-unrelated-invited-member",
            account_type: "member",
            lifecycle_state: "invited",
            email: "unrelated-wp003@example.invalid",
            organization: "PoC Organization",
            name: "Unrelated Member PoC",
            keycloak_issuer: null,
            keycloak_sub: null,
            service_access_roles: []
          }
        ]
      },
      {
        scenario: "duplicate-local-invitations",
        expected_result: "deny",
        identity: $safeIdentity[0],
        local_accounts: [
          {
            account_id: "acct-wp003-duplicate-a",
            account_type: "member",
            lifecycle_state: "invited",
            email: $safeIdentity[0].email,
            organization: "PoC Organization",
            name: "Duplicate Member A",
            keycloak_issuer: null,
            keycloak_sub: null,
            service_access_roles: []
          },
          {
            account_id: "acct-wp003-duplicate-b",
            account_type: "member",
            lifecycle_state: "invited",
            email: $safeIdentity[0].email,
            organization: "PoC Organization",
            name: "Duplicate Member B",
            keycloak_issuer: null,
            keycloak_sub: null,
            service_access_roles: []
          }
        ]
      },
      {
        scenario: "unverified-authenticated-email",
        expected_result: "deny",
        identity: $unverifiedIdentity[0],
        local_accounts: [
          {
            account_id: "acct-wp003-unverified-member",
            account_type: "member",
            lifecycle_state: "invited",
            email: $unverifiedIdentity[0].email,
            organization: "PoC Organization",
            name: "Unverified Member PoC",
            keycloak_issuer: null,
            keycloak_sub: null,
            service_access_roles: []
          }
        ]
      },
      {
        scenario: "pre-linked-local-account",
        expected_result: "deny",
        identity: $safeIdentity[0],
        local_accounts: [
          {
            account_id: "acct-wp003-prelinked-member",
            account_type: "member",
            lifecycle_state: "invited",
            email: $safeIdentity[0].email,
            organization: "PoC Organization",
            name: "Prelinked Member PoC",
            keycloak_issuer: "https://issuer-already-linked.example.invalid",
            keycloak_sub: "already-linked-subject",
            service_access_roles: []
          }
        ]
      }
    ]
  }' > "$inputs_file"

jq \
  --arg activatedAt "$(utc_timestamp)" \
  '
  def has_subject_link:
    ((.keycloak_issuer // "") != "") or ((.keycloak_sub // "") != "");

  def deny($reason; $emailMatches):
    {
      scenario: .scenario,
      expected_result: .expected_result,
      observed_result: "deny",
      pass: (.expected_result == "deny"),
      reason_code: $reason,
      authenticated_identity: .identity,
      matching_invited_email_account_count: ($emailMatches | length),
      candidate_account_ids: (.local_accounts | map(.account_id)),
      matching_account_ids: ($emailMatches | map(.account_id)),
      target_account_id: (if ($emailMatches | length) == 1 then $emailMatches[0].account_id else null end),
      activated_account: null,
      local_session_created: false,
      before_accounts: .local_accounts,
      after_accounts: .local_accounts
    };

  def allow($account; $emailMatches):
    .identity as $identity
    |
    {
      scenario: .scenario,
      expected_result: .expected_result,
      observed_result: "allow",
      pass: (.expected_result == "allow"),
      reason_code: "safe_invited_match",
      authenticated_identity: .identity,
      matching_invited_email_account_count: ($emailMatches | length),
      candidate_account_ids: (.local_accounts | map(.account_id)),
      matching_account_ids: ($emailMatches | map(.account_id)),
      target_account_id: $account.account_id,
      activated_account: (
        $account
        + {
          lifecycle_state: "active",
          keycloak_issuer: $identity.iss,
          keycloak_sub: $identity.sub,
          activated_at: $activatedAt
        }
      ),
      local_session_created: true,
      before_accounts: .local_accounts,
      after_accounts: [
        .local_accounts[]
        | if .account_id == $account.account_id then
            . + {
              lifecycle_state: "active",
              keycloak_issuer: $identity.iss,
              keycloak_sub: $identity.sub,
              activated_at: $activatedAt
            }
          else
            .
          end
      ]
    };

  .scenarios
  | map(
      . as $scenario
      | [.local_accounts[] | select(.lifecycle_state == "invited" and .email == $scenario.identity.email)] as $emailMatches
      | if $scenario.identity.email_verified != true then
          deny("email_not_verified"; $emailMatches)
        elif ($emailMatches | length) == 0 then
          deny("no_local_invitation"; $emailMatches)
        elif ($emailMatches | length) > 1 then
          deny("duplicate_local_invitation"; $emailMatches)
        elif ($emailMatches[0] | has_subject_link) then
          deny("existing_subject_link"; $emailMatches)
        else
          allow($emailMatches[0]; $emailMatches)
        end
    )
  ' "$inputs_file" > "$decisions_file"

jq -e 'all(.[]; .pass == true)' "$decisions_file" >/dev/null \
  || fail "one or more onboarding decisions did not match the expected result"
pass "All WP-003 onboarding decisions matched expected allow/deny outcomes"

allowed_count=$(jq '[.[] | select(.observed_result == "allow")] | length' "$decisions_file")
denied_count=$(jq '[.[] | select(.observed_result == "deny")] | length' "$decisions_file")
[[ "$allowed_count" == "1" ]] || fail "expected exactly one allowed onboarding activation, got $allowed_count"
[[ "$denied_count" == "4" ]] || fail "expected four denied onboarding attempts, got $denied_count"
pass "Exactly one safe activation and four unsafe denials were recorded"

jq -e '
  any(.[]; .scenario == "safe-invited-member" and .activated_account.lifecycle_state == "active" and .activated_account.keycloak_sub == .authenticated_identity.sub)
' "$decisions_file" >/dev/null \
  || fail "safe scenario did not create the expected immutable subject link"
pass "Safe onboarding created the subject link and activated the local account"

jq -e '
  all(.[] | select(.observed_result == "deny"); .local_session_created == false and (.after_accounts == .before_accounts))
' "$decisions_file" >/dev/null \
  || fail "one or more denied scenarios changed local accounts or created a session"
pass "Unsafe onboarding attempts did not mutate local accounts or create a session"

jq \
  --arg timestamp "$(utc_timestamp)" \
  '
  map(
    {
      event_id: ("wp-003-" + .scenario),
      correlation_id: ("wp-003-" + .scenario),
      timestamp: $timestamp,
      source_component: "local-access-control-poc",
      actor_account_id: null,
      actor_keycloak_sub: .authenticated_identity.sub,
      action: (if .observed_result == "allow" then "automatic_onboarding_activation" else "automatic_onboarding_activation_denied" end),
      result: .observed_result,
      target_type: "backoffice_account",
      target_id: .target_account_id,
      candidate_account_ids,
      matching_account_ids,
      matching_invited_email_account_count,
      reason_code,
      keycloak_event_reference: "supplemental; see wp-003-keycloak-events.json"
    }
  )
  ' "$decisions_file" > "$audit_file"

safe_subject=$(jq -r '.[] | select(.scenario == "safe-invited-member") | .authenticated_identity.sub' "$decisions_file")
unverified_subject=$(jq -r '.[] | select(.scenario == "unverified-authenticated-email") | .authenticated_identity.sub' "$decisions_file")
[[ -n "$safe_subject" && "$safe_subject" != "null" ]] || fail "safe subject missing from decisions"
[[ -n "$unverified_subject" && "$unverified_subject" != "null" ]] || fail "unverified subject missing from decisions"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events?max=100" \
  | jq \
      --slurpfile safeIdentity "$safe_identity_file" \
      --slurpfile unverifiedIdentity "$unverified_identity_file" \
      --argjson eventWindowStartedAtMs "$event_window_started_at_ms" \
      '
      [$safeIdentity[0].sub, $unverifiedIdentity[0].sub] as $subjects
      | [.[] | select(
          .time >= $eventWindowStartedAtMs
          and (.userId as $userId | $subjects | index($userId))
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
          details
        }]
    ' > "$EVIDENCE_DIR/wp-003-keycloak-events.json"

for subject in "$safe_subject" "$unverified_subject"; do
  for event_type in LOGIN CODE_TO_TOKEN; do
    event_count=$(jq \
      --arg subject "$subject" \
      --arg eventType "$event_type" \
      '[.[] | select(.userId == $subject and .type == $eventType)] | length' \
      "$EVIDENCE_DIR/wp-003-keycloak-events.json")
    [[ "$event_count" -ge 1 ]] \
      || fail "expected run-scoped Keycloak $event_type event for subject $subject"
  done
done
pass "Run-scoped Keycloak LOGIN and CODE_TO_TOKEN events collected for both subjects"

cat > "$EVIDENCE_DIR/wp-003-evidence.md" <<EOF
# WP-003 Evidence

Scenario: Safe and unsafe onboarding
Work package: WP-003
Requirement links: FR-039, FR-043, FR-044
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production users \`$POC_MEMBER_USERNAME\` and \`$POC_UNSAFE_USERNAME\`
Action: Scripted browser-like Authorization Code flow with PKCE for a verified member identity and an unverified unsafe identity, followed by PoC-only local onboarding rule evaluation for safe, no-invitation, duplicate-invitation, unverified-email, and pre-linked-subject fixtures
Expected result: The local onboarding evaluator links and activates exactly one invited account only when the authenticated identity has a verified matching email and the local account has no existing subject link; unsafe cases deny access, keep accounts unchanged, and do not create a local session
Observed result: The script completed all assertions and collected sanitized evidence files in this directory
Evidence collected:
- \`wp-003-safe-member-token-response.json\`
- \`wp-003-safe-member-id-token-claims.json\`
- \`wp-003-safe-member-id-token-signature.txt\`
- \`wp-003-safe-member-userinfo.json\`
- \`wp-003-unverified-user-token-response.json\`
- \`wp-003-unverified-user-id-token-claims.json\`
- \`wp-003-unverified-user-id-token-signature.txt\`
- \`wp-003-unverified-user-userinfo.json\`
- \`wp-003-local-onboarding-inputs.json\`
- \`wp-003-onboarding-decisions.json\`
- \`wp-003-local-audit.json\`
- \`wp-003-event-window.json\`
- \`wp-003-keycloak-events.json\`
Pass / fail / blocked: Pass
Residual risk: This is a fixture-based local onboarding evaluator, not production onboarding code, persistent storage, concurrency handling, email normalization policy, or administrator intervention workflow.
Production gap: A production implementation still needs transactional subject-link creation, uniqueness constraints, immutable-link enforcement, audit persistence, admin review workflows for denied onboarding, email normalization rules, and privileged-authentication evidence before admin or super-admin activation.
Decision impact: WP-003 supports the selected boundary where Keycloak supplies authenticated subject and verified-email evidence, while local access control owns subject-link creation, activation, fail-closed denial, and audit records.
Generated at: $(utc_timestamp)
EOF

echo "WP-003 verification passed"
echo "Evidence written to $EVIDENCE_DIR"
