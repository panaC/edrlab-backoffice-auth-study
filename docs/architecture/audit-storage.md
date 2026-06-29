# Audit Storage Architecture

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Architecture
Last reviewed: 2026-06-29

## Contents

- [Purpose](#purpose)
- [Accepted Decision](#accepted-decision)
- [Event File Format](#event-file-format)
- [Append-Only Rules](#append-only-rules)
- [Retention](#retention)
- [Read and Export](#read-and-export)
- [Correlation](#correlation)
- [Proposed Subject-Link Ledger](#proposed-subject-link-ledger)
- [Backup and Restore](#backup-and-restore)
- [Confidentiality](#confidentiality)
- [Operational Limits](#operational-limits)
- [References](#references)

## Purpose

This document defines the durable audit storage architecture for the MVP: a basic local file-backed audit store, append-only, with one JSON event object per physical line. Concrete runtime commands, paths, backup scripts, and restore scripts belong in the access-control runtime runbook ([MVP scope](../evaluation/mvp-scope.md), [Access-Control runtime runbook](../../access-control/README.md#backup-and-restore), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

The project still treats local EDRLab audit as the authoritative business audit source. Keycloak events remain supplemental provider evidence and do not replace the local audit records required for account lifecycle, subject-link, service-role, protected-service denial, audit-read, onboarding, bootstrap, and recovery-related events (`FR-027`, `FR-028`, `FR-035`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Accepted Decision

| Topic | MVP decision |
| --- | --- |
| Storage type | Local durable file storage. |
| Write model | Append-only application writes. Existing audit lines are never edited or deleted by normal application code. |
| Record format | One complete JSON object per physical line. |
| Encoding | UTF-8. JSON is the project format for audit event serialization, aligned with RFC 8259 JSON syntax and interoperability guidance ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)). |
| Retention | Indefinite retention under the initial policy. |
| Read path | `super-admin` reads through the IAM Control Plane API audit endpoints. |
| Export | Out of scope for the initial MVP. A later export feature must be explicitly accepted and audited. |
| Correlation | Every event includes `correlationId`; Keycloak event references are optional supplemental links. |
| Backup | Audit files are included in backup and restore planning before production data is trusted. |
| Confidentiality | Audit files contain security-relevant metadata only; secrets and raw credentials are forbidden. |

This is intentionally basic. It is accepted because the first MVP needs durable, reviewable audit evidence without prematurely introducing a database-backed audit subsystem, SIEM integration, WORM storage, or cryptographic tamper-evidence.

## Event File Format

Each physical line in the audit file is one complete JSON object. The application must not pretty-print audit events across multiple lines, because chronological line scanning and append-only review depend on one event per line. JSON object members should use unique names, because RFC 8259 notes that duplicate object member names produce unpredictable receiver behavior ([RFC 8259 - Objects](https://www.rfc-editor.org/rfc/rfc8259)).

The event object uses the minimum event fields exposed by the MVP audit API ([IAM Control Plane API Contract - Audit](./iam-control-plane-api-contract.md#audit)):

Example line:

```json
{"eventId":"evt_01J...","occurredAt":"2026-06-26T13:00:00Z","actorType":"super-admin","actorAccountId":"acc_001","operation":"account.disable","targetType":"account","targetId":"acc_123","outcome":"changed","reasonCode":"requested_by_super_admin","correlationId":"01J...","keycloakEventRef":"kc-admin-event-..."}
```

## Append-Only Rules

The IAM Control Plane API appends a new line for every required audit event. Normal application code must not rewrite, truncate, compact, or delete existing audit lines. If a correction is needed, the application writes a new corrective audit event referencing the original `eventId`; it does not mutate the original record.

Idempotent mutating calls still create audit events when they represent a business operation, because outcomes such as `changed`, `no_change`, and `rejected` must remain visible in the local business audit trail ([Feature requirements `FR-027` and `FR-035`](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

Phase 6 implementation must define file permissions and process ownership so routine runtime users can write audit events without exposing broad edit or read access. OWASP notes that applications may write event logs to the file system, but logs should not be exposed from web-accessible locations and access to log data must be controlled ([OWASP Logging Cheat Sheet - Where to record event data](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#where-to-record-event-data)).

## Retention

The MVP policy is indefinite retention. No automatic deletion, compaction, or retention shortening is accepted in the initial MVP, because `FR-035` requires append-only audit records retained indefinitely and requires explicit review before any later retention, privacy, or deletion policy change ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

File rotation is allowed only as an implementation detail when it preserves every audit event, chronological readability, correlation, backup coverage, and restore behavior. Rotation must not become deletion.

## Read and Export

Audit reading is super-admin-only through the accepted IAM Control Plane API endpoints:

- `GET /iam/audit/events` returns a chronological audit list with minimal filters.
- `GET /iam/audit/events/{eventId}` returns basic event detail.

Audit reads must create audit events, and `admin` or `member` actors must not consult audit records (`FR-028`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [IAM Control Plane API Contract - Audit](./iam-control-plane-api-contract.md#audit)).

Audit export is out of scope for the initial MVP. If export is later added, it must be explicitly accepted, authorized for `super-admin` only unless a later decision changes that rule, and audited as an audit export event.

## Correlation

Every audit event includes `correlationId`. The IAM Control Plane API accepts `X-Correlation-Id` from trusted callers, validates and normalizes it, generates one when missing, returns it on responses, stores it in audit events, and propagates it across protected-service calls, Keycloak calls, technical logs, and Problem Details responses ([IAM Control Plane API Contract - Audit](./iam-control-plane-api-contract.md#audit)).

`correlationId` is operational evidence, not authorization evidence. It helps join related records; it does not prove that a caller was authorized.

`keycloakEventRef` is optional and supplemental. It can link a local EDRLab business event to a Keycloak provider event, but the local file-backed audit event remains the project audit record.

## Proposed Subject-Link Ledger

Status: Proposed, not implemented.

`SEC-DRIFT-004` may require audit-adjacent evidence that is optimized for runtime lookup, not only human audit review. The proposed design is an EDRLab-controlled append-only subject-link ledger outside Keycloak, written by the IAM Control Plane API when first-`super-admin` bootstrap or onboarding activation accepts a subject link ([MVP Security Test Plan - Test Tracker](../evaluation/security-test-plan.md#test-tracker), [Keycloak IAM Schema Policy - Proposed Subject-Link Drift Evidence](./keycloak-iam-schema-policy.md#proposed-subject-link-drift-evidence)).

The proposed ledger would remain JSONL and append-only, with one object per physical line. Each record would be keyed by `accountId`, include a `subjectDigest` rather than a raw bearer token or raw subject token, and include `correlationId` so reviewers can join it to the corresponding bootstrap or onboarding audit event. A runtime reader could build a compact `accountId -> subjectDigest` index and compare it with the current Keycloak `iam.linked_subject` during sensitive operations.

This proposal is not part of the accepted MVP storage behavior yet. Before acceptance, the project must decide whether the digest is plain SHA-256 or HMAC-SHA-256, how HMAC secrets are backed up and rotated if used, how existing active accounts without ledger rows are handled, and whether the ledger file is exposed through audit-read APIs or remains internal operational evidence only.

## Backup and Restore

Audit files are part of the MVP's durable state. Phase 6 must include them in backup, restore, and restore-test planning before production data is trusted. Backup behavior must preserve file contents and event order; restore behavior must make the restored audit records readable through the same IAM Control Plane API audit consultation path.

Backup copies inherit the same confidentiality expectations as live audit files. OWASP notes that log data can be present in repositories, archives, and backups, and that access to logs should be restricted and monitored ([OWASP Logging Cheat Sheet - Protection](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#protection)).

Concrete local backup and restore commands live in the access-control runtime runbook. Deployment-specific backup schedule, off-host storage, encryption mechanism, and restore-test cadence remain operations decisions outside this architecture page ([Access-Control runtime runbook - Backup and Restore](../../access-control/README.md#backup-and-restore)).

## Confidentiality

Audit records must be useful for security review while avoiding unnecessary sensitive data. The MVP audit file must not store passwords, OTP values, recovery codes, access tokens, refresh tokens, client secrets, private keys, raw session identifiers, or raw subject tokens. OWASP recommends excluding, masking, sanitizing, hashing, or encrypting sensitive data before it is written to logs ([OWASP Logging Cheat Sheet - Data to exclude](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude)).

Use stable identifiers and reason codes rather than raw credentials or large request/response bodies. When personal data is necessary for review, prefer stable account identifiers and minimal metadata. Audit file read access is restricted to the application runtime, authorized operators, and `super-admin` consultation through the IAM Control Plane API.

## Operational Limits

This accepted MVP storage is intentionally not:

- a SIEM;
- a database-backed audit ledger;
- WORM or immutable media;
- cryptographic tamper-evidence;
- advanced search or analytics;
- a replacement for Keycloak technical logs or infrastructure logs.

Residual risk: file-backed append-only storage gives a simple durable audit trail, but it depends on operating-system permissions, runtime identity, backups, and operator discipline. Tamper detection, read-only media, centralized log management, or cryptographic integrity can be reviewed later if the risk or compliance profile requires them. OWASP identifies logs as attack targets and recommends considering tamper detection, restricted read privileges, and monitoring of log access ([OWASP Logging Cheat Sheet - Protection](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#protection)).

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [MVP Scope - Access-Control Production MVP](../evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](./iam-control-plane-api-contract.md)
- [Authorization Check Behavior](./authorization-check-behavior.md)
- [Access-Control runtime runbook](../../access-control/README.md)
- [Phase 5 Review Note](../evaluation/phase-5-review-note.md)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [RFC 8259 - The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
