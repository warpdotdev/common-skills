---
name: fix-errors
description: Fix build, compilation, lint, formatting, and test errors in a repository. Use when the user hits build errors, lint or format failures, or test failures, or needs to run and interpret the repository's checks before a PR.
---

# fix-errors

Fix build, lint, formatting, and test errors in a repository.

## Related Skills

- `fix-errors-local` - Optional per-repo companion that documents exact toolchain commands, known error patterns, and repo-specific validation rules.
- `create-pr` - Run final repository checks before opening or updating a pull request.

## Overview

This skill helps resolve common issues encountered during development, including:
- Build and compilation errors (syntax errors, unresolved imports, type mismatches, etc.)
- Lint failures
- Formatting violations
- Test failures

Before opening or updating a pull request, the repository's checks must pass.

## Workflow

1. **Run the repository's own checks.** Use whatever the repo documents (a check script, a `Makefile` target, or the language toolchain's format/lint/build/test commands). If you are unsure which commands to run, look for an `AGENTS.md`, a contributing guide, a build config, or a CI workflow that lists them. A repo may also provide an optional `fix-errors-local` companion that names its exact toolchain commands.
2. **Read the full output and categorize the errors.** Group related errors by type; fixing one often resolves others.
3. **Fix one class of error at a time.** Make the smallest change that addresses the root cause, not just the symptom.
4. **Re-run the narrow check** for the class you fixed to confirm it passes and did not introduce new errors.
5. **Run the repository's full check** once individual classes are resolved, and repeat until everything passes.

## Local extension point

This core intentionally avoids naming language-specific commands or exhaustively listing error categories. A repo may provide a `fix-errors-local` companion with exact format, lint, build, and test commands plus known local failure patterns. Prefer that companion when available; otherwise infer commands from `AGENTS.md`, contributing docs, build files, and CI workflows.

## Best Practices

**Before fixing:**
- Read the full error message to understand the root cause.
- Check whether multiple errors are related (fixing one may resolve others).
- For type or signature errors, confirm you understand the expected vs. actual types.

**When fixing:**
- Fix one error type at a time when there are multiple issues.
- Re-run a fast build/check frequently to verify progress.
- Run relevant tests after non-trivial changes.

**After fixing:**
- Run the repository's full set of checks before opening or updating a PR. Use the `create-pr` skill for more detailed instructions.
- Verify tests pass in the areas you modified.

A repo may provide a `fix-errors-local` companion that documents its exact toolchain commands and repo-specific error patterns.
