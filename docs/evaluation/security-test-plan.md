# MVP Security Test Plan

Status: Accepted
Phase: Phase 5 - Review and Decision
Scope: Evaluation
Last reviewed: 2026-06-26

## Contents

- [Purpose](#purpose)
- [Principles](#principles)
- [Test Dataset](#test-dataset)
- [Test Matrix](#test-matrix)
- [Evidence Requirements](#evidence-requirements)
- [Execution Expectations](#execution-expectations)
- [Acceptance Criteria](#acceptance-criteria)
- [Phase 6 Implementation Inputs](#phase-6-implementation-inputs)
- [References](#references)

## Purpose

This document fixes the MVP security regression test plan for the accepted Keycloak IAM plus EDRLab IAM Control Plane API direction. It covers the minimum tests required before declaring the MVP production-ready: no frontend-only authorization, no raw token-claim authorization, issuer/audience/token validation, immutable subject link, fail-closed behavior, direct-admin drift denial, and audit evidence ([Phase 5 review note](./phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp), [IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md)).

The plan is a Phase 5 evaluation artifact. It does not add production code, test code, CI, deployment, or runtime PoC artifacts. Phase 6 must turn it into executable Linux/Docker-friendly tests before production data or protected services are trusted ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Principles

All MVP security tests follow these principles:

- Authorization is enforced server-side by the IAM Control Plane API or protected service backend, not by UI visibility, hidden buttons, route guards, or browser-held state (`FR-020`, `FR-033`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#verify-that-authorization-checks-are-performed-in-the-right-location)).
- Permissions are validated on every security-relevant request. OWASP recommends validating permissions on every request and creating unit and integration tests for authorization logic ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#validate-the-permissions-on-every-request)).
- Deny-by-default and fail-closed behavior are required when authorization state is missing, stale, inconsistent, unreadable, or unsafe (`FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).
- Token claims may be inspected as evidence or UI hints, but protected services do not authorize from raw claims. They call `POST /iam/authorization/check` and use current Keycloak state mediated by the IAM Control Plane API ([Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md#token-and-claim-boundary)).
- Every failed or rejected security-relevant operation must leave reviewable evidence: HTTP response, state before/after, correlation ID, and audit event where required ([Audit Storage Policy](../architecture/audit-storage.md), [OWASP Authorization Cheat Sheet - logging](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#implement-appropriate-logging)).

## Test Dataset

The MVP test suite needs these minimum subjects, accounts, service roles, and state variants:

| Fixture | Purpose |
| --- | --- |
| `member_active_with_role` | Positive protected-service access for `access-check-demo:consult`. |
| `member_active_without_role` | Member deny without service role. |
| `member_disabled_with_old_role` | Access-stop and stale-token denial after disablement. |
| `member_archived` | Terminal lifecycle deny. |
| `member_invited` | No protected-service access before onboarding activation. |
| `admin_active` | Automatic covered-service access without member service-role assignment. |
| `super_admin_active` | Inherited admin access and audit consultation capability. |
| `subject_unlinked_invited` | Safe onboarding activation candidate. |
| `subject_linked_active` | Subject-link immutability candidate. |
| `drift_service_role_added` | Direct Keycloak service-role mutation outside the IAM Control Plane API. |
| `drift_lifecycle_changed` | Direct Keycloak lifecycle mutation outside the IAM Control Plane API. |
| `drift_account_type_changed` | Direct Keycloak account-type mutation or multiple account-type roles. |
| `drift_subject_link_changed` | Direct Keycloak subject-link mutation. |

The dataset follows the accepted MVP scope, schema policy, and `authorization/check` behavior ([MVP scope](./mvp-scope.md), [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md), [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).

## Test Matrix

| ID | Security area | Test case | Expected result |
| --- | --- | --- | --- |
| `SEC-FE-001` | No frontend-only authorization | Call every IAM admin endpoint directly as a `member`, bypassing UI route visibility. | Server returns `401` or `403`; no Keycloak state mutation; rejection audit where the operation is security-relevant. |
| `SEC-FE-002` | No frontend-only authorization | Submit admin-only payload fields from the browser, such as account type, lifecycle, subject link, or service-role changes outside the allowed operation. | Untrusted fields are ignored or rejected; invariant-changing requests fail; no hidden field changes state. |
| `SEC-FE-003` | No frontend-only authorization | Call `access-check-demo-service` directly after hiding or showing UI links client-side. | Protected service calls `authorization/check`; UI state does not grant access. |
| `SEC-CLAIM-001` | No raw claims | Reuse a token that still contains a service role after the role is removed from the current account state. | Protected service returns `403` KO after current-state check; raw token role is not sufficient. |
| `SEC-CLAIM-002` | No raw claims | Use a token or crafted test fixture with misleading account-type or service-role claims. | IAM API ignores raw claims for final authorization and uses managed Keycloak state plus invariants. |
| `SEC-CLAIM-003` | No raw claims | Call protected service with an admin-looking token for an account that is currently inactive or drifted. | Fail closed: deny or indeterminate `503` KO depending on whether current state is known invalid or unreadable. |
| `SEC-TOKEN-001` | Token validation | Use a token with wrong issuer. | Rejected before account resolution. OIDC requires the issuer value to match the expected issuer exactly for ID Token validation ([OpenID Connect Core - ID Token Validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)). |
| `SEC-TOKEN-002` | Token validation | Use a token with wrong audience or missing expected audience. | Rejected before account resolution. JWT audience identifies intended recipients, and processors must reject tokens whose audience does not include them when `aud` is present ([RFC 7519 - audience](https://www.rfc-editor.org/rfc/rfc7519#section-4.1.3)). |
| `SEC-TOKEN-003` | Token validation | Use expired token, invalid signature, unsupported algorithm, or token from another client. | Rejected before account resolution; no fallback to raw profile or email lookup. OIDC validation requires signature validation for ID Tokens and current time before `exp` ([OpenID Connect Core - ID Token Validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)). |
| `SEC-SUBJECT-001` | Subject-link immutability | Activate exactly one invited account with verified matching email and no subject link. | Account becomes active, `edrlab.linked_subject` is set once, audit event is written. |
| `SEC-SUBJECT-002` | Subject-link immutability | Repeat activation with the same subject after successful activation. | Idempotent success or no-op with no link mutation; audit distinguishes `no_change` if applicable. |
| `SEC-SUBJECT-003` | Subject-link immutability | Attempt activation or admin mutation with a different subject. | Rejected; original `edrlab.linked_subject` remains unchanged; audit records rejected subject-link mutation. |
| `SEC-FAIL-001` | Fail-closed | Make IAM Control Plane API unreachable from `access-check-demo-service`. | Demo service returns HTTP `503` with `{"result":"KO","authorized":false}`. |
| `SEC-FAIL-002` | Fail-closed | Make Keycloak unavailable or force timeout during `authorization/check`. | IAM API returns indeterminate `503`; demo service returns `503` KO; no allow is produced. |
| `SEC-FAIL-003` | Fail-closed | Remove or corrupt required managed attributes such as lifecycle, account ID, or schema version. | Sensitive operations block; protected-service checks deny or return indeterminate `503` KO. |
| `SEC-FAIL-004` | Fail-closed | Use unknown service ID, unknown role ID, disabled role, archived role, or inactive account. | Confirmed business deny returns `403` KO; unreadable or incoherent state returns `503` KO. |
| `SEC-DRIFT-001` | Drift denial | Directly add `consult` role on `access-check-demo-service` to a member in Keycloak. | IAM API detects unmanaged change or quarantine need; sensitive operations and protected access deny until reconciliation. |
| `SEC-DRIFT-002` | Drift denial | Directly change lifecycle from `disabled` to `active` in Keycloak. | Treated as unmanaged lifecycle drift; access remains denied or quarantined until reviewed. |
| `SEC-DRIFT-003` | Drift denial | Directly change `account-type-member` to `account-type-admin`, add multiple account-type roles, or remove all account-type roles. | Invariant violation; admin operations block; protected-service checks fail closed. |
| `SEC-DRIFT-004` | Drift denial | Directly change `edrlab.linked_subject`. | Invariant violation; access and sensitive operations deny; audit records drift or rejected mutation. |
| `SEC-AUDIT-001` | Audit coverage | Execute allowed, denied, rejected, indeterminate, drift, bootstrap, onboarding, role, lifecycle, and audit-read scenarios. | Required local audit events exist with `eventId`, `occurredAt`, actor, operation, target, outcome, reason where useful, and `correlationId`. |
| `SEC-AUDIT-002` | Audit format | Inspect audit file after security tests. | One JSON event object per physical line; append-only behavior preserved; no multiline pretty-printing. |
| `SEC-AUDIT-003` | Audit confidentiality | Search audit records for access tokens, refresh tokens, OTP values, passwords, recovery codes, client secrets, private keys, raw session identifiers, or raw subject tokens. | No forbidden sensitive values are present; audit uses stable IDs and reason codes. |

This matrix targets the OWASP API authorization risk families most relevant to the MVP, including broken object-level authorization and broken function-level authorization ([OWASP API Security Top 10 2023](https://owasp.org/API-Security/)).

## Evidence Requirements

Every test case must produce enough evidence for review:

| Evidence | Required for |
| --- | --- |
| Test ID, timestamp, actor, target, and correlation ID. | Every test. |
| HTTP request summary and response status/body. | Every API or protected-service test. |
| Keycloak state before and after. | Mutating, drift, lifecycle, role, and subject-link tests. |
| IAM Control Plane API decision record. | Authorization, admin, subject-link, fail-closed, and drift tests. |
| Local audit event reference. | Mutating, rejected, denied, indeterminate, drift, audit-read, onboarding, and bootstrap tests. |
| Assertion that no unauthorized mutation occurred. | Every negative mutation test. |
| Assertion that `authorization/check` was invoked. | Every protected-service access test. |

The evidence should be machine-readable enough for automation and human-readable enough for Phase 5/Phase 6 review. The audit evidence must follow the accepted audit storage and event-field policies ([Audit Storage Policy](../architecture/audit-storage.md), [IAM Control Plane API contract - Audit](../architecture/iam-control-plane-api-contract.md#audit)).

## Execution Expectations

Phase 6 should implement this plan as automated tests. The preferred runtime is a Linux-targeted Docker-based test environment, consistent with the repository's runtime documentation rules ([AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)). Manual Keycloak Console actions are acceptable only as exploratory inspection; core validation steps must be scripted or explicitly recorded as partial-manual limitations.

The test suite should run at three levels:

| Level | Scope |
| --- | --- |
| Unit/contract | Token validation, invariant checks, reason-code mapping, audit-event construction, and fail-closed decision helpers. |
| Integration | IAM Control Plane API with Keycloak test realm and local audit file. |
| End-to-end | `access-check-demo-service` calling `authorization/check`, including unavailable dependency and stale-token scenarios. |

## Acceptance Criteria

The MVP security test gate passes only when:

- all tests in the matrix are implemented or explicitly deferred with accepted risk;
- every negative authorization test rejects access server-side;
- every negative mutation test proves state was not changed;
- every protected-service test proves `authorization/check` is the enforcement decision;
- every token-validation test rejects invalid issuer, invalid audience, expired token, invalid signature, or unsupported token;
- every subject-link mutation attempt after activation is rejected and audited;
- every dependency failure or unsafe state fails closed;
- every direct Keycloak business mutation is denied, quarantined, or reported as drift;
- audit records are created for all required events and contain no forbidden secrets.

Failure of any implemented test blocks declaring the MVP production-ready unless the project owner explicitly records a Phase 6 risk acceptance.

## Phase 6 Implementation Inputs

| Input | Status |
| --- | --- |
| Exact test runner and language | Open Phase 6 implementation detail. |
| Exact Docker Compose test topology | Open Phase 6 implementation detail. |
| Fixture creation mechanism | Open implementation detail; must be scripted and repeatable. |
| Evidence output format | Open implementation detail; should be JSON plus a short human summary. |
| CI integration | Open Phase 6 implementation detail; not created in Phase 5. |
| Risk-acceptance format for deferred tests | Open governance detail before production readiness. |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [MVP Scope - Keycloak IAM Control Plane API](./mvp-scope.md)
- [Phase 5 Review Note](./phase-5-review-note.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](../poc/keycloak-wp011-result.md)
- [Keycloak WP-012 Result - Account Lifecycle and Onboarding](../poc/keycloak-wp012-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](../poc/keycloak-wp013-result.md)
- [Keycloak WP-014 Result - Service Access Authorization](../poc/keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](../poc/keycloak-wp015-result.md)
- [Keycloak WP-016 Result - Audit and Operations Review](../poc/keycloak-wp016-result.md)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
