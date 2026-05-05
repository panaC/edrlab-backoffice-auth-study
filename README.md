# Internal Backoffice Authorization Server Study

This repository contains a technical study for implementing an authorization server for a company's internal backoffice.

The study must help the company decide whether to:

- adopt a self-hosted open-source identity and authorization solution;
- use a managed identity provider;
- build a minimal internal authorization server using existing frameworks or libraries;
- combine existing identity components with a custom administration layer.

The expected outcome is not a production-ready authorization server. The expected outcome is a documented, evidence-based technical recommendation supported by comparison documents and minimal Proofs of Concept.

## Selected Study Architecture

The study now uses the **Central IAM Control Plane Architecture**:

```text
Backoffice BFF (Backend-for-Frontend)
    -> IdP / Authorization Server / Admin Control Plane
    -> one or more backend API resource servers
```

The focus of this project is the **IdP / Authorization Server / Admin Control Plane** component. The Backoffice BFF, meaning Backend-for-Frontend, and backend API services are treated as integration context: they define the token, session, administration, and authorization boundaries that the central IAM component must support. The first study and minimal Proof of Concept can use one demonstration API resource server.

The study does not choose a final product, vendor, database, hosting model, or implementation stack yet.

## Business and Technical Requirements

The authorization server must support:

- OAuth2 authentication and authorization flows;
- OpenID Connect for user identity;
- authentication of internal backoffice users;
- Role-Based Access Control (RBAC);
- member and user management;
- administration by internal administrators only;
- a REST administration API for managing users, roles, permissions, and service access;
- access control for internal backoffice services.

Service-to-service authentication is a future extension topic, not part of the first study or minimal Proof of Concept scope.

The administration API should support, at minimum:

- creating a member;
- reading member details;
- updating member details;
- disabling or deleting a member;
- creating roles;
- assigning roles to members;
- removing roles from members;
- listing roles;
- listing members;
- checking whether a member has access to a given backoffice service.

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

- the selected micro-service architecture shape with a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/control plane, and one or more backend API resource servers;
- the responsibilities, API boundaries, token boundaries, and data ownership of the IdP/authorization server/control plane;
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

1. Document the IAM concepts needed to reason about the authorization server.
2. Define the business, technical, security, and operational requirements.
3. Compare self-hosted, managed, minimal-library, and hybrid approaches.
4. Build a minimal Proof of Concept covering the narrowed study scope.
5. Produce a final evidence-based technical recommendation.

## Documentation

- [Phase 1 working notes](./docs/phase-1-working-notes.md)
- [Documentation index](./docs/README.md)
- [Minimal backoffice IAM architecture notes](./docs/minimal-backoffice-iam-architecture.md)
- [BFF Sessions and Token Handling](./docs/bff-sessions-and-token-handling.md)
- [Member Lifecycle](./docs/member-lifecycle.md)
- [Evaluation framework](./docs/evaluation-framework.md)
- [Candidate shortlist](./docs/candidate-shortlist.md)
- [IAM documentation wiki](./docs/wiki/README.md)
- [Authentication vs Authorization](./docs/wiki/01-authentication-vs-authorization.md)
- [OAuth2](./docs/wiki/02-oauth2.md)
- [OpenID Connect](./docs/wiki/03-openid-connect.md)
- [Tokens and JWTs](./docs/wiki/04-tokens-and-jwt.md)
- [RBAC](./docs/wiki/05-rbac.md)
- [OAuth2 Flows](./docs/wiki/06-oauth2-flows.md)
- [Service-to-Service Authentication](./docs/wiki/07-service-to-service-authentication.md)
- [Administration APIs](./docs/wiki/08-admin-api.md)
- [Security Best Practices](./docs/wiki/09-security-best-practices.md)
- [Auditability, Access Reviews, and Operational Ownership](./docs/wiki/10-auditability-access-reviews-operational-ownership.md)
- [MFA, 2FA, Passwordless, and One-Time Passwords](./docs/wiki/11-mfa-2fa-passwordless-and-otp.md)
- [Administrator Authentication Policy](./docs/administrator-authentication-policy.md)
