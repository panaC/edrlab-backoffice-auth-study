# Administrator Authentication Policy

## What it is

Administrator authentication policy defines how privileged backoffice users prove their identity before they can manage IAM state.

It is related to, but separate from, authorization. Authentication answers whether the person signed in successfully. Authorization answers whether that signed-in administrator may create members, assign roles, rotate credentials, export audit logs, or perform another privileged operation.

This document is conceptual study material for Phase 1. It does not choose a vendor, authenticator type, MFA product, password policy, final break-glass process, or production implementation.

## Current study position

The current study baseline is intentionally small:

- the project remains limited to the internal backoffice;
- members are created manually by administrators;
- public registration is out of scope;
- the initial role model is simple: `admin` and `member`;
- the initial protected resource can be a demonstration API service;
- the administration API is consumed only by the backoffice UI through the BFF;
- access tokens are JWTs;
- removed access is allowed to expire at token expiry for the first study or PoC version;
- service-to-service authentication is a future theoretical extension, not part of the first study or PoC scope;
- auditability is a strong requirement;
- operational ownership is still to be defined.

Within that baseline, administrator authentication should be strong enough to protect a control plane, but simple enough for a minimal study and PoC.

## Why administrator authentication is special

An ordinary member login gives access to backoffice features. An administrator login can change who exists, who has access, which roles mean what, and which clients can call protected APIs. That gives administrator accounts a larger blast radius than ordinary user accounts.

The policy therefore needs to account for:

| Concern | Why it matters |
| --- | --- |
| Account takeover | A compromised administrator can create users, assign roles, disable members, or change clients. |
| Self-escalation | An administrator should not be able to grant permissions outside their authority. |
| Stale access | Removed admin access may remain active until JWT expiry in the first version. |
| Audit evidence | Privileged authentication and admin operations need enough evidence for incident review. |
| Recovery | Losing the only administrator account can lock the team out of the IAM control plane. |

These concerns do not require enterprise complexity in the first version. They do require deliberate policy choices.

## Minimal first-version baseline

For the first study and minimal PoC, use this baseline unless a later requirement changes it:

| Area | Baseline |
| --- | --- |
| Login protocol | Administrators authenticate through the same OIDC-compatible login path as other backoffice members. |
| Browser session | The browser holds only an HttpOnly session cookie managed by the BFF. OAuth tokens stay server-side. |
| Admin authorization | The admin API enforces `admin` role or explicit admin permissions server-side. UI checks are usability only. |
| Token format | Access tokens are JWTs. Resource servers validate issuer, audience, signature, expiry, and required permissions. |
| Access removal | Admin role removal or member disablement takes effect when existing short-lived access tokens expire. |
| Public signup | No public registration or self-service administrator creation. |
| Audit | Privileged admin operations must produce audit events. Admin login events, denied privileged attempts, member changes, role changes, and token or session invalidation decisions are first audit candidates. |
| Service callers | No machine caller can use the admin API in the initial PoC. Future service access is evaluated separately. |

This baseline favors a small number of understandable controls over a larger policy surface. The main security trade-off is that access removal is not immediate while an existing JWT is still valid. That trade-off is acceptable only if token lifetimes are short and high-risk changes are audited.

## MFA, step-up, and passwordless options

MFA should be evaluated for administrators because administrator accounts protect the IAM control plane. The study should distinguish three levels:

| Option | Where it fits | Trade-off |
| --- | --- | --- |
| No MFA in minimal PoC | Keeps the first PoC focused on OIDC login, JWT validation, RBAC, and admin API protection. | Does not prove the final administrator authentication posture. |
| MFA for all administrators | Strong default for privileged access. | Requires enrollment, recovery, lost-factor handling, and provider support. |
| Step-up authentication | Useful for high-risk actions such as role assignment, credential rotation, audit export, or break-glass activation. | Adds policy complexity and needs clear user experience and audit behavior. |

Passwordless authenticators or hardware-backed authenticators may be attractive later, especially for phishing resistance, but they should be evaluated against team usability, recovery, vendor support, and operational burden.

The study should not treat SMS or email codes as equal to stronger possession-based authenticators without documenting the risk. If a managed or self-hosted provider offers several factors, the evaluation should record which factors are supported, which are default, and which are realistic for the internal team.

## Break-glass access

Break-glass access is emergency administrator access for situations where normal administration is unavailable. It is not automatically required for the first PoC, but the study should decide whether production needs it.

If break-glass access is required later, it should be:

- limited to the smallest number of accounts or procedures;
- disabled or dormant during normal operation where possible;
- protected by stronger authentication than routine member access;
- monitored and audited separately;
- time-bound or reviewed immediately after use;
- documented with recovery steps and ownership.

The absence of break-glass access is also a risk: a provider outage, lost admin factors, bad role change, or misconfiguration can lock out legitimate operators. The final decision should explicitly accept one side of that trade-off.

## Evaluation prompts

When comparing managed, self-hosted, minimal-library, or hybrid options, ask:

- Can administrators be required to use MFA without forcing MFA on every ordinary member?
- Can the provider or implementation distinguish admin login from ordinary login in logs and policies?
- Can high-risk admin actions require step-up authentication if needed later?
- Can lost-factor recovery be handled without allowing easy account takeover?
- Can administrator access be removed, disabled, or allowed to expire in a predictable window?
- Can admin sessions, refresh tokens, and access tokens be revoked or expired during an incident?
- Can audit logs show administrator login, MFA enrollment or reset, privileged denial, and role assignment events?
- Can emergency access be designed without creating an unreviewed permanent super-admin path?

These are evidence-gathering questions, not a final policy recommendation.

## Common mistakes

Treating an authenticated member as an administrator without checking admin permissions exposes the control plane.

Relying only on the admin UI to hide privileged actions leaves the admin API vulnerable.

Using long-lived JWTs for administrator permissions makes removed access remain effective for too long.

Allowing administrators to reset their own MFA, grant themselves stronger roles, or create unmanaged break-glass accounts creates escalation paths.

Logging passwords, recovery codes, bearer tokens, refresh tokens, or client secrets turns audit and troubleshooting systems into credential stores.

Failing to plan administrator recovery can make the system secure in theory but unavailable in practice.

## Related documents

- [Authentication vs Authorization](./wiki/01-authentication-vs-authorization.md)
- [OpenID Connect](./wiki/03-openid-connect.md)
- [Tokens and JWTs](./wiki/04-tokens-and-jwt.md)
- [RBAC](./wiki/05-rbac.md)
- [Admin API](./wiki/08-admin-api.md)
- [Security Best Practices](./wiki/09-security-best-practices.md)
- [Auditability, Access Reviews, and Operational Ownership](./wiki/10-auditability-access-reviews-operational-ownership.md)

## Open study questions

- Is MFA required for production administrators, or only recommended for later evaluation?
- Which authenticator types are acceptable for administrators?
- Should high-risk operations require step-up authentication?
- Does production need break-glass access?
- Who approves administrator recovery, MFA reset, and emergency access?
- What is the maximum acceptable lifetime for an access token carrying administrator permissions?

## References

- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
- [NIST SP 800-63B - Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Multifactor Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
