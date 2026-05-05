# Security Best Practices

## What it is

Security best practices for this study are conservative controls that reduce common IAM, OAuth2, token, API, and administration risks. They are minimum expectations for the selected Central IAM Control Plane Architecture, not a final product or implementation design.

The most important principle is that identity systems are control planes. A weakness in authentication, token validation, role assignment, client management, or admin APIs can affect every protected backoffice service.

## Why it matters

The expected scale is modest, but security impact is not determined only by user count. A small internal backoffice can still expose member data, billing actions, operational controls, or privileged service access.

Good IAM security is mostly about avoiding known failure modes: weak credential handling, overbroad roles, token replay, missing audience checks, stale access, exposed secrets, unprotected admin APIs, and frontend-only authorization.

## Token and OAuth2 practices

Use short-lived access tokens unless there is a specific, documented reason not to. Short lifetimes reduce the damage from bearer token leakage.

Validate access tokens at resource servers. At minimum, check issuer, audience, lifetime, signature or introspection result, token type where applicable, and required authorization data.

Use Authorization Code Flow with PKCE for public browser-based clients. Do not use Implicit Flow for new browser applications.

Protect refresh tokens carefully. Where refresh tokens are used by public clients, rotation and reuse detection are important mitigations. Refresh tokens should be revocable.

Do not use ID tokens as API access tokens. ID tokens are intended for clients; APIs should validate access tokens intended for them.

Avoid putting unnecessary personal data, secrets, or high-churn authorization state into JWTs. Claims can leak to clients and logs, and stale claims can outlive role changes.

## API authorization practices

Enforce authorization on the server side. UI checks improve usability but do not protect APIs.

Use least privilege. Roles should contain only the permissions needed for a business function. Service accounts should have narrow service permissions rather than human administrator roles.

Prefer explicit permissions for sensitive operations. `members:delete`, `roles:assign`, and `clients:write` are easier to review than a generic `admin` flag.

Check authorization at the operation level. A subject allowed to list members is not automatically allowed to disable members or assign roles.

Design for denied requests. APIs should return consistent authorization failures and avoid leaking sensitive resource details through error messages.

## Admin and operational practices

Protect administration APIs as high-risk resource servers. Require strong administrator authorization, audit privileged mutations, and avoid exposing secret values after creation.

Keep audit logs for security-relevant events: login failures, token revocation, member creation or disabling, role assignment, client changes, service account changes, and permission changes.

Make access review possible. Administrators should be able to answer who has a role, what permissions a role grants, which clients exist, and which service accounts have access to each API.

Rate limit or otherwise protect sensitive endpoints such as login, token exchange, password reset if present, and admin mutation operations. The exact mechanism belongs to later implementation work.

Separate disabling from deletion. Disabling can stop access while preserving auditability and recovery options. Deletion may have data retention and compliance implications.

## Credential and secret practices

Never store passwords in plaintext. Password storage should use a purpose-built password hashing algorithm and parameters appropriate for the deployment. Do not build custom password hashing or cryptography.

Store client secrets and private keys in controlled secret storage, not source code, frontend bundles, logs, container images, or ticket comments.

Rotate credentials and keys. Key rotation needs operational planning so resource servers can validate old tokens during transition and reject tokens signed by retired keys after their useful lifetime.

Redact tokens and secrets from logs, traces, crash reports, analytics, and support tooling. Bearer tokens are credentials.

## Compliance and governance considerations

Even in Phase 1, the wiki should keep future compliance and governance questions visible:

- auditability of privileged changes;
- password and authenticator policy;
- access reviews for roles and service accounts;
- logging retention and privacy;
- incident response for token or secret compromise;
- data retention for disabled or deleted members;
- regulatory constraints relevant to the business domain.

These are requirements discovery topics, not a final compliance design.

## Example checklist

Before a protected API trusts a request, engineers should be able to explain:

- which authorization server or identity provider issued the token;
- which API the token is intended for;
- whether the token is expired or otherwise inactive;
- which subject and client the token represents;
- which permission the endpoint requires;
- where the permission came from;
- how the access can be revoked or allowed to expire;
- whether the action is audited.

## Common mistakes

Skipping issuer validation allows tokens from unexpected issuers.

Skipping audience validation allows tokens intended for one API to be replayed to another.

Using long-lived bearer access tokens increases the damage from logs, browser storage, proxies, or compromised clients.

Putting authorization only in the frontend leaves APIs exposed.

Giving service accounts human administrator roles makes automation credentials too powerful.

Inventing custom cryptography or token formats creates avoidable security risk. Use maintained libraries and standards-based protocols.

Ignoring audit and access review makes it difficult to detect and recover from mistakes.

## References

- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 8725 - JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
