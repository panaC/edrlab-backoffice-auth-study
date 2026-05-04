# Phase 1 Working Notes

This work-in-progress document collects Phase 1 requirements, open questions, evaluation notes, and risk notes for later comparison work. It does not choose a vendor, product, architecture, database, hosting model, or implementation approach.

The expected system is an internal backoffice IAM control plane for fewer than 1,000 users. Public registration, customer identity, social login, and broad enterprise IAM complexity are out of scope. Members are created and managed by administrators, RBAC is required, and administration operations must be auditable.

## Requirement Levels

| Level | Meaning |
| --- | --- |
| Required | Needed to satisfy the current project brief. |
| Expected | Strongly implied by the requirements or by conservative IAM practice, but details can be finalized later. |
| Study question | Must be answered before a final recommendation, but should not be assumed during Phase 1. |

## Requirements Inventory

### Identity and Member Lifecycle

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Administrators can create, read, update, list, disable, and delete members. | Deletion and disabling should remain distinct because disabling preserves recovery and audit options. |
| Required | Public self-service registration is not supported. | Member onboarding is an internal administrative process. |
| Required | Members can receive and lose role assignments. | See [RBAC](./wiki/05-rbac.md) for the role and permission model. |
| Expected | Member records have stable identifiers separate from mutable display attributes. | Email addresses and names can change; audit trails and role assignments need durable references. |
| Expected | Disabled members cannot authenticate or keep using privileged access. | Token lifetime, session handling, and revocation behavior need later design work. |
| Study question | Which member attributes are required beyond identity, status, and role assignments? | Keep attributes minimal unless backoffice workflows require more. |

### Authentication and OIDC

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Backoffice users authenticate through OAuth2/OIDC-compatible login. | OIDC provides the identity layer on top of OAuth2; see [OpenID Connect](./wiki/03-openid-connect.md). |
| Required | Browser-based backoffice clients use Authorization Code Flow with PKCE. | Implicit Flow should not be used for new browser applications. |
| Expected | Authentication results are represented separately from API authorization decisions. | A successful login does not imply access to admin APIs or backoffice services. |
| Expected | Login, session, and token behavior can support account disablement and incident response. | The exact balance among short token lifetimes, refresh tokens, session invalidation, and revocation is a later design topic. |
| Study question | Is an existing corporate identity provider available and preferred for primary authentication? | This affects managed, self-hosted, and hybrid options. |
| Study question | Are MFA, passwordless login, or step-up authentication required for administrators? | This should be decided from business risk and operational expectations, not assumed from tooling. |

### OAuth2, Tokens, and API Protection

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Protected APIs receive and validate access tokens. | Resource servers need issuer, audience, lifetime, signature or introspection, and authorization checks. |
| Required | Access control works for internal backoffice services. | The authorization model must be enforceable by each protected service. |
| Required | User-facing and service-to-service access are both supported. | Human users and machine clients should be modeled distinctly. |
| Expected | Access tokens are short-lived unless a later design documents a specific reason otherwise. | Bearer token leakage risk increases with token lifetime. |
| Expected | Token claims, scopes, roles, and permissions are defined with clear responsibilities. | Avoid making one token field carry every authorization concern. |
| Study question | Should access tokens be JWTs, opaque tokens with introspection, or a mixed model? | See [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) for trade-offs. |
| Study question | Where should high-churn authorization state be checked? | Options include token claims, local policy, IAM lookups, introspection, or a dedicated authorization check. |

### RBAC and Permission Modeling

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | RBAC is supported. | Roles group permissions for business-readable access management. |
| Required | Roles can be created, listed, assigned to members. | These operations are part of the minimum administration API. |
| Expected | Sensitive operations use explicit permissions. | `members:read`, `members:disable`, and `roles:assign` are easier to reason about than a single broad admin flag. |
| Expected | Service permissions are separated from human administrator permissions. | Automation should not inherit broad human privileges by convenience. |
| Study question | What initial role catalog is needed for the backoffice? | The study should identify examples, but final role design belongs closer to implementation. |
| Study question | Are role hierarchies, resource-level permissions, or ABAC-style rules needed? | Avoid adding these unless concrete workflows require them. |

### Administration API

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | The administration API manages members, roles, role assignments, and access checks. | See [Admin API](./wiki/08-admin-api.md) for the conceptual control-plane model. |
| Required | Administration is restricted to internal administrators only. | Admin UI checks are not enough; the API must enforce authorization server-side. |
| Required | The API can check whether a member has access to a given backoffice service. | The shape may be an endpoint, library call, policy lookup, or product capability later. |
| Expected | Privileged mutations produce audit events. | Actor, action, target, result, timestamp, and request context are the minimum useful shape. |
| Expected | Admin endpoints prevent self-escalation and privilege grant beyond the actor's authority. | Role assignment and client creation are especially sensitive. |
| Expected | Admin mutations have clear validation, idempotency, and concurrency behavior. | Duplicate role assignment and racing updates should be predictable. |
| Study question | Which consumers need the admin API besides a backoffice admin UI? | Internal automation may need separate client credentials and narrower permissions. |

### Service-to-Service Authentication

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Applications and services can authenticate without a human browser session. | OAuth2 Client Credentials Flow is the baseline concept to evaluate. |
| Required | Service access can be restricted by role or permission. | Service accounts should have least-privilege permissions. |
| Expected | Service credentials can be rotated and disabled. | Rotation must account for rollout windows and auditability. |
| Expected | Machine clients are auditable as distinct actors. | Audit logs should distinguish automation from human administrators. |
| Study question | Which client authentication method is appropriate for internal services? | Options may include client secrets, private key JWT, mTLS, or provider-specific mechanisms. |

### Auditability, Governance, and Operations

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Administration operations are auditable. | Audit data should support incident review and access review. |
| Required | Operational complexity is justified by security, compliance, maintainability, or product needs. | A powerful IAM product is not automatically the simplest fit. |
| Expected | Access review is possible from the data model and admin surface. | Engineers should be able to answer who has which role and why. |
| Expected | Secrets, passwords, refresh tokens, and bearer tokens are never logged. | Redaction should apply to logs, traces, analytics, and support tooling. |
| Expected | Key and credential rotation can be performed without breaking all services at once. | This is a core operational requirement for token-based systems. |
| Study question | What audit retention, privacy, and compliance rules apply? | Retention choices should reflect business and legal constraints. |
| Study question | Who owns IAM operations after launch? | Ownership includes onboarding, offboarding, incident response, backups, reviews, and upgrades. |

## Later Evaluation Criteria

Use the detailed [Evaluation Framework](./evaluation-framework.md) for later product-neutral comparison work. The criteria below summarize the main dimensions so these working notes stay useful as a quick requirements map.

Later comparison work should judge self-hosted, managed, minimal-library, and hybrid options against the same criteria. The criteria below are intentionally product-neutral.

| Criterion | What to evaluate |
| --- | --- |
| Requirements coverage | Whether the option supports OAuth2, OIDC, RBAC, admin-only member management, service authentication, admin API needs, and auditability. |
| Security posture | Token validation support, secure defaults, MFA options, secret handling, revocation behavior, admin authorization controls, and exposure to common OAuth2/OIDC mistakes. |
| Operational simplicity | Installation, upgrades, backups, key rotation, monitoring, failure modes, incident response, and day-to-day administration effort. |
| Data and API fit | Whether members, roles, permissions, service accounts, clients, and audit events map cleanly to the project's needs. |
| Maintainability | How understandable the option is for the internal team, including configuration complexity and customization burden. |
| Extensibility | Ability to add roles, services, clients, access checks, and audit workflows without rewriting the core identity system. |
| Cost and lock-in | License, hosting, support, migration path, data export, provider coupling, and long-term ownership. |
| Proof-of-concept value | Which unknowns can be answered with a minimal, non-production PoC if documentation alone is insufficient. |

## Risk Register

| Risk | What can go wrong | Mitigation direction |
| --- | --- | --- |
| Authentication is treated as authorization. | Logged-in users gain access without operation-specific checks. | Separate login from API permissions; enforce authorization on resource servers. |
| Token validation is incomplete. | Tokens from wrong issuers, wrong audiences, expired tokens, or tampered JWTs are accepted. | Validate issuer, audience, lifetime, signature or introspection result, and required permissions. |
| Admin API permissions are too broad. | Read-only administrators can mutate IAM state, or role managers can grant themselves stronger roles. | Use explicit admin permissions and self-escalation controls. |
| JWTs carry stale authorization state. | A removed role remains effective until token expiry. | Prefer short-lived access tokens and define revocation or lookup behavior for high-risk changes. |
| Service accounts reuse human admin roles. | Automation credentials become too powerful and hard to review. | Model service accounts separately with narrow service permissions. |
| Audit logs are incomplete or unsafe. | Incidents cannot be reconstructed, or logs leak secrets and tokens. | Capture useful privileged events while redacting credentials and sensitive token values. |
| Operational ownership is underestimated. | Self-hosted or customized IAM becomes difficult to patch, back up, monitor, or debug. | Include operations in evaluation, not just feature coverage. |
| Scope grows into enterprise IAM by default. | The solution becomes more complex than the expected internal scale requires. | Tie features to concrete backoffice requirements and document why complexity is needed. |

## Open Questions

- Which existing identity systems, directories, or HR sources should be considered authoritative for internal members?
- Are administrators required to use MFA, step-up authentication, or hardware-backed authenticators?
- What are the initial backoffice services and sensitive operations that need permissions?
- What member lifecycle states are required: invited, active, disabled, deleted, suspended, or archived?
- What is the retention policy for disabled or deleted members and audit events?
- Who can create roles, assign roles, create clients, and rotate service credentials?
- Does the backoffice need break-glass administrator access, and how would it be controlled and audited?
- Which service-to-service callers exist today, and which permissions should each have?
- What uptime, backup, recovery, and upgrade expectations apply to the IAM control plane?
- Which unknowns require a minimal PoC, and which can be resolved by documentation and product evaluation?

## Traceability

| Topic | Supporting wiki page |
| --- | --- |
| Product-neutral comparison method | [Evaluation Framework](./evaluation-framework.md) |
| Candidate options for later evaluation | [Candidate Shortlist](./candidate-shortlist.md) |
| Authentication and authorization boundary | [Authentication vs Authorization](./wiki/01-authentication-vs-authorization.md) |
| OAuth2 roles, tokens, and scopes | [OAuth2](./wiki/02-oauth2.md) |
| OIDC login and identity claims | [OpenID Connect](./wiki/03-openid-connect.md) |
| Token validation and JWT trade-offs | [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) |
| RBAC modeling | [RBAC](./wiki/05-rbac.md) |
| Authorization Code with PKCE and Client Credentials | [OAuth2 Flows](./wiki/06-oauth2-flows.md) |
| Machine-to-machine access | [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md) |
| Administration control plane | [Admin API](./wiki/08-admin-api.md) |
| Conservative security practices | [Security Best Practices](./wiki/09-security-best-practices.md) |

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
