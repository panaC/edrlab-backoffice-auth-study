# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-06-29

### Added

- Added Docker-volume backup and restore scripts for the Phase 6 `access-control/` MVP runtime, including checksum verification, a restore confirmation gate, and generated-backup ignore rules.
- Added `docs/architecture/keycloak-iam-onboarding.md` as the dedicated Keycloak/IAM onboarding architecture note.

### Changed

- Promoted `docs/architecture/iam-control-plane-api-contract.md` as the current IAM route, payload, schema, error, and authorization contract for the Phase 6 runtime.
- Removed the separate runtime-tree API reference location so runtime documentation stays in the runbook and API contract tracking stays under `docs/architecture/`.
- Split the demo protected service runtime code into its own `access_check_demo_service` source package under `access-control/src/`.
- Made `docs/evaluation/mvp-scope.md` the Phase 6 MVP source of truth, superseding ADR 0005 for current MVP authority and replacing the old IAM API contract as the required runtime API source.
- Added a production readiness tracker to `docs/evaluation/mvp-scope.md` for non-security MVP gaps, required evidence, next actions, and deferral risks.
- Converted `docs/evaluation/security-test-plan.md` into a Phase 6 security evidence tracker with `Implemented`, `Partial`, `Open`, and `Deferred` status values for every test row.
- Cleaned architecture documents so `authorization/check`, audit storage, and Keycloak schema pages describe architecture behavior and policy while concrete runtime commands remain in `access-control/README.md`.
- Reduced context-heavy documentation by compressing `docs/README.md` into a short active/archive map, compacting `docs/evaluation/security-test-plan.md` into a tracker, and adding AGENTS context-budget rules for historical material.
- Added compact Agent Brief sections to the MVP scope and access-control runtime runbook to reduce first-read context for iterative agents.
- Added AGENTS change gates to prevent source drift while keeping trigger-based reading for feature, API, runtime, authorization, audit, and Keycloak schema changes.
- Compressed the AGENTS MVP boundary section into a short guard that delegates detailed scope authority to `docs/evaluation/mvp-scope.md`.
- Refined AGENTS source-drift rules with narrower README and documentation-policy triggers, a security evidence gate, and explicit evidence requirements for security or production-readiness claims.
- Moved older changelog entries to `CHANGELOG.archive.md` so the default changelog stays short and current.
- Documented the local MVP backup and restore procedure, generated evidence and backup locations, and remaining deployment-operation limitations in `access-control/README.md`.
- Simplified `AGENTS.md` into a concise Phase 6 MVP implementation guide and moved the longer documentation, citation, and wiki rules into `docs/agent-policy.md` for documentation-heavy tasks.
- Aligned Keycloak schema and onboarding architecture references with the current runtime names: managed `iam.*` attributes and configurable backoffice client ID defaulting to `backoffice`.
- Made Keycloak bootstrap explicitly set and verify disabled unmanaged User Profile attributes, with tests covering the schema policy guard.
- Tightened OIDC service-token validation for `authorization/check` to require issuer, audience, expiry, subject, and expected service client, with a matching Keycloak audience mapper for the Docker runtime.
- Aligned member service-role removal with the IAM API contract so inactive roles can be removed from members and repeated removal stays idempotent.
- Tightened onboarding repeat activation idempotence so only already-active accounts with the same immutable subject return no-change success, matching `FR-043` and `FR-044`.
- Aligned the documented audit `actorType` schema with runtime events by adding `authenticated-subject` for onboarding and `iam-api` for IAM dependency-failure audit records.
- Aligned IAM API JSON body validation with the contract so non-object JSON request bodies return `422 validation_error` instead of a generic `503`.


Older entries are archived in [CHANGELOG.archive.md](./CHANGELOG.archive.md). Do not read the archive by default; use it only for historical lookup.
