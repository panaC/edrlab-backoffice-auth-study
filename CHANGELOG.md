# Changelog

All notable project-level documentation changes should be recorded here.

This repository is a study repository, not a released software package. Changelog entries should focus on meaningful changes to project phase, scope, requirements, documentation structure, evaluation artifacts, and Proof-of-Concept planning.

## 2026-06-26

### Changed

- Moved the repository's current operating phase from `Phase 4 - Proof of Concept` to `Phase 5 - Review and Decision` after explicit user request.
- Updated `AGENTS.md`, `ABSTRACT.md`, `README.md`, and `docs/README.md` so phase status, metadata examples, active-direction references, and review-facing open-study wording reflect the Phase 5 review state.
- Added ADR 0004 to record the accepted Phase 5 decision adopting the Keycloak IAM Control Plane API architecture for constrained MVP design without authorizing Phase 6 implementation.
- Updated the Phase 5 review note, documentation map, decision index, and abstract to reference the accepted MVP architecture decision and remaining MVP authorization gates.
- Added `docs/evaluation/mvp-scope.md` to define the review-state MVP boundary for account operations, lifecycle, service-access roles, protected services, audit, privileged onboarding, out-of-scope items, and remaining Phase 6 inputs.
- Updated the Phase 5 review note and documentation map to link the new MVP scope gate artifact.
- Updated the MVP scope and Phase 5 review note with the user-selected first protected service: a synthetic access-check service whose only purpose is to verify the current user's access and return `OK` or `KO`.
- Refined the MVP scope with the concrete `access-check-demo-service` service, `access-check-demo:consult` role, `OK`/`KO` HTTP response contract, required account fields, build-initialization first-super-admin bootstrap, simplest audit consultation, and confirmed MVP exclusions.
- Added `docs/architecture/iam-control-plane-api-contract.md` to accept the MVP IAM Control Plane API contract: REST endpoints under `/iam`, actors, Keycloak/OIDC user authentication, service-to-service client credentials, operation authorization, RFC 9457 Problem Details errors, idempotence, correlation IDs, and audit.
- Updated the MVP scope to make the `access-check-demo-service` `OK`/`KO` response JSON everywhere, and linked the accepted API contract from the Phase 5 review note and documentation map.
- Added `docs/architecture/authorization-check-behavior.md` to accept the MVP runtime behavior for `authorization/check`: `500 ms` protected-service timeout per attempt, one retry with jitter, `1000 ms` IAM-to-Keycloak timeout, one transient dependency retry, no positive cache, optional `5 second` deny cache, no indeterminate cache, fail-closed `KO`, next-check access stop with `<= 1 second` measurable bound outside outage, durable audit for deny/indeterminate outcomes, and required metrics.
- Updated the IAM Control Plane API contract, Phase 5 review note, and documentation map to link the accepted authorization-check runtime behavior.
- Added `docs/architecture/audit-storage.md` to accept the MVP audit storage policy: local durable file-backed append-only records, one JSON event object per line, indefinite retention, super-admin API read, no initial export, correlation IDs, backup inclusion, confidentiality controls, and explicit operational limits.
- Updated the MVP scope, IAM Control Plane API contract, authorization-check behavior note, Phase 5 review note, and documentation map to link the accepted audit storage policy.
- Added `docs/architecture/keycloak-iam-schema-policy.md` to accept the MVP Keycloak IAM schema policy: managed User Profile attributes, unmanaged attributes disabled, account-type client roles, protected-service client roles, role lifecycle metadata, IAM Control Plane API-only mutation, strict invariant checks, dry-run migration, and token-claim boundaries.
- Updated the MVP scope, IAM Control Plane API contract, authorization-check behavior note, Phase 5 review note, and documentation map to link the accepted Keycloak IAM schema policy.
- Added `docs/evaluation/security-test-plan.md` to accept the MVP security regression test plan covering frontend-only bypass rejection, raw token-claim rejection, issuer/audience/token validation, immutable subject link, fail-closed dependency behavior, drift denial, and audit evidence.
- Updated the Phase 5 review note and documentation map to link the accepted MVP security test plan and close the security regression test gate for design.
- Accepted the MVP scope and added ADR 0005 to explicitly authorize `Phase 6 - Production MVP` implementation for the accepted Keycloak IAM Control Plane API scope.
- Recorded the final Phase 5 closure decisions: formal direct Keycloak admin governance is post-MVP, `super-admin` owns Keycloak operations for the MVP, OTP safeguards follow Keycloak documented built-ins, and first-super-admin bootstrap remains simple, idempotent, outside the public API, and audited.
- Updated `AGENTS.md`, `ABSTRACT.md`, `README.md`, the documentation map, decision index, MVP scope, and Phase 5 review note so the repository status and guardrails reflect the Phase 6 authorization.

## 2026-06-25

### Added

- Added `docs/poc/keycloak-wp010-result.md` to record the selected Keycloak IAM mapping for the first IAM Control Plane API-backed validation slice: account type client roles, lifecycle user attributes, service-access client roles, IAM Control Plane API-mediated protected-service authorization, and local business audit plus Keycloak event evidence.
- Added `docs/poc/keycloak-wp011-result.md` to define the IAM Control Plane API anti-bypass path, operation contract, drift handling, runtime evidence expectations, and residual risks for Keycloak-backed account administration.
- Added `docs/poc/keycloak-wp012-result.md` to define the Keycloak-backed lifecycle and onboarding activation scenarios, unsafe onboarding denials, protected-service access expectations, and runtime evidence requirements.
- Added `docs/poc/keycloak-wp013-result.md` to select ACR/LoA step-up as the first privileged-authentication evidence path for `admin` and `super-admin` onboarding and to keep privileged activation blocked until runtime evidence proves the path.
- Added `docs/poc/keycloak-wp014-result.md` to define the service-access-role model, IAM Control Plane API `authorization/check` contract, fail-closed decision logic, access-stop scenarios, and runtime evidence expectations for protected-service authorization.
- Added `docs/poc/keycloak-wp015-result.md` to define direct Keycloak Admin Console drift classes, shortcut rejection, drift detection evidence, event-gap handling, and residual risks for the IAM Control Plane API direction.
- Added `docs/poc/keycloak-wp016-result.md` to define the audit boundary, local EDRLab audit event contract, Keycloak evidence role, operational review items, and runtime evidence expectations.
- Added `docs/poc/keycloak-wp017-result.md` to consolidate `WP-010` through `WP-016` into Phase 5 review inputs, runtime evidence gaps, residual risks, review questions, and decision options.
- Added `poc/keycloak/scripts/verify-iam-control-plane-runtime.sh` as the PoC-only Linux runtime bundle for `WP-011` through `WP-016`, covering controlled Keycloak Admin REST mutations, local IAM Control Plane API fixture decisions, protected-service checks, direct-admin drift handling, Keycloak admin-event collection, and local EDRLab audit examples.
- Added `docs/poc/keycloak-wp011-016-runtime-result.md` to record the Docker execution of the `WP-011` through `WP-016` runtime bundle, the decision matrix, generated evidence path, Keycloak user-profile finding, and remaining `WP-013` blocker.
- Added `poc/keycloak/scripts/verify-iam-control-plane-wp013.sh` and its containerized runner for the dedicated `WP-013` ACR/LoA step-up validation using only Docker runtime execution.
- Added `docs/decisions/0003-accept-otp-for-privileged-authentication.md` to record the accepted decision that OTP MFA is sufficient privileged-authentication evidence for the current Keycloak IAM direction, with WebAuthn/passkeys deferred as future hardening.
- Added `docs/evaluation/phase-5-review-note.md` to summarize what the Keycloak IAM Control Plane API PoC validates, remaining production risks, decisions to take, and minimum MVP authorization gates.

### Changed

- Updated `docs/poc/keycloak-iam-bff-validation-plan.md` and `docs/README.md` to link the completed `WP-010` mapping result, documentation-first `WP-011` anti-bypass result, documentation-first `WP-012` lifecycle/onboarding result, documentation-first `WP-013` privileged-authentication evidence result, and documentation-first `WP-014` service-access authorization result.
- Replaced the active validation terminology from `BFF/Admin API` to `EDRLab IAM Control Plane API` in ADR 0002, the active architecture scope, the active validation plan, and `WP-010` through `WP-014`; existing filenames keep `bff` until an explicit rename is requested.
- Extended `docs/poc/keycloak-wp014-result.md` with the IAM Control Plane API `GET /me/services` effective-service listing contract, scenarios, and runtime evidence expectations, while keeping `authorization/check` as the protected-service enforcement decision.
- Updated `docs/poc/keycloak-iam-bff-validation-plan.md` and `docs/README.md` to link the documentation-first `WP-015` drift and shortcut-rejection result, the documentation-first `WP-016` audit and operations result, and the documentation-first `WP-017` consolidation result.
- Updated `poc/keycloak/README.md`, `docs/poc/keycloak-iam-bff-validation-plan.md`, and `docs/poc/keycloak-wp017-result.md` to document the prepared `WP-011` through `WP-016` runtime bundle and to keep execution evidence distinct from script preparation.
- Tightened the prepared `WP-011` through `WP-016` runtime bundle with an explicit IAM Control Plane API decision matrix, stricter local audit actor fields, resource-specific Keycloak admin-event correlation, and a visible `blocked` marker for unresolved privileged-authentication evidence.
- Executed the `WP-011` through `WP-016` runtime bundle against the Docker Keycloak PoC, fixed the runtime script to configure Keycloak User Profile unmanaged attributes as `ADMIN_EDIT` for PoC IAM attributes, preserved user profile fields during attribute updates, and recorded the final `pass_with_blocked_privileged_evidence` result.
- Executed the dedicated `WP-013` Docker runner, configured PoC-only Keycloak ACR/LoA step-up with OTP, validated normal-login denial, privileged admin and super-admin activation fixture allows, mismatched-subject denial, and updated the `WP-013` result note with the passing evidence path and remaining production gaps.
- Updated `WP-013`, `WP-017`, the active architecture scope, the active validation plan, and documentation indexes to reflect the user decision that OTP MFA is acceptable for privileged admin authentication in the current direction.

## 2026-06-23

### Added

- Added `poc/keycloak/scripts/verify-onboarding.sh` for `WP-003`, covering scripted Authorization Code evidence for verified and unverified Keycloak users plus PoC-only local onboarding decisions for safe activation, no invitation, duplicate invitation, unverified email, and pre-linked subject.
- Added `docs/poc/keycloak-wp003-result.md` to document the WP-003 runtime validation, generated evidence path, first-attempt script correction, and remaining limitations.
- Added `poc/keycloak/scripts/verify-privileged-auth.sh` for `WP-004`, covering scripted admin and super-admin Authorization Code evidence, Keycloak `amr`/flow/event inspection, and PoC-only local privileged-activation blocker decisions.
- Added `docs/poc/keycloak-wp004-result.md` to document the WP-004 runtime validation, generated evidence path, current privileged-authentication evidence blocker, and remaining limitations.
- Added `poc/keycloak/scripts/verify-claim-override.sh` for `WP-005`, covering scripted misleading Keycloak role, group, and hardcoded-claim evidence plus PoC-only local claim-override rejection decisions.
- Added `docs/poc/keycloak-wp005-result.md` as a draft status note for the WP-005 claim-override rejection scenario, including expected evidence and the current Windows host execution limitation.
- Added `poc/keycloak/scripts/verify-authorization-access-stop.sh` for `WP-006`, covering scripted member authentication evidence plus PoC-only local `authorization/check`, fail-closed, no-positive-cache, and access-stop decisions.
- Added `docs/poc/keycloak-wp006-result.md` as a review-state result note for the WP-006 authorization and access-stop scenario.
- Added `poc/keycloak/scripts/verify-audit-correlation.sh` for `WP-007`, covering scripted member authentication evidence, supplemental Keycloak user/admin event evidence, PoC-only local audit examples, correlation checks, and expected audit-gap records.
- Added `docs/poc/keycloak-wp007-result.md` as a review-state result note for the WP-007 audit-correlation scenario.
- Added `docs/poc/keycloak-wp008-result.md` as a documentation-first review note for the Keycloak Web Admin boundary and self-hosted operations checklist.
- Added `docs/poc/keycloak-wp009-result.md` as the Phase 4 evidence consolidation note for the Keycloak PoC result matrix, blockers, accepted limitations, residual risks, and Phase 5 review questions.
- Added `docs/decisions/0002-validate-keycloak-iam-bff.md` to record the user-selected pivot toward Keycloak as the IAM source with an EDRLab IAM Control Plane API.
- Added `docs/architecture/keycloak-iam-bff-scope.md` to describe the new Keycloak-IAM-backed administration boundary, state ownership questions, protected-service authorization options, and audit boundary.
- Added `docs/poc/keycloak-iam-bff-validation-plan.md` to define the next Phase 4 validation work packages for the Keycloak IAM plus EDRLab IAM Control Plane API direction.

### Changed

- Updated `poc/keycloak/README.md` with `WP-003` Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-003` result note in the project documentation map.
- Updated `poc/keycloak/README.md` with `WP-004` Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-004` result note in the project documentation map.
- Expanded the WP-004 result note with a reviewer-facing conclusion: Keycloak remains the validation candidate, but privileged `admin` and `super-admin` onboarding stays blocked until explicit privileged-authentication evidence is configured and verified.
- Corrected the WP-003 local onboarding `jq` evaluator after the first runtime attempt exposed invalid field access and function-argument syntax.
- Tightened WP-003 evidence by filtering Keycloak events to the current run window, asserting expected authentication/token events for both subjects, and avoiding misleading audit `target_id` values for no-match or duplicate-match denials.
- Expanded the WP-003 result note with a reviewer-oriented explanation of the test purpose, real versus simulated runtime parts, script flow, scenario matrix, success criteria, and evidence map.
- Updated `poc/keycloak/README.md` with `WP-005` Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-005` status note in the project documentation map.
- Tightened the prepared WP-005 validation by verifying access-token signature and core claims before using access-token role evidence, and documented the reset expectation after the claim-override scenario mutates the throwaway realm.
- Executed the WP-005 runtime validation in a temporary Linux container against the Docker Keycloak PoC runtime, recorded the passing evidence path, and promoted the WP-005 result note to review state.
- Documented the Keycloak role/group boundary in the integration scope: Keycloak roles, groups, and claims may support technical administration or non-authoritative evidence, but local EDRLab account state remains authoritative for business authorization.
- Updated `poc/keycloak/README.md` with `WP-006` Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-006` status note in the project documentation map.
- Executed the WP-006 runtime validation against the Docker Keycloak PoC runtime, recorded the passing evidence path, and promoted the WP-006 result note to review state.
- Tightened WP-006 Keycloak event evidence so token and authorization-code identifiers are recorded only as presence flags.
- Updated `poc/keycloak/README.md` with `WP-007` Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-007` result note in the project documentation map.
- Executed the WP-007 runtime validation against the Docker Keycloak PoC runtime, recorded the passing evidence path, and documented expected gaps where Keycloak events do not prove local EDRLab authorization, audit-read, persistence, or retention behavior.
- Updated `docs/README.md` to include the new `WP-008` and `WP-009` review notes in the project documentation map.
- Revised `FR-038` from a blanket identity-provider claim override rejection into the new anti-bypass requirement for controlled server-side IAM administration and authorization paths.
- Marked the original Keycloak local-access-control validation decision, solution-choice note, integration-scope note, and validation plan as superseded by the Keycloak IAM Control Plane API validation direction while preserving their evidence history.
- Marked the earlier architecture-options, technical-solutions, and Keycloak setup-runbook artifacts as superseded for future validation because they belong to the local-access-control-authority interpretation.
- Updated `docs/README.md` and `docs/decisions/README.md` to list the new Keycloak IAM Control Plane API direction, validation plan, and superseded prior boundary.

## 2026-06-07

### Added

- Added `poc/keycloak/scripts/verify-login-sso.sh` for `WP-002`, covering scripted Authorization Code login, PKCE token exchange, ID token validation, UserInfo subject matching, local `iss` + `sub` account resolution, local session decision, prompt-none SSO validation, and logout validation.
- Added `docs/poc/keycloak-wp002-result.md` as the review-state result note for the login and SSO boundary scenario, recording the successful runtime validation, generated evidence path, and remaining limitations.

### Changed

- Updated `poc/keycloak/README.md` with `WP-002` prerequisites, Linux run commands, expected outputs, evidence files, and non-production limitations.
- Updated `docs/README.md` to include the new `WP-002` result note in the project documentation map.
- Hardened the WP-002 PKCE helper so URL-safe random values strip carriage returns before being used as `code_verifier` values.

## 2026-06-05

### Added

- Added `docs/evaluation/solution-choice.md` as the Phase 3 working entry point for shortlist comparison, decision criteria, open evidence, and candidate solution choice readiness.
- Added `docs/decisions/0001-choose-keycloak-for-validation.md` to record the accepted Phase 3 solution choice.
- Added `docs/poc/keycloak-validation-plan.md` to define the Keycloak validation objectives, scenarios, success criteria, non-production limits, and Phase 4 readiness gate.
- Added `docs/architecture/keycloak-integration-scope.md` to document the EDRLab development block, Keycloak configuration block, SSO session flow, and user-session-management boundary for the accepted Keycloak candidate.
- Added `poc/keycloak/` as the executable Linux/Docker Keycloak PoC runtime for `WP-001`, including Compose runtime, environment template, start/bootstrap/verify/evidence/stop/reset scripts, and local runtime documentation.
- Added `docs/poc/keycloak-wp001-result.md` to record the Docker-verified `WP-001` result, generated evidence location, and limitations.
- Restored `jq` as the JSON tooling dependency for the Keycloak PoC scripts after user direction, keeping JSON construction, parsing, validation, and evidence formatting explicit.
- Retested the scripted Keycloak `WP-001` Docker PoC with `jq`, refreshed the local generated evidence, and updated the result note with the latest evidence path.

### Changed

- Moved the repository's current operating phase from `Phase 2 - Requirements and Risk Framing` to `Phase 3 - Solution Choice` after explicit user request.
- Updated `AGENTS.md`, `ABSTRACT.md`, `README.md`, and `docs/README.md` so phase status, metadata examples, and documentation routing reflect the Phase 3 start.
- Started the Phase 3 comparison pass in `docs/evaluation/solution-choice.md`, adding source-backed evidence snapshots, criterion-by-criterion comparison, and the next solution-choice work items.
- Accepted self-hosted Keycloak with a local EDRLab access-control service as the Phase 3 candidate solution to validate, while preserving the explicit boundary that this is not production approval or PoC implementation.
- Documented the rationale for keeping access-control local instead of implementing the whole model inside the Keycloak realm, including requirement fit, stale-access risk, audit ownership, extension ownership, and reversibility.
- Documented the Keycloak Web Admin boundary: the Admin Console may be used for Keycloak technical administration and validation support, but not as the EDRLab business Access Control Manager for local accounts, lifecycle, service-access roles, protected-service decisions, or project audit truth.
- Added a proposed Phase 4 entry set to the Keycloak validation plan, covering the first protected-service contract, browser/session assumption, access-stop assumption, privileged-authentication evidence, audit correlation, Keycloak configuration scope, PoC data set, and minimal runtime validation slices.
- Added proposed Phase 4 work packages and a reusable evidence-record template to the Keycloak validation plan so the future non-production PoC can produce reviewable results without expanding into production implementation.
- Completed Phase 3 and moved the repository's current operating phase to `Phase 4 - Proof of Concept` after explicit user request.
- Marked the Keycloak validation plan as the accepted Phase 4 entry plan and recorded the Phase 3 closure checklist in the solution-choice artifact.
- Closed `OQ-KIS-001` / `OQ-KV-008` for Phase 4 by selecting a BFF/server-side local application session as the first browser pattern to validate.
- Closed `OQ-KIS-002` / `OQ-KV-001` for Phase 4 by selecting immediate next-check denial with no positive authorization cache as the access-stop validation target.
- Closed the remaining `Open Questions Before Runtime PoC` entries by selecting local `authorization/check`, a Keycloak `amr`-first privileged-authentication evidence path, a minimum audit correlation schema, a self-hosted operations review list, a documentation/runtime validation split, and a Keycloak Web Admin allow/deny boundary.
- Closed `OQ-KIS-003` and `OQ-KIS-004` for Phase 4 by documenting the privileged-authentication evidence approach and deferring EDRLab UI exposure of Keycloak SSO-session administration actions.
- Compressed and finalized `docs/poc/keycloak-validation-plan.md` around accepted validation decisions, runtime scope, work packages, evidence records, and readiness gates.
- Aligned the Phase 3 closure summary with the finalized Keycloak validation plan sections.
- Added `docs/poc/keycloak-setup-runbook.md` as the `WP-001` execution runbook for the first non-production Keycloak setup pass.
- Updated `AGENTS.md` so project runbooks and PoC instructions target Linux by default and every runtime PoC includes a Docker-based runtime definition; aligned the Keycloak setup runbook with that rule.
- Updated `AGENTS.md` and the Keycloak setup runbook so every runtime PoC must be fully scripted, documented, reproducible from a clean Linux checkout, and explicit about any unscripted blocker or residual manual step.
- Simplified the project roadmap from seven study phases plus optional MVP to five study phases plus `Phase 6 - Production MVP`, preserving conceptual foundation and requirements/risk framing before solution choice, Proof of Concept, and review/decision.
- Updated `PROJECT-GOVERNANCE.md`, `README.md`, `AGENTS.md`, `docs/README.md`, and `ABSTRACT.md` to align phase names, boundaries, and documentation routing with the simplified governance model.
- Replaced the optional non-production MVP phase with `Phase 6 - Production MVP`, keeping the explicit rule that implementation starts only when the user moves the project into that phase.

## 2026-05-08

### Added

- Started the final review pass for the consolidated `FR-*` feature requirements and recorded the review slices in `docs/requirements/feature-requirements-review.md`.
- Added `FR-036` for resolving an authenticated identity to exactly one linked backoffice account before evaluating backoffice authorization.
- Added `FR-037` to state that a successful identity-provider authentication result must not automatically create, activate, or authorize a backoffice account.
- Added `FR-038` for prevention of identity-provider claims, groups, or roles overriding the backoffice authorization model.
- Added `FR-039` to require authorized and audited management of the authenticated-subject link on backoffice accounts.
- Added `FR-040` through `FR-044` for the validated account-onboarding feature: invited account creation with `email`, `organization`, and `name`; pre-activation member service-access-role assignment without access; IdP-managed invitation and authentication; safe automatic onboarding activation with initial subject linking; and fail-closed handling when matching is unsafe.
- Added threat-model review focus, requirement refinement candidates, and expanded threat scenarios for onboarding, identity-provider claim override, privileged authentication, token/session replay, audit integrity, unsafe failure modes, and operational artifacts.
- Added `docs/evaluation/technical-solutions.md` with three concrete technical solution candidates: Auth0 managed login plus local access-control, self-hosted Keycloak plus local access-control, and a Spring-based local IAM control plane.

### Changed

- Promoted `docs/risks/threat-model.md` from draft to review state and realigned it with the consolidated `FR-*` feature requirements.
- Reworked `docs/architecture/options.md` into a Phase 2 review-state architecture option framing derived from the consolidated feature requirements and threat model, with option comparison, threat-fit review, PoC/evaluation implications, and open architecture questions.
- Updated the responsibility model so active `super-admin` accounts automatically receive access to every protected backend service covered by service-access roles, like active `admin` accounts, while service-access role assignments remain limited to `member` accounts.
- Simplified the responsibility model so `super-admin` is a high-level administration superset of `admin`, inheriting admin capabilities and adding high-level administration capabilities.
- Clarified `FR-003` and `FR-004` so `FR-003` describes admin capabilities and `FR-004` gives super-admins those capabilities by inheritance plus high-level administration capabilities.
- Split the identity-provider clarification out of `FR-010`, keeping `FR-010` focused on stable authenticated-subject linkage.
- Reworked `FR-036` from an identity-provider contract placeholder into concrete authenticated-identity resolution behavior.
- Merged the fail-closed identity-resolution behavior from an earlier draft into `FR-036` to avoid duplicate IdP requirements.
- Completed the final review pass for the consolidated feature list, which at that point contained 39 active requirements from `FR-001` through `FR-039`.
- Strengthened `FR-016`, `FR-027`, and `FR-032` so service-access role disablement or archival has a clear access-stop effect, audit coverage includes role lifecycle and authenticated-subject link changes, and only active service-access roles can be used for assignments or protected-service access decisions.
- Recorded user validation of the seven final-review slices covering all consolidated feature requirements and out-of-scope boundaries.
- Updated `FR-039` so authenticated-subject links are created only through automatic onboarding activation, are immutable after creation, and cannot be manually created, changed, removed, or rebound by admins, super-admins, or other processes outside the onboarding activation flow.
- Extended `FR-027` audit coverage to include account activation and failed automatic onboarding activation.
- Clarified `FR-012`, `FR-039`, `FR-043`, and `FR-044` so automatic account onboarding is coupled to backoffice verification of one invited account with no existing authenticated-subject link and a verified matching IdP email, not to the user's first IdP login.
- Generalized onboarding from `member` accounts to all account types, with production `admin` and `super-admin` activation requiring evidence that the privileged-authentication requirement was satisfied.
- Clarified `FR-037` so identity-provider authentication alone does not create, activate, or authorize a backoffice account, while preserving the controlled onboarding activation flow in `FR-043`.
- Clarified `FR-025` so recovery and login reset are own-account responsibilities for members, admins, and super-admins, with no cross-account reset capability in the initial feature requirements.
- Clarified `FR-027` so authenticated-subject link audit coverage records link creation and rejected or attempted link mutation, without implying that post-creation link changes are normal allowed operations.

## 2026-05-07

### Added

- Added the top-level `README.md` core features list as the project reference for account management, identity-provider authentication, account-type separation, service-access roles, protected-service access control, and sensitive-action auditability.
- Added `docs/requirements/feature-requirements-review.md` as the live consolidation trail for replacing the separate requirements baseline with one unique root `FEATURE-REQUIREMENTS.md` list.
- Added `docs/requirements/feature-scope-review.md` to record step-by-step validation of each immutable `FS-*` requirement, starting with the validated `FS-001` scope.
- Added `docs/requirements/baseline-review.md` to record step-by-step validation of each `RB-*` requirement against the validated `FS-*` interpretations.
- Added root `FEATURE-REQUIREMENTS.md` as the blank-slate iterative working base for the final-solution feature requirements of the access-control capability.
- Added the validated `Goal` section to root `FEATURE-REQUIREMENTS.md`.
- Added `FR-001` to root `FEATURE-REQUIREMENTS.md` for fixed immutable account types.
- Added `FR-002` to root `FEATURE-REQUIREMENTS.md` for service-access role independence from account types.
- Added `FR-003` to root `FEATURE-REQUIREMENTS.md` for automatic admin access to all service-access-role-covered protected services and admin assignment/removal of member service-access roles.
- Added `FR-004` to root `FEATURE-REQUIREMENTS.md` for super-admin service-access-role catalog management and member role assignment without super-admin protected-service access or admin role assignment.
- Added `FR-005` to root `FEATURE-REQUIREMENTS.md` for member protected-service access only through assigned service-access roles.
- Added `FR-006` to root `FEATURE-REQUIREMENTS.md` for backoffice-only user scope and explicit exclusion of public or consumer identity flows.
- Added `FR-007` to root `FEATURE-REQUIREMENTS.md` for administrative-only backoffice account creation with no public or self-service registration.
- Added `FR-008` to root `FEATURE-REQUIREMENTS.md` for account creation authority by account type and first-super-admin bootstrap separation.
- Added `FR-009` to root `FEATURE-REQUIREMENTS.md` for stable internal account identifiers separate from mutable profile attributes.
- Added `FR-010` to root `FEATURE-REQUIREMENTS.md` for linking backoffice accounts to stable authenticated subjects while keeping credentials, MFA, sessions, and IdP recovery outside the access-control capability.
- Added `FR-011` to root `FEATURE-REQUIREMENTS.md` for required backoffice account lifecycle states.
- Added `FR-012` to root `FEATURE-REQUIREMENTS.md` for invited account activation after first authentication or onboarding completion.
- Added `FR-013` to root `FEATURE-REQUIREMENTS.md` for disable, restore, and archive lifecycle transitions.
- Added `FR-014` to root `FEATURE-REQUIREMENTS.md` for retaining backoffice account records instead of hard-deleting them in the initial policy.
- Added `FR-015` to root `FEATURE-REQUIREMENTS.md` for requiring active lifecycle state before protected-service access.
- Added `FR-016` to root `FEATURE-REQUIREMENTS.md` for documenting and evaluating already-issued access stop behavior after lifecycle or role changes.
- Added `FR-017` to root `FEATURE-REQUIREMENTS.md` for admin management of member accounts and exclusion of admin or super-admin account management.
- Added `FR-018` to root `FEATURE-REQUIREMENTS.md` for super-admin management of admin and member accounts.
- Added `FR-019` to root `FEATURE-REQUIREMENTS.md` for member read-only self-profile access and member self-service exclusions.
- Added `FR-020` to root `FEATURE-REQUIREMENTS.md` for server-side protected-service authorization based on active state and account type or assigned service-access role rules.
- Added `FR-021` to root `FEATURE-REQUIREMENTS.md` for fail-closed protected-service access decisions.
- Added `FR-022` to root `FEATURE-REQUIREMENTS.md` for explicit service-access-role coverage of protected backend service access.
- Added `FR-023` to root `FEATURE-REQUIREMENTS.md` for consultation-style minimal member service-access and justified future permission refinement.
- Added `FR-024` to root `FEATURE-REQUIREMENTS.md` for a controlled administration capability without choosing its technical form.
- Added `FR-025` to root `FEATURE-REQUIREMENTS.md` for own-account recovery and login reset boundaries.
- Added `FR-026` to root `FEATURE-REQUIREMENTS.md` for preventing privilege escalation and audit bypass paths.
- Added `FR-027` to root `FEATURE-REQUIREMENTS.md` for minimum audit event coverage.
- Added `FR-028` to root `FEATURE-REQUIREMENTS.md` for super-admin audit consultation and audit logging of reads or exports.
- Added `FR-029` to root `FEATURE-REQUIREMENTS.md` for the target production-grade internal access-control posture and documented hardening path for shortcuts.
- Added `FR-030` to root `FEATURE-REQUIREMENTS.md` for internal-team understandability, operability, and justified complexity.
- Added a coverage review to `docs/requirements/feature-requirements-review.md` mapping `README.md` `FS-*` and baseline `RB-*` material to the consolidated `FR-*` list and recording deletion blockers for the old baseline.
- Added `FR-031` to root `FEATURE-REQUIREMENTS.md` to forbid returning an account to `invited` after it has left that state.
- Added `FR-032` to root `FEATURE-REQUIREMENTS.md` for service-access-role catalog creation, listing, update, disablement, archival, and no hard deletion in the initial policy.
- Added `FR-033` to root `FEATURE-REQUIREMENTS.md` for server-side authorization of admin and super-admin operations.
- Added `FR-034` to root `FEATURE-REQUIREMENTS.md` for production MFA or phishing-resistant passwordless authentication on admin and super-admin accounts, with exact authenticator choices deferred to security and architecture evaluation.
- Added `FR-035` to root `FEATURE-REQUIREMENTS.md` for append-only, indefinitely retained audit records in the initial policy.
- Added the root `FEATURE-REQUIREMENTS.md` out-of-scope section for public identity exclusions, non-decisions, implementation boundaries, and break-glass deferral.
- Recorded the out-of-scope consolidation decision in `docs/requirements/feature-requirements-review.md` and closed `OQ-010`.

### Removed

- Removed `docs/requirements/baseline.md` after consolidating useful `FS-*` and `RB-*` coverage into root `FEATURE-REQUIREMENTS.md` and preserving the review trail in `docs/requirements/feature-requirements-review.md`.

### Changed

- Removed the temporary stabilized `FR-*` feature-requirement table from `README.md`.
- Rewrote the `README.md` project goal for clearer scope, access-control purpose, and protected-service wording.
- Updated backoffice-user wording across project documents to remove the extra qualifier.
- Replaced the temporary `README.md` project-purpose note with a concise description aligned with the study roadmap.
- Added a compact Mermaid flow under the `README.md` core features list to show user and admin entry paths through authentication, identity provider, access control, protected services, and account management.
- Removed the dedicated Phase 2 threat-modeling baseline requirement and kept threat modeling documented as a risk artifact.
- Expanded the Phase 2 threat model with explicit external dependencies, entry points, and exit points to improve OWASP threat-modeling alignment.
- Validated the Phase 2 interpretation of `FS-002`: member creation or invitation must be admin-initiated before activation, with no public or self-service member creation.
- Validated the Phase 2 interpretation of `FS-003`: stable member identifiers are the canonical reference for lifecycle, roles, audit, and access decisions.
- Validated the Phase 2 interpretation of `FS-004`: lifecycle states and member retention are baseline constraints, with `archived` terminal in the baseline.
- Validated the Phase 2 interpretation of `FS-005`: non-active members cannot obtain new access, and already-issued access removal remains an explicit revocation-evaluation topic.
- Added the related baseline requirement list to the `FS-005` scope-review note.
- Updated `FS-006` in `README.md` to clarify that administrators remove role-based service access for members rather than generic already-issued access.
- Aligned the Phase 2 requirements baseline and threat-model wording with the clarified `FS-006` scope.
- Validated the Phase 2 interpretation of `FS-006`: administrators manage member operations and role-based service-access removal within lifecycle policy and audit requirements.
- Updated `FS-007` in `README.md` to separate admin role listing, assignment, and removal from super-admin role creation.
- Aligned the threat-model role-management entry point with the clarified `FS-007` responsibility split.
- Corrected the requirements traceability matrix so `FS-007` includes `RB-016` for already-issued access behavior after role-access removal.
- Validated the Phase 2 interpretation of `FS-007`: super-admins create roles, while admins list, assign, and remove roles from members.
- Validated the Phase 2 interpretation of `FS-008`: baseline authorization is simple role-based service access, with finer permissions deferred until justified by real service needs.
- Validated the Phase 2 interpretation of `FS-009`: the minimal member role is consultation/read-only, with stronger or finer permissions deferred until a real service need is reviewed.
- Validated the Phase 2 interpretation of `FS-010`: the system needs a controlled, auditable administration capability without selecting its technical form.
- Validated the Phase 2 interpretation of `FS-011`: protected backend services must authorize server-side from active member state and role-based service access, failing closed when uncertain.
- Validated the Phase 2 interpretation of `FS-012`: member self-service is limited to viewing one's own profile, while profile and service-access changes remain admin-controlled.
- Updated `FS-013` and the actor responsibilities in `README.md` to separate member recovery/login reset, administrator recovery/login reset, and super-admin audit/break-glass responsibility.
- Aligned the Phase 2 requirements baseline and threat model with the clarified `FS-013` responsibility split.
- Clarified `FS-013` further so member and administrator recovery/login reset are own-account responsibilities only, and administrators cannot recover or reset members or other administrators.
- Validated the Phase 2 interpretation of `FS-013`: recovery/login reset is own-account only for members and administrators, with audit and any future break-glass under super-admin responsibility.
- Validated the Phase 2 interpretation of `FS-014`: production-grade internal access control is the target, while simpler authentication is only transitional or non-production and must be risk-assessed.
- Updated `FS-015` in `README.md` to use `login reset` instead of `authenticator reset`, aligned with the clarified `FS-013` vocabulary.
- Validated the Phase 2 interpretation of `FS-015`: audit coverage includes lifecycle, role/access changes, protected-service denials, audit reads/exports, and recovery/login reset actions.
- Validated the Phase 2 interpretation of `FS-016`: audit access is super-admin-only and audit reads or exports must themselves be logged.
- Validated the Phase 2 interpretation of `FS-017`: simplicity and operability are baseline requirements, and added complexity must be justified by concrete needs.
- Completed the step-by-step Phase 2 scope review for `FS-001` through `FS-017`.
- Validated `RB-001` as correctly scoped to `FS-001`: the baseline remains limited to backoffice users and excludes public signup, public customer accounts, social login, and consumer IAM flows.
- Refined and validated `RB-002` so it covers administrator-created member records and administrative member management without conflicting with member own-profile read or own-account recovery/login reset.
- Validated `RB-003` as correctly scoped to `FS-017` and the company scale constraint: the solution must remain understandable for fewer than 1,000 internal users and added operational complexity must be justified.
- Refined and validated `RB-004` so it models the three feature-specified Phase 2 actors and prevents adding or merging actor responsibilities without an explicit scope change.
- Retired `RB-005` from active baseline requirements because it mixed administrative member management, role assignment, service access, profile-data changes, and logging into one broad requirement.
- Reframed the immutable feature specification in `README.md` to distinguish account types (`super-admin`, `admin`, `member`) from service-access roles, and clarified super-admin, admin, and member responsibilities accordingly.
- Clarified in `README.md` that an account type is fixed at account creation and cannot be changed later; a `member` account must never become an `admin` account.
- Added the initial identity-provider, OAuth2/OIDC, backoffice-account, account-type, service-access-role, and authorization-boundary definitions to root `FEATURE-REQUIREMENTS.md`.
- Updated `AGENTS.md` to identify root `FEATURE-REQUIREMENTS.md` as the dedicated working base for access-control capability requirements.
- Realigned `README.md` with the consolidated responsibility model: admins automatically access all service-access-role-covered protected services, admins and super-admins assign service-access roles only to members, super-admins manage the role catalog without protected-service access through those roles, service-access roles are not assigned to admin accounts, and break-glass remains a Phase 2 debate topic unless explicitly adopted later.
- Replaced the `README.md` `FS-*` minimum feature requirements table with a short pointer to root `FEATURE-REQUIREMENTS.md` as the single feature-requirements source.
- Renamed the `README.md` title and tightened its introduction to present the repository as the EDRLab backoffice access-control study.
- Refined the `README.md` core features list so it summarizes capabilities without duplicating the consolidated feature requirements.
- Updated the `README.md` Mermaid diagram to show member, admin/super-admin, identity-provider, access-control, role-management, audit, and protected-service flows.
- Tightened the `README.md` project goal so it states the study objective and main account-type/service-access-role distinction without repeating detailed requirements.
- Reworked the `README.md` actors and role types section into readable per-role responsibility blocks while preserving the validated access-control model.
- Renamed the `README.md` retired requirements section to `Feature Requirements Source` while preserving the old `minimum-feature-requirements` anchor for existing documentation links.
- Condensed the `README.md` initial scope section into grouped in-scope and out-of-scope boundaries without repeating detailed role requirements.
- Renamed the `README.md` Phase 2 debate topics section to `Open Study Questions` and grouped unresolved security, architecture, access-evidence, operations, and PoC questions.
- Reworked the `README.md` documentation section into a task-oriented entry-point table.
- Updated `ABSTRACT.md` to reflect the 2026-05-07 consolidation state: `FEATURE-REQUIREMENTS.md` as the single requirements source, baseline retirement, current validated responsibility model, and remaining open study questions.
- Updated `ABSTRACT.md` to reflect the review-state `FR-001` through `FR-044` feature requirements, explicit identity-provider and onboarding boundary, and current Phase 2 threat-model, architecture-option, and technical-solution-candidate artifacts.
- Promoted `FEATURE-REQUIREMENTS.md` from blank-slate working base to review-state single feature-requirements source and replaced former `FS-*` source links with consolidation-review traceability.

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
- Removed the duplicate out-of-scope section from the requirements baseline so scope exclusions stay centralized in the root `README.md`.
- Simplified `RB-016` to require defining how already-issued access stops without embedding JWT-versus-opaque-token comparison in the requirement text.

### Added

- Added the initial Phase 2 threat model skeleton under `docs/risks/threat-model.md`.
- Added initial Phase 2 project requirements based on current stakeholder scoping answers.
- Added initial Phase 2 architecture option framing for monolithic, modular monolithic, split control-plane, microservices, and hybrid IAM shapes.
- Added the Phase 2 requirements baseline under `docs/requirements/baseline.md`.

### Removed

- Removed the initial Phase 2 project requirements document at stakeholder request.
