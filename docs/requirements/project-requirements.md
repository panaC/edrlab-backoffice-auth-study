# Project Requirements

Status: Draft
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements
Last reviewed: 2026-05-06

## Contents

- [Purpose](#purpose)
- [Current Inputs](#current-inputs)
- [Requirement Groups](#requirement-groups)
- [Traceability Summary](#traceability-summary)
- [Open Questions](#open-questions)
- [References](#references)

## Purpose

This document translates the immutable feature specification and the latest stakeholder scoping answers into Phase 2 requirements. It does not choose a vendor, product, architecture, database, hosting model, token strategy, or implementation stack, which remain explicitly unsettled by the project brief ([README](../../README.md#phase-2-debate-topics), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

## Current Inputs

| Input | Current Phase 2 interpretation | Source |
| --- | --- | --- |
| Priority deliverable | Requirements are the primary Phase 2 artifact to refine first. | User-provided answer, 2026-05-06. |
| Starting point | The backoffice auth server starts from zero, so requirements should not assume legacy migration constraints unless discovered later. | User-provided answer, 2026-05-06. |
| Human actors | Initial human actors are company employee administrators and member users. The root specification also separates super-admin, admin, and member responsibilities ([README](../../README.md#actors)). | User-provided answer, 2026-05-06; [README](../../README.md#actors). |
| Super-admin-only minimum operations | Audit reads, authenticator reset, administrator recovery, role definition changes, and break-glass activation are super-admin-only at minimum. | User-provided answer, 2026-05-06; [README](../../README.md#actors); [README](../../README.md#minimum-feature-requirements). |
| Machine access | Service-to-machine access is not part of the initial scope. Protected backend services still need to validate and enforce human-user access to company-controlled services ([README](../../README.md#minimum-feature-requirements)). | User-provided answer, 2026-05-06; [README](../../README.md#minimum-feature-requirements). |
| Permission model | The initial permission model should be simple fixed roles, aligned with the feature specification's role-based service access requirement ([README](../../README.md#minimum-feature-requirements)) and the RBAC model explained in the wiki ([RBAC](../wiki/05-rbac.md)). | User-provided answer, 2026-05-06; [README](../../README.md#minimum-feature-requirements); [RBAC](../wiki/05-rbac.md). |
| Role assignment duration | Role assignments are permanent by default. Temporary role assignments with expiration are not part of the baseline requirements unless a later business or security requirement justifies them. | User-provided answer, 2026-05-06; [README](../../README.md#minimum-feature-requirements); [RBAC](../wiki/05-rbac.md). |
| Primary risk concern | Security is the main risk area to refine in Phase 2. The feature specification already requires a production-grade internal access-control security posture, even if a first minimal version uses simpler authentication ([README](../../README.md#minimum-feature-requirements)). | User-provided answer, 2026-05-06; [README](../../README.md#minimum-feature-requirements). |
| Candidate list | No candidates are named yet. Candidate identification and comparison should remain later-phase or preparatory work, not a final decision ([Project governance](../../PROJECT-GOVERNANCE.md#phase-3---candidate-approach-catalog)). | User-provided answer, 2026-05-06; [Project governance](../../PROJECT-GOVERNANCE.md#phase-3---candidate-approach-catalog). |
| PoC learning target | A future lightweight PoC should test OAuth2/OIDC flows, the fixed-role permission model, backoffice integration, and the administration API. OAuth2 and OIDC are protocol foundations for authorization tokens and login identity respectively ([RFC 6749](https://www.rfc-editor.org/rfc/rfc6749), [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)). | User-provided answer, 2026-05-06; [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749); [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html). |
| PoC protected-service count | The PoC should stay minimal and use one protected backend service to test authorization behavior. Multi-service service-boundary testing is not required for the first PoC. | User-provided answer, 2026-05-06; [README](../../README.md#minimum-feature-requirements). |

## Requirement Groups

### Business and Scope

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-BIZ-001 | The system must serve internal company backoffice users only. | The immutable specification excludes public signup, public customer accounts, social login, and external consumer identity flows ([README](../../README.md#company-goal), [README](../../README.md#minimum-feature-requirements)). | Requirements and architecture notes do not introduce public-customer or social-login scope. |
| REQ-BIZ-002 | Member accounts must be administrator-created and administrator-managed. | The feature specification requires administrator-only member creation and management ([README](../../README.md#minimum-feature-requirements)). | Member lifecycle, admin API, and audit requirements all treat member creation and updates as privileged operations. |
| REQ-BIZ-003 | The initial study scope must cover human users only: super-admins, admins, and members. | The feature specification defines those actors, and the latest stakeholder input excludes service-to-machine access for the initial scope ([README](../../README.md#actors); user-provided answer, 2026-05-06). | Service accounts and Client Credentials are tracked only as future or out-of-scope questions unless explicitly reintroduced. |
| REQ-BIZ-004 | The solution must remain understandable and operable by the internal team. | Simplicity is an explicit feature requirement, not only an implementation preference ([README](../../README.md#minimum-feature-requirements)). | Architecture options must explain operational complexity, not only feature coverage. |

### Identity and Lifecycle

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-ID-001 | Member records must use stable identifiers separate from mutable email and name attributes. | Stable identifiers are required by FS-003 ([README](../../README.md#minimum-feature-requirements)). | Requirements and data-model notes distinguish immutable member ID from mutable profile fields. |
| REQ-ID-002 | Member lifecycle must include at least `invited`, `active`, `disabled`, and `archived`. | Lifecycle states are required by FS-004 ([README](../../README.md#minimum-feature-requirements)). | Lifecycle requirements explain which states can obtain access and which admin operations change state. |
| REQ-ID-003 | Non-active members must not obtain new access to protected services. | FS-005 requires non-active members to be blocked from new access and requires access-removal behavior to be documented and evaluated ([README](../../README.md#minimum-feature-requirements)). | Phase 2 must define the expected revocation or stale-access window as an open requirement before later candidate evaluation. |

### Authorization and Access Checks

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-AUTHZ-001 | The initial authorization model must be simple role-based access to protected backend services. | The immutable specification requires role-based service access, and the stakeholder confirmed fixed roles as the expected baseline ([README](../../README.md#minimum-feature-requirements); user-provided answer, 2026-05-06). | Role definitions, role assignments, and access checks stay explicit and small; fine-grained policy engines are not assumed. |
| REQ-AUTHZ-002 | Protected backend services must enforce authorization server-side. | FS-011 requires protected backend services to determine whether an active member is allowed to access a service, and OWASP authorization guidance emphasizes server-side authorization controls ([README](../../README.md#minimum-feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Architecture notes identify where token validation and permission checks happen for each option. |
| REQ-AUTHZ-003 | Role management must support create, list, assign, and remove-role operations. | FS-007 requires administrator role management and role assignment operations ([README](../../README.md#minimum-feature-requirements)). | Admin API requirements include role definition and assignment operations. |
| REQ-AUTHZ-004 | Privilege escalation must be controlled. | The actor model states that admins must not silently grant themselves super-admin privileges or bypass privileged auditability ([README](../../README.md#actors)). | Requirements identify self-escalation, delegated escalation, and super-admin-only operations as security risks. |
| REQ-AUTHZ-005 | Role assignments must be permanent by default. | The stakeholder confirmed permanent assignments as the baseline, and the feature specification requires administrator-managed role assignment and removal without requiring assignment expiration ([README](../../README.md#minimum-feature-requirements); user-provided answer, 2026-05-06). | Baseline role-assignment requirements do not require expiration fields or temporary-access workflows; temporary assignments remain a later optional requirement. |

### OAuth2, OIDC, and Tokens

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-OIDC-001 | Phase 2 must evaluate OAuth2/OIDC login and API-access flows for the future PoC. | The stakeholder selected OAuth2/OIDC flow testing as a PoC target, while OAuth2 defines access-token issuance concepts and OIDC defines the identity layer on top of OAuth2 ([RFC 6749](https://www.rfc-editor.org/rfc/rfc6749), [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)). | The PoC plan must identify login, token exchange, token validation, and protected API access checks as learning goals. |
| REQ-OIDC-002 | Browser-based login candidates must evaluate Authorization Code Flow with PKCE rather than Implicit Flow for new browser clients. | PKCE is standardized in RFC 7636, and OAuth 2.0 security best current practice discourages the Implicit Flow for modern browser-based applications ([RFC 7636](https://www.rfc-editor.org/rfc/rfc7636), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)). | Later candidate and PoC documents do not treat Implicit Flow as the default browser-login path. |
| REQ-OIDC-003 | Resource servers must validate access tokens before trusting token claims or authorization inputs. | Bearer-token usage and OAuth2 security guidance require careful validation of token issuer, audience, lifetime, and integrity or introspection result before protected-resource access is granted ([RFC 6750](https://www.rfc-editor.org/rfc/rfc6750), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)). | Architecture options describe validation responsibility for each protected backend service. |

### Administration and Audit

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-ADMIN-001 | The administration capability must manage members, roles, role assignments, service access checks, and audit-supporting operations. | FS-006 through FS-012 define administrator CRUD, role, service access, and member-profile control responsibilities ([README](../../README.md#minimum-feature-requirements)). | Admin API scope is explicit and does not depend on frontend-only controls. |
| REQ-ADMIN-002 | Super-admin, admin, and member responsibilities must remain separated. | FS-013 assigns recovery, authenticator reset, administrator recovery, audit access, and future break-glass responsibilities to the super-admin role ([README](../../README.md#minimum-feature-requirements)). | Requirements identify high-impact operations and owner role boundaries. |
| REQ-ADMIN-003 | Audit reads, authenticator reset, administrator recovery, role definition changes, and break-glass activation must be super-admin-only at minimum. | The stakeholder confirmed these operations as super-admin-only, and the feature specification already requires separation of super-admin, admin, and member responsibilities ([README](../../README.md#actors), [README](../../README.md#minimum-feature-requirements); user-provided answer, 2026-05-06). | Admin/API and architecture notes treat these operations as high-impact privileged operations requiring explicit server-side authorization and audit events. |
| REQ-AUDIT-001 | Audit events must cover member lifecycle changes, role changes, access configuration changes, authorization denials, audit reads or exports, and recovery/reset actions. | FS-015 lists these audit event categories, and FS-016 requires super-admin audit consultation with audit access itself logged ([README](../../README.md#minimum-feature-requirements)). | Risk and architecture artifacts explain where audit events are produced and who can read them. |

### Security and Operations

| ID | Requirement | Rationale and source | Phase 2 acceptance |
| --- | --- | --- | --- |
| REQ-SEC-001 | Security must be treated as the top Phase 2 risk lens. | The stakeholder named security as the primary concern, and FS-014 requires a production-grade internal access-control security posture ([README](../../README.md#minimum-feature-requirements); user-provided answer, 2026-05-06). | Requirements, risks, and architecture options identify concrete controls and open security questions. |
| REQ-SEC-002 | The study must evaluate access-removal behavior for already-issued access. | FS-005 requires access removal for already-issued access to be simple, documented, and evaluated ([README](../../README.md#minimum-feature-requirements)). | Token lifetime, revocation, introspection, or server-side authorization lookup are tracked as evaluation questions, not silently assumed. |
| REQ-OPS-001 | Architecture options must compare operational burden, especially for microservices or self-hosted IAM responsibilities. | The project requires simplicity and explicitly leaves architecture and hosting decisions open ([README](../../README.md#minimum-feature-requirements), [README](../../README.md#phase-2-debate-topics)). | Architecture analysis includes deployment, monitoring, key rotation, backup, audit, and incident-response ownership questions. |

## Traceability Summary

| Requirement area | Feature-spec anchors | Current source of refinement |
| --- | --- | --- |
| Internal-only scope | FS-001, FS-002 | User confirmed company employee admins and member users only. |
| Member lifecycle | FS-003, FS-004, FS-005, FS-006 | No extra lifecycle states added yet. |
| RBAC and service access | FS-007, FS-008, FS-009, FS-011 | User confirmed fixed roles as the baseline and permanent role assignments by default. |
| Admin capability | FS-010, FS-012, FS-013 | Admin API remains in scope for PoC learning; user confirmed audit reads, authenticator reset, administrator recovery, role definition changes, and break-glass activation as super-admin-only minimum operations. |
| Security posture | FS-014 | User selected security as the primary risk concern. |
| Auditability | FS-015, FS-016 | Audit requirements remain mandatory. |
| Simplicity | FS-017 | Architecture options must account for operational complexity. |
| OAuth2/OIDC PoC focus | FS-011, FS-014, FS-017 | User selected OAuth2/OIDC flows, RBAC, backoffice integration, and admin/API as PoC targets; user also confirmed the first PoC should stay minimal with one protected backend service. |

## Open Questions

1. Which concrete protected backend service should be used for the first PoC: a member-management API, a synthetic demo API, or an existing internal API?
2. Which human login method should be evaluated first: local username/password, passkey/passwordless, workforce SSO federation, or a provider-hosted login page?
3. What token stale-access window is acceptable after member disablement or role removal: immediate, minutes, or access-token lifetime?
4. What audit retention, export, and privacy expectations apply to internal employee identity data?

## References

- [README - Immutable Feature Specification](../../README.md#immutable-feature-specification)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [Wiki - RBAC and Permission Modeling](../wiki/05-rbac.md)
- [Wiki - OAuth2 Flows](../wiki/06-oauth2-flows.md)
- [Wiki - Token Lifecycle](../wiki/12-token-lifecycle.md)
- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7636 - Proof Key for Code Exchange](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
