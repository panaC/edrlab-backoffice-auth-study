# Decision Records

This directory holds ADR-style decision records for the project. Use it only when the study records a real decision or a proposed decision that needs review; open analysis, candidate comparison, and unresolved trade-offs belong in `architecture/`, `evaluation/`, or `requirements/`.

ADRs should stay short, factual, and tied to context, options, decision outcome, trade-offs, confidence, and consequences, matching the lightweight guidance from Microsoft and the ADR community ([Microsoft ADR guidance](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record), [ADR GitHub organization](https://adr.github.io/)).

## Contents

- [Naming](#naming)
- [Template](#template)
- [Current Records](#current-records)
- [References](#references)

## Naming

Use numbered lowercase files:

```text
0001-short-decision-title.md
0002-short-decision-title.md
```

Do not renumber existing decision records. If a decision changes, create a new record that supersedes the old one and link both records; Microsoft describes the ADR log as append-only and recommends preserving decision history ([Microsoft ADR guidance](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record)).

## Template

```text
# 0001 - Decision Title

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD
Supersedes: none

## Context

## Options Considered

## Decision

## Consequences

## References
```

## Current Records

| Record | Status | Summary |
| --- | --- | --- |
| [0001 - Choose Keycloak for Validation](./0001-choose-keycloak-for-validation.md) | Accepted | Selects self-hosted Keycloak with a local access-control service as the Phase 3 candidate solution to validate. |

## References

- [Microsoft - Maintain an architecture decision record](https://learn.microsoft.com/en-ie/azure/well-architected/architect-role/architecture-decision-record)
- [ADR GitHub organization](https://adr.github.io/)
