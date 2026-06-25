# 0003 - Accept OTP for Privileged Authentication

Status: Accepted
Date: 2026-06-25
Supersedes: none

## Context

`FR-034` requires production `admin` and `super-admin` authentication to use MFA or phishing-resistant passwordless authentication, with the exact authenticator choice deferred to evaluation ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The dedicated `WP-013` Docker runtime validated a Keycloak ACR/LoA step-up path using OTP: normal admin authentication was denied for privileged onboarding, admin and super-admin authentication with `edrlab-privileged` ACR was accepted by the IAM Control Plane API fixture, and a mismatched-subject attempt was denied ([Keycloak WP-013 result](../poc/keycloak-wp013-result.md#runtime-execution)). Keycloak documents step-up authentication and ACR-to-LoA mapping, and OpenID Connect defines the `acr` claim used as the server-validated evidence ([Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism), [Keycloak ACR to LoA mapping](https://www.keycloak.org/docs/latest/server_admin/#_acr-loa), [OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken)).

User decision on 2026-06-25: OTP is acceptable for admins. This record treats `admin` and `super-admin` as the privileged account types covered by this decision unless a later decision creates a stricter split.

## Options Considered

| Option | Outcome |
| --- | --- |
| Require WebAuthn/passkeys before continuing. | Rejected as a blocker for the first validation direction. WebAuthn/passkeys remain a possible hardening path. |
| Accept OTP MFA for privileged accounts. | Accepted for the current Keycloak IAM plus EDRLab IAM Control Plane API direction. |

## Decision

Accept OTP MFA as sufficient privileged-authentication evidence for `admin` and `super-admin` onboarding in the current target direction, provided that:

- Keycloak emits explicit ACR/LoA evidence for the current authentication attempt;
- the EDRLab IAM Control Plane API validates issuer, audience, expiry, nonce/session binding where applicable, subject, and the expected privileged `acr`;
- activation fails closed when the privileged `acr` is missing, stale, weaker than required, or belongs to another subject;
- OTP enrollment, reset, recovery, and administrative intervention are audited and reviewed before production rollout.

WebAuthn/passkeys are not required to unblock Phase 5 review or the first production design decision. They remain a future security-hardening option.

## Consequences

- The `WP-013` PoC blocker is closed for the current review path.
- Phase 5 can treat OTP MFA as accepted for the current direction; WebAuthn/passkeys remain future hardening candidates, not a current blocker.
- Production design still needs recovery policy, OTP enrollment governance, reset controls, rate limiting, monitoring, and audit storage.
- OTP MFA is not phishing-resistant. NIST SP 800-63B distinguishes phishing-resistant authenticators from other MFA patterns, so this decision accepts a lower operationally simpler assurance path rather than the strongest available authenticator class ([NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)).
- This decision does not approve Phase 6 production MVP implementation; Phase 6 still requires explicit project movement ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](../poc/keycloak-wp013-result.md)
- [Keycloak Step-Up Authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)
- [Keycloak ACR to LoA Mapping](https://www.keycloak.org/docs/latest/server_admin/#_acr-loa)
- [OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
