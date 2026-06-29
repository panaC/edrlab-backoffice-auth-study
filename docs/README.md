# Project Documentation Map

This is the compact navigation map for project-facing documentation. It is
organized around the current Phase 6 access-control MVP so agents and reviewers
can avoid loading historical material unless they need provenance.

## Current Reading Path

| Need | Read |
| --- | --- |
| MVP boundary, accepted scope, readiness gaps | [MVP scope](./evaluation/mvp-scope.md) |
| Runtime commands, evidence, backup, restore, stop/reset | [Access-control runtime runbook](../access-control/README.md) |
| IAM routes, payloads, schemas, and errors | [IAM Control Plane API contract](./architecture/iam-control-plane-api-contract.md) |
| Keycloak/IAM onboarding flow | [Keycloak/IAM onboarding](./architecture/keycloak-iam-onboarding.md) |
| `authorization/check` behavior | [Authorization check behavior](./architecture/authorization-check-behavior.md) |
| Audit storage architecture | [Audit storage architecture](./architecture/audit-storage.md) |
| Keycloak managed schema and drift policy | [Keycloak IAM schema policy](./architecture/keycloak-iam-schema-policy.md) |
| Security evidence status | [MVP security test plan](./evaluation/security-test-plan.md) |
| Feature scope or behavior questions | [Feature requirements](../FEATURE-REQUIREMENTS.md) |
| Documentation-heavy rules and citation policy | [Agent documentation policy](./agent-policy.md) |

## Historical Material

Do not read these by default. Use them only for decision provenance, earlier
phase reconstruction, or when a current document explicitly sends you there.

| Location | Contains |
| --- | --- |
| `docs/poc/` | Phase 4 validation plans and WP result notes. |
| `docs/decisions/` | ADR history, including superseded decisions. |
| `docs/requirements/` | Requirements consolidation and review trails. |
| `docs/risks/` | Earlier risk and threat-model material. |
| `docs/evaluation/phase-5-review-note.md` | Phase 5 closure note and historical gate context. |
| `CHANGELOG.archive.md` | Older changelog entries; do not read by default. |
| `docs/wiki/` | Conceptual IAM background, not project runtime authority. |

For historical lookup, prefer targeted search:

```bash
rg "term" docs
```

## Folder Map

| Folder | Use |
| --- | --- |
| `architecture/` | Current architecture behavior, API contracts, and policy. |
| `evaluation/` | Current MVP scope and evidence trackers, plus historical evaluation notes. |
| `decisions/` | ADR-style project or architecture decisions. |
| `poc/` | Non-production validation material from earlier phases. |
| `requirements/` | Requirements traceability and review history. |
| `risks/` | Threat and risk analysis. |
| `wiki/` | General IAM concepts and source-backed explanations. |

## Document Rules

Current Phase 6 runtime work should prefer the active reading path above. For
documentation-heavy tasks, follow [docs/agent-policy.md](./agent-policy.md).
That file owns citation rules, wiki placement, study-document metadata, and
long-form writing guidance.

This map follows a task-oriented documentation structure: Diataxis recommends
organizing documentation around user needs, and arc42 is a pragmatic reference
for architecture communication structure ([Diataxis](https://diataxis.fr/),
[arc42 overview](https://arc42.org/overview)).

## References

- [Diataxis](https://diataxis.fr/)
- [arc42 Template Overview](https://arc42.org/overview)
- [Agent documentation policy](./agent-policy.md)
- [MVP scope](./evaluation/mvp-scope.md)
