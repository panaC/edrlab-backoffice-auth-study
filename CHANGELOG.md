# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-05-05

### Added

- Added root `ABSTRACT.md` to summarize the study purpose, architecture, current phase, and key links.
- Added root `CHANGELOG.md` to track project-level documentation and phase changes.
- Added `docs/architecture-central-iam-control-plane-decision-analysis.md` to analyze the selected central IAM architecture against narrower alternatives.
- Added `docs/architecture-oauth-oidc-protocol-decision-analysis.md` to analyze the OAuth2/OIDC protocol boundary and alternatives.
- Added `docs/architecture-token-and-api-access-decision-analysis.md` to analyze JWT, introspection, and runtime access-check trade-offs.
- Added `docs/requirements-baseline.md` as the consolidated Phase 2 requirements baseline with stable requirement IDs and evaluation gate traceability.
- Added `docs/requirements-question-register.md` as the consolidated Phase 2 question register with status, owner, blocked-decision, current-default, and resolution-traceability fields.
- Added `docs/wiki/25-kubernetes-api-access-control.md` to explain Kubernetes' access-control pipeline as a conceptual IAM and API authorization reference model.

### Changed

- Switched the active operating phase in `AGENTS.md` from Phase 1 - IAM Study Foundation to Phase 2 - Requirements Definition.
- Added strict top-level `docs/` file-naming rules to `AGENTS.md` with approved artifact-family prefixes.
- Added `AGENTS.md` guidance for architecture decision analysis notes, including naming, structure, and the distinction from accepted `decision-*.md` records.
- Renamed `docs/minimal-backoffice-iam-architecture.md` to `docs/architecture-minimal-backoffice-iam.md` and updated documentation links.
- Renamed `docs/administrator-authentication-policy.md` to `docs/security-administrator-authentication-policy.md` and updated documentation links.
- Renamed `docs/bff-sessions-and-token-handling.md` to `docs/security-bff-sessions-and-token-handling.md` and updated documentation links.
- Renamed `docs/initial-permission-model.md` to `docs/requirements-initial-permission-model.md` and updated documentation links.
- Renamed `docs/member-lifecycle.md` to `docs/requirements-member-lifecycle.md` and updated documentation links.
- Renamed `docs/open-questions.md` to `docs/requirements-question-register.md` and updated documentation links.
- Renamed `docs/study-notes.md` to `docs/requirements-study-inputs.md` and updated documentation links.
- Renamed `docs/threat-model.md` to `docs/security-threat-model.md` and updated documentation links.
- Updated the roadmap in `README.md` to name the study phases explicitly.
- Added root `ABSTRACT.md` and `CHANGELOG.md` to the README documentation links.
- Updated README, abstract, requirements baseline, requirements question register, and documentation index links to surface the current consolidated Phase 2 artifacts.
- Reduced duplicated requirement and documentation detail in `README.md`; `docs/requirements-baseline.md` remains the detailed ID-based requirements source.
- Split architecture reasoning out of `docs/requirements-study-inputs.md` into dedicated architecture decision analysis notes, leaving study inputs as a concise historical index.
- Updated the abstract status and key links to reflect the current consolidated Phase 2 artifacts.
- Updated top-level study documents so Phase 1 foundation pages clearly read as Phase 2 requirements inputs.
- Refined the evaluation framework with requirement-ID traceability, mandatory evidence capture in the evaluation template, stronger BFF/CSRF criteria, and a new OAuth client safety gate.
- Clarified in `AGENTS.md` that project history must be kept in root `CHANGELOG.md`, with `README.md` reserved for the final-review project brief.
- Removed project-facing wiki-index links and clarified in `AGENTS.md` that the conceptual wiki index is agent-facing only.
- Added the conceptual wiki index link back to the root README documentation list by explicit request.
- Renamed `docs/phase-1-working-notes.md` to `docs/requirements-study-inputs.md` and updated documentation links to use the phase-neutral study-notes artifact.
- Removed the page-level references section from the conceptual wiki index; baseline references remain in `AGENTS.md`.

### Removed

- Removed stale `docs/phase-2-working-notes.md`; Phase 2 working documentation now lives in `docs/requirements-baseline.md` and `docs/requirements-question-register.md`.
- Removed `docs/candidate-shortlist.md`; candidate evaluation remains governed by `docs/evaluation-framework.md` until a new candidate inventory is explicitly requested.
