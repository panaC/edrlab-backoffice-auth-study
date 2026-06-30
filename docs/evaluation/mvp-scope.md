# MVP Scope - Access-Control Production MVP

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Evaluation
Last reviewed: 2026-06-29

## Agent Brief

- Read this file first for the Phase 6 MVP boundary, exclusions, readiness gaps, and source map.
- This file is the current MVP authority; the current IAM API contract lives in the architecture docs.
- Runtime commands and evidence belong in the [access-control runbook](../../access-control/README.md).
- Endpoint schemas belong in the [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md).
- Security closure status belongs in the [MVP security test tracker](./security-test-plan.md#test-tracker).
- Current blockers are Admin Console UI, full schema migration and drift workflow, operations hardening, and security evidence closure.
- Read [FEATURE-REQUIREMENTS.md](../../FEATURE-REQUIREMENTS.md) only when changing behavior or checking feature scope.

## Contents

- [Agent Brief](#agent-brief)
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

This document is the Phase 6 MVP source of truth. It owns the accepted
production-MVP boundary, the current readiness state, and the remaining gates
before production data can be trusted.

Detailed runtime commands belong in the
[access-control runtime runbook](../../access-control/README.md). Endpoint
schemas belong in the
[IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md). Architecture
behavior and policies stay in the linked architecture documents.

## Executive Summary

The accepted MVP is a self-hosted Keycloak-backed access-control runtime with an
EDRLab IAM Control Plane API, the synthetic protected service
`access-check-demo-service`, the first service role `access-check-demo:consult`,
local append-only audit storage, and executable MVP security evidence.

The MVP covers the minimum access-control loop from the feature requirements:
controlled backoffice account creation, safe onboarding activation, immutable
account types, service-access-role assignment, server-side protected-service
authorization, fail-closed denials, and local business audit
([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements),
[README - Core Features](../../README.md#core-features)).

The Phase 6 runtime slice already provides Dockerized Keycloak, an IAM API, the
demo protected service, append-only JSONL audit storage, first-`super-admin`
bootstrap, Linux scripts, Docker tests, backup/restore scripts, and a Keycloak
smoke verification path
([Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes),
[Access-Control Runtime - Backup and Restore](../../access-control/README.md#backup-and-restore)).

Production readiness still requires explicit closure or accepted deferral of the
security-test plan, plus operations evidence for Keycloak ownership by
`super-admin`, backup/restore, secrets handling, monitoring, incident handling,
rollback, and residual runtime limitations
([MVP Security Test Plan](./security-test-plan.md#test-tracker),
[Access-Control Runtime - Evidence](../../access-control/README.md#evidence)).

## MVP Boundary

| Area | In the MVP | Detailed source |
| --- | --- | --- |
| Architecture boundary | Self-hosted Keycloak stores accepted IAM state; EDRLab business administration and authorization checks go through the Admin Console and IAM Control Plane API. | [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md) |
| IAM API | REST API under `/iam` for self-profile, accounts, onboarding, service roles, assignments, `authorization/check`, and audit reads. | [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md) |
| Account model | Backoffice accounts use fixed account types `super-admin`, `admin`, and `member`; account types are not mutable after creation. | [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Onboarding | Invited accounts activate only through safe bearer-token-derived onboarding evidence; privileged accounts also require accepted privileged-authentication evidence. | [Feature requirements `FR-043` and `FR-044`](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak/IAM Onboarding](../architecture/keycloak-iam-onboarding.md), [IAM Control Plane API Contract - Onboarding](../architecture/iam-control-plane-api-contract.md#onboarding) |
| First protected service | The first protected service is `access-check-demo-service`, a synthetic service that verifies the current user's access and returns JSON `OK` or `KO`. | [Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes) |
| First service role | The first service-access role is `access-check-demo:consult`; member service access is consultation-style only. | [Feature requirements `FR-023`](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes) |
| Authorization behavior | Protected services call `POST /iam/authorization/check`; the path has accepted timeout, retry, cache, fail-closed, access-stop, audit, and metrics behavior. | [Authorization Check Behavior](../architecture/authorization-check-behavior.md) |
| Audit | Local EDRLab audit is durable, file-backed, append-only, one JSON event object per physical line, with super-admin API consultation and no initial export. | [Audit Storage Architecture](../architecture/audit-storage.md) |
| Keycloak schema | The MVP uses managed Keycloak User Profile attributes, disables unmanaged attributes, uses account-type and service-access client roles, and treats unmanaged business mutation as drift. | [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md) |
| Security evidence | The MVP security gate covers frontend-bypass rejection, raw-claim rejection, token validation, subject-link immutability, fail-closed behavior, drift denial, and audit evidence. | [MVP Security Test Plan](./security-test-plan.md) |

## Current MVP State

| Item | State | Notes |
| --- | --- | --- |
| Scope authorization | Done | This page is the accepted Phase 6 MVP source of truth. |
| Runtime runbook | In place | `access-control/README.md` is the required runtime runbook for Phase 6 commands, evidence, known shortcuts, stop/reset, and backup/restore procedures ([Access-Control Runtime](../../access-control/README.md)). |
| Runtime slice | In place | The `access-control/` runtime includes Docker Compose, Keycloak, IAM API, demo service, bootstrap, audit storage, Linux scripts, Docker tests, backup/restore scripts, and smoke verification ([Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes)). |
| Keycloak-backed IAM state | In place for the runtime slice | The Docker runtime uses `IAM_STATE_BACKEND=keycloak`; account type, lifecycle, subject link, organization, schema marker, service-role metadata, and member role assignments are read from and written to Keycloak through the IAM Control Plane API ([Access-Control Runtime - Run](../../access-control/README.md#run)). |
| IAM API contract | In place | Runtime endpoint families, payloads, errors, actor model, authorization check, and audit reads are described in `docs/architecture/iam-control-plane-api-contract.md` ([IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)). |
| Security tests | Partially complete as runtime evidence | Docker-only tests exist for the runtime slice, while production readiness still depends on closing or explicitly deferring every test-plan gap before declaring the MVP production-ready ([Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes), [MVP Security Test Plan - Test Tracker](./security-test-plan.md#test-tracker)). |
| Admin Console UI | Not included yet | The runtime documentation explicitly states that the Admin Console UI is not included yet ([Access-Control Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts)). |
| Full schema migration and drift workflow | Not complete | The runtime represents drift with invariant checks, while full migration reporting, reconciliation workflow, and production direct-admin governance remain outside the current slice ([Access-Control Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts), [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)). |
| Operations hardening | Not complete | The runbook has backup/restore scripts and evidence procedures, but production trust still needs accepted evidence for secrets handling, monitoring, incident handling, rollback, ownership, and residual limitations ([Access-Control Runtime - Backup and Restore](../../access-control/README.md#backup-and-restore), [Access-Control Runtime - Known MVP Shortcuts](../../access-control/README.md#known-mvp-shortcuts)). |

## Included Capabilities

### Account Management

The MVP includes controlled creation, listing, reading, profile update,
disablement, restoration, and archival for `member` accounts by `admin`, and for
`admin` and `member` accounts by `super-admin`, within the management scopes
defined by the feature requirements and IAM API contract
([Feature requirements `FR-017` and `FR-018`](../../FEATURE-REQUIREMENTS.md#feature-requirements),
[IAM Control Plane API Contract - Accounts](../architecture/iam-control-plane-api-contract.md#accounts)).

Accounts start as invited, require at least email, organization, name, and a
stable internal account identifier, and are retained rather than hard-deleted in
the initial policy
([Feature requirements `FR-009`, `FR-014`, and `FR-040`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Onboarding and Bootstrap

The MVP includes safe onboarding activation through
`POST /iam/onboarding/activate`, where the IAM API derives identity evidence
from the authenticated user's bearer token and activates only when the accepted
match rules pass
([IAM Control Plane API Contract - Onboarding](../architecture/iam-control-plane-api-contract.md#onboarding),
[Keycloak/IAM Onboarding](../architecture/keycloak-iam-onboarding.md),
[Feature requirements `FR-043` and `FR-044`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The first `super-admin` is handled by a controlled bootstrap process outside the
public IAM API. The process is idempotent and audited, and it may seed the first
`super-admin` only when no valid `super-admin` exists
([Access-Control Runtime - Super-Admin Bootstrap](../../access-control/README.md#super-admin-bootstrap)).

### Service-Access Roles

The MVP includes service-access-role listing for `admin` and `super-admin`,
catalog mutation by `super-admin`, and assignment or removal of active
service-access roles for `member` accounts only
([Feature requirements `FR-002`, `FR-003`, `FR-004`, and `FR-032`](../../FEATURE-REQUIREMENTS.md#feature-requirements),
[IAM Control Plane API Contract - Service Roles](../architecture/iam-control-plane-api-contract.md#service-roles)).

Service-access roles must not be assigned to `admin` or `super-admin` accounts.
Active `admin` accounts receive covered service access automatically, and active
`super-admin` accounts receive that access through inherited admin capability
([Feature requirements `FR-002`, `FR-003`, and `FR-004`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Protected-Service Authorization

The MVP includes `access-check-demo-service` as the first protected-service
integration. It calls `POST /iam/authorization/check` using service-to-service
authentication and maps IAM decisions to `OK` or `KO` JSON responses
([IAM Control Plane API Contract - Authorization](../architecture/iam-control-plane-api-contract.md#authorization),
[Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes)).

Protected-service authorization is server-side and fail-closed. The accepted
architecture behavior defines timeout, retry, no positive cache, optional short
deny cache, no indeterminate cache, next-check access stop, audit, and metrics
expectations
([Authorization Check Behavior](../architecture/authorization-check-behavior.md)).

### Audit and Security Evidence

The MVP includes local EDRLab business audit events for account lifecycle,
onboarding, subject-link, role, authorization denial, audit-read, bootstrap,
rejected privileged onboarding, and indeterminate dependency scenarios
([IAM Control Plane API Contract - Audit](../architecture/iam-control-plane-api-contract.md#audit),
[Audit Storage Architecture](../architecture/audit-storage.md)).

The MVP includes an accepted security regression test plan. The
production-readiness gate passes only when the required tests are implemented or
explicitly deferred with accepted risk, and the implemented tests prove
server-side rejection, no unauthorized mutation, fail-closed behavior, drift
handling, and audit evidence
([MVP Security Test Plan - Test Tracker](./security-test-plan.md#test-tracker)).

## Out of Scope

| Out of scope for this MVP | Rationale |
| --- | --- |
| Public signup, public customer identity, social login, and consumer identity flows | The access-control capability is limited to backoffice users ([Feature requirements `FR-006`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Company-wide workforce IAM replacement | The repository scope excludes a full workforce IAM replacement ([README - Initial Scope](../../README.md#initial-scope)). |
| Member self-service beyond read-only own-profile consultation | Members cannot update their own profile, manage accounts, assign roles, or consult audit records ([Feature requirements `FR-019`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Account-type mutation, member-to-admin conversion, account merge, or subject-link rebinding | These actions violate fixed account type, privilege-escalation, and immutable subject-link requirements ([Feature requirements `FR-001`, `FR-026`, and `FR-039`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Hard deletion of accounts, service roles, or audit records | The initial policy retains accounts, forbids service-role hard deletion, and keeps audit append-only ([Feature requirements `FR-014`, `FR-032`, and `FR-035`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Routine business administration directly in Keycloak Admin Console | Business administration goes through the EDRLab Admin Console and IAM Control Plane API; unmanaged Keycloak mutation is drift ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)). |
| Real business protected-service integration | The first MVP protected service is the synthetic `access-check-demo-service`; real business protected services require explicit later scope and testing ([Access-Control Runtime - What This Slice Includes](../../access-control/README.md#what-this-slice-includes)). |
| Fine-grained per-action permission matrix beyond consultation-style member access | The first member permission is consultation-style access; more granular permissions require a concrete protected-service need ([Feature requirements `FR-023` and `FR-030`](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Audit export and advanced audit search/filtering | The MVP keeps audit consultation to chronological list and basic detail, with no initial export ([Audit Storage Architecture](../architecture/audit-storage.md)). |
| WebAuthn/passkeys as a mandatory MVP prerequisite | OTP safeguards are accepted for the current MVP direction; WebAuthn/passkeys remain future hardening ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| Production high availability and multi-replica Keycloak operation | High availability is outside the current MVP unless explicitly added later. |

## Production Readiness Gaps

This tracker uses the same status vocabulary as the security tracker:
`Implemented`, `Partial`, `Open`, and `Deferred`.

| Gap | Status | Required evidence | Next action | Risk if deferred |
| --- | --- | --- | --- | --- |
| Admin Console UI | `Open` | Business UI or accepted operator workflow that uses the IAM API rather than routine direct Keycloak business administration ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [runtime shortcuts](../../access-control/README.md#known-mvp-shortcuts)). | Build the minimal admin/super-admin workflow or explicitly accept an API/script-only MVP operator workflow. | Human operations stay dependent on technical API/script access, increasing operator error and bypass pressure. |
| Keycloak schema migration and drift workflow | `Partial` | Exact schema/bootstrap or migration commands, dry-run/report output, invalid-state handling, and reconciliation or quarantine evidence following the schema policy ([Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md), [runtime shortcuts](../../access-control/README.md#known-mvp-shortcuts)). | Turn current invariant checks into migration/drift evidence for lifecycle drift and linked-subject drift. | Production state may contain unmanaged or inconsistent Keycloak data that blocks access or hides privilege drift. |
| Operations evidence | `Partial` | Backup/restore evidence plus secrets handling, monitoring, incident handling, rollback, accountable ownership, and residual-limitation review ([runtime backup/restore](../../access-control/README.md#backup-and-restore), [runtime evidence](../../access-control/README.md#evidence)). | Extend the runbook with secrets, monitoring, incident, rollback, and ownership evidence. | Production recovery and incident response remain ad hoc even if the runtime works. |
| OTP operational safeguards | `Partial` | Configured and verified privileged OTP path, including required actions, reset/recovery posture, brute-force safeguards, and audit-relevant operations where IAM participates ([ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). | Retain the Docker human e2e evidence for `iam-privileged` ACR activation, then add an accepted operations note for OTP reset/recovery, brute-force safeguards, monitoring, and support posture. | Privileged recovery and support operations may rely on assumptions even though the runtime step-up activation path is repeatably verified. |
| Security evidence closure | `Partial` | All security tracker rows are `Implemented` or explicitly `Deferred` with accepted risk, and evidence is retained through the runtime evidence workflow ([security tracker](./security-test-plan.md#test-tracker), [runtime evidence](../../access-control/README.md#evidence)). | Close the `Open` rows first, then reduce `Partial` rows for fail-closed, stale-token, drift, and audit coverage. | A production-ready claim would rest on incomplete server-side authorization and audit proof. |
| Runtime limitations review | `Open` | Explicit decision on which known MVP shortcuts are accepted, removed, or kept test-only/non-production-only ([runtime shortcuts](../../access-control/README.md#known-mvp-shortcuts), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)). | Review every known shortcut before any production-readiness claim. | Temporary shortcuts may silently become production behavior. |

## Source of Truth Map

| Need | Source |
| --- | --- |
| Accepted Phase 6 MVP scope, residual risks, and readiness gaps | This document |
| Feature requirements and actor rules | [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md) |
| Accepted architecture direction | [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md) |
| IAM routes, payloads, errors, and endpoint behavior | [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md) |
| `authorization/check` timeout, retry, cache, fail-closed, access-stop, audit, and metrics behavior | [Authorization Check Behavior](../architecture/authorization-check-behavior.md) |
| Audit storage architecture | [Audit Storage Architecture](../architecture/audit-storage.md) |
| Keycloak state model and drift policy | [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md) |
| Keycloak/IAM onboarding flow | [Keycloak/IAM Onboarding](../architecture/keycloak-iam-onboarding.md) |
| Security regression test gate | [MVP Security Test Plan](./security-test-plan.md) |
| Executable Phase 6 runtime and commands | [Access-Control Runtime Runbook](../../access-control/README.md) |
| Phase boundaries | [Project Governance](../../PROJECT-GOVERNANCE.md) |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [README - Core Features](../../README.md#core-features)
- [README - Initial Scope](../../README.md#initial-scope)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [IAM Control Plane API Contract](../architecture/iam-control-plane-api-contract.md)
- [Authorization Check Behavior](../architecture/authorization-check-behavior.md)
- [Audit Storage Architecture](../architecture/audit-storage.md)
- [Keycloak IAM Schema Policy](../architecture/keycloak-iam-schema-policy.md)
- [Keycloak/IAM Onboarding](../architecture/keycloak-iam-onboarding.md)
- [MVP Security Test Plan](./security-test-plan.md)
- [Access-Control Runtime Runbook](../../access-control/README.md)
