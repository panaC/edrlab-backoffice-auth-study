# Phase 2 Minimal PoC Plan

This document defines the smallest useful Proof of Concept for the internal backoffice IAM study. It turns the current Phase 2 requirements, open-question triage, and service-permission inventory into concrete checks.

This is a planning document only. It does not add runnable code, choose a vendor, choose a framework, choose a database, or make a final production recommendation.

## Purpose

The PoC should prove the selected architecture can support:

- OIDC-compatible login through a Backoffice BFF;
- browser session isolation from OAuth tokens;
- JWT access-token validation by resource servers;
- RBAC and explicit permission enforcement;
- administrator-only member and role management;
- access checks for a representative backoffice service;
- audit events for privileged IAM changes;
- bounded access-removal latency after role removal or member disablement.

The PoC should answer whether the architecture and candidate IAM approach behave correctly across trust boundaries. It should not become a production backoffice.

## Architecture under test

```text
Browser
  -> Backoffice BFF
  -> IdP / Authorization Server / Admin Control Plane
  -> reports API resource server
```

The representative service is defined in [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md):

| Service | Role in PoC |
| --- | --- |
| `iam-admin` | IAM administration API for members, roles, assignments, and access checks. |
| `reports` | Demonstration non-IAM resource server requiring `reports:read`. |

## In scope

| Area | First-PoC scope |
| --- | --- |
| Login | OIDC-compatible Authorization Code Flow with PKCE through the BFF. |
| Browser session | Opaque HttpOnly BFF session cookie; tokens stay server-side. |
| Token format | JWT access tokens. |
| Token validation | Issuer, audience, expiry, signature, and required permission. |
| Resource server | `reports` API with `GET /reports/summary`. |
| Admin API | Member create/read/update/disable/restore, role assign/remove, role list, authorization check. |
| Roles | `member` and `admin`. |
| Permissions | `session:read_self`, `reports:read`, `members:read`, `members:create`, `members:update`, `members:disable`, `roles:read`, `roles:assign`, `authorization:check`. |
| Lifecycle states | `active` and `disabled`. |
| Access removal | Access stops no later than the configured access-token lifetime, unless a stronger mechanism is tested. |
| Audit | Privileged member and role changes produce audit events. |

## Out of scope

| Area | Reason |
| --- | --- |
| Service-to-service authentication | Future extension; not part of first PoC. |
| Public registration | Explicitly out of project scope. |
| Company-wide SSO | Outside current backoffice IAM scope. |
| Production database choice | Candidate-dependent and not needed to test behavior. |
| Production deployment topology | The first PoC tests behavior, not scaling or HA. |
| Multi-replica BFF session design | Production deployment question. |
| MFA and step-up | Production administrator policy remains open. |
| Break-glass | Production recovery decision. |
| Role creation, role update, and role deletion | Use pre-seeded roles first. |
| Hard delete, archive, and retention policy | Open lifecycle and audit decision. |
| Report export | Adds audit/data-loss questions beyond the first service-access check. |
| Client creation and secret rotation | Higher-risk control-plane topic for a later PoC or candidate evaluation. |

## Working assumptions

These assumptions keep the PoC small. They should be revisited before final recommendation.

| Area | Working assumption |
| --- | --- |
| Access-token lifetime | Use a short lifetime for PoC testing. Target `15 minutes or less`; shorter is acceptable if the candidate supports it cleanly. |
| Refresh tokens | Do not require refresh tokens in the first PoC. When an access token expires, force re-login or repeat the login flow. |
| Removed access | Role removal or member disablement may remain effective until the existing access token expires. |
| Admin MFA | Not required in the first PoC. Candidate evaluations should still record MFA support for production. |
| Roles | Use pre-seeded `member` and `admin` roles. |
| Lifecycle | Use `active` and `disabled`; defer `invited`, `archived`, and `deleted`. |
| Reports data | Use static or fixture data; business data modeling is irrelevant. |

## Seed scenario

The PoC should start with a small, known fixture set:

| Entity | State | Roles | Purpose |
| --- | --- | --- | --- |
| `admin_user` | `active` | `admin` | Performs IAM administration operations. |
| `member_user` | `active` | `member` | Proves ordinary service access. |
| `limited_user` | `active` | none or no `reports:read` | Proves service access denial. |
| `disabled_user` | `disabled` | `member` retained for review | Proves disabled-state denial. |
| `reports` service | active | requires `reports:read` | Demonstration resource server. |

## Acceptance checks

| ID | Check | Given | When | Then | Evidence |
| --- | --- | --- | --- | --- | --- |
| POC-AUTHN-001 | OIDC login through BFF | `member_user` exists and is active. | User completes login through the BFF. | Browser receives an opaque BFF session cookie. | Login trace; cookie attributes; no tokens in browser-readable storage. |
| POC-AUTHN-002 | ID token validation | OIDC callback returns an ID token. | BFF handles callback. | BFF validates issuer, audience, nonce, signature, and expiry before creating a session. | Callback validation notes or test result. |
| POC-SESSION-001 | Browser token isolation | User is logged in through BFF. | Browser storage is inspected after callback handling. | No access token, refresh token, authorization code, or ID token appears in `localStorage`, `sessionStorage`, readable cookies, URLs, or frontend logs. | Browser inspection result. |
| POC-API-001 | Reports access allowed | `member_user` has `reports:read`. | User calls `GET /reports/summary` through the BFF. | Reports API returns success. | API response and authorization decision. |
| POC-API-002 | Reports access denied without permission | `limited_user` lacks `reports:read`. | User calls `GET /reports/summary`. | Reports API denies access. | API response showing denial reason category. |
| POC-API-003 | Wrong audience rejected | A token intended for `iam-admin-api` is sent to `reports`. | Reports API validates token. | Reports API rejects the token. | Token validation failure reason. |
| POC-API-004 | Expired token rejected | Access token is expired. | Request reaches reports API. | Reports API rejects the token. | Token validation failure reason. |
| POC-ADMIN-001 | Member cannot call admin API | `member_user` lacks admin permissions. | User calls `GET /members`. | Admin API denies access. | Denied response; optional denial audit. |
| POC-ADMIN-002 | Admin can create member | `admin_user` has `members:create`. | Admin calls `POST /members`. | Member is created with stable ID and no public registration path. | API response; `member.created` audit event. |
| POC-ADMIN-003 | Admin can update member | `admin_user` has `members:update`. | Admin updates safe profile metadata. | Member stable ID is unchanged and update is audited. | API response; `member.updated` audit event. |
| POC-ADMIN-004 | Admin can disable member | `admin_user` has `members:disable`. | Admin disables `member_user`. | Member state becomes `disabled`; new login is blocked. | API response; login denial; `member.disabled` audit event. |
| POC-ADMIN-005 | Admin can restore member | `admin_user` has `members:disable`. | Admin restores disabled member. | Member state becomes `active`; role assignments are reviewable. | API response; `member.restored` audit event. |
| POC-RBAC-001 | Admin can assign role | `admin_user` has `roles:assign`. | Admin assigns `member` role to `limited_user`. | `limited_user` gains effective `reports:read` after token refresh/re-login. | API response; `role.assigned` audit event. |
| POC-RBAC-002 | Admin can remove role | `admin_user` has `roles:assign`. | Admin removes `member` role from `member_user`. | Reports access stops within configured access-token lifetime or stronger mechanism. | Access before/after evidence; `role.removed` audit event. |
| POC-RBAC-003 | Self-escalation blocked | Admin operation would grant authority outside actor boundary or disable last admin path. | Operation is attempted. | Admin API denies the operation. | Denied response; denial audit or log entry. |
| POC-AUTHZ-001 | Access check allowed | Active member has `reports:read`. | Admin calls `POST /authorization/check`. | Response says allowed for `reports:read`. | Access-check response. |
| POC-AUTHZ-002 | Access check denied | Member lacks permission or is disabled. | Admin calls `POST /authorization/check`. | Response says denied with reason category. | Access-check response. |
| POC-AUDIT-001 | Privileged audit events | Admin mutates member or role state. | Operation succeeds or is denied. | Audit event records actor, action, target, result, timestamp, and request context where safe. | Audit event sample. |
| POC-LOG-001 | Secret redaction | Login, token exchange, admin, and reports calls run. | Logs are inspected. | No passwords, tokens, authorization codes, refresh tokens, raw session IDs, client secrets, or recovery material are logged. | Log inspection notes. |

## Negative checks

The PoC is not useful if it only proves happy paths.

| ID | Negative case | Expected result |
| --- | --- | --- |
| NEG-001 | Use reports token against admin API. | Admin API rejects wrong audience. |
| NEG-002 | Use admin token against reports API if audience differs. | Reports API rejects wrong audience. |
| NEG-003 | Call reports API without `reports:read`. | Reports API denies access. |
| NEG-004 | Call admin API as ordinary `member`. | Admin API denies access. |
| NEG-005 | Use expired access token. | Resource server rejects token. |
| NEG-006 | Disable member and attempt new login. | Login is blocked. |
| NEG-007 | Remove member role and wait for token lifetime. | Reports access stops. |
| NEG-008 | Attempt unsafe self-escalation. | Admin API denies operation. |
| NEG-009 | Attempt to disable the last usable admin path. | Admin API denies operation. |
| NEG-010 | Submit state-changing BFF request without CSRF protection. | BFF rejects request. |

## Evidence to collect

The PoC should produce a short evidence note rather than a production report:

| Evidence | Why it matters |
| --- | --- |
| Login flow notes | Confirms OIDC + PKCE path and session creation. |
| Browser storage inspection | Confirms tokens stay out of browser-readable storage. |
| Token validation examples | Confirms issuer, audience, expiry, signature, and permission checks. |
| Role assignment/removal results | Confirms RBAC behavior and access-removal latency. |
| Access-check examples | Confirms admin API can answer service-access questions. |
| Audit event samples | Confirms privileged changes are reviewable. |
| Denial cases | Confirms authorization is enforced server-side. |
| Log redaction notes | Confirms logs are not credential stores. |

## Candidate evaluation impact

After the PoC plan is stable, candidate evaluation records should explicitly answer:

- Can the candidate support this PoC with ordinary configuration?
- Which acceptance checks require custom code?
- Which acceptance checks are unsupported or unclear?
- Which checks depend on provider-specific token claims or APIs?
- Which checks require a stronger PoC because documentation is ambiguous?
- Which operational behaviors remain unknown after the PoC?

## Open decisions after this plan

The plan creates working assumptions for the first PoC, but it does not close all Phase 2 decisions.

| Question | Status after this plan |
| --- | --- |
| Production administrator MFA | Still open. |
| Production step-up authentication | Still open. |
| Audit retention and export policy | Still open. |
| Break-glass access | Still open. |
| Production database and hosting model | Still open. |
| Service-to-service authentication | Deferred future scope. |
| Real backoffice service inventory | Replace `reports` when available. |
| Immediate revocation/introspection need | Still open for higher-risk production paths. |

## PoC exit criteria

The PoC is useful enough for Phase 2 if:

- all required acceptance checks are either passed or recorded as unsupported with evidence;
- failures clearly identify whether the problem is product fit, configuration, custom-code burden, or unresolved requirement;
- the result can feed candidate evaluation without becoming a production implementation;
- no final vendor or architecture recommendation is made solely from the PoC.

## Related documents

- [Phase 2 Requirements Baseline](./phase-2-requirements-baseline.md)
- [Phase 2 Open-Question Triage](./phase-2-open-question-triage.md)
- [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Member Lifecycle](./member-lifecycle.md)
- [Threat Model](./threat-model.md)
- [Evaluation Framework](./evaluation-framework.md)
