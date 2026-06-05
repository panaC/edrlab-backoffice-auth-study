#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
POC_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd -- "$POC_DIR/../.." && pwd)
ENV_FILE=${ENV_FILE:-"$POC_DIR/.env.local"}
COMPOSE_FILE="$POC_DIR/compose.yaml"

require_command() {
  local command_name=$1
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 127
  fi
}

load_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing environment file: $ENV_FILE" >&2
    echo "Create it with: cp $POC_DIR/.env.example $ENV_FILE" >&2
    exit 2
  fi

  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a

  : "${KEYCLOAK_IMAGE:=quay.io/keycloak/keycloak:26.6.1}"
  : "${KEYCLOAK_HOST_BIND:=127.0.0.1}"
  : "${KEYCLOAK_PORT:=8080}"
  : "${KEYCLOAK_BASE_URL:=http://localhost:${KEYCLOAK_PORT}}"
  : "${KEYCLOAK_REALM:=edrlab-backoffice-poc}"
  : "${KEYCLOAK_CLIENT_ID:=backoffice-bff-poc}"
  : "${KEYCLOAK_EVENTS_EXPIRATION_SECONDS:=3600}"
  : "${BACKOFFICE_BASE_URL:=http://localhost:3000}"
  : "${BACKOFFICE_REDIRECT_URI:=${BACKOFFICE_BASE_URL}/auth/callback}"
  : "${BACKOFFICE_LOGOUT_REDIRECT_URI:=${BACKOFFICE_BASE_URL}/logout/callback}"
  : "${POC_MEMBER_USERNAME:=kc-member-poc}"
  : "${POC_MEMBER_EMAIL:=kc-member-poc@example.invalid}"
  : "${POC_ADMIN_USERNAME:=kc-admin-poc}"
  : "${POC_ADMIN_EMAIL:=kc-admin-poc@example.invalid}"
  : "${POC_SUPER_ADMIN_USERNAME:=kc-super-admin-poc}"
  : "${POC_SUPER_ADMIN_EMAIL:=kc-super-admin-poc@example.invalid}"
  : "${POC_UNSAFE_USERNAME:=kc-unsafe-poc}"
  : "${POC_UNSAFE_EMAIL:=kc-unsafe-poc@example.invalid}"

  require_env KC_BOOTSTRAP_ADMIN_USERNAME
  require_env KC_BOOTSTRAP_ADMIN_PASSWORD
  require_env KEYCLOAK_CLIENT_SECRET
  require_env POC_USER_PASSWORD

  export KEYCLOAK_IMAGE KEYCLOAK_HOST_BIND KEYCLOAK_PORT KEYCLOAK_BASE_URL
  export KC_BOOTSTRAP_ADMIN_USERNAME KC_BOOTSTRAP_ADMIN_PASSWORD
  export KEYCLOAK_REALM KEYCLOAK_CLIENT_ID KEYCLOAK_CLIENT_SECRET
  export KEYCLOAK_EVENTS_EXPIRATION_SECONDS
  export BACKOFFICE_BASE_URL BACKOFFICE_REDIRECT_URI BACKOFFICE_LOGOUT_REDIRECT_URI
  export POC_USER_PASSWORD
  export POC_MEMBER_USERNAME POC_MEMBER_EMAIL
  export POC_ADMIN_USERNAME POC_ADMIN_EMAIL
  export POC_SUPER_ADMIN_USERNAME POC_SUPER_ADMIN_EMAIL
  export POC_UNSAFE_USERNAME POC_UNSAFE_EMAIL
}

require_env() {
  local name=$1
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 2
  fi
}

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_for_url() {
  local url=$1
  local label=$2
  local max_attempts=${3:-90}
  local attempt=1

  while (( attempt <= max_attempts )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$label is reachable: $url"
      return 0
    fi
    sleep 2
    attempt=$((attempt + 1))
  done

  echo "Timed out waiting for $label: $url" >&2
  return 1
}

admin_token() {
  curl -fsS \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "client_id=admin-cli" \
    --data-urlencode "username=$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --data-urlencode "password=$KC_BOOTSTRAP_ADMIN_PASSWORD" \
    --data-urlencode "grant_type=password" \
    "$KEYCLOAK_BASE_URL/realms/master/protocol/openid-connect/token" \
    | jq -r '.access_token'
}

api_url() {
  local path=$1
  printf '%s/admin/%s' "$KEYCLOAK_BASE_URL" "$path"
}

urlencode() {
  jq -nr --arg value "$1" '$value|@uri'
}

api_get() {
  local token=$1
  local path=$2
  curl -fsS -H "Authorization: Bearer $token" "$(api_url "$path")"
}

api_json() {
  local method=$1
  local token=$2
  local path=$3
  local payload=$4
  local expected_status=${5:-'^(200|201|204)$'}
  local response_file
  local status

  response_file=$(mktemp)
  status=$(curl -sS \
    -o "$response_file" \
    -w "%{http_code}" \
    -X "$method" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    --data "$payload" \
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

client_id_query() {
  urlencode "$KEYCLOAK_CLIENT_ID"
}

client_uuid() {
  local token=$1
  api_get "$token" "realms/$KEYCLOAK_REALM/clients?clientId=$(client_id_query)" \
    | jq -r '.[0].id // empty'
}

user_uuid() {
  local token=$1
  local username=$2
  local encoded_username
  encoded_username=$(urlencode "$username")
  api_get "$token" "realms/$KEYCLOAK_REALM/users?username=$encoded_username&exact=true" \
    | jq -r '.[0].id // empty'
}

utc_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
