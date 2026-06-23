# Keycloak PoC Runtime

This is the executable runtime for the Phase 4 Keycloak validation plan. It is Linux-first, Docker-based, fully scripted, and non-production only.

It validates that a throwaway Keycloak realm can be created with an OIDC backoffice client, Authorization Code flow, no browser-token shortcuts, non-production users, event capture, and discovery evidence. It does not approve production adoption or production infrastructure.

## Prerequisites

- Linux shell with Bash.
- Docker Engine with the Compose plugin.
- `curl`.
- `jq`.
- `openssl`.
- `python3`.
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
| `scripts/verify-login-sso.sh` | Runs `WP-002`: scripted Authorization Code login, token validation, local `sub` resolution, local session decision, SSO check, and logout check. |
| `scripts/stop.sh` | Stops the runtime without deleting the volume. |
| `scripts/reset.sh` | Deletes local PoC state and generated evidence after explicit confirmation. |

## Setup

From the repository root:

```bash
cp poc/keycloak/.env.example poc/keycloak/.env.local
```

Edit `poc/keycloak/.env.local` and replace the placeholder passwords and client secret. Do not commit `.env.local`.

## Run WP-001 Setup

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

## Run WP-002 Login And SSO Boundary

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-login-sso.sh
```

Expected result:

- The script reaches the Keycloak login form for the non-production member user.
- The first Authorization Code flow returns a code after posting credentials to Keycloak.
- The backend-side token exchange succeeds with PKCE and the confidential client secret.
- The ID token signature verifies against the realm JWKS.
- ID token issuer, audience, nonce, time claims, verified email, and `sub` are validated.
- UserInfo `sub` matches the ID token `sub`.
- A PoC-only local account fixture resolves exactly one active account by `iss` + `sub`.
- A local session decision is recorded without writing raw tokens to evidence.
- A second `prompt=none` authorization succeeds through the existing Keycloak SSO session without posting credentials again.
- Keycloak logout redirects to the local logout callback, and a post-logout `prompt=none` request no longer returns an authorization code.

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

`scripts/verify-login-sso.sh` writes:

- `wp-002-first-token-response.json`
- `wp-002-id-token-claims.json`
- `wp-002-id-token-signature.txt`
- `wp-002-userinfo.json`
- `wp-002-local-accounts.json`
- `wp-002-local-session.json`
- `wp-002-second-token-response.json`
- `wp-002-second-id-token-claims.json`
- `wp-002-login-sso-trace.json`
- `wp-002-keycloak-events.json`
- `wp-002-evidence.md`

Generated evidence is ignored by Git by default. Summarize reviewable results in `docs/poc/` when closing a work package.

## Non-Production Limits

- The runtime uses Keycloak `start-dev`.
- The compose file is not production infrastructure.
- The users, emails, passwords, realm, client, and secrets are local PoC data only.
- Keycloak roles, groups, organizations, or token claims must not become EDRLab account type, lifecycle, service-access role, protected-service authorization, or audit authority.
- Production database, HA, backup, restore, monitoring, CI, migration, secret management, and deployment hardening are out of scope for this PoC runtime.
- `WP-002` uses a curl cookie jar as a browser simulation and a generated local account fixture. It is not a production BFF, UI, session store, protected-service implementation, or onboarding implementation.
- `WP-002` does not validate production cookie flags, HTTPS, CSRF protection, framework OIDC middleware, persistent session storage, protected-service authorization, safe onboarding activation, privileged-authentication evidence, or audit authority.

## References

- [Keycloak validation plan](../../docs/poc/keycloak-validation-plan.md)
- [Keycloak setup runbook](../../docs/poc/keycloak-setup-runbook.md)
- [Keycloak container guide](https://www.keycloak.org/server/containers)
- [Keycloak OIDC endpoints and grant types](https://www.keycloak.org/securing-apps/oidc-layers)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [RFC 7636 - Proof Key for Code Exchange](https://www.rfc-editor.org/rfc/rfc7636)
