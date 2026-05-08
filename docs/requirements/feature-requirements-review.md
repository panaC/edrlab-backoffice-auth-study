# Feature Requirements Review

Status: Review
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements
Last reviewed: 2026-05-08

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
- [Final Review](#final-review)
- [Account Onboarding Review](#account-onboarding-review)
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
| 1 | Responsibility model | Account type responsibilities and service-access-role ownership affect lifecycle, role assignment, audit, and escalation rules. | Final-reviewed |
| 2 | User population and account creation | Scope and account creation boundaries prevent the list from accidentally growing public or self-service flows. | Final-reviewed |
| 3 | Account lifecycle and retention | Lifecycle states drive access eligibility, audit events, and restoration/archive rules. | Final-reviewed |
| 4 | Stable identity and authentication boundary | The access-control capability needs a stable authenticated subject without taking over identity-provider responsibilities. | Final-reviewed |
| 5 | Service-access roles and protected-service decisions | These requirements define how active accounts receive access to protected backend services. | Final-reviewed |
| 6 | Administration capability | The final list must describe required admin and super-admin operations without choosing the technical form. | Final-reviewed |
| 7 | Auditability | Sensitive and privileged operations require auditable events and controlled audit access. | Final-reviewed |
| 8 | Security and operational constraints | Production-grade posture, revocation behavior, and simplicity must stay visible without becoming product or architecture decisions. | Final-reviewed |
| 9 | Out-of-scope and deletion readiness | Before retiring `baseline.md`, verify that useful coverage has moved into the unique feature list or into explicit open questions. | Baseline retired |
| 10 | Account onboarding | New account creation, invited-state role assignment for members, IdP-managed invitation and authentication, backoffice-driven onboarding activation, immutable subject linking, and safe failure behavior. | Accepted by D-029 |

## Decision Log

| ID | Topic | Decision | Source |
| --- | --- | --- | --- |
| D-001 | Review artifact | Use this document as the live review trail for consolidating feature requirements into root `FEATURE-REQUIREMENTS.md`. | User-provided working objective, 2026-05-07 |
| D-002 | Baseline retirement | Do not delete `docs/requirements/baseline.md` until the consolidated list has been checked for coverage and unresolved points have been preserved as assumptions or open questions. | User-provided working objective, 2026-05-07; [Project governance](../../PROJECT-GOVERNANCE.md#evidence-standard) |
| D-003 | Responsibility model | Treat the current `README.md` responsibility model as authoritative for consolidation: super-admins create, list, assign, and remove service-access roles for eligible `admin` and `member` accounts; admins manage member lifecycle and profile data within scope but do not assign service-access roles, consult audit records, or reset another account; members can view their own profile in read-only mode and access protected backend services only when active and authorized through assigned service-access roles. | User confirmation, 2026-05-07; [README](../../README.md#actors-and-role-types), [README](../../README.md#minimum-feature-requirements) |
| D-004 | Identifier scheme | Use new `FR-*` identifiers for the consolidated feature requirements list. Keep old `FS-*` and `RB-*` identifiers only as source and traceability references while the consolidation is in progress. | User validation of `FR-001`, 2026-05-07 |
| D-005 | Responsibility model revision | Reopen the responsibility model. The user wants a simpler split: super-admins do not use service-access roles for protected-service access and only manage or assign them; admins have broad service-access-role access and can assign service-access roles to members. Exact wording must distinguish protected-service access from role-management access before the final requirement is written. This was later revised for super-admin protected-service access by `D-030`. | User correction, 2026-05-07 |
| D-006 | Admin service-access model | Admin accounts automatically have access to all protected services covered by all service-access roles, and admins can assign those service-access roles to member accounts. This supersedes the earlier current-`README.md` interpretation for admin service-access assignment. | User confirmation, 2026-05-07 |
| D-007 | Super-admin role assignment target | Super-admins may assign or remove service-access roles for `member` accounts, but do not assign service-access roles to `admin` accounts because active admins already receive the covered protected-service access automatically. | User confirmation, 2026-05-07 |
| D-008 | Account creation authority | Super-admins can create `admin` and `member` accounts. Admins can create only `member` accounts. Initial creation of the first `super-admin` is a bootstrap/provisioning concern, not a normal self-service backoffice workflow. | User confirmation, 2026-05-07 |
| D-009 | Out-of-scope consolidation | Replace the placeholder out-of-scope section in root `FEATURE-REQUIREMENTS.md` with explicit exclusions for public identity flows, company-wide IAM replacement, final vendor/architecture/implementation decisions, production high availability as a minimum feature, custom IAM/cryptographic implementation, implementation artifacts outside PoC scope, and break-glass until reopened. | User confirmation, 2026-05-07; [README](../../README.md#initial-scope), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#out-of-scope) |
| D-010 | README responsibility-model realignment | Realign root `README.md` with the consolidated model: active admins automatically access all protected services covered by service-access roles, admins and super-admins assign service-access roles to members only, super-admins do not receive protected-service access through service-access roles, and service-access roles are not assigned to admin accounts. This was later revised for super-admin protected-service access by `D-030`. | User confirmation, 2026-05-07; [README](../../README.md#actors-and-role-types), [README feature requirements source](../../README.md#minimum-feature-requirements), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-011 | Baseline retirement | Delete the former Phase 2 `docs/requirements/baseline.md` file after coverage review, README realignment, out-of-scope consolidation, and explicit user approval. Keep root `FEATURE-REQUIREMENTS.md` as the unique feature requirements list. | User confirmation, 2026-05-07; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md), [Deletion readiness](#deletion-readiness) |
| D-012 | Final-review slice 1 validation | Keep `FR-001` through `FR-005` as written. The user explicitly reconfirmed the broad admin model: active admins automatically receive access to every protected backend service covered by any service-access role, without assigning service-access roles to admin accounts. This was later revised for super-admin protected-service access by `D-030`. | User confirmation, 2026-05-08; [Final review - Slice 1](#slice-1---responsibility-model), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-013 | Identity-provider study boundary | Keep the capability model as access-control and backoffice account management, while making the identity-provider or authentication-system usage part of the study. The access-control capability consumes authentication results and links accounts to a stable authenticated subject; it does not itself implement or own credentials, MFA, login sessions, or IdP account recovery. | User clarification, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-014 | Dedicated identity-provider integration feature | Split the IdP concern out of `FR-010`. Keep `FR-010` focused on linking each backoffice account to a stable authenticated subject, and use dedicated IdP/access-control requirements for concrete runtime behavior instead of one umbrella contract-definition requirement. | User suggestion, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-015 | Authenticated identity is not backoffice authorization | Add `FR-037` to make explicit that a successful IdP authentication result must not automatically create, activate, or authorize a backoffice account. Backoffice access still requires an existing linked account that is active and authorized by the access-control model. | User request, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-016 | IdP requirements decomposition | Replace the umbrella wording of `FR-036` with concrete access-attempt resolution behavior, including fail-closed denial when the authenticated identity cannot be safely resolved to exactly one linked backoffice account. Add `FR-038` to protect against IdP claim, group, or role override of the backoffice authorization model. | User validation, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-017 | Authenticated-subject link management | Add `FR-039` to require that creation, change, or removal of a backoffice account's authenticated-subject link happens only through an authorized administrative workflow and must be audited. | User validation, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-018 | Final-review numbering cleanup | Keep the active consolidated list contiguous at 39 feature requirements after the draft fail-closed identity-resolution requirement was merged into `FR-036`. Renumber the IdP claim-override and authenticated-subject link requirements to `FR-038` and `FR-039`. | Final review, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-019 | Final-review slice 2 validation | Keep `FR-006` through `FR-010` and `FR-036` through `FR-039` as written. The user validated the population, account-creation, stable identity, IdP boundary, exact identity resolution, no implicit IdP authorization, no IdP override, and audited authenticated-subject link rules. | User confirmation, 2026-05-08; [Final review - Slice 2](#slice-2---population-creation-and-authentication-boundary), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-020 | Final-review slice 3 validation | Keep `FR-011` through `FR-016` and `FR-031` as written after final-review strengthening. The user validated the account lifecycle states, invited activation rule, initial archived-account non-restoration policy, account-record retention, active-state access eligibility, already-issued access-stop requirement, and no return to `invited` after onboarding. | User confirmation, 2026-05-08; [Final review - Slice 3](#slice-3---lifecycle-retention-and-access-stop), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-021 | Final-review slice 4 validation | Keep `FR-017` through `FR-019`, `FR-024`, `FR-025`, `FR-032`, and `FR-033` as written after final-review strengthening. The user validated admin management of members only, super-admin management of admins and members, read-only member self-profile access, controlled administration capability without implementation choice, own-account recovery/reset boundaries, super-admin-only service-access-role catalog management, active-role-only assignment and access use, and server-side authorization for privileged operations. | User confirmation, 2026-05-08; [Final review - Slice 4](#slice-4---administration-capability-and-role-catalog), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-022 | Final-review slice 5 validation | Keep `FR-020` through `FR-023` as written. The user validated server-side protected-service authorization, fail-closed denial when authorization cannot be safely determined, explicit service-access-role coverage, and consultation-only initial member service access. | User confirmation, 2026-05-08; [Final review - Slice 5](#slice-5---protected-service-authorization), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-023 | Final-review slice 6 validation | Keep `FR-026` through `FR-030`, `FR-034`, and `FR-035` as written after final-review strengthening. The user validated privilege-escalation prevention, minimum audit event coverage, super-admin-only audit consultation, production-grade internal access-control posture, operability at expected scale, MFA or phishing-resistant passwordless authentication for production admin and super-admin accounts, and append-only indefinite initial audit retention. | User confirmation, 2026-05-08; [Final review - Slice 6](#slice-6---audit-security-and-operability), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-024 | Final-review slice 7 validation | Keep the out-of-scope section as written. The user validated that public identity flows, company-wide IAM replacement, final technical choices, production high availability as a minimum feature, custom cryptographic/IAM implementation, implementation artifacts outside explicit PoC or later phase, and break-glass access remain outside the current feature requirements list. | User confirmation, 2026-05-08; [Final review - Slice 7](#slice-7---out-of-scope-boundaries), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#out-of-scope) |
| D-025 | Initial member onboarding feature | Add initial member-onboarding requirements `FR-040` through `FR-044`: new members start `invited` with `email`, `organization`, and `name`; service-access roles may be assigned while invited but produce no access until activation; the IdP/auth system manages invitation and authentication; automatic onboarding activation may link the stable authenticated subject and activate the account only when the backoffice finds exactly one invited member with no existing authenticated-subject link and a verified matching email; unsafe matches deny access and require administrative intervention. This was later generalized by `D-029`. | User validation, 2026-05-08; [Account Onboarding Review](#account-onboarding-review), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-026 | Authenticated-subject link exception for onboarding | Update `FR-039` to preserve the authorized administrative workflow rule for authenticated-subject link management, while allowing only the validated automatic onboarding activation link creation under `FR-043`. Automatic onboarding must not change or remove an existing authenticated-subject link. This was later tightened by `D-029` so the subject link is created only by automatic onboarding activation and is immutable after creation. | User validation, 2026-05-08; [Account Onboarding Review](#account-onboarding-review), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-027 | Onboarding audit coverage | Update `FR-027` so onboarding activation and failed automatic onboarding activation are covered by minimum audit events, alongside authenticated-subject link and role-assignment events. | User validation, 2026-05-08; [Account Onboarding Review](#account-onboarding-review), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-028 | Onboarding coupling clarification | Clarify that automatic onboarding is not coupled to the user's first IdP login. It is coupled to a backoffice onboarding attempt where the backoffice verifies exactly one account in `invited` state, no existing authenticated-subject link, and a verified IdP email matching the account email. | User validation, 2026-05-08; [Account Onboarding Review](#account-onboarding-review), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-029 | Account onboarding expansion and immutable subject link | Generalize onboarding from `member` accounts to all backoffice account types. `super-admin`, `admin`, and `member` accounts all get their authenticated-subject link through automatic onboarding activation under `FR-043`; no admin, super-admin, or other automated process may manually create, change, remove, or rebind the link outside that flow. The subject link is immutable after creation. Production onboarding activation for `admin` and `super-admin` also requires evidence that `FR-034` was satisfied. | User validation, 2026-05-08; [Account Onboarding Review](#account-onboarding-review), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-030 | Super-admin protected-service access update | Active `super-admin` accounts automatically receive access to every protected backend service covered by any service-access role, like active `admin` accounts. Service-access roles remain assigned only to `member` accounts; they are not assigned to `admin` or `super-admin` accounts because protected-service access for those account types is automatic. | User request, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements), [README](../../README.md#actors-and-role-types) |
| D-031 | Super-admin inheritance simplification | Model `super-admin` as a high-level administration superset of `admin`: a super-admin inherits every admin capability and adds high-level administration capabilities. High-level administration includes admin account management, service-access-role catalog management, and audit consultation. Admin accounts do not inherit super-admin capabilities, account types remain immutable, and service-access roles remain assigned only to member accounts. | User request, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements), [README](../../README.md#actors-and-role-types) |
| D-032 | `FR-037` onboarding-flow clarification | Clarify `FR-037` so an authenticated identity from the identity provider must not, by itself, create, activate, or authorize a backoffice account, while preserving the controlled onboarding activation exception defined in `FR-043`. | User validation, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-033 | `FR-025` recovery and login reset boundary | Clarify `FR-025` so recovery and login reset are own-account responsibilities for `member`, `admin`, and `super-admin` accounts, and so neither admins nor super-admins may recover or reset another account in the initial feature requirements. | User validation, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| D-034 | `FR-027` authenticated-subject link audit wording | Clarify `FR-027` so audit coverage includes authenticated-subject link creation and rejected or attempted link change, removal, or rebinding, without implying that post-creation link mutation is an allowed normal operation. | User validation, 2026-05-08; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Accepted Theme Notes

### Responsibility Model

The consolidated feature requirements no longer follow the previous root `README.md` responsibility model as originally written. The user reopened this topic on 2026-05-07 to simplify the split between `super-admin` and `admin`, and `README.md` was realigned by `D-010`. The user then revised super-admin protected-service access on 2026-05-08 by `D-030` and simplified the hierarchy by `D-031`.

Validated so far: `super-admin`, `admin`, and `member` remain fixed account types, and service-access roles remain independent from account types ([README](../../README.md#actors-and-role-types)).

Current revision: `super-admin` is a high-level administration superset of `admin`. Super-admins inherit every admin capability, including member account management, member service-access-role assignment or removal, and automatic protected-service access. They also add high-level administration capabilities: admin account management, service-access-role catalog management, and audit consultation. Members receive protected-service access only through assigned service-access roles ([D-031](#decision-log), [README](../../README.md#actors-and-role-types)).

Candidate final requirements to draft from this decision:

| Candidate ID | Requirement intent |
| --- | --- |
| `FR-001` | Accepted: every backoffice account has exactly one fixed account type, set at account creation and never changed, merged, or elevated later. |
| `FR-002` | Accepted: service-access roles are independent from account types and must not change account type or grant account-management responsibilities. They may describe access consumed automatically by active admins, inherited by active super-admins, or granted through assignment to members. |
| `FR-004` | Accepted: super-admins are a high-level administration superset of admins, inheriting every admin capability and adding high-level administration capabilities. |
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

## Final Review

Final review started on 2026-05-08 after README realignment, baseline retirement, and consolidation into root `FEATURE-REQUIREMENTS.md` ([README](../../README.md#feature-requirements-source), [Feature requirements specification](../../FEATURE-REQUIREMENTS.md), [Deletion readiness](#deletion-readiness)).

Each final-review pass checks that a requirement is unique, goal-oriented, concrete enough for later evaluation, traceable, and free of hidden product, vendor, architecture, or implementation decisions unless explicitly adopted by the user ([Working rules](#working-rules), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

At the end of the final-review pass, before the later account-onboarding extension, the consolidated list contained 39 unique requirements, `FR-001` through `FR-039`, with no duplicate or missing active identifier after the final-review numbering cleanup.

| Slice | Requirements | Review focus | Status |
| --- | --- | --- | --- |
| 1 | `FR-001` through `FR-005` | Responsibility model, account-type immutability, service-access-role separation, and protected-service access rules. | Accepted by D-012 |
| 2 | `FR-006` through `FR-010`, `FR-036` through `FR-039` | User population, account creation, stable identifiers, authentication boundary, identity resolution, and authenticated-subject link management. | Accepted by D-019 and D-032 |
| 3 | `FR-011` through `FR-016`, `FR-031` | Lifecycle, retention, invited-state rule, access eligibility, and revocation evaluation. | Accepted by D-020 |
| 4 | `FR-017` through `FR-019`, `FR-024`, `FR-025`, `FR-032`, `FR-033` | Administrative capabilities, role-catalog management, recovery/reset boundaries, and server-side admin authorization. | Accepted by D-021 and D-033 |
| 5 | `FR-020` through `FR-023` | Protected-service authorization and service-access-role semantics. | Accepted by D-022 |
| 6 | `FR-026` through `FR-030`, `FR-034`, `FR-035` | Privilege-escalation controls, auditability, security posture, operability, privileged authentication, and audit retention. | Accepted by D-023 and D-034 |
| 7 | Out-of-scope section | Scope boundaries and deferred study topics. | Accepted by D-024 |

### Slice 1 - Responsibility Model

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-001` | Unique and foundational. It fixes the immutable account-type model used by every later access and administration rule. | Keep as written. |
| `FR-002` | Unique and necessary. It separates service-access roles from account types and management responsibilities. It was later updated by `D-030` and `D-031` so active admins consume covered service access automatically and active super-admins receive the same access by inheritance. | Keep as updated. |
| `FR-003` | Concrete and user-validated. It intentionally gives active admins automatic protected-service access for all services covered by service-access roles, while preserving admin member-role assignment/removal authority. | Keep as clarified by `D-031`. |
| `FR-004` | Concrete and user-validated. It simplifies the model by treating super-admins as a high-level administration superset of admins: inherited admin capabilities plus high-level administration capabilities, without assigning service-access roles to privileged account types. | Keep as updated by `D-031`. |
| `FR-005` | Unique and testable. It defines the member access rule and prevents member access from account type alone. | Keep as written. |

Final decision: keep `FR-001` through `FR-005`, as later updated by `D-030` and `D-031`. `FR-003` defines the admin protected-service access and member role-assignment behavior. `FR-004` now simplifies the responsibility model by defining `super-admin` as a high-level administration superset of `admin`: super-admins inherit admin capabilities, including protected-service access, and add high-level administration capabilities.

### Slice 2 - Population, Creation, and Authentication Boundary

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-006` | Unique and scope-protecting. It keeps the capability limited to backoffice users and prevents accidental expansion into public or consumer identity. | Keep as written. |
| `FR-007` | Unique and testable. It forbids public or self-service registration and ties account creation to authorized administrative workflows. | Keep as written. |
| `FR-008` | Concrete. It captures super-admin/admin creation boundaries and keeps first-super-admin bootstrap outside normal self-service workflows. | Keep as written. |
| `FR-009` | Concrete and important for auditability. It requires stable internal account identifiers separate from mutable profile data. | Keep as written. |
| `FR-010` | Concrete after clarification. It now focuses on linking each backoffice account to a stable authenticated subject and avoiding access decisions based only on mutable profile attributes. | Keep revised wording. |
| `FR-036` | Concrete runtime rule. It requires every authenticated access attempt to resolve to exactly one linked backoffice account before authorization is evaluated, and to deny access if safe resolution is not possible. | Keep merged wording. |
| `FR-037` | Dedicated safety rule. It prevents IdP authentication by itself from becoming implicit backoffice provisioning, activation, or authorization, while preserving the controlled onboarding activation flow in `FR-043`. | Keep as clarified by `D-032`. |
| `FR-038` | Concrete authorization-boundary rule. It prevents IdP claims, groups, or roles from overriding the backoffice account type, lifecycle, service-access role, or audit model. | Keep with final numbering. |
| `FR-039` | Concrete link-management rule. It protects the sensitive link between an authenticated subject and a backoffice account by requiring an authorized administrative workflow and audit trail for creation, change, or removal. | Keep with final numbering. |

The IdP-related requirements now cover stable subject linkage, exact account resolution, fail-closed unresolved identity behavior, no automatic provisioning or authorization from IdP authentication alone, no IdP claim/group/role override, and immutable subject-account link creation through controlled onboarding activation. This appears complete at feature-requirements level; product choice, token/session strategy, browser storage, and exact IdP architecture remain later evaluation topics.

### Slice 3 - Lifecycle, Retention, and Access Stop

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-011` | Unique and foundational for account lifecycle. It defines the minimum lifecycle states used by access and management rules. | Keep as written. |
| `FR-012` | Concrete account-creation follow-through rule. It prevents invited accounts from becoming active before the required onboarding activation step. | Keep aligned with `FR-043` for automatic account onboarding. |
| `FR-013` | Concrete lifecycle-transition rule. It captures disable, restore, archive, and initial no-restore-from-archive policy without choosing implementation mechanics. | Keep as written. |
| `FR-014` | Unique retention rule for account records. It preserves audit and history by avoiding hard deletion in the initial policy. | Keep as written. |
| `FR-015` | Concrete access-eligibility rule. It prevents non-active accounts from obtaining new protected-service access. | Keep as written. |
| `FR-016` | Necessary but needed a stronger feature-oriented wording. The previous wording focused on defining and evaluating access-stop behavior and did not mention service-access role disablement or archival. | Strengthen wording to require the ability to stop already-issued access after account disablement, account archival, member role removal, or service-access role disablement or archival. |
| `FR-031` | Unique lifecycle invariant. It prevents reusing the invited state after an account has moved beyond onboarding. | Keep as written. |

Final decision: keep the lifecycle set and retention policy. Strengthen `FR-016` so role disablement and archival cannot leave stale protected-service access outside the access-stop review.

### Slice 4 - Administration Capability and Role Catalog

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-017` | Concrete admin scope rule. It gives admins member-management capability and explicitly excludes admin or super-admin account management. | Keep as written. |
| `FR-018` | Concrete super-admin account-management rule. It covers admin and member lifecycle/profile management where policy allows. | Keep as written. |
| `FR-019` | Concrete member self-access rule. It limits members to read-only self-profile access and excludes self-management, role assignment, account management, and audit access. | Keep as written. |
| `FR-024` | Broad but useful administration-capability requirement. It names the controlled operations without choosing UI, API, product, or implementation form. | Keep as written. |
| `FR-025` | Unique recovery/reset boundary. It keeps recovery and login reset as own-account responsibilities for `member`, `admin`, and `super-admin` accounts, and prevents admins or super-admins from recovering or resetting another account. | Keep as clarified by `D-033`. |
| `FR-032` | Needed one access-effect clarification. It covered role catalog lifecycle but did not explicitly say that disabled or archived service-access roles stop being usable for assignment and protected-service authorization. | Strengthen wording so only active service-access roles may be assigned to members or used in protected-service access decisions. |
| `FR-033` | Concrete server-side authorization rule for administrative actions. It prevents frontend-only enforcement of privileged operations. | Keep as written. |

Final decision: keep the administration split. Strengthen `FR-032` so service-access role lifecycle has a clear authorization effect.

### Slice 5 - Protected-Service Authorization

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-020` | Concrete allow-side authorization rule. It requires protected services to enforce server-side authorization using active state and the account-type or assigned-role access model. | Keep as written. |
| `FR-021` | Concrete deny-side rule. It complements `FR-020` by requiring denial when active state, applicable access, or safe authorization determination is missing. | Keep as written. |
| `FR-022` | Unique service-access-role definition rule. It makes protected-service coverage explicit enough for consistent decisions. | Keep as written. |
| `FR-023` | Intentionally minimal member-access rule. It keeps the first member role consultation-style and defers stronger permissions until a real protected-service need exists. | Keep as written, but confirm concrete protected-service examples during service inventory. |

Final decision: keep `FR-020` through `FR-023`. The only residual precision work is later service inventory detail for what each consultation-style member role covers.

### Slice 6 - Audit, Security, and Operability

| Requirement | Final-review finding | Proposed action |
| --- | --- | --- |
| `FR-026` | Unique escalation-prevention requirement. It captures the major forbidden paths: account-type change, self-granted broader responsibility, and unaudited privileged actions. | Keep as written. |
| `FR-027` | Necessary audit coverage rule. It now explicitly includes service-access-role update, disablement, archival, authenticated-subject link creation, and rejected or attempted authenticated-subject link mutation so the audit list stays aligned with immutable subject-link policy. | Keep as clarified by `D-034`. |
| `FR-028` | Concrete audit-access rule. It limits audit consultation to super-admins and requires audit reads/exports to be audited. | Keep as written. |
| `FR-029` | Useful security-posture requirement. It allows transitional shortcuts only when explicitly documented with risk and hardening path, without choosing a final architecture. | Keep as written. |
| `FR-030` | Useful operability constraint. It keeps complexity justified by concrete security, compliance, maintainability, or product needs. | Keep as written. |
| `FR-034` | Concrete privileged-authentication requirement. It requires MFA or phishing-resistant passwordless authentication for production admin and super-admin authentication while leaving exact method and fallback policy for evaluation. | Keep as written. |
| `FR-035` | Concrete initial audit-retention rule. It makes audit records append-only and retained indefinitely until an explicit later review changes that policy. | Keep as written. |

Final decision: keep the security and operability set. Strengthen `FR-027` so every sensitive capability introduced by the final list has audit coverage, including rejected or attempted authenticated-subject link mutation.

### Slice 7 - Out-of-Scope Boundaries

The out-of-scope section remains aligned with the README and Phase 2 governance: it excludes public identity flows, company-wide IAM replacement, final vendor or architecture choices, production high availability as a minimum feature, complete custom cryptographic/IAM implementation, implementation artifacts outside an explicit PoC or later phase, and break-glass until reopened ([README](../../README.md#initial-scope), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

Final decision: keep the out-of-scope section as written. It is useful because it prevents the consolidated feature list from silently expanding into architecture, vendor, production deployment, or emergency-access policy decisions.

## Account Onboarding Review

Account onboarding was reviewed on 2026-05-08 after the seven final-review slices were accepted. The user explicitly asked to validate every new feature before writing. The review started with `member` onboarding, then the user validated generalizing the same automatic onboarding activation model to `super-admin`, `admin`, and `member` accounts.

The active consolidated list now contains 44 unique requirements, `FR-001` through `FR-044`, after adding the validated account-onboarding requirements.

| Requirement | Review finding | Decision |
| --- | --- | --- |
| `FR-040` | New account creation needs concrete minimum input data and must remain aligned with the lifecycle model. | Update requirement: an authorized account manager creates a new backoffice account in `invited` state with `email`, `organization`, and `name`. |
| `FR-041` | Assigning service-access roles at invitation time is useful for operational preparation, but must not bypass the active-state access rule. | Add requirement: roles may be assigned while invited, but they produce no protected-service access until the member is active. |
| `FR-042` | The user clarified that the auth/IdP manages invitation and authentication. | Add requirement: IdP/auth owns invitation delivery and authentication; the access-control capability does not own IdP invitation delivery, credentials, MFA, sessions, or IdP recovery. |
| `FR-043` | The user selected automatic creation of the initial authenticated-subject link during backoffice onboarding activation. This must be coupled to backoffice account state rather than to the user's first IdP login. | Update requirement: automatic onboarding activation may link and activate only when the backoffice finds exactly one invited account with no existing authenticated-subject link and a verified email matching the authenticated identity; production `admin` and `super-admin` activation also requires evidence that `FR-034` was satisfied. |
| `FR-044` | Unsafe matching must fail closed instead of creating a wrong account link or implicit authorization. | Update requirement: do not link, activate, or authorize; keep `invited`, deny access, and require administrative intervention when the safe-match or privileged-authentication conditions are not met. |
| `FR-039` | The user rejected manual subject-link creation, even through an admin workflow. The link should be created only by automatic onboarding activation and be immutable afterward. | Update wording: subject-link creation happens only under `FR-043`; no admin, super-admin, or automated process outside that flow may create, change, remove, or rebind an existing link. |
| `FR-027` | Onboarding activation and failed automatic activation are security-relevant events and must be auditable. | Update minimum audit coverage to include account activation and failed automatic onboarding activation. |

Final decision: keep the onboarding feature as `FR-040` through `FR-044`, generalize it to all account types, update `FR-039` so the authenticated-subject link is created only by automatic onboarding activation and is immutable afterward, and keep `FR-027` audit coverage for onboarding activation and failed automatic onboarding activation. This preserves the validated rule that IdP authentication alone never grants access: activation happens only after the backoffice verifies exactly one invited account with no existing authenticated-subject link and a verified matching email; production `admin` and `super-admin` activation also requires privileged-authentication evidence; authorization still requires an active account plus the existing access-control model.

## Accepted Requirements

| ID | Requirement | Validation | Target |
| --- | --- | --- | --- |
| FR-001 | Every backoffice account must have exactly one fixed account type: `super-admin`, `admin`, or `member`. The account type is set at account creation and must never be changed, merged, or elevated later. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-002 | Service-access roles must be independent from account types. A service-access role may describe protected backend service access consumed automatically by active `admin` accounts, inherited by active `super-admin` accounts under `FR-004`, or granted through assignment to `member` accounts, but must not change an account type or grant account-management responsibilities. | User validation, 2026-05-07; super-admin access update, 2026-05-08; super-admin inheritance simplification, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-003 | Active `admin` accounts must automatically be allowed to access every protected backend service covered by any service-access role. Admins must also be able to assign and remove service-access roles for `member` accounts. | User validation, 2026-05-07; super-admin inheritance simplification, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-004 | `super-admin` accounts must be treated as a high-level administration superset of `admin` accounts. A super-admin must inherit every admin capability, including protected-service access and member service-access-role assignment or removal under `FR-003`, and member account management under `FR-017`. Super-admins must also provide high-level administration capabilities, including admin account management under `FR-018`, audit consultation under `FR-028`, and service-access-role catalog management under `FR-032`. This inherited access must not require assigning service-access roles to `super-admin` or `admin` accounts. | User validation, 2026-05-07; super-admin access update, 2026-05-08; super-admin inheritance simplification, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-005 | Active `member` accounts must be allowed to access a protected backend service only when at least one assigned service-access role covers that service. Members must not receive protected-service access from their account type alone. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-006 | The system must serve backoffice users only. Public signup, public customer accounts, social login, and consumer identity flows are out of scope. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-007 | Backoffice accounts must be created only through authorized administrative workflows. There must be no public or self-service account registration. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-008 | Super-admins must be able to create `admin` and `member` accounts. Admins must be able to create only `member` accounts. Initial provisioning of the first `super-admin` account is a separate bootstrap concern and must not be treated as a normal backoffice self-service workflow. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-009 | Every backoffice account must have a stable internal identifier that is separate from mutable attributes such as email address, display name, or profile data. Lifecycle state, role assignments, access decisions, and audit records must reference this stable identifier. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-010 | The access-control capability must link each backoffice account to a stable authenticated subject from the identity provider or authentication system. Access decisions must rely on this stable subject linkage rather than on mutable profile attributes alone. | User validation, 2026-05-07 and clarification, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-011 | Backoffice accounts must support at least these lifecycle states: `invited`, `active`, `disabled`, and `archived`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-012 | New backoffice accounts must start in `invited` state and become `active` only after the invited user completes the required onboarding activation step. For automatic account onboarding, the activation step is governed by `FR-043`. | User validation, 2026-05-07; account onboarding clarification, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-013 | Authorized account managers must be able to disable an `active` account, restore a `disabled` account to `active`, and archive a `disabled` account. An `archived` account must not be restored in the initial policy. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-014 | Backoffice account records must be retained rather than hard-deleted in the initial policy, including archived accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-015 | `invited`, `disabled`, and `archived` accounts must not obtain new protected backend service access. Protected-service access requires the account to be `active`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-016 | The system must be able to stop already-issued protected-service access after account disablement, account archival, member service-access role removal, or service-access role disablement or archival. The final mechanism and acceptable delay may be decided later during architecture evaluation. | User validation, 2026-05-07; final review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-017 | Admins must be able to list, create, read, update profile data, disable, archive, and restore `member` accounts where lifecycle policy allows. Admins must not manage `admin` or `super-admin` accounts. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-018 | Super-admins must be able to list, create, read, update profile data, disable, archive, and restore `admin` and `member` accounts where lifecycle policy allows. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-019 | Members must be able to view their own profile information in read-only mode. Members must not update their own profile data, assign roles, manage accounts, or consult audit records. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-020 | Protected backend services must enforce authorization server-side. A protected service must grant access only when it can determine that the backoffice account is `active` and allowed by the account type or assigned service-access role rules. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-021 | Protected backend services must deny access when the account is not `active`, has no applicable access rule, or the service cannot safely determine the authorization result. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-022 | Each service-access role must explicitly identify the protected backend service access it covers, so access decisions can be evaluated consistently by the system and protected services. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-023 | The minimal member service-access role must provide consultation-style access only. More granular or stronger permissions may be added later only when a real protected-service need justifies them. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-024 | The system must provide a controlled administration capability for account management, service-access-role catalog management, service-access-role assignment and removal, protected-service access checks, and audit-supporting operations. This requirement does not choose whether the capability is implemented as a UI, API, product feature, or other technical form. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-025 | Recovery and login reset must be own-account responsibilities for `member`, `admin`, and `super-admin` accounts. Admins and super-admins must not recover or reset another account. | User validation, 2026-05-07; manual review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-026 | The system must prevent privilege escalation paths that change account type, let an account grant itself broader management responsibility, or bypass auditability for privileged actions. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-027 | Audit events must cover account creation, profile update, activation, disablement, archival, restoration, authenticated-subject link creation, rejected or attempted authenticated-subject link change, removal, or rebinding, failed automatic onboarding activation, service-access-role creation, update, disablement, archival, assignment, removal, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or login reset actions. | User validation, 2026-05-07; final review, 2026-05-08; account onboarding review, 2026-05-08; manual review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-028 | Super-admins must be able to consult audit records. Audit reads and exports must themselves create audit events. Admins and members must not consult audit records. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-029 | The target security posture must be production-grade internal access control. Simpler authentication or access-control shortcuts may be used only as non-production or transitional constraints, and their risks and hardening path must be documented during the study. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-030 | The system must remain understandable and operable by the internal team at the expected scale. Added operational or architectural complexity must be justified by concrete security, compliance, maintainability, or product needs. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-031 | Once a backoffice account has left `invited` state, it must not be moved back to `invited`. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-032 | Super-admins must be able to create, list, update, disable, and archive service-access roles. Service-access roles must not be hard-deleted in the initial policy. Only active service-access roles may be assigned to members or used in protected-service access decisions. | User validation, 2026-05-07; final review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-033 | All admin and super-admin operations must be authorized server-side according to the acting account type, lifecycle state, and permitted management scope. The system must not rely on frontend-only checks for administrative authorization. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-034 | Production `admin` and `super-admin` authentication must require MFA or phishing-resistant passwordless authentication. The exact authenticator method and fallback policy may be selected later during security and architecture evaluation. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-035 | Audit records must be append-only and retained indefinitely in the initial policy. Any later retention, privacy, or deletion policy change must be explicitly reviewed before adoption. | User validation, 2026-05-07 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-036 | For each authenticated access attempt, the system must resolve the authenticated identity to exactly one linked backoffice account before evaluating backoffice authorization. If it cannot do so safely, it must deny backoffice access. | User validation, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-037 | An authenticated identity from the identity provider must not, by itself, create, activate, or authorize a backoffice account. Backoffice access requires an existing linked backoffice account that is active and authorized by the access-control model, except for the controlled onboarding activation flow defined in `FR-043`. | User request, 2026-05-08; manual review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-038 | Identity-provider claims, groups, or roles must not override backoffice account type, lifecycle state, service-access role assignments, or audit requirements. | User validation, 2026-05-08; final-review numbering cleanup, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-039 | The authenticated-subject link of a backoffice account must be created only through automatic onboarding activation under `FR-043`. The link must be immutable after creation. The system must not let an `admin`, `super-admin`, or any automated process outside `FR-043` create, change, remove, or rebind an existing authenticated-subject link. If a subject link is incorrect or no longer usable, the affected account must be disabled or archived and a new backoffice account must be created where lifecycle policy allows. Subject-link creation and rejected or attempted subject-link changes must be audited. | User validation, 2026-05-08; final-review numbering cleanup, 2026-05-08; account onboarding review, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-040 | When an authorized account manager creates a new backoffice account, the account must be created in `invited` state with at least these profile fields: `email`, `organization`, and `name`. | User validation, 2026-05-08; account onboarding expansion, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-041 | Authorized account managers may assign service-access roles to a `member` account while it is still in `invited` state, but those assignments must not grant protected backend service access until the member account is `active`. | User validation, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-042 | The identity provider or authentication system must manage invitation delivery and authentication for invited backoffice accounts. The access-control capability must not own IdP invitation delivery, credentials, MFA, login sessions, or IdP account recovery for account onboarding. | User validation, 2026-05-08; account onboarding expansion, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-043 | When an authenticated identity attempts backoffice onboarding, the system may automatically link the stable authenticated subject to a backoffice account and activate that account only when the backoffice finds exactly one account in `invited` state, with no existing authenticated-subject link, whose account email matches a verified email address from the authenticated identity. In production, onboarding activation for `admin` and `super-admin` accounts also requires evidence that the privileged-authentication requirement in `FR-034` has been satisfied. | User validation, 2026-05-08; account onboarding expansion, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |
| FR-044 | If automatic onboarding activation cannot safely match the authenticated identity to exactly one invited backoffice account with no existing authenticated-subject link and a verified matching email address, or cannot verify the privileged-authentication requirement for an invited `admin` or `super-admin` account in production, the system must not create the authenticated-subject link, must not activate or authorize the account, must keep the account in `invited` state, must deny backoffice access, and must require administrative intervention. | User validation, 2026-05-08; account onboarding expansion, 2026-05-08 | Added to [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements). |

## References

- [README - Core Features](../../README.md#core-features)
- [README - Actors and Role Types](../../README.md#actors-and-role-types)
- [README - Feature Requirements Source](../../README.md#minimum-feature-requirements)
- [README - Initial Scope](../../README.md#initial-scope)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Feature Scope Review](./feature-scope-review.md)
- [Requirements Baseline Review](./baseline-review.md)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Project Governance - Evidence Standard](../../PROJECT-GOVERNANCE.md#evidence-standard)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [AGENTS - Instruction Priority](../../AGENTS.md#instruction-priority)
