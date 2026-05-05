# Evaluation Framework

This document defines a minimal, product-neutral framework for deciding whether an IAM candidate is worth a small MVP/PoC for the internal backoffice authorization server study.

It intentionally avoids numeric scoring, weighted criteria, and broad comparison matrices. The goal is to reduce Phase 2 combinatorial explosion by separating:

- minimal MVP/PoC requirements that must be satisfied now;
- future evolution checks that should be recorded without blocking the first PoC.

The study target remains the Central IAM Control Plane Architecture: a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/admin control plane, and one or more backend API resource servers. This framework evaluates the central IdP/authorization server/admin control-plane component only. It does not recommend a vendor, product, database, hosting model, or implementation approach.

## How to use this framework

Use this framework once per candidate option: managed provider, self-hosted IAM product, minimal library-based service, or hybrid pattern.

For each candidate:

- check the minimal MVP/PoC gates first;
- mark each gate `OK`, `KO`, or `Unknown`;
- treat `Unknown` as not yet `OK`; resolve it with official documentation or a targeted PoC before using the candidate for a first MVP/PoC;
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

## Minimal MVP/PoC gates

These gates decide whether a candidate can participate in the first minimal MVP/PoC. Each `KO` should produce a clear explanation and normally means `NO-GO` for the first PoC.

| Gate | Minimal requirement | `OK` explanation should prove | `KO` explanation should identify | Future evolution to record |
| --- | --- | --- | --- | --- |
| OIDC login | Backoffice users can authenticate through OIDC using Authorization Code Flow with PKCE through the BFF. | Supported flow, issuer metadata, callback handling, and ID-token validation path are documented or proven. | No OIDC support, Implicit Flow dependency, unclear issuer metadata, or browser flow that does not fit a BFF. | MFA, step-up authentication, enterprise SSO, passwordless/passkeys. |
| Browser session boundary | Browser receives an opaque HttpOnly BFF session; OAuth tokens remain server-side. | Candidate can support a BFF session model without exposing access tokens, refresh tokens, or client secrets to browser-readable storage. | Candidate requires frontend token storage, frontend-only authorization, or unsafe callback/session handling. | Session HA, refresh-token rotation, CSRF hardening, session revocation. |
| API token validation | Resource servers can validate short-lived JWT access tokens and enforce permissions server-side. | Issuer, audience, expiry, signature, required permission checks, and bounded stale-access behavior after role removal or member disablement are documented or proven. | APIs must trust ID tokens as access tokens, cannot validate audience/issuer/signature, use long-lived access tokens without a bounded stale-access window, or cannot enforce operation permissions server-side. | Immediate revocation, introspection or opaque-token alternatives, JWKS/key rotation behavior, token exchange. |
| Admin-managed members | Internal administrators can create, read, update, list, disable, restore or retain, and remove access for members. | Required lifecycle operations are available through documented APIs or small bounded integration work. | Public self-registration is mandatory, admin lifecycle APIs are missing, or disabled users can still obtain new access. | Invite flow, archive/delete policy, retention policy, recovery flow. |
| No public registration | The system can operate without public account creation. | Public registration can be disabled, omitted, or isolated from the backoffice tenant/application. | Self-service registration cannot be disabled or would expose the backoffice to unmanaged accounts. | Optional invitation UX or delegated onboarding workflow. |
| RBAC and permissions | Members can receive roles or equivalent permission groups, roles can be listed, and the first-PoC `member` role can be assigned and removed. | Roles/permissions map cleanly to `member`, `admin`, and representative service permissions such as `reports:read`; `roles:read` and `roles:assign` behavior is documented or proven. | Only coarse global admin roles exist, authorization is UI-only, required role assignment/removal is missing, or permission mapping is too awkward for the PoC. | Role creation/update/delete, permission reviews, separation of duties, fine-grained policy. |
| Administration API fit and guardrails | A REST administration surface can manage members, role assignments, and service-access checks while enforcing admin safety guardrails. | Required operations can be called programmatically with least-privilege admin authorization, self-escalation prevention, over-grant prevention, and last-admin lockout protection. | Administration is UI-only, admin API requires excessive privilege, required guardrails are missing, or a large custom control plane would be needed. | Client management, service account management, custom admin facade, delegated admin roles. |
| Access checks | The control plane can answer whether a member has access to a representative backoffice service/operation. | Access checks can be derived from tokens, roles, permissions, or a documented API in a way resource servers can trust. | Effective access is opaque, cannot be explained, or requires duplicating authorization state unsafely. | Central policy service, cached authorization decisions, richer denial reasons. |
| Auditability | Privileged member, role, and access changes are auditable. | Audit events include actor, action, target, result, timestamp, and safe request context, or a credible equivalent. | Audit logs cannot answer who changed access, when, and for which target. | Audit export, retention, access reviews, SIEM integration. |
| Secret redaction | Logs and audit records do not expose credentials or bearer material. | Passwords, access tokens, refresh tokens, authorization codes, raw session IDs, client secrets, private keys, and recovery material are redacted or never logged. | Normal login, token exchange, admin, or API flows expose credentials, tokens, secrets, or raw sessions in logs or audit records. | Central log filtering, audit export controls, secret scanning, retention policy. |
| Operational fit | The option is understandable and operable for fewer than 1,000 internal users. | Deployment, upgrades, backup/restore, signing-key handling, monitoring, and ownership are proportionate to the project. | Required infrastructure, expertise, or operational burden is disproportionate to the expected scale. | HA, disaster recovery, external support, production database choice, patch cadence. |
| Custom work boundary | Security-sensitive IAM behavior is not mostly custom unless explicitly accepted. | Custom work is limited, understandable, and avoids custom cryptography or custom protocol implementation. | The candidate effectively requires building an authorization server, token model, password storage, RBAC engine, audit system, and admin API from scratch. | Security review, library upgrades, extension points, migration path. |

## Future evolution checks

These checks should be recorded, but they are not first-MVP/PoC blockers unless the user explicitly changes scope.

| Evolution | What to record | First-PoC effect |
| --- | --- | --- |
| Service-to-service authentication | Whether machine clients, Client Credentials Flow or equivalent, scoped service tokens, credential rotation, and audit trail are supported. | Future extension only; do not reject a first PoC solely for this unless it exposes an architectural dead end. |
| Strong administrator authentication | MFA, step-up, passkeys, conditional access, and break-glass options. | Record the path; not required in the first PoC. |
| Client and secret lifecycle | Client creation, secret rotation, disablement, JWKS/key rotation, and environment separation. | Record risks; test later if candidate remains viable. |
| Data export and exit | Export of members, roles, assignments, clients, and audit events. | Important for lock-in assessment; usually not a first-PoC blocker. |
| Production operations | HA, backup/restore, monitoring, incident response, RPO/RTO, and patch cadence. | Record operational risk; keep the first PoC behavior-focused. |
| Advanced member lifecycle | Invitations, archival, deletion, recovery, retention, and access review workflows. | Defer beyond active/disabled lifecycle unless policy requires more now. |
| Fine-grained authorization | ABAC, relationship-based access, policy engines, or dynamic authorization decisions. | Defer unless simple RBAC cannot meet the representative service checks. |

## Minimal PoC triggers

Run a targeted PoC only when documentation cannot answer a minimal gate or when behavior is security-sensitive.

Good PoC triggers:

- OIDC login through the BFF using Authorization Code Flow with PKCE;
- resource-server JWT validation with issuer, audience, expiry, signature, and required permission;
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

| Gate | Status | Explanation | Evidence or PoC needed |
| --- | --- | --- | --- |
| OIDC login | Unknown |  |  |
| Browser session boundary | Unknown |  |  |
| API token validation | Unknown |  |  |
| Admin-managed members | Unknown |  |  |
| No public registration | Unknown |  |  |
| RBAC and permissions | Unknown |  |  |
| Administration API fit and guardrails | Unknown |  |  |
| Access checks | Unknown |  |  |
| Auditability | Unknown |  |  |
| Secret redaction | Unknown |  |  |
| Operational fit | Unknown |  |  |
| Custom work boundary | Unknown |  |  |

## Future Evolution Notes

| Evolution | Status | Explanation | Later decision or PoC |
| --- | --- | --- | --- |
| Service-to-service authentication | Unknown |  |  |
| Strong administrator authentication | Unknown |  |  |
| Client and secret lifecycle | Unknown |  |  |
| Data export and exit | Unknown |  |  |
| Production operations | Unknown |  |  |
| Advanced member lifecycle | Unknown |  |  |
| Fine-grained authorization | Unknown |  |  |

## Result

- MVP/PoC result: GO / NO-GO
- Main reason:
- Smallest useful PoC:
- Risks:
- Open questions:
```
