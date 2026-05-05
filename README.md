# Internal Backoffice IAM Control Plane Study

This repository contains a technical study for implementing an **IAM Control Plane** for a company's internal backoffice. In this study, IAM Control Plane means the central **IdP / Authorization Server / Admin Control Plane** component.

The study must help the company decide whether to:

- adopt a self-hosted open-source identity and authorization solution;
- use a managed identity provider;
- build a minimal internal IAM Control Plane using existing frameworks or libraries;
- combine existing identity components with a custom administration layer.

The expected outcome is not a production-ready IAM Control Plane. The expected outcome is a documented, evidence-based technical recommendation supported by comparison documents and minimal Proofs of Concept.

## Selected Study Architecture

The study now uses the **Central IAM Control Plane Architecture**:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IAM Control Plane (IdP / Authorization Server / Admin Control Plane)
    -> one or more backend API resource servers
```

The focus of this project is the **IAM Control Plane** component. The Backoffice BFF, meaning Backend-for-Frontend, and backend API services are treated as integration context: they define the token, session, administration, and authorization boundaries that the IAM Control Plane must support. The first study and minimal Proof of Concept can use one demonstration API resource server.

The study does not choose a final product, vendor, database, hosting model, or implementation stack yet.

## Business and Technical Requirements

The detailed, ID-based requirements source is the [Requirements baseline](./docs/requirements-baseline.md). At project-brief level, the IAM Control Plane must support:

- OAuth2/OIDC-compatible login for internal backoffice users;
- administrator-managed member lifecycle with no public registration;
- Role-Based Access Control (RBAC) with explicit permissions where needed;
- a REST administration API for members, roles, permissions, service access checks, and audit-supporting operations;
- backend API protection through token validation and server-side permission checks;
- auditability for privileged administration operations.

Service-to-service authentication is a future extension topic, not part of the first study or minimal Proof of Concept scope.

The minimum administration API capability set is tracked by `API-003` in the requirements baseline. Access-check behavior is tracked by `API-004`.

## Project Constraints

- Keep the solution simple, efficient, and maintainable.
- Target fewer than 1,000 users.
- Compare self-hosted and managed options.
- Prefer open-source components when relevant.
- If self-hosted, prefer SQLite where realistic.
- Do not expose public account registration.
- Users must be created and managed by administrators.
- RBAC is required.
- The solution must remain understandable and operable by the internal team.
- Avoid unnecessary enterprise IAM complexity.
- Avoid over-engineering for the expected scale.
- Administration operations must be auditable.
- Operational complexity must be justified by concrete security, compliance, maintainability, or product needs.

## Scope

In scope for the study:

- the selected micro-service architecture shape with a Backoffice BFF (Backend-for-Frontend), a central IAM Control Plane, and one or more backend API resource servers;
- the responsibilities, API boundaries, token boundaries, and data ownership of the IAM Control Plane;
- internal member lifecycle management;
- administrator-only account creation and access management;
- OAuth2/OIDC-based authentication and authorization patterns;
- RBAC and permission modeling for backoffice services;
- API protection and token validation;
- service-to-service authentication as a future theoretical extension;
- administration API shape, risks, and controls;
- auditability, access reviews, and operational ownership;
- self-hosted, managed, minimal-library, and hybrid options as later study candidates.

Out of scope:

- implementing the Backoffice BFF, backend API services, or service databases except as minimal Proof-of-Concept integration stubs where needed;
- public customer identity;
- public self-service registration;
- company-wide workforce IAM or SSO beyond the internal backoffice scope;
- social login;
- consumer marketing account flows;
- multi-tenant external SaaS identity requirements;
- service-to-service implementation in the first study or minimal Proof of Concept;
- a complete custom cryptographic or IAM implementation.

## Roadmap

1. Phase 1 - Document the IAM concepts needed to reason about the IdP / Authorization Server / Admin Control Plane.
2. Phase 2 - Define the business, technical, security, and operational requirements, and resolve open questions.
3. Phase 3 - Catalog self-hosted, managed, minimal-library, and hybrid solution approaches.
4. Phase 4 - Evaluate shortlisted solutions using lightweight Proofs of Concept where needed, and record the evaluation results.
5. Phase 5 - Define the specification for a minimum viable IAM Control Plane.
6. Phase 6 - Build a non-production MVP covering the specification, with tests.
7. Phase 7 - Produce a final evidence-based technical recommendation.

## Documentation

- [Abstract](./ABSTRACT.md)
- [Changelog](./CHANGELOG.md)
- [Documentation index](./docs/README.md)
- [Requirements baseline](./docs/requirements-baseline.md)
- [Requirements question register](./docs/requirements-question-register.md)
- [Minimal backoffice IAM architecture notes](./docs/architecture-minimal-backoffice-iam.md)
- [Threat Model](./docs/security-threat-model.md)
- [Evaluation framework](./docs/evaluation-framework.md)
- [IAM documentation wiki](./docs/wiki/README.md)
