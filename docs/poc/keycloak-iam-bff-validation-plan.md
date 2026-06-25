# Keycloak IAM BFF Validation Plan

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-23

## Contents

- [Purpose](#purpose)
- [Validation Target](#validation-target)
- [Non-Production Scope](#non-production-scope)
- [Accepted Direction](#accepted-direction)
- [Open Mapping Decisions](#open-mapping-decisions)
- [Work Packages](#work-packages)
- [Evidence Record](#evidence-record)
- [Readiness Gate](#readiness-gate)
- [References](#references)

## Purpose

This plan defines the next Phase 4 validation path after the 2026-06-23 pivot toward Keycloak as the IAM source with an EDRLab Admin Console and BFF/Admin API facade. It supersedes the completed local-access-control-boundary validation plan for future work, while preserving `WP-001` through `WP-009` as historical evidence for the earlier boundary ([ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md), [Keycloak validation plan](./keycloak-validation-plan.md), [Keycloak WP-009 result](./keycloak-wp009-result.md)).

This is a non-production PoC plan. It does not approve production implementation, production deployment, production database topology, CI, migrations, application code, or durable infrastructure ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Validation Target

The target to validate is self-hosted Keycloak as the backing IAM product for selected backoffice account and service-access state, with the EDRLab BFF/Admin API enforcing business invariants before calling Keycloak Admin REST or approved Keycloak policy APIs. Keycloak documents users, roles, groups, attributes, authentication flows, sessions, events, Admin REST APIs, and Authorization Services as product capabilities that can support this validation ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)).

The EDRLab Admin Console remains the business administration surface. Business administrators must not be sent directly to Keycloak Admin Console for account type, lifecycle, service-access-role, protected-service authorization, or audit-sensitive changes because `FR-038` requires controlled server-side administration and authorization for IAM-backed business state ([Keycloak IAM BFF scope](../architecture/keycloak-iam-bff-scope.md), `FR-024`, `FR-033`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Non-Production Scope

This plan creates no runtime artifact by itself. Any future runtime work package must be executed in a clearly named PoC-only workspace, include a Docker-based runtime definition, be fully scripted for Linux review, and document bootstrap, start, verification, evidence collection, stop, and cleanup steps where applicable ([AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

The validation data set should stay minimal:

- one invited `member`;
- one invited `admin`;
- one invited `super-admin`;
- one protected backend service role or equivalent authorization object;
- unsafe cases for no invitation, duplicate invitation, unverified email, pre-linked subject, disabled account, archived account, missing role, and direct Keycloak-admin drift.

Out of scope until explicit Phase 5 or Phase 6 movement:

- production Keycloak deployment, database, high availability, monitoring, backup automation, migrations, CI, or application code;
- production database topology decisions beyond logical responsibility notes;
- public signup, public customer accounts, consumer IAM, social login for consumers, or company-wide IAM replacement ([README - Initial Scope](../../README.md#initial-scope)).

## Accepted Direction

The next validation assumes the following direction:

| Area | Phase 4 assumption | Evidence expected |
| --- | --- | --- |
| IAM source | Keycloak may hold account identity, account-type representation, lifecycle representation, service-access-role representation, authentication policy, sessions, and provider-side events, subject to validation. | Mapping table plus runtime proof for allowed and denied cases ([Keycloak IAM BFF scope](../architecture/keycloak-iam-bff-scope.md#state-ownership)). |
| Business facade | EDRLab Admin Console calls an EDRLab BFF/Admin API. The BFF authorizes the actor server-side, validates business invariants, calls Keycloak Admin REST or approved policy APIs, and records business audit evidence. | Request/decision/mutation/audit examples for each sensitive operation ([Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), `FR-024`, `FR-027`, `FR-033`, `FR-038`). |
| Direct Keycloak Admin Console | Direct console access is limited to technical operators and treated as a drift source to control or detect. Keycloak documents realm administrators and delegated administration, so administrative grants must be reviewed rather than assumed safe for business administration ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). | Allow/deny list, drift scenario, and residual-risk note. |
| Protected-service authorization | The first runtime slice must choose one contract: BFF-mediated check, Keycloak Authorization Services, constrained token claims, introspection-style check, or a reviewed hybrid. Protected services still enforce authorization server-side and fail closed when authorization cannot be determined (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Contract definition plus allow, deny, stale-access, and outage/fail-closed evidence. |
| Audit | Keycloak events may be provider-side evidence, but EDRLab must decide which business decisions still require local audit records. Keycloak documents user and admin events, but the BFF may need local records for rationale, denied operations, audit reads, and correlation (`FR-027`, `FR-028`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). | Audit matrix, correlation IDs, sample local audit events, and Keycloak event references where useful. |

## Open Mapping Decisions

These decisions must be closed before or during `WP-010`; they are validation inputs, not production recommendations.

| ID | Decision to validate | Candidate choices | Requirement pressure |
| --- | --- | --- | --- |
| `OMD-KIB-001` | Account type representation for `super-admin`, `admin`, and `member`. | Realm roles, client roles, groups, user attributes, or a constrained combination. | Account type is fixed and must not be changed, merged, or elevated later (`FR-001`, `FR-026`). |
| `OMD-KIB-002` | Lifecycle representation for `invited`, `active`, `disabled`, and `archived`. | Keycloak `enabled`, attributes, groups, required actions, or a constrained combination. | Non-active accounts must not obtain protected-service access, and accounts must not return to `invited` (`FR-011` through `FR-016`, `FR-031`). |
| `OMD-KIB-003` | Service-access-role representation. | Realm/client roles, groups, Authorization Services resources/scopes/policies, or constrained claims. | Service-access roles must stay separate from account types and must not grant account-management responsibilities (`FR-002`, `FR-022`, `FR-032`). |
| `OMD-KIB-004` | Protected-service authorization contract. | BFF-mediated check, Keycloak Authorization Services, introspection-style check, constrained token claims, or reviewed hybrid. | Protected services must authorize server-side and fail closed (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). |
| `OMD-KIB-005` | Privileged-authentication evidence. | Keycloak authentication flow, WebAuthn/OTP/passwordless configuration, `amr`, `acr`, event evidence, or explicit blocker. | Production `admin` and `super-admin` onboarding requires privileged-authentication evidence (`FR-034`, `FR-043`, `FR-044`; [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)). |
| `OMD-KIB-006` | Local audit responsibility. | Keycloak events only for provider evidence plus local EDRLab audit for business decisions, or another justified split. | Audit coverage must include business operations, denials, audit reads/exports, and append-only retention expectations (`FR-027`, `FR-028`, `FR-035`). |

## Work Packages

| Work package | Runtime or document | Goal | Evidence |
| --- | --- | --- | --- |
| `WP-010` Keycloak IAM mapping design | Documentation-first | Choose the first validation mapping for account type, lifecycle, subject link, service-access roles, protected-service authorization evidence, and audit identifiers. | Mapping table, rejected shortcuts, requirement trace, and residual risks. |
| `WP-011` BFF admin anti-bypass path | Runtime or documentation-first | Show that business admin operations go through the EDRLab BFF/Admin API before Keycloak mutation, and that the BFF enforces actor scope, lifecycle, account-type immutability, and audit. | Example calls, server-side decisions, Keycloak Admin REST mutation evidence, denied bypass cases, and local audit event examples. |
| `WP-012` Account lifecycle and onboarding in Keycloak IAM | Runtime | Validate safe onboarding and unsafe onboarding cases using the selected Keycloak-backed lifecycle and subject-link mapping. | Safe activation record; denied records for no invitation, duplicate invitation, unverified email, pre-linked subject, disabled account, and archived account (`FR-039`, `FR-043`, `FR-044`). |
| `WP-013` Privileged account evidence | Runtime | Resolve the previous privileged-authentication blocker by configuring and verifying explicit evidence for `admin` and `super-admin` activation, or keep it blocked with a precise reason. | Token claim, authentication-flow, event, or configuration evidence; blocker if evidence is not explicit enough (`FR-034`, `FR-043`, `FR-044`). |
| `WP-014` Service-access roles and protected-service authorization | Runtime | Validate the selected service-access-role and protected-service authorization contract, including access-stop behavior after account or role changes. | Allow, deny, fail-closed, stale-access, and next-check-denial evidence (`FR-016`, `FR-020`, `FR-021`, `FR-032`). |
| `WP-015` Direct-admin-console drift and shortcut rejection | Runtime or documentation-first | Prove unmanaged Keycloak Admin Console edits, misleading raw token claims, or frontend/protected-service shortcuts cannot bypass the controlled BFF path, or record the residual risk. | Drift scenario, detection or prevention evidence, rejected shortcut list, and residual-risk note (`FR-026`, `FR-038`). |
| `WP-016` Audit and operations review | Documentation-first, runtime where useful | Decide which events are Keycloak evidence, which are local EDRLab business audit records, and what operational duties the Keycloak-IAM-backed model adds. | Audit boundary matrix, sample records, event correlation, backup/restore/admin-surface notes, and unresolved operator risks. |
| `WP-017` Results and Phase 5 review inputs | Documentation | Consolidate the Keycloak-IAM/BFF evidence into decision-ready review inputs. | Pass/fail/blocked matrix, accepted limitations, residual risks, Phase 5 questions, and recommendation options. |

Suggested order: close `WP-010` first; run `WP-011` before relying on any Keycloak-backed mutation; run `WP-012` and `WP-013` before accepting privileged onboarding; run `WP-014` before treating service access as validated; keep `WP-015` and `WP-016` active across runtime work; finish with `WP-017`.

## Evidence Record

Each runtime or documentation-first package should produce a short result note using this shape:

```text
Scenario:
Work package:
Requirement links:
Mapping under test:
Setup:
Action:
Expected result:
Observed result:
Evidence collected:
Pass / fail / blocked:
Residual risk:
Production gap:
Decision impact:
```

Use `blocked` rather than inferring Keycloak behavior when the evidence is not explicit enough. This is especially important for privileged-authentication evidence, direct admin-console drift, access-stop delay, event retention, and token-claim freshness (`FR-016`, `FR-034`, `FR-038`, `FR-043`, `FR-044`).

## Readiness Gate

Start runtime execution only when:

- `WP-010` has named the exact Keycloak representation to test for account type, lifecycle, subject link, service-access roles, and audit identifiers;
- the BFF/Admin API responsibilities are explicit enough to produce allowed and denied examples;
- the protected-service authorization contract is selected for the first runtime slice;
- direct Keycloak Admin Console access is classified as technical-operator access, drift, or explicitly blocked business access;
- the runtime PoC can be run from a clean Linux checkout with Docker-based orchestration and documented commands;
- evidence outputs are limited to results, failures, surprises, residual risks, and Phase 5 review inputs;
- no production application code, production database, production migration, CI, generated artifact, or deployment file is required.

If these conditions are not met, continue documentation-level validation instead of creating runtime artifacts ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

## References

- [ADR 0002 - Validate Keycloak IAM With EDRLab BFF](../decisions/0002-validate-keycloak-iam-bff.md)
- [ADR 0001 - Choose Keycloak for Validation](../decisions/0001-choose-keycloak-for-validation.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Keycloak IAM BFF Scope](../architecture/keycloak-iam-bff-scope.md)
- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Keycloak WP-009 Result](./keycloak-wp009-result.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [README - Initial Scope](../../README.md#initial-scope)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak Roles and Groups](https://www.keycloak.org/docs/latest/server_admin/#assigning-permissions-using-roles-and-groups)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
