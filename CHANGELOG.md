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

### Added

- Added initial Phase 2 project requirements based on current stakeholder scoping answers.
- Added initial Phase 2 architecture option framing for monolithic, modular monolithic, split control-plane, microservices, and hybrid IAM shapes.
