# Access-Control MVP Runtime

Status: Draft
Phase: Phase 6 - Production MVP
Scope: Runtime
Last reviewed: 2026-06-26

## Contents

- [Purpose](#purpose)
- [What This Slice Includes](#what-this-slice-includes)
- [Prerequisites](#prerequisites)
- [Environment](#environment)
- [Run](#run)
- [Expected Outputs](#expected-outputs)
- [Evidence](#evidence)
- [Stop and Reset](#stop-and-reset)
- [Known MVP Shortcuts](#known-mvp-shortcuts)
- [References](#references)

## Purpose

This directory contains the Phase 6 executable MVP runtime for the accepted MVP scope: Keycloak, an IAM Control Plane API, an `access-check-demo-service`, append-only local audit storage, idempotent first-`super-admin` bootstrap, Linux scripts, Docker Compose runtime, and executable tests. The runtime follows the accepted MVP boundary in ADR 0005 and the accepted API, audit, authorization-check, schema, and security-test artifacts ([ADR 0005](../docs/decisions/0005-authorize-phase-6-production-mvp.md), [MVP scope](../docs/evaluation/mvp-scope.md), [IAM Control Plane API contract](../docs/architecture/iam-control-plane-api-contract.md), [Authorization Check Runtime Behavior](../docs/architecture/authorization-check-behavior.md), [Audit Storage Policy](../docs/architecture/audit-storage.md), [Keycloak IAM Schema Policy](../docs/architecture/keycloak-iam-schema-policy.md), [MVP Security Test Plan](../docs/evaluation/security-test-plan.md)).

This is production-scope code, not a Phase 4 PoC. It is still an early Phase 6 runtime: it now validates the protected-service subject-token path and service-to-service authentication through Keycloak/OIDC, but it does not yet include the Admin Console UI, full Keycloak IAM schema migration, or production operations hardening.

## What This Slice Includes

| Item | Included |
| --- | --- |
| Keycloak runtime | Local Docker Keycloak with a scripted MVP realm, backoffice OIDC client, service client, audience mapper, and smoke-test user. |
| IAM API | `GET /healthz`, `/iam/me`, account management, onboarding activation, service-role management, service-role assignment, `POST /iam/authorization/check`, super-admin audit reads, OIDC subject-token introspection, and OIDC service-token validation. |
| Demo protected service | `GET /access-check-demo`, returning JSON `OK` or `KO`, obtaining a client-credentials service token, and calling `POST /iam/authorization/check`. |
| Audit storage | Local append-only JSON Lines file with one complete event object per physical line. |
| Bootstrap | Scripted Keycloak realm/client/user bootstrap plus idempotent first-`super-admin` bootstrap outside the public API and the initial `access-check-demo:consult` role. |
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
| `KEYCLOAK_SUPER_ADMIN_USERNAME` / `KEYCLOAK_SUPER_ADMIN_PASSWORD` | Local non-production super-admin user used by Docker smoke verification of admin API calls. |
| `KEYCLOAK_SMOKE_USERNAME` / `KEYCLOAK_SMOKE_EMAIL` / `KEYCLOAK_SMOKE_PASSWORD` | Local non-production user used by the Docker smoke verification. |
| `BOOTSTRAP_SUPER_ADMIN_EMAIL` | First `super-admin` email used by the bootstrap process. |
| `BOOTSTRAP_SUPER_ADMIN_NAME` | First `super-admin` display name. |
| `BOOTSTRAP_SUPER_ADMIN_ORGANIZATION` | First `super-admin` organization. |
| `BOOTSTRAP_SUPER_ADMIN_SUBJECT` | Local development subject linked to the bootstrapped `super-admin`. |

## Run

From the repository root:

```bash
bash access-control/scripts/start.sh
bash access-control/scripts/bootstrap.sh
bash access-control/scripts/verify.sh
```

The IAM API is exposed on `http://127.0.0.1:8000`. The demo protected service is exposed on `http://127.0.0.1:8001`. Keycloak is exposed on `http://127.0.0.1:8080`.

The Docker smoke verification obtains a Keycloak access token through Authorization Code + PKCE and calls the demo service with that token. It also checks that an invalid bearer value returns `KO`.

## Expected Outputs

`verify.sh` should show:

- the Docker `unittest` security and contract tests pass;
- the Docker Keycloak smoke check returns JSON with `status: "ok"`;
- the smoke check proves a real Keycloak access token can authorize `access-check-demo-service`;
- the smoke check proves an invalid bearer value returns `KO`.

## Evidence

Collect local runtime evidence with:

```bash
bash access-control/scripts/collect-evidence.sh
```

Evidence is written to `access-control/evidence/<timestamp>/` and is ignored by Git. The evidence includes Docker Compose service status, the Docker test summary, and the Docker Keycloak smoke result.

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
- Admin Console-to-IAM API calls authenticate with bearer user tokens in the runtime. `X-Actor-Account-Id` is ignored unless `IAM_ALLOW_DEV_ACTOR_HEADER=true` is set explicitly for focused local tests.
- The state backend is a local file-backed implementation of the accepted control-plane contract. It is intentionally isolated behind code boundaries so the Keycloak Admin REST adapter can replace it.
- The runtime does not include the Admin Console UI yet.
- Direct Keycloak drift detection is represented by invariant checks in this runtime. Real Keycloak schema migration, drift reconciliation, and managed-attribute enforcement still need the production Keycloak adapter and migration workflow.
- The smoke-test user, realm, clients, redirect URI, and secrets are local runtime fixtures only.
- High availability, multi-replica Keycloak operation, advanced audit search/export, and real business protected-service integration remain outside the accepted MVP scope unless explicitly added.

## References

- [ADR 0005 - Authorize Phase 6 Production MVP](../docs/decisions/0005-authorize-phase-6-production-mvp.md)
- [MVP Scope - Keycloak IAM Control Plane API](../docs/evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](../docs/architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../docs/architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../docs/architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../docs/architecture/keycloak-iam-schema-policy.md)
- [MVP Security Test Plan](../docs/evaluation/security-test-plan.md)
