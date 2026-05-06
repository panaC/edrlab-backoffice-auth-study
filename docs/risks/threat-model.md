# Threat Model

Status: Draft
Phase: Phase 2 - Requirements and Risk Framing
Scope: Risks
Last reviewed: 2026-05-06

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Source Inputs](#source-inputs)
- [Protected Assets and Security Objectives](#protected-assets-and-security-objectives)
- [Actors and Trust Boundaries](#actors-and-trust-boundaries)
- [Threat Scenarios](#threat-scenarios)
- [Requirement Refinement Candidates](#requirement-refinement-candidates)
- [Assumptions](#assumptions)
- [Open Questions](#open-questions)
- [References](#references)

## Purpose

This document records Phase 2 threat modeling for the internal backoffice access-control study. It supports `RB-048`, which requires threat modeling and security requirement refinement before candidate evaluation ([Requirements baseline](../requirements/baseline.md#security-baseline)).

## Scope

The threat model covers the in-scope study areas from the immutable feature specification: internal member lifecycle management, administrator-only account and role management, role-based access to protected backend services, service access checks, auditability, and security requirement refinement ([README](../../README.md#initial-scope)).

It does not select a final vendor, product, architecture, hosting model, implementation stack, access-token format, or browser token storage model during Phase 2 ([Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), [Requirements baseline](../requirements/baseline.md#simplicity-and-study-constraints)).

## Source Inputs

- Immutable feature specification and initial study scope in the root [README](../../README.md#immutable-feature-specification).
- Phase 2 boundaries and evidence rules in [Project governance](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing).
- Phase 2 requirements baseline, especially `RB-048`, in [Requirements baseline](../requirements/baseline.md#security-baseline).

## Protected Assets and Security Objectives

| Protected asset | Security objective | Source |
| --- | --- | --- |
| Member identities and profile data | Keep stable member identity separate from mutable profile attributes, and allow profile changes only through authorized admin workflows. | [FS-003](../../README.md#minimum-feature-requirements), [FS-012](../../README.md#minimum-feature-requirements) |
| Member lifecycle state | Prevent non-active members from obtaining new protected-service access, and define how already-issued access stops after disablement, archival, or access removal. | [FS-004](../../README.md#minimum-feature-requirements), [FS-005](../../README.md#minimum-feature-requirements), [RB-016](../requirements/baseline.md#member-lifecycle) |
| Roles and role assignments | Ensure service access is granted only through authorized role assignment and cannot be changed silently or by unauthorized actors. | [FS-007](../../README.md#minimum-feature-requirements), [FS-008](../../README.md#minimum-feature-requirements), [RB-019](../requirements/baseline.md#administration-and-role-management) |
| Protected-service access decisions | Ensure backend services make server-side access decisions based on active member state and assigned roles. | [FS-011](../../README.md#minimum-feature-requirements), [RB-023](../requirements/baseline.md#protected-service-access), [RB-024](../requirements/baseline.md#protected-service-access) |
| Admin and super-admin operations | Preserve separation between admin and super-admin responsibilities, especially for recovery, login-factor reset, audit access, and future break-glass handling. | [FS-013](../../README.md#minimum-feature-requirements), [RB-007](../requirements/baseline.md#actors-and-responsibility-separation), [RB-008](../requirements/baseline.md#actors-and-responsibility-separation) |
| Access tokens or sessions | Ensure protected services can validate access server-side without assuming a final token format or browser storage model during Phase 2. | [FS-011](../../README.md#minimum-feature-requirements), [RB-038](../requirements/baseline.md#security-baseline), [RB-045](../requirements/baseline.md#simplicity-and-study-constraints) |
| Audit records | Preserve useful auditability for privileged and security-relevant operations, including audit access itself. | [FS-015](../../README.md#minimum-feature-requirements), [FS-016](../../README.md#minimum-feature-requirements), [RB-027](../requirements/baseline.md#auditability), [RB-031](../requirements/baseline.md#auditability) |
| Recovery and login-factor reset actions | Keep recovery and login-factor reset under super-admin control and ensure those actions are auditable. | [FS-013](../../README.md#minimum-feature-requirements), [FS-015](../../README.md#minimum-feature-requirements), [RB-032](../requirements/baseline.md#auditability) |

## Actors and Trust Boundaries

### Actors and System Participants

| Actor or participant | Role in the threat model | Source |
| --- | --- | --- |
| Member | Internal user who can view their own profile and access protected backend services only when active and authorized by role. | [Actors](../../README.md#actors), [RB-006](../requirements/baseline.md#actors-and-responsibility-separation) |
| Admin | Privileged operator who manages members, role assignments, service access, and member profile data. Admin actions are security-relevant and must be auditable. | [Actors](../../README.md#actors), [RB-005](../requirements/baseline.md#actors-and-responsibility-separation), [RB-027](../requirements/baseline.md#auditability) |
| Super-admin | Highest-privilege operator responsible for audit access, recovery, login-factor reset, administrator recovery, and any future break-glass process if adopted. | [Actors](../../README.md#actors), [RB-007](../requirements/baseline.md#actors-and-responsibility-separation) |
| Protected backend service | Company-controlled service that must determine whether an active member is authorized before granting access. | [FS-011](../../README.md#minimum-feature-requirements), [RB-023](../requirements/baseline.md#protected-service-access) |
| Access-control capability | Project capability responsible for member lifecycle, roles, role assignments, service access checks, and audit-supporting operations. | [FS-010](../../README.md#minimum-feature-requirements), [RB-017](../requirements/baseline.md#administration-and-role-management), [RB-018](../requirements/baseline.md#administration-and-role-management) |
| Audit reader | Super-admin activity that consults or exports audit records. Audit access itself must be logged. | [FS-016](../../README.md#minimum-feature-requirements), [RB-031](../requirements/baseline.md#auditability) |

### Trust Boundaries

To be completed in the next step.

## Threat Scenarios

To be completed in a later step.

## Requirement Refinement Candidates

To be completed after threat scenarios are identified.

## Assumptions

To be completed as assumptions are identified.

## Open Questions

To be completed as open questions are identified.

## References

- [README - Immutable Feature Specification](../../README.md#immutable-feature-specification)
- [README - Actors](../../README.md#actors)
- [README - Minimum Feature Requirements](../../README.md#minimum-feature-requirements)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 2](../../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [Requirements Baseline - Security Baseline](../requirements/baseline.md#security-baseline)
