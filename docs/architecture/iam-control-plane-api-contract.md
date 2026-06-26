# IAM Control Plane API Contract

Status: Accepted
Phase: Phase 5 - Review and Decision
Scope: Architecture
Last reviewed: 2026-06-26

## Contents

- [Purpose](#purpose)
- [Contract Summary](#contract-summary)
- [Bootstrap Process](#bootstrap-process)
- [Conventions](#conventions)
- [Actors and Authentication](#actors-and-authentication)
- [Endpoints](#endpoints)
- [Operational Authorization](#operational-authorization)
- [Error Contract](#error-contract)
- [Idempotence](#idempotence)
- [Audit](#audit)
- [Phase 6 Implementation Inputs](#phase-6-implementation-inputs)
- [References](#references)

## Purpose

This document fixes the accepted MVP contract for the EDRLab IAM Control Plane API. It turns the accepted Keycloak IAM Control Plane architecture into concrete API boundaries for endpoints, actors, service-to-service authentication, operation authorization, errors, idempotence, and audit, and now constrains Phase 6 implementation ([ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md), [ADR 0005](../decisions/0005-authorize-phase-6-production-mvp.md), [MVP scope](../evaluation/mvp-scope.md)).

The contract is intentionally limited to the MVP scope. It does not start Phase 6 implementation, choose a framework, create production code, or define deployment topology ([Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

## Contract Summary

| Topic | Decision |
| --- | --- |
| API style | REST API under `/iam`. |
| Representation | JSON request and response bodies everywhere. Error responses use Problem Details for HTTP APIs from RFC 9457, serialized as `application/problem+json` ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)). |
| Account identifier | API paths use the stable internal account ID, never email or Keycloak user ID, because account state, lifecycle, roles, and audit must reference a stable account identifier (`FR-009`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Protected service | The first MVP protected service is `access-check-demo-service`. |
| Initial service role | The first MVP service-access role is `access-check-demo:consult`. |
| Protected-service result | The access-check demo returns JSON containing `result: "OK"` or `result: "KO"` plus an HTTP status. |
| Correlation | Clients may send `X-Correlation-Id`; the IAM Control Plane API generates one when missing and returns it in every response. |
| Audit storage | Local file-backed append-only storage with one JSON event object per physical line. |
| Keycloak schema | Managed Keycloak User Profile attributes, unmanaged attributes disabled, account-type client roles on `edrlab-backoffice`, and service-access client roles on protected-service clients. |
| Direct Keycloak administration | Not a business API path. Business administration goes through the EDRLab Admin Console and IAM Control Plane API (`FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [ADR 0004](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)). |

## Bootstrap Process

`bootstrap-process` is necessary in the contract as a special initialization actor, but it is not a normal public API actor.

The reason is simple: the first `super-admin` cannot be created by an existing `super-admin`, because none exists yet. `FR-008` explicitly keeps first-super-admin provisioning separate from normal self-service and routine business administration ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). The contract therefore models `bootstrap-process` so the exception is explicit, auditable, and not confused with a reusable backdoor.

MVP rule:

- `bootstrap-process` runs during MVP build or initialization.
- It is outside the public IAM Control Plane API.
- It may create or seed the first `super-admin` only when the environment has no existing valid `super-admin`.
- It must be idempotent.
- It must emit an EDRLab audit event.
- Its exact initialization mechanism, credential handling, secret source, and audit event shape remain Phase 6 implementation details.

## Conventions

| Convention | Decision |
| --- | --- |
| Base path | `/iam` |
| Request body format | JSON where a request body exists. |
| Success response format | JSON. Empty success responses may use `204 No Content` only where listed below. |
| Error response format | `application/problem+json` following RFC 9457 ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)). |
| Path account identifier | `{accountId}` is the stable internal EDRLab account ID. |
| Path service-role identifier | `{roleId}` is the stable service-access role identifier, for example `access-check-demo:consult`. |
| Correlation header | `X-Correlation-Id`, optional on request and always present on response. |

The IAM Control Plane API must validate the issuer, audience, expiry, and subject of security tokens before using them for account resolution or service authorization. The feature requirements forbid frontend-only authorization and unmanaged raw-claim authorization shortcuts (`FR-020`, `FR-021`, `FR-033`, `FR-038`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

The Keycloak IAM schema policy is fixed separately: EDRLab IAM user attributes are managed attributes, unmanaged attributes are disabled, account type is exactly one `edrlab-backoffice` client role, and the first service-access role maps to client `access-check-demo-service` role `consult` ([Keycloak IAM schema policy](./keycloak-iam-schema-policy.md)).

## Actors and Authentication

| Actor | Authenticates as | Allowed API surface |
| --- | --- | --- |
| `member` | Browser user authenticated through Keycloak/OIDC and resolved to an active linked `member` account. | `GET /iam/me`, `GET /iam/me/services`, and protected service access when authorized by service-access role. |
| `admin` | Browser user authenticated through Keycloak/OIDC and resolved to an active linked `admin` account. | Member account management, member service-role assignment/removal, own profile, own effective services. |
| `super-admin` | Browser user authenticated through Keycloak/OIDC and resolved to an active linked `super-admin` account. | Admin and member account management, service-role catalog management, member role assignment/removal, audit consultation, own profile, own effective services. |
| `protected-service` | Dedicated service client using OAuth 2.0 client credentials through Keycloak. | `POST /iam/authorization/check` only. |
| `bootstrap-process` | Controlled build or initialization process, outside the public API. | First `super-admin` seed only, when no valid `super-admin` exists. |

Admin Console to IAM API authentication:

- The EDRLab Admin Console sends the user's authenticated session evidence to the IAM Control Plane API.
- The IAM Control Plane API resolves the authenticated subject to exactly one backoffice account before authorizing an operation (`FR-036`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).
- The IAM Control Plane API denies the operation when the account is not active, cannot be resolved safely, or lacks the required account type or management scope (`FR-021`, `FR-033`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

Protected service to IAM API authentication:

- `access-check-demo-service` uses a dedicated Keycloak confidential client and OAuth 2.0 client credentials to call `POST /iam/authorization/check`.
- OAuth 2.0 defines the client credentials grant for confidential clients that request tokens using their own credentials, and Keycloak service accounts support client credentials for OIDC clients ([RFC 6749 - Client Credentials Grant](https://www.rfc-editor.org/rfc/rfc6749#section-4.4), [Keycloak - Using a service account](https://www.keycloak.org/docs/latest/server_admin/#_service_accounts)).
- The protected service authenticates itself with a service token and supplies the current end-user access evidence to the IAM Control Plane API. The IAM Control Plane API, not the protected service, performs account resolution and authorization.

## Endpoints

### Self

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `GET` | `/iam/me` | `member`, `admin`, `super-admin` | Return the current linked account profile visible to the current user. |
| `GET` | `/iam/me/services` | `member`, `admin`, `super-admin` | Return current effective protected-service access, including `access-check-demo-service` when applicable. |

### Accounts

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `GET` | `/iam/accounts` | `admin`, `super-admin` | List accounts in the actor's management scope. |
| `POST` | `/iam/accounts` | `admin`, `super-admin` | Create an `invited` account. `admin` may create `member`; `super-admin` may create `admin` and `member`. |
| `GET` | `/iam/accounts/{accountId}` | `admin`, `super-admin` | Read an account in the actor's management scope. |
| `PATCH` | `/iam/accounts/{accountId}/profile` | `admin`, `super-admin` | Update allowed profile fields in the actor's management scope. |
| `POST` | `/iam/accounts/{accountId}/disable` | `admin`, `super-admin` | Disable an active account in the actor's management scope. |
| `POST` | `/iam/accounts/{accountId}/restore` | `admin`, `super-admin` | Restore a disabled account in the actor's management scope. |
| `POST` | `/iam/accounts/{accountId}/archive` | `admin`, `super-admin` | Archive a disabled account in the actor's management scope. |

### Onboarding

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `POST` | `/iam/onboarding/activate` | Authenticated browser subject | Safely link and activate one invited account when the match rules are satisfied. This is not a member/admin/super-admin operation because the account may not be active yet. |

The onboarding endpoint uses the safe automatic activation rules from `FR-043` and must deny unsafe activation under `FR-044` ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Service-Access Roles

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `GET` | `/iam/service-roles` | `admin`, `super-admin` | List service-access roles. Admins need read visibility to assign roles to members; only super-admins mutate the catalog. |
| `POST` | `/iam/service-roles` | `super-admin` | Create a service-access role. |
| `GET` | `/iam/service-roles/{roleId}` | `admin`, `super-admin` | Read a service-access role. |
| `PATCH` | `/iam/service-roles/{roleId}` | `super-admin` | Update a service-access role. |
| `POST` | `/iam/service-roles/{roleId}/disable` | `super-admin` | Disable a service-access role. |
| `POST` | `/iam/service-roles/{roleId}/archive` | `super-admin` | Archive a disabled service-access role. |

### Service-Role Assignment

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `PUT` | `/iam/accounts/{accountId}/service-roles/{roleId}` | `admin`, `super-admin` | Assign an active service-access role to a `member` account in the actor's management scope. |
| `DELETE` | `/iam/accounts/{accountId}/service-roles/{roleId}` | `admin`, `super-admin` | Remove a service-access role from a `member` account in the actor's management scope. |

Service-access roles must not be assigned to `admin` or `super-admin` accounts (`FR-002`, `FR-003`, `FR-004`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

### Authorization

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `POST` | `/iam/authorization/check` | `protected-service` | Return an allow/deny decision for a protected-service request. |

Runtime behavior for timeout, retry, cache, fail-closed handling, access-stop delay, audit, and metrics is fixed in the accepted [Authorization Check Runtime Behavior](./authorization-check-behavior.md) note.

Request body:

```json
{
  "subjectToken": "<current-user-token-or-session-evidence>",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult"
}
```

Success response body:

```json
{
  "decision": "allow",
  "accountId": "acc_123",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult",
  "correlationId": "01J..."
}
```

Deny response body:

```json
{
  "decision": "deny",
  "reason": "not_authorized",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult",
  "correlationId": "01J..."
}
```

The access-check demo service maps the authorization decision to its external MVP response:

| Case | HTTP status | JSON body |
| --- | --- | --- |
| Authorized for `access-check-demo-service` | `200` | `{"result":"OK","authorized":true}` |
| Authenticated but not authorized | `403` | `{"result":"KO","authorized":false}` |
| Missing or invalid authentication | `401` | `{"result":"KO","authorized":false}` |
| Authorization cannot be safely determined | `503` | `{"result":"KO","authorized":false}` |

### Audit

| Method | Path | Actor | Purpose |
| --- | --- | --- | --- |
| `GET` | `/iam/audit/events` | `super-admin` | Return chronological audit events with minimal filters. |
| `GET` | `/iam/audit/events/{eventId}` | `super-admin` | Return basic event detail. |

Audit export and advanced audit search are out of scope for the initial MVP ([MVP scope](../evaluation/mvp-scope.md#audit)). Durable audit storage is accepted as local file-backed append-only storage with one JSON event object per physical line ([Audit storage policy](./audit-storage.md)).

## Operational Authorization

| Operation group | `member` | `admin` | `super-admin` | `protected-service` | `bootstrap-process` |
| --- | --- | --- | --- | --- | --- |
| Read own profile | Yes | Yes | Yes | No | No |
| Read own effective services | Yes | Yes | Yes | No | No |
| Create account | No | `member` only | `admin`, `member` | No | First `super-admin` only during initialization |
| List/read managed accounts | No | `member` accounts | `admin`, `member` accounts | No | No |
| Update managed profile | No | `member` accounts | `admin`, `member` accounts | No | No |
| Disable/restore/archive accounts | No | `member` accounts | `admin`, `member` accounts | No | No |
| Manage service-role catalog | No | Read only | Create, update, disable, archive | No | No |
| Assign/remove member service roles | No | `member` accounts only | `member` accounts only | No | No |
| Consult audit | No | No | Chronological list and basic detail | No | No |
| Authorization check | No | No | No | Yes | No |

All administrative authorization is enforced server-side by the IAM Control Plane API and must not rely on frontend-only checks (`FR-033`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Error Contract

The IAM Control Plane API uses RFC 9457 Problem Details for error responses. RFC 9457 defines a JSON problem detail object and the `application/problem+json` media type for machine-readable HTTP API error details ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)).

Minimum error body:

```json
{
  "type": "https://docs.edrlab.example/problems/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "The authenticated account is not allowed to perform this operation.",
  "instance": "/iam/accounts/acc_123/archive",
  "code": "forbidden",
  "correlationId": "01J..."
}
```

`code` and `correlationId` are project extension members. Validation errors may add an `errors` extension with field-level details.

| HTTP status | Use |
| --- | --- |
| `400` | Invalid request syntax, malformed JSON, unsupported query shape, or invalid pagination/filter parameter. |
| `401` | Missing, invalid, expired, or unverifiable authentication. |
| `403` | Authenticated actor is not allowed to perform the operation. |
| `404` | Target resource is not found or not visible in the actor's management scope. |
| `409` | Conflict with an invariant or existing state, such as duplicate invited-account match or attempted subject-link conflict. |
| `422` | Well-formed request rejected by a business rule, such as archiving an active account before disablement. |
| `503` | Required authorization or IAM dependency is unavailable, stale, or cannot safely determine the result; callers must treat this as fail-closed. |

## Idempotence

| Endpoint | Idempotence rule |
| --- | --- |
| `POST /iam/accounts/{accountId}/disable` | Repeating disable on an already disabled account returns success with no state change. Disabling an archived account is rejected. |
| `POST /iam/accounts/{accountId}/restore` | Repeating restore on an already active account returns success with no state change. Restoring an archived account is rejected. |
| `POST /iam/accounts/{accountId}/archive` | Repeating archive on an already archived account returns success with no state change. Archiving an active account is rejected. |
| `PUT /iam/accounts/{accountId}/service-roles/{roleId}` | Repeating the same assignment returns success and does not create duplicate role state. |
| `DELETE /iam/accounts/{accountId}/service-roles/{roleId}` | Repeating removal of an absent assignment returns success with no state change. |
| `POST /iam/onboarding/activate` | Repeating activation for an account already active with the same immutable subject returns success with the existing link. Attempts with a different subject are rejected. |

All mutating calls, including idempotent no-op retries, create audit events. The event outcome must distinguish `changed`, `no_change`, and `rejected`.

## Audit

The IAM Control Plane API must create local EDRLab audit events for:

- account creation, profile update, activation, disablement, restoration, archival, and rejected lifecycle changes;
- authenticated-subject link creation and rejected or attempted link mutation;
- service-access-role creation, update, disablement, archival, assignment, and removal;
- protected-service authorization denials;
- audit reads;
- first-super-admin bootstrap;
- rejected privileged onboarding or missing privileged-authentication evidence.

Audit events include at minimum:

| Field | Purpose |
| --- | --- |
| `eventId` | Stable audit event identifier. |
| `occurredAt` | Server-side event timestamp. |
| `actorType` | `member`, `admin`, `super-admin`, `protected-service`, or `bootstrap-process`. |
| `actorAccountId` | Present for linked account actors. |
| `clientId` | Present for service actors. |
| `operation` | Operation name, such as `account.disable` or `authorization.check.denied`. |
| `targetType` | Target resource type. |
| `targetId` | Target resource identifier. |
| `outcome` | `changed`, `no_change`, or `rejected`. |
| `reasonCode` | Stable machine-readable reason where useful. |
| `correlationId` | Correlation ID shared across API response, logs, Keycloak event references, and protected-service calls. |
| `keycloakEventRef` | Optional Keycloak event reference when useful. |

`X-Correlation-Id` exists to connect a user action across Admin Console, IAM Control Plane API, Keycloak calls, protected-service calls, logs, and audit. It is not authorization evidence. When a client supplies it, the IAM Control Plane API validates and normalizes it; when absent, the API generates one. The API returns the value in `X-Correlation-Id`, includes it in Problem Details, and stores it in audit events.

## Phase 6 Implementation Inputs

| Input | Status |
| --- | --- |
| Exact routes for `access-check-demo-service` | Open. This contract fixes IAM API routes and response semantics, but the demo service route can be selected during Phase 6 implementation. |
| JSON schema detail | Phase 6 implementation detail. Field-level schemas must be produced from this accepted contract. |
| Timeout, retry, cache, and access-stop delay | Closed for MVP behavior. See [Authorization Check Runtime Behavior](./authorization-check-behavior.md). |
| Durable audit storage | Closed for MVP storage choice. See [Audit Storage Policy](./audit-storage.md). |
| Keycloak IAM schema policy | Closed for MVP schema choice. See [Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md). |
| Bootstrap implementation mechanism | Open Phase 6 implementation detail. The contract fixes that bootstrap is outside the public API, idempotent, controlled, and audited. |

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [MVP Scope - Keycloak IAM Control Plane API](../evaluation/mvp-scope.md)
- [Authorization Check Runtime Behavior](./authorization-check-behavior.md)
- [Audit Storage Policy](./audit-storage.md)
- [Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)
- [ADR 0004 - Adopt Keycloak IAM Control Plane for MVP Design](../decisions/0004-adopt-keycloak-iam-control-plane-for-mvp-design.md)
- [ADR 0005 - Authorize Phase 6 Production MVP](../decisions/0005-authorize-phase-6-production-mvp.md)
- [Project Governance - Phase 5](../../PROJECT-GOVERNANCE.md#phase-5---review-and-decision)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 9457 - Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [Keycloak - Using a service account](https://www.keycloak.org/docs/latest/server_admin/#_service_accounts)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
