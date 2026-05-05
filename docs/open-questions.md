# Open Questions

This document consolidates unresolved Phase 2 decisions for the internal backoffice IAM Control Plane study. It intentionally uses top-level `docs/` because these are project-specific requirements and evaluation questions, not conceptual IAM wiki material.

Status values:

| Status | Meaning |
| --- | --- |
| `Open` | Needs a decision or explicit default before later specification work. |
| `Accepted default` | A default has been accepted for the current phase, but may be revisited before production. |
| `Resolved` | The decision is recorded in a requirements or specification artifact. |

All owners are `TBD` until the project assigns business, security, engineering, or operations ownership.

## Question register

| ID | Status | Owner | Question | Blocks | Current default for Phase 2 | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| `OQ-001` | Open | TBD | Are MFA, step-up authentication, passwordless login, or hardware-backed authenticators required for production administrators? | `SEC-004`, candidate evaluation, production auth policy | Evaluate support; do not require MFA in the minimal PoC unless explicitly added. | [Administrator authentication policy](./administrator-authentication-policy.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-002` | Open | TBD | Which authenticator types are acceptable for administrators, and are SMS or email codes acceptable only as fallback? | `SEC-004`, admin recovery design | Record provider support and risk; prefer stronger possession-based factors where production risk requires them. | [Administrator authentication policy](./administrator-authentication-policy.md), [MFA wiki](./wiki/11-mfa-2fa-passwordless-and-otp.md) |
| `OQ-003` | Open | TBD | Should high-risk operations require step-up authentication or recent authentication freshness? | `API-005`, `SEC-004`, `RBAC-005` | Treat step-up as a production evaluation topic for role assignment, recovery, audit export, client changes, and break-glass. | [Administrator authentication policy](./administrator-authentication-policy.md), [BFF sessions](./bff-sessions-and-token-handling.md) |
| `OQ-004` | Open | TBD | Does production need break-glass access, and who approves or reviews its use? | `OPS-006`, incident response, admin lockout recovery | Not required for the first PoC; production must explicitly accept or define it. | [Administrator authentication policy](./administrator-authentication-policy.md), [Operational model](./operational-model.md) |
| `OQ-005` | Open | TBD | Who approves administrator recovery, MFA reset, authenticator reset, and emergency access? | `MEM-005`, `SEC-004`, incident response | Treat recovery and reset as privileged lifecycle operations with audit evidence. | [Administrator authentication policy](./administrator-authentication-policy.md), [Member lifecycle](./member-lifecycle.md) |
| `OQ-006` | Open | TBD | What is the maximum acceptable lifetime for access tokens carrying administrator permissions? | `TOKEN-003`, `TOKEN-004`, `SEC-004` | Use short-lived JWT access tokens; exact lifetime remains undecided. | [Administrator authentication policy](./administrator-authentication-policy.md), [BFF sessions](./bff-sessions-and-token-handling.md) |
| `OQ-007` | Open | TBD | Which lifecycle states are required for the first PoC: only `active` and `disabled`, or also `invited`, `archived`, `deleted`, or `suspended`? | `MEM-004`, admin API shape, audit and retention | Require `active` and `disabled`; keep other states policy-dependent. | [Member lifecycle](./member-lifecycle.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-008` | Open | TBD | Should deletion be hard delete, soft delete, archive, or policy-dependent retention? | `MEM-001`, `AUD-004`, privacy and retention | Prefer disable/archive until retention policy is defined. | [Member lifecycle](./member-lifecycle.md), [Initial permission model](./initial-permission-model.md) |
| `OQ-009` | Open | TBD | What member attributes are required beyond stable ID, email, display name, status, and role assignments? | `MEM-002`, admin API schema, audit summaries | Keep attributes minimal unless concrete backoffice workflows require more. | [Member lifecycle](./member-lifecycle.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-010` | Open | TBD | Can an administrator restore a disabled member without a second approval, and must roles be reviewed before restoration? | `MEM-001`, `RBAC-005`, access review | Allow restore only with sufficient admin permission; review roles before reactivation. | [Member lifecycle](./member-lifecycle.md), [Initial permission model](./initial-permission-model.md) |
| `OQ-011` | Open | TBD | Which lifecycle and role events require a reason field and inclusion in access reviews? | `AUD-001`, `AUD-003`, `AUD-004` | Require audit metadata for privileged changes; reason-field policy remains undecided. | [Member lifecycle](./member-lifecycle.md), [Initial permission model](./initial-permission-model.md) |
| `OQ-012` | Open | TBD | What should the BFF session lifetime be, and should it use idle timeout, absolute timeout, or both? | `SESS-003`, `SEC-002`, operations | Use both concepts in requirements; exact durations remain undecided. | [BFF sessions](./bff-sessions-and-token-handling.md) |
| `OQ-013` | Open | TBD | Should the first PoC use refresh tokens, or force re-login when access tokens expire? | `SESS-003`, `TOKEN-003`, PoC scope | Either is acceptable if the behavior is documented and tokens remain server-side. | [BFF sessions](./bff-sessions-and-token-handling.md), [Evaluation framework](./evaluation-framework.md) |
| `OQ-014` | Open | TBD | Where should token material be stored server-side: encrypted session store, token vault, provider reference, or another mechanism? | `SESS-002`, `SESS-003`, operational model | Prove server-side storage in the first PoC; exact storage mechanism is candidate-dependent. | [BFF sessions](./bff-sessions-and-token-handling.md), [Operational model](./operational-model.md) |
| `OQ-015` | Open | TBD | Which SameSite setting is compatible with the login callback, and which state-changing routes need CSRF tokens and Origin checks? | `SESS-001`, `SEC-002`, BFF design | Use SameSite-aware cookies plus CSRF and Origin/Referer checks for state-changing routes. | [BFF sessions](./bff-sessions-and-token-handling.md), [Threat model](./threat-model.md) |
| `OQ-016` | Open | TBD | What should logout mean for local BFF session, provider session, refresh token, and existing access tokens? | `SESS-003`, `TOKEN-003`, audit events | Minimum: end local BFF session and delete cookie; broader provider/token logout remains policy-dependent. | [BFF sessions](./bff-sessions-and-token-handling.md) |
| `OQ-017` | Open | TBD | How quickly must disabled members and removed roles lose effective access? | `TOKEN-003`, `TOKEN-004`, `MEM-003`, `RBAC-005` | First baseline allows access to expire at short access-token expiry; high-risk paths may need stronger controls. | [BFF sessions](./bff-sessions-and-token-handling.md), [Member lifecycle](./member-lifecycle.md) |
| `OQ-018` | Open | TBD | How will BFF sessions work if the BFF has multiple replicas? | `SESS-003`, `OPS-003`, PoC and production topology | Multi-replica production needs shared session state or equivalent; first PoC may stay single-replica if documented. | [BFF sessions](./bff-sessions-and-token-handling.md), [Operational model](./operational-model.md) |
| `OQ-019` | Open | TBD | What exact permissions should the initial `admin` and `member` roles grant in the demonstration API? | `RBAC-003`, `RBAC-004`, `API-004`, PoC design | Use `admin` and `member`; representative service permissions can start with the catalog in the initial permission model. | [Initial permission model](./initial-permission-model.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-020` | Open | TBD | Who can create roles, assign roles, create clients, and rotate service credentials? | `RBAC-005`, `API-007`, `OPS-004` | Keep `admin` restrained; introduce higher-impact IAM-owner style authority only if needed. | [Initial permission model](./initial-permission-model.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-021` | Open | TBD | What audit retention, privacy, and compliance rules apply to members, access changes, and audit events? | `AUD-004`, `OPS-003`, candidate evaluation | Preserve privileged audit evidence; exact retention and export rules remain undecided. | [Phase 1 working notes](./phase-1-working-notes.md), [Operational model](./operational-model.md), [Threat model](./threat-model.md) |
| `OQ-022` | Open | TBD | What uptime, backup, recovery, restore-test, and upgrade expectations apply to the IAM Control Plane? | `OPS-003`, `OPS-005`, `EVAL-001` | Require proportionate backup, restore, monitoring, and incident-response evidence before production. | [Operational model](./operational-model.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-023` | Open | TBD | Which team owns IAM operations after launch? | `OPS-001`, access review, incident response | No production-ready plan until an accountable owner is named. | [Operational model](./operational-model.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-024` | Open | TBD | What is the smallest useful PoC that validates OIDC login, JWT validation, RBAC, Admin API behavior, audit events, secret redaction, and access expiry? | `EVAL-005`, Phase 3/4 planning | Keep each PoC targeted to one or two high-value unknowns. | [Evaluation framework](./evaluation-framework.md), [Phase 1 working notes](./phase-1-working-notes.md) |
| `OQ-025` | Open | TBD | Which session and token events should be recorded for session creation, logout, refresh failure, token revocation, and denied admin actions? | `AUD-003`, `SESS-003`, `OPS-005` | Treat these as first audit candidates; exact event names and retention remain undecided. | [BFF sessions](./bff-sessions-and-token-handling.md), [Initial permission model](./initial-permission-model.md) |

## Resolution rules

- Resolve questions in the artifact that owns the decision, then update this register to `Resolved`.
- If a question only needs a temporary Phase 2 assumption, mark it `Accepted default` and link the requirement or evaluation artifact using that default.
- Do not move project-specific question triage into `docs/wiki/`.
- Do not treat unanswered production questions as blockers for documentation-only Phase 2 work unless they affect candidate evaluation gates.

## References

- [Requirements Baseline](./requirements-baseline.md)
- [Administrator Authentication Policy](./administrator-authentication-policy.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Member Lifecycle](./member-lifecycle.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Operational Model](./operational-model.md)
- [Threat Model](./threat-model.md)
- [Evaluation Framework](./evaluation-framework.md)
- [Phase 1 Working Notes](./phase-1-working-notes.md)
