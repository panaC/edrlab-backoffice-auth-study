# Requirements Baseline

This document is the Phase 2 requirements baseline for the internal backoffice IAM Control Plane study. It consolidates requirements from the project brief and existing study documents. The [Requirements Question Register](./requirements-question-register.md) tracks unresolved decisions, accepted working defaults, and resolution traceability for working documentation.

The baseline is product-neutral. It does not choose a vendor, product, database, hosting model, implementation stack, or final architecture beyond the selected Central IAM Control Plane study architecture.

## Priority meanings

| Priority | Meaning |
| --- | --- |
| `Must` | Required by the project brief or needed to evaluate a first minimal PoC candidate. |
| `Should` | Expected for a credible design or evaluation, but may need a policy decision or candidate-specific evidence. |
| `Future` | Record for later evolution; not part of the first study or minimal PoC scope. |
| `Out of scope` | Explicitly excluded unless the project phase or scope changes. |

## Business and scope requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `BR-001` | Must | The study focuses on the IAM Control Plane: IdP, authorization server, and admin control-plane responsibilities. | [README](../README.md), [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `BR-002` | Must | The system serves internal backoffice users, not public customers or public self-service accounts. | [README](../README.md), [Member lifecycle](./requirements-member-lifecycle.md) |
| `BR-003` | Must | Members are created and managed by internal administrators only. | [README](../README.md), [Member lifecycle](./requirements-member-lifecycle.md) |
| `BR-004` | Must | The study must compare self-hosted, managed, minimal-library, and hybrid solution approaches without making a final recommendation in Phase 2. | [README](../README.md), [Evaluation framework](./evaluation-framework.md) |
| `BR-005` | Must | The expected scale is fewer than 1,000 users, so operational complexity must stay proportionate. | [README](../README.md), [Operational model](./operational-model.md) |
| `BR-006` | Should | Prefer open-source components where relevant, and prefer SQLite for self-hosted options only where realistic and supported. | [README](../README.md) |
| `BR-007` | Out of scope | Public customer identity, public registration, social login, company-wide workforce IAM, and external multi-tenant SaaS identity requirements are not part of the first study. | [README](../README.md) |
| `BR-008` | Out of scope | A production-ready IAM Control Plane is not an expected Phase 2 outcome. | [README](../README.md) |

## Architecture and ownership requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `ARCH-001` | Must | The selected study architecture is a Backoffice BFF, a central IAM Control Plane, and one or more backend API resource servers. | [README](../README.md), [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `ARCH-002` | Must | The IAM Control Plane is the source of truth for members, credentials or external identities, clients, roles, permissions, role assignments, token contracts, key metadata, and IAM audit logs. | [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `ARCH-003` | Must | The Backoffice BFF owns browser sessions and OIDC callback handling, but it must not become a second IAM authority or permanent role database. | [Minimal architecture](./architecture-minimal-backoffice-iam.md), [BFF sessions](./security-bff-sessions-and-token-handling.md) |
| `ARCH-004` | Must | Backend APIs own business logic and data, validate access tokens, and enforce operation-level permissions server-side. | [README](../README.md), [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `ARCH-005` | Must | Backend services must not read the IAM database directly for authorization. They should use token validation, introspection, or a documented authorization/check path. | [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `ARCH-006` | Should | The first minimal PoC may use one demonstration backend API resource server to prove token validation and permission enforcement. | [README](../README.md), [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `ARCH-007` | Future | Service clients and workers should remain distinct from human users if service-to-service authentication becomes in scope later. | [Minimal architecture](./architecture-minimal-backoffice-iam.md), [Initial permission model](./requirements-initial-permission-model.md) |

## Authentication, sessions, and token requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `AUTH-001` | Must | Backoffice users authenticate through OAuth2/OIDC-compatible login. | [README](../README.md), [OAuth2 and OIDC protocol analysis](./architecture-oauth-oidc-protocol-decision-analysis.md) |
| `AUTH-002` | Must | Browser-based backoffice login uses Authorization Code Flow with PKCE through the BFF. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [OAuth2 flows](./wiki/06-oauth2-flows.md) |
| `AUTH-003` | Must | The BFF validates OIDC callback state and ID-token issuer, audience, nonce, signature, and expiry before creating a browser session. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Threat model](./security-threat-model.md) |
| `AUTH-004` | Must | Implicit Flow is not used for new browser-based backoffice applications. | [README](../README.md), [BFF sessions](./security-bff-sessions-and-token-handling.md) |
| `SESS-001` | Must | The browser receives only an opaque, high-entropy, HttpOnly, Secure, SameSite-aware BFF session cookie. | [BFF sessions](./security-bff-sessions-and-token-handling.md) |
| `SESS-002` | Must | OAuth access tokens, refresh tokens, authorization codes, ID tokens, client secrets, passwords, private keys, recovery codes, and raw session IDs are not exposed in browser-readable storage or logs. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Threat model](./security-threat-model.md) |
| `SESS-003` | Should | BFF sessions should have explicit idle timeout, absolute timeout, refresh behavior, logout behavior, and multi-replica storage behavior before production. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Requirements question register](./requirements-question-register.md) |
| `TOKEN-001` | Must | The first study and minimal PoC baseline uses JWT access tokens. | [Token and API access analysis](./architecture-token-and-api-access-decision-analysis.md), [Administrator authentication policy](./security-administrator-authentication-policy.md) |
| `TOKEN-002` | Must | Resource servers validate issuer, audience, expiry, signature or introspection result, and required permissions for every protected API request. | [README](../README.md), [Threat model](./security-threat-model.md) |
| `TOKEN-003` | Should | Access tokens should be short-lived; in the first study baseline, removed access may remain effective only until access-token expiry. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Member lifecycle](./requirements-member-lifecycle.md) |
| `TOKEN-004` | Should | Immediate revocation, token introspection, or runtime authorization lookup should be evaluated when the accepted stale-access window is shorter than access-token lifetime. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Threat model](./security-threat-model.md) |

## Member lifecycle and RBAC requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `MEM-001` | Must | Administrators can create, read, update, list, disable, delete or retain, restore where policy allows, and remove access for members. | [README](../README.md), [Member lifecycle](./requirements-member-lifecycle.md) |
| `MEM-002` | Must | Member records use stable identifiers separate from mutable attributes such as email, username, display name, title, or department. | [Member lifecycle](./requirements-member-lifecycle.md) |
| `MEM-003` | Must | Non-active members cannot obtain new effective backoffice access. | [Member lifecycle](./requirements-member-lifecycle.md), [Threat model](./security-threat-model.md) |
| `MEM-004` | Should | The first baseline treats `active` and `disabled` as the required lifecycle states; `invited`, `archived`, `deleted`, and `suspended` remain policy decisions. | [Member lifecycle](./requirements-member-lifecycle.md), [Requirements question register](./requirements-question-register.md) |
| `MEM-005` | Should | Member recovery, authenticator reset, MFA reset, and email changes are sensitive lifecycle operations with explicit authorization and audit behavior. | [Member lifecycle](./requirements-member-lifecycle.md), [Administrator authentication policy](./security-administrator-authentication-policy.md) |
| `RBAC-001` | Must | RBAC is required for backoffice access management. | [README](../README.md), [Initial permission model](./requirements-initial-permission-model.md) |
| `RBAC-002` | Must | Roles can be created, listed, assigned to members, and removed from members. | [README](../README.md), [Initial permission model](./requirements-initial-permission-model.md) |
| `RBAC-003` | Must | The initial role baseline includes `admin` and `member`. | [README](../README.md), [Initial permission model](./requirements-initial-permission-model.md) |
| `RBAC-004` | Should | Sensitive operations use explicit permissions, such as `members:read`, `members:disable`, `roles:assign`, and `authorization:check`, rather than one broad admin flag. | [Initial permission model](./requirements-initial-permission-model.md) |
| `RBAC-005` | Should | Role assignment and role-definition changes prevent self-escalation, over-granting, and disabling or deleting the last usable administrator path. | [Initial permission model](./requirements-initial-permission-model.md), [Threat model](./security-threat-model.md) |
| `RBAC-006` | Future | Role hierarchies, ABAC, relationship-based authorization, separate policy engines, and resource-level permissions are later study topics unless concrete workflows require them. | [Initial permission model](./requirements-initial-permission-model.md), [Authorization models](./wiki/18-authorization-models.md) |

## Administration API and access-check requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `API-001` | Must | The IAM Control Plane exposes or supports a REST administration API for members, roles, permissions, role assignments, clients where relevant, service access, and audit-supporting operations. | [README](../README.md), [Minimal architecture](./architecture-minimal-backoffice-iam.md) |
| `API-002` | Must | Administration is restricted to internal administrators and enforced server-side by the IAM Control Plane, not only by the UI or BFF. | [README](../README.md), [Administrator authentication policy](./security-administrator-authentication-policy.md) |
| `API-003` | Must | The minimum administration API supports creating, reading, updating, disabling or deleting members; creating roles; assigning and removing roles; listing roles; listing members; and checking access to a given backoffice service. | [README](../README.md) |
| `API-004` | Must | The system can answer whether a member has access to a representative backoffice service or operation. | [README](../README.md), [Evaluation framework](./evaluation-framework.md) |
| `API-005` | Should | Admin mutations have documented validation, idempotency, concurrency behavior, and safe error behavior. | [Initial permission model](./requirements-initial-permission-model.md) |
| `API-006` | Should | The first baseline treats the Backoffice UI through the BFF as the only admin API consumer; machine callers are later service-client scope. | [Central IAM Control Plane analysis](./architecture-central-iam-control-plane-decision-analysis.md), [Administrator authentication policy](./security-administrator-authentication-policy.md) |
| `API-007` | Should | Client management, redirect URI changes, client secret rotation, and client disablement are treated as sensitive admin operations where the chosen candidate exposes them to this project. | [Initial permission model](./requirements-initial-permission-model.md), [Threat model](./security-threat-model.md) |

## Security, audit, and operational requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `SEC-001` | Must | The design does not rely on custom cryptography, unsigned JWTs, skipped issuer validation, skipped audience validation, frontend-only authorization checks, or long-lived access tokens without justification. | [Threat model](./security-threat-model.md), [Security best practices](./wiki/09-security-best-practices.md) |
| `SEC-002` | Must | Cookie-authenticated BFF routes use CSRF defenses for state-changing requests. | [BFF sessions](./security-bff-sessions-and-token-handling.md), [Threat model](./security-threat-model.md) |
| `SEC-003` | Must | OAuth clients use exact redirect URI registration, environment separation, and audited redirect/client changes where applicable. | [Threat model](./security-threat-model.md), [Initial permission model](./requirements-initial-permission-model.md) |
| `SEC-004` | Should | Administrator authentication strength, including MFA, step-up, passwordless options, hardware-backed authenticators, and recovery controls, is evaluated before production. | [Administrator authentication policy](./security-administrator-authentication-policy.md), [Requirements question register](./requirements-question-register.md) |
| `AUD-001` | Must | Privileged administration operations are auditable with actor, action, target, result, timestamp, and safe request context. | [README](../README.md), [Initial permission model](./requirements-initial-permission-model.md) |
| `AUD-002` | Must | Logs and audit records do not expose passwords, bearer tokens, refresh tokens, authorization codes, client secrets, private keys, recovery material, or raw session IDs. | [Initial permission model](./requirements-initial-permission-model.md), [Evaluation framework](./evaluation-framework.md) |
| `AUD-003` | Should | Audit events cover member creation/update/disable/restore, role assignment/removal, role changes, client changes, authorization denials, audit reads/exports, and recovery or authenticator reset. | [Initial permission model](./requirements-initial-permission-model.md), [Member lifecycle](./requirements-member-lifecycle.md) |
| `AUD-004` | Should | Access review is possible from the member, role, permission, assignment, client, and audit surfaces. | [Initial permission model](./requirements-initial-permission-model.md), [Operational model](./operational-model.md) |
| `OPS-001` | Must | Operational ownership for the IAM Control Plane is named before production. | [Operational model](./operational-model.md), [Requirements question register](./requirements-question-register.md) |
| `OPS-002` | Must | Operational complexity is justified by concrete security, compliance, maintainability, or product needs. | [README](../README.md), [Evaluation framework](./evaluation-framework.md) |
| `OPS-003` | Should | Backup and restore expectations cover member data, authorization data, client metadata, configuration, signing key metadata, and audit logs. | [Operational model](./operational-model.md) |
| `OPS-004` | Should | Key, client-secret, credential, and backup-key rotation procedures are documented before production. | [Operational model](./operational-model.md), [Threat model](./security-threat-model.md) |
| `OPS-005` | Should | Monitoring and incident-response playbooks cover token theft, refresh-token theft, client secret leaks, signing-key compromise, compromised administrators, bad role assignments, audience-validation failures, provider outage, and audit failure. | [Operational model](./operational-model.md), [Threat model](./security-threat-model.md) |
| `OPS-006` | Should | The project explicitly accepts, rejects, or defines break-glass access before production. | [Operational model](./operational-model.md), [Administrator authentication policy](./security-administrator-authentication-policy.md) |

## Evaluation-readiness requirements

| ID | Priority | Requirement | Source |
| --- | --- | --- | --- |
| `EVAL-001` | Must | Candidate evaluation uses the product-neutral gates in the evaluation framework before detailed comparison. | [Evaluation framework](./evaluation-framework.md) |
| `EVAL-002` | Must | Gate status values are `OK`, `KO`, or `Unknown`; `Unknown` is not treated as a pass. | [Evaluation framework](./evaluation-framework.md) |
| `EVAL-003` | Must | Candidate evidence comes from official documentation, standards, reputable security guidance, or targeted PoCs for unresolved security-sensitive behavior. | [Evaluation framework](./evaluation-framework.md) |
| `EVAL-004` | Must | Candidate comparison remains neutral in Phase 2 and does not produce a final vendor, product, architecture, hosting, or stack recommendation. | [README](../README.md), [Evaluation framework](./evaluation-framework.md) |
| `EVAL-005` | Should | Targeted PoCs answer one or two high-value uncertainties, such as OIDC login through the BFF, resource-server token validation, member disablement and role-removal latency, admin API coverage, audit event quality, secret redaction, or self-hosted operations ambiguity. | [Evaluation framework](./evaluation-framework.md), [BFF sessions](./security-bff-sessions-and-token-handling.md) |
| `EVAL-006` | Future | Service-to-service authentication fit is recorded as an evolution note, not a first-PoC blocker unless the project explicitly changes scope. | [README](../README.md), [Evaluation framework](./evaluation-framework.md) |

## Evaluation gate traceability

| Evaluation gate | Requirement IDs |
| --- | --- |
| OIDC login | `AUTH-001`, `AUTH-002`, `AUTH-003`, `AUTH-004` |
| Browser session boundary | `ARCH-003`, `SESS-001`, `SESS-002`, `SESS-003`, `SEC-002` |
| API token validation | `ARCH-004`, `TOKEN-001`, `TOKEN-002`, `TOKEN-003`, `TOKEN-004` |
| OAuth client safety | `SEC-003`, `API-007`, `OPS-004` |
| Admin-managed members | `BR-003`, `MEM-001`, `MEM-002`, `MEM-003`, `MEM-004`, `MEM-005` |
| No public registration | `BR-002`, `BR-003`, `BR-007` |
| RBAC and permissions | `RBAC-001`, `RBAC-002`, `RBAC-003`, `RBAC-004`, `RBAC-005` |
| Administration API fit and guardrails | `API-001`, `API-002`, `API-003`, `API-005`, `API-006`, `RBAC-005` |
| Access checks | `API-004`, `ARCH-004`, `TOKEN-002` |
| Auditability | `AUD-001`, `AUD-003`, `AUD-004` |
| Secret redaction | `SESS-002`, `AUD-002` |
| Operational fit | `BR-005`, `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006` |
| Custom work boundary | `BR-008`, `SEC-001`, `EVAL-003`, `EVAL-004` |
| Future evolution checks | `ARCH-007`, `RBAC-006`, `EVAL-006` |

## References

- [Project README](../README.md)
- [Requirements Question Register](./requirements-question-register.md)
- [Minimal Backoffice IAM Architecture Notes](./architecture-minimal-backoffice-iam.md)
- [BFF Sessions and Token Handling](./security-bff-sessions-and-token-handling.md)
- [Member Lifecycle](./requirements-member-lifecycle.md)
- [Initial Permission Model](./requirements-initial-permission-model.md)
- [Operational Model](./operational-model.md)
- [Threat Model](./security-threat-model.md)
- [Administrator Authentication Policy](./security-administrator-authentication-policy.md)
- [Evaluation Framework](./evaluation-framework.md)
- [OAuth2](./wiki/02-oauth2.md)
- [OpenID Connect](./wiki/03-openid-connect.md)
- [OAuth2 Flows](./wiki/06-oauth2-flows.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [RBAC](./wiki/05-rbac.md)
- [Administration APIs](./wiki/08-admin-api.md)
- [Security Best Practices](./wiki/09-security-best-practices.md)
