#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command curl
require_command docker
require_command jq
load_env

wait_for_url "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" "PoC realm discovery"

TOKEN=$(admin_token)
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "Unable to obtain Keycloak admin token" >&2
  exit 1
fi

EVIDENCE_ROOT="$POC_DIR/evidence"
EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +"%Y%m%dT%H%M%SZ")"
mkdir -p "$EVIDENCE_DIR"

discovery_file="$EVIDENCE_DIR/discovery.json"
client_file="$EVIDENCE_DIR/client.json"
users_file="$EVIDENCE_DIR/users.json"
events_file="$EVIDENCE_DIR/events-config.json"
compose_file="$EVIDENCE_DIR/compose-ps.txt"
logs_file="$EVIDENCE_DIR/keycloak-logs-tail.txt"
summary_file="$EVIDENCE_DIR/wp-001-evidence.md"

curl -fsS "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" \
  | jq '.' > "$discovery_file"

CLIENT_UUID=$(client_uuid "$TOKEN")
api_get "$TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID" \
  | jq 'del(.secret)' > "$client_file"

api_get "$TOKEN" "realms/$KEYCLOAK_REALM/users" \
  | jq '[.[] | {id, username, email, emailVerified, enabled, requiredActions}]' > "$users_file"

api_get "$TOKEN" "realms/$KEYCLOAK_REALM/events/config" \
  | jq '.' > "$events_file"

compose ps > "$compose_file"
compose logs --no-color keycloak | tail -n 200 > "$logs_file"

cat > "$summary_file" <<EOF
# WP-001 Evidence

Scenario: Keycloak setup
Work package: WP-001
Requirement links: FR-036, FR-037, FR-038, FR-039, FR-043, FR-044
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`
Action: Start runtime, bootstrap realm/client/users/events, verify OIDC discovery and client safety settings
Expected result: Realm discovery is available, Authorization Code flow is enabled, Implicit Flow and Direct Access Grants are disabled, non-production users exist, and event capture is enabled
Observed result: Collected by \`scripts/verify.sh\`; see generated files in this directory
Evidence collected:
- \`discovery.json\`
- \`client.json\`
- \`users.json\`
- \`events-config.json\`
- \`compose-ps.txt\`
- \`keycloak-logs-tail.txt\`
Pass / fail / blocked: Pending reviewer confirmation after \`bash scripts/verify.sh\`
Residual risk: This is a development-mode Keycloak runtime and not production infrastructure
Production gap: Production deployment, database, backup, restore, HA, monitoring, secret management, upgrade, and hardening are out of scope
Decision impact: If verification passes, WP-002 can validate login and SSO boundary behavior
Generated at: $(utc_timestamp)
EOF

echo "Evidence written to $EVIDENCE_DIR"
