# Abstract

This repository contains a technical study for an internal backoffice IAM Control Plane.

The study evaluates whether the company should adopt a self-hosted open-source identity and authorization product, use a managed identity provider, build a minimal internal IAM Control Plane with maintained frameworks or libraries, or combine an identity provider with a custom administration layer.

The selected study architecture is:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IAM Control Plane (IdP / Authorization Server / Admin Control Plane)
    -> one or more backend API resource servers
```

The project focus is the central IAM Control Plane. The Backoffice BFF and backend API services are integration context used to define token, session, administration, and authorization boundaries.

The repository is in Phase 2: requirements definition.

As of 2026-05-05, the Phase 2 baseline is established through a consolidated requirements baseline, open-question register, architecture notes, security and operational study documents, and an evaluation framework. The next work is to resolve or accept defaults for high-impact open questions, refine candidate-evaluation evidence, and plan focused non-production PoCs where documentation alone cannot answer a material requirement.

Phase 2 remains product-neutral. It should refine business, technical, security, and operational requirements without choosing a final vendor, product, architecture implementation, hosting model, database, or production stack.

The expected output remains a documented, evidence-based technical recommendation supported by comparison documents and minimal, non-production Proofs of Concept.

## Key Links

- [Project brief](./README.md)
- [Agent instructions](./AGENTS.md)
- [Documentation index](./docs/README.md)
- [Requirements baseline](./docs/requirements-baseline.md)
- [Open questions](./docs/open-questions.md)
- [Minimal backoffice IAM architecture notes](./docs/minimal-backoffice-iam-architecture.md)
- [Administrator authentication policy](./docs/administrator-authentication-policy.md)
- [Study notes](./docs/study-notes.md)
- [Evaluation framework](./docs/evaluation-framework.md)
