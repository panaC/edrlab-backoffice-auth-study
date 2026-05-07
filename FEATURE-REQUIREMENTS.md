# Feature Requirements Specification

Status: Review
Last reviewed: 2026-05-07

This document is the single feature-requirements source for the backoffice access-control capability. It consolidates the former `README.md` `FS-*` requirements and retired Phase 2 baseline material into one goal-oriented, concrete, and traceable `FR-*` list.

## Contents

- [Goal](#goal)
- [Definitions](#definitions)
- [Account Types](#account-types)
- [Invariants](#invariants)
- [Feature Requirements](#feature-requirements)
- [Out of Scope](#out-of-scope)
- [References](#references)

## Goal

The system must provide a simple, secure, and auditable way to manage backoffice accounts, keep account types separated and immutable, and control access to company-controlled protected backend services through service-access roles.

## Definitions

`authentication identity`
: The identity authenticated by an external identity provider or authentication system. OpenID Connect adds an identity layer on top of OAuth 2.0 and can provide claims about an authenticated end-user ([OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)). Access-control may consume an authenticated subject identifier, but it does not own credentials, MFA, login sessions, or identity-provider account recovery.

`backoffice account`
: The access-control account record used by this capability. A backoffice account is linked to an authenticated subject and owns the access-control state needed by protected backend services: account type, lifecycle state, any service-access role assignments, and audit-relevant account metadata.

`account type`
: The immutable account category of a backoffice account. The account types are `super-admin`, `admin`, and `member`. An account type is fixed when the account is created and cannot be changed later.

`service-access role`
: An access-control role that represents access to a protected backend service. Active `admin` accounts automatically receive the protected-service access covered by service-access roles, while `member` accounts receive that access only when a role is assigned to them. This follows the RBAC idea that users are assigned roles and roles are assigned privileges ([NIST RBAC](https://csrc.nist.gov/projects/role-based-access-control)), with a project-specific rule for automatic admin service access. A service-access role is separate from an account type and must not grant account-management responsibilities.

`protected backend service`
: A company-controlled backend service that requires an access decision before serving a request. In OAuth 2.0 terms, protected resources are hosted by resource servers and accessed with access tokens issued by an authorization server ([RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)).

`authorization boundary`
: The boundary between authentication and access-control. The identity provider authenticates the subject. The access-control capability decides whether the authenticated subject is represented by an active backoffice account and whether the account type or assigned service-access roles allow access to a protected backend service.

## Account Types

The supported account types are:

- `super-admin`
- `admin`
- `member`

## Invariants

- Every backoffice account has exactly one `account type`: `super-admin`, `admin`, or `member`.
- An `account type` is set at account creation and must never be changed, merged, or elevated later ([README](./README.md#actors-and-role-types)).
- Service-access roles are independent from account types and must not grant account-management responsibilities ([README](./README.md#actors-and-role-types)).
- `super-admin` responsibility for service-access-role management must not grant protected backend service access, and service-access roles are assigned to `member` accounts rather than to `admin` accounts.

## Feature Requirements

| ID | Requirement | Source |
| --- | --- | --- |
| FR-001 | Every backoffice account must have exactly one fixed account type: `super-admin`, `admin`, or `member`. The account type is set at account creation and must never be changed, merged, or elevated later. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-002 | Service-access roles must be independent from account types. A service-access role may describe protected backend service access consumed automatically by active `admin` accounts or through assignment to `member` accounts, but must not change an account type or grant account-management responsibilities. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-003 | Active `admin` accounts must automatically be allowed to access every protected backend service covered by any service-access role. Admins must also be able to assign and remove service-access roles for `member` accounts. | User validation, 2026-05-07; [Feature requirements review - D-006](./docs/requirements/feature-requirements-review.md#decision-log) |
| FR-004 | `super-admin` accounts must not receive protected backend service access through service-access roles. Super-admins must be able to manage the service-access-role catalog and assign or remove service-access roles for `member` accounts. Super-admins must not assign service-access roles to `admin` accounts, because active admins receive the covered protected-service access automatically under `FR-003`. | User validation, 2026-05-07; [Feature requirements review - D-005 and D-007](./docs/requirements/feature-requirements-review.md#decision-log) |
| FR-005 | Active `member` accounts must be allowed to access a protected backend service only when at least one assigned service-access role covers that service. Members must not receive protected-service access from their account type alone. | User validation, 2026-05-07; [Feature requirements review - D-006](./docs/requirements/feature-requirements-review.md#decision-log) |
| FR-006 | The system must serve backoffice users only. Public signup, public customer accounts, social login, and consumer identity flows are out of scope. | [README - Initial Scope](./README.md#initial-scope), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-007 | Backoffice accounts must be created only through authorized administrative workflows. There must be no public or self-service account registration. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-008 | Super-admins must be able to create `admin` and `member` accounts. Admins must be able to create only `member` accounts. Initial provisioning of the first `super-admin` account is a separate bootstrap concern and must not be treated as a normal backoffice self-service workflow. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-009 | Every backoffice account must have a stable internal identifier that is separate from mutable attributes such as email address, display name, or profile data. Lifecycle state, role assignments, access decisions, and audit records must reference this stable identifier. | [README - Core Features](./README.md#core-features), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-010 | The access-control capability must link each backoffice account to a stable authenticated subject from the identity provider or authentication system. It must consume authentication results, but must not own credentials, MFA, login sessions, or identity-provider account recovery. | [README - Core Features](./README.md#core-features), [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html), user validation, 2026-05-07 |
| FR-011 | Backoffice accounts must support at least these lifecycle states: `invited`, `active`, `disabled`, and `archived`. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-012 | New backoffice accounts must start in `invited` state and become `active` only after the invited user completes the required first authentication or onboarding step. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-013 | Authorized account managers must be able to disable an `active` account, restore a `disabled` account to `active`, and archive a `disabled` account. An `archived` account must not be restored in the initial policy. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-014 | Backoffice account records must be retained rather than hard-deleted in the initial policy, including archived accounts. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-015 | `invited`, `disabled`, and `archived` accounts must not obtain new protected backend service access. Protected-service access requires the account to be `active`. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-016 | The system must define, document, and evaluate how already-issued protected-service access stops after account disablement, account archival, or member service-access role removal. The final mechanism and acceptable delay may be decided later during architecture evaluation. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), [Project governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), user validation, 2026-05-07 |
| FR-017 | Admins must be able to list, create, read, update profile data, disable, archive, and restore `member` accounts where lifecycle policy allows. Admins must not manage `admin` or `super-admin` accounts. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-018 | Super-admins must be able to list, create, read, update profile data, disable, archive, and restore `admin` and `member` accounts where lifecycle policy allows. | [README - Actors and Role Types](./README.md#actors-and-role-types), user validation, 2026-05-07 |
| FR-019 | Members must be able to view their own profile information in read-only mode. Members must not update their own profile data, assign roles, manage accounts, or consult audit records. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-020 | Protected backend services must enforce authorization server-side. A protected service must grant access only when it can determine that the backoffice account is `active` and allowed by the account type or assigned service-access role rules. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), user validation, 2026-05-07 |
| FR-021 | Protected backend services must deny access when the account is not `active`, has no applicable access rule, or the service cannot safely determine the authorization result. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), user validation, 2026-05-07 |
| FR-022 | Each service-access role must explicitly identify the protected backend service access it covers, so access decisions can be evaluated consistently by the system and protected services. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-023 | The minimal member service-access role must provide consultation-style access only. More granular or stronger permissions may be added later only when a real protected-service need justifies them. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-024 | The system must provide a controlled administration capability for account management, service-access-role catalog management, service-access-role assignment and removal, protected-service access checks, and audit-supporting operations. This requirement does not choose whether the capability is implemented as a UI, API, product feature, or other technical form. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), [Project governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), user validation, 2026-05-07 |
| FR-025 | Recovery and login reset must be own-account responsibilities for `member` and `admin` accounts. Admins must not recover or reset `member`, other `admin`, or `super-admin` accounts. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-026 | The system must prevent privilege escalation paths that change account type, let an account grant itself broader management responsibility, or bypass auditability for privileged actions. | [README - Actors and Role Types](./README.md#actors-and-role-types), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-027 | Audit events must cover account creation, profile update, disablement, archival, restoration, service-access-role creation, service-access-role assignment, service-access-role removal, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or login reset actions. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-028 | Super-admins must be able to consult audit records. Audit reads and exports must themselves create audit events. Admins and members must not consult audit records. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-029 | The target security posture must be production-grade internal access control. Simpler authentication or access-control shortcuts may be used only as non-production or transitional constraints, and their risks and hardening path must be documented during the study. | [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), [Project governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing), user validation, 2026-05-07 |
| FR-030 | The system must remain understandable and operable by the internal team at the expected scale. Added operational or architectural complexity must be justified by concrete security, compliance, maintainability, or product needs. | [README - Project Goal](./README.md#project-goal), [Feature requirements review - coverage](./docs/requirements/feature-requirements-review.md#coverage-review), user validation, 2026-05-07 |
| FR-031 | Once a backoffice account has left `invited` state, it must not be moved back to `invited`. | User validation, 2026-05-07; [Feature requirements review - OQ-005](./docs/requirements/feature-requirements-review.md#open-questions) |
| FR-032 | Super-admins must be able to create, list, update, disable, and archive service-access roles. Service-access roles must not be hard-deleted in the initial policy. | User validation, 2026-05-07; [Feature requirements review - OQ-006](./docs/requirements/feature-requirements-review.md#open-questions) |
| FR-033 | All admin and super-admin operations must be authorized server-side according to the acting account type, lifecycle state, and permitted management scope. The system must not rely on frontend-only checks for administrative authorization. | [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), user validation, 2026-05-07; [Feature requirements review - OQ-007](./docs/requirements/feature-requirements-review.md#open-questions) |
| FR-034 | Production `admin` and `super-admin` authentication must require MFA or phishing-resistant passwordless authentication. The exact authenticator method and fallback policy may be selected later during security and architecture evaluation. | [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html), user validation, 2026-05-07; [Feature requirements review - OQ-008](./docs/requirements/feature-requirements-review.md#open-questions) |
| FR-035 | Audit records must be append-only and retained indefinitely in the initial policy. Any later retention, privacy, or deletion policy change must be explicitly reviewed before adoption. | User validation, 2026-05-07; [Feature requirements review - OQ-009](./docs/requirements/feature-requirements-review.md#open-questions) |

## Out of Scope

- Public signup, public customer accounts, social login, and external consumer identity flows are out of scope for this capability ([README - Initial Scope](./README.md#initial-scope)).
- A complete company-wide workforce IAM replacement is out of scope for the initial specification ([README - Initial Scope](./README.md#initial-scope)).
- Final vendor, product, architecture, hosting, database, implementation-stack, access-token format, and browser token storage decisions are out of scope for this feature requirements list and remain study/evaluation topics ([README - Initial Scope](./README.md#initial-scope), [Project governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).
- Production high availability or multi-replica operation is not a minimum initial feature requirement ([README - Initial Scope](./README.md#initial-scope)).
- A complete custom cryptographic or IAM implementation is out of scope ([README - Initial Scope](./README.md#initial-scope)).
- Application code, dependencies, package managers, Docker files, databases, migrations, CI files, generated artifacts, and deployment files are out of scope unless the project explicitly moves to a Proof of Concept or implementation phase ([AGENTS - Current Operating Phase](./AGENTS.md#current-operating-phase), [Project governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)).
- Break-glass access is out of scope for the current consolidated feature list until explicitly reopened and reviewed ([README - Open Study Questions](./README.md#phase-2-debate-topics), [Feature requirements review - OQ-010](./docs/requirements/feature-requirements-review.md#open-questions)).

## References

- [README - Actors and Role Types](./README.md#actors-and-role-types)
- [README - Initial Scope](./README.md#initial-scope)
- [README - Feature Requirements Source](./README.md#minimum-feature-requirements)
- [README - Open Study Questions](./README.md#phase-2-debate-topics)
- [AGENTS - Current Operating Phase](./AGENTS.md#current-operating-phase)
- [NIST SP 800-63B - Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Project Governance - Phase 2](./PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [Feature Requirements Review](./docs/requirements/feature-requirements-review.md)
- [NIST Role Based Access Control](https://csrc.nist.gov/projects/role-based-access-control)
