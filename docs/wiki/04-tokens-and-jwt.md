# Tokens and JWTs

## What it is

A token is a credential issued by an authorization server or identity provider. The client presents the token to another component to prove an authorization grant, authentication event, or refresh capability.

The main token types in this study are:

| Token | Primary audience | Purpose |
| --- | --- | --- |
| Access token | Resource server | Authorizes API access. |
| ID token | Client | Communicates user authentication and identity information in OIDC. |
| Refresh token | Authorization server | Lets a client request a new access token without repeating the full authorization flow. |

A JSON Web Token, or JWT, is a compact JSON-based token format. JWTs are commonly signed as JSON Web Signatures so a receiver can verify integrity and issuer authenticity. JWTs are not automatically secure because they are JWTs; security depends on correct signing, validation, key management, claims, lifetimes, and audience boundaries.

## Why it matters

Backoffice APIs will likely make authorization decisions using access tokens. Engineers need to understand what tokens prove, what they do not prove, and how resource servers validate them before trusting token contents.

The study also needs to compare token styles later. JWTs allow local validation and can reduce dependency on a network lookup for each request. Opaque tokens reveal no structured claims to the client or API and usually require introspection or a lookup. Neither approach is always correct. The trade-off depends on revocation needs, performance, privacy, key rotation, service boundaries, and operational simplicity.

## How it works

A JWT has three base64url-encoded parts: header, payload, and signature. The header describes metadata such as the signing algorithm and key identifier. The payload contains claims. The signature protects the header and payload from tampering when the receiver validates it with the correct key.

Common claims include:

| Claim | Meaning |
| --- | --- |
| `iss` | Issuer. The authorization server or identity provider that issued the token. |
| `sub` | Subject. The member, user, service account, or client the token is about. |
| `aud` | Audience. The intended recipient, such as a specific API. |
| `exp` | Expiration time. The token should not be accepted after this time. |
| `nbf` | Not before time. The token should not be accepted before this time. |
| `iat` | Issued at time. Useful for age checks and debugging. |
| `scope` | Delegated access values, often space-delimited in OAuth2. |
| `client_id` | The OAuth2 client associated with the token, where used. |

Some systems include roles or permissions in access tokens. That can make API checks fast, but it also means role changes may not take effect until tokens expire unless the system supports revocation, introspection, short lifetimes, or another invalidation strategy. See [RBAC](./05-rbac.md) for modeling details.

For the broader lifecycle of issuing, storing, validating, refreshing, revoking, expiring, and rotating tokens, see [Token Lifecycle](./12-token-lifecycle.md). For JWKS, signing keys, key rotation, client secrets, private key JWT, and mTLS, see [Key Management and Signing Keys](./23-key-management-and-signing-keys.md).

## Token validation

Before trusting an access token, a resource server should check at least:

- the token came from the expected issuer;
- the token audience includes the API or resource server;
- the token is not expired and is currently valid;
- the signature is valid when using signed JWTs;
- the signing algorithm is expected and not attacker-controlled;
- the key used for verification is trusted and current;
- required scopes, roles, or permissions are present and meaningful for the API;
- the token type is appropriate for the endpoint.

Opaque token validation usually uses OAuth2 Token Introspection or a similar server-side lookup. JWT validation usually uses issuer metadata and a JWKS endpoint to find signing keys. A system can also combine approaches.

```text
validate access token:
  require expected issuer
  require expected audience
  require valid lifetime
  require trusted signature or active introspection result
  require operation permission
```

This pseudocode is illustrative only. Production validation should use well-maintained libraries and the chosen provider's documented validation rules.

## Access tokens vs ID tokens

Access tokens are for resource servers. ID tokens are for clients. A backoffice API should not accept an ID token merely because it is signed by the same provider. The audience, token purpose, and claims differ.

In OIDC, the ID token tells the client about the authentication event and user identity. The access token is what the client sends to the API. See [OpenID Connect](./03-openid-connect.md) for the identity side.

## Refresh tokens

A refresh token is presented to the authorization server to get a new access token. It is more sensitive than a short-lived access token because it can often be exchanged repeatedly. Refresh token handling depends on client type and security posture.

For browser and public clients, refresh token rotation and reuse detection are important mitigations where refresh tokens are used. Confidential backend clients may be able to protect refresh tokens more strongly, but they still need secure storage, least privilege, and revocation behavior.

## JWTs vs opaque tokens

| Choice | Strengths | Trade-offs |
| --- | --- | --- |
| JWT access token | Local validation, no per-request introspection dependency, can carry selected claims. | Harder immediate revocation, claim leakage risk, key rotation and validation complexity. |
| Opaque access token | Minimal data exposure, central introspection can reflect current state. | Adds network dependency or cache design, resource server needs introspection trust. |

For this wiki, the goal is to understand the options, not to choose one.

## Common mistakes

Accepting unsigned tokens or attacker-selected algorithms is unsafe. Validation logic must restrict acceptable algorithms and keys.

Skipping issuer or audience checks allows token substitution across issuers or APIs.

Putting too much data in tokens increases privacy risk and makes stale authorization data harder to manage.

Logging bearer tokens can turn logs into credentials. Tokens should be redacted in application logs, traces, analytics, and error reports.

Using long-lived access tokens makes compromise more damaging. Short lifetimes reduce exposure, especially for bearer tokens.

## References

- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7515 - JSON Web Signature (JWS)](https://www.rfc-editor.org/rfc/rfc7515)
- [RFC 7517 - JSON Web Key (JWK)](https://www.rfc-editor.org/rfc/rfc7517)
- [RFC 7519 - JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8725 - JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725)
- [RFC 9068 - JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
