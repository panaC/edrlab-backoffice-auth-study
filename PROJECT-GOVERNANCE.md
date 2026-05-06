# Project Governance

This document describes how the study is conducted.

The root [README.md](./README.md) contains the immutable feature specification and the public project roadmap. This document explains how agents should interpret the roadmap when creating study artifacts, evaluating options, or moving between phases.

The roadmap has seven study phases. Phase 8 is an optional post-study implementation phase and must not start unless the user explicitly moves the project into implementation.

Agents must respect the current operating phase recorded in [AGENTS.md](./AGENTS.md). Do not perform work from a later phase just because it seems useful. A user request overrides the current phase only when it explicitly changes phase, asks for a later-phase artifact, expands scope, requests a final recommendation, or requests a Proof of Concept.

## Evidence Standard

The study must be source-led. A debate, trade-off, risk, candidate evaluation, or recommendation is not valid unless the material claims are supported by inline citations or explicitly recorded as assumptions/open questions.

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
- prepare candidate-evaluation criteria.

Boundaries:

- do not choose a final vendor, product, architecture, database, hosting model, token strategy, or implementation stack;
- do not add application code, dependencies, deployment files, databases, migrations, or CI;
- do not change the immutable feature specification unless explicitly requested.

## Phase 3 - Candidate Approach Catalog

Purpose: identify and describe viable solution approaches before evaluation.

Allowed work:

- catalog managed, self-hosted, minimal internal, library-based, SSO-first, and hybrid approaches;
- record candidate capabilities, assumptions, constraints, and known unknowns;
- map candidates to feature-spec needs at a high level.

Boundaries:

- do not rank candidates as final winners;
- do not present a final recommendation;
- do not run broad implementation work.

## Phase 4 - Evidence-Based Candidate Evaluation

Purpose: compare shortlisted candidates using evidence and run focused non-production Proofs of Concept only where documentation cannot answer material uncertainties.

Allowed work:

- build comparison matrices and candidate evaluation records;
- collect official documentation evidence and cite it accurately;
- run tightly scoped PoCs that answer a specific evaluation question;
- record PoC assumptions, limits, results, and non-production status.

Boundaries:

- do not let a PoC become a hidden MVP;
- do not build production infrastructure;
- do not treat a PoC result as the final recommendation without Phase 5 through Phase 7 synthesis.

## Phase 5 - Proposed Target Solution Draft

Purpose: synthesize the evidence into a proposed target solution draft that can be challenged before final recommendation.

Allowed work:

- draft the proposed target solution specification;
- map the proposal to feature-spec requirements and evaluation evidence;
- describe logical responsibilities, major flows, integration boundaries, and unresolved decisions;
- explain why alternatives appear weaker based on the available evidence.

Boundaries:

- do not treat the draft as the final approved recommendation;
- do not start implementation from the draft;
- clearly mark reversible assumptions and remaining validation needs.

## Phase 6 - Adoption and Production-Readiness Review

Purpose: stress-check the proposed target solution before the final recommendation.

Allowed work:

- document adoption constraints, operational risks, security gaps, migration concerns, backup and recovery expectations, audit retention, administrator recovery, MFA or step-up gaps, break-glass questions, monitoring, upgrade burden, and ownership;
- identify what must be solved before production use;
- estimate operational complexity and residual risks.

Boundaries:

- do not change the target proposal silently;
- do not make the final recommendation yet;
- do not implement production readiness controls unless the user explicitly moves to implementation.

## Phase 7 - Produce a final evidence-based technical recommendation

Purpose: make the final study recommendation.

Allowed work:

- recommend the final approach;
- explain how it satisfies the immutable feature specification;
- summarize evidence, trade-offs, rejected alternatives, production-readiness gaps, residual risks, and adoption path;
- clearly distinguish required production work from optional future improvements.

Boundaries:

- only enter this phase when the user explicitly asks for the final recommendation or changes the project into the decision phase;
- do not overstate certainty where evidence is incomplete.

## Phase 8 - Optional Non-Production MVP

Purpose: build a non-production MVP after the final recommendation only if the user explicitly moves the project into implementation.

Allowed work:

- create implementation code, dependencies, local services, tests, and development tooling needed for the approved MVP scope;
- keep the MVP non-production unless the user explicitly changes that boundary.

Boundaries:

- Phase 8 is not part of the study's seven-phase decision process;
- do not start Phase 8 from curiosity, PoC momentum, or candidate preference;
- do not treat the MVP as production-ready without a separate production readiness process.
