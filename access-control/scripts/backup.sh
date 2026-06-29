#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/access-control/compose.yaml"
ENV_FILE="$ROOT_DIR/access-control/.env.local"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-access-control-mvp}"
BACKUP_IMAGE="${ACCESS_CONTROL_BACKUP_IMAGE:-busybox:1.36.1}"
BACKUP_ROOT="${ACCESS_CONTROL_BACKUP_DIR:-$ROOT_DIR/access-control/backups}"
BACKUP_ID="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_ID"

ENV_ARGS=()
if [[ -f "$ENV_FILE" ]]; then
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

mkdir -p "$BACKUP_DIR"

docker compose "${ENV_ARGS[@]}" -f "$COMPOSE_FILE" stop keycloak iam-api access-check-demo-service

for volume in access-control-runtime keycloak-data; do
  volume_name="${PROJECT_NAME}_${volume}"
  archive="${volume}.tgz"
  docker volume inspect "$volume_name" >/dev/null
  docker run --rm \
    -e "ARCHIVE=$archive" \
    -v "$volume_name:/source:ro" \
    -v "$BACKUP_DIR:/backup" \
    "$BACKUP_IMAGE" \
    sh -c 'cd /source && tar -czf "/backup/$ARCHIVE" .'
  docker run --rm \
    -e "ARCHIVE=$archive" \
    -v "$BACKUP_DIR:/backup" \
    "$BACKUP_IMAGE" \
    sh -c 'test -s "/backup/$ARCHIVE" && tar -tzf "/backup/$ARCHIVE" >/dev/null'
done

(
  cd "$BACKUP_DIR"
  sha256sum access-control-runtime.tgz keycloak-data.tgz > SHA256SUMS
)

cat > "$BACKUP_DIR/manifest.txt" <<EOF
Access-Control MVP backup
Created at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Compose file: $COMPOSE_FILE
Compose project: $PROJECT_NAME
Volumes:
- ${PROJECT_NAME}_access-control-runtime -> access-control-runtime.tgz
- ${PROJECT_NAME}_keycloak-data -> keycloak-data.tgz
Restore command:
RESTORE_CONFIRM=restore-access-control-mvp-state bash access-control/scripts/restore.sh $BACKUP_DIR
EOF

echo "Backup written to $BACKUP_DIR"
