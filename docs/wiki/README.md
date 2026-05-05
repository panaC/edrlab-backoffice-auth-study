# Internal Backoffice IAM Wiki

This wiki is the conceptual IAM reference for the internal backoffice IAM Control Plane study. It explains vocabulary, protocols, authorization, security, operations, and industry architecture patterns without choosing a vendor, product, hosting model, database, or final architecture.

## Reading Path

Read the wiki in this order if you want the domain to build progressively.

### 1. Build the mental model

1. [IAM Architecture](./15-iam-architecture.md)
2. [IAM Control Plane vs Data Plane](./14-iam-control-plane-vs-data-plane.md)
3. [IAM Responsibility Model](./16-iam-responsibility-model.md)
4. [IAM Data Model](./22-iam-data-model.md)
5. [Authentication vs Authorization](./01-authentication-vs-authorization.md)

### 2. Learn the protocol foundation

1. [OAuth2](./02-oauth2.md)
2. [OpenID Connect](./03-openid-connect.md)
3. [OAuth2 Flows](./06-oauth2-flows.md)
4. [Web Sessions, Cookies, and BFF Pattern](./24-web-sessions-cookies-and-bff.md)
5. [Tokens and JWTs](./04-tokens-and-jwt.md)
6. [Token Lifecycle](./12-token-lifecycle.md)
7. [OAuth Client Management](./13-oauth-client-management.md)
8. [Key Management and Signing Keys](./23-key-management-and-signing-keys.md)

### 3. Learn authorization and enforcement

1. [RBAC](./05-rbac.md)
2. [Authorization Models](./18-authorization-models.md)
3. [PDP, PEP, PIP, and PAP](./17-pdp-pep-pip-pap.md)
4. [Policy Engines and Fine-Grained Authorization](./21-policy-engines-and-fine-grained-authorization.md)
5. [Admin API](./08-admin-api.md)
6. [Service-to-Service Authentication](./07-service-to-service-authentication.md)

### 4. Learn identity lifecycle and enterprise integration

1. [MFA, 2FA, Passwordless, and One-Time Passwords](./11-mfa-2fa-passwordless-and-otp.md)
2. [Federation and Enterprise SSO](./19-federation-and-enterprise-sso.md)
3. [Identity Provisioning and SCIM](./20-identity-provisioning-and-scim.md)
4. [Auditability, Access Reviews, and Operational Ownership](./10-auditability-access-reviews-operational-ownership.md)

### 5. Read the security baseline

1. [Security Best Practices](./09-security-best-practices.md)

## Page Map

| Page | Read when you need to answer |
| --- | --- |
| [01 - Authentication vs Authorization](./01-authentication-vs-authorization.md) | What is the difference between proving identity and deciding access? |
| [02 - OAuth2](./02-oauth2.md) | What is OAuth2, and what are authorization servers, clients, scopes, resource owners, and resource servers? |
| [03 - OpenID Connect](./03-openid-connect.md) | How does OIDC add login and identity information on top of OAuth2? |
| [04 - Tokens and JWTs](./04-tokens-and-jwt.md) | What are access tokens, ID tokens, refresh tokens, JWTs, claims, signatures, issuers, and audiences? |
| [05 - RBAC](./05-rbac.md) | How should members, roles, permissions, assignments, and operation-level checks be modeled? |
| [06 - OAuth2 Flows](./06-oauth2-flows.md) | Which OAuth2/OIDC flows matter for browser login, BFFs, refresh, and service clients? |
| [07 - Service-to-Service Authentication](./07-service-to-service-authentication.md) | How should future machine clients and service accounts authenticate without pretending to be users? |
| [08 - Admin API](./08-admin-api.md) | What makes an IAM administration API high risk, and how should privileged mutations be controlled? |
| [09 - Security Best Practices](./09-security-best-practices.md) | What conservative security rules should guide the whole IAM design? |
| [10 - Auditability, Access Reviews, and Operational Ownership](./10-auditability-access-reviews-operational-ownership.md) | What evidence and operating model are needed to explain, review, and recover from IAM changes? |
| [11 - MFA, 2FA, Passwordless, and One-Time Passwords](./11-mfa-2fa-passwordless-and-otp.md) | How should stronger authentication, OTP, passkeys, recovery, and step-up be understood? |
| [12 - Token Lifecycle](./12-token-lifecycle.md) | How do issuance, storage, validation, refresh, revocation, logout, key rotation, and stale access fit together? |
| [13 - OAuth Client Management](./13-oauth-client-management.md) | How should OAuth2/OIDC clients, redirect URIs, grants, secrets, keys, and lifecycle be governed? |
| [14 - IAM Control Plane vs Data Plane](./14-iam-control-plane-vs-data-plane.md) | What belongs in the IAM Control Plane, what belongs in runtime enforcement, and what root problems does the split solve? |
| [15 - IAM Architecture](./15-iam-architecture.md) | What is the overall industry map across identity platforms, cloud IAM, self-hosted IdPs, libraries, policy engines, and hybrid systems? |
| [16 - IAM Responsibility Model](./16-iam-responsibility-model.md) | Which component or team owns each IAM responsibility, and where do provider boundaries end? |
| [17 - PDP, PEP, PIP, and PAP](./17-pdp-pep-pip-pap.md) | Where are policies authored, decisions made, attributes sourced, and decisions enforced? |
| [18 - Authorization Models](./18-authorization-models.md) | How do RBAC, ABAC, ReBAC, ACLs, scopes, claims, entitlements, and policy engines compare? |
| [19 - Federation and Enterprise SSO](./19-federation-and-enterprise-sso.md) | What does enterprise SSO solve, how do OIDC and SAML fit, and what remains local to the app? |
| [20 - Identity Provisioning and SCIM](./20-identity-provisioning-and-scim.md) | How are users and groups created, updated, disabled, synchronized, and deprovisioned across systems? |
| [21 - Policy Engines and Fine-Grained Authorization](./21-policy-engines-and-fine-grained-authorization.md) | How do OPA, Cedar, Verified Permissions, OpenFGA, SpiceDB, and Zanzibar-style systems solve detailed authorization problems? |
| [22 - IAM Data Model](./22-iam-data-model.md) | What are principals, subjects, users, members, identities, accounts, groups, roles, permissions, clients, service accounts, tenants, and organizations? |
| [23 - Key Management and Signing Keys](./23-key-management-and-signing-keys.md) | How do JWKS, signing keys, key rotation, client secrets, private key JWT, mTLS, certificates, and secret storage fit IAM? |
| [24 - Web Sessions, Cookies, and BFF Pattern](./24-web-sessions-cookies-and-bff.md) | How do browser sessions, cookies, CSRF, browser token storage, refresh tokens, and the BFF pattern work? |

## Vocabulary

| Term | Short meaning |
| --- | --- |
| Authentication | Verifies who a user, service, or application is. |
| Authorization | Decides what an authenticated subject may access. |
| Member | Company-managed human account in the backoffice IAM domain. |
| Administrator | Privileged member who can manage IAM data. |
| Client | OAuth2/OIDC application registered with the authorization server. |
| Identity provider | Authenticates users and provides identity information. |
| Authorization server | Issues OAuth2 access tokens and runs authorization flows. |
| IAM Control Plane | Study shorthand for the central IdP / Authorization Server / Admin Control Plane. |
| BFF | Backend-for-Frontend that holds browser sessions and handles OIDC callbacks server-side. |
| Resource server | Protected API that validates tokens and enforces access. |
| Session | Continuity state for a browser or user interaction. |
| Signing key | Key used by an issuer to sign tokens. |
| JWKS | Public key set used by resource servers and clients to verify JWT signatures. |
| Role | Business-level access group. |
| Permission | Granular capability such as `members:read` or `roles:assign`. |
| Scope | OAuth2 delegated access requested by a client. |
| Claim | Token field carrying an assertion after token validation. |
| PDP | Policy Decision Point. |
| PEP | Policy Enforcement Point. |
| PIP | Policy Information Point. |
| PAP | Policy Administration Point. |

## How Pages Connect

| If a page mentions | Go to |
| --- | --- |
| OAuth2, scopes, authorization server, client | [OAuth2](./02-oauth2.md) |
| OIDC, ID token, UserInfo, discovery | [OpenID Connect](./03-openid-connect.md) |
| JWT, issuer, audience, claim, signature | [Tokens and JWTs](./04-tokens-and-jwt.md) |
| Authorization Code Flow, PKCE, refresh tokens, client credentials | [OAuth2 Flows](./06-oauth2-flows.md) |
| Token expiry, revocation, introspection, JWKS, logout | [Token Lifecycle](./12-token-lifecycle.md) |
| Signing keys, JWKS, `kid`, client secrets, private key JWT, mTLS | [Key Management and Signing Keys](./23-key-management-and-signing-keys.md) |
| Cookies, browser sessions, CSRF, BFF, browser token storage | [Web Sessions, Cookies, and BFF Pattern](./24-web-sessions-cookies-and-bff.md) |
| Principals, subjects, members, identities, accounts, tenants | [IAM Data Model](./22-iam-data-model.md) |
| Roles, permissions, assignments | [RBAC](./05-rbac.md) and [Authorization Models](./18-authorization-models.md) |
| PEP, PDP, PIP, PAP, policy engine | [PDP, PEP, PIP, and PAP](./17-pdp-pep-pip-pap.md) and [Policy Engines and Fine-Grained Authorization](./21-policy-engines-and-fine-grained-authorization.md) |
| Admin operations, IAM mutations, privileged API | [Admin API](./08-admin-api.md) |
| Service accounts or machine clients | [Service-to-Service Authentication](./07-service-to-service-authentication.md) |
| SSO, SAML, external IdP, identity broker | [Federation and Enterprise SSO](./19-federation-and-enterprise-sso.md) |
| Provisioning, deprovisioning, groups, SCIM | [Identity Provisioning and SCIM](./20-identity-provisioning-and-scim.md) |
| Audit logs, access reviews, operations, ownership | [Auditability, Access Reviews, and Operational Ownership](./10-auditability-access-reviews-operational-ownership.md) |
