# Solution Choice

Status: Accepted
Phase: Phase 3 - Solution Choice
Scope: Evaluation
Last reviewed: 2026-06-05

## Contents

- [Purpose](#purpose)
- [Phase 3 Inputs](#phase-3-inputs)
- [Shortlist](#shortlist)
- [Decision Criteria](#decision-criteria)
- [Evidence Snapshot](#evidence-snapshot)
- [Comparison Pass 1](#comparison-pass-1)
- [Selected Candidate](#selected-candidate)
- [Decision Gate](#decision-gate)
- [Conditions and Open Evidence](#conditions-and-open-evidence)
- [Next Phase 3 Work](#next-phase-3-work)
- [References](#references)

## Purpose

This document is the Phase 3 working entry point for choosing the candidate solution to validate for the EDRLab backoffice access-control capability. Phase 3 may compare a focused shortlist and choose a candidate solution, but that choice is not production approval and must not start implementation work unless the user explicitly scopes a non-production PoC or moves the project to Phase 6 ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The existing three-candidate shortlist was used as the decision set. The governance boundary explicitly discourages broad market survey work when the existing shortlist is sufficient to decide ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Concrete technical solution candidates](./technical-solutions.md#selection-basis)).

## Phase 3 Inputs

| Source | Phase 3 use |
| --- | --- |
| [README.md](../../README.md) | Confirms the project goal, scale, actor model, initial scope, and open study questions for the access-control study. |
| [FEATURE-REQUIREMENTS.md](../../FEATURE-REQUIREMENTS.md) | Provides the `FR-*` requirements that every candidate must satisfy before it can be chosen. |
| [Threat model](../risks/threat-model.md) | Supplies the main risk pressures that the chosen candidate must answer, especially stale access, claim override, onboarding takeover, authorization bypass, audit gaps, unsafe failure modes, and operational bypass. |
| [Architecture options](../architecture/options.md) | Provides architecture families and cross-option implications without making a final decision. |
| [Concrete technical solution candidates](./technical-solutions.md) | Provides the current shortlist and candidate-specific evaluation questions. |

## Shortlist

| Candidate | Phase 3 evaluation focus | Source |
| --- | --- | --- |
| Auth0 managed login with local access-control service | Validate whether managed OIDC login, MFA/passwordless policy, provider logs, and local authorization can preserve the backoffice account model without IdP claim override. | [Technical solutions - Solution 1](./technical-solutions.md#solution-1---auth0-managed-login-with-local-access-control-service) |
| Self-hosted Keycloak with local access-control service | Validate whether self-hosted OIDC, WebAuthn/OTP configuration, events, backups, upgrades, and local authorization remain operable and auditable at the expected scale. | [Technical solutions - Solution 2](./technical-solutions.md#solution-2---self-hosted-keycloak-with-local-access-control-service) |
| Spring-based local IAM control plane | Validate whether local protocol ownership, introspection or authorization checks, access-stop behavior, audit correlation, and operational responsibility are justified by the project needs. | [Technical solutions - Solution 3](./technical-solutions.md#solution-3---spring-based-local-iam-control-plane) |

Chosen candidate: self-hosted Keycloak with a local access-control service, accepted by user direction on 2026-06-05 and recorded in [ADR 0001](../decisions/0001-choose-keycloak-for-validation.md).

## Decision Criteria

| ID | Criterion | What must be shown | Source |
| --- | --- | --- | --- |
| SC-001 | Local authorization authority | The candidate keeps account type, lifecycle state, authenticated-subject link, service-access roles, and audit requirements authoritative in the backoffice access-control capability. | `FR-001`, `FR-002`, `FR-036` through `FR-039` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [Threat model TS-008](../risks/threat-model.md#threat-scenarios) |
| SC-002 | Server-side enforcement | Admin operations and protected-service access are authorized server-side and fail closed when the result cannot be determined safely. | `FR-020`, `FR-021`, `FR-033` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| SC-003 | Access-stop behavior | The candidate can define and test an acceptable delay for stopping already-issued access after lifecycle or service-access-role changes. | `FR-016`, `FR-032` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [Threat model RC-003](../risks/threat-model.md#requirement-refinement-candidates) |
| SC-004 | Privileged-authentication evidence | The candidate can provide evidence that production `admin` and `super-admin` onboarding satisfied MFA or phishing-resistant passwordless authentication. | `FR-034`, `FR-043`, `FR-044` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) |
| SC-005 | Audit ownership and correlation | The candidate preserves project-owned audit records and can correlate provider, local access-control, and protected-service events where applicable. | `FR-027`, `FR-028`, `FR-035` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [Threat model TS-011](../risks/threat-model.md#threat-scenarios) |
| SC-006 | Operational fit | The candidate keeps complexity justified for fewer than 1,000 internal users and makes backup, restore, support export, migration, upgrade, outage, and lock-in risks visible. | [README - Project Goal](../../README.md#project-goal), `FR-030` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)); [Threat model TS-012 and TS-013](../risks/threat-model.md#threat-scenarios) |
| SC-007 | PoC value | The candidate has a tight non-production validation path for the uncertainties that documentation alone cannot settle. | [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept); [Architecture options - PoC and evaluation implications](../architecture/options.md#poc-and-evaluation-implications) |

## Evidence Snapshot

These notes capture the first Phase 3 source check. They use official product or framework documentation only where product behavior matters. They do not settle pricing, plan, tenant, hosting, data-residency, retention, support, or operational ownership questions.

| Candidate | Source-backed evidence useful for comparison | Phase 3 implication | Still open |
| --- | --- | --- | --- |
| Auth0 managed login with local access-control service | Auth0 documents MFA factors including OTP, WebAuthn security keys, WebAuthn device biometrics, and recovery codes, with factor availability depending on subscription plan ([Auth0 MFA factors](https://auth0.com/docs/secure/multi-factor-authentication/multi-factor-authentication-factors)). Auth0 also documents tenant logs for administrator actions, Management API operations, authentications, and Management API correlation through `X-Correlation-ID` ([Auth0 logs](https://auth0.com/docs/deploy-monitor/logs)). Auth0 RBAC roles and permissions can be managed through the Dashboard or Management API ([Auth0 RBAC roles](https://auth0.com/docs/manage-users/access-control/configure-core-rbac/roles)). | Auth0 can be evaluated as an authentication and evidence provider while keeping EDRLab account type, lifecycle, service-access roles, and audit requirements local. Auth0 RBAC is useful context but must not become authoritative for the local backoffice authorization model under `FR-038` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Subscription-plan constraints, tenant/data location, log retention/export, Management API limits, exact MFA evidence shape, outage handling, and lock-in. |
| Self-hosted Keycloak with local access-control service | Keycloak documents WebAuthn policy and credential registration behavior, including passwordless and two-factor use in realm authentication flows ([Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn)). Keycloak also documents user/admin event configuration and retrieval, including enabling admin event details and fetching events ([Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events)). The Keycloak Admin REST API is a documented management surface ([Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)). | Keycloak can be evaluated as a self-hosted OIDC/authentication product with configurable privileged-authentication and event evidence, while local access-control remains authoritative. | Hosting, upgrades, backups, restore tests, key rotation, event retention, admin API protection, realm drift, support access, and whether self-hosting/control is a real project constraint. |
| Spring-based local IAM control plane | Spring Authorization Server is documented as a framework for building OAuth/OIDC authorization server and identity-provider products, with support for JWT and opaque token formats and endpoints including token introspection, revocation, metadata, JWK Set, OIDC provider configuration, logout, UserInfo, and client registration ([Spring Authorization Server overview](https://docs.spring.io/spring-authorization-server/reference/overview.html)). Spring Security documents opaque-token resource-server support where a resource server queries an introspection endpoint and checks for `active: true`, which is relevant when revocation is required ([Spring Security opaque token resource server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/opaque-token.html)). | Spring gives the clearest local control path for access-stop and protected-service contract PoC work, but it also moves the most protocol, security, and operational ownership into the project. | Whether the team wants to own an authorization-server runtime, how credentials/MFA remain outside the access-control capability, key management, protocol hardening, client management, monitoring, and long-term maintenance. |

## Comparison Pass 1

This is an initial comparison pass, not a solution choice. `Fit` means the candidate has a plausible path to satisfy the criterion. `Open` means the candidate can still fit, but a material evidence item is missing.

| Criterion | Auth0 managed login + local AC | Self-hosted Keycloak + local AC | Spring local IAM control plane |
| --- | --- | --- | --- |
| `SC-001` Local authorization authority | Fit, if Auth0 roles, groups, and claims remain non-authoritative for EDRLab account type, lifecycle, service-access roles, and audit state. The main risk is accidental IdP claim override (`FR-038`; [Threat model TS-008](../risks/threat-model.md#threat-scenarios)). | Fit, if Keycloak roles/groups stay provider-side and the local access-control service remains the source of truth. The drift risk is higher because Keycloak has rich local role and admin features ([Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), `FR-038`). | Fit. The local domain can own the full account model, but this fit comes with the most local IAM ownership ([Spring Authorization Server overview](https://docs.spring.io/spring-authorization-server/reference/overview.html), `FR-030`). |
| `SC-002` Server-side enforcement | Fit. Protected services should call local authorization or use a BFF-mediated session contract; Auth0 login state alone is not sufficient (`FR-020`, `FR-021`, `FR-037`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Fit. Protected services should call local authorization or local introspection rather than authorizing from Keycloak roles alone (`FR-020`, `FR-021`, `FR-038`). | Fit. Local introspection or authorization-check APIs are directly testable, and Spring Security supports opaque-token introspection for resource servers ([Spring Security opaque token resource server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/opaque-token.html)). |
| `SC-003` Access-stop behavior | Open. Local authorization checks can stop access quickly, but provider token/session behavior and protected-service caching still need explicit limits (`FR-016`; [Threat model RC-003](../risks/threat-model.md#requirement-refinement-candidates)). | Open. Self-hosting may give more control over token/session configuration, but the team must operate and test that configuration. | Strong fit for PoC validation. Opaque introspection can check current state before returning active access evidence, but cache and outage rules still need acceptance (`FR-016`; [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662)). |
| `SC-004` Privileged-authentication evidence | Open. Auth0 documents multiple MFA factors, but the exact machine-readable evidence for admin/super-admin onboarding must be verified ([Auth0 MFA factors](https://auth0.com/docs/secure/multi-factor-authentication/multi-factor-authentication-factors), `FR-034`, `FR-043`). | Open. Keycloak documents OTP/WebAuthn two-factor and passwordless WebAuthn flows, but the exact claim, event, or local signal consumed by onboarding must be specified ([Keycloak WebAuthn](https://www.keycloak.org/docs/latest/server_admin/#_webauthn), `FR-034`, `FR-043`). | Open. If Spring delegates authentication to an upstream IdP, the evidence depends on that provider. If Spring also owns authentication, that expands ownership beyond the preferred access-control boundary (`FR-042`). |
| `SC-005` Audit ownership and correlation | Fit with open retention/export questions. Auth0 logs can supplement local audit evidence, but `FR-027` and `FR-035` still require project-owned append-only audit records ([Auth0 logs](https://auth0.com/docs/deploy-monitor/logs)). | Fit with operational burden. Keycloak events can supplement local audit evidence, but retention, export, restore, and event integrity become self-hosted responsibilities ([Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events)). | Fit if implemented. A single local audit stream is possible, but event schema, append-only storage, retention, and export controls are project work (`FR-027`, `FR-035`). |
| `SC-006` Operational fit | Lower local authentication ownership than the self-hosted and local-IAM candidates, but vendor governance, plan limits, logs, data location, export, outage, and lock-in remain material open questions ([Auth0 logs](https://auth0.com/docs/deploy-monitor/logs), `FR-030`). | Highest product-operations burden among the provider candidates: deployment, upgrades, backups, restores, event retention, and admin-surface hardening must be owned locally (`FR-030`; [Threat model TS-013](../risks/threat-model.md#threat-scenarios)). | Highest engineering/security ownership: protocol endpoints, signing keys, client management, introspection behavior, security updates, and monitoring must be designed and operated locally ([Spring Authorization Server overview](https://docs.spring.io/spring-authorization-server/reference/overview.html), `FR-030`). |
| `SC-007` PoC value | Useful PoC if the main uncertainty is provider evidence, safe onboarding, local authorization, and claim-override prevention. | Useful PoC only if self-hosting/control is a real project constraint to validate. | Useful PoC if the main uncertainty is access-stop latency, introspection, and audit correlation. |

Initial comparison pressure before the accepted decision: Auth0 plus local access-control had the smallest authentication-ownership surface to investigate, Spring local IAM had the clearest access-stop validation path but the largest ownership burden, and Keycloak was the self-hosted-control candidate. The accepted decision below selects Keycloak for validation, not for production adoption.

## Selected Candidate

Decision: choose self-hosted Keycloak with a local access-control service as the candidate solution to validate next. This records a Phase 3 solution choice, not a production adoption decision and not approval to start implementation or production infrastructure ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [ADR 0001](../decisions/0001-choose-keycloak-for-validation.md)).

The chosen shape is:

- Keycloak provides the self-hosted OIDC/OAuth2 authentication product, login flows, MFA/WebAuthn or OTP configuration, provider-side events, and documented administration surface ([Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)).
- The local EDRLab access-control service remains authoritative for backoffice accounts, immutable account types, lifecycle state, authenticated-subject links, service-access roles, protected-service authorization, and project-owned audit records (`FR-001`, `FR-002`, `FR-036` through `FR-039`; [Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
- Protected services must authorize from the local access-control model, not directly from Keycloak roles, groups, or claims (`FR-020`, `FR-021`, `FR-038`; [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).
- Keycloak events may support authentication and provider-administration evidence, but local append-only audit remains required for the project audit event set (`FR-027`, `FR-035`; [Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events)).

Rationale:

| Reason | Why it matters | Source |
| --- | --- | --- |
| Self-hosted control is now accepted as the candidate direction. | The user explicitly selected Keycloak on 2026-06-05. This makes the self-hosted-control candidate the target for validation, while preserving later PoC and review gates. | User direction, 2026-06-05; [Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice) |
| Keycloak can provide mature authentication-product behavior without making provider roles authoritative. | Keycloak documents OIDC/OAuth2 administration, WebAuthn/two-factor/passwordless behavior, events, and Admin REST APIs, while the local access-control service can keep the EDRLab-specific authorization state authoritative. | [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), `FR-038` |
| The choice keeps the custom authorization model local. | The EDRLab feature model needs immutable account types, member-only service-access role assignments, local onboarding rules, protected-service authorization, and project-owned audit evidence. | `FR-001` through `FR-005`, `FR-027`, `FR-036` through `FR-044` ([Feature requirements specification](../../FEATURE-REQUIREMENTS.md#feature-requirements)) |
| The main risks are explicit enough for a focused validation path. | The self-hosted option concentrates the next work on operational ownership, role/claim separation, privileged-authentication evidence, event correlation, access-stop behavior, and backup/restore safety. | [Threat model TS-005, TS-008, TS-011, TS-012, and TS-013](../risks/threat-model.md#threat-scenarios) |

## Decision Gate

The decision gate is satisfied for choosing a candidate to validate:

- evidence or explicitly marked assumptions for each decision criterion;
- residual risks and conditions that must be checked in a non-production PoC or review;
- a clear user-selected candidate and rationale for why its fit can be validated against this project scope;
- the smallest useful PoC question set, if validation beyond documentation is required.

The Phase 3 output should be a candidate solution choice for validation, not a production adoption decision ([Project governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)).

## Conditions and Open Evidence

| ID | Question | Why it blocks or shapes the choice | Source |
| --- | --- | --- | --- |
| OE-001 | What access-stop delay is acceptable after disablement, archival, role removal, or role disablement? | The answer affects whether the protected-service contract can use live authorization checks, opaque introspection, short-lived JWTs, session invalidation, caching, or a combination. | `FR-016`; [Threat model RC-003](../risks/threat-model.md#requirement-refinement-candidates); [Architecture options - Open Questions](../architecture/options.md#open-questions) |
| OE-002 | What exact signal proves privileged authentication during admin or super-admin onboarding? | The selected identity provider or local runtime must make this evidence consumable by the access-control capability. | `FR-034`, `FR-043`, `FR-044`; [Technical solutions - Evaluation Questions](./technical-solutions.md#evaluation-questions) |
| OE-003 | What protected-service authorization contract should be validated first? | The choice changes latency, availability, audit correlation, stale-access behavior, and the number of components each protected service must trust. | `FR-020`, `FR-021`; [Architecture options - Shared Design Questions](../architecture/options.md#shared-design-questions) |
| OE-004 | What minimum audit schema and correlation model is enough for review? | Audit evidence must remain project-owned even when authentication or provider events come from Auth0, Keycloak, or another runtime. | `FR-027`, `FR-028`, `FR-035`; [Threat model TS-011](../risks/threat-model.md#threat-scenarios) |
| OE-005 | Which operational artifacts are in scope for comparison? | Backups, restores, support exports, migrations, upgrades, and provider export behavior can bypass or weaken account-state and audit invariants if ignored. | `FR-014`, `FR-029`, `FR-030`, `FR-035`; [Threat model TS-013](../risks/threat-model.md#threat-scenarios) |

These are now validation conditions for the Keycloak candidate, not blockers to recording the Phase 3 solution choice.

## Next Phase 3 Work

| Step | Output | Why this is next |
| --- | --- | --- |
| Define Keycloak validation scope | A Phase 4-ready PoC question set or a review checklist if no PoC is needed. | The solution choice is now made; the next useful work is to decide what must be validated before review. |
| Define the protected-service authorization contract | Candidate contract such as local authorization-check API, local introspection, BFF-mediated session, or short-lived token plus local lookup. | This is the main cross-candidate integration point for `FR-020`, `FR-021`, and `FR-016`, and it remains open for the Keycloak candidate. |
| Verify Keycloak privileged-authentication evidence shape | A documented Keycloak claim, authentication context, event, or local rule that can satisfy `FR-043` for admin/super-admin onboarding. | `FR-043` requires evidence for production admin and super-admin onboarding, not just a general MFA feature. |
| Define Keycloak operational evidence | Backup, restore, upgrade, event retention, realm configuration, key rotation, and support/export review items. | Self-hosting makes these operational controls part of the validation burden under `FR-030` and `TS-013`. |
| Prepare the Phase 4 transition if validation needs runtime evidence | A tight non-production PoC plan under `docs/poc/`. | Phase 4 can validate Keycloak behavior that documentation alone cannot settle without turning the PoC into an MVP. |

## References

- [README - Project Goal](../../README.md#project-goal)
- [README - Initial Scope](../../README.md#initial-scope)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Architecture Options](../architecture/options.md)
- [Concrete Technical Solution Candidates](./technical-solutions.md)
- [ADR 0001 - Choose Keycloak for Validation](../decisions/0001-choose-keycloak-for-validation.md)
- [Project Governance - Phase 3](../../PROJECT-GOVERNANCE.md#phase-3---solution-choice)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Auth0 - Multi-Factor Authentication Factors](https://auth0.com/docs/secure/multi-factor-authentication/multi-factor-authentication-factors)
- [Auth0 - Logs](https://auth0.com/docs/deploy-monitor/logs)
- [Auth0 - Manage Role-Based Access Control Roles](https://auth0.com/docs/manage-users/access-control/configure-core-rbac/roles)
- [Keycloak - Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [Keycloak - Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Spring Authorization Server - Overview](https://docs.spring.io/spring-authorization-server/reference/overview.html)
- [Spring Security - OAuth 2.0 Resource Server Opaque Token](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/opaque-token.html)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63B - Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
