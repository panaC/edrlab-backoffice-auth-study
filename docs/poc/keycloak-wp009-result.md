# Keycloak WP-009 Result

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-23

## Contents

- [Summary](#summary)
- [Post-PoC Pivot Note](#post-poc-pivot-note)
- [Result Matrix](#result-matrix)
- [Validation Coverage](#validation-coverage)
- [Blockers](#blockers)
- [Accepted Limitations](#accepted-limitations)
- [Residual Risks](#residual-risks)
- [Phase 5 Review Questions](#phase-5-review-questions)
- [Decision Impact](#decision-impact)
- [References](#references)

## Summary

`WP-009` converts the Phase 4 Keycloak evidence into Phase 5 review inputs. It is a documentation work package and does not add runtime artifacts beyond the scripted evidence already captured in `WP-001` through `WP-007` and the documentation-first boundary review in `WP-008` ([Keycloak validation plan - Work Packages](./keycloak-validation-plan.md#work-packages), [Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)).

Phase 4 produced strong evidence for the core Keycloak-plus-local-access-control boundary: Keycloak can authenticate and provide OIDC/UserInfo/event evidence, while the local side remains authoritative for subject resolution, safe member onboarding, claim override rejection, protected-service authorization, access-stop checks, and audit authority (`FR-020`, `FR-036`, `FR-037`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [Keycloak WP-002 result](./keycloak-wp002-result.md), [Keycloak WP-003 result](./keycloak-wp003-result.md), [Keycloak WP-005 result](./keycloak-wp005-result.md), [Keycloak WP-006 result](./keycloak-wp006-result.md), [Keycloak WP-007 result](./keycloak-wp007-result.md)).

Phase 4 did not prove production adoption. The current blocking gap is privileged `admin` and `super-admin` activation evidence: `WP-004` found no usable AMR claim, AMR protocol mapper, or configured-flow reference value in the default PoC configuration, so privileged onboarding activation remains blocked (`FR-034`, `FR-043`, `FR-044`; [Keycloak WP-004 result](./keycloak-wp004-result.md)). Production operations also remain open because `WP-008` records the self-hosted Keycloak operational checklist as review input, not production readiness ([Keycloak WP-008 result](./keycloak-wp008-result.md)).

## Post-PoC Pivot Note

After this result consolidation, user direction on 2026-06-23 changed the next validation direction to Keycloak as the IAM source with an EDRLab BFF/Admin API facade. This `WP-009` result remains valid evidence for the completed local-access-control-boundary PoC, but it is no longer sufficient as the active target direction. Use [ADR 0002](../decisions/0002-validate-keycloak-iam-bff.md) and [Keycloak IAM BFF scope](../architecture/keycloak-iam-bff-scope.md) for the next validation scope.

## Result Matrix

| Work package | Status | Result | Phase 5 use |
| --- | --- | --- | --- |
| `WP-001` Keycloak setup | Review | Pass | The non-production Docker runtime, realm, OIDC client, test users, event settings, and discovery checks were scripted and verified ([Keycloak WP-001 result](./keycloak-wp001-result.md)). |
| `WP-002` Login and SSO boundary | Review | Pass | Keycloak authenticated through Authorization Code flow, local code validated token/UserInfo evidence, resolved `iss` + `sub`, created only a local session decision, and verified SSO/logout behavior ([Keycloak WP-002 result](./keycloak-wp002-result.md)). |
| `WP-003` Safe and unsafe onboarding | Review | Pass for `member` onboarding | The PoC activated exactly one safe invited `member` fixture and denied no-invitation, duplicate-invitation, unverified-email, and pre-linked-subject cases ([Keycloak WP-003 result](./keycloak-wp003-result.md)). |
| `WP-004` Privileged-authentication evidence | Review | Blocked | The default PoC configuration authenticated privileged users but did not expose explicit evidence accepted for production `admin` or `super-admin` activation ([Keycloak WP-004 result](./keycloak-wp004-result.md)). |
| `WP-005` Claim override rejection | Review | Pass | Misleading Keycloak roles, group, and claims were present, but local decisions denied account-type, lifecycle, service-access-role, and audit-bypass overrides ([Keycloak WP-005 result](./keycloak-wp005-result.md)). |
| `WP-006` Authorization and access stop | Review | Pass | Local `authorization/check` fixtures allowed only current local state, denied fail-closed cases, and denied on the next fresh check after lifecycle or role changes with no positive authorization cache ([Keycloak WP-006 result](./keycloak-wp006-result.md)). |
| `WP-007` Audit correlation | Review | Pass | Local minimum-schema audit examples remained authoritative, while Keycloak user/admin events were recorded as supplemental evidence with expected gaps ([Keycloak WP-007 result](./keycloak-wp007-result.md)). |
| `WP-008` Admin Console and operations boundary | Review | Review-ready with open operations | Keycloak Web Admin is limited to technical IAM administration; self-hosted operations remain Phase 5 and later hardening questions ([Keycloak WP-008 result](./keycloak-wp008-result.md)). |
| `WP-009` Results and residual risks | Review | Review input prepared | This document consolidates the matrix, blockers, accepted limitations, residual risks, and production-hardening questions. |

## Validation Coverage

| Validation concern | Phase 4 evidence | Remaining gap |
| --- | --- | --- |
| Local authorization authority | Supported by `WP-002`, `WP-003`, `WP-005`, `WP-006`, and `WP-007`: local state decides subject resolution, onboarding, authorization, claim rejection, and audit authority. | Production implementation must preserve this boundary in real code, tests, data storage, and operational procedures (`FR-020`, `FR-036`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Server-side protected-service enforcement | Supported by `WP-006`: the local `authorization/check` fixture returns allow/deny decisions, fails closed, and records request/response evidence. OWASP recommends server-side authorization checks and deny-by-default/fail-safe behavior ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)). | Production API shape, service authentication, latency, caching, retries, audit writes, and outage behavior remain implementation and review work. |
| Access-stop target | Supported by `WP-006`: next fresh checks denied after local account disablement, archival, member role removal, and service-access-role disablement. | A future production token/session/cache strategy must explicitly preserve or revise the accepted delay; Phase 4 validated only the no-positive-cache path ([Keycloak integration scope - Validated Access-Stop Delay](../architecture/keycloak-integration-scope.md#validated-access-stop-delay)). |
| Safe member onboarding | Supported by `WP-003`: exactly one invited `member` with verified matching email and no subject link was activated; unsafe cases denied. OpenID Connect defines `sub` and `email_verified` semantics used by the PoC evidence ([OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)). | Production email normalization, concurrency, administrative intervention, persistence, and user-facing error handling remain unimplemented. |
| Privileged onboarding | Blocked by `WP-004`: privileged identities authenticated, but no accepted privileged-authentication evidence was present. | Configure and validate an explicit privileged-authentication evidence path before activating production `admin` or `super-admin` accounts (`FR-034`, `FR-043`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Claim override rejection | Supported by `WP-005`: local decisions ignored Keycloak roles, groups, and claims that looked privileged. | Production code must prevent future shortcuts that consume Keycloak roles/groups/claims as local business authority. |
| Audit correlation | Supported by `WP-007`: local audit examples carried the minimum schema and correlation IDs; Keycloak events remained supplemental. | Production append-only storage, retention, tamper resistance, privacy handling, export, backup, restore, and reconciliation remain open (`FR-027`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Keycloak Web Admin and operations | Covered by `WP-008`: technical administration is allowed, business access-control management is rejected, and operations gaps are listed. | Production admin access governance, backup/restore, monitoring, key rotation, event retention/export, upgrade process, and drift control remain review topics. |

## Blockers

| ID | Blocker | Impact | Needed before adoption review can clear it |
| --- | --- | --- | --- |
| `B-WP009-001` | Privileged-authentication evidence is missing for `admin` and `super-admin` onboarding. | Production privileged account activation cannot be accepted from the current PoC evidence. The local decision path must keep subject-link creation, activation, authorization, and local session creation blocked for those account types. | A follow-up validation pass that configures the selected Keycloak privileged-authentication policy and proves an explicit local evidence value, or a Phase 5 decision that records the gap and sends the work back to Phase 4 (`FR-034`, `FR-043`, `FR-044`; [Keycloak WP-004 result](./keycloak-wp004-result.md)). |
| `B-WP009-002` | Self-hosted production operations are not validated. | The PoC does not prove production database, backup/restore, monitoring, key rotation, event retention/export, admin-surface protection, upgrade, or drift-control readiness. | A Phase 5 operations review plan that decides which items must be validated before production adoption and which can move to Phase 6 hardening ([Keycloak WP-008 result](./keycloak-wp008-result.md), `FR-030`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |

## Accepted Limitations

- All runtime scripts and local evaluators are PoC-only fixtures. They prove validation behavior without creating production application code, dependencies, databases, migrations, CI, or deployment artifacts ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)).
- The runtime uses a throwaway realm and non-production Docker setup. `WP-001` explicitly does not validate production deployment, hosting, database, high availability, backup, restore, monitoring, or hardening ([Keycloak WP-001 result](./keycloak-wp001-result.md)).
- Browser behavior is simulated with scripted HTTP/cookie flows. `WP-002` does not validate a production browser UI, BFF middleware, persistent session store, HTTPS, cookie flags, or CSRF controls ([Keycloak WP-002 result](./keycloak-wp002-result.md)).
- Local onboarding, authorization, and audit behavior is represented by JSON fixtures. Production persistence, transactions, concurrency, middleware, service-to-service authentication, and audit storage are not implemented ([Keycloak WP-003 result](./keycloak-wp003-result.md), [Keycloak WP-006 result](./keycloak-wp006-result.md), [Keycloak WP-007 result](./keycloak-wp007-result.md)).
- Generated evidence is stored under ignored PoC evidence directories and is summarized in review documents. It is not a durable audit store or compliance archive ([Keycloak PoC runtime](../../poc/keycloak/README.md)).

## Residual Risks

| ID | Residual risk | Current evidence | Review disposition |
| --- | --- | --- | --- |
| `RR-WP009-001` | Privileged onboarding could be accepted without real MFA/passwordless evidence if the blocker is bypassed. | `WP-004` blocks activation in the current configuration. | Treat as a Phase 5 blocker or return-to-Phase-4 item before privileged activation is accepted. |
| `RR-WP009-002` | Production code could drift into trusting Keycloak roles, groups, or token claims for local business authorization. | `WP-005` proves the desired denial behavior in fixtures. | Require production tests and code review rules that preserve `FR-038`. |
| `RR-WP009-003` | Production cache, token, session, or protected-service shortcuts could reintroduce stale access after local lifecycle or role changes. | `WP-006` proves only the no-positive-cache validation path. | Decide the production access-stop delay and cache policy explicitly in Phase 5 or Phase 6. |
| `RR-WP009-004` | Local audit could be incomplete, mutable, unavailable, overexposed, or hard to reconcile with provider events. | `WP-007` proves minimum-schema examples and expected gaps, not durable audit integrity. | Review append-only storage, retention, export, privacy, backup, restore, and write-path coverage. |
| `RR-WP009-005` | Keycloak technical administrators could change realm configuration in ways that weaken the accepted boundary. | `WP-008` records admin-surface and drift-control risks. | Review admin-role governance, change control, configuration reproduction, and event/audit monitoring. |
| `RR-WP009-006` | Backup or restore could lose events, sessions, workflow state, revoked-token information, or local audit/account state. | `WP-008` cites Keycloak import/export limitations. | Review database backup/restore, local audit backup, restore tests, and recovery procedures. |
| `RR-WP009-007` | Keycloak outage, local authorization outage, or audit sink outage could create fail-open behavior if production code diverges from the PoC rule. | `WP-006` validates fail-closed local authorization fixture behavior. | Define failure-mode behavior and tests for authentication, authorization, protected services, and audit writes. |

## Phase 5 Review Questions

| Question | Why it matters | Source |
| --- | --- | --- |
| What exact privileged-authentication policy and machine-readable evidence will unblock `admin` and `super-admin` onboarding? | `FR-034`, `FR-043`, and `FR-044` require production privileged activation to prove the stronger authentication requirement, and `WP-004` did not find usable evidence in the default PoC runtime. | [Keycloak WP-004 result](./keycloak-wp004-result.md), [Keycloak authentication flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows) |
| Is the no-positive-cache access-stop target acceptable for production, or should Phase 5 accept a bounded delay with explicit risk handling? | `WP-006` validated immediate next-check denial; a different production token/session/cache strategy would change the stale-access risk. | [Keycloak WP-006 result](./keycloak-wp006-result.md), [Keycloak integration scope - Validated Access-Stop Delay](../architecture/keycloak-integration-scope.md#validated-access-stop-delay) |
| What local audit storage, integrity, retention, export, privacy, and reconciliation model is required before production? | `WP-007` proves correlation shape, not production audit durability or compliance posture. | [Keycloak WP-007 result](./keycloak-wp007-result.md), `FR-027`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements) |
| Which Keycloak production operations must be proven before adoption, and which can be accepted as Phase 6 hardening tasks? | Self-hosted Keycloak adds database, backup/restore, monitoring, key rotation, upgrade, admin access, and drift-control ownership. | [Keycloak WP-008 result](./keycloak-wp008-result.md), [Keycloak production configuration](https://www.keycloak.org/server/configuration-production) |
| What is the first production protected-service contract shape: local `authorization/check`, BFF-mediated checks, local introspection, or another explicitly reviewed contract? | The PoC used local `authorization/check`; production must settle authentication between services, request schema, latency, retries, fail-closed behavior, and audit correlation. | [Keycloak validation plan - Accepted Validation Decisions](./keycloak-validation-plan.md#accepted-validation-decisions), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| How will realm configuration changes be reviewed and reproduced? | Drift in protocol mappers, roles, groups, authentication flows, session/token settings, events, or admin grants could invalidate `WP-004`, `WP-005`, `WP-006`, or `WP-007` assumptions. | [Keycloak WP-008 result](./keycloak-wp008-result.md), [Threat model TS-008 and TS-013](../risks/threat-model.md#threat-scenarios) |

## Decision Impact

The Phase 4 evidence supports continuing to Phase 5 review with Keycloak as the validation candidate, but it does not support production adoption by itself. Phase 5 should treat the local authorization boundary as well-supported, privileged account activation as blocked, and self-hosted operations as a material decision topic rather than a solved implementation detail ([Project governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision), [ADR 0001](../decisions/0001-choose-keycloak-for-validation.md)).

No Phase 6 production MVP work is implied by this result. Production implementation still requires an explicit phase movement and scope decision ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## References

- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Keycloak PoC Runtime](../../poc/keycloak/README.md)
- [Keycloak WP-001 Result](./keycloak-wp001-result.md)
- [Keycloak WP-002 Result](./keycloak-wp002-result.md)
- [Keycloak WP-003 Result](./keycloak-wp003-result.md)
- [Keycloak WP-004 Result](./keycloak-wp004-result.md)
- [Keycloak WP-005 Result](./keycloak-wp005-result.md)
- [Keycloak WP-006 Result](./keycloak-wp006-result.md)
- [Keycloak WP-007 Result](./keycloak-wp007-result.md)
- [Keycloak WP-008 Result](./keycloak-wp008-result.md)
- [ADR 0001 - Choose Keycloak for Validation](../decisions/0001-choose-keycloak-for-validation.md)
- [Keycloak Integration Scope](../architecture/keycloak-integration-scope.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Threat Model](../risks/threat-model.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [Keycloak Production Configuration](https://www.keycloak.org/server/configuration-production)
- [Keycloak Authentication Flows](https://www.keycloak.org/docs/latest/server_admin/#creating-flows)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
