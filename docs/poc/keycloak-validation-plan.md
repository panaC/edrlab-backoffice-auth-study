# Keycloak Validation Plan

Status: Draft
Phase: Phase 3 - Solution Choice
Scope: PoC
Last reviewed: 2026-06-05

## Contents

- [Purpose](#purpose)
- [Decision Context](#decision-context)
- [Development and Configuration Scope](#development-and-configuration-scope)
- [Validation Objectives](#validation-objectives)
- [Validation Scope](#validation-scope)
- [Candidate Validation Scenarios](#candidate-validation-scenarios)
- [Success Criteria](#success-criteria)
- [Non-Production Limits](#non-production-limits)
- [Open Questions Before Phase 4](#open-questions-before-phase-4)
- [Phase 4 Readiness Gate](#phase-4-readiness-gate)
- [References](#references)

## Purpose

This document prepares validation of the accepted Keycloak candidate. It is a Phase 3 planning artifact for a possible Phase 4 non-production PoC, not a PoC execution artifact and not implementation approval ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

The plan focuses only on uncertainties that matter to the accepted solution choice: self-hosted Keycloak for authentication and provider-side evidence, plus a local EDRLab access-control service as the authoritative source for account lifecycle, account types, service-access roles, protected-service authorization, and project audit records ([ADR 0001](../decisions/0001-choose-keycloak-for-validation.md), [Solution choice - Selected Candidate](../evaluation/solution-choice.md#selected-candidate)).

The validation target is the first integration option: self-hosted Keycloak plus local access-control. It does not validate an all-in-Keycloak realm model for account lifecycle, service-access roles, protected-service authorization, or project audit because the accepted rationale keeps those responsibilities local ([Solution choice - Why Keep Access-Control Local](../evaluation/solution-choice.md#why-keep-access-control-local), [ADR 0001 - Integration Rationale](../decisions/0001-choose-keycloak-for-validation.md#integration-rationale)).

## Decision Context

The accepted candidate is self-hosted Keycloak with a local EDRLab access-control service ([ADR 0001](../decisions/0001-choose-keycloak-for-validation.md)). Keycloak is the candidate authentication product and OIDC/OAuth2 runtime to validate, but it must not become the source of truth for the EDRLab authorization model (`FR-001`, `FR-002`, `FR-038`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The local access-control service must remain authoritative for:

| Local responsibility | Why it matters | Source |
| --- | --- | --- |
| Backoffice account type and lifecycle state | Account type is fixed, lifecycle state controls access, and IdP claims must not override these facts. | `FR-001`, `FR-011` through `FR-016`, `FR-038` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)) |
| Authenticated-subject link and onboarding activation | Automatic onboarding can link and activate only one safe invited account with verified matching email and privileged-authentication evidence where required. | `FR-036`, `FR-039`, `FR-043`, `FR-044` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)) |
| Service-access roles and protected-service decisions | Protected services must authorize server-side from active account state and account type or member service-access role rules. | `FR-002`, `FR-020`, `FR-021`, `FR-032`, `FR-033` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| Project audit records | Keycloak events may support authentication evidence, but project audit records must cover the `FR-027` event set and remain append-only under the initial policy. | `FR-027`, `FR-035` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events) |

## Development and Configuration Scope

The validation plan uses [Keycloak integration scope](../architecture/keycloak-integration-scope.md) as the reference for the concrete split between:

| Block | Validation interpretation | Source |
| --- | --- | --- |
| EDRLab development block | Local access-control domain model, onboarding and activation, local administration API, EDRLab Access Control Manager UI, protected-service authorization contract, local application session behavior, local audit, and logout integration. | [Keycloak integration scope - Development Block](../architecture/keycloak-integration-scope.md#development-block); `FR-020`, `FR-024`, `FR-027`, `FR-036` through `FR-039` |
| Keycloak configuration block | Realm and client configuration, OIDC Authorization Code flow, authentication flows, MFA/WebAuthn/OTP behavior, session and token timeouts, JWK/discovery inputs, Keycloak user/session administration, events, and operational configuration evidence. | [Keycloak integration scope - Configuration Block](../architecture/keycloak-integration-scope.md#configuration-block); [Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers) |
| SSO session flow | Keycloak manages SSO authentication/session behavior; EDRLab resolves the `sub` to a local account and performs local authorization before protected-service access. | [Keycloak integration scope - SSO Session Flow](../architecture/keycloak-integration-scope.md#sso-session-flow); [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html) |

## Validation Objectives

| ID | Objective | Validation target | Evidence to collect |
| --- | --- | --- | --- |
| KV-001 | Preserve the authorization boundary | Keycloak authenticates; local access-control authorizes. Keycloak roles, groups, token claims, and mutable email must not grant EDRLab account type or service-access role authority. | Flow notes, rejected shortcut list, and a mapping table showing which claims are consumed only as authentication evidence (`FR-038`; [Threat model TS-008](../risks/threat-model.md#threat-scenarios)). |
| KV-002 | Define protected-service authorization contract | Choose the first contract to validate: local `authorization/check`, local introspection, BFF-mediated session, or short-lived token plus local lookup. | Contract sketch with trusted inputs, failure behavior, cache tolerance, audit correlation ID, and denial behavior (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| KV-003 | Verify privileged-authentication evidence | Determine how Keycloak configuration or event data can prove production admin or super-admin onboarding satisfied MFA, WebAuthn, OTP, or passwordless requirements. | Candidate evidence field, event, authentication context, or local rule; Keycloak documents WebAuthn, passwordless, and two-factor flows as configurable authentication mechanisms ([Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn), `FR-034`, `FR-043`). |
| KV-004 | Validate access-stop behavior | Show how protected-service access stops after account disablement, archival, member role removal, or service-access-role disablement or archival. | Target delay assumption, chosen mechanism, and failure/caching behavior; Keycloak has session and token timeout controls, but local authorization state must remain decisive ([Keycloak sessions and token timeouts](https://www.keycloak.org/docs/latest/server_admin/#session-and-token-timeouts), `FR-016`). |
| KV-005 | Validate audit correlation | Correlate local account, role, onboarding, protected-service denial, and audit-read events with relevant Keycloak authentication or admin events where useful. | Minimum audit fields, correlation ID convention, Keycloak event types to retain, and local append-only audit responsibilities (`FR-027`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). |
| KV-006 | Validate self-hosted operational responsibilities | Identify evidence needed for realm configuration, import/export, backup/restore expectations, upgrade path, key rotation, event retention, and support/export access. | Operations checklist and residual risk list; Keycloak documents realm import/export and configuration sources, which are relevant inputs but not a complete operational plan ([Keycloak import/export](https://www.keycloak.org/server/importExport), [Keycloak configuration](https://www.keycloak.org/server/configuration), `FR-030`). |
| KV-007 | Validate fail-closed dependency behavior | Define what happens when Keycloak, local access-control, protected-service authorization, audit sink, or session/token validation is unavailable. | Failure matrix showing deny behavior, audit handling, retry limits, and residual risks (`FR-021`, `FR-029`; [Threat model TS-012](../risks/threat-model.md#threat-scenarios)). |
| KV-008 | Validate the Keycloak Web Admin boundary | Confirm that Keycloak Web Admin is used only for Keycloak realm administration and not as the EDRLab business access-control manager. | Boundary checklist showing accepted Keycloak Admin Console uses and rejected shortcuts for account type, lifecycle, subject-link, service-access role, authorization, and audit management ([Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary), `FR-038`). |
| KV-009 | Validate the SSO session boundary | Confirm that Keycloak SSO session management is not treated as local business authorization and that local application session behavior, if used, is explicitly owned by EDRLab. | Flow notes showing OIDC Authorization Code flow, local `sub` resolution, local session creation or non-creation, logout behavior, and fail-closed access after local account changes ([Keycloak integration scope - SSO Session Flow](../architecture/keycloak-integration-scope.md#sso-session-flow), `FR-016`, `FR-020`, `FR-021`). |

## Validation Scope

In scope for validation planning:

- one Keycloak realm for non-production authentication behavior, with no production users or production secrets ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept));
- representative account types: `member`, `admin`, and `super-admin`, with local account state remaining outside Keycloak (`FR-001`, `FR-038`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements));
- one protected-service example for the first authorization contract, because `FR-020` and `FR-021` require server-side protected-service authorization and fail-closed denial;
- Keycloak WebAuthn/OTP/passwordless evidence exploration for privileged onboarding (`FR-034`, `FR-043`; [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn));
- Keycloak authentication/admin event review only as supporting evidence for local audit (`FR-027`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events));
- Keycloak Web Admin / Admin Console usage for non-production realm setup, authentication configuration, and provider-side inspection only; Keycloak documents this console for realm administration, while the accepted boundary keeps EDRLab access-control state local ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary));
- SSO session flow review: Keycloak owns the SSO session, while EDRLab owns local account resolution, local application session behavior if selected, and protected-service authorization ([Keycloak integration scope - User Session Management Boundary](../architecture/keycloak-integration-scope.md#user-session-management-boundary));
- self-hosted operational review topics that can affect safety or maintainability at the expected scale (`FR-030`; [README - Project Goal](../../README.md#project-goal)).

Out of scope until explicitly approved:

- production Keycloak deployment, production hosting, production database, production high availability, or CI/deployment automation ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp));
- application code, dependencies, Docker files, generated artifacts, migrations, or executable configuration in this Phase 3 planning step ([AGENTS](../../AGENTS.md#current-operating-phase));
- using Keycloak roles, groups, organizations, or token claims as the authoritative EDRLab service-access-role or account-type model (`FR-002`, `FR-038`);
- using the Keycloak Web Admin / Admin Console as the EDRLab business Access Control Manager for local account lifecycle, service-access role assignments, protected-service decisions, or project audit (`FR-020`, `FR-024`, `FR-027`, `FR-032`; [Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary));
- replacing local project audit records with Keycloak event logs (`FR-027`, `FR-035`);
- public customer identity, public signup, social login, or company-wide IAM replacement ([README - Initial Scope](../../README.md#initial-scope)).

## Candidate Validation Scenarios

| Scenario | Setup assumption | Test question | Expected result |
| --- | --- | --- | --- |
| KS-001: Safe member onboarding | Keycloak authenticates a user whose verified email matches exactly one invited local member account. | Can the local service create the immutable subject link and activate the local account only under `FR-043` conditions? | Local account activates, subject link is created once, local audit records the activation, and no Keycloak role or group becomes a local service-access role (`FR-039`, `FR-043`). |
| KS-002: Unsafe onboarding fails closed | Keycloak authenticates a user with no invited local account, duplicate invited accounts, unverified email, or an existing subject link. | Does onboarding deny access without creating or mutating the subject link? | Local account remains unchanged, access is denied, failed onboarding is audited, and administrative intervention is required (`FR-044`). |
| KS-003: Privileged onboarding evidence | Keycloak authenticates an invited admin or super-admin after a configured MFA/WebAuthn/OTP/passwordless flow. | Can the local onboarding flow verify evidence that the privileged-authentication requirement was satisfied? | Evidence is explicit enough to accept or reject activation; lack of evidence denies activation (`FR-034`, `FR-043`, `FR-044`; [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)). |
| KS-004: Claim override rejection | Keycloak emits roles, groups, or claims that look like admin or service access. | Does the local service ignore those signals for EDRLab account type, lifecycle, and service-access-role assignment? | Authorization uses only local account state and local service-access roles; provider claims are treated as non-authoritative (`FR-038`; [Threat model TS-008](../risks/threat-model.md#threat-scenarios)). |
| KS-005: Protected-service allow/deny | A protected service asks for access using the chosen validation contract. | Does the service grant only active authorized access and deny inactive, missing, stale, or unsafe results? | The service fails closed and records denial context for audit (`FR-020`, `FR-021`, `FR-027`). |
| KS-006: Access stop after local change | A local admin disables an account or removes a member service-access role. | Does protected-service access stop within the target delay? | Access stops within the accepted delay; any cache or session behavior is documented (`FR-016`, `FR-032`). |
| KS-007: Audit correlation | Local account/role changes and Keycloak authentication/admin events occur in the same flow. | Can the review link local audit events with Keycloak supporting events without replacing local audit? | Local audit is complete and append-only; Keycloak events are supplemental and correlated where useful (`FR-027`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). |
| KS-008: Operational restore/import review | A realm configuration is exported and imported in a non-production review. | What operational evidence is needed so restore or migration does not break subject-link and audit invariants? | Import/export behavior is understood, but account state, subject links, service-access roles, and audit records remain local responsibilities ([Keycloak import/export](https://www.keycloak.org/server/importExport), `FR-014`, `FR-035`). |
| KS-009: Admin Console boundary review | An operator uses Keycloak Web Admin to configure the realm or inspect users/events. | Can the team distinguish accepted Keycloak administration from rejected EDRLab access-control management shortcuts? | Realm setup and provider evidence are allowed; account type, lifecycle, subject-link, service-access role assignment, protected-service authorization, and project audit truth remain local ([Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary), `FR-038`). |
| KS-010: SSO session flow review | A user logs in to the backoffice through Keycloak and receives a local application session if that pattern is selected. | Does the flow preserve the boundary between Keycloak SSO authentication and local EDRLab authorization? | Keycloak authenticates and maintains SSO state; EDRLab resolves the `sub`, checks local account state, creates or rejects local session state, and denies protected-service access when local state is inactive or unauthorized ([Keycloak integration scope - SSO Session Flow](../architecture/keycloak-integration-scope.md#sso-session-flow), `FR-036`, `FR-038`). |

## Success Criteria

| ID | Criterion | Pass condition |
| --- | --- | --- |
| KP-001 | Boundary preserved | The validation evidence shows that Keycloak authentication results are mapped into exactly one local account before authorization, and provider roles/groups/claims do not override local access-control state (`FR-036`, `FR-038`). |
| KP-002 | Protected-service contract selected for validation | The team has one concrete contract to test first, with trusted inputs, denial behavior, failure mode, and audit correlation defined (`FR-020`, `FR-021`, `FR-027`). |
| KP-003 | Privileged-auth evidence path identified | The plan identifies a Keycloak-supported evidence path or records the gap as a blocker for production admin/super-admin onboarding (`FR-034`, `FR-043`, `FR-044`). |
| KP-004 | Access-stop target defined | The plan records an accepted access-stop delay assumption and the mechanism to validate it (`FR-016`, `FR-032`). |
| KP-005 | Audit ownership clear | Local audit remains authoritative, Keycloak events are only supporting evidence, and minimum correlation fields are defined (`FR-027`, `FR-035`). |
| KP-006 | Operational risks visible | Self-hosted Keycloak responsibilities are listed with evidence needed for backup, restore, upgrade, configuration, key rotation, event retention, support access, and outage behavior (`FR-030`; [Threat model TS-013](../risks/threat-model.md#threat-scenarios)). |
| KP-007 | Phase 4 scope is tight | Any runtime validation can be performed with non-production data, one realm, representative accounts, one protected-service path, and no production deployment work ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)). |
| KP-008 | Admin Console boundary clear | The validation notes identify what the Keycloak Admin Console may manage and explicitly reject using it as the EDRLab business Access Control Manager (`FR-024`, `FR-038`; [Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)). |
| KP-009 | SSO session boundary clear | The validation notes distinguish Keycloak SSO session behavior from local application session and local authorization behavior, including logout and account disablement effects ([Keycloak integration scope - User Session Management Boundary](../architecture/keycloak-integration-scope.md#user-session-management-boundary), `FR-016`). |

## Non-Production Limits

If the project moves into Phase 4, the PoC must stay inside these limits:

- use throwaway non-production identities, secrets, realm names, and service identifiers only ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept));
- do not connect to production protected services, production IdP data, production audit storage, or production account data;
- do not create production deployment, monitoring, backup, restore, CI, or migration artifacts;
- do not promote PoC configuration into durable application code or production infrastructure without Phase 5 review and explicit Phase 6 movement ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp));
- document any shortcut, fake service, fake user, local-only configuration, or simplified audit sink as a PoC-only limitation.

## Open Questions Before Phase 4

| ID | Question | Needed answer before runtime validation |
| --- | --- | --- |
| OQ-KV-001 | What access-stop delay is acceptable for the initial validation target? | A numeric target or stated assumption for `FR-016`; for example, immediate local denial on fresh checks plus a maximum cache/session tolerance to be reviewed. |
| OQ-KV-002 | Which protected-service contract should be validated first? | Choose one first path: local `authorization/check`, local introspection, BFF-mediated session, or short-lived token plus local lookup. |
| OQ-KV-003 | What Keycloak evidence proves privileged authentication? | Candidate claim, event, authentication context, or local validation rule tied to WebAuthn/OTP/passwordless configuration. |
| OQ-KV-004 | What is the minimum audit correlation schema? | Actor stable ID, local account ID, Keycloak subject, action, result, target, timestamp, correlation ID, and source context should be accepted or revised. |
| OQ-KV-005 | Which self-hosted operations must be reviewed before Phase 5? | Backup, restore, realm import/export, upgrade, configuration drift, key rotation, event retention, support access, and outage behavior. |
| OQ-KV-006 | Can documentation alone answer any objective? | If yes, mark it as documentation-validated and avoid runtime PoC work for that objective. |
| OQ-KV-007 | Which Keycloak Web Admin actions are acceptable during validation? | A short allow/deny list separating Keycloak realm administration from EDRLab account, role, authorization, and audit management. |
| OQ-KV-008 | Which local browser/session pattern should be validated first? | BFF/server-side session, direct OIDC client, or another pattern; the answer affects token exposure, logout, local session storage, and protected-service authorization. |

## Phase 4 Readiness Gate

Move from this Phase 3 plan to a Phase 4 non-production PoC only when:

- the validation scenarios are narrowed to the smallest set that can answer unresolved Keycloak-specific risks;
- the protected-service authorization contract to validate first is selected;
- the PoC data set is non-production and minimal;
- no production infrastructure, generated application artifact, dependency, or CI work is required;
- expected outputs are limited to results, gaps, residual risks, and review inputs.

If these conditions are not met, continue with documentation-level evaluation instead of starting a PoC ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

## References

- [ADR 0001 - Choose Keycloak for Validation](../decisions/0001-choose-keycloak-for-validation.md)
- [Solution Choice](../evaluation/solution-choice.md)
- [Solution Choice - Why Keep Access-Control Local](../evaluation/solution-choice.md#why-keep-access-control-local)
- [Solution Choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)
- [Keycloak Integration Scope](../architecture/keycloak-integration-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Project Governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [README - Project Goal](../../README.md#project-goal)
- [README - Initial Scope](../../README.md#initial-scope)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak - Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak - Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [Keycloak - Configuring Keycloak](https://www.keycloak.org/server/configuration)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63B - Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
