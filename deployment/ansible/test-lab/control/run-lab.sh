#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="${LAB_TARGET_HOST:-172.28.47.10}"
TARGET_PORT="${LAB_TARGET_PORT:-22}"
TARGET_ROOT_PASSWORD="${LAB_TARGET_ROOT_PASSWORD:-root}"
RUN_FULL_DEPLOY="${LAB_RUN_FULL_DEPLOY:-0}"
LAB_DIR="/lab"
KEY_PATH="$LAB_DIR/deploy_ed25519"
ROOT_INVENTORY="$LAB_DIR/inventory-root.yml"
DEPLOY_INVENTORY="$LAB_DIR/inventory-deploy.yml"
LAB_VARS="$LAB_DIR/lab-vars.yml"
DEFAULT_VARS="/work/deployment/ansible/inventories/production/group_vars/all.yml"

export ANSIBLE_ROLES_PATH="/work/deployment/ansible/roles"
export ANSIBLE_HOST_KEY_CHECKING="False"

mkdir -p "$LAB_DIR"

if [[ ! -f "$KEY_PATH" ]]; then
  ssh-keygen -t ed25519 -N "" -f "$KEY_PATH" -C "ansible-docker-lab" >/dev/null
fi

PUBLIC_KEY="$(cat "$KEY_PATH.pub")"

cat >"$ROOT_INVENTORY" <<EOF_INVENTORY
all:
  hosts:
    lab-debian-vps:
      ansible_host: ${TARGET_HOST}
      ansible_port: ${TARGET_PORT}
      ansible_user: root
      ansible_password: ${TARGET_ROOT_PASSWORD}
      ansible_ssh_common_args: "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
EOF_INVENTORY

cat >"$DEPLOY_INVENTORY" <<EOF_INVENTORY
all:
  hosts:
    lab-debian-vps:
      ansible_host: ${TARGET_HOST}
      ansible_port: ${TARGET_PORT}
      ansible_user: deploy
      ansible_ssh_private_key_file: ${KEY_PATH}
      ansible_ssh_common_args: "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
EOF_INVENTORY

cat >"$LAB_VARS" <<EOF_VARS
deployment_admin_user: deploy
deployment_admin_ssh_public_keys:
  - ${PUBLIC_KEY}
access_control_deploy_method: synchronize
access_control_source_path: /work
access_control_repo_url: ""
access_control_run_bootstrap: true
access_control_run_verify_after_deploy: false
access_control_command_environment:
  COMPOSE_DOCKER_CLI_BUILD: "0"
  DOCKER_BUILDKIT: "0"
caddy_enabled: true
caddy_tls_mode: internal
caddy_sites:
  - name: keycloak
    address: lab-auth.localhost
    upstream: "http://127.0.0.1:8080"
    tls_mode: internal
  - name: iam-api
    address: lab-iam.localhost
    upstream: "http://127.0.0.1:8000"
    tls_mode: internal
  - name: demo
    address: lab-demo.localhost
    upstream: "http://127.0.0.1:8001"
    tls_mode: internal
docker_daemon_config:
  storage-driver: vfs
vault_iam_service_token: lab-iam-service-token
vault_keycloak_bootstrap_admin_password: lab-keycloak-admin-password
vault_keycloak_backoffice_client_secret: lab-backoffice-client-secret
vault_keycloak_service_client_secret: lab-demo-service-client-secret
vault_keycloak_iam_control_plane_client_secret: lab-iam-control-plane-client-secret
vault_keycloak_super_admin_password: lab-super-admin-password
vault_keycloak_smoke_password: lab-smoke-member-password
vault_bootstrap_super_admin_email: super-admin@example.invalid
vault_bootstrap_super_admin_subject: lab-bootstrap-super-admin-subject
EOF_VARS

echo "Waiting for SSH on ${TARGET_HOST}:${TARGET_PORT}..."
for _ in $(seq 1 60); do
  if sshpass -p "$TARGET_ROOT_PASSWORD" ssh \
    -p "$TARGET_PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    "root@${TARGET_HOST}" true >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

sshpass -p "$TARGET_ROOT_PASSWORD" ssh \
  -p "$TARGET_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  "root@${TARGET_HOST}" true

ansible-galaxy collection install -r requirements.yml
ansible-playbook -i "$ROOT_INVENTORY" playbooks/provision.yml --syntax-check
ansible-playbook -i "$ROOT_INVENTORY" playbooks/deploy-access-control.yml --syntax-check

ansible-playbook -i "$ROOT_INVENTORY" playbooks/provision.yml -e "@${DEFAULT_VARS}" -e "@${LAB_VARS}"
ansible -i "$DEPLOY_INVENTORY" all -m ping

if [[ "$RUN_FULL_DEPLOY" == "1" ]]; then
  ansible-playbook -i "$DEPLOY_INVENTORY" playbooks/deploy-access-control.yml -e "@${DEFAULT_VARS}" -e "@${LAB_VARS}"
  curl --fail --silent --show-error --insecure --resolve "lab-auth.localhost:443:${TARGET_HOST}" \
    "https://lab-auth.localhost/realms/access-control-mvp/.well-known/openid-configuration" >/dev/null
  curl --fail --silent --show-error --insecure --resolve "lab-iam.localhost:443:${TARGET_HOST}" \
    "https://lab-iam.localhost/healthz" >/dev/null
  curl --fail --silent --show-error --insecure --resolve "lab-demo.localhost:443:${TARGET_HOST}" \
    "https://lab-demo.localhost/healthz" >/dev/null
  echo "Caddy reverse proxy TLS smoke checks passed."
else
  echo "Skipping full runtime deployment. Set LAB_RUN_FULL_DEPLOY=1 to run deploy-access-control.yml."
fi
