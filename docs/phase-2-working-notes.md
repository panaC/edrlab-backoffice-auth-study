# Phase 2 Working Notes

This document is the single working note for Phase 2 requirements definition, open decisions, and candidate-evaluation setup.

Phase 2 should define the minimal requirements and decisions that make a later PoC useful. It should not become the PoC itself.

This document does not choose a vendor, product, database, hosting model, implementation stack, or production architecture. It should be read with the [Evaluation Framework](./evaluation-framework.md), which turns these notes into `OK` / `KO` / `Unknown` candidate gates.

## Goal

Keep Phase 2 focused on the minimum requirements and open decisions needed to evaluate candidates and prepare a useful later PoC:

```text
Browser
  -> Backoffice BFF
  -> IdP / Authorization Server / Admin Control Plane
  -> reports API
```

The study target remains the IdP / Authorization Server / Admin Control Plane. The BFF and `reports` API are integration boundaries used to make requirements concrete; they are not implementation scope for Phase 2.

## Requirement Baseline

| ID | Requirement | Level | Later-PoC planning baseline |
| --- | --- | --- | --- |
| IAM-SCOPE-001 | The study remains limited to internal backoffice IAM. | Required | Do not expand into public customer identity, public registration, social login, or company-wide workforce IAM. |
| IAM-SCOPE-002 | The selected study shape is the Central IAM Control Plane Architecture. | Required | Browser -> Backoffice BFF -> IdP / Authorization Server / Admin Control Plane -> one demonstration API. |
| IAM-SCOPE-003 | The project focus is the IdP / Authorization Server / Admin Control Plane. | Required | BFF and APIs define integration boundaries, but are not the main implementation subject. |
| IAM-SCOPE-004 | The expected scale is fewer than 1,000 internal users. | Required | Operational complexity must stay proportionate. |
| IAM-SCOPE-005 | Managed, self-hosted, minimal-library, and hybrid approaches remain comparison candidates. | Required | No final product or architecture recommendation in Phase 2. |
| IAM-SCOPE-006 | Service-to-service authentication is future scope. | Future option | Record fit as an evolution note; do not make it a minimal-gate blocker. |
| IAM-AUTHN-001 | Backoffice users authenticate through OIDC. | Required | Authorization Code Flow with PKCE through the BFF. |
| IAM-SESSION-001 | Browser sessions are isolated from OAuth tokens. | Required | Browser gets an opaque `HttpOnly` BFF session cookie; tokens stay server-side. |
| IAM-SESSION-002 | State-changing browser-to-BFF requests use CSRF protection. | Required | Required for cookie-backed sessions. |
| IAM-TOKEN-001 | Protected APIs validate OAuth2 access tokens server-side. | Required | Validate issuer, audience, expiry, signature, and required permission. |
| IAM-TOKEN-002 | The later PoC should use JWT access tokens. | Initial baseline | Opaque tokens, introspection, and immediate revocation can be evaluated later. |
| IAM-TOKEN-003 | Access tokens are short-lived. | Expected | Removed access may remain effective only until token expiry. |
| IAM-TOKEN-004 | Tokens, codes, passwords, raw sessions, and secrets are not logged. | Required | Secret redaction is a minimal evaluation gate. |
| IAM-ID-001 | Members are administrator-managed. | Required | No public self-service registration. |
| IAM-ID-002 | Member lifecycle supports create, read, update, list, disable, and restore or retention. | Required | Later-PoC planning uses `active` and `disabled`; deletion/archive policy remains open. |
| IAM-ID-003 | Member records have stable identifiers. | Expected | Email/display name can change without breaking audit or role history. |
| IAM-RBAC-001 | RBAC is required. | Required | Start with `member` and `admin`. |
| IAM-RBAC-002 | Roles can be listed, assigned to members, and removed from members. | Required | Later-PoC planning may use pre-seeded roles; role create/update/delete can be deferred. |
| IAM-RBAC-003 | Sensitive admin operations use explicit permissions behind roles. | Expected | Avoid treating `admin` as an unrestricted bypass flag. |
| IAM-RBAC-004 | Admin operations prevent self-escalation, over-granting, and last-admin lockout. | Required | Must be part of the later-PoC acceptance plan or marked `KO` for the MVP. |
| IAM-ADMIN-001 | The administration API is server-authorized and internal-admin-only. | Required | UI hiding is not enough. |
| IAM-ADMIN-002 | The administration API supports member, role-assignment, and access-check operations. | Required | Minimum later-PoC planning surface is below. |
| IAM-ADMIN-003 | The admin API can check whether a member has access to a service permission. | Required | Diagnostic/support operation only; resource servers still enforce access. |
| IAM-AUDIT-001 | Privileged administration operations are auditable. | Required | Actor, action, target, result, timestamp, and safe request context. |
| IAM-OPS-001 | Operational complexity must be justified. | Required | Candidate evaluation must cover deployment, upgrade, backup/restore, monitoring, ownership, and credential/key rotation. |

## Decisions Needed For Later PoC

| ID | Decision | Status | Current handling |
| --- | --- | --- | --- |
| P2-Q001 | Which service defines the first service-access permissions? | Working assumption | Use `reports` as one representative API. |
| P2-Q002 | What roles and permissions should the later PoC test? | Working assumption | Use `member`, `admin`, and the small permission set below. |
| P2-Q003 | Which lifecycle states are required? | Working assumption | Use `active` and `disabled`. |
| P2-Q004 | What stale-access window is acceptable? | Working assumption | Removed access may last until short-lived access-token expiry. |
| P2-Q005 | Should the later PoC require refresh tokens? | Working assumption | No. Re-login or repeat login after access-token expiry. |
| P2-Q006 | Which candidates deserve first evaluation records? | Open | Choose a small batch from the candidate shortlist. |

## Services And Subjects

| Service ID | Audience | Purpose |
| --- | --- | --- |
| `iam-admin` | `iam-admin-api` | IAM administration API for members, role assignments, and access checks. |
| `reports` | `reports-api` | Demonstration API requiring `reports:read`. |

| Subject | Later-PoC use |
| --- | --- |
| `member` | Human backoffice user. |
| `admin` | Human member with IAM administration permissions. |
| `service_account` | Future extension only. Do not model services as fake users. |

## Permissions And Roles

| Permission | Needed for later PoC | Meaning |
| --- | --- | --- |
| `session:read_self` | Yes | Read the current signed-in member's safe profile/session summary. |
| `reports:read` | Yes | Read the demonstration reports API. |
| `members:read` | Yes | List and view member records. |
| `members:create` | Yes | Create administrator-managed members. |
| `members:update` | Yes | Update non-credential member metadata. |
| `members:disable` | Yes | Disable or restore member access. |
| `roles:read` | Yes | List roles and inspect role definitions. |
| `roles:assign` | Yes | Assign and remove roles for members. |
| `authorization:check` | Yes | Ask whether a member has a declared permission for a service. |
| `clients:read` | Optional | View non-secret OAuth2/OIDC client metadata. |

Deferred permissions: `members:delete`, `members:recover`, `roles:create`, `roles:update`, `roles:delete`, `clients:write`, `audit:read`, `operations:break_glass`, and `reports:export`.

| Role | Included permissions | Purpose |
| --- | --- | --- |
| `member` | `session:read_self`, `reports:read` | Ordinary signed-in backoffice member. |
| `admin` | `session:read_self`, `reports:read`, `members:read`, `members:create`, `members:update`, `members:disable`, `roles:read`, `roles:assign`, `authorization:check`, optionally `clients:read` | Later-PoC IAM administrator. |

The `admin` role includes `reports:read` only to keep the later PoC small. A later production design may separate business-service access from IAM administration authority.

## Minimal Operations

| Operation | Surface | Permission | Required behavior |
| --- | --- | --- | --- |
| `GET /me` | BFF or `iam-admin` | `session:read_self` | Return safe signed-in member summary. |
| `GET /members` | `iam-admin` | `members:read` | List members without credential metadata. |
| `POST /members` | `iam-admin` | `members:create` | Create member; no public registration path. |
| `PATCH /members/{id}` | `iam-admin` | `members:update` | Preserve stable member ID. |
| `POST /members/{id}/disable` | `iam-admin` | `members:disable` | Disable member and block new login/access. |
| `POST /members/{id}/restore` | `iam-admin` | `members:disable` | Restore active state after role review. |
| `GET /roles` | `iam-admin` | `roles:read` | List roles and included permissions. |
| `POST /members/{id}/roles` | `iam-admin` | `roles:assign` | Assign role; prevent self-escalation and over-granting. |
| `DELETE /members/{id}/roles/{roleId}` | `iam-admin` | `roles:assign` | Remove role; access stops within accepted stale-access window. |
| `POST /authorization/check` | `iam-admin` | `authorization:check` | Return allowed/denied and reason category. |
| `GET /reports/summary` | `reports` | `reports:read` | Validate token and permission server-side. |

## Token And Access-Check Expectations

For the later PoC, resource servers validate:

| Field | `iam-admin` | `reports` |
| --- | --- | --- |
| Issuer | Trusted study IdP / authorization server | Same |
| Audience | `iam-admin-api` | `reports-api` |
| Subject | Stable member subject | Stable member subject |
| Expiry | Short-lived access token | Short-lived access token |
| Permission | Required admin permission | `reports:read` |

Minimum access-check request:

```text
member_id
service_id: reports
permission: reports:read
```

Minimum access-check response:

```text
allowed: true | false
reason: active assignment | missing permission | disabled member | unknown service | unknown permission
```

The access check is for administration and support diagnostics. It does not replace enforcement inside `reports`.

## Later PoC Planning Baseline

The later PoC should answer one question:

```text
Can the selected IAM approach support the Central IAM Control Plane architecture with one BFF, one IAM control plane, and one protected API?
```

### In Scope

| Area | Later-PoC planning baseline |
| --- | --- |
| Login | OIDC Authorization Code Flow with PKCE through the BFF. |
| Browser session | Opaque `HttpOnly` BFF session cookie; tokens server-side. |
| Token format | Short-lived JWT access tokens. |
| Resource API | `GET /reports/summary` requiring `reports:read`. |
| Admin API | Member create/read/update/disable/restore, role list, role assign/remove, authorization check. |
| Roles | Pre-seeded `member` and `admin`. |
| Lifecycle | `active` and `disabled`. |
| Access removal | Access stops no later than access-token expiry unless a stronger mechanism is tested. |
| Audit/logs | Privileged changes audited; secrets and bearer material not logged. |

### Out Of Scope

| Area | Reason |
| --- | --- |
| Service-to-service authentication | Future extension. |
| Public registration | Explicitly outside project scope. |
| Production database and deployment topology | Candidate-dependent and not needed for behavior testing. |
| MFA, step-up, and break-glass | Production administrator policy remains open. |
| Role creation/update/delete | Use pre-seeded roles first. |
| Member deletion/archive/recovery | Lifecycle and retention policy remains open. |
| Client creation and secret rotation | Later control-plane hardening topic. |
| Report export or mutable report data | Adds data-loss/audit questions unrelated to IAM fit. |

### Seed Data

| Entity | State | Roles | Purpose |
| --- | --- | --- | --- |
| `admin_user` | `active` | `admin` | Performs IAM administration. |
| `member_user` | `active` | `member` | Proves ordinary service access. |
| `limited_user` | `active` | none | Proves service access denial. |
| `disabled_user` | `disabled` | `member` retained | Proves disabled-state denial. |
| `reports` | active | requires `reports:read` | Demonstration resource server. |

### Acceptance Checks

| ID | Check | Success condition |
| --- | --- | --- |
| POC-01 | Login through BFF | Active member completes OIDC + PKCE login and receives only an opaque BFF session cookie. |
| POC-02 | Browser token isolation | Browser-readable storage, URLs, cookies, and frontend logs contain no OAuth tokens, auth codes, raw sessions, or secrets. |
| POC-03 | JWT validation | `reports` rejects wrong issuer, wrong audience, expired token, invalid signature, and missing `reports:read`. |
| POC-04 | Service access | `member_user` can call `GET /reports/summary`; `limited_user` cannot. |
| POC-05 | Admin API protection | Ordinary members cannot call member or role administration endpoints. |
| POC-06 | Member lifecycle | Admin can create, view, update, disable, and restore members; disabled members cannot start new login. |
| POC-07 | Role assignment and removal | Admin can assign/remove `member`; gained access works after token refresh/re-login and removed access stops within the configured token lifetime. |
| POC-08 | Admin guardrails | Self-escalation, over-granting, and disabling the last usable admin path are denied. |
| POC-09 | Access check | `POST /authorization/check` returns allowed/denied with a reason category for `reports:read`. |
| POC-10 | Audit and redaction | Member and role mutations create audit events; logs/audit do not expose passwords, tokens, auth codes, raw session IDs, client secrets, or recovery material. |

## Open Decisions

### For Later PoC

| Decision | Current handling |
| --- | --- |
| First candidate batch | Open. Pick a small batch from [Candidate Shortlist](./candidate-shortlist.md). |

### Before Final Recommendation

| Decision | Why it matters |
| --- | --- |
| Administrator MFA and step-up | Affects provider fit, recovery, and admin UX. |
| Audit retention, privacy, and export | Affects managed-provider fit and operational burden. |
| IAM operations ownership | Determines whether self-hosting is realistic. |
| Uptime, backup, restore, and upgrade expectations | Defines the operational fit gate. |
| Break-glass access | Balances lockout risk against permanent-bypass risk. |
| Member deletion, archive, retention, and recovery | Affects member lifecycle, audit continuity, and data model fit. |
| Role/client administration authority | Defines admin guardrails and separation of duties. |

### Deferred Evolution

| Topic | Current position |
| --- | --- |
| Service-to-service authentication | Future extension; record candidate fit only. |
| Role hierarchies, ABAC, ReBAC, or policy engine | Future authorization complexity; avoid in later-PoC planning unless a requirement forces it. |
| Multi-replica BFF session design | Production deployment question. |
| Client creation and secret rotation PoC | Later control-plane hardening topic. |

## Candidate Evaluation Rule

For each candidate, use [Evaluation Framework](./evaluation-framework.md):

- mark each minimal gate `OK`, `KO`, or `Unknown`;
- treat `Unknown` as not yet accepted;
- record future evolution separately;
- do not average away blockers.

If a candidate cannot support OIDC login, protected API token validation, administrator-managed members, RBAC, administration API needs, auditability, secret redaction, or safe operation at the expected scale, record it before doing deeper comparison.

## PoC Evidence And Exit Criteria

Keep the evidence note short:

- login flow summary;
- browser storage inspection result;
- token validation examples;
- allowed and denied service calls;
- member lifecycle and role assignment/removal results;
- access-check examples;
- audit event samples;
- log redaction notes;
- unresolved `Unknown` gates for candidate evaluation.

The PoC is useful enough if all acceptance checks pass or are recorded as `KO` / `Unknown` with evidence, failures distinguish product fit from configuration or custom-code burden, and no final vendor or architecture recommendation is made from the PoC alone.

## Related Documents

- [Evaluation Framework](./evaluation-framework.md)
- [Candidate Shortlist](./candidate-shortlist.md)
- [Minimal backoffice IAM architecture notes](./minimal-backoffice-iam-architecture.md)
- [Initial Permission Model](./initial-permission-model.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
