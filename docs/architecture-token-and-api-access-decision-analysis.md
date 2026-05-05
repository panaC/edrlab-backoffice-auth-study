# Architecture Decision Analysis: Token and API Access Strategy

## Purpose

This note analyzes the current token and API access strategy for the internal backoffice IAM study. It is an analysis artifact, not an accepted production architecture decision.

## Decision Context

The selected architecture has a browser-facing BFF, a central IAM Control Plane, and one or more backend API resource servers. The browser should not store OAuth tokens. The BFF handles login and server-side token handling. Backend APIs must validate access tokens and enforce permissions.

The core decision is how much authorization state should live in short-lived access tokens versus runtime checks, introspection, or local application sessions.

## Current Baseline

The current study baseline is:

- the browser receives only an opaque BFF session cookie;
- OAuth tokens remain server-side in the BFF or behind a token-reference pattern;
- the first study and minimal PoC use JWT access tokens;
- resource servers validate issuer, audience, expiry, signature or introspection result, and required permissions;
- removed access may remain effective only until short access-token expiry for the first study baseline;
- immediate revocation, introspection, or runtime authorization lookup are later options when stale-access tolerance is lower.

## Decision To Make

Decide the token and access-check strategy for the first PoC and later production design:

- self-contained JWT access tokens;
- opaque tokens with introspection;
- JWTs plus runtime authorization checks for sensitive operations;
- BFF-only local sessions with no independent resource-server tokens;
- another candidate-specific mechanism.

This note does not choose final token lifetimes, signing algorithms, key storage, or provider-specific implementation.

## Options Considered

| Option | Summary |
| --- | --- |
| Short-lived JWT access tokens | Resource servers validate tokens locally using issuer metadata and signing keys. |
| Opaque tokens plus introspection | Resource servers call the authorization server or introspection endpoint to validate token status. |
| JWTs plus authorization lookup | APIs validate JWTs, then call a permission or policy service for high-risk operations. |
| BFF-only session authorization | Backend behavior relies on BFF session state rather than independent access tokens. |
| Local application sessions | A single app backend owns sessions and authorization without OAuth access tokens. |

## Evaluation Criteria

| Criterion | Why it matters |
| --- | --- |
| Browser token exposure | Tokens and secrets must not be stored in browser-readable storage. |
| Resource-server independence | APIs should be able to validate requests without trusting only UI or BFF checks. |
| Stale-access tolerance | Role removal and disablement may not take effect immediately with self-contained JWTs. |
| Operational simplicity | Token strategy should be understandable and supportable by the internal team. |
| Incident response | Token theft, refresh-token theft, key compromise, and bad role assignment need containment paths. |
| Auditability | Privileged access and denials should produce useful evidence. |

## Option Analysis

| Option | Strengths | Limitations |
| --- | --- | --- |
| Short-lived JWT access tokens | Efficient local validation, common provider support, good first PoC fit. | Permission changes may remain stale until token expiry unless tokens are very short-lived or sensitive operations use stronger checks. |
| Opaque tokens plus introspection | Can reflect revocation or disablement more quickly. | Adds runtime dependency on the authorization server and latency/error handling for every protected request or selected requests. |
| JWTs plus authorization lookup | Keeps efficient token validation while allowing fresher decisions for high-risk operations. | Adds an authorization/check path that must be secured, monitored, and designed carefully. |
| BFF-only session authorization | Simple for browser-only calls through one trusted backend path. | Backend APIs lose independent token validation and become tightly coupled to the BFF trust boundary. |
| Local application sessions | Simple for a single monolith. | Poor fit for multiple resource servers and product-neutral IAM candidate comparison. |

## Trade-Off Summary

JWT access tokens are a practical first study baseline because they prove issuer, audience, signature, expiry, and permission validation across a resource-server boundary. The main trade-off is stale authorization: removed roles or disabled members may keep effective access until token expiry.

Opaque tokens, introspection, or runtime authorization checks reduce stale-access windows but add runtime dependencies and operational complexity. They should be evaluated when the accepted stale-access window is shorter than the JWT lifetime.

## Risks And Unknowns

- Access tokens may carry stale role or permission claims after a role removal.
- Resource servers may skip issuer, audience, expiry, signature, or permission validation.
- BFF token storage may become a credential store if refresh tokens are stored without encryption, vaulting, rotation, and redaction.
- Logout semantics may be misunderstood if local session logout does not immediately revoke every access token.
- Audit logs may accidentally capture bearer tokens, refresh tokens, authorization codes, raw session IDs, or client secrets.

## Evidence Needed

- PoC validation that resource servers reject wrong issuer, wrong audience, expired, invalid-signature, and insufficient-permission tokens.
- PoC evidence for how role removal or member disablement affects existing access.
- Candidate evidence for token revocation, introspection, refresh-token rotation, logout, and JWKS/key rotation behavior.
- Logging tests proving that tokens, client secrets, authorization codes, and raw session IDs are redacted.

## Current Working Position

The current working position is to use short-lived JWT access tokens for the first study and minimal PoC, with removed access allowed to expire at access-token expiry. This is not a final production recommendation.

If production requires faster access removal, the project should evaluate introspection, token revocation, shorter token lifetimes, or a runtime authorization/check path.

## Open Questions

- What is the maximum acceptable lifetime for access tokens carrying administrator permissions?
- Should the first PoC use refresh tokens, or force re-login when access tokens expire?
- Where should server-side token material be stored?
- Which operations require fresher authorization than JWT expiry can provide?
- What should logout mean for local BFF sessions, provider sessions, refresh tokens, and existing access tokens?

## Related Documents

- [Requirements Baseline](./requirements-baseline.md)
- [BFF Sessions and Token Handling](./security-bff-sessions-and-token-handling.md)
- [Member Lifecycle](./requirements-member-lifecycle.md)
- [Security Threat Model](./security-threat-model.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [Token Lifecycle](./wiki/12-token-lifecycle.md)
- [OAuth2 Flows](./wiki/06-oauth2-flows.md)
- [Evaluation Framework](./evaluation-framework.md)

## References

- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
