# OAuth Client Management

## What it is

OAuth client management is the lifecycle of applications registered with an authorization server. It answers questions such as:

- which application is allowed to request tokens;
- which redirect URIs are valid for browser-based flows;
- which grant types and response types are enabled;
- whether the client is public or confidential;
- how the client authenticates at the token endpoint, if it can;
- which scopes, audiences, and token policies the client may use;
- who owns the client and who may update or disable it.

This page is conceptual learning material. It explains the vocabulary and risks around OAuth2/OIDC client registration without choosing a product, endpoint shape, database model, vendor API, or final architecture.

## Why it matters

An authorization server cannot issue tokens safely unless it knows the client that is asking. Client management exists because token issuance depends on registered policy:

| Question | Why the authorization server needs it |
| --- | --- |
| Is this `client_id` known? | Unknown clients should not receive tokens from normal authorization flows. |
| Which redirect URIs are allowed? | Authorization codes and login responses must not be sent to attacker-controlled locations. |
| Which grant types are allowed? | A browser-facing client should not automatically be allowed to use machine-to-machine flows. |
| Can this client keep a secret? | Public clients cannot prove identity with embedded secrets. |
| Which scopes or audiences may be requested? | The client should not be able to mint tokens for unrelated APIs. |
| Who owns this client? | Rotation, disablement, review, and incident response need accountable owners. |

Without a client registry, every token request becomes a special case. With a client registry, the authorization server can apply stable rules before issuing an authorization code, access token, ID token, or refresh token.

## Core concepts

| Concept | Meaning |
| --- | --- |
| Client | An application registered with the authorization server, such as a BFF, SPA, CLI, mobile app, backend service, or scheduled worker. |
| Client identifier | The public identifier for the registered client, usually sent as `client_id`. It is not a secret. |
| Client credential | A secret, private key, certificate, or other proof used by a confidential client to authenticate to the authorization server. |
| Client metadata | Registered data about a client, such as redirect URIs, grant types, response types, name, token endpoint authentication method, and key references. |
| Public client | A client that cannot keep long-term credentials confidential, such as a browser-only app or installed app. |
| Confidential client | A client that can protect credentials, such as a server-side BFF or backend service. |
| Redirect URI | A registered URI where the authorization server may send the user-agent after a redirect-based authorization request. |
| Grant type | A protocol flow the client is allowed to use, such as authorization code, refresh token, or client credentials. |
| Scope | Delegated access the client may request. The authorization server may grant less than was requested. |
| Audience | The resource server or API a token is intended for. Audience handling is essential when multiple APIs exist. |

The word "client" does not mean "frontend" or "user". A server-side BFF is a client. A backend job can be a client. A browser-only app can be a client. The important question is what security properties that client has.

## Public and confidential clients

OAuth2 distinguishes between clients that can protect credentials and clients that cannot. This distinction drives which controls make sense.

| Client type | Examples | Main control |
| --- | --- | --- |
| Confidential client | Server-side BFF, backend service, scheduled worker | Authenticate at the token endpoint with a protected credential where applicable. |
| Public client | Browser-only SPA, mobile app, desktop app, distributed CLI | Use protocol controls such as PKCE and strict redirect handling; do not rely on embedded secrets. |

A client secret in JavaScript, a mobile binary, a desktop app, or a public repository should be treated as exposed. It may identify the application in a weak operational sense, but it cannot prove that the caller is trustworthy.

A distributed application can have components with different security properties. For example, a browser frontend and a server-side BFF should not be treated as one undifferentiated client if they need different credentials, redirect URIs, token policies, or risk controls.

## What is registered

Some client metadata is standardized by OAuth2 dynamic client registration and OpenID Connect registration. Other metadata is operational governance data that an internal control plane usually needs, even though OAuth2 does not standardize it.

Protocol-facing metadata:

| Field | Purpose |
| --- | --- |
| `client_id` | Stable public identifier issued by the authorization server. |
| `client_name` | Human-readable name for operators and consent screens where applicable. |
| `redirect_uris` | Allowed redirect targets for authorization responses. |
| `grant_types` | Grant types the client may use, such as `authorization_code`, `refresh_token`, or `client_credentials`. |
| `response_types` | Authorization endpoint response types the client may request. |
| `scope` | Scopes the client is allowed to request by default or at registration time. |
| `token_endpoint_auth_method` | How the client authenticates to the token endpoint, such as a client secret, private key JWT, mTLS, or `none` for a public client. |
| `jwks_uri` or `jwks` | Public keys used to verify client assertions or other key-based client behavior. |
| `client_uri`, `logo_uri`, `policy_uri`, `tos_uri` | Optional human-facing metadata, more relevant when users or admins review third-party clients. |

Operational metadata:

| Field | Purpose |
| --- | --- |
| Owner | Team, service, or administrator responsible for the client. |
| Purpose | Why the client exists and which workflow it supports. |
| Environment | Development, staging, production, or another deployment boundary. |
| Status | Draft, active, disabled, or retired state. |
| Allowed audiences | APIs or resource servers for which this client may receive tokens. |
| Credential metadata | Secret/key creation time, rotation time, expiry, and last-used information without revealing secret material. |
| Risk level | Whether updates require approval, step-up authentication, or extra review. |
| Audit metadata | Who created or changed the client, what changed, and why. |

Not every implementation exposes all fields directly. The important concept is that token issuance must be constrained by registered client policy, and privileged changes to that policy should be accountable.

## Environment separation

Development, staging, and production clients should be separate registrations unless a later implementation has a strong reason to combine them. Environment separation keeps unsafe test callbacks, broad local scopes, and experimental credentials away from production token issuance.

| Concern | Practical guidance |
| --- | --- |
| Redirect URIs | Keep localhost, development, staging, and production redirect URIs in separate clients where possible. |
| Credentials | Use different secrets, keys, or certificates per environment. |
| Allowed scopes | Do not let a development client request production administration scopes. |
| Audiences | Production APIs should not accept tokens minted for development or staging audiences. |
| Owners | Each environment should still have an owner and purpose, even if the same team owns all of them. |
| Rotation | Rotate credentials per environment so a development leak does not force an emergency production rotation. |
| Disablement | Retire stale development and staging clients; do not leave old callbacks active indefinitely. |

Environment separation also helps incident response. If a staging client secret leaks, operators should be able to disable or rotate that staging client without disturbing production clients.

## Registration models

There are two broad registration models:

| Model | Meaning | Typical use |
| --- | --- | --- |
| Admin-managed registration | An administrator or approved automation creates and updates clients through an admin console or administration API. | Internal systems with controlled client inventory. |
| Dynamic client registration | A client or developer programmatically registers client metadata with the authorization server. | Ecosystems with many clients, external developers, or deployments that cannot preconfigure all clients manually. |

OAuth2 dynamic client registration defines a standard protocol for creating clients and registering metadata. A companion experimental RFC describes a management protocol for reading, updating, and deleting dynamic client registrations.

Dynamic registration does not mean open registration. It can be protected with an initial access token, software statement, approval workflow, or other policy. The key governance question is not "can dynamic registration exist?" but "who is authorized to create or mutate a client, and how is that change reviewed and audited?"

## Redirect URI management

Redirect URIs are one of the most important client controls for browser-based flows. During Authorization Code Flow, the authorization server sends the user-agent back to a redirect URI with an authorization code. If redirect URI validation is loose, codes can be leaked to the wrong place.

Useful rules:

- register exact redirect URIs for each environment;
- avoid broad wildcard redirect rules;
- avoid open redirectors as registered callback targets;
- prefer HTTPS for web clients;
- keep development redirect URIs separate from production clients;
- remove unused callbacks;
- audit additions and changes to redirect URIs;
- bind the authorization response to the client transaction with `state`;
- use PKCE for authorization code flows, especially for public and browser-facing clients.

Redirect URI management belongs in the client registry because the authorization server must check it before issuing or redeeming an authorization code.

## Grant and flow constraints

Each client should be allowed to use only the flows it actually needs. A client registration that enables every grant type expands the attack surface.

| Client shape | Flow to understand | Notes |
| --- | --- | --- |
| Server-side BFF for a browser UI | Authorization Code Flow with PKCE, usually with OIDC | The BFF may be confidential and can keep tokens server-side, while PKCE still protects the code exchange. |
| Browser-only or installed public client | Authorization Code Flow with PKCE | Do not rely on a client secret embedded in distributed code. |
| Backend service or worker | Client Credentials Flow | The token represents the service client, not a human user. |
| Long-lived user session | Refresh Token Flow or reauthorization | Refresh token issuance should depend on client type, storage, rotation, and revocation policy. |

Flows are explained in [OAuth2 Flows](./06-oauth2-flows.md). Client management is where the authorization server records which of those flows a specific client may use.

The safest default is deny-by-default for flows: a client receives no grant type unless the owner can explain why it is needed.

## Client credentials and authentication methods

Confidential clients may authenticate at the token endpoint. Common methods include:

| Method | How it works | Management concern |
| --- | --- | --- |
| Client secret | The client presents a shared secret. | Generate high-entropy secrets, store them safely, show them only at creation or rotation time, rotate them, and never log them. |
| Private key JWT | The client signs an assertion with a private key; the authorization server verifies it with registered public key material. | Manage key registration, key rollover, assertion lifetime, and private key protection. |
| Mutual TLS | The client authenticates with a certificate during the TLS connection. | Manage certificate issuance, renewal, trust anchors, deployment rollout, and failure modes. |
| None | Public clients do not authenticate with a long-term secret. | Use PKCE, redirect constraints, and client-specific policy instead of pretending a public secret is confidential. |

Client authentication is not the same as user authentication. A confidential client can prove that the server-side application is the registered client, but it does not prove which human user is signed in. User identity comes from the login flow and token subject.

For the dedicated key and secret lifecycle model, see [Key Management and Signing Keys](./23-key-management-and-signing-keys.md).

## Scopes, audiences, roles, and permissions

Client management should constrain what a client can ask for, but it does not replace application authorization.

| Layer | Question |
| --- | --- |
| Client allowed scopes | What access may this client request? |
| Granted scopes | What access did the authorization server actually include in this token? |
| Token audience | Which API should accept this token? |
| Roles and permissions | What may the subject do inside the API or business domain? |
| Resource server enforcement | Does this request satisfy the operation-specific policy? |

A client allowed to request `members:read` should not automatically be allowed to request `members:disable`. A service client for reporting should not receive tokens for the administration API unless that is explicitly intended and authorized.

See [RBAC](./05-rbac.md) for roles and permissions, and [Tokens and JWTs](./04-tokens-and-jwt.md) for token claims, audiences, and validation.

## Client lifecycle

Client lifecycle states are implementation-specific, but the concept is useful:

| State | Meaning | Token behavior to define |
| --- | --- | --- |
| Draft | Client metadata is being prepared but should not yet receive production tokens. | No production grants. |
| Active | Client may use its configured flows and policies. | Normal token issuance. |
| Disabled | Client is temporarily blocked. | New grants should stop; existing tokens need an expiry, revocation, or introspection policy. |
| Rotating | Client has overlapping old and new credentials during a controlled rollout. | Both credentials may be accepted for a short, audited window. |
| Retired | Client is no longer used and should not be reactivated casually. | New grants stop; old credentials and callbacks should be removed or invalidated. |
| Deleted | Client registration is removed where retention policy permits. | Audit history should still preserve stable references. |

Disabling a client is not the same as deleting it. Rotating a secret is not the same as disabling the client. Revoking a refresh token is not the same as blocking all future token grants. These operations should be modeled separately so incident response is predictable.

## Administration and audit

Client management is a privileged control-plane function. Updating a client can change where authorization codes are sent, which flows are enabled, what APIs tokens can target, and which credentials can authenticate.

Typical audit events include:

| Event | Why it matters |
| --- | --- |
| `client.created` | A new application can request tokens. |
| `client.updated` | Metadata changed and may affect token behavior. |
| `client.redirect_uri_added` | A new browser callback location became trusted. |
| `client.grant_type_enabled` | A new flow became available to the client. |
| `client.scope_allowed` | The client may request broader delegated access. |
| `client.secret_rotated` | Credential material changed. |
| `client.disabled` | Future grants should stop. |
| `client.deleted` or `client.retired` | The client left the active inventory. |

Audit logs should record actor, client, action, target, result, timestamp, request context, and a safe change summary. They should not record client secret values, private keys, bearer tokens, authorization codes, refresh tokens, or one-time recovery material.

See [Admin API](./08-admin-api.md) and [Auditability, Access Reviews, and Operational Ownership](./10-auditability-access-reviews-operational-ownership.md) for the broader administration and governance concepts.

## Runtime effects

Client updates can affect both future and already-issued credentials:

| Change | Future grants | Already-issued tokens |
| --- | --- | --- |
| Disable client | Should stop new authorization and token grants. | Access tokens may remain valid until expiry unless introspection or revocation policy checks client state. |
| Remove redirect URI | Should stop new authorization responses to that URI. | Already-issued tokens are usually unaffected. |
| Remove allowed scope | Should stop future grants for that scope. | Existing JWT access tokens may keep old claims until expiry. |
| Rotate secret | New token requests should use the new secret after rollout. | Existing access tokens are usually unaffected; refresh token behavior depends on policy. |
| Delete client | Should stop new grants. | Audit and stable references still matter for incident response. |

This is why token lifetime, revocation, introspection, and client status checks need to be considered together. See [Token Lifecycle](./12-token-lifecycle.md) for the dedicated token lifecycle model and [Tokens and JWTs](./04-tokens-and-jwt.md) for token validation trade-offs.

## Common mistakes

Treating `client_id` as a secret. It is normally public and appears in authorization requests, logs, and configuration.

Embedding a client secret in browser or mobile code. Distributed code cannot keep that secret confidential.

Allowing broad or wildcard redirect URIs. Loose redirect matching can leak authorization codes or tokens.

Enabling every grant type for convenience. Each client should have the minimum flow set needed for its purpose.

Sharing one client across unrelated applications. Shared clients make rotation, audit, least privilege, and incident response harder.

Letting low-risk clients request high-risk scopes or audiences. Client policy should constrain what tokens can be minted.

Failing to record an owner and purpose. Orphan clients often survive long after the application is gone.

Returning client secrets from read endpoints. Secrets should be shown only at creation or rotation time, if at all.

Logging authorization codes, bearer tokens, refresh tokens, client secrets, or private keys.

Disabling a client without understanding existing tokens. New grants may stop immediately while already-issued JWTs remain valid until expiry.

Treating service clients as human users. Machine clients should have distinct subjects, credentials, permissions, and audit trails.

## Concept checklist

When reading a product manual, provider API, or future project design, engineers should be able to answer:

- Which components are OAuth2/OIDC clients?
- Which clients are public and which are confidential?
- Which client owns each redirect URI?
- Which grant types are enabled per client?
- Which scopes and audiences can each client request?
- Which token endpoint authentication method is used per confidential client?
- How are client secrets, public keys, or certificates rotated?
- Who can create, update, disable, delete, or rotate a client?
- Are client changes audited with safe before/after metadata?
- What happens to active sessions, refresh tokens, and access tokens when a client is disabled?
- Are development, staging, and production clients separated?
- Are unused clients and redirect URIs reviewed and retired?

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7523 - JSON Web Token (JWT) Profile for OAuth 2.0 Client Authentication and Authorization Grants](https://www.rfc-editor.org/rfc/rfc7523)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration Protocol](https://www.rfc-editor.org/rfc/rfc7591)
- [RFC 7592 - OAuth 2.0 Dynamic Client Registration Management Protocol](https://www.rfc-editor.org/rfc/rfc7592)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 8705 - OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens](https://www.rfc-editor.org/rfc/rfc8705)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Dynamic Client Registration 1.0](https://openid.net/specs/openid-connect-registration-1_0.html)
