# Keycloak WP-008 Result

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-23

## Contents

- [Summary](#summary)
- [How To Read This Review](#how-to-read-this-review)
- [Admin Console Boundary](#admin-console-boundary)
- [Operations Checklist](#operations-checklist)
- [Review Status](#review-status)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Summary

`WP-008` is a documentation-first review of the Keycloak Web Admin and self-hosted operations boundary. It does not add a new runtime scenario because the accepted validation plan defines this work package as documentation-first; the runtime work is already covered by `WP-001` through `WP-007` ([Keycloak validation plan - Work Packages](./keycloak-validation-plan.md#work-packages), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).

Result: review-ready boundary, with production operations still open. Keycloak Web Admin remains accepted only for Keycloak technical administration and inspection: realm configuration, OIDC clients, authentication flows, session/token settings, event settings, and non-production user setup. It is not accepted as the EDRLab business Access Control Manager for local account type, lifecycle, subject links, service-access roles, protected-service authorization, or project audit truth (`FR-001`, `FR-002`, `FR-020`, `FR-024`, `FR-027`, `FR-032`, `FR-036` through `FR-039`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Solution choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)).

## How To Read This Review

Read `WP-008` as a boundary and operations checklist, not as production approval. The PoC runtime uses Docker Compose and Keycloak `start-dev` for non-production validation; production adoption still requires a separate Phase 5 review and any later Phase 6 implementation decision ([Keycloak WP-001 result](./keycloak-wp001-result.md), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The key question is whether Keycloak administration can stay technical while local EDRLab access control remains authoritative. `WP-005` validated that Keycloak roles, groups, and claims do not override local account and authorization state; `WP-007` validated that Keycloak events remain supplemental to local audit examples ([Keycloak WP-005 result](./keycloak-wp005-result.md), [Keycloak WP-007 result](./keycloak-wp007-result.md)).

## Admin Console Boundary

| Area | Allowed in Keycloak Web Admin or Admin REST | Rejected for Keycloak Web Admin | Source |
| --- | --- | --- | --- |
| Realm and client administration | Configure the PoC realm, OIDC client, redirect URI, protocol mappers, and Keycloak-side technical settings. Keycloak documents the Admin Console as the place to configure realms and perform most administrative tasks. | Do not treat realm/client settings as the EDRLab account or service-access authorization model. | [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/#configuring-realms), [Keycloak integration scope](../architecture/keycloak-integration-scope.md#configuration-block) |
| Authentication flows and privileged authentication | Configure and inspect authentication flows, MFA, WebAuthn, OTP, and the AMR/evidence path selected for validation. | Do not activate invited `admin` or `super-admin` local accounts unless the local side can verify explicit privileged-authentication evidence. `WP-004` currently blocks that activation. | [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows), [Keycloak WP-004 result](./keycloak-wp004-result.md), `FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Keycloak user setup | Create or adjust throwaway Keycloak users for non-production validation. | Do not use Keycloak user attributes, groups, or roles as the durable EDRLab account type, lifecycle state, subject-link owner, or service-access role owner. | [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Keycloak WP-005 result](./keycloak-wp005-result.md), `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Roles, groups, and mappers | Use roles, groups, and mappers for Keycloak technical administration, PoC probes, or non-authoritative evidence. | Do not grant protected-service access, account-management authority, lifecycle changes, or audit bypass through Keycloak roles, groups, or claims. | [Keycloak integration scope - Role And Group Boundary](../architecture/keycloak-integration-scope.md#role-and-group-boundary), [Keycloak WP-005 result](./keycloak-wp005-result.md) |
| Sessions and tokens | Inspect and configure Keycloak SSO sessions, token lifetimes, logout behavior, and revocation controls for the authentication product. | Do not rely on an active Keycloak SSO session or token alone to grant EDRLab protected-service access after local lifecycle or role changes. | [Keycloak session and token timeouts](https://www.keycloak.org/docs/latest/server_admin/#session-and-token-timeouts), [Keycloak WP-006 result](./keycloak-wp006-result.md), `FR-016`, `FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| User and admin events | Enable and inspect Keycloak user/admin events as supplemental authentication and provider-administration evidence. | Do not replace the project-owned local audit stream with Keycloak events. Local audit remains authoritative for local decisions and audit-read authorization. | [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events), [Keycloak WP-007 result](./keycloak-wp007-result.md), `FR-027`, `FR-035`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Keycloak administrator accounts | Manage Keycloak technical administrators with least privilege and review server/realm administrator grants. Keycloak documents server administrators, realm administrators, and delegated realm administrators. | Do not equate Keycloak `admin` or `realm-admin` roles with EDRLab `admin` or `super-admin` account types. Keycloak warns that server and realm administrators are not affected by fine-grained realm-resource permissions. | [Keycloak realm administrators](https://www.keycloak.org/docs/latest/server_admin/#dedicated-realm-admin-consoles), [Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources), `FR-001`, `FR-026`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |

## Operations Checklist

| Topic | Phase 4 review result | Phase 5 or production-hardening question | Source |
| --- | --- | --- | --- |
| Production runtime | Not validated. The PoC runtime is non-production Docker Compose and Keycloak `start-dev`. | Decide the production runtime shape, TLS, hostname, reverse proxy, database, and availability posture before adoption. Keycloak production guidance covers TLS, hostname, reverse proxy, production database, clustering, and readiness behavior. | [Keycloak production configuration](https://www.keycloak.org/server/configuration-production), [Keycloak container guide](https://www.keycloak.org/server/containers), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp) |
| Configuration and secrets | Not validated beyond PoC environment files. | Choose a production configuration source and secret-handling pattern. Keycloak can read configuration from CLI parameters, environment variables, configuration files, and a Java KeyStore, with source precedence documented. | [Keycloak configuration](https://www.keycloak.org/server/configuration), `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Database | Not validated for production. The PoC uses Keycloak's development mode boundary. | Select and operate a supported production database, backup it directly, and test restore. Keycloak production guidance treats the database as crucial for performance, availability, reliability, and integrity. | [Keycloak production configuration](https://www.keycloak.org/server/configuration-production), [Keycloak database configuration](https://www.keycloak.org/server/db) |
| Realm import/export and backup | Not validated as backup/restore. | Do not treat Admin Console partial export as a backup. Keycloak documents that import/export has backup limitations: consistency requires stopping nodes, and exported data omits user/admin events, persisted sessions, workflow state, and revoked tokens. | [Keycloak importing and exporting realms](https://www.keycloak.org/server/importExport), `FR-030`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Key rotation | Not validated. | Define realm signing-key rotation, JWKS cache behavior, and client rollout handling. Keycloak documents active and passive keys so previous signatures can still be verified during rotation. | [Keycloak realm keys](https://www.keycloak.org/docs/latest/server_admin/#configuring-realm-keys), `FR-029`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Health and metrics | Not validated. | Decide whether and how to expose management-port health and metrics endpoints. Keycloak health and metrics endpoints are disabled by default and become available when the corresponding options are enabled. | [Keycloak health checks](https://www.keycloak.org/observability/health), [Keycloak metrics](https://www.keycloak.org/observability/configuration-metrics) |
| Admin surface exposure | Not validated. | Keep public login endpoints separate from administration endpoints. Keycloak production guidance says it is a best practice to expose Admin REST API and Console on a different hostname or context path and block REST APIs at the reverse proxy when they should not be public. | [Keycloak production configuration](https://www.keycloak.org/server/configuration-production), [Keycloak reverse proxy](https://www.keycloak.org/server/reverseproxy) |
| Event retention and export | Partially validated only as run-scoped PoC evidence. | Define retention/export for Keycloak events and local audit separately. Keycloak can record user/admin events, but project audit remains local and must satisfy `FR-027` and `FR-035`. | [Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events), [Keycloak WP-007 result](./keycloak-wp007-result.md) |
| Configuration drift | Not validated. | Decide how realm, client, mapper, flow, admin-role, event, and timeout changes are reviewed and reproduced. Drift could reintroduce claim override, weak privileged evidence, or missing audit/event settings. | [Keycloak validation plan - Readiness Gate](./keycloak-validation-plan.md#readiness-gate), [Threat model TS-008 and TS-013](../risks/threat-model.md#threat-scenarios) |
| Outage and failure mode | Partially validated only for local authorization/check fail-closed behavior in `WP-006`. | Define how login, token refresh, Keycloak outage, local authorization outage, audit-write failure, and protected-service behavior fail safely in production. | [Keycloak WP-006 result](./keycloak-wp006-result.md), [Threat model TS-012](../risks/threat-model.md#threat-scenarios) |

## Review Status

| Review item | Status | Evidence |
| --- | --- | --- |
| Keycloak Web Admin technical boundary | Pass for Phase 4 review | Boundary is recorded in the solution choice, integration scope, and this `WP-008` checklist. |
| Keycloak roles/groups/claims non-authoritative | Pass for Phase 4 review | `WP-005` produced misleading Keycloak evidence and local denial decisions ([Keycloak WP-005 result](./keycloak-wp005-result.md)). |
| Local audit authority with supplemental Keycloak events | Pass for Phase 4 review | `WP-007` produced local audit examples, supplemental Keycloak events, and expected audit gaps ([Keycloak WP-007 result](./keycloak-wp007-result.md)). |
| Privileged account activation | Blocked | `WP-004` found no usable AMR/flow evidence in the default PoC configuration, so local `admin` and `super-admin` activation remains blocked ([Keycloak WP-004 result](./keycloak-wp004-result.md)). |
| Production operations readiness | Open | Production runtime, database, backup/restore, key rotation, monitoring, admin-surface exposure, event retention/export, and drift controls are review inputs, not validated production artifacts. |

## Residual Risks

- Keycloak technical administrators could bypass or weaken the validation boundary by changing realm roles, protocol mappers, authentication flows, event settings, or admin grants unless production governance and change control are explicit ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources), [Threat model TS-013](../risks/threat-model.md#threat-scenarios)).
- Realm export alone is not a complete backup strategy because Keycloak documents omitted event, session, workflow, and revocation data; production recovery still needs direct database backup/restore planning and test evidence ([Keycloak importing and exporting realms](https://www.keycloak.org/server/importExport)).
- Keycloak event evidence can support correlation but cannot satisfy local append-only audit persistence, integrity, retention, export, privacy, or audit-read authorization by itself (`FR-027`, `FR-028`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-007 result](./keycloak-wp007-result.md)).
- Production `admin` and `super-admin` onboarding remains blocked until a configured privileged-authentication evidence path is validated (`FR-034`, `FR-043`, `FR-044`; [Keycloak WP-004 result](./keycloak-wp004-result.md)).

## Decision Impact

`WP-008` preserves the accepted candidate boundary for Phase 5 review: Keycloak can remain the authentication product and technical IAM administration surface, while EDRLab business access-control and audit truth stay local. It also makes self-hosted operations a material review topic rather than an implicit production approval ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## References

- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Keycloak WP-001 Result](./keycloak-wp001-result.md)
- [Keycloak WP-004 Result](./keycloak-wp004-result.md)
- [Keycloak WP-005 Result](./keycloak-wp005-result.md)
- [Keycloak WP-006 Result](./keycloak-wp006-result.md)
- [Keycloak WP-007 Result](./keycloak-wp007-result.md)
- [Solution Choice - Keycloak Web Admin Boundary](../evaluation/solution-choice.md#keycloak-web-admin-boundary)
- [Keycloak Integration Scope](../architecture/keycloak-integration-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Production Configuration](https://www.keycloak.org/server/configuration-production)
- [Keycloak Configuration](https://www.keycloak.org/server/configuration)
- [Keycloak Container Guide](https://www.keycloak.org/server/containers)
- [Keycloak Database Configuration](https://www.keycloak.org/server/db)
- [Keycloak Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [Keycloak Health Checks](https://www.keycloak.org/observability/health)
- [Keycloak Metrics](https://www.keycloak.org/observability/configuration-metrics)
- [Keycloak Reverse Proxy](https://www.keycloak.org/server/reverseproxy)
