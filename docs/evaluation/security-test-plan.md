# MVP Security Test Plan

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Evaluation
Last reviewed: 2026-06-29

## Purpose

This page is the compact Phase 6 security evidence tracker. The MVP cannot be
called production-ready while any row is `Partial` or `Open`, unless the row is
moved to `Deferred` with explicit accepted risk. Scope and behavior details live
in [MVP scope](./mvp-scope.md), the
[IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md),
[authorization check behavior](../architecture/authorization-check-behavior.md),
[audit storage architecture](../architecture/audit-storage.md), and
[Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md).

Statuses are based on the current Docker runtime tests in
[`access-control/tests/test_mvp_security.py`](../../access-control/tests/test_mvp_security.py)
and the evidence workflow in the
[access-control runtime runbook](../../access-control/README.md#evidence).

## Status Legend

| Status | Meaning |
| --- | --- |
| `Implemented` | Current Docker runtime tests cover the row. |
| `Partial` | Some coverage exists, but the full scenario or evidence is not closed. |
| `Open` | No executable MVP test was found for the row. |
| `Deferred` | Postponed with explicit accepted Phase 6 risk. None are currently recorded. |

## Test Tracker

| ID | Status | Proof target | Current evidence or gap |
| --- | --- | --- | --- |
| `SEC-FE-001` | `Implemented` | Member cannot bypass UI and call admin endpoints directly. | Covered by member/admin bearer and impersonation tests. |
| `SEC-FE-002` | `Partial` | Client-supplied hidden/admin fields cannot mutate protected state. | Onboarding identity override and rejected mutations covered; full field coverage across admin endpoints remains open. |
| `SEC-FE-003` | `Implemented` | Protected service ignores UI state and calls `authorization/check`. | Covered by demo service authentication and authorization tests. |
| `SEC-CLAIM-001` | `Partial` | Stale token role claims do not keep access after role removal. | Access-stop after role removal and disablement covered; stale real-token role-claim evidence remains open. |
| `SEC-CLAIM-002` | `Implemented` | Misleading raw account or service-role claims do not authorize access. | Covered by raw OIDC claim rejection tests. |
| `SEC-CLAIM-003` | `Partial` | Admin-looking token for inactive or drifted state fails closed. | Drift and fail-closed paths covered; explicit inactive admin-looking token case remains open. |
| `SEC-TOKEN-001` | `Implemented` | Wrong issuer is rejected before account resolution. | Covered by OIDC subject-token and service-token validation tests; issuer validation is required by OpenID Connect ID Token validation ([OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)). |
| `SEC-TOKEN-002` | `Implemented` | Wrong or missing audience is rejected before account resolution. | Covered by OIDC subject-token and service-token validation tests; JWT audience identifies intended recipients ([RFC 7519](https://www.rfc-editor.org/rfc/rfc7519#section-4.1.3)). |
| `SEC-TOKEN-003` | `Partial` | Expired, invalid-signature, unsupported-algorithm, or wrong-client token is rejected. | Expiry, subject, and expected-client checks are covered for OIDC subject-token and service-token introspection; invalid-signature and unsupported-algorithm cases remain open for local JWT-validation paths. |
| `SEC-SUBJECT-001` | `Implemented` | One invited account activates from verified bearer evidence. | Covered by bearer-derived onboarding activation tests. |
| `SEC-SUBJECT-002` | `Implemented` | Repeating activation for the same subject is idempotent and audited. | Covered by repeat onboarding activation test asserting unchanged active subject linkage and `onboarding.activate` audit outcome `no_change`. |
| `SEC-SUBJECT-003` | `Partial` | Different-subject activation or mutation cannot rebind the link. | Client-supplied identity claims covered; direct linked-subject mutation and audit evidence remain open. |
| `SEC-FAIL-001` | `Partial` | Demo service returns `503 KO` when IAM API is unreachable. | Auth failure mappings covered; explicit network-unreachable evidence remains open. |
| `SEC-FAIL-002` | `Partial` | Keycloak outage or timeout during `authorization/check` returns indeterminate `503 KO`. | Unexpected Keycloak state errors are audited; full unavailable/timeout end-to-end evidence remains open. |
| `SEC-FAIL-003` | `Partial` | Missing or corrupt managed attributes block sensitive operations. | Account-type drift covered; lifecycle, account ID, and schema-version corruption remain open. |
| `SEC-FAIL-004` | `Partial` | Unknown service/role, inactive account, disabled role, or archived role fails closed. | Role removal and disablement covered; unknown IDs, archived role, and inactive account remain open. |
| `SEC-DRIFT-001` | `Implemented` | Direct protected-service role mapping in Keycloak is detected and denied. | Covered by direct service-role drift tests. |
| `SEC-DRIFT-002` | `Open` | Direct lifecycle change in Keycloak is treated as drift. | Add lifecycle-drift test and audit assertion. |
| `SEC-DRIFT-003` | `Implemented` | Missing, multiple, or elevated account-type roles block access. | Covered by account-type drift tests. |
| `SEC-DRIFT-004` | `Open` | Direct `iam.linked_subject` change is drift. | Proposed EDRLab-controlled append-only subject-link ledger outside Keycloak; no runtime ledger or executable drift test yet. |
| `SEC-AUDIT-001` | `Partial` | Required events exist for allow, deny, reject, indeterminate, drift, bootstrap, onboarding, role, lifecycle, and audit-read scenarios. | Several event classes covered; full matrix-wide audit evidence remains open. |
| `SEC-AUDIT-002` | `Implemented` | Audit file remains one JSON object per physical line. | Covered by audit JSONL format test. |
| `SEC-AUDIT-003` | `Partial` | Audit contains no tokens, OTP values, passwords, recovery codes, client secrets, private keys, raw session IDs, or raw subject tokens. | Raw subject-token absence covered; full forbidden-value list remains open. |

## Evidence Rule

Each closed row must leave machine-readable and human-reviewable evidence:
test ID, timestamp, actor, target, correlation ID, HTTP status/body where
applicable, before/after state for mutations or drift, local audit event
references, and an assertion that unauthorized mutation did not occur.

The tracker focuses on authorization and audit risks aligned with OWASP
authorization testing guidance and API authorization risk families
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
[OWASP API Security Top 10](https://owasp.org/API-Security/)).

## References

- [MVP scope](./mvp-scope.md)
- [Access-control runtime runbook](../../access-control/README.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Access-control MVP security tests](../../access-control/tests/test_mvp_security.py)
- [Authorization check behavior](../architecture/authorization-check-behavior.md)
- [Audit storage architecture](../architecture/audit-storage.md)
- [Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
