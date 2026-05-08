# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-05-08

### Added

- Started the final review pass for the consolidated `FR-*` feature requirements and recorded the review slices in `docs/requirements/feature-requirements-review.md`.
- Added `FR-036` for resolving an authenticated identity to exactly one linked backoffice account before evaluating backoffice authorization.
- Added `FR-037` to state that a successful identity-provider authentication result must not automatically create, activate, or authorize a backoffice account.
- Added `FR-038` for prevention of identity-provider claims, groups, or roles overriding the backoffice authorization model.
- Added `FR-039` to require authorized and audited management of the authenticated-subject link on backoffice accounts.
- Added `FR-040` through `FR-044` for the validated account-onboarding feature: invited account creation with `email`, `organization`, and `name`; pre-activation member service-access-role assignment without access; IdP-managed invitation and authentication; safe automatic onboarding activation with initial subject linking; and fail-closed handling when matching is unsafe.
- Added threat-model review focus, requirement refinement candidates, and expanded threat scenarios for onboarding, identity-provider claim override, privileged authentication, token/session replay, audit integrity, unsafe failure modes, and operational artifacts.

### Changed

- Promoted `docs/risks/threat-model.md` from draft to review state and realigned it with the consolidated `FR-*` feature requirements.
- Reworked `docs/architecture/options.md` into a Phase 2 review-state architecture option framing derived from the consolidated feature requirements and threat model, with option comparison, threat-fit review, PoC/evaluation implications, and open architecture questions.
- Updated the responsibility model so active `super-admin` accounts automatically receive access to every protected backend service covered by service-access roles, like active `admin` accounts, while service-access role assignments remain limited to `member` accounts.
- Simplified the responsibility model so `super-admin` is a high-level administration superset of `admin`, inheriting admin capabilities and adding high-level administration capabilities.
- Clarified `FR-003` and `FR-004` so `FR-003` describes admin capabilities and `FR-004` gives super-admins those capabilities by inheritance plus high-level administration capabilities.
- Split the identity-provider clarification out of `FR-010`, keeping `FR-010` focused on stable authenticated-subject linkage.
- Reworked `FR-036` from an identity-provider contract placeholder into concrete authenticated-identity resolution behavior.
- Merged the fail-closed identity-resolution behavior from an earlier draft into `FR-036` to avoid duplicate IdP requirements.
- Completed the final review pass for the consolidated feature list, which at that point contained 39 active requirements from `FR-001` through `FR-039`.
- Strengthened `FR-016`, `FR-027`, and `FR-032` so service-access role disablement or archival has a clear access-stop effect, audit coverage includes role lifecycle and authenticated-subject link changes, and only active service-access roles can be used for assignments or protected-service access decisions.
- Recorded user validation of the seven final-review slices covering all consolidated feature requirements and out-of-scope boundaries.
- Updated `FR-039` so authenticated-subject links are created only through automatic onboarding activation, are immutable after creation, and cannot be manually created, changed, removed, or rebound by admins, super-admins, or other processes outside the onboarding activation flow.
- Extended `FR-027` audit coverage to include account activation and failed automatic onboarding activation.
- Clarified `FR-012`, `FR-039`, `FR-043`, and `FR-044` so automatic account onboarding is coupled to backoffice verification of one invited account with no existing authenticated-subject link and a verified matching IdP email, not to the user's first IdP login.
- Generalized onboarding from `member` accounts to all account types, with production `admin` and `super-admin` activation requiring evidence that the privileged-authentication requirement was satisfied.
- Clarified `FR-037` so identity-provider authentication alone does not create, activate, or authorize a backoffice account, while preserving the controlled onboarding activation flow in `FR-043`.
- Clarified `FR-025` so recovery and login reset are own-account responsibilities for members, admins, and super-admins, with no cross-account reset capability in the initial feature requirements.
- Clarified `FR-027` so authenticated-subject link audit coverage records link creation and rejected or attempted link mutation, without implying that post-creation link changes are normal allowed operations.

## 2026-05-07

### Added

- Added the top-level `README.md` core features list as the project reference for account management, identity-provider authentication, account-type separation, service-access roles, protected-service access control, and sensitive-action auditability.
- Added `docs/requirements/feature-requirements-review.md` as the live consolidation trail for replacing the separate requirements baseline with one unique root `FEATURE-REQUIREMENTS.md` list.
- Added `docs/requirements/feature-scope-review.md` to record step-by-step validation of each immutable `FS-*` requirement, starting with the validated `FS-001` scope.
- Added `docs/requirements/baseline-review.md` to record step-by-step validation of each `RB-*` requirement against the validated `FS-*` interpretations.
- Added root `FEATURE-REQUIREMENTS.md` as the blank-slate iterative working base for the final-solution feature requirements of the access-control capability.
- Added the validated `Goal` section to root `FEATURE-REQUIREMENTS.md`.
- Added `FR-001` to root `FEATURE-REQUIREMENTS.md` for fixed immutable account types.
- Added `FR-002` to root `FEATURE-REQUIREMENTS.md` for service-access role independence from account types.
- Added `FR-003` to root `FEATURE-REQUIREMENTS.md` for automatic admin access to all service-access-role-covered protected services and admin assignment/removal of member service-access roles.
- Added `FR-004` to root `FEATURE-REQUIREMENTS.md` for super-admin service-access-role catalog management and member role assignment without super-admin protected-service access or admin role assignment.
- Added `FR-005` to root `FEATURE-REQUIREMENTS.md` for member protected-service access only through assigned service-access roles.
- Added `FR-006` to root `FEATURE-REQUIREMENTS.md` for backoffice-only user scope and explicit exclusion of public or consumer identity flows.
- Added `FR-007` to root `FEATURE-REQUIREMENTS.md` for administrative-only backoffice account creation with no public or self-service registration.
- Added `FR-008` to root `FEATURE-REQUIREMENTS.md` for account creation authority by account type and first-super-admin bootstrap separation.
- Added `FR-009` to root `FEATURE-REQUIREMENTS.md` for stable internal account identifiers separate from mutable profile attributes.
- Added `FR-010` to root `FEATURE-REQUIREMENTS.md` for linking backoffice accounts to stable authenticated subjects while keeping credentials, MFA, sessions, and IdP recovery outside the access-control capability.
- Added `FR-011` to root `FEATURE-REQUIREMENTS.md` for required backoffice account lifecycle states.
- Added `FR-012` to root `FEATURE-REQUIREMENTS.md` for invited account activation after first authentication or onboarding completion.
- Added `FR-013` to root `FEATURE-REQUIREMENTS.md` for disable, restore, and archive lifecycle transitions.
- Added `FR-014` to root `FEATURE-REQUIREMENTS.md` for retaining backoffice account records instead of hard-deleting them in the initial policy.
- Added `FR-015` to root `FEATURE-REQUIREMENTS.md` for requiring active lifecycle state before protected-service access.
- Added `FR-016` to root `FEATURE-REQUIREMENTS.md` for documenting and evaluating already-issued access stop behavior after lifecycle or role changes.
- Added `FR-017` to root `FEATURE-REQUIREMENTS.md` for admin management of member accounts and exclusion of admin or super-admin account management.
- Added `FR-018` to root `FEATURE-REQUIREMENTS.md` for super-admin management of admin and member accounts.
- Added `FR-019` to root `FEATURE-REQUIREMENTS.md` for member read-only self-profile access and member self-service exclusions.
- Added `FR-020` to root `FEATURE-REQUIREMENTS.md` for server-side protected-service authorization based on active state and account type or assigned service-access role rules.
- Added `FR-021` to root `FEATURE-REQUIREMENTS.md` for fail-closed protected-service access decisions.
- Added `FR-022` to root `FEATURE-REQUIREMENTS.md` for explicit service-access-role coverage of protected backend service access.
- Added `FR-023` to root `FEATURE-REQUIREMENTS.md` for consultation-style minimal member service-access and justified future permission refinement.
- Added `FR-024` to root `FEATURE-REQUIREMENTS.md` for a controlled administration capability without choosing its technical form.
- Added `FR-025` to root `FEATURE-REQUIREMENTS.md` for own-account recovery and login reset boundaries.
- Added `FR-026` to root `FEATURE-REQUIREMENTS.md` for preventing privilege escalation and audit bypass paths.
- Added `FR-027` to root `FEATURE-REQUIREMENTS.md` for minimum audit event coverage.
- Added `FR-028` to root `FEATURE-REQUIREMENTS.md` for super-admin audit consultation and audit logging of reads or exports.
- Added `FR-029` to root `FEATURE-REQUIREMENTS.md` for the target production-grade internal access-control posture and documented hardening path for shortcuts.
- Added `FR-030` to root `FEATURE-REQUIREMENTS.md` for internal-team understandability, operability, and justified complexity.
- Added a coverage review to `docs/requirements/feature-requirements-review.md` mapping `README.md` `FS-*` and baseline `RB-*` material to the consolidated `FR-*` list and recording deletion blockers for the old baseline.
- Added `FR-031` to root `FEATURE-REQUIREMENTS.md` to forbid returning an account to `invited` after it has left that state.
- Added `FR-032` to root `FEATURE-REQUIREMENTS.md` for service-access-role catalog creation, listing, update, disablement, archival, and no hard deletion in the initial policy.
- Added `FR-033` to root `FEATURE-REQUIREMENTS.md` for server-side authorization of admin and super-admin operations.
- Added `FR-034` to root `FEATURE-REQUIREMENTS.md` for production MFA or phishing-resistant passwordless authentication on admin and super-admin accounts, with exact authenticator choices deferred to security and architecture evaluation.
- Added `FR-035` to root `FEATURE-REQUIREMENTS.md` for append-only, indefinitely retained audit records in the initial policy.
- Added the root `FEATURE-REQUIREMENTS.md` out-of-scope section for public identity exclusions, non-decisions, implementation boundaries, and break-glass deferral.
- Recorded the out-of-scope consolidation decision in `docs/requirements/feature-requirements-review.md` and closed `OQ-010`.

### Removed

- Removed `docs/requirements/baseline.md` after consolidating useful `FS-*` and `RB-*` coverage into root `FEATURE-REQUIREMENTS.md` and preserving the review trail in `docs/requirements/feature-requirements-review.md`.

### Changed

- Removed the temporary stabilized `FR-*` feature-requirement table from `README.md`.
- Rewrote the `README.md` project goal for clearer scope, access-control purpose, and protected-service wording.
- Updated backoffice-user wording across project documents to remove the extra qualifier.
- Replaced the temporary `README.md` project-purpose note with a concise description aligned with the study roadmap.
- Added a compact Mermaid flow under the `README.md` core features list to show user and admin entry paths through authentication, identity provider, access control, protected services, and account management.
- Removed the dedicated Phase 2 threat-modeling baseline requirement and kept threat modeling documented as a risk artifact.
- Expanded the Phase 2 threat model with explicit external dependencies, entry points, and exit points to improve OWASP threat-modeling alignment.
- Validated the Phase 2 interpretation of `FS-002`: member creation or invitation must be admin-initiated before activation, with no public or self-service member creation.
- Validated the Phase 2 interpretation of `FS-003`: stable member identifiers are the canonical reference for lifecycle, roles, audit, and access decisions.
- Validated the Phase 2 interpretation of `FS-004`: lifecycle states and member retention are baseline constraints, with `archived` terminal in the baseline.
- Validated the Phase 2 interpretation of `FS-005`: non-active members cannot obtain new access, and already-issued access removal remains an explicit revocation-evaluation topic.
- Added the related baseline requirement list to the `FS-005` scope-review note.
- Updated `FS-006` in `README.md` to clarify that administrators remove role-based service access for members rather than generic already-issued access.
- Aligned the Phase 2 requirements baseline and threat-model wording with the clarified `FS-006` scope.
- Validated the Phase 2 interpretation of `FS-006`: administrators manage member operations and role-based service-access removal within lifecycle policy and audit requirements.
- Updated `FS-007` in `README.md` to separate admin role listing, assignment, and removal from super-admin role creation.
- Aligned the threat-model role-management entry point with the clarified `FS-007` responsibility split.
- Corrected the requirements traceability matrix so `FS-007` includes `RB-016` for already-issued access behavior after role-access removal.
- Validated the Phase 2 interpretation of `FS-007`: super-admins create roles, while admins list, assign, and remove roles from members.
- Validated the Phase 2 interpretation of `FS-008`: baseline authorization is simple role-based service access, with finer permissions deferred until justified by real service needs.
- Validated the Phase 2 interpretation of `FS-009`: the minimal member role is consultation/read-only, with stronger or finer permissions deferred until a real service need is reviewed.
- Validated the Phase 2 interpretation of `FS-010`: the system needs a controlled, auditable administration capability without selecting its technical form.
- Validated the Phase 2 interpretation of `FS-011`: protected backend services must authorize server-side from active member state and role-based service access, failing closed when uncertain.
- Validated the Phase 2 interpretation of `FS-012`: member self-service is limited to viewing one's own profile, while profile and service-access changes remain admin-controlled.
- Updated `FS-013` and the actor responsibilities in `README.md` to separate member recovery/login reset, administrator recovery/login reset, and super-admin audit/break-glass responsibility.
- Aligned the Phase 2 requirements baseline and threat model with the clarified `FS-013` responsibility split.
- Clarified `FS-013` further so member and administrator recovery/login reset are own-account responsibilities only, and administrators cannot recover or reset members or other administrators.
- Validated the Phase 2 interpretation of `FS-013`: recovery/login reset is own-account only for members and administrators, with audit and any future break-glass under super-admin responsibility.
- Validated the Phase 2 interpretation of `FS-014`: production-grade internal access control is the target, while simpler authentication is only transitional or non-production and must be risk-assessed.
- Updated `FS-015` in `README.md` to use `login reset` instead of `authenticator reset`, aligned with the clarified `FS-013` vocabulary.
- Validated the Phase 2 interpretation of `FS-015`: audit coverage includes lifecycle, role/access changes, protected-service denials, audit reads/exports, and recovery/login reset actions.
- Validated the Phase 2 interpretation of `FS-016`: audit access is super-admin-only and audit reads or exports must themselves be logged.
- Validated the Phase 2 interpretation of `FS-017`: simplicity and operability are baseline requirements, and added complexity must be justified by concrete needs.
- Completed the step-by-step Phase 2 scope review for `FS-001` through `FS-017`.
- Validated `RB-001` as correctly scoped to `FS-001`: the baseline remains limited to backoffice users and excludes public signup, public customer accounts, social login, and consumer IAM flows.
- Refined and validated `RB-002` so it covers administrator-created member records and administrative member management without conflicting with member own-profile read or own-account recovery/login reset.
- Validated `RB-003` as correctly scoped to `FS-017` and the company scale constraint: the solution must remain understandable for fewer than 1,000 internal users and added operational complexity must be justified.
- Refined and validated `RB-004` so it models the three feature-specified Phase 2 actors and prevents adding or merging actor responsibilities without an explicit scope change.
- Retired `RB-005` from active baseline requirements because it mixed administrative member management, role assignment, service access, profile-data changes, and logging into one broad requirement.
- Reframed the immutable feature specification in `README.md` to distinguish account types (`super-admin`, `admin`, `member`) from service-access roles, and clarified super-admin, admin, and member responsibilities accordingly.
- Clarified in `README.md` that an account type is fixed at account creation and cannot be changed later; a `member` account must never become an `admin` account.
- Added the initial identity-provider, OAuth2/OIDC, backoffice-account, account-type, service-access-role, and authorization-boundary definitions to root `FEATURE-REQUIREMENTS.md`.
- Updated `AGENTS.md` to identify root `FEATURE-REQUIREMENTS.md` as the dedicated working base for access-control capability requirements.
- Realigned `README.md` with the consolidated responsibility model: admins automatically access all service-access-role-covered protected services, admins and super-admins assign service-access roles only to members, super-admins manage the role catalog without protected-service access through those roles, service-access roles are not assigned to admin accounts, and break-glass remains a Phase 2 debate topic unless explicitly adopted later.
- Replaced the `README.md` `FS-*` minimum feature requirements table with a short pointer to root `FEATURE-REQUIREMENTS.md` as the single feature-requirements source.
- Renamed the `README.md` title and tightened its introduction to present the repository as the EDRLab backoffice access-control study.
- Refined the `README.md` core features list so it summarizes capabilities without duplicating the consolidated feature requirements.
- Updated the `README.md` Mermaid diagram to show member, admin/super-admin, identity-provider, access-control, role-management, audit, and protected-service flows.
- Tightened the `README.md` project goal so it states the study objective and main account-type/service-access-role distinction without repeating detailed requirements.
- Reworked the `README.md` actors and role types section into readable per-role responsibility blocks while preserving the validated access-control model.
- Renamed the `README.md` retired requirements section to `Feature Requirements Source` while preserving the old `minimum-feature-requirements` anchor for existing documentation links.
- Condensed the `README.md` initial scope section into grouped in-scope and out-of-scope boundaries without repeating detailed role requirements.
- Renamed the `README.md` Phase 2 debate topics section to `Open Study Questions` and grouped unresolved security, architecture, access-evidence, operations, and PoC questions.
- Reworked the `README.md` documentation section into a task-oriented entry-point table.
- Updated `ABSTRACT.md` to reflect the 2026-05-07 consolidation state: `FEATURE-REQUIREMENTS.md` as the single requirements source, baseline retirement, current validated responsibility model, and remaining open study questions.
- Promoted `FEATURE-REQUIREMENTS.md` from blank-slate working base to review-state single feature-requirements source and replaced former `FS-*` source links with consolidation-review traceability.

## 2026-05-06

### Changed

- Replaced prefix-based study document naming with a folder-based documentation structure and added `docs/README.md` plus `docs/decisions/README.md`.
- Clarified that the project study metadata block does not apply to conceptual wiki pages.
- Updated `FS-003` in `README.md` to narrow the mutable attribute examples to email and name.
- Updated `FS-013` in `README.md` to keep recovery, authenticator reset, administrator recovery, audit access, and future break-glass responsibility under super-admin responsibility.
- Refined Phase 2 requirements to mark audit reads, authenticator reset, administrator recovery, role definition changes, and break-glass activation as super-admin-only minimum operations.
- Refined Phase 2 PoC framing to keep the first protected backend test minimal with one protected service.
- Refined Phase 2 RBAC requirements to make role assignments permanent by default.
- Moved initial scope framing from current inputs into explicit Phase 2 requirement groups.
- Aligned architecture option framing with the requirements baseline for access-token constraints, privileged login controls, append-only audit records, and the minimal protected-service PoC boundary.
- Reframed JWT from a fixed baseline requirement into an access-token format option to compare against opaque tokens and introspection.
- Removed `RB-039` as a standalone baseline requirement and kept access-token format as an architecture evaluation question.
- Clarified `RB-005` so admins manage role assignments, while role creation remains a super-admin responsibility.
- Clarified member lifecycle transitions in `RB-013`: admins may disable `active` members, restore `disabled` members to `active`, and archive `disabled` members; `archived` members are non-restorable in the baseline.
- Removed the duplicate out-of-scope section from the requirements baseline so scope exclusions stay centralized in the root `README.md`.
- Simplified `RB-016` to require defining how already-issued access stops without embedding JWT-versus-opaque-token comparison in the requirement text.

### Added

- Added the initial Phase 2 threat model skeleton under `docs/risks/threat-model.md`.
- Added initial Phase 2 project requirements based on current stakeholder scoping answers.
- Added initial Phase 2 architecture option framing for monolithic, modular monolithic, split control-plane, microservices, and hybrid IAM shapes.
- Added the Phase 2 requirements baseline under `docs/requirements/baseline.md`.

### Removed

- Removed the initial Phase 2 project requirements document at stakeholder request.
