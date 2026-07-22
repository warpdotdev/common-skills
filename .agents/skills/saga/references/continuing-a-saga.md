# Continuing a saga

Use this when asked to continue, resume, or pick up a saga — typically a fresh orchestrator with no memory of the earlier session. Everything you need is on disk in the saga directory; the specs are the contract and `PROGRESS.md` is the current state. Your job is to reconstruct where the saga stands, reconcile it against reality, and resume the Phase 2/3 loop from `SKILL.md` — without re-reading the whole tree into context.

## 1. Locate the saga directory

Find the saga under `~/.sagas/`. If the user named it or gave a path, use that. Otherwise `ls ~/.sagas/` and, if ambiguous, ask the user which one with structured options listing the candidates. The directory name is the saga's stable identity.

## 2. Rebuild orientation cheaply

Read, in this order, and stop once you know the next action:

1. `SAGA.md` — problem statement, environment/capabilities, saga exit criteria, milestone index, and `Status`.
2. `PROGRESS.md` — `Phase`, `Current milestone`, per-task status, worker run IDs for any in-progress tasks, integration notes, open questions, and the recent log.

Do **not** bulk-read every `MILESTONE.md` and task spec. Open only the spec(s) for the milestone you're about to act on. This is the same context discipline the orchestrator uses normally.

## 3. Reconcile the log against reality

`PROGRESS.md` can be stale if the previous session was interrupted. Before trusting it, verify the actual state for anything not clearly settled:

- Check git: do the branches/worktrees referenced for `done`/`in progress` tasks exist? Were they merged? All saga branches follow the convention `saga/<saga-name>/m<M>t<T>-<task-slug>` (possibly behind a team/user branch prefix), so you can enumerate them with `git branch --list '*saga/<saga-name>/*'` even without reading `PROGRESS.md`.
- For tasks marked `done`, spot-check the evidence still holds — re-run the task's validation if there's any doubt that it landed. A task is only really done when its criteria pass against the current integrated code.
- For tasks marked `in progress`, use the recorded `worker_run_id` to decide whether the prior worker is still reachable. Do not rely on a display name alone; if there is no addressable run ID, or the agent is no longer reachable, treat the task as not started and re-delegate from its spec.

Update `PROGRESS.md` to match reality before proceeding, noting the reconciliation in the log.

## 4. Determine the next action and resume

From the reconciled state:

- If milestones remain, resume the **Phase 2 orchestration loop** at the current milestone: launch the next batch of pending/blocked tasks (workers in isolated worktrees), collect reports, integrate, run milestone-level validation, and advance. Follow `SKILL.md` Phase 2.
- If all milestones are integrated and validated, move to **Phase 3 final validation**: check the saga exit criteria and loop the user in for manual acceptance.
- If a blocker or open question recorded in `PROGRESS.md` needs the user, resolve it first with structured options.

## 5. Keep the contract intact

You are bound by the same specs and validation criteria as the original orchestrator. Don't silently re-scope. If resuming reveals the spec is wrong or a task's criteria are unachievable, update the relevant spec file (and note it under "Decisions & deviations" in `PROGRESS.md`), and escalate to the user if it changes agreed behavior or the saga exit criteria.

## Quick checklist

- [ ] Found and confirmed the saga directory.
- [ ] Read `SAGA.md` + `PROGRESS.md`; know phase, current milestone, and next action.
- [ ] Reconciled branches/worktrees/evidence with git; fixed `PROGRESS.md`.
- [ ] Resumed the correct phase loop from `SKILL.md`.
- [ ] Kept specs and `PROGRESS.md` current as work proceeds.
