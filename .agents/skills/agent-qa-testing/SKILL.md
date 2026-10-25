---
name: agent-qa-testing
description: "Validates, runs, and triages agent-qa web/mobile regression tests when a project already uses agent-qa or the user chooses it. Use for YAML tests, run verdicts, and memory evidence. Do not use for unit-test generation or exploratory testing."
license: MIT
compatibility: "Requires Node.js 24+, an installed agent-qa CLI, and the project's configured model and browser/device target."
metadata:
  version: "1.0.1"
  author: "vostride"
---

# agent-qa testing

Use agent-qa for web, Android, and iOS regression tests with advanced memidex memory and self-improvement. Work with the project's existing tests, targets, and model configuration.

## When to Use

- Validate or run a selected agent-qa regression test in an initialized project.
- Investigate a failed or healed agent-qa run using recorded evidence.
- Inspect the memidex knowledge associated with that run.

## Establish the test scope

- Locate `agent-qa.config.yaml` and the requested test or suite. Run from that project directory; a global `--config <path>` must appear before the command.
- Use the project's installed version and package manager. The examples below assume an npm installation and use `--no-install` to avoid downloading a different version. Replace `tests/checkout.yaml` with the selected test path.
- Record the version separately; do not insert its number between the executable and subcommand.
- agent-qa requires Node.js 24+. If it is not installed or initialized, use the [official quickstart](https://vostride.com/docs/agent-qa/quickstart) and the user's chosen provider; preserve existing configuration and credentials.

```sh
npx --no-install agent-qa --version
npx --no-install agent-qa run --help
```

## Validate before executing

```sh
npx --no-install agent-qa validate tests/checkout.yaml
npx --no-install agent-qa run tests/checkout.yaml --dry-run
```

Validation checks configuration, test structure, and references. A dry run lists the selected tests without executing them. Neither proves that an application flow passes. Check the selected target and test files before running; omitting the path runs all discovered tests.

For suite selection or mobile device overrides, consult the installed command's help and existing project configuration. `doctor` can help diagnose setup failures, but its checks may contact the configured model provider.

## Run the selected flow

Run against the environment and test data authorized by the user. Application actions can change data, and configured providers may charge for execution.

```sh
npx --no-install agent-qa run tests/checkout.yaml --junit-output results.xml
```

Preserve the exit status and report path. Exit `0` means passed or healed; `1` covers failed or timed-out tests and missing required files; `2` means agent-qa could not run; `130` means cancelled. Inspect the verdict to distinguish a clean pass from a healed run; treat setup failures as unresolved execution, not application failures.

## Triage from recorded evidence

```sh
npx --no-install agent-qa runs list --verdict failed --limit 10 --json
npx --no-install agent-qa runs overview RUN_ID --json
npx --no-install agent-qa runs knowledge RUN_ID --json
npx --no-install agent-qa knowledge inspect --json
```

Replace `RUN_ID` with the relevant recorded run ID. Use `runs list --json` without the verdict filter when investigating a healed run or another outcome.

If a run has no completed verdict or its knowledge view reports `evidence-incomplete`, report that gap. Do not infer a completed application outcome from an incomplete record.

Read the failed step and available evidence before changing a test or application. Distinguish an application defect, a test expectation problem, and an environment/provider failure. Use the run's knowledge view to see what memidex supplied or learned. Do not erase the cache or knowledge store merely to obtain a passing result.

Rerun the selected flow after an evidence-based correction. Stop and report an unchanged failure when no new corrective action is justified. Report the command, run ID, verdict, relevant evidence/report paths, and what remains unverified; redact credentials and sensitive application data.

## Example

Input: "Validate checkout and inspect the recorded run without executing the application."

```text
Fixture observations:
- YAML validation succeeds and dry-run selection lists one checkout test.
- The failed-run list is empty.
- The selected run has no completed verdict; knowledge reports evidence-incomplete.

Expected output:
Structure and selection checks passed. The selected run is unresolved because
its evidence is incomplete. Application behavior has not been verified.
```

## Acceptance criteria

- Identify the selected test and target, executed commands, exit status, and relevant run ID.
- Link available evidence and report paths; distinguish validation from application execution and a passed verdict from a healed one.
- State any unresolved setup, incomplete evidence, or unexecuted checks without claiming success.

## Edge cases

- Missing configuration, required files, or provider/device access: report the setup gap before execution.
- No matching tests: inspect the selection; do not silently expand to all tests.
- Empty failed-run list or missing verdict: inspect the relevant run and report uncertainty.

## References and licensing

- [CLI commands and exit codes](https://vostride.com/docs/agent-qa/cli)
- [Inspect and correct memory](https://vostride.com/docs/agent-qa/memory/inspect)
- [agent-qa repository](https://github.com/vostride/agent-qa)

These original skill instructions use this repository's MIT license. The separately installed agent-qa package is licensed under FSL-1.1-ALv2; model, browser, and device providers have their own requirements and costs.
