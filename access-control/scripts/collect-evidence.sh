#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"
EVIDENCE_DIR="$ROOT_DIR/access-control/evidence/$(date -u +%Y%m%dT%H%M%SZ)"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

mkdir -p "$EVIDENCE_DIR"

docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" ps > "$EVIDENCE_DIR/compose-ps.txt"
docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm tests > "$EVIDENCE_DIR/test-summary.txt" 2>&1
docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm keycloak-smoke > "$EVIDENCE_DIR/keycloak-smoke.json" 2>&1

cat > "$EVIDENCE_DIR/evidence.md" <<EOF
# Access-Control MVP Evidence

- Collected at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Compose status: compose-ps.txt
- Docker test summary: test-summary.txt
- Docker Keycloak smoke result: keycloak-smoke.json

This evidence is Docker runtime evidence for the Phase 6 MVP slice.
EOF

echo "Evidence written to $EVIDENCE_DIR"
