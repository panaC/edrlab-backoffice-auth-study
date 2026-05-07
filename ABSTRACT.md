# Abstract

This repository contains the EDRLab backoffice access-control study.

The study objective is to define, compare, and eventually recommend the simplest secure way to authenticate selected backoffice users, manage their accounts, control access to company-controlled protected backend services, and audit privileged or security-relevant actions.

## Current State

Current phase: Phase 2 - Requirements and Risk Framing.

As of 2026-05-07, the requirements work has been consolidated:

- `README.md` is the project entry point. It summarizes project purpose, actor model, scope, roadmap, open study questions, and documentation links.
- `FEATURE-REQUIREMENTS.md` is the single feature-requirements source for the access-control capability.
- The former `docs/requirements/baseline.md` file has been retired after coverage review.
- `docs/requirements/feature-requirements-review.md` records the consolidation trail, validation decisions, baseline coverage review, and retirement decision.

The current validated access-control model keeps fixed account types separate from service-access roles:

- account types are `super-admin`, `admin`, and `member`;
- account type is fixed at account creation and cannot be changed later;
- service-access roles describe protected backend service access and do not grant account-management responsibilities;
- active admins automatically receive access to every protected backend service covered by service-access roles;
- admins and super-admins can assign service-access roles to members;
- super-admins manage the role catalog and audit access but do not receive protected-service access through service-access roles;
- members access protected backend services only when active and assigned a covering service-access role.

The study still does not choose a final product, vendor, architecture, hosting model, database, implementation stack, token format, session strategy, browser storage model, or production deployment model. Those remain open study questions unless explicitly promoted into the consolidated feature requirements.

The expected output remains a documented, evidence-based technical recommendation supported by comparison documents and targeted non-production Proofs of Concept when documentation alone cannot answer a material question.

## Key Links

- [Project brief](./README.md)
- [Consolidated feature requirements](./FEATURE-REQUIREMENTS.md)
- [Feature requirements review](./docs/requirements/feature-requirements-review.md)
- [Project study documentation map](./docs/README.md)
- [Project governance](./PROJECT-GOVERNANCE.md)
- [Changelog](./CHANGELOG.md)
- [Agent instructions](./AGENTS.md)
- [Conceptual IAM wiki](./docs/wiki/README.md)
