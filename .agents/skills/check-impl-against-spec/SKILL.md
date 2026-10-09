---
name: check-impl-against-spec
description: Compare a pull request's implementation against spec context in spec_context.md and feed any material mismatches into review.json. Use during PR review when approved or repository spec context is available.
---

# Check implementation against spec

Use this skill only when `spec_context.md` exists during PR review.

## Goal

Determine whether the implementation in the checked-out PR materially matches the approved spec context. This is a supplement to the normal code review, not a separate output.

## Inputs

- `spec_context.md` contains the approved spec context to compare against. It may combine behavior, design, constraints, validation, migrations, rollout, and non-goals from any relevant specs.
- `pr_diff.txt` contains the annotated diff for the PR.
- `pr_description.md` may contain additional scope or rationale.
- The working tree contains the PR branch contents.

## Process

1. Read `spec_context.md` and extract the concrete commitments it makes, regardless of which source document contains them:
   - required behaviors
   - design and implementation constraints
   - required validation, migrations, rollout, or compatibility steps
   - non-goals and intentionally deferred work
2. Compare those commitments against the actual implementation in `pr_diff.txt` and the checked-out files.
3. Treat small implementation-level adjustments as acceptable when they preserve the spec's intent. Do not flag harmless differences in naming, structure, or low-level technique.
4. Flag a mismatch only when it is material, such as:
   - required behavior from the approved spec context is missing
   - the implementation contradicts an approved decision or constraint
   - the change introduces significant unplanned scope
   - a required validation, migration, rollout, or compatibility step is absent

## Outputs

- Do not create a separate report file.
- Fold spec-alignment findings into `review.json`.
- Put broad spec-drift concerns in the review summary.
- Add inline comments only when the mismatch can be tied to changed lines in the diff.
- Treat material spec drift as at least an important concern.
- If the implementation matches the spec closely enough, do not add comments just to mention alignment.

## Boundaries

- Do not require literal one-to-one implementation of the spec when the PR achieves the same outcome safely.
- Do not speculate about spec details that are not actually present in `spec_context.md`.
- Evaluate each commitment on its substance regardless of which source document contains it.
- Do not post to GitHub directly.
