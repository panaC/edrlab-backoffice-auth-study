# Evaluation Framework

This document defines a minimal, product-neutral framework for deciding whether an IAM candidate is worth a small MVP/PoC for the internal backoffice IAM Control Plane study.

It intentionally avoids numeric scoring, weighted criteria, and broad comparison matrices. The goal is to reduce Phase 2 combinatorial explosion by separating:

- minimal MVP/PoC requirements that must be satisfied now;
- future evolution checks that should be recorded without blocking the first PoC.

The study target remains the Central IAM Control Plane Architecture: a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/admin control plane, and one or more backend API resource servers. This framework evaluates the central IdP/authorization server/admin control-plane component only. It does not recommend a vendor, product, database, hosting model, or implementation approach.

Use [Requirements Baseline](./requirements-baseline.md) as the traceability source for gate IDs and requirement priorities.

## How to use this framework

Use this framework once per candidate option: managed provider, self-hosted IAM product, minimal library-based service, or hybrid pattern.

For each candidate:

- check the minimal MVP/PoC gates first;
- mark each gate `OK`, `KO`, or `Unknown`;
- treat `Unknown` as not yet `OK`; resolve it with official documentation or a targeted PoC before using the candidate for a first MVP/PoC;
- record the requirement IDs covered by each gate;
- cite the official source, standard, reputable security guidance, or targeted PoC evidence that supports each `OK`;
- stop detailed analysis when a minimal gate is `KO`, unless the custom work is intentionally small and documented;
- record future evolution fit separately from MVP/PoC fit;
- keep the result product-neutral until the project explicitly enters a decision phase.

Do not average away failures. A strong operations story, low cost, or convenient UI does not compensate for inability to support OAuth2/OIDC, administrator-managed users, RBAC, protected API authorization, administration API needs, auditability, secret redaction, or safe operation at the expected scale.

## Status values

| Status | Meaning |
| --- | --- |
| `OK` | Supported by official documentation, a standard specification, or a targeted PoC, with ordinary configuration or small clearly bounded integration work. |
| `KO` | Unsupported, unsafe, incompatible with project constraints, or possible only through disproportionate custom work for the first MVP/PoC. |
| `Unknown` | Not verified yet. This is not a pass; identify the documentation check or minimal PoC needed to resolve it. |

## Gate traceability

| Gate | Requirement IDs |
| --- | --- |
| OIDC login | `AUTH-001`, `AUTH-002`, `AUTH-003`, `AUTH-004` |
| Browser session boundary | `ARCH-003`, `SESS-001`, `SESS-002`, `SESS-003`, `SEC-002` |
| API token validation | `ARCH-004`, `TOKEN-001`, `TOKEN-002`, `TOKEN-003`, `TOKEN-004` |
| OAuth client safety | `SEC-003`, `API-007`, `OPS-004` |
| Admin-managed members | `BR-003`, `MEM-001`, `MEM-002`, `MEM-003`, `MEM-004`, `MEM-005` |
| No public registration | `BR-002`, `BR-003`, `BR-007` |
| RBAC and permissions | `RBAC-001`, `RBAC-002`, `RBAC-003`, `RBAC-004`, `RBAC-005` |
| Administration API fit and guardrails | `API-001`, `API-002`, `API-003`, `API-005`, `API-006`, `RBAC-005` |
| Access checks | `API-004`, `ARCH-004`, `TOKEN-002` |
| Auditability | `AUD-001`, `AUD-003`, `AUD-004` |
| Secret redaction | `SESS-002`, `AUD-002` |
| Operational fit | `BR-005`, `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006` |
| Custom work boundary | `BR-008`, `SEC-001`, `EVAL-003`, `EVAL-004` |

## Minimal MVP/PoC gates

These gates decide whether a candidate can participate in the first minimal MVP/PoC. Each `KO` should produce a clear explanation and normally means `NO-GO` for the first PoC.

| Gate | Minimal requirement | `OK` explanation should prove | `KO` explanation should identify | Future evolution to record |
| --- | --- | --- | --- | --- |
| OIDC login | Backoffice users can authenticate through OIDC using Authorization Code Flow with PKCE through the BFF. | Supported flow, issuer metadata, callback handling, and ID-token validation path are documented or proven. | No OIDC support, Implicit Flow dependency, unclear issuer metadata, or browser flow that does not fit a BFF. | MFA, step-up authentication, enterprise SSO, passwordless/passkeys. |
| Browser session boundary | Browser receives an opaque HttpOnly, Secure, SameSite-aware BFF session; OAuth tokens remain server-side; cookie-authenticated state-changing BFF routes can use CSRF defenses. | Candidate can support the BFF session model without exposing access tokens, refresh tokens, or client secrets to browser-readable storage, and the BFF can apply CSRF protection for unsafe browser requests. | Candidate requires frontend token storage, frontend-only authorization, unsafe callback/session handling, or has no credible CSRF protection path for cookie-authenticated BFF operations. | Session HA, refresh-token rotation, stronger CSRF hardening, session revocation. |
| API token validation | Resource servers can validate short-lived JWT access tokens and enforce permissions server-side. | Issuer, audience, expiry, signature, required permission checks, and bounded stale-access behavior after role removal or member disablement are documented or proven. | APIs must trust ID tokens as access tokens, cannot validate audience/issuer/signature, use long-lived access tokens without a bounded stale-access window, or cannot enforce operation permissions server-side. | Immediate revocation, introspection or opaque-token alternatives, JWKS/key rotation behavior, token exchange. |
| OAuth client safety | OAuth2/OIDC clients can be configured with exact redirect URIs, allowed flows, environment separation, safe client-secret handling, and auditable redirect/client changes where the candidate owns those controls. | Client registration, redirect URI validation, allowed grant/flow controls, audience or resource configuration, secret metadata behavior, and client-change auditability are documented or proven. | Redirect URIs are loose or wildcarded without strong controls, Implicit Flow is required, client secrets are returned through ordinary reads, environment separation is unclear, or client changes are unaudited. | Full client lifecycle, secret rotation rollout, private key JWT, mTLS, client disablement, client inventory. |
| Admin-managed members | Internal administrators can create, read, update, list, disable, restore or retain, and remove access for members. | Required lifecycle operations are available through documented APIs or small bounded integration work. | Public self-registration is mandatory, admin lifecycle APIs are missing, or disabled users can still obtain new access. | Invite flow, archive/delete policy, retention policy, recovery flow. |
| No public registration | The system can operate without public account creation. | Public registration can be disabled, omitted, or isolated from the backoffice tenant/application. | Self-service registration cannot be disabled or would expose the backoffice to unmanaged accounts. | Optional invitation UX or delegated onboarding workflow. |
| RBAC and permissions | Members can receive roles or equivalent permission groups, roles can be listed, and the first-PoC `member` role can be assigned and removed. | Roles/permissions map cleanly to `member`, `admin`, and representative service permissions such as `reports:read`; `roles:read` and `roles:assign` behavior is documented or proven. | Only coarse global admin roles exist, authorization is UI-only, required role assignment/removal is missing, or permission mapping is too awkward for the PoC. | Role creation/update/delete, permission reviews, separation of duties, fine-grained policy. |
| Administration API fit and guardrails | A REST administration surface can manage members, roles, role assignments, member and role listing, and service-access checks while enforcing admin safety guardrails. | Required operations can be called programmatically with least-privilege admin authorization, self-escalation prevention, over-grant prevention, last-admin lockout protection, and ordinary validation behavior. | Administration is UI-only, admin API requires excessive privilege, required member/role/list/access-check operations are missing, guardrails are missing, or a large custom control plane would be needed. | Client management, service account management, custom admin facade, delegated admin roles. |
| Access checks | The control plane can answer whether a member has access to a representative backoffice service/operation. | Access checks can be derived from tokens, roles, permissions, or a documented API in a way resource servers can trust. | Effective access is opaque, cannot be explained, or requires duplicating authorization state unsafely. | Central policy service, cached authorization decisions, richer denial reasons. |
| Auditability | Privileged member, role, and access changes are auditable. | Audit events include actor, action, target, result, timestamp, and safe request context, or a credible equivalent. | Audit logs cannot answer who changed access, when, and for which target. | Audit export, retention, access reviews, SIEM integration. |
| Secret redaction | Logs and audit records do not expose credentials or bearer material. | Passwords, access tokens, refresh tokens, authorization codes, raw session IDs, client secrets, private keys, and recovery material are redacted or never logged. | Normal login, token exchange, admin, or API flows expose credentials, tokens, secrets, or raw sessions in logs or audit records. | Central log filtering, audit export controls, secret scanning, retention policy. |
| Operational fit | The option is understandable and operable for fewer than 1,000 internal users. | Deployment, upgrades, backup/restore, signing-key handling, monitoring, and ownership are proportionate to the project. | Required infrastructure, expertise, or operational burden is disproportionate to the expected scale. | HA, disaster recovery, external support, production database choice, patch cadence. |
| Custom work boundary | Security-sensitive IAM behavior is inventoried and bounded; large custom ownership is accepted only when explicitly documented. | Custom work is limited, understandable, avoids custom cryptography or custom protocol implementation, and has a clear ownership and verification path. | The candidate effectively requires building an authorization server, token model, password storage, RBAC engine, audit system, and admin API from scratch without explicit acceptance of that ownership. | Security review, library upgrades, extension points, migration path. |

## Future evolution checks

These checks should be recorded, but they are not first-MVP/PoC blockers unless the user explicitly changes scope.

| Evolution | What to record | First-PoC effect |
| --- | --- | --- |
| Service-to-service authentication | Whether machine clients, Client Credentials Flow or equivalent, scoped service tokens, credential rotation, and audit trail are supported. | Future extension only; do not reject a first PoC solely for this unless it exposes an architectural dead end. |
| Strong administrator authentication | MFA, step-up, passkeys, conditional access, and break-glass options. | Record the path; not required in the first PoC. |
| Client and secret lifecycle | Client creation beyond the first BFF client, secret rotation rollout, disablement, JWKS/key rotation, private key JWT, mTLS, and client inventory. | Record risks; test later if candidate remains viable. Basic redirect URI, allowed-flow, environment, and secret-read safety is already part of the minimal gates. |
| Data export and exit | Export of members, roles, assignments, clients, and audit events. | Important for lock-in assessment; usually not a first-PoC blocker. |
| Production operations | HA, backup/restore, monitoring, incident response, RPO/RTO, and patch cadence. | Record operational risk; keep the first PoC behavior-focused. |
| Advanced member lifecycle | Invitations, archival, deletion, recovery, retention, and access review workflows. | Defer beyond active/disabled lifecycle unless policy requires more now. |
| Fine-grained authorization | ABAC, relationship-based access, policy engines, or dynamic authorization decisions. | Defer unless simple RBAC cannot meet the representative service checks. |

## Minimal PoC triggers

Run a targeted PoC only when documentation cannot answer a minimal gate or when behavior is security-sensitive.

Good PoC triggers:

- OIDC login through the BFF using Authorization Code Flow with PKCE;
- BFF session boundary and CSRF behavior for cookie-authenticated state-changing routes;
- resource-server JWT validation with issuer, audience, expiry, signature, and required permission;
- OAuth client registration safety, including exact redirect URIs, allowed flows, environment separation, and secret read behavior;
- member disablement and role removal latency;
- admin API coverage for member lifecycle and role assignment;
- audit event quality for privileged changes;
- log inspection for token, secret, password, and session redaction;
- operational feasibility for a self-hosted candidate when documentation is ambiguous.

Avoid broad PoCs that become implementation work. A useful PoC should answer one or two high-value uncertainties and document its assumptions, limits, and non-production status.

## Evaluation record template

Use this compact template when evaluating a candidate.

```markdown
# Option Evaluation: <name>

## Summary

- Category:
- Version or service tier:
- Evaluation date:
- Hosting assumption:
- Primary sources:
- Decision status: study only, no final recommendation

## Minimal MVP/PoC Gate Check

| Gate | Requirement IDs | Status | Evidence/source | Explanation | PoC or follow-up needed |
| --- | --- | --- | --- | --- | --- |
| OIDC login | `AUTH-001`, `AUTH-002`, `AUTH-003`, `AUTH-004` | Unknown |  |  |  |
| Browser session boundary | `ARCH-003`, `SESS-001`, `SESS-002`, `SESS-003`, `SEC-002` | Unknown |  |  |  |
| API token validation | `ARCH-004`, `TOKEN-001`, `TOKEN-002`, `TOKEN-003`, `TOKEN-004` | Unknown |  |  |  |
| OAuth client safety | `SEC-003`, `API-007`, `OPS-004` | Unknown |  |  |  |
| Admin-managed members | `BR-003`, `MEM-001`, `MEM-002`, `MEM-003`, `MEM-004`, `MEM-005` | Unknown |  |  |  |
| No public registration | `BR-002`, `BR-003`, `BR-007` | Unknown |  |  |  |
| RBAC and permissions | `RBAC-001`, `RBAC-002`, `RBAC-003`, `RBAC-004`, `RBAC-005` | Unknown |  |  |  |
| Administration API fit and guardrails | `API-001`, `API-002`, `API-003`, `API-005`, `API-006`, `RBAC-005` | Unknown |  |  |  |
| Access checks | `API-004`, `ARCH-004`, `TOKEN-002` | Unknown |  |  |  |
| Auditability | `AUD-001`, `AUD-003`, `AUD-004` | Unknown |  |  |  |
| Secret redaction | `SESS-002`, `AUD-002` | Unknown |  |  |  |
| Operational fit | `BR-005`, `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006` | Unknown |  |  |  |
| Custom work boundary | `BR-008`, `SEC-001`, `EVAL-003`, `EVAL-004` | Unknown |  |  |  |

## Future Evolution Notes

| Evolution | Requirement IDs | Status | Evidence/source | Explanation | Later decision or PoC |
| --- | --- | --- | --- | --- | --- |
| Service-to-service authentication | `ARCH-007`, `EVAL-006` | Unknown |  |  |  |
| Strong administrator authentication | `SEC-004`, `OPS-006` | Unknown |  |  |  |
| Client and secret lifecycle | `API-007`, `OPS-004` | Unknown |  |  |  |
| Data export and exit | `OPS-003`, `AUD-004` | Unknown |  |  |  |
| Production operations | `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006` | Unknown |  |  |  |
| Advanced member lifecycle | `MEM-004`, `MEM-005`, `AUD-004` | Unknown |  |  |  |
| Fine-grained authorization | `RBAC-006`, `API-004` | Unknown |  |  |  |

## Result

- MVP/PoC result: GO / NO-GO
- Main reason:
- Smallest useful PoC:
- Risks:
- Open questions:
```

## References

- [Requirements Baseline](./requirements-baseline.md)
- [Candidate Shortlist](./candidate-shortlist.md)
- [Minimal Backoffice IAM Architecture Notes](./minimal-backoffice-iam-architecture.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Threat Model](./threat-model.md)
- [Initial Permission Model](./initial-permission-model.md)
