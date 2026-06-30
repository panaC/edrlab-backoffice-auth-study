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
- Endpoint schemas live in [docs/architecture/iam-control-plane-api-contract.md](../docs/architecture/iam-control-plane-api-contract.md).
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
- [Expected Outputs](#expected-outputs)
- [Human E2E Testing](#human-e2e-testing)
- [Evidence](#evidence)
- [Backup and Restore](#backup-and-restore)
- [Stop and Reset](#stop-and-reset)
- [Known MVP Shortcuts](#known-mvp-shortcuts)
- [References](#references)

## Purpose

- Runtime runbook for the accepted Phase 6 access-control MVP: Dockerized Keycloak, IAM Control Plane API, `access-check-demo-service`, local append-only audit storage, first-`super-admin` bootstrap, Linux scripts, tests, and current MVP limitations ([MVP scope](../docs/evaluation/mvp-scope.md), [IAM Control Plane API Contract](../docs/architecture/iam-control-plane-api-contract.md)).
- Production-scope Phase 6 code that validates Keycloak/OIDC-backed IAM state and protected-service authorization, with Admin Console UI, full Keycloak IAM schema migration, and production operations hardening still open.

## What This Slice Includes

| Item | Included |
| --- | --- |
| Keycloak runtime | Local Docker Keycloak with a scripted MVP realm, managed IAM User Profile attributes, account-type roles, service-role metadata, canonical member service-role assignments in managed attributes, backoffice OIDC client, service client, IAM Control Plane service account, user-token and service-token audience mappers, invited-user required actions for onboarding, optional Keycloak action-email dispatch, OTP step-up ACR/LoA configuration for privileged onboarding, and smoke-test user. |
| IAM API | `GET /healthz`, `/iam/me`, Keycloak-backed account management, onboarding activation, service-role management, service-role assignment, `POST /iam/authorization/check`, super-admin audit reads, OIDC subject-token introspection, and OIDC service-token validation. |
| Demo protected service | Split into `access-control/src/access_check_demo_service/`; exposes `GET /access-check-demo`, returns JSON `OK` or `KO`, obtains a client-credentials service token, and calls `POST /iam/authorization/check`. |
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
| `KEYCLOAK_BACKOFFICE_REDIRECT_URI` | Redirect URI used by the local backoffice Authorization Code flow and optional onboarding action-email links. |
| `KEYCLOAK_ONBOARDING_ACTION_EMAILS` | Optional Keycloak `execute-actions-email` dispatch for newly invited accounts. Defaults to `false` because the local Docker runtime does not configure SMTP. |
| `KEYCLOAK_ONBOARDING_ACTION_EMAIL_LIFESPAN_SECONDS` | Optional action-email link lifespan when `KEYCLOAK_ONBOARDING_ACTION_EMAILS=true`. Leave empty to use Keycloak's default. |
| `KEYCLOAK_SMTP_HOST` / `KEYCLOAK_SMTP_PORT` / `KEYCLOAK_SMTP_FROM` | Local SMTP settings used by the onboarding email e2e script when it configures Keycloak for Mailpit. |
| `MAILPIT_IMAGE` / `MAILPIT_API_BASE_URL` | Mailpit container image and in-network API URL used by the onboarding email e2e script. |
| `KEYCLOAK_SERVICE_CLIENT_ID` / `KEYCLOAK_SERVICE_CLIENT_SECRET` | Confidential service client used by `access-check-demo-service` with OAuth client credentials. |
| `KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_ID` / `KEYCLOAK_IAM_CONTROL_PLANE_CLIENT_SECRET` | Confidential Keycloak service-account client used by the IAM API to read and mutate managed IAM state through Keycloak Admin REST. |
| `KEYCLOAK_SUPER_ADMIN_USERNAME` / `KEYCLOAK_SUPER_ADMIN_PASSWORD` | Local non-production super-admin user used by Docker smoke verification of admin API calls. |
| `KEYCLOAK_BOOTSTRAP_RESET_FIXTURE_PASSWORDS` | Optional local recovery switch. Set to `true` only when the Keycloak bootstrap should reset existing non-production fixture user passwords. |
| `KEYCLOAK_SMOKE_USERNAME` / `KEYCLOAK_SMOKE_EMAIL` / `KEYCLOAK_SMOKE_PASSWORD` | Local non-production user used by the Docker smoke verification. |
| `IAM_NORMAL_ACR` | Non-privileged ACR value mapped to Keycloak LoA 1. Defaults to `iam-normal`. |
| `IAM_PRIVILEGED_ACR` | Privileged ACR value required by IAM onboarding for `admin` and `super-admin` activation and mapped to Keycloak LoA 2. Defaults to `iam-privileged`. |
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

Endpoint families, request schemas, response examples, and common error codes are documented in [docs/architecture/iam-control-plane-api-contract.md](../docs/architecture/iam-control-plane-api-contract.md). This runbook remains the required runtime entry point for starting, verifying, backing up, restoring, stopping, and resetting the Phase 6 MVP.

## Expected Outputs

`verify.sh` should show:

- the Docker `unittest` security and contract tests pass;
- the Docker Keycloak smoke check returns JSON with `status: "ok"`;
- the smoke check proves a real Keycloak access token can authorize `access-check-demo-service`;
- the smoke check creates or reuses a member account whose lifecycle, subject link, account type, and service-role assignment are stored in Keycloak;
- the smoke check proves an invalid bearer value returns `KO`.

## Human E2E Testing

Use [Human E2E Test Process](./human-e2e-test-process.md) when a tester needs a
manual pass with real Keycloak login/logout, member self-consultation, protected
demo service access, admin member management, super-admin-only operations, audit
consultation, and evidence capture.

The current MVP runtime still has no Admin Console UI. Human e2e testing
therefore uses Keycloak browser authentication plus IAM Control Plane API calls
as the temporary operator workflow, while `access-check-demo-service` remains the
real protected-service access check. Admin activation requests Keycloak
step-up/OTP and records the observed `iam-privileged` ACR without storing OTP
seed values. The helper
`access-control/scripts/human-e2e-login.py` performs the browser Authorization
Code + PKCE login and local callback capture needed to obtain short-lived bearer
tokens for the manual API calls.

Run the Docker-backed interactive script with:

```bash
bash access-control/scripts/run-human-e2e.sh
```

For a non-interactive pass that still writes script evidence:

```bash
bash access-control/scripts/run-human-e2e.sh --yes
```

The script writes a Docker wrapper log to
`access-control/evidence/human-e2e-docker-<timestamp>/docker-run.log`. The
Docker test container writes its own readable log and JSON summary under
`access-control/evidence/human-e2e-script-<timestamp>/`.

To verify the optional SMTP-backed onboarding action-email path, run:

```bash
bash access-control/scripts/run-onboarding-email-e2e.sh
```

This starts the Docker Mailpit SMTP catcher, runs the IAM API with
`KEYCLOAK_ONBOARDING_ACTION_EMAILS=true`, configures the local Keycloak realm
SMTP settings for Mailpit, creates a fresh invited member through the IAM API,
captures the Keycloak action email, completes the required first-login actions,
and activates the account through `POST /iam/onboarding/activate`. Mailpit is
available on `http://127.0.0.1:8025` during the run. The wrapper log is written
to `access-control/evidence/onboarding-email-e2e-docker-<timestamp>/`, and the
script evidence remains under
`access-control/evidence/human-e2e-script-<timestamp>/`.

## Evidence

Collect local runtime evidence with:

```bash
bash access-control/scripts/collect-evidence.sh
```

Evidence is written to `access-control/evidence/<timestamp>/` and is ignored by Git. The evidence includes Docker Compose service status, the Docker test summary, and the Docker Keycloak smoke result.

## Backup and Restore

The local MVP stores durable runtime state in two Docker volumes:

- `access-control-mvp_access-control-runtime` for local IAM runtime files, including audit JSONL;
- `access-control-mvp_keycloak-data` for the local Keycloak data directory.

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
- The Docker MVP validates OIDC access tokens through Keycloak introspection rather than local JWT signature validation. Local JWT validation, JWKS caching, algorithm allowlisting, and signing-key rotation behavior are not runtime paths in this slice.
- The Keycloak bootstrap configures OTP step-up for the MVP privileged onboarding path, but production OTP reset/recovery governance, brute-force posture review, monitoring, and support procedures still require explicit operations evidence.
- Admin Console-to-IAM API calls authenticate with bearer user tokens in the runtime. `X-Actor-Account-Id` is ignored unless `IAM_ALLOW_DEV_ACTOR_HEADER=true` is set explicitly for focused local tests.
- Onboarding activation now uses bearer-derived identity evidence and rejects request-body attempts to provide `subject`, `emailVerified`, `acr`, or other authorization-significant fields.
- Invited Keycloak users created by the IAM API receive first-login required actions: `VERIFY_EMAIL` and `UPDATE_PASSWORD` for members, plus `CONFIGURE_TOTP` for `admin` and `super-admin` accounts. The local runtime prepares those actions but does not send Keycloak action emails unless `KEYCLOAK_ONBOARDING_ACTION_EMAILS=true` and realm SMTP is configured.
- Indeterminate Keycloak state read failures are fail-closed and create local audit events with `operation=iam.request.indeterminate` or `authorization.check.indeterminate`.
- The runtime does not include the Admin Console UI yet.
- Direct Keycloak drift detection is represented by invariant checks in this runtime, including rejection of direct protected-service role mappings on users. Member service-role assignments are stored in IAM Control Plane-managed attributes. Full migration reporting, reconciliation workflow, and production direct-admin governance remain outside this slice.
- Subject-link drift detection for direct `iam.linked_subject` edits is proposed but not implemented. The proposed direction is an EDRLab-controlled append-only subject-link ledger outside Keycloak; until accepted and tested, `SEC-DRIFT-004` remains open.
- The smoke-test user, realm, clients, redirect URI, and secrets are local runtime fixtures only.
- High availability, multi-replica Keycloak operation, advanced audit search/export, and real business protected-service integration remain outside the accepted MVP scope unless explicitly added.

## References

- [MVP Scope - Access-Control Production MVP](../docs/evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](../docs/architecture/iam-control-plane-api-contract.md)
- [Authorization Check Behavior](../docs/architecture/authorization-check-behavior.md)
- [Audit Storage Architecture](../docs/architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../docs/architecture/keycloak-iam-schema-policy.md)
- [MVP Security Test Plan](../docs/evaluation/security-test-plan.md)
