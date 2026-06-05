# Project Governance

This document describes how the study is conducted.

The root [README.md](./README.md) contains the immutable feature specification and the public project roadmap. This document explains how agents should interpret the roadmap when creating study artifacts, evaluating options, or moving between phases.

The roadmap has five study phases. Phase 6 is an optional post-study production MVP phase and must not start unless the user explicitly moves the project into production MVP implementation.

Agents must respect the current operating phase recorded in [AGENTS.md](./AGENTS.md). Do not perform work from a later phase just because it seems useful. A user request overrides the current phase only when it explicitly changes phase, asks for a later-phase artifact, expands scope, requests a solution choice, requests a review decision, or requests a Proof of Concept.

## Evidence Standard

The study must be source-led. A debate, trade-off, risk, solution-choice evaluation, or recommendation is not valid unless the material claims are supported by inline citations or explicitly recorded as assumptions/open questions.

All study and wiki pages must include source links in the content near the claims they support. Pure navigation indexes may satisfy this with links to the pages they summarize, but any explanatory claim still needs a supporting source. Non-index pages must also include a `References` section; a bottom source list is useful as an index, but it is not sufficient by itself.

Primary sources are preferred for standards, protocol behavior, security guidance, and product behavior. Secondary sources such as practitioner articles, tutorials, vendor explainers, and marketing pages may be used for context, product positioning, operational experience, or market framing when their limits are clear.

## Phase 1 - Conceptual IAM Foundation

Purpose: maintain the conceptual IAM wiki needed to reason about identity, authentication, authorization, tokens, roles, sessions, MFA, auditability, and security.

Allowed work:

- create or refine conceptual IAM pages under `docs/wiki/`;
- cite official specifications, standards, and reputable security guidance;
- explain concepts, terminology, protocols, risks, and common mistakes.

Boundaries:

- do not debate project scope, evaluate candidates, plan implementation, or recommend a final solution in the wiki;
- do not use wiki pages as project-specific decision records.

## Phase 2 - Requirements and Risk Framing

Purpose: translate the immutable feature specification into business, technical, security, operational, and evaluation requirements without choosing a final solution.

Allowed work:

- create or refine top-level `docs/` study artifacts for requirements, security analysis, operational analysis, evaluation criteria, question registers, and lightweight PoC planning;
- trace requirements back to the immutable feature specification in `README.md`;
- identify open questions, assumptions, risks, threat-model topics, and acceptance criteria;
- prepare solution-choice and PoC evaluation criteria.

Boundaries:

- do not choose a vendor, product, architecture, database, hosting model, token strategy, or implementation stack;
- do not add application code, dependencies, deployment files, databases, migrations, or CI;
- do not change the immutable feature specification unless explicitly requested.

## Phase 3 - Solution Choice

Purpose: compare a small set of realistic solution options and choose the candidate solution to validate.

Allowed work:

- keep a focused shortlist of realistic options;
- compare options against the feature requirements, threat model, operational constraints, simplicity goal, and source-backed product or standards evidence;
- record assumptions, open questions, risks, and trade-offs;
- choose the candidate solution to take into PoC or review, including the rationale and conditions.

Boundaries:

- do not treat the solution choice as production approval;
- do not start implementation work unless it is explicitly scoped as a non-production PoC;
- do not expand into a broad market survey when the existing shortlist is enough to decide.

## Phase 4 - Proof of Concept

Purpose: validate the chosen solution against the important uncertainties that documentation alone cannot settle.

Allowed work:

- define a tight PoC scope, success criteria, and explicit non-production limits;
- create or edit PoC documentation under `docs/poc/`;
- create temporary non-production PoC artifacts only within the agreed scope;
- test the uncertain integration, authorization, security, lifecycle, audit, or operational behaviors that matter to the solution choice;
- record results, failures, surprises, residual risks, and any evidence that changes the solution choice.

Boundaries:

- do not let a PoC become a hidden MVP;
- do not build production infrastructure;
- do not turn temporary PoC artifacts into durable application code without an explicit move to Phase 6 or another implementation phase.

## Phase 5 - Review and Decision

Purpose: review the chosen solution and PoC evidence, then decide whether to adopt the solution, adjust it, or go back to solution choice.

Allowed work:

- review the solution against feature requirements, security risks, operational ownership, auditability, reversibility, and project constraints;
- summarize what the PoC proved, what it did not prove, and what remains risky;
- record required adjustments, unresolved questions, production-readiness gaps, and residual risks;
- make the study decision: adopt the solution for the next step, adjust and re-review, or return to Phase 3 or Phase 4.

Boundaries:

- do not treat the review decision as automatic production MVP approval;
- do not hide unresolved production-readiness work inside the decision;
- do not overstate certainty where evidence is incomplete.

## Phase 6 - Production MVP

Purpose: build the first production-scope MVP after the review decision only if the user explicitly moves the project into production MVP implementation.

Allowed work:

- create implementation code, dependencies, services, tests, and development tooling needed for the approved MVP scope;
- create production-oriented configuration, deployment, observability, backup, recovery, audit, security-hardening, and operational artifacts needed for the approved MVP scope;
- document the production MVP scope, remaining non-MVP gaps, operating assumptions, residual risks, rollout path, and rollback or recovery expectations.

Boundaries:

- Phase 6 is not part of the five-phase study decision process;
- do not start Phase 6 from curiosity, PoC momentum, or candidate preference;
- do not promote PoC artifacts to production without explicit review, hardening, and acceptance;
- do not expand beyond the approved production MVP scope without an explicit scope change;
- do not claim full production completeness where the MVP intentionally defers non-critical capabilities.
