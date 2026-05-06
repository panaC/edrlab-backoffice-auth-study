# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-05-06

### Changed

- Replaced prefix-based study document naming with a folder-based documentation structure and added `docs/README.md` plus `docs/decisions/README.md`.
- Clarified that the project study metadata block does not apply to conceptual wiki pages.
- Updated `FS-003` in `README.md` to narrow the mutable attribute examples to email and name.
- Updated `FS-013` in `README.md` to keep recovery, authenticator reset, administrator recovery, audit access, and future break-glass responsibility under super-admin responsibility.
- Refined Phase 2 requirements to mark audit reads, authenticator reset, administrator recovery, role definition changes, and break-glass activation as super-admin-only minimum operations.
- Refined Phase 2 PoC framing to keep the first protected backend test minimal with one protected service.
- Refined Phase 2 RBAC requirements to make role assignments permanent by default.
- Moved initial scope framing from current inputs into explicit Phase 2 requirement groups.
- Aligned architecture option framing with the requirements baseline for access-token constraints, privileged login controls, append-only audit records, and the minimal protected-service PoC boundary.
- Reframed JWT from a fixed baseline requirement into an access-token format option to compare against opaque tokens and introspection.
- Removed `RB-039` as a standalone baseline requirement and kept access-token format as an architecture evaluation question.
- Clarified `RB-005` so admins manage role assignments, while role creation remains a super-admin responsibility.
- Clarified member lifecycle transitions in `RB-013`: admins may disable `active` members, restore `disabled` members to `active`, and archive `disabled` members; `archived` members are non-restorable in the baseline.
- Added `RB-048` to require Phase 2 threat modeling and security requirement refinement before candidate evaluation.
- Removed the duplicate out-of-scope section from the requirements baseline so scope exclusions stay centralized in the root `README.md`.
- Simplified `RB-016` to require defining how already-issued access stops without embedding JWT-versus-opaque-token comparison in the requirement text.

### Added

- Added the initial Phase 2 threat model skeleton under `docs/risks/threat-model.md`.
- Added initial Phase 2 project requirements based on current stakeholder scoping answers.
- Added initial Phase 2 architecture option framing for monolithic, modular monolithic, split control-plane, microservices, and hybrid IAM shapes.
- Added the Phase 2 requirements baseline under `docs/requirements/baseline.md`.

### Removed

- Removed the initial Phase 2 project requirements document at stakeholder request.
