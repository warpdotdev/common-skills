---
name: diagnose-ci-failures
description: Diagnose CI failures for a PR using the GitHub CLI, extract error logs, and generate a plan to fix them. Use when the user asks to check CI status, pull CI issues, triage test failures, or investigate PR build failures.
---

# diagnose-ci-failures

Programmatically diagnose CI failures for a PR and generate a plan to fix them.

## Related Skills

- `fix-errors` - Resolve the build, lint, formatting, and test failures identified by the diagnosis.
- `diagnose-ci-failures-local` - Optional per-repo companion that documents exact CI check names and local failure categories.

## Overview

This skill provides a deterministic workflow to check CI status for a PR, extract failure logs, analyze errors, and create a plan (not code changes) to resolve issues. The output is always a plan document that can be reviewed before execution.

## Workflow

### 1. Verify PR exists for current branch

Get the current branch and check if a PR exists:

```bash
# Get current branch
git branch --show-current

# Check for PR
gh --no-pager pr view <branch-name> --json number,title,url,state
```

If no PR exists, inform the user and offer to create one using the `create-pr` skill.

### 2. Check CI status

Fetch the status of all CI checks:

```bash
gh pr view <branch-name> --json statusCheckRollup
```

Parse the output to identify:
- Completed checks vs. in-progress checks
- Successful checks
- Failed checks with their names and details URLs

If CI is still running, inform the user which checks have already failed or passed, highlight the checks that are still running, and suggest waiting for completion before diagnosis.

### 3. Extract failure logs

For each failed check, pull the logs using the run ID from the status check:

```bash
gh run view <run-id> --log-failed
```

Focus on extracting:
- Error messages and their locations (file paths, line numbers)
- Build and compilation errors (unresolved imports, type mismatches, etc.)
- Lint errors with specific lint names
- Test failure messages and stack traces
- Build failures and their root causes

### 4. Categorize errors

Group errors by type, for example:
- **Formatting issues**: formatter check failures
- **Lint issues**: linter warnings/errors
- **Build/compilation errors**: type errors, missing imports, signature mismatches
- **Test failures**: failing tests with their names and failure reasons
- **Platform-specific issues**: failures isolated to a particular OS, architecture, or build target

### 5. Generate fix plan

Create a plan document (using `create_plan` tool) with:
- **Problem Statement**: Summary of failing checks
- **Current State**: What errors were found and where
- **Proposed Changes**: Specific fixes needed for each error category
- **Validation Steps**: The repository's check commands needed to verify the fixes

The plan should reference the `fix-errors` skill for detailed guidance on resolving specific error types.

## Important Notes

- **Always create a plan first**: Never make code changes directly. Generate a plan for user review
- **Check test status in CI**: Even if tests fail locally, verify they passed in CI before flagging as issues
- **Unrelated test failures**: If tests passed in CI but fail locally, they may be environment-specific or flaky
- **Multiple error types**: Fix one category at a time (e.g., all lint errors before tests)
- **Cross-reference fix-errors skill**: For detailed error resolution strategies, use the `fix-errors` skill

A repo may provide a `diagnose-ci-failures-local` companion that documents its specific CI check names and error categories.

## Example Commands

**Get PR status with details:**
```bash
gh --no-pager pr view --json number,title,state,statusCheckRollup
```

**Get logs from specific failed run:**
```bash
gh run view 12345678 --log-failed
```

**Check for specific error in logs:**
```bash
gh run view 12345678 --log-failed 2>&1 | grep -A 5 "error:"
```
