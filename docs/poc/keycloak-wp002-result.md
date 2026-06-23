# Keycloak WP-002 Result

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-07

## Contents

- [Summary](#summary)
- [Scenario Added](#scenario-added)
- [Commands Verified](#commands-verified)
- [Local Execution Status](#local-execution-status)
- [Observed Result](#observed-result)
- [Evidence Collected](#evidence-collected)
- [Limitations](#limitations)
- [References](#references)

## Summary

`WP-002` was executed against the scripted [Keycloak PoC runtime](../../poc/keycloak/README.md) on 2026-06-07. The scripted scenario targets the accepted login and SSO boundary: Keycloak authenticates through OIDC Authorization Code flow, while the local EDRLab side validates token evidence, resolves `iss` + `sub` to one local account, and creates only a local application session. This matches the accepted Phase 4 browser/session pattern and keeps Keycloak authentication separate from EDRLab authorization (`FR-010`, `FR-020`, `FR-036`, `FR-037`, `FR-038`; [Keycloak integration scope - Validated Browser Pattern](../architecture/keycloak-integration-scope.md#validated-browser-pattern), [Keycloak validation plan - WP-002](./keycloak-validation-plan.md#work-packages)).

Result: pass for the login and SSO boundary validation. Keycloak authenticated the non-production member user, returned an Authorization Code, exchanged it for server-side tokens with PKCE, exposed ID token/UserInfo subject evidence, preserved SSO for a second `prompt=none` authorization, and stopped silent authentication after logout. The PoC local side resolved `iss` + `sub` to exactly one active local account fixture before recording a local session decision.

## Scenario Added

The script [verify-login-sso.sh](../../poc/keycloak/scripts/verify-login-sso.sh) adds a narrow, non-production WP-002 check:

| Step | Validation target | Source |
| --- | --- | --- |
| Reach Keycloak login form | Browser-style redirect to the Keycloak authorization endpoint. | Keycloak documents the authorization endpoint and Authorization Code flow as redirecting the user agent to Keycloak and returning a code after authentication ([Keycloak OIDC endpoints and grant types](https://www.keycloak.org/securing-apps/oidc-layers)). |
| Exchange authorization code | Backend-side code exchange with confidential client secret and PKCE. | RFC 7636 defines the `code_verifier` / `code_challenge` pattern; OAuth 2.0 Security BCP recommends PKCE for confidential clients as protection against code misuse and injection ([RFC 7636](https://www.rfc-editor.org/rfc/rfc7636), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)). |
| Validate ID token evidence | Verify RS256 signature using realm JWKS; check issuer, audience, nonce, time claims, verified email, and `sub`. | Keycloak documents the realm certificate/JWKS endpoint for verifying tokens; OpenID Connect defines ID token and subject-identifier behavior ([Keycloak certificate endpoint](https://www.keycloak.org/securing-apps/oidc-layers), [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)). |
| Check UserInfo subject | Confirm UserInfo `sub` matches the ID token `sub`. | OpenID Connect warns that UserInfo values must not be used if the UserInfo `sub` does not exactly match the ID token `sub` ([OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)). |
| Resolve local account | Use a PoC-only local account fixture to resolve exactly one active account by issuer and subject. | The local account model remains authoritative for account state and authorization (`FR-036`, `FR-037`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Record local session decision | Record a local session boundary without writing raw tokens to evidence. | The accepted browser pattern keeps Keycloak tokens server-side and uses a local session cookie for the browser validation path ([Keycloak validation plan - Accepted Validation Decisions](./keycloak-validation-plan.md#accepted-validation-decisions)). |
| Check SSO | Run a second `prompt=none` authorization with the same Keycloak cookie jar and no credential post. | Keycloak owns SSO session behavior for the PoC boundary ([Keycloak integration scope - SSO Session Flow](../architecture/keycloak-integration-scope.md#sso-session-flow)). |
| Check logout | Use the Keycloak logout endpoint and confirm post-logout `prompt=none` does not silently return a new authorization code. | Keycloak documents the logout endpoint and recommends protocol-standard logout rather than its legacy direct logout format ([Keycloak logout endpoint](https://www.keycloak.org/securing-apps/oidc-layers)). |

## Commands Verified

From a clean Linux checkout with Docker running:

```bash
cp poc/keycloak/.env.example poc/keycloak/.env.local
# Edit poc/keycloak/.env.local for local non-production secrets.

bash poc/keycloak/scripts/start.sh
bash poc/keycloak/scripts/bootstrap.sh
bash poc/keycloak/scripts/verify.sh
bash poc/keycloak/scripts/verify-login-sso.sh
bash poc/keycloak/scripts/stop.sh
```

For placeholder-only validation, the same path can use:

```bash
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/start.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/bootstrap.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/verify.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/verify-login-sso.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/stop.sh
```

The placeholder-only path above was executed successfully on the current host after preparing temporary local prerequisites for `jq` and `python3`. Those host-specific prerequisites were placed under ignored `poc/keycloak/tmp/` and are not project artifacts.

## Local Execution Status

Syntax validation passed:

```text
bash -n poc/keycloak/scripts/verify-login-sso.sh
```

The first execution attempt failed during token exchange with:

```text
PKCE verification failed: Invalid code verifier
```

The script was corrected to remove carriage returns from generated URL-safe random values before using them as PKCE code verifiers. The corrected script then passed the full runtime validation. The Keycloak runtime was stopped after verification.

## Observed Result

| Check | Result |
| --- | --- |
| Keycloak container startup | Pass |
| WP-001 realm/client/user/event verification before WP-002 | Pass |
| Keycloak login form reached | Pass |
| First Authorization Code returned after Keycloak login | Pass |
| Authorization code exchanged for server-side tokens | Pass |
| ID token signature verified against realm JWKS | Pass |
| ID token issuer matches realm | Pass |
| ID token audience includes `backoffice-bff-poc` | Pass |
| ID token nonce matches authorization request | Pass |
| ID token email is the verified member email | Pass |
| ID token time claims are within expected bounds | Pass |
| UserInfo `sub` matches ID token `sub` | Pass |
| Local resolver matched exactly one active account by issuer and subject | Pass |
| Local session decision recorded after local account resolution | Pass |
| Second `prompt=none` authorization returned a code without posting credentials again | Pass |
| Silent SSO token keeps the same subject and request nonce | Pass |
| Keycloak logout redirected to the local logout callback | Pass |
| Post-logout `prompt=none` did not silently authenticate | Pass |
| Runtime stopped after verification | Pass |

## Evidence Collected

The scripted evidence collector wrote local generated evidence to:

```text
poc/keycloak/evidence/20260607T084318Z
```

Generated evidence is ignored by Git by default. The evidence directory contained:

- `wp-002-first-token-response.json`
- `wp-002-id-token-claims.json`
- `wp-002-id-token-signature.txt`
- `wp-002-userinfo.json`
- `wp-002-local-accounts.json`
- `wp-002-local-session.json`
- `wp-002-second-token-response.json`
- `wp-002-second-id-token-claims.json`
- `wp-002-login-sso-trace.json`
- `wp-002-keycloak-events.json`
- `wp-002-evidence.md`

The script intentionally stores sanitized token-response metadata, token claims, subject-resolution evidence, and SSO/logout trace data, not raw access tokens, refresh tokens, or ID tokens.

## Limitations

- The local account fixture in WP-002 is PoC-only. It demonstrates resolution after a subject link exists; `WP-003` must validate safe subject-link creation and unsafe onboarding denials (`FR-039`, `FR-043`, `FR-044`; [Keycloak validation plan - WP-003](./keycloak-validation-plan.md#work-packages)).
- The script uses a curl cookie jar to simulate browser SSO behavior. It does not validate a real browser UI, production BFF middleware, persistent session storage, HTTPS, `Secure` / `HttpOnly` / `SameSite` cookie flags, or CSRF controls ([Web sessions, cookies, and BFF pattern](../wiki/24-web-sessions-cookies-and-bff.md)).
- The script does not validate protected-service authorization, access-stop behavior, privileged-authentication evidence, claim override rejection, or local audit authority. Those remain later work packages in the accepted plan ([Keycloak validation plan - Work Packages](./keycloak-validation-plan.md#work-packages)).
- The validation used `.env.example` placeholder values to prove runtime behavior. Real local execution should copy `.env.example` to ignored `.env.local` and replace placeholder secrets before use ([Keycloak PoC runtime - Setup](../../poc/keycloak/README.md#setup)).

## References

- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Keycloak Integration Scope](../architecture/keycloak-integration-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Keycloak PoC Runtime](../../poc/keycloak/README.md)
- [Keycloak OIDC Endpoints and Grant Types](https://www.keycloak.org/securing-apps/oidc-layers)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [RFC 7636 - Proof Key for Code Exchange](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [Web Sessions, Cookies, and BFF Pattern](../wiki/24-web-sessions-cookies-and-bff.md)
