---
name: spec-driven-implementation
description: Guides a pragmatic spec-first workflow for substantial work, including deciding which specs add value, getting them approved, and keeping them current through implementation. Use when starting a significant feature or hardening effort, planning agent-driven implementation, or deciding which specs should be checked into source control.
---

# spec-driven-implementation

Drive a spec-first workflow for substantial work in Warp.

## Overview

Use this skill for significant work where a written spec will improve implementation quality, reduce ambiguity, or make review easier. Be pragmatic: not every change needs specs, and not every technically complex change needs a product spec.

Specs may live in:

- `specs/<id>/PRODUCT.md`
- `specs/<id>/TECH.md`

Use a Linear ticket number, `gh-`-prefixed GitHub issue id, or short kebab-case feature name as `<id>`. For example:

- `specs/APP-1234/PRODUCT.md`
- `specs/gh-4567/TECH.md`
- `specs/vertical-tabs-hover-sidecar/TECH.md`

`specs/` should contain only id-named directories as direct children. Do not create engineer-named subdirectories there.

Use a relevant Linear or GitHub issue when one already exists. If none exists, ask the user for a short feature name. Only create an issue when the user explicitly asks; use the Linear MCP tools or `gh` CLI respectively. For Linear:

- `list_teams` to find the appropriate team
- `list_issue_labels` to inspect the expected labels/tags
- `save_issue` to create the issue with the appropriate team and labels

If the correct team or labels are not obvious from the request and surrounding context, use `ask_user_question` to clarify rather than guessing.

Specs should largely be written by agents, not by hand, and should be checked into source control when their ongoing review value exceeds the cost of keeping them current with the code.

## When specs add value

Strongly prefer specs when the change is substantial, such as:

- product or architectural ambiguity
- expected implementation size around 1k+ LOC
- deep or cross-cutting stack changes
- risky behavior changes where regressions would be expensive
- work where agent quality will improve materially from clearer inputs

Specs are often unnecessary for:

- small, local bug fixes
- straightforward refactors
- narrow UI tweaks with little ambiguity

For pure UI changes, the product spec is often useful while the tech spec may be unnecessary.

Choose the smallest document set that adds independent value:

- **No spec** — Small, clear work that is better captured by the issue, code, and tests.
- **`PRODUCT.md` only** — Meaningful user-facing, public-contract, or deliberately stable cross-team consumer behavior is ambiguous, but implementation is straightforward.
- **`TECH.md` only** — Internal hardening, a bug fix, refactor, migration, lifecycle/concurrency work, or another technically complex change whose relevant consumer semantics remain unchanged. Include concise `Technical safety and preservation guarantees`.
- **Both** — Product behavior and technical design each contain meaningful, independently reviewable decisions.

Technical size or cross-cutting scope alone is not a reason to create `PRODUCT.md`.

Before choosing an artifact set without `PRODUCT.md`, state in one sentence whether user-visible, public, and deliberately stable cross-team consumer semantics — including failure and recovery behavior — change. If they change, explain briefly why the independent-value test still does not warrant a product spec; small, obvious changes may still need no spec. Task labels such as "bug fix," "refactor," and "hardening" are not evidence that semantics remain unchanged.

## Workflow

### 1. Decide whether the work needs specs

Evaluate the size, ambiguity, and risk of the work. If specs will not meaningfully improve execution or review, skip them and focus on verification instead.

### 2. Choose the artifact set

Do not assume `PRODUCT.md` comes first or that both documents are required. Choose no spec, `PRODUCT.md` only, `TECH.md` only, or both using the independent-value and semantic-preservation tests above.

Present the chosen artifact set and a brief rationale to the user or another explicitly identified human approver, and get explicit approval before proceeding with the selected path.

Treat the approved artifact set as part of the reviewed plan. Route any later artifact-selection review back through this workflow while implementation consumes the settled artifact set.

### 3. Write and approve the selected specs

Use the `write-product-spec` skill only when consumer behavior has independent review value. The product spec should define:

- what problem is being solved
- the desired user experience or consumer contract
- meaningful product invariants and consumer-visible edge cases

If the work has UI or interaction design, ask for a Figma mock if one exists. If there is no mock, continue but call that out explicitly in the product spec.

Reference the Linear or GitHub issue in the spec when one exists.

Use the `write-tech-spec` skill when the selected artifact set includes `TECH.md`. Prefer a tech spec when the implementation spans multiple subsystems, architecture or extensibility matters, there are meaningful tradeoffs to document, or reviewers will benefit more from reviewing the plan than the raw code.

It is acceptable to write the tech spec after an e2e prototype if that leads to a more accurate implementation plan. Do not force a premature tech spec when the implementation details are still too uncertain.

After the selected specs are drafted, present the material decisions, important tradeoffs, and unresolved questions. Ask the user or another explicitly identified human approver to resolve or explicitly defer every question that would affect implementation, then get explicit approval for the specs before implementation begins.

### 4. Implement approved specs

After the warranted specs are approved, use the `implement-specs` skill to build from whichever approved documents exist.

The implementation can often be pushed in the same PR as the specs. As the engineer iterates, keep the applicable specs, code changes, and tests in that same PR so the review reflects the change that will actually ship.

For PRODUCT-only work, keep a lightweight map from important product behavior to concrete verification in the implementation plan or PR rather than adding a testing section to `PRODUCT.md`.

For large features, the implementer may optionally offer:

- `PROJECT_LOG.md` to track explored paths, checkpoints, and current implementation state
- `DECISIONS.md` to capture concrete product and technical decisions made during design and implementation

These are optional aids, not required outputs.

### 5. Keep specs current during implementation

A material change alters an approved behavior, guarantee, architectural decision, scope boundary, risk or rollout assumption, or validation expectation. A routine edit records factual implementation detail or clarifies wording while preserving every approved decision.

When implementation reveals a proposed material change, describe its impact and get explicit approval from the user or another explicitly identified human approver before persisting it in the specs or acting on it in the implementation. Ask when the distinction between material and routine is unclear. Apply routine edits that keep the approved intent current.

Update `PRODUCT.md`, when it exists, when:

- user-facing behavior changes
- meaningful product guarantees change
- UX details or edge cases change

Update `TECH.md`, when it exists, when:

- the implementation approach changes
- architectural boundaries move
- risks, dependencies, or rollout details change
- the testing or validation plan changes

The checked-in specs should describe the change that actually ships, not just the initial intent. Keep those spec updates in the same PR as the related code changes whenever practical.

If evolving design calls the approved artifact set into question, return to the artifact-selection step. Explain the proposed artifact set, show how every durable guarantee remains represented, and get explicit confirmation from the user or another explicitly identified human approver before changing the approved artifact set.

### 6. Verify behavior against the spec

Before considering the work complete, make sure verification maps back to the applicable specs and guarantees, or to the lightweight validation map for PRODUCT-only work. Prefer tests and artifacts that validate the product behavior or technical safety and preservation guarantees directly:

- unit tests and regression coverage that follow the repository's local testing conventions
- integration tests for critical user flows
- loom walkthroughs or equivalent feature demonstrations when appropriate
- screenshots or videos when useful for UI-heavy work

## Best Practices

- Be pragmatic above all else.
- Write specs to improve input quality for agents, not as ceremony.
- Choose document types based on independent review value, not implementation size alone.
- Keep product specs behavior-oriented and implementation-light.
- Keep tech specs implementation-oriented and grounded in current codebase patterns; use concise technical safety and preservation guarantees when they add independent value.
- When a spec references relevant code chunks, include the inspected commit SHA in the file reference when possible and link the reference to the exact GitHub `blob/<sha>/...#Lx-Ly` lines.
- Use review time to validate specs and behavior, not to over-index on code style nits.

## Related Skills

- `implement-specs`
- `write-product-spec`
- `write-tech-spec`
