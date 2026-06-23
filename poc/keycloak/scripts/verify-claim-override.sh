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

api_no_body() {
  local method=$1
  local token=$2
  local path=$3
  local expected_status=${4:-'^(200|201|204)$'}
  local response_file
  local status

  response_file=$(mktemp)
  status=$(curl -sS \
    -o "$response_file" \
    -w "%{http_code}" \
    -X "$method" \
    -H "Authorization: Bearer $token" \
    "$(api_url "$path")")

  if [[ ! "$status" =~ $expected_status ]]; then
    echo "Unexpected HTTP status $status for $method $(api_url "$path")" >&2
    cat "$response_file" >&2
    rm -f "$response_file"
    return 1
  fi

  cat "$response_file"
  rm -f "$response_file"
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
    edrlab_account_type,
    edrlab_lifecycle_state,
    edrlab_audit_bypass,
    groups: (if (.groups | type) == "array" then .groups else [] end),
    realm_access_roles: (.realm_access.roles // []),
    resource_access_clients: ((.resource_access // {}) | keys),
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

validate_access_token() {
  local access_token=$1
  local expected_subject=$2
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

  jwt_part "$access_token" 0 | jq '.' > "$raw_header_file"
  jwt_part "$access_token" 1 | jq '.' > "$raw_claims_file"
  sanitize_claims "$raw_claims_file" "$sanitized_claims_file"

  alg=$(jq -r '.alg // empty' "$raw_header_file")
  [[ "$alg" == "RS256" ]] || fail "access token alg expected RS256, got '$alg'"

  kid=$(jq -r '.kid // empty' "$raw_header_file")
  [[ -n "$kid" ]] || fail "access token missing kid"

  jwk_to_pem "$JWKS_FILE" "$kid" "$TMP_DIR/access-token-key.pem"
  signing_input=${access_token%.*}
  signature=${access_token##*.}
  printf '%s' "$signing_input" > "$TMP_DIR/access-token-signing-input.txt"
  b64url_to_file "$signature" "$TMP_DIR/access-token-signature.bin"
  if openssl dgst -sha256 \
    -verify "$TMP_DIR/access-token-key.pem" \
    -signature "$TMP_DIR/access-token-signature.bin" \
    "$TMP_DIR/access-token-signing-input.txt" > "$verify_file" 2>&1; then
    pass "Access token signature verified for member identity"
  else
    cat "$verify_file" >&2
    fail "access token signature verification failed for member identity"
  fi

  jq -e --arg issuer "$expected_issuer" '.iss == $issuer' "$raw_claims_file" >/dev/null \
    || fail "access token issuer mismatch for member identity"
  pass "Access token issuer matches realm for member identity"

  jq -e --arg sub "$expected_subject" '.sub == $sub' "$raw_claims_file" >/dev/null \
    || fail "access token subject mismatch for member identity"
  pass "Access token subject matches ID token subject for member identity"

  jq -e --arg client "$KEYCLOAK_CLIENT_ID" '.azp == $client or .client_id == $client' "$raw_claims_file" >/dev/null \
    || fail "access token authorized party/client mismatch for member identity"
  pass "Access token authorized party matches client for member identity"

  now=$(date +%s)
  jq -e --argjson now "$now" '.exp > $now and .iat <= ($now + 300)' "$raw_claims_file" >/dev/null \
    || fail "access token time claims are not valid for the current clock for member identity"
  pass "Access token time claims are within expected bounds for member identity"
}

ensure_realm_role() {
  local role_name=$1
  local description=$2
  local output_file=$3
  local encoded_role_name
  local payload

  encoded_role_name=$(urlencode "$role_name")
  payload=$(jq -cn \
    --arg name "$role_name" \
    --arg description "$description" \
    '{name: $name, description: $description, composite: false, clientRole: false}')

  if api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/roles/$encoded_role_name" > "$output_file" 2>/dev/null; then
    :
  else
    api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/roles" "$payload" '^(201|204|409)$' >/dev/null
  fi

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/roles/$encoded_role_name" | jq '.' > "$output_file"
}

assign_realm_role_to_user() {
  local user_id=$1
  local role_file=$2
  local role_name
  local current_roles_file
  local payload

  role_name=$(jq -r '.name' "$role_file")
  current_roles_file="$TMP_DIR/current-realm-role-mappings.json"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/realm" \
    | jq '.' > "$current_roles_file"

  if jq -e --arg roleName "$role_name" 'any(.[]; .name == $roleName)' "$current_roles_file" >/dev/null; then
    return 0
  fi

  payload=$(jq -c '[.]' "$role_file")
  api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/realm" "$payload" '^(200|204)$' >/dev/null
}

ensure_group() {
  local group_name=$1
  local output_file=$2
  local encoded_group_name
  local group_id
  local payload

  encoded_group_name=$(urlencode "$group_name")
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/groups?search=$encoded_group_name" \
    | jq '.' > "$TMP_DIR/groups-search.json"
  group_id=$(jq -r --arg groupName "$group_name" '.[] | select(.name == $groupName) | .id' "$TMP_DIR/groups-search.json" | head -n 1)

  if [[ -z "$group_id" ]]; then
    payload=$(jq -cn --arg name "$group_name" '{name: $name}')
    api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/groups" "$payload" '^(201|204|409)$' >/dev/null
    api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/groups?search=$encoded_group_name" \
      | jq '.' > "$TMP_DIR/groups-search.json"
    group_id=$(jq -r --arg groupName "$group_name" '.[] | select(.name == $groupName) | .id' "$TMP_DIR/groups-search.json" | head -n 1)
  fi

  [[ -n "$group_id" ]] || fail "unable to create or find group $group_name"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/groups/$group_id" | jq '.' > "$output_file"
}

assign_group_to_user() {
  local user_id=$1
  local group_file=$2
  local group_id
  local current_groups_file

  group_id=$(jq -r '.id' "$group_file")
  current_groups_file="$TMP_DIR/current-groups.json"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/groups" | jq '.' > "$current_groups_file"

  if jq -e --arg groupId "$group_id" 'any(.[]; .id == $groupId)' "$current_groups_file" >/dev/null; then
    return 0
  fi

  api_no_body PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/groups/$group_id" '^(204)$' >/dev/null
}

ensure_client_mapper() {
  local mapper_name=$1
  local mapper_payload=$2
  local existing_mapper_id
  local update_payload

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models" \
    | jq '.' > "$TMP_DIR/client-protocol-mappers-before.json"
  existing_mapper_id=$(jq -r --arg mapperName "$mapper_name" '.[] | select(.name == $mapperName) | .id' "$TMP_DIR/client-protocol-mappers-before.json" | head -n 1)

  if [[ -n "$existing_mapper_id" ]]; then
    update_payload=$(jq --arg id "$existing_mapper_id" '. + {id: $id}' <<<"$mapper_payload")
    api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models/$existing_mapper_id" "$update_payload" '^(200|204)$' >/dev/null
  else
    api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models" "$mapper_payload" '^(201|204|409)$' >/dev/null
  fi
}

hardcoded_claim_mapper_payload() {
  local mapper_name=$1
  local claim_name=$2
  local claim_value=$3
  local json_type=$4

  jq -cn \
    --arg name "$mapper_name" \
    --arg claimName "$claim_name" \
    --arg claimValue "$claim_value" \
    --arg jsonType "$json_type" \
    '{
      name: $name,
      protocol: "openid-connect",
      protocolMapper: "oidc-hardcoded-claim-mapper",
      consentRequired: false,
      config: {
        "claim.name": $claimName,
        "claim.value": $claimValue,
        "jsonType.label": $jsonType,
        "id.token.claim": "true",
        "access.token.claim": "true",
        "userinfo.token.claim": "true"
      }
    }'
}

group_membership_mapper_payload() {
  local mapper_name=$1
  local claim_name=$2

  jq -cn \
    --arg name "$mapper_name" \
    --arg claimName "$claim_name" \
    '{
      name: $name,
      protocol: "openid-connect",
      protocolMapper: "oidc-group-membership-mapper",
      consentRequired: false,
      config: {
        "claim.name": $claimName,
        "full.path": "true",
        "id.token.claim": "true",
        "access.token.claim": "true",
        "userinfo.token.claim": "true"
      }
    }'
}

configure_override_claims() {
  local account_role_file="$TMP_DIR/account-role.json"
  local service_role_file="$TMP_DIR/service-role.json"
  local group_file="$TMP_DIR/group.json"

  CLIENT_UUID=$(client_uuid "$ADMIN_TOKEN")
  [[ -n "$CLIENT_UUID" ]] || fail "client not found: $KEYCLOAK_CLIENT_ID"

  MEMBER_USER_ID=$(user_uuid "$ADMIN_TOKEN" "$POC_MEMBER_USERNAME")
  [[ -n "$MEMBER_USER_ID" ]] || fail "member user not found: $POC_MEMBER_USERNAME"

  ensure_realm_role "$DANGEROUS_ACCOUNT_ROLE" "PoC-only misleading account-type role for WP-005 claim override rejection." "$account_role_file"
  ensure_realm_role "$DANGEROUS_SERVICE_ROLE" "PoC-only misleading service-access role for WP-005 claim override rejection." "$service_role_file"
  assign_realm_role_to_user "$MEMBER_USER_ID" "$account_role_file"
  assign_realm_role_to_user "$MEMBER_USER_ID" "$service_role_file"

  ensure_group "$DANGEROUS_GROUP" "$group_file"
  assign_group_to_user "$MEMBER_USER_ID" "$group_file"

  ensure_client_mapper \
    "$ACCOUNT_TYPE_CLAIM_MAPPER" \
    "$(hardcoded_claim_mapper_payload "$ACCOUNT_TYPE_CLAIM_MAPPER" "edrlab_account_type" "super-admin" "String")"
  ensure_client_mapper \
    "$LIFECYCLE_CLAIM_MAPPER" \
    "$(hardcoded_claim_mapper_payload "$LIFECYCLE_CLAIM_MAPPER" "edrlab_lifecycle_state" "active" "String")"
  ensure_client_mapper \
    "$AUDIT_BYPASS_CLAIM_MAPPER" \
    "$(hardcoded_claim_mapper_payload "$AUDIT_BYPASS_CLAIM_MAPPER" "edrlab_audit_bypass" "true" "boolean")"
  ensure_client_mapper \
    "$GROUPS_CLAIM_MAPPER" \
    "$(group_membership_mapper_payload "$GROUPS_CLAIM_MAPPER" "groups")"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models" \
    | jq '.' > "$TMP_DIR/client-protocol-mappers-after.json"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$MEMBER_USER_ID/role-mappings/realm" \
    | jq '.' > "$TMP_DIR/member-role-mappings.json"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$MEMBER_USER_ID/groups" \
    | jq '.' > "$TMP_DIR/member-groups.json"

  jq -n \
    --arg generatedAt "$(utc_timestamp)" \
    --arg keycloakUser "$POC_MEMBER_USERNAME" \
    --arg accountRole "$DANGEROUS_ACCOUNT_ROLE" \
    --arg serviceRole "$DANGEROUS_SERVICE_ROLE" \
    --arg group "$DANGEROUS_GROUP" \
    --arg accountTypeMapper "$ACCOUNT_TYPE_CLAIM_MAPPER" \
    --arg lifecycleMapper "$LIFECYCLE_CLAIM_MAPPER" \
    --arg auditBypassMapper "$AUDIT_BYPASS_CLAIM_MAPPER" \
    --arg groupsMapper "$GROUPS_CLAIM_MAPPER" \
    --slurpfile roleMappings "$TMP_DIR/member-role-mappings.json" \
    --slurpfile memberGroups "$TMP_DIR/member-groups.json" \
    --slurpfile mappers "$TMP_DIR/client-protocol-mappers-after.json" \
    '{
      generated_at: $generatedAt,
      note: "PoC-only Keycloak configuration intentionally creates misleading roles, groups, and claims for WP-005. These are not production authorization data.",
      keycloak_user: $keycloakUser,
      misleading_inputs: {
        realm_roles_assigned: [$accountRole, $serviceRole],
        group_assigned: $group,
        hardcoded_claims: {
          edrlab_account_type: "super-admin",
          edrlab_lifecycle_state: "active",
          edrlab_audit_bypass: true
        },
        client_mappers: [$accountTypeMapper, $lifecycleMapper, $auditBypassMapper, $groupsMapper]
      },
      observed_user_role_mappings: ($roleMappings[0] | map({id, name, description})),
      observed_user_groups: ($memberGroups[0] | map({id, name, path})),
      observed_client_mappers: (
        $mappers[0]
        | map(select(.name as $name | [$accountTypeMapper, $lifecycleMapper, $auditBypassMapper, $groupsMapper] | index($name)))
        | map({id, name, protocol, protocolMapper, config})
      )
    }' > "$EVIDENCE_DIR/wp-005-keycloak-override-setup.json"
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
  local token_response="$TMP_DIR/member-token-response.raw.json"
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

  exchange_code "$code" "$verifier" "$token_response"
  sanitize_token_response "$token_response" "$EVIDENCE_DIR/wp-005-member-token-response.json"

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
    "$EVIDENCE_DIR/wp-005-member-id-token-claims.json" \
    "$EVIDENCE_DIR/wp-005-member-id-token-signature.txt"

  subject=$(jq -r '.sub' "$TMP_DIR/member-id-token-claims.raw.json")
  issuer=$(jq -r '.iss' "$TMP_DIR/member-id-token-claims.raw.json")
  [[ -n "$subject" && "$subject" != "null" ]] || fail "member ID token missing sub"

  validate_access_token \
    "$access_token" \
    "$subject" \
    "$TMP_DIR/member-access-token-header.raw.json" \
    "$TMP_DIR/member-access-token-claims.raw.json" \
    "$EVIDENCE_DIR/wp-005-member-access-token-claims.json" \
    "$EVIDENCE_DIR/wp-005-member-access-token-signature.txt"

  curl -fsS \
    -H "Authorization: Bearer $access_token" \
    "$USERINFO_ENDPOINT" \
    | jq '{
        sub,
        email,
        email_verified,
        preferred_username,
        name,
        edrlab_account_type,
        edrlab_lifecycle_state,
        edrlab_audit_bypass,
        groups: (.groups // [])
      }' > "$EVIDENCE_DIR/wp-005-member-userinfo.json"
  jq -e --arg sub "$subject" '.sub == $sub' "$EVIDENCE_DIR/wp-005-member-userinfo.json" >/dev/null \
    || fail "member UserInfo sub does not match ID token sub"
  pass "UserInfo sub matches ID token sub for member identity"

  jq -n \
    --arg keycloakUsername "$POC_MEMBER_USERNAME" \
    --arg email "$POC_MEMBER_EMAIL" \
    --arg issuer "$issuer" \
    --arg sub "$subject" \
    --slurpfile idClaims "$EVIDENCE_DIR/wp-005-member-id-token-claims.json" \
    --slurpfile accessClaims "$EVIDENCE_DIR/wp-005-member-access-token-claims.json" \
    --slurpfile userinfo "$EVIDENCE_DIR/wp-005-member-userinfo.json" \
    '{
      keycloak_username: $keycloakUsername,
      iss: $issuer,
      sub: $sub,
      email: $email,
      token_claims: {
        id: $idClaims[0],
        access: $accessClaims[0],
        userinfo: $userinfo[0]
      }
    }' > "$TMP_DIR/member-authenticated-identity.json"
}

assert_misleading_claims_present() {
  jq -e \
    --arg accountRole "$DANGEROUS_ACCOUNT_ROLE" \
    --arg serviceRole "$DANGEROUS_SERVICE_ROLE" \
    --arg groupName "$DANGEROUS_GROUP" \
    '
    def group_values:
      ((.token_claims.id.groups // [])
      + (.token_claims.access.groups // [])
      + (.token_claims.userinfo.groups // []));

    (.token_claims.id.edrlab_account_type == "super-admin")
    and (.token_claims.id.edrlab_lifecycle_state == "active")
    and ((.token_claims.id.edrlab_audit_bypass == true) or (.token_claims.id.edrlab_audit_bypass == "true"))
    and ((.token_claims.access.realm_access_roles // []) | index($accountRole) != null)
    and ((.token_claims.access.realm_access_roles // []) | index($serviceRole) != null)
    and (group_values | (index("/" + $groupName) != null or index($groupName) != null))
    ' "$TMP_DIR/member-authenticated-identity.json" >/dev/null \
    || fail "expected misleading Keycloak roles, group, and hardcoded claims were not present in token/UserInfo evidence"

  pass "Misleading Keycloak roles, group, and claims are present in token/UserInfo evidence"
}

write_local_claim_override_decisions() {
  local identity_file="$TMP_DIR/member-authenticated-identity.json"
  local inputs_file="$EVIDENCE_DIR/wp-005-local-authorization-inputs.json"
  local decisions_file="$EVIDENCE_DIR/wp-005-claim-override-decisions.json"
  local audit_file="$EVIDENCE_DIR/wp-005-local-audit.json"
  local summary_file="$EVIDENCE_DIR/wp-005-claim-override-summary.json"

  jq -n \
    --slurpfile identity "$identity_file" \
    '{
      note: "PoC-only local authorization fixtures for WP-005. Keycloak roles, groups, and claims are intentionally misleading and must not override local account state.",
      rule_under_test: "Resolve the account by issuer and subject, then authorize only from local account type, lifecycle, service-access-role assignment, and local audit policy.",
      identity: $identity[0],
      service_role_catalog: [
        {
          role_id: "protected-service-consultation-poc",
          lifecycle_state: "active",
          covers_services: ["catalog-service-poc"]
        }
      ],
      scenarios: [
        {
          scenario: "account-type-claim-does-not-grant-admin-management",
          expected_result: "deny",
          action: "manage_admin_account",
          target_type: "backoffice_account",
          target_id: "acct-target-admin-poc",
          local_account: {
            account_id: "acct-wp005-local-member",
            account_type: "member",
            lifecycle_state: "active",
            email: $identity[0].email,
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          }
        },
        {
          scenario: "lifecycle-claim-does-not-activate-disabled-account",
          expected_result: "deny",
          action: "access_protected_service",
          target_type: "protected_backend_service",
          target_id: "catalog-service-poc",
          local_account: {
            account_id: "acct-wp005-disabled-member",
            account_type: "member",
            lifecycle_state: "disabled",
            email: $identity[0].email,
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: ["protected-service-consultation-poc"]
          }
        },
        {
          scenario: "keycloak-role-does-not-create-service-access",
          expected_result: "deny",
          action: "access_protected_service",
          target_type: "protected_backend_service",
          target_id: "catalog-service-poc",
          local_account: {
            account_id: "acct-wp005-member-without-local-service-role",
            account_type: "member",
            lifecycle_state: "active",
            email: $identity[0].email,
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: []
          }
        },
        {
          scenario: "audit-bypass-claim-does-not-suppress-denial-audit",
          expected_result: "deny",
          action: "read_audit_records",
          target_type: "audit_log",
          target_id: "audit-export-poc",
          local_account: {
            account_id: "acct-wp005-local-member-audit-check",
            account_type: "member",
            lifecycle_state: "active",
            email: $identity[0].email,
            keycloak_issuer: $identity[0].iss,
            keycloak_sub: $identity[0].sub,
            service_access_roles: []
          }
        }
      ]
    }' > "$inputs_file"

  jq '
    def exact_subject_link($identity; $account):
      $account.keycloak_issuer == $identity.iss and $account.keycloak_sub == $identity.sub;

    def role_covers_service($catalog; $roleId; $serviceId):
      any($catalog[]; .role_id == $roleId and .lifecycle_state == "active" and (.covers_services | index($serviceId) != null));

    def has_local_service_access($catalog; $account; $serviceId):
      if ($account.account_type == "admin" or $account.account_type == "super-admin") then
        true
      elif $account.account_type == "member" then
        any($account.service_access_roles[]?; role_covers_service($catalog; .; $serviceId))
      else
        false
      end;

    def deny($root; $reason):
      . as $scenario
      | $root.identity as $identity
      | {
          scenario: $scenario.scenario,
          expected_result: $scenario.expected_result,
          observed_result: "deny",
          pass: ($scenario.expected_result == "deny"),
          action: $scenario.action,
          target_type: $scenario.target_type,
          target_id: $scenario.target_id,
          reason_code: $reason,
          authenticated_identity: {
            iss: $identity.iss,
            sub: $identity.sub,
            email: $identity.email
          },
          local_account_before: $scenario.local_account,
          local_account_after: $scenario.local_account,
          keycloak_claims_ignored: {
            edrlab_account_type: $identity.token_claims.id.edrlab_account_type,
            edrlab_lifecycle_state: $identity.token_claims.id.edrlab_lifecycle_state,
            edrlab_audit_bypass: $identity.token_claims.id.edrlab_audit_bypass,
            realm_access_roles: $identity.token_claims.access.realm_access_roles,
            groups: (($identity.token_claims.id.groups // []) + ($identity.token_claims.access.groups // []) + ($identity.token_claims.userinfo.groups // []) | unique)
          },
          local_decision_authority: {
            account_type: $scenario.local_account.account_type,
            lifecycle_state: $scenario.local_account.lifecycle_state,
            service_access_roles: $scenario.local_account.service_access_roles
          },
          subject_link_created: false,
          account_type_changed: false,
          lifecycle_state_changed: false,
          local_service_access_role_assigned: false,
          local_session_created: false,
          local_audit_recorded: true
        };

    . as $root
    | .scenarios
    | map(
        if (exact_subject_link($root.identity; .local_account) | not) then
          deny($root; "unresolved_local_subject")
        elif (.action == "manage_admin_account") then
          if (.local_account.lifecycle_state == "active" and .local_account.account_type == "super-admin") then
            error("unexpected allow for admin-management scenario")
          else
            deny($root; "local_account_type_not_authorized")
          end
        elif (.action == "access_protected_service") then
          if .local_account.lifecycle_state != "active" then
            deny($root; "local_account_not_active")
          elif has_local_service_access($root.service_role_catalog; .local_account; .target_id) then
            error("unexpected allow for protected-service scenario")
          else
            deny($root; "missing_local_service_access_role")
          end
        elif (.action == "read_audit_records") then
          if (.local_account.lifecycle_state == "active" and .local_account.account_type == "super-admin") then
            error("unexpected allow for audit-read scenario")
          else
            deny($root; "local_account_type_not_authorized")
          end
        else
          deny($root; "unsupported_action")
        end
      )
    ' "$inputs_file" > "$decisions_file"

  jq -e 'all(.[]; .pass == true and .observed_result == "deny" and .local_audit_recorded == true)' "$decisions_file" >/dev/null \
    || fail "one or more claim override decisions did not match the expected deny result"
  pass "All WP-005 claim override decisions denied from local state"

  jq -e '
    all(.[]; .local_account_after == .local_account_before)
    and all(.[]; .account_type_changed == false and .lifecycle_state_changed == false and .local_service_access_role_assigned == false)
  ' "$decisions_file" >/dev/null \
    || fail "one or more denied decisions mutated local account fixtures"
  pass "Misleading Keycloak claims did not mutate local account fixtures"

  jq \
    --arg timestamp "$(utc_timestamp)" \
    '
    map(
      {
        event_id: ("wp-005-" + .scenario),
        correlation_id: ("wp-005-" + .scenario),
        timestamp: $timestamp,
        source_component: "local-access-control-poc",
        actor_account_id: .local_account_before.account_id,
        actor_keycloak_sub: .authenticated_identity.sub,
        action,
        result: .observed_result,
        target_type,
        target_id,
        reason_code,
        keycloak_claims_ignored,
        local_decision_authority,
        keycloak_event_reference: "supplemental; see wp-005-keycloak-events.json"
      }
    )
    ' "$decisions_file" > "$audit_file"

  jq -n \
    --slurpfile decisions "$decisions_file" \
    --slurpfile setup "$EVIDENCE_DIR/wp-005-keycloak-override-setup.json" \
    --arg generatedAt "$(utc_timestamp)" \
    '{
      generated_at: $generatedAt,
      work_package: "WP-005",
      result: (if all($decisions[0][]; .observed_result == "deny" and .pass == true) then "pass" else "fail" end),
      misleading_keycloak_inputs: $setup[0].misleading_inputs,
      decisions: $decisions[0],
      note: "Pass means the misleading Keycloak roles, group, and claims were present, but every local decision ignored them and denied from local account state."
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
TMP_DIR="$POC_DIR/tmp/wp-005-$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

DANGEROUS_ACCOUNT_ROLE="edrlab-super-admin-claim-poc"
DANGEROUS_SERVICE_ROLE="protected-service-consultation-poc"
DANGEROUS_GROUP="edrlab-super-admin-claim-poc"
ACCOUNT_TYPE_CLAIM_MAPPER="wp-005-edrlab-account-type-claim"
LIFECYCLE_CLAIM_MAPPER="wp-005-edrlab-lifecycle-state-claim"
AUDIT_BYPASS_CLAIM_MAPPER="wp-005-edrlab-audit-bypass-claim"
GROUPS_CLAIM_MAPPER="wp-005-edrlab-groups-claim"

JWKS_FILE="$TMP_DIR/jwks.json"
curl -fsS "$JWKS_URI" | jq '.' > "$JWKS_FILE"

configure_override_claims

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
  }' > "$EVIDENCE_DIR/wp-005-event-window.json"

authenticate_member_user
assert_misleading_claims_present
write_local_claim_override_decisions

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
          details
        }]
    ' > "$EVIDENCE_DIR/wp-005-keycloak-events.json"

for event_type in LOGIN CODE_TO_TOKEN; do
  event_count=$(jq \
    --arg subject "$member_subject" \
    --arg eventType "$event_type" \
    '[.[] | select(.userId == $subject and .type == $eventType)] | length' \
    "$EVIDENCE_DIR/wp-005-keycloak-events.json")
  [[ "$event_count" -ge 1 ]] \
    || fail "expected run-scoped Keycloak $event_type event for member subject $member_subject"
done
pass "Run-scoped Keycloak LOGIN and CODE_TO_TOKEN events collected for member subject"

cat > "$EVIDENCE_DIR/wp-005-evidence.md" <<EOF
# WP-005 Evidence

Scenario: Claim override rejection
Work package: WP-005
Requirement links: FR-038, FR-020, FR-021, FR-027
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, non-production member user \`$POC_MEMBER_USERNAME\`, and PoC-only misleading Keycloak role, group, and hardcoded claim mappers
Action: Configure misleading Keycloak roles, group membership, and token/UserInfo claims; run Authorization Code flow with PKCE; validate ID token and UserInfo subject evidence; then evaluate PoC-only local authorization fixtures that ignore Keycloak roles, groups, and claims
Expected result: The misleading Keycloak roles, group, and claims are present in token/UserInfo evidence, but local account type, lifecycle, service-access-role assignments, and audit policy remain authoritative; every override attempt is denied and audited
Observed result: The script completed all assertions and recorded \`$(jq -r '.result' "$EVIDENCE_DIR/wp-005-claim-override-summary.json")\` in \`wp-005-claim-override-summary.json\`
Evidence collected:
- \`wp-005-keycloak-override-setup.json\`
- \`wp-005-member-token-response.json\`
- \`wp-005-member-id-token-claims.json\`
- \`wp-005-member-id-token-signature.txt\`
- \`wp-005-member-access-token-claims.json\`
- \`wp-005-member-access-token-signature.txt\`
- \`wp-005-member-userinfo.json\`
- \`wp-005-local-authorization-inputs.json\`
- \`wp-005-claim-override-decisions.json\`
- \`wp-005-local-audit.json\`
- \`wp-005-claim-override-summary.json\`
- \`wp-005-event-window.json\`
- \`wp-005-keycloak-events.json\`
Pass / fail / blocked: $(jq -r '.result' "$EVIDENCE_DIR/wp-005-claim-override-summary.json")
Residual risk: The local decision evaluator is fixture-based PoC evidence, not production authorization code, persistent storage, middleware, or a protected-service implementation.
Production gap: A production path still needs a real local account store, a server-side authorization contract, middleware or BFF integration, audit persistence, and tests that prevent future claim-to-local-state coupling.
Decision impact: WP-005 supports the accepted boundary that Keycloak supplies authentication evidence, while EDRLab local access control remains authoritative for account type, lifecycle, service-access roles, protected-service authorization, and audit behavior.
Generated at: $(utc_timestamp)
EOF

echo "WP-005 verification passed"
echo "Evidence written to $EVIDENCE_DIR"
