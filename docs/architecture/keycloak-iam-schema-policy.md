# Keycloak IAM Schema Policy

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Architecture
Last reviewed: 2026-06-29

## Contents

- [Purpose](#purpose)
- [Accepted Policy](#accepted-policy)
- [Managed User Attributes](#managed-user-attributes)
- [Roles](#roles)
- [Edit Permissions](#edit-permissions)
- [Invariant Checks](#invariant-checks)
- [Migration Policy](#migration-policy)
- [Token and Claim Boundary](#token-and-claim-boundary)
- [References](#references)

## Purpose

This document defines the accepted Keycloak IAM schema policy for the MVP: managed attributes, role representation, edit permissions, drift handling, and migration rules. It turns the `WP-010` mapping and the `WP-011` through `WP-016` runtime findings into a Phase 6 architecture constraint ([Keycloak WP-010 result](../poc/keycloak-wp010-result.md), [runtime result](../poc/keycloak-wp011-016-runtime-result.md#surprises), [MVP scope](../evaluation/mvp-scope.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The policy keeps Keycloak as the IAM-state holder for the accepted architecture, but only through the EDRLab IAM Control Plane API. Direct Keycloak Admin Console or Admin REST mutations of EDRLab business IAM state remain drift unless they are explicitly tied to an approved control-plane technical actor and local EDRLab audit evidence (`FR-026`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-015 result](../poc/keycloak-wp015-result.md)).

## Accepted Policy

| Topic | MVP policy |
| --- | --- |
| Unmanaged attributes | Disabled. Production IAM state must not depend on unmanaged Keycloak attributes. |
| Managed attributes | Every EDRLab IAM user attribute is declared in the Keycloak User Profile schema. |
| Account type | Exactly one client role on the configured backoffice client, default `backoffice`: `account-type-member`, `account-type-admin`, or `account-type-super-admin`. |
| Service-access roles | Client roles on the protected-service client. The first MVP role is client `access-check-demo-service`, role `consult`, exposed by the IAM Control Plane API as `access-check-demo:consult`. |
| Role lifecycle metadata | Schema-controlled role metadata marks service-access roles as `active`, `disabled`, or `archived`; disabled or archived roles do not authorize access. |
| Edit path | Routine writes happen only through the IAM Control Plane API. Human Keycloak admin edits of business IAM state are not normal administration. |
| Direct admin mutation | Treat as drift, deny or quarantine sensitive operations, and audit the detection. |
| Migration | Dry-run first, report discrepancies, migrate only valid states, and block or quarantine invalid states rather than silently repairing them. |
| Token roles | Allowed only as UI hints or diagnostics; protected services must not authorize from raw token roles or claims. |

Keycloak documents that its User Profile can distinguish managed and unmanaged attributes, and that unmanaged attributes are disabled by default unless configured otherwise. It also recommends using strict attribute policies where possible ([Keycloak User Profile - managed and unmanaged attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)). This MVP adopts that strict posture.

## Managed User Attributes

The MVP Keycloak User Profile must declare these custom EDRLab attributes:

| Attribute | Required for | Write rule | Validation |
| --- | --- | --- | --- |
| `iam.account_id` | Stable internal account identifier. | Written once at account creation or first-super-admin bootstrap; immutable afterwards. | Required, unique, opaque string. |
| `iam.lifecycle` | Backoffice lifecycle state. | Written only through authorized lifecycle operations. | Enum: `invited`, `active`, `disabled`, `archived`. |
| `iam.linked_subject` | Immutable subject link created during safe onboarding. | Empty before activation; written only by onboarding activation; immutable afterwards. | Empty or exactly the resolved Keycloak subject for the account. |
| `iam.organization` | Required account profile field. | Written only through authorized account creation or profile update. | Non-empty string in MVP account creation. |
| `iam.assigned_service_roles` | Canonical member service-role assignments. | Written only by the IAM Control Plane API when member service-access roles are assigned, removed, or otherwise persisted. | JSON array of service-access role IDs. For `member` accounts, authorization uses this managed attribute rather than Keycloak user role mappings; any protected-service client-role mapping directly assigned to a user is treated as direct-admin drift (`FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| `iam.schema_version` | Schema evolution marker. | Written by bootstrap, migration, or IAM Control Plane API mutation. | Current MVP value: `iam-schema-v1`. |
| `iam.last_control_plane_mutation_at` | Drift and reconciliation support. | Written by the IAM Control Plane API after accepted mutations. | Server timestamp; advisory, not sole proof of authorization. |

The standard Keycloak profile fields `email`, `firstName`, and `lastName` continue to hold the MVP `email` and `name` data, while `iam.organization` covers the required organization field. Mutable profile data must not be used as stable authorization identity; account state, lifecycle, audit, and access decisions use `iam.account_id` (`FR-009`, `FR-040`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

Keycloak Admin REST exposes user profile data through `UserRepresentation`, including `email`, `firstName`, `lastName`, `enabled`, and an `attributes` map, which is the product surface used by the control plane for this schema ([Keycloak Admin REST - UserRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#UserRepresentation)).

## Roles

### Account Type Roles

Account type uses one dedicated client:

| Keycloak client | Role | Project account type |
| --- | --- | --- |
| configured backoffice client, default `backoffice` | `account-type-member` | `member` |
| configured backoffice client, default `backoffice` | `account-type-admin` | `admin` |
| configured backoffice client, default `backoffice` | `account-type-super-admin` | `super-admin` |

Rules:

- exactly one account-type role is required for every backoffice account;
- account type is assigned at account creation or bootstrap only;
- account type is never changed, merged, elevated, or represented by groups in the MVP;
- composite roles are not used for account type in the MVP.

If an account has zero or multiple account-type roles, the IAM Control Plane API treats the state as an invariant violation and fails closed. This preserves fixed account types and privilege-escalation prevention (`FR-001`, `FR-026`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Service-Access Roles

Service-access roles use client roles on protected-service clients. For the first MVP service:

| Project service role ID | Keycloak client | Keycloak role | Status |
| --- | --- | --- | --- |
| `access-check-demo:consult` | `access-check-demo-service` | `consult` | `active` |

Future protected services follow the same pattern: one protected-service client owns the client roles that apply to that service. A service role grants protected-service access only; it must not grant account-management power.

Service-role lifecycle is represented as schema-controlled role metadata with at least:

| Role metadata | Values |
| --- | --- |
| `iam.role_status` | `active`, `disabled`, `archived` |
| `iam.schema_version` | `iam-schema-v1` |
| `iam.last_control_plane_mutation_at` | server timestamp |

Keycloak Admin REST supports client-level roles and `RoleRepresentation` includes role attributes, so the MVP can carry schema-controlled role metadata with the Keycloak role object ([Keycloak Admin REST - client roles](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Keycloak Admin REST - RoleRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#RoleRepresentation)). Disabled or archived service roles cannot be assigned and cannot authorize protected-service access (`FR-032`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Edit Permissions

The routine writer for EDRLab IAM schema state is the IAM Control Plane API technical actor. End users must not edit EDRLab IAM attributes, account-type roles, service-access roles, role metadata, or subject-link state.

Human Keycloak administrators may inspect technical state where operationally necessary, but routine business changes must go through the EDRLab Admin Console and IAM Control Plane API. Keycloak supports realm-management roles and fine-grained administration, but it warns that server administrators and realm administrators are not affected by fine-grained realm-resource permissions, so broad `admin` or `realm-admin` grants remain a privilege-escalation and drift risk ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)).

MVP edit policy:

| Surface | Allowed routine access |
| --- | --- |
| End-user account UI | No edit of EDRLab IAM attributes or roles. |
| EDRLab Admin Console | Business operations only through the IAM Control Plane API. |
| IAM Control Plane API service account | Approved writer for managed attributes, role assignments, service-role metadata, and Keycloak `enabled` state. |
| Keycloak Admin Console | Technical inspection and break-glass only; routine business mutation is drift. |
| Direct Keycloak Admin REST | IAM Control Plane API technical actor only, except explicit technical setup, migration, or break-glass procedures. |

If Keycloak user-profile attribute permissions cannot fully separate human admin read-only inspection from IAM Control Plane API writes, Phase 6 must compensate with restricted admin grants, break-glass procedure, reconciliation, and drift detection. Keycloak's User Profile schema exposes attribute permission concepts for view and edit, but the project still needs an operational role model for human and technical administrators ([Keycloak Admin REST - UPAttributePermissions](https://www.keycloak.org/docs-api/latest/rest-api/index.html#UPAttributePermissions)).

## Invariant Checks

The IAM Control Plane API must check the current Keycloak state before every sensitive admin operation, `GET /iam/me/services`, and `POST /iam/authorization/check`.

Minimum invariant checks:

- `iam.account_id` exists, is unique, and has not changed;
- `iam.lifecycle` is one of `invited`, `active`, `disabled`, or `archived`;
- Keycloak `enabled=false` for `disabled` and `archived`, and `enabled=true` for `invited` and `active`;
- `iam.linked_subject` is empty before activation and immutable after activation;
- exactly one account-type role exists on the configured backoffice client;
- service-access roles are assigned only to `member` accounts;
- no user has direct protected-service client-role mappings; member service-role assignments are read from `iam.assigned_service_roles`;
- assigned service-access roles exist and are `active`;
- role metadata schema version is recognized;
- `iam.last_control_plane_mutation_at` and local audit/correlation evidence are consistent enough for the operation being evaluated.

Known invalid state returns deny or blocks the operation. Unreadable, incomplete, or incoherent state returns indeterminate `503` for authorization checks and blocks sensitive admin operations, following the accepted authorization-check behavior ([Authorization Check Behavior](./authorization-check-behavior.md)).

## Migration Policy

Migration from PoC or manually prepared Keycloak state to the MVP schema is strict:

1. Back up or export the relevant Keycloak realm and collect a current inventory before mutation.
2. Run a dry-run migration that validates users, account-type roles, service roles, role metadata, lifecycle values, subject links, and unmanaged attributes.
3. Produce a human-readable migration report listing valid records, invalid records, proposed mutations, and blocked records.
4. Convert only valid records to the managed schema.
5. Disable unmanaged attributes after migration validation.
6. Do not auto-repair privilege, account-type, subject-link, lifecycle, or service-role inconsistencies silently.
7. Record migration execution and rejected records in local EDRLab audit.

Invalid records are migration blockers. The migration may keep them out of the MVP, keep them inactive, or quarantine them for manual review, but it must not create active access from inconsistent state. A temporary `migration_blocked` lifecycle value is not part of the MVP lifecycle; if a state must be represented in Keycloak before correction, use non-active access behavior and the migration report rather than expanding the lifecycle enum.

Unmanaged `iam.*` attributes found during migration are either mapped to declared managed attributes through an explicit migration rule or rejected. They must not survive as free-form business IAM state.

## Token and Claim Boundary

Account-type roles and service-access roles may appear in Keycloak tokens only as display hints, diagnostics, or integration evidence. They are not the final authorization authority for protected backend services.

Protected backend services must call `POST /iam/authorization/check`. The IAM Control Plane API reads current Keycloak state, applies invariant checks, handles drift, and returns the decision. This preserves the anti-bypass rule that frontend state, raw token claims, and protected-service local guesses do not decide business access (`FR-020`, `FR-021`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [IAM Control Plane API Contract - Authorization](./iam-control-plane-api-contract.md#authorization)).

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [MVP Scope - Access-Control Production MVP](../evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](./iam-control-plane-api-contract.md)
- [Authorization Check Behavior](./authorization-check-behavior.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [Keycloak WP-010 Result - IAM Mapping Design](../poc/keycloak-wp010-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](../poc/keycloak-wp015-result.md)
- [Keycloak WP-011 Through WP-016 Runtime Result](../poc/keycloak-wp011-016-runtime-result.md)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak User Profile - Managed and Unmanaged Attributes](https://www.keycloak.org/docs/latest/server_admin/#understanding-managed-and-unmanaged-attributes)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
