# Keycloak WP-013 Result - Privileged Authentication Evidence

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Runtime Execution](#runtime-execution)
- [Accepted Evidence Model](#accepted-evidence-model)
- [Privileged Activation Contract](#privileged-activation-contract)
- [Scenario Matrix](#scenario-matrix)
- [Rejected Evidence](#rejected-evidence)
- [Runtime Evidence To Produce](#runtime-evidence-to-produce)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-013` defines how the Keycloak IAM plus EDRLab IAM Control Plane API validation should prove the privileged-authentication requirement for invited `admin` and `super-admin` onboarding. It closes the documentation-first design gap left by `WP-010` and `WP-012`: member onboarding can be validated with safe identity matching, but privileged onboarding also needs explicit evidence that `FR-034` was satisfied ([Keycloak WP-010 result](./keycloak-wp010-result.md), [Keycloak WP-012 result](./keycloak-wp012-result.md), `FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

This result now includes a dedicated Docker runtime validation for `WP-013`. It remains non-production PoC evidence: it does not add production code, production dependencies, database schema, CI, deployment artifacts, durable audit storage, or production approval ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp), [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Result

Use Keycloak step-up authentication with `acr` / Level of Authentication as the primary privileged-authentication evidence for the first validation slice.

Runtime decision: `pass` for the PoC slice executed on 2026-06-25. The script configured a PoC-only Keycloak ACR-to-LoA mapping, bound a PoC-only browser step-up flow, enrolled OTP credentials through Keycloak `CONFIGURE_TOTP`, requested `edrlab-privileged` in OIDC authentication, verified ID-token signatures and claims, and recorded IAM Control Plane API fixture decisions. Keycloak documents ACR-to-LoA mapping and step-up authentication, while OpenID Connect defines the `acr` claim and authentication request parameters used by the scenario ([Keycloak ACR to LoA mapping](https://www.keycloak.org/docs/latest/server_admin/#_acr-loa), [Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism), [OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken), [OpenID Connect Core - Authentication Request](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)).

The first acceptable privileged evidence target is:

- a Keycloak browser flow that requires a higher LoA for privileged onboarding;
- a realm-level or client-level ACR-to-LoA mapping for an EDRLab privileged value such as `edrlab-privileged`;
- an onboarding authentication request that explicitly asks Keycloak for that privileged ACR value;
- an ID token or equivalent server-validated authentication result whose `acr` claim proves that the requested privileged level was reached;
- local IAM Control Plane API verification that the privileged evidence belongs to the current subject and current onboarding attempt, not to an unrelated old session.

Keycloak documents ACR-to-LoA mapping, step-up authentication, the use of OIDC `claims` / `acr_values`, and the need for clients to check the resulting `acr` claim in the token ([Keycloak ACR to LoA mapping](https://www.keycloak.org/docs/latest/server_admin/#_acr-loa), [Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)). OpenID Connect defines `acr` as an Authentication Context Class Reference value in the ID Token and defines `acr_values` as a way to request authentication context values ([OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken), [OpenID Connect Core - Authentication Request](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)).

`amr` evidence remains optional and supplemental for this PoC. RFC 8176 defines Authentication Method Reference values, but this validation must not assume `amr` is present or meaningful unless the Keycloak runtime explicitly emits and verifies it ([RFC 8176](https://www.rfc-editor.org/rfc/rfc8176)).

## Runtime Execution

Environment:

- Runtime: Docker Compose Keycloak PoC under [`poc/keycloak`](../../poc/keycloak/README.md).
- Command: `bash poc/keycloak/scripts/verify-iam-control-plane-wp013.sh`.
- Runner: PoC-only `python:3.13-alpine` container joined to the Keycloak container network.
- Final evidence directory: [`poc/keycloak/evidence/20260625T152839Z`](../../poc/keycloak/evidence/20260625T152839Z/).
- Final summary file: [`wp-013-summary.json`](../../poc/keycloak/evidence/20260625T152839Z/wp-013-summary.json).

The runtime passed these checks:

| Scenario | Expected | Observed | Runtime decision |
| --- | --- | --- | --- |
| Admin onboarding with normal `acr` only | Deny activation. | Denied with `privileged_acr_missing_or_low`. | Pass. |
| Admin onboarding with current `edrlab-privileged` `acr` | Allow activation fixture. | Allowed with `verified_invitation_with_current_privileged_acr`. | Pass. |
| Super-admin onboarding with current `edrlab-privileged` `acr` | Allow activation fixture. | Allowed with `verified_invitation_with_current_privileged_acr`. | Pass. |
| Privileged `acr` for a different subject | Deny activation. | Denied through mismatch checks. | Pass. |

Operational findings:

- The PoC runner had to intercept the final OIDC redirect to the local backoffice callback because no production backoffice service is part of the PoC runtime.
- The runner had to treat Keycloak dev-mode `localhost` secure cookies as a local PoC browser-simulation shortcut; this does not validate production HTTPS cookie behavior.
- Keycloak OTP setup rejected immediate reuse of the same TOTP window, so the runner waits for the next TOTP period before performing step-up login.
- Failed intermediate evidence directories were removed after the passing run because early debug pages could expose PoC TOTP setup material. The passing evidence does not store raw tokens, refresh tokens, ID tokens, or TOTP secrets.

## Accepted Evidence Model

| Evidence layer | Required for first validation | Why it matters |
| --- | --- | --- |
| Keycloak flow configuration | Yes. A documented flow must require a privileged step such as OTP or WebAuthn/passkey for the requested privileged LoA. | Configuration evidence proves the privileged level is not just a token label. Keycloak documents OTP, WebAuthn, passkeys, and step-up flows as configurable authentication mechanisms ([Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows), [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn), [Keycloak passkeys](https://www.keycloak.org/docs/latest/server_admin/#passkeys)). |
| `acr` / LoA mapping | Yes. `edrlab-privileged` or equivalent must map to the privileged LoA in Keycloak. | The IAM Control Plane API needs a stable value to verify in the authentication result rather than inferring from UI or admin memory. |
| Token or server-side auth result | Yes. The IAM Control Plane API must verify the current login result contains the privileged `acr`. | Keycloak documentation says clients are encouraged to check the ID Token to confirm the expected `acr` after authentication ([Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)). |
| Current-attempt freshness | Yes. The privileged level should be fresh for onboarding. For PoC validation, use `Max Age=0` or an explicitly documented short lifetime. | Keycloak documents `Max Age=0` for LoA as valid for the current authentication only, which avoids relying on an old SSO session for privileged activation ([Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)). |
| Authenticator category | Yes. The runtime result must record whether the privileged step is OTP-based MFA or WebAuthn/passkey/passwordless. | `FR-034` allows MFA or phishing-resistant passwordless; NIST SP 800-63B distinguishes stronger assurance levels and requires phishing-resistant authentication at AAL3 while AAL2 requires two factors ([NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)). |
| Keycloak events | Supplemental. Use events to correlate login and admin-side configuration, not as the sole proof. | Events help audit correlation, but the IAM Control Plane API must still verify the authentication result and record local business audit. |
| Local IAM Control Plane API audit | Yes. Activation, denial, and blocker decisions must be recorded locally. | Keycloak events do not express the EDRLab business rationale required by `FR-027`, `FR-043`, and `FR-044`. |

## Privileged Activation Contract

For `admin` and `super-admin` onboarding activation, the IAM Control Plane API must:

1. Run all safe onboarding checks from `WP-012`: exactly one invited account, matching verified email, no existing `edrlab.linked_subject`, and exactly one account-type role.
2. Require a current privileged authentication result for the same Keycloak `sub`.
3. Verify the ID token or server-side authentication result signature, issuer, audience, expiration, nonce/session binding where applicable, subject, and `acr`.
4. Require the `acr` value to equal the configured privileged value, such as `edrlab-privileged`.
5. Record the configured privileged method class: OTP MFA, WebAuthn second factor, passkey/passwordless, or another reviewed mechanism.
6. Link `edrlab.linked_subject` and set `edrlab.lifecycle=active` only after all checks pass.
7. Keep the account `invited`, deny access, and audit the blocker if privileged evidence is missing, stale, weaker than required, mismatched to another subject, or impossible to verify.

This keeps the `FR-043` privileged-account exception narrow: authentication alone is not activation, and a privileged authentication result only helps after the safe account match has already succeeded.

## Scenario Matrix

| Scenario | Expected IAM Control Plane API result | Key evidence |
| --- | --- | --- |
| Invited admin with valid privileged `acr` | Activate, link subject, write local audit, and allow later access according to account type and lifecycle. | OIDC/token validation evidence, `acr=edrlab-privileged`, Keycloak flow config, before/after attributes, local activation audit. |
| Invited super-admin with valid privileged `acr` | Activate, link subject, write local audit, and allow later access according to account type and lifecycle. | Same as admin, plus super-admin account-type evidence. |
| Invited admin with only normal login LoA | Block activation, keep `invited`, do not link subject, deny backoffice access. | Token with lower or missing `acr`, local blocker audit `privileged_auth_evidence_missing_or_low`. |
| Invited super-admin with OTP/WebAuthn performed but no verifiable `acr` | Block activation unless the runtime has another explicit, documented, server-verified proof. | Flow/event evidence plus blocker explaining why token/auth result was not explicit enough. |
| Privileged `acr` belongs to another subject | Block activation and audit subject mismatch. | Current onboarding subject, token subject, denial audit. |
| Privileged `acr` is stale | Block activation and require fresh step-up. | Token/session timing evidence, `max_age` or LoA max-age evidence, denial audit. |
| `amr` present but `acr` absent | Treat as supplemental only; block unless a reviewed runtime contract makes `amr` explicit and reliable. | Token claims, RFC 8176 value interpretation, blocker or accepted supplemental note. |
| Privileged auth succeeds but safe onboarding match fails | Deny; do not link or activate. | Duplicate/no-match/unverified-email evidence from `WP-012`, denial audit. |
| Direct Keycloak Admin Console activates admin lifecycle without IAM Control Plane API evidence | Treat as drift; deny or quarantine through IAM Control Plane API and protected-service checks. | Keycloak admin event, before/after attributes, local drift audit. |

## Rejected Evidence

| Evidence candidate | Status | Reason |
| --- | --- | --- |
| Raw account-type role claim | Rejected. | Account type proves authorization category, not authentication strength. |
| Keycloak user has an OTP or WebAuthn credential registered | Rejected as sole proof. | Credential registration does not prove the current onboarding authentication used that credential. |
| A visible login screen that included OTP/WebAuthn | Rejected as sole proof. | UI inspection is not enough for automated server-side activation. |
| Keycloak admin event only | Rejected as sole proof. | Admin/user events are supplemental correlation, not the IAM Control Plane API's verified authentication result. |
| Long-lived privileged session without freshness rule | Rejected for the PoC. | Privileged onboarding should use current-attempt evidence or a documented short lifetime. |
| `acr_values` requested by the browser but not checked after authentication | Rejected. | Keycloak documentation warns clients should check the resulting `acr`; request parameters alone can be changed or fail to enforce the expected level ([Keycloak step-up authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)). |

## Runtime Evidence To Produce

`WP-013` runtime validation produced:

- Keycloak realm/client configuration showing the privileged ACR-to-LoA mapping;
- the authentication flow configuration proving the privileged level requires the selected factor, such as OTP or WebAuthn/passkey;
- OIDC Authorization Code login evidence requesting the privileged ACR for invited `admin` and `super-admin`;
- validated ID token or server-side authentication result evidence with issuer, audience, subject, expiration, nonce/session binding where applicable, and `acr`;
- passing activation evidence for invited `admin` and `super-admin` only when privileged evidence is present and current;
- blocked activation evidence for missing, lower, stale, mismatched, or unverifiable privileged evidence;
- local EDRLab audit events for activation, denial, blocker, and drift;
- supplemental Keycloak authentication/admin events where useful, clearly marked as supplemental.

The runtime result uses the evidence-record shape from the [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md#evidence-record).

## Residual Risks

- OTP-based MFA satisfies the project's broad MFA wording and is accepted for the current privileged-authentication direction by ADR 0003. It is not equivalent to phishing-resistant passwordless, so WebAuthn/passkeys remain a future hardening option rather than a blocker ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)).
- WebAuthn/passkey strength depends on realm policy, authenticator policy, user verification settings, attestation expectations, and recovery/fallback rules. The PoC must record configuration, not just the presence of a WebAuthn credential.
- `acr` proves the authentication context that Keycloak emitted, not the whole security posture. Token validation, client configuration, flow binding, and IAM Control Plane API checks remain required.
- `amr` is not accepted as primary evidence unless the runtime explicitly emits, documents, and verifies it. This avoids repeating the earlier `WP-004` blocker as a quiet assumption.
- First-super-admin bootstrap remains a separate concern. `WP-013` validates invited privileged-account activation, not production bootstrap ceremony.
- The Docker runner proves the step-up evidence path, not production browser UX, production HTTPS cookie configuration, service-to-service authentication, durable audit persistence, or operational recovery.

## Decision Impact

`WP-013` is complete at PoC level for the selected ACR/LoA step-up evidence path. The previous `missing_explicit_privileged_authentication_evidence` blocker is resolved for the Docker PoC slice.

ADR 0003 accepts OTP MFA as sufficient privileged-authentication evidence for `admin` and `super-admin` accounts in the current target direction. This result supports moving the Keycloak IAM plus EDRLab IAM Control Plane API direction into Phase 5 review, but it does not approve production activation of `admin` or `super-admin` accounts by itself.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-012 Result - Lifecycle and Onboarding](./keycloak-wp012-result.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak ACR to LoA Mapping](https://www.keycloak.org/docs/latest/server_admin/#_acr-loa)
- [Keycloak Step-Up Authentication](https://www.keycloak.org/docs/latest/server_admin/#creating-a-browser-login-flow-with-step-up-mechanism)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)
- [Keycloak Passkeys](https://www.keycloak.org/docs/latest/server_admin/#passkeys)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Core - Authentication Request](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)
- [OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [RFC 8176 - Authentication Method Reference Values](https://www.rfc-editor.org/rfc/rfc8176)
