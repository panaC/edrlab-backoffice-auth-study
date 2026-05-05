# Evaluation Framework

This document defines a product-neutral framework for later evaluation of self-hosted, managed, minimal-library, and hybrid IAM options for the internal backoffice authorization server study.

The study now uses the Central IAM Control Plane Architecture as its target scope: a Backoffice BFF (Backend-for-Frontend), a central IdP/authorization server/admin control plane, and multiple backend API resource servers. This framework evaluates options for the central IdP/authorization server/admin control-plane component. It does not recommend a vendor, product, database, hosting model, or implementation approach.

## How to use this framework

Use this framework once per candidate option. A candidate might be a managed identity provider, a self-hosted open-source IAM product, a minimal internal service built from existing libraries, or a hybrid where authentication, authorization, and administration responsibilities are split across systems while still satisfying the selected Central IAM Control Plane Architecture boundaries.

For each option:

- record the option category, product or library version where relevant, hosting assumptions, and evaluation date;
- cite official documentation or specifications for protocol and product behavior;
- separate confirmed support from inferred support;
- identify which questions require a minimal proof of concept;
- keep the evaluation product-neutral until the project explicitly chooses a product or implementation path.

Do not average away a requirement failure. A high score in operations or cost does not compensate for inability to support OAuth2/OIDC, administrator-managed users, RBAC, protected APIs, service authentication, or auditability.

## Evaluation gates

The gates below come from the project brief. If an option cannot satisfy a gate, mark it as a blocker or document the compensating custom work required.

| Gate | What must be true |
| --- | --- |
| OAuth2 support | The option supports OAuth2-compatible authorization and token issuance for protected APIs. |
| OIDC support | The option supports OpenID Connect login and identity claims for backoffice users. |
| Modern browser flow | Browser-based backoffice clients can use Authorization Code Flow with PKCE. |
| Service authentication | Backend services can authenticate as machine clients, commonly through Client Credentials Flow or an equivalent standard mechanism. |
| Admin-managed members | Administrators can create, read, update, list, disable, and delete or retain member accounts according to policy. |
| No public registration requirement | The system can operate without public self-service registration. |
| RBAC | Members and service identities can receive roles or equivalent permission groups. |
| API authorization | Resource servers can validate tokens and enforce operation-level permissions server-side. |
| Administration API fit | The option exposes or can support a REST administration API for members, roles, assignments, clients, service access, and access checks. |
| Auditability | Privileged administration operations can be audited with enough context for incident review and access review. |
| Operational fit | The option can remain understandable and operable for fewer than 1,000 internal users. |

## Evidence levels

Use evidence levels to avoid treating assumptions as facts.

| Level | Meaning |
| --- | --- |
| Confirmed | Verified from official documentation, a standard specification, or a targeted PoC. |
| Likely | Strongly suggested by official documentation, but not yet tested in the intended shape. |
| Inferred | Reasonable engineering inference, but not directly documented for this use case. |
| Unknown | Not yet researched. |
| Unsupported | Documentation or testing shows the option cannot satisfy the requirement without unacceptable workarounds. |

Evaluations should prefer confirmed evidence for security-sensitive claims such as token validation, key rotation, refresh token handling, admin authorization, audit logging, and service credential rotation.

## Scoring scale

Scores are useful for comparison, but they should not create false precision. Use the scale below for each criterion.

| Score | Meaning |
| --- | --- |
| 0 | Unsupported or incompatible with the project requirement. |
| 1 | Possible only with substantial custom work, unclear security behavior, or high operational risk. |
| 2 | Partially supported, but with meaningful gaps, awkward mapping, or unresolved risks. |
| 3 | Supported in a normal, understandable way with manageable trade-offs. |
| 4 | Strong fit with simple operation, clear documentation, and low custom burden. |

When a score depends on a later PoC, mark it as provisional.

## Default criteria

The weights are starting points for later comparison. They can be adjusted if business priorities change, but every candidate should use the same weights within a comparison round.

| Criterion | Default weight | What to evaluate |
| --- | ---: | --- |
| Requirements coverage | 20 | OAuth2, OIDC, RBAC, admin-only member management, REST administration needs, service authentication, and protected API access. |
| Security and standards alignment | 20 | Secure OAuth2/OIDC flows, token validation, issuer and audience handling, PKCE, refresh token behavior, secret handling, password handling where applicable, and resistance to common IAM mistakes. |
| Admin API and data model fit | 15 | Whether members, roles, permissions, service accounts, clients, assignments, access checks, and audit events map cleanly to the project's control-plane needs. |
| Operational simplicity | 15 | Deployment, upgrades, backups, key rotation, monitoring, failure modes, incident response, and day-to-day administration effort. |
| Audit and governance | 10 | Audit event quality, access review support, privileged mutation traceability, retention controls, and separation between human and service actors. |
| Integration fit | 10 | Fit with existing backoffice APIs, existing identity sources, internal service authentication, SDKs, metadata discovery, and migration or export needs. |
| Maintainability and extensibility | 5 | Understandability for the internal team, configuration complexity, customization surface, and ability to add roles, clients, services, and access checks later. |
| Cost and lock-in | 5 | License or subscription cost, hosting cost, support cost, migration path, data export, provider coupling, and exit risk. |

## Requirements coverage prompts

Use these prompts to collect comparable evidence.

| Area | Questions |
| --- | --- |
| OAuth2/OIDC | Which flows are supported? Are Authorization Code with PKCE and Client Credentials supported? Is OIDC Discovery available? Are JWKS, issuer metadata, and client registration behavior documented? |
| Tokens | Are access tokens JWTs, opaque tokens, or configurable? How are issuer, audience, expiration, key rotation, revocation, and introspection handled? |
| Members | Can administrators create, update, list, disable, delete, and recover or retain members? Are stable identifiers separate from mutable email or display fields? |
| RBAC | Are roles and permissions first-class concepts? Can permissions be assigned to roles and roles to members or service accounts? Can role changes be reviewed? |
| Admin API | Are required operations available through documented APIs? Are admin API permissions explicit enough to prevent accidental broad access? |
| Service accounts | Can machine clients be modeled as distinct actors with narrow permissions, credential rotation, disablement, and audit trail? |
| Access checks | Can a backoffice service determine whether a member or service has access to a protected operation or service? |
| Audit | Which privileged events are recorded? Do audit events identify actor, action, target, result, timestamp, and request context? |

## Security prompts

Security evaluation should be conservative and evidence-based.

Check whether the option:

- supports Authorization Code Flow with PKCE for browser-based clients;
- avoids Implicit Flow for new browser applications;
- supports Client Credentials Flow or an equivalent standard machine-client pattern;
- provides clear token validation guidance for resource servers;
- supports issuer, audience, lifetime, and signature or introspection checks;
- supports key rotation without breaking all resource servers at once;
- supports refresh token rotation, reuse detection, revocation, or equivalent mitigations where refresh tokens are used;
- prevents admin APIs from relying on frontend-only checks;
- supports least-privilege administrator permissions;
- prevents self-escalation in role, client, and service-account management;
- redacts tokens, secrets, passwords, and refresh tokens from logs;
- provides safe password storage behavior if it manages passwords directly;
- supports MFA or stronger administrator authentication if later requirements demand it.

Document any security claim that depends on configuration. "Supported if configured correctly" is materially different from "safe by default."

## Operations prompts

Operational simplicity is a project requirement, not a nice-to-have. For each option, evaluate:

- installation and environment requirements;
- upgrade process and compatibility risks;
- backup and restore process;
- database requirements, including whether SQLite is realistic for a self-hosted option;
- signing key and client credential rotation;
- monitoring and alerting surface;
- audit log retention and export;
- disaster recovery expectations;
- local development and test setup;
- ownership model after launch;
- support channels and security patch cadence;
- failure modes when the authorization server, identity provider, database, network, or introspection endpoint is unavailable.

Prefer concrete operational evidence over feature lists. A product can have every IAM feature and still be a poor fit if operating it is disproportionate to the internal scale.

## Approach-specific prompts

### Managed identity provider

- Does the provider support admin-only member management without public registration?
- Are admin APIs complete enough for the required member, role, assignment, client, and audit workflows?
- Can data be exported for audit, migration, or exit?
- How are tenants, environments, custom domains, callbacks, and secrets managed?
- What are the pricing thresholds for fewer than 1,000 users and service clients?
- Which outages or provider changes would affect backoffice access?
- How much provider-specific behavior would application code depend on?

### Self-hosted open-source product

- What database, runtime, deployment, and storage assumptions does the product require?
- Is SQLite realistic, supported, unsupported, or only suitable for development?
- How are upgrades, backups, signing keys, secrets, and admin users managed?
- What audit logs exist out of the box?
- How much customization is needed for the REST admin API and access-check requirements?
- Who owns patching and incident response?

### Minimal internal service using existing libraries

- Which OAuth2/OIDC responsibilities are provided by maintained libraries rather than custom protocol code?
- What remains custom: member storage, admin API, RBAC, token issuance, token validation, sessions, audit logs, or service credentials?
- Does the team have enough IAM expertise to own the security-sensitive parts?
- How are password storage, MFA, refresh tokens, key rotation, revocation, and account disablement handled?
- Which pieces would require security review before production?

### Hybrid approach

- Which system is the source of truth for authentication, members, roles, permissions, clients, and audit events?
- How are identities linked across systems?
- What happens when synchronization fails?
- Which system enforces authorization for APIs?
- Does the split reduce complexity or merely move it into integration code?
- Can administrators understand and review effective access from one place?

## Proof-of-concept triggers

A PoC should be minimal and answer a specific uncertainty. During Phase 1, document the PoC plan rather than adding runnable implementation unless the user explicitly asks for a PoC.

Good PoC triggers include:

- validating access tokens in a representative resource server;
- proving that Authorization Code with PKCE works with the intended browser client shape;
- testing Client Credentials Flow for one backend service;
- confirming admin API coverage for member lifecycle and role assignment;
- measuring how quickly disabled members or removed roles lose access;
- testing token revocation or introspection behavior;
- confirming audit events for privileged operations;
- verifying key rotation and JWKS behavior;
- confirming SQLite support or rejecting it as unrealistic for a self-hosted candidate;
- exporting members, roles, assignments, clients, and audit data.

Avoid broad PoCs that accidentally become implementation work. A PoC should answer one or two high-value questions and document its assumptions and non-production status.

## Red flags

Treat these as reasons to pause and investigate before scoring an option positively:

- no documented support for Authorization Code Flow with PKCE;
- no OIDC support for login and identity claims;
- APIs are expected to trust ID tokens as access tokens;
- resource servers cannot validate issuer and audience;
- access tokens are long-lived by default without clear mitigation;
- role changes cannot be reflected, revoked, or allowed to expire in an acceptable window;
- admin authorization is only enforced in a UI;
- role assignment allows easy self-escalation;
- service accounts share human administrator roles by default;
- secrets or tokens are exposed after creation or written to logs;
- password storage behavior is undocumented or custom-built;
- audit logs cannot answer who changed access, when, and for which target;
- public registration cannot be disabled;
- data export or migration path is unclear;
- operating the system requires expertise or infrastructure disproportionate to the expected scale.

## Evaluation record template

Use this template when evaluating a candidate option.

```markdown
# Option Evaluation: <name>

## Summary

- Category:
- Version or service tier:
- Evaluation date:
- Hosting assumption:
- Primary sources:
- Evidence status:
- Decision status: study only, no final recommendation

## Gate Check

| Gate | Status | Evidence | Notes |
| --- | --- | --- | --- |
| OAuth2 support | Unknown |  |  |
| OIDC support | Unknown |  |  |
| Modern browser flow | Unknown |  |  |
| Service authentication | Unknown |  |  |
| Admin-managed members | Unknown |  |  |
| No public registration requirement | Unknown |  |  |
| RBAC | Unknown |  |  |
| API authorization | Unknown |  |  |
| Administration API fit | Unknown |  |  |
| Auditability | Unknown |  |  |
| Operational fit | Unknown |  |  |

## Criteria Scores

| Criterion | Weight | Score | Evidence level | Notes |
| --- | ---: | ---: | --- | --- |
| Requirements coverage | 20 |  | Unknown |  |
| Security and standards alignment | 20 |  | Unknown |  |
| Admin API and data model fit | 15 |  | Unknown |  |
| Operational simplicity | 15 |  | Unknown |  |
| Audit and governance | 10 |  | Unknown |  |
| Integration fit | 10 |  | Unknown |  |
| Maintainability and extensibility | 5 |  | Unknown |  |
| Cost and lock-in | 5 |  | Unknown |  |

## Risks

- TBD

## Open Questions

- TBD

## PoC Candidates

- TBD
```

## References

- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7519 - JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
