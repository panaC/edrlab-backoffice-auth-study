#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="$ROOT_DIR/access-control/evidence/onboarding-email-e2e-docker-$RUN_ID"
LOG_FILE="$EVIDENCE_DIR/docker-run.log"

mkdir -p "$EVIDENCE_DIR"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

export KEYCLOAK_ONBOARDING_ACTION_EMAILS=true
export KEYCLOAK_SMTP_HOST="${KEYCLOAK_SMTP_HOST:-mailpit}"
export KEYCLOAK_SMTP_PORT="${KEYCLOAK_SMTP_PORT:-1025}"
export KEYCLOAK_SMTP_FROM="${KEYCLOAK_SMTP_FROM:-no-reply@example.test}"
export MAILPIT_API_BASE_URL="${MAILPIT_API_BASE_URL:-http://mailpit:8025}"

{
  echo "Onboarding email E2E Docker run started at $RUN_ID"
  echo "Evidence directory: $EVIDENCE_DIR"
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools up --build -d mailpit keycloak iam-api access-check-demo-service
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm keycloak-bootstrap
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm bootstrap
  docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm human-e2e \
    python -m access_control.human_e2e --yes --email-onboarding
  echo "Onboarding email E2E Docker run finished at $(date -u +%Y%m%dT%H%M%SZ)"
} 2>&1 | tee "$LOG_FILE"

echo "Docker wrapper log: $LOG_FILE"
