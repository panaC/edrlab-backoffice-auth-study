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
| `evaluation/` | Candidate evaluation | Evaluation criteria, candidate catalogues, comparison matrices, evidence notes, and phase-appropriate scoring ([Project governance](../PROJECT-GOVERNANCE.md#phase-3---candidate-approach-catalog), [Project governance](../PROJECT-GOVERNANCE.md#phase-4---evidence-based-candidate-evaluation)). |
| `poc/` | Proof-of-Concept planning and results | Lightweight non-production PoC plans, assumptions, limits, evaluation questions, and results ([Project governance](../PROJECT-GOVERNANCE.md#phase-4---evidence-based-candidate-evaluation)). |
| [`decisions/`](./decisions/) | Decision records | ADR-style records for real project or architecture decisions. ADR guidance recommends keeping decision records short, factual, statused, and tied to context and consequences ([Microsoft ADR guidance](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record), [ADR GitHub organization](https://adr.github.io/)). |
| [`wiki/`](./wiki/) | Conceptual IAM reference | General IAM concepts, protocol explanations, security concepts, terminology, and source-backed reference pages ([Project governance](../PROJECT-GOVERNANCE.md#phase-1---conceptual-iam-foundation)). |

## Current Study Documents

| Document | Purpose |
| --- | --- |
| [Requirements baseline](./requirements/baseline.md) | Phase 2 requirements baseline with traceability to the immutable feature specification, user-provided constraints, assumptions, and scope boundaries. |
| [Threat model](./risks/threat-model.md) | Phase 2 threat model used to identify access-control risks and refine security requirements before candidate evaluation. |
| [Architecture options](./architecture/options.md) | Phase 2 architecture option framing for monolithic, modular monolithic, split control-plane, microservices, and hybrid shapes. |

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
Phase: Phase 2 - Requirements and Risk Framing
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
