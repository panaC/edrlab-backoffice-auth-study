# Keycloak PoC Runtime

This is the executable runtime for `WP-001` from the Phase 4 Keycloak validation plan. It is Linux-first, Docker-based, fully scripted, and non-production only.

It validates that a throwaway Keycloak realm can be created with an OIDC backoffice client, Authorization Code flow, no browser-token shortcuts, non-production users, event capture, and discovery evidence. It does not approve production adoption or production infrastructure.

## Prerequisites

- Linux shell with Bash.
- Docker Engine with the Compose plugin.
- `curl`.
- `jq`.
- Network access to pull the pinned Keycloak container image the first time.

## Files

| Path | Purpose |
| --- | --- |
| `compose.yaml` | PoC-only Keycloak runtime. |
| `.env.example` | Template for local non-production settings. |
| `.env.local` | Local secret/config file, ignored by Git. |
| `scripts/start.sh` | Starts Keycloak and waits for readiness. |
| `scripts/bootstrap.sh` | Creates or updates the realm, client, users, event settings, and rejected shortcut settings. |
| `scripts/verify.sh` | Verifies discovery, client settings, users, and events. |
| `scripts/collect-evidence.sh` | Collects sanitized evidence into `evidence/<timestamp>/`. |
| `scripts/stop.sh` | Stops the runtime without deleting the volume. |
| `scripts/reset.sh` | Deletes local PoC state and generated evidence after explicit confirmation. |

## Setup

From the repository root:

```bash
cp poc/keycloak/.env.example poc/keycloak/.env.local
```

Edit `poc/keycloak/.env.local` and replace the placeholder passwords and client secret. Do not commit `.env.local`.

## Run

```bash
bash poc/keycloak/scripts/start.sh
bash poc/keycloak/scripts/bootstrap.sh
bash poc/keycloak/scripts/verify.sh
bash poc/keycloak/scripts/collect-evidence.sh
```

Expected result:

- Keycloak is reachable at `http://localhost:8080`.
- Realm `edrlab-backoffice-poc` exists.
- Client `backoffice-bff-poc` exists.
- Authorization Code flow is enabled.
- Implicit Flow is disabled.
- Direct Access Grants are disabled.
- Four non-production users exist.
- The unsafe user keeps `emailVerified=false`.
- User and admin events are enabled.
- Evidence is written under `poc/keycloak/evidence/<timestamp>/`.

## Stop

```bash
bash poc/keycloak/scripts/stop.sh
```

## Reset

This deletes the local PoC Keycloak volume and generated evidence. It does not touch production data because this runtime is local and PoC-only.

```bash
RESET_CONFIRM=delete-poc-state bash poc/keycloak/scripts/reset.sh
```

## Evidence

`scripts/collect-evidence.sh` writes:

- `discovery.json`
- `client.json`
- `users.json`
- `events-config.json`
- `compose-ps.txt`
- `keycloak-logs-tail.txt`
- `wp-001-evidence.md`

Generated evidence is ignored by Git by default. Summarize reviewable results in `docs/poc/` when closing a work package.

## Non-Production Limits

- The runtime uses Keycloak `start-dev`.
- The compose file is not production infrastructure.
- The users, emails, passwords, realm, client, and secrets are local PoC data only.
- Keycloak roles, groups, organizations, or token claims must not become EDRLab account type, lifecycle, service-access role, protected-service authorization, or audit authority.
- Production database, HA, backup, restore, monitoring, CI, migration, secret management, and deployment hardening are out of scope for `WP-001`.

## References

- [Keycloak validation plan](../../docs/poc/keycloak-validation-plan.md)
- [Keycloak setup runbook](../../docs/poc/keycloak-setup-runbook.md)
- [Keycloak container guide](https://www.keycloak.org/server/containers)
- [Keycloak OIDC endpoints and grant types](https://www.keycloak.org/securing-apps/oidc-layers)
