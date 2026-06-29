# Access-Control API Reference

Status: MVP runtime reference
Phase: Phase 6 - Production MVP
Last reviewed: 2026-06-29

This is the endpoint and schema reference for the local Phase 6 access-control
runtime. The MVP boundary is owned by
[docs/evaluation/mvp-scope.md](../../docs/evaluation/mvp-scope.md); runtime
commands are owned by [access-control/README.md](../README.md).

## Contents

- [Authentication](#authentication)
- [Common Conventions](#common-conventions)
- [Health](#health)
- [Accounts](#accounts)
- [Onboarding](#onboarding)
- [Service Roles](#service-roles)
- [Authorization](#authorization)
- [Audit](#audit)

## Authentication

Human-account endpoints use `Authorization: Bearer <user-access-token>`. The IAM
API resolves the actor from server-side token evidence. The local dev actor
header is ignored unless `IAM_ALLOW_DEV_ACTOR_HEADER=true` is explicitly enabled
for focused local tests ([access-control runtime runbook](../README.md#known-mvp-shortcuts)).

`POST /iam/authorization/check` uses service authentication with
`Authorization: Bearer <service-token>`.

Actor classes:

| Actor | Purpose |
| --- | --- |
| `super-admin` | Bootstrap owner and emergency/root IAM operator. |
| `admin` | Backoffice IAM operator inside the approved MVP limits. |
| `member` | Service user who can inspect own identity and effective services. |
| `protected-service` | Service caller using `authorization/check`. |

## Common Conventions

All responses include:

```text
Cache-Control: no-store
X-Correlation-Id: <correlation-id>
```

Clients may send `X-Correlation-Id`. Invalid or missing values are replaced by
the server.

Error responses use `application/problem+json`:

```json
{
  "type": "https://docs.access-control.example/problems/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Operation is not allowed.",
  "code": "forbidden",
  "correlationId": "corr_...",
  "instance": "/iam/accounts"
}
```

Common error codes include `missing_bearer_token`, `forbidden`, `not_found`,
`validation_error`, `duplicate_account_email`, `role_not_active`,
`iam_state_drift`, and `indeterminate`.

## Health

### `GET /healthz`

Response:

```json
{
  "status": "ok"
}
```

## Accounts

Account objects returned by the runtime use this public shape:

```json
{
  "accountId": "acc_123",
  "email": "member@example.test",
  "organization": "MVP Organization",
  "name": "Member One",
  "accountType": "member",
  "lifecycle": "active",
  "hasLinkedSubject": true,
  "serviceRoles": ["access-check-demo:consult"]
}
```

### `GET /iam/me`

Returns the authenticated account.

### `GET /iam/me/services`

Returns effective service access for the authenticated account.

Response:

```json
{
  "services": [
    {
      "serviceId": "access-check-demo-service",
      "roleId": "access-check-demo:consult"
    }
  ]
}
```

### `GET /iam/accounts`

Admin-only account listing.

Response:

```json
{
  "accounts": []
}
```

### `POST /iam/accounts`

Creates an invited account. `admin` may create `member` accounts only.
`super-admin` may create `admin` or `member` accounts.

Request:

```json
{
  "email": "member@example.test",
  "organization": "MVP Organization",
  "name": "Member One",
  "accountType": "member"
}
```

Response: account object.

### `GET /iam/accounts/{accountId}`

Returns one account visible in the actor's management scope.

### `PATCH /iam/accounts/{accountId}/profile`

Updates mutable profile fields only. Protected fields such as `accountId`,
`accountType`, `lifecycle`, `linkedSubject`, and `serviceRoles` are rejected.

Request:

```json
{
  "email": "member@example.test",
  "organization": "MVP Organization",
  "name": "Member One"
}
```

Response: account object.

### `POST /iam/accounts/{accountId}/disable`

Changes an active account to `disabled`. Response: account object.

### `POST /iam/accounts/{accountId}/restore`

Changes a disabled account to `active`. Response: account object.

### `POST /iam/accounts/{accountId}/archive`

Changes a disabled account to `archived`. Response: account object.

## Onboarding

### `POST /iam/onboarding/activate`

Activates exactly one invited account from authenticated bearer evidence. The
request body may be empty. The route rejects client-supplied identity or
authorization-significant fields such as `subject`, `email`, `emailVerified`,
`acr`, `accountType`, `lifecycle`, `linkedSubject`, or `serviceRoles`.

Request:

```json
{}
```

Response: account object.

## Service Roles

Service role objects use this shape:

```json
{
  "roleId": "access-check-demo:consult",
  "serviceId": "access-check-demo-service",
  "status": "active",
  "description": "Initial MVP access-check demo consultation role.",
  "schemaVersion": "iam-schema-v1"
}
```

### `GET /iam/service-roles`

Lists service roles for `admin` and `super-admin`.

Response:

```json
{
  "serviceRoles": []
}
```

### `POST /iam/service-roles`

Creates a service role. `super-admin` only.

Request:

```json
{
  "roleId": "access-check-demo:consult",
  "serviceId": "access-check-demo-service",
  "description": "Initial MVP access-check demo consultation role."
}
```

Response: service role object.

### `GET /iam/service-roles/{roleId}`

Returns one service role.

### `PATCH /iam/service-roles/{roleId}`

Updates mutable service-role metadata. `roleId` and `serviceId` are protected.

Request:

```json
{
  "description": "Updated description"
}
```

Response: service role object.

### `POST /iam/service-roles/{roleId}/disable`

Changes an active service role to `disabled`. Response: service role object.

### `POST /iam/service-roles/{roleId}/archive`

Changes a disabled service role to `archived`. Response: service role object.

### `PUT /iam/accounts/{accountId}/service-roles/{roleId}`

Assigns an active service role to a managed `member` account. Response: account
object.

### `DELETE /iam/accounts/{accountId}/service-roles/{roleId}`

Removes a service role from a managed `member` account. Response: account
object.

## Authorization

### `POST /iam/authorization/check`

Checks current managed IAM state for a protected service. Behavior requirements
for timeout, retry, caching, fail-closed responses, audit, and metrics are
documented in
[docs/architecture/authorization-check-behavior.md](../../docs/architecture/authorization-check-behavior.md).

Request:

```json
{
  "subjectToken": "<user-access-token>",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult"
}
```

Allow response:

```json
{
  "decision": "allow",
  "accountId": "acc_123",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult",
  "correlationId": "corr_..."
}
```

Deny response:

```json
{
  "decision": "deny",
  "reason": "not_authorized",
  "serviceId": "access-check-demo-service",
  "requiredRole": "access-check-demo:consult",
  "correlationId": "corr_..."
}
```

Indeterminate dependency or unsafe-state failures return Problem Details with
HTTP `503` and no allow decision.

## Audit

### `GET /iam/audit/events`

Lists local audit events. `super-admin` only. Audit reads are themselves
audited.

Response:

```json
{
  "events": [
    {
      "eventId": "evt_...",
      "occurredAt": "2026-06-29T12:00:00Z",
      "actorType": "super-admin",
      "actorAccountId": "acc_123",
      "operation": "account.disable",
      "targetType": "account",
      "targetId": "acc_456",
      "outcome": "changed",
      "reasonCode": "active_to_disabled",
      "correlationId": "corr_..."
    }
  ]
}
```

### `GET /iam/audit/events/{eventId}`

Returns one audit event. `super-admin` only.

Audit storage architecture is documented in
[docs/architecture/audit-storage.md](../../docs/architecture/audit-storage.md).

## References

- [MVP scope source of truth](../../docs/evaluation/mvp-scope.md)
- [Access-control runtime runbook](../README.md)
- [Authorization check behavior](../../docs/architecture/authorization-check-behavior.md)
- [Audit storage architecture](../../docs/architecture/audit-storage.md)
- [Keycloak IAM schema policy](../../docs/architecture/keycloak-iam-schema-policy.md)
