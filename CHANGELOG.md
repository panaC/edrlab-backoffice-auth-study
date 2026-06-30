# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-06-30

### Changed

- Hardened the Phase 6 Keycloak smoke path diagnostics: IAM API and demo
  service requests now emit structured technical JSON logs, response
  BrokenPipe/client-disconnects stay out of durable indeterminate audit events,
  `authorization/check` and demo-to-IAM calls emit timing evidence, and the demo
  service IAM call timeout can be overridden for staging smoke investigation.
- Compressed `ABSTRACT.md` into a short current-state summary for the Phase 6
  access-control MVP runtime and remaining readiness gates.
- Implemented Keycloak-side onboarding preparation for newly invited accounts:
  required first-login actions are set for members and privileged accounts, and
  optional `execute-actions-email` dispatch can be enabled for SMTP-backed
  runtimes.
- Added an automated SMTP-backed onboarding email e2e path using Docker Mailpit,
  including a `run-onboarding-email-e2e.sh` wrapper and an `E2E-012` test case
  that captures the Keycloak action email and completes member activation.
- Configured the Phase 6 `access-control/` Keycloak bootstrap with OTP
  step-up ACR/LoA evidence for privileged onboarding, mapping `iam-normal` to
  LoA 1 and `iam-privileged` to LoA 2.
- Updated the Docker human e2e runner so admin onboarding provisions a
  non-production OTP fixture credential, performs a real Keycloak OTP step-up
  login, records the observed privileged ACR without storing OTP seed values,
  and completes downstream admin/member/protected-service flows.
- Updated the human e2e service-role catalog check to disable and archive its
  run-scoped service role after proving super-admin catalog mutation, preventing
  active test roles from accumulating in the runtime catalog.
- Updated runtime, onboarding, MVP scope, and human e2e documentation to mark
  the privileged OTP activation path as verified while keeping OTP
  reset/recovery, brute-force, monitoring, and support posture as partial
  production-readiness evidence.

## 2026-06-29

### Added

- Added `access-control/human-e2e-test-process.md` with a manual human e2e
  checklist for real Keycloak authentication, login/logout handling, member
  self-service, protected demo-service access, admin member management,
  super-admin-only operations, audit consultation, and evidence capture.
- Added `access-control/scripts/human-e2e-login.py` as a local manual-test
  helper for browser Authorization Code + PKCE login and localhost callback token
  capture.
- Added a Docker-backed human e2e runner with
  `access-control/scripts/run-human-e2e.sh`, a `human-e2e` Compose tool service,
  and readable script evidence logs under `access-control/evidence/`.
- Added Docker-volume backup and restore scripts for the Phase 6 `access-control/` MVP runtime, including checksum verification, a restore confirmation gate, and generated-backup ignore rules.
- Added `docs/architecture/keycloak-iam-onboarding.md` as the dedicated Keycloak/IAM onboarding architecture note.
- Added `SEC-DRIFT-002` regression evidence for direct Keycloak lifecycle drift, including fail-closed authorization denial and `drift_detected` audit assertions.
- Added `SEC-CLAIM-001` Docker Keycloak smoke evidence that stale real-token service-role claims return confirmed `403 KO` after IAM-managed role removal.
- Added `SEC-CLAIM-003` regression evidence that an admin-looking OIDC token for a disabled account fails closed against canonical IAM lifecycle state.
- Added `SEC-FE-002` regression evidence that client-supplied hidden or admin fields cannot mutate protected account, service-role, lifecycle, or assignment state.
- Added `SEC-SUBJECT-003` regression evidence that different-subject onboarding cannot rebind an existing subject link and leaves rejected audit evidence.
- Added `SEC-FAIL-004` regression evidence for fail-closed `authorization/check` decisions on unknown service or role IDs, inactive accounts, and inactive service roles.
- Added `SEC-TOKEN-003` closure notes confirming the Phase 6 Docker MVP delegates invalid-signature and unsupported-algorithm rejection to Keycloak introspection rather than a local JWT-validation path.

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
- Made Keycloak User Profile bootstrap and schema documentation compatible with runtimes that omit the unmanaged-attribute policy field when the server default is already disabled.
- Tightened onboarding repeat activation idempotence so only already-active accounts with the same immutable subject return no-change success, matching `FR-043` and `FR-044`.
- Added SEC-SUBJECT-002 regression evidence for repeat onboarding activation idempotence and `no_change` onboarding audit events.
- Aligned the documented audit `actorType` schema with runtime events by adding `authenticated-subject` for onboarding and `iam-api` for IAM dependency-failure audit records.
- Aligned IAM API JSON body validation with the contract so non-object JSON request bodies return `422 validation_error` instead of a generic `503`.
- Documented a proposal for closing `SEC-DRIFT-004` with an EDRLab-controlled append-only subject-link ledger outside Keycloak, while keeping the tracker row open until runtime evidence exists.


Older entries are archived in [CHANGELOG.archive.md](./CHANGELOG.archive.md). Do not read the archive by default; use it only for historical lookup.
