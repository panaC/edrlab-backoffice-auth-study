# Threat Model

Status: Draft
Phase: Phase 2 - Requirements and Risk Framing
Scope: Risks
Last reviewed: 2026-05-07

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Source Inputs](#source-inputs)
- [Method](#method)
- [Protected Assets and Security Objectives](#protected-assets-and-security-objectives)
- [Actors and Trust Boundaries](#actors-and-trust-boundaries)
- [External Dependencies](#external-dependencies)
- [Entry Points](#entry-points)
- [Exit Points](#exit-points)
- [Threat Scenarios](#threat-scenarios)
- [Requirement Refinement Candidates](#requirement-refinement-candidates)
- [Assess Your Work](#assess-your-work)
- [References](#references)

## Purpose

This document records Phase 2 threat modeling for the internal backoffice access-control study. It supports security requirement refinement before candidate evaluation while staying within the Phase 2 study scope ([README](../../README.md#initial-scope), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Scope

The threat model covers the in-scope study areas from the immutable feature specification: internal member lifecycle management, administrator-only account and role management, role-based access to protected backend services, service access checks, auditability, and security requirement refinement ([README](../../README.md#initial-scope)).

It does not select a final vendor, product, architecture, hosting model, implementation stack, access-token format, or browser token storage model during Phase 2 ([Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Source Inputs

- Feature specification and initial study scope in the root [README](../../README.md#minimum-feature-requirements).
- Phase 2 boundaries and evidence rules in [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing).
- Consolidated feature requirements in [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements).

## Method

This document follows the four-step OWASP threat-modeling process while staying within Phase 2 boundaries: it frames risks and requirement refinements without selecting a final product, architecture, token strategy, or implementation stack ([OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

| OWASP process step | How this document applies it |
| --- | --- |
| Step 1: Scope your work | Use the immutable feature specification, Phase 2 boundaries, protected assets, actors, external dependencies, entry points, exit points, and trust boundaries to define what is being modeled. |
| Step 2: Determine threats | Record concrete threat scenarios against the protected assets and trust boundaries. |
| Step 3: Determine countermeasures and mitigation | Translate mitigations into requirement refinement candidates, not final implementation choices. |
| Step 4: Assess your work | Review assumptions, open questions, traceability, and whether the model is sufficient before candidate evaluation. |

The OWASP Threat Modeling Project is used as the main OWASP entry point for broader technique and methodology references, while the OWASP community process page is used to structure this document ([OWASP Threat Modeling Project](https://owasp.org/www-project-threat-modeling/), [OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process)).

## Protected Assets and Security Objectives

| Protected asset | Security objective | Source |
| --- | --- | --- |
| Member identities and profile data | Keep stable member identity separate from mutable profile attributes, and allow profile changes only through authorized admin workflows. | [FS-003](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements) |
| Member lifecycle state | Prevent non-active members from obtaining new protected-service access, and define how already-issued access stops after disablement, archival, or access removal. | [FS-004](../../README.md#minimum-feature-requirements), [FS-005](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Roles and role assignments | Ensure service access is granted only through authorized role assignment and cannot be changed silently or by unauthorized actors. | [FS-007](../../README.md#minimum-feature-requirements), [FS-008](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Protected-service access decisions | Ensure backend services make server-side access decisions based on active account state, account type, and member service-access role assignments. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Actor responsibility separation | Preserve separation between member, admin, and super-admin responsibilities, especially for recovery, login reset, audit access, and future break-glass handling. | [FS-013](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Access tokens or sessions | Ensure protected services can validate access server-side without assuming a final token format or browser storage model during Phase 2. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Audit records | Preserve useful auditability for privileged and security-relevant operations, including audit access itself. | [FS-015](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Recovery and login-reset actions | Keep member and administrator recovery or login reset scoped to the actor's own account. Administrators cannot recover or reset member accounts or other administrator accounts. Security-relevant recovery or reset actions remain auditable. | [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Actors and Trust Boundaries

### Actors and System Participants

| Actor or participant | Role in the threat model | Source |
| --- | --- | --- |
| Member | Internal user who can view their own profile, own only their own member recovery and login reset, and access protected backend services only when active and authorized by role. | [Actors](../../README.md#actors-and-role-types), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Admin | Privileged operator who manages members, role assignments, service access, and member profile data. Admins own only their own administrator recovery and login reset, and cannot recover or reset member accounts or other administrator accounts. Admin actions are security-relevant and must be auditable. | [Actors](../../README.md#actors-and-role-types), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Super-admin | Highest-privilege operator responsible for audit access and any future break-glass process if adopted. | [Actors](../../README.md#actors-and-role-types), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Protected backend service | Company-controlled service that must determine whether an active account is authorized before granting access. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Access-control capability | Project capability responsible for member lifecycle, roles, role assignments, service access checks, and audit-supporting operations. | [FS-010](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Audit reader | Super-admin activity that consults or exports audit records. Audit access itself must be logged. | [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

### Trust Boundaries

| Trust boundary | Why it matters | Source |
| --- | --- | --- |
| User browser or client to access-control capability | Requests crossing this boundary must not be trusted only because they come from an internal user interface. Profile changes, role assignment, and service access changes remain server-side admin workflows. | [FS-006](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Admin interface to privileged admin operations | Admin workflows can change member records, roles, and service access, so this boundary needs strong authorization and auditability. | [FS-006](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Access-control capability to protected backend services | Protected services must make server-side access decisions using active account state, account type, and member service-access role assignments instead of trusting frontend-only checks. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Access-control capability to audit storage | Audit records support accountability for privileged and security-relevant operations, so audit writes and reads need integrity and access-control assumptions recorded. | [FS-015](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Super-admin audit access to audit records | Super-admin audit reads and exports cross into sensitive accountability data and must themselves be logged. | [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Authentication, session, or token handling to protected-service authorization checks | Phase 2 has not selected a token format or browser storage model, but protected services still need server-side validation before access. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## External Dependencies

OWASP treats external dependencies as part of threat-model scoping because dependencies outside the immediate application code can introduce security assumptions and failure modes ([OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process)). This Phase 2 list stays decision-neutral: it identifies dependency categories that candidate approaches must evaluate without choosing a final vendor, product, hosting model, token strategy, database, or implementation stack ([Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

| ID | External dependency | Why it matters | Source |
| --- | --- | --- | --- |
| ED-001 | Authentication, session, or token mechanism | The access-control capability depends on a secure way to authenticate internal members and carry authorization evidence to protected services; Phase 2 has not selected the mechanism or token format. | [FS-014](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| ED-002 | MFA or phishing-resistant passwordless authenticator support for privileged users | Admin and super-admin accounts are high-value targets, so candidate approaches must account for stronger privileged-user authentication without assuming the final authenticator model. | [FS-014](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| ED-003 | Protected backend services | Protected services depend on the access-control capability for server-side authorization decisions; a broken integration can expose company-controlled backend services. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| ED-004 | Audit storage, retention, and export mechanism | Auditability depends on records that are complete, attributable, append-only in the consolidated requirements, and controlled for reads and exports. | [FS-015](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| ED-005 | Member invitation or onboarding delivery path | New members start as `invited` and become `active` after first successful connection, so the invitation or onboarding path must not become an account-takeover shortcut. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| ED-006 | Backup, recovery, upgrade, and support process for each candidate approach | Candidate evaluation must account for operational recovery and maintenance because loss, corruption, or stale operation of identity and audit data can affect access control and accountability. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Entry Points

OWASP uses entry points to identify where a potential attacker or legitimate actor can interact with the system or supply data across a trust boundary ([OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process)). The table below records logical entry points for the study rather than final API routes.

| ID | Entry point | Expected actor or participant | Security relevance | Source |
| --- | --- | --- | --- | --- |
| EP-001 | Member sign-in or first successful connection | Invited member, active member, authentication mechanism | Activates member access and creates the first practical opportunity for authentication, session, or token abuse. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-002 | Member self-profile read | Active member | Must show only the member's own profile data and must not become a profile-update path. | [FS-012](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-003 | Admin member-management operations | Admin | Allows member creation, update, disablement, restoration, archival, and role-based service-access removal, so authorization and auditability are required. | [FS-006](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-004 | Role creation, role listing, role assignment, and role removal | Admin, super-admin | Service-access-role catalog management and member role assignment or removal can change who reaches protected services and can create privilege-escalation paths if responsibilities are blurred. | [FS-007](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-005 | Protected-service authorization check | Protected backend service | Determines whether an active account is allowed by account type or member service-access role assignment and must fail closed when the decision cannot be made safely. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-006 | Audit read or export operation | Super-admin | Exposes sensitive accountability records and must itself be logged. | [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-007 | Own-account recovery or login-reset operation | Member, admin | Can recover or take over the actor's own account access if abused, so actor-specific verification, authentication freshness, and audit evidence need explicit refinement. Cross-account recovery or reset by administrators is out of current scope. | [FS-013](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| EP-008 | Candidate-specific token, session, revocation, or introspection endpoint | Authentication, session, or token mechanism; protected backend service | The exact mechanism is undecided, but any endpoint that issues, refreshes, validates, revokes, or introspects access evidence becomes security-critical. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Exit Points

OWASP uses exit points to identify where data leaves the modeled system or component; exit points can expose sensitive data, authorization results, error details, or audit data if controls are missing ([OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process)). The table below keeps exit points at the logical study level.

| ID | Exit point | Data or result leaving the capability | Security relevance | Source |
| --- | --- | --- | --- | --- |
| XP-001 | Authorization decision returned to a protected backend service | Allow or deny result, member identity reference, role or service-access context | Incorrect or stale decisions can grant access to company-controlled backend services. | [FS-011](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| XP-002 | Access token, session artifact, or equivalent access evidence returned to a client or service | Bearer token, session identifier, or equivalent access artifact if selected | Access evidence must be protected because possession can be enough to access protected resources when bearer-style tokens are used. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750) |
| XP-003 | Member profile data shown to a member or admin | Profile fields tied to a stable member identifier | Profile data must be scoped to the authorized viewer and must not let mutable attributes replace stable identity. | [FS-003](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| XP-004 | Audit event written to audit storage | Security-relevant event, actor, target, action, timestamp, and decision context to be refined | Missing, mutable, or unattributable audit data weakens investigation and accountability. | [FS-015](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| XP-005 | Audit records returned to a super-admin or exported | Audit query results or exported audit records | Audit reads and exports expose sensitive accountability data and must be logged. | [FS-016](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| XP-006 | Recovery or login-reset result | Reset confirmation, changed login state, or recovery decision record | Reset outcomes must preserve accountability and must not erase evidence of who approved or performed recovery. | [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| XP-007 | Operational backup, recovery, support, or upgrade artifact | Backup, restore output, support export, or upgrade state for a candidate approach | Candidate evaluation must verify that operational artifacts do not undermine access control, audit retention, or recovery expectations. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Threat Scenarios

| ID | Threat | What can go wrong | Existing requirement coverage | Refinement needed |
| --- | --- | --- | --- | --- |
| TS-001 | Admin privilege escalation | An admin grants themselves super-admin capability, changes role definitions indirectly, or performs privileged actions without proper separation. | `FS-013`, `FS-015`, and consolidated `FR-*` requirements require responsibility separation, auditability, and strong server-side authorization for privileged operations ([README](../../README.md#actors-and-role-types), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Define explicit controls for self-service privilege changes, super-admin-only operations, and audit evidence for privilege changes. |
| TS-002 | Access after disablement or role removal | A disabled, archived, or de-authorized member continues accessing a protected backend service because already-issued access is still accepted. | `FS-005`, `FS-011`, and consolidated `FR-*` requirements require non-active accounts to lose new access and protected services to deny access when authorization cannot be made safely ([README](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Define acceptable revocation delay and required behavior for already-issued access after lifecycle or role changes. |
| TS-003 | Protected service trusts the wrong signal | A backend service grants access based on frontend state, unvalidated claims, stale role data, or incomplete authorization checks. | `FS-011` and consolidated `FR-*` requirements require backend services to validate access server-side and avoid frontend-only authorization checks ([README](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Define minimum protected-service validation rules: active account state, account type or assigned member service-access role, trusted issuer or lookup source, and fail-closed behavior. |
| TS-004 | Audit gap or audit tampering | Security-relevant admin, super-admin, access-denial, recovery, or audit-read actions are missing, mutable, or not attributable enough to investigate abuse. | `FS-015`, `FS-016`, and consolidated `FR-*` requirements require audit coverage for privileged and security-relevant operations, including audit access itself ([README](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Define required audit event fields, integrity expectations, read/export logging, and operational ownership for audit review. |
| TS-005 | Recovery or login-reset abuse | A member or administrator own-account recovery or login-reset path is abused to take over an account, bypass stronger authentication, or erase accountability. An admin cross-account reset path would violate the current scope. | `FS-013`, `FS-014`, `FS-015`, and consolidated `FR-*` requirements require own-account recovery and login-reset separation, audit evidence, and privileged authentication controls for admin and super-admin accounts ([README](../../README.md#actors-and-role-types), [README](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Define actor-specific own-account recovery and login-reset rules, what evidence is logged, whether step-up or recent authentication is needed, and what remains out of scope. |

## Requirement Refinement Candidates

These candidates are not final requirements. They record security refinements discovered during threat modeling and need review before any promotion to the consolidated feature requirements list.

| Source threat | Candidate refinement | Status |
| --- | --- | --- |
| `TS-001` | Define controls that prevent an admin from granting themselves super-admin privileges, changing super-admin-only role definitions indirectly, or performing privileged operations without auditable authorization. | Draft |
| `TS-002` | Define the acceptable revocation delay after member disablement, archival, role removal, or service-access removal, including expected behavior for already-issued access. | Draft |
| `TS-003` | Define minimum protected-service authorization validation rules: active account state, account type or assigned member service-access role, trusted authorization source, and fail-closed behavior when the decision cannot be made safely. | Draft |
| `TS-004` | Define minimum audit event fields, audit integrity expectations, audit read/export logging, and responsibility for reviewing security-relevant audit events. | Draft |
| `TS-005` | Define member and administrator own-account recovery and login-reset rules, required audit evidence, and whether step-up or recent authentication is required for those operations. | Draft |

## Assess Your Work

This section checks whether the threat model is fit for Phase 2 use. It is not a production security sign-off and does not replace later candidate evaluation or implementation review ([OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

| Review question | Assessment | Result |
| --- | --- | --- |
| Is the modeled scope clear? | The scope is tied to the immutable feature specification and Phase 2 boundaries. | Pass |
| Are protected assets identified? | The model identifies member identity, lifecycle state, roles, access decisions, privileged operations, tokens or sessions, audit records, and recovery or login-reset actions. | Pass |
| Are actors and trust boundaries identified? | The model identifies the main legitimate participants and the key boundaries where trust changes or server-side checks are required. | Pass |
| Are external dependencies, entry points, and exit points identified? | The model records decision-neutral Phase 2 dependencies and logical interaction points without selecting final architecture, token format, or implementation details. | Pass |
| Are concrete threats recorded? | The initial threat set covers privilege escalation, access after disablement or role removal, incorrect protected-service trust, audit gaps or tampering, and recovery or login-reset abuse. | Pass |
| Are mitigations linked to requirements work? | The model records requirement refinement candidates instead of silently changing the consolidated feature requirements list. | Pass |
| Is the model ready for candidate evaluation input? | The model is ready to inform Phase 2 requirement refinement, but candidate evaluation should not treat the draft refinements as accepted requirements until they are reviewed. | Needs review |
| Does the model avoid final solution selection? | The model does not select a vendor, architecture, token format, browser storage model, implementation stack, or production design. | Pass |

## References

- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [README - Actors and Role Types](../../README.md#actors-and-role-types)
- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [RFC 6750 - OAuth 2.0 Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [OWASP - Threat Modeling Project](https://owasp.org/www-project-threat-modeling/)
- [OWASP - Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [OWASP - Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process)
