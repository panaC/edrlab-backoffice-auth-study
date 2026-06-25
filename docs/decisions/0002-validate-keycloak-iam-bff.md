# 0002 - Validate Keycloak IAM With EDRLab BFF

Status: Accepted
Date: 2026-06-23
Supersedes: 0001-choose-keycloak-for-validation.md for the validation boundary

## Context

ADR 0001 selected self-hosted Keycloak with a local EDRLab access-control service as the Phase 3 validation candidate. In that boundary, Keycloak authenticated users and emitted provider-side evidence, while local EDRLab state remained authoritative for account type, lifecycle, service-access roles, protected-service authorization, and project audit ([ADR 0001](./0001-choose-keycloak-for-validation.md)).

After reviewing whether `FR-038` could be bypassed, the user selected a new direction on 2026-06-23: validate Keycloak as the candidate IAM source for the business access-control state, with an EDRLab Admin Console and BFF/Admin API as the controlled business administration facade. This remains a validation direction, not production approval ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

Keycloak can manage users, roles, groups, clients, authentication flows, sessions, and events through its Admin Console and Admin REST API. Keycloak also documents Authorization Services for resource, scope, permission, policy, PDP, PEP, and PAP-style authorization modeling ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)).

## Options Considered

| Option | Result | Notes |
| --- | --- | --- |
| Keep ADR 0001 unchanged: Keycloak authentication plus local access-control authority | Superseded for the next validation direction. | This model has strong Phase 4 evidence from `WP-001` through `WP-009`, but the user now prefers exploring Keycloak as the IAM authority. |
| Use Keycloak IAM state with an EDRLab BFF/Admin API facade | Chosen for validation. | The BFF can preserve EDRLab workflows and invariants while using Keycloak users, roles, groups, attributes, Admin REST, and possibly Authorization Services as the backing IAM model. |
| Expose Keycloak Admin Console directly as the business Access Control Manager | Rejected. | Direct business administration through Keycloak Admin Console would make EDRLab invariants and audit harder to control. Keycloak warns that server and realm administrators are not affected by fine-grained realm-resource permissions, so administrative grants must be reviewed carefully ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). |

## Decision

Validate self-hosted Keycloak as the candidate IAM source for backoffice account and service-access state, with a dedicated EDRLab Admin Console and BFF/Admin API as the business administration surface.

This decision means:

- Keycloak may become the backing store and policy source for users, account-type representation, lifecycle representation, service-access role representation, authentication policy, sessions, and provider-side events, subject to validation ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)).
- The EDRLab Admin Console should not send business administrators directly to Keycloak Admin Console. It should call a server-side EDRLab BFF/Admin API that enforces the EDRLab invariants and invokes Keycloak Admin REST or approved Keycloak policy APIs ([Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), `FR-024`, `FR-033`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
- `FR-038` is no longer a blanket ban on using IAM roles, groups, attributes, or claims as business state. It is now the anti-bypass rule: those IAM values may be authoritative only through the controlled server-side administration and authorization path; raw token claims, frontend checks, protected-service shortcuts, and unmanaged console edits must not bypass that path.
- The previous `WP-005` claim-override result remains useful as negative evidence for unsafe shortcut behavior, but the new validation must prove the approved mapping from Keycloak IAM state to EDRLab business behavior rather than rejecting every Keycloak role/group/claim by default.
- Local audit may still be needed for EDRLab business decisions because Keycloak events can support provider-side correlation but do not automatically prove every EDRLab business decision or audit-read authorization requirement (`FR-027`, `FR-028`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

## Consequences

The Phase 4 evidence from `WP-001` through `WP-009` remains valid for the previous boundary, but it is not enough to approve the new Keycloak-IAM-backed direction. The next validation work should prove:

- how `super-admin`, `admin`, and `member` account types are represented in Keycloak without allowing account-type mutation or self-elevation (`FR-001`, `FR-026`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements));
- how lifecycle states are represented and how disabled or archived accounts stop protected-service access (`FR-011` through `FR-016`);
- how service-access roles are represented and assigned only to `member` accounts while active admins and super-admins receive covered protected-service access (`FR-002` through `FR-005`, `FR-032`);
- how the EDRLab BFF prevents direct Keycloak Admin Console drift from bypassing business workflows, server-side authorization, and audit (`FR-024`, `FR-027`, `FR-033`, `FR-038`);
- how protected backend services authorize safely: through the BFF, Keycloak Authorization Services, token claims with explicit freshness limits, introspection, or another reviewed contract (`FR-020`, `FR-021`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html));
- how privileged authentication evidence for `admin` and `super-admin` activation is configured and verified (`FR-034`, `FR-043`, `FR-044`; [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows));
- which audit records remain in Keycloak events and which require a local EDRLab audit store (`FR-027`, `FR-028`, `FR-035`; [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)).

This ADR does not approve production implementation, production deployment, production database topology, CI, migrations, or application code. It changes the validation direction and requirements interpretation that the next Phase 4/Phase 5 artifacts must use.

## References

- [ADR 0001 - Choose Keycloak for Validation](./0001-choose-keycloak-for-validation.md)
- [Keycloak IAM BFF Scope](../architecture/keycloak-iam-bff-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Authorization Services](https://www.keycloak.org/docs/latest/authorization_services/)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

