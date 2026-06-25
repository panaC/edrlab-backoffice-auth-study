# Keycloak WP-010 Result - IAM Mapping Design

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Selected Mapping](#selected-mapping)
- [IAM Control Plane API Invariants](#iam-control-plane-api-invariants)
- [Rejected Shortcuts](#rejected-shortcuts)
- [Validation Scenarios Unlocked](#validation-scenarios-unlocked)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-010` chooses the first concrete Keycloak IAM mapping to validate after the pivot to Keycloak as IAM source with an EDRLab Admin Console and EDRLab IAM Control Plane API. It is documentation-first evidence for the next runtime work packages, not production approval or implementation work ([Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md), [ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

The mapping uses Keycloak users, user attributes, client roles, authentication evidence, Admin REST, and admin events as validation inputs. Keycloak Admin REST exposes user fields such as `id`, `email`, `emailVerified`, `attributes`, `enabled`, `requiredActions`, `realmRoles`, `clientRoles`, and `groups`; Keycloak also documents user attributes, roles and groups, authentication flows, Admin REST, and admin events as product capabilities ([Keycloak Admin REST API - UserRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_userrepresentation), [Keycloak user attributes](https://www.keycloak.org/docs/latest/server_admin/#managing-user-attributes), [Keycloak roles and groups](https://www.keycloak.org/docs/latest/server_admin/#assigning-permissions-using-roles-and-groups), [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows), [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

## Result

Choose this mapping for the first Keycloak IAM Control Plane API validation slice:

- account type as exactly one Keycloak client role on a dedicated `edrlab-backoffice` client;
- lifecycle as an EDRLab namespaced Keycloak user attribute, with Keycloak `enabled` used only as a coarse login/session guard for disabled and archived accounts;
- service-access roles as Keycloak client roles on a dedicated `edrlab-protected-services` client;
- protected-service authorization as an IAM Control Plane API-mediated fresh check against current Keycloak IAM state;
- project audit as local EDRLab business audit plus supplemental Keycloak admin/user event evidence.

This closes `OMD-KIB-001` through `OMD-KIB-004` for the first validation slice. `OMD-KIB-005` moved to `WP-013` for explicit privileged-authentication proof and was later validated at PoC level by the dedicated `WP-013` Docker runtime ([Keycloak WP-013 result](./keycloak-wp013-result.md#runtime-execution)). `OMD-KIB-006` is partially closed: Keycloak events are supplemental, while local EDRLab business audit remains required for the PoC evidence boundary.

## Selected Mapping

| State or decision | Selected Keycloak mapping for validation | IAM Control Plane API responsibility | Requirement fit |
| --- | --- | --- | --- |
| Stable account identity | Keycloak user plus immutable EDRLab user attribute `edrlab.account_id`. The Keycloak OIDC `sub` is the authenticated subject, while `edrlab.account_id` remains the business audit/account identifier. OpenID Connect defines `sub` as the subject identifier for the authenticated end-user ([OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html#IDToken)). | Generate `edrlab.account_id` once at account creation, never update it, and deny if it is missing, duplicated, or changed. | Keeps the stable account identifier separate from mutable profile data (`FR-009`, `FR-010`). |
| Subject link | User attribute `edrlab.linked_subject` is empty while the account is `invited`; on safe onboarding activation, the IAM Control Plane API stores the current Keycloak `sub` value and treats it as immutable. | Link only during `FR-043` onboarding activation; deny and audit any attempt to create, change, remove, or rebind the link outside that flow. | Preserves controlled subject-link creation and fail-closed unsafe onboarding (`FR-039`, `FR-043`, `FR-044`). |
| Profile fields | Keycloak standard profile fields for `email`, `firstName`, and `lastName`, plus `edrlab.organization` as a user attribute. | Update profile only through authorized IAM Control Plane API operations; never authorize by mutable email, name, or organization alone. | Supports invited account profile needs without making mutable fields authoritative (`FR-009`, `FR-040`). |
| Account type | Exactly one client role on client `edrlab-backoffice`: `account-type-member`, `account-type-admin`, or `account-type-super-admin`. Do not use composite roles for this first validation. | Assign the role at account creation only; deny if zero or multiple account-type roles are present; forbid account-type mutation and self-elevation. | Models the three fixed account types while keeping the anti-bypass rule explicit (`FR-001`, `FR-026`, `FR-038`). |
| Lifecycle | User attribute `edrlab.lifecycle` with values `invited`, `active`, `disabled`, or `archived`; Keycloak `enabled=false` for `disabled` and `archived`, and `enabled=true` for `invited` and `active`. | Enforce allowed transitions: `invited -> active`, `active -> disabled`, `disabled -> active`, and `disabled -> archived`; reject return to `invited`; deny protected-service access unless lifecycle is `active`. | Represents lifecycle semantics that Keycloak `enabled` alone cannot express (`FR-011` through `FR-016`, `FR-031`). |
| Invited onboarding | `edrlab.lifecycle=invited`, `enabled=true`, required email verification evidence, and no `edrlab.linked_subject`. Keycloak required actions may be used for password/email setup but are not sufficient by themselves for EDRLab activation. | Allow only the onboarding activation path; require exactly one invited account, verified matching email evidence, and no existing subject link before activation. | Preserves safe automatic onboarding and unsafe-match denial (`FR-037`, `FR-043`, `FR-044`). |
| Service-access roles | Client roles on client `edrlab-protected-services`, named per service and access level, starting with `service-catalog-consult` for the first protected backend service. | Assign service-access roles only to `member` accounts; never assign them to `admin` or `super-admin`; reject inactive service roles once role lifecycle is modeled. | Keeps service-access roles separate from account types and account-management powers (`FR-002`, `FR-005`, `FR-022`, `FR-032`). |
| Admin and super-admin protected-service access | No service-access role assignment to `admin` or `super-admin`. The IAM Control Plane API computes automatic covered-service access from the account-type role when lifecycle is `active`. | Grant covered-service access to active admins and super-admins through account type, not through member service-role assignments. | Preserves inherited admin service access without merging account types and service roles (`FR-003`, `FR-004`). |
| Protected-service authorization | Protected backend services call an EDRLab IAM Control Plane API endpoint such as `authorization/check`. The IAM Control Plane API reads current Keycloak user attributes and role mappings before returning `allow` or `deny`. OWASP guidance requires authorization checks server-side and safe handling when checks fail ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Perform a fresh check with no positive authorization cache in the PoC; deny when Keycloak state is missing, inconsistent, stale, or unreachable. | Keeps authorization server-side and fail-closed while avoiding raw token-claim bypass (`FR-020`, `FR-021`, `FR-038`). |
| Token claims | Account-type and service-access roles may appear in tokens only as non-authoritative UI hints or diagnostic evidence for this validation slice. | Protected services must not grant access from raw token roles or frontend checks; they must call the IAM Control Plane API contract. | Reuses Keycloak evidence without bypassing the controlled path (`FR-020`, `FR-033`, `FR-038`). |
| Privileged-authentication evidence | Validate in `WP-013` using Keycloak authentication flow, `acr`/`amr`-style token evidence, admin/user events, or explicit configuration evidence. | Block production-like `admin` and `super-admin` activation unless the evidence is explicit enough; record a blocker if it is not. | The dedicated `WP-013` Docker runtime later validated the ACR/LoA step-up path at PoC level (`FR-034`, `FR-043`, `FR-044`; [Keycloak WP-013 result](./keycloak-wp013-result.md#runtime-execution)). |
| Business audit | Local EDRLab audit event for each business decision, with Keycloak admin/user event references where useful. Keycloak can record administrator actions performed through the Admin Console or REST interface, but those events do not express the EDRLab business rationale by themselves ([Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). | Record actor, action, target, result, reason, correlation ID, before/after business state, and Keycloak resource references. | Covers business audit and audit-read/export requirements that provider events alone do not prove (`FR-027`, `FR-028`, `FR-035`). |

## IAM Control Plane API Invariants

The IAM Control Plane API must enforce these invariants in every validation scenario:

- resolve the actor to exactly one active Keycloak-backed EDRLab account before administrative authorization;
- require exactly one account-type client role and deny if the role set is missing or inconsistent;
- never update account type after account creation;
- never assign service-access roles to `admin` or `super-admin` accounts;
- deny protected-service access unless `edrlab.lifecycle=active`;
- treat any unmanaged Keycloak Admin Console mutation of account type, lifecycle, subject link, or service roles as drift unless it was performed by the approved IAM Control Plane API technical path;
- record a local EDRLab audit event for every allowed, denied, blocked, or drift-detected business operation;
- fail closed when Keycloak current state cannot be read or when the state violates one of these invariants.

These invariants are the practical interpretation of `FR-038`: Keycloak IAM state may be authoritative only through the controlled server-side administration and authorization path, not through browser clients, frontend checks, raw claims, or unmanaged console edits.

## Rejected Shortcuts

| Shortcut | Status for first validation | Reason |
| --- | --- | --- |
| Lifecycle represented only by Keycloak `enabled` | Rejected. | `enabled` can help stop login/session behavior for disabled and archived accounts, but it does not represent `invited`, `active`, `disabled`, and `archived` semantics by itself. |
| Protected services authorize directly from token role claims | Rejected. | Token claims can be stale or over-scoped, and raw claims would bypass the controlled IAM Control Plane API authorization path required by `FR-038`. |
| Business administrators use Keycloak Admin Console directly | Rejected. | Direct edits can bypass EDRLab invariants and audit; Keycloak realm/admin permissions are a technical administration surface to review, not the business access-control UI ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). |
| Account type through groups or default groups | Deferred. | Groups are useful in Keycloak, but the first validation should minimize membership drift and prove exactly-one account-type semantics with dedicated client roles. |
| Keycloak Organizations for `organization` profile field | Deferred. | The current requirement needs an account profile field, not organization membership management; adding Keycloak Organizations would expand the PoC beyond the first mapping question. |
| Keycloak Authorization Services as the first protected-service contract | Deferred. | Authorization Services may be useful later, but the first slice should prove the simpler IAM Control Plane API-mediated contract before adding resource/scope/policy complexity ([Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)). |

## Validation Scenarios Unlocked

| Next work package | Scenario now ready to validate |
| --- | --- |
| `WP-011` | The IAM Control Plane API creates a `member`, `admin`, and `super-admin` user through Keycloak Admin REST, assigns exactly one account-type role, writes lifecycle attributes, and records local business audit. |
| `WP-012` | Invited account onboarding activates only when the current Keycloak subject has verified matching email evidence and no existing linked subject. |
| `WP-013` | `admin` and `super-admin` activation requires Keycloak flow, token, event, or configuration evidence proving the privileged-authentication requirement; the dedicated runtime later validated the first ACR/LoA path at PoC level. |
| `WP-014` | Protected-service access uses `authorization/check`, reads current Keycloak state, grants active admins and super-admins automatically, grants members only through service-access roles, and denies after lifecycle or role changes. |
| `WP-015` | Direct Keycloak Admin Console changes to roles or attributes are treated as drift and must not silently authorize access. |
| `WP-016` | Local audit examples can be compared with Keycloak admin events to decide which business audit records remain outside Keycloak. |

## Residual Risks

- Keycloak user attributes and role mappings are mutable through sufficiently privileged administrative access. The PoC must therefore validate restricted technical administration, drift detection, and fail-closed behavior for invariant violations (`FR-026`, `FR-038`).
- The selected mapping still needs a local EDRLab audit sink for business decisions. That is a logical persistence responsibility, not a production database topology decision.
- IAM Control Plane API-mediated authorization makes the IAM Control Plane API part of the protected-service access path. The PoC must measure failure behavior and record availability/latency implications before Phase 5 review.
- Token claims may still expose role evidence to clients. The PoC must prove that protected services ignore those claims for final authorization.
- Privileged-authentication evidence is not closed by this document. The follow-up `WP-013` runtime proves the selected ACR/LoA evidence path at PoC level; Phase 5 still needs to decide the production authenticator policy.

## Decision Impact

`WP-010` is complete for documentation-level mapping selection. The next useful work is `WP-011`: validate the IAM Control Plane API admin anti-bypass path for creating and mutating Keycloak-backed EDRLab accounts through the controlled server-side control-plane path.

This result changes no production requirements, adds no production code, and creates no runtime PoC artifact. Runtime work still requires a Linux-targeted, Docker-based, fully scripted PoC definition before execution.

## References

- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [Keycloak IAM Control Plane API Scope](../architecture/keycloak-iam-bff-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak UserRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_userrepresentation)
- [Keycloak User Attributes](https://www.keycloak.org/docs/latest/server_admin/#managing-user-attributes)
- [Keycloak Roles and Groups](https://www.keycloak.org/docs/latest/server_admin/#assigning-permissions-using-roles-and-groups)
- [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
