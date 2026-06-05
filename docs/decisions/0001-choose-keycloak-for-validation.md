# 0001 - Choose Keycloak for Validation

Status: Accepted
Date: 2026-06-05
Supersedes: none

## Context

The project is in Phase 3 - Solution Choice. Phase 3 may choose a candidate solution to validate, but the choice is not production approval and must not start implementation work unless it is explicitly scoped as a non-production PoC ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

The current shortlist contains Auth0 managed login plus local access-control, self-hosted Keycloak plus local access-control, and a Spring-based local IAM control plane ([Solution choice](../evaluation/solution-choice.md#shortlist), [Concrete technical solution candidates](../evaluation/technical-solutions.md#selection-basis)). The user selected Keycloak as the solution choice on 2026-06-05.

The access-control feature model still requires the local backoffice capability to own account type, lifecycle state, authenticated-subject link, service-access roles, protected-service authorization, and project audit evidence. Identity-provider roles, groups, or claims must not override the local authorization model (`FR-001`, `FR-002`, `FR-036` through `FR-039`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Options Considered

| Option | Result | Notes |
| --- | --- | --- |
| Auth0 managed login plus local access-control | Not chosen for the current validation candidate. | Lower local authentication ownership, but the user selected the self-hosted Keycloak direction; Auth0 remains useful as a managed-provider comparison reference ([Solution choice - Comparison Pass 1](../evaluation/solution-choice.md#comparison-pass-1)). |
| Self-hosted Keycloak plus local access-control | Chosen for validation. | Keycloak documents OIDC/OAuth2 administration, WebAuthn/two-factor/passwordless behavior, events, and Admin REST APIs; local access-control remains authoritative ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Solution choice - Selected Candidate](../evaluation/solution-choice.md#selected-candidate)). |
| Spring-based local IAM control plane | Not chosen for the current validation candidate. | Strong local control path, but it carries the highest protocol and security ownership burden; it remains a comparison reference for access-stop and introspection behavior ([Spring Authorization Server overview](https://docs.spring.io/spring-authorization-server/reference/overview.html), [Solution choice - Comparison Pass 1](../evaluation/solution-choice.md#comparison-pass-1)). |

## Decision

Choose self-hosted Keycloak with a local EDRLab access-control service as the Phase 3 candidate solution to validate.

This decision means:

- Keycloak is the candidate authentication product and OIDC/OAuth2 runtime to validate, not the source of truth for EDRLab account types, lifecycle state, service-access roles, or audit requirements ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), `FR-038`).
- The local EDRLab access-control service remains authoritative for the project authorization model and must enforce protected-service authorization server-side (`FR-020`, `FR-021`, `FR-033`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).
- Keycloak roles, groups, claims, and admin features may support authentication, realm configuration, or provider-side evidence, but they must not replace the local account-type and service-access-role model (`FR-001`, `FR-002`, `FR-038`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
- Keycloak events may supplement local audit evidence, but local append-only audit remains required for the project event set (`FR-027`, `FR-035`; [Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events)).

## Consequences

The next work should focus on Keycloak-specific validation rather than broad market comparison.

Required validation conditions:

- define the protected-service authorization contract so protected services do not authorize directly from Keycloak roles, groups, mutable email, or frontend state (`FR-020`, `FR-021`, `FR-038`; [Threat model TS-006 and TS-008](../risks/threat-model.md#threat-scenarios));
- verify how Keycloak will provide or support privileged-authentication evidence for production `admin` and `super-admin` onboarding (`FR-034`, `FR-043`, `FR-044`; [Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn));
- define access-stop behavior after account disablement, archival, member role removal, or service-access-role disablement or archival (`FR-016`, `FR-032`; [Threat model RC-003](../risks/threat-model.md#requirement-refinement-candidates));
- define audit correlation between local access-control events, protected-service denials, and Keycloak authentication or admin events (`FR-027`, `FR-035`; [Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events));
- define self-hosting operational evidence for backup, restore, upgrade, realm configuration, key rotation, event retention, support/export access, and outage behavior (`FR-030`; [Threat model TS-012 and TS-013](../risks/threat-model.md#threat-scenarios)).

This ADR does not approve production adoption, production deployment, database choice, hosting choice, implementation stack, token format, browser storage, or CI/deployment work. Those remain later PoC, review, or production MVP decisions ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## References

- [Solution Choice](../evaluation/solution-choice.md)
- [Concrete Technical Solution Candidates](../evaluation/technical-solutions.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Project Governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Spring Authorization Server - Overview](https://docs.spring.io/spring-authorization-server/reference/overview.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
