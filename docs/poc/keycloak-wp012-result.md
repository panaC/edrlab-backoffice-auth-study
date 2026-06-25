# Keycloak WP-012 Result - Lifecycle and Onboarding

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Lifecycle Contract](#lifecycle-contract)
- [Onboarding Activation Flow](#onboarding-activation-flow)
- [Scenario Matrix](#scenario-matrix)
- [Protected-Service Access Expectations](#protected-service-access-expectations)
- [Runtime Evidence To Produce](#runtime-evidence-to-produce)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-012` defines the lifecycle and onboarding behavior to validate for the Keycloak IAM plus EDRLab IAM Control Plane API direction. It builds on the `WP-010` mapping and the `WP-011` IAM Control Plane API anti-bypass contract: lifecycle and subject-link mutations are business operations mediated by the IAM Control Plane API, not direct Keycloak Admin Console edits ([Keycloak WP-010 result](./keycloak-wp010-result.md), [Keycloak WP-011 result](./keycloak-wp011-result.md), [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md)).

This is documentation-first PoC evidence. It does not add runtime scripts, production code, production dependencies, database schema, CI, or deployment artifacts. Runtime validation still needs a Linux-targeted, Docker-based, fully scripted PoC before execution ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Result

Use the `WP-010` lifecycle mapping for the first validation slice:

- `edrlab.lifecycle=invited`, `active`, `disabled`, or `archived` is the EDRLab lifecycle value stored as a Keycloak user attribute;
- Keycloak `enabled=false` is used only as a coarse login/session guard for `disabled` and `archived`, not as the complete lifecycle model;
- `edrlab.linked_subject` is empty for invited accounts and is created exactly once during safe onboarding activation;
- `email` and verified-email evidence are used for onboarding match, but mutable email is never a post-activation account identifier;
- `admin` and `super-admin` onboarding activation requires explicit privileged-authentication evidence. The follow-up `WP-013` runtime proves the first ACR/LoA step-up path at PoC level ([Keycloak WP-013 result](./keycloak-wp013-result.md#runtime-execution)).

Keycloak `UserRepresentation` includes fields used by this mapping, including `email`, `emailVerified`, `attributes`, `enabled`, `requiredActions`, and role mappings ([Keycloak UserRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_userrepresentation)). Keycloak also supports required actions such as `Verify Email`, where the user must verify the email account before login continues ([Keycloak required actions](https://www.keycloak.org/docs/latest/server_admin/#defining-actions-required-at-login)). OpenID Connect defines `sub` as the subject identifier and defines `email` / `email_verified` claims, while warning that the `email` claim must not be relied on as unique ([OpenID Connect Core - ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDToken), [OpenID Connect Core - Standard Claims](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims)).

## Lifecycle Contract

| Lifecycle state | Keycloak representation | Protected-service access | Allowed transitions | Notes |
| --- | --- | --- | --- | --- |
| `invited` | `edrlab.lifecycle=invited`, `enabled=true`, no `edrlab.linked_subject`. | Deny. Service-access roles may be preassigned to invited members, but they must not grant access until activation. | `invited -> active` only through safe onboarding activation. | Supports administrative account creation before the first successful backoffice activation (`FR-012`, `FR-041`). |
| `active` | `edrlab.lifecycle=active`, `enabled=true`, immutable `edrlab.linked_subject` present. | Allow only when account type and service-access rules allow it. | `active -> disabled`. | Activation proves one safe subject link, not general self-service registration (`FR-037`, `FR-043`). |
| `disabled` | `edrlab.lifecycle=disabled`, `enabled=false`. | Deny. | `disabled -> active` or `disabled -> archived`. | `enabled=false` is a coarse Keycloak login/session guard; the IAM Control Plane API still checks lifecycle. |
| `archived` | `edrlab.lifecycle=archived`, `enabled=false`. | Deny. | No restore in the initial policy. | Records remain retained; hard deletion is out of scope (`FR-014`). |

The IAM Control Plane API must reject every transition not listed above, including `active -> invited`, `disabled -> invited`, `archived -> active`, and any hard-delete path. OWASP guidance says authorization failures must be handled safely and should not leave the software in a state that can lead to bypass; this supports fail-closed behavior when lifecycle state is missing or inconsistent ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#exit-safely-when-authorization-checks-fail)).

EDRLab attributes such as `edrlab.lifecycle`, `edrlab.account_id`, and `edrlab.linked_subject` should be treated as controlled attributes. Keycloak documents managed and unmanaged user attributes and recommends strict control over unexpected attributes and values, which supports defining EDRLab attributes intentionally rather than accepting arbitrary user-managed attributes ([Keycloak managed and unmanaged attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)).

## Onboarding Activation Flow

The runtime PoC should validate this IAM Control Plane API-mediated activation flow:

1. The invited user authenticates through Keycloak OIDC.
2. The IAM Control Plane API validates the authentication result and extracts the current Keycloak `sub`, `email`, and verified-email evidence.
3. The IAM Control Plane API searches current Keycloak IAM state for exactly one account with `edrlab.lifecycle=invited`, no `edrlab.linked_subject`, matching email, and exactly one account-type role.
4. If the target account is `member`, the IAM Control Plane API stores `edrlab.linked_subject=<sub>`, changes `edrlab.lifecycle` to `active`, leaves `enabled=true`, records a local EDRLab audit event, and allows normal authorization checks to continue.
5. If the target account is `admin` or `super-admin`, the IAM Control Plane API performs the same matching checks but must also require privileged-authentication evidence. The follow-up `WP-013` runtime validates the first PoC evidence path; a production implementation must still enforce that evidence before linking or activating privileged accounts.
6. If any matching condition is unsafe, the IAM Control Plane API must keep the account `invited`, avoid creating `edrlab.linked_subject`, deny access, and record a local audit event.

The IAM Control Plane API must not activate from authentication alone. It must require the controlled onboarding conditions from `FR-043`, and it must fail closed under `FR-044` when no safe unique match exists.

## Scenario Matrix

| Scenario | Input state | Expected IAM Control Plane API result | Key evidence |
| --- | --- | --- | --- |
| Safe member activation | One invited member with matching email, verified email evidence, no linked subject, exactly one account-type role. | Link current `sub`, set lifecycle `active`, allow later protected-service checks according to account type or assigned member service roles. | Before/after user attributes, OIDC `sub`, verified-email evidence, local `account.activated` audit. |
| Invited member with preassigned service role | Invited member has `service-catalog-consult` before activation. | Deny protected-service access while `invited`; after safe activation, allow only through the normal IAM Control Plane API authorization check. | Authorization denial before activation, activation audit, authorization result after activation. |
| Invited admin without privileged evidence | One invited admin matches email and subject-link criteria, but `WP-013` evidence is absent. | Keep `invited`, do not link subject, deny backoffice access, record blocker. | Blocker audit with reason `privileged_auth_evidence_missing`. |
| Invited super-admin without privileged evidence | One invited super-admin matches email and subject-link criteria, but `WP-013` evidence is absent. | Keep `invited`, do not link subject, deny backoffice access, record blocker. | Blocker audit with reason `privileged_auth_evidence_missing`. |
| No invitation | Authenticated subject has verified email but no invited account matches. | Deny; no user is created or activated. | Local denial audit, no Keycloak mutation. |
| Duplicate invited accounts | Two or more invited accounts match the same verified email. | Deny; no subject link is created. | Local denial audit with duplicate candidate IDs. |
| Unverified email | Authentication result has matching email but verified-email evidence is false or absent. | Deny; keep account `invited`. | OIDC/UserInfo evidence and denial audit. |
| Email mismatch | Authenticated verified email differs from invited account email. | Deny; keep account `invited`. | Candidate account email, authenticated email, denial audit. |
| Pre-linked invited account | Invited account already has `edrlab.linked_subject`. | Deny as invariant violation or drift; no rebinding. | Before-state attributes and drift/denial audit. |
| Disabled account login attempt | Account has `edrlab.lifecycle=disabled` and `enabled=false`. | Deny backoffice access; no onboarding. | Lifecycle state, `enabled=false`, denial audit. |
| Archived account login attempt | Account has `edrlab.lifecycle=archived` and `enabled=false`. | Deny backoffice access; no restore. | Lifecycle state, `enabled=false`, denial audit. |
| Return to invited attempt | Admin command or direct edit tries to move a non-invited account back to `invited`. | Deny or detect drift; no authorized transition. | Before/after lifecycle evidence and local audit. |

## Protected-Service Access Expectations

The runtime PoC must prove that lifecycle state gates protected-service access:

- `invited`, `disabled`, and `archived` always deny protected-service access;
- `active member` allows protected-service access only through assigned service-access roles;
- `active admin` and `active super-admin` receive covered protected-service access through account type, not through member service-role assignment;
- lifecycle changes deny on the next fresh IAM Control Plane API authorization check;
- missing, duplicated, or invalid lifecycle attributes fail closed.

This keeps `FR-015`, `FR-016`, `FR-020`, and `FR-021` tied to the IAM Control Plane API authorization contract rather than to token claims or frontend checks.

## Runtime Evidence To Produce

`WP-012` runtime validation should produce:

- a clean Keycloak state fixture for invited member, invited admin, invited super-admin, unsafe duplicates, unverified email, pre-linked subject, disabled, and archived accounts;
- OIDC authentication evidence containing `sub`, `email`, and verified-email evidence for safe and unsafe cases;
- Keycloak Admin REST evidence showing `edrlab.lifecycle`, `edrlab.linked_subject`, `enabled`, account-type client role, and member service-access role state before and after activation;
- IAM Control Plane API request/response examples for activation, denied onboarding, lifecycle transitions, restore, archive, and protected-service authorization;
- local EDRLab audit events for activation, denial, blocker, lifecycle change, and drift;
- Keycloak admin/user event references as supplemental provider-side evidence where useful. Keycloak can record admin actions performed through the Admin Console or Admin REST, including the representation sent through Admin REST when enabled ([Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

The runtime result should use the evidence-record shape from the [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md#evidence-record).

## Residual Risks

- Email matching remains a bootstrap/onboarding convenience, not a durable identity key. After activation, `edrlab.linked_subject` and `edrlab.account_id` must be the durable references.
- Keycloak email verification configuration must be part of the runtime setup; otherwise, unverified-email denial cannot be proven cleanly.
- `admin` and `super-admin` activation remains dependent on explicit privileged-authentication evidence; the follow-up `WP-013` runtime validates the first ACR/LoA evidence path at PoC level.
- If direct Keycloak Admin Console edits can change `edrlab.lifecycle` or `edrlab.linked_subject`, `WP-015` must prove drift handling before Phase 5 review.
- `enabled=false` may stop Keycloak login/session behavior, but it does not replace IAM Control Plane API lifecycle checks for authorization decisions.

## Decision Impact

`WP-012` is complete at documentation level. It defines the lifecycle and onboarding scenarios that the runtime PoC must execute next.

The follow-up `WP-013` result validates privileged-authentication evidence for the first PoC path, and ADR 0003 accepts OTP MFA for the current direction. Remaining review work should focus on OTP enrollment, reset, recovery, and audit safeguards rather than treating WebAuthn/passkeys as a blocker.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak UserRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_userrepresentation)
- [Keycloak Required Actions](https://www.keycloak.org/docs/latest/server_admin/#defining-actions-required-at-login)
- [Keycloak Managed and Unmanaged Attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Core - Standard Claims](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
