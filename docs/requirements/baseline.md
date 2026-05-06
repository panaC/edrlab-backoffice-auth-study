# Requirements Baseline

Status: Draft
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements
Last reviewed: 2026-05-06

## Contents

- [Purpose](#purpose)
- [Source Inputs](#source-inputs)
- [Requirement Format](#requirement-format)
- [Baseline Requirements](#baseline-requirements)
- [Traceability Matrix](#traceability-matrix)
- [Assumptions](#assumptions)
- [Open Questions](#open-questions)
- [References](#references)

## Purpose

This document will translate the immutable feature specification into a Phase 2 requirements baseline without selecting a final vendor, product, architecture, hosting model, implementation stack, access-token format, or browser token storage model ([README](../../README.md#immutable-feature-specification), [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).

## Source Inputs

- Immutable feature specification in the root [README](../../README.md#minimum-feature-requirements).
- Phase 2 boundaries and evidence rules in [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing).
- Repository documentation and citation rules in [AGENTS](../../AGENTS.md#documentation-rules).

## Requirement Format

Baseline requirements will use `RB-001`, `RB-002`, and following identifiers. Each requirement should trace back to one or more immutable feature-specification requirements, user-provided assumptions, or cited external sources where appropriate.

## Baseline Requirements

### Scope and User Population

| ID | Requirement | Source |
| --- | --- | --- |
| RB-001 | Serve internal backoffice users only. Do not include public signup, customer accounts, social login, or consumer IAM flows. | [FS-001](../../README.md#minimum-feature-requirements), [Initial Scope](../../README.md#initial-scope) |
| RB-002 | Create and manage members through administrator workflows only. Do not assume self-service registration. | [FS-002](../../README.md#minimum-feature-requirements) |
| RB-003 | Keep the solution understandable for fewer than 1,000 internal users. Justify added operational complexity. | [Company Goal](../../README.md#company-goal), [FS-017](../../README.md#minimum-feature-requirements) |

### Actors and Responsibility Separation

| ID | Requirement | Source |
| --- | --- | --- |
| RB-004 | Support three baseline actors: super-admin, admin, and member. Do not merge their responsibilities. | [Actors](../../README.md#actors), [FS-013](../../README.md#minimum-feature-requirements) |
| RB-005 | Let admins manage members, role assignments, service access, and member profile data. Log admin actions. | [Actors](../../README.md#actors), [FS-006](../../README.md#minimum-feature-requirements), [FS-007](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |
| RB-006 | Let members view their own profile and access protected services only when active and authorized by role. | [Actors](../../README.md#actors), [FS-005](../../README.md#minimum-feature-requirements), [FS-011](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements) |
| RB-007 | Keep recovery, login-factor reset, administrator recovery, audit access, and future break-glass responsibility under super-admin control. | [FS-013](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements) |
| RB-008 | Prevent silent privilege escalation. An admin must not grant themselves super-admin privileges or bypass auditability. | [Actors](../../README.md#actors), [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |

### Member Lifecycle

| ID | Requirement | Source |
| --- | --- | --- |
| RB-009 | Use stable member identifiers. Do not use email or name as the permanent member identity. | [FS-003](../../README.md#minimum-feature-requirements) |
| RB-010 | Support these member states: `invited`, `active`, `disabled`, and `archived`. | [FS-004](../../README.md#minimum-feature-requirements) |
| RB-011 | Create new members in `invited` state. Move them to `active` after their first successful connection. | [FS-004](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |
| RB-012 | Do not let admins move an `active`, `disabled`, or `archived` member back to `invited`. | user-provided requirement, 2026-05-06 |
| RB-013 | Let admins disable an `active` member, restore a `disabled` member to `active`, and archive a `disabled` member. An `archived` member cannot be restored in the baseline. | [FS-004](../../README.md#minimum-feature-requirements), [FS-005](../../README.md#minimum-feature-requirements), [FS-006](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |
| RB-014 | Retain member records instead of hard-deleting them in the initial policy. | [FS-004](../../README.md#minimum-feature-requirements) |
| RB-015 | Block new protected-service access for non-active members. | [FS-005](../../README.md#minimum-feature-requirements) |
| RB-016 | Define how already-issued access stops after disablement, archival, or role-access removal. | [FS-005](../../README.md#minimum-feature-requirements), [FS-007](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |

### Administration and Role Management

| ID | Requirement | Source |
| --- | --- | --- |
| RB-017 | Provide an admin capability for member management, role listing, and role assignment. | [FS-006](../../README.md#minimum-feature-requirements), [FS-007](../../README.md#minimum-feature-requirements), [FS-010](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |
| RB-018 | Provide a super-admin capability for role creation and audit-supporting operations. | [FS-007](../../README.md#minimum-feature-requirements), [FS-010](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |
| RB-019 | Let admins assign roles to members and remove roles from members. | [FS-007](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements) |
| RB-020 | Use role-based service access as the baseline authorization model. | [FS-008](../../README.md#minimum-feature-requirements) |
| RB-021 | Keep the minimal member role read-only by default. Add finer permissions only when a real service needs them. | [FS-009](../../README.md#minimum-feature-requirements) |
| RB-022 | Let only admins change member profile attributes and service access assignments. | [FS-012](../../README.md#minimum-feature-requirements) |

### Protected Service Access

| ID | Requirement | Source |
| --- | --- | --- |
| RB-023 | Let protected backend services check whether a member is active and allowed by role before granting access. | [FS-005](../../README.md#minimum-feature-requirements), [FS-011](../../README.md#minimum-feature-requirements) |
| RB-024 | Grant service access through assigned roles only. Do not rely on frontend-only checks. | [FS-008](../../README.md#minimum-feature-requirements), [FS-011](../../README.md#minimum-feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| RB-025 | Define how each protected backend service maps roles to allowed access. | [FS-008](../../README.md#minimum-feature-requirements), [FS-011](../../README.md#minimum-feature-requirements) |
| RB-026 | Deny protected-service access when the member is not active, has no matching role, or the access decision cannot be made safely. | [FS-005](../../README.md#minimum-feature-requirements), [FS-011](../../README.md#minimum-feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |

### Auditability

| ID | Requirement | Source |
| --- | --- | --- |
| RB-027 | Log security-relevant admin and super-admin actions. | [Actors](../../README.md#actors), [FS-015](../../README.md#minimum-feature-requirements) |
| RB-028 | Log member lifecycle changes, including creation, update, disablement, restoration, and archival. | [FS-004](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |
| RB-029 | Log role and access changes, including role assignment, role removal, role changes, and protected-service access configuration changes. | [FS-007](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |
| RB-030 | Log protected-service authorization denials. | [FS-011](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |
| RB-031 | Let super-admins consult and export audit records. Log audit reads and exports. | [FS-016](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), user-provided requirement, 2026-05-06 |
| RB-032 | Log recovery and login-factor reset actions. | [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements) |

### Security Baseline

| ID | Requirement | Source |
| --- | --- | --- |
| RB-033 | Target production-grade internal access control. Treat simpler first-version authentication as a risk to evaluate, not as the final security posture. | [FS-014](../../README.md#minimum-feature-requirements), [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics) |
| RB-034 | Protect admin and super-admin operations with strong server-side authorization. | [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| RB-035 | Require admins and super-admins to use MFA or phishing-resistant passwordless login. | [FS-014](../../README.md#minimum-feature-requirements), [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics), [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html), user-provided requirement, 2026-05-06 |
| RB-036 | Do not rely on custom cryptography or plain-text password storage. | [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) |
| RB-037 | If OAuth2 or OIDC is used, do not use the Implicit Flow for new browser-based applications. | [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700), [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics) |
| RB-038 | Use access tokens for protected-service access. Validate them server-side before protected-service access. | [FS-011](../../README.md#minimum-feature-requirements), [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750), [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700), user-provided requirement, 2026-05-06 |
| RB-048 | Perform threat modeling during Phase 2 and refine security requirements from identified risks before candidate evaluation. | [Initial Scope](../../README.md#initial-scope), [FS-014](../../README.md#minimum-feature-requirements), [Project Governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing) |

### Operational Baseline

| ID | Requirement | Source |
| --- | --- | --- |
| RB-040 | Keep audit records indefinitely. Store audit events as append-only records. | [FS-015](../../README.md#minimum-feature-requirements), [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics), user-provided requirement, 2026-05-06 |
| RB-041 | For each candidate approach, check how backups, recovery, upgrades, and support would work. | [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics), [Project Governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing) |
| RB-042 | Keep operational complexity proportional to the internal scale and team capability. | [Company Goal](../../README.md#company-goal), [FS-017](../../README.md#minimum-feature-requirements) |
| RB-043 | Keep break-glass access out of the current study scope. Revisit it only if the scope explicitly changes. | [FS-013](../../README.md#minimum-feature-requirements), [Phase 2 Debate Topics](../../README.md#phase-2-debate-topics), user-provided requirement, 2026-05-06 |

### Simplicity and Study Constraints

| ID | Requirement | Source |
| --- | --- | --- |
| RB-044 | Keep every baseline requirement tied to the immutable feature specification, a cited source, or a user-provided requirement. | [README](../../README.md#immutable-feature-specification), [Project Governance](../../PROJECT-GOVERNANCE.md#evidence-standard) |
| RB-045 | Do not select a final vendor, product, architecture, hosting model, implementation stack, access-token format, or browser token storage model in this baseline. Decide the access-token format and browser token storage model before any production recommendation. | [README](../../README.md#phase-2-debate-topics), [Project Governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing) |
| RB-046 | Do not add implementation code, dependencies, deployment files, databases, migrations, or CI unless the scope explicitly changes or a PoC is requested. | [Project Governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), [AGENTS](../../AGENTS.md#current-operating-phase) |
| RB-047 | Record uncertain points as assumptions or open questions instead of turning them into hidden decisions. | [Project Governance](../../PROJECT-GOVERNANCE.md#evidence-standard), [AGENTS](../../AGENTS.md#citation-rules) |

## Traceability Matrix

| Feature spec | Baseline requirements |
| --- | --- |
| FS-001 | RB-001 |
| FS-002 | RB-002 |
| FS-003 | RB-009 |
| FS-004 | RB-010, RB-011, RB-013, RB-014, RB-028 |
| FS-005 | RB-006, RB-013, RB-015, RB-016, RB-023, RB-026 |
| FS-006 | RB-005, RB-013, RB-017 |
| FS-007 | RB-005, RB-017, RB-018, RB-019, RB-029 |
| FS-008 | RB-020, RB-024, RB-025 |
| FS-009 | RB-021 |
| FS-010 | RB-017, RB-018 |
| FS-011 | RB-006, RB-023, RB-024, RB-025, RB-026, RB-030, RB-038 |
| FS-012 | RB-005, RB-006, RB-019, RB-022 |
| FS-013 | RB-004, RB-007, RB-008, RB-032, RB-034, RB-043 |
| FS-014 | RB-033, RB-035, RB-048 |
| FS-015 | RB-005, RB-008, RB-027, RB-028, RB-029, RB-030, RB-031, RB-032, RB-034, RB-040 |
| FS-016 | RB-007, RB-018, RB-031 |
| FS-017 | RB-003, RB-042 |

## Assumptions

- New members start in `invited` state and become `active` after their first successful connection.
- Admins cannot move an `active`, `disabled`, or `archived` member back to `invited`.
- Only super-admins can create roles.
- Audit records are kept indefinitely as append-only records.
- The first evaluation or PoC uses one simple protected backend API whose only purpose is to answer whether a member has access to a demo resource, using a simple role such as `demo:read`.

## Open Questions

- Should protected services use JWT access tokens ([RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)), opaque access tokens with introspection or authorization lookup ([RFC 7662](https://www.rfc-editor.org/rfc/rfc7662)), or a hybrid pattern?

## References

- [README - Immutable Feature Specification](../../README.md#immutable-feature-specification)
- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [AGENTS - Documentation Rules](../../AGENTS.md#documentation-rules)
- [RFC 6750 - OAuth 2.0 Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
