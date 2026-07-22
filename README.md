# Common Skills

Common Skills is a public library of reusable agent skills. Install the generic cores as-is, then add small companion skills only where your repository or team has local conventions the core should not hardcode.

The model is intentionally composable:

- **Generic cores** live here in `common-skills`.
- **Repo-specific companions** live in the consuming repository and are named `*-local`.
- **Team-specific companions** live in a team's shared skills repository and capture branding, attribution, issue tracking, and other organization-wide conventions.

This keeps common workflows portable while letting each team plug in its own commands, trackers, brand rules, and review norms.

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

Each installed skill lives in its own directory under `.agents/skills/`. The only required file is `SKILL.md` with YAML frontmatter containing at least:

- `name`: the kebab-case skill identifier
- `description`: what the skill does and when agents should use it

Companion skills that extend a core also declare these in their `SKILL.md` YAML frontmatter:

- `specializes: <core-skill-name>`
- `specializes_source: <owner/repo>:<path>`

## Current skills

### Spec workflow

- `write-product-spec` — writes user-facing `PRODUCT.md` specs.
- `write-tech-spec` — writes implementation-oriented `TECH.md` specs.
- `spec-driven-implementation` — guides the full spec-first workflow for substantial features.
- `implement-specs` — implements approved `PRODUCT.md` and `TECH.md` files while keeping specs and code aligned.
- `validate-changes-match-specs` — validates implementation changes against introduced or modified specs.
- `check-impl-against-spec` — compares PR implementation changes against provided spec context during review.

### Development workflow

- `create-pr` — prepares and opens pull requests; specialize per repo with `create-pr-local`.
- `diagnose-ci-failures` — inspects GitHub CI failures and produces a fix plan; specialize per repo with `diagnose-ci-failures-local`.
- `fix-errors` — fixes build, lint, formatting, and test failures; specialize per repo with `fix-errors-local`.
- `respond-to-pr-comments` — walks through PR review comments, applies requested fixes, and previews replies.
- `resolve-merge-conflicts` — resolves git conflicts with compact context.
- `review-pr` — produces structured PR review feedback from local diff artifacts.

### Investigation and decision-making

- `research` — delegates noisy research work to subagents and returns distilled findings.
- `council` — gathers model-diverse perspectives on one question.
- `cross-critique` — sharpens contested decisions by having agents critique each other's proposals.
- `saga` — orchestrates medium-to-large spec-driven implementations across worker agents.

### Product, design, and UX

- `pr-walkthrough` — generates an interactive PR walkthrough visualization.
- `reproduce-bug-report` — reproduces UI-focused bug reports with computer use.

### Skill authoring

- `update-skill` — creates and maintains skill directories and `SKILL.md` files.

## Extension model

There are two kinds of companion, each with its own naming convention:

- **Repo-specific modifiers** use the `<core>-local` suffix (for example `create-pr-local`, `fix-errors-local`, `diagnose-ci-failures-local`) and specialize a core for a single repository.
- **Team-specific modifiers** are named to match the exact reference a core makes (for example `agent-attribution`, `issue-tracking`, `branding`) and are shared across a team's repos.

These are the supported companion conventions today. A core is not replaced by a same-name skill: a companion either specializes a core or is referenced by it, rather than overriding it.

### Repo-specific companions (`*-local`)

Some cores expect the consuming repository to supply its own local facts — commands, file paths, CI check names, labels, reviewers, or test frameworks. Those live in `*-local` companions that specialize a core. The cores that expect one, and the companion each looks for:

- `create-pr` → `create-pr-local`: local PR checks, testing conventions, and tracker linkage.
- `fix-errors` → `fix-errors-local`: the repo's exact format/lint/build/test commands and known failure patterns.
- `diagnose-ci-failures` → `diagnose-ci-failures-local`: the repo's CI check names and local error categories.

To add one, create `.agents/skills/<core>-local/SKILL.md` in your repository and point it at the parent core:

```yaml
name: create-pr-local
description: Add this repository's PR conventions to the generic create-pr workflow.
specializes: create-pr
specializes_source: warpdotdev/common-skills:.agents/skills/create-pr
```

A companion should only add local facts. It must not copy the core's methodology, schemas, safety rules, or generic workflow.

### Team-specific companions

Some cores reference organization-wide skills by name. These are standalone skills (no `specializes`) that live in your team's shared skills repository; cores fall back gracefully when they are absent. The ones the cores reference:

- `agent-attribution`: canonical co-author trailer and agent review-reply prefix. Referenced by `create-pr`, `validate-changes-match-specs`, and `respond-to-pr-comments`.
- `issue-tracking`: tracker, team/project selection, labels, and ticket conventions. Referenced by `create-pr`, `spec-driven-implementation`, `write-product-spec`, and `write-tech-spec`.
- `branding`: brand voice, visual identity, and design tokens. Referenced by `pr-walkthrough`.

To add one, create `.agents/skills/<name>/SKILL.md` in your team repo. Match the `name` the core references so the soft reference resolves:

```yaml
name: agent-attribution
description: Your team's canonical co-author trailer and agent reply prefix.
```

### Optional runtime affordances

Generic cores may mention optional tools only with fallbacks. For example, a core can say to use a rendered comment-list tool if available, otherwise fall back to `gh` or plain text. Warp-only affordances, private services, and brand-specific examples belong in companions unless a skill is intentionally about a Warp-built workflow.

## Bootstrapping an internal skills repo

Create a private team skills repo (or an `.agents/skills/` directory inside an application repo) with only the companions your team needs:

```sh
mkdir -p my-team-skills/.agents/skills
```

Then add a `<name>/SKILL.md` for each companion your cores reference (see [Extension model](#extension-model) for the full list):

1. Set the frontmatter `name` to the exact name the core references (e.g. `create-pr-local`, `agent-attribution`, `branding`).
2. For a repo-specific `*-local` companion, add `specializes` and `specializes_source` pointing at the generic parent. Team-specific companions stand alone and omit both.
3. Fill in your team's actual commands, trackers, brand sources, or conventions.
4. Keep it to local signal only — do not restate the core's generic workflow.

## Usage

List available skills:

```sh
npx skills@latest add warpdotdev/common-skills --list
```

Install all common skills globally:

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

Prefer installing only the skills a repository actually needs. If a common skill needs repository-specific behavior, add a small companion skill rather than forking the shared core unless the change is useful everywhere.

## Adding a core skill

When adding a reusable core:

1. Put it under `.agents/skills/<skill-name>/`.
2. Include a `SKILL.md` with clear frontmatter.
3. Keep it focused on workflows that apply across repositories.
4. Move large reference material into `references/` and helper automation into `scripts/`.
5. Leave private commands, trackers, attribution, and brand details to companions.
