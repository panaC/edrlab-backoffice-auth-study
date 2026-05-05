# Internal Backoffice IAM Wiki

This wiki is the Phase 1 documentation for an internal backoffice authorization server study. Its purpose is to build a shared, evidence-backed understanding of identity and access management for the selected Central IAM Control Plane Architecture before any product, vendor, database, hosting, or implementation decision is made.

The audience is senior engineers who understand backend systems, APIs, distributed systems, databases, and general security concepts, but who may not work with IAM, OAuth2, OpenID Connect, JWTs, token validation, or RBAC every day.

This page is the entry point. It introduces the big picture, shows how the main parts interact, and links to the topic pages that will fill in the details.

## Phase 1 boundary

The wiki itself is documentation-only. Phase 1 may also document a minimal PoC plan, and a PoC may be built later if explicitly requested. The study now assumes the Central IAM Control Plane Architecture: a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/admin control plane, and one or more backend API resource servers. The first study and minimal PoC can use one demonstration API resource server. The wiki should explain the concepts and trade-offs needed to evaluate that central IAM component, but it should not recommend a final identity provider product, vendor, hosting model, database, deployment topology, or production implementation.

For this study, the future system is assumed to protect internal backoffice services for fewer than 1,000 users. Public account registration is out of scope. Members are created and managed by administrators. RBAC is required. The goal is to keep the eventual system simple, maintainable, understandable, and operable by the internal team.

## Project big picture

This project is not only about adding a login page. The backoffice needs a controlled way to answer six questions every time a person, application, or service touches protected functionality:

- Who is the actor?
- Which application or service is acting?
- Which API is being called?
- Which operation is being requested?
- Is the actor allowed to do that operation?
- Who changed access, when, and why?

The selected Central IAM Control Plane Architecture exists to keep those answers consistent across the backoffice. Instead of each backend service inventing its own users, roles, tokens, and administrator rules, one central IAM component owns identity, token issuance, roles, permissions, administration, and audit evidence. Backend services still enforce authorization for their own operations, but they do it from a shared trust model.

The future implementation or PoC can be understood as these responsibilities, not as a final product choice:

| Responsibility | Main concept | Why it exists | Example implementation question |
| --- | --- | --- | --- |
| Prove who signed in | Authentication, IdP, OIDC | The system needs a reliable answer to "who is this user?" without every service handling credentials directly. | How does a backoffice member authenticate and receive a verifiable identity result? |
| Keep browser tokens safer | Backoffice BFF | Browsers are a weaker place to store OAuth tokens and refresh tokens. | Should the browser hold only an HttpOnly session cookie while the BFF stores tokens server-side? |
| Issue API access tokens | OAuth2 authorization server | APIs need a standard, verifiable credential for requests instead of trusting arbitrary session or header data. | What issuer, audience, lifetime, scopes, roles, or permissions should access tokens contain? |
| Protect backend APIs | Resource server token validation | A successful login is not enough; each API must verify that the presented token was issued for it and is still valid. | How does each API validate issuer, audience, signature or introspection result, expiry, and required permission? |
| Decide what users may do | Authorization, RBAC, permissions | Different members need different capabilities, and privileged operations need explicit checks. | Which roles and permissions allow actions such as `members:read`, `members:disable`, or `roles:assign`? |
| Manage IAM state | Administration API, control plane | Member creation, role assignment, client configuration, and access removal are privileged system changes. | Which admin endpoints exist, who can call them, and how is self-escalation prevented? |
| Preserve evidence | Audit logs, access reviews | Incidents and reviews require knowing who changed access, what changed, and whether the operation succeeded. | Which admin actions, denied attempts, login events, and access-review records must be retained? |
| Support later machine access | Service clients, Client Credentials Flow | Future backend automation should not pretend to be a human user or reuse broad administrator roles. | If service-to-service access becomes in scope, how are machine clients created, scoped, rotated, disabled, and audited? |

These concepts exist because identity and authorization fail in different ways. Authentication can succeed while authorization should still deny the operation. A valid token can be unsafe if the API skips issuer or audience validation. A role assignment can be technically valid but operationally dangerous if it allows self-escalation. An admin change can be correct but still unacceptable if it leaves no audit evidence. The study keeps the concepts separate so the eventual system can be simple without being vague about security boundaries.

## Page map

| Page | Purpose |
| --- | --- |
| [Authentication vs Authorization](./01-authentication-vs-authorization.md) | Defines the boundary between verifying identity and deciding access. |
| [OAuth2](./02-oauth2.md) | Explains OAuth2 as an authorization framework with clients, resource owners, scopes, access tokens, authorization servers, and resource servers. |
| [OpenID Connect](./03-openid-connect.md) | Explains OIDC as an identity layer on top of OAuth2 for login, ID tokens, user claims, UserInfo, and discovery. |
| [Tokens and JWTs](./04-tokens-and-jwt.md) | Covers access tokens, ID tokens, refresh tokens, JWT structure, claims, signatures, expiration, audiences, issuers, and opaque token trade-offs. |
| [RBAC](./05-rbac.md) | Explains members, users, administrators, roles, permissions, role assignment, permission checks, and how ABAC compares. |
| [OAuth2 Flows](./06-oauth2-flows.md) | Covers Authorization Code Flow, Authorization Code Flow with PKCE, Client Credentials Flow, and Refresh Token Flow. |
| [Service-to-Service Authentication](./07-service-to-service-authentication.md) | Covers future machine-to-machine authentication concepts, service accounts, client credentials, private key JWT, mTLS, and service permissions. |
| [Admin API](./08-admin-api.md) | Covers administrator-only APIs for members, roles, permissions, clients, service accounts, audit logs, and privileged operations. |
| [Security Best Practices](./09-security-best-practices.md) | Summarizes conservative security practices for tokens, secrets, PKCE, validation, least privilege, auditability, rate limiting, and password handling. |
| [Auditability, Access Reviews, and Operational Ownership](./10-auditability-access-reviews-operational-ownership.md) | Covers audit event content, access review workflows, retention, evidence, and operational responsibility boundaries. |
| [MFA, 2FA, Passwordless, and One-Time Passwords](./11-mfa-2fa-passwordless-and-otp.md) | Explains MFA, 2FA, passwordless authentication, OTP families, SMS, email, passkeys, WebAuthn, enrollment, recovery, and step-up trade-offs. |

Related study documents:

- [Administrator Authentication Policy](../administrator-authentication-policy.md)
- [BFF Sessions and Token Handling](../bff-sessions-and-token-handling.md)

## Big-picture model

IAM combines identity, tokens, clients, APIs, and authorization data. The terms are easy to blur, so this wiki keeps them separate:

- **Authentication** verifies who a user, service, or application is.
- **Authorization** decides what an authenticated subject may access.
- A **member** is a company-managed user account.
- A **user** is a human actor using the system.
- An **administrator** is a privileged user who manages IAM data.
- A **client** is an OAuth2/OIDC application registered with the authorization server.
- An **authorization server** issues tokens and runs OAuth2 authorization flows.
- An **identity provider** authenticates users and provides identity information.
- A **BFF**, or Backend-for-Frontend, is a server-side component used by the backoffice UI to hold browser sessions, handle OIDC callbacks, keep tokens server-side, and call the central IAM component and backend APIs.
- A **resource server** is an API or backend service that validates tokens and enforces access control.
- A **role** is a business-level access group, such as `admin`, `support`, `manager`, or `viewer`.
- A **permission** is a granular capability, such as `members:read` or `billing:write`.
- A **scope** is delegated access requested by a client.
- A **claim** is a piece of information inside a token.

OAuth2 and OIDC are related but not the same thing. OAuth2 is about delegated authorization and access tokens. OIDC adds an identity layer for login and ID tokens. A system can use both: OIDC to authenticate the user and OAuth2 access tokens to call protected APIs. See [OAuth2](./02-oauth2.md) and [OpenID Connect](./03-openid-connect.md) for the detailed distinction.

## Conceptual architecture

The diagram below is a vocabulary map for the selected Central IAM Control Plane Architecture, not a final product or deployment design.

```mermaid
flowchart LR
    User["User / Member"]
    Admin["Administrator"]
    Client["Backoffice BFF / Client"]
    AS["Authorization Server / OpenID Provider / Admin Control Plane"]
    ExternalIdP["External Identity Provider (optional)"]
    API["Backoffice Service / Resource Server"]
    AdminAPI["Administration API"]
    Data["IAM Data: members, roles, permissions, clients, service accounts"]
    Service["Backend Service Client"]
    Decision["Token validation and permission check"]

    User --> Client
    Client --> AS
    AS -. "may delegate authentication" .-> ExternalIdP
    AS --> Client
    Client --> API
    API --> Decision
    Decision -. "JWKS, introspection, metadata, or authorization lookup" .-> AS

    Admin --> AdminAPI
    AdminAPI --> AS
    AdminAPI --> Data
    AS --> Data

    Service --> AS
    Service --> API
```

In the selected study shape, the OAuth2 authorization server, OIDC identity provider, and administration control plane are treated as the central IAM component. They may still be implemented by one product, multiple products, a managed provider, a self-hosted product, a library-based service, or a hybrid. Phase 1 does not choose that implementation path.

The key responsibility boundary is that IAM data is managed by the authorization and administration side. A resource server should not need to be the owner of member, role, permission, client, or service account records. It validates tokens and enforces access using trusted token claims, authorization server metadata and keys, token introspection, local policy, or an explicit authorization lookup depending on the eventual design.

## End-to-end login and API flow

A typical internal backoffice login flow looks like this:

```mermaid
sequenceDiagram
    participant User
    participant Client as Backoffice BFF
    participant AS as Authorization Server / IdP
    participant API as Resource Server
    participant Authz as Roles and Permissions

    User->>Client: Open backoffice
    Client->>AS: Start login with authorization request
    User->>AS: Authenticate
    AS->>Client: Return authorization code
    Client->>AS: Exchange code for tokens
    AS->>Client: Return access token and ID token
    Client->>Client: Store tokens or token references server-side
    Client->>API: Call API with bearer access token
    API->>API: Validate token issuer, audience, signature, and expiry
    API->>Authz: Check required role or permission
    Authz->>API: Allow or deny
    API->>Client: Return response or access denied
```

The important separation is that login is not the same as API authorization. A successful login proves the user authenticated. It does not automatically mean the user can read members, update billing data, create clients, or call an administrator-only endpoint. The resource server still needs to validate the access token and enforce the required permission for the requested operation.

The permission check may be based on token claims, local policy configuration, a lookup into IAM data, or a separate authorization service. This wiki entry page names the responsibility without choosing which runtime pattern should be used later.

For browser-based backoffice clients, the modern OAuth2 direction is Authorization Code Flow with PKCE rather than the older Implicit Flow. See [OAuth2 Flows](./06-oauth2-flows.md) and the OAuth2 security best current practice for why token exposure and redirect handling matter.

## Administration flow

Administrators need privileged operations that ordinary members should never receive by accident. The administration API is the management surface for IAM data.

Examples of administration operations include:

- creating, reading, updating, disabling, and deleting members;
- listing members;
- creating and listing roles;
- assigning and removing roles from members;
- managing permissions and clients;
- managing service accounts or machine clients if service-to-service access becomes in scope later;
- checking whether a member has a required role or permission for a backoffice service.

The administration API must itself be protected like any other resource server, with stronger authorization because mistakes have a larger blast radius. Admin endpoints should be checked server-side, audited, rate limited where relevant, and designed so that authorization decisions are explicit rather than implied by frontend UI state.

See [Admin API](./08-admin-api.md) for the dedicated page.

## Future service-to-service flow

Service-to-service authentication is a future theoretical extension for this project, not part of the first study or minimal PoC scope. If later needed, backend services may need to call other internal services without a browser session. In OAuth2 terms, these services can be clients acting on their own behalf, commonly using Client Credentials Flow.

The service receives an access token representing the service client, then calls a resource server. The resource server validates the token and checks service-level permissions. These permissions should be modeled separately enough that a service account does not accidentally inherit broad human administrator privileges.

See [Service-to-Service Authentication](./07-service-to-service-authentication.md) for the dedicated page.

## Common mistakes to avoid

Do not treat authentication as authorization. Knowing that `alice@example.com` logged in is different from knowing that Alice can perform `members:delete`.

Do not treat an ID token as an API access token. ID tokens are for the client to learn authentication and identity information about the user. APIs should validate access tokens intended for them.

Do not rely on frontend-only authorization. Hiding a button in the backoffice UI can improve usability, but the resource server must enforce the rule.

Do not confuse scopes, roles, permissions, and claims. Scopes describe delegated access requested by a client. Roles group business access for members. Permissions describe granular capabilities. Claims are token fields that may carry identity, token metadata, roles, permissions, or other assertions depending on the system.

Do not skip token validation details. A resource server should validate issuer, audience, signature, expiration, and relevant token constraints before trusting token contents. Some systems validate self-contained JWTs locally; others use opaque tokens with introspection. The trade-off belongs in the token page, not in this wiki entry page.

Do not expose administration APIs as ordinary APIs. They change IAM state and should require explicit administrator authorization, audit logging, and conservative operational controls.

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7519 - JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [OWASP API Security](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
