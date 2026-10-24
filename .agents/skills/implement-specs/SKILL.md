---
name: implement-specs
description: Implements approved PRODUCT.md and/or TECH.md specs, keeping applicable specs and code aligned as implementation evolves. Use after the specs are approved and the next step is implementation.
---

# implement-specs

Implement approved work from `PRODUCT.md`, `TECH.md`, or both.

## Overview

Use this skill after the applicable specs are approved. The goal is to build the change described by the available specs while keeping those checked-in specs and the implementation aligned as the work evolves.

Approved specs should live directly under `specs/<id>/`, for example `specs/APP-1234/PRODUCT.md`, `specs/gh-4567/TECH.md`, or both.

In many cases, the implementation should be pushed in the same PR as the applicable specs. As the engineer iterates, changes to those specs and the code should all be pushed in that same PR so review stays anchored to the change that will actually ship.

## Prerequisites

Before using this skill:

- identify and read every approved spec relevant to the change
- confirm that at least one approved spec exists and has explicit approval to start implementation
- confirm that every implementation-blocking open question has been resolved or explicitly deferred by the user or another explicitly identified human approver

If the approval or disposition of an implementation-blocking question is not evident from the current context, ask before writing code.

## Workflow

### 1. Read the approved specs first

Treat every approved spec as authoritative input to the intended change. Read all available specs before writing code and make sure you understand the expected behavior, design, constraints, risks, and validation plan.

### 2. Offer optional implementation aids for large features

For large or long-running features, optionally offer one of these aids to the user before implementation begins:

- `PROJECT_LOG.md` to track checkpoints, explored paths, partial findings, and current implementation state
- `DECISIONS.md` to capture concrete product and technical decisions made during the PRD and tech design process

These are optional aids, not required deliverables. Offer them when they would reduce confusion or help future agents avoid re-exploring the same paths.

### 3. Plan and implement against the specs

Break the work into concrete implementation steps, then implement the change against the approved specs.

During implementation:

- keep behavior, design, and implementation aligned with all approved specs
- add or update tests and verification artifacts as the work lands

Use the same PR for the specs and implementation when practical so the full evolution of the change is reviewable in one place.

### 4. Update specs as the implementation evolves

A material change alters an approved behavior, guarantee, architectural decision, scope boundary, risk or rollout assumption, or validation expectation. A routine edit records factual implementation detail or clarifies wording while preserving every approved decision.

When implementation reveals a proposed material change, describe its impact and get explicit approval from the user or another explicitly identified human approver before persisting it in the checked-in specs or acting on it in the implementation. Ask when the distinction between material and routine is unclear. Apply routine edits that keep the approved intent current.

In particular:

- update whichever approved specs describe the changed behavior, design, constraints, risks, or validation
- keep those updates in the same PR as the corresponding code changes

The PR should describe the change that actually ships, not just the initial draft of the specs.

### 5. Verify against the specs

Before considering the work complete, verify that the code matches the current specs.

Prefer:

- unit tests and regression coverage that follow the repository's local testing conventions
- integration or end-to-end tests for important user flows

Map each important approved commitment to at least one concrete verification step without creating an exhaustive duplicate matrix.

## Best Practices

- Keep specs and code synchronized throughout implementation.
- Treat the approved artifact set as settled input during implementation and surface material conflicts for review.
- Record approved material decisions in the applicable specs promptly.
- Use optional tracking documents only when they add real value for a complex feature.
- Keep the same PR coherent: spec updates, code changes, tests, and optional tracking docs should all support the same change narrative.

## Related Skills

- `spec-driven-implementation`
- `write-product-spec`
- `write-tech-spec`
