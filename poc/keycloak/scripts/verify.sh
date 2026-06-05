#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command curl
require_command docker
require_command jq
load_env

assert_eq() {
  local actual=$1
  local expected=$2
  local label=$3
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL $label: expected '$expected', got '$actual'" >&2
    exit 1
  fi
  echo "PASS $label"
}

assert_bool() {
  local json=$1
  local filter=$2
  local expected=$3
  local label=$4
  local actual
  actual=$(jq -r "$filter" <<<"$json")
  assert_eq "$actual" "$expected" "$label"
}

wait_for_url "$KEYCLOAK_BASE_URL/realms/master/.well-known/openid-configuration" "Keycloak master realm"
wait_for_url "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" "PoC realm discovery"

TOKEN=$(admin_token)
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "Unable to obtain Keycloak admin token" >&2
  exit 1
fi

discovery=$(curl -fsS "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration")
assert_eq "$(jq -r '.issuer' <<<"$discovery")" "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM" "realm issuer"
assert_eq "$(jq -r '.authorization_endpoint' <<<"$discovery")" "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/auth" "authorization endpoint"
assert_eq "$(jq -r '.token_endpoint' <<<"$discovery")" "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" "token endpoint"

CLIENT_UUID=$(client_uuid "$TOKEN")
if [[ -z "$CLIENT_UUID" ]]; then
  echo "FAIL client exists: $KEYCLOAK_CLIENT_ID" >&2
  exit 1
fi
echo "PASS client exists: $KEYCLOAK_CLIENT_ID"

client_json=$(api_get "$TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID")
assert_bool "$client_json" '.standardFlowEnabled' "true" "authorization code flow enabled"
assert_bool "$client_json" '.implicitFlowEnabled' "false" "implicit flow disabled"
assert_bool "$client_json" '.directAccessGrantsEnabled' "false" "direct access grants disabled"
assert_eq "$(jq -r '.redirectUris[0]' <<<"$client_json")" "$BACKOFFICE_REDIRECT_URI" "redirect URI"
assert_eq "$(jq -r '.webOrigins[0]' <<<"$client_json")" "$BACKOFFICE_BASE_URL" "web origin"

for username in "$POC_MEMBER_USERNAME" "$POC_ADMIN_USERNAME" "$POC_SUPER_ADMIN_USERNAME" "$POC_UNSAFE_USERNAME"; do
  if [[ -z "$(user_uuid "$TOKEN" "$username")" ]]; then
    echo "FAIL user exists: $username" >&2
    exit 1
  fi
  echo "PASS user exists: $username"
done

unsafe_user=$(api_get "$TOKEN" "realms/$KEYCLOAK_REALM/users?username=$(urlencode "$POC_UNSAFE_USERNAME")&exact=true")
assert_bool "$unsafe_user" '.[0].emailVerified' "false" "unsafe user email remains unverified"

events_config=$(api_get "$TOKEN" "realms/$KEYCLOAK_REALM/events/config")
assert_bool "$events_config" '.eventsEnabled' "true" "user events enabled"
assert_bool "$events_config" '.adminEventsEnabled' "true" "admin events enabled"
assert_bool "$events_config" '.adminEventsDetailsEnabled' "true" "admin event details enabled"

echo "WP-001 verification passed"
