# Common Skills

This repository is where common agent skills that should be shared across repositories go.

A skill belongs here when it captures a reusable workflow, convention, or operating procedure that is useful in more than one repository. Repository-specific skills should stay with the repository they apply to unless they can be generalized without losing important context.

## Repository layout

```text
.agents/
  skills/
    <skill-name>/
      SKILL.md
      scripts/      # optional helper scripts
      references/   # optional supporting docs
      assets/       # optional bundled assets
```

Each skill lives in its own directory under `.agents/skills/`. The only required file for a skill is `SKILL.md` with YAML frontmatter containing at least:

- `name`: the kebab-case skill identifier
- `description`: what the skill does and when agents should use it

## Current skills

### Spec workflow

- `write-product-spec` — writes user-facing `PRODUCT.md` specs.
- `write-tech-spec` — writes implementation-oriented `TECH.md` specs.
- `spec-driven-implementation` — guides the full spec-first workflow for substantial features.
- `implement-specs` — implements approved `PRODUCT.md` and `TECH.md` files while keeping specs and code aligned.

#### How this compares to OpenSpec

The spec skills overlap with [OpenSpec](https://github.com/Fission-AI/OpenSpec) in their central goal: make the intended behavior reviewable before an agent implements it. They differ in scope and in how they manage specifications:

| | Common Skills spec workflow | OpenSpec |
| --- | --- | --- |
| Scope | A small, composable part of a broader skill library that also covers PRs, CI, research, and other development work | A dedicated spec-driven development framework and CLI |
| Artifacts | A behavior-focused `PRODUCT.md` and, when needed, an implementation-focused `TECH.md` for each change | Proposals, capability specs, designs, and task lists generated according to a configurable schema |
| Lifecycle | Keeps the approved change specs beside the implementation and updates them as the implementation evolves | Maintains canonical specs separately from change deltas, then syncs and archives completed changes |
| Tooling | Plain agent skills installed selectively with the `skills` CLI; there is no separate spec runtime or state manager | Its own CLI and agent commands for initialization, artifact generation, validation, synchronization, and archival |
| Customization | Compose individual skills and add repository-local companion skills for project-specific behavior | Configure project context and rules or define custom artifact schemas |

Use these spec skills when you want lightweight product/technical documents that compose with the rest of this repository's workflows. Use OpenSpec when you want a dedicated, tool-managed lifecycle for evolving canonical specifications and change deltas. The approaches can coexist, but a project should choose one of them as the source of truth for a given change to avoid maintaining duplicate specs.

### Development workflow

- `create-pr` — guidance for preparing and opening pull requests.
- `write-pr-description` — writes the PR body: template sections, plain-language prose, and reviewer guidance.
- `diagnose-ci-failures` — workflow for inspecting GitHub CI failures and producing a fix plan.
- `fix-errors` — guidance for fixing build, lint, formatting, and test failures.
- `resolve-merge-conflicts` — workflow and helper script for resolving git conflicts with compact context.
- `review-pr` — produces structured PR review feedback from local diff artifacts.
- `check-impl-against-spec` — compares PR implementation changes against provided spec context during review.

### Investigation and decision-making

- `research` — delegates low signal-to-noise-ratio research work to subagents and returns distilled, evidence-backed findings.
- `cross-critique` — sharpens contested decisions by having agents critique one another's independent proposals before synthesis.

### Skill authoring

- `update-skill` — guidance for creating and maintaining skill directories and `SKILL.md` files.
- `skill-doctor` — grades a repo's installed skills by scoring recent local agent conversations, then drafts the skill edits the evidence justifies.

## Adding a shared skill

When adding a skill to this repository:

1. Put it under `.agents/skills/<skill-name>/`.
2. Include a `SKILL.md` with clear frontmatter.
3. Keep the skill focused on a reusable workflow rather than one repository's private details.
4. Move large reference material into `references/` and helper automation into `scripts/`.
5. If copying from another repo, copy first, then generalize in a separate change so the provenance is easy to review.

## Generalizing repository-specific skills

Some skills copied here may still contain repository-specific examples, paths, commands, or assumptions. That is okay during initial migration, but shared skills should eventually be generalized by:

- replacing hard-coded repository names with placeholders or conditional guidance
- separating common workflow guidance from local repository conventions
- moving repo-specific overrides back into the repository that needs them
- keeping descriptions broad enough to trigger in multiple repositories, but specific enough to avoid unrelated tasks

## Usage

Consumers can install the shared skills with the `skills` CLI.

List available skills:

```sh
npx skills@latest add warpdotdev/common-skills --list
```

Install all common skills for Warp globally:

```sh
npx skills@latest add warpdotdev/common-skills --skill '*' --agent warp --global
```

Install one skill:

```sh
npx skills@latest add warpdotdev/common-skills --skill write-tech-spec --agent warp --global
```

Update installed skills later:

```sh
npx skills@latest update --global --agent warp
```

You can also copy or sync selected directories from `.agents/skills/` into a repository's own `.agents/skills/` directory.

Prefer copying only the skills a repository actually needs. If a common skill needs repository-specific behavior, add a small local companion skill in that repository rather than forking the shared skill unless the change is useful everywhere.
