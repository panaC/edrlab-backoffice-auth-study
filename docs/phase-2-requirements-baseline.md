# Phase 2 Requirements Baseline

This document converts the Phase 1 study material into a requirements baseline for Phase 2. It is intended to make later candidate evaluation and Proof-of-Concept planning testable.

This is not a final recommendation and does not choose a vendor, product, database, hosting model, implementation stack, or production architecture. It records what the project currently needs, what is assumed for the first comparison and minimal PoC, what is explicitly future scope, and which decisions still need stakeholder input.

## How to use this baseline

Use this file as the first checkpoint before evaluating a managed provider, self-hosted product, minimal library-based service, or hybrid pattern.

Each candidate evaluation should answer:

- which requirements are satisfied from official documentation;
- which requirements are likely but need a targeted PoC;
- which requirements require custom implementation or operational process;
- which requirements are unsupported or unclear;
- which open decisions materially change the evaluation.

Do not average away a blocker. If a candidate cannot support OIDC login, protected API token validation, administrator-managed members, RBAC, administration API needs, or auditability, record that clearly before assigning broad scores.

## Requirement levels

| Level | Meaning |
| --- | --- |
| Required | Needed to satisfy the current project brief. |
| Expected | Strongly implied by the requirements or by conservative IAM practice, but exact details may be finalized later. |
| Initial baseline | Current working assumption for the first comparison pass or minimal PoC. |
| Future option | Useful for later evolution, but not required for the first study or minimal PoC. |
| Open decision | Must be resolved before a final recommendation or production design. |

## Verification routes

| Route | Meaning |
| --- | --- |
| Documentation evidence | Confirm from official specifications, official product documentation, or existing local study documents. |
| Candidate evaluation | Score in a per-candidate evaluation record using [Evaluation Framework](./evaluation-framework.md). |
| PoC check | Validate with a minimal non-production PoC when documentation is insufficient. |
| Stakeholder decision | Requires project, security, operations, legal, or business input. |
| Not first-PoC scope | Track for future compatibility, but do not implement in the initial PoC. |

## Architecture and scope requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-SCOPE-001 | The study remains limited to internal backoffice IAM. | Required | Prevents accidental expansion into customer identity, social login, broad workforce IAM, or public registration. | [README](../README.md), [Phase 1 working notes](./phase-1-working-notes.md) | Documentation evidence |
| IAM-SCOPE-002 | The selected study shape is the Central IAM Control Plane Architecture: Backoffice BFF, central IdP / authorization server / admin control plane, and backend API resource servers. | Required | Candidate evaluation needs a fixed responsibility boundary. | [README](../README.md), [Architecture notes](./minimal-backoffice-iam-architecture.md) | Documentation evidence |
| IAM-SCOPE-003 | The project focus is the IdP / authorization server / admin control-plane component. | Required | The BFF and resource servers define integration behavior, but are not the main implementation subject. | [README](../README.md), [Architecture notes](./minimal-backoffice-iam-architecture.md) | Documentation evidence |
| IAM-SCOPE-004 | The expected scale is fewer than 1,000 internal users. | Required | Operational complexity must match the actual scale. | [README](../README.md), [Operational Model](./operational-model.md) | Candidate evaluation |
| IAM-SCOPE-005 | The study must compare managed, self-hosted, minimal-library, and hybrid approaches before a final recommendation. | Required | The project outcome is evidence-based comparison, not a predetermined product choice. | [README](../README.md), [Candidate Shortlist](./candidate-shortlist.md) | Candidate evaluation |
| IAM-SCOPE-006 | Service-to-service authentication is a future extension topic, not part of the first study or minimal PoC implementation. | Initial baseline | Keeps the first PoC focused on human backoffice login, RBAC, admin API, audit, and one protected API. | [README](../README.md), [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md) | Not first-PoC scope |

## Identity and member lifecycle requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-ID-001 | Members are created and managed by administrators. | Required | Public self-service registration is out of scope. | [README](../README.md), [Member Lifecycle](./member-lifecycle.md) | Candidate evaluation |
| IAM-ID-002 | Public self-service registration must be disabled, absent, or unreachable in the selected design. | Required | Backoffice membership is an internal administrative process. | [README](../README.md), [Phase 1 working notes](./phase-1-working-notes.md) | Candidate evaluation |
| IAM-ID-003 | Administrators can create, read, update, list, disable, and delete or retain member accounts according to policy. | Required | These operations are minimum administration API capabilities. | [README](../README.md), [Member Lifecycle](./member-lifecycle.md) | Candidate evaluation + PoC check |
| IAM-ID-004 | Member records use stable identifiers separate from mutable attributes such as email and display name. | Expected | Audit history, role assignments, and local resource references must survive profile changes. | [Member Lifecycle](./member-lifecycle.md) | Candidate evaluation + PoC check |
| IAM-ID-005 | Disabled members cannot start new authentication and must not receive new effective access. | Required | Offboarding and incident containment depend on account status having real access effects. | [Member Lifecycle](./member-lifecycle.md), [Threat Model](./threat-model.md) | Candidate evaluation + PoC check |
| IAM-ID-006 | Role assignments can be retained for disabled members for review, but must not produce effective access while the member is non-active. | Expected | Access review needs history without silently preserving access. | [Member Lifecycle](./member-lifecycle.md), [Initial Permission Model](./initial-permission-model.md) | PoC check |
| IAM-ID-007 | The first PoC may use only `active` and `disabled` states unless invitations, archive, or deletion semantics are needed. | Initial baseline | Keeps lifecycle behavior testable without solving retention and recovery policy too early. | [Member Lifecycle](./member-lifecycle.md) | Stakeholder decision + PoC check |
| IAM-ID-008 | Deletion, archive, and retention semantics must be decided before a final recommendation. | Open decision | Hard delete can break audit, recovery, and historical access review. | [Member Lifecycle](./member-lifecycle.md) | Stakeholder decision |

## Authentication and session requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-AUTHN-001 | Backoffice users authenticate through an OIDC-compatible login path. | Required | OIDC is the product-neutral identity contract for the selected architecture. | [README](../README.md), [OpenID Connect](./wiki/03-openid-connect.md) | Candidate evaluation + PoC check |
| IAM-AUTHN-002 | Browser-based login uses Authorization Code Flow with PKCE. | Required | This is the modern browser login baseline; Implicit Flow should not be used for new browser applications. | [OAuth2 Flows](./wiki/06-oauth2-flows.md), [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) | Candidate evaluation + PoC check |
| IAM-AUTHN-003 | Authentication results are separate from API authorization decisions. | Required | A logged-in user is not automatically allowed to call admin APIs or protected services. | [Authentication vs Authorization](./wiki/01-authentication-vs-authorization.md), [Threat Model](./threat-model.md) | PoC check |
| IAM-AUTHN-004 | Administrator authentication must be evaluated as higher risk than ordinary member authentication. | Expected | Administrators can change IAM state and token/client trust boundaries. | [Administrator Authentication Policy](./administrator-authentication-policy.md) | Candidate evaluation |
| IAM-AUTHN-005 | Production administrator MFA, passwordless, and step-up policy remains undecided. | Open decision | Stronger admin authentication may be required, but the final burden depends on risk and operations expectations. | [Administrator Authentication Policy](./administrator-authentication-policy.md) | Stakeholder decision |
| IAM-SESSION-001 | The browser should carry only an opaque BFF session cookie; OAuth access tokens and refresh tokens stay server-side. | Required | Reduces direct token exposure through browser storage and frontend JavaScript. | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) | PoC check |
| IAM-SESSION-002 | BFF session cookies use conservative attributes such as `HttpOnly`, `Secure`, and SameSite where deployment allows. | Expected | Browser sessions are security-sensitive credentials. | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) | PoC check |
| IAM-SESSION-003 | State-changing browser-to-BFF requests use CSRF defenses. | Required | Cookie-based BFF sessions require request-forgery protection. | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md), [Threat Model](./threat-model.md) | PoC check |
| IAM-SESSION-004 | Logout behavior must define local BFF session effects, provider session effects, refresh-token effects, and access-token effects. | Expected | "Logout" can mean different things at different layers. | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) | Candidate evaluation + PoC check |

## Token and API protection requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-TOKEN-001 | Protected APIs receive and validate OAuth2 access tokens. | Required | Resource servers must enforce access independently of frontend UI behavior. | [README](../README.md), [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) | Candidate evaluation + PoC check |
| IAM-TOKEN-002 | Resource servers validate issuer, audience, expiry, and signature or introspection result. | Required | Accepting wrong-issuer, wrong-audience, expired, or tampered tokens is a core IAM failure. | [Threat Model](./threat-model.md), [Security Best Practices](./wiki/09-security-best-practices.md) | PoC check |
| IAM-TOKEN-003 | Access tokens are JWTs for the first study and minimal PoC baseline. | Initial baseline | Gives the first resource-server PoC a concrete validation target. | [Phase 1 working notes](./phase-1-working-notes.md), [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) | PoC check |
| IAM-TOKEN-004 | Access tokens should be short-lived unless a later design documents a specific reason otherwise. | Expected | Short lifetimes reduce bearer-token leakage and stale-permission risk. | [Token Lifecycle](./wiki/12-token-lifecycle.md), [Threat Model](./threat-model.md) | Candidate evaluation |
| IAM-TOKEN-005 | Removed access may expire at access-token expiry in the first version. | Initial baseline | Avoids requiring immediate revocation in the first PoC, while preserving a bounded stale-access window. | [Phase 1 working notes](./phase-1-working-notes.md), [Member Lifecycle](./member-lifecycle.md) | PoC check |
| IAM-TOKEN-006 | High-risk or high-churn authorization may later require introspection, revocation, or runtime authorization lookup. | Future option | Some operations may need faster denial than JWT expiry permits. | [Architecture notes](./minimal-backoffice-iam-architecture.md), [Token Lifecycle](./wiki/12-token-lifecycle.md) | Candidate evaluation |
| IAM-TOKEN-007 | Token values, authorization codes, refresh tokens, passwords, and client secrets must not be logged. | Required | Logs must not become credential stores. | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md), [Operational Model](./operational-model.md) | PoC check |

## RBAC and permission requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-RBAC-001 | The system supports RBAC. | Required | Roles are the project baseline for business-readable access management. | [README](../README.md), [RBAC](./wiki/05-rbac.md) | Candidate evaluation + PoC check |
| IAM-RBAC-002 | Roles can be created, listed, assigned to members, and removed from members. | Required | These are minimum administration API capabilities. | [README](../README.md), [Initial Permission Model](./initial-permission-model.md) | Candidate evaluation + PoC check |
| IAM-RBAC-003 | Sensitive operations use explicit permissions behind roles. | Expected | A single broad admin flag is harder to review and test. | [Initial Permission Model](./initial-permission-model.md) | Candidate evaluation + PoC check |
| IAM-RBAC-004 | The first role model starts with `member` and `admin`. | Initial baseline | Matches the current project brief while leaving room for later role split. | [Phase 1 working notes](./phase-1-working-notes.md), [Initial Permission Model](./initial-permission-model.md) | PoC check |
| IAM-RBAC-005 | The initial `admin` role should grant restrained IAM administration permissions rather than unrestricted bypass authority. | Expected | Small systems still need clear privilege boundaries. | [Initial Permission Model](./initial-permission-model.md), [Threat Model](./threat-model.md) | Candidate evaluation |
| IAM-RBAC-006 | Admin operations prevent self-escalation, over-granting, and disabling the last usable administrator path. | Required | These are common control-plane escalation and lockout failures. | [Initial Permission Model](./initial-permission-model.md), [Threat Model](./threat-model.md) | PoC check |
| IAM-RBAC-007 | Service-account permissions remain distinct from human administrator permissions if service-to-service enters scope later. | Future option | Automation should not inherit broad human privileges by convenience. | [Initial Permission Model](./initial-permission-model.md), [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md) | Not first-PoC scope |

## Administration API requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-ADMIN-001 | The administration API manages members, roles, role assignments, clients, and access checks according to scope. | Required | The central control plane must expose the project's core IAM operations. | [README](../README.md), [Admin API](./wiki/08-admin-api.md) | Candidate evaluation + PoC check |
| IAM-ADMIN-002 | Administration is restricted to internal administrators only. | Required | Member management and role assignment are privileged control-plane functions. | [README](../README.md), [Administrator Authentication Policy](./administrator-authentication-policy.md) | Candidate evaluation + PoC check |
| IAM-ADMIN-003 | The admin API enforces authorization server-side. | Required | UI-only or BFF-only authorization is insufficient. | [Admin API](./wiki/08-admin-api.md), [Threat Model](./threat-model.md) | PoC check |
| IAM-ADMIN-004 | The admin API can check whether a member has access to a given backoffice service. | Required | The project brief requires service access checks. | [README](../README.md), [Initial Permission Model](./initial-permission-model.md) | Candidate evaluation + PoC check |
| IAM-ADMIN-005 | The initial admin API consumer is the backoffice UI through the BFF. | Initial baseline | Avoids introducing machine callers into the initial control-plane surface. | [Phase 1 working notes](./phase-1-working-notes.md), [Admin API](./wiki/08-admin-api.md) | PoC check |
| IAM-ADMIN-006 | Admin mutations should define validation, idempotency, concurrency, and denial behavior. | Expected | Duplicate assignments, racing updates, and invalid transitions should be predictable. | [Admin API](./wiki/08-admin-api.md), [Threat Model](./threat-model.md) | Candidate evaluation + PoC check |

## Audit, governance, and operations requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-AUDIT-001 | Privileged administration operations are auditable. | Required | Incident review and access review require durable evidence. | [README](../README.md), [Auditability, Access Reviews, and Operational Ownership](./wiki/10-auditability-access-reviews-operational-ownership.md) | Candidate evaluation + PoC check |
| IAM-AUDIT-002 | Audit events identify actor, action, target, result, timestamp, and request context where safe. | Expected | These fields are the minimum useful shape for reconstructing privileged changes. | [Member Lifecycle](./member-lifecycle.md), [Initial Permission Model](./initial-permission-model.md) | Candidate evaluation + PoC check |
| IAM-AUDIT-003 | Audit design supports access reviews for administrators, roles, clients, and future service accounts. | Expected | The team must be able to answer who has access and why. | [Operational Model](./operational-model.md), [Auditability, Access Reviews, and Operational Ownership](./wiki/10-auditability-access-reviews-operational-ownership.md) | Candidate evaluation |
| IAM-AUDIT-004 | Audit retention, privacy, and export rules remain undecided. | Open decision | Retention choices depend on business, legal, security, and operations expectations. | [Phase 1 working notes](./phase-1-working-notes.md), [Operational Model](./operational-model.md) | Stakeholder decision |
| IAM-OPS-001 | Operational complexity must be justified by concrete security, compliance, maintainability, or product needs. | Required | A feature-rich IAM system can still be a poor fit if operating it is disproportionate. | [README](../README.md), [Operational Model](./operational-model.md) | Candidate evaluation |
| IAM-OPS-002 | The owning team for IAM operations must be defined before production recommendation. | Open decision | Backups, incident response, upgrades, access reviews, and account recovery need named owners. | [Phase 1 working notes](./phase-1-working-notes.md), [Operational Model](./operational-model.md) | Stakeholder decision |
| IAM-OPS-003 | Candidate evaluation must cover backup, restore, upgrade, migration, monitoring, incident response, and key or credential rotation. | Expected | IAM state and credentials are security-critical. | [Operational Model](./operational-model.md), [Evaluation Framework](./evaluation-framework.md) | Candidate evaluation |
| IAM-OPS-004 | Break-glass access must be either designed with controls or explicitly rejected with accepted risk. | Open decision | Emergency access can prevent lockout, but can also become a permanent bypass. | [Operational Model](./operational-model.md), [Administrator Authentication Policy](./administrator-authentication-policy.md) | Stakeholder decision |

## Candidate evaluation and PoC requirements

| ID | Requirement | Level | Rationale | Source | Verification |
| --- | --- | --- | --- | --- | --- |
| IAM-EVAL-001 | Candidate evaluation uses the same gates and scoring criteria for all comparable options. | Required | Consistency prevents product bias and false precision. | [Evaluation Framework](./evaluation-framework.md) | Candidate evaluation |
| IAM-EVAL-002 | Candidate behavior must be marked as Confirmed, Likely, Inferred, Unknown, or Unsupported. | Required | Security-sensitive assumptions must not be treated as facts. | [Evaluation Framework](./evaluation-framework.md) | Candidate evaluation |
| IAM-EVAL-003 | Product behavior claims should be supported by official documentation, specifications, or targeted PoC evidence. | Required | The study must not rely on marketing language or unsupported assumptions. | [Evaluation Framework](./evaluation-framework.md), [Candidate Shortlist](./candidate-shortlist.md) | Candidate evaluation |
| IAM-EVAL-004 | The candidate shortlist is a starting set, not a final recommendation. | Required | Phase 2 prepares for comparison; it does not select a winner. | [Candidate Shortlist](./candidate-shortlist.md) | Documentation evidence |
| IAM-POC-001 | The first PoC should validate OIDC login, JWT validation, RBAC enforcement, Admin API behavior, audit events, and access expiry against one demonstration API. | Initial baseline | This is the smallest useful cross-boundary check currently identified. | [Phase 1 working notes](./phase-1-working-notes.md), [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) | PoC check |
| IAM-POC-002 | The PoC must remain non-production and scoped to one or two high-value uncertainties unless the phase is explicitly expanded. | Required | Prevents a study PoC from turning into an unreviewed implementation. | [Evaluation Framework](./evaluation-framework.md), [AGENTS](../AGENTS.md) | Documentation evidence |

## Phase 2 open decisions

These decisions are the most useful next targets for Phase 2. They do not need to be solved in this document, but candidate evaluation and PoC planning should not ignore them. Detailed priority and sequencing are tracked in [Phase 2 Open-Question Triage](./phase-2-open-question-triage.md).

| ID | Decision | Why it matters | Suggested next artifact |
| --- | --- | --- | --- |
| P2-Q001 | Which real or representative backoffice service should define the first service-access permissions? | The current docs allow one demonstration API, but service access needs concrete operations to test. | [Service and permission inventory](./phase-2-service-permission-inventory.md) |
| P2-Q002 | What exact permissions should `member` and `admin` have in the first PoC? | The initial permission catalog is intentionally broader than the minimum PoC. | [Service and permission inventory](./phase-2-service-permission-inventory.md) |
| P2-Q003 | Is administrator MFA required for production, and should high-risk actions require step-up? | This affects candidate fit, recovery process, and operational burden. | Administrator authentication decision note |
| P2-Q004 | Which lifecycle states are required in the first PoC and final recommendation? | `active` and `disabled` may be enough initially, but deletion/archive/retention policy affects audit and data model fit. | Lifecycle decision note |
| P2-Q005 | What is the maximum acceptable stale-access window after role removal or member disablement? | JWT-only validation allows stale permissions until token expiry. | Token lifecycle decision note |
| P2-Q006 | Who owns IAM operations after launch? | Self-hosted, managed, and hybrid options have very different ownership costs. | Operational ownership note |
| P2-Q007 | What audit retention, privacy, and export expectations apply? | Audit requirements can disqualify or complicate candidates. | Audit and retention decision note |
| P2-Q008 | Does production require break-glass access? | The design must balance lockout risk against bypass risk. | Break-glass decision note |
| P2-Q009 | Which candidates deserve first evaluation records? | The shortlist is broad; Phase 2 should narrow the first comparison batch. | Candidate evaluation plan |

## Phase 2 exit criteria

Phase 2 should be considered ready to hand off to detailed candidate comparison when:

- required and expected requirements have stable IDs;
- open decisions are either answered or explicitly deferred with impact noted;
- the first demonstration service and minimum permissions are defined;
- the first PoC question set is narrow enough to avoid implementation drift;
- evaluation records can be filled from the same gates and requirements;
- no final product or implementation recommendation has been made prematurely.

## Related documents

- [README](../README.md)
- [Phase 2 Open-Question Triage](./phase-2-open-question-triage.md)
- [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md)
- [Phase 1 working notes](./phase-1-working-notes.md)
- [Minimal Backoffice IAM Architecture Notes](./minimal-backoffice-iam-architecture.md)
- [Member Lifecycle](./member-lifecycle.md)
- [Initial Permission Model](./initial-permission-model.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Operational Model](./operational-model.md)
- [Threat Model](./threat-model.md)
- [Administrator Authentication Policy](./administrator-authentication-policy.md)
- [Evaluation Framework](./evaluation-framework.md)
- [Candidate Shortlist](./candidate-shortlist.md)
