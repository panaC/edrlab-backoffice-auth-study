# Abstract

This repository contains a technical study for an internal backoffice IAM control plane and authorization server.

The study evaluates whether the company should adopt a self-hosted open-source identity and authorization product, use a managed identity provider, build a minimal internal authorization server with maintained frameworks or libraries, or combine an identity provider with a custom administration layer.

The selected study architecture is:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IdP / Authorization Server / Admin Control Plane
    -> one or more backend API resource servers
```

The project focus is the central IdP / authorization server / admin control-plane component. The Backoffice BFF and backend API services are integration context used to define token, session, administration, and authorization boundaries.

The repository is now in Phase 2: requirements definition. Phase 2 should turn the Phase 1 IAM foundation into clearer business, technical, security, and operational requirements, without choosing a final vendor, product, architecture implementation, hosting model, database, or production stack.

The expected output remains a documented, evidence-based technical recommendation supported by comparison documents and minimal, non-production Proofs of Concept.

## Key Links

- [Project brief](./README.md)
- [Agent instructions](./AGENTS.md)
- [Documentation index](./docs/README.md)
- [Phase 2 requirements baseline](./docs/phase-2-requirements-baseline.md)
- [Phase 2 open-question triage](./docs/phase-2-open-question-triage.md)
- [Phase 2 service and permission inventory](./docs/phase-2-service-permission-inventory.md)
- [Phase 2 minimal PoC plan](./docs/phase-2-minimal-poc-plan.md)
- [Phase 1 working notes](./docs/phase-1-working-notes.md)
- [Evaluation framework](./docs/evaluation-framework.md)
- [Candidate shortlist](./docs/candidate-shortlist.md)
