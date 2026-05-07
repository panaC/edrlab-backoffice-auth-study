# Feature Requirements Review

Status: Draft
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements
Last reviewed: 2026-05-07

## Contents

- [Purpose](#purpose)
- [Source Inputs](#source-inputs)
- [Working Rules](#working-rules)
- [Consolidation Target](#consolidation-target)
- [Review Queue](#review-queue)
- [Decision Log](#decision-log)
- [Accepted Theme Notes](#accepted-theme-notes)
- [Coverage Review](#coverage-review)
- [Open Questions](#open-questions)
- [Accepted Requirements](#accepted-requirements)
- [References](#references)

## Purpose

This document records the step-by-step review used to consolidate the root `README.md` project brief, the former `README.md` `FS-*` table, and the former Phase 2 requirements baseline into one final-solution feature requirements list in root `FEATURE-REQUIREMENTS.md` ([README](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md)).

The working objective, provided by the user on 2026-05-07, is to progressively define one unique, goal-oriented, concrete, and complete feature requirements list, then retire the separate baseline file only after coverage has been verified. This review is the collaboration trail for those decisions.

## Source Inputs

| Source | How it is used |
| --- | --- |
| Root `README.md` | Primary project brief, core features, actor model, initial scope, and the former minimum `FS-*` requirement source now replaced by root `FEATURE-REQUIREMENTS.md` ([README](../../README.md#core-features), [README](../../README.md#actors-and-role-types), [README](../../README.md#minimum-feature-requirements)). |
| Root `FEATURE-REQUIREMENTS.md` | Target document for the final consolidated feature requirements list ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md)). |
| Former `docs/requirements/baseline.md` | Retired Phase 2 baseline material mined for useful `RB-*` detail before deletion; coverage is preserved in this review and in the consolidated feature requirements list. |
| `docs/requirements/feature-scope-review.md` | Historical validation notes for the earlier `FS-*` review, useful as context but subject to re-validation when it conflicts with current source text ([Feature scope review](./feature-scope-review.md)). |
| `docs/requirements/baseline-review.md` | Historical validation trail for `RB-*` requirements, useful for preserving rationale during consolidation ([Requirements baseline review](./baseline-review.md)). |

## Working Rules

- Review one requirement theme at a time and record each accepted wording before moving to the next one.
- Prefer goal-oriented requirements over implementation choices. A requirement should say what capability or invariant the system must provide, not which vendor, token format, database, or architecture must provide it ([Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).
- Keep each final requirement concrete enough to test during later evaluation.
- Resolve conflicts in favor of the current user decision and the current root `README.md` unless the user explicitly changes the project brief ([AGENTS](../../AGENTS.md#instruction-priority)).
- Record unresolved points as open questions instead of turning them into hidden decisions ([Project governance](../../PROJECT-GOVERNANCE.md#evidence-standard)).
- Keep this review as the coverage trail after retiring the former baseline file.

## Consolidation Target

The target artifact is root `FEATURE-REQUIREMENTS.md`. The consolidated list should cover these reader tasks without requiring a separate baseline document:

| Area | Target content |
| --- | --- |
| Goal and definitions | Keep the existing goal and definitions as the shared vocabulary for the feature list ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#goal), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#definitions)). |
| Invariants | Record rules that must not be violated, such as immutable account types and separation from service-access roles ([README](../../README.md#actors-and-role-types)). |
| Feature requirements | Maintain one unique list of accepted feature requirements, with stable identifiers and traceability to former `FS-*`/`RB-*` material where that historical context still matters. |
| Out of scope | Keep explicit exclusions from the initial study scope so the final feature list does not silently expand to public identity, consumer IAM, or implementation decisions ([README](../../README.md#initial-scope)). |

## Review Queue

| Order | Theme | Why it comes here | Status |
| --- | --- | --- | --- |
| 1 | Responsibility model | Account type responsibilities and service-access-role ownership affect lifecycle, role assignment, audit, and escalation rules. | Covered; README aligned |
| 2 | User population and account creation | Scope and account creation boundaries prevent the list from accidentally growing public or self-service flows. | Draft-covered |
| 3 | Account lifecycle and retention | Lifecycle states drive access eligibility, audit events, and restoration/archive rules. | Draft-covered |
| 4 | Stable identity and authentication boundary | The access-control capability needs a stable authenticated subject without taking over identity-provider responsibilities. | Draft-covered |
| 5 | Service-access roles and protected-service decisions | These requirements define how active accounts receive access to protected backend services. | Draft-covered |
| 6 | Administration capability | The final list must describe required admin and super-admin operations without choosing the technical form. | Draft-covered |
| 7 | Auditability | Sensitive and privileged operations require auditable events and controlled audit access. | Draft-covered |
| 8 | Security and operational constraints | Production-grade posture, revocation behavior, and simplicity must stay visible without becoming product or architecture decisions. | Draft-covered |
| 9 | Out-of-scope and deletion readiness | Before retiring `baseline.md`, verify that useful coverage has moved into the unique feature list or into explicit open questions. | Baseline retired |

## Decision Log

| ID | Topic | Decision | Source |
| --- | --- | --- | --- |
| D-001 | Review artifact | Use this document as the live review trail for consolidating feature requirements into root `FEATURE-REQUIREMENTS.md`. | User-provided working objective, 2026-05-07 |
| D-002 | Baseline retirement | Do not delete `docs/requirements/baseline.md` until the consolidated list has been checked for coverage and unresolved points have been preserved as assumptions or open questions. | User-provided working objective, 2026-05-07; [Project governance](../../PROJECT-GOVERNANCE.md#evidence-standard) |
| D-003 | Responsibility model | Treat the current `README.md` responsibility model as authoritative for consolidation: super-admins create, list, assign, and remove service-access roles for eligible `admin` and `member` accounts; admins manage member lifecycle and profile data within scope but do not assign service-access roles, consult audit records, or reset another account; members can view their own profile in read-only mode and access protected backend services only when active and authorized through assigned service-access roles. | User confirmation, 2026-05-07; [README](../../README.md#actors-and-role-types), [README](../../README.md#minimum-feature-requirements) |
| D-004 | Identifier scheme | Use new `FR-*` identifiers for the consolidated feature requirements list. Keep old `FS-*` and `RB-*` identifiers only as source and traceability references while the consolidation is in progress. | User validation of `FR-001`, 2026-05-07 |
| D-005 | Responsibility model revision | Reopen the responsibility model. The user wants a simpler split: super-admins do not use service-access roles for protected-service access and only manage or assign them; admins have broad service-access-role access and can assign service-access roles to members. Exact wording must distinguish protected-service access from role-management access before the final requirement is written. | User correction, 2026-05-07 |
| D-006 | Admin service-access model | Admin accounts automatically have access to all protected services covered by all service-access roles, and admins can assign those service-access roles to member accounts. This supersedes the earlier current-`README.md` interpretation for admin service-access assignment. | User confirmation, 2026-05-07 |
| D-007 | Super-admin role assignment target | Super-admins may assign or remove service-access roles for `member` accounts, but do not assign service-access roles to `admin` accounts because active admins already receive the covered protected-service access automatically. | User confirmation, 2026-05-07 |
| D-008 | Account creation authority | Super-admins can create `admin` and `member` accounts. Admins can create only `member` accounts. Initial creation of the first `super-admin` is a bootstrap/provisioning concern, not a normal self-service backoffice workflow. | User confirmation, 2026-05-07 |
| D-009 | Out-of-scope consolidation | Replace the placeholder out-of-scope section in root `FEATURE-REQUIREMENTS.md` with explicit exclusions for public identity flows, company-wide IAM replacement, final vendor/architecture/implementation decisions, production high availability as a minimum feature, custom IAM/cryptographic implementation, implementation artifacts outside PoC scope, and break-glass until reopened. | User confirmation, 2026-05-07; [README](../../README.md#initial-scope), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#out-of-scope) |
| D-010 | README responsibility-model realignment | Realign root `README.md` with the consolidated model: active admins automatically access all protected services covered by service-access roles, admins and super-admins assign service-access roles to members only, super-admins do not receive protected-service access through service-access roles, and service-access roles are not assigned to admin accounts. | User confirmation, 2026-05-07; [README](../../README.md#actors-and-role-types), [README feature requirements source](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-011 | Baseline retirement | Delete the former Phase 2 `docs/requirements/baseline.md` file after coverage review, README realignment, out-of-scope consolidation, and explicit user approval. Keep root `FEATURE-REQUIREMENTS.md` as the unique feature requirements list. | User confirmation, 2026-05-07; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md), [Deletion readiness](#deletion-readiness) |

## Accepted Theme Notes

### Responsibility Model

The consolidated feature requirements no longer follow the previous root `README.md` responsibility model as originally written. The user reopened this topic on 2026-05-07 to simplify the split between `super-admin` and `admin`, and `README.md` was realigned by `D-010`.

Validated so far: `super-admin`, `admin`, and `member` remain fixed account types, and service-access roles remain independent from account types ([README](../../README.md#actors-and-role-types)).

Revision settled: super-admins should not receive protected-service access through service-access roles; they manage the role catalog and may assign or remove service-access roles for member accounts. Admins automatically have protected-service access to all services covered by all service-access roles, and can assign those service-access roles to member accounts. Members receive protected-service access only through assigned service-access roles.

Candidate final requirements to draft from this decision:

| Candidate ID | Requirement intent |
| --- | --- |
| `FR-001` | Accepted: every backoffice account has exactly one fixed account type, set at account creation and never changed, merged, or elevated later. |
| `FR-002` | Accepted: service-access roles are independent from account types and must not change account type or grant account-management responsibilities. |
| `FR-004` | Accepted: super-admins can manage the service-access-role catalog and assign or remove roles for members, but must not receive protected-service access through those roles or assign them to admins. |
| `FR-003` | Accepted: active admins automatically receive protected-service access covered by all service-access roles and can assign or remove service-access roles for members. |
| `FR-017` | Accepted: admins can manage member lifecycle and profile data within lifecycle policy, but cannot manage admin or super-admin accounts. |
| `FR-005` | Accepted: active members receive protected-service access only through assigned service-access roles. |
| `FR-025`, `FR-026`, `FR-028` | Accepted: admins cannot recover or reset other accounts, cannot bypass auditability, and cannot consult audit records. |

## Coverage Review

Coverage pass performed on 2026-05-07 against root `README.md`, root `FEATURE-REQUIREMENTS.md`, the former `README.md` `FS-*` table, and the former Phase 2 baseline material ([README feature requirements source](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Former README `FS-*` Coverage

All former `README.md` `FS-*` minimum feature requirements have coverage in the consolidated `FR-*` list. The README responsibility wording has been realigned with user-validated decisions `D-005` through `D-010`, and the `FS-*` table has been retired.

| README requirement | Consolidated coverage | Status |
| --- | --- | --- |
| `FS-001` | `FR-006` | Covered. |
| `FS-002` | `FR-001`, `FR-007`, `FR-008` | Covered. |
| `FS-003` | `FR-009` | Covered. |
| `FS-004` | `FR-011`, `FR-012`, `FR-013`, `FR-014` | Covered. |
| `FS-005` | `FR-013`, `FR-015`, `FR-016`, `FR-020`, `FR-021` | Covered. |
| `FS-006` | `FR-003`, `FR-008`, `FR-017`, `FR-025`, `FR-026`, `FR-027` | Covered. |
| `FS-007` | `FR-002`, `FR-003`, `FR-004`, `FR-022`, `FR-027`, `FR-032` | Covered. |
| `FS-008` | `FR-002`, `FR-003`, `FR-005`, `FR-020`, `FR-022` | Covered. |
| `FS-009` | `FR-023` | Covered. |
| `FS-010` | `FR-024` | Covered. |
| `FS-011` | `FR-020`, `FR-021`, `FR-022` | Covered. |
| `FS-012` | `FR-003`, `FR-004`, `FR-017`, `FR-018`, `FR-019`, `FR-028` | Covered. |
| `FS-013` | `FR-001`, `FR-002`, `FR-004`, `FR-025`, `FR-026`, `FR-028` | Covered for responsibility separation and recovery/reset boundaries; break-glass is explicitly deferred in the out-of-scope section. |
| `FS-014` | `FR-029` | Covered. |
| `FS-015` | `FR-027`, `FR-028`, `FR-035` | Covered for event categories, audit access logging, append-only storage, and indefinite initial retention. |
| `FS-016` | `FR-028` | Covered. |
| `FS-017` | `FR-030` | Covered. |

### Baseline `RB-*` Coverage

Most baseline requirements are either covered by the consolidated list or intentionally superseded by the simplified responsibility model. The baseline is ready for deletion confirmation because the remaining questions below are resolved or explicitly deferred.

| Baseline area | Coverage status | Notes |
| --- | --- | --- |
| Scope and user population, `RB-001` through `RB-003` | Covered by `FR-006`, `FR-007`, `FR-008`, and `FR-030`. | No blocker. |
| Actor separation, `RB-004`, `RB-006` through `RB-008` | Covered by `FR-001` through `FR-005`, `FR-019`, `FR-025`, `FR-026`, and `FR-028`. | Uses the revised user-validated model instead of the older README wording. |
| Lifecycle, `RB-009` through `RB-016` | Covered by `FR-009`, `FR-011` through `FR-016`, and `FR-031`. | No blocker. |
| Administration and role management, `RB-017` through `RB-022` | Covered or superseded by `FR-003`, `FR-004`, `FR-017`, `FR-018`, `FR-022`, `FR-024`, and `FR-032`. | `RB-022` is superseded because role assignment is now allowed for both admins and super-admins over member accounts. |
| Protected-service access, `RB-023` through `RB-026` | Covered by `FR-020`, `FR-021`, and `FR-022`. | No blocker. |
| Auditability, `RB-027` through `RB-032` | Covered by `FR-027`, `FR-028`, and `FR-035`. | Audit retention and append-only policy from `RB-040` are now covered. |
| Security baseline, `RB-033` through `RB-038` | Partially covered by `FR-029`, `FR-020`, `FR-024`, `FR-026`, `FR-033`, and `FR-034`. | Privileged MFA/passwordless is now covered. Custom credential cryptography, OAuth flow constraints, and exact token use remain security/evaluation constraints rather than settled feature requirements unless explicitly promoted later. |
| Operational baseline, `RB-040` through `RB-043` | Covered or intentionally deferred by `FR-030`, `FR-016`, `FR-035`, and the out-of-scope section. | Backup, recovery, restore-test, upgrade, and break-glass details remain study or later-phase topics unless explicitly promoted into final feature requirements. |
| Study constraints, `RB-044` through `RB-047` | Covered by governance/review rules rather than final feature requirements. | These should stay in governance/review material, not the final feature list. |

### Deletion Readiness

The former baseline has been retired. The consolidated list covers the useful `FS-*` and `RB-*` material, unresolved items have either become `FR-*` requirements or explicit scope/evaluation deferrals, and root `README.md` has been realigned with the user-validated responsibility model.

## Open Questions

| ID | Question | Why it matters | Status |
| --- | --- | --- | --- |
| OQ-001 | Should the consolidated list use new `FR-*` identifiers, keeping old `FS-*` and `RB-*` IDs only as traceability references? | A new identifier family would make the final list clearly distinct from both the README minimum specification and the retiring baseline. | Closed by D-004 |
| OQ-002 | Should the current `README.md` responsibility model be treated as authoritative for service-access role assignment, meaning super-admins assign and remove service-access roles for eligible admins and members? | The earlier `README.md` gave this responsibility to super-admins, while older baseline material gave member role assignment/removal to admins. This had to be settled before consolidating lifecycle, role, and audit requirements ([README feature requirements source](../../README.md#minimum-feature-requirements), [Coverage review](#coverage-review)). | Closed by D-005 through D-010 |
| OQ-003 | Does "admin has access to all service-access roles" mean admins automatically have protected-service access to every service-access role, or only that admins can see and assign all service-access roles to members? | This changes the authorization model substantially. Automatic protected-service access for admins is a different requirement from role catalog and assignment authority. | Closed by D-006 |
| OQ-004 | Should root `README.md` be realigned to the consolidated model where admins automatically access all service-access-role-covered services and admins plus super-admins can assign roles to members? | Earlier README wording said admins access services through assigned roles and that service-access role assignments are super-admin-controlled, which conflicted with validated `FR-003` and `FR-004`. | Closed by D-010 |
| OQ-005 | Should the final list explicitly forbid moving an account back to `invited` after it has left `invited`? | `RB-012` carried this rule, while `FR-012` and `FR-013` imply but do not explicitly state it. | Closed by `FR-031` |
| OQ-006 | What exact operations are included in service-access-role catalog management: create, list, update, disable/archive, delete, or some smaller set? | `FR-004` says super-admins manage the catalog, but evaluation and audit coverage need precise verbs. | Closed by `FR-032` |
| OQ-007 | Should the final list add an explicit requirement for strong server-side authorization on all admin and super-admin operations? | `FR-020` covers protected backend services, but administrative operations also need a clear authorization boundary. | Closed by `FR-033` |
| OQ-008 | Should privileged accounts require MFA or phishing-resistant passwordless authentication in the final feature list, or should that remain a Phase 2 security evaluation topic? | `RB-035` asserted this requirement, while `README.md` currently lists privileged-login controls as a debate topic. | Closed by `FR-034` |
| OQ-009 | Should audit records be append-only and retained indefinitely in the final feature list? | `RB-040` asserted this policy, while `README.md` leaves audit retention, privacy, export, and compliance expectations open for Phase 2 debate. | Closed by `FR-035` |
| OQ-010 | Should `FEATURE-REQUIREMENTS.md` include a complete out-of-scope section before baseline deletion? | The target document still has a placeholder out-of-scope section, and baseline deletion would otherwise lose explicit exclusions such as public identity flows, final architecture decisions, implementation files, and break-glass scope. | Closed by D-009 |

## Accepted Requirements

| ID | Requirement | Validation | Target |
| --- | --- | --- | --- |
| FR-001 | Every backoffice account must have exactly one fixed account type: `super-admin`, `admin`, or `member`. The account type is set at account creation and must never be changed, merged, or elevated later. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-002 | Service-access roles must be independent from account types. A service-access role may describe protected backend service access consumed automatically by active `admin` accounts or through assignment to `member` accounts, but must not change an account type or grant account-management responsibilities. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-003 | Active `admin` accounts must automatically be allowed to access every protected backend service covered by any service-access role. Admins must also be able to assign and remove service-access roles for `member` accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-004 | `super-admin` accounts must not receive protected backend service access through service-access roles. Super-admins must be able to manage the service-access-role catalog and assign or remove service-access roles for `member` accounts. Super-admins must not assign service-access roles to `admin` accounts, because active admins receive the covered protected-service access automatically under `FR-003`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-005 | Active `member` accounts must be allowed to access a protected backend service only when at least one assigned service-access role covers that service. Members must not receive protected-service access from their account type alone. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-006 | The system must serve backoffice users only. Public signup, public customer accounts, social login, and consumer identity flows are out of scope. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-007 | Backoffice accounts must be created only through authorized administrative workflows. There must be no public or self-service account registration. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-008 | Super-admins must be able to create `admin` and `member` accounts. Admins must be able to create only `member` accounts. Initial provisioning of the first `super-admin` account is a separate bootstrap concern and must not be treated as a normal backoffice self-service workflow. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-009 | Every backoffice account must have a stable internal identifier that is separate from mutable attributes such as email address, display name, or profile data. Lifecycle state, role assignments, access decisions, and audit records must reference this stable identifier. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-010 | The access-control capability must link each backoffice account to a stable authenticated subject from the identity provider or authentication system. It must consume authentication results, but must not own credentials, MFA, login sessions, or identity-provider account recovery. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-011 | Backoffice accounts must support at least these lifecycle states: `invited`, `active`, `disabled`, and `archived`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-012 | New backoffice accounts must start in `invited` state and become `active` only after the invited user completes the required first authentication or onboarding step. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-013 | Authorized account managers must be able to disable an `active` account, restore a `disabled` account to `active`, and archive a `disabled` account. An `archived` account must not be restored in the initial policy. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-014 | Backoffice account records must be retained rather than hard-deleted in the initial policy, including archived accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-015 | `invited`, `disabled`, and `archived` accounts must not obtain new protected backend service access. Protected-service access requires the account to be `active`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-016 | The system must define, document, and evaluate how already-issued protected-service access stops after account disablement, account archival, or member service-access role removal. The final mechanism and acceptable delay may be decided later during architecture evaluation. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-017 | Admins must be able to list, create, read, update profile data, disable, archive, and restore `member` accounts where lifecycle policy allows. Admins must not manage `admin` or `super-admin` accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-018 | Super-admins must be able to list, create, read, update profile data, disable, archive, and restore `admin` and `member` accounts where lifecycle policy allows. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-019 | Members must be able to view their own profile information in read-only mode. Members must not update their own profile data, assign roles, manage accounts, or consult audit records. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-020 | Protected backend services must enforce authorization server-side. A protected service must grant access only when it can determine that the backoffice account is `active` and allowed by the account type or assigned service-access role rules. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-021 | Protected backend services must deny access when the account is not `active`, has no applicable access rule, or the service cannot safely determine the authorization result. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-022 | Each service-access role must explicitly identify the protected backend service access it covers, so access decisions can be evaluated consistently by the system and protected services. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-023 | The minimal member service-access role must provide consultation-style access only. More granular or stronger permissions may be added later only when a real protected-service need justifies them. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-024 | The system must provide a controlled administration capability for account management, service-access-role catalog management, service-access-role assignment and removal, protected-service access checks, and audit-supporting operations. This requirement does not choose whether the capability is implemented as a UI, API, product feature, or other technical form. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-025 | Recovery and login reset must be own-account responsibilities for `member` and `admin` accounts. Admins must not recover or reset `member`, other `admin`, or `super-admin` accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-026 | The system must prevent privilege escalation paths that change account type, let an account grant itself broader management responsibility, or bypass auditability for privileged actions. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-027 | Audit events must cover account creation, profile update, disablement, archival, restoration, service-access-role creation, service-access-role assignment, service-access-role removal, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or login reset actions. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-028 | Super-admins must be able to consult audit records. Audit reads and exports must themselves create audit events. Admins and members must not consult audit records. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-029 | The target security posture must be production-grade internal access control. Simpler authentication or access-control shortcuts may be used only as non-production or transitional constraints, and their risks and hardening path must be documented during the study. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-030 | The system must remain understandable and operable by the internal team at the expected scale. Added operational or architectural complexity must be justified by concrete security, compliance, maintainability, or product needs. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-031 | Once a backoffice account has left `invited` state, it must not be moved back to `invited`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-032 | Super-admins must be able to create, list, update, disable, and archive service-access roles. Service-access roles must not be hard-deleted in the initial policy. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-033 | All admin and super-admin operations must be authorized server-side according to the acting account type, lifecycle state, and permitted management scope. The system must not rely on frontend-only checks for administrative authorization. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-034 | Production `admin` and `super-admin` authentication must require MFA or phishing-resistant passwordless authentication. The exact authenticator method and fallback policy may be selected later during security and architecture evaluation. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-035 | Audit records must be append-only and retained indefinitely in the initial policy. Any later retention, privacy, or deletion policy change must be explicitly reviewed before adoption. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |

## References

- [README - Core Features](../../README.md#core-features)
- [README - Actors and Role Types](../../README.md#actors-and-role-types)
- [README - Feature Requirements Source](../../README.md#minimum-feature-requirements)
- [README - Initial Scope](../../README.md#initial-scope)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Feature Scope Review](./feature-scope-review.md)
- [Requirements Baseline Review](./baseline-review.md)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [Project Governance - Evidence Standard](../../PROJECT-GOVERNANCE.md#evidence-standard)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [AGENTS - Instruction Priority](../../AGENTS.md#instruction-priority)
