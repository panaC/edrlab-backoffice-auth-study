# Keycloak Setup Runbook

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-05

## Contents

- [Purpose](#purpose)
- [Setup Boundaries](#setup-boundaries)
- [Runtime Inputs](#runtime-inputs)
- [Setup Steps](#setup-steps)
- [Evidence To Collect](#evidence-to-collect)
- [Stop Conditions](#stop-conditions)
- [References](#references)

## Purpose

This runbook starts `WP-001` from the accepted [Keycloak validation plan](./keycloak-validation-plan.md#work-packages). Its goal is to create a minimal, throwaway Keycloak runtime that can support later login, SSO boundary, onboarding, privileged-authentication evidence, and authorization-check scenarios without starting production implementation ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The expected output is the executable PoC workspace at [poc/keycloak](../../poc/keycloak/README.md) plus evidence: realm/client settings, discovery endpoint values, event settings, test-user setup notes, and explicit limitations for Phase 5 review ([Keycloak validation plan - Evidence Record](./keycloak-validation-plan.md#evidence-record)).

## Setup Boundaries

| Boundary | Rule | Reason |
| --- | --- | --- |
| Runtime | Use a throwaway local or isolated non-production Keycloak runtime. Keycloak documents `start-dev` as a development mode for trying Keycloak quickly, and also says development mode has defaults intended for development, not production ([Keycloak configuration](https://www.keycloak.org/server/configuration), [Keycloak container guide](https://www.keycloak.org/server/containers)). | Keeps Phase 4 evidence separate from production infrastructure. |
| Data | Use only non-production users, emails, passwords, realm names, client names, redirect URIs, and secrets. | Prevents accidental production coupling during evidence collection. |
| Files | Add a Linux-targeted Docker runtime definition for runtime execution, preferably `compose.yaml` or `docker-compose.yml`; add a `Dockerfile` only if a custom image is needed. Do not add CI files, generated realm exports, migrations, production databases, package managers, production dependencies, or production deployment artifacts in this step. | Preserves the Phase 4 boundary and the user-provided Linux/Docker PoC rule in [AGENTS](../../AGENTS.md#current-operating-phase). |
| Scriptability | Script setup, start, verification, evidence collection, stop, and reset/cleanup where applicable. Manual Admin Console actions are inspection-only; if a core setup or validation step cannot be scripted, record `blocked` or `partial-manual` evidence. | Preserves the user-provided rule that each runtime PoC must be fully scripted and documented. |
| Authorization | Do not model EDRLab account type, lifecycle, service-access roles, or protected-service authorization in Keycloak roles, groups, organizations, or claims. | The accepted solution keeps local access-control authoritative (`FR-001`, `FR-002`, `FR-020`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Browser flow | Validate Authorization Code flow for a BFF or server-side local session pattern. Keycloak documents Authorization Code as redirecting the user agent to Keycloak, then exchanging the returned code for tokens; its OIDC endpoint documentation also lists discovery, authorization, token, userinfo, logout, and certificate endpoints ([Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)). | Keeps credentials at Keycloak and avoids browser token ownership as the first validation pattern. |
| Forbidden shortcut | Do not use Implicit Flow or Resource Owner Password Credentials for this browser PoC. Keycloak's own OIDC guide says Implicit has security risks and cites OAuth 2.0 Security BCP; it also says Resource Owner Password Credentials must not be used under the current BCP ([Keycloak OIDC grant types](https://www.keycloak.org/securing-apps/oidc-layers), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)). | Keeps the PoC aligned with modern OAuth/OIDC security guidance. |

## Runtime Inputs

Use these names unless a later runtime constraint requires a change:

| Input | Proposed value | Evidence note |
| --- | --- | --- |
| Realm | `edrlab-backoffice-poc` | Record the final realm name and base URL. |
| Client | `backoffice-bff-poc` | Record whether the client is confidential, which redirect URIs are allowed, and whether PKCE is configured. |
| Redirect URI | `http://localhost:<backoffice-port>/auth/callback` | Replace `<backoffice-port>` with the actual local test port. |
| Logout redirect URI | `http://localhost:<backoffice-port>/logout/callback` | Record whether logout is front-channel, back-channel, or only observed as a Keycloak session event in WP-001. |
| Member user | `kc-member-poc` | Use a non-production email that maps to the future invited local `member` test account. |
| Admin user | `kc-admin-poc` | Use a non-production email that maps to the future invited local `admin` test account. |
| Super-admin user | `kc-super-admin-poc` | Use a non-production email that maps to the future invited local `super-admin` test account. |
| Unsafe user | `kc-unsafe-poc` | Use for no-invitation, duplicate-invitation, unverified-email, or pre-linked-subject cases in later work packages. |

## Setup Steps

1. Prepare the PoC Docker runtime.

   Create the runtime under [poc/keycloak](../../poc/keycloak/README.md), with `compose.yaml` as the Docker runtime definition. Keep it Linux-oriented and PoC-only. If using a container, the official Keycloak container guide documents `start-dev` for development/testing and warns that this mode should be avoided in production ([Keycloak container guide](https://www.keycloak.org/server/containers)).

   ```yaml
   services:
     keycloak:
       image: quay.io/keycloak/keycloak:<pinned-version>
       command: start-dev
       ports:
         - "127.0.0.1:8080:8080"
       environment:
         KC_BOOTSTRAP_ADMIN_USERNAME: ${KC_BOOTSTRAP_ADMIN_USERNAME}
         KC_BOOTSTRAP_ADMIN_PASSWORD: ${KC_BOOTSTRAP_ADMIN_PASSWORD}
   ```

   Store temporary credentials outside the committed compose file, for example in local shell variables or an untracked `.env.local` file.

2. Prepare the PoC script set.

   The first executable PoC pass should include these Linux shell scripts under the PoC workspace:

   | Script | Responsibility |
   | --- | --- |
   | `scripts/start.sh` | Start the Docker runtime and wait for Keycloak readiness. |
   | `scripts/bootstrap.sh` | Create or update the realm, OIDC client, redirect/logout URIs, users, required actions, event settings, and rejected shortcut settings. |
   | `scripts/verify.sh` | Verify discovery endpoint, issuer, client flow settings, test users, event settings, and rejected shortcuts. |
   | `scripts/collect-evidence.sh` | Write sanitized runtime notes and command outputs needed for the WP-001 evidence record. |
   | `scripts/stop.sh` | Stop the PoC runtime without deleting reusable local state unless explicitly requested. |
   | `scripts/reset.sh` | Remove the PoC runtime state and return to a clean WP-001 starting point. |

   Evidence: script paths, documented `bash` commands, documented inputs, documented outputs, and any intentionally unsupported operation.

3. Document the PoC workspace.

   Add a local `README.md` beside the compose file. It must explain Linux prerequisites, environment variables, exact commands, expected outputs, evidence location, stop/reset commands, and non-production limitations. Keep secrets out of committed files.

   Evidence: README path and confirmation that a reviewer can run the PoC from a clean checkout.

4. Start the isolated Keycloak runtime.

   ```bash
   bash poc/keycloak/scripts/start.sh
   ```

   Evidence: Keycloak base URL, version or image tag, start mode, admin bootstrap method, and a note that the runtime is throwaway.

5. Bootstrap the `edrlab-backoffice-poc` realm.

   The bootstrap script should create or update the realm without relying on manual Admin Console setup. Keycloak describes a realm as the isolated container for users, clients, roles, and authentication flows ([Keycloak server administration guide](https://www.keycloak.org/docs/latest/server_admin/)). Keep the `master` realm only for Keycloak administration.

   Evidence: realm name, creation timestamp, and screenshot or sanitized notes.

6. Bootstrap the `backoffice-bff-poc` OIDC client.

   The bootstrap script should configure the client for Authorization Code flow and the planned local redirect/logout URI. Keycloak's OIDC guide documents the authorization endpoint, token endpoint, userinfo endpoint, logout endpoint, certificate endpoint, and well-known discovery endpoint used by OIDC clients ([Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)).

   Evidence: client ID, client type, redirect URIs, logout URIs, selected grant/flow settings, token/session settings, and whether PKCE is enabled.

7. Disable browser-flow shortcuts that would weaken the validation.

   The bootstrap or verification script should prove that Implicit Flow and Direct Access Grants are disabled for this PoC unless a later documented test explicitly needs to prove rejection. Keycloak's OIDC guide flags Implicit Flow security risks and says Resource Owner Password Credentials should not be used under the current OAuth security BCP ([Keycloak OIDC grant types](https://www.keycloak.org/securing-apps/oidc-layers), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)).

   Evidence: selected client flow settings and rejected shortcut list.

8. Bootstrap non-production Keycloak users.

   The bootstrap script should create one user for each planned account type and one unsafe-case user. Do not assign Keycloak roles or groups that would be interpreted as EDRLab account type or service-access role evidence. The accepted boundary rejects Keycloak roles, groups, organizations, and claims as authoritative EDRLab authorization state ([Solution choice - Why Keep Access-Control Local](../evaluation/solution-choice.md#why-keep-access-control-local), `FR-038`).

   Evidence: usernames, verified/unverified email flags, password or required-action policy notes, and confirmation that no Keycloak role/group is used as EDRLab authority.

9. Enable authentication and admin event capture.

   The bootstrap script should enable the event settings needed for WP-001 and later audit-correlation review. Keycloak documents user-event auditing through realm event settings and says successful login, incorrect password, account update, logout, and code-to-token events are event types that can be saved. Keycloak also documents admin-event auditing for actions performed through the Admin Console, with an optional representation setting that stores JSON documents sent through the Admin REST API ([Keycloak user events](https://www.keycloak.org/docs/latest/server_admin/#auditing-user-events), [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

   Evidence: user-event setting, selected saved event types, expiration setting, admin-event setting, include-representation setting, and any privacy/storage caveat.

10. Capture OIDC discovery data.

   Open:

   ```text
   http://localhost:8080/realms/edrlab-backoffice-poc/.well-known/openid-configuration
   ```

   Keycloak documents the well-known endpoint as the place where applications can discover OIDC endpoints and configuration options ([Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)).

   Evidence: issuer, authorization endpoint, token endpoint, userinfo endpoint, logout endpoint, certificate/JWKS endpoint, and supported response/grant information relevant to the PoC.

11. Record the first WP-001 evidence entry.

   Use the [evidence-record template](./keycloak-validation-plan.md#evidence-record) and mark the scenario as `pass`, `fail`, `partial-manual`, or `blocked`. A pass means the Docker runtime, scripts, documentation, realm, client, users, events, and discovery endpoint are configured well enough to start `WP-002`.

## Evidence To Collect

| Evidence | Minimum content |
| --- | --- |
| Docker runtime note | Path to `compose.yaml` or `docker-compose.yml`, image tag, exposed local port, environment-variable handling, and PoC-only warning. |
| Script note | Script paths for start, bootstrap, verify, evidence collection, stop, and reset; documented `bash` commands; documented inputs and outputs. |
| Documentation note | PoC workspace `README.md`, exact Linux commands, expected outputs, evidence location, stop/reset instructions, and non-production limitations. |
| Runtime note | Keycloak version/image tag, base URL, start mode, and non-production warning. |
| Realm note | Realm name, why it is isolated, and whether any production data was avoided. |
| Client note | Client ID, redirect/logout URIs, grant/flow settings, token/session settings, and PKCE status. |
| User note | Four test users, email verification state, required actions, and no authoritative local roles/groups. |
| Event note | User/admin event settings, saved event types, expiration, include-representation status, and storage/privacy caveat. |
| Discovery note | Issuer, auth/token/userinfo/logout/certs endpoints, and any mismatch with expected local URLs. |
| Boundary note | Explicit statement that account type, lifecycle, subject link, service-access roles, protected-service authorization, and local audit remain outside Keycloak. |

## Stop Conditions

Stop WP-001 and record `blocked` if any of these happen:

- Keycloak cannot be started locally or in an isolated non-production environment.
- A Linux-targeted Docker runtime definition cannot be produced for the PoC.
- The PoC cannot be executed by scripts from a clean Linux checkout.
- The OIDC discovery endpoint is unavailable or reports an issuer/base URL that cannot support the local redirect path.
- The client cannot be configured without enabling Implicit Flow or Resource Owner Password Credentials.
- Event settings cannot capture enough authentication/admin evidence to support later audit-correlation review.
- The setup starts requiring production infrastructure, production users, production secrets, committed generated configuration, CI, migrations, or durable deployment artifacts.

## References

- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Feature Requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)
- [Solution Choice - Why Keep Access-Control Local](../evaluation/solution-choice.md#why-keep-access-control-local)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak Configuration](https://www.keycloak.org/server/configuration)
- [Keycloak Container Guide](https://www.keycloak.org/server/containers)
- [Keycloak OIDC Endpoints and Grant Types](https://www.keycloak.org/securing-apps/oidc-layers)
- [Keycloak User Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-user-events)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
