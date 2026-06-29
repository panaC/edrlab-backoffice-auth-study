# AGENTS.md - MVP Agent Instructions

## Current Mission

Implement the `Phase 6 - Production MVP` for the backoffice access-control capability.

Default work should focus on the approved `access-control/` MVP runtime: code, tests, Docker runtime, bootstrap or migration scripts, operational evidence, and runtime documentation needed by the accepted MVP scope.

## Read First

Before changing the repository, read the smallest set that applies to the task:

- [docs/evaluation/mvp-scope.md](./docs/evaluation/mvp-scope.md) as the Phase 6 MVP source of truth.
- [access-control/README.md](./access-control/README.md) as the required runtime runbook for Phase 6 work.
- [README.md](./README.md) only when changing the project brief, root documentation, or checking project purpose or actor model not covered by MVP scope.
- [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md) only when changing access-control behavior or checking feature scope.
- [access-control/docs/api.md](./access-control/docs/api.md) when changing IAM HTTP routes, payloads, errors, or endpoint behavior.
- [docs/architecture/authorization-check-behavior.md](./docs/architecture/authorization-check-behavior.md) when changing `authorization/check` architecture behavior.
- [docs/architecture/audit-storage.md](./docs/architecture/audit-storage.md) when changing audit storage architecture.
- [docs/architecture/keycloak-iam-schema-policy.md](./docs/architecture/keycloak-iam-schema-policy.md) when changing managed Keycloak schema or drift policy.
- [docs/evaluation/security-test-plan.md](./docs/evaluation/security-test-plan.md) when adding or closing MVP security evidence.
- [docs/agent-policy.md](./docs/agent-policy.md) when adding or changing substantive claims, citations, wiki content, study-document placement, or long-form documentation.

## Context Budget Rules

- Do not read `docs/poc/`, superseded ADRs, superseded architecture notes, historical requirements reviews, or `docs/wiki/` by default.
- Use [docs/README.md](./docs/README.md) only as a navigation map, not as a required project briefing.
- When updating [CHANGELOG.md](./CHANGELOG.md), inspect only the current top date section unless historical provenance is explicitly needed; do not read `CHANGELOG.archive.md` by default.
- Prefer targeted search with `rg` before opening large historical documents.
- Read historical documents only for provenance, audits of earlier decisions, or when a current source explicitly points to them.
- For security-test work, start with the tracker table in [docs/evaluation/security-test-plan.md](./docs/evaluation/security-test-plan.md), then inspect the test code or architecture docs only for the specific open row.

## Change Gates

Use these gates before editing behavior, code, tests, runtime docs, or architecture docs:

| Change type | Must read before edit | Must update or check |
| --- | --- | --- |
| Feature behavior, actor permissions, lifecycle, onboarding, or service-access rules | [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md) | Name the relevant `FR-*` in the summary or tests. |
| MVP boundary, exclusions, readiness, or residual risk | [docs/evaluation/mvp-scope.md](./docs/evaluation/mvp-scope.md) | Update scope, gaps, or source map if the boundary changes. |
| IAM HTTP routes, payloads, errors, auth rules, or endpoint behavior | [access-control/docs/api.md](./access-control/docs/api.md) | Keep code, tests, and API reference in the same change. |
| Runtime commands, environment variables, evidence, backup, restore, stop, or reset | [access-control/README.md](./access-control/README.md) | Keep the runbook executable from a clean Linux checkout. |
| `authorization/check` timeout, retry, cache, fail-closed, audit, or metrics semantics | [docs/architecture/authorization-check-behavior.md](./docs/architecture/authorization-check-behavior.md) | Update security tests or the security tracker when evidence changes. |
| Audit event shape, storage, retention, confidentiality, or read behavior | [docs/architecture/audit-storage.md](./docs/architecture/audit-storage.md) | Update audit tests or tracker rows when behavior changes. |
| Keycloak managed attributes, roles, migration, service-account grants, or drift policy | [docs/architecture/keycloak-iam-schema-policy.md](./docs/architecture/keycloak-iam-schema-policy.md) | Update bootstrap, migration, drift tests, or runtime docs as applicable. |
| Security tests, evidence, or tracker status | [docs/evaluation/security-test-plan.md](./docs/evaluation/security-test-plan.md) | Update tracker status/evidence and run or record relevant tests. |

Behavior changes must name their source document. API drift is not allowed: any route, payload, error code, or authorization rule change must update implementation, tests, and [access-control/docs/api.md](./access-control/docs/api.md) together.

## Operating Rules

- Follow the user's explicit request first, then this file, then the linked source documents, then existing repository conventions. A user request may change scope, but security and production-readiness claims still require evidence or explicit risk acceptance.
- Prefer existing `access-control/` patterns over new abstractions or new tooling.
- Keep changes inside the accepted MVP boundary unless the user explicitly expands scope.
- Use Linux and Docker-oriented commands in runtime docs and scripts.
- Check for a suitable existing file before creating a new one.
- Preserve unrelated user changes. Do not revert work you did not make.
- Record meaningful project/runtime changes in [CHANGELOG.md](./CHANGELOG.md).

## MVP Boundary Guard

- The MVP source of truth is [docs/evaluation/mvp-scope.md](./docs/evaluation/mvp-scope.md).
- Stay inside the accepted Phase 6 access-control runtime scope unless the user explicitly changes scope.
- Do not add real business protected-service integration, advanced audit export/search, mandatory WebAuthn/passkeys, high-availability Keycloak, formal direct-admin governance, public signup, or consumer identity flows.
- Do not promote PoC or historical artifacts into runtime code without review and acceptance.
- Do not claim production readiness until security evidence, audit behavior, bootstrap behavior, Keycloak schema or migration behavior, and minimum operations evidence are verified or explicitly risk-accepted.

## Security Rules

- Do not recommend or implement plain-text password storage, custom cryptography, unsigned JWTs, skipped issuer validation, skipped audience validation, frontend-only authorization, or exposed admin APIs without strong authorization.
- Protected services must authorize server-side through the accepted `authorization/check` boundary and fail closed when access cannot be safely determined.
- Direct Keycloak business mutations are not a routine administration path. Treat unmanaged business mutation as drift, denial, quarantine, or fail-closed behavior according to the accepted schema policy.
- Audit records must not store access tokens, refresh tokens, OTP values, passwords, recovery codes, client secrets, private keys, raw session identifiers, or raw subject tokens.

## Documentation Rules

- Keep root [README.md](./README.md) review-facing and edit [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md) only when the user is refining final-solution feature requirements.
- When adding or changing substantive documentation claims, citations, wiki content, study-document placement, or long-form documentation, follow [docs/agent-policy.md](./docs/agent-policy.md).
- For runtime docs under `access-control/`, include prerequisites, environment variables, exact Linux commands, expected outputs, evidence produced, stop/reset steps, known shortcuts, and MVP or production limitations when relevant.

## Completion Checks

Before finishing a change:

- confirm the work matches the latest user request and the accepted MVP boundary;
- confirm the immutable feature specification was not changed unless explicitly requested;
- run relevant tests or explain why they were not run;
- run `git diff --check` or another suitable lightweight validation after edits;
- update `CHANGELOG.md` for meaningful project/runtime changes;
- mention remaining risk, skipped tests, or operational limitations clearly.
