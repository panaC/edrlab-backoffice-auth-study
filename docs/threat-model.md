# Threat Model

This document records concrete abuse scenarios for the internal backoffice IAM study. It is intentionally practical: what can go wrong, how the system should reduce the risk, and what evidence should exist during review or incident response.

This is Phase 1 study material. It does not choose a final threat modeling method, risk scoring model, security tool, provider, or production control set.

## Scope

The modeled system is the selected Central IAM Control Plane Architecture:

```text
Browser
  -> Backoffice BFF
  -> IdP / Authorization Server / Admin Control Plane
  -> backend API resource servers
```

Primary assets:

- member identities and lifecycle state;
- administrator authority;
- roles, permissions, and role assignments;
- OAuth2/OIDC client registrations;
- authorization codes, access tokens, ID tokens, refresh tokens, and sessions;
- signing keys, client secrets, and service credentials;
- audit logs and access-review evidence;
- protected backoffice APIs and service data.

Primary trust boundaries:

- browser to BFF;
- BFF to authorization server and admin API;
- BFF to backend resource servers;
- resource servers to authorization server metadata, JWKS, introspection, or authorization lookup;
- administrators to privileged admin API operations;
- operations team to backups, logs, keys, and break-glass procedures.

## Method

This document uses a lightweight STRIDE-style structure:

| STRIDE category | IAM examples |
| --- | --- |
| Spoofing | Stolen session cookie, stolen token, fake client, wrong issuer. |
| Tampering | Role assignment abuse, redirect URI change, token claim manipulation, audit log alteration. |
| Repudiation | Missing audit events, mutable names without stable IDs, unaudited break-glass. |
| Information disclosure | Token or secret leakage, audit export exposure, overbroad member reads. |
| Denial of service | Locking out admins, breaking token validation, IAM/provider outage. |
| Elevation of privilege | Self-escalation, broken audience validation, overbroad service account, compromised admin. |

The threat model should be maintained. It should change when the architecture, provider, token strategy, admin API, BFF behavior, or operational model changes.

## Scenario matrix

| Scenario | What can go wrong | Primary controls |
| --- | --- | --- |
| Stolen browser session cookie | Attacker uses an active BFF session as the user. | HttpOnly Secure SameSite cookie, session hash storage, CSRF controls, idle/absolute timeout, logout and revocation. |
| Stolen access token | Attacker calls APIs until expiry. | Short-lived tokens, audience validation, issuer validation, signature/introspection, token redaction, revocation/introspection for high-risk paths. |
| Stolen refresh token | Attacker mints new access tokens. | Server-side storage, encryption or vaulting, refresh rotation, reuse detection, revocation on logout/disablement. |
| Authorization code interception | Attacker redeems code. | PKCE, exact redirect URI validation, state, short code lifetime, one-time use. |
| CSRF against BFF | Browser sends authenticated state-changing request. | SameSite, CSRF token, Origin/Referer validation, unsafe operations on non-GET methods. |
| XSS in backoffice UI | Attacker drives user session or calls BFF actions. | Keep tokens out of browser storage, output encoding, CSP where feasible, CSRF protections, operation-level authorization, audit. |
| Compromised administrator | Attacker changes members, roles, clients, or audit access. | MFA/step-up, least privilege, self-escalation guardrails, audit, access review, incident playbook. |
| Bad role assignment | Member receives access they should not have. | Grant boundaries, role review, audit, short token lifetime, removal workflow. |
| Self-escalation | Admin grants themselves stronger role or changes role they hold. | Target-aware authorization, cannot grant beyond authority, approval or step-up for sensitive role changes. |
| Broken audience validation | API accepts token intended for another API. | Per-API audience validation, tests for wrong audience, resource-server configuration review. |
| Wrong issuer or environment mix-up | Dev/staging token accepted in production. | Issuer allowlist, environment-separated clients, metadata pinning, deployment tests. |
| Loose redirect URI validation | Authorization code sent to attacker-controlled endpoint. | Exact redirect URI registration, no broad wildcards, audit redirect changes. |
| Client secret leak | Attacker authenticates as confidential client. | Secret storage, rotation, per-environment credentials, least-privilege scopes, audit. |
| Signing key compromise | Attacker forges tokens. | Key protection, key inventory, emergency rotation, JWKS propagation, incident playbook. |
| Audit tampering or loss | Investigation cannot reconstruct privileged actions. | Append-oriented logs, restricted audit access, audit export, monitor logging failures, backup/retention. |
| Break-glass abuse | Emergency path becomes permanent bypass. | Dormant account/procedure, time-bound activation, alerting, separate audit, post-use review. |
| IAM outage | Users cannot log in or tokens cannot be validated. | Monitoring, restore plan, fail-closed decisions, cached JWKS behavior, backup/restore tests. |

## Detailed scenarios

### Stolen token

An attacker obtains an access token from logs, browser storage, a proxy, a crash report, or a compromised BFF/session store.

Expected mitigations:

- do not store OAuth tokens in browser-readable storage for the BFF architecture;
- redact bearer tokens, authorization codes, refresh tokens, and session IDs from logs;
- keep access tokens short-lived;
- validate issuer, audience, signature or introspection result, lifetime, and required permission at each resource server;
- use token revocation, introspection, or authorization lookup where immediate denial is required;
- audit suspicious token validation failures and incident response actions.

Residual risk:

- a self-contained JWT access token may remain usable until expiry if the resource server validates it locally and no revocation-aware path exists.

### Compromised administrator

An attacker controls an administrator account through phishing, credential theft, device compromise, or recovery abuse.

Expected mitigations:

- require strong authentication for administrators in production evaluation;
- consider step-up for role assignment, client updates, credential rotation, audit export, and recovery reset;
- prevent administrators from granting themselves roles outside their authority;
- protect last-admin and break-glass paths from accidental or malicious disablement;
- audit member, role, client, credential, and audit-log operations;
- review recent changes by the compromised administrator during incident response.

Residual risk:

- an administrator with broad legitimate authority can still cause damage before detection. Monitoring and access review reduce but do not eliminate this risk.

### Bad role assignment

An administrator accidentally assigns `admin` or another privileged role to the wrong member, or grants a role containing broader permissions than expected.

Expected mitigations:

- keep role names and permission membership reviewable;
- show role effects before assignment in admin workflows;
- require reason or ticket for privileged assignment;
- audit role assignment and removal;
- prevent assignment outside the actor's grant boundary;
- define role-removal latency in the token lifecycle;
- run periodic access reviews for administrator roles.

Residual risk:

- if roles or permissions are embedded in JWT access tokens, the mistaken access may remain effective until token expiry unless stronger runtime controls exist.

### Broken audience validation

A resource server accepts an access token minted for a different API, allowing a low-risk token to be replayed against a high-risk endpoint.

Expected mitigations:

- each API validates expected `aud` or equivalent resource indicator;
- tests include wrong-audience tokens;
- admin API has a distinct audience from ordinary backoffice APIs;
- clients are constrained to allowed audiences;
- token validation configuration is reviewed during deployment and upgrade.

Residual risk:

- provider-specific token formats can make audience semantics confusing. Evaluation must verify exact behavior rather than assume standard-looking claims are enforced correctly.

### Loose redirect URI or client registration

An attacker adds or abuses a redirect URI so an authorization code is sent to an attacker-controlled endpoint.

Expected mitigations:

- register exact redirect URIs;
- avoid broad wildcards and open redirectors;
- separate development, staging, and production clients;
- audit redirect URI changes;
- use PKCE and short-lived one-time authorization codes;
- restrict who can create or update clients.

Residual risk:

- PKCE reduces the value of a stolen code but does not make unsafe redirect management acceptable.

### Recovery or MFA reset abuse

An attacker convinces support or an administrator to reset MFA, change email, or activate a recovery path for a privileged member.

Expected mitigations:

- model recovery and authenticator reset as privileged lifecycle operations;
- use separate permissions for recovery where useful;
- avoid unsafe self-reset by administrators;
- require step-up, approval, or notification for administrator recovery;
- audit reset events without storing recovery secrets;
- review restored administrator access after recovery.

Residual risk:

- recovery processes are partly human. The system should make unsafe recovery visible and difficult, not rely only on memory.

### Audit loss or tampering

An attacker or mistaken administrator deletes, alters, or prevents audit events for privileged IAM changes.

Expected mitigations:

- restrict audit-log read, export, retention, and deletion operations;
- audit audit-log reads and exports;
- monitor logging failures;
- back up audit evidence;
- use stable IDs and safe before/after summaries;
- keep secrets out of logs;
- export audit data where product lock-in or console-only evidence would block review.

Residual risk:

- audit logs can contain sensitive personal and operational data. Access and retention need privacy and security review.

## Abuse-case test checklist

A later PoC or implementation should include tests or manual verification for:

- API rejects access token with wrong issuer;
- API rejects access token with wrong audience;
- API rejects expired token;
- API rejects token missing required permission;
- member cannot call admin-only endpoints;
- admin cannot assign themselves a stronger role;
- admin cannot disable the last administrator path;
- disabled member cannot start new login or refresh access;
- role removal stops access within the documented latency window;
- BFF state-changing route rejects missing/invalid CSRF token;
- OAuth callback rejects wrong `state`;
- token endpoint exchange requires PKCE verifier where applicable;
- client read endpoint never returns existing secrets;
- redirect URI updates are audited;
- audit-log export is itself audited.

## Threats to revisit later

These require more detail when the final stack or provider is known:

- provider-specific token claim semantics;
- exact refresh-token rotation and reuse-detection behavior;
- exact OIDC logout behavior;
- JWKS caching behavior in each resource server framework;
- password, passkey, MFA, and recovery implementation;
- database backup encryption and restore process;
- admin UI XSS and frontend dependency risks;
- service-to-service authentication if it enters scope;
- multi-environment deployment and secret distribution;
- provider outage and managed-vendor incident response.

## Related documents

- [Security Best Practices](./wiki/09-security-best-practices.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Operational Model](./operational-model.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Member Lifecycle](./member-lifecycle.md)
- [Token Lifecycle](./wiki/12-token-lifecycle.md)
- [OAuth Client Management](./wiki/13-oauth-client-management.md)
- [Admin API](./wiki/08-admin-api.md)

## References

- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- [OWASP API Security Top 10 - 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [NIST SP 800-30 Rev. 1 - Guide for Conducting Risk Assessments](https://csrc.nist.gov/pubs/sp/800/30/r1/final)
- [NIST SP 800-61 Rev. 3 - Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
