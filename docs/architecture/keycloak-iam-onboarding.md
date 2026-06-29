# Keycloak/IAM Onboarding

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Architecture
Last reviewed: 2026-06-29

## Contents

- [Purpose](#purpose)
- [Boundary](#boundary)
- [Provisioning Flow](#provisioning-flow)
- [Minimum Keycloak Configuration](#minimum-keycloak-configuration)
- [IAM Activation Behavior](#iam-activation-behavior)
- [Admin Console Flow](#admin-console-flow)
- [Current Limitations](#current-limitations)
- [References](#references)

## Purpose

This document is the Phase 6 onboarding bridge between Keycloak and the EDRLab
IAM Control Plane API. It owns the Keycloak-facing provisioning and first-login
shape for invited backoffice accounts. Endpoint schemas stay in the
[IAM Control Plane API Contract](./iam-control-plane-api-contract.md#onboarding),
runtime commands stay in the
[access-control runbook](../../access-control/README.md), and managed Keycloak
state rules stay in the
[Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md).

## Boundary

Backoffice account creation starts in the IAM Control Plane API, not in public
Keycloak self-registration. New accounts are created in `invited` state with
the required profile fields, and the authenticated-subject link is created only
by the safe onboarding activation flow (`FR-007`, `FR-039`, `FR-040`;
[Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

Keycloak owns authentication, credentials, required actions, login sessions, and
IdP-side recovery for invited users. The access-control capability consumes
validated bearer-token evidence and decides whether one invited backoffice
account can be linked and activated (`FR-042`, `FR-043`, `FR-044`;
[Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

Routine business administration still goes through the EDRLab Admin Console and
IAM Control Plane API. Direct Keycloak business edits are treated as drift under
the accepted schema policy ([Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)).

## Provisioning Flow

1. An `admin` or `super-admin` creates an invited account through the IAM
   Control Plane API.
2. The controlled provisioning path creates or updates the matching Keycloak
   user in the MVP realm with the same email. Public registration remains
   disabled ([MVP scope - Out of Scope](../evaluation/mvp-scope.md#out-of-scope)).
3. Keycloak delivers first-login setup through an actions email. Keycloak
   documents realm SMTP configuration, per-user required actions, and the Admin
   REST `execute-actions-email` operation ([Keycloak email configuration](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm),
   [Keycloak required actions](https://www.keycloak.org/docs/latest/server_admin/#setting-required-actions-for-one-user),
   [Keycloak Admin REST users resource](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_users_resource)).
4. For `member` accounts, first-login actions should make the user own their
   credential and satisfy email verification before IAM activation. For `admin`
   and `super-admin` accounts, activation also requires accepted privileged
   authentication evidence (`FR-034`, `FR-043`, `FR-044`;
   [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
5. After Keycloak login and required actions, the Admin Console calls
   `POST /iam/onboarding/activate` with the invited user's bearer token.

## Minimum Keycloak Configuration

| Configuration item | Requirement |
| --- | --- |
| Realm SMTP | Configure realm email so Keycloak can send action emails for verification and credential setup ([Keycloak email configuration](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm)). |
| Public registration | Keep disabled; account creation starts in the IAM Control Plane API, not in public Keycloak self-registration ([MVP scope - Out of Scope](../evaluation/mvp-scope.md#out-of-scope)). |
| Backoffice client | Use the configured backoffice Authorization Code + PKCE client, default `backoffice`, and a redirect URI controlled by the Admin Console ([access-control runbook](../../access-control/README.md#what-this-slice-includes)). |
| User provisioning | Create or update the Keycloak user through the controlled provisioning path, using the same email as the IAM invited account ([Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md#edit-permissions)). |
| Member actions | Send `VERIFY_EMAIL` and `UPDATE_PASSWORD` through `execute-actions-email`. |
| Privileged actions | Send `VERIFY_EMAIL`, `UPDATE_PASSWORD`, and `CONFIGURE_TOTP` when the accepted OTP privileged-authentication path applies ([Keycloak OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| IAM schema | Keep EDRLab IAM state in managed Keycloak attributes and roles defined by the schema policy ([Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)). |
| IAM state | Keep the IAM account `invited` until bearer-derived onboarding evidence passes the safe match rules ([IAM Control Plane API Contract - Onboarding](./iam-control-plane-api-contract.md#onboarding)). |

The recommended `execute-actions-email` action lists are:

```json
["VERIFY_EMAIL", "UPDATE_PASSWORD"]
```

```json
["VERIFY_EMAIL", "UPDATE_PASSWORD", "CONFIGURE_TOTP"]
```

## IAM Activation Behavior

The onboarding request is intentionally empty because the IAM API derives
identity and privileged-authentication evidence from validated bearer-token or
trusted IdP evidence:

```http
POST /iam/onboarding/activate
Authorization: Bearer <keycloak-user-access-token>
Content-Type: application/json

{}
```

The IAM Control Plane API must:

- validate the bearer token issuer, audience, expiry, subject, and expected
  OAuth client before account resolution;
- derive `sub`, `email`, `email_verified`, and privileged-authentication
  evidence such as `acr` from validated token or trusted IdP evidence;
- reject request-body attempts to supply `subject`, `emailVerified`, `acr`,
  `accountType`, `lifecycle`, `linkedSubject`, or other
  authorization-significant fields;
- find exactly one `invited` account with no existing authenticated-subject link
  and a verified email matching the authenticated subject;
- require accepted privileged-authentication evidence for `admin` and
  `super-admin` activation;
- set the immutable subject link and move the account to `active` only after
  the safe match passes;
- audit successful activation, idempotent repeat activation for the same
  subject, unsafe matches, missing verified email, missing privileged evidence,
  and rejected subject-link mutation attempts.

The endpoint schema and runtime error codes are defined in the
[IAM Control Plane API Contract - Onboarding](./iam-control-plane-api-contract.md#onboarding).

## Admin Console Flow

1. An `admin` or `super-admin` creates an invited backoffice account.
2. The invited user signs in through Keycloak and completes required actions.
3. The Admin Console calls `GET /iam/me` with the user's bearer token.
4. If the account is not active and linked yet, the Admin Console calls
   `POST /iam/onboarding/activate` with the same bearer token.
5. After successful activation, `GET /iam/me` returns the linked active account.

## Current Limitations

- The Phase 6 runtime does not include the Admin Console UI yet
  ([MVP scope - Current MVP State](../evaluation/mvp-scope.md#current-mvp-state)).
- OTP operational safeguards remain open MVP evidence. Production privileged
  activation must not be accepted without explicit closure or accepted risk
  (`FR-034`, `FR-043`, `FR-044`;
  [MVP scope - Production Readiness Gaps](../evaluation/mvp-scope.md#production-readiness-gaps)).
- Full Keycloak schema migration and drift workflow evidence remains partial
  ([MVP scope - Production Readiness Gaps](../evaluation/mvp-scope.md#production-readiness-gaps)).

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [MVP Scope - Access-Control Production MVP](../evaluation/mvp-scope.md)
- [IAM Control Plane API Contract - Onboarding](./iam-control-plane-api-contract.md#onboarding)
- [Access-Control Runtime Runbook](../../access-control/README.md)
- [Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak Email Configuration](https://www.keycloak.org/docs/latest/server_admin/#configuring-email-for-a-realm)
- [Keycloak Required Actions](https://www.keycloak.org/docs/latest/server_admin/#setting-required-actions-for-one-user)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak OTP](https://www.keycloak.org/docs/latest/server_admin/#creating-an-otp)
