---
name: sweep-low-value-tests
description: Sweep an existing test suite for low-value tests - tests that re-assert the source, assert implementation instead of behavior, duplicate coverage, or exist only to justify a production seam - then fix, narrow, or delete them in reviewable batches and remove the seams they leave behind. Use when asked to sweep for low-value tests, prune or clean up a test suite, do a test cleanup pass, remove tests that re-assert the source, or find tests that should not be in the codebase.
---

# Sweep Low-Value Tests

## Overview

A sweep is not a code review. A review reads a diff and reacts to what an author just added. A sweep reads a suite that was merged months ago, with no diff to anchor on: it has to find candidates at scale, rank them, prove each deletion did not drop real coverage, and remove the production indirection the deletions leave dead.

Deleting a test is not the goal. A suite you trust is the goal. A sweep that drops real coverage is worse than no sweep, and "found nothing worth deleting here" is a valid result. Most of what a sweep finds wants a one-line fix, not a deletion.

Counterpart: the factory `code-review` skill (`v1/skills/code-review/SKILL.md` in `warpdotdev/factory-dev`) applies the same criteria to a single diff at review time. When the criteria change in one, update the other.

## Workflow

1. Pick a bounded target.
2. Surface candidates mechanically.
3. Judge each candidate.
4. Rank into fix, rewrite, delete, ask, keep.
5. Prove each deletion is safe.
6. Delete in reviewable batches.
7. Remove the dead seams.

## The decision question

This question is the whole skill; the names used below are only shorthand for its common answers. Apply it to each test or case, where a table row or a subtest is a case: what behavior change would make this fail, and would that failure be a real defect that no other test catches? When the honest answer is "a behavior-preserving refactor", "nothing", or "a higher-level test already covers it", the test is a candidate.

Never delete a test because it matches one of those names. A `Default` test reads as trivial and is vital when the default is a security posture. Reach for a name, then answer the question, and let the question win. A sweep reads at volume, which is exactly the condition under which name-matching replaces thinking.

When the answer is "nothing", check whether the behavior the test *names* is real and uncovered before proposing removal. An assertion that only runs inside an `if`, or a case that pins the pass-through and skips the error branch, is a coverage finding wearing a test-value costume: the test does not do its job, and the correction is to make it do it. A deletion must also carry any coverage gap it exposes - the branch check that condemns one case routinely reveals the arm nobody tested, and that gap is worth more than the deletion.

### The remediation ladder

The unit of judgment is the assertion, not the file. Take the least destructive correction that removes the problem:

1. Fix the assertion, keep the test.
2. Narrow the case to the distinct path it adds.
3. Move the test to the level where the behavior is observable.
4. Delete.

Every candidate records its rung and why the rung above does not work. Rung 1 dominates by site count - a redundant assertion inside an otherwise sound test is the commonest defect in a mature suite - but a cluster of cases that all assert one branch is rung 2, not rung 1. A sweep that reports mostly rung 4 has either found an unusual suite or stopped reading carefully; assume the second.

## 1. Pick a bounded target

Sweep one package, crate, or directory at a time. A whole-repository sweep is not one task, and the deletions have to land in batches a human will actually read. Note the test command for that target before starting - step 5 needs it.

## 2. Surface candidates mechanically

### Git history: tests that change whenever their source changes

The sharpest signal available in a sweep. A test that is edited in the same commit as its production file is tracking the implementation, not the behavior. History measures this directly.

```bash
git ls-files '*_tests.rs' '*_test.go' '*.test.ts' '*.test.tsx' '*_test.py' | while read -r t; do
  p=$(printf '%s' "$t" | sed -E 's/(_tests?|\.test|\.spec|_spec)\.([A-Za-z]+)$/.\2/')
  [ "$p" != "$t" ] && [ -f "$p" ] || continue
  tc=$(git log --oneline -- "$t" | wc -l)
  pc=$(git log --oneline -- "$p" | wc -l)
  uc=$(git log --oneline -- "$t" "$p" | wc -l)
  [ "$tc" -ge 5 ] || continue
  awk -v t="$t" -v a=$((tc+pc-uc)) -v b="$tc" 'BEGIN{printf "%.2f %3d %s\n", a/b, b, t}'
done | sort -rn | head -40
```

The columns are co-change ratio, commit count, path. `tc + pc - uc` is the number of commits that touched both files, by inclusion-exclusion. Adjust the globs and the `sed` pairing rule to the repository's naming convention, and verify the pairing prints real source paths before trusting the ranking.

Two caveats before relying on this:
- **A partial clone will hang.** On a `tree:0` or blobless checkout, a path-filtered `git log` lazily fetches trees and can take minutes per file. Check with `git config remote.origin.partialclonefilter`, and run the sweep against a full clone.
- **The threshold is unvalidated.** Treat a ratio above roughly 0.8 over a meaningful number of commits as "this test has almost never changed for its own reasons", but no measured baseline exists yet. A file that legitimately grew alongside a young feature scores high too.

### Shape heuristics

Cheap greps that correlate with low value. Use them to build a candidate list, not a verdict.

```bash
# Assertions on interactions rather than state.
grep -rnE 'toHaveBeenCalled|call_count|assert_called|AssertNotCalled|\.mock\.calls|\.times\(' <target>

# Mock density: which test files stub out every collaborator.
grep -rciE 'mock|stub|fake|spy' <target> | grep -v ':0$' | sort -t: -k2 -rn | head -20

# Quarantined tests.
grep -rnE '#\[ignore|t\.Skip\(|it\.skip\(|describe\.skip\(|@pytest.mark.skip' <target>

# Test names that betray a trivial subject.
grep -rnE '(fn test_|func Test|[ (]it\(|[ (]test\()' <target> --include='*test*' \
  | grep -iE 'default|getter|setter|construct|to_string|new_|clone|display|debug'
```

Also compare sizes: a test file several times longer than the source it covers is usually enumerating the implementation rather than the behavior.

Every heuristic here nominates a file to read; none of them convicts one. The name heuristic is the weakest. Run against `warpdotdev/warp` it surfaces `test_debug_representation_no_secrets`, which asserts a `Debug` implementation does not leak a secret - one of the more valuable tests in the crate. Its four near-identical siblings look duplicative and are not: each covers a distinct hand-written match arm, and the real defect there is the arm that has *no* test. Read the source before believing any of these lists.

## 3. Judge each candidate

Answer the decision question against the production code, never against the test's name or shape. You will usually be reaching that answer because the assertion restates a literal or a constant from the source; because it checks what the framework already enforces, such as a not-called assertion on a mock that already fails on any unexpected call; because the subject is a getter, a default, or plain construction; because another case already reaches the same branch; or because the test asserts a call sequence or private state instead of an outcome. Those are conclusions to arrive at, not patterns to match.

Read "Scoping a framework-enforced assertion" below before acting on the framework case. It is the largest surface in a mock-heavy suite, it is rung 1 at every site, and it is the easiest to get wrong at volume.

Species a sweep finds that a diff review cannot:

- **Orphaned**: the sweep-time form of an out-of-scope test. Its subject no longer exists in the form it tests, or the production code it exercises has no caller but the test. Delete the test; route the production deletion to a human.
- **Never-load-bearing**: the sweep-time form of scaffolding. The author is gone, so decide it on evidence instead of intent - `git log --follow` shows only mechanical edits (renames, signature churn, compile fixes) and no commit where it changed as part of a bug fix, and step 5 shows another test already fails when the behavior breaks.
- **Assertion-free**: sets up state, calls the unit, and asserts nothing - including an assertion that only fires inside a conditional the test never enters. The name claims a behavior the body never checks. Rung 1 whenever that behavior is real and uncovered: make the assertion unconditional, or add it. Delete only when the behavior is not real or is already covered.
- **Quarantined**: skipped or ignored with no live owner. When the linked ticket is stale or the data it guards is now empty, delete it; a permanently skipped test is a false signal of coverage.
- **Harness**: the subject is test infrastructure rather than product code - asserting a mock store holds exactly 31 fixtures, so adding a 32nd fails.
- **Config-mirror**: asserts the literal contents of a config file, including that a flag is still off, so it has to be edited to ship the feature it guards.
- **Frozen incidental output**: pins an exact value that was only ever incidental - an exact draw count from a fixed-seed generator under a comment reading "about half the time", where the intent was a tolerance band. Rung 1: widen the assertion, never delete it.
- **Third-party-shape**: asserts a dependency's own export shape rather than this repository's usage of it.

When a test fits two of these, take the one that lands on the higher rung.

### Scoping a framework-enforced assertion

On a strict mock - one constructed with the test handle, so it fails on any unexpected call - a negative call assertion restates the framework's own guarantee **only when no live expectation for that method exists on that mock instance in that subtest**. The precise rules:

- A "was not called" assertion with no live expectation for the method: framework-enforced, delete the line.
- A "was called" assertion: framework-enforced only when a non-optional expectation with matching arguments already exists. An expectation marked optional is what flips the assertion from redundant to load-bearing, since the framework no longer requires the call.
- A call-count assertion: essentially never framework-enforced, because registering an expectation permits unlimited calls. Leave it.
- An explicit "assert all expectations met" call on a strict mock: always redundant.

Scope every check to the mock instance and the subtest. An expectation registered in a sibling subtest is indistinguishable from a live one to a grep, and that single mistake produced 149 false leads in one automated scan. A candidate list from the interaction grep is not reviewable until it has been scoped this way.

## Never delete these

Each is a case where the thing that looks redundant is the only expression of the behavior.

- **A case pinning a contract another system depends on** where nothing else fails when the value silently changes - a flag spelling, a wire format, a telemetry key, the absence of an interface implementation - provided the case observes the value where that consumer reads it. "Another system" means outside the unit's compile-time reach, not outside the repository. This outranks the tautological and trivial-code readings.
- **A call assertion where the collaborator is the unit's only observable output.** This includes a not-called assertion where non-invocation is the behavior under test and nothing else fails when the call reappears: the framework's panic is not a substitute for the test stating what it guards.
- **A class or markup assertion where the rendered class is all the unit exposes.** Where no styles compute, it is the only observable output. Flag one only when the same behavior is visible in accessible state, role, or text - and then the correction is to assert that instead, not to delete.
- **Real IO where the IO is the subject** rather than incidental to the logic. A log rotator's tests belong on a real filesystem.
- **A near-identical case that reaches a different branch or pins a boundary the others do not.** Two rows hitting `hour < 12` are duplicates until one of them is hour zero.
- **A small test.** The burden is "what defect does this catch", never "is this test big enough".
- **A test that references a bug or issue ID.** It exists because something actually broke.
- **A failing or flaky test.** That is a different job: fix or quarantine it, do not sweep it away.

## 4. Rank

Order by confidence, and act by tier. The tiers run in ladder order, and that is also their expected size:

- **Fix or narrow** (rungs 1-2): a framework-enforced assertion, an assertion that only fires inside a conditional, a frozen incidental value that should be a tolerance band, a cluster of cases that all reach one branch. The test stays. Expect this to be the largest tier.
- **Rewrite** (rungs 1-3): a test asserting a call sequence or private state where the behavior underneath is real and uncovered, or one sitting at the wrong level. Never delete one and leave the behavior unguarded.
- **Delete** (rung 4): a test restating the source, one whose subject cannot break independently, and the orphaned, harness, and config-mirror species above - where the question, not a name, put them here, and where no higher rung applies. Every deletion goes through step 5 first and carries any coverage gap it exposed.
- **Ask a human**: anything where the behavior the test guards is unclear, anything step 5 cannot settle, any deletion of production code, and anything in an authentication, authorization, billing, or data-integrity path. Hand these over with the reasoning; do not decide them on the sweep's own judgment.
- **Keep**: everything else. Default here.

## 5. Prove each deletion is safe

Deleting a test always makes the suite pass, so a green run proves nothing. Prove instead that something else still guards the behavior:

1. Name the behavior the candidate claims to cover.
2. Break that behavior in the production code: invert a condition, return a wrong constant, drop a branch.
3. Run the target's tests with the candidate still present. It must fail. If it does not, the test does not cover what it claims: re-read it to find what it does cover. When the behavior it names is real and uncovered, fix the test instead of deleting it; delete only when it covers nothing anyone needs.
4. Remove the candidate and run again. If something else fails, the coverage is duplicated and the deletion is safe. If nothing fails, the candidate was the only guard: do not delete it, rewrite it as a behavior assertion instead.
5. Revert the production break. Confirm the tree is clean before moving on.

This check is the expensive step and it has no cheap substitute. A coverage tool reports that a line executed, not that anything was verified. Do not trade the check for throughput; it is the only thing standing between a sweep and silently deleted coverage.

One break can clear several candidates that claim the same behavior. Record, per deletion, the behavior and the test that still covers it - that record is the PR description in step 6.

## 6. Delete in reviewable batches

- One batch per package or area, small enough for a human to read in one sitting. Never one repository-wide deletion PR.
- List every deleted test in the PR description with one line each: the behavior it claimed to cover, and what still covers it.
- Keep rewrites in separate PRs from deletions. They need different review attention.

## 7. Remove the dead seams

Production indirection that existed only to serve a deleted test may now be dead, and removing it is the payoff the sweep is for.

Remove a seam only when the behavior it exposes is reachable at comparable cost without it. A seam that is the only affordable route to the behavior stays, whatever its motive, and a doc comment admitting the motive does not change that. Gratuitous indirection is distinguished by having a cheap alternative, not by why it was added; extracting logic into a directly testable unit is a legitimate design.

Before removing one, name what replaces any tests it still carries. If you cannot, there is no removal. Never remove a seam together with tests that have not already cleared step 5.

For the seams that do fail the cost test:

```bash
# The repository's own dead-code check first - it finds most of it.
# Rust: cargo clippy --workspace --all-targets. TypeScript: tsc --noUnusedLocals.
# Go: staticcheck ./... . Python: ruff check.
cargo clippy --workspace --all-targets 2>&1 | grep -E 'never used|never read'

# Then, per symbol the deleted tests referenced, count remaining non-test callers.
grep -rnE '\b<Symbol>\b' <target> --exclude='*test*' --exclude='*spec*' | wc -l
```

Narrow `pub(crate)` and `pub` back down, collapse a trait with one implementation into that implementation, and inline a wrapper whose only justification was the test. Land the seam removal in its own PR referencing the deletion batch, so a reviewer can judge the production change on its own merits.

## What to leave alone

Beyond the exemptions in "Never delete these":

- **A coverage drop is not proof of harm, and a coverage target is not the goal.** Step 5 is the proof.
- **Never chase a deletion count.** The pressure to hit a number is much stronger in a sweep than at review time, and it is exactly how a sweep starts deleting real coverage.
- **Read the repository's own testing skills and apply what they add**, including per-package ones, after checking their claims still hold against the repository - a rule forbidding a library the repository now declares as a dependency is stale, and a stale rule is a finding to report rather than one to sweep by. They do not displace the exemptions above: a local skill listing `Default` impls or near-identical tests as delete-worthy does not authorise deleting one this skill protects. When two packages in the same repository mandate opposite styles, that is a question for a human, not something to resolve mid-sweep.
