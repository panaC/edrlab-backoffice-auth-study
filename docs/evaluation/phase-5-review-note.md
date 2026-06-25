# Phase 5 Review Note - Keycloak IAM Control Plane API

Status: Review
Phase: Phase 5 - Review and Decision
Scope: Evaluation
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Review Position](#review-position)
- [What the PoC Validates](#what-the-poc-validates)
- [Production Risks Remaining](#production-risks-remaining)
- [Decisions To Take](#decisions-to-take)
- [Minimum Conditions To Authorize an MVP](#minimum-conditions-to-authorize-an-mvp)
- [Decision Matrix](#decision-matrix)
- [References](#references)

## Purpose

This note summarizes the Phase 5 review position for the active Keycloak IAM plus EDRLab IAM Control Plane API direction. Phase 5 is the review step where the project decides whether to adopt the validated direction, adjust it, or return to earlier study phases; it is not automatic production MVP approval ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The active direction is the one accepted in ADR 0002: Keycloak may hold IAM state, while the EDRLab Admin Console and IAM Control Plane API mediate business administration, protected-service authorization, and audit-relevant behavior so that raw IAM-console edits, token claims, browser checks, or protected-service shortcuts do not bypass `FR-038` ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Review Position

The PoC is strong enough to support a Phase 5 decision to continue with the Keycloak IAM plus EDRLab IAM Control Plane API direction for a constrained MVP design. It is not strong enough, by itself, to authorize production implementation or deployment. The executed Docker evidence remains PoC-only, and the production risks below must either be resolved or explicitly accepted with owners before Phase 6 starts ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md), [Keycloak WP-011 through WP-016 runtime result](../poc/keycloak-wp011-016-runtime-result.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

Review recommendation:

| Review outcome | Position | Reason |
| --- | --- | --- |
| Adopt direction for MVP design | Yes, conditionally. | The PoC validates the core control-plane shape, lifecycle checks, privileged step-up evidence, protected-service authorization contract, drift handling, and audit boundary at PoC level ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md#result)). |
| Authorize Phase 6 MVP implementation | Not yet. | The project still needs explicit MVP scope, production operations, audit storage, direct-admin governance, protected-service availability behavior, service-to-control-plane authentication, and OTP operational safeguards ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md#runtime-evidence-and-remaining-gaps)). |
| Return to Phase 3 solution choice | No, unless reviewers reject Keycloak operations or the IAM Control Plane API boundary. | No PoC result currently invalidates the selected direction; the remaining items are production-readiness and governance gaps rather than proof that the direction cannot satisfy the requirements. |

## What the PoC Validates

| Area | Validated by PoC | Phase 5 interpretation |
| --- | --- | --- |
| IAM mapping | `WP-010` selected a concrete Keycloak representation for account type, lifecycle, authenticated-subject link, service-access roles, protected-service authorization input, and audit identifiers ([Keycloak WP-010 result](../poc/keycloak-wp010-result.md)). | The mapping is concrete enough for MVP design, but production must review managed attributes, role boundaries, and invariant checks. |
| Controlled administration path | `WP-011` and the runtime bundle validated a server-side IAM Control Plane API path that evaluates business rules before Keycloak mutation, including denial of unsafe account-type mutation ([Keycloak WP-011 result](../poc/keycloak-wp011-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#decision-matrix)). | Business administration should go through the EDRLab Admin Console and IAM Control Plane API, not direct Keycloak Admin Console edits. |
| Lifecycle and onboarding | `WP-012` and the runtime bundle validated safe onboarding activation, unsafe unverified onboarding denial, subject-link handling, and lifecycle-based denial behavior ([Keycloak WP-012 result](../poc/keycloak-wp012-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#decision-matrix)). | The onboarding contract is viable at PoC level for `FR-043` and `FR-044`, pending production persistence and uniqueness controls. |
| Privileged authentication | `WP-013` validated Keycloak ACR/LoA step-up with OTP, including denial without privileged `acr`, allow for admin and super-admin with privileged `acr`, subject-mismatch denial, and ID-token claim validation ([Keycloak WP-013 result](../poc/keycloak-wp013-result.md#runtime-execution)). | OTP MFA is accepted for the current privileged-authentication direction by ADR 0003; WebAuthn/passkeys remain future hardening, not a current blocker ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| Protected-service authorization | `WP-014` and the runtime bundle validated `GET /me/services`, `authorization/check`, allow for active authorized member, deny for disabled member, and fail-closed denial on drift ([Keycloak WP-014 result](../poc/keycloak-wp014-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#decision-matrix)). | The `authorization/check` contract is acceptable for first MVP design if service authentication, timeout, retry, cache, and availability behavior are explicitly decided. |
| Direct-admin drift handling | `WP-015` and the runtime bundle validated that direct Keycloak Admin REST changes can be detected as drift and denied by the control-plane authorization path ([Keycloak WP-015 result](../poc/keycloak-wp015-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#decision-matrix)). | Direct Keycloak administration must be treated as technical operation or break-glass, not routine business administration. |
| Audit boundary | `WP-016` and the runtime bundle validated local EDRLab audit-shaped records plus supplemental Keycloak admin-event correlation ([Keycloak WP-016 result](../poc/keycloak-wp016-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#evidence-map)). | Keycloak events are useful supporting evidence, but the project still needs local durable append-only business audit for `FR-027`, `FR-028`, and `FR-035` ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Docker reproducibility | The runtime PoC was executed with Docker Compose Keycloak and PoC-only scripts, with evidence recorded for `WP-011` through `WP-016` and the dedicated `WP-013` step-up run ([runtime result](../poc/keycloak-wp011-016-runtime-result.md#execution), [WP-013 runtime](../poc/keycloak-wp013-result.md#runtime-execution)). | The evidence is reviewable and reproducible at PoC level, but it is not production code, production deployment, or production operations proof. |

## Production Risks Remaining

| Risk | Why it remains production-relevant | Required Phase 5 handling |
| --- | --- | --- |
| IAM Control Plane API is still a fixture. | The PoC validates behavior, not production service code, service authentication, authorization middleware, persistence, concurrency, or API hardening ([runtime result](../poc/keycloak-wp011-016-runtime-result.md#residual-risks)). | Decide the production API boundary, endpoint set, operation-level authorization, service credentials, error model, and audit behavior before Phase 6. |
| Protected services depend on a live authorization decision path. | `FR-020` and `FR-021` require server-side authorization and safe denial when the result cannot be determined; the runtime does not prove production latency, timeout, retry, or availability behavior ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Set a service-to-control-plane authentication model, timeout policy, retry policy, cache policy, and accepted access-stop delay. |
| Audit storage is not production-ready. | The runtime emits JSON audit evidence, but `FR-035` requires append-only audit records retained indefinitely under the initial policy ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#residual-risks)). | Choose durable audit storage, append-only controls, correlation IDs, retention policy, read/export authorization, privacy review, and backup behavior. |
| Direct Keycloak admin access can bypass business workflows. | Keycloak is an administrative product; direct realm administration must not become a shortcut around the IAM Control Plane API under `FR-038` ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). | Define direct-admin roles, break-glass process, reconciliation, alerting, drift quarantine, and review cadence. |
| OTP is accepted but operationally sensitive. | ADR 0003 accepts OTP MFA, while noting that OTP is not phishing-resistant and still needs enrollment, reset, recovery, rate limiting, monitoring, and audit safeguards ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)). | Approve OTP enrollment, reset, recovery, administrative intervention, and monitoring rules before privileged production onboarding. |
| Keycloak self-hosting needs operations proof. | The PoC does not prove production backup/restore, upgrades, event retention, secrets, monitoring, incident response, or recovery procedures; Keycloak distinguishes backup-suitable CLI export from partial Admin Console export ([Keycloak import/export](https://www.keycloak.org/server/importExport), [Keycloak WP-017 result](../poc/keycloak-wp017-result.md#residual-risks-for-review)). | Assign Keycloak operational ownership and define backup, restore-test, upgrade, monitoring, secrets, event-retention, and rollback requirements. |
| User-profile and IAM-state policy are PoC-level. | The runtime had to configure Keycloak user-profile unmanaged attributes for PoC IAM attributes, and production should review explicit managed attributes and permissions ([runtime result](../poc/keycloak-wp011-016-runtime-result.md#surprises), [Keycloak user profile](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)). | Decide the production Keycloak schema policy for IAM attributes, validation, visibility, edit permissions, and migration behavior. |
| First-super-admin and recovery flows are not validated. | `WP-013` validates invited privileged-account activation, not first-super-admin bootstrap, account recovery, or emergency access ([Keycloak WP-013 result](../poc/keycloak-wp013-result.md#residual-risks)). | Define bootstrap and break-glass ceremonies, including audit, approval, expiry, and recovery evidence. |

## Decisions To Take

| Decision | Recommended Phase 5 outcome | Why it is needed |
| --- | --- | --- |
| Adopt, adjust, or reject the active direction. | Adopt for constrained MVP design, with explicit production gates. | The PoC validates the core behavior, and no current evidence forces a return to Phase 3 ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md#decision-options)). |
| Define the MVP boundary. | Include only the minimum account lifecycle, admin operations, service-role assignment, service listing, protected-service authorization check, audit, and privileged onboarding flows needed for the first internal backoffice use. | `FR-030` requires complexity to remain understandable and justified at the expected internal scale ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Confirm `authorization/check` as the protected-service contract. | Accept for MVP if service authentication, timeout, retry, cache, and fail-closed rules are decided. | The PoC validates the contract shape, but not production availability or latency behavior ([Keycloak WP-014 result](../poc/keycloak-wp014-result.md), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| Confirm OTP safeguards for privileged accounts. | Accept OTP MFA with mandatory operational safeguards. | ADR 0003 accepts OTP, but production still needs enrollment, reset, recovery, monitoring, rate limiting, and audit controls ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| Choose durable audit storage. | Decide before Phase 6 starts. | Local audit is required for business decisions and audit reads/exports; JSON evidence is not a production audit store (`FR-027`, `FR-028`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Define direct Keycloak administration governance. | Restrict to technical operations and break-glass, with drift detection and reconciliation. | The PoC treats direct business edits as drift, and ADR 0002 rejects direct Keycloak Admin Console as the business Access Control Manager ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Keycloak WP-015 result](../poc/keycloak-wp015-result.md)). |
| Assign Keycloak operations ownership. | Decide owner, runbooks, backup/restore tests, monitoring, event retention, upgrade path, and incident process. | Self-hosting is part of the chosen direction and remains a material operations risk under `FR-030` ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-017 result](../poc/keycloak-wp017-result.md#residual-risks-for-review)). |
| Decide whether another Phase 4 runtime is needed. | Optional, targeted only. | If reviewers are uncomfortable with protected-service availability or OTP reset/recovery, run one more PoC-only validation before MVP authorization; otherwise carry them as MVP design gates. |

## Minimum Conditions To Authorize an MVP

The project should authorize a production MVP only if all conditions below are met. If one condition is missing, Phase 5 can still authorize more design or targeted PoC work, but not Phase 6 production MVP implementation.

| Gate | Minimum condition | Evidence expected before authorization |
| --- | --- | --- |
| Explicit movement to Phase 6 | The user or project owner explicitly approves starting Phase 6 MVP implementation. | A decision record or project note that says Phase 6 is authorized, because governance says Phase 6 must not start implicitly ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)). |
| MVP scope | The first MVP scope is bounded to named account operations, lifecycle transitions, service-role operations, protected services, audit views/exports, and onboarding flows. | A short MVP scope note linked to `FR-*` requirements and excluding non-MVP work. |
| Control-plane API contract | The IAM Control Plane API endpoint set, actor model, service authentication, operation authorization, error model, idempotency expectations, and audit behavior are accepted. | API contract or implementation plan showing server-side checks for `FR-020`, `FR-021`, `FR-033`, and `FR-038` ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Protected-service access stop | The project accepts an access-stop delay and defines timeout, retry, cache, and fail-closed behavior for `authorization/check`. | Design decision and tests planned for disablement, archival, role removal, role disablement, drift, outage, and stale-cache cases (`FR-016`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Audit storage | The project chooses durable append-only audit storage, retention policy, correlation IDs, audit read/export authorization, and backup behavior. | Audit design covering `FR-027`, `FR-028`, and `FR-035`, plus evidence that Keycloak events are supplemental rather than the only business audit source. |
| Privileged authentication | OTP step-up is configured for admin and super-admin onboarding, ACR/LoA validation is required by the IAM Control Plane API, and OTP enrollment/reset/recovery is audited. | Production design and test plan derived from `WP-013` and ADR 0003 ([Keycloak WP-013 result](../poc/keycloak-wp013-result.md), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| Direct-admin governance | Keycloak direct administration is limited to technical operation and break-glass, with drift reconciliation and alerting. | Role matrix, break-glass procedure, reconciliation job or review process, and audit requirements linked to `WP-015`. |
| Keycloak operations | Backup/restore, upgrade, monitoring, secrets, event retention, incident response, and rollback responsibilities are assigned. | Operational runbook and ownership model; at least one backup/restore validation should be planned before production data is trusted. |
| IAM-state schema policy | Production Keycloak attributes, roles, and client-role mappings are schema-controlled and reviewed. | Managed attribute or equivalent policy decision, migration plan, and permission model based on the PoC user-profile finding. |
| Security regression tests | The MVP test plan covers no frontend-only authorization, no raw token claim authorization, issuer/audience/token validation, subject-link immutability, fail-closed denials, drift denial, and audit creation. | Test plan linked to `WP-011` through `WP-016`, `FR-038`, and OWASP authorization guidance ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |

## Decision Matrix

| Decision path | Accept when | Result |
| --- | --- | --- |
| Adopt for MVP design | Reviewers accept the PoC evidence and agree to close the minimum MVP gates before Phase 6 implementation. | Recommended current path. |
| Adjust and re-review | Reviewers accept Keycloak but reject one production boundary, such as `authorization/check`, local audit storage, or direct-admin governance. | Update the relevant architecture or PoC artifact, then re-run a targeted review. |
| Continue Phase 4 validation | Reviewers need one more runtime proof for a high-risk item such as protected-service availability or OTP recovery/reset. | Add one narrow Docker-only PoC, then update this note. |
| Return to Phase 3 | Reviewers reject Keycloak self-hosting, reject the IAM Control Plane API boundary, or decide production operations are too heavy for `FR-030`. | Reopen solution choice with the current PoC evidence as negative or conditional evidence. |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak WP-010 Result - IAM Mapping Design](../poc/keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](../poc/keycloak-wp011-result.md)
- [Keycloak WP-012 Result - Account Lifecycle and Onboarding](../poc/keycloak-wp012-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](../poc/keycloak-wp013-result.md)
- [Keycloak WP-014 Result - Service Access Authorization](../poc/keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](../poc/keycloak-wp015-result.md)
- [Keycloak WP-016 Result - Audit and Operations Review](../poc/keycloak-wp016-result.md)
- [Keycloak WP-017 Result - Results and Phase 5 Review Inputs](../poc/keycloak-wp017-result.md)
- [Keycloak WP-011 Through WP-016 Runtime Result](../poc/keycloak-wp011-016-runtime-result.md)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak User Profile - Managed and Unmanaged Attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)
- [Keycloak Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
