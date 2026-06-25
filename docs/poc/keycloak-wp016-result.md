# Keycloak WP-016 Result - Audit and Operations Review

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-25

## Contents

- [Purpose](#purpose)
- [Result](#result)
- [Audit Boundary](#audit-boundary)
- [Local EDRLab Audit Event Contract](#local-edrlab-audit-event-contract)
- [Audit Event Matrix](#audit-event-matrix)
- [Keycloak Evidence To Collect](#keycloak-evidence-to-collect)
- [Operational Review Items](#operational-review-items)
- [Runtime Evidence To Produce](#runtime-evidence-to-produce)
- [Residual Risks](#residual-risks)
- [Decision Impact](#decision-impact)
- [References](#references)

## Purpose

`WP-016` defines the audit and operational boundary for the active Keycloak IAM plus EDRLab IAM Control Plane API validation direction. It answers which events can be treated as Keycloak provider evidence, which decisions require a local EDRLab business audit record, and which operator duties remain review inputs before any production decision (`FR-027`, `FR-028`, `FR-035`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

This result builds on the selected Keycloak mapping, IAM Control Plane API anti-bypass path, service authorization contract, and direct-admin drift handling from `WP-010`, `WP-011`, `WP-014`, and `WP-015` ([Keycloak WP-010 result](./keycloak-wp010-result.md), [Keycloak WP-011 result](./keycloak-wp011-result.md), [Keycloak WP-014 result](./keycloak-wp014-result.md), [Keycloak WP-015 result](./keycloak-wp015-result.md)).

This is documentation-first PoC evidence. It does not add runtime scripts, production code, production dependencies, database schema, CI, deployment files, or production operations policy. Runtime validation still needs a Linux-targeted, Docker-based, fully scripted PoC before execution ([Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Result

Keycloak events are useful provider-side evidence, but they are not sufficient as the EDRLab business audit trail. Keycloak documents user and admin events, and admin events can include JSON representations sent through Admin REST when representation capture is enabled, but the business decision, denial reason, correlation intent, audit-read event, and EDRLab rationale must be recorded by the EDRLab IAM Control Plane API ([Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html), [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#which-events-to-log)).

For the first validation slice:

- the EDRLab IAM Control Plane API records the business audit event before or with every controlled IAM state mutation;
- Keycloak admin and user events are retained as supplemental provider evidence and correlation material;
- denied business operations are audited locally even when no Keycloak mutation occurs;
- audit reads and exports are audited locally because they are EDRLab business operations, not only Keycloak provider events (`FR-028`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements));
- drift and event gaps are recorded locally when Keycloak current state cannot be tied to an approved control-plane mutation;
- at least two logical persistence responsibilities remain: the Keycloak product state store and the EDRLab business audit/reconciliation store.

The last point is a logical responsibility split, not a production database-topology decision. Phase 5 may decide whether those responsibilities become two physical databases, one database with separate schemas and privileges, an external audit store, or another production storage design.

## Audit Boundary

| Evidence source | What it proves | What it does not prove |
| --- | --- | --- |
| Keycloak user events | Authentication and user-event activity produced by the Keycloak realm. Keycloak supports event viewing and event configuration for realm events ([Keycloak events](https://www.keycloak.org/docs/latest/server_admin/#events)). | EDRLab business approval, local account resolution, service-access rationale, or denied control-plane decisions. |
| Keycloak admin events | Provider-side administrative changes such as Admin Console or Admin REST operations, with optional representation capture when configured ([Keycloak admin events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)). | Complete EDRLab audit coverage, denied operations that never reached Keycloak, immutable business rationale, or tamper-resistant retention. |
| EDRLab business audit | Actor, operation, target, decision, reason, before/after business state, correlation ID, and Keycloak references for EDRLab IAM actions (`FR-027`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). | Raw Keycloak provider internals beyond the captured references and evidence snapshots. |
| EDRLab reconciliation evidence | Whether current Keycloak state matches the latest approved IAM Control Plane API mutation and selected mapping invariants ([Keycloak WP-015 result](./keycloak-wp015-result.md#drift-detection-contract)). | Long-term production recovery or break-glass governance; those remain Phase 5 review items. |
| Protected-service access evidence | Server-side allow/deny decisions from `authorization/check`, including fail-closed denials and access-stop behavior ([Keycloak WP-014 result](./keycloak-wp014-result.md#protected-service-authorization-contract)). | Frontend-only visibility or raw token claims as final authorization; OWASP says client-side checks must not decide access ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#verify-that-authorization-checks-are-performed-in-the-right-location)). |

## Local EDRLab Audit Event Contract

The first runtime slice should use a small local audit event record that is explicit enough to test `FR-027`, `FR-028`, `FR-035`, and `FR-038` without pretending to be a production audit database. OWASP logging guidance recommends logging security-relevant events such as authentication, authorization failures, user administration actions, privileged actions, imports/exports, and enough "when, where, who and what" fields for later analysis ([OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#which-events-to-log), [OWASP Logging Cheat Sheet - event attributes](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#event-attributes)).

```json
{
  "audit_event_id": "audit-poc-wp016-001",
  "correlation_id": "poc-wp016-001",
  "occurred_at": "2026-06-25T10:15:30Z",
  "actor_account_id": "acct-admin-001",
  "actor_subject": "keycloak:edrlab:9c4b...",
  "operation": "service_role.assigned",
  "target_account_id": "acct-member-042",
  "target_service": "catalog",
  "decision": "allow",
  "reason_code": "actor_scope_allows_service_role_assignment",
  "before": {
    "lifecycle": "active",
    "service_roles": []
  },
  "after": {
    "lifecycle": "active",
    "service_roles": ["service-catalog-consult"]
  },
  "keycloak_refs": [
    {
      "type": "admin_event",
      "id": "kc-event-optional",
      "resource_path": "users/{id}/role-mappings/clients/{client-id}"
    }
  ],
  "source": "edrlab-iam-control-plane-api"
}
```

Minimum fields for the PoC:

| Field | PoC rule |
| --- | --- |
| `audit_event_id` | Unique local event identifier. |
| `correlation_id` | Shared across EDRLab request, local audit event, Keycloak Admin REST call, and evidence files where possible. |
| `occurred_at` | Timestamp in an unambiguous format. |
| `actor_account_id` and `actor_subject` | Local account plus authenticated subject used for the decision. |
| `operation` | Stable operation name such as `account.disabled`, `service_role.assigned`, `authorization.check.denied`, or `audit.exported`. |
| `target_*` | Local target account, service, role, or audit resource. |
| `decision` | `allow`, `deny`, `blocked`, `drift_detected`, or `event_gap`. |
| `reason_code` | Machine-readable explanation for the decision. |
| `before` and `after` | Minimal business state snapshot needed to prove lifecycle, account type, subject link, or service-role impact. |
| `keycloak_refs` | Optional Keycloak user, role, client, or event references. Empty is valid when the operation was denied before Keycloak mutation. |
| `source` | Fixed to `edrlab-iam-control-plane-api` for local business audit events. |

The PoC must avoid logging secrets, raw tokens, passwords, or unnecessary personal data. OWASP explicitly warns to exclude data that should not be logged and to avoid unlawful or excessive logging ([OWASP Logging Cheat Sheet - data to exclude](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude)).

## Audit Event Matrix

| Event class | Local EDRLab audit required | Keycloak evidence expected | Notes |
| --- | --- | --- | --- |
| `account.created.member` | Yes. | Admin REST or Admin Console event if Keycloak user is created or updated. | Records creator, invitation basis, target email, initial lifecycle, and subject-link state. |
| `account.created.admin` / `account.created.super_admin` | Yes. | Keycloak user and privileged-authentication evidence where configured. | The dedicated `WP-013` runtime proves the selected ACR/LoA path at PoC level, and ADR 0003 accepts OTP MFA; production still needs durable audit storage and OTP enrollment/reset/recovery controls ([Keycloak WP-013 result](./keycloak-wp013-result.md#runtime-execution), [ADR 0003](../decisions/0003-accept-otp-for-privileged-authentication.md)). |
| `onboarding.activation.allowed` | Yes. | User authentication event and resulting Keycloak user state. | Records safe invitation match and initial subject link. |
| `onboarding.activation.denied` | Yes. | Authentication evidence may exist, but no business mutation should occur. | Denials include no invitation, duplicate invitation, unverified email, pre-linked account, or missing privileged evidence (`FR-042`, `FR-044`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| `account.disabled` / `account.restored` / `account.archived` | Yes. | Admin event for lifecycle attribute update. | Protected services must deny disabled or archived users on current-state check ([Keycloak WP-014 result](./keycloak-wp014-result.md)). |
| `account_type.mutation_denied` | Yes. | Usually none, because the IAM Control Plane API must reject before Keycloak mutation. | Account type is fixed by the selected mapping and feature requirements (`FR-001`, `FR-026`; [Keycloak WP-010 result](./keycloak-wp010-result.md#account-type-mapping)). |
| `subject_link.created` | Yes. | Admin event for user attribute or linkage metadata when persisted in Keycloak. | Records first safe link between authenticated subject and local account. |
| `subject_link.mutation_denied` | Yes. | Usually none, because unauthorized relinking is rejected before mutation. | Supports the immutable subject-link boundary in `FR-039` and `WP-015`. |
| `service_role.assigned` / `service_role.removed` | Yes. | Admin event for client-role mapping changes. | Records actor scope, target service, role state, before/after mapping, and access-stop implications. |
| `service_role.disabled` / `service_role.archived` | Yes. | Admin event if represented as Keycloak role attribute or config change. | Denial must happen on next current-state authorization check. |
| `authorization.check.allowed` | Optional sample in PoC. | Usually none. | A sample allow event can prove correlation, but production volume and retention policy remain review questions. |
| `authorization.check.denied` | Yes for PoC access-stop, drift, inactive account, invalid role, and fail-closed cases. | Usually none. | OWASP recommends logging authorization failures and handling access-check failures safely ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#exit-safely-when-authorization-checks-fail), [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#which-events-to-log)). |
| `effective_services.listed` | Optional sample in PoC. | Usually none. | `GET /me/services` is navigation evidence, not final protected-service authorization. |
| `effective_services.denied` | Yes. | Usually none. | Deny or block on inactive account, invalid mapping, or drift. |
| `drift.detected` | Yes. | Admin event if available; current-state evidence even when events are missing. | Records `invariant_violation`, `unmanaged_change_detected`, `untrusted_claim_shortcut`, or `event_gap` from `WP-015`. |
| `audit.read` / `audit.exported` | Yes. | Usually none unless Keycloak admin events are inspected directly. | `FR-028` requires audit consultation/export to be authorized and audited; OWASP treats data export and administrative activity as higher-risk logging subjects ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#which-events-to-log)). |

## Keycloak Evidence To Collect

Runtime validation should collect Keycloak evidence as supplemental proof, not as the sole business audit trail:

- realm event settings showing whether events, admin events, and representation capture are enabled;
- admin events for controlled IAM Control Plane API mutations through Keycloak Admin REST;
- admin events for direct Admin Console or direct Admin REST drift scenarios;
- user or authentication events for onboarding and privileged-authentication evidence where configured;
- Keycloak identifiers needed for correlation: realm, user ID, client ID, role name or role ID, resource path, and event timestamp;
- evidence gaps when admin events are disabled, cleared, truncated, or insufficient to tie current state to an approved EDRLab mutation.

Keycloak supports realm admin permissions, realm-management roles, Admin Console access, and Admin API access controls; therefore, operator access must be explicitly reviewed rather than assumed safe ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). Keycloak import/export behavior must also be reviewed separately from business audit because Admin Console exports are partial and Keycloak states that CLI exports are the suitable path for backups or transfer between servers ([Keycloak import/export](https://www.keycloak.org/server/importExport)).

## Operational Review Items

| Topic | Why it matters | Phase 4 evidence | Phase 5 question |
| --- | --- | --- | --- |
| Keycloak state backup and restore | Keycloak remains the IAM state holder for the selected mapping. | Record import/export and backup assumptions; do not treat Admin Console partial export as backup evidence ([Keycloak import/export](https://www.keycloak.org/server/importExport)). | What restore objective, backup scope, and restore test are required before production? |
| EDRLab audit/reconciliation storage | Local business audit is needed for denials, rationale, drift, and audit reads. | Produce JSON audit samples and correlation records. | Is this a separate database, schema, append-only log, WORM storage, or another auditable store? |
| Audit retention and immutability | `FR-035` asks for durable audit history, while Keycloak event retention/configuration can be operationally limited. | Record retention assumptions and event-gap cases. | What retention, privacy, tamper-resistance, and purge/legal model applies? |
| IAM Control Plane API service account | The control plane needs technical rights to mutate Keycloak through an approved path. | Record scope of the PoC service account and its Keycloak roles. | How are credentials stored, rotated, monitored, and restricted? |
| Direct Keycloak admin access | Direct mutation can bypass business workflow unless constrained and detected. | Collect admin-permission evidence and drift scenarios. | Who has direct admin access, when is break-glass allowed, and how is it reconciled? |
| Realm-management permissions | Keycloak has realm-management roles and fine-grained admin permissions. | Capture assigned roles for technical users in the PoC realm ([Keycloak managing access to realm resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)). | Which least-privilege admin model is acceptable? |
| Protected-service integration | Protected services must call the IAM Control Plane API authorization decision rather than trusting frontend state or raw token claims. | Produce `authorization/check` allow/deny evidence and shortcut rejection evidence. | What service-to-service authentication, timeout, retry, and fail-closed policy is required? |
| Monitoring and alerting | Drift, authorization failures, event gaps, and admin changes are operational signals. | Produce local audit samples and event-gap examples. | Which alerts, dashboards, and incident workflow are required? |
| First super-admin bootstrap | A first privileged actor must exist without weakening normal onboarding controls. | Record bootstrap as a separate setup/evidence scenario if needed. | What controlled bootstrap or break-glass process is acceptable? |
| Runtime recovery after drift | Operators need a safe way to resolve valid-looking unmanaged changes. | Record denied/quarantined drift and reconciliation evidence. | Is there a formal reconciliation workflow, or must all unmanaged changes be reverted? |

## Runtime Evidence To Produce

`WP-016` runtime validation should produce:

- Keycloak event settings evidence, including admin events and representation capture status;
- one local EDRLab audit JSON sample for each required event class in the audit matrix;
- correlation between local EDRLab audit events and Keycloak admin events for successful controlled mutations;
- denial-only local audit events where no Keycloak mutation occurs;
- direct-admin drift evidence showing Keycloak event presence when available and local `drift.detected` evidence either way;
- event-gap evidence for disabled, cleared, missing, or insufficient Keycloak events;
- `audit.read` and `audit.exported` local audit examples;
- protected-service authorization denial evidence for fail-closed and access-stop cases;
- operator-surface evidence listing the Keycloak admin roles used by PoC technical actors;
- a clear note that backup/restore, retention, tamper resistance, and production database topology are review inputs, not solved by the PoC.

The runtime result should use the evidence-record shape from the [Keycloak IAM Control Plane API validation plan](./keycloak-iam-bff-validation-plan.md#evidence-record). If a step cannot be scripted, it must be marked partially manual, blocked, or residual risk according to the Phase 4 runtime rules ([AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)).

## Residual Risks

- Keycloak events can be supplemental evidence, but they are not the EDRLab business audit authority for denials, rationale, audit reads, drift classification, or immutable retention.
- Privileged Keycloak administrators may still mutate IAM state or affect event evidence. The PoC can classify this as drift, but production separation of duties and tamper-resistant audit remain open.
- Local EDRLab audit/reconciliation storage is logically required, but the production physical storage topology is not decided.
- `FR-035` durability expectations may create cost, privacy, retention, and legal-review questions that are outside this documentation-first WP.
- Successful `authorization.check.allowed` logging may be too high-volume for production if recorded for every request. The PoC should sample or fixture allow events and record the future retention decision.
- Backup/restore, break-glass, first-super-admin bootstrap, secret rotation, alerting, and incident response are identified but not production-approved.
- Runtime evidence has not yet been executed for `WP-016`.

## Decision Impact

`WP-016` is complete at documentation level. It confirms that the active direction needs Keycloak as the IAM state provider plus local EDRLab business audit/reconciliation responsibility behind the IAM Control Plane API. This does not force two production databases yet; it does force two logical ownership areas to be reviewed in Phase 5.

The follow-up `WP-017` consolidation and runtime results now provide Phase 5 review inputs. Remaining audit work should focus on production storage, retention, export, tamper resistance, direct-admin reconciliation, and operations rather than more PoC JSON samples.

## References

- [Keycloak WP-010 Result - IAM Mapping Design](./keycloak-wp010-result.md)
- [Keycloak WP-011 Result - IAM Control Plane API Admin Anti-Bypass Path](./keycloak-wp011-result.md)
- [Keycloak WP-013 Result - Privileged Authentication Evidence](./keycloak-wp013-result.md)
- [ADR 0003 - Accept OTP for Privileged Authentication](../decisions/0003-accept-otp-for-privileged-authentication.md)
- [Keycloak WP-014 Result - Service Access Authorization](./keycloak-wp014-result.md)
- [Keycloak WP-015 Result - Direct Admin Drift and Shortcut Rejection](./keycloak-wp015-result.md)
- [Keycloak IAM Control Plane API Validation Plan](./keycloak-iam-bff-validation-plan.md)
- [Keycloak IAM Control Plane API Scope](../architecture/keycloak-iam-bff-scope.md)
- [ADR 0002 - Validate Keycloak IAM With EDRLab IAM Control Plane API](../decisions/0002-validate-keycloak-iam-bff.md)
- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [AGENTS - Current Operating Phase](../../AGENTS.md#current-operating-phase)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [Keycloak Admin Events](https://www.keycloak.org/docs/latest/server_admin/#auditing-admin-events)
- [Keycloak Events](https://www.keycloak.org/docs/latest/server_admin/#events)
- [Keycloak Managing Access to Realm Resources](https://www.keycloak.org/docs/latest/server_admin/#managing-access-to-realm-resources)
- [Keycloak Importing and Exporting Realms](https://www.keycloak.org/server/importExport)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
