#!/usr/bin/env bash
set -euo pipefail

if [[ "${RESET_CONFIRM:-}" != "delete-access-control-mvp-state" ]]; then
  echo "Refusing to reset. Set RESET_CONFIRM=delete-access-control-mvp-state." >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" down -v
rm -rf "$ROOT_DIR/access-control/evidence" "$ROOT_DIR/access-control/runtime"

