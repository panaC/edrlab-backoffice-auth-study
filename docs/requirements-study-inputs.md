# Requirements Study Inputs

This document is the phase-neutral index for historical study inputs that fed the current Phase 2 requirements baseline. Detailed architectural reflection has been split into dedicated architecture decision analysis notes.

The current authoritative requirements source is [Requirements Baseline](./requirements-baseline.md). The unresolved-decision and working-default register is the [Requirements Question Register](./requirements-question-register.md).

## Current Baseline Inputs

| Area | Baseline input | Primary artifact |
| --- | --- | --- |
| Project scope | The project remains limited to the internal backoffice. Company-wide workforce IAM and broad SSO are not part of the current scope. | [Requirements Baseline](./requirements-baseline.md) |
| Selected architecture | The study uses a Backoffice BFF, a central IAM Control Plane, and one or more backend API resource servers. | [Central IAM Control Plane Decision Analysis](./architecture-central-iam-control-plane-decision-analysis.md) |
| Member source of truth | Members are created and managed by administrators. Public self-registration is out of scope. | [Member Lifecycle](./requirements-member-lifecycle.md) |
| Authentication protocol | OIDC-compatible login remains part of the study baseline for human backoffice users. | [OAuth2 and OIDC Protocol Boundary Decision Analysis](./architecture-oauth-oidc-protocol-decision-analysis.md) |
| API access | Protected APIs validate access tokens and enforce permissions server-side. | [Token and API Access Strategy Decision Analysis](./architecture-token-and-api-access-decision-analysis.md) |
| RBAC baseline | The first model starts with `admin` and `member` roles, with explicit permissions where needed. | [Initial Permission Model](./requirements-initial-permission-model.md) |
| Administration API | The first baseline treats the Backoffice UI through the BFF as the only admin API consumer. | [Requirements Baseline](./requirements-baseline.md) |
| Service-to-service access | Service-to-service authentication is a future theoretical extension, not part of the first study or minimal PoC scope. | [Requirements Baseline](./requirements-baseline.md) |
| Auditability | Privileged IAM changes and access-review evidence must be auditable. | [Security Threat Model](./security-threat-model.md) |
| Operations ownership | The owning team and operating model remain to be defined before production. | [Operational Model](./operational-model.md) |

## Extracted Architecture Analysis

| Analysis note | Main question |
| --- | --- |
| [Central IAM Control Plane Decision Analysis](./architecture-central-iam-control-plane-decision-analysis.md) | Should the study continue with a central IAM Control Plane, or narrow to an application-owned authentication and authorization model? |
| [OAuth2 and OIDC Protocol Boundary Decision Analysis](./architecture-oauth-oidc-protocol-decision-analysis.md) | Should OAuth2/OIDC remain part of the requirements baseline, and what problem does each protocol layer solve? |
| [Token and API Access Strategy Decision Analysis](./architecture-token-and-api-access-decision-analysis.md) | Should the first PoC use short-lived JWT access tokens, introspection, runtime authorization lookup, or another access-check strategy? |

These notes are not accepted decision records. They document Phase 2 reasoning, options, trade-offs, risks, evidence needed, and current working positions.

## Remaining Study Inputs

The historical study inputs have been consolidated into more focused artifacts:

- requirement IDs and evaluation-gate traceability live in [Requirements Baseline](./requirements-baseline.md);
- unresolved decisions and accepted working defaults live in the [Requirements Question Register](./requirements-question-register.md);
- product-neutral evaluation criteria live in [Evaluation Framework](./evaluation-framework.md);
- member lifecycle behavior lives in [Member Lifecycle](./requirements-member-lifecycle.md);
- RBAC and initial permissions live in [Initial Permission Model](./requirements-initial-permission-model.md);
- BFF session and token handling lives in [BFF Sessions and Token Handling](./security-bff-sessions-and-token-handling.md);
- concrete abuse scenarios live in [Security Threat Model](./security-threat-model.md);
- operational readiness lives in [Operational Model](./operational-model.md).

## Traceability

| Topic | Supporting artifact |
| --- | --- |
| Requirements source of truth | [Requirements Baseline](./requirements-baseline.md) |
| Open decisions and working defaults | [Requirements Question Register](./requirements-question-register.md) |
| Central architecture shape | [Central IAM Control Plane Decision Analysis](./architecture-central-iam-control-plane-decision-analysis.md) |
| OAuth2/OIDC protocol rationale | [OAuth2 and OIDC Protocol Boundary Decision Analysis](./architecture-oauth-oidc-protocol-decision-analysis.md) |
| Token and API access strategy | [Token and API Access Strategy Decision Analysis](./architecture-token-and-api-access-decision-analysis.md) |
| Conceptual IAM reading path | [IAM Wiki](./wiki/README.md) |

## References

- [Project README](../README.md)
- [Requirements Baseline](./requirements-baseline.md)
- [Requirements Question Register](./requirements-question-register.md)
- [Evaluation Framework](./evaluation-framework.md)
- [Minimal Backoffice IAM Architecture](./architecture-minimal-backoffice-iam.md)
