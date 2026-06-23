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
| `scripts/verify-onboarding.sh` | Runs `WP-003`: scripted authenticated-identity evidence plus safe and unsafe local onboarding decisions. |
| `scripts/verify-privileged-auth.sh` | Runs `WP-004`: scripted admin and super-admin authentication, token evidence, Keycloak `amr`/flow/event inspection, and local privileged-activation blocker decision. |
| `scripts/verify-claim-override.sh` | Runs `WP-005`: scripted misleading Keycloak role, group, and claim evidence plus local claim-override rejection decisions. |
| `scripts/verify-authorization-access-stop.sh` | Runs `WP-006`: scripted member authentication evidence plus PoC-only local `authorization/check`, fail-closed, and access-stop decisions. |
| `scripts/verify-audit-correlation.sh` | Runs `WP-007`: scripted member authentication evidence, supplemental Keycloak event evidence, PoC-only local audit examples, correlation checks, and audit-gap records. |
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

## Run WP-003 Safe And Unsafe Onboarding

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-onboarding.sh
```

Expected result:

- The script authenticates the verified non-production member user and the unverified unsafe user through Authorization Code flow with PKCE.
- The ID token signatures verify against the realm JWKS.
- ID token issuer, audience, nonce, time claims, email, email verification state, and `sub` are validated.
- UserInfo `sub` matches the ID token `sub`.
- A PoC-only local onboarding fixture activates exactly one invited `member` account with a verified matching email and no existing subject link.
- The local fixture denies no-invitation, duplicate-invitation, unverified-email, and pre-linked-subject cases.
- Denied cases do not mutate local accounts and do not create a local session.
- Local audit-shaped evidence is recorded for the safe activation and each denial.

For a reviewer-friendly explanation of what the script tests and how to read the generated evidence, see the [WP-003 result note](../../docs/poc/keycloak-wp003-result.md).

## Run WP-004 Privileged-Authentication Evidence

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-privileged-auth.sh
```

Expected result:

- The script authenticates the verified non-production `admin` and `super-admin` users through Authorization Code flow with PKCE.
- The ID token signatures verify against the realm JWKS.
- ID token issuer, audience, nonce, time claims, email, email verification state, and `sub` are validated.
- UserInfo `sub` matches the corresponding ID token `sub`.
- The script inspects client protocol mappers, the bound browser authentication flow, token `amr` values, and run-scoped Keycloak `LOGIN` / `CODE_TO_TOKEN` events.
- The local privileged-activation decision records either candidate explicit evidence or `blocked`. In the current default PoC configuration, `blocked` is expected because no AMR mapper or browser-flow reference value is configured.

Keycloak documents that authenticator executions can have reference values and that an AMR protocol mapper can populate the OIDC `amr` claim from successfully completed executions; OpenID Connect defines `amr` as an optional array of authentication-method identifiers ([Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows), [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)).

For a reviewer-friendly explanation of what the script tests and how to read the generated evidence, see the [WP-004 result note](../../docs/poc/keycloak-wp004-result.md).

## Run WP-005 Claim Override Rejection

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-claim-override.sh
```

Expected result:

- The script configures PoC-only Keycloak inputs that deliberately look dangerous: realm roles named like an account-management role and a service-access role, a group named like a privileged backoffice group, and hardcoded OIDC claims for `edrlab_account_type`, `edrlab_lifecycle_state`, and `edrlab_audit_bypass`.
- The script authenticates the verified non-production member user through Authorization Code flow with PKCE.
- The ID token signature, issuer, audience, nonce, verified email, `sub`, and time claims are validated.
- The access token signature, issuer, subject, authorized party, and time claims are validated before role evidence is used.
- UserInfo `sub` matches the ID token `sub`.
- Token/UserInfo evidence proves the misleading Keycloak roles, group, and claims are present.
- A PoC-only local authorization fixture denies account-management, disabled-account protected-service access, missing-local-role protected-service access, and audit-read attempts from local state.
- Denied cases do not mutate local account type, lifecycle state, subject link, or local service-access-role assignments.
- Local audit-shaped evidence is recorded even when the token contains the misleading `edrlab_audit_bypass` claim.

`WP-005` intentionally mutates the throwaway realm with misleading roles, group membership, and protocol mappers. Run `reset.sh` before later work packages if they should start from the baseline `WP-001` realm configuration.

For a reviewer-friendly explanation of what the script tests and how to read the generated evidence, see the [WP-005 result note](../../docs/poc/keycloak-wp005-result.md).

## Run WP-006 Authorization And Access Stop

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-authorization-access-stop.sh
```

Expected result:

- The script authenticates the verified non-production member user through Authorization Code flow with PKCE.
- The ID token signature, issuer, audience, nonce, verified email, `sub`, and time claims are validated.
- UserInfo `sub` matches the ID token `sub`.
- A PoC-only local `authorization/check` fixture allows an active linked member with an active covering local service-access role.
- The fixture denies unresolved subject, unavailable authorization result, disabled account, and active member with no local service-access role.
- The fixture records next-fresh-check denials after local account disablement, account archival, member service-access-role removal, and service-access-role disablement.
- Every access-stop case records that no positive authorization cache was used in the validation path.
- Local audit-shaped evidence is recorded for the authorization decisions.

`WP-006` does not require Keycloak roles, groups, or claims to be clean because the local evaluator ignores them. If the previous `WP-005` claim-override scenario was executed and a clean Keycloak realm is desired for review, run `reset.sh`, then rerun `start.sh`, `bootstrap.sh`, and `verify.sh` before `verify-authorization-access-stop.sh`.

For a reviewer-friendly explanation of what the script tests and how to read the generated evidence, see the [WP-006 result note](../../docs/poc/keycloak-wp006-result.md).

## Run WP-007 Audit Correlation

Run `WP-001` setup first, then:

```bash
bash poc/keycloak/scripts/verify-audit-correlation.sh
```

Expected result:

- The script authenticates the verified non-production member user through Authorization Code flow with PKCE.
- The ID token signature, issuer, audience, nonce, verified email, `sub`, and time claims are validated.
- UserInfo `sub` matches the ID token `sub`.
- Keycloak user events are collected for the run-scoped `LOGIN` and `CODE_TO_TOKEN` events.
- A PoC-only Keycloak admin-event probe updates a non-authoritative user attribute so the script can collect a run-scoped Keycloak admin `UPDATE` event as supplemental technical evidence.
- PoC-only local audit examples contain the accepted minimum schema fields and correlation IDs.
- The correlation map shows Keycloak events as supplemental evidence while local audit remains authoritative for local account resolution, protected-service authorization, and audit-read decisions.
- The audit-gap record explicitly states the expected gaps that this PoC does not prove: production append-only persistence, tamper resistance, retention, export, backup, restore, and privacy policy.

`WP-007` updates a non-authoritative attribute on the throwaway member user to create a Keycloak admin event probe. Run `reset.sh` before later work packages if a clean baseline realm is desired.

For a reviewer-friendly explanation of what the script tests and how to read the generated evidence, see the [WP-007 result note](../../docs/poc/keycloak-wp007-result.md).

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

`scripts/verify-onboarding.sh` writes:

- `wp-003-safe-member-token-response.json`
- `wp-003-safe-member-id-token-claims.json`
- `wp-003-safe-member-id-token-signature.txt`
- `wp-003-safe-member-userinfo.json`
- `wp-003-unverified-user-token-response.json`
- `wp-003-unverified-user-id-token-claims.json`
- `wp-003-unverified-user-id-token-signature.txt`
- `wp-003-unverified-user-userinfo.json`
- `wp-003-local-onboarding-inputs.json`
- `wp-003-onboarding-decisions.json`
- `wp-003-local-audit.json`
- `wp-003-event-window.json`
- `wp-003-keycloak-events.json`
- `wp-003-evidence.md`

`scripts/verify-privileged-auth.sh` writes:

- `wp-004-admin-token-response.json`
- `wp-004-admin-id-token-claims.json`
- `wp-004-admin-id-token-signature.txt`
- `wp-004-admin-userinfo.json`
- `wp-004-super-admin-token-response.json`
- `wp-004-super-admin-id-token-claims.json`
- `wp-004-super-admin-id-token-signature.txt`
- `wp-004-super-admin-userinfo.json`
- `wp-004-client-protocol-mappers.json`
- `wp-004-realm-flow-bindings.json`
- `wp-004-browser-flow-executions.json`
- `wp-004-event-window.json`
- `wp-004-keycloak-events.json`
- `wp-004-privileged-auth-decisions.json`
- `wp-004-local-audit.json`
- `wp-004-privileged-auth-summary.json`
- `wp-004-evidence.md`

`scripts/verify-claim-override.sh` writes:

- `wp-005-keycloak-override-setup.json`
- `wp-005-member-token-response.json`
- `wp-005-member-id-token-claims.json`
- `wp-005-member-id-token-signature.txt`
- `wp-005-member-access-token-claims.json`
- `wp-005-member-access-token-signature.txt`
- `wp-005-member-userinfo.json`
- `wp-005-local-authorization-inputs.json`
- `wp-005-claim-override-decisions.json`
- `wp-005-local-audit.json`
- `wp-005-claim-override-summary.json`
- `wp-005-event-window.json`
- `wp-005-keycloak-events.json`
- `wp-005-evidence.md`

`scripts/verify-authorization-access-stop.sh` writes:

- `wp-006-member-token-response.json`
- `wp-006-member-id-token-claims.json`
- `wp-006-member-id-token-signature.txt`
- `wp-006-member-userinfo.json`
- `wp-006-local-authorization-inputs.json`
- `wp-006-authorization-check-requests.json`
- `wp-006-authorization-check-responses.json`
- `wp-006-authorization-check-decisions.json`
- `wp-006-local-state-transitions.json`
- `wp-006-local-audit.json`
- `wp-006-authorization-access-stop-summary.json`
- `wp-006-event-window.json`
- `wp-006-keycloak-events.json`
- `wp-006-evidence.md`

`scripts/verify-audit-correlation.sh` writes:

- `wp-007-member-token-response.json`
- `wp-007-member-id-token-claims.json`
- `wp-007-member-id-token-signature.txt`
- `wp-007-member-userinfo.json`
- `wp-007-keycloak-admin-event-probe.json`
- `wp-007-event-window.json`
- `wp-007-keycloak-events.json`
- `wp-007-keycloak-admin-events.json`
- `wp-007-local-audit.json`
- `wp-007-audit-correlation-map.json`
- `wp-007-audit-gaps.json`
- `wp-007-audit-correlation-summary.json`
- `wp-007-evidence.md`

Generated evidence is ignored by Git by default. Summarize reviewable results in `docs/poc/` when closing a work package.

## Non-Production Limits

- The runtime uses Keycloak `start-dev`.
- The compose file is not production infrastructure.
- The users, emails, passwords, realm, client, and secrets are local PoC data only.
- Keycloak roles, groups, organizations, or token claims must not become EDRLab account type, lifecycle, service-access role, protected-service authorization, or audit authority.
- Production database, HA, backup, restore, monitoring, CI, migration, secret management, and deployment hardening are out of scope for this PoC runtime.
- `WP-002` uses a curl cookie jar as a browser simulation and a generated local account fixture. It is not a production BFF, UI, session store, protected-service implementation, or onboarding implementation.
- `WP-002` does not validate production cookie flags, HTTPS, CSRF protection, framework OIDC middleware, persistent session storage, protected-service authorization, safe onboarding activation, privileged-authentication evidence, or audit authority.
- `WP-003` uses a PoC-only local onboarding evaluator and JSON fixtures. It is not production onboarding code, persistent storage, a concurrency test, an administrator intervention workflow, or privileged-authentication evidence for admin or super-admin activation.
- `WP-004` uses PoC-only evidence inspection and blocker decisions. It does not configure a production MFA or passwordless policy, does not accept a final privileged authenticator set, and does not activate admin or super-admin accounts.
- `WP-005` intentionally adds misleading PoC-only Keycloak roles, group membership, and token/UserInfo claims to the non-production member user. These inputs are evidence hazards for the test only; they must not become EDRLab account type, lifecycle, service-access-role, protected-service authorization, or audit authority.
- `WP-005` uses a PoC-only local authorization evaluator and JSON fixtures. It is not production authorization middleware, a BFF, a protected backend service, persistent storage, or audit persistence.
- `WP-006` uses a PoC-only local `authorization/check` evaluator and JSON fixtures. It is not production middleware, BFF code, protected-service code, persistent storage, distributed cache behavior, or audit persistence.
- `WP-007` uses PoC-only local audit JSON fixtures and a Keycloak admin-event probe on a throwaway user attribute. It is not production append-only audit storage, tamper resistance, retention, export, backup, restore, privacy policy, or reconciliation logic.

## References

- [Keycloak validation plan](../../docs/poc/keycloak-validation-plan.md)
- [Keycloak setup runbook](../../docs/poc/keycloak-setup-runbook.md)
- [Keycloak container guide](https://www.keycloak.org/server/containers)
- [Keycloak OIDC endpoints and grant types](https://www.keycloak.org/securing-apps/oidc-layers)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [RFC 8176 - Authentication Method Reference Values](https://www.rfc-editor.org/rfc/rfc8176)
- [RFC 7636 - Proof Key for Code Exchange](https://www.rfc-editor.org/rfc/rfc7636)
