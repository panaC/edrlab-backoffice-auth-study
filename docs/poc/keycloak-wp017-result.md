# Keycloak WP-017 Result - Results and Phase 5 Review Inputs

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Consolidated Evidence Matrix](#consolidated-evidence-matrix)
- [Requirement Coverage Snapshot](#requirement-coverage-snapshot)
- [Runtime Evidence and Remaining Gaps](#runtime-evidence-and-remaining-gaps)
- [Residual Risks for Review](#residual-risks-for-review)
- [Phase 5 Review Questions](#phase-5-review-questions)
- [Decision Options](#decision-options)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-017` consolidates the Keycloak IAM plus EDRLab IAM Control Plane API validation results from `WP-010` through `WP-016` into Phase 5 review inputs. Phase 5 is the project step for reviewing PoC evidence and deciding whether to adopt, adjust, or return to earlier study phases; it is not automatic production MVP approval ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

This result now includes references to the executed PoC runtime bundle and the dedicated `WP-013` Docker runtime. It still does not create production code, production dependencies, database schema, CI, deployment files, or production operations policy ([AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Result

The active direction is coherent enough for Phase 5 review, but it is not ready for production adoption. The current validation has selected and tested:

- a Keycloak mapping for account type, lifecycle, subject link, service-access roles, protected-service checks, and audit identifiers ([Keycloak WP-010 result](./keycloak-wp010-result.md));
- an EDRLab IAM Control Plane API path for controlled business administration before Keycloak mutation ([Keycloak WP-011 result](./keycloak-wp011-result.md));
- a lifecycle and onboarding contract using Keycloak-backed state plus EDRLab business decisions ([Keycloak WP-012 result](./keycloak-wp012-result.md));
- ACR/LoA step-up as the first privileged-authentication evidence path, with a dedicated Docker runtime proving the PoC path for admin and super-admin onboarding ([Keycloak WP-013 result](./keycloak-wp013-result.md));
- an IAM Control Plane API `GET /me/services` listing and `authorization/check` protected-service contract for the first validation slice ([Keycloak WP-014 result](./keycloak-wp014-result.md));
- direct Keycloak Admin Console edits classified as setup, inspection, explicit drift tests, or rejected business-administration bypasses ([Keycloak WP-015 result](./keycloak-wp015-result.md));
- Keycloak events as supplemental provider evidence plus local EDRLab audit/reconciliation responsibility for business decisions, denials, audit reads/exports, drift, and rationale ([Keycloak WP-016 result](./keycloak-wp016-result.md)).

Overall status: Phase 4 now has runtime evidence for `WP-011` through `WP-016` and a dedicated passing runtime for `WP-013`. ADR 0003 accepts OTP MFA for privileged authentication in the current direction, so Phase 5 should treat production audit storage, direct-admin controls, protected-service availability, service-to-service authentication, operations, and OTP operational safeguards as the remaining production inputs, not solved implementation details ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)).

## Consolidated Evidence Matrix

| Work package | Current status | Review value | Blocking gap |
| --- | --- | --- | --- |
| `WP-010` IAM mapping | Review, documentation-first complete. | Gives a concrete Keycloak representation to test for account type, lifecycle, subject link, service roles, and audit identifiers. | Runtime must prove the mapping can be read, mutated, and validated through Keycloak Admin REST without hidden shortcuts ([Keycloak WP-010 result](./keycloak-wp010-result.md)). |
| `WP-011` admin anti-bypass path | PoC runtime pass. | Defines and tests the EDRLab IAM Control Plane API as the controlled server-side business path before Keycloak mutation. | Production still needs service authentication, operation authorization, and durable audit. |
| `WP-012` lifecycle and onboarding | PoC runtime pass. | Tests safe activation, unsafe activation denial, lifecycle state, and subject-link behavior. | Production still needs transactional persistence, uniqueness constraints, and admin review workflows. |
| `WP-013` privileged evidence | PoC runtime pass. | Selects and tests ACR/LoA step-up as the first privileged-authentication evidence path. | ADR 0003 accepts OTP MFA for the current direction; WebAuthn/passkeys remain future hardening (`FR-034`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| `WP-014` service authorization | PoC runtime pass. | Defines and tests effective-service listing, protected-service `authorization/check`, and fail-closed behavior. | Production still needs service-to-control-plane authentication, latency, timeout, retry, and availability review ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| `WP-015` drift and shortcuts | PoC runtime pass. | Tests direct-admin drift detection and shortcut rejection against current Keycloak state. | Production still needs direct-admin role boundaries, reconciliation, alerting, and break-glass governance. |
| `WP-016` audit and operations | PoC runtime pass with production gaps. | Produces local audit samples and Keycloak event correlation while keeping local EDRLab audit as the business authority. | Production still needs append-only storage, tamper resistance, retention, export controls, and operational procedures ([OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)). |

## Requirement Coverage Snapshot

| Requirement area | Documentation-first coverage | Missing proof |
| --- | --- | --- |
| Fixed account types and no escalation | `WP-010`, `WP-011`, and `WP-015` define fixed account-type roles, mutation rejection, and direct-admin drift handling (`FR-001`, `FR-026`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Runtime invariant checks and denied mutation evidence. |
| Lifecycle and access stop | `WP-012` and `WP-014` define lifecycle state, active-only access, and next-check denial after disablement, archival, role removal, or role disablement (`FR-011` through `FR-016`). | Runtime lifecycle transitions, current-state reads, and stale-access denial evidence. |
| Controlled administration | `WP-011` defines the IAM Control Plane API as the server-side business administration path and rejects direct business edits in Keycloak (`FR-024`, `FR-033`, `FR-038`). | Runtime endpoint calls, actor-scope denials, service-account scope evidence, and direct-admin bypass tests. |
| Protected-service authorization | `WP-014` chooses the IAM Control Plane API `authorization/check` contract; OWASP requires server-side authorization and safe handling of failed checks ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#verify-that-authorization-checks-are-performed-in-the-right-location)). | Runtime service integration, timeout/retry behavior, no-positive-cache behavior, and fail-closed evidence. |
| Audit and audit consultation | `WP-016` defines local EDRLab audit as the business audit authority and Keycloak events as supplemental evidence (`FR-027`, `FR-028`, `FR-035`). | Runtime audit samples, read/export audit records, append-only/tamper-resistance review, and retention decision. |
| Privileged authentication | `WP-013` selects and validates ACR/LoA step-up as the first validation path for privileged account activation, and ADR 0003 accepts OTP MFA for the current direction (`FR-034`, `FR-043`, `FR-044`; [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). | Production OTP enrollment, reset, recovery, rate limiting, monitoring, and audit safeguards. |
| Onboarding and subject link | `WP-012` defines safe automatic activation, unsafe denial cases, and immutable subject link handling (`FR-039` through `FR-044`). | Runtime safe/unsafe onboarding evidence and subject-link drift checks. |

## Runtime Evidence and Remaining Gaps

The PoC-only runtime bundle for `WP-011` through `WP-016` was executed and recorded in the [Keycloak WP-011 through WP-016 runtime result](./keycloak-wp011-016-runtime-result.md). The final bundle result was `pass_with_blocked_privileged_evidence`: `WP-011`, `WP-012`, `WP-014`, `WP-015`, and `WP-016` passed at PoC level, while `WP-013` still needed a dedicated step-up run.

The dedicated `WP-013` Docker runtime was then executed and recorded in the [Keycloak WP-013 result](./keycloak-wp013-result.md#runtime-execution). It passed at PoC level for normal-login denial, privileged admin and super-admin step-up allows, and mismatched-subject denial.

Remaining production gaps:

- production IAM Control Plane API implementation and operation-level authorization;
- service-to-control-plane authentication, latency, retries, timeout behavior, and fail-closed availability policy;
- production audit storage, retention, tamper resistance, export controls, and privacy review;
- direct Keycloak admin role boundaries, drift reconciliation, alerting, and break-glass governance;
- production OTP policy for privileged users: enrollment, reset, recovery, rate limiting, monitoring, and audit safeguards;
- backup/restore, upgrades, monitoring, secrets, event retention, first-super-admin bootstrap, and recovery procedures.

## Residual Risks for Review

| Risk | Why it matters | Review handling |
| --- | --- | --- |
| Runtime evidence is PoC-only. | The executed scripts use fixtures and throwaway Keycloak configuration, not production service code or durable storage. | Use the evidence for Phase 5 review only; do not infer Phase 6 approval. |
| Privileged activation evidence uses OTP in the PoC. | ADR 0003 accepts OTP MFA, but OTP is not phishing-resistant and depends on enrollment, reset, recovery, and rate-limit controls. | Carry OTP operational safeguards into Phase 5 and keep WebAuthn/passkeys as future hardening ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)). |
| IAM Control Plane API on the protected-service path. | Availability, latency, timeout, retry, and fail-closed behavior affect every protected service using `authorization/check`. | Measure and decide acceptable behavior before production design. |
| Direct Keycloak admin access. | Privileged operators can bypass business workflows or affect evidence if not constrained and monitored. | Define direct-admin roles, break-glass rules, drift reconciliation, and audit controls. |
| Local audit/reconciliation storage. | EDRLab business audit cannot be replaced by Keycloak provider events alone. | Decide storage topology, retention, append-only guarantees, tamper resistance, and privacy review. |
| Keycloak operations. | Self-hosted IAM needs backup/restore, upgrades, monitoring, secrets, event retention, and incident handling. | Treat as a material Phase 5 operations topic; Keycloak import/export docs distinguish backup-suitable CLI export from Admin Console partial export ([Keycloak import/export](https://www.keycloak.org/server/importExport)). |
| Production shortcuts after PoC. | Frontend checks, raw claims, cached positive decisions, or direct Admin Console edits could reintroduce bypass. | Preserve `WP-015` shortcut rejection as a review gate and future test requirement. |

## Phase 5 Review Questions

| Question | Evidence to review | Decision pressure |
| --- | --- | --- |
| Is the selected Keycloak mapping acceptable if the runtime bundle passes? | `WP-010` mapping plus runtime Admin REST read/write evidence. | If not, return to `WP-010` before runtime expansion. |
| Is the IAM Control Plane API the accepted business administration boundary? | `WP-011`, `WP-015`, local audit records, and direct-admin drift results. | If yes, business admins should remain in EDRLab Admin Console, not Keycloak Admin Console. |
| Is `authorization/check` acceptable as the first protected-service contract? | `WP-014` runtime evidence for allow/deny/fail-closed behavior. | If not, evaluate Keycloak Authorization Services, introspection, constrained claims, or a reviewed hybrid before Phase 6. |
| What privileged-authentication level is required for production? | `WP-013` ACR/LoA runtime evidence, ADR 0003, and `FR-034`. | OTP MFA is accepted for the current direction; review the required operational safeguards. |
| What is the production audit storage and retention model? | `WP-016` audit matrix, local audit samples, Keycloak event evidence, and `FR-035`. | Decide physical storage topology and retention/privacy constraints. |
| Who may use direct Keycloak administration? | `WP-015` drift evidence and `WP-016` admin-surface review. | Decide technical operator scope, break-glass process, reconciliation, and alerting. |
| What self-hosted Keycloak operations must be validated before adoption? | `WP-016` operations table and backup/restore/event evidence. | Decide which operations are adoption blockers and which are Phase 6 hardening work. |
| What is the minimum acceptance gate for Phase 6 production MVP? | Runtime evidence matrix, blockers, residual risks, and team ownership. | Phase 6 requires explicit user movement and must not be inferred from PoC completion ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)). |

## Decision Options

| Option | Meaning | Consequence |
| --- | --- | --- |
| Enter Phase 5 review. | Review the documentation and runtime PoC evidence now, with production gaps explicitly carried into the decision. | Best next governance step if the team wants to decide whether to adopt, adjust, or reject the Keycloak IAM direction. |
| Continue Phase 4 targeted runtime validation. | Add one or two more PoC-only scripts for high-risk production gaps such as service-to-control-plane availability or OTP recovery/reset handling. | Produces stronger evidence before Phase 5, but delays the adoption/adjust/reject decision. |
| Revise mapping or authorization contract before runtime. | Reopen `WP-010` or `WP-014` if the team dislikes the current mapping, audit split, or `authorization/check` path. | Avoids implementing a runtime slice for a contract the reviewers already reject. |

## Decision Impact

`WP-017` now consolidates both documentation and runtime PoC evidence for the Keycloak IAM plus EDRLab IAM Control Plane API direction. The strongest next governance action is a Phase 5 review with the remaining production gaps made explicit, especially OTP operational safeguards, production audit storage, direct-admin governance, protected-service availability, and operations.

No production adoption, production database topology, production API shape, production Keycloak operations model, or Phase 6 MVP implementation is approved by this result.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak WP-012 Result - Account Lifecycle and Onboarding](./keycloak-wp012-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](./keycloak-wp013-result.md)
- [Keycloak WP-014 Result - Service Access Authorization](./keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](./keycloak-wp015-result.md)
- [Keycloak WP-016 Result - Audit and Operations Review](./keycloak-wp016-result.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Keycloak IAM Control Plane API Scope](../architecture/keycloak-iam-bff-scope.md)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
