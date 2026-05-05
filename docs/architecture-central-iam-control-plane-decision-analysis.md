# Architecture Decision Analysis: Central IAM Control Plane

## Purpose

This note analyzes why the study currently uses a central IAM Control Plane architecture for the internal backoffice. It is an analysis artifact, not an accepted production architecture decision.

## Decision Context

The project studies an IAM Control Plane for fewer than 1,000 internal backoffice users. The expected outcome is a documented, evidence-based recommendation supported by comparison documents and minimal Proofs of Concept, not a production-ready IAM system.

The main question is whether the backoffice IAM responsibilities should live in one application-owned backend or in a central component that provides identity provider, authorization server, administration, and audit-control-plane behavior.

## Current Baseline

The current study baseline is:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IAM Control Plane (IdP / Authorization Server / Admin Control Plane)
    -> one or more backend API resource servers
```

The IAM Control Plane is the source of truth for members, roles, permissions, clients, token contracts, key metadata, and IAM audit events. The BFF owns browser sessions and OIDC callback handling. Backend APIs validate tokens and enforce operation-level permissions.

## Decision To Make

Decide whether the project should continue evaluating a central IAM Control Plane architecture, or narrow the architecture to a simpler application-owned authentication and authorization model.

This decision remains study-scoped. It does not choose a product, vendor, database, hosting model, or production implementation stack.

## Options Considered

| Option | Summary |
| --- | --- |
| Central IAM Control Plane | Separate central component owns login, token issuance, IAM state, admin API behavior, and auditability. |
| Application-owned auth model | One backoffice backend owns local login, sessions, members, roles, permissions, and audit logs. |
| Workforce SSO plus local authorization | A corporate IdP handles login while the backoffice owns local roles, permissions, and admin behavior. |
| Gateway-authenticated access | A trusted reverse proxy or access gateway authenticates users before the app. |
| Custom token/session system | The team builds enough authentication, session, and token behavior directly. |

## Evaluation Criteria

| Criterion | Why it matters |
| --- | --- |
| Boundary clarity | The architecture must make it clear who owns login, sessions, tokens, roles, permissions, and business data. |
| API protection | Backend APIs must validate credentials and enforce permissions server-side. |
| Member lifecycle | Administrators must create, disable, restore, and review internal members without public registration. |
| Auditability | Privileged IAM changes must be attributable and reviewable. |
| Operational proportionality | Complexity must be justified for fewer than 1,000 users. |
| Candidate comparability | Managed, self-hosted, minimal-library, and hybrid options need a common evaluation shape. |
| Future fit | Service-to-service authentication and multiple resource servers are future topics, not first-PoC blockers. |

## Option Analysis

| Option | Strengths | Limitations |
| --- | --- | --- |
| Central IAM Control Plane | Strong boundary for IAM state, token issuance, admin API behavior, and audit events. Fits multiple protected APIs and product-neutral comparison. | Adds OAuth/OIDC, client, key, token, and operations complexity that must be justified. |
| Application-owned auth model | Simpler for one server-rendered internal application with one backend and one database. Avoids separate authorization-server operation. | The team owns password policy, session security, optional MFA, recovery, audit integrity, and all auth implementation details. Poorer fit for multiple independent APIs. |
| Workforce SSO plus local authorization | Delegates login, MFA, and workforce lifecycle if an enterprise IdP exists. | No enterprise SSO is assumed today; adopting one is itself an IAM and operations decision. Local roles, permissions, admin API behavior, and audit mapping still remain. |
| Gateway-authenticated access | Can be simple for coarse app-level access. | Usually insufficient for operation-level authorization in a privileged admin API unless combined with server-side permission checks. |
| Custom token/session system | Can be tailored and minimal. | High risk of weak token validation, poor key rotation, bad revocation behavior, and fragile incident response. |

## Trade-Off Summary

The central IAM Control Plane architecture is more complex than a single application-owned model. Its value comes from explicit separation of IAM authority, browser session handling, protected API access, administration controls, and audit evidence.

The application-owned model remains a useful scope guard. If the real scope collapses to one internal app, one backend, no independent APIs, and no provider interoperability need, it may be the simpler option to evaluate.

## Risks And Unknowns

- The central architecture may overfit a small backoffice if there is only one backend application.
- The team may underestimate the operational cost of an authorization server, client management, signing keys, token lifecycles, and audit retention.
- A managed or self-hosted candidate may not expose enough admin API, audit, SQLite, or operational behavior to satisfy the requirements.
- A local-only model may look simple while hiding password, MFA, recovery, session, and audit responsibilities.

## Evidence Needed

- Candidate evidence for OIDC login, admin API coverage, RBAC behavior, audit events, and operations.
- A minimal PoC proving BFF login, token validation, permission enforcement, and access-removal latency.
- A clearer inventory of real backend services and whether they need independent resource-server boundaries.
- Ownership decision for IAM operations before production.

## Current Working Position

The current working position is to keep the central IAM Control Plane architecture as the study baseline. This is not a final production recommendation. It is the architecture shape used for Phase 2 requirements definition and later candidate evaluation.

## Open Questions

- Is there truly more than one protected backend API boundary, or only one internal application?
- Who will own IAM operations, incident response, backups, key rotation, and access reviews?
- Which candidates can satisfy the admin API and audit requirements without excessive customization?
- What is the smallest PoC that proves the central architecture adds useful evidence?

## Related Documents

- [Project README](../README.md)
- [Requirements Baseline](./requirements-baseline.md)
- [Requirements Question Register](./requirements-question-register.md)
- [Minimal Backoffice IAM Architecture](./architecture-minimal-backoffice-iam.md)
- [Evaluation Framework](./evaluation-framework.md)
- [Security Threat Model](./security-threat-model.md)
