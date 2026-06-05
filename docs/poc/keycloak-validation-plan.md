# Keycloak Validation Plan

Status: Accepted
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-05

## Contents

- [Purpose](#purpose)
- [Accepted Validation Decisions](#accepted-validation-decisions)
- [Runtime Scope](#runtime-scope)
- [Work Packages](#work-packages)
- [Evidence Record](#evidence-record)
- [Readiness Gate](#readiness-gate)
- [References](#references)

## Purpose

This is the finalized Phase 4 entry plan for validating the accepted Keycloak candidate. It is a non-production PoC plan, not production implementation approval, production adoption, or production infrastructure approval ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The validation target is self-hosted Keycloak plus a local EDRLab access-control service. Keycloak provides authentication, OIDC/OAuth2 runtime behavior, SSO session behavior, realm administration, and provider-side evidence; the local access-control service remains authoritative for account type, lifecycle, subject link, service-access roles, protected-service authorization, and project audit records ([ADR 0001](../decisions/0001-choose-keycloak-for-validation.md), [Keycloak integration scope](../architecture/keycloak-integration-scope.md), `FR-001`, `FR-002`, `FR-020`, `FR-027`, `FR-036` through `FR-039`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The PoC does not validate an all-in-Keycloak realm model for EDRLab account lifecycle, service-access roles, protected-service authorization, or project audit. That boundary is part of the accepted Phase 3 rationale ([Solution choice - Why Keep Access-Control Local](../evaluation/solution-choice.md#why-keep-access-control-local), [Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)).

## Accepted Validation Decisions

| Area | Phase 4 decision | Evidence expectation |
| --- | --- | --- |
| Browser/session pattern | Validate a BFF or server-side local application session first. The browser stores only the local session cookie; Keycloak tokens stay server-side. | OIDC Authorization Code flow trace, `sub` resolution, local session decision, logout behavior, and rejected shortcut list ([Keycloak integration scope - Validated Browser Pattern](../architecture/keycloak-integration-scope.md#validated-browser-pattern), [Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)). |
| Protected-service contract | Validate local `authorization/check` first. A protected service or BFF sends trusted local account context, target service, action, and correlation ID to the local access-control service. | Request/response examples with `allow` or `deny`, reason code, fail-closed behavior, and audit correlation (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| Access stop | Immediate means the next fresh protected-service authorization check after local account disablement, archival, member role removal, or service-access-role disablement must deny. No positive authorization cache is allowed in the validation path. | Post-change denial evidence, no-positive-cache evidence, and separate notes for any in-flight request that started before the local change ([Keycloak integration scope - Validated Access-Stop Delay](../architecture/keycloak-integration-scope.md#validated-access-stop-delay), `FR-016`, `FR-032`). |
| Privileged authentication | Validate Keycloak `amr` first, then explicit Keycloak event or configured-flow evidence. If neither is explicit enough, production `admin` and `super-admin` activation is blocked for review. | Candidate `amr` claim, event/configuration evidence, or blocker record. Keycloak documents authenticator reference values and an AMR protocol mapper; RFC 8176 defines Authentication Method Reference values ([Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows), [RFC 8176](https://www.rfc-editor.org/rfc/rfc8176), `FR-034`, `FR-043`, `FR-044`). |
| Audit correlation | Minimum local audit schema: `event_id`, `correlation_id`, `timestamp`, `source_component`, `actor_account_id`, `actor_keycloak_sub`, `action`, `result`, `target_type`, `target_id`, `reason_code`, and optional Keycloak event reference. | Local audit examples plus relevant Keycloak authentication/admin events as supplemental evidence; local audit remains authoritative (`FR-027`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). |
| Keycloak Web Admin | Allow only Keycloak technical administration and inspection: realm, client, redirect URI, authentication flow, MFA/WebAuthn/OTP, session/token, event, and non-production user setup. Reject EDRLab account type, lifecycle, subject-link, service-access-role, authorization, and audit management through Keycloak Web Admin. | Allow/deny checklist and setup notes showing local access-control truth stays outside Keycloak ([Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary), `FR-038`). |
| Self-hosted operations | Review backup, restore, realm import/export, upgrade, key rotation, event retention/export, configuration drift, admin/support access, and outage behavior before Phase 5. | Document-only operations checklist unless one item blocks a runtime validation scenario ([Keycloak import/export](https://www.keycloak.org/server/importExport), [Keycloak configuration](https://www.keycloak.org/server/configuration), `FR-030`). |
| Documentation-only vs runtime | Keep Keycloak Admin boundary, BFF rationale, operational checklist, and standard Keycloak capability review as documentation-first. Runtime validation covers login, local account resolution/onboarding, privileged-authentication evidence, claim override rejection, `authorization/check`, access stop, and audit correlation. | Pass/fail/blocked records for runtime items; documentation review notes for documentation-only items ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)). |

## Runtime Scope

The runtime PoC uses one throwaway Keycloak realm, one backoffice OIDC client, Authorization Code flow, one test authentication flow with MFA/WebAuthn/OTP evidence exploration, basic session/token timeout settings, and admin/authentication events enabled ([Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers), [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)).

The PoC data set is non-production only:

- one invited `member`;
- one invited `admin`;
- one invited `super-admin`;
- unsafe onboarding cases: no local invitation, duplicate invited account, unverified email, and pre-linked subject.

Out of scope until explicit approval:

- production Keycloak deployment, hosting, database, high availability, monitoring, CI, migration, backup, or restore artifacts ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp));
- production application code, production dependencies, generated artifacts, migrations, or executable configuration outside the accepted non-production PoC scope ([AGENTS](../../AGENTS.md#current-operating-phase));
- using Keycloak roles, groups, organizations, or token claims as the authoritative EDRLab account-type or service-access-role model (`FR-002`, `FR-038`);
- replacing local project audit with Keycloak event logs (`FR-027`, `FR-035`);
- public signup, public customer identity, social login as public customer identity, or company-wide IAM replacement ([README - Initial Scope](../../README.md#initial-scope)).

## Work Packages

| Work package | Runtime or document | Goal | Evidence |
| --- | --- | --- | --- |
| `WP-001` Keycloak setup | Runtime | Configure the throwaway realm, backoffice OIDC client, redirect URI, Authorization Code flow, test authentication flow, session/token settings, and event settings. | Realm/client notes, discovery endpoint values, selected timeout settings, event settings; execute the [Keycloak PoC runtime](../../poc/keycloak/README.md) and use the [Keycloak setup runbook](./keycloak-setup-runbook.md) for evidence review. |
| `WP-002` Login and SSO boundary | Runtime | Prove Keycloak authenticates and maintains SSO while EDRLab resolves the Keycloak `sub` and owns local authorization. | Login trace, token-validation notes, `sub`, local account resolution, local session decision, logout notes. |
| `WP-003` Safe and unsafe onboarding | Runtime | Validate activation for exactly one safe invited local account and fail-closed behavior for unsafe matches. | Safe activation record; denied cases for no invitation, duplicate invitation, unverified email, and pre-linked subject (`FR-039`, `FR-043`, `FR-044`). |
| `WP-004` Privileged-authentication evidence | Runtime | Determine whether `admin` and `super-admin` activation can rely on explicit Keycloak `amr`, event, or configured-flow evidence. | Candidate `amr` claim, event/configuration evidence, or blocker. |
| `WP-005` Claim override rejection | Runtime | Show Keycloak roles, groups, or claims that look privileged do not grant EDRLab account type, lifecycle state, or service-access roles. | Token/claim example, local decision trace, explicit rejection note (`FR-038`; [Threat model TS-008](../risks/threat-model.md#threat-scenarios)). |
| `WP-006` Authorization and access stop | Runtime | Validate `authorization/check` with allow, deny, inactive account, missing role, and post-change access-stop cases. | Request/response examples, fail-closed behavior, no-positive-cache evidence, and proof that the next fresh check denies after local state changes. |
| `WP-007` Audit correlation | Runtime | Prove local audit remains authoritative and Keycloak events are supplemental. | Local audit examples using the minimum schema, relevant Keycloak events, correlation ID usage, and audit gaps. |
| `WP-008` Admin Console and operations boundary | Documentation-first | Confirm Keycloak Web Admin stays technical and review self-hosted operational responsibilities. | Keycloak Web Admin allow/deny list, operations checklist, residual-risk notes. |
| `WP-009` Results and residual risks | Documentation | Convert evidence into Phase 5 review inputs. | Pass/fail/blocked matrix, blockers, accepted limitations, residual risks, and production-hardening questions. |

Suggested order: run `WP-001` first; run `WP-002` and `WP-003` together; run `WP-004` before treating privileged onboarding as valid; run `WP-005` before `WP-006`; run `WP-006` and `WP-007` together; keep `WP-008` active throughout; finish with `WP-009`.

## Evidence Record

Every runtime scenario must produce a short evidence record:

```text
Scenario:
Work package:
Requirement links:
Setup:
Action:
Expected result:
Observed result:
Evidence collected:
Pass / fail / blocked:
Residual risk:
Production gap:
Decision impact:
```

Use `blocked` rather than inventing product behavior when Keycloak evidence is not explicit enough, especially for privileged-authentication evidence, token/session behavior, event retention, and claim shape consumed by onboarding (`FR-034`, `FR-043`, `FR-044`; [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)).

## Readiness Gate

Begin runtime PoC execution only when:

- the local `authorization/check` contract is preserved as the first protected-service authorization contract;
- the immediate next-check denial target is preserved for access-stop validation;
- the privileged-authentication evidence path is tested as `amr` first, then explicit event/configuration evidence, then blocked if neither is sufficient;
- the minimum audit correlation schema is used in runtime evidence records;
- the Keycloak Web Admin allow/deny boundary is preserved;
- the PoC data set is non-production and minimal;
- no production infrastructure, generated application artifact, production dependency, migration, or CI work is required;
- expected outputs are limited to results, gaps, residual risks, and review inputs.

If these conditions are not met, continue documentation-level evaluation instead of starting runtime PoC work ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

## References

- [ADR 0001 - Choose Keycloak for Validation](../decisions/0001-choose-keycloak-for-validation.md)
- [Solution Choice](../evaluation/solution-choice.md)
- [Solution Choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)
- [Keycloak Integration Scope](../architecture/keycloak-integration-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [README - Initial Scope](../../README.md#initial-scope)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak OIDC Endpoints and Grant Types](https://www.keycloak.org/securing-apps/oidc-layers)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [Keycloak Configuration](https://www.keycloak.org/server/configuration)
- [RFC 8176 - Authentication Method Reference Values](https://www.rfc-editor.org/rfc/rfc8176)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
