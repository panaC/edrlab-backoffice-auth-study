# Candidate Shortlist

This document identifies candidate IAM approaches for later evaluation using the [Evaluation Framework](./evaluation-framework.md).

The project now uses the Central IAM Control Plane Architecture as the study scope: a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/admin control plane, and multiple backend API resource servers. This document does not choose a vendor, product, database, hosting model, or implementation approach. Its purpose is to compare ways to realize the central IdP/authorization server/admin control-plane component.

Evaluation date: 2026-05-04.

## Selection logic

The first shortlist should cover four shapes:

- managed identity providers, to understand what can be delegated to a service;
- self-hosted open-source IAM products, to understand operational burden and control;
- minimal library-based internal services, to understand the cost of owning more IAM behavior directly;
- hybrid approaches, to understand whether splitting authentication, authorization, and administration reduces complexity or merely moves it.

Each candidate must be checked against the project gates:

- OAuth2 and OIDC support;
- Authorization Code Flow with PKCE for browser-based backoffice clients;
- service-to-service authentication;
- administrator-managed members with no public registration requirement;
- RBAC or an equivalent role/permission model;
- protected API token validation and operation-level authorization;
- REST administration API fit;
- auditability;
- operational simplicity for fewer than 1,000 internal users.

## Managed provider candidates

Managed providers reduce infrastructure ownership, but they may introduce tenant configuration complexity, provider-specific APIs, pricing thresholds, data-export concerns, and lock-in. These options should be evaluated only from official documentation and, where useful, a small configuration PoC.

| Candidate | Why evaluate | First unknowns |
| --- | --- | --- |
| Auth0 by Okta | App-centric managed OAuth2/OIDC provider with documented Authorization Code with PKCE, Client Credentials Flow, Management API, and API RBAC features. | Whether Auth0's RBAC, Management API, audit/event model, service accounts, and pricing fit an internal admin-only backoffice with fewer than 1,000 users. |
| Clerk | Managed authentication and user management platform with embeddable UIs, Backend API, Organizations roles and permissions, session JWTs/JWKS, OAuth/OIDC provider support, and machine authentication tokens. | Whether Clerk's OAuth/OIDC provider and session-token model can serve protected internal APIs with the required audience/scope semantics, whether organization-scoped roles fit non-tenant backoffice RBAC, and whether admin-only lifecycle, audit/export, and no-self-hosting constraints are acceptable. |
| Okta | Workforce-oriented identity platform with OIDC/OAuth2, scoped OAuth access to Okta management APIs, admin roles, custom roles, service apps, and system logs. | Whether Okta's admin-role and group model maps cleanly to application permissions and whether the project wants a workforce IdP dependency rather than an app-local IAM surface. |
| Microsoft Entra ID | Strong candidate if the company already uses Microsoft identity. Microsoft Graph can manage users, applications, service principals, groups, and app roles. | Whether app roles, groups, Graph permissions, audit logs, and tenant administration provide a simple enough model for the backoffice's own member and permission semantics. |
| Amazon Cognito User Pools | Managed AWS-native user directory and OIDC IdP with user-pool APIs, groups, resource servers, custom scopes, and Client Credentials support for machine identities. | Whether Cognito's group/scope model, IAM-authorized admin APIs, hosted login behavior, and audit story are ergonomic for internal administrator-only backoffice access. |
| ZITADEL Cloud | Managed version of a product that also supports self-hosting. Official docs show OIDC/OAuth standards, management APIs, service accounts, project roles, and audit-oriented event concepts. | Whether its organization/project/user-grant model is simple for this project and whether Cloud vs self-hosted behavior changes admin API, data export, or operations assumptions. |
| Cloud-IAM managed Keycloak | Managed Keycloak hosting with dedicated paid deployments, shared free-tier realm option, full native Keycloak Admin REST API access, managed upgrades, backups, observability, support, and SLA tiers. | Whether a managed Keycloak service gives enough operational relief while preserving the Keycloak model, and which plan-level limits, RPO/RTO, region, extension, audit, export, and support constraints matter for the backoffice. |
| Hanko Cloud | Managed authentication and user management platform with hosted Hanko backend, passkeys, passwords, MFA, SAML enterprise SSO, OAuth/OIDC social connections, session JWTs, Admin API, and analytics. | Whether Hanko can act as the OAuth2/OIDC authorization server for protected APIs, supports Client Credentials and API audience/scope semantics, and has mature roles/permissions for backoffice RBAC. |

## Self-hosted product candidates

Self-hosted products increase control and reduce some vendor lock-in, but they move upgrades, backups, key rotation, incident response, monitoring, and database operations onto the internal team.

| Candidate | Why evaluate | First unknowns |
| --- | --- | --- |
| Keycloak | Mature open-source IAM product with OIDC/OAuth2, users, realms, clients, roles, groups, admin console, and Admin REST API. | Operational weight for fewer than 1,000 users, supported database choices, admin API fit, audit event coverage, and whether lack of production SQLite support is acceptable. |
| ZITADEL self-hosted | Open-source/self-hostable IAM product with OIDC/OAuth standards, management APIs, machine users, project roles, and PostgreSQL-oriented deployment docs. | Operational complexity, PostgreSQL requirement, upgrade process, local team familiarity, and whether its model maps cleanly to member lifecycle and access checks. |
| authentik | Open-source identity provider with OIDC/OAuth2 providers, users, groups, roles, policy concepts, OpenAPI-based API surface, PostgreSQL, and Redis. | Whether it is a clean authorization server fit rather than mainly an identity/application access gateway, and whether roles/groups and API permissions map to backoffice service permissions. |
| Authelia | Open-source authentication and authorization server, OpenID Certified OIDC provider, and reverse-proxy companion with MFA, passkeys, file or LDAP authentication backends, access-control rules, OAuth2 bearer token support, and Client Credentials support. | Whether Authelia can satisfy the control-plane requirements rather than only gateway authorization: administrator-managed users, role/permission administration, REST admin API shape, auditability of privileged mutations, and operational fit outside a reverse-proxy-centric model. |
| Hanko self-hosted | Open-source authentication and user management system with a self-hosting path, Hanko backend, Hanko Elements, passkeys, session JWTs, Admin API, and cloud-to-self-host migration story. | Production deployment, database, backup, and upgrade requirements; self-hosted feature parity for Admin API, audit logs, SAML, and metrics; and the same OAuth2 authorization-server, Client Credentials, and RBAC gates as Hanko Cloud. |
| Ory open-source stack | Modular OSS components: Hydra for OAuth2/OIDC, Kratos for identity management, and Keto/Ory Permissions for authorization. | Whether assembling multiple components creates more custom integration than the project wants, especially for admin API shape, member lifecycle, RBAC, and auditability. |

## Minimal library-based candidates

These are not complete products. They are frameworks for building an authorization server or OIDC provider. They may fit only if the team explicitly accepts owning the surrounding IAM behavior: member lifecycle, administration API, RBAC, audit logs, credential lifecycle, user sessions, password policy, MFA, revocation, and operations.

| Candidate | Why evaluate | First unknowns |
| --- | --- | --- |
| Spring Authorization Server | Java/Spring framework implementing OAuth2/OIDC authorization server capabilities, including Authorization Code, Client Credentials, Refresh Token, token introspection, revocation, JWKS, metadata, and PKCE support. | Whether the team wants to own identity storage, admin APIs, RBAC, sessions, audit logs, and operational hardening around the protocol engine. |
| OpenIddict | .NET OAuth2/OIDC stack with server, client, and validation components; docs cover standard flows and PKCE enforcement. | Whether the target stack is .NET and whether ASP.NET Identity or a custom member model can support the required admin-only lifecycle and audit controls. |
| node-oidc-provider | Node.js OpenID Certified OAuth2/OIDC authorization server library with many standards implemented, opaque/JWT access token options, PKCE, revocation, introspection, and extensibility. | Whether the sole-maintainer/library ownership model, storage adapter work, admin UI/API work, RBAC, and operational security burden are acceptable. |

## Hybrid patterns to study

Hybrid patterns should be evaluated as patterns first, not as implementation plans.

| Pattern | Why evaluate | Main risk |
| --- | --- | --- |
| New or existing IdP for authentication plus custom backoffice authorization/admin API | Introduces or reuses a trusted IdP for primary login and MFA while letting the backoffice own application roles, permissions, access checks, and audit events. | If no IdP exists today, adoption or operation becomes part of the scope; identity linking, stale authorization state, duplicated admin surfaces, and custom control-plane code remain risks. |
| Managed or self-hosted OIDC provider plus local policy service | Uses standard login and tokens from an IdP, while a local service decides high-churn permissions and backoffice-specific access. | Runtime dependency on policy lookups and potential confusion about which system owns roles. |
| Product IAM for users and clients plus custom administration facade | Uses the provider's admin APIs through a narrower internal REST API shaped around the project's member, role, and service-access requirements. | The facade can hide provider complexity, but it can also become a second IAM system if it stores too much independent state. |
| Ory Hydra plus existing or custom member system | Uses Hydra for protocol correctness while the project controls login, consent, identity, and administration behavior. | Requires building or integrating substantial identity and admin workflows around the OAuth2/OIDC server. |

## First comparison order

The first comparison pass should favor breadth over depth:

1. Run the [Evaluation Framework](./evaluation-framework.md) gate check for each managed and self-hosted candidate.
2. Mark evidence as Confirmed, Likely, Inferred, Unknown, or Unsupported.
3. Identify blockers before assigning detailed scores.
4. Record only official-documentation evidence at this stage.
5. Create targeted PoC plans only for unknowns that materially affect the decision.

Suggested first-pass order:

| Step | Candidates | Goal |
| --- | --- | --- |
| 1 | Keycloak, ZITADEL self-hosted, authentik, Authelia, Hanko self-hosted | Establish open-source self-hosted baseline and operational burden. |
| 2 | Auth0, Clerk, Okta, Microsoft Entra ID, Amazon Cognito, ZITADEL Cloud, Cloud-IAM managed Keycloak, Hanko Cloud | Establish managed baseline and lock-in/API fit concerns. |
| 3 | Spring Authorization Server, OpenIddict, node-oidc-provider | Establish how much custom work a minimal-library approach would require. |
| 4 | Hybrid patterns | Decide whether a split model deserves a PoC plan. |

## Early disqualification checks

Before doing detailed scoring, check these questions:

- Can public registration be disabled or avoided?
- Can administrators create, disable, delete or retain, list, and update members?
- Can roles or permissions be managed without giving every administrator full control?
- Can service clients be modeled separately from human administrators?
- Can resource servers validate access tokens with issuer, audience, lifetime, and signature or introspection checks?
- Can role removal, member disablement, and service credential revocation take effect in an acceptable window?
- Can privileged admin operations be audited with actor, action, target, result, timestamp, and request context?
- Is there a credible operations model for upgrades, backups, key rotation, secret rotation, and incident response?
- If self-hosted, is SQLite supported for production, unsupported, or only a development convenience?
- If managed, is data export and migration possible enough to avoid unacceptable lock-in?

## PoC candidates

These are possible PoCs to plan later. Do not implement them during Phase 1 unless explicitly requested.

| PoC | Candidate types | Question answered |
| --- | --- | --- |
| Browser login with Authorization Code and PKCE | Managed, self-hosted, library | Can the provider support the expected backoffice client flow? |
| API token validation | All OAuth2/OIDC candidates | Can a representative resource server validate issuer, audience, lifetime, signature or introspection, and permissions cleanly? |
| Admin API member lifecycle | Managed, self-hosted | Can required member and role operations be automated through documented APIs? |
| Role removal latency | Managed, self-hosted, hybrid | How long does removed access remain effective through tokens, sessions, caches, or local policy? |
| Service-to-service token flow | Managed, self-hosted, library | Can a backend service get a narrow token and call a protected API as a distinct auditable actor? |
| Audit event export | Managed, self-hosted | Can privileged member, role, client, and service-account changes be reviewed outside the provider UI? |
| SQLite feasibility check | Self-hosted | Is SQLite production-supported, development-only, or not supported? |

## Candidate evidence notes

These notes are intentionally brief. Full scoring belongs in one evaluation record per candidate.

| Candidate | Initial evidence status | Notes |
| --- | --- | --- |
| Auth0 by Okta | Likely | Official docs cover OAuth2/OIDC flows, PKCE, Client Credentials, Management API, and Core RBAC for APIs. Needs admin-only lifecycle, audit, and cost review. |
| Clerk | Likely | Official docs and GitHub materials identify Clerk as a managed authentication and user management platform with Backend API, OAuth/OIDC provider behavior, PKCE for public clients, token introspection, session JWT/JWKS verification, Organizations roles and permissions, and M2M tokens. Needs validation of internal admin-only lifecycle, custom API scope/audience support, audit/export, and vendor lock-in. |
| Okta | Likely | Official docs cover scoped OAuth access to Okta APIs, admin roles, custom roles, service apps, users, groups, and system log concepts. Needs app-specific permission mapping review. |
| Microsoft Entra ID | Likely | Official docs cover Microsoft Graph management of users, applications, service principals, and app roles. Needs review of application RBAC fit and operational dependency on the tenant. |
| Amazon Cognito User Pools | Likely | Official docs cover OIDC IdP behavior, OAuth2 resource servers, custom scopes, M2M authorization, groups, and admin APIs. Needs review of internal-admin ergonomics and audit path. |
| Keycloak | Likely | Official docs cover Admin REST API resources and supported production databases. Needs operational sizing, audit coverage, and role/permission mapping review. |
| ZITADEL | Likely | Official docs cover cloud/self-hosting, REST/gRPC APIs, management APIs, service accounts, OIDC/OAuth endpoints, and PostgreSQL. Needs data-model fit and operations review. |
| Cloud-IAM managed Keycloak | Likely | Official docs describe Cloud-IAM as managed Keycloak with vanilla upstream compatibility, full native Keycloak Admin REST API access, dedicated paid clusters, shared free-tier realm hosting, audit logs, backups, exports, service accounts for Cloud-IAM APIs, SLA tiers, and upgrade processes. Needs plan-level operations, exit, extension, support, and compliance review. |
| authentik | Likely | Official docs cover OIDC/OAuth2 providers, roles, groups, API reference, PostgreSQL, and Redis. Needs access-check and admin API fit review. |
| Authelia | Inferred | Official docs confirm an open-source authentication and authorization server, OpenID Certified OIDC provider, Client Credentials support, OAuth2 bearer-token authorization, file and LDAP user backends, access-control rules, MFA, passkeys, and reverse-proxy integrations. Control-plane fit is unclear because admin REST API, member lifecycle, role management, and privileged mutation audit requirements may need external systems or configuration management. |
| Hanko Cloud | Unknown | Official docs confirm Hanko Cloud as a hosted backend with user management and analytics, Admin API access to user data, audit logs, metrics, session JWTs, SAML SSO, and data export paths. OAuth2 authorization-server behavior, Client Credentials, API scope/audience semantics, and RBAC maturity still require qualification. |
| Hanko self-hosted | Unknown | Official docs and repository material confirm open source code, self-hosting, Hanko backend, Hanko Elements, JWT issuing, and Docker/local deployment paths. Production operations, self-hosted feature parity, OAuth2 authorization-server behavior, Client Credentials, and RBAC maturity still require qualification. |
| Ory open-source stack | Inferred | Official docs describe Hydra, Kratos, and Keto/Permissions capabilities, but the combined backoffice control plane would need integration design. |
| Spring Authorization Server | Likely | Official docs cover OAuth2/OIDC server features and PKCE. It is a framework, so member/admin/RBAC/audit burden remains custom. |
| OpenIddict | Likely | Official docs cover OAuth2/OIDC server/client/validation stack, standard flows, and PKCE. Admin and identity behavior must be built or integrated. |
| node-oidc-provider | Likely | Official repository documents OAuth2/OIDC support, certification, PKCE, revocation, introspection, and token format options. Admin and identity behavior remain custom. |

## References

- [Evaluation Framework](./evaluation-framework.md)
- [OAuth2](./wiki/02-oauth2.md)
- [OpenID Connect](./wiki/03-openid-connect.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [RBAC](./wiki/05-rbac.md)
- [OAuth2 Flows](./wiki/06-oauth2-flows.md)
- [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md)
- [Admin API](./wiki/08-admin-api.md)
- [Security Best Practices](./wiki/09-security-best-practices.md)
- [Auth0 - Authentication and Authorization Flows](https://auth0.com/docs/api-auth)
- [Auth0 - Authorization Code Flow with PKCE](https://auth0.com/docs/flows/guides/auth-code-pkce/call-api-auth-code-pkce)
- [Auth0 - Configure Core Authorization Features for RBAC](https://auth0.com/docs/manage-users/access-control/configure-core-rbac)
- [Auth0 - Enable RBAC for APIs](https://auth0.com/docs/get-started/apis/enable-role-based-access-control-for-apis)
- [Clerk GitHub Organization](https://github.com/clerk)
- [Clerk - API Reference](https://clerk.com/docs/reference/api/overview)
- [Clerk - How Clerk Works](https://clerk.com/docs/guides/how-clerk-works/overview)
- [Clerk - How Clerk Implements OAuth](https://clerk.com/docs/guides/configure/auth-strategies/oauth/how-clerk-implements-oauth)
- [Clerk - OAuth SSO](https://clerk.com/docs/guides/configure/auth-strategies/oauth/single-sign-on)
- [Clerk - Organizations](https://clerk.com/docs/organizations/overview)
- [Clerk - Roles and Permissions](https://clerk.com/docs/guides/organizations/control-access/roles-and-permissions)
- [Clerk - Machine Authentication](https://clerk.com/docs/guides/development/machine-auth/overview)
- [Clerk - M2M Tokens](https://clerk.com/docs/guides/development/machine-auth/m2m-tokens)
- [Clerk - Manual JWT Verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
- [Okta - Okta Management API Overview](https://developer.okta.com/docs/api/openapi/okta-management/guides/overview/)
- [Okta - OAuth 2.0 Scopes](https://developer.okta.com/docs/api/oauth2)
- [Okta - Roles in Okta](https://developer.okta.com/docs/reference/api/roles/)
- [Okta - Set up Okta for OAuth API access](https://developer.okta.com/docs/guides/set-up-oauth-api/main/)
- [Microsoft Graph - Manage Microsoft Entra applications and service principals](https://learn.microsoft.com/en-us/graph/api/resources/applications-api-overview?view=graph-rest-1.0)
- [Microsoft Entra ID - App Roles for Applications](https://learn.microsoft.com/en-us/entra/external-id/customers/how-to-use-app-roles-customers)
- [Microsoft Entra ID - Built-in Roles](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference)
- [Amazon Cognito - User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html)
- [Amazon Cognito - Scopes, M2M, and Resource Servers](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-define-resource-servers.html)
- [Amazon Cognito - OAuth 2.0 Grants](https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints-oauth-grants.html)
- [Amazon Cognito - AdminCreateUser](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminCreateUser.html)
- [Amazon Cognito - AdminAddUserToGroup](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminAddUserToGroup.html)
- [Keycloak - Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak - Admin REST API](https://www.keycloak.org/docs-api/26.5.2/rest-api/)
- [Keycloak - Configuring the Database](https://www.keycloak.org/server/db)
- [Cloud-IAM - Managed Keycloak](https://www.cloud-iam.com/keycloak/)
- [Cloud-IAM - Official Documentation](https://documentation.cloud-iam.com/)
- [Cloud-IAM - Deploy Managed Keycloak](https://documentation.cloud-iam.com/get-started/deploy-my-keycloak.html)
- [Cloud-IAM - Keycloak FAQ](https://documentation.cloud-iam.com/faq/keycloak.html)
- [Cloud-IAM - Keycloak Admin REST API](https://documentation.cloud-iam.com/resources/keycloak-api.html)
- [Cloud-IAM - Audit Logs](https://documentation.cloud-iam.com/how-to-guides/audit-logs.html)
- [Cloud-IAM - Service Accounts](https://documentation.cloud-iam.com/how-to-guides/service-account.html)
- [Cloud-IAM - Keycloak Upgrades](https://documentation.cloud-iam.com/references/keycloak-upgrades.html)
- [Cloud-IAM - Data Deletion and Exit Policy](https://documentation.cloud-iam.com/references/data-deletion-exit-policy.html)
- [ZITADEL - Documentation](https://zitadel.com/docs)
- [ZITADEL - API Reference Overview](https://zitadel.com/docs/apis/introduction)
- [ZITADEL - Management API](https://zitadel.com/docs/reference/api/management)
- [ZITADEL - Database](https://zitadel.com/docs/self-hosting/manage/database)
- [authentik - OAuth2 Provider](https://docs.goauthentik.io/add-secure-apps/providers/oauth2/)
- [authentik - About Roles](https://docs.goauthentik.io/users-sources/roles/)
- [authentik - API Overview](https://api.goauthentik.io/)
- [authentik - Architecture](https://docs.goauthentik.io/docs/core/architecture)
- [Authelia](https://www.authelia.com/)
- [Authelia GitHub Repository](https://github.com/authelia/authelia)
- [Authelia - OpenID Connect Overview](https://www.authelia.com/overview/authorization/openid-connect-1.0/)
- [Authelia - OpenID Connect Integration](https://www.authelia.com/integration/openid-connect/introduction/)
- [Authelia - OpenID Connect Provider Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/provider/)
- [Authelia - OpenID Connect Clients Configuration](https://www.authelia.com/configuration/identity-providers/openid-connect/clients/)
- [Authelia - OAuth 2.0 Bearer Token Usage](https://www.authelia.com/integration/openid-connect/oauth-2.0-bearer-token-usage/)
- [Authelia - Access Control](https://www.authelia.com/configuration/security/access-control/)
- [Authelia - First Factor](https://www.authelia.com/configuration/first-factor/introduction/)
- [Authelia - File Authentication Backend](https://www.authelia.com/configuration/first-factor/file/)
- [Authelia - LDAP Authentication Backend](https://www.authelia.com/configuration/first-factor/ldap/)
- [Hanko - Documentation](https://docs.hanko.io/)
- [Hanko - Getting started with Hanko Cloud](https://docs.hanko.io/setup-hanko-cloud)
- [Hanko - Admin API Introduction](https://docs.hanko.io/api-reference/admin/introduction)
- [Hanko - Hanko APIs](https://docs.hanko.io/api-reference/introduction)
- [Hanko - Sessions and tokens](https://docs.hanko.io/guides/session-management)
- [Hanko - SAML SSO](https://docs.hanko.io/guides/enterprise-sso/introduction)
- [Hanko - FAQ](https://docs.hanko.io/community-support/faq)
- [Hanko GitHub Repository](https://github.com/teamhanko/hanko)
- [Ory Hydra](https://www.ory.com/hydra)
- [Ory Kratos](https://www.ory.com/kratos/)
- [Ory Keto](https://www.ory.com/keto)
- [Spring Authorization Server - Overview](https://docs.spring.io/spring-authorization-server/reference/overview.html)
- [Spring Authorization Server - SPA with PKCE](https://docs.spring.io/spring-authorization-server/reference/guides/how-to-pkce.html)
- [OpenIddict - Introduction](https://documentation.openiddict.com/introduction)
- [OpenIddict - Choosing the Right Flow](https://documentation.openiddict.com/guides/choosing-the-right-flow)
- [OpenIddict - Proof Key for Code Exchange](https://documentation.openiddict.com/configuration/proof-key-for-code-exchange)
- [node-oidc-provider GitHub Repository](https://github.com/panva/node-oidc-provider)
