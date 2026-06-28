# MVP Scope - Keycloak IAM Control Plane API

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Evaluation
Last reviewed: 2026-06-28

## Contents

- [Purpose](#purpose)
- [Executive Summary](#executive-summary)
- [MVP Boundary](#mvp-boundary)
- [Current MVP State](#current-mvp-state)
- [Included Capabilities](#included-capabilities)
- [Out of Scope](#out-of-scope)
- [Production Readiness Gaps](#production-readiness-gaps)
- [Source of Truth Map](#source-of-truth-map)
- [References](#references)

## Purpose

This document is the short scope and status page for the accepted Keycloak IAM plus EDRLab IAM Control Plane API MVP. It states what belongs in the MVP, what is explicitly outside it, what is already represented by the Phase 6 runtime, and which items still block production trust ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

It is a scope summary, not the detailed API contract, runtime runbook, security test plan, Keycloak schema policy, or audit-storage specification. Those details remain in the linked source documents listed in [Source of Truth Map](#source-of-truth-map).

## Executive Summary

The MVP is authorized for `Phase 6 - Production MVP` inside the boundary accepted by ADR 0005: self-hosted Keycloak, an EDRLab IAM Control Plane API, the first synthetic protected service `access-check-demo-service`, the first service role `access-check-demo:consult`, local append-only audit storage, and executable MVP security evidence ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)).

The MVP covers the minimum access-control loop from the feature requirements: controlled backoffice account creation, safe onboarding activation, immutable account types, service-access-role assignment, server-side protected-service authorization, fail-closed denials, and local business audit ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [README - Core Features](../../README.md#core-features)).

The Phase 6 runtime slice already provides Dockerized Keycloak, an IAM API, the demo protected service, append-only JSONL audit storage, first-`super-admin` bootstrap, Linux scripts, Docker tests, and a Keycloak smoke verification path. It is still documented as an early Phase 6 runtime and does not yet include the Admin Console UI, full Keycloak IAM schema migration, or production operations hardening ([Access-Control MVP Runtime](../../access-control/README.md#purpose), [Access-Control MVP Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts)).

Production readiness still requires concrete operations evidence before production data is trusted, including Keycloak ownership by `super-admin`, backup/restore evidence, secrets handling, monitoring, incident handling, rollback notes, and completion of the accepted security-test gate ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision), [MVP Security Test Plan](./security-test-plan.md#acceptance-criteria)).

## MVP Boundary

| Area | In the MVP | Detailed source |
| --- | --- | --- |
| Architecture boundary | Self-hosted Keycloak stores the accepted IAM state, while EDRLab business administration and authorization checks go through the Admin Console and IAM Control Plane API. | [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md) |
| IAM API | REST API under `/iam` for self-profile, accounts, onboarding, service roles, assignments, `authorization/check`, and audit reads. | [IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md#endpoints) |
| Account model | Backoffice accounts use fixed account types `super-admin`, `admin`, and `member`; account types are not mutable after creation. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Onboarding | Invited accounts activate only through safe bearer-token-derived onboarding evidence; privileged accounts also require accepted privileged-authentication evidence. | [Feature requirements `FR-043` and `FR-044`](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Access-Control MVP Runtime - Onboarding Activation](../../access-control/README.md#onboarding-activation) |
| First protected service | The first protected service is `access-check-demo-service`, a synthetic service that verifies the current user's access and returns JSON `OK` or `KO`. | [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision), [IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md#authorization) |
| First service role | The first service-access role is `access-check-demo:consult`; member service access is consultation-style only. | [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision), [Feature requirements `FR-023`](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Authorization behavior | Protected services call `POST /iam/authorization/check`; the path has accepted timeout, retry, cache, fail-closed, access-stop, audit, and metrics behavior. | [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md) |
| Audit | Local EDRLab audit is durable, file-backed, append-only, one JSON event object per physical line, with super-admin API consultation and no initial export. | [Audit Storage Policy](../architecture/audit-storage.md) |
| Keycloak schema | The MVP uses managed Keycloak User Profile attributes, disables unmanaged attributes, uses account-type and service-access client roles, and treats unmanaged business mutation as drift. | [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md) |
| Security evidence | The MVP security gate covers frontend-bypass rejection, raw-claim rejection, token validation, subject-link immutability, fail-closed behavior, drift denial, and audit evidence. | [MVP Security Test Plan](./security-test-plan.md) |

## Current MVP State

| Item | State | Notes |
| --- | --- | --- |
| Scope authorization | Done | ADR 0005 authorizes Phase 6 production MVP implementation only inside the accepted MVP boundary ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Runtime slice | In place | The `access-control/` runtime includes Docker Compose, Keycloak, IAM API, demo service, bootstrap, audit storage, Linux scripts, Docker tests, and smoke verification ([Access-Control MVP Runtime](../../access-control/README.md#what-this-slice-includes)). |
| Keycloak-backed IAM state | In place for the runtime slice | The Docker runtime uses `IAM_STATE_BACKEND=keycloak`; account type, lifecycle, subject link, organization, schema marker, service-role metadata, and member role assignments are read from and written to Keycloak through the IAM Control Plane API ([Access-Control MVP Runtime - Run](../../access-control/README.md#run)). |
| IAM API contract | Accepted | Endpoint families, actors, authentication model, authorization rules, error contract, idempotence, and audit expectations are fixed in the API contract ([IAM Control Plane API contract](../architecture/iam-control-plane-api-contract.md)). |
| Security tests | Partially complete as runtime evidence | Docker-only tests exist for the runtime slice, while production readiness still depends on satisfying or explicitly accepting every test-plan gap before declaring the MVP production-ready ([Access-Control MVP Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes), [MVP Security Test Plan - Acceptance Criteria](./security-test-plan.md#acceptance-criteria)). |
| Admin Console UI | Not included yet | The runtime documentation explicitly states that the Admin Console UI is not included yet ([Access-Control MVP Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts)). |
| Full schema migration and drift workflow | Not complete | The runtime represents drift with invariant checks, while full migration reporting, reconciliation workflow, and production direct-admin governance remain outside the current slice ([Access-Control MVP Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts), [Keycloak IAM Schema Policy - Phase 6 Implementation Inputs](../architecture/keycloak-iam-schema-policy.md#phase-6-implementation-inputs)). |
| Operations hardening | Not complete | ADR 0005 requires concrete runbooks, backup/restore evidence, monitoring, secrets handling, incident handling, and rollback notes before production data is trusted ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision)). |

## Included Capabilities

### Account Management

The MVP includes controlled creation, listing, reading, profile update, disablement, restoration, and archival for `member` accounts by `admin`, and for `admin` and `member` accounts by `super-admin`, within the management scopes defined by the feature requirements and API contract ([Feature requirements `FR-017` and `FR-018`](../../FEATURE-REQUIREMENTS.md#feature-requirements), [IAM Control Plane API contract - Accounts](../architecture/iam-control-plane-api-contract.md#accounts)).

Accounts start as `invited`, require at least `email`, `organization`, `name`, and a stable internal account identifier, and are retained rather than hard-deleted in the initial policy ([Feature requirements `FR-009`, `FR-014`, and `FR-040`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Onboarding and Bootstrap

The MVP includes safe onboarding activation through `POST /iam/onboarding/activate`, where the IAM API derives identity evidence from the authenticated user's bearer token and activates only when the accepted match rules pass ([IAM Control Plane API contract - Onboarding](../architecture/iam-control-plane-api-contract.md#onboarding), [Access-Control MVP Runtime - Onboarding Activation](../../access-control/README.md#onboarding-activation)).

The first `super-admin` is handled by a controlled bootstrap process outside the public IAM API. The process is idempotent and audited, and it may seed the first `super-admin` only when no valid `super-admin` exists ([IAM Control Plane API contract - Bootstrap Process](../architecture/iam-control-plane-api-contract.md#bootstrap-process), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision)).

### Service-Access Roles

The MVP includes service-access-role listing for `admin` and `super-admin`, catalog mutation by `super-admin`, and assignment or removal of active service-access roles for `member` accounts only ([Feature requirements `FR-002`, `FR-003`, `FR-004`, and `FR-032`](../../FEATURE-REQUIREMENTS.md#feature-requirements), [IAM Control Plane API contract - Service-Access Roles](../architecture/iam-control-plane-api-contract.md#service-access-roles)).

Service-access roles must not be assigned to `admin` or `super-admin` accounts. Active `admin` accounts receive covered service access automatically, and active `super-admin` accounts receive that access through inherited admin capability ([Feature requirements `FR-002`, `FR-003`, and `FR-004`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Protected-Service Authorization

The MVP includes `access-check-demo-service` as the first protected-service integration. It calls `POST /iam/authorization/check` using service-to-service authentication and maps IAM decisions to `OK` or `KO` JSON responses ([IAM Control Plane API contract - Authorization](../architecture/iam-control-plane-api-contract.md#authorization), [Access-Control MVP Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes)).

Protected-service authorization is server-side and fail-closed. The accepted behavior defines timeout, retry, no positive cache, optional short deny cache, no indeterminate cache, next-check access stop, audit, and metrics expectations ([Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)).

### Audit and Security Evidence

The MVP includes local EDRLab business audit events for account lifecycle, onboarding, subject-link, role, authorization denial, audit-read, bootstrap, rejected privileged onboarding, and indeterminate dependency scenarios ([IAM Control Plane API contract - Audit](../architecture/iam-control-plane-api-contract.md#audit), [Audit Storage Policy](../architecture/audit-storage.md)).

The MVP includes an accepted security regression test plan. The production-readiness gate passes only when the required tests are implemented or explicitly deferred with accepted risk, and the implemented tests prove server-side rejection, no unauthorized mutation, fail-closed behavior, drift handling, and audit evidence ([MVP Security Test Plan - Acceptance Criteria](./security-test-plan.md#acceptance-criteria)).

## Out of Scope

| Out of scope for this MVP | Rationale |
| --- | --- |
| Public signup, public customer identity, social login, and consumer identity flows | The access-control capability is limited to backoffice users ([Feature requirements `FR-006`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Company-wide workforce IAM replacement | The repository scope excludes a full workforce IAM replacement ([README - Initial Scope](../../README.md#initial-scope)). |
| Member self-service beyond read-only own-profile consultation | Members cannot update their own profile, manage accounts, assign roles, or consult audit records ([Feature requirements `FR-019`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Account-type mutation, member-to-admin conversion, account merge, or subject-link rebinding | These actions violate fixed account type, privilege-escalation, and immutable subject-link requirements ([Feature requirements `FR-001`, `FR-026`, and `FR-039`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Hard deletion of accounts, service roles, or audit records | The initial policy retains accounts, forbids service-role hard deletion, and keeps audit append-only ([Feature requirements `FR-014`, `FR-032`, and `FR-035`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Routine business administration directly in Keycloak Admin Console | Business administration goes through the EDRLab Admin Console and IAM Control Plane API; unmanaged Keycloak mutation is drift ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)). |
| Real business protected-service integration | The first MVP protected service is the synthetic `access-check-demo-service`; real business protected services require explicit later scope and testing ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision)). |
| Fine-grained per-action permission matrix beyond consultation-style member access | The first member permission is consultation-style access; more granular permissions require a concrete protected-service need ([Feature requirements `FR-023` and `FR-030`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Audit export and advanced audit search/filtering | The MVP keeps audit consultation to chronological list and basic detail, with no initial export ([Audit Storage Policy](../architecture/audit-storage.md)). |
| WebAuthn/passkeys as a mandatory MVP prerequisite | OTP safeguards are accepted for the current MVP direction; WebAuthn/passkeys remain future hardening ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md)). |
| Production high availability and multi-replica Keycloak operation | High availability is outside the accepted MVP scope unless explicitly added later ([ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#consequences)). |

## Production Readiness Gaps

| Gap | Required before production trust | Source |
| --- | --- | --- |
| Admin Console UI | Build or integrate the business UI that uses the accepted IAM API rather than relying on direct Keycloak business administration. | [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [Access-Control MVP Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts) |
| Keycloak schema migration | Provide exact User Profile JSON, service-account grants, migration or bootstrap scripts, dry-run behavior, and drift reconciliation evidence. | [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision) |
| Operations evidence | Produce runbooks and evidence for backup/restore, secrets handling, monitoring, incident handling, rollback, and accountable Keycloak ownership by `super-admin`. | [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision) |
| OTP operational safeguards | Configure and verify the MVP OTP path, including required actions, recovery-code or reset posture, brute-force safeguards, and audit-relevant operations where the IAM boundary participates. | [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md#decision) |
| Security evidence closure | Run and retain the executable evidence required by the MVP security test plan, or explicitly defer any missing test with accepted Phase 6 risk. | [MVP Security Test Plan - Acceptance Criteria](./security-test-plan.md#acceptance-criteria), [Access-Control MVP Runtime - Evidence](../../access-control/README.md#evidence) |
| Runtime limitations review | Decide which early-runtime shortcuts are acceptable for the MVP, which must be removed, and which remain test-only or non-production-only. | [Access-Control MVP Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp) |

## Source of Truth Map

| Need | Source |
| --- | --- |
| Feature requirements and actor rules | [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md) |
| MVP authorization and accepted residual risks | [ADR 0005 - Authorize Phase 6 Production MVP](../decisions/0005-authorize-phase-6-production-mvp.md) |
| Accepted architecture direction | [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md) |
| IAM routes, actors, errors, idempotence, and audit contract | [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md) |
| `authorization/check` timeout, retry, cache, fail-closed, access-stop, audit, and metrics behavior | [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md) |
| Audit storage rules | [Audit Storage Policy](../architecture/audit-storage.md) |
| Keycloak state model and drift policy | [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md) |
| Security regression test gate | [MVP Security Test Plan](./security-test-plan.md) |
| Executable Phase 6 runtime and commands | [Access-Control MVP Runtime](../../access-control/README.md) |
| Phase boundaries | [Project Governance](../../PROJECT-GOVERNANCE.md) |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [README - Core Features](../../README.md#core-features)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [ADR 0005 - Authorize Phase 6 Production MVP](../decisions/0005-authorize-phase-6-production-mvp.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Runtime Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Policy](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
- [MVP Security Test Plan](./security-test-plan.md)
- [Access-Control MVP Runtime](../../access-control/README.md)
