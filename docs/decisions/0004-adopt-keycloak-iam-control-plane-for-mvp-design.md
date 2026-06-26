# 0004 - Adopt Keycloak IAM Control Plane for MVP Design

Status: Accepted
Date: 2026-06-26
Supersedes: none

## Context

ADR 0002 selected the active validation direction: self-hosted Keycloak may hold IAM state, while the EDRLab Admin Console and IAM Control Plane API mediate business administration, protected-service authorization, and audit-relevant behavior ([ADR 0002](./0002-validate-keycloak-iam-bff.md)). ADR 0003 accepted OTP MFA as sufficient privileged-authentication evidence for the current direction, while keeping enrollment, reset, recovery, monitoring, and audit safeguards as production design work ([ADR 0003](./0003-accept-otp-for-privileged-authentication.md)).

The Phase 4 PoC evidence validates the core control-plane shape, lifecycle and onboarding checks, privileged step-up evidence, protected-service `authorization/check` contract, direct-admin drift handling, and audit boundary at PoC level ([Keycloak WP-017 result](../poc/keycloak-wp017-result.md), [Phase 5 review note](../evaluation/phase-5-review-note.md)). Phase 5 may adopt the solution for the next step, adjust it, return to Phase 3, or run targeted additional Phase 4 validation; it must not be treated as automatic production MVP approval ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

User decision on 2026-06-26: adopt this architectural choice for the MVP.

## Options Considered

| Option | Outcome | Reason |
| --- | --- | --- |
| Adopt Keycloak IAM plus EDRLab IAM Control Plane API for MVP design. | Accepted. | The PoC validates the main behavior needed to continue into constrained MVP design, with MVP authorization tracked separately ([Phase 5 review note](../evaluation/phase-5-review-note.md#review-position)). |
| Adjust and re-review before MVP design. | Rejected for now. | No current PoC result invalidates the selected architecture; remaining work is production-readiness definition rather than a proof that the direction cannot work. |
| Return to Phase 3 solution choice. | Rejected for now. | Review has not rejected Keycloak self-hosting or the IAM Control Plane API boundary. |

## Decision

Adopt self-hosted Keycloak as the IAM source with an EDRLab Admin Console and EDRLab IAM Control Plane API as the architectural direction for the constrained MVP design.

This decision means:

- the MVP design should use Keycloak for the validated IAM state and authentication-policy responsibilities described in ADR 0002;
- business administration must go through the EDRLab Admin Console and IAM Control Plane API, not routine direct Keycloak Admin Console edits;
- protected services should authorize through the reviewed `authorization/check` control-plane contract unless a later decision explicitly changes that contract;
- local EDRLab business audit remains required for access-control decisions, audit reads/exports, drift, and rationale; Keycloak events are supplemental evidence;
- OTP MFA is accepted for privileged onboarding in the current direction, with operational safeguards still required before production rollout.

This decision did not start Phase 6 production MVP implementation by itself. Follow-up ADR 0005 explicitly authorizes Phase 6 for the accepted MVP scope and records the closed or accepted residual-risk gates ([ADR 0005](./0005-authorize-phase-6-production-mvp.md), [Phase 5 review note - Minimum Conditions](../evaluation/phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Consequences

MVP planning can now assume the Keycloak IAM Control Plane architecture instead of reopening the vendor or architecture choice by default.

ADR 0005 later closed the Phase 6 authorization question for the accepted MVP scope. Production readiness still depends on Phase 6 implementation evidence for code, tests, runtime behavior, audit behavior, Keycloak schema migration, bootstrap behavior, and minimum operations evidence ([ADR 0005](./0005-authorize-phase-6-production-mvp.md), [Phase 5 review note - Minimum Conditions](../evaluation/phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp)).

No production code, production deployment, database schema, CI, migration, or durable production infrastructure is approved by this ADR.

## References

- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](./0002-validate-keycloak-iam-bff.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](./0003-accept-otp-for-privileged-authentication.md)
- [ADR 0005 - Authorize Phase 6 Production MVP](./0005-authorize-phase-6-production-mvp.md)
- [Phase 5 Review Note - Keycloak IAM Control Plane API](../evaluation/phase-5-review-note.md)
- [Keycloak WP-017 Result - Results and Phase 5 Review Inputs](../poc/keycloak-wp017-result.md)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
