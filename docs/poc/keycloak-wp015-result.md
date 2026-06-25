# Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Direct Keycloak Admin Boundary](#direct-keycloak-admin-boundary)
- [Drift Classes](#drift-classes)
- [Drift Detection Contract](#drift-detection-contract)
- [Shortcut Rejection Matrix](#shortcut-rejection-matrix)
- [Scenario Matrix](#scenario-matrix)
- [Runtime Evidence To Produce](#runtime-evidence-to-produce)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-015` defines how the Keycloak IAM plus EDRLab IAM Control Plane API validation must handle unmanaged Keycloak Admin Console edits, misleading token claims, frontend-only checks, and protected-service shortcuts. It closes the documentation-first anti-bypass gap left by `WP-010` through `WP-014`: Keycloak may hold IAM state, but business state must not be silently changed or consumed outside the controlled EDRLab path ([Keycloak WP-010 result](./keycloak-wp010-result.md), [Keycloak WP-011 result](./keycloak-wp011-result.md), [Keycloak WP-014 result](./keycloak-wp014-result.md), `FR-026`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

This is documentation-first PoC evidence. It does not add runtime scripts, production code, production dependencies, database schema, CI, deployment files, or production operations policy. Runtime validation still needs a Linux-targeted, Docker-based, fully scripted PoC before execution ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Result

Treat the EDRLab IAM Control Plane API as the only approved business path for account lifecycle, account type, subject link, service-access role assignment, effective-service listing, and protected-service authorization decisions.

For the first validation slice:

- direct Keycloak Admin Console access is allowed only as a technical operator surface for PoC inspection, setup, and explicit drift scenarios;
- any direct mutation of EDRLab business IAM state is drift unless it is explicitly tied to the approved control-plane technical actor and local EDRLab audit evidence;
- invalid current state must fail closed immediately in `GET /me/services` and `authorization/check`;
- valid-looking but unmanaged current state must be treated as review-required drift for sensitive operations until the PoC proves a stronger detection or reconciliation method;
- raw token claims, frontend hidden buttons, or protected-service local guesses cannot authorize access.

This preserves the `FR-038` interpretation selected in ADR 0002: Keycloak IAM values may be authoritative only through the controlled server-side administration and authorization path, not through unmanaged console edits or raw claim consumption ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Keycloak IAM Control Plane API scope](../architecture/keycloak-iam-bff-scope.md), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Direct Keycloak Admin Boundary

Direct Keycloak Admin Console access is not the EDRLab business administration interface. Keycloak documents realm administrators and delegated administration, and direct administrative grants must be reviewed carefully because privileged administrators can affect realm resources outside the EDRLab business workflow ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)).

| Direct Keycloak use | WP-015 status | Rule |
| --- | --- | --- |
| PoC setup by a technical operator | Allowed with evidence. | Setup actions must be documented as fixture/setup, not business account administration. |
| Inspection of users, roles, events, and realm settings | Allowed with evidence. | Inspection must not mutate EDRLab business state. |
| Direct mutation used to create a drift scenario | Allowed only as an explicit test action. | The expected result is detection, quarantine, denial, or a documented residual risk. |
| Business admin lifecycle/account-type/service-role change through Keycloak Admin Console | Rejected. | Business admins must use the EDRLab Admin Console and IAM Control Plane API path. |
| Protected-service authorization from Keycloak Admin Console view or raw token claims | Rejected. | Protected services must rely on server-side authorization checks, not console-visible state or frontend/token hints. |

## Drift Classes

| Drift class | Definition | Expected control-plane behavior |
| --- | --- | --- |
| `invariant_violation` | Current Keycloak state violates the selected mapping, such as zero or multiple account-type roles, invalid lifecycle value, changed immutable subject link, service-access role assigned to `admin` or `super-admin`, or inactive role used for access. | Deny `GET /me/services`, deny `authorization/check`, block sensitive admin operations, and record local drift evidence. |
| `unmanaged_change_detected` | Current Keycloak state changed outside the IAM Control Plane API path, even if it still looks internally valid. | Treat as review-required drift for sensitive operations; deny or quarantine until reconciliation evidence exists. |
| `untrusted_claim_shortcut` | A token claim, group, role, or frontend hint suggests access that current control-plane checks do not confirm. | Ignore for final authorization and deny if current state does not pass. |
| `protected_service_shortcut` | A protected service grants access without calling the approved authorization contract. | Mark the integration invalid for this validation slice. |
| `event_gap` | Keycloak current state changed, but admin events are missing, disabled, cleared, truncated, or insufficient to prove who changed it. | Do not infer safety; record a blocker or residual risk. |

Keycloak admin events can be useful evidence for administrator actions, and Keycloak can include JSON representations sent through Admin REST when configured, but event evidence is supplemental and may introduce storage/retention limits ([Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). Therefore, `WP-015` also requires current-state invariant checks and local EDRLab audit/correlation evidence.

## Drift Detection Contract

The first runtime slice should validate this detection order:

1. Read current Keycloak user attributes, account-type roles, service-access roles, role status, and coverage metadata before every sensitive admin operation, `GET /me/services`, and `authorization/check`.
2. Run invariant checks from `WP-010` and `WP-014`; fail closed on any invariant violation.
3. Compare the current state with local EDRLab business audit/correlation evidence for the expected latest managed mutation.
4. Use Keycloak admin events as supplemental evidence to identify direct console/API mutations, including actor, operation, resource path, and representation where configured.
5. If state is valid but cannot be tied to an approved IAM Control Plane API mutation, treat it as `unmanaged_change_detected` for the PoC.
6. Deny or quarantine sensitive operations until a reviewer explicitly resolves the drift in the PoC evidence.

The PoC may use a simple local reconciliation ledger or evidence fixture for step 3. That ledger is a Phase 4 evidence mechanism, not a production database topology decision. If runtime validation cannot detect valid-looking unmanaged changes, the result must record a residual risk rather than silently accepting direct Keycloak Admin Console edits.

## Shortcut Rejection Matrix

| Shortcut | Expected result | Why |
| --- | --- | --- |
| Frontend hides or shows service links based on token roles only. | UI hint allowed only as display state; no backend authorization. | Client-side checks can improve UX but must not decide access ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#verify-that-authorization-checks-are-performed-in-the-right-location)). |
| Protected service trusts `realm_access`, `resource_access`, group, or custom claim directly. | Reject as unsupported integration for this validation slice. | Current lifecycle, role status, drift, and access-stop behavior are enforced through the IAM Control Plane API. |
| Protected service calls `GET /me/services` and treats the listing as final authorization. | Reject. | `GET /me/services` is for UI navigation; `authorization/check` remains the enforcement decision ([Keycloak WP-014 result](./keycloak-wp014-result.md#effective-service-listing-contract)). |
| Direct Keycloak Admin Console assigns a member service role. | Treat as drift unless it is an explicit test setup action. | Service-role assignment is a business operation that must be authorized and audited through the control plane. |
| Direct Keycloak Admin Console changes lifecycle from `disabled` to `active`. | Treat as drift; deny or quarantine until reviewed. | Restore is a business lifecycle operation with actor scope and audit requirements (`FR-013`, `FR-027`, `FR-033`, `FR-038`). |
| Direct Keycloak Admin Console changes a `member` into an `admin`. | Deny as invariant violation or unmanaged privilege escalation. | Account type is fixed and must not be mutated (`FR-001`, `FR-026`). |
| Token still has a service role after the role was removed or disabled. | Deny on next current-state check. | Access-stop behavior must not rely on stale claims (`FR-016`, `FR-021`). |

## Scenario Matrix

| Scenario | Expected `GET /me/services` | Expected `authorization/check` | Evidence |
| --- | --- | --- | --- |
| Direct console adds `service-catalog-consult` to active member. | Deny or quarantine as unmanaged drift unless the PoC marks it setup-only. | Deny or quarantine until managed reconciliation exists. | Before/after role mapping, Keycloak admin event if available, local drift record. |
| Direct console assigns service role to active admin. | No positive service entries from that direct role; drift/invariant violation. | Deny or block because direct service-role assignment to admin violates the mapping. | Role mapping evidence and local drift audit. |
| Direct console changes `account-type-member` to `account-type-admin`. | No positive service entries; drift or account-type invariant violation. | Deny or block sensitive operations. | Before/after account-type role evidence. |
| Direct console changes lifecycle `disabled -> active`. | Deny or quarantine as unmanaged lifecycle restore. | Deny or quarantine until reviewed. | Attribute before/after, admin event, local drift record. |
| Direct console changes `edrlab.linked_subject`. | Deny as immutable subject-link violation. | Deny. | Attribute before/after and subject-link drift audit. |
| Token contains old service role after controlled role removal. | Current listing omits removed access. | Deny. | Old token sample, current Keycloak role mapping, local access-stop audit. |
| Frontend shows stale service link from cached `GET /me/services`. | UI may show stale display state. | Deny if current state no longer allows access. | Cached listing, current check response, protected-service denial. |
| Protected service bypasses `authorization/check`. | Not applicable. | Integration invalid for WP-015. | Request trace showing no authorization call and explicit rejection note. |
| Keycloak admin events disabled or cleared before drift check. | No positive service entries if state cannot be trusted. | Deny or record blocker depending on current-state invariants and local evidence. | Event settings/evidence gap and residual-risk record. |

## Runtime Evidence To Produce

`WP-015` runtime validation should produce:

- a documented technical-operator allow/deny boundary for direct Keycloak Admin Console access;
- Keycloak admin-event configuration evidence, including whether admin events and representation capture are enabled;
- at least one direct console or direct Admin REST drift mutation for account type, lifecycle, subject link, and service-access role assignment;
- before/after Keycloak state evidence for each drift mutation;
- IAM Control Plane API responses showing fail-closed behavior for `GET /me/services` and `authorization/check`;
- protected-service shortcut evidence showing that raw token claims and stale UI listing do not authorize backend execution;
- local EDRLab drift/audit examples for `invariant_violation`, `unmanaged_change_detected`, `untrusted_claim_shortcut`, and `event_gap`;
- explicit residual-risk notes for any valid-looking unmanaged change that cannot be detected with the selected PoC mechanism.

The runtime result should use the evidence-record shape from the [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md#evidence-record).

## Residual Risks

- Keycloak administrators with sufficient privileges can mutate or erase evidence. The PoC can classify and detect drift, but production operator controls, separation of duties, backup, and tamper-resistant audit remain later review topics.
- Keycloak admin events are useful but not sufficient as the only business audit mechanism. Event settings can be disabled, events can be cleared, representation capture can be limited, and retention/storage limits matter.
- Valid-looking unmanaged changes are harder than invalid-state drift. Without a local reconciliation ledger, change marker, event pipeline, or review workflow, the system may not know that a technically valid state bypassed business approval.
- Denying all valid-looking unmanaged changes can create operational friction after emergency technical fixes. Phase 5 must decide whether production needs a formal break-glass/reconciliation workflow.
- `WP-015` does not prove production service-to-service authentication, tamper-resistant logging, or operator RBAC. It only defines the anti-bypass behavior to validate.

## Decision Impact

`WP-015` is complete at documentation level. It defines direct Keycloak Admin Console edits as drift unless they are explicit technical setup or test actions, rejects token/frontend/protected-service shortcuts, and sets the runtime evidence needed to prove that the IAM Control Plane API remains the controlled path.

The next useful documentation-first work is `WP-016`: audit and operations review. The next runtime work can bundle `WP-011` through `WP-015`, because drift detection depends on controlled mutations, lifecycle state, service-role authorization, effective-service listing, and protected-service enforcement.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak WP-014 Result - Service Access Authorization](./keycloak-wp014-result.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Keycloak IAM Control Plane API Scope](../architecture/keycloak-iam-bff-scope.md)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
