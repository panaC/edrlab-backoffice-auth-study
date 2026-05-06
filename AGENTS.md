# AGENTS.md - Agent Instructions

## Read First

Read this file before modifying the repository. Then use:

- [README.md](./README.md) for the project brief and immutable feature specification;
- [PROJECT-GOVERNANCE.md](./PROJECT-GOVERNANCE.md) for study phases and phase boundaries;
- [CHANGELOG.md](./CHANGELOG.md) for project history.

## Current Operating Phase

The current phase is `Phase 2 - Requirements and Risk Framing`.

Default Phase 2 work: business, technical, security, and operational requirements definition against the immutable feature specification; requirements traceability; open-question resolution; service and permission inventory refinement; candidate-evaluation preparation; lightweight PoC planning; and Markdown study artifacts.

Phase 2 boundaries:

- create or edit Markdown study artifacts under top-level `docs/` by default;
- keep conceptual IAM wiki pages under `docs/wiki/`;
- keep project-specific scope debate, requirements refinement, option analysis, candidate evaluation, PoC planning, implementation notes, phase status, and recommendations out of `docs/wiki/`;
- do not make a final vendor, product, architecture, or production implementation recommendation unless the user explicitly requests a decision or final recommendation;
- do not add application code, dependencies, package managers, Docker files, databases, migrations, CI files, generated artifacts, or deployment files unless the user explicitly expands the phase or asks for a Proof of Concept.

## Instruction Priority

If instructions conflict:

1. Follow the user's explicit request for the current task.
2. Follow this `AGENTS.md`.
3. Follow `PROJECT-GOVERNANCE.md` for phase conduct and boundaries.
4. Follow `README.md` for project goal, immutable feature specification, constraints, scope, roadmap, and documentation links.
5. Follow existing repository conventions.
6. Follow general best practices.

A user request overrides the Phase 2 boundary only when it explicitly changes phase, expands scope, asks for project-instruction changes, asks for project-brief changes, asks for a later-phase artifact, requests a final recommendation, or asks for a Proof of Concept.

## Non-Negotiable Rules

- Check for an existing suitable file before creating a new one.
- Keep README final-review-facing. Do not use it for project tracking, working notes, open questions, terminology dumps, comparison matrices, option analysis, evaluation scoring, or phase-by-phase progress.
- `README.md` may be edited for project brief changes. Its immutable feature specification may be edited only when explicitly requested.
- `AGENTS.md` may be edited when the user asks to refine agent instructions.
- Root `ABSTRACT.md` and `CHANGELOG.md` may be edited for project summary, project history, phase movement, or release-style documentation.
- Record meaningful project history in `CHANGELOG.md`, not in `README.md` or ad hoc notes.
- Do not make final vendor, product, architecture, or production recommendations unless explicitly requested.
- Do not invent citations, RFC numbers, standards, specification names, URLs, product behavior, or business facts.
- A debate, requirement interpretation, risk analysis, candidate comparison, or recommendation is not valid unless its material claims are sourced or explicitly marked as assumptions/open questions.
- Every Markdown documentation page under `docs/` or `docs/wiki/` must include source links in the content near the claims they support. Non-index pages must also include a `References` section. A bottom `References` section is required, but not sufficient by itself.
- Official specifications, standards bodies, official security guidance, and official product documentation are preferred for normative, security, protocol, and product-behavior claims. Reputable technical articles, practitioner write-ups, tutorials, vendor explainers, and marketing pages may be used as secondary or contextual sources when appropriate, but their source type and limits must be clear.
- Keep Mermaid diagrams simple and directly related to the explanation.
- Cross-reference overlapping topics instead of duplicating large sections.

## Documentation Rules

Project study documents must be organized by reader task and project artifact type, not by filename prefixes. Use these folders under `docs/`:

```text
docs/
  README.md
  requirements/
  risks/
  architecture/
  evaluation/
  poc/
  decisions/
  wiki/
```

Use lowercase `kebab-case.md` filenames inside those folders. Do not repeat the folder category as a filename prefix unless it materially improves clarity. Examples: `docs/requirements/project-requirements.md`, `docs/risks/security-risk-register.md`, `docs/architecture/context.md`, `docs/evaluation/criteria.md`, `docs/poc/plans.md`, and `docs/decisions/0001-example.md`.

Use `docs/README.md` as the documentation map. It should explain where each artifact type belongs, list current study documents, and point readers to the right entry point. Create topic folders only when they hold a real document or useful index; do not add placeholder analysis documents.

Decision records belong under `docs/decisions/` and should be numbered ADR-style only when a real project, architecture, vendor, product, or production-impacting decision is being proposed or accepted. Do not use decision records for open analysis, comparison tables, or working notes.

Non-index project study documents outside `docs/decisions/` should start with a compact metadata block:

```text
Status: Draft | Review | Accepted | Superseded
Phase: Phase 2 - Requirements and Risk Framing
Scope: Requirements | Risks | Architecture | Evaluation | PoC
Last reviewed: YYYY-MM-DD
```

Conceptual wiki pages under `docs/wiki/` are not required to use this metadata block. Decision records under `docs/decisions/` should use the ADR template from `docs/decisions/README.md`.

Keep the conceptual IAM wiki under `docs/wiki/`. It is for general IAM concepts, terminology, protocol explanations, security concepts, and references. Use the wiki index as an agent-facing reading path only; project-facing documents should link directly to specific supporting wiki pages.

Prefer updating existing documents over creating near-duplicates. If a document debates project scope, records trade-offs, evaluates options, plans a PoC, or describes implementation-oriented behavior, place it under top-level `docs/`, not `docs/wiki/`.

All study and wiki pages must cite sources inline in the relevant content, including tables where practical. Pure navigation indexes may satisfy this with links to the pages they summarize, but any explanatory claim still needs a supporting source. Page-level `References` sections should collect the sources used, not replace inline citations. If a claim comes from the immutable feature specification, cite or link to `README.md`; if it comes from the user, record it as a stated assumption or user-provided requirement.

Use one `#` page title. If a Markdown document has more than two top-level sections (`##`), add a short table of contents or chapter list near the top. Keep the chapter list factual and compact.

## Writing Style

Write for senior software engineers who know backend systems, APIs, databases, distributed systems, security basics, and architecture, but may not know IAM-specific standards.

Work pragmatically, with a targeted, action-oriented style. Read existing context first, identify the most direct useful action, then execute it or answer briefly.

Be precise, practical, evidence-based, technically rigorous, explicit about assumptions and trade-offs, and focused on real system behavior. Use clear definitions, short sections, practical examples, tables where they clarify a decision, simple Mermaid diagrams when useful, common mistakes, security notes, and references.

Prefer short, concrete, human sentences. Avoid long introductions, decorative Markdown, endless option lists, unnecessary tables, generic theory, unsupported claims, vendor bias, unexplained acronyms, beginner-level oversimplification, absolute architecture claims, filler, and repeated explanations.

Do not turn a small task into a full analysis. If a decision is needed, give one or two options at most and name the recommended action. If something is uncertain, state the assumption and move forward carefully.

## Citation Rules

Citation is part of the reasoning, not decoration. Put links next to the claims they support, especially in requirement reasoning, threat/risk analysis, comparison matrices, candidate evaluations, PoC plans/results, and recommendation drafts.

Use a bottom `References` section as a source index, but do not rely on it alone. A reader should be able to tell which source supports which claim without guessing.

Source requirements:

- cite only sources that support the relevant statement;
- verify RFC numbers, specification names, URLs, and product behavior before including them;
- prefer stable URLs and primary sources for normative claims;
- omit sources that cannot be verified;
- cite `README.md` for immutable project needs and clearly label user-provided assumptions when no external source can exist;
- when using tutorials, blogs, vendor explainers, marketing pages, pricing pages, or practitioner write-ups, treat them as secondary/contextual evidence and avoid using them as the sole support for security, protocol, compliance, or normative claims;
- when sources disagree, name the disagreement and avoid forcing a conclusion.

Preferred source order for strong claims:

1. official specifications and standards;
2. official security guidance;
3. official product documentation;
4. reputable technical references and practitioner evidence;
5. vendor explainers, marketing, pricing, and tutorial material for context or vendor-positioning claims.

Baseline references:

- [RFC 6749 - OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 6750 - OAuth 2.0 Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7636 - Proof Key for Code Exchange](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 7662 - OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
- [RFC 9700 - Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)

## Security Rules

Security guidance must be conservative and evidence-based. Do not recommend:

- plain-text password storage;
- custom cryptography;
- unsigned JWTs;
- skipping issuer validation;
- skipping audience validation;
- long-lived access tokens without justification;
- exposed admin APIs without strong authorization;
- frontend-only authorization checks;
- Implicit Flow for new browser-based applications.

When describing risks, explain what can go wrong and how to reduce the risk.

## Proof-Of-Concept Boundary

In Phase 2, prefer PoC planning, evaluation criteria, short pseudocode, and short illustrative examples. Full candidate evaluation belongs to later phases unless the user explicitly asks for that artifact now.

If the user asks for a Proof of Concept, keep it scoped to the learning goal, document assumptions and limits, mark it non-production, and avoid production infrastructure.

Code examples must be short, illustrative, and clearly non-production.

## Repository Hygiene

When modifying the repository:

- preserve project conventions and make small, focused changes;
- avoid generated files;
- use targeted edits instead of replacing whole files unless the current content is clearly wrong, incomplete, or the user asks for a restructuring;
- do not revert existing user changes unless explicitly requested.

## Completion Checks

Before finishing, verify the result rather than restating the workflow:

- confirm the work follows the current user request;
- confirm facts align with `README.md`, `PROJECT-GOVERNANCE.md`, and this file;
- confirm the immutable feature specification was not changed unless explicitly requested;
- confirm no forbidden implementation files or unnecessary dependencies were added;
- confirm no final recommendation was made unless explicitly requested;
- confirm meaningful project history was recorded in `CHANGELOG.md` when required;
- confirm edited `docs/` or `docs/wiki/` pages follow the citation rules: inline citations near claims and useful `References` sections for non-index pages;
- confirm citations are real, relevant, appropriate, and not merely decorative;
- confirm unsourced claims are either removed, sourced, or marked as assumptions/open questions;
- confirm overlapping topics are cross-referenced instead of heavily duplicated;
- run `git diff --check` or another suitable lightweight validation when files were edited.
