# Project Study Documentation

This directory contains the project-facing study documents for the internal backoffice access-control study. Organize documents by reader task and artifact type: Diataxis recommends organizing documentation around user needs such as explanation, reference, and practical task support ([Diataxis](https://diataxis.fr/)); arc42 is a pragmatic reference for structuring architecture communication around goals, constraints, context, decisions, quality requirements, and risks ([arc42 overview](https://arc42.org/overview)).

## Contents

- [Documentation Map](#documentation-map)
- [Reading Path](#reading-path)
- [Document Rules](#document-rules)
- [References](#references)

## Documentation Map

| Location | Purpose | Use for |
| --- | --- | --- |
| `requirements/` | Requirements and traceability | Requirements derived from the immutable feature specification, traceability matrices, acceptance criteria, assumptions, and open questions ([README](../README.md), [Project governance](../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)). |
| `risks/` | Risk registers | Security, operational, privacy, audit, lifecycle, and delivery risks that need tracking or mitigation during the study ([Project governance](../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)). |
| `architecture/` | Architecture study material | Context boundaries, important flows, option analysis, integration boundaries, and architecture notes that are not final decisions ([arc42 overview](https://arc42.org/overview), [Project governance](../PROJECT-GOVERNANCE.md#phase-2---requirements-and-risk-framing)). |
| `evaluation/` | Solution-choice evaluation | Evaluation criteria, candidate catalogues, comparison matrices, evidence notes, solution-choice rationale, review inputs, and accepted MVP scope boundaries ([Project governance](../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance](../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance](../PROJECT-GOVERNANCE.md#phase-6---production-mvp)). |
| `poc/` | Proof-of-Concept planning and results | Lightweight non-production PoC plans, assumptions, limits, evaluation questions, and results ([Project governance](../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)). |
| [`decisions/`](./decisions/) | Decision records | ADR-style records for real project or architecture decisions. ADR guidance recommends keeping decision records short, factual, statused, and tied to context and consequences ([Microsoft ADR guidance](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record), [ADR GitHub organization](https://adr.github.io/)). |
| [`wiki/`](./wiki/) | Conceptual IAM reference | General IAM concepts, protocol explanations, security concepts, terminology, and source-backed reference pages ([Project governance](../PROJECT-GOVERNANCE.md#phase-1---conceptual-iam-foundation)). |

## Current Study Documents

| Document | Purpose |
| --- | --- |
| [Feature requirements specification](../FEATURE-REQUIREMENTS.md) | Consolidated final-solution feature requirements list for the access-control capability. |
| [Feature requirements review](./requirements/feature-requirements-review.md) | Live step-by-step consolidation trail for turning the root `README.md` feature specification and retired baseline material into one unique root `FEATURE-REQUIREMENTS.md` list. |
| [Feature scope review](./requirements/feature-scope-review.md) | Historical step-by-step validation trail for each immutable `FS-*` requirement, including agreed Phase 2 scope and threat-model implications. |
| [Requirements baseline review](./requirements/baseline-review.md) | Historical validation trail for the retired `RB-*` requirements, checking sufficiency, scope fit, and concordance with the validated `FS-*` interpretation. |
| [Threat model](./risks/threat-model.md) | Phase 2 threat model used to identify access-control risks and refine security requirements before solution choice. |
| [Architecture options](./architecture/options.md) | Superseded Phase 2 architecture option framing derived from the earlier local-access-control-authority interpretation. |
| [Keycloak integration scope](./architecture/keycloak-integration-scope.md) | Superseded architecture note that separates EDRLab development responsibilities, Keycloak configuration responsibilities, and the SSO session flow for the original local-access-control-authority Keycloak candidate. |
| [Keycloak IAM Control Plane API scope](./architecture/keycloak-iam-bff-scope.md) | Review-state architecture note for the active pivot: Keycloak as IAM source with an EDRLab Admin Console and IAM Control Plane API. |
| [IAM Control Plane API contract](./architecture/iam-control-plane-api-contract.md) | Accepted Phase 5 API contract for MVP endpoints, actors, service-to-service authentication, operation authorization, Problem Details errors, idempotence, correlation IDs, and audit. |
| [Authorization check runtime behavior](./architecture/authorization-check-behavior.md) | Accepted Phase 5 runtime behavior for `authorization/check` timeout, retry, cache, fail-closed handling, access-stop delay, audit, metrics, and cache headers. |
| [Audit storage policy](./architecture/audit-storage.md) | Accepted Phase 5 audit storage policy for local file-backed append-only audit records with one JSON event object per line, retention, read/export boundary, correlation, backup, and confidentiality. |
| [Keycloak IAM schema policy](./architecture/keycloak-iam-schema-policy.md) | Accepted Phase 5 Keycloak IAM schema policy for managed attributes, client roles, edit permissions, invariant checks, migration, and token-claim boundaries. |
| [Concrete technical solution candidates](./evaluation/technical-solutions.md) | Superseded Phase 2 candidate catalogue for Auth0 plus local access-control, Keycloak plus local access-control, and Spring local IAM. |
| [Solution choice](./evaluation/solution-choice.md) | Superseded Phase 3 artifact recording self-hosted Keycloak plus local access-control as the original candidate solution to validate. |
| [Phase 5 review note](./evaluation/phase-5-review-note.md) | Accepted Phase 5 note recording adoption of the Keycloak IAM Control Plane API architecture, accepted residual risks, and closed Phase 6 MVP authorization gates. |
| [MVP scope](./evaluation/mvp-scope.md) | Accepted Phase 6 MVP scope and readiness map for the current boundary, implementation state, exclusions, production-readiness gaps, and detailed source links. |
| [MVP security test plan](./evaluation/security-test-plan.md) | Accepted Phase 5 security regression test plan for frontend-only bypass rejection, raw-claim rejection, token validation, subject-link immutability, fail-closed behavior, drift denial, and audit evidence. |
| [Keycloak validation plan](./poc/keycloak-validation-plan.md) | Superseded Phase 4 entry plan for the completed non-production Keycloak local-access-control-boundary validation. |
| [Keycloak IAM Control Plane API validation plan](./poc/keycloak-iam-bff-validation-plan.md) | Review-state Phase 4 plan for validating Keycloak as the IAM source with an EDRLab Admin Console and IAM Control Plane API. |
| [Keycloak setup runbook](./poc/keycloak-setup-runbook.md) | Superseded Phase 4 runbook for executing `WP-001`: throwaway realm, backoffice OIDC client, test users, event settings, discovery evidence, and the executable runtime under [`poc/keycloak`](../poc/keycloak/README.md). |
| [Keycloak WP-001 result](./poc/keycloak-wp001-result.md) | Review-state Phase 4 result note recording the Docker execution, scripted bootstrap, verification checks, evidence location, and limitations for `WP-001`. |
| [Keycloak WP-002 result](./poc/keycloak-wp002-result.md) | Review-state Phase 4 result note recording the scripted login and SSO boundary validation, generated evidence location, and limitations for `WP-002`. |
| [Keycloak WP-003 result](./poc/keycloak-wp003-result.md) | Review-state Phase 4 result note recording the scripted safe/unsafe onboarding validation, generated evidence location, and limitations for `WP-003`. |
| [Keycloak WP-004 result](./poc/keycloak-wp004-result.md) | Review-state Phase 4 result note recording the scripted privileged-authentication evidence validation and current blocker for `admin` and `super-admin` activation. |
| [Keycloak WP-005 result](./poc/keycloak-wp005-result.md) | Review-state Phase 4 result note recording the scripted claim-override rejection validation, generated evidence location, and limitations for `WP-005`. |
| [Keycloak WP-006 result](./poc/keycloak-wp006-result.md) | Review-state Phase 4 result note recording the scripted local `authorization/check`, fail-closed, and access-stop validation. |
| [Keycloak WP-007 result](./poc/keycloak-wp007-result.md) | Review-state Phase 4 result note recording the scripted audit-correlation validation, generated evidence location, expected audit gaps, and local-audit authority boundary. |
| [Keycloak WP-008 result](./poc/keycloak-wp008-result.md) | Review-state Phase 4 documentation-first result note recording the Keycloak Web Admin boundary and self-hosted operations checklist. |
| [Keycloak WP-009 result](./poc/keycloak-wp009-result.md) | Review-state Phase 4 result note consolidating the Keycloak PoC matrix, blockers, accepted limitations, residual risks, and Phase 5 review questions. |
| [Keycloak WP-010 result](./poc/keycloak-wp010-result.md) | Review-state Phase 4 result note selecting the first Keycloak IAM mapping for account type, lifecycle, subject link, service-access roles, protected-service authorization, and audit evidence. |
| [Keycloak WP-011 result](./poc/keycloak-wp011-result.md) | Review-state Phase 4 documentation-first result note defining the IAM Control Plane API anti-bypass path for Keycloak-backed account and service-access administration. |
| [Keycloak WP-012 result](./poc/keycloak-wp012-result.md) | Review-state Phase 4 documentation-first result note defining Keycloak-backed lifecycle, onboarding activation, unsafe onboarding denials, and runtime evidence expectations. |
| [Keycloak WP-013 result](./poc/keycloak-wp013-result.md) | Review-state Phase 4 result note selecting and validating ACR/LoA step-up as the privileged-authentication evidence path for admin and super-admin onboarding. |
| [Keycloak WP-014 result](./poc/keycloak-wp014-result.md) | Review-state Phase 4 documentation-first result note defining the service-access-role model, IAM Control Plane API `GET /me/services` listing, `authorization/check` contract, fail-closed behavior, and access-stop evidence expectations. |
| [Keycloak WP-015 result](./poc/keycloak-wp015-result.md) | Review-state Phase 4 documentation-first result note defining direct Keycloak Admin Console drift handling, shortcut rejection, event-gap evidence, and residual risks. |
| [Keycloak WP-016 result](./poc/keycloak-wp016-result.md) | Review-state Phase 4 documentation-first result note defining the audit boundary, local EDRLab audit event contract, Keycloak evidence role, operational review items, and runtime evidence expectations. |
| [Keycloak WP-011 through WP-016 runtime result](./poc/keycloak-wp011-016-runtime-result.md) | Review-state Phase 4 runtime result note recording the Docker execution, decision matrix, evidence path, Keycloak user-profile surprise, and the follow-up `WP-013` runtime closure. |
| [Keycloak WP-017 result](./poc/keycloak-wp017-result.md) | Review-state Phase 4 documentation-first result note consolidating `WP-010` through `WP-016` into Phase 5 review inputs, runtime evidence gaps, residual risks, and decision options. |
| [ADR 0001 - Choose Keycloak for validation](./decisions/0001-choose-keycloak-for-validation.md) | Superseded decision record for the original Phase 3 Keycloak local-access-control validation candidate. |
| [ADR 0002 - Validate Keycloak IAM with EDRLab IAM Control Plane API](./decisions/0002-validate-keycloak-iam-bff.md) | Accepted decision record for the active Keycloak-IAM-source validation direction with an EDRLab IAM Control Plane API. |
| [ADR 0003 - Accept OTP for privileged authentication](./decisions/0003-accept-otp-for-privileged-authentication.md) | Accepted decision record confirming OTP MFA as sufficient privileged-authentication evidence for the current Keycloak IAM direction. |
| [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP design](./decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md) | Accepted Phase 5 decision adopting the Keycloak IAM Control Plane architecture for constrained MVP design without starting Phase 6 production implementation. |
| [ADR 0005 - Authorize Phase 6 production MVP](./decisions/0005-authorize-phase-6-production-mvp.md) | Accepted Phase 5 decision authorizing Phase 6 production MVP implementation for the accepted Keycloak IAM Control Plane API scope, with explicit residual risks and post-MVP deferrals. |

## Reading Path

1. Start with the root [README](../README.md) for the immutable feature specification and current roadmap.
2. Use [Project governance](../PROJECT-GOVERNANCE.md) for phase boundaries and evidence rules.
3. Use the [conceptual IAM wiki](./wiki/README.md) when a project study document depends on IAM terminology or protocol background.
4. Use this map to find project-specific requirements, risks, architecture notes, evaluations, PoC material, and decisions as they are created.

## Document Rules

Study documents use lowercase `kebab-case.md` filenames inside their topic folder. The folder carries the category, so filenames should stay short and specific, as defined by the repository agent instructions ([AGENTS](../AGENTS.md#documentation-rules)).

Non-index project study documents outside `decisions/` should start with:

```text
Status: Draft | Review | Accepted | Superseded
Phase: Phase 6 - Production MVP
Scope: Requirements | Risks | Architecture | Evaluation | PoC
Last reviewed: YYYY-MM-DD
```

Conceptual wiki pages under `wiki/` keep their existing wiki format and are not required to use this metadata block. Decision records under `decisions/` use the ADR template in [`decisions/README.md`](./decisions/README.md).

Inline citations must sit near the claims they support. Non-index study and wiki pages also need a `References` section, as required by [Project governance](../PROJECT-GOVERNANCE.md#evidence-standard).

## References

- [Diataxis](https://diataxis.fr/)
- [arc42 Template Overview](https://arc42.org/overview)
- [Microsoft - Maintain an architecture decision record](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record)
- [ADR GitHub organization](https://adr.github.io/)
