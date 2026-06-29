# Agent Documentation Policy

Status: Accepted
Phase: Phase 6 - Production MVP
Scope: Agent Policy
Last reviewed: 2026-06-29

Use this page only for documentation-heavy tasks: study documents, wiki pages, citations, document placement, decision records, and project-governance edits. Routine `access-control/` implementation work should stay guided by the short root [AGENTS.md](../AGENTS.md).

## Contents

- [Purpose](#purpose)
- [Document Placement](#document-placement)
- [Repository Documents](#repository-documents)
- [Citation Rules](#citation-rules)
- [Writing Style](#writing-style)
- [Security Documentation](#security-documentation)
- [Documentation Completion Checks](#documentation-completion-checks)
- [References](#references)

## Purpose

The root agent instructions are intentionally short for Phase 6 implementation. This policy keeps the longer study-era documentation, citation, and wiki rules available when the task is documentation-heavy.

The repository remains source-led for project study material. A debate, requirement interpretation, risk analysis, candidate comparison, or recommendation is not valid unless its material claims are supported by inline citations or explicitly recorded as assumptions or open questions ([Project governance - Evidence Standard](../PROJECT-GOVERNANCE.md#evidence-standard)).

## Document Placement

Project study documents are organized by reader task and artifact type, not by filename prefixes. Use these folders under `docs/`:

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

Use [docs/README.md](./README.md) as the documentation map. It should explain where each artifact type belongs, list current study documents, and point readers to the right entry point.

Decision records belong under `docs/decisions/` and should be numbered ADR-style only when a real project, architecture, vendor, product, or production-impacting decision is being proposed or accepted. Do not use decision records for open analysis, comparison tables, or working notes. Decision records should follow the local [ADR template guidance](./decisions/README.md).

Non-index project study documents outside `docs/decisions/` should start with:

```text
Status: Draft | Review | Accepted | Superseded
Phase: Phase 6 - Production MVP
Scope: Requirements | Risks | Architecture | Evaluation | PoC
Last reviewed: YYYY-MM-DD
```

Conceptual wiki pages under `docs/wiki/` are not required to use this metadata block.

## Repository Documents

Keep root [README.md](../README.md) final-review-facing. Do not use it for project tracking, working notes, open questions, terminology dumps, comparison matrices, option analysis, evaluation scoring, or phase-by-phase progress.

Root [FEATURE-REQUIREMENTS.md](../FEATURE-REQUIREMENTS.md) is the dedicated working base for the backoffice access-control and access-management capability. Edit it only when the user is refining final-solution feature requirements.

Record meaningful project history in [CHANGELOG.md](../CHANGELOG.md), not in `README.md` or ad hoc notes.

Keep the conceptual IAM wiki under `docs/wiki/`. It is for general IAM concepts, terminology, protocol explanations, security concepts, and references. Keep project-specific scope debate, requirements refinement, option analysis, solution-choice evaluation, PoC planning, review notes, implementation notes, phase status, and recommendations out of `docs/wiki/`.

Prefer updating existing documents over creating near-duplicates. If a document debates project scope, records trade-offs, evaluates options, plans a PoC, or describes implementation-oriented behavior, place it under top-level `docs/`, not `docs/wiki/`.

## Citation Rules

Citation is part of the reasoning, not decoration. Put links next to the claims they support, especially in requirement reasoning, threat or risk analysis, comparison matrices, solution-choice evaluations, PoC plans or results, and recommendation drafts.

Use a bottom `References` section as a source index, but do not rely on it alone. A reader should be able to tell which source supports which claim without guessing.

Source requirements:

- cite only sources that support the relevant statement;
- verify RFC numbers, specification names, URLs, and product behavior before including them;
- prefer stable URLs and primary sources for normative claims;
- omit sources that cannot be verified;
- cite [README.md](../README.md) for immutable project needs and clearly label user-provided assumptions when no external source can exist;
- treat tutorials, blogs, vendor explainers, marketing pages, pricing pages, and practitioner write-ups as secondary or contextual evidence;
- avoid using secondary sources as the sole support for security, protocol, compliance, or normative claims;
- when sources disagree, name the disagreement and avoid forcing a conclusion.

Preferred source order for strong claims:

1. official specifications and standards;
2. official security guidance;
3. official product documentation;
4. reputable technical references and practitioner evidence;
5. vendor explainers, marketing, pricing, and tutorial material for context or vendor-positioning claims.

Every Markdown study or wiki page under `docs/` should include source links in the content near the claims they support. Pure navigation indexes may satisfy this with links to the pages they summarize, but any explanatory claim still needs a supporting source. Non-index pages also need a `References` section.

## Writing Style

Write for senior software engineers who know backend systems, APIs, databases, distributed systems, security basics, and architecture, but may not know IAM-specific standards.

Be precise, practical, evidence-based, technically rigorous, explicit about assumptions and trade-offs, and focused on real system behavior. Use clear definitions, short sections, practical examples, tables where they clarify a decision, simple Mermaid diagrams when useful, common mistakes, security notes, and references.

Prefer short, concrete, human sentences. Avoid long introductions, decorative Markdown, endless option lists, unnecessary tables, generic theory, unsupported claims, vendor bias, unexplained acronyms, beginner-level oversimplification, absolute architecture claims, filler, and repeated explanations.

Do not turn a small task into a full analysis. If a decision is needed, give one or two options at most and name the recommended action. If something is uncertain, state the assumption and move forward carefully.

Use one `#` page title. If a Markdown document has more than two top-level sections (`##`), add a short table of contents or chapter list near the top. Keep the chapter list factual and compact.

## Security Documentation

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

## Documentation Completion Checks

Before finishing documentation-heavy work:

- confirm the work follows the current user request and the accepted MVP boundary;
- confirm the immutable feature specification was not changed unless explicitly requested;
- confirm meaningful project history was recorded in [CHANGELOG.md](../CHANGELOG.md) when required;
- confirm edited `docs/` or `docs/wiki/` pages have inline citations near claims and useful `References` sections for non-index pages;
- confirm citations are real, relevant, appropriate, and not merely decorative;
- confirm unsourced claims are either removed, sourced, or marked as assumptions or open questions;
- confirm overlapping topics are cross-referenced instead of heavily duplicated;
- run `git diff --check` or another suitable lightweight validation when files were edited.

## References

- [Project Governance - Evidence Standard](../PROJECT-GOVERNANCE.md#evidence-standard)
- [Project Governance - Phase 6](../PROJECT-GOVERNANCE.md#phase-6---production-mvp)
- [README - Documentation](../README.md#documentation)
- [FEATURE-REQUIREMENTS.md](../FEATURE-REQUIREMENTS.md)
- [docs/README.md](./README.md)
- [docs/decisions/README.md](./decisions/README.md)
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
