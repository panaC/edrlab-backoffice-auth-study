# Abstract

This repository contains the EDRLab backoffice access-control study.

The study objective is to define, compare, and eventually recommend the simplest secure way to authenticate selected backoffice users, manage their accounts, control access to company-controlled protected backend services, and audit privileged or security-relevant actions without expanding into public customer identity or a company-wide IAM replacement.

## Current State

Current phase: Phase 5 - Review and Decision.

The requirements work is consolidated:

- [README.md](./README.md) is the project entry point. It summarizes project purpose, actor model, scope, roadmap, open study questions, and documentation links.
- [FEATURE-REQUIREMENTS.md](./FEATURE-REQUIREMENTS.md) is the single review-state feature-requirements source for the access-control capability, currently covering `FR-001` through `FR-044`.
- The former `docs/requirements/baseline.md` file has been retired after coverage review.
- [docs/requirements/feature-requirements-review.md](./docs/requirements/feature-requirements-review.md) records the consolidation trail, validation decisions, final review slices, onboarding review, baseline coverage review, and retirement decision.

The current validated access-control model keeps fixed account types separate from service-access roles:

- account types are `super-admin`, `admin`, and `member`;
- account type is fixed at account creation and cannot be changed, merged, or elevated later;
- service-access roles describe protected backend service access and do not grant account-management responsibilities;
- active admins automatically receive access to every protected backend service covered by service-access roles;
- `super-admin` is a high-level administration superset of `admin`, inheriting admin protected-service access and member-management capabilities while adding admin account management, service-access-role catalog management, and audit consultation;
- service-access roles are assigned to members only; inherited admin or super-admin protected-service access does not require assigning service-access roles to privileged account types;
- members access protected backend services only when active and assigned a covering active service-access role.

The identity-provider and onboarding boundary is now explicit:

- the identity provider or authentication system owns authentication, invitation delivery, credentials, MFA, identity-provider login sessions, and identity-provider recovery;
- the access-control capability owns backoffice account state, lifecycle, immutable subject links, service-access roles, protected-service authorization, and project audit evidence;
- an authenticated identity must resolve to exactly one linked backoffice account before authorization is evaluated;
- identity-provider claims, groups, or roles must not override the backoffice account type, lifecycle state, service-access-role assignments, or audit requirements;
- automatic onboarding activation may create the immutable authenticated-subject link only when the backoffice finds exactly one invited account with no existing subject link and a verified matching email; production admin and super-admin onboarding also requires privileged-authentication evidence;
- unsafe onboarding matches fail closed: no subject link, no activation, no authorization, and administrative intervention required.

The completed Phase 2 and Phase 3 study artifacts, plus the Phase 4 Keycloak PoC results, provide the evidence base for the Phase 5 review:

- [docs/risks/threat-model.md](./docs/risks/threat-model.md) frames protected assets, trust boundaries, threat scenarios, requirement-refinement candidates, and review questions.
- [docs/architecture/options.md](./docs/architecture/options.md) frames plausible architecture shapes without choosing a final target architecture.
- [docs/evaluation/technical-solutions.md](./docs/evaluation/technical-solutions.md) identifies three concrete candidates for later evaluation: Auth0 managed login with local access control, self-hosted Keycloak with local access control, and a Spring-based local IAM control plane.
- [docs/evaluation/solution-choice.md](./docs/evaluation/solution-choice.md) records the original self-hosted Keycloak candidate selection and closes Phase 3.
- [docs/decisions/0001-choose-keycloak-for-validation.md](./docs/decisions/0001-choose-keycloak-for-validation.md) records the original Keycloak validation decision, now superseded for the active validation boundary.
- [docs/decisions/0002-validate-keycloak-iam-bff.md](./docs/decisions/0002-validate-keycloak-iam-bff.md) records the accepted active direction: Keycloak as IAM source with an EDRLab IAM Control Plane API.
- [docs/decisions/0003-accept-otp-for-privileged-authentication.md](./docs/decisions/0003-accept-otp-for-privileged-authentication.md) records the accepted OTP privileged-authentication decision for the current direction.
- [docs/poc/keycloak-validation-plan.md](./docs/poc/keycloak-validation-plan.md) is the original Phase 4 entry plan for the targeted non-production Keycloak validation.
- [docs/poc/keycloak-iam-bff-validation-plan.md](./docs/poc/keycloak-iam-bff-validation-plan.md) is the active Phase 4 validation plan for Keycloak as IAM source with an EDRLab IAM Control Plane API.
- [docs/evaluation/phase-5-review-note.md](./docs/evaluation/phase-5-review-note.md) summarizes what the Keycloak IAM Control Plane API PoC validates, what remains risky, which decisions remain open, and the minimum conditions before any Phase 6 MVP authorization.

The study has completed Phase 4 by producing targeted non-production Keycloak PoC evidence. Phase 5 is now the review and decision step. It is not production approval and does not start Phase 6 without an explicit user or project-owner decision.

The expected output remains a documented, evidence-based review decision supported by comparison documents and targeted non-production Proofs of Concept when documentation alone cannot answer a material question.

## Key Links

- [Project brief](./README.md)
- [Consolidated feature requirements](./FEATURE-REQUIREMENTS.md)
- [Feature requirements review](./docs/requirements/feature-requirements-review.md)
- [Threat model](./docs/risks/threat-model.md)
- [Architecture options](./docs/architecture/options.md)
- [Concrete technical solution candidates](./docs/evaluation/technical-solutions.md)
- [Solution choice](./docs/evaluation/solution-choice.md)
- [ADR 0001 - Choose Keycloak for validation](./docs/decisions/0001-choose-keycloak-for-validation.md)
- [Keycloak validation plan](./docs/poc/keycloak-validation-plan.md)
- [Project study documentation map](./docs/README.md)
- [Project governance](./PROJECT-GOVERNANCE.md)
- [Changelog](./CHANGELOG.md)
- [Agent instructions](./AGENTS.md)
- [Conceptual IAM wiki](./docs/wiki/README.md)
