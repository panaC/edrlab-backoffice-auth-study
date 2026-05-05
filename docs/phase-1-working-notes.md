# Phase 1 Working Notes

This work-in-progress document collects Phase 1 requirements, open questions, evaluation notes, and risk notes for later comparison work. The study now selects the Central IAM Control Plane Architecture, but it does not choose a vendor, product, database, hosting model, or implementation approach.

The expected system is an internal backoffice IAM control plane for fewer than 1,000 users. Public registration, customer identity, social login, and broad enterprise IAM complexity are out of scope. Members are created and managed by administrators, RBAC is required, and administration operations must be auditable.

## Selected Architecture Scope

The selected architecture is:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IdP / Authorization Server / Admin Control Plane
    -> one or more backend API resource servers
```

The purpose of this study is the **IdP / Authorization Server / Admin Control Plane** component. The Backoffice BFF, meaning Backend-for-Frontend, backend API services, workers, and service databases are integration context. They define the token, session, administration, and authorization boundaries that the central IAM component must support.

## Current Answered Inputs

The following inputs are now the baseline for the first study and minimal PoC. They narrow earlier open questions without selecting a final vendor, product, database, hosting model, or production implementation.

| Area | Baseline input |
| --- | --- |
| Project scope | The project remains limited to the internal backoffice. Company-wide workforce IAM and broad SSO are not part of the current scope. |
| Member source of truth | Members are created manually by administrators. No HR directory, enterprise directory, or public self-registration source is assumed. |
| Protected API baseline | No real backoffice service inventory is available yet. The first study and PoC can use one demonstration API resource server. |
| RBAC baseline | Keep the first model simple with `admin` and `member` roles and explicit permissions where needed. |
| Administrator authentication | Administrator authentication policy is documented separately in [Administrator Authentication Policy](./administrator-authentication-policy.md). |
| Access removal | For the first version, removed access can expire at access-token expiry rather than requiring immediate revocation. Token lifetimes should stay short. |
| Token format | Use JWT access tokens for the first study and PoC baseline. |
| Admin API consumer | The administration API is consumed only by the backoffice UI through the BFF in the initial scope. |
| Service-to-service access | Service-to-service authentication is a future theoretical extension, not part of the first study or PoC scope. |
| Auditability | Audit expectations are strong and should cover privileged IAM changes and access-review evidence. |
| Operations ownership | The owning team and operating model remain to be defined. |
| PoC scope | The project should plan a minimal PoC across the study scope rather than relying only on documentation. |

## Requirement Levels

| Level | Meaning |
| --- | --- |
| Required | Needed to satisfy the current project brief. |
| Expected | Strongly implied by the requirements or by conservative IAM practice, but details can be finalized later. |
| Initial baseline | Current working assumption for the first study and minimal PoC. |
| Future option | Useful for later evolution, but not required for the first study or minimal PoC. |
| Study question | Must be answered before a final recommendation, but should not be assumed during Phase 1. |

## OAuth2/OIDC Requirement Rationale and Alternatives

The current brief says the authorization server must support "OAuth2 authentication and authorization flows." That wording should be treated carefully. OAuth2 is primarily an authorization framework for obtaining and using access tokens. OpenID Connect (OIDC) is the identity layer on top of OAuth2 that provides user authentication semantics, ID tokens, and standard identity claims.

For this project, the sharper requirement is:

- use OIDC-compatible login for human backoffice users when standardized user authentication is needed;
- use OAuth2-compatible access-token flows when clients, APIs, and services need a standard way to request, receive, validate, and restrict access.

This distinction matters because a logged-in user is not automatically authorized to call a protected backoffice API. The system must still decide whether the actor may perform the requested operation, such as `members:read`, `members:disable`, `roles:assign`, or access to a specific internal service.

### Why OAuth2/OIDC is a reasonable default

OAuth2/OIDC is useful if the backoffice IAM control plane has multiple trust boundaries: a browser client, protected APIs, an administration API, possible future service-to-service callers, and possibly managed or self-hosted IAM products. In that shape, the protocol gives the project a common vocabulary and integration contract:

| Project need | Why OAuth2/OIDC helps |
| --- | --- |
| Browser-based backoffice login | OIDC provides a standard login and identity layer instead of a custom authentication protocol. |
| Protected internal APIs | APIs can receive access tokens and validate issuer, audience, lifetime, signature or introspection result, and required permissions. |
| Multiple resource servers | Each service can enforce access without sharing a web session store or directly handling user credentials. |
| Administration API | Privileged operations can require explicit permissions and can be audited as control-plane changes. |
| Future service-to-service access | OAuth2 Client Credentials Flow gives machine clients a standard model distinct from human users if this becomes in scope later. |
| Candidate comparison | Managed providers, self-hosted products, libraries, and hybrid options can be compared against the same protocol expectations. |

The strongest reason to keep OAuth2/OIDC in the requirements layer is not fashion or user count. It is separation of responsibilities. The authorization server or identity provider authenticates users and issues tokens. Clients use tokens. Resource servers validate tokens and enforce permissions. Administration APIs manage IAM state under stricter authorization and audit controls.

### What OAuth2/OIDC does not solve by itself

OAuth2/OIDC should not be treated as the whole authorization design. The project still needs explicit requirements for:

- member lifecycle states such as active, disabled, deleted, suspended, or archived;
- role and permission modeling;
- which API operations require which permissions;
- whether roles and permissions appear in token claims or are checked through another lookup;
- how quickly removed access must stop working;
- service-account ownership, rotation, disablement, and auditability;
- admin self-escalation controls;
- audit event content, retention, export, and review.

OAuth2 also introduces complexity. The team must understand clients, redirect URIs, token lifetimes, scopes, audiences, issuer validation, signing keys, refresh tokens, revocation or introspection, and failure modes. If those concepts are not actually needed, adopting OAuth2 can make a small internal system harder to operate.

### When OAuth2/OIDC may be overkill

OAuth2/OIDC should be challenged if the real system is only one server-rendered internal application with one backend, one database, and no independent APIs or machine clients. In that narrower design, a traditional server-side session with application-level RBAC might satisfy the business need with less protocol surface.

OAuth2/OIDC is also less compelling if every protected resource is behind a single trusted reverse proxy and the application only needs coarse application-level allow/deny rules. That pattern may be simpler, but it is usually weak for operation-level administration permissions such as role assignment, client creation, or member disablement.

The requirement should therefore not be "use OAuth2 because modern authentication uses OAuth2." It should be "use OAuth2/OIDC where the project needs standardized login, token issuance, token validation, API protection, service clients, and provider interoperability."

### Question: why not just use SSO if none exists today?

Question: If no enterprise SSO exists today, should the project introduce SSO instead of studying an internal backoffice authorization server?

Answer: no existing SSO removes the easy hybrid option of reusing a corporate identity provider. It does not remove the need for standardized authentication, API authorization, member lifecycle management, RBAC, administration controls, auditability, or possible future service authentication.

In this context, SSO is a capability a product or provider may deliver, not a complete replacement for the backoffice IAM control plane. Choosing "SSO" would still mean selecting, subscribing to, or operating an identity provider and deciding where the project owns:

- member creation, disablement, deletion or retention, and recovery;
- roles, permissions, and service access checks;
- access tokens for protected APIs;
- possible future service-to-service credentials and permissions;
- administration APIs and privileged admin authorization;
- audit events for access and control-plane changes.

For Phase 1, the practical answer is:

- do not plan around integration with a non-existent corporate SSO;
- evaluate whether a managed or self-hosted IAM product should become the backoffice's primary identity provider and possibly provide SSO across backoffice applications;
- keep the initial scope as a backoffice IAM control plane, not company-wide workforce IAM, unless stakeholders explicitly expand the scope;
- avoid building username/password, MFA, session, and token behavior from scratch if a maintained product or provider can satisfy the requirements more simply and securely;
- treat future company-wide SSO as a possible expansion path, not as a current assumption.

So the answer to "why don't we use SSO?" is: there is no existing enterprise SSO to reuse, and creating one is itself an IAM product and operations decision. The study should compare managed, self-hosted, library-based, and hybrid options against the project requirements, while recognizing that some options may also provide SSO across multiple internal applications.

### Non-selected narrower option: one backoffice only

Question: If the real scope were a single internal backoffice, what would be the simplest credible solution?

Answer: if there is only one backoffice application, one backend, one database, no independent resource servers, no company-wide SSO, and no complex service-to-service authorization need, the simplest option to evaluate is a conventional application-owned authentication and authorization model:

```text
Backoffice UI + Backend
        |
        | HttpOnly server-side session cookie
        |
Database
  - members
  - roles
  - permissions
  - role_assignments
  - sessions
  - audit_logs
```

In that model:

- administrators create and manage members;
- users authenticate directly with the backoffice;
- the backend creates and validates server-side sessions;
- every protected operation checks permissions server-side;
- role and permission assignments live in the application database;
- privileged changes write audit events;
- the browser does not need to manage access tokens or JWTs.

For example, `POST /members/{id}/disable` should check that the caller is authenticated, active, authorized with a permission such as `members:disable`, blocked from unsafe self-escalation or self-disablement where policy requires it, and recorded in the audit log with actor, action, target, result, timestamp, and request context.

This option is simpler because it avoids operating a separate authorization server, configuring OAuth2 clients, managing redirect URIs, issuing browser access tokens, validating token audiences across services, and handling cross-application SSO.

The trade-off is ownership. The team must own password policy, password storage through a well-maintained framework, account recovery, optional MFA, session security, CSRF protection, lockout or rate-limiting behavior, account disablement semantics, audit log integrity, and administrator access recovery. Those responsibilities should not be underestimated.

This option becomes less attractive if the scope grows to multiple backoffice applications, multiple independently deployed APIs, third-party or managed IdP integration, machine clients, standardized API tokens, or future SSO across internal tools. In that broader shape, an OIDC/OAuth2-capable IdP or authorization server becomes more justified.

This is not the selected architecture anymore. It remains useful as a scope guard: the Central IAM Control Plane Architecture should be justified by a real protected-API boundary, central token issuance, a real admin control-plane need, or future expansion requirements, not by habit.

### Alternatives to evaluate

The alternatives below are not final recommendations. They are design options to challenge against the same requirements.

| Alternative | Where it may fit | Main limitation |
| --- | --- | --- |
| Server-side sessions with application RBAC | A single internal application owns login, session state, roles, permissions, and all protected operations. | Poorer fit for multiple independently deployed APIs, service-to-service callers, and future provider interoperability. |
| New or existing corporate SSO plus local authorization | A workforce identity provider exists or is introduced for login, MFA, and employee lifecycle. | No enterprise SSO exists today, so this option requires adopting or operating an IdP before it can be reused; the project still needs local roles, permissions, admin API behavior, access checks, future service-authentication fit, and audit mapping. |
| Reverse-proxy or gateway authentication | Coarse access to internal web applications is enough. | Usually insufficient for per-operation authorization inside a privileged administration API. |
| API keys or mTLS for services | Machine-to-machine calls are the only problem being solved. | Does not solve human login, delegated user access, role assignment, or member lifecycle. |
| Custom session or JWT token system | The system is small, fully internal, and the team accepts owning security-sensitive token behavior. | Easy to get validation, key rotation, revocation, expiry, audience handling, and incident response wrong. |
| SAML-based SSO | Enterprise login integration is the primary requirement. | Less natural for protecting APIs and service-to-service access than OAuth2/OIDC. |

### Current study position

OAuth2/OIDC should remain in the requirements because the selected Central IAM Control Plane Architecture includes browser login through a Backoffice BFF, protected backend APIs, an administration API, RBAC, managed and self-hosted comparison, later PoC planning, and possible future service-to-service evolution.

The earlier single-application alternative remains documented only as a narrower non-selected shape. The current study should focus on how the central IdP/authorization server/control plane satisfies the selected micro-service architecture without drifting into unnecessary enterprise IAM complexity.

## OIDC Requirement Rationale and Alternatives

OIDC should be analyzed separately from OAuth2 access-token flows. OAuth2 can protect APIs, but it does not by itself define a complete login protocol for the backoffice UI. OIDC adds the standardized identity layer: a client can redirect a user to an OpenID Provider, receive proof that authentication occurred, and obtain identity claims about the signed-in subject.

For this project, OIDC is needed if the backoffice client must rely on an external or centralized identity component for login rather than owning all username, password, MFA, and session behavior locally. OIDC gives the project a standard way to answer:

- who signed in;
- which issuer authenticated the user;
- which client the authentication result was issued for;
- when the authentication result expires;
- which stable subject identifier should be used to link the login to a member record;
- where to discover provider metadata and signing keys.

### Why OIDC is a reasonable default

| Project need | Why OIDC helps |
| --- | --- |
| Standardized user login | The backoffice client can use a well-known login protocol instead of inventing its own authentication exchange. |
| Identity claims | The client can receive a stable subject identifier and basic identity claims in a standard shape. |
| Managed or self-hosted IdP comparison | Providers can be evaluated against the same OIDC expectations: discovery, issuer, clients, redirect handling, ID tokens, and user claims. |
| Corporate identity integration | If a workforce IdP already exists, OIDC can let the project delegate login, MFA, and account authentication to that system. |
| Separation between login and API access | OIDC answers authentication questions, while access tokens and resource-server checks answer API authorization questions. |
| Safer interoperability | OIDC Discovery and provider metadata reduce hardcoded assumptions about endpoints, issuers, and signing keys. |

The main reason to require OIDC is not that every internal app needs federated login. It is that this project is studying an IAM control plane, not a single page with a password form. If the future system may compare managed identity providers, self-hosted identity products, or hybrid models, OIDC is the common identity contract that keeps the login side product-neutral.

### What OIDC does not solve by itself

OIDC should not be mistaken for authorization. An ID token can tell the client that a user authenticated with a provider. It should not be treated as proof that the user may call `POST /members`, assign roles, create service clients, or access a particular backoffice service. Those decisions still belong to the authorization model and must be enforced server-side.

OIDC also does not remove the need to define:

- the source of truth for member records;
- onboarding and offboarding behavior;
- whether email, username, or an immutable provider subject links to the local member;
- role and permission assignment;
- administrator privileges;
- audit events for privileged changes;
- how disabled users lose sessions, refresh tokens, and API access;
- what happens if the identity provider is unavailable.

If the provider manages passwords and MFA, the project may avoid owning those pieces directly. But that moves operational dependency to the provider. The study still needs to understand account recovery, lockout behavior, identity proofing expectations, MFA policy, admin access recovery, outage handling, and export or migration options.

### When OIDC may be unnecessary

OIDC may be unnecessary if the final system is deliberately narrower than the current study scope: one internal server-rendered application, one backend, no separate resource servers, no managed provider comparison, no corporate SSO requirement, and no need for provider interoperability. In that case, server-side sessions with local authentication and RBAC can be simpler.

OIDC may also be unnecessary if login is already handled by a trusted internal gateway that forwards authenticated identity to the application. That can be operationally simple, but the trust boundary becomes the gateway. The application must be sure headers cannot be spoofed, direct access bypasses are blocked, and operation-level authorization still happens inside the API.

SAML can also satisfy enterprise SSO requirements. It may be a better fit where the company's existing identity infrastructure is SAML-first. For this project, the limitation is that SAML mainly addresses login federation; it is less natural than OIDC/OAuth2 for API token validation, service clients, and modern provider/library comparison.

### Alternatives to evaluate

| Alternative | Where it may fit | Main limitation |
| --- | --- | --- |
| Local login with server-side sessions | A small internal monolith owns all authentication and authorization. | The team owns password policy, MFA decisions, account recovery, session security, and offboarding behavior. |
| New or existing SAML-based SSO | A SAML-based workforce identity platform exists or is introduced. | No enterprise SSO exists today, so this requires adopting or operating one; SAML also does not provide the same API-oriented token model as OIDC/OAuth2. |
| Gateway-authenticated identity headers | A trusted reverse proxy or access gateway authenticates users before requests reach the app. | Header spoofing, bypass paths, audit attribution, and operation-level authorization must be controlled carefully. |
| New or existing workforce IdP with OIDC | An OIDC-capable identity provider exists or is introduced. | This still uses OIDC; if introduced for this project, operating or subscribing to the provider becomes part of the scope. |
| Application-specific session bridge over external login | The app exchanges external identity for its own session cookie. | The bridge must define identity linking, session expiry, logout, disablement behavior, and auditability. |

### Current study position

OIDC should remain a requirement because the selected Central IAM Control Plane Architecture needs standardized backoffice login through the BFF, comparison of managed and self-hosted IAM options, possible future SSO expansion, and a clean separation between user authentication and API authorization.

The requirement should still be implemented with restraint. OIDC is the product-neutral login contract for the selected architecture; it is not a reason to add company-wide workforce IAM features that the backoffice does not need.

## Requirements Inventory

### Identity and Member Lifecycle

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Administrators can create, read, update, list, disable, and delete members. | Deletion and disabling should remain distinct because disabling preserves recovery and audit options. |
| Required | Public self-service registration is not supported. | Member onboarding is an internal administrative process. |
| Initial baseline | Members are created manually by administrators. | No external directory, HR source, or public registration flow is assumed for the first study or PoC. |
| Required | Members can receive and lose role assignments. | See [RBAC](./wiki/05-rbac.md) for the role and permission model. |
| Expected | Member records have stable identifiers separate from mutable display attributes. | Email addresses and names can change; audit trails and role assignments need durable references. |
| Expected | Disabled members cannot authenticate or keep using privileged access. | Token lifetime, session handling, and revocation behavior need later design work. |
| Study question | Which member attributes are required beyond identity, status, and role assignments? | Keep attributes minimal unless backoffice workflows require more. |

### Authentication and OIDC

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Backoffice users authenticate through OAuth2/OIDC-compatible login. | OIDC provides the identity layer on top of OAuth2; see [OpenID Connect](./wiki/03-openid-connect.md). |
| Required | Browser-based backoffice clients use Authorization Code Flow with PKCE. | Implicit Flow should not be used for new browser applications. |
| Initial baseline | The project remains limited to backoffice IAM and does not assume company-wide SSO. | A product may support SSO later, but broad workforce IAM is not part of the initial scope. |
| Expected | Authentication results are represented separately from API authorization decisions. | A successful login does not imply access to admin APIs or backoffice services. |
| Expected | Login, session, and token behavior can support account disablement and incident response. | The exact balance among short token lifetimes, refresh tokens, session invalidation, and revocation is a later design topic. |
| Study question | Are MFA, passwordless login, or step-up authentication required for administrators? | See [Administrator Authentication Policy](./administrator-authentication-policy.md). This should be decided from business risk and operational expectations, not assumed from tooling. |

### OAuth2, Tokens, and API Protection

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Protected APIs receive and validate access tokens. | Resource servers need issuer, audience, lifetime, signature or introspection, and authorization checks. |
| Required | Access control works for internal backoffice services. | The authorization model must be enforceable by each protected service. |
| Initial baseline | The first study and PoC use one demonstration API resource server. | There is no confirmed real service inventory yet. |
| Future option | Service-to-service access is a later theoretical extension. | Human and machine clients should still be modeled distinctly if this becomes in scope later. |
| Expected | Access tokens are short-lived unless a later design documents a specific reason otherwise. | Bearer token leakage risk increases with token lifetime. |
| Expected | Token claims, scopes, roles, and permissions are defined with clear responsibilities. | Avoid making one token field carry every authorization concern. |
| Initial baseline | Use JWT access tokens for the first study and PoC. | See [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) for validation rules and trade-offs. |
| Initial baseline | Removed access can expire at token expiry in the first version. | Keep access tokens short-lived; immediate revocation and introspection can be evaluated later if risk requires it. |

### RBAC and Permission Modeling

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | RBAC is supported. | Roles group permissions for business-readable access management. |
| Required | Roles can be created, listed, assigned to members. | These operations are part of the minimum administration API. |
| Expected | Sensitive operations use explicit permissions. | `members:read`, `members:disable`, and `roles:assign` are easier to reason about than a single broad admin flag. |
| Expected | Service permissions are separated from human administrator permissions. | Automation should not inherit broad human privileges by convenience. |
| Initial baseline | Start with `admin` and `member` roles. | This is enough for the first study and PoC; final role design can expand only when concrete workflows require it. |
| Future option | Role hierarchies, resource-level permissions, or ABAC-style rules are not part of the first baseline. | Avoid adding these unless concrete workflows require them. |

### Administration API

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | The administration API manages members, roles, role assignments, and access checks. | See [Admin API](./wiki/08-admin-api.md) for the conceptual control-plane model. |
| Required | Administration is restricted to internal administrators only. | Admin UI checks are not enough; the API must enforce authorization server-side. |
| Required | The API can check whether a member has access to a given backoffice service. | The shape may be an endpoint, library call, policy lookup, or product capability later. |
| Expected | Privileged mutations produce audit events. | Actor, action, target, result, timestamp, and request context are the minimum useful shape. |
| Expected | Admin endpoints prevent self-escalation and privilege grant beyond the actor's authority. | Role assignment and client creation are especially sensitive. |
| Expected | Admin mutations have clear validation, idempotency, and concurrency behavior. | Duplicate role assignment and racing updates should be predictable. |
| Initial baseline | The backoffice UI through the BFF is the only admin API consumer. | Internal automation can be considered later as a separate service-client scope. |

### Future Service-to-Service Authentication

| Level | Requirement | Notes |
| --- | --- | --- |
| Future option | Applications and services may authenticate without a human browser session in a later phase. | OAuth2 Client Credentials Flow remains the baseline concept to understand, but it is not part of the first study or PoC scope. |
| Future option | Service access should be restricted by role or permission if service-to-service becomes in scope. | Service accounts should have least-privilege permissions and should not reuse human admin roles. |
| Future option | Service credentials should be rotatable, disableable, and auditable if added later. | Rotation must account for rollout windows and auditability. |
| Future option | Machine clients should be auditable as distinct actors if added later. | Audit logs should distinguish automation from human administrators. |
| Future option | The service client authentication method remains undecided. | Options may include client secrets, private key JWT, mTLS, or provider-specific mechanisms. |

### Auditability, Governance, and Operations

| Level | Requirement | Notes |
| --- | --- | --- |
| Required | Administration operations are auditable. | Audit data should support incident review and access review. |
| Required | Operational complexity is justified by security, compliance, maintainability, or product needs. | A powerful IAM product is not automatically the simplest fit. |
| Initial baseline | Audit expectations are strong for privileged IAM behavior. | The first study should preserve evidence for member, role, permission, admin, and access-review changes. |
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
| Requirements coverage | Whether the option supports OAuth2, OIDC, RBAC, admin-only member management, protected API access, admin API needs, auditability, and future service-authentication fit. |
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

- Are administrators required to use MFA, step-up authentication, or hardware-backed authenticators in production?
- What exact permissions should the initial `admin` and `member` roles grant in the demonstration API?
- What member lifecycle states are required: invited, active, disabled, deleted, suspended, or archived?
- What is the retention policy for disabled or deleted members and audit events?
- Who can create roles, assign roles, create clients, and, if later in scope, rotate service credentials?
- Does the backoffice need break-glass administrator access, and how would it be controlled and audited?
- What uptime, backup, recovery, and upgrade expectations apply to the IAM control plane?
- Which team owns IAM operations after launch?
- What is the smallest useful PoC that validates OIDC login, JWT validation, RBAC, Admin API behavior, audit events, and access expiry?

## Traceability

| Topic | Supporting wiki page |
| --- | --- |
| Product-neutral comparison method | [Evaluation Framework](./evaluation-framework.md) |
| Candidate options for later evaluation | [Candidate Shortlist](./candidate-shortlist.md) |
| Authentication and authorization boundary | [Authentication vs Authorization](./wiki/01-authentication-vs-authorization.md) |
| OAuth2 roles, tokens, and scopes | [OAuth2](./wiki/02-oauth2.md) |
| OIDC login and identity claims | [OpenID Connect](./wiki/03-openid-connect.md) |
| BFF browser sessions and server-side token handling | [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md) |
| Token validation and JWT trade-offs | [Tokens and JWTs](./wiki/04-tokens-and-jwt.md) |
| RBAC modeling | [RBAC](./wiki/05-rbac.md) |
| Authorization Code with PKCE and Client Credentials | [OAuth2 Flows](./wiki/06-oauth2-flows.md) |
| Future machine-to-machine access | [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md) |
| Administration control plane | [Admin API](./wiki/08-admin-api.md) |
| Conservative security practices | [Security Best Practices](./wiki/09-security-best-practices.md) |
| Administrator authentication policy | [Administrator Authentication Policy](./administrator-authentication-policy.md) |

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
