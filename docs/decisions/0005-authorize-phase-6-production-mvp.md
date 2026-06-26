# 0005 - Authorize Phase 6 Production MVP

Status: Accepted
Date: 2026-06-26
Supersedes: none

## Context

ADR 0004 adopted the self-hosted Keycloak IAM plus EDRLab Admin Console and IAM Control Plane API architecture for constrained MVP design, but explicitly did not authorize Phase 6 production MVP implementation ([ADR 0004](./0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)).

The remaining Phase 5 design gates have now been accepted or explicitly deferred as accepted MVP residual risk:

- MVP scope is accepted for the first production MVP ([MVP scope](../evaluation/mvp-scope.md)).
- IAM Control Plane API contract is accepted ([IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md)).
- `authorization/check` timeout, retry, cache, fail-closed, access-stop, audit, and metrics behavior is accepted ([Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).
- Durable audit storage is accepted as local file-backed append-only JSON-lines-style storage ([Audit Storage Policy](../architecture/audit-storage.md)).
- Keycloak IAM schema policy is accepted with managed attributes, client roles, control-plane-only mutation, and strict migration ([Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)).
- MVP security regression test plan is accepted ([MVP Security Test Plan](../evaluation/security-test-plan.md)).
- User decision on 2026-06-26: direct Keycloak admin governance can be defined post-MVP; the MVP must still reject routine direct Keycloak business administration and treat unmanaged mutation as drift.
- User decision on 2026-06-26: `super-admin` is the accountable Keycloak operations owner for the MVP.
- User decision on 2026-06-26: privileged OTP safeguards should follow Keycloak's recommended and documented built-in mechanisms for the MVP.
- User decision on 2026-06-26: first-super-admin bootstrap should stay simple for the MVP.

Keycloak documents OTP policies, required OTP reconfiguration paths, recovery codes, and brute-force detection for password, OTP, and recovery-code attempts ([Keycloak OTP policies](https://www.keycloak.org/docs/latest/server_admin/#one-time-password-otp-policies), [Keycloak creating an OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp), [Keycloak recovery codes](https://www.keycloak.org/docs/latest/server_admin/#recovery-codes), [Keycloak brute force attacks](https://www.keycloak.org/docs/latest/server_admin/#brute-force-attacks)). Keycloak also documents initial administrator bootstrapping and warns that broad realm administration is a privileged technical surface, which supports keeping EDRLab business administration behind the IAM Control Plane API ([Keycloak creating the first administrator](https://www.keycloak.org/docs/latest/server_admin/#creating-the-first-administrator), [Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)).

## Options Considered

| Option | Outcome | Reason |
| --- | --- | --- |
| Authorize Phase 6 production MVP with accepted residual risks. | Accepted. | The MVP design gates are accepted, and the remaining governance/operations details are either Phase 6 implementation work or explicitly accepted post-MVP follow-up. |
| Stay in Phase 5 until every operations and governance detail is fully specified. | Rejected. | The user explicitly accepts a simple MVP and defers direct-admin governance detail post-MVP. |
| Return to Phase 4 or Phase 3. | Rejected. | No current evidence invalidates the accepted Keycloak IAM Control Plane API direction. |

## Decision

Authorize the project to move from `Phase 5 - Review and Decision` to `Phase 6 - Production MVP`.

Phase 6 is authorized only for the accepted MVP scope:

- EDRLab Admin Console plus IAM Control Plane API as the business administration and authorization boundary.
- Self-hosted Keycloak as the IAM source for the accepted managed schema.
- `access-check-demo-service` as the first protected-service integration.
- `access-check-demo:consult` as the first service-access role.
- File-backed append-only local audit storage.
- Security tests defined by the accepted MVP security test plan.

Accepted MVP constraints:

- Direct Keycloak Admin Console is not a routine business administration path in the MVP. Formal direct-admin governance is deferred post-MVP, but unmanaged Keycloak mutations remain drift and must deny, quarantine, or fail closed as already specified.
- `super-admin` is the accountable Keycloak operations owner for the MVP. Phase 6 implementation must still create concrete runbooks, backup/restore evidence, monitoring, secrets handling, incident handling, and rollback notes before production data is trusted.
- OTP safeguards use Keycloak's documented built-in OTP policy, required-action, recovery-code, and brute-force protection mechanisms for the MVP; exact values and realm configuration are Phase 6 implementation details.
- First-super-admin bootstrap remains simple: an initialization process seeds the first EDRLab `super-admin` only when no valid `super-admin` exists, outside the public API, idempotently, and with local audit evidence.

## Consequences

Production MVP implementation work may start. Phase 6 may add production application code, dependencies, services, tests, runtime configuration, Docker artifacts, migration scripts, CI, and operational documentation when they are needed for the approved MVP scope ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

This decision does not approve work beyond the MVP scope. Real business protected-service integration, advanced audit export/search, WebAuthn/passkeys as mandatory authentication, production high availability, formal direct-admin governance, and broad Keycloak operations hardening remain post-MVP or later explicit scope decisions.

The MVP is not considered production-complete until Phase 6 implements and verifies the accepted security tests, audit behavior, bootstrap behavior, Keycloak schema migration, and minimum operations evidence.

## References

- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](./0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [Phase 5 Review Note](../evaluation/phase-5-review-note.md)
- [MVP Scope](../evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
- [MVP Security Test Plan](../evaluation/security-test-plan.md)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak OTP Policies](https://www.keycloak.org/docs/latest/server_admin/#one-time-password-otp-policies)
- [Keycloak Creating an OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp)
- [Keycloak Recovery Codes](https://www.keycloak.org/docs/latest/server_admin/#recovery-codes)
- [Keycloak Brute Force Attacks](https://www.keycloak.org/docs/latest/server_admin/#brute-force-attacks)
- [Keycloak Creating the First Administrator](https://www.keycloak.org/docs/latest/server_admin/#creating-the-first-administrator)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
