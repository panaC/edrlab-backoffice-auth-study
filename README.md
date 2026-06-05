# EDRLab Backoffice Access-Control Study

This repository is the study space for the EDRLab backoffice access-control solution. It defines the project scope, captures the consolidated feature requirements, frames security and operational risks, compares candidate approaches, and prepares an evidence-based technical recommendation.

> https://www.notion.so/edrlab/Member-s-back-office-2eca1ca5712f806b9594dd987b5af9e1

## Core Features

The project is organized around the following essential capabilities:

- Manage backoffice accounts, lifecycle states, and stable account identifiers.
- Authenticate backoffice users through an identity provider while keeping access-control decisions in the backoffice capability.
- Keep fixed account types separate from independently managed service-access roles.
- Authorize protected backend services from account state, account type, and member service-access role assignments.
- Audit privileged and security-relevant actions.

```mermaid
flowchart LR
  Member["Member"] --> IdP["Identity provider"]
  Admin["Admin / Super-admin"] --> IdP

  IdP --> AC["Access-control"]

  Admin --> AdminOps["Account and role management"]
  AdminOps --> AC

  AC --> Roles["Service-access roles"]
  AC --> Audit["Audit records"]
  AC --> Services["Protected backend services"]
```

## Project Goal

The project goal is to define a simple, secure, and auditable access-control model for selected EDRLab backoffice users.

The model must support account lifecycle management, identity-provider authentication, protected backend service authorization, and auditability without expanding into public customer identity or a company-wide IAM replacement.

The project keeps two concepts separate:

- account types define backoffice responsibilities: `super-admin`, `admin`, and `member`;
- service-access roles describe protected backend service access for admins and super-admins automatically and for members through assignment.

The expected scale is fewer than 1,000 users. Operational complexity must be justified by concrete security, compliance, maintainability, or product needs.

## Actors and Role Types

The account types are application account categories in the company system, not only study labels. `super-admin`, `admin`, and `member` accounts are separated account types. An account type is fixed when the account is created and cannot be changed later. A `member` account must never become an `admin` account.

Service-access roles are separate from account types. They are managed by super-admins and assigned to `member` accounts by admins or super-admins. Active admins automatically receive access to every protected backend service covered by any service-access role, and active super-admins receive the same access through inherited admin capabilities. A service-access role must not grant account-management responsibilities.

A `super-admin` is a high-level administration superset of `admin`: it inherits every admin capability and adds high-level administration capabilities. An `admin` does not inherit super-admin capabilities, and the admin limits below apply to admin accounts only.

### Super-admin

High-level management account.

- Inherits every `admin` capability.
- Can manage `admin` accounts where lifecycle policy allows.
- Can manage the service-access-role catalog.
- Can consult audit records.

### Admin

Operational management account for `member` accounts.

- Can manage `member` accounts where lifecycle policy allows.
- Automatically receives access to every protected backend service covered by any service-access role.
- Can assign or remove service-access roles for `member` accounts.
- Cannot manage `admin` or `super-admin` accounts.
- Cannot create service-access roles or consult audit records.

### Member

Internal company user account.

- Can view their own profile in read-only mode.
- Can access protected backend services only when active and authorized by assigned service-access roles.
- Cannot modify their own profile, manage accounts, create or assign service-access roles, or consult audit records.

Privilege escalation must be controlled. An account type must not be changed, merged, or elevated after account creation. An admin must not be able to grant themselves a super-admin account type, create service-access roles, assign service-access roles to privileged account types, or bypass auditability for privileged actions.

<a id="minimum-feature-requirements"></a>

## Feature Requirements Source

The former `Minimum Feature Requirements` (`FS-*`) table has been retired. The single feature-requirements source for the access-control capability is [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md).

This README summarizes the project purpose, actor model, scope, roadmap, and documentation entry points. Concrete requirement changes should be made in `FEATURE-REQUIREMENTS.md` and recorded in [CHANGELOG.md](./CHANGELOG.md).

## Initial Scope

In scope for the study:

- backoffice account lifecycle and profile-management boundaries for `super-admin`, `admin`, and `member` accounts;
- identity-provider authentication boundary and stable authenticated-subject linkage;
- service-access-role catalog management, member role assignment and removal, and protected backend service access decisions;
- auditability of privileged and security-relevant operations;
- Phase 2 requirements and risk framing, Phase 3 solution choice, Phase 4 targeted non-production Proof of Concept, and Phase 5 review and decision.

Out of scope for the initial specification:

- public signup, public customer identity, social login, and consumer marketing account flows;
- a complete company-wide workforce IAM replacement;
- final vendor, product, architecture, hosting, database, implementation-stack, token-format, session, or browser-storage decisions;
- production high availability or multi-replica operation as a minimum initial requirement;
- a complete custom cryptographic or IAM implementation.

<a id="phase-2-debate-topics"></a>

## Open Study Questions

These topics remain open for Phase 4 or later study. They are not feature requirements until explicitly adopted in [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md).

- Solution validation: self-hosted Keycloak with local access control has been selected for validation in [ADR 0001](./docs/decisions/0001-choose-keycloak-for-validation.md); production adoption remains open until PoC evidence and review.
- Privileged account protection: MFA, step-up authentication, passwordless login, hardware-backed authenticators, fallback authenticators, super-admin provisioning, super-admin recovery, and break-glass.
- Access evidence and revocation: acceptable access lifetime, refresh behavior, revocation delay, token or session strategy, validation model, and browser storage.
- Audit and operations: audit retention, privacy, export, compliance expectations, backup, recovery, restore testing, upgrades, and operational ownership.
- Proof of Concept scope: exact demo permissions and protected services to exercise.

## Roadmap

1. Phase 1 - Conceptual IAM Foundation.
2. Phase 2 - Requirements and Risk Framing.
3. Phase 3 - Solution Choice.
4. Phase 4 - Proof of Concept.
5. Phase 5 - Review and Decision.
6. Phase 6 - Production MVP.

## Documentation

| Need | Entry point |
| --- | --- |
| Project summary | [Abstract](./ABSTRACT.md) |
| Consolidated feature requirements | [Feature requirements](./FEATURE-REQUIREMENTS.md) |
| Phase boundaries and study rules | [Project governance](./PROJECT-GOVERNANCE.md) |
| Project study documents | [Documentation map](./docs/README.md) |
| General IAM concepts and references | [Conceptual IAM wiki](./docs/wiki/README.md) |
| Project history | [Changelog](./CHANGELOG.md) |
| Agent working instructions | [Agent instructions](./AGENTS.md) |
