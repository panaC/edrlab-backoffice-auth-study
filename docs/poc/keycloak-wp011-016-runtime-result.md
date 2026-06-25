# Keycloak WP-011 Through WP-016 Runtime Result

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Execution](#execution)
- [Result](#result)
- [Decision Matrix](#decision-matrix)
- [Evidence Map](#evidence-map)
- [Surprises](#surprises)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

This result records the Docker execution of the prepared `WP-011` through `WP-016` runtime bundle for the active Keycloak IAM plus EDRLab IAM Control Plane API direction. The bundle validates controlled Keycloak Admin REST mutations, local IAM Control Plane API fixture decisions, onboarding/lifecycle behavior, protected-service authorization checks, direct-admin drift handling, Keycloak admin-event correlation, and local EDRLab audit examples ([Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

This remains a non-production PoC execution. It does not approve production code, production database topology, CI, deployment, durable audit storage, service-to-service authentication, monitoring, backup/restore, or Phase 6 MVP implementation ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Execution

Environment:

- Runtime: Docker Compose Keycloak PoC under [`poc/keycloak`](../../poc/keycloak/README.md).
- Scripts executed: `start.sh`, `bootstrap.sh`, `verify.sh`, then `verify-iam-control-plane-runtime.sh`.
- Final evidence directory: [`poc/keycloak/evidence/20260625T145126Z`](../../poc/keycloak/evidence/20260625T145126Z/).
- Final summary file: [`wp-011-016-summary.json`](../../poc/keycloak/evidence/20260625T145126Z/wp-011-016-summary.json).

`WP-001` setup verification passed before the bundle. The final runtime bundle completed with `result = pass_with_blocked_privileged_evidence`, `blocked = true`, and `blocked_work_packages = ["WP-013"]`.

## Result

The runtime evidence supports the selected Keycloak IAM plus EDRLab IAM Control Plane API direction for `WP-011`, `WP-012`, `WP-014`, `WP-015`, and `WP-016` at PoC level. This bundle did not clear `WP-013`: privileged authentication evidence remained blocked because the PoC realm had no explicit ACR/LoA, AMR mapper, or browser-flow reference value that could prove step-up authentication for `admin` or `super-admin` activation (`FR-034`, `FR-043`, `FR-044`; [Keycloak WP-013 result](./keycloak-wp013-result.md)).

Follow-up note: a dedicated `WP-013` Docker runtime was executed after this bundle and resolved the privileged-evidence blocker at PoC level by configuring and verifying Keycloak ACR/LoA step-up with OTP ([Keycloak WP-013 result - Runtime Execution](./keycloak-wp013-result.md#runtime-execution)).

The runtime confirms:

- controlled member service-role assignment is visible in Keycloak state;
- account-type mutation is denied before Keycloak mutation;
- safe onboarding activates and links a verified invited user;
- unsafe unverified onboarding is denied without Keycloak mutation;
- `authorization/check` allows an active member with a current service role;
- `authorization/check` denies a disabled member and fails closed on direct-admin drift;
- Keycloak admin events correlate with service-role, lifecycle, onboarding, and drift scenarios;
- local EDRLab audit records include the required actor, decision, reason, before/after state, and source fields.

## Decision Matrix

| Work package | Runtime decision | Evidence | Phase 5 interpretation |
| --- | --- | --- | --- |
| `WP-011` IAM Control Plane API admin anti-bypass path | Pass. | `service-role-assignment` observed `allow`; `account-type-mutation-denied` observed `deny`; local audit has actor and reason fields. | The controlled server-side path is viable at PoC level, but still fixture-based. |
| `WP-012` lifecycle and onboarding | Pass. | `safe-onboarding-activation` observed `allow`; `unverified-onboarding-denied` observed `deny`; denied case did not mutate Keycloak. | The selected lifecycle and subject-link mapping is viable at PoC level. |
| `WP-013` privileged account evidence | Blocked in this bundle. | `privileged-evidence-check` observed `blocked` with `missing_explicit_privileged_authentication_evidence`. | This bundle required a follow-up dedicated step-up validation, later completed in `WP-013`. |
| `WP-014` service access and protected-service authorization | Pass. | `authorization_allow_active_member`, `authorization_deny_disabled_member`, and `authorization_deny_drift` are all true in the summary. | `authorization/check` is viable as the first protected-service contract, subject to later service-to-service and availability review. |
| `WP-015` direct-admin drift and shortcut rejection | Pass. | Direct Admin REST lifecycle change observed as `drift_detected`; authorization fails closed on drift. | Direct Keycloak admin mutation must be treated as drift unless explicitly reconciled. |
| `WP-016` audit and operations review | Pass with production gaps. | 12 local audit records, 7 control-plane decisions, and admin-event correlation passed. | Local EDRLab audit remains required; Keycloak events are useful supplemental evidence, not the business audit authority. |

Overall decision for this runtime bundle: `pass_with_blocked_privileged_evidence`.

## Evidence Map

| Evidence file | Meaning |
| --- | --- |
| `wp-011-016-summary.json` | Final bundle result, pass flags, blocked work packages, and production gaps. |
| `wp-011-016-control-plane-decisions.json` | Decision matrix with expected result, observed result, actor, target, reason code, mutation expectation, and pass flag. |
| `wp-011-016-keycloak-mapping.json` | Keycloak client-role and user-attribute mapping under test. |
| `wp-011-016-user-profile-config.json` | Keycloak user profile configuration used so PoC IAM attributes can be written from the administrative context. |
| `wp-011-016-keycloak-admin-event-correlation.json` | Resource-specific Keycloak admin-event correlation for service-role, lifecycle, onboarding, and drift scenarios. |
| `wp-011-016-local-audit.json` | Local EDRLab audit-shaped records for controlled mutations, denials, onboarding, authorization, drift, privileged-evidence checks, and audit read/export examples. |
| `wp-011-016-authorization-*.json` | Protected-service `authorization/check` allow, disabled-deny, and drift-deny evidence. |
| `wp-011-016-effective-services-*.json` | `GET /me/services` effective-service listing evidence for active, disabled, and drifted states. |
| `wp-011-016-privileged-evidence.json` | Privileged-authentication evidence inspection and current blocker. |

## Surprises

The first runtime attempt exposed that Keycloak did not persist the PoC IAM user attributes until the realm user profile allowed those attributes in the administrative context. Keycloak documents that it recognizes only attributes defined in the user profile by default, and unmanaged attributes are disabled by default unless configured otherwise ([Keycloak user profile - managed and unmanaged attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)). The script now configures `unmanagedAttributePolicy = "ADMIN_EDIT"` for the PoC realm and records the resulting configuration in `wp-011-016-user-profile-config.json`.

This is acceptable for the PoC, but Phase 5 should decide whether production uses managed attributes with explicit schema/permissions instead of unmanaged administrative attributes. Keycloak recommends staying strict with attribute policy where possible ([Keycloak user profile - managed and unmanaged attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)).

## Residual Risks

- This bundle did not configure or verify a real privileged step-up login path; the follow-up dedicated `WP-013` runtime later covered that gap at PoC level.
- The IAM Control Plane API is still a PoC fixture, not production service code.
- The local audit evidence is JSON output, not durable append-only storage.
- The runtime does not prove service-to-control-plane authentication, latency, retries, timeout behavior, monitoring, alerting, backup/restore, break-glass governance, or database topology.
- User profile policy is PoC-level. Production should review explicit managed attributes, permissions, validations, and end-user visibility before accepting Keycloak user attributes as IAM state.

## Decision Impact

The runtime bundle was strong enough to move the Keycloak IAM plus EDRLab IAM Control Plane API direction into Phase 5 review with one explicit blocker: privileged authentication evidence for `admin` and `super-admin` onboarding. The dedicated `WP-013` runtime later resolved that blocker at PoC level, and ADR 0003 accepted OTP MFA for the current direction. Phase 5 should still not clear production adoption until the production gaps above, plus OTP enrollment/reset/recovery safeguards, are either resolved or explicitly accepted as follow-up constraints ([Keycloak WP-013 result](./keycloak-wp013-result.md), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)).

## References

- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak WP-012 Result - Account Lifecycle and Onboarding](./keycloak-wp012-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](./keycloak-wp013-result.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak WP-014 Result - Service Access Authorization](./keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](./keycloak-wp015-result.md)
- [Keycloak WP-016 Result - Audit and Operations Review](./keycloak-wp016-result.md)
- [Keycloak WP-017 Result - Results and Phase 5 Review Inputs](./keycloak-wp017-result.md)
- [Keycloak PoC Runtime](../../poc/keycloak/README.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak User Profile - Managed and Unmanaged Attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
