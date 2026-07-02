# Access-Control Ansible Deployment

Status: Draft
Phase: Phase 6 - Production MVP
Scope: Runtime deployment
Last reviewed: 2026-07-02

## Contents

- [Purpose](#purpose)
- [Current Boundary](#current-boundary)
- [Prerequisites](#prerequisites)
- [Inventory](#inventory)
- [First Run](#first-run)
- [Reverse Proxy](#reverse-proxy)
- [Playbooks](#playbooks)
- [Evidence](#evidence)
- [Security Posture](#security-posture)
- [Known Limitations](#known-limitations)
- [References](#references)

## Purpose

This Ansible slice provisions a freshly installed Debian VPS for the accepted
Phase 6 access-control MVP runtime. It installs a hardened single-host Docker
baseline, deploys the existing `access-control/` Docker Compose runtime, renders
`access-control/.env.local` from Ansible-managed variables, runs bootstrap, and
can run the existing Docker verification and evidence scripts.

## Current Boundary

The deployment remains inside the accepted single-host Docker MVP boundary from
`docs/evaluation/mvp-scope.md`. It does not add high availability, a multi-node
Keycloak topology, real business protected-service integration, or advanced
audit export/search.

The runtime services are bound to `127.0.0.1` by default. Public HTTPS exposure
is handled by the optional Caddy reverse-proxy role.

With the reverse proxy disabled, browser-based human testing on a remote VPS
requires an SSH tunnel.

## Prerequisites

From the Ansible control machine:

```bash
cd deployment/ansible
ansible-galaxy collection install -r requirements.yml
cp inventories/production/hosts.example.yml inventories/production/hosts.yml
cp inventories/production/group_vars/vault.example.yml inventories/production/group_vars/vault.yml
ansible-vault encrypt inventories/production/group_vars/vault.yml
```

Edit:

- `inventories/production/hosts.yml` with the VPS IP address and first SSH user.
- `inventories/production/group_vars/all.yml` with the deploy user, SSH public
  key, repository URL, branch or tag, and runtime defaults.
- `inventories/production/group_vars/vault.yml` with generated secrets.

`hosts.yml` and `vault.yml` are ignored by Git. Commit only the example files
unless an encrypted inventory file is intentionally accepted later.

## Inventory

The first connection to a clean VPS commonly uses `root` over the provider's
default SSH configuration:

```yaml
all:
  hosts:
    access-control-vps:
      ansible_host: 203.0.113.10
      ansible_user: root
      ansible_port: 22
```

Set `deployment_admin_ssh_public_keys` before running `provision.yml`. The base
role refuses to continue without at least one key because the SSH hardening role
disables password login and root login by default.

## First Run

Provision the host first:

```bash
ansible-playbook playbooks/provision.yml --ask-vault-pass
```

After `provision.yml`, change the inventory to connect as the managed admin
user:

```yaml
ansible_user: deploy
```

Then deploy and verify:

```bash
ansible-playbook playbooks/deploy-access-control.yml --ask-vault-pass
ansible-playbook playbooks/reverse-proxy.yml --ask-vault-pass
ansible-playbook playbooks/verify.yml --ask-vault-pass
```

For already-provisioned hosts where the inventory uses the managed admin user,
the full sequence is:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

## Reverse Proxy

The Caddy role is opt-in because public TLS requires real DNS names pointing at
the VPS before certificate issuance can work. To enable it, set:

```yaml
caddy_enabled: true
caddy_email: ops@example.org
public_keycloak_fqdn: auth.example.org
public_iam_fqdn: iam.example.org
public_demo_fqdn: demo.example.org
```

The default Caddy sites proxy:

| Public host | Local upstream |
| --- | --- |
| `public_keycloak_fqdn` | `127.0.0.1:8080` |
| `public_iam_fqdn` | `127.0.0.1:8000` |
| `public_demo_fqdn` | `127.0.0.1:8001` |

For production, keep the Docker services bound to loopback and expose only
ports `80` and `443` through Caddy. The role rejects placeholder
`example.invalid` hostnames when `caddy_tls_mode` is `public`.

For disposable lab or private-network tests, use internal Caddy certificates:

```yaml
caddy_enabled: true
caddy_tls_mode: internal
```

After changing Caddy variables, run:

```bash
ansible-playbook playbooks/reverse-proxy.yml --ask-vault-pass
```

## Playbooks

| Playbook | Purpose |
| --- | --- |
| `playbooks/provision.yml` | Installs base packages, creates the managed admin user, configures unattended upgrades, installs Docker Engine and Compose, enables UFW, and installs the SSH hardening drop-in. |
| `playbooks/deploy-access-control.yml` | Checks out the repository, writes `access-control/.env.local`, runs `start.sh`, and runs `bootstrap.sh`. |
| `playbooks/reverse-proxy.yml` | Installs Caddy, renders `/etc/caddy/Caddyfile`, validates it, enables the service, and proxies configured public hostnames to the loopback runtime. |
| `playbooks/verify.yml` | Runs `verify.sh` and `collect-evidence.sh` through the deployed Docker runtime. |
| `playbooks/backup.yml` | Runs the existing local Docker-volume backup script. |

## Evidence

The verification playbook uses the existing runtime evidence flow:

```bash
ansible-playbook playbooks/verify.yml --ask-vault-pass
```

Expected runtime evidence is still written under `access-control/evidence/` on
the VPS, matching the access-control runbook. Backups are still local
Docker-volume backups created under `access-control/backups/` unless the
deployment is extended with off-host retention.

## Docker Lab

Use `test-lab/` to exercise the playbooks from an Ansible control container
against a minimal Debian SSH target on a dedicated Docker bridge IP:

```bash
cd deployment/ansible/test-lab
docker compose build
docker compose up -d debian-vps
docker compose run --rm ansible-control
```

The default lab verifies provisioning and post-hardening SSH access as the
managed deploy user. Set `LAB_RUN_FULL_DEPLOY=1` to attempt the full
access-control runtime deployment inside the target container and verify Caddy
over HTTPS using internal lab certificates.

## Security Posture

The first baseline applies:

- key-only SSH for the managed admin user;
- disabled root SSH login after the initial provisioning pass;
- UFW default-deny inbound firewall rules with SSH, HTTP, and HTTPS allowed;
- unattended security upgrades;
- Docker installed from the Docker Debian repository;
- runtime secrets rendered from Ansible variables into a `0600` `.env.local`;
- optional Caddy HTTPS reverse proxy with Caddyfile validation before reload;
- Keycloak, IAM API, demo service, and Mailpit host bindings set to loopback by
  default.

## Known Limitations

- This is a deployment baseline, not a production-readiness declaration.
- External Keycloak hostname behavior, monitoring, alerting, off-host encrypted
  backups, restore-test cadence, incident response, and rollback evidence still
  need explicit verification, implementation, or accepted risk.
- The access-control runtime still has the MVP limitations documented in
  `access-control/README.md`, including no Admin Console UI and no high
  availability.
- Direct production use requires closing or explicitly deferring the remaining
  operations and security evidence gaps in `docs/evaluation/mvp-scope.md` and
  `docs/evaluation/security-test-plan.md`.

## References

- `access-control/README.md`
- `docs/evaluation/mvp-scope.md`
- `docs/evaluation/security-test-plan.md`
