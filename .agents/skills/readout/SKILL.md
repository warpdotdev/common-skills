---
name: readout
description: Produce a polished, self-contained HTML "readout" document under ~/.readouts (with an auto-maintained index page) and optionally publish it to Vercel after explicit user consent. Works by snapshotting the current conversation or researching a fresh question in the codebase, using a child agent so the main conversation stays clean. Use whenever the user invokes /readout, says "write this up", "turn this into a doc/page", "make a readout", or asks for a readable, shareable document capturing findings or explaining how something works.
---

# Readout

A readout turns an investigation into a durable HTML document someone can read weeks later without any of the original context. It starts one of two ways:

- **Snapshot mode** — invoked mid-conversation ("write this up"): the conversation's accumulated findings are the source material.
- **Research mode** — invoked fresh ("/readout on how github webhook events are processed in the server"): there is no conversation to mine, so the investigation itself is part of the job.

Either way, invoking this skill is a **side task**. Your job as the main agent is to sharpen the scope, launch a child agent with a good brief, and get out of the way — the child does the mining/research and the writing, keeping that (often large) work out of your context window.

## Orchestrator workflow

### 1. Sharpen the scope — ask before launching

A vague brief produces a vague document. Before launching you should be able to list the specific questions the document will answer; if you can't, interview the user first:

- Ask 2–4 targeted questions, offering concrete options rather than open prompts — take a quick look at the code or topic first so the options are real (subsystems, entry points, competing concerns). For "/readout on how github webhook events are processed": which direction matters — inbound triggers, post-back, or both? a current-state reference or a gotcha hunt? which repo(s)?
- Always pin down **depth and audience**: high-level orientation vs. deep mechanics with line-level grounding; personal notes vs. shared with the team.
- Always pin down **deployment**: local HTML only, or publish publicly with Vercel. Recommend local-only. Never infer consent to publish from words like "shareable" or "for my team."
- If offering public deployment, say plainly that the generated HTML and its embedded source snippets will be visible to anyone on the internet, and that Vercel Authentication will be disabled for a dedicated readouts project so all current and future deployments in that project are public.
- After the user selects public Vercel, run `python3 <skill-directory>/scripts/list_vercel_scopes.py`. Present its `scopes` as concrete choices and ask which account/team should own the deployment. Do not guess from the active team or hardcode an organization.
- Only record `public Vercel (explicitly approved)` after the user approves both public content and disabling protection for the dedicated project, and chooses a scope.
- Respect a shrug. "Just a high-level overview" is a valid answer — record it in the brief and move on rather than interrogating. Even then, try to extract the two or three questions the reader most needs answered; specificity is what makes a readout useful.
- Skip the interview when the scope is already specific — a snapshot of a focused conversation, or a precise research request, needs no questions. In snapshot mode the conversation usually supplies the questions; ask only when the invocation is ambiguous about which threads to include.

### 2. Compose the brief

Write a short brief (roughly 10–20 lines) carrying **pointers, not payloads**:

- A working title / topic, and the mode (snapshot or research)
- The specific questions the document must answer (from the conversation or the interview), plus depth and audience
- Scope: which threads/subsystems to cover, and anything to explicitly exclude
- Deployment: `local only` or `public Vercel (explicitly approved)`
- For public Vercel: the exact selected scope slug and, only if requested, a non-default project name
- Snapshot mode: headline conclusions worth centering the doc on, one line each — the child pulls the full content from conversation history itself, so don't paste findings wholesale
- Research mode: starting pointers — entry-point files, symbols, or directories you already know about
- Absolute paths to the repos/directories that ground the work
- Each repo's hosted URL and the examined commit when known (e.g. `github.com/org/repo @ abc123`), so the document can hyperlink code references

### 3. Launch one local child agent

Spawn exactly one child agent via `run_agents`, **local** execution. Local matters: the document lands on the user's filesystem and opens in their browser. Name the child `readout-<topic-slug>`.

Build the child's prompt from the template below. It must include:

- The brief
- The source-material block matching the mode (snapshot mode also needs your agent run ID — `current_run_id` from the orchestration runtime context — so the child can mine the parent conversation with `search_conversation_history`)
- The instruction to read `references/doc-guide.md` from this skill's directory before writing
- The output path convention, deployment choice, and completion protocol

### 4. Publish only when explicitly approved

Local-only is the default. If the brief says `public Vercel (explicitly approved)`, the child publishes the finished file with:
`python3 <skill-directory>/scripts/publish_vercel.py <doc.html> --scope <approved-scope> --confirm-public --confirm-disable-protection --json`

The helper:

- Requires an installed and authenticated Vercel CLI.
- Requires an explicit account/team scope returned by `list_vercel_scopes.py`; it has no organization-specific default.
- Defaults to a collision-resistant `readouts-<vercel-user>` project within that scope.
- Uses the Vercel API to distinguish a missing project from authentication, permission, and network errors.
- Creates or links the project non-interactively, records a local managed-project marker, adds only explicitly selected readouts, and regenerates the public index.
- Refuses to change protection on an existing unmarked project. `--allow-existing-project` is allowed only after the user separately confirms that the named project is dedicated to readouts and contains no unrelated deployments.
- Disables Vercel Authentication only for the managed project; it does not change scope defaults or other projects.
- Resolves the production alias instead of returning Vercel's often-protected immutable deployment URL.
- Runs `verify_public_url.py` anonymously and reports success only after HTTP 200 and an exact `<title>` match.

Before invoking it, inspect the generated document for credentials, tokens, private customer data, or source that should not be public. Embedded snippets are part of the HTML and become public too. If anything looks sensitive or the user's consent is absent or ambiguous, do not publish; return the local file and explain the blocker.

### 5. Get back to work

After launching, resume whatever you were doing, or end your turn — the child's completion message arrives on its own; relay the local file path and, when approved and successfully published, the public URL with a one-line description. In research mode a fresh conversation may have nothing else pending; just end the turn. Don't sit in a wait loop unless the user asked to wait for the document.

## Child agent prompt template

Adapt this; keep the structure, and include the source-material block that matches the mode.

```
You are producing a "readout": a single self-contained HTML document that answers a
specific set of questions about <topic>, for a reader who has none of this context.

Brief:
<brief — including the questions to answer, depth, and audience>

Source material (snapshot mode):
- The parent conversation: agent run ID <current_run_id>. Use search_conversation_history
  with agent_run_id set to that ID. Make several targeted queries — one per question in
  the brief — rather than one broad query; targeted queries surface far more usable detail.
- The codebase(s) at <absolute paths>. The conversation is your starting point, not a cage:
  verify file references before asserting them, and where a section needs more depth to
  stand on its own, go read the code and fill the gap.

Source material (research mode):
- Investigate directly in the codebase(s) at <absolute paths>. Let the brief's questions
  drive the investigation: trace the actual code paths, read the real implementations, and
  ground every claim in file:line references. Distinguish verified from inferred. Do not
  pad the document with generic knowledge — its value is what's true of THIS codebase.

- Repo host + commit for linked code references, if known: <github.com/org/repo @ commit>
  (otherwise derive from git; see the doc guide's "Linked code references").

Start from the canonical template at <skill-directory>/assets/template.html — its
data-readout chrome blocks must be copied verbatim so every readout looks like every
other. Before writing, read <skill-directory>/references/doc-guide.md and follow it.

Output:
- Write ONE self-contained HTML file to ~/.readouts/<YYYY-MM-DD>-<topic-slug>.html
  (create ~/.readouts if it doesn't exist; suffix -2, -3, ... if the name is taken;
  get the date from `date +%F`).
- Embed referenced source per the doc guide when a repo is checked out
  (<skill-directory>/scripts/embed_snippets.py).
- Refresh the readouts index: python3 <skill-directory>/scripts/update_index.py
  (fully regenerates ~/.readouts/index.html listing every readout).
- When the file is written, open it with `open <path>` (skip this if the environment is
  headless).
- Deployment: <local only | public Vercel (explicitly approved)>.
  Vercel scope: <exact approved scope slug; required for public deployment>.
  For local only, do not publish. For explicitly approved public deployment, first inspect
  the final HTML for secrets and private data, then run:
  python3 <skill-directory>/scripts/publish_vercel.py <doc.html>
    --scope <approved-scope> --confirm-public --confirm-disable-protection --json
  Add --project <project-name> only if the brief names a non-default project. Never add
  --allow-existing-project unless the brief records the user's separate approval to adopt
  that exact existing project.
- Report back to your orchestrator: the absolute file path, the public URL if deployed, a
  2–3 sentence summary of what the document covers, the anonymous verification result,
  and anything you could not verify.
```

## Fallbacks

- **Child spawning unavailable or denied**: produce the document yourself, following `references/doc-guide.md`. If a research subagent is available, delegate the conversation-mining or code investigation to it so your context still stays lean.
- **Child can't search conversation history** (snapshot mode; it will report this back): reply to the child with a distilled dump of the findings so it can proceed — this is the one case where payload-in-prompt is the right call.
- **User-provided material instead of a conversation** (transcripts, files, links): treat that material as the source; everything else in the workflow is unchanged.
- **Public deployment fails**: keep the local artifact, report the exact deployment or verification error, and do not substitute another hosting provider, return an unverified URL, adopt an existing project, or change deployment visibility without fresh user consent.
