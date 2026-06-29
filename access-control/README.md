# Access-Control MVP Runtime

Status: Draft
Phase: Phase 6 - Production MVP
Scope: Runtime
Last reviewed: 2026-06-29

## Agent Brief

- Use this file as the required Phase 6 runtime runbook for Docker start, bootstrap, verification, evidence, backup, restore, stop, and reset.
- Use Linux shell examples. Do not add PowerShell or Windows runtime commands unless explicitly requested.
- Run MVP verification through Docker Compose; do not use local Python test execution for this runtime.
- MVP boundary lives in [docs/evaluation/mvp-scope.md](../docs/evaluation/mvp-scope.md).
- Endpoint schemas live in [access-control/docs/api.md](./docs/api.md).
- Security evidence status lives in [docs/evaluation/security-test-plan.md](../docs/evaluation/security-test-plan.md#test-tracker).
- Treat `.env.local`, generated evidence, and backups as local operational data that must not be committed.

## Contents

- [Agent Brief](#agent-brief)
- [Purpose](#purpose)
- [What This Slice Includes](#what-this-slice-includes)
- [Prerequisites](#prerequisites)
- [Environment](#environment)
- [Run](#run)
- [Super-Admin Bootstrap](#super-admin-bootstrap)
- [API Reference](#api-reference)
- [Onboarding Activation](#onboarding-activation)
- [Expected Outputs](#expected-outputs)
- [Evidence](#evidence)
- [Backup and Restore](#backup-and-restore)
- [Stop and Reset](#stop-and-reset)
- [Known MVP Shortcuts](#known-mvp-shortcuts)
- [References](#references)

## Purpose

This directory contains the required Phase 6 runtime runbook for the accepted access-control MVP scope: Keycloak, an IAM Control Plane API, an `access-check-demo-service`, append-only local audit storage, idempotent first-`super-admin` bootstrap, Linux scripts, Docker Compose runtime, and executable tests. The runtime follows the accepted MVP boundary and the supporting API, audit, authorization-check, schema, and security-test artifacts ([MVP scope](../docs/evaluation/mvp-scope.md), [Access-Control API Reference](./docs/api.md), [Authorization Check Behavior](../docs/architecture/authorization-check-behavior.md), [Audit Storage Architecture](../docs/architecture/audit-storage.md), [Keycloak IAM Schema Policy](../docs/architecture/keycloak-iam-schema-policy.md), [MVP Security Test Plan](../docs/evaluation/security-test-plan.md)).

This is production-scope code, not a Phase 4 PoC. It is still an early Phase 6 runtime: it now validates the protected-service subject-token path, service-to-service authentication, and Keycloak-backed IAM state through Keycloak/OIDC and Admin REST, but it does not yet include the Admin Console UI, full Keycloak IAM schema migration, or production operations hardening.

## What This Slice Includes

| Item | Included |
| --- | --- |
| Keycloak runtime | Local Docker Keycloak with a scripted MVP realm, managed EDRLab User Profile attributes, account-type roles, service-role metadata, canonical member service-role assignments in managed attributes, backoffice OIDC client, service client, IAM Control Plane service account, audience mapper, and smoke-test user. |
| IAM API | `GET /healthz`, `/iam/me`, Keycloak-backed account management, onboarding activation, service-role management, service-role assignment, `POST /iam/authorization/check`, super-admin audit reads, OIDC subject-token introspection, and OIDC service-token validation. |
| Demo protected service | `GET /access-check-demo`, returning JSON `OK` or `KO`, obtaining a client-credentials service token, and calling `POST /iam/authorization/check`. |
| Audit storage | Local append-only JSON Lines file with one complete event object per physical line. |
| Bootstrap | Scripted Keycloak realm/client/user/profile/role bootstrap plus idempotent first-`super-admin` bootstrap outside the public API and the initial `access-check-demo:consult` role. |
| Tests | Docker-only Python `unittest` coverage for bootstrap, actor authorization, onboarding, access checks, OIDC token validation, service authentication, access-stop behavior, audit format, and audit confidentiality. |
| Smoke test | Docker-only Authorization Code + PKCE login against Keycloak, local account activation, service-role assignment, and access-check demo call with a real Keycloak access token. |
| Runtime | Linux-first Docker Compose runtime for Keycloak, the IAM API, demo service, bootstrap, tests, and smoke verification. |

## Prerequisites

- Linux shell with Bash.
- Docker Engine with the Compose plugin.
- Network access to pull `python:3.12-slim` and the pinned Keycloak container image the first time Docker builds or starts the runtime.

All tests and runtime verification commands in this directory run through Docker Compose. Do not use local Python test execution for this MVP runtime.

## Environment

Create a local environment file:

```bash
cp access-control/.env.example access-control/.env.local
```

Edit `access-control/.env.local` and replace the placeholder secrets and bootstrap values. Do not commit `.env.local`.

The main variables are:

| Variable | Purpose |
| --- | --- |
| `IAM_SERVICE_TOKEN` | Shared local service token used by `access-check-demo-service` to call `POST /iam/authorization/check`. |
| `KEYCLOAK_IMAGE` | Pinned local Keycloak image used by Docker Compose. |
| `KEYCLOAK_REALM` | Local MVP realm name. |
| `KC_BOOTSTRAP_ADMIN_USERNAME` / `KC_BOOTSTRAP_ADMIN_PASSWORD` | Local Keycloak bootstrap administrator used by the scripted realm setup. |
| `KEYCLOAK_BACKOFFICE_CLIENT_ID` / `KEYCLOAK_BACKOFFICE_CLIENT_SECRET` | Confidential OIDC client used for the backoffice user Authorization Code flow and user-token introspection. |
| `KEYCLOAK_SERVICE_CLIENT_ID` / `KEYCLOAK_SERVICE_CLIENT_SECRET` | Confidential service client used by `access-check-demo-service` with OAuth client credentials. |
| `KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_ID` / `KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_SECRET` | Confidential Keycloak service-account client used by the IAM API to read and mutate managed IAM state through Keycloak Admin REST. |
| `KEYCLOAK_SUPER_ADMIN_USERNAME` / `KEYCLOAK_SUPER_ADMIN_PASSWORD` | Local non-production super-admin user used by Docker smoke verification of admin API calls. |
| `KEYCLOAK_BOOTSTRAP_RESET_FIXTURE_PASSWORDS` | Optional local recovery switch. Set to `true` only when the Keycloak bootstrap should reset existing non-production fixture user passwords. |
| `KEYCLOAK_SMOKE_USERNAME` / `KEYCLOAK_SMOKE_EMAIL` / `KEYCLOAK_SMOKE_PASSWORD` | Local non-production user used by the Docker smoke verification. |
| `BOOTSTRAP_SUPER_ADMIN_EMAIL` | First `super-admin` email used by the bootstrap process. |
| `BOOTSTRAP_SUPER_ADMIN_NAME` | First `super-admin` display name. |
| `BOOTSTRAP_SUPER_ADMIN_ORGANIZATION` | First `super-admin` organization. |
| `BOOTSTRAP_SUPER_ADMIN_SUBJECT` | Local development subject linked to the bootstrapped `super-admin`. |
| `ACCESS_CONTROL_BACKUP_DIR` | Optional host directory for local MVP backups. Defaults to `access-control/backups/`. |
| `ACCESS_CONTROL_BACKUP_IMAGE` | Optional helper image for backup and restore. Defaults to `busybox:1.36.1`. |

## Run

From the repository root:

```bash
bash access-control/scripts/start.sh
bash access-control/scripts/bootstrap.sh
bash access-control/scripts/verify.sh
```

The IAM API is exposed on `http://127.0.0.1:8000`. The demo protected service is exposed on `http://127.0.0.1:8001`. Keycloak is exposed on `http://127.0.0.1:8080`.

In the Docker runtime, `IAM_STATE_BACKEND=keycloak`. Account type, lifecycle, immutable subject link, organization, schema marker, service-role metadata, and member role assignments are read from and written to Keycloak through the IAM Control Plane API. The local runtime volume still holds audit JSONL and bootstrap evidence files, but `state.json` is not the canonical IAM account store.

The Docker smoke verification obtains a Keycloak access token through Authorization Code + PKCE and calls the demo service with that token. It also checks that an invalid bearer value returns `KO`.

## Super-Admin Bootstrap

The first `super-admin` bootstrap is run with:

```bash
bash access-control/scripts/bootstrap.sh
```

The bootstrap uses the `BOOTSTRAP_SUPER_ADMIN_*` environment values from
`access-control/.env.local`, creates or reuses the managed Keycloak realm state,
seeds the initial `access-check-demo:consult` service role, and creates the
first `super-admin` only when no active valid `super-admin` already exists. The
operation is idempotent and writes local audit/bootstrap evidence as part of the
runtime state.

## API Reference

Endpoint families, request schemas, response examples, and common error codes are documented in [access-control/docs/api.md](./docs/api.md). This runbook remains the required runtime entry point for starting, verifying, backing up, restoring, stopping, and resetting the Phase 6 MVP.

## Onboarding Activation

`POST /iam/onboarding/activate` is the transition from a pre-created `invited` account to an `active` linked account. It is called by the invited user after Keycloak authentication, not by an admin activating another account. This follows the accepted onboarding rule that a backoffice account is activated only when the IAM API can safely match one invited account to the authenticated subject's verified email ([Feature requirements `FR-043` and `FR-044`](../FEATURE-REQUIREMENTS.md#feature-requirements), [Access-Control API Reference - Onboarding](./docs/api.md#onboarding)).

Recommended MVP scenario:

1. An admin or super-admin creates the backoffice account through the IAM Control Plane API. The account starts in `invited` state, has `email`, `name`, `organization`, and `accountType`, and has no `linkedSubject`.
2. The controlled provisioning path creates or updates the matching user in the Keycloak MVP realm with the same email. Public registration remains disabled and routine direct Keycloak business administration remains out of scope for the MVP ([MVP scope - Out of Scope](../docs/evaluation/mvp-scope.md#out-of-scope)).
3. Keycloak sends the invited user an actions email for first login setup, instead of an EDRLab admin sending a reusable password. Keycloak documents SMTP-based realm email, per-user required actions, `execute-actions-email`, and password-reset/update-password emails ([Keycloak email configuration](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm), [Keycloak required actions](https://www.keycloak.org/docs/latest/server_admin/#setting-required-actions-for-one-user), [Keycloak Admin REST `execute-actions-email`](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_users_resource)).
4. For a `member`, the first-login actions should at least make the user own their credential and satisfy email verification before IAM activation. For an `admin` or `super-admin`, the actions must also satisfy the accepted privileged-authentication evidence requirement, using the MVP OTP direction where applicable ([MVP scope - Onboarding and Bootstrap](../docs/evaluation/mvp-scope.md#onboarding-and-bootstrap), [Keycloak creating an OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp)).
5. The user follows the Keycloak link or signs in through the Admin Console, completes the required Keycloak actions, and returns to the Admin Console with a user access token.
6. The Admin Console calls `POST /iam/onboarding/activate` with that bearer token. The IAM API activates the account only if the token evidence safely matches exactly one invited account.

Recommended Keycloak configuration for the MVP:

| Area | MVP setting |
| --- | --- |
| Realm email | Configure SMTP for the MVP realm so Keycloak can send verification and action emails. Keycloak sends verification, password, and event notification emails only after realm SMTP settings are configured ([Keycloak email configuration](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm)). |
| Public registration | Keep public registration disabled. Backoffice accounts are created only through authorized administration workflows. |
| Backoffice OIDC client | Use the `edrlab-backoffice` Authorization Code + PKCE client and allow only the Admin Console redirect URI used after first-login actions. |
| User creation | The controlled provisioning path creates or updates the Keycloak user that matches the IAM invited account email. |
| Required actions for `member` | Send `VERIFY_EMAIL` and `UPDATE_PASSWORD`, so the user proves email ownership and owns their credential before IAM activation. Keycloak supports required actions per user and default required actions for new users ([Keycloak required actions](https://www.keycloak.org/docs/latest/server_admin/#setting-required-actions-for-one-user)). |
| Required actions for `admin` and `super-admin` | Send `VERIFY_EMAIL`, `UPDATE_PASSWORD`, and `CONFIGURE_TOTP` where the MVP privileged-authentication flow uses OTP. Keycloak documents that when OTP is required, the user must configure an OTP generator at login ([Keycloak creating an OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp)). |
| Action email API | Use Keycloak Admin REST `PUT /admin/realms/{realm}/users/{user-id}/execute-actions-email` with the required-action list. Keycloak documents this endpoint as sending an email link for the user to execute selected actions ([Keycloak Admin REST users resource](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_users_resource)). |
| IAM activation | Do not mark the IAM account active from the provisioning step. Activation happens only when the invited user returns with validated token evidence and `POST /iam/onboarding/activate` succeeds. |

Example action email payloads:

```json
["VERIFY_EMAIL", "UPDATE_PASSWORD"]
```

```json
["VERIFY_EMAIL", "UPDATE_PASSWORD", "CONFIGURE_TOTP"]
```

The first payload is for `member` onboarding. The second is for privileged onboarding when the MVP OTP safeguard applies.

Onboarding activation call shape:

```http
POST /iam/onboarding/activate
Authorization: Bearer <keycloak-user-access-token>
Content-Type: application/json

{}
```

The IAM API validates the bearer token issuer, audience, expiry, subject, and expected OAuth client, extracts the authenticated `sub`, `email`, `email_verified`, and privileged-authentication evidence such as `acr`, then applies the safe match rules. The client must not provide `subject`, `emailVerified`, or `acr` as trusted request-body fields.

Expected caller flow:

1. Admin or super-admin creates the backoffice account in `invited` state.
2. The invited user signs in through Keycloak.
3. The Admin Console calls `GET /iam/me` with the user's bearer token.
4. If no active linked account is resolved, the Admin Console calls `POST /iam/onboarding/activate` with the same bearer token.
5. On success, the IAM API returns the activated account profile; subsequent `GET /iam/me` calls resolve normally.

For `admin` and `super-admin` accounts, activation also requires the accepted privileged-authentication evidence. Without it, the route denies activation and leaves the account in `invited` state ([MVP scope - Onboarding and Bootstrap](../docs/evaluation/mvp-scope.md#onboarding-and-bootstrap)).

## Expected Outputs

`verify.sh` should show:

- the Docker `unittest` security and contract tests pass;
- the Docker Keycloak smoke check returns JSON with `status: "ok"`;
- the smoke check proves a real Keycloak access token can authorize `access-check-demo-service`;
- the smoke check creates or reuses a member account whose lifecycle, subject link, account type, and service-role assignment are stored in Keycloak;
- the smoke check proves an invalid bearer value returns `KO`.

## Evidence

Collect local runtime evidence with:

```bash
bash access-control/scripts/collect-evidence.sh
```

Evidence is written to `access-control/evidence/<timestamp>/` and is ignored by Git. The evidence includes Docker Compose service status, the Docker test summary, and the Docker Keycloak smoke result.

## Backup and Restore

The local MVP stores durable runtime state in two Docker volumes:

- `edrlab-access-control-mvp_access-control-runtime` for local IAM runtime files, including audit JSONL;
- `edrlab-access-control-mvp_keycloak-data` for the local Keycloak data directory.

Audit files are durable MVP state and must be included in backup and restore planning before production data is trusted ([Audit Storage Architecture](../docs/architecture/audit-storage.md#backup-and-restore), [MVP scope - Production Readiness Gaps](../docs/evaluation/mvp-scope.md#production-readiness-gaps)).

Create a local backup from the repository root:

```bash
bash access-control/scripts/backup.sh
```

The script stops `keycloak`, `iam-api`, and `access-check-demo-service` before copying the volumes so the local Docker volume snapshot is consistent enough for this MVP runtime. It writes archives, a `SHA256SUMS` file, and a manifest under `access-control/backups/<timestamp>/`. Generated backup files are ignored by Git and must be treated as confidential operational data.

Restore a backup from the repository root:

```bash
RESTORE_CONFIRM=restore-access-control-mvp-state bash access-control/scripts/restore.sh access-control/backups/<timestamp>
bash access-control/scripts/start.sh
```

The restore script verifies checksums, stops the runtime services, clears the target Docker volumes, and restores the saved volume contents. It is intentionally gated by `RESTORE_CONFIRM` because it overwrites current local MVP runtime state. After restore, run `bootstrap.sh` only if the restored environment did not already include the expected Keycloak realm and first `super-admin`; otherwise run `verify.sh` to prove the restored runtime still serves the MVP path.

Known restore limitations for this Phase 6 slice:

- the backup is a local Docker-volume procedure, not a production hosted-backup design;
- encryption at rest, off-host retention, backup scheduling, and restore-test cadence remain deployment operations decisions;
- restoring onto a runtime with different secrets, image versions, or realm names is not guaranteed by this script.

## Stop and Reset

Stop without deleting state:

```bash
bash access-control/scripts/stop.sh
```

Delete the local Docker volume and generated evidence:

```bash
RESET_CONFIRM=delete-access-control-mvp-state bash access-control/scripts/reset.sh
```

## Known MVP Shortcuts

- `dev-sub:<subject>` remains available only for focused unit tests and non-OIDC local fallback paths.
- `FileStateStore` remains available for focused unit tests and non-OIDC local fallback paths. The Docker MVP runtime uses `KeycloakStateStore` as the IAM state backend.
- Admin Console-to-IAM API calls authenticate with bearer user tokens in the runtime. `X-Actor-Account-Id` is ignored unless `IAM_ALLOW_DEV_ACTOR_HEADER=true` is set explicitly for focused local tests.
- Onboarding activation now uses bearer-derived identity evidence and rejects request-body attempts to provide `subject`, `emailVerified`, `acr`, or other authorization-significant fields.
- Indeterminate Keycloak state read failures are fail-closed and create local audit events with `operation=iam.request.indeterminate` or `authorization.check.indeterminate`.
- The runtime does not include the Admin Console UI yet.
- Direct Keycloak drift detection is represented by invariant checks in this runtime, including rejection of direct protected-service role mappings on users. Member service-role assignments are stored in IAM Control Plane-managed attributes. Full migration reporting, reconciliation workflow, and production direct-admin governance remain outside this slice.
- The smoke-test user, realm, clients, redirect URI, and secrets are local runtime fixtures only.
- High availability, multi-replica Keycloak operation, advanced audit search/export, and real business protected-service integration remain outside the accepted MVP scope unless explicitly added.

## References

- [MVP Scope - Access-Control Production MVP](../docs/evaluation/mvp-scope.md)
- [Access-Control API Reference](./docs/api.md)
- [Authorization Check Behavior](../docs/architecture/authorization-check-behavior.md)
- [Audit Storage Architecture](../docs/architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../docs/architecture/keycloak-iam-schema-policy.md)
- [MVP Security Test Plan](../docs/evaluation/security-test-plan.md)
- [Keycloak - Configuring email for a realm](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm)
- [Keycloak - Required actions](https://www.keycloak.org/docs/latest/server_admin/#setting-required-actions-for-one-user)
- [Keycloak - Creating an OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp)
- [Keycloak Admin REST API - Users resource](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_users_resource)
