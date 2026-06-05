#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command docker
load_env

if [[ "${RESET_CONFIRM:-}" != "delete-poc-state" ]]; then
  echo "This removes the local Keycloak PoC container state and generated evidence." >&2
  echo "Run with RESET_CONFIRM=delete-poc-state to confirm." >&2
  exit 2
fi

compose down -v --remove-orphans
find "$POC_DIR/evidence" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
rm -rf "$POC_DIR/tmp"

echo "Keycloak PoC runtime state reset"
