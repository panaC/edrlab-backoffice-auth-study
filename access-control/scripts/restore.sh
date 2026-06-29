#!/usr/bin/env bash
set -euo pipefail

if [[ "${RESTORE_CONFIRM:-}" != "restore-access-control-mvp-state" ]]; then
  echo "Refusing to restore. Set RESTORE_CONFIRM=restore-access-control-mvp-state." >&2
  exit 2
fi

if [[ $# -ne 1 ]]; then
  echo "Usage: RESTORE_CONFIRM=restore-access-control-mvp-state bash access-control/scripts/restore.sh <backup-directory>" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-edrlab-access-control-mvp}"
BACKUP_IMAGE="${ACCESS_CONTROL_BACKUP_IMAGE:-busybox:1.36.1}"
BACKUP_DIR="$1"

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "Backup directory does not exist: $BACKUP_DIR" >&2
  exit 2
fi

for required in access-control-runtime.tgz keycloak-data.tgz SHA256SUMS; do
  if [[ ! -f "$BACKUP_DIR/$required" ]]; then
    echo "Backup file is missing: $BACKUP_DIR/$required" >&2
    exit 2
  fi
done

(
  cd "$BACKUP_DIR"
  sha256sum -c SHA256SUMS
)

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" stop keycloak iam-api access-check-demo-service

for volume in access-control-runtime keycloak-data; do
  volume_name="${PROJECT_NAME}_${volume}"
  archive="${volume}.tgz"
  docker volume create "$volume_name" >/dev/null
  docker run --rm \
    -e "ARCHIVE=$archive" \
    -v "$volume_name:/target" \
    -v "$BACKUP_DIR:/backup:ro" \
    "$BACKUP_IMAGE" \
    sh -c 'find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} + && tar -xzf "/backup/$ARCHIVE" -C /target'
done

echo "Backup restored from $BACKUP_DIR"
echo "Run: bash access-control/scripts/start.sh"
