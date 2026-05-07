# Feature Scope Review

Status: Superseded
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements
Last reviewed: 2026-05-07

## Contents

- [Purpose](#purpose)
- [Review Method](#review-method)
- [Review Status](#review-status)
- [Validated Scope Notes](#validated-scope-notes)
- [Pending Review Queue](#pending-review-queue)
- [References](#references)

## Purpose

This document records the historical step-by-step review of each immutable `FS-*` requirement. It does not rewrite the feature specification; it records validated interpretation, retired baseline scope, and threat-model implications for Phase 2 requirement refinement ([README](../../README.md#minimum-feature-requirements), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

The root `FEATURE-REQUIREMENTS.md` file is now the consolidated requirements artifact. This review document remains as a historical validation trail for the earlier `FS-*` review and for traceability into the feature requirements review and threat model ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md), [Feature requirements review](./feature-requirements-review.md), [Threat model](../risks/threat-model.md)).

## Review Method

Each `FS-*` review step records:

| Field | Meaning |
| --- | --- |
| `Reviewed requirement` | The immutable feature-specification requirement being discussed. |
| `Validated interpretation` | The stakeholder-validated meaning for Phase 2. |
| `Consolidation implication` | How the interpretation fed the consolidated feature requirements after the former baseline was retired. |
| `Related retired baseline requirements` | The former `RB-*` requirements mapped to the `FS-*` requirement during consolidation. |
| `Threat-model implication` | Which risks, trust boundaries, entry points, or threat scenarios should be kept, refined, or excluded. |
| `Status` | `Pending`, `Validated`, or `Needs follow-up`. |

This review remains Phase 2 work: it may refine requirements, assumptions, risks, and open questions, but it must not select a final vendor, product, architecture, token strategy, implementation stack, or production recommendation ([Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

## Review Status

| Requirement | Status | Validation source | Notes |
| --- | --- | --- | --- |
| `FS-001` | Validated | User validation, 2026-05-07 | Internal human backoffice users only; no public accounts, social login, or service-account actor expansion in the Phase 2 baseline. |
| `FS-002` | Validated | User validation, 2026-05-07 | Members must be created or invited by an admin before activation; no public or self-service member creation. |
| `FS-003` | Validated | User validation, 2026-05-07 | Stable canonical member identifiers are required for lifecycle, roles, audit, and access decisions; email and name remain mutable attributes. |
| `FS-004` | Validated | User validation, 2026-05-07 | Explicit lifecycle states are required; members are retained, `archived` is terminal in the baseline, and transitions are controlled and auditable. |
| `FS-005` | Validated | User validation, 2026-05-07 | Non-active state blocks new access; already-issued access removal needs an explicit evaluated delay and strategy without selecting token format or final architecture now. |
| `FS-006` | Validated | User validation, 2026-05-07 | Admins own member-management operations and role-based service-access removal, within validated lifecycle policy and audit requirements. |
| `FS-007` | Validated | User validation, 2026-05-07 | Super-admins create roles; admins list, assign, and remove roles from members. Role definition changes remain non-admin unless explicitly scoped later. |
| `FS-008` | Validated | User validation, 2026-05-07 | Baseline authorization is simple role-based service access; finer permissions and policy engines remain outside baseline until justified by real service needs. |
| `FS-009` | Validated | User validation, 2026-05-07 | The minimal member role is consultation/read-only; stronger or finer permissions require a real service need and later review. |
| `FS-010` | Validated | User validation, 2026-05-07 | The baseline requires a controlled, auditable administration capability without selecting its technical form. |
| `FS-011` | Validated | User validation, 2026-05-07 | Protected backend services must authorize server-side from active member state and role-based service access, failing closed when uncertain. |
| `FS-012` | Validated | User validation, 2026-05-07 | Members may view only their own profile; profile changes and service-access assignments remain admin-controlled operations. |
| `FS-013` | Validated | User validation, 2026-05-07 | Recovery/login reset is own-account only for members and administrators. Admins cannot recover or reset members or other admins; audit and future break-glass remain super-admin responsibilities. |
| `FS-014` | Validated | User validation, 2026-05-07 | Production-grade internal access control is the target; simpler authentication is only transitional/non-production and must be risk-assessed. |
| `FS-015` | Validated | User validation, 2026-05-07 | Audit must cover lifecycle, role/access changes, protected-service denials, audit reads/exports, and recovery/login reset actions. |
| `FS-016` | Validated | User validation, 2026-05-07 | Audit access is super-admin-only, and audit reads or exports must themselves be logged. |
| `FS-017` | Validated | User validation, 2026-05-07 | Simplicity and operability are baseline requirements; added complexity must be justified by concrete needs. |

## Validated Scope Notes

### FS-001 - Backoffice Users Only

Reviewed requirement: `FS-001` requires the system to support backoffice users only, with public signup, public customer accounts, and social login out of scope for the initial specification ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-001` means human internal users only for the Phase 2 baseline. The baseline does not expand the actor model to public customers, public self-service users, social-login users, or service accounts. This was validated by the user on 2026-05-07.

Baseline implication: Keep `RB-001` as the direct baseline mapping for `FS-001`: the access-control capability serves backoffice users only and excludes public signup, customer accounts, social login, and consumer IAM flows ([Feature requirements review](./feature-requirements-review.md#coverage-review)). This interpretation also keeps the baseline aligned with the initial study scope in the project brief ([README](../../README.md#initial-scope)).

Threat-model implication: The threat model can deprioritize public-registration abuse, public customer account lifecycle abuse, and social-login callback abuse for the initial baseline. It must still model internal-user compromise, privileged-user abuse, invitation or onboarding abuse, protected-service authorization mistakes, access after disablement or role removal, and audit gaps because those scenarios remain in scope for internal backoffice access control ([Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-002 - Administrator-Created Members Only

Reviewed requirement: `FS-002` requires members to be created and managed only by administrators, with no public self-service registration in the initial specification ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-002` means every member must have been created or invited by an administrator before activation. A member may complete their onboarding after an admin-created invitation, but they cannot create their own member record or self-enroll into the backoffice. This was validated by the user on 2026-05-07.

Baseline implication: Keep `RB-002` as the direct baseline mapping for `FS-002`: member creation and management happen through administrator workflows only, without self-service registration ([Feature requirements review](./feature-requirements-review.md#coverage-review)). This also supports the existing lifecycle assumption that new members start in `invited` state and become `active` only after first successful connection ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model can deprioritize public signup abuse, bot-driven public account creation, and public customer account promotion into backoffice membership. It must still model invitation or onboarding abuse, compromised-admin member creation, creation of fraudulent internal members, missing audit evidence for member creation, and accidental access before the member is fully `active` ([Threat model](../risks/threat-model.md#external-dependencies), [Threat model](../risks/threat-model.md#entry-points), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-003 - Stable Member Identifiers

Reviewed requirement: `FS-003` requires member records to use stable identifiers separate from mutable attributes such as email and name ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-003` means each member has one stable canonical identifier used as the durable identity reference. Email and name may be used for display, search, notification, or candidate-specific login behavior, but they must not be used as permanent authorization, lifecycle, or audit keys. This was validated by the user on 2026-05-07.

Baseline implication: Keep `RB-009` as the direct baseline mapping for `FS-003`: do not use email or name as the permanent member identity ([Feature requirements review](./feature-requirements-review.md#coverage-review)). Lifecycle state, role assignments, protected-service access decisions, audit actor and target references, and any future token or session identity reference must resolve to the stable member identifier rather than to mutable profile attributes ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep identity-confusion risks in scope, including role transfer after email reuse, broken audit history after profile changes, authorization decisions based on stale mutable attributes, and tokens or sessions that treat email or name as the canonical subject. The model already treats member identities and profile data as protected assets and records profile data as an exit point that must remain tied to stable identity ([Threat model](../risks/threat-model.md#protected-assets-and-security-objectives), [Threat model](../risks/threat-model.md#exit-points)).

Status: Validated.

### FS-004 - Member Lifecycle States and Retention

Reviewed requirement: `FS-004` requires the member lifecycle to support at least `invited`, `active`, `disabled`, and `archived` states. It also states that members are retained rather than hard-deleted in the initial policy ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-004` makes explicit lifecycle state a baseline constraint. New members start as `invited`, become `active` after first successful connection, may be moved from `active` to `disabled`, may be restored from `disabled` to `active`, and may be archived from `disabled`. In the baseline, `archived` is terminal and member records are retained rather than hard-deleted. This was validated by the user on 2026-05-07.

Baseline implication: Keep `RB-010`, `RB-011`, `RB-013`, and `RB-014` as the lifecycle baseline: the system must support the four required states, controlled transitions, and record retention ([Feature requirements review](./feature-requirements-review.md#coverage-review)). Keep `RB-028` as the audit baseline for lifecycle changes, including creation, update, disablement, restoration, and archival ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep lifecycle-state abuse in scope, including access before activation, access after disablement or archival, abusive restoration, archival used to obscure history, and missing audit evidence for lifecycle transitions. This aligns with the member lifecycle protected asset and the access-after-disablement threat scenario ([Threat model](../risks/threat-model.md#protected-assets-and-security-objectives), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-005 - Non-Active Members and Access Removal

Reviewed requirement: `FS-005` requires non-active members to be unable to obtain new access to protected backoffice services. It also requires access removal for already-issued access to be simple, documented, and evaluated during the study ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-005` has two distinct meanings for Phase 2. First, `invited`, `disabled`, and `archived` members must not obtain new protected-service access. Second, already-issued access must have an explicit removal behavior that Phase 2 evaluates without selecting the final token format, browser storage model, or authorization architecture. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-005` to `RB-006`, `RB-013`, `RB-015`, `RB-016`, `RB-023`, and `RB-026` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-005` |
| --- | --- |
| `RB-006` | Members may access protected services only when they are `active` and authorized by role. |
| `RB-013` | Lifecycle transitions define how an admin disables, restores, or archives a member, which are the state changes that affect access. |
| `RB-015` | Non-active members are blocked from obtaining new protected-service access. |
| `RB-016` | Already-issued access must have a defined stopping behavior after disablement, archival, or role-access removal. |
| `RB-023` | Protected backend services must check active member state and role-based permission before granting access. |
| `RB-026` | Protected backend services must deny access when the member is not active, has no matching role, or the decision cannot be made safely. |

Baseline implication: Keep `RB-015` as the firm baseline rule that non-active members cannot obtain new protected-service access. Keep `RB-016` as the required study work to define how already-issued access stops after disablement, archival, or role-access removal ([Feature requirements review](./feature-requirements-review.md#coverage-review)). Protected services must also deny access when active member state or authorization cannot be safely established (`RB-023` and `RB-026`) ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep access-after-disablement and access-after-role-removal as a central threat scenario. The key risks are stale tokens or sessions, stale role claims, protected services that do not re-check member state, inconsistent revocation behavior across services, and revocation strategies too complex for the internal team to operate reliably ([Threat model](../risks/threat-model.md#threat-scenarios), [Threat model](../risks/threat-model.md#entry-points)).

Status: Validated.

### FS-006 - Administrator Member Management Operations

Reviewed requirement: `FS-006` requires administrators to create, read, update, list, disable, archive, restore, and remove role-based service access for members ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-006` defines administrator operations over members and role-based service access. Administrators can create or invite members, read and list members, update allowed profile attributes, disable active members, restore disabled members to active where baseline policy allows, archive disabled members, and remove members' role-based service access. It does not make administrators responsible for technical revocation of already-issued access, which remains a separate `FS-005` evaluation topic. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-006` to `RB-013`, `RB-017`, `RB-019`, and `RB-022` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-006` |
| --- | --- |
| `RB-013` | Lifecycle transitions define the allowed admin operations for disablement, restoration, and archival. |
| `RB-017` | The admin capability must cover member management, role listing, role assignment, and role-based service-access removal. |
| `RB-019` | Admins can assign roles to members and remove roles from members. |
| `RB-022` | Only admins can change member profile attributes and service access assignments. |

Baseline implication: Keep administrator member-management operations in the baseline, but keep them bounded by validated lifecycle policy and role-based service access. `FS-006` does not grant role creation, super-admin elevation, audit deletion, audit bypass, archived-member restoration, recovery authority, login-reset authority, or a guarantee of immediate already-issued access revocation ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep admin-operation abuse in scope, including compromised-admin member creation, fraudulent member restoration, unaudited access changes, profile update abuse, role removal that is not reflected in protected-service decisions, and privilege escalation attempted through member or role management. This aligns with the admin interface trust boundary and the admin member-management entry point ([Threat model](../risks/threat-model.md#trust-boundaries), [Threat model](../risks/threat-model.md#entry-points)).

Status: Validated.

### FS-007 - Role Creation and Assignment Responsibilities

Reviewed requirement: `FS-007` requires administrators to list roles, assign roles to members, and remove roles from members. It also requires super-admins to create roles ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-007` separates role-definition responsibility from operational role assignment. Super-admins create roles. Administrators can list existing roles, assign roles to members, and remove roles from members. Role modification or deletion is not an implicit administrator power and should remain outside admin scope unless explicitly refined later. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-007` to `RB-016`, `RB-017`, `RB-018`, `RB-019`, and `RB-029` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-007` |
| --- | --- |
| `RB-016` | Already-issued access must have a defined stopping behavior after role-access removal. |
| `RB-017` | The admin capability must support role listing, role assignment, and role-based service-access removal. |
| `RB-018` | The super-admin capability must support role creation. |
| `RB-019` | Admins can assign roles to members and remove roles from members. |
| `RB-029` | Role assignment, role removal, role changes, and protected-service access configuration changes must be logged. |

Baseline implication: Keep role creation under super-admin responsibility and keep day-to-day role assignment/removal under administrator responsibility. The baseline should not treat role modification, role deletion, creation of privileged role definitions, or self-service privilege elevation as admin capabilities unless a later explicit requirement changes that scope ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep role-management abuse in scope, including overly powerful role creation, accidental or malicious role assignment, role removal that is not reflected in protected-service decisions, missing audit records for role changes, and indirect privilege escalation through role definitions or assignments. This aligns with the role-management entry point and the admin privilege-escalation threat scenario ([Threat model](../risks/threat-model.md#entry-points), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-008 - Role-Based Service Access

Reviewed requirement: `FS-008` defines the minimum authorization model as role-based service access: a member either can or cannot access a protected backend service through an assigned role ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-008` makes simple service-level RBAC the baseline authorization model. The minimum unit of access is a protected backend service. A member can access that service only through an assigned role that grants the service-level access. Fine-grained permissions, contextual authorization rules, ABAC, policy engines, and ownership-style rules are not baseline requirements unless a later real service need justifies them. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-008` to `RB-020`, `RB-024`, and `RB-025` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-008` |
| --- | --- |
| `RB-020` | The baseline authorization model is role-based service access. |
| `RB-024` | Service access is granted through assigned roles and must not rely on frontend-only checks. |
| `RB-025` | Each protected backend service must define how roles map to allowed access. |

Baseline implication: Keep authorization simple and service-oriented in the baseline. Each protected service needs a clear mapping from assigned roles to allowed service access, but the baseline should not require fine-grained permission vocabularies, policy engines, contextual rules, or per-resource authorization unless later evidence shows that service-level access is insufficient ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep role-to-service mapping failures in scope, including overly broad roles, protected services interpreting roles inconsistently, frontend-only enforcement, stale or mismatched role information, and role explosion if too many fine-grained details are encoded prematurely. This aligns with the protected-service authorization-check entry point and the protected-service trust scenario ([Threat model](../risks/threat-model.md#entry-points), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-009 - Minimal Member Role

Reviewed requirement: `FS-009` requires the minimal member role to allow consultation-style access only. More precise permissions may be debated later if real service needs require them ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-009` makes the minimal member role read-only by default. It must not grant member management, role management, audit access, recovery authority, service configuration, write operations, destructive operations, or administrative powers. Any permission beyond consultation-style access must be justified by a real protected-service need and reviewed later instead of being included implicitly in the baseline. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-009` to `RB-021` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-009` |
| --- | --- |
| `RB-021` | The minimal member role remains read-only by default; finer permissions are added only when a real service needs them. |

Baseline implication: Keep the baseline member role strictly consultation/read-only. Do not introduce write permissions, administrative permissions, export permissions, or fine-grained permission vocabularies unless a later service-specific requirement proves they are needed ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep member-role overreach in scope, including a minimal role that becomes too powerful, backend services allowing mutation through a read-only role, fine-grained permissions added without a real need, and broad role definitions used as shortcuts for unrelated capabilities. This aligns with the role-management and protected-service authorization-check entry points ([Threat model](../risks/threat-model.md#entry-points)).

Status: Validated.

### FS-010 - Administration Capability

Reviewed requirement: `FS-010` requires the system to provide an administration capability for member management, role management, role assignment, service access checks, and audit-supporting operations ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-010` requires a controlled and auditable administration capability, but it does not require a specific technical form. The capability may later be realized as an administration UI, admin API, internal tool, managed product feature, or combination. It must preserve the validated admin and super-admin responsibility split and support the operations validated in `FS-006` and `FS-007`. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-010` to `RB-017` and `RB-018` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-010` |
| --- | --- |
| `RB-017` | The admin capability must support member management, role listing, role assignment, and role-based service-access removal. |
| `RB-018` | The super-admin capability must support role creation and audit-supporting operations. |

Baseline implication: Keep the administration capability as a required operational surface while leaving its implementation form open. The baseline should require authorization, responsibility separation, and auditability for administrative operations, but it should not select a final UI/API/product/architecture shape during Phase 2 ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep administration-surface risks in scope, including admin APIs exposed without strong authorization, blurred admin and super-admin responsibilities, unaudited administrative actions, inconsistent service-access checks, overly complex operations, and weak assumptions that an internal-only tool is automatically safe. This aligns with the admin interface trust boundary and admin member-management entry point ([Threat model](../risks/threat-model.md#trust-boundaries), [Threat model](../risks/threat-model.md#entry-points)).

Status: Validated.

### FS-011 - Protected Backend Service Access Decisions

Reviewed requirement: `FS-011` requires protected backend services to determine whether a given active member is allowed to access the service ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-011` means each protected backend service must enforce authorization server-side. The service must be able to determine that the member is `active` and has role-based service access before granting access. Frontend-only visibility, navigation state, or UI controls are not sufficient. If the service cannot safely determine the member state or authorization result, it must deny access. The exact mechanism for carrying or looking up the access decision remains open for Phase 2 evaluation. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-011` to `RB-006`, `RB-023`, `RB-024`, `RB-025`, `RB-026`, `RB-030`, and `RB-038` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-011` |
| --- | --- |
| `RB-006` | Members can access protected services only when they are active and authorized by role. |
| `RB-023` | Protected backend services must check active member state and role-based permission before granting access. |
| `RB-024` | Service access is granted through assigned roles and must not rely on frontend-only checks. |
| `RB-025` | Each protected backend service must define how roles map to allowed access. |
| `RB-026` | Services deny access when the member is not active, lacks a matching role, or the decision cannot be made safely. |
| `RB-030` | Protected-service authorization denials must be logged. |
| `RB-038` | If access tokens are used, protected services must validate them server-side before access. |

Baseline implication: Keep server-side protected-service authorization as a baseline requirement. Each protected service must have a clear way to evaluate active member state and role-based access, and must fail closed when authorization cannot be established. The baseline should not yet choose JWT, opaque tokens, introspection, session lookup, authorization lookup, or a hybrid strategy; those remain evaluation questions ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep protected-service enforcement failures in scope, including trusting frontend state, accepting unvalidated tokens or claims, using stale role data, allowing disabled members, inconsistent role-to-service mapping, fail-open behavior when authorization is unavailable, and missing logs for denied authorization decisions. This aligns with the protected-service access decision asset and the protected-service trust scenario ([Threat model](../risks/threat-model.md#protected-assets-and-security-objectives), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-012 - Member Profile Read and Admin-Controlled Changes

Reviewed requirement: `FS-012` requires only administrators to change member profile attributes and service access assignments, while members may view their own profile information ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-012` limits member self-service to read-only consultation of the member's own profile. Members cannot update their own profile attributes, change their service access, assign roles to themselves, or request access as a baseline self-service workflow. Administrators control profile changes and service-access assignments, and those changes remain audit-relevant. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-012` to `RB-006`, `RB-019`, and `RB-022` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-012` |
| --- | --- |
| `RB-006` | Members may view their own profile and access protected services only when active and authorized by role. |
| `RB-019` | Admins can assign roles to members and remove roles from members. |
| `RB-022` | Only admins can change member profile attributes and service access assignments. |

Baseline implication: Keep member self-service read-only in the baseline. Profile changes, role assignment, role removal, and service-access assignment remain administrator operations. Protected services and profile endpoints must scope member reads to the authenticated member's own profile and must not treat mutable profile attributes as authorization keys ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep profile and assignment abuse in scope, including members modifying their own email or name to cause identity confusion, members assigning themselves access, IDOR-style profile reads for other members, unaudited admin updates, and authorization decisions based on mutable profile fields. This aligns with the member profile exit point and the user-browser trust boundary ([Threat model](../risks/threat-model.md#exit-points), [Threat model](../risks/threat-model.md#trust-boundaries)).

Status: Validated.

### FS-013 - Responsibility Separation and Own-Account Recovery

Reviewed requirement: `FS-013` requires super-admin, admin, and member responsibilities to remain separated. Member recovery and login reset belong only to the member's own-account responsibility. Administrator recovery and login reset belong only to the administrator's own-account responsibility. Administrators must not recover or reset member accounts or other administrator accounts. Audit access and any future break-glass process belong to the super-admin responsibility ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-013` makes recovery and login reset own-account responsibilities for members and administrators. A member can recover or reset only their own member login. An administrator can recover or reset only their own administrator login. Administrators cannot recover or reset member accounts, other administrator accounts, or super-admin accounts. Super-admin responsibility covers audit access and any future break-glass process, but not routine cross-account recovery or login reset. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-013` to `RB-004`, `RB-007`, `RB-008`, `RB-032`, `RB-034`, and `RB-043` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-013` |
| --- | --- |
| `RB-004` | The baseline keeps super-admin, admin, and member as separate actors. |
| `RB-007` | Recovery and login-reset responsibilities are separated by actor and limited to own-account scope; audit access and future break-glass remain super-admin responsibilities. |
| `RB-008` | Admins must not silently escalate privileges or bypass auditability. |
| `RB-032` | Recovery and login-reset actions affecting account access or privileged accountability must be logged. |
| `RB-034` | Admin and super-admin operations need strong server-side authorization. |
| `RB-043` | Break-glass access remains out of current scope unless explicitly reopened. |

Baseline implication: Keep recovery and login reset self-scoped by account owner for members and administrators. Do not include administrator cross-account reset, member reset by admin, admin reset by another admin, or routine super-admin reset as baseline capabilities. Keep audit access super-admin-only, and keep break-glass out of the current baseline unless the study scope explicitly changes ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep own-account recovery and login-reset abuse in scope, including account takeover through weak recovery, reset used to bypass MFA or passkeys, missing audit evidence for security-relevant recovery, and any accidental introduction of cross-account reset paths. Super-admin audit access abuse and any future break-glass abuse remain separate high-risk topics ([Threat model](../risks/threat-model.md#threat-scenarios), [Threat model](../risks/threat-model.md#entry-points)).

Status: Validated.

### FS-014 - Production-Grade Security Posture

Reviewed requirement: `FS-014` requires the security posture to target production-grade internal access control. The first minimal version may use simpler authentication, but Phase 2 must evaluate the risks and the path toward stronger production controls ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-014` treats production-grade internal access control as the target posture. Internal use does not mean trusted-by-default access. Simpler authentication may be acceptable only as a non-production, PoC, or explicitly transitional step, and must be recorded as a risk rather than as the target security posture. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-014` to `RB-033` and `RB-035` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-014` |
| --- | --- |
| `RB-033` | The target is production-grade internal access control; simpler first-version authentication is a risk to evaluate. |
| `RB-035` | Admins and super-admins need MFA or phishing-resistant passwordless login. |

Baseline implication: Keep production-grade internal access control as the security target while allowing simple authentication only as a documented transitional or non-production constraint. Phase 2 must evaluate the risk and hardening path for privileged login controls, recovery and login reset, token or session strategy, server-side authorization, access removal, auditability, and operational ownership without selecting the final product or architecture yet ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep weak transitional authentication in scope, including privileged accounts without MFA or phishing-resistant login, weak recovery or login reset, poorly protected sessions or access tokens, frontend-only authorization, insufficient auditability, and treating PoC controls as production controls. This aligns with the authentication/session dependency and privileged-user authenticator dependency ([Threat model](../risks/threat-model.md#external-dependencies)).

Status: Validated.

### FS-015 - Audit Event Coverage

Reviewed requirement: `FS-015` requires audit events to cover member creation, member update, member disablement, member restoration, role assignment, role removal, role changes, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or login reset actions ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-015` defines the minimum security-relevant audit event coverage. The audit baseline covers member lifecycle changes, admin-controlled profile updates, role assignment and removal, role changes, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or login reset actions. It does not require logging every ordinary business read as an audit event. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-015` to `RB-008`, `RB-027`, `RB-028`, `RB-029`, `RB-030`, `RB-031`, `RB-032`, `RB-034`, and `RB-040` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-015` |
| --- | --- |
| `RB-008` | Admins must not silently escalate privileges or bypass auditability. |
| `RB-027` | Security-relevant admin and super-admin actions must be logged. |
| `RB-028` | Member lifecycle changes must be logged. |
| `RB-029` | Role and access changes must be logged. |
| `RB-030` | Protected-service authorization denials must be logged. |
| `RB-031` | Audit reads and exports must be logged. |
| `RB-032` | Recovery and login-reset actions affecting account access or privileged accountability must be logged. |
| `RB-034` | Admin and super-admin operations need strong server-side authorization. |
| `RB-040` | Audit records are retained indefinitely as append-only records in the baseline. |

Baseline implication: Keep audit coverage focused on security-relevant and accountability-relevant events. The baseline should require enough event detail to identify actor, target, action, time, decision/result, and relevant access context during later refinement, while leaving exact schema, storage, retention tooling, and export format open for Phase 2 evaluation ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep audit gaps and audit tampering in scope, including privileged actions without trace, mutable or deletable audit records, missing protected-service denial logs, audit reads or exports without their own audit events, recovery or login reset without attribution, and audit records too sparse for investigation. This aligns with the audit-records protected asset and the audit-gap threat scenario ([Threat model](../risks/threat-model.md#protected-assets-and-security-objectives), [Threat model](../risks/threat-model.md#threat-scenarios)).

Status: Validated.

### FS-016 - Super-Admin Audit Access

Reviewed requirement: `FS-016` requires super-admins to be able to consult audit records, and requires audit access itself to be logged ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-016` makes audit access a super-admin responsibility. Super-admins can consult audit records, and any audit read or export must itself create an audit event. Audit access is not a standard administrator capability. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-016` to `RB-007`, `RB-018`, and `RB-031` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-016` |
| --- | --- |
| `RB-007` | Audit access remains under super-admin responsibility. |
| `RB-018` | The super-admin capability must support audit-supporting operations. |
| `RB-031` | Super-admins can consult and export audit records, and audit reads or exports must be logged. |

Baseline implication: Keep audit access super-admin-only. Any audit read or export must be logged with enough context to support accountability. The baseline should not grant audit-record consultation to ordinary admins unless an explicit later requirement changes the responsibility model ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep audit-access abuse in scope, including unlogged audit reads, unlogged exports, administrators accessing audit records without super-admin responsibility, audit records exposing sensitive accountability data, and inability to determine who consulted or exported audit material. This aligns with the audit-read entry point and super-admin audit access trust boundary ([Threat model](../risks/threat-model.md#entry-points), [Threat model](../risks/threat-model.md#trust-boundaries)).

Status: Validated.

### FS-017 - Simplicity and Operability

Reviewed requirement: `FS-017` requires the system to remain understandable and operable by the internal team. Simplicity is a requirement, not merely an implementation preference ([README](../../README.md#minimum-feature-requirements)).

Validated interpretation: `FS-017` makes simplicity and operability baseline requirements. Future options must remain understandable, supportable, recoverable, and maintainable by the internal team at the expected scale. Added complexity must be justified by concrete security, compliance, maintainability, or product needs rather than by architectural preference. This was validated by the user on 2026-05-07.

Related baseline requirements: the requirements baseline traceability matrix maps `FS-017` to `RB-003` and `RB-042` ([Feature requirements review](./feature-requirements-review.md#coverage-review)).

| Baseline requirement | Why it matters for `FS-017` |
| --- | --- |
| `RB-003` | The solution must remain understandable for fewer than 1,000 internal users, and added operational complexity must be justified. |
| `RB-042` | Operational complexity must stay proportional to the internal scale and team capability. |

Baseline implication: Keep simplicity and operability as evaluation constraints. The baseline should resist unnecessary architecture, product, workflow, policy-engine, or authorization-model complexity unless the study records a concrete need and supporting evidence. Candidate approaches must be evaluated on whether the team can operate, troubleshoot, back up, restore, upgrade, and evolve them safely ([Feature requirements review](./feature-requirements-review.md#coverage-review), [Feature requirements review](./feature-requirements-review.md#coverage-review)).

Threat-model implication: The threat model must keep operational complexity risks in scope, including systems that are too complex to operate reliably, access rules that are misunderstood, recovery or revocation paths that are hard to test, audit procedures that are ambiguous, and security controls that look strong on paper but are fragile in day-to-day operation. This aligns with the external dependency on backup, recovery, upgrade, and support process ([Threat model](../risks/threat-model.md#external-dependencies)).

Status: Validated.

## Pending Review Queue

All `FS-001` through `FS-017` requirements have been reviewed and validated for Phase 2 scope interpretation as of 2026-05-07.

## References

- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Feature Requirements Review](./feature-requirements-review.md)
- [Threat Model](../risks/threat-model.md)

