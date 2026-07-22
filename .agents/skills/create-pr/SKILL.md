---
name: create-pr
description: Create a pull request for the current branch. Use when the user mentions opening a PR, creating a pull request, submitting changes for review, or preparing code for merge.
---

# create-pr

## Overview

This guide covers best practices for creating pull requests, including merging the base branch, running the repository's checks, linking tracker tasks, ensuring appropriate test coverage, and structuring your PR for effective review.

## Related Skills

- `fix-errors` - Fix build, lint, formatting, and test failures before opening a PR
- `create-pr-local` - Optional per-repo companion that layers repo-specific build/test commands and PR conventions on top of this core

## Pre-PR Checklist

### 1. Merge the base branch into your feature branch

**Always merge the latest base branch into your feature branch before starting the review process.**
If the base branch is not already known, determine it before merging. Prefer the current PR's base from `gh pr view`, then the remote default branch from `git symbolic-ref --short refs/remotes/origin/HEAD`, then a documented repository convention.

```bash
git fetch origin
git merge origin/<base-branch>
```

Resolve any merge conflicts locally before opening the PR.

### 2. Run the repository's checks for code changes

If the PR includes code changes, run the repository's own formatting, linting, build, and test checks before opening or updating it. Consult the repo's `AGENTS.md`, which usually documents the exact format/lint/build/test commands; otherwise fall back to whatever the repo documents (for example, a check script, a `Makefile` target, or the language toolchain's commands). When a repo provides an optional `create-pr-local` companion skill, it documents the exact check commands to run.

If the PR is documentation-only (for example, skills, markdown, or other non-code content), you do not need to run code formatting or linting just to open or update the PR.

If checks fail for a code-changing PR, use the `fix-errors` skill to resolve issues.

**Run the repository's formatting, linting, and tests before:**
- Opening a new PR that includes code changes
- Pushing new commits that include code changes to an existing PR branch
- Any reviewed branch update that changes code

### 3. Review your changes

Before creating a PR, review what changes you're about to submit:

```bash
# View commits in your branch (comparing against base branch)
git --no-pager log <base-branch>..HEAD --oneline

# View file statistics for changes
git --no-pager diff <base-branch>...HEAD --stat

# View full diff
git --no-pager diff <base-branch>...HEAD
```

This helps you:
- Verify all intended changes are included
- Catch unintended changes before review
- Write an accurate PR description
- Ensure you're comparing against the correct base branch
- **Tests:** Include tests when required—bug fixes (regression test) and algorithmic code (unit tests). See Testing Requirements below.

### 4. Link to a tracker task

When possible, PRs should be associated with an issue tracker task. If a team-specific `issue-tracking` skill is available, use it to find the corresponding issue and linking convention. Otherwise, look for tracker guidance in `AGENTS.md`, a repo-specific `create-pr-local` companion, or repository docs. If the tracker, team, labels, or issue are still unclear and a structured question tool is available, ask the user; outside environments with such a tool, ask concisely in chat.

**Branch naming convention:**
Remote branches should be prefixed with your name (e.g., `zheng/feature`, `alice/fix-bug`).

**How to link PRs to the tracker:**
Include the issue ID in the PR title (e.g., `[APP-1234] Add new feature`). Do this **before** creating the PR for automatic linking.

### 5. Open the PR

Use the PR template at `.github/pull_request_template.md` when the repository provides one. If the repo provides an optional `create-pr-local` companion skill, follow its PR conventions (labels, reviewers, template specifics) as well.

**CLI workflow:**

- **Check if PR exists** for current branch:
  ```bash
  gh pr view --json number,url
  ```
  Exit code 0 if PR exists, 1 if not.

- **Create a new PR:**
  ```bash
  # With title and body
  gh pr create --title "Title" --body "Description" --draft

  # Auto-fill from commits
  gh pr create --fill --draft

  # Use PR template file
  gh pr create --body-file .github/pull_request_template.md --title "Title" --draft
  ```
  Key flags: `--draft` / `-d`, `--fill` / `-f`, `--body-file` / `-F`, `--web` / `-w`

- **Update an existing PR:**
  ```bash
  gh pr edit --title "New title" --body "New body"
  gh pr edit --add-reviewer username --add-label bug
  ```

- **Mark PR ready for review:**
  ```bash
  gh pr ready
  ```

### 6. Include co-author attribution

When committing changes or creating a PR, include your agent's co-author attribution at the end of every commit message or PR description, for example:

```
Co-Authored-By: <Your Agent> <agent@example.com>
```

For the exact trailer and reply prefix your team uses, follow the optional attribution companion when one is available — a repo's `create-pr-local` skill or a shared team `agent-attribution` skill — rather than hardcoding a specific agent identity here.

## Testing Requirements

### Bug fixes require regression tests

**All bug fixes should be accompanied by a regression test.** This helps prevent re-breaking something that was already broken once.

The test should:
- Reproduce the original bug (would fail before the fix)
- Pass after the fix is applied
- Be clearly named to indicate what bug it's preventing

### Algorithmic code requires unit tests

Code with non-trivial logic should have unit tests to validate functionality:

**Examples of what needs unit tests:**
- Custom data structures
- APIs that should return expected results for a given input
- Any algorithmic or computational logic

**Not required for:**
- Sufficiently-simple functions
- Trivial getters/setters

Follow the repository's local testing conventions for guidance on writing unit tests.

### Cover user-visible flows and critical paths

If the PR changes a user-visible flow, fixes an end-to-end regression, or covers a critical (P0) use case—any behavior that would warrant an urgent fix if broken—add or update the appropriate integration or end-to-end coverage following the repository's conventions. If you are unsure whether coverage is warranted and a structured question tool is available, use it to confirm before creating or updating the PR; otherwise, ask the user concisely in chat before adding broad coverage.

A repo may document its integration-test framework and P0 expectations in a `create-pr-local` companion.

## PR Description Guidelines

Your PR summary under the "Description" section should include:

1. **What** - What changes are being made
2. **Why** - Why these changes are necessary (link to the tracker task if applicable)
3. **How** - Brief explanation of the approach taken

## After Opening the PR

1. **Monitor CI checks** - Ensure all automated checks pass
2. **Respond to review comments** - Address feedback promptly
3. **Keep the PR up to date** - Merge the base branch if conflicts arise
4. **Re-run relevant validation** - After making changes based on review feedback. For code changes, re-run the repository's formatting, linting, and tests; for documentation-only changes, this is not required.

## Best Practices

- **Keep PRs focused** - One logical change per PR when possible
- **Write clear commit messages** - Explain what and why, not just what
- **Self-review first** - Review your own diff before requesting review
- **Update tests** - Ensure test coverage reflects your changes
- **Document breaking changes** - Call out any API changes or breaking modifications
- **Use feature flags** - Gate risky changes behind feature flags when appropriate
