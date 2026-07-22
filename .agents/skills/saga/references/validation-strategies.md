# Validation strategies

Validation is what makes a saga autonomous: if each task's criteria are airtight and checked by an appropriate method, workers can self-verify and the orchestrator can trust their reports. This file covers (1) discovering what's feasible, (2) choosing a method, and (3) writing criteria tight enough to be a contract.

## 1. Discover what validation is feasible

Before defining any criteria (Phase 1), establish — by inspecting the repo/environment first, asking the user only for what you can't discover:

- The program type (web app, native GUI, TUI, CLI/library, backend service).
- Whether **computer use** (browser/GUI automation, visual inspection) is available to you or to remote workers.
- The **test toolchain**: test runner, integration harness, build, lint, typecheck — and confirm the commands actually run.
- How the program is launched for manual/interactive verification.

Record these in `SAGA.md`. Criteria you can't actually check are worthless, so feasibility constrains the criteria you write.

## 2. Choose a validation method

Pick the strongest method the task and environment support. Tests are the baseline regardless — prefer to add automated tests for everything that can be tested, even when also using computer use or CLI verification, because tests are repeatable and guard against regressions.

Priority order:

1. **Computer use — for GUI and web UI behavior.** When the task's correctness is visual or interaction-driven (rendering, layout, flows, click/keyboard behavior), and computer use is available, validate by driving the running app and inspecting the result (screenshots, asserted on-screen state). If computer use is only available remotely, route that validation through a remote worker with computer use enabled and have it return screenshots/evidence as a durable artifact.
2. **Interactive CLI subagent — for TUIs and interactive terminal programs.** When the program is a TUI or otherwise interactive in the terminal, validate by driving it in an interactive session (e.g. a subagent operating a live PTY): send input, observe rendered output, assert expected states. This catches behavior that non-interactive runs miss.
3. **Unit & integration tests — otherwise, or when the above are unavailable/not applicable.** For libraries, CLIs, backend services, and pure logic, write and run unit and integration tests that assert the task's criteria. This is also the fallback when computer use / interactivity isn't available even for a GUI/TUI task.

A task may combine methods (e.g. integration tests *and* a computer-use check of the resulting UI). State the method(s) explicitly in the task.

## 3. Write airtight validation criteria

The bar: when the criteria are satisfied, there should be little-to-no possibility the task was completed incorrectly. To get there:

- **Make each criterion checkable, not aspirational.** "Login works" is not a criterion. "Submitting valid credentials redirects to `/dashboard` and shows the user's name; invalid credentials show an inline error and do not navigate" is.
- **Name the observable signal.** Tie each criterion to a concrete signal: a passing test name, an HTTP status + body, an on-screen element/text, a CLI exit code + output, a file's contents.
- **Cover the unhappy paths.** Specify error handling, empty/edge inputs, and boundaries — not just the happy path. Most "done but wrong" outcomes hide here.
- **Pin down interfaces.** If the task produces an API, schema, or function signature other tasks depend on, state the exact shape so parallel workers integrate cleanly.
- **State what must NOT change.** Where regressions are a risk, include "existing X still passes / behaves as before" as an explicit criterion.
- **Require evidence.** Each task must specify what the worker returns to prove completion: test output, screenshots, an interactive transcript, sample command output. No evidence, no pass.

If you cannot express a task's criteria this concretely, the task is under-specified: split it, add detail, or resolve the ambiguity with the user using structured options.

## 4. What workers do with criteria (self-validation loop)

Each worker should treat its criteria as a checklist to drive a fix→validate loop:

1. Implement the task.
2. Run the prescribed validation method and check every criterion.
3. If any fail, fix and re-validate. Repeat until all pass or genuinely blocked.
4. Return the evidence and a clear pass/blocked status.

The orchestrator trusts a "pass" only when the returned evidence actually demonstrates the criteria. At milestone boundaries, re-run validation across the integrated result, since independently-passing tasks can still conflict once merged.
