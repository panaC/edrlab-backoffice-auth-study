#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command docker
require_command curl
load_env

compose up -d
wait_for_url "$KEYCLOAK_BASE_URL/realms/master/.well-known/openid-configuration" "Keycloak master realm"

echo "Keycloak PoC runtime started at $KEYCLOAK_BASE_URL"
