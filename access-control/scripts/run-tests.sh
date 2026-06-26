#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" --profile tools run --build --rm tests
