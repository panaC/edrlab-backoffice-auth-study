#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command curl
require_command docker
require_command jq
load_env

wait_for_url "$KEYCLOAK_BASE_URL/realms/master/.well-known/openid-configuration" "Keycloak master realm"

TOKEN=$(admin_token)
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "Unable to obtain Keycloak admin token" >&2
  exit 1
fi

event_types_json=$(jq -cn '[
  "LOGIN",
  "LOGIN_ERROR",
  "LOGOUT",
  "CODE_TO_TOKEN",
  "CLIENT_LOGIN",
  "UPDATE_PROFILE",
  "UPDATE_PASSWORD",
  "VERIFY_EMAIL"
]')

realm_payload=$(jq -cn \
  --arg realm "$KEYCLOAK_REALM" \
  --arg expiration "$KEYCLOAK_EVENTS_EXPIRATION_SECONDS" \
  --argjson eventTypes "$event_types_json" \
  '{
    realm: $realm,
    enabled: true,
    displayName: "EDRLab Backoffice PoC",
    eventsEnabled: true,
    eventsExpiration: ($expiration | tonumber),
    enabledEventTypes: $eventTypes,
    adminEventsEnabled: true,
    adminEventsDetailsEnabled: true
  }')

if api_get "$TOKEN" "realms/$KEYCLOAK_REALM" >/dev/null 2>&1; then
  api_json PUT "$TOKEN" "realms/$KEYCLOAK_REALM" "$realm_payload" '^(200|204)$' >/dev/null
  echo "Updated realm: $KEYCLOAK_REALM"
else
  api_json POST "$TOKEN" "realms" "$realm_payload" '^(201|204)$' >/dev/null
  echo "Created realm: $KEYCLOAK_REALM"
fi

client_payload=$(jq -cn \
  --arg clientId "$KEYCLOAK_CLIENT_ID" \
  --arg secret "$KEYCLOAK_CLIENT_SECRET" \
  --arg redirectUri "$BACKOFFICE_REDIRECT_URI" \
  --arg logoutRedirectUri "$BACKOFFICE_LOGOUT_REDIRECT_URI" \
  --arg webOrigin "$BACKOFFICE_BASE_URL" \
  '{
    clientId: $clientId,
    name: "Backoffice BFF PoC",
    enabled: true,
    protocol: "openid-connect",
    publicClient: false,
    clientAuthenticatorType: "client-secret",
    secret: $secret,
    standardFlowEnabled: true,
    implicitFlowEnabled: false,
    directAccessGrantsEnabled: false,
    serviceAccountsEnabled: false,
    bearerOnly: false,
    consentRequired: false,
    redirectUris: [$redirectUri],
    webOrigins: [$webOrigin],
    attributes: {
      "pkce.code.challenge.method": "S256",
      "post.logout.redirect.uris": $logoutRedirectUri
    }
  }')

CLIENT_UUID=$(client_uuid "$TOKEN")
if [[ -z "$CLIENT_UUID" ]]; then
  api_json POST "$TOKEN" "realms/$KEYCLOAK_REALM/clients" "$client_payload" '^(201|204)$' >/dev/null
  CLIENT_UUID=$(client_uuid "$TOKEN")
  echo "Created OIDC client: $KEYCLOAK_CLIENT_ID"
else
  api_json PUT "$TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID" "$client_payload" '^(200|204)$' >/dev/null
  echo "Updated OIDC client: $KEYCLOAK_CLIENT_ID"
fi

ensure_user() {
  local username=$1
  local email=$2
  local email_verified=$3
  local first_name=$4
  local last_name=$5
  local user_id
  local user_payload
  local credential_payload

  user_payload=$(jq -cn \
    --arg username "$username" \
    --arg email "$email" \
    --arg firstName "$first_name" \
    --arg lastName "$last_name" \
    --argjson emailVerified "$email_verified" \
    '{
      username: $username,
      enabled: true,
      email: $email,
      emailVerified: $emailVerified,
      firstName: $firstName,
      lastName: $lastName,
      requiredActions: []
    }')

  user_id=$(user_uuid "$TOKEN" "$username")
  if [[ -z "$user_id" ]]; then
    api_json POST "$TOKEN" "realms/$KEYCLOAK_REALM/users" "$user_payload" '^(201|204)$' >/dev/null
    user_id=$(user_uuid "$TOKEN" "$username")
    echo "Created user: $username"
  else
    api_json PUT "$TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" "$user_payload" '^(200|204)$' >/dev/null
    echo "Updated user: $username"
  fi

  credential_payload=$(jq -cn \
    --arg password "$POC_USER_PASSWORD" \
    '{type: "password", value: $password, temporary: false}')
  api_json PUT "$TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/reset-password" "$credential_payload" '^(200|204)$' >/dev/null
}

ensure_user "$POC_MEMBER_USERNAME" "$POC_MEMBER_EMAIL" true "Member" "PoC"
ensure_user "$POC_ADMIN_USERNAME" "$POC_ADMIN_EMAIL" true "Admin" "PoC"
ensure_user "$POC_SUPER_ADMIN_USERNAME" "$POC_SUPER_ADMIN_EMAIL" true "SuperAdmin" "PoC"
ensure_user "$POC_UNSAFE_USERNAME" "$POC_UNSAFE_EMAIL" false "Unsafe" "PoC"

echo "Bootstrap complete for realm $KEYCLOAK_REALM"
