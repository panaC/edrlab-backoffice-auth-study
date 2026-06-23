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
    amr: (if (.amr | type) == "array" then .amr else [] end),
    amr_present: ((.amr | type) == "array" and (.amr | length) > 0),
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

authenticate_privileged_user() {
  local username=$1
  local email=$2
  local account_type=$3
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
  sanitize_token_response "$token_response" "$EVIDENCE_DIR/wp-004-$prefix-token-response.json"

  id_token=$(jq -r '.id_token // empty' "$token_response")
  access_token=$(jq -r '.access_token // empty' "$token_response")
  [[ -n "$id_token" && "$id_token" != "null" ]] || fail "$label token response missing ID token"
  [[ -n "$access_token" && "$access_token" != "null" ]] || fail "$label token response missing access token"
  pass "Authorization code exchanged for server-side tokens for $label"

  validate_id_token \
    "$id_token" \
    "$nonce" \
    "$email" \
    "$TMP_DIR/$prefix-id-token-header.raw.json" \
    "$TMP_DIR/$prefix-id-token-claims.raw.json" \
    "$EVIDENCE_DIR/wp-004-$prefix-id-token-claims.json" \
    "$EVIDENCE_DIR/wp-004-$prefix-id-token-signature.txt"

  subject=$(jq -r '.sub' "$TMP_DIR/$prefix-id-token-claims.raw.json")
  issuer=$(jq -r '.iss' "$TMP_DIR/$prefix-id-token-claims.raw.json")
  [[ -n "$subject" && "$subject" != "null" ]] || fail "$label ID token missing sub"

  curl -fsS \
    -H "Authorization: Bearer $access_token" \
    "$USERINFO_ENDPOINT" \
    | jq '{sub, email, email_verified, preferred_username, name}' > "$EVIDENCE_DIR/wp-004-$prefix-userinfo.json"
  jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-004-$prefix-userinfo.json" >/dev/null \
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
    --arg accountType "$account_type" \
    --arg issuer "$issuer" \
    --arg sub "$subject" \
    --argjson adminIdMatchesSub "$admin_id_matches_sub" \
    --slurpfile claims "$EVIDENCE_DIR/wp-004-$prefix-id-token-claims.json" \
    '{
      label: $label,
      keycloak_username: $username,
      candidate_account_type: $accountType,
      iss: $issuer,
      sub: $sub,
      email: $email,
      email_verified: true,
      amr: ($claims[0].amr // []),
      amr_present: (($claims[0].amr // []) | length > 0),
      acr: $claims[0].acr,
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
TMP_DIR="$POC_DIR/tmp/wp-004-$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

JWKS_FILE="$TMP_DIR/jwks.json"
curl -fsS "$JWKS_URI" | jq '.' > "$JWKS_FILE"

CLIENT_UUID=$(client_uuid "$ADMIN_TOKEN")
[[ -n "$CLIENT_UUID" ]] || fail "client not found: $KEYCLOAK_CLIENT_ID"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models" \
  | jq '[.[] | {id, name, protocol, protocolMapper, config}]' \
  > "$EVIDENCE_DIR/wp-004-client-protocol-mappers.json"
client_amr_mapper_count=$(jq '[.[] | select(((.protocolMapper // "") | test("amr"; "i")) or ((.name // "") | test("amr|authentication method"; "i")))] | length' "$EVIDENCE_DIR/wp-004-client-protocol-mappers.json")

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM" \
  | jq '{realm, browserFlow, registrationFlow, directGrantFlow, resetCredentialsFlow, clientAuthenticationFlow}' \
  > "$EVIDENCE_DIR/wp-004-realm-flow-bindings.json"
browser_flow=$(jq -r '.browserFlow // "browser"' "$EVIDENCE_DIR/wp-004-realm-flow-bindings.json")
encoded_browser_flow=$(urlencode "$browser_flow")

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/authentication/flows/$encoded_browser_flow/executions" \
  | jq '[
      .[]
      | {
          id,
          displayName,
          providerId,
          authenticator,
          authenticatorConfig,
          requirement,
          level,
          index,
          authenticationFlow,
          flowId,
          requirementChoices,
          reference_value_fields: (to_entries | map(select(.key | test("reference|amr"; "i"))))
        }
    ]' \
  > "$EVIDENCE_DIR/wp-004-browser-flow-executions.json"
configured_reference_values=$(jq '[.[] | .reference_value_fields[]?.value | select(type == "string" and length > 0)] | unique' "$EVIDENCE_DIR/wp-004-browser-flow-executions.json")

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
  }' > "$EVIDENCE_DIR/wp-004-event-window.json"

authenticate_privileged_user "$POC_ADMIN_USERNAME" "$POC_ADMIN_EMAIL" "admin" "admin" "admin identity"
authenticate_privileged_user "$POC_SUPER_ADMIN_USERNAME" "$POC_SUPER_ADMIN_EMAIL" "super-admin" "super-admin" "super-admin identity"

admin_identity_file="$TMP_DIR/admin-authenticated-identity.json"
super_admin_identity_file="$TMP_DIR/super-admin-authenticated-identity.json"
events_file="$EVIDENCE_DIR/wp-004-keycloak-events.json"
decisions_file="$EVIDENCE_DIR/wp-004-privileged-auth-decisions.json"
audit_file="$EVIDENCE_DIR/wp-004-local-audit.json"
summary_file="$EVIDENCE_DIR/wp-004-privileged-auth-summary.json"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events?max=100" \
  | jq \
      --slurpfile adminIdentity "$admin_identity_file" \
      --slurpfile superAdminIdentity "$super_admin_identity_file" \
      --argjson eventWindowStartedAtMs "$event_window_started_at_ms" \
      '
      [$adminIdentity[0].sub, $superAdminIdentity[0].sub] as $subjects
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
    ' > "$events_file"

for subject in "$(jq -r '.sub' "$admin_identity_file")" "$(jq -r '.sub' "$super_admin_identity_file")"; do
  for event_type in LOGIN CODE_TO_TOKEN; do
    event_count=$(jq \
      --arg subject "$subject" \
      --arg eventType "$event_type" \
      '[.[] | select(.userId == $subject and .type == $eventType)] | length' \
      "$events_file")
    [[ "$event_count" -ge 1 ]] \
      || fail "expected run-scoped Keycloak $event_type event for subject $subject"
  done
done
pass "Run-scoped Keycloak LOGIN and CODE_TO_TOKEN events collected for privileged subjects"

jq -n \
  --slurpfile adminIdentity "$admin_identity_file" \
  --slurpfile superAdminIdentity "$super_admin_identity_file" \
  --slurpfile events "$events_file" \
  --argjson clientAmrMapperCount "$client_amr_mapper_count" \
  --argjson configuredReferenceValues "$configured_reference_values" \
  '
  def candidate_privileged_amr_values:
    ["mfa", "otp", "hwk", "swk"];

  def matching_privileged_amr($identity):
    [($identity.amr // [])[] as $value | select(candidate_privileged_amr_values | index($value))];

  def event_types_for($subject):
    [$events[0][] | select(.userId == $subject) | .type] | unique | sort;

  def scenario($identity):
    matching_privileged_amr($identity) as $matchedAmr
    | event_types_for($identity.sub) as $eventTypes
    | {
        scenario: ($identity.candidate_account_type + "-activation-privileged-authentication-evidence"),
        expected_result: "candidate evidence or explicit blocker",
        observed_result: (if ($matchedAmr | length) > 0 then "candidate_evidence_found" else "blocked" end),
        pass: true,
        reason_code: (
          if ($matchedAmr | length) > 0 then
            "candidate_privileged_amr_present"
          elif (($identity.amr // []) | length) > 0 then
            "amr_present_but_not_sufficient_for_fr034"
          elif ($clientAmrMapperCount | tonumber) == 0 then
            "missing_amr_claim_and_client_mapper"
          else
            "missing_explicit_privileged_authentication_evidence"
          end
        ),
        candidate_account: {
          account_id: ("acct-wp004-" + ($identity.candidate_account_type | gsub("-"; "_"))),
          account_type: $identity.candidate_account_type,
          lifecycle_state: "invited",
          email: $identity.email,
          keycloak_issuer: null,
          keycloak_sub: null
        },
        authenticated_identity: $identity,
        token_amr_values: ($identity.amr // []),
        candidate_privileged_amr_values: $matchedAmr,
        client_amr_mapper_count: $clientAmrMapperCount,
        configured_browser_flow_reference_values: $configuredReferenceValues,
        keycloak_event_types: $eventTypes,
        account_activated: false,
        subject_link_created: false,
        local_session_created: false
      };

  [
    scenario($adminIdentity[0]),
    scenario($superAdminIdentity[0])
  ]
  ' > "$decisions_file"

jq \
  --arg timestamp "$(utc_timestamp)" \
  '
  map(
    {
      event_id: ("wp-004-" + .scenario),
      correlation_id: ("wp-004-" + .scenario),
      timestamp: $timestamp,
      source_component: "local-access-control-poc",
      actor_account_id: null,
      actor_keycloak_sub: .authenticated_identity.sub,
      action: "privileged_onboarding_activation_evidence_check",
      result: .observed_result,
      target_type: "backoffice_account",
      target_id: .candidate_account.account_id,
      reason_code,
      token_amr_values,
      candidate_privileged_amr_values,
      keycloak_event_reference: "supplemental; see wp-004-keycloak-events.json"
    }
  )
  ' "$decisions_file" > "$audit_file"

jq -n \
  --slurpfile decisions "$decisions_file" \
  --slurpfile realmFlow "$EVIDENCE_DIR/wp-004-realm-flow-bindings.json" \
  --slurpfile clientMappers "$EVIDENCE_DIR/wp-004-client-protocol-mappers.json" \
  --arg generatedAt "$(utc_timestamp)" \
  --arg browserFlow "$browser_flow" \
  --argjson clientAmrMapperCount "$client_amr_mapper_count" \
  --argjson configuredReferenceValues "$configured_reference_values" \
  '{
    generated_at: $generatedAt,
    work_package: "WP-004",
    result: (if all($decisions[0][]; .observed_result == "candidate_evidence_found") then "candidate_evidence_found" else "blocked" end),
    browser_flow: $browserFlow,
    client_amr_mapper_count: $clientAmrMapperCount,
    configured_browser_flow_reference_values: $configuredReferenceValues,
    realm_flow_bindings: $realmFlow[0],
    client_mapper_names: ($clientMappers[0] | map(.name)),
    decisions: $decisions[0],
    note: "This PoC records candidate evidence only. Production acceptance of any amr value, flow reference, MFA method, or passwordless method remains a Phase 5/security-review decision."
  }' > "$summary_file"

cat > "$EVIDENCE_DIR/wp-004-evidence.md" <<EOF
# WP-004 Evidence

Scenario: Privileged-authentication evidence
Work package: WP-004
Requirement links: FR-034, FR-043, FR-044
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production users \`$POC_ADMIN_USERNAME\` and \`$POC_SUPER_ADMIN_USERNAME\`
Action: Scripted browser-like Authorization Code flow with PKCE for admin and super-admin identities; ID token validation; UserInfo subject check; client protocol-mapper inspection; browser-flow execution inspection; run-scoped Keycloak event collection; PoC-only local privileged-activation evidence decision
Expected result: Either explicit candidate privileged-authentication evidence is present in token/configuration evidence, or production admin and super-admin activation remains blocked for review
Observed result: The script completed all assertions and recorded \`$(jq -r '.result' "$summary_file")\` in \`wp-004-privileged-auth-summary.json\`
Evidence collected:
- \`wp-004-admin-token-response.json\`
- \`wp-004-admin-id-token-claims.json\`
- \`wp-004-admin-id-token-signature.txt\`
- \`wp-004-admin-userinfo.json\`
- \`wp-004-super-admin-token-response.json\`
- \`wp-004-super-admin-id-token-claims.json\`
- \`wp-004-super-admin-id-token-signature.txt\`
- \`wp-004-super-admin-userinfo.json\`
- \`wp-004-client-protocol-mappers.json\`
- \`wp-004-realm-flow-bindings.json\`
- \`wp-004-browser-flow-executions.json\`
- \`wp-004-event-window.json\`
- \`wp-004-keycloak-events.json\`
- \`wp-004-privileged-auth-decisions.json\`
- \`wp-004-local-audit.json\`
- \`wp-004-privileged-auth-summary.json\`
Pass / fail / blocked: $(jq -r '.result' "$summary_file")
Residual risk: Keycloak authentication events prove login/token activity only as supplemental evidence. They do not, by themselves, prove MFA or phishing-resistant passwordless satisfaction for FR-034.
Production gap: A production path still needs an accepted privileged authenticator policy, scripted Keycloak flow/client mapper configuration, explicit accepted evidence values, fallback/recovery policy, and local activation enforcement before admin or super-admin onboarding can be allowed.
Decision impact: WP-004 keeps privileged admin and super-admin onboarding blocked unless explicit privileged-authentication evidence is present and accepted for review.
Generated at: $(utc_timestamp)
EOF

echo "WP-004 verification completed with result: $(jq -r '.result' "$summary_file")"
echo "Evidence written to $EVIDENCE_DIR"
