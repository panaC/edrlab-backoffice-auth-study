# Phase 2 Open-Question Triage

This document triages the open questions that emerged from Phase 1 and the [Phase 2 Requirements Baseline](./phase-2-requirements-baseline.md). It is a working Phase 2 planning artifact, not a final decision record.

The goal is to decide what must be answered now, what can be deferred safely, and which follow-up artifacts should resolve each question.

## Triage vocabulary

| Field | Meaning |
| --- | --- |
| Priority | `P0` blocks the first useful PoC or candidate-evaluation setup. `P1` blocks a credible final recommendation. `P2` can wait until production design or later scope expansion. |
| Status | `Open` needs a decision. `Working assumption` has a temporary baseline but should be confirmed. `Deferred` is intentionally outside the first PoC or Phase 2 decision set. |
| Decision type | Identifies whether the answer is mainly product, security, operations, architecture, legal/compliance, or PoC scoping. |
| Blocks | Names what cannot move cleanly without the answer. |

## Recommended Phase 2 sequence

Phase 2 should not try to answer every open question with equal urgency. The useful order is:

1. Define a representative service and permission inventory.
2. Freeze the minimum PoC role and permission set.
3. Decide the minimum lifecycle states and stale-access window for the PoC.
4. Convert those answers into a narrow PoC plan.
5. Select the first candidate-evaluation batch.
6. Resolve administrator authentication, audit, and operations questions before final recommendation.

That order keeps the study testable without making production-only policy questions block early learning.

## Triage table

| ID | Question | Priority | Status | Decision type | Blocks | Recommended next artifact |
| --- | --- | --- | --- | --- | --- | --- |
| P2-Q001 | Which real or representative backoffice service should define the first service-access permissions? | P0 | Working assumption | Product / PoC scope | PoC scope, permission model, access-check requirement | [Service and permission inventory](./phase-2-service-permission-inventory.md) |
| P2-Q002 | What exact permissions should `member` and `admin` have in the first PoC? | P0 | Working assumption | Authorization model | PoC tests, admin API evaluation, RBAC candidate fit | [Service and permission inventory](./phase-2-service-permission-inventory.md) |
| P2-Q003 | What is the smallest useful PoC question set? | P0 | Working assumption | PoC scope | PoC planning and effort control | [Minimal PoC plan](./phase-2-minimal-poc-plan.md) |
| P2-Q004 | Which lifecycle states are required for the first PoC? | P0 | Working assumption | Product / security | Member lifecycle tests, disablement behavior | Lifecycle decision note |
| P2-Q005 | What is the maximum acceptable stale-access window after role removal or member disablement? | P0 | Working assumption | Security / token lifecycle | Token lifetime choice, revocation/introspection need, PoC acceptance criteria | [Minimal PoC plan](./phase-2-minimal-poc-plan.md) |
| P2-Q006 | Should the first PoC use refresh tokens or force re-login when access tokens expire? | P0 | Working assumption | Security / PoC scope | BFF session behavior, token handling tests | [Minimal PoC plan](./phase-2-minimal-poc-plan.md) |
| P2-Q007 | Which candidates deserve first evaluation records? | P0 | Open | Evaluation planning | Phase 3 handoff, comparison effort | Candidate evaluation plan |
| P2-Q008 | Are administrators required to use MFA in production? | P1 | Open | Security | Candidate fit, administrator authentication policy, recovery design | Administrator authentication decision note |
| P2-Q009 | Should high-risk admin actions require step-up authentication? | P1 | Open | Security / UX | Role assignment, client rotation, audit export, recovery reset requirements | Administrator authentication decision note |
| P2-Q010 | What member attributes are required beyond email, display name, status, and role assignments? | P1 | Open | Product / data model | Admin API shape, candidate data model mapping | Member attribute inventory |
| P2-Q011 | Should deletion be hard delete, soft delete, archive, or policy-dependent? | P1 | Open | Security / legal / data lifecycle | Retention, audit continuity, member lifecycle evaluation | Lifecycle and retention decision note |
| P2-Q012 | What audit retention, privacy, and export expectations apply? | P1 | Open | Legal / security / operations | Auditability evaluation, managed-provider fit, operational model | Audit and retention decision note |
| P2-Q013 | Who can create roles, assign roles, create clients, and rotate credentials? | P1 | Open | Authorization governance | Admin role design, self-escalation controls, candidate admin model | Privileged administration policy |
| P2-Q014 | Which team owns IAM operations after launch? | P1 | Open | Operations | Self-hosted feasibility, managed-provider risk, final recommendation | Operational ownership note |
| P2-Q015 | What uptime, backup, restore, and upgrade expectations apply? | P1 | Open | Operations | Operational scoring, self-hosted vs managed comparison | Operational requirements note |
| P2-Q016 | Does production need break-glass access? | P1 | Open | Security / operations | Recovery design, administrator authentication policy, incident response | Break-glass decision note |
| P2-Q017 | How should account recovery, MFA reset, and authenticator reset be approved and audited? | P1 | Open | Security / operations | Admin recovery, credential lifecycle, audit model | Recovery policy decision note |
| P2-Q018 | How should BFF sessions work with multiple replicas? | P2 | Deferred | Architecture / operations | Production deployment design | Deployment/session design note |
| P2-Q019 | Should service-to-service authentication enter the first implementation scope? | P2 | Deferred | Scope / architecture | Future machine-client model | Later service-to-service scope decision |
| P2-Q020 | Should role hierarchies, ABAC, resource-level permissions, or a policy engine be considered? | P2 | Deferred | Authorization architecture | Future authorization complexity | Later authorization model review |

## Current working assumptions

These assumptions let Phase 2 continue without pretending the questions are fully answered.

| Area | Working assumption | Risk if wrong |
| --- | --- | --- |
| First protected service | Use one representative demonstration API resource server until a real backoffice service inventory exists. | Permissions may be too generic to expose real candidate-fit problems. |
| Role baseline | Start with `member` and `admin`, backed by explicit permissions rather than a magical bypass flag. | The PoC may hide future need for more granular IAM-owner or read-only administrator roles. |
| Lifecycle baseline | Use `active` and `disabled` as the minimum PoC states. | Invitation, archive, delete, and recovery behavior may affect candidate selection later. |
| Token format | Use JWT access tokens for the first study and PoC baseline. | Immediate access removal may require introspection, revocation, or runtime authorization lookup later. |
| Access removal | Removed access may remain effective until short-lived access-token expiry in the first version. | High-risk admin access may need a shorter lifetime or stronger revocation model. |
| Refresh tokens | Do not require refresh tokens in the first PoC; force re-login or repeat login after access-token expiry. | Does not prove production refresh-token rotation, revocation, or reuse detection behavior. |
| Admin API consumer | The backoffice UI through the BFF is the only first-PoC admin API consumer. | Automation and service-account requirements may change the admin permission model later. |
| Service-to-service | Keep service-to-service authentication as future scope. | Some candidates may look better or worse once machine-client lifecycle is in scope. |

## Immediate decisions to make next

The next useful Phase 2 work should answer the P0 items in this order:

| Order | Decision | Output |
| ---: | --- | --- |
| 1 | Choose the representative service and operations for the first PoC. | [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md) |
| 2 | Define the exact `member` and `admin` permissions used by that service and the admin API. | [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md) |
| 3 | Decide the minimum lifecycle states for the PoC. | `docs/phase-2-lifecycle-decisions.md` or a section in the service/permission inventory |
| 4 | Decide the stale-access window and first token/session behavior. | [Phase 2 Minimal PoC Plan](./phase-2-minimal-poc-plan.md) |
| 5 | Write the minimal PoC plan from those decisions. | [Phase 2 Minimal PoC Plan](./phase-2-minimal-poc-plan.md) |
| 6 | Choose the first evaluation batch. | `docs/phase-2-candidate-evaluation-plan.md` |

## Decision impact map

| If this changes | Revisit these requirements or documents |
| --- | --- |
| Real service inventory appears | `IAM-ADMIN-004`, `IAM-RBAC-*`, [Initial Permission Model](./initial-permission-model.md), PoC plan |
| Administrator MFA becomes mandatory | `IAM-AUTHN-004`, `IAM-AUTHN-005`, [Administrator Authentication Policy](./administrator-authentication-policy.md), candidate evaluations |
| Immediate access removal becomes mandatory | `IAM-TOKEN-004`, `IAM-TOKEN-005`, `IAM-TOKEN-006`, [Token Lifecycle](./wiki/12-token-lifecycle.md), PoC plan |
| Hard delete is required | `IAM-ID-003`, `IAM-ID-008`, `IAM-AUDIT-*`, [Member Lifecycle](./member-lifecycle.md), audit retention decisions |
| Service-to-service enters first scope | `IAM-SCOPE-006`, `IAM-RBAC-007`, [Service-to-Service Authentication](./wiki/07-service-to-service-authentication.md), candidate evaluation gates |
| Self-hosting becomes preferred by policy | `IAM-OPS-*`, [Operational Model](./operational-model.md), candidate evaluation plan |

## Related documents

- [Phase 2 Requirements Baseline](./phase-2-requirements-baseline.md)
- [Phase 2 Service and Permission Inventory](./phase-2-service-permission-inventory.md)
- [Phase 2 Minimal PoC Plan](./phase-2-minimal-poc-plan.md)
- [Phase 1 working notes](./phase-1-working-notes.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Member Lifecycle](./member-lifecycle.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Administrator Authentication Policy](./administrator-authentication-policy.md)
- [Operational Model](./operational-model.md)
- [Threat Model](./threat-model.md)
- [Evaluation Framework](./evaluation-framework.md)
- [Candidate Shortlist](./candidate-shortlist.md)
