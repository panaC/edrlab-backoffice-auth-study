# Phase 5 Review Note - Keycloak IAM Control Plane API

Status: Accepted
Phase: Phase 5 - Review and Decision
Scope: Evaluation
Last reviewed: 2026-06-26

## Contents

- [Purpose](#purpose)
- [Review Position](#review-position)
- [Review Decision](#review-decision)
- [What the PoC Validates](#what-the-poc-validates)
- [Production Risks Remaining](#production-risks-remaining)
- [Decisions To Take](#decisions-to-take)
- [Minimum Conditions To Authorize an MVP](#minimum-conditions-to-authorize-an-mvp)
- [Accepted API Contract](#accepted-api-contract)
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
| Adopt direction for MVP design | Accepted by user decision on 2026-06-26. | The PoC validates the core control-plane shape, lifecycle checks, privileged step-up evidence, protected-service authorization contract, drift handling, and audit boundary at PoC level ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md#result), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)). |
| Authorize Phase 6 MVP implementation | Accepted by ADR 0005 on 2026-06-26. | The project accepted the MVP scope, API contract, authorization-check behavior, audit storage, schema policy, security test plan, and explicit residual-risk deferrals ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Return to Phase 3 solution choice | No, unless reviewers reject Keycloak operations or the IAM Control Plane API boundary. | No PoC result currently invalidates the selected direction; the remaining items are production-readiness and governance gaps rather than proof that the direction cannot satisfy the requirements. |

## Review Decision

The Phase 5 review decision is to adopt the self-hosted Keycloak IAM plus EDRLab Admin Console and IAM Control Plane API architecture for constrained MVP design ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)).

ADR 0005 now authorizes Phase 6 production MVP implementation for the accepted MVP scope. The authorization keeps the recorded MVP constraints and accepted residual risks; it does not approve work beyond the MVP boundary ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

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
| Audit storage is now selected for MVP but not implemented. | The runtime emits JSON audit evidence, and Phase 5 accepts local file-backed append-only storage with one JSON event object per line for the MVP. `FR-035` still requires append-only audit records retained indefinitely under the initial policy ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Audit storage policy](../architecture/audit-storage.md)). | Implement exact file path, rotation, file permissions, backup/restore test, and confidentiality controls in Phase 6 before production data is trusted. |
| Direct Keycloak admin access can bypass business workflows. | Keycloak is an administrative product; direct realm administration must not become a shortcut around the IAM Control Plane API under `FR-038` ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). | Accepted MVP residual risk: detailed direct-admin governance is deferred post-MVP, while the MVP still forbids routine direct Keycloak business administration and treats unmanaged mutation as drift ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| OTP is accepted but operationally sensitive. | ADR 0003 accepts OTP MFA, while noting that OTP is not phishing-resistant and still needs safeguards. Keycloak documents OTP policies, OTP reset/reconfiguration paths, recovery codes, and brute-force detection for password, OTP, and recovery-code attempts ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [Keycloak OTP policies](https://www.keycloak.org/docs/latest/server_admin/#one-time-password-otp-policies), [Keycloak brute force attacks](https://www.keycloak.org/docs/latest/server_admin/#brute-force-attacks)). | Accepted MVP direction: use Keycloak's documented built-in OTP, recovery-code, required-action, and brute-force protection mechanisms; exact values are Phase 6 implementation details ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Keycloak self-hosting needs operations proof. | The PoC does not prove production backup/restore, upgrades, event retention, secrets, monitoring, incident response, or recovery procedures; Keycloak distinguishes backup-suitable CLI export from partial Admin Console export ([Keycloak import/export](https://www.keycloak.org/server/importExport), [Keycloak WP-017 result](../poc/keycloak-wp017-result.md#residual-risks-for-review)). | Accepted MVP owner: `super-admin` is accountable for Keycloak operations. Phase 6 must still produce concrete runbooks and minimum backup/restore evidence before production data is trusted ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| User-profile and IAM-state policy is now selected for MVP but not implemented. | The runtime had to configure Keycloak user-profile unmanaged attributes for PoC IAM attributes, and Phase 5 now accepts managed attributes with unmanaged attributes disabled for the MVP ([runtime result](../poc/keycloak-wp011-016-runtime-result.md#surprises), [Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md)). | Implement exact User Profile JSON, service-account grants, role metadata serialization, migration dry-run, and reconciliation workflow in Phase 6. |
| First-super-admin and recovery flows are not fully validated. | `WP-013` validates invited privileged-account activation, not first-super-admin bootstrap, account recovery, or emergency access ([Keycloak WP-013 result](../poc/keycloak-wp013-result.md#residual-risks)). | Accepted MVP direction: keep first-super-admin bootstrap simple, idempotent, outside the public API, and audited; broader recovery and break-glass ceremony remains later hardening ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |

## Decisions To Take

| Decision | Recommended Phase 5 outcome | Why it is needed |
| --- | --- | --- |
| Adopt, adjust, or reject the active direction. | Accepted: adopt for constrained MVP design, with explicit MVP constraints. | The PoC validates the core behavior, and no current evidence forces a return to Phase 3 ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md#decision-options), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)). |
| Define the MVP boundary. | Accepted. | The MVP scope is accepted and authorized for Phase 6 by ADR 0005 ([MVP scope](./mvp-scope.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Confirm `authorization/check` as the protected-service contract. | Accept for MVP if service authentication, timeout, retry, cache, and fail-closed rules are decided. | The PoC validates the contract shape, but not production availability or latency behavior ([Keycloak WP-014 result](../poc/keycloak-wp014-result.md), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| Confirm OTP safeguards for privileged accounts. | Accepted for MVP: follow Keycloak documented built-in OTP, required-action, recovery-code, and brute-force protection mechanisms. | Exact realm values remain Phase 6 implementation details ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Choose durable audit storage. | Accepted for MVP: local file-backed append-only audit storage with one JSON event object per line. | Local audit is required for business decisions and audit reads/exports; storage policy is now fixed, while implementation details remain Phase 6 work (`FR-027`, `FR-028`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Audit storage policy](../architecture/audit-storage.md)). |
| Define direct Keycloak administration governance. | Accepted post-MVP deferral. | The MVP must still reject routine direct Keycloak business administration and treat unmanaged mutation as drift ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Assign Keycloak operations ownership. | Accepted for MVP: `super-admin`. | Phase 6 must turn this into concrete runbooks, backup/restore evidence, monitoring, secrets, incident, and rollback notes ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Lock Keycloak IAM schema policy. | Accepted for MVP: managed attributes, unmanaged attributes disabled, account-type client roles, protected-service client roles, IAM Control Plane API-only mutation, and strict migration. | The PoC used unmanaged attributes as a shortcut; the accepted schema policy closes that production gap while preserving direct-admin drift detection (`FR-026`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md)). |
| Prepare MVP security regression tests. | Accepted for MVP: no frontend-only authorization, no raw-claim authorization, token validation, subject-link immutability, fail-closed behavior, drift denial, and audit evidence. | The test gate turns the accepted architecture rules into executable Phase 6 evidence before production readiness ([MVP Security Test Plan](./security-test-plan.md), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| Decide whether another Phase 4 runtime is needed. | Optional, targeted only. | If reviewers are uncomfortable with protected-service availability or OTP reset/recovery, run one more PoC-only validation before MVP authorization; otherwise carry them as MVP design gates. |

## Minimum Conditions To Authorize an MVP

The project has authorized Phase 6 because the conditions below are met or explicitly accepted as MVP residual risk. Phase 6 must still implement the accepted evidence before the MVP is declared production-ready.

| Gate | Minimum condition | Evidence expected before authorization |
| --- | --- | --- |
| Explicit movement to Phase 6 | Accepted. | ADR 0005 explicitly authorizes Phase 6 production MVP implementation for the accepted MVP scope ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| MVP scope | Accepted. | The [MVP scope note](./mvp-scope.md) is accepted and linked from ADR 0005. |
| Control-plane API contract | The IAM Control Plane API endpoint set, actor model, service authentication, operation authorization, error model, idempotency expectations, and audit behavior are accepted. | Accepted in the [IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md), with remaining Phase 6 schema detail and implementation choices separated from the contract. |
| Protected-service access stop | Accepted: `authorization/check` has fixed timeout, retry, cache, fail-closed, and access-stop behavior for MVP. | The [authorization-check runtime behavior](../architecture/authorization-check-behavior.md) sets no positive cache, one retry on transient failures, fail-closed `KO`, and next-check access stop with `<= 1 second` measurable bound outside outage (`FR-016`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Audit storage | Accepted for MVP: local durable file-backed audit storage, append-only, with one JSON event object per physical line; indefinite retention; super-admin API read; export out of scope; correlation IDs; backup and confidentiality requirements. | Accepted in the [Audit storage policy](../architecture/audit-storage.md), with Phase 6 details for file path, rotation, permissions, backup mechanism, restore testing, and encryption-at-rest. |
| Privileged authentication | Accepted for MVP. | Use Keycloak's documented built-in OTP policy, OTP reset/reconfiguration, recovery-code, and brute-force protection mechanisms; Phase 6 defines exact values and verifies the flow ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Direct-admin governance | Accepted post-MVP deferral. | Formal governance is deferred, but the MVP still rejects routine direct Keycloak business administration and treats unmanaged mutation as drift ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Keycloak operations | Accepted MVP owner: `super-admin`. | Phase 6 must produce concrete operations evidence before production data is trusted ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| IAM-state schema policy | Accepted for MVP: Keycloak User Profile managed attributes, unmanaged attributes disabled, account-type client roles on `edrlab-backoffice`, service-access client roles on protected-service clients, IAM Control Plane API-only mutation, strict invariant checks, and dry-run migration. | Accepted in the [Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md), with Phase 6 details for exact User Profile JSON, technical service-account grants, role metadata serialization, migration scripts, and drift reconciliation. |
| Security regression tests | Accepted for MVP: the test plan covers no frontend-only authorization, no raw token claim authorization, issuer/audience/token validation, subject-link immutability, fail-closed denials, drift denial, and audit creation. | Accepted in the [MVP Security Test Plan](./security-test-plan.md); Phase 6 must implement the tests as executable evidence before production readiness. |

## Accepted API Contract

The IAM Control Plane API contract is accepted for MVP design. It fixes REST endpoints under `/iam`, actors, Keycloak/OIDC user authentication, service-to-service client credentials for `access-check-demo-service`, operation authorization, RFC 9457 Problem Details errors, idempotence rules, audit event coverage, and `X-Correlation-Id` propagation ([IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md), [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)).

The runtime behavior for `authorization/check` is also accepted: `500 ms` protected-service timeout per attempt, one retry with jitter, `1000 ms` IAM-to-Keycloak timeout, one IAM retry on transient Keycloak/network failures, no positive cache, optional `5 second` negative cache, no indeterminate cache, fail-closed `KO`, and next-check access stop with a `<= 1 second` measurable bound outside outage ([Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).

The durable audit storage policy is accepted for MVP design: local file-backed append-only audit storage, one JSON event object per physical line, indefinite initial retention, super-admin API consultation, no initial export, required `correlationId`, backup inclusion, and confidentiality controls ([Audit Storage Policy](../architecture/audit-storage.md)).

The Keycloak IAM schema policy is accepted for MVP design: managed EDRLab attributes, unmanaged attributes disabled, account type represented by exactly one `edrlab-backoffice` client role, service access represented by protected-service client roles, control-plane-only mutation, fail-closed invariant checks, and strict dry-run migration ([Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)).

The MVP security regression test plan is accepted for MVP design. It fixes the required tests for frontend-only bypass rejection, raw-claim rejection, issuer and audience validation, subject-link immutability, fail-closed dependency behavior, drift denial, and audit evidence ([MVP Security Test Plan](./security-test-plan.md)).

ADR 0005 authorizes Phase 6 production MVP implementation. The authorization carries forward accepted residual risks: detailed direct-admin governance is post-MVP, `super-admin` owns Keycloak operations for MVP, OTP safeguards follow Keycloak built-ins, and first-super-admin bootstrap stays simple but idempotent and audited ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)).

The `bootstrap-process` is intentionally modeled as an initialization actor, not a public API actor. It is needed only because the first `super-admin` cannot be created by an existing `super-admin`; it must remain outside the public API, idempotent, controlled, and audited (`FR-008`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Decision Matrix

| Decision path | Accept when | Result |
| --- | --- | --- |
| Adopt for MVP design and authorize Phase 6 | Accepted by ADR 0005 on 2026-06-26. | Current accepted path; Phase 6 may start inside the accepted MVP scope. |
| Adjust and re-review | Reviewers accept Keycloak but reject one production boundary, such as `authorization/check`, local audit storage, or direct-admin governance. | Update the relevant architecture or PoC artifact, then re-run a targeted review. |
| Continue Phase 4 validation | Reviewers need one more runtime proof for a high-risk item such as protected-service availability or OTP recovery/reset. | Add one narrow Docker-only PoC, then update this note. |
| Return to Phase 3 | Reviewers reject Keycloak self-hosting, reject the IAM Control Plane API boundary, or decide production operations are too heavy for `FR-030`. | Reopen solution choice with the current PoC evidence as negative or conditional evidence. |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [ADR 0005 - Authorize Phase 6 Production MVP](../decisions/0005-authorize-phase-6-production-mvp.md)
- [MVP Scope - Keycloak IAM Control Plane API](./mvp-scope.md)
- [MVP Security Test Plan](./security-test-plan.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
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
