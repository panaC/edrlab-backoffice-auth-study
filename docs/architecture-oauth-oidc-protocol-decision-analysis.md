# Architecture Decision Analysis: OAuth2 and OIDC Protocol Boundary

## Purpose

This note analyzes whether OAuth2 and OpenID Connect should remain part of the study baseline. It is an analysis artifact, not an accepted production architecture decision.

## Decision Context

The project brief requires OAuth2 authentication and authorization flows and OpenID Connect for user identity. That wording needs precision: OAuth2 is primarily an authorization framework for access tokens, while OpenID Connect adds a standardized user-authentication and identity layer.

The decision is not "use OAuth2 because modern systems use OAuth2." The decision is whether the selected architecture needs standardized login, token issuance, token validation, API protection, provider interoperability, and future service-client fit.

## Current Baseline

The current baseline keeps both protocol families:

- OIDC-compatible login for human backoffice users through the BFF;
- OAuth2-compatible access tokens for protected backend APIs;
- Authorization Code Flow with PKCE for browser-facing login;
- no Implicit Flow for new browser-based backoffice applications;
- server-side BFF token handling, with only an opaque session cookie in the browser.

## Decision To Make

Decide whether OAuth2/OIDC should remain a requirement for the central IAM Control Plane study, or whether a narrower login/session model should be evaluated as the main architecture.

This note does not choose a provider or implementation stack.

## Options Considered

| Option | Summary |
| --- | --- |
| OAuth2/OIDC central IdP and authorization server | Standard login and token contracts across the BFF, IAM Control Plane, and resource servers. |
| Local login with server-side sessions | One application owns authentication, session state, roles, permissions, and all protected operations. |
| Workforce IdP or SSO integration | A corporate identity provider handles login, MFA, and possibly employee lifecycle. |
| Gateway-authenticated identity headers | A trusted gateway authenticates users and forwards identity to the application. |
| SAML-based SSO | Enterprise login federation, if the company identity environment is SAML-first. |
| Custom token model | Project-specific tokens or sessions instead of standardized OAuth2/OIDC contracts. |

## Evaluation Criteria

| Criterion | Why it matters |
| --- | --- |
| Login correctness | The browser-facing backoffice must know who authenticated, with which issuer, client, expiry, and stable subject. |
| API authorization fit | Protected APIs need credentials they can validate independently. |
| Provider comparability | Managed and self-hosted candidates can be compared against common protocol expectations. |
| Operational simplicity | Protocol surface should not exceed the backoffice's real needs. |
| Security defaults | The design should avoid custom authentication flows, token formats, and cryptography. |
| Future extensibility | Later service-to-service access should not require modeling automation as fake human users. |

## Option Analysis

| Option | Strengths | Limitations |
| --- | --- | --- |
| OAuth2/OIDC central IdP and authorization server | Product-neutral, widely supported, separates authentication from API authorization, supports BFF login and protected APIs. | Adds client registration, redirect URI, token lifetime, issuer, audience, key, revocation, and introspection concepts. |
| Local login with server-side sessions | Simpler for a single internal monolith. Avoids OAuth client and token operations. | The team owns password policy, recovery, optional MFA, session security, account disablement semantics, and audit evidence. |
| Workforce IdP or SSO integration | Can delegate login and MFA if a corporate IdP exists. | No enterprise SSO is assumed today; local authorization, roles, access checks, and admin audit still remain. |
| Gateway-authenticated identity headers | Can simplify coarse-grained access to internal web apps. | Requires strong bypass prevention and header-spoofing controls; does not solve operation-level authorization by itself. |
| SAML-based SSO | May fit existing enterprise federation environments. | Less natural for API token validation, service clients, and modern OAuth/OIDC provider comparison. |
| Custom token model | Can be tailored to the project. | High risk around validation, expiry, key rotation, audience handling, revocation, and incident response. |

## Trade-Off Summary

OAuth2/OIDC is useful for this study because the selected architecture has multiple trust boundaries: browser client, BFF, central IAM component, admin API, protected backend APIs, and possible future service clients.

OAuth2/OIDC may be overkill if the real product is only one internal app with one backend and no independent APIs or provider interoperability need. That narrower possibility should stay visible as a scope guard.

## Risks And Unknowns

- Teams may confuse OIDC authentication with authorization to perform admin actions.
- Teams may use access tokens without validating issuer, audience, signature, expiry, or required permissions.
- A product may support "OIDC" but still lack adequate admin API, audit, lifecycle, or operational behavior.
- If no SSO exists today, "use SSO" still means adopting, subscribing to, or operating an identity provider.

## Evidence Needed

- Candidate support for Authorization Code Flow with PKCE, OIDC Discovery, issuer metadata, JWKS, token validation, and logout behavior where relevant.
- PoC evidence that the BFF can complete OIDC login without exposing tokens to browser-readable storage.
- PoC evidence that a resource server rejects wrong issuer, wrong audience, expired, tampered, or insufficient-permission tokens.
- Evidence about how each candidate maps member state, roles, permissions, admin API operations, and audit events.

## Current Working Position

The current working position is to keep OAuth2/OIDC in the requirements baseline for the selected central IAM Control Plane architecture. This is not a final production recommendation or provider choice.

OIDC is the product-neutral login contract. OAuth2 access-token behavior is the product-neutral API protection contract. Neither replaces explicit member lifecycle, RBAC, permission checks, admin API controls, or audit requirements.

## Open Questions

- Is the backoffice actually a multi-resource-server environment, or a single application?
- What token lifetime is acceptable for administrator access?
- What should logout mean across the BFF session, provider session, refresh token, and access tokens?
- Which provider or library behaviors need PoC evidence rather than documentation-only evaluation?

## Related Documents

- [Requirements Baseline](./requirements-baseline.md)
- [BFF Sessions and Token Handling](./security-bff-sessions-and-token-handling.md)
- [OpenID Connect](./wiki/03-openid-connect.md)
- [OAuth2](./wiki/02-oauth2.md)
- [OAuth2 Flows](./wiki/06-oauth2-flows.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [Evaluation Framework](./evaluation-framework.md)

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
