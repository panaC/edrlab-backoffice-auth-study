#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command docker
load_env

RUNNER_IMAGE=${WP013_RUNNER_IMAGE:-python:3.13-alpine}
KEYCLOAK_CONTAINER_ID=$(compose ps -q keycloak)

if [[ -z "$KEYCLOAK_CONTAINER_ID" ]]; then
  echo "Keycloak container is not running. Run: bash poc/keycloak/scripts/start.sh" >&2
  exit 2
fi

MSYS_NO_PATHCONV=1 docker run --rm \
  --network "container:$KEYCLOAK_CONTAINER_ID" \
  -v "$REPO_ROOT:/work" \
  -w /work \
  -e KEYCLOAK_BASE_URL="http://localhost:8080" \
  -e KEYCLOAK_REALM="$KEYCLOAK_REALM" \
  -e KEYCLOAK_CLIENT_ID="$KEYCLOAK_CLIENT_ID" \
  -e KEYCLOAK_CLIENT_SECRET="$KEYCLOAK_CLIENT_SECRET" \
  -e KC_BOOTSTRAP_ADMIN_USERNAME="$KC_BOOTSTRAP_ADMIN_USERNAME" \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD="$KC_BOOTSTRAP_ADMIN_PASSWORD" \
  -e BACKOFFICE_REDIRECT_URI="$BACKOFFICE_REDIRECT_URI" \
  -e POC_USER_PASSWORD="$POC_USER_PASSWORD" \
  -e POC_ADMIN_USERNAME="$POC_ADMIN_USERNAME" \
  -e POC_ADMIN_EMAIL="$POC_ADMIN_EMAIL" \
  -e POC_SUPER_ADMIN_USERNAME="$POC_SUPER_ADMIN_USERNAME" \
  -e POC_SUPER_ADMIN_EMAIL="$POC_SUPER_ADMIN_EMAIL" \
  -e EVIDENCE_ROOT="/work/poc/keycloak/evidence" \
  "$RUNNER_IMAGE" \
  python /work/poc/keycloak/scripts/verify_iam_control_plane_wp013.py
