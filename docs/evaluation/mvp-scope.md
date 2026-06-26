# MVP Scope - Keycloak IAM Control Plane API

Status: Accepted
Phase: Phase 5 - Review and Decision
Scope: Evaluation
Last reviewed: 2026-06-26

## Contents

- [Purpose](#purpose)
- [Decision Status](#decision-status)
- [Closed Scope Decisions](#closed-scope-decisions)
- [MVP Boundary](#mvp-boundary)
- [Account Operations](#account-operations)
- [Lifecycle](#lifecycle)
- [Service-Access Roles](#service-access-roles)
- [Protected Services](#protected-services)
- [Audit](#audit)
- [Privileged Onboarding](#privileged-onboarding)
- [Out of Scope](#out-of-scope)
- [Phase 6 Input Status](#phase-6-input-status)
- [References](#references)

## Purpose

This document defines the accepted functional MVP scope for the Keycloak IAM plus EDRLab Admin Console and IAM Control Plane API architecture. ADR 0004 adopts that architecture for constrained MVP design, and ADR 0005 authorizes Phase 6 production MVP implementation inside this scope ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The scope is limited to the access-control capability described in the feature requirements: account management, lifecycle, service-access roles, protected-service authorization, audit, and privileged onboarding ([Feature requirements](../../FEATURE-REQUIREMENTS.md#goal), [README - Core Features](../../README.md#core-features)).

## Decision Status

This is the accepted functional MVP scope for Phase 6 production MVP implementation. It remains a scope boundary, not a complete implementation plan; Phase 6 implementation must still produce code, tests, runtime configuration, migration scripts, and operations evidence inside this boundary ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

Current decision: accepted by user decision on 2026-06-26 and authorized for Phase 6 by ADR 0005.

## Closed Scope Decisions

| Topic | Decision |
| --- | --- |
| First protected service | The first MVP protected service is `access-check-demo-service`. It is a synthetic service used only to verify whether the current user has access. |
| Initial service-access role | The first service-access role is `access-check-demo:consult`. It covers only `access-check-demo-service` and grants consultation-style access. |
| Access-check response contract | Authorized access returns HTTP `200` with JSON body `{"result":"OK","authorized":true}`. Authenticated but unauthorized access returns HTTP `403` with JSON body `{"result":"KO","authorized":false}`. Missing or invalid authentication returns HTTP `401` with JSON body `{"result":"KO","authorized":false}`. If the authorization result cannot be safely determined, the service fails closed with HTTP `503` and JSON body `{"result":"KO","authorized":false}`. |
| Actor and operation matrix | Use the account, lifecycle, service-role, protected-service, audit, and onboarding rules already defined in this document. |
| Required account fields | The MVP requires the already-defined account fields: stable internal account identifier, `email`, `organization`, and `name`. No additional mandatory profile fields are specified for the MVP. |
| First `super-admin` bootstrap | The first `super-admin` is bootstrapped during MVP build or initialization, not through public registration, self-service, or routine business administration. The exact initialization mechanism is a Phase 6 implementation detail, but it must be controlled and auditable. |
| Audit consultation | The MVP uses the simplest useful super-admin-only audit consultation: chronological audit list, basic event detail, and read audit logging. Audit export and advanced search/filtering are not part of the initial MVP scope unless explicitly added later. |
| Audit storage | The MVP uses local durable file-backed audit storage, append-only, with one complete JSON event object per physical line. |
| Keycloak IAM schema | The MVP uses managed Keycloak User Profile attributes, disables unmanaged attributes, models account type and service access with client roles, and treats direct Keycloak business mutation as drift. |
| MVP exclusions | The exclusions in [Out of Scope](#out-of-scope) are confirmed for the MVP. |

These decisions come from user direction on 2026-06-26 and refine the MVP gate defined in the Phase 5 review note ([Phase 5 review note](./phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp)).

## MVP Boundary

The MVP includes the smallest complete access-control loop:

1. create invited backoffice accounts through authorized administration workflows;
2. activate accounts only through safe onboarding;
3. manage lifecycle states without hard deletion;
4. manage service-access roles and assign them only to members;
5. let the MVP protected access-check service ask for server-side authorization decisions;
6. record durable EDRLab business audit events for sensitive operations and authorization denials;
7. require privileged-authentication evidence for `admin` and `super-admin` onboarding.

This boundary follows ADR 0004: Keycloak is the IAM source, while EDRLab business administration and authorization checks go through the EDRLab Admin Console and IAM Control Plane API rather than unmanaged Keycloak Admin Console edits ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Account Operations

| Operation | MVP scope | Requirement trace |
| --- | --- | --- |
| Account creation | `admin` can create `member` accounts. `super-admin` can create `admin` and `member` accounts. Created accounts start as `invited`. | `FR-007`, `FR-008`, `FR-012`, `FR-017`, `FR-018`, `FR-040`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Account listing and reading | `admin` can list and read `member` accounts. `super-admin` can list and read `admin` and `member` accounts. `member` can read only their own profile. | `FR-017`, `FR-018`, `FR-019`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Profile update | `admin` can update `member` profile data. `super-admin` can update `admin` and `member` profile data. Members cannot update their own profile in the MVP. | `FR-017`, `FR-018`, `FR-019`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Minimum profile fields | Account creation captures at least `email`, `organization`, and `name`, plus a stable internal account identifier. | `FR-009`, `FR-040`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Authenticated-subject link display | The Admin Console may display whether a subject link exists, but the link is created only by onboarding and is immutable after creation. | `FR-010`, `FR-039`, `FR-043`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Account-type mutation | Not allowed. Account type is fixed at account creation and cannot be changed, merged, or elevated. | `FR-001`, `FR-026`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Hard deletion | Not allowed. Accounts are retained, including archived accounts. | `FR-014`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

Routine creation of new `super-admin` accounts is not in the MVP account-management scope. The first `super-admin` is a bootstrap concern and must be handled by a controlled bootstrap procedure rather than normal self-service or routine admin workflow (`FR-008`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Lifecycle

The MVP lifecycle state machine is:

```mermaid
flowchart LR
  Invited["invited"] -->|"safe onboarding activation"| Active["active"]
  Active -->|"disable"| Disabled["disabled"]
  Disabled -->|"restore"| Active
  Disabled -->|"archive"| Archived["archived"]
```

| Transition or rule | MVP scope | Requirement trace |
| --- | --- | --- |
| `created -> invited` | All normal account creation creates an `invited` account. | `FR-012`, `FR-040`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| `invited -> active` | Allowed only through safe onboarding. `admin` and `super-admin` onboarding also requires privileged-authentication evidence. | `FR-012`, `FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md) |
| `active -> disabled` | Authorized account managers can disable accounts in their management scope. Disabled accounts cannot receive protected-service access. | `FR-013`, `FR-015`, `FR-017`, `FR-018`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| `disabled -> active` | Authorized account managers can restore disabled accounts in their management scope. | `FR-013`, `FR-017`, `FR-018`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| `disabled -> archived` | Authorized account managers can archive disabled accounts in their management scope. | `FR-013`, `FR-017`, `FR-018`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| `archived -> active` | Not allowed in the initial policy. | `FR-013`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| return to `invited` | Not allowed once an account has left `invited`. | `FR-031`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

Protected-service access requires `active` state. `invited`, `disabled`, and `archived` accounts must be denied, and already-issued access must stop within the accepted access-stop behavior decided before Phase 6 (`FR-015`, `FR-016`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Service-Access Roles

| Capability | MVP scope | Requirement trace |
| --- | --- | --- |
| Role catalog management | `super-admin` can create, list, read, update, disable, and archive service-access roles. Hard deletion is not allowed. | `FR-004`, `FR-032`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Role purpose | A service-access role represents access to protected backend service coverage. It must not grant account-management responsibility. The initial MVP role is `access-check-demo:consult`. | User decision, 2026-06-26; `FR-002`, `FR-022`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Minimal member permission | MVP member access is consultation-style service access only. More granular or stronger permission models are out of scope until justified by a real protected-service need. | `FR-023`, `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Assignment | `admin` and `super-admin` can assign or remove active service-access roles for `member` accounts only. | `FR-003`, `FR-004`, `FR-005`, `FR-017`, `FR-018`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Invited member assignment | A role may be assigned to an `invited` member, but it grants no protected-service access until the member becomes `active`. | `FR-041`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Privileged account assignment | Service-access roles are not assigned to `admin` or `super-admin` accounts. Active `admin` accounts receive covered service access automatically, and active `super-admin` accounts receive it through inherited admin capability. | `FR-002`, `FR-003`, `FR-004`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Inactive role behavior | Disabled or archived service-access roles cannot be assigned and cannot authorize protected-service access. | `FR-032`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

The MVP should use a service-level role model, not a fine-grained permission matrix. Keycloak representation is fixed by the accepted schema policy: account type uses exactly one client role on `edrlab-backoffice`, and the first service-access role uses client `access-check-demo-service` with role `consult`, exposed by the IAM Control Plane API as `access-check-demo:consult` ([Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md)). That keeps the first implementation aligned with the simplicity constraint while still allowing later refinement when a concrete protected-service need appears (`FR-023`, `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Protected Services

| Capability | MVP scope | Requirement trace |
| --- | --- | --- |
| Effective service listing | The IAM Control Plane API exposes the current user's effective protected-service access for UI use, following the `GET /me/services` shape validated in `WP-014`. | [Keycloak WP-014 result](../poc/keycloak-wp014-result.md), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md) |
| Authorization check | Protected backend services authorize server-side by calling the IAM Control Plane API `authorization/check` contract unless a later decision explicitly changes the contract. | `FR-020`, `FR-021`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| Allow rules | Active `admin` and `super-admin` accounts are allowed for active service-role-covered protected services. Active `member` accounts are allowed only when an active assigned service-access role covers the requested service. | `FR-003`, `FR-004`, `FR-005`, `FR-020`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Deny rules | Deny when the account is not `active`, no applicable active service-access role exists, the protected service is unknown or inactive, direct-admin drift makes the state unsafe, or the result cannot be safely determined. | `FR-015`, `FR-020`, `FR-021`, `FR-032`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-015 result](../poc/keycloak-wp015-result.md) |
| First protected-service integration | The MVP scope includes `access-check-demo-service` as a synthetic protected access-check service and release blocker. Its only purpose is to verify whether the current authenticated user is authorized for `access-check-demo:consult` and return `OK` or `KO` with an HTTP status. Additional protected services can be represented in the catalog only when they are explicitly named and tested for `authorization/check`. | User decision, 2026-06-26; `FR-020`, `FR-021`, `FR-022`, `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Phase 5 review note](./phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp) |

The first MVP protected service is therefore not a business backend. It is a synthetic protected access-check service. It must still behave like a protected backend service for the authorization path: it must not authorize from frontend state or raw token claims, and it must return `KO` when authorization cannot be safely determined (`FR-020`, `FR-021`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The response contract is intentionally small and uses JSON for both `OK` and `KO` outcomes:

| Case | HTTP status | JSON body |
| --- | --- | --- |
| Authorized for `access-check-demo-service` | `200` | `{"result":"OK","authorized":true}` |
| Authenticated but not authorized | `403` | `{"result":"KO","authorized":false}` |
| Missing or invalid authentication | `401` | `{"result":"KO","authorized":false}` |
| Authorization cannot be safely determined | `503` | `{"result":"KO","authorized":false}` |

The route family, JSON media type, service-to-control-plane authentication model, timeout, retry, cache, and access-stop behavior are accepted in the IAM Control Plane API contract and `authorization/check` behavior notes. Phase 6 must implement them so the protected-service path fails closed when authorization cannot be determined safely (`FR-016`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md), [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).

## Audit

The MVP requires local EDRLab business audit records. Keycloak events are useful supplemental provider evidence, but they do not replace local business audit for EDRLab decisions, denials, audit reads/exports, drift, and rationale ([Keycloak WP-016 result](../poc/keycloak-wp016-result.md), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), `FR-027`, `FR-028`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

| Audit area | MVP scope | Requirement trace |
| --- | --- | --- |
| Account events | Audit account creation, profile update, activation, disablement, restoration, archival, and attempted disallowed lifecycle changes. | `FR-027`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Subject-link and onboarding events | Audit authenticated-subject link creation, rejected or attempted link mutation, failed onboarding activation, and privileged-onboarding denial. | `FR-027`, `FR-039`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Service-role events | Audit service-access-role creation, update, disablement, archival, assignment, removal, and protected-service access configuration changes. | `FR-027`, `FR-032`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Authorization events | Audit protected-service authorization denials. Allowed checks may be logged for diagnostics, but denial audit is required by the MVP scope. | `FR-027`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Audit consultation | `super-admin` can consult a chronological audit list and basic event detail. Audit reads create audit events. `admin` and `member` cannot consult audit records. Audit export is out of scope for the initial MVP unless explicitly added later. | User decision, 2026-06-26; `FR-028`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Retention and mutation | Audit records are append-only and retained indefinitely in the initial policy. Any later retention, privacy, or deletion policy change requires explicit review. | `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Audit storage policy](../architecture/audit-storage.md) |
| Recovery and login reset | Any EDRLab-side recovery or login-reset event exposed by the MVP must be audited. Identity-provider-owned recovery remains outside the access-control capability unless the IAM Control Plane API participates in the workflow. | `FR-025`, `FR-027`, `FR-042`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

The durable audit storage technology is selected for the MVP as local file-backed append-only storage with one JSON event object per line. Export, advanced search, tamper-evidence, exact file path, rotation, permissions, backup mechanism, and encryption-at-rest mechanism remain outside the functional MVP scope or Phase 6 implementation details as described in the accepted audit storage policy ([Audit storage policy](../architecture/audit-storage.md), [Phase 5 review note](./phase-5-review-note.md#minimum-conditions-to-authorize-an-mvp)).

## Privileged Onboarding

| Flow | MVP scope | Requirement trace |
| --- | --- | --- |
| Member onboarding | The IAM Control Plane API may activate an invited `member` only when exactly one invited account has no existing subject link and its account email matches a verified email from the authenticated identity. | `FR-036`, `FR-037`, `FR-039`, `FR-043`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Admin onboarding | The same safe match is required, plus privileged-authentication evidence. OTP step-up with ACR/LoA is accepted for the current direction. | `FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [Keycloak WP-013 result](../poc/keycloak-wp013-result.md) |
| Super-admin bootstrap and onboarding | First `super-admin` setup is a controlled bootstrap concern. Any project-approved `super-admin` onboarding must require privileged-authentication evidence and must not become public or self-service registration. | `FR-006`, `FR-007`, `FR-008`, `FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Unsafe onboarding | Missing match, duplicate match, unverified email, existing subject link, missing privileged evidence, stale privileged evidence, or subject mismatch must deny activation and authorization. | `FR-036`, `FR-037`, `FR-039`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-013 result](../poc/keycloak-wp013-result.md) |
| Subject-link changes | Not allowed after creation. If a link is wrong or unusable, the account is disabled or archived and a new account is created where lifecycle policy allows. | `FR-039`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

OTP enrollment, reset, recovery, monitoring, rate limiting, and audit safeguards are Phase 6 implementation and operations tasks using the accepted Keycloak built-in mechanisms. WebAuthn/passkeys remain future hardening, not an MVP blocker in the accepted current direction ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [Phase 5 review note](./phase-5-review-note.md#production-risks-remaining)).

## Out of Scope

| Out of scope for MVP | Reason |
| --- | --- |
| Public signup, public customer identity, social login, and consumer identity flows. | The capability is limited to backoffice users (`FR-006`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Company-wide workforce IAM replacement. | The repository scope excludes a complete company-wide IAM replacement ([README - Initial Scope](../../README.md#initial-scope)). |
| Member self-service beyond read-only own-profile consultation. | Members cannot update their own profile, assign roles, manage accounts, or consult audit records (`FR-019`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Routine business administration directly in Keycloak Admin Console. | ADR 0004 keeps business administration behind the EDRLab Admin Console and IAM Control Plane API; direct Keycloak admin remains technical or break-glass governance work ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)). |
| Account-type changes, member-to-admin conversion, account merge, or subject-link rebinding. | These violate fixed account type and immutable subject-link requirements (`FR-001`, `FR-026`, `FR-039`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Hard deletion of accounts, service-access roles, or audit records. | Initial policy retains accounts, forbids service-role hard deletion, and keeps audit append-only (`FR-014`, `FR-032`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Fine-grained per-action permission matrix beyond consultation-style member service access. | The initial policy keeps member access minimal until real service needs justify more detail (`FR-023`, `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Real business protected backend service integration. | The initial MVP protected service is `access-check-demo-service`, a synthetic access-check service only. |
| Audit export and advanced audit search/filtering. | The MVP keeps audit consultation to the simplest useful super-admin-only list and detail view; reads are audited. |
| WebAuthn/passkeys as a mandatory MVP prerequisite. | ADR 0003 accepts OTP MFA for the current direction and defers WebAuthn/passkeys as future hardening ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| Production high availability, multi-replica Keycloak operation, or broad production infrastructure design beyond the single MVP runtime. | Minimum runtime and operations evidence belongs to Phase 6, but high-availability and broader infrastructure design are outside this functional MVP scope unless explicitly added ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)). |

## Phase 6 Input Status

| Input | Status | Notes |
| --- | --- | --- |
| First protected-service identity and role | Closed for scope | User decision on 2026-06-26: use `access-check-demo-service` with service role `access-check-demo:consult`. The service returns JSON `OK` or `KO` outcomes with the HTTP statuses defined above. Exact route and transport details belong to the IAM Control Plane API contract gate. |
| MVP scope acceptance | Closed | Accepted by user decision on 2026-06-26 and authorized for Phase 6 by ADR 0005. |
| IAM Control Plane API contract | Closed | Accepted in the IAM Control Plane API contract ([IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md)). |
| Protected-service timeout, retry, cache, and access-stop delay | Closed | Accepted in the authorization-check behavior note ([Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)). |
| Durable audit storage | Closed for MVP storage choice | User decision on 2026-06-26: use local file-backed append-only storage with one JSON event object per line. Phase 6 still needs exact file path, rotation, permissions, backup mechanism, restore test, and encryption-at-rest choices ([Audit storage policy](../architecture/audit-storage.md)). |
| Keycloak IAM schema policy | Closed for MVP schema choice | User decision on 2026-06-26: use managed attributes, disable unmanaged attributes, use account-type and service-access client roles, enforce IAM Control Plane API-only mutation, and require strict migration ([Keycloak IAM schema policy](../architecture/keycloak-iam-schema-policy.md)). |
| Direct Keycloak admin governance | Accepted post-MVP deferral | User decision on 2026-06-26: define detailed governance post-MVP. MVP still forbids routine direct Keycloak business administration and treats unmanaged mutation as drift (`FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| First-super-admin bootstrap procedure | Closed for MVP direction | User decision on 2026-06-26: keep bootstrap simple for the MVP. Phase 6 must implement an idempotent, audited initialization process outside the public API. |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [README - Core Features](../../README.md#core-features)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [ADR 0005 - Authorize Phase 6 Production MVP](../decisions/0005-authorize-phase-6-production-mvp.md)
- [Phase 5 Review Note](./phase-5-review-note.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](../poc/keycloak-wp013-result.md)
- [Keycloak WP-014 Result - Service Access Authorization](../poc/keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](../poc/keycloak-wp015-result.md)
- [Keycloak WP-016 Result - Audit and Operations Review](../poc/keycloak-wp016-result.md)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
