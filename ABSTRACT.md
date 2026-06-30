# Abstract

This repository is the EDRLab backoffice access-control workspace. It has moved
from study and validation into Phase 6 production-MVP implementation.

The approved MVP is a Keycloak-backed IAM Control Plane API for selected
backoffice users. It keeps fixed account types (`super-admin`, `admin`,
`member`) separate from service-access roles, supports safe onboarding,
authorizes protected services through server-side `authorization/check`, and
records local append-only business audit
([MVP scope](./docs/evaluation/mvp-scope.md),
[feature requirements](./FEATURE-REQUIREMENTS.md)).

The current runtime lives in [access-control/](./access-control/README.md). It
includes Dockerized Keycloak, the IAM API, `access-check-demo-service`, first
`super-admin` bootstrap, Keycloak-backed IAM state, Docker tests, human e2e
evidence, SMTP-backed onboarding evidence, and backup/restore scripts.

The project is suitable for controlled MVP hardening and staging rehearsal with
non-production data. A production-ready claim still requires closure or accepted
deferral of the remaining readiness gaps: Admin Console UI or accepted operator
workflow, full schema migration and drift workflow, operations evidence, OTP
support posture, security-evidence closure, and runtime shortcut review
([readiness gaps](./docs/evaluation/mvp-scope.md#production-readiness-gaps),
[security tracker](./docs/evaluation/security-test-plan.md#test-tracker)).

## Key Links

- [Project brief](./README.md)
- [MVP scope](./docs/evaluation/mvp-scope.md)
- [Access-control runtime](./access-control/README.md)
- [IAM API contract](./docs/architecture/iam-control-plane-api-contract.md)
- [Security test plan](./docs/evaluation/security-test-plan.md)
- [Changelog](./CHANGELOG.md)
