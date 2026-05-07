# EDRLab Backoffice Access Control Study

This repository contains a study for the EDRLab backoffice access-control capability.

> https://www.notion.so/edrlab/Member-s-back-office-2eca1ca5712f806b9594dd987b5af9e1

The study objective is to define, compare, and eventually recommend the simplest secure way for  the company to authenticate backoffice members, manage their access, and protect company controlled backend services.

The expected outcome is not a production-ready system. The expected outcome is a documented, evidence-based recommendation supported by requirements analysis, comparison documents, and minimal non-production Proofs of Concept where needed.

No final product, vendor, architecture, hosting model, database, framework, token strategy, or implementation stack is selected in this specification. Those choices must be debated progressively during Phase 2 and later decision phases.

## Immutable Feature Specification

This section is the initial immutable feature specification for the study. It records company needs, not a solution design. It may be changed only by an explicit stakeholder request to change the feature specification itself.

Phase 2 study documents may refine interpretations, risks, evaluation criteria, and implementation options, but they must not silently change these feature requirements.

## Company Goal

The company needs a simple, secure, auditable way to manage access for internal backoffice users.

The system serves internal company users only. It does not serve public customers, public self-service accounts, social login users, or external consumer identity flows.

Protected access is centered on company-controlled backend services. Access to those services is granted by administrators through roles.

The expected scale is fewer than 1,000 internal users. Operational complexity must be justified by concrete security, compliance, maintainability, or product needs.

## Actors

| Actor | Minimum responsibility |
| --- | --- |
| Super-admin | Highest privilege operator. Can review audit records, manage administrator recovery or reset decisions, and own any future emergency or break-glass process if one is adopted. |
| Admin | Manages members, roles, role assignments, service access, and member profile data. Admin actions must be logged and auditable. |
| Member | Internal company user who can view their own profile and access protected backend services only when active and authorized by role. |

Privilege escalation must be controlled. An admin must not be able to silently grant themselves super-admin privileges or bypass auditability for privileged actions.

## Minimum Feature Requirements

| ID | Requirement |
| --- | --- |
| FS-001 | The system must support internal backoffice users only. Public signup, public customer accounts, and social login are out of scope for the initial specification. |
| FS-002 | Members must be created and managed by administrators only. There is no public self-service registration. |
| FS-003 | Member records must use stable identifiers that are separate from mutable attributes such as email, name. |
| FS-004 | The member lifecycle must support at least `invited`, `active`, `disabled`, and `archived` states. Members are retained rather than hard-deleted in the initial policy. |
| FS-005 | Non-active members must not be able to obtain new access to protected backoffice services. Access removal for already-issued access must be simple, documented, and evaluated during the study. |
| FS-006 | Administrators must be able to create, read, update, list, disable, archive, restore where policy allows, and remove access for members. |
| FS-007 | Administrators must be able to create roles, list roles, assign roles to members, and remove roles from members. |
| FS-008 | The minimum authorization model is role-based service access: a member either can or cannot access a protected backend service through an assigned role. |
| FS-009 | The minimal member role must allow consultation-style access only. More precise permissions may be debated later if real service needs require them. |
| FS-010 | The system must provide an administration capability for member management, role management, role assignment, service access checks, and audit-supporting operations. |
| FS-011 | Protected backend services must be able to determine whether a given active member is allowed to access the service. |
| FS-012 | Only administrators may change member profile attributes and service access assignments. Members may view their own profile information. |
| FS-013 | Super-admin, admin, and member responsibilities must remain separated. Recovery, authenticator reset, administrator recovery, audit access, and any future break-glass process belong to the super-admin responsibility. |
| FS-014 | The security posture must target production-grade internal access control. The first minimal version may use simpler authentication, but Phase 2 must evaluate the risks and the path toward stronger production controls. |
| FS-015 | Audit events must cover member creation, member update, member disablement, member restoration, role assignment, role removal, role changes, protected-service access configuration changes, protected-service authorization denials, audit reads or exports, and recovery or authenticator reset actions. |
| FS-016 | Super-admins must be able to consult audit records. Audit access itself must be logged. |
| FS-017 | The system must remain understandable and operable by the internal team. Simplicity is a requirement, not merely an implementation preference. |

## Initial Scope

In scope for the study:

- internal member lifecycle management;
- administrator-only account and role management;
- role-based access to protected backend services;
- service access checks for backend services;
- auditability of privileged and security-relevant operations;
- threat modeling and security requirement refinement;
- comparison of managed, self-hosted, minimal internal, and hybrid approaches;
- minimal non-production Proofs of Concept when documentation alone cannot answer a material question.

Out of scope for the initial immutable specification:

- public account registration;
- public customer identity;
- social login;
- consumer marketing account flows;
- a complete company-wide workforce IAM replacement;
- a final vendor, product, architecture, hosting, database, or implementation-stack decision;
- production high availability or multi-replica operation as a minimum initial requirement;
- a complete custom cryptographic or IAM implementation.

## Phase 2 Debate Topics

These topics are not settled by the immutable feature specification and must be debated during Phase 2 or later:

- whether the eventual solution should be a simple internal authentication system, SSO integration, an IAM control plane, a managed provider, a self-hosted product, a minimal internal build, or a hybrid approach;
- whether production administrators require MFA, step-up authentication, passwordless login, hardware-backed authenticators, or fallback authenticators;
- whether high-risk operations require recent authentication freshness;
- whether production needs break-glass access, who can activate it, and how it is reviewed;
- acceptable access lifetime, refresh behavior, revocation delay, and token or session storage strategy;
- exact token format and validation model;
- audit retention, privacy, export, and compliance expectations;
- backup, recovery, restore-test, upgrade, and operational ownership expectations;
- the exact demo permissions and protected services used by a future Proof of Concept.

## Roadmap

1. Phase 1 - Conceptual IAM Foundation.
2. Phase 2 - Requirements and Risk Framing.
3. Phase 3 - Candidate Approach Catalog.
4. Phase 4 - Evidence-Based Candidate Evaluation.
5. Phase 5 - Proposed Target Solution Draft.
6. Phase 6 - Adoption and Production-Readiness Review.
7. Phase 7 - Produce a final evidence-based technical recommendation.
8. Phase 8 - Optional Non-Production MVP.

## Documentation

- [Abstract](./ABSTRACT.md)
- [Project governance](./PROJECT-GOVERNANCE.md)
- [Changelog](./CHANGELOG.md)
- [Agent instructions](./AGENTS.md)
- [Project study documentation map](./docs/README.md)
- [Conceptual IAM wiki](./docs/wiki/README.md)

## References

- [The bottleneck was never the code](https://www.thetypicalset.com/blog/thoughts-on-coding-agents)