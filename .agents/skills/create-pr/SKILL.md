---
name: create-pr
description: Create a pull request in the warp repository for the current branch. Use when the user mentions opening a PR, creating a pull request, submitting changes for review, or preparing code for merge.
---

# create-pr

## Overview

This guide covers best practices for creating pull requests in the warp repository, including merging master, validating changes efficiently, linking Linear tasks, ensuring appropriate test coverage, and structuring your PR for effective review.

## Related Skills

- `write-pr-description` - Write the PR body itself: template sections, prose, and reviewer guidance
- `fix-errors` - Fix targeted compilation, test, lint, or formatting failures before opening a PR
- `warp-integration-test` - Add or update integration coverage for user-visible flows, regressions, and P0 use cases
- `add-feature-flag` - Gate changes behind feature flags

## Pre-PR Checklist

### 1. Merge master into your feature branch

**Always merge master into your feature branch before starting the review process.**

```bash
git fetch origin
git merge origin/master
```

Resolve any merge conflicts locally before opening the PR.

### 2. Review your changes

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
- **Tests:** Check that relevant tests cover the change and passed for the current candidate—bug fixes (regression test), algorithmic code (unit tests), UI components (layout test), P0 use cases (integration test). See Testing Requirements below.

### 3. Respect implementation agent validation

PR creation is not a validation boundary. Check the evidence that relevant tests passed for the current candidate; tests existing in the diff alone are not proof they ran. If the implementation workflow already completed its tests, lint checks, and final formatting pass and the candidate has not changed, reuse that evidence without rerunning checks or asking whether to validate again.

If evidence is missing or the candidate changed (including source, tests, manifests, generated code, or configuration changed by merging master or preparing the PR), use suitable existing tests; when appropriate coverage is missing, add a targeted test proportionate to the risk rather than defaulting to an integration test. Validate this candidate in order:

1. Run the relevant tests and fix the code until they pass.
2. Run the applicable Clippy and other lint, typecheck, or build checks and fix their findings. Return to affected tests only when a fix materially changes behavior.
3. Run `./script/format` once after all other code changes are complete.

Do not rerun tests or lint after formatting, and do not run `./script/presubmit`, unless the user, task, or approved spec explicitly requires it. CI owns uncommon failures outside targeted local coverage. Documentation-only changes do not require Rust tests, Clippy, or formatting.

### 4. Link to Linear task

When possible, PRs should be associated with a Linear task. Use the Linear MCP tool (if available) to find corresponding issues.

**Branch naming convention:**
Remote branches should be prefixed with your name (e.g., `zheng/feature`, `alice/fix-bug`).

**How to link PRs to Linear:**
Include the issue ID in the PR title (e.g., `[WARP-1234] Add new feature`). Do this **before** creating the PR for automatic linking.

### 5. Open the PR

Use the PR template at `.github/pull_request_template.md` when opening PRs.

Add changelog entries when appropriate using the format at the bottom of the PR template. Some examples:
- Feature: "Global search in files across your current directories. Use CMD-F/CTRL-SHIFT-F to open."
- Improvement: "Added horizontal autoscrolling when jumping to line/column."
- Bug fix: "Fixed session viewer input being cleared when agent runs commands.

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

When committing changes, include attribution as a trailer at the end of the commit message only — never in the PR description — and never add a second Warp/Oz co-author trailer if the commit already has one:

```
Co-Authored-By: Warp Agent <agent@warp.dev>
```

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
- Custom data structures (e.g., `SumTree`)
- Search-related APIs that should return expected results for a given query
- Core layout code in the UI framework
- Any algorithmic or computational logic

**Not required for:**
- Sufficiently-simple functions
- Trivial getters/setters

Follow the repository's local testing conventions for guidance on writing unit tests.

### UI components need layout validation tests

**All UI components (implementations of `View`) should have a simple unit test** to validate that they can be laid out without a panic.

This provides high-level coverage over rendering "safety" (though not "correctness"):

```rust
#[test]
fn test_component_can_layout() {
    use warpui::App;
    use warp::test_util::{terminal::initialize_app_for_terminal_view, add_window_with_terminal};
    
    App::test((), |mut app| async move {
        initialize_app_for_terminal_view(&mut app);
        let term = add_window_with_terminal(&mut app, None);
        
        // Render the component - should not panic
        term.update(&mut app, |view, ctx| {
            // Create and layout your component
        });
    })
}
```

### Choose integration coverage based on risk

Do not ask about adding an integration test merely because a change is user-visible or a PR was requested. Check whether existing tests already exercise the changed behavior and passed for the current candidate. Unit or layout tests may be sufficient for contained changes.

Add or update integration coverage when the defect or critical behavior depends on a full user-facing flow or interactions that targeted tests cannot establish; P0 use cases always require it. Run any newly added or changed test, but do not duplicate adequate coverage or rerun passing tests for an unchanged candidate solely to open the PR. Ask the user only when a genuine decision about scope remains after investigating, not as a routine pre-PR gate.

### P0 use cases require integration tests

**All "P0 use cases" require an integration test** that covers the behavior/flow in question.
An existing integration test satisfies this requirement when it covers the changed behavior and passed for the current candidate; add one only when that coverage is missing.

**A "P0 use case" is defined as:** Any behavior of the application that, if broken, warrants an out-of-band release.

Integration tests should:
- Exercise the full user-facing flow
- Validate end-to-end functionality
- Be placed in the `integration/` directory

Use the `warp-integration-test` skill for implementation details, test registration steps, and validation workflow.

## PR Description Guidelines

Use the `write-pr-description` skill for the body itself. It covers following the
repository's template, the prose baseline, and when to add a reading order and focus
areas for the reviewer.

## After Opening the PR

1. **Monitor CI checks** - Ensure all automated checks pass
2. **Respond to review comments** - Address feedback promptly
3. **Keep the PR up to date** - Merge master if conflicts arise
4. **Validate changed candidates** - After code changes from review feedback, run affected tests, then lint checks, then `./script/format` once. Do not repeat validation for PR metadata or an unchanged candidate.

## Best Practices

- **Keep PRs focused** - One logical change per PR when possible
- **Write clear commit messages** - Explain what and why, not just what
- **Self-review first** - Review your own diff before requesting review
- **Update tests** - Ensure test coverage reflects your changes
- **Document breaking changes** - Call out any API changes or breaking modifications
- **Use feature flags** - Gate risky changes behind feature flags when appropriate (see the `add-feature-flag` skill)
