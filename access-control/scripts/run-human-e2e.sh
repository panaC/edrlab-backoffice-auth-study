#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="$ROOT_DIR/access-control/evidence/human-e2e-docker-$RUN_ID"
LOG_FILE="$EVIDENCE_DIR/docker-run.log"

mkdir -p "$EVIDENCE_DIR"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

{
  echo "Human E2E Docker run started at $RUN_ID"
  echo "Evidence directory: $EVIDENCE_DIR"
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" up --build -d keycloak iam-api access-check-demo-service
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm keycloak-bootstrap
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm bootstrap
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm human-e2e python -m access_control.human_e2e "$@"
  echo "Human E2E Docker run finished at $(date -u +%Y%m%dT%H%M%SZ)"
} 2>&1 | tee "$LOG_FILE"

echo "Docker wrapper log: $LOG_FILE"
