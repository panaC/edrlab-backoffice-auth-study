# Initial Permission Model

This document records the project-specific first-pass permission model for the internal backoffice IAM study. It complements the general [RBAC](./wiki/05-rbac.md) wiki page.

This document originated as Phase 1 study material and now supports Phase 2 requirements definition. It does not choose a final provider, database schema, authorization library, policy engine, or production implementation.

## Purpose

The first permission model should be small enough to understand and strict enough to test. The project needs administrator-managed members, RBAC, an administration API, auditability, and protected access to internal backoffice services. It does not need a large enterprise role hierarchy for the first study.

The baseline model is:

- two human-facing role families: `member` and `admin`;
- explicit operation-level permissions behind the `admin` role;
- server-side permission enforcement at the administration API and protected resource servers;
- guardrails for self-escalation, last-admin lockout, and dangerous credential operations;
- audit events for privileged permission and lifecycle changes.

The phrase `admin` is useful for the initial mental model, but production design should avoid treating it as a magical bypass flag. Even if the first implementation has a single admin role, the system should still name the permissions that role grants.

## Subjects

| Subject type | Example | Initial scope |
| --- | --- | --- |
| Member | Internal backoffice user. | Can sign in and use backoffice features according to assigned roles. |
| Administrator | Member with IAM management authority. | Can manage members, roles, assignments, clients, and access checks according to permissions. |
| Service account | Non-human caller. | Future extension only; not an initial admin API consumer. |

Service-to-service access remains a future extension. The initial permission model still names service-account permissions so that later work does not accidentally assign human administrator roles to automation.

## Minimal permission catalog

These permissions are a first-pass catalog for evaluation and PoC planning. They are intentionally concrete but not final.

| Area | Permission | Meaning |
| --- | --- | --- |
| Session | `session:read_self` | Read the current signed-in member's own session/profile summary. |
| Members | `members:read` | List and view member records. |
| Members | `members:create` | Create administrator-managed member accounts. |
| Members | `members:update` | Update non-credential member metadata. |
| Members | `members:disable` | Disable or restore member access according to policy. |
| Members | `members:delete` | Delete or archive member records where retention policy allows. |
| Members | `members:recover` | Start or approve account recovery, authenticator reset, or MFA reset. |
| Roles | `roles:read` | List roles and inspect role definitions. |
| Roles | `roles:create` | Create role definitions. |
| Roles | `roles:update` | Change role metadata or permission membership. |
| Roles | `roles:delete` | Retire or delete role definitions where policy allows. |
| Roles | `roles:assign` | Assign or remove roles for members. |
| Clients | `clients:read` | View OAuth2/OIDC client metadata that is not secret. |
| Clients | `clients:write` | Create, update, disable, or rotate OAuth2/OIDC clients. |
| Authorization | `authorization:check` | Ask whether a member has a declared permission for a service. |
| Audit | `audit:read` | Read IAM audit events. |
| Operations | `operations:break_glass` | Activate emergency administration if the final design includes break-glass. |

The first PoC can use fewer permissions if the scope is narrowed, but the study should keep the full catalog visible so later product evaluation does not hide important control-plane needs.

## Role matrix

| Permission | `member` | `admin` | Notes |
| --- | --- | --- | --- |
| `session:read_self` | Yes | Yes | A member can see their own signed-in identity and safe profile summary. |
| `members:read` | No | Yes | Ordinary members should not list the IAM directory by default. |
| `members:create` | No | Yes | No public registration. |
| `members:update` | No | Yes | Self-service profile updates are not part of the first baseline. |
| `members:disable` | No | Yes | Guardrails apply for self-disable and last-admin disable. |
| `members:delete` | No | Restricted | Prefer archive/disable until retention policy is clear. |
| `members:recover` | No | Restricted | Treat recovery, email change, MFA reset, and authenticator reset as sensitive. |
| `roles:read` | No | Yes | Required for administration and access review. |
| `roles:create` | No | Restricted | Role definition changes affect many subjects. |
| `roles:update` | No | Restricted | Requires self-escalation and grant-boundary controls. |
| `roles:delete` | No | Restricted | Prefer retire/archive where audit history matters. |
| `roles:assign` | No | Restricted | Admins can assign only roles within their grant boundary. |
| `clients:read` | No | Yes | Secret values must not be returned. |
| `clients:write` | No | Restricted | Redirect URIs, allowed flows, and secrets affect token issuance. |
| `authorization:check` | No | Yes | Available to trusted admin workflows, not untrusted frontend logic. |
| `audit:read` | No | Restricted | Audit data is sensitive and may include personal or operational data. |
| `operations:break_glass` | No | Emergency only | Dormant unless a break-glass process is explicitly adopted. |

`Restricted` means the permission is not enough by itself. The operation also needs additional checks such as grant boundary, self-action restriction, step-up authentication, approval, reason field, or break-glass procedure.

## Operation matrix

| Operation | Required permission | Additional rule |
| --- | --- | --- |
| `GET /me` | `session:read_self` | Return only safe profile/session data. |
| `GET /members` | `members:read` | Paginate and avoid exposing credential metadata. |
| `POST /members` | `members:create` | No public registration; audit actor and target. |
| `PATCH /members/{id}` | `members:update` | Email changes preserve stable member ID and are audited. |
| `POST /members/{id}/disable` | `members:disable` | Prevent disabling self if it would remove the last admin path. |
| `POST /members/{id}/restore` | `members:disable` | Review existing roles before reactivation. |
| `POST /members/{id}/recovery` | `members:recover` | Sensitive; consider step-up and notification. |
| `DELETE /members/{id}` | `members:delete` | Prefer archive until deletion policy is defined. |
| `GET /roles` | `roles:read` | Include permission membership for review. |
| `POST /roles` | `roles:create` | Prevent creating roles outside admin's grant boundary. |
| `PATCH /roles/{id}` | `roles:update` | Prevent adding permissions the actor cannot grant. |
| `POST /members/{id}/roles` | `roles:assign` | Prevent self-escalation and over-granting. |
| `DELETE /members/{id}/roles/{roleId}` | `roles:assign` | Audit removal and define access latency. |
| `GET /clients` | `clients:read` | Never return client secrets. |
| `POST /clients` | `clients:write` | Validate redirect URIs, allowed flows, owner, and environment. |
| `POST /clients/{id}/rotate-secret` | `clients:write` | Show new secret once; audit rotation metadata, not secret value. |
| `POST /authorization/check` | `authorization:check` | The check is diagnostic/supportive; resource servers still enforce access. |
| `GET /audit-events` | `audit:read` | Audit audit-log access and export. |

## Self-escalation guardrails

Self-escalation is any path where a caller can increase their own future authority or remove oversight.

Minimum guardrails:

- an administrator cannot grant themselves a role they do not already have authority to grant;
- an administrator cannot add permissions to a role they currently hold if that would increase their own authority without a separate approval path;
- an administrator cannot disable, delete, or demote the last usable administrator path;
- an administrator cannot reset their own MFA, recovery codes, or recovery email without an explicit recovery policy;
- an administrator cannot create a client that can mint broader admin tokens than the actor is allowed to manage;
- service accounts cannot receive human `admin` roles by default;
- break-glass activation, if added, is time-bound, audited, and reviewed afterward.

For a small first version, these controls can be implemented as simple operation checks rather than a full policy engine. The important point is that the checks are explicit and tested.

## Minimal role definitions

| Role | Included permissions | Purpose |
| --- | --- | --- |
| `member` | `session:read_self` plus service-specific permissions assigned later. | Ordinary signed-in backoffice member. |
| `admin` | `members:read`, `members:create`, `members:update`, `members:disable`, `roles:read`, `roles:assign`, `authorization:check`, `clients:read`. | Initial IAM administrator with restrained mutation authority. |
| `iam_owner` or equivalent later role | Adds restricted permissions such as `roles:create`, `roles:update`, `clients:write`, `audit:read`, and `members:recover`. | Higher-impact IAM owner role if the first admin role becomes too broad. |

The first project brief mentions admin and member. This document keeps that baseline but names where a future split may be justified. A final design can keep one admin role only if the team accepts the operational risk.

## Audit expectations

These events should be auditable in the initial permission model:

| Event | Minimum evidence |
| --- | --- |
| `member.created` | Actor, target, result, timestamp, request ID. |
| `member.updated` | Safe before/after summary, especially for email or status changes. |
| `member.disabled` or `member.restored` | Actor, target, reason, token/session effect where known. |
| `member.recovery_started` or `member.authenticator_reset` | Actor, target, method family, reason, notification outcome. |
| `role.assigned` or `role.removed` | Actor, target subject, role, result, reason. |
| `role.updated` | Safe before/after permission membership. |
| `client.created`, `client.updated`, `client.secret_rotated` | Client ID, owner, environment, safe metadata changes. |
| `authorization.denied` | Actor, operation, required permission, target where safe. |
| `audit.read` or `audit.exported` | Actor, query/export scope, result. |

Never log passwords, bearer tokens, refresh tokens, client secrets, authorization codes, recovery codes, private keys, or raw session IDs.

## Negative test checklist

A later PoC or implementation should prove denied paths, not only happy paths:

- a `member` cannot call admin API endpoints;
- an `admin` cannot assign a role to themselves beyond their grant boundary;
- an `admin` cannot disable the last administrator;
- an `admin` cannot read client secrets after creation or rotation;
- a token with the wrong audience is rejected by the admin API;
- a token with `members:read` cannot call `members:disable`;
- a disabled member cannot refresh or receive new effective access;
- role removal stops access within the documented token lifecycle window;
- audit events are written for both successful and denied privileged actions.

## Related documents

- [RBAC](./wiki/05-rbac.md)
- [Admin API](./wiki/08-admin-api.md)
- [Member Lifecycle](./member-lifecycle.md)
- [OAuth Client Management](./wiki/13-oauth-client-management.md)
- [Token Lifecycle](./wiki/12-token-lifecycle.md)
- [Threat Model](./threat-model.md)
- [Operational Model](./operational-model.md)

## References

- [The NIST Model for Role-Based Access Control: Towards a Unified Standard](https://www.nist.gov/publications/nist-model-role-based-access-control-towards-unified-standard)
- [A Revised Model for Role-Based Access Control - NISTIR 6192](https://www.nist.gov/publications/revised-model-role-based-access-control)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP API Security Top 10 - 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
