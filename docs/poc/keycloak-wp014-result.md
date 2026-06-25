# Keycloak WP-014 Result - Service Access Authorization

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Service-Access Role Contract](#service-access-role-contract)
- [Effective Service Listing Contract](#effective-service-listing-contract)
- [Effective Service Listing Scenarios](#effective-service-listing-scenarios)
- [Authorization Check Contract](#authorization-check-contract)
- [Decision Logic](#decision-logic)
- [Scenario Matrix](#scenario-matrix)
- [Access-Stop Evidence](#access-stop-evidence)
- [Rejected Shortcuts](#rejected-shortcuts)
- [Runtime Evidence To Produce](#runtime-evidence-to-produce)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-014` defines the first validation contract for service-access roles and protected-service authorization in the Keycloak IAM plus EDRLab IAM Control Plane API direction. It builds on the selected `WP-010` mapping: service-access roles are Keycloak client roles, protected services do not authorize from raw token claims, and final access decisions go through an EDRLab IAM Control Plane API endpoint such as `authorization/check` ([Keycloak WP-010 result](./keycloak-wp010-result.md), [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md)).

This result is documentation-first PoC evidence. It does not add runtime scripts, production code, production dependencies, database schema, CI, deployment files, or a production database topology decision ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Result

Use an IAM Control Plane API-mediated `authorization/check` contract as the first protected-service authorization slice, and expose a separate `GET /me/services` read contract for UI navigation.

The selected validation behavior is:

- authenticated backoffice UI clients call `GET /me/services` to list currently visible protected services and actions for the current account;
- protected backend services call the EDRLab IAM Control Plane API before serving a protected action;
- the IAM Control Plane API reads current Keycloak account state and role mappings, not only already-issued token claims;
- the IAM Control Plane API returns `allow` only when account lifecycle, account type, service coverage, service-access role state, and assignment rules all pass;
- the IAM Control Plane API returns `deny` when Keycloak is unreachable, state is missing, state is inconsistent, the caller is not trusted, or any invariant is violated;
- the PoC uses no positive authorization cache, so account or role changes must affect the next authorization check and the next effective-service listing.

This fits `FR-015`, `FR-016`, `FR-020`, `FR-021`, `FR-022`, `FR-032`, `FR-038`, and `FR-041`: protected-service access requires active account state, active service-role coverage, server-side authorization, fail-closed behavior, controlled IAM-backed authorization paths, and no access for invited accounts even when roles were preassigned ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Service-Access Role Contract

For the first runtime slice, model the protected-service catalog with Keycloak client roles on client `edrlab-protected-services`. Keycloak documents role mappings and Admin REST role representations; the Admin REST `RoleRepresentation` includes role attributes, which the PoC can use to represent EDRLab service-role status for validation ([Keycloak roles and groups](https://www.keycloak.org/docs/latest/server_admin/#assigning-permissions-using-roles-and-groups), [Keycloak Admin REST API - RoleRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_rolerepresentation)).

| Field | First validation value | Rule |
| --- | --- | --- |
| Client | `edrlab-protected-services` | Dedicated to protected-service access roles, separate from account-type roles on `edrlab-backoffice`. |
| Role name | `service-catalog-consult` | First minimal protected-service role for a consultation-style backend service. |
| Role status | Role attribute `edrlab.role_status=active`; later test values can be `disabled` or `archived`. | Only `active` roles can be assigned or used for protected-service access decisions (`FR-032`). |
| Coverage | Role attribute or IAM Control Plane API catalog mapping `edrlab.covered_service=catalog` and `edrlab.allowed_action=consult`. | The runtime must record which protected service and action the role covers (`FR-022`, `FR-023`). |
| Assignment target | `member` accounts only. | The IAM Control Plane API must reject service-role assignment to `admin` and `super-admin`; admins and super-admins receive covered-service access through account type when active (`FR-003`, `FR-004`, `FR-005`). |
| Pre-activation assignment | Allowed for invited accounts as assignment state only. | Invited accounts must still be denied protected-service access until safe onboarding activation succeeds (`FR-041`, `FR-043`, `FR-044`). |

If role attributes prove awkward in runtime, the result should mark that part as blocked or replace it with an explicit PoC catalog fixture. It should not silently treat all Keycloak roles as active, because that would fail to validate service-role disablement and archival under `FR-032`.

## Effective Service Listing Contract

`GET /me/services` is a read endpoint for the current authenticated backoffice account. It helps the EDRLab Admin Console or another backoffice UI render navigation, service launchers, and available actions. It is not the final enforcement decision for protected backend services.

Example request:

```http
GET /me/services
```

Example response for an active `member`:

```json
{
  "account_id": "acct-member-001",
  "account_type": "member",
  "lifecycle": "active",
  "checked_at": "2026-06-25T00:00:00Z",
  "services": [
    {
      "service": "catalog",
      "actions": ["consult"],
      "source_roles": ["service-catalog-consult"]
    }
  ]
}
```

The IAM Control Plane API must compute this list from current Keycloak-backed account state and the active service-role catalog. For `member` accounts, the list contains services covered by assigned active service-access roles. For active `admin` and `super-admin` accounts, the list contains services covered by active service-access roles, without assigning service-access roles directly to those account types (`FR-003`, `FR-004`, `FR-005`, `FR-022`, `FR-032`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The endpoint must not return positive service entries when account resolution fails, lifecycle is not `active`, Keycloak current state cannot be read, the service-role catalog is inconsistent, or direct Keycloak Admin Console drift violates the selected invariants. In those cases, the UI must behave as if no protected service is available, and any backend action still requires `authorization/check` before execution (`FR-015`, `FR-020`, `FR-021`, `FR-038`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

The listing can be cached by the browser only as display state, not as authority. A stale visible link is acceptable only if the protected service still calls `authorization/check` and denies when current state no longer allows access.

## Effective Service Listing Scenarios

| Scenario | Expected `GET /me/services` result | Enforcement reminder |
| --- | --- | --- |
| Active member assigned `service-catalog-consult`, role active | Returns `catalog` with `consult` action and `service-catalog-consult` as source role. | Protected service still calls `authorization/check` before executing `catalog:consult`. |
| Active member without service role | Returns an empty service list or a business denial with no positive service entries. | No backend action may be inferred from old UI state. |
| Active admin with no direct service role | Returns every service/action covered by active service-access roles. | Admin access is computed from account type and active service coverage, not direct role assignment. |
| Active super-admin with no direct service role | Returns every service/action covered by active service-access roles. | Super-admin inherits admin covered-service access through account type. |
| Invited member with preassigned service role | Returns no positive service entries because lifecycle is not `active`. | Pre-activation assignment does not grant access (`FR-041`). |
| Disabled or archived account with assigned service role | Returns no positive service entries because lifecycle is not `active`. | Next protected-service check must also deny. |
| Assigned service role becomes `disabled` or `archived` | Removes the covered service/action from the next listing. | Next protected-service check must deny for the inactive role. |
| Keycloak state unavailable or inconsistent | Returns no positive service entries and records fail-closed evidence. | UI availability must not become authorization bypass. |

## Authorization Check Contract

The first contract is intentionally small and reviewable. It is a PoC contract, not a production API shape.

Example request:

```json
{
  "correlation_id": "poc-wp014-001",
  "subject": "current-authenticated-subject",
  "target_service": "catalog",
  "action": "consult",
  "resource_context": {
    "resource_id": "optional-poc-resource"
  }
}
```

Example response:

```json
{
  "decision": "allow",
  "reason_code": "active_member_with_active_service_role",
  "account_id": "acct-member-001",
  "account_type": "member",
  "lifecycle": "active",
  "matched_service_role": "service-catalog-consult",
  "checked_at": "2026-06-25T00:00:00Z",
  "audit_event_id": "audit-poc-wp014-001"
}
```

The protected service must treat any missing response, invalid response, timeout, failed caller authentication at the IAM Control Plane API, unknown reason, or `deny` response as no access. OWASP authorization guidance recommends validating permissions on the server side and denying by default when authorization cannot be established ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Decision Logic

The IAM Control Plane API should evaluate the first validation decision in this order:

1. Authenticate the protected service caller to the IAM Control Plane API and deny if the caller is unknown or not allowed to ask about the target service.
2. Resolve the authenticated subject to exactly one Keycloak-backed EDRLab account; deny if resolution is missing, duplicated, or inconsistent (`FR-036`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
3. Read current Keycloak user attributes, account-type client role mappings, and service-access client role mappings through the controlled IAM Control Plane API technical path; deny if Keycloak state cannot be read.
4. Require exactly one account-type role: `account-type-member`, `account-type-admin`, or `account-type-super-admin`; deny and audit drift if zero or multiple account-type roles are present.
5. Require `edrlab.lifecycle=active`; deny invited, disabled, archived, missing, or unknown lifecycle values.
6. For `member`, require an assigned active service-access role that covers the target service and action.
7. For `admin` and `super-admin`, allow covered protected services when the account is active and the target service/action is covered by an active service-access role, without assigning service-access roles to those account types.
8. Deny if a service-access role is disabled, archived, missing coverage metadata, or assigned to an account type that must not receive direct service-access-role assignments.
9. Record local business audit evidence for allow, deny, blocker, and drift outcomes, with Keycloak event references as supplemental evidence where useful.

Keycloak Admin REST can expose user, role, and mapping state, but Keycloak provider state alone does not express the EDRLab business rationale; `WP-010` therefore keeps local business audit as required PoC evidence ([Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events), [Keycloak WP-010 result](./keycloak-wp010-result.md#selected-mapping)).

## Scenario Matrix

| Scenario | Expected IAM Control Plane API result | Key evidence |
| --- | --- | --- |
| Active member assigned `service-catalog-consult`, role active, target `catalog:consult` | `allow` | Current lifecycle, member account type, assigned active role, coverage match, local audit. |
| Active member without service role | `deny` with `service_role_missing` | Current lifecycle, no matching role mapping, denial audit. |
| Invited member with preassigned service role | `deny` with `account_not_active` | `edrlab.lifecycle=invited`, role mapping present, no protected-service access, denial audit (`FR-041`). |
| Disabled member with assigned service role | `deny` with `account_not_active` | `edrlab.lifecycle=disabled`, `enabled=false` if configured by `WP-010`, denial audit. |
| Archived member with assigned service role | `deny` with `account_not_active` | `edrlab.lifecycle=archived`, terminal/non-active state evidence, denial audit. |
| Active admin with no service role, target covered by active service role | `allow` | Account type `admin`, active lifecycle, active coverage role exists, no direct service-role assignment. |
| Active super-admin with no service role, target covered by active service role | `allow` | Account type `super-admin`, active lifecycle, active coverage role exists, no direct service-role assignment. |
| Active admin or super-admin directly assigned `service-catalog-consult` | `deny` or `blocked_drift` | Drift evidence: service-access roles must not be directly assigned to privileged account types. |
| Active member assigned role after role status becomes `disabled` | `deny` with `service_role_inactive` | Role attribute/status evidence, access-stop audit (`FR-032`). |
| Active admin accesses service after the only covering role is disabled | `deny` with `service_not_covered_by_active_role` | Coverage role inactive; admin inheritance covers only active service-role-covered services. |
| Member role removed in Keycloak after prior allow | Next check returns `deny` | Before/after role mapping evidence, no positive cache, access-stop audit (`FR-016`). |
| Account lifecycle changed from `active` to `disabled` after prior allow | Next check returns `deny` | Before/after lifecycle evidence, no positive cache, access-stop audit (`FR-016`). |
| Raw token still contains old service role after role removal | `deny` | Token-claim evidence marked non-authoritative, current Keycloak read shows no matching assignment. |
| Keycloak unavailable or Admin REST read fails | `deny` with `state_unavailable` | Failure evidence and fail-closed audit (`FR-021`). |
| Protected service skips the IAM Control Plane API and authorizes from frontend/token hint | Scenario invalid and rejected | Shortcut evidence for `WP-015`; protected service must not be considered compliant. |

## Access-Stop Evidence

Runtime `WP-014` evidence should prove next-check denial after each relevant change:

- assigned service-access role removed from an active member;
- service-access role status changed from `active` to `disabled` or `archived`;
- account lifecycle changed from `active` to `disabled` or `archived`;
- account type/service-role invariant broken by direct Keycloak Admin Console mutation;
- Keycloak read path unavailable during authorization.

The PoC should use no positive authorization cache. If a future production design proposes caching, that design must define maximum stale-access duration, invalidation behavior, and residual risk before Phase 5 review; `WP-014` does not approve that shortcut (`FR-016`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Rejected Shortcuts

| Shortcut | Status | Reason |
| --- | --- | --- |
| Protected services authorize directly from token role claims | Rejected. | Token role claims may be stale and would bypass the controlled server-side authorization path selected in `WP-010`. |
| Frontend-only authorization checks | Rejected. | Protected backend services must authorize server-side and fail closed (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| Positive authorization cache in the PoC | Rejected. | The first slice must prove immediate next-check denial after lifecycle or role changes (`FR-016`). |
| Assigning service-access roles to admins or super-admins | Rejected. | Admin and super-admin covered-service access comes from active account type, while service-access-role assignments remain member-only (`FR-003`, `FR-004`, `FR-005`). |
| Keycloak Authorization Services as the first runtime authorization engine | Deferred. | Keycloak Authorization Services may be validated later, but the first slice should prove the simpler IAM Control Plane API contract before adding resource/scope/policy complexity ([Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)). |
| Treating Keycloak realm-admin permissions as protected-service access | Rejected. | Realm administration is a technical operator surface, not the EDRLab business service-access role model ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). |

## Runtime Evidence To Produce

The runtime result should produce:

- Keycloak client role definitions for `edrlab-protected-services`, including `service-catalog-consult` and role status/coverage evidence;
- account fixtures for invited, active, disabled, and archived members, plus active admin and active super-admin accounts;
- IAM Control Plane API `GET /me/services` examples for active member, active admin, active super-admin, non-active account, inactive service role, missing role, and unavailable Keycloak state;
- IAM Control Plane API `authorization/check` examples for each scenario in the matrix;
- evidence that the IAM Control Plane API reads current Keycloak state instead of relying on stale token claims;
- before/after evidence for role removal, role disablement, account disablement, and account archival;
- fail-closed evidence for Keycloak read failure and invalid/inconsistent Keycloak state;
- local EDRLab audit examples for allow, deny, access-stop, fail-closed, and drift outcomes;
- supplemental Keycloak admin/user event references where the runtime can collect them.

The runtime package must be Linux-targeted, Docker-based, fully scripted, and documented before execution, as required for Phase 4 runtime PoCs ([AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Residual Risks

- IAM Control Plane API-mediated authorization puts the IAM Control Plane API on the protected-service request path. The PoC still needs runtime latency, availability, timeout, and retry behavior before Phase 5 review.
- `GET /me/services` introduces a user-facing entitlement list. The PoC must prove that stale UI state cannot authorize a backend action and that protected services still rely on `authorization/check`.
- Role status stored as Keycloak role attributes must be proven through runtime Admin REST reads. If role attributes are not reliable enough for the target Keycloak version or tooling, the result must record a blocker or move service-role status into an explicit reviewed catalog.
- Direct Keycloak Admin Console edits can still mutate roles and attributes for sufficiently privileged operators. `WP-015` must validate prevention, detection, or quarantine of that drift.
- Local business audit remains necessary for EDRLab decision rationale, even if Keycloak events are collected as supplemental evidence.
- Service-to-control-plane caller authentication is part of the authorization boundary but is not designed in detail here. Runtime evidence must at least prove the IAM Control Plane API denies unknown protected-service callers.
- This document validates one consultation-style protected service. It does not decide future fine-grained permission semantics beyond the first `catalog:consult` slice.

## Decision Impact

`WP-014` is complete at documentation level. It selects the IAM Control Plane API-mediated `authorization/check` contract, adds `GET /me/services` for effective-service listing, and defines the exact role, lifecycle, service coverage, fail-closed, stale-access, and drift cases that runtime evidence must prove.

The next useful documentation-first work is `WP-015`: direct-admin-console drift and shortcut rejection. The next runtime work can bundle `WP-011` through `WP-014`, because service authorization depends on the controlled IAM Control Plane API mutation path, lifecycle/onboarding state, and current Keycloak role mappings.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak WP-012 Result - Lifecycle and Onboarding](./keycloak-wp012-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](./keycloak-wp013-result.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Admin REST API - RoleRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_rolerepresentation)
- [Keycloak Roles and Groups](https://www.keycloak.org/docs/latest/server_admin/#assigning-permissions-using-roles-and-groups)
- [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
