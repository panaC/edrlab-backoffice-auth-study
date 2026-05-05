# Minimal Backoffice IAM Architecture Notes

This document consolidates the Phase 1 discussion about SSO, identity providers, IAM control planes, Backend-for-Frontend sessions, and the minimal micro-service architecture for an internal backoffice authorization server.

The study now adopts the **Central IAM Control Plane Architecture** as its target shape:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IdP / Authorization Server / Admin Control Plane
    -> one or more backend API resource servers
```

The focus of this project is the **IdP / Authorization Server / Admin Control Plane** part. The Backoffice BFF, backend API services, workers, and service databases are included to define integration boundaries, but they are not the main implementation subject of the study. The first study and minimal PoC can use one demonstration API resource server.

This document does not choose a final product, vendor, database, hosting model, or implementation stack.

## Core Terms

| Term | Meaning | Main question answered |
| --- | --- | --- |
| SSO | Single Sign-On. A user experience where one login session can be reused across multiple applications. | Can the user sign in once and access several apps? |
| IdP | Identity Provider. The system that authenticates users and provides identity assertions or tokens. | Who authenticated this user? |
| Authorization Server | OAuth2 server that issues access tokens to clients. In OIDC systems, this is often also the OpenID Provider. | Which tokens can this client receive? |
| Admin Control Plane | Administrative surface for users, roles, permissions, clients, service accounts, access checks, and audit events. | Who manages IAM state and privileged changes? |
| BFF | Backend-for-Frontend. A server-side component tailored to one frontend experience. | How can the browser use the system without storing OAuth tokens directly? |
| Resource Server | Backend API that receives and validates access tokens before serving protected resources. | Is this API request authorized? |

SSO is not the same thing as an IdP or an IAM control plane. SSO is the user-visible effect. The IdP and control plane are the systems that authenticate users, issue tokens, manage access, and record privileged changes.

## What BFF Means In This Study

BFF means **Backend-for-Frontend**. In this architecture, it is the browser-facing backend for the internal backoffice UI. Its architecture-level purpose is to let the browser use an opaque session cookie while the BFF handles OIDC login, server-side token handling, Admin API calls, and backend API calls.

The BFF is a security and ergonomics boundary for the browser-facing backoffice. It is not the IAM authority, does not issue OAuth2/OIDC tokens, does not own members, roles, or permissions, and does not replace backend API authorization checks.

Detailed BFF session, token storage, CSRF, refresh, and logout behavior belongs in [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md). This architecture note keeps only the system boundary.

## Starting Assumption: No Existing Enterprise SSO

The current assumption is that no enterprise SSO exists today. That matters because the project cannot simply reuse a corporate identity provider for login, MFA, and employee lifecycle.

If the project says "use SSO", it is really saying one of these:

- adopt a managed identity provider that can provide SSO;
- operate a self-hosted identity provider that can provide SSO;
- build enough identity and session behavior internally to create a backoffice-specific login system;
- defer company-wide SSO and keep the scope limited to the backoffice IAM need.

Creating or adopting SSO is therefore an IAM architecture decision, not a shortcut around the IAM control-plane requirements.

The current project scope stays limited to the internal backoffice. Company-wide workforce IAM or broad SSO remains outside the first study and PoC scope.

## Non-Selected Narrower Shape: One Backoffice Only

If the real scope is only one internal backoffice application, one backend, one database, no independent backend APIs, no company-wide SSO, and no complex service-to-service authorization, the simplest credible option to evaluate is a conventional application-owned model:

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

In this model:

- administrators create and manage members;
- users authenticate directly with the backoffice;
- the backend creates and validates server-side sessions;
- every protected operation checks permissions server-side;
- role and permission assignments live in the application database;
- privileged changes write audit events;
- the browser does not need to manage access tokens or JWTs.

Example operation:

```text
POST /members/{id}/disable

Backend checks:
- caller has a valid session;
- caller is active;
- caller has permission members:disable;
- operation does not violate self-escalation or self-disablement policy;
- audit log records actor, action, target, result, timestamp, and request context.
```

This shape avoids operating a separate authorization server, configuring OAuth2 clients, managing redirect URIs, issuing browser access tokens, validating token audiences across services, and supporting cross-application SSO.

The trade-off is ownership. The team must own password policy, password storage through a well-maintained framework, account recovery, optional MFA, session security, CSRF protection, lockout or rate-limiting behavior, account disablement semantics, audit log integrity, and administrator access recovery.

This shape is not the selected study architecture. It is retained as a rationale for why the project would be simpler if it only had one backoffice with local sessions, and why a separate IAM control plane should be justified by a real protected-API boundary, administration-control-plane need, or future expansion need rather than by habit.

## Selected Architecture: Central IAM Control Plane

The selected architecture is an authorization server with an IdP, an admin control plane, and one or more backend API services. The minimal architecture separates IAM authority from application business logic.

```text
Browser
  |
  | HttpOnly session cookie
  v
Backoffice UI / BFF
  |
  | OIDC login, token exchange, Admin API calls, API calls
  v
IdP / Authorization Server / Admin Control Plane
  |
  | OAuth2 access tokens
  v
Backend API Services
```

### Runtime Layers

| Layer | Responsibility | Owns IAM authority? |
| --- | --- | --- |
| Browser | Displays UI and sends the BFF session cookie. | No |
| Backoffice UI / BFF | Serves UI, owns browser session, handles OIDC callback, keeps tokens server-side, calls IdP Admin API and backend APIs. | No |
| IdP / Authorization Server / Admin Control Plane | Authenticates users, issues tokens, manages members, roles, permissions, clients, service accounts, and audit events. | Yes |
| Backend API Services | Own business logic and data, validate access tokens, enforce permissions server-side. | No, but they enforce authorization for their own operations |
| Service Clients / Workers | Future extension: authenticate as machine clients and call backend APIs with service access tokens. | No |

The BFF is not the IAM authority. It is a secure web facade. The IdP/control plane is the IAM authority. Backend APIs trust tokens from the IdP, but still enforce permissions themselves.

## Project Focus: IdP / Authorization Server / Admin Control Plane

The central component is the purpose of this study. It should be evaluated and designed as the system that owns:

- OIDC login and user authentication behavior;
- OAuth2 token issuance for browser-backed clients and, if later in scope, machine clients;
- members, lifecycle states, credentials or external identities;
- clients, redirect URIs, service accounts, and client permissions;
- roles, permissions, and assignments;
- administration APIs for members, roles, clients, and access checks;
- audit events for privileged IAM changes;
- issuer metadata, JWKS or introspection, token validation contracts, and key rotation behavior.

It should not own backend business data. Backend API services keep their own databases and enforce permissions for their own operations after validating tokens issued by the IdP/authorization server.

The BFF should not become a second IAM authority. It may provide a project-specific UI and call the IdP Admin API, but the IdP/control plane must enforce administrative permissions server-side.

## Minimal Micro-Service Architecture

```text
+--------------------+
| Browser            |
| - HTML/CSS/JS      |
| - session cookie   |
+---------+----------+
          |
          v
+--------------------+        +----------------------+
| Backoffice BFF     |------->| BFF Session Store    |
| - serves UI        |        | sessions, CSRF,      |
| - OIDC callback    |        | token references or  |
| - server sessions  |        | encrypted tokens     |
| - calls IdP API    |        +----------------------+
| - calls services   |
+---------+----------+
          |
          | OIDC / OAuth2 / Admin API
          v
+----------------------------------+        +----------------------------------+
| IdP / Authorization Server       |------->| IdP Database                     |
| / Admin Control Plane            |        | members, credentials, sessions,  |
| - login                          |        | clients, roles, permissions,     |
| - OIDC provider                  |        | assignments, refresh tokens,     |
| - OAuth2 token issuance          |        | key metadata, audit logs         |
| - users, roles, permissions      |        +----------------------------------+
| - clients, service accounts      |
| - admin API                      |
| - audit                          |
+----------------+-----------------+
                 |
                 | access tokens
                 v
       +--------------------+      +--------------------+
       | Backend API A      |      | Backend API B      |
       | - business logic   |      | - business logic   |
       | - token validation |      | - token validation |
       | - permission check |      | - permission check |
       +---------+----------+      +---------+----------+
                 |                           |
                 v                           v
       +--------------------+      +--------------------+
       | Service A DB       |      | Service B DB       |
       | business data only |      | business data only |
       +--------------------+      +--------------------+
```

### Minimal Services

| Service | Responsibility | Database |
| --- | --- | --- |
| Backoffice BFF | UI delivery, browser sessions, OIDC callback, token handling, calls to IdP Admin API and backend APIs. | BFF session store |
| IdP / Authorization Server / Control Plane | Login, token issuance, users, roles, permissions, clients, service accounts, audit logs. | IAM database |
| Demonstration Backend API | First PoC resource server, token validation, operation-level authorization. | Demo data only, if needed |
| Later Backend APIs | Future business APIs, token validation, operation-level authorization. | One database per service, if needed |
| Workers / Service Clients | Future extension: background jobs or internal automation using Client Credentials Flow. | Own database only if they own durable business state |

Backend services should not read the IdP database directly. They should validate tokens through JWKS, introspection, or a dedicated authorization/check API if needed.

## Minimal Database Boundaries

### BFF Session Store

The BFF session store exists so the browser can carry only an opaque session cookie while OAuth tokens or token references stay server-side. At the architecture level, the important boundary is:

- the browser should not store OAuth access tokens or refresh tokens;
- the BFF session store is BFF-owned state, not IAM source-of-truth data;
- a multi-replica BFF needs a shared session store;
- backend APIs should still validate access tokens and required permissions.

Cookie attributes, session table fields, token storage options, CSRF handling, refresh behavior, and logout semantics are covered in [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md).

### IdP Database

The IdP database owns IAM state:

```text
members
credentials_or_external_identities
sessions_or_refresh_tokens
clients
service_accounts
roles
permissions
role_assignments
client_permissions
signing_key_metadata
audit_logs
```

This database is security-sensitive. Backend business services should not couple themselves to its schema.

### Backend Service Databases

Each backend API owns its business data:

```text
service_a_db
- service A business entities

service_b_db
- service B business entities
```

Service databases may store local identifiers that reference IAM subjects, but they should not become alternate sources of truth for global roles or member lifecycle.

## Request Flows

### Browser Login

Use Authorization Code Flow with PKCE for browser-facing login. In the BFF pattern, the BFF handles the callback and stores tokens server-side.

```text
Browser -> BFF: open backoffice
BFF -> IdP: redirect to login with client_id, redirect_uri, state, nonce, PKCE challenge
User -> IdP: authenticate
IdP -> BFF: authorization code
BFF -> IdP: exchange code plus PKCE verifier for tokens
BFF -> BFF Session Store: create session and store token data or references
BFF -> Browser: set HttpOnly session cookie
```

### Admin Control-Plane Operation

```text
Browser -> BFF: disable member
BFF -> BFF Session Store: validate session
BFF -> IdP Admin API: disable member
IdP -> IdP Database: update member status
IdP -> Audit Log: record actor, action, target, result, timestamp, request context
BFF -> Browser: return result
```

The IdP Admin API must enforce admin authorization server-side. The BFF may hide UI actions, but it must not be the only authorization layer.

### Backend API Call From Browser UI

```text
Browser -> BFF: read billing reports
BFF -> BFF Session Store: validate session and retrieve token or token reference
BFF -> Billing API: call with access token
Billing API -> Billing API: validate issuer, audience, expiry, signature or introspection
Billing API -> Billing API: check permission billing:reports:read
Billing API -> Billing DB: read data
Billing API -> BFF: return data
BFF -> Browser: render result
```

### Service-to-Service Call

Service-to-service authentication is a future theoretical extension, not part of the first study or minimal PoC scope. If it becomes in scope later, use Client Credentials Flow or an equivalent strong machine-client mechanism.

```text
Worker -> IdP: authenticate client and request token
IdP -> Worker: access token for worker identity
Worker -> Backend API: call with access token
Backend API -> Backend API: validate token and required service permission
Backend API -> Worker: return result
```

Do not model services as fake users. Human users and machine clients should have distinct subjects, permissions, credentials, and audit trails.

## Token and Permission Baseline

For the multi-service shape:

- access tokens should be short-lived;
- access tokens should have clear issuer and audience values;
- backend APIs must validate issuer, audience, expiry, and signature or introspection result;
- backend APIs must enforce operation-level permissions server-side;
- permissions in tokens are acceptable only when staleness is acceptable for the token lifetime;
- high-risk or high-churn authorization can use introspection or a dedicated authorization/check API;
- refresh tokens, if used by the BFF, should stay server-side and be encrypted or stored through a token vault pattern;
- token values, passwords, client secrets, and refresh tokens must not be logged.

## What To Avoid In The Minimal Version

Do not add these until a concrete requirement justifies them:

- API gateway as an authorization substitute;
- event bus for IAM propagation;
- separate policy engine;
- shared authorization database read directly by services;
- custom cryptography;
- browser localStorage or sessionStorage for OAuth tokens;
- service accounts modeled as human users;
- frontend-only authorization checks;
- broad admin roles where explicit permissions are needed.

## Growth Triggers

The minimal architecture should be reconsidered if any of these become true:

- there are multiple independently deployed backoffice UIs;
- external or company-wide SSO becomes a requirement;
- backend APIs need independently issued audience-specific tokens;
- many service clients need lifecycle, rotation, and least-privilege controls;
- role changes must take effect immediately across all APIs;
- audit logs need centralized export, retention, or compliance controls;
- administrators need MFA, step-up authentication, or break-glass processes;
- the team cannot safely own password/session/MFA behavior in a local-only design.

## Current Study Position

The selected study architecture is the Central IAM Control Plane Architecture. The minimal runtime shape is:

```text
1 Backoffice BFF
1 IdP / Authorization Server / Admin Control Plane
1 demonstration backend API resource server for the first PoC
1 BFF session store
1 IdP database
optional demo API data store only if needed
```

The project focus is the IdP / Authorization Server / Admin Control Plane. The BFF, demonstration API, and storage choices define required integration behavior, but the study should avoid drifting into implementing business services or a full backoffice product. Service-to-service authentication remains a future option rather than an initial PoC requirement.

This shape keeps the browser simple, centralizes IAM authority in the IdP/control plane, keeps backend services responsible for their own authorization enforcement, and avoids unnecessary infrastructure until the requirements prove it is needed.

## Related Documents

- [Phase 1 working notes](./phase-1-working-notes.md)
- [Evaluation framework](./evaluation-framework.md)
- [Candidate shortlist](./candidate-shortlist.md)
- [Authentication vs Authorization](./wiki/01-authentication-vs-authorization.md)
- [OAuth2](./wiki/02-oauth2.md)
- [OpenID Connect](./wiki/03-openid-connect.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [RBAC](./wiki/05-rbac.md)
- [OAuth2 Flows](./wiki/06-oauth2-flows.md)
- [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md)
- [Administration APIs](./wiki/08-admin-api.md)
- [Security Best Practices](./wiki/09-security-best-practices.md)
- [Administrator Authentication Policy](./administrator-authentication-policy.md)

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
