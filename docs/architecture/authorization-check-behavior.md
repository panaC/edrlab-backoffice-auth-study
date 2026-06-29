# Authorization Check Behavior

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Architecture
Last reviewed: 2026-06-29

## Contents

- [Purpose](#purpose)
- [Accepted Behavior](#accepted-behavior)
- [Timeouts and Retries](#timeouts-and-retries)
- [Cache Policy](#cache-policy)
- [Fail-Closed Outcomes](#fail-closed-outcomes)
- [Access-Stop Delay](#access-stop-delay)
- [Audit and Metrics](#audit-and-metrics)
- [HTTP and Cache Headers](#http-and-cache-headers)
- [References](#references)

## Purpose

This document defines the MVP architecture behavior for `POST /iam/authorization/check`, including timeout, retry, cache, fail-closed handling, acceptable access-stop delay, audit, and metrics. Endpoint schemas live in the IAM API contract; the accepted MVP boundary lives in the MVP scope document ([IAM Control Plane API Contract - Authorization](./iam-control-plane-api-contract.md#authorization), [MVP scope](../evaluation/mvp-scope.md), [Project governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)).

Protected services must enforce authorization server-side and deny when access cannot be safely determined (`FR-020`, `FR-021`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).

## Accepted Behavior

| Topic | MVP decision |
| --- | --- |
| Protected service -> IAM API timeout | `500 ms` per attempt for `access-check-demo-service` calling `POST /iam/authorization/check`. |
| IAM API -> Keycloak timeout | `1000 ms` for IAM Control Plane API reads needed to evaluate authorization. |
| Protected-service retry | `1` immediate retry with small jitter after timeout or transient network failure. |
| IAM API -> Keycloak retry | `1` retry only for transient network errors or Keycloak `5xx`; never retry Keycloak `4xx`. |
| Positive cache | No positive authorization cache in the MVP. |
| Negative cache | Optional very short negative cache, maximum `5 seconds`, only for explicit deny decisions. |
| Indeterminate cache | No cache for indeterminate decisions. |
| Access-stop delay | Target is next authorization check; measurable MVP bound is `<= 1 second` outside outage or dependency failure. |
| IAM API outage | `access-check-demo-service` returns HTTP `503` with JSON `{"result":"KO","authorized":false}`. |
| Keycloak outage | IAM API returns HTTP `503` Problem Details; `access-check-demo-service` maps that to HTTP `503` with JSON `{"result":"KO","authorized":false}`. |
| Unknown or unsafe state | Deny when the state is known and not authorized; return indeterminate `503` when the state cannot be verified reliably. |
| Drift | Confirmed direct-admin drift that makes access non-compliant returns deny; incomplete or inconsistent reads return indeterminate `503`. |
| Durable audit for checks | Durable audit is required for deny and indeterminate outcomes; allow outcomes use technical logs and metrics, not mandatory durable audit. Durable audit is stored in the accepted file-backed append-only audit store. |
| Reason codes | IAM API returns machine-readable reason codes to trusted service callers. The demo service exposes only `OK` or `KO`. |
| Cache headers | `POST /iam/authorization/check` responses include `Cache-Control: no-store`. |
| Formal SLO | No formal SLO in Phase 5; metrics must be planned. |

## Timeouts and Retries

`access-check-demo-service` waits up to `500 ms` per call attempt to the IAM Control Plane API. On timeout or transient network failure, it may perform one immediate retry with small jitter. If the retry does not produce a usable authorization decision, the service fails closed with HTTP `503` and JSON `{"result":"KO","authorized":false}`.

The IAM Control Plane API waits up to `1000 ms` for Keycloak reads required by `authorization/check`. It may retry once on transient network errors or Keycloak `5xx`, but it must not retry Keycloak `4xx` responses because those are not transient infrastructure failures.

The protected service may timeout before the IAM Control Plane API finishes a Keycloak read. That is acceptable for the MVP: the protected service returns fail-closed immediately, while the IAM API may complete later and write audit or logs correlated by `X-Correlation-Id`.

## Cache Policy

| Cache type | MVP policy | Rationale |
| --- | --- | --- |
| Positive allow cache | Forbidden. | A positive cache could keep access alive after disablement, archival, role removal, or role disablement, which would undermine `FR-016` and the next-check access-stop target ([Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)). |
| Negative deny cache | Allowed for at most `5 seconds`, only for explicit deny decisions. | A short deny cache can absorb immediate repeated denials without granting access. It may delay newly granted access, but must not prolong unauthorized access. |
| Indeterminate cache | Forbidden. | Dependency failure, timeout, incomplete reads, or unsafe state must be re-evaluated on the next request rather than cached as durable state. |

Any cache key must include at least the resolved account or subject evidence, `serviceId`, `requiredRole`, decision reason, and relevant state version or timestamp if available. Cache entries must not be shared across users. The Keycloak schema policy requires managed lifecycle, account-type, service-role, and mutation-marker state so the IAM Control Plane API can detect missing, incoherent, or unmanaged state before returning a decision ([Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)).

## Fail-Closed Outcomes

| Situation | IAM API result | Demo service response |
| --- | --- | --- |
| User is active and authorized for `access-check-demo:consult` | `allow` | HTTP `200`, `{"result":"OK","authorized":true}` |
| User is authenticated but inactive, missing role, or outside access rules | `deny` with reason code | HTTP `403`, `{"result":"KO","authorized":false}` |
| User evidence is missing, invalid, expired, or issuer/audience validation fails | authentication failure | HTTP `401`, `{"result":"KO","authorized":false}` |
| IAM API is unreachable from the demo service | no IAM decision | HTTP `503`, `{"result":"KO","authorized":false}` |
| Keycloak is unreachable or times out during IAM evaluation | `indeterminate` Problem Details | HTTP `503`, `{"result":"KO","authorized":false}` |
| Service, role, or account state cannot be read reliably | `indeterminate` Problem Details | HTTP `503`, `{"result":"KO","authorized":false}` |
| Direct-admin drift is confirmed and makes access non-compliant | `deny` with `drift_detected` or related reason | HTTP `403`, `{"result":"KO","authorized":false}` |
| Direct-admin drift or state read is incomplete/incoherent | `indeterminate` Problem Details | HTTP `503`, `{"result":"KO","authorized":false}` |

HTTP `401`, `403`, and `503` follow the HTTP status-code semantics defined by RFC 9110: `401` is for missing or invalid authentication credentials, `403` is refusal after understanding the request, and `503` is temporary inability to handle the request ([RFC 9110 - 401](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.2), [RFC 9110 - 403](https://www.rfc-editor.org/rfc/rfc9110#section-15.5.4), [RFC 9110 - 503](https://www.rfc-editor.org/rfc/rfc9110#section-15.6.4)).

## Access-Stop Delay

The accepted MVP access-stop target is "next authorization check." After account disablement, account archival, member role removal, service-role disablement, or service-role archival, `access-check-demo-service` must return `KO` on the next `authorization/check` evaluation.

The measurable MVP bound is `<= 1 second` outside dependency outage. If the IAM API or Keycloak is unavailable, the service still returns `KO`, but the reason is indeterminate `503` rather than a confirmed business deny.

This keeps the MVP aligned with the no-positive-cache rule and the feature requirement that already-issued protected-service access must stop after lifecycle or role changes (`FR-016`; [Feature requirements](../../FEATURE-REQUIREMENTS.md#feature-requirements)).

## Audit and Metrics

Durable audit events are required for:

- explicit deny decisions;
- indeterminate decisions;
- dependency timeouts that produce `KO`;
- direct-admin drift denials or indeterminate drift reads;
- audit-relevant state changes that caused later access-stop behavior.

Allow decisions do not require durable business audit in the MVP. They must still produce technical logs and metrics with `X-Correlation-Id`, because the team needs latency and reliability evidence before production hardening.

The durable audit events produced by deny and indeterminate outcomes use the accepted local file-backed append-only storage architecture, with one JSON event object per physical line ([Audit Storage Architecture](./audit-storage.md)).

Required MVP metrics:

| Metric | Purpose |
| --- | --- |
| `authorization_check_allow_total` | Count successful allows. |
| `authorization_check_deny_total` | Count explicit denies. |
| `authorization_check_indeterminate_total` | Count fail-closed indeterminate decisions. |
| `authorization_check_latency_ms` | Track p50 and p95 latency. |
| `authorization_check_timeout_total` | Count service-to-IAM and IAM-to-Keycloak timeouts. |
| `authorization_check_retry_total` | Count retries by caller and dependency. |
| `authorization_check_keycloak_error_total` | Count Keycloak dependency failures. |

## HTTP and Cache Headers

`POST /iam/authorization/check` responses must include:

```text
Cache-Control: no-store
X-Correlation-Id: <correlation-id>
```

RFC 9111 defines the `no-store` response directive as an instruction that a cache must not store any part of the request or response and must not use the response for another request ([RFC 9111 - no-store](https://www.rfc-editor.org/rfc/rfc9111#section-5.2.2.5)). This is used here to avoid accidental HTTP-level reuse of authorization decisions. It does not replace the explicit application cache policy above.

The IAM API may include `Retry-After` on `503` responses when it has a useful retry hint, but protected services must still fail closed for the current request.

## References

- [Feature Requirements Specification](../../FEATURE-REQUIREMENTS.md)
- [MVP Scope - Access-Control Production MVP](../evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](./iam-control-plane-api-contract.md)
- [Audit Storage Architecture](./audit-storage.md)
- [Keycloak IAM Schema Policy](./keycloak-iam-schema-policy.md)
- [Project Governance - Phase 6](../../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9111 - HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
