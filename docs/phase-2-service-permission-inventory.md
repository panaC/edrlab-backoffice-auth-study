# Phase 2 Service and Permission Inventory

This document defines the first representative backoffice service, operation inventory, permission set, role mapping, and verification checks for Phase 2.

It answers the first two `P0` questions from [Phase 2 Open-Question Triage](./phase-2-open-question-triage.md):

- `P2-Q001`: Which real or representative backoffice service should define the first service-access permissions?
- `P2-Q002`: What exact permissions should `member` and `admin` have in the first PoC?

This is a working baseline for requirements refinement and PoC planning. It does not choose a provider, framework, database, or production implementation.

## Scope

No real backoffice service inventory is available yet. Until one exists, the first representative protected resource server is:

```text
reports
```

The `reports` service is intentionally small. It represents a normal internal backoffice API that is not the IAM control plane. Its purpose is to test whether the selected IAM approach can issue tokens, let a resource server validate those tokens, and enforce service permissions separately from login and admin UI behavior.

The first PoC should therefore cover two protected API surfaces:

| Service ID | Surface | Purpose | First-PoC status |
| --- | --- | --- | --- |
| `iam-admin` | IAM administration API | Manage members, roles, assignments, OAuth clients, and access checks. | Required |
| `reports` | Demonstration resource server | Prove non-IAM service access through token validation and permission checks. | Required |

Service-to-service callers remain future scope. The first PoC models only human backoffice users calling through the BFF.

## Service inventory

| Service ID | Audience | Owner | Data sensitivity | Permission style | Notes |
| --- | --- | --- | --- | --- | --- |
| `iam-admin` | `iam-admin-api` | IAM owner | High | Explicit admin permissions | Control-plane operations must be strongly authorized and audited. |
| `reports` | `reports-api` | Demonstration service owner | Medium | Service permissions | Represents one ordinary backoffice resource server. |

The audience values are placeholders for study and PoC planning. A later provider may use different exact audience syntax, but the requirement remains: a token for `reports-api` must not be accepted by `iam-admin-api`, and a token for `iam-admin-api` must not automatically authorize ordinary service operations.

## Subject types

| Subject type | First-PoC use | Notes |
| --- | --- | --- |
| `member` | Human backoffice user. | Can authenticate and receive service access. |
| `admin` | Human backoffice user with IAM control-plane permissions. | Should also remain a member, but admin authority must be checked explicitly. |
| `service_account` | Not used in the first PoC. | Future extension only. Do not model services as fake human users. |

## First-PoC permissions

The first PoC uses a deliberately small permission set. Broader permissions from [Initial Permission Model](./initial-permission-model.md) remain visible for later evaluation but are not required in the first test pass.

| Permission | Area | Meaning | First-PoC status |
| --- | --- | --- | --- |
| `session:read_self` | Session | Read the current signed-in member's safe profile and session summary. | Required |
| `reports:read` | Reports service | Read report list and report details from the demonstration API. | Required |
| `members:read` | IAM admin | List and view member records. | Required |
| `members:create` | IAM admin | Create administrator-managed member accounts. | Required |
| `members:update` | IAM admin | Update non-credential member metadata. | Required |
| `members:disable` | IAM admin | Disable or restore member access according to policy. | Required |
| `roles:read` | IAM admin | List roles and inspect role definitions. | Required |
| `roles:assign` | IAM admin | Assign and remove roles for members. | Required |
| `authorization:check` | IAM admin | Ask whether a member has a declared permission for a service. | Required |
| `clients:read` | IAM admin | View OAuth2/OIDC client metadata that is not secret. | Optional in first PoC |

## Deferred permissions

These permissions remain important for candidate evaluation, but they can wait until after the first PoC unless a candidate's data model requires earlier clarification.

| Permission | Reason to defer |
| --- | --- |
| `members:delete` | Deletion, archive, and retention policy are still open. |
| `members:recover` | Recovery and authenticator reset policy need separate security decisions. |
| `roles:create` | The first PoC can use pre-seeded `member` and `admin` roles. |
| `roles:update` | Changing role definitions raises self-escalation and review questions. |
| `roles:delete` | Role retirement needs audit and retention semantics. |
| `clients:write` | Client creation and secret rotation are higher-risk control-plane operations. |
| `audit:read` | Audit access/export policy is still open. |
| `operations:break_glass` | Break-glass is a production decision, not a first-PoC requirement. |
| `reports:export` | Export adds data-loss and audit questions beyond simple service access. |

## Role mapping

The first PoC keeps the role model small:

| Role | Included permissions | Purpose |
| --- | --- | --- |
| `member` | `session:read_self`, `reports:read` | Ordinary backoffice member who can sign in and access the demonstration service. |
| `admin` | `session:read_self`, `reports:read`, `members:read`, `members:create`, `members:update`, `members:disable`, `roles:read`, `roles:assign`, `authorization:check`, optionally `clients:read` | IAM administrator for the first PoC. |

The `admin` role includes `reports:read` only to keep the first PoC simple. A later production design may assign business-service access separately from IAM administration authority.

Candidate evaluation should record whether a product supports this as:

- one role containing all permissions;
- multiple role assignments, such as `member` plus `admin`;
- groups plus application permissions;
- scopes or claims mapped into API permissions;
- provider-specific constructs that need translation.

## Operation inventory

### Backoffice session operations

| Operation | Surface | Required permission | Expected result |
| --- | --- | --- | --- |
| `GET /me` | BFF or admin API | `session:read_self` | Returns safe signed-in member summary. |

### IAM administration operations

| Operation | Surface | Required permission | Additional rule | Audit event |
| --- | --- | --- | --- | --- |
| `GET /members` | `iam-admin` | `members:read` | Paginate and hide credential metadata. | Optional read audit |
| `GET /members/{id}` | `iam-admin` | `members:read` | Return safe member details. | Optional read audit |
| `POST /members` | `iam-admin` | `members:create` | No public registration; assign stable member ID. | `member.created` |
| `PATCH /members/{id}` | `iam-admin` | `members:update` | Preserve stable ID; audit sensitive field changes. | `member.updated` |
| `POST /members/{id}/disable` | `iam-admin` | `members:disable` | Prevent unsafe self-disablement and last-admin lockout. | `member.disabled` |
| `POST /members/{id}/restore` | `iam-admin` | `members:disable` | Review role assignments before effective access returns. | `member.restored` |
| `GET /roles` | `iam-admin` | `roles:read` | Include permission membership for review. | Optional read audit |
| `POST /members/{id}/roles` | `iam-admin` | `roles:assign` | Prevent self-escalation and over-granting. | `role.assigned` |
| `DELETE /members/{id}/roles/{roleId}` | `iam-admin` | `roles:assign` | Define access-removal latency. | `role.removed` |
| `POST /authorization/check` | `iam-admin` | `authorization:check` | Diagnostic only; resource servers still enforce access. | `authorization.checked` or `authorization.denied` |

### Reports service operations

| Operation | Surface | Required permission | Additional rule | Audit event |
| --- | --- | --- | --- | --- |
| `GET /reports` | `reports` | `reports:read` | Token audience must be `reports-api`. | Optional read audit |
| `GET /reports/{id}` | `reports` | `reports:read` | Enforce permission server-side. | Optional read audit |
| `GET /reports/summary` | `reports` | `reports:read` | Useful minimal PoC endpoint. | Optional read audit |

The first PoC does not need mutable `reports` operations. The demonstration service should be boring by design; the interesting behavior is token validation, audience checking, permission enforcement, and access removal.

## Access-check model

The administration API must support checking whether a member has access to a backoffice service. For the first PoC, the minimum access-check shape is:

```text
POST /authorization/check

Inputs:
- member_id
- service_id: reports
- permission: reports:read

Decision:
- allowed: true or false
- reason category: active assignment, missing permission, disabled member, unknown service, or unknown permission
```

This check is useful for administration workflows and support diagnostics. It must not replace enforcement inside `reports`. The `reports` API still validates the token and checks `reports:read` on every protected request.

## Token expectation

For the first PoC, resource servers should be able to validate:

| Token field or property | `iam-admin` expectation | `reports` expectation |
| --- | --- | --- |
| Issuer | Trusted study IdP / authorization server. | Same trusted study IdP / authorization server. |
| Audience | `iam-admin-api`. | `reports-api`. |
| Subject | Stable member subject. | Stable member subject. |
| Expiry | Short-lived access token. | Short-lived access token. |
| Permissions | Required admin permission. | `reports:read`. |

Negative tests must include wrong audience, missing permission, expired token, and disabled member behavior.

## First-PoC acceptance checks

| Check | Success condition |
| --- | --- |
| Member login | A `member` can authenticate through OIDC-compatible login and obtain a BFF session. |
| Member service access | A `member` can call `GET /reports/summary` through the BFF when effective permissions include `reports:read`. |
| Member admin denial | A `member` cannot call `GET /members` or assign roles. |
| Admin member management | An `admin` can create, view, update, disable, and restore members. |
| Admin role assignment | An `admin` can assign and remove the `member` role according to self-escalation guardrails. |
| Access check | `POST /authorization/check` returns allowed for an active member with `reports:read` and denied for a member without it. |
| Disabled member | A disabled member cannot start a new login and cannot receive new effective access. |
| Role removal latency | Removing `member` or `reports:read` stops reports access within the documented token lifetime or through a stronger mechanism. |
| Wrong audience rejection | The reports API rejects a token intended for `iam-admin-api`; the admin API rejects a token intended for `reports-api`. |
| Audit events | Member create/update/disable/restore and role assign/remove create audit events with actor, target, result, timestamp, and request context. |
| Secret redaction | Tokens, authorization codes, refresh tokens, session IDs, client secrets, passwords, and recovery material are not logged. |

## Candidate-evaluation prompts

When evaluating a candidate, use this inventory to ask:

- Can the candidate represent `member` and `admin` roles with explicit permissions?
- Can it express a normal service permission such as `reports:read` separately from IAM administration permissions?
- Can tokens carry or reference permissions in a way resource servers can enforce?
- Can the admin API or management API answer an access-check question for a member and service?
- Can role removal or member disablement affect service access within the accepted stale-access window?
- Can admin operations and role changes be audited with enough context?
- Can the model avoid giving every administrator unrestricted access to every business service by default?

## Open follow-ups

| Question | Current handling |
| --- | --- |
| Should `reports:export` be included? | Defer until audit/export policy is clearer. |
| Should `admin` automatically inherit `member` service access? | Allow in first PoC for simplicity; revisit before production recommendation. |
| Should there be a read-only administrator role? | Defer until candidate evaluation or stakeholder need. |
| Should role definitions be mutable in the first PoC? | No. Use pre-seeded roles and test assignment/removal first. |
| What is the real first backoffice service? | Replace `reports` when a real service inventory exists. |

## Related documents

- [Phase 2 Requirements Baseline](./phase-2-requirements-baseline.md)
- [Phase 2 Open-Question Triage](./phase-2-open-question-triage.md)
- [Phase 2 Minimal PoC Plan](./phase-2-minimal-poc-plan.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Member Lifecycle](./member-lifecycle.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Admin API](./wiki/08-admin-api.md)
- [RBAC](./wiki/05-rbac.md)
- [Token Lifecycle](./wiki/12-token-lifecycle.md)
- [Threat Model](./threat-model.md)
