---
name: write-product-spec
description: Writes a consumer-behavior-focused PRODUCT.md spec. Use when the user asks for a product spec, desired behavior document, or PRD.
---

# write-product-spec

Write a consumer-behavior-focused `PRODUCT.md` spec that adds durable product-level value.

## Overview

The product spec should make meaningful product behavior decisions unambiguous enough that an agent can implement them correctly and reviewers can evaluate them independently of the implementation. Describe the feature purely from the user's perspective — what the user sees, does, and experiences, and the stable guarantees that must hold for them. Do not include implementation details (internal types, state layout, module boundaries, data flow, algorithms).

"User" includes a human using Warp and consumers of a deliberately exposed, durable product surface:

- For UI / UX features: the human using Warp.
- For a public API, versioned protocol, or externally consumed library: the callers of that surface — other services, client code, plugins, or agents.
- For a deliberately stable cross-team contract: the named teams or services whose compatibility expectations are intentionally defined and reviewed.
- For a CLI tool or developer-facing surface: the developer invoking it.

Internal code that calls a data model, module, or helper is not by itself a product audience. A cross-team contract qualifies only when its owners and consumers deliberately treat its semantics as stable and worth independent review. Other internal contracts, lifecycle transitions, failure handling, and correctness matrices belong in `TECH.md` and tests.

A product spec does not imply that a tech spec is needed, and a tech spec does not imply that a product spec is needed. When both add independent value, implementation details, validation, and test planning live in the companion `TECH.md`, produced by the `write-tech-spec` skill.

## Right-size `PRODUCT.md` around its independent value

If the artifact set has not been chosen, use `spec-driven-implementation` to decide which specs add value. When the user directly asks for `PRODUCT.md`, honor that choice. Use the questions below to right-size the document and avoid treating technical complexity as product ambiguity:

- Would `PRODUCT.md` still be useful if the implementation changed completely?
- Does it contain decisions that a product/design stakeholder, public consumer, or owner of a deliberately stable cross-team contract should review?
- Will it be an independent source of truth, rather than a less precise duplicate of `TECH.md` and its test plan?

Use the answers to focus the requested document on its independently valuable consumer decisions. Keep this skill focused on producing and right-sizing the requested `PRODUCT.md`; artifact selection belongs to `spec-driven-implementation`.

Write specs to `specs/<id>/PRODUCT.md`, where `<id>` is one of:

- a Linear ticket number (e.g. `specs/APP-1234/PRODUCT.md`)
- a GitHub issue id, prefixed with `gh-` (e.g. `specs/gh-4567/PRODUCT.md`)
- a short kebab-case feature name (e.g. `specs/vertical-tabs-hover-sidecar/PRODUCT.md`)

`specs/` should contain only id-named directories as direct children — no engineer-named subdirectories.

Ticket / issue references are optional. If the user has a Linear ticket or GitHub issue, use its id. If they don't, ask them for a feature name to use as the directory. Only create a new Linear ticket or GitHub issue when the user explicitly asks for one; in that case use the Linear MCP tools or `gh` CLI respectively (and `ask_user_question` if team, labels, or repo are unclear).

## Before writing

Use the value test above to right-size the document, then gather only the context you need: directory id (Linear ticket, GitHub issue, or feature name), feature summary, target users, meaningful behavior choices, and user-visible edge cases. Use `ask_user_question` for missing context rather than guessing.

### Figma mocks

If the feature has any UI or interaction design, ask the user whether a Figma mock exists before drafting the Behavior section, and include the link in the spec when one is provided. A mock is often the most reliable source of truth for visual states, spacing, and edge-case layouts — not asking can cause the Behavior section to guess at intent the designer already settled.

- If the user provides a link, include it under a short `## Figma` section (or inline near the top of Behavior) as `Figma: <link>`.
- If the user confirms no mock exists, note `Figma: none provided` so the absence is explicit rather than ambiguous.
- If the feature is purely backend (data model, API, CLI with no visual surface), skip the question and omit the section.

Do not silently drop design context; an explicit "none" is preferable to no mention at all on features where design would normally be expected.

## Structure

Required sections:

1. **Summary** — 1–3 sentences describing the feature and desired outcome.
2. **Behavior** — The meat of the spec. A right-sized English description of the meaningful product behavior and stable guarantees, preferably written as numbered, testable invariants. See "The Behavior section" below — this is where the spec earns its length, and everything else should stay thin to avoid duplicating it.

Optional sections — include only when they add signal beyond the core. Omit the heading entirely if empty; do not write "None" as a placeholder.

- **Problem** — Include only when the motivation isn't obvious from Summary.
- **Goals / Non-goals** — Include when scope is ambiguous or has been contested.
- **Figma** — Include with a link when one exists, or an explicit `Figma: none provided` note when design matters but no mock exists. Omit entirely for non-visual features. See "Figma mocks" above.
- **Open questions** — Prefer inline `**Open question:** …` next to the relevant behavior. Include a dedicated section only if there are multiple unresolved questions worth collecting.

Do not include Validation, Success criteria, or Testing sections. Validation and test planning live in `TECH.md` when one exists. For PRODUCT-only work, keep a lightweight validation map in the implementation plan or PR. Write Behavior as testable guarantees that verification can reference without duplicating them.

## The Behavior section

Behavior is the spec. Everything else is framing.

The goal of Behavior is to resolve product ambiguity, not to enumerate every technical state transition or test case. It should be detailed enough that an implementer does not need to guess about meaningful product intent. Stop when additional detail would merely duplicate the technical design, lifecycle matrix, or validation plan.

Describe the items below only when they are relevant to the product surface:

- Default behavior and the happy-path user flow.
- Every user-visible state and the transitions between them.
- All inputs the user can provide and how the feature responds.
- Empty states, error states, loading / pending states, and cancellation.
- User-visible edge cases and decisions a reasonable implementer would not think to ask about — permission denied, offline behavior, cancellation, focus loss, and interactions with adjacent features.
- Keyboard, accessibility, and focus expectations where relevant.
- Invariants that must hold at all times and behaviors that must not regress.

Do not enumerate internal races, stale events, missing messages, concurrency cases, persistence details, or downstream test expectations unless they change a consumer contract that belongs in `PRODUCT.md`. Put those in `TECH.md` and tests. Length Behavior to match the amount of genuine product ambiguity, not the implementation's technical complexity.

## Length heuristic

Behavior should be as long as the product ambiguity requires. Do not inflate it to reflect technical complexity or to enumerate the validation matrix. The heuristic below applies to everything around Behavior (Summary, optional sections): keep that framing thin so the spec's total length reflects the product surface, not structural overhead.

- Bug fix, hardening, or refactor that preserves relevant consumer semantics: keep the requested product spec focused on any genuine consumer decisions and leave technical safety and preservation guarantees to `TECH.md` when one exists.
- Trivial feature or narrow UI tweak: keep the requested product spec brief and focused on the few meaningful decisions.
- Small product surface with few meaningful decisions or edge cases: framing plus Behavior typically ~30–60 lines total.
- Medium product surface with multiple user-visible states or interactions: typically ~80–150 lines total.
- Large or behaviorally rich feature: longer is fine, and most of the length should live in Behavior.

If you find yourself writing the same idea in Summary, Problem, Goals, and Behavior, collapse the framing — not the Behavior content.

## Writing guidance

- Prefer concrete, observable behavior over aspirational wording.
- Write Behavior as a list of invariants rather than prose when possible.
- Capture product invariants that must not regress and user-visible edge cases that are easy to miss.
- Avoid mirroring a technical transition matrix or test plan in product language.
- Avoid implementation details unless unavoidable for the UX.
- Each section should earn its place — if a section would repeat another or contain only boilerplate, omit it.

## Approval handoff

After drafting, present a concise summary of the material decisions and unresolved questions. When called by `spec-driven-implementation`, return this handoff so that workflow can coordinate approval across the selected specs. When called directly, ask the user or another explicitly identified human approver to resolve or explicitly defer every question that would affect implementation, then ask them to approve the spec or request revisions before it is treated as ready for implementation.

## Keep the spec current

Approved specs may ship in the same PR as the implementation. As implementation evolves, update `PRODUCT.md` in the same PR when user-facing behavior, UX details, public contracts, or deliberately stable cross-team contracts change. The checked-in spec should describe the feature that actually ships.

If evolving design changes the document's value, keep `PRODUCT.md` current for its approved behavior and return to `spec-driven-implementation` to revisit artifact selection. Present proposed material behavior changes to the user or another explicitly identified human approver and get explicit approval before updating the approved spec; routine edits that keep the approved intent current do not require renewed approval.

For large features, the implementer may optionally keep a `DECISIONS.md` file summarizing concrete decisions made during design and implementation. Offer it when it would help future agents; otherwise skip it.

## Related Skills

- `implement-specs`
- `write-tech-spec`
- `spec-driven-implementation`

## Example Behavior section

A sample Behavior section for a hypothetical feature: rendering GitHub-flavored Markdown tables in the Warp block list. It demonstrates the expected shape — numbered, testable, user-perspective invariants that enumerate defaults, edge cases, malformed input, streaming, selection/copy, search, sharing, theming, and cross-surface consistency, with one inline open question.

This is intentionally a behaviorally rich, user-facing example. Do not use its length or exhaustiveness as the default for bug fixes, hardening, refactors, or internal technical work; keep any requested product spec for those changes short and focused on genuine consumer decisions.

````markdown
## Behavior

1. When a terminal output block contains a GitHub-flavored Markdown table (a header row, a separator row of one or more `---` segments, and one or more body rows, all delimited by `|`), that table renders as a visually formatted table in the block — not as raw pipe-delimited text.

2. The table renders with:
   - A visually distinct header row.
   - Aligned columns based on the separator row: `|:---|` left-align, `|:---:|` center, `|---:|` right-align. `|---|` with no colons falls back to the default alignment (left for text, right for numeric-looking values).
   - Visible row separators (or equivalent spacing) consistent with the active theme.

3. Inline markdown inside a cell renders inline: bold, italic, inline code, strikethrough, and links all render the same way they do in the surrounding block output. Line breaks inside a cell (`<br>` or escaped `\n`) render as in-cell line breaks.

4. Column widths are chosen to fit the table's natural content when it fits inside the block. If a single cell's content is very long, that cell wraps its text within its column rather than forcing the column to an unreasonable width.
   - **Open question:** when a wrapped cell would produce an unreasonably tall row, do we clip with an "expand" affordance, or let the row grow unbounded?

5. Horizontal scrolling: when the table's total width exceeds the block width — many columns, or wide columns that can't reasonably be narrowed — the table becomes horizontally scrollable within the block. Scrolling horizontally reveals off-screen columns without clipping or truncating them. Vertical scrolling of the block continues to work independently of table scroll.

6. When the block is resized (terminal resize, pane split, sidebar open/close), the table reflows to the new width without losing row or column order.

7. Empty cells render as visibly empty (same row height as surrounding cells, no placeholder text). A row with all empty cells still renders as a row.

8. A table with only a header and separator (zero body rows) renders as a header-only table, not as raw text.

9. A single-column table renders as a single-column table (not collapsed to a bullet list or similar).

10. Malformed tables fall back gracefully:
    - Missing separator row → rendered as preformatted text, not as a table.
    - Ragged rows (some rows have fewer or more cells than the header) → missing cells render empty; extra cells are shown, with the header row extended visually if possible. The block should never silently drop data.
    - Unclosed table (last row truncated mid-stream) → rendered as a partial table; see (11).

11. Streaming output: while a command is still producing rows, the table renders incrementally. New rows append as they arrive. The header row locks in as soon as the separator line is received; rows before the separator render as plain text until the table is recognized.

12. Selection and copy:
    - Selecting across cells with the mouse or keyboard selects their visible text content.
    - Copying the selection produces tab-separated plain text by default (one row per line, cells separated by tabs). An affordance (context menu, shortcut) lets the user copy the original markdown source instead.
    - Copying the entire block preserves the original markdown source verbatim.

13. Search within a block (find-in-block) matches against cell text content. Matches highlight in place in the rendered cell; navigating matches scrolls the table into view, including horizontally if the match is in an off-screen column.

14. Sharing or exporting a block (Warp Drive, share link, save as file) preserves the original markdown source, not the rendered form.

15. Theming: table borders, header backgrounds, alternating row shading (if any), and link/code styles all come from the active Warp theme. No hard-coded colors.

16. Markdown tables render consistently wherever block-list markdown already renders — command output, agent responses, and any other block type that supports inline markdown. The same input produces the same table in each surface.

17. Non-table pipe content is not misrendered as a table. Text that contains `|` characters but no valid header-separator line remains plain text, even if it visually resembles a table.
````
