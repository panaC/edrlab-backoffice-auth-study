# Abstract

This repository contains the EDRLab backoffice access-control study.

The study objective is to define, compare, and eventually recommend the simplest secure way to authenticate selected backoffice users, manage their accounts, control access to company-controlled protected backend services, and audit privileged or security-relevant actions without expanding into public customer identity or a company-wide IAM replacement.

## Current State

Current phase: Phase 3 - Solution Choice.

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

The completed Phase 2 study artifacts provide the evidence base for Phase 3 solution choice:

- [docs/risks/threat-model.md](./docs/risks/threat-model.md) frames protected assets, trust boundaries, threat scenarios, requirement-refinement candidates, and review questions.
- [docs/architecture/options.md](./docs/architecture/options.md) frames plausible architecture shapes without choosing a final target architecture.
- [docs/evaluation/technical-solutions.md](./docs/evaluation/technical-solutions.md) identifies three concrete candidates for later evaluation: Auth0 managed login with local access control, self-hosted Keycloak with local access control, and a Spring-based local IAM control plane.
- [docs/evaluation/solution-choice.md](./docs/evaluation/solution-choice.md) records self-hosted Keycloak with a local access-control service as the Phase 3 candidate solution to validate.
- [docs/decisions/0001-choose-keycloak-for-validation.md](./docs/decisions/0001-choose-keycloak-for-validation.md) records the accepted decision and its validation conditions.

The study has chosen a candidate solution to validate. That choice is not production approval, does not start implementation, and does not replace the later Proof of Concept and review decision.

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
- [Project study documentation map](./docs/README.md)
- [Project governance](./PROJECT-GOVERNANCE.md)
- [Changelog](./CHANGELOG.md)
- [Agent instructions](./AGENTS.md)
- [Conceptual IAM wiki](./docs/wiki/README.md)
