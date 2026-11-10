---
name: write-feature-docs
description: Draft a complete documentation page for a new Warp feature from its PRODUCT.md and/or TECH.md spec. Use when an engineer has written a spec and needs to produce a first-pass MDX draft for the warpdotdev/docs repo. Also handles features without specs by researching the codebase first. Invoke this skill whenever an engineer mentions writing docs for a feature, drafting a docs page, creating feature documentation, starting the eng-docs workflow, or converting a spec into documentation. Requires an interactive session with the engineer present - it confirms a content design plan, then an outline, before drafting, and cannot run unattended. For automated, release-triggered docs, use the missing_docs skill in warpdotdev/docs instead. Works from warp-internal or warp-server.
---

# write-feature-docs

Draft a complete documentation page for a new Warp feature. You read the feature's spec, verify technical claims by researching the codebase yourself, confirm the content design plan and then the outline with the engineer, and only then produce a complete MDX draft and open a draft PR in `warpdotdev/docs` — tagging the docs team for review.

The engineer's job is to confirm what you couldn't verify from the spec and code — not to do a full accuracy review, not to polish prose, not to know docs conventions.

## Load the docs checkout's guidance

Before planning or drafting, locate or obtain a clean `warpdotdev/docs` checkout and read its `AGENTS.md`, `.agents/rules/warp-positioning.md`, `.agents/references/terminology.md`, `.agents/references/doc-quality-policy.md`, and `.agents/skills/draft_docs/SKILL.md`. Use a separate worktree for the docs task rather than switching a checkout with in-progress work. Read `.agents/references/writing-examples.md` when drafting explanatory copy, and the selected content-type skill and template before writing the page.

Use those versioned sources for positioning, voice, names, evidence, and delivery requirements instead of a remembered or installed summary. If a required source is missing, pause dependent drafting and report the gap. Do not substitute the unmaintained Notion Dictionary or an old positioning filename.

Apply the docs checkout's verification and rollout checks to technical claims. A spec establishes intent, not shipped behavior. Keep the interactive confirmations below; canonical guidance does not remove them.

## The workflow

1. Find and read the spec files
2. Research the codebase to verify technical claims — minimize what the engineer needs to check
3. Present the content design plan and wait for confirmation — who the page is for
4. Present the outline and wait for confirmation — what the page will contain
5. Generate the complete MDX draft
5.5. Attempt screenshot capture via computer use (if available)
6. Open a draft PR in `warpdotdev/docs` and tag the docs team

Steps 3 and 4 are **two separate confirmations, in that order.** The outline is derived from the plan — the plan picks the content type, and the content type determines what sections the outline has. Presenting them together would show the engineer an outline built on an audience they have not agreed to yet, and they would anchor on the concrete outline instead of reconsidering the question above it. Settle who the page is for, then decide what goes in it.

---

## Step 1: Find and read the spec

Ask the engineer for the spec ID if they haven't provided it. The spec ID is one of:
- A Linear ticket number: `APP-1234`, `REMOTE-1234`, `QUALITY-408`
- A GitHub issue (prefixed with `gh-`): `gh-4567`
- A short kebab-case feature name: `vertical-tabs-hover-sidecar`

Look for the spec files at:
- `specs/<id>/PRODUCT.md` — primary source: user-facing behavior, what and why
- `specs/<id>/TECH.md` — secondary source: implementation, data model

Read both files if both exist. `PRODUCT.md` is the primary driver for the docs content.

**When reading `TECH.md`:** Before incorporating anything from it, identify content that looks like internal implementation detail — database schema, internal service names, private API endpoints, confidential server architecture. Present these flagged items to the engineer and ask them to confirm what's safe to include in public docs and what should stay internal. Do not include anything marked confidential in the draft.

This confirmation is why the skill requires a present engineer. There is no unattended path: without someone to say what is safe to publish, `TECH.md` content cannot be drafted at all.

If neither file exists, skip to [No-spec fallback](#no-spec-fallback).

---

## Step 2: Research the codebase

Before presenting the plan or the outline, use the GitHub CLI to verify as much technical content as possible yourself — reducing what the engineer needs to confirm to only what you genuinely cannot determine from the code.

Things to verify from code:
- **Feature flag name**: search for a safe feature token from the spec title or ticket. Before any shell use, reduce it to an allowlisted token matching `^[A-Za-z0-9][A-Za-z0-9_-]*$` and skip the shell search if you cannot produce one safely; then run `FEATURE_TOKEN="<validated-token>" && gh search code "${FEATURE_TOKEN}" --repo warpdotdev/warp-internal`.
- **UI strings**: search for user-visible button labels, menu item names, or setting names referenced in the spec
- **Settings paths**: confirm exact Settings menu paths (e.g., `**Settings** > **AI** > **Knowledge**`)
- **CLI commands or keyboard shortcuts** mentioned in the spec
- **Related features**: identify other features that cross-reference this one for "Related pages"
- **Engineer to tag**: identify the GitHub handle of the engineer who owns the spec.
  - *Interactive mode*: run `gh api user --jq .login` to get the handle of the person currently running the skill — use this only when the skill is being invoked directly by the spec engineer. If a docs team member or non-author is running the skill, use the discovery steps below instead.
  - *Non-author runs (a docs team member or anyone who did not write the spec)*: before running any lookup commands, validate that the spec ID contains only alphanumeric characters and hyphens (matching `^[A-Za-z0-9][A-Za-z0-9-]*$`). If the spec ID contains any other characters, skip the lookup entirely and use `[TODO: tag spec author]` as a placeholder. If the spec ID is valid, assign it to `SPEC_ID` and work through these steps in order, stopping as soon as a handle is found:
    1. **Check `Co-authored-by:` trailers in the commit message** — in repos that mirror from a private source (like `warp-internal`), the sync bot is the commit author but the real author appears in a `Co-authored-by:` trailer. Extract the first non-bot entry:
       ```bash
       git log --follow -1 --format="%B" -- "specs/${SPEC_ID}/PRODUCT.md" \
         | grep -i "^Co-authored-by:" \
         | grep -v "\[bot\]" \
         | head -1 \
         | grep -oP '<[^>]+>' | tr -d '<>'
       ```
       This returns an email (possibly a GitHub noreply address). If the email matches the pattern `<userid>+<username>@users.noreply.github.com`, extract the handle directly: `echo "$EMAIL" | grep -oP '\+\K[^@]+'`. If it's a real email, resolve it via `gh api "search/users?q=${EMAIL}+in:email" --jq '.items[0].login'`.
    2. **Parse the synced-from PR URL** — some sync bots embed the original PR URL in the commit body (e.g. `Synced from warp: https://github.com/warpdotdev/warp/pull/11901`). Extract it and fetch the PR author:
       ```bash
       ORIG_PR=$(git log --follow -1 --format="%B" -- "specs/${SPEC_ID}/PRODUCT.md" \
         | grep -oP 'https://github\.com/[^/]+/[^/]+/pull/\d+' | head -1)
       # Extract owner/repo and PR number, then: gh pr view <N> --repo <owner/repo> --json author --jq '.author.login'
       ```
    3. **Search the origin repo PRs** — try the repo that actually owns the code (checking both the public mirror and the private source if accessible):
       ```bash
       gh pr list --search "specs/${SPEC_ID}" --repo warpdotdev/warp-internal --state merged --json author --limit 1 --jq '.[0].author.login'
       # Also try: gh pr list --search "specs/${SPEC_ID}" --repo warpdotdev/warp --state merged --json author --limit 1 --jq '.[0].author.login'
       ```
       Skip any result where the login contains `[bot]`.
    4. **Fall back to commit author email** — only if the email does NOT contain `[bot]`:
       ```bash
       EMAIL=$(git log --follow -1 --pretty=format:"%ae" -- "specs/${SPEC_ID}/PRODUCT.md")
       ```
       If `${EMAIL}` is non-empty and bot-free, resolve it to a handle via `gh api "search/users?q=${EMAIL}+in:email" --jq '.items[0].login'`.
    5. If no handle is found after all steps, use `[TODO: tag spec author]` as a placeholder in the PR body.

For each claim you verify from code, mark it confirmed. For claims you can't verify (UI behavior not in code, product intent, behavior of unreleased features), flag them as `[UNVERIFIED]` in the outline — those are the only things the engineer needs to focus on.

---

## Step 3: Present the content design plan and wait

**This is the first of two confirmations, and it comes before the outline.** Settle who the page is for before deciding what goes in it.

Fill in `.agents/templates/content-design-plan.md` from the docs repo, using `.agents/references/content-design-plan.md` for what each field is asking: audience and JTBD, problem, goals, purpose and value, content type, skill and template, and high-impact scenarios with explicit exclusions.

Print it to the terminal, then say:

> "Before I outline the page, please confirm this is the right reader and the right job. Correct anything that's off, or say 'looks good' and I'll draft the outline."

**Wait for the engineer's reply.** Do not produce the outline in the same message. The plan decides the content type, and the content type decides what sections the outline has — an outline shown alongside an unconfirmed plan invites the engineer to anchor on the concrete sections in front of them rather than question the audience above them.

If they change the audience, the content type, or the scope, revise the plan and re-confirm before moving on. Carry the confirmed plan into the PR body in Step 6.

---

## Step 4: Present the outline and wait

Generate a concise outline — no prose — built on the **confirmed** plan from Step 3. The outline shows what you've confirmed from research and exactly what still needs engineer input.

Print the outline to the terminal in this format:

```
📄 Docs outline for [Feature name]

PROPOSED PLACEMENT
  Section:  src/content/docs/<section>/   (e.g., agent-platform/cloud-agents/)
  File:     <feature-name>.mdx
  URL:      docs.warp.dev/<path>/<feature-name>

CONTENT SECTIONS
  title:  <Feature name>   (frontmatter; Starlight renders it as the H1)
  Opening paragraph: [1-sentence description of what you'll write]
  ## Key features — [which 2-4 capabilities to highlight as bullets]
  ## How it works — [the conceptual model: what and why, no steps]
  ## <Usage section title> — [e.g., "Creating environments", "Configuring X"]
      Prerequisites: [any prerequisites to list]
      Steps:
        1. [Step description]
        2. [Step description]
        3. [Step description]
        ...
  ## Related pages — [cross-links to suggest]
```

> The sections above are defaults. Adapt the outline to the feature: omit `## How it works` if the feature needs no conceptual explanation, add multiple usage sections if the feature has distinct workflows, and collapse `## Key features` into the opening paragraph if the feature is simple enough.

```
VERIFIED FROM CODEBASE ✅
  - [e.g., "Feature flag: `my_feature_flag` confirmed in warp-internal"]
  - [e.g., "Settings path: confirmed as Settings > AI > Agents > Permissions"]

NEEDS YOUR CONFIRMATION ⚠️
  - [e.g., "Step 3 — does the sync trigger automatically or require a manual action?"]
  - [e.g., "Is the 'Export' button visible before the feature flag is enabled?"]
```

After printing the outline, say:

> "I've verified what I could from the codebase. Please check the items marked ⚠️ above and reply with any corrections, or say 'looks good' to proceed."

Wait for the engineer's reply before continuing. Incorporate their feedback, then draft.

If their feedback contradicts the plan confirmed in Step 3 — a different reader, a different content type — revise the plan too rather than letting the two drift apart. The plan travels into the PR body, so a stale one misleads the reviewer.

---

## Step 5: Generate the MDX draft

Generate a complete `.mdx` file based on the confirmed outline. The output is ready to drop directly into `warpdotdev/docs`.

### Template structure

**Use the canonical template for the content type the plan chose**, from `.agents/templates/` in the docs repo — `feature-doc.md`, `conceptual.md`, `procedural.md`, `reference.md`, `troubleshooting.md`, `quickstart.md`, or `guide-page.md`. Those are the source of truth and they carry their own field-by-field guidance. The sketch below shows the shape of the most common one, feature documentation, so you know what to expect; it is not a substitute for reading the real template.

Two rules the templates enforce that are easy to get wrong from memory: the page title goes in **frontmatter**, not a body H1 (Starlight renders the frontmatter title as the H1, so a body H1 duplicates it), and every bracketed instruction must be deleted before the page ships.

```mdx
---
title: [Feature name — sentence case]
description: >-
  [1-2 sentence standalone summary. Lead with the user benefit. Include the
  feature name and a key term or two so it works as a search result snippet.]
---

[Opening paragraph: what the feature does and its primary benefit.
1-3 sentences. Lead with what the user can accomplish, not the implementation.]

:::note
[Optional: key context the reader needs upfront — a prerequisite, a limitation,
or when NOT to use this feature. Delete this callout if nothing applies.]
:::

## Key features

* **Feature A** - What it does and why it matters to the user.
* **Feature B** - What it does and why it matters to the user.

## How it works

[CONCEPTUAL section: explain system behavior, data flow, or architecture.
Answer "what" and "why" before "how." Define any new terms when they
first appear. Do NOT include step-by-step procedures in this section —
keep conceptual and procedural content clearly separated.]

## [Usage section title]

[PROCEDURAL section: motivate the task first, then give numbered steps.
Briefly explain why the user is doing this before telling them how.]

### Prerequisites

* **[Prerequisite]** - What it is and where to get it. See [full reference](link-here).

### [Task name — sentence case, e.g., "Create an environment with the CLI"]

1. First step. Expected outcome if not obvious.
2. Second step.
3. Third step.

## Related pages

* [Related feature](../path/to/page.md)
* [Deeper guide](../path/to/guide.md)
```

### Style rules — apply exactly

Apply the target docs checkout's `AGENTS.md` and selected drafting skill to headings, lists, UI labels, descriptions, variables, callouts, and voice. Check the opening and metadata against `.agents/rules/warp-positioning.md`, then verify names against `.agents/references/terminology.md`. Do not define Warp Factories or a customer's factory as a team of agents; keep literal shipped role names.

Run the selected drafting skill's validation before delivery, including the applicable build, style, technical-reference, and PR-contract checks. Record skipped or unavailable checks as such, not passes.

**What to leave as `[TODO: docs reviewer — ...]` placeholders**
- Screenshots where computer use fails the quality gate, is unavailable, or the feature isn't yet shipped
- Video/GIF embeds
- Exact Settings path if the feature hasn't shipped yet
- Final URL path (docs team confirms placement)
- Any behavior that remained unverified after engineer confirmation

---

## Step 5.5: Capture screenshots via computer use (if available)

After generating the draft, attempt to capture screenshots for any `[TODO: docs reviewer — screenshot needed]` placeholders using computer use. This step is **optional** — only run it if the `computer_use` tool is available. If computer use is unavailable, leave all placeholders as-is.

### Decide which screenshots to attempt

Only attempt screenshots where **all** of the following are true:
- The feature is already shipped (not behind a feature flag or unreleased)
- The UI state can be reliably navigated to programmatically
- The placeholder specifies a concrete UI surface (not vague like "show the feature working")

Skip screenshots that require account-specific state, specific data, or content that would expose sensitive information.

### Pre-capture setup

Before taking any screenshot:
1. Launch Warp at a consistent window size (use the `warp-internal-computer-use` skill for launch guidance)
2. Navigate to the relevant UI surface or trigger the relevant feature state
3. **Wait** for all animations to complete and the UI to be fully settled
4. Dismiss any unrelated popups, notifications, or toasts that aren't part of the feature being documented
5. Close any sidebar panels or panes not relevant to this screenshot
6. **Verify no sensitive data is visible**: check for tokens, API keys, private repo names, customer workspace data, email addresses, or personal information. If any is visible, do not take the screenshot.

### Capture protocol: predict → capture → verify → retry once

This is a structured self-verification loop. Do not skip it — it's the primary guard against wrong-state, wrong-crop, and wrong-framing captures.

**Step 1: State the expectation before capturing**

Before taking any screenshot, write out what you expect to see:

```
CAPTURE EXPECTATION
  Subject:            [The specific UI element or surface being documented]
  Expected elements:  [2-3 specific things that MUST be visible — e.g. a panel title, a button, a specific setting]
  Expected state:     [The UI state — e.g. "Settings panel open", "Modal visible", "Feature active and showing output"]
  Must not contain:   [Anything that must NOT be visible — e.g. sensitive data, unrelated popups, loading spinners]
```

**Step 2: Capture**

Take the screenshot.

**Step 3: View and verify against the expectation**

Use computer use to view the captured image, then check it against the expectation:

- Is the stated **subject** visible and clearly the focal point?
- Are all **expected elements** present?
- Is the UI in the **expected state** (not a transitional or loading state)?
- Is anything from **must not contain** visible?
- Is text **legible** at the target display width?

If all pass → proceed to the quality gate.

If any fail → **attempt once more**: re-navigate to the UI state, wait longer for the UI to settle, then re-capture and re-verify.

If the second attempt also fails → **discard** the screenshot and leave the `[TODO: docs reviewer — screenshot]` placeholder. Do not include a screenshot you can't verify.

**Step 4: Quality gate — final check before including**

- [ ] Text in the screenshot is **legible** at the target display size
- [ ] The documented UI element is **clearly the focal point** — not buried, cropped out, or obscured
- [ ] **No sensitive data** is visible (tokens, private repos, personal info, customer data)
- [ ] UI is in a **stable, non-loading state** — no spinners, skeleton screens, or transitional states
- [ ] Screenshot **matches the capture expectation** stated before capture
- [ ] The screenshot would make sense at its target rendered width without looking blurry or oversized

If any item fails, discard the screenshot and leave the `[TODO: docs reviewer — screenshot]` placeholder.

> **Maximum attempts per screenshot: 2.** If both fail, move on.

### Sizing — choose the closest standard width

- **Full-width (default)** — full-window captures, broad product surfaces, layouts where surrounding context matters
- **~375px** — narrow UI surfaces: popovers, command menus, side panes, dropdowns, focused interaction flows
- **~300–350px** — tightly cropped controls, chips, buttons, tooltips, small menus

Crop unnecessary empty space before sizing. Keep sequences of screenshots in the same section at the same width.

### Placement — where to insert the screenshot in the MDX

Insert each screenshot:
- **Immediately after** the paragraph that introduces the UI or state it shows
- **Near configuration instructions** — show settings panels or menus where users make choices
- **Near status or result explanations** — show completion states or outputs that help users recognize success
- **At the start of a visual feature page** — use a broad orientation screenshot early

Do **not** add a screenshot for every step in a procedure. Only add one where the visual genuinely aids comprehension.

### MDX format

```mdx
<figure>
  <img
    src="[relative path from this MDX file to src/assets/<section>/<feature-name>-<ui-state>.png — count the directory depth of the MDX file and use that many ../ levels; e.g. 3 levels deep → ../../../assets/<section>/...]"
    alt="[Descriptive alt text: what the image shows, not just 'screenshot']"
  />
  <figcaption>[Caption: complete sentence, ≤10 words, orient don’t instruct, no marketing language, sentence case, ends with period.]</figcaption>
</figure>
```

**Alt text rules:**
- Describe what the image shows, not just "screenshot"
- ✅ `alt="Agent permissions settings with 'Always allow' selected for file reads"`
- ❌ `alt="screenshot"` or `alt=""`

**Caption rules:**
- Orient the reader — describe what is shown, not what to do
- Complete sentence, ≤10 words ideally, never exceed ~20 words
- No marketing language (avoid "easily," "quickly," "powerful," "at a glance")
- Don't repeat the prose — the caption adds context, not an echo
- Don't list everything visible — name the subject
- ✅ `<figcaption>The Environments page in the Oz web app.</figcaption>`
- ❌ `<figcaption>Click the toast to jump to the agent’s session.</figcaption>` (procedural — put this in body text)

**File naming:** lowercase, hyphens, descriptive — e.g. `agent-mode-permissions-panel.png`

**File location:** Save PNGs to `src/assets/<section>/` in `warpdotdev/docs` (Astro optimizes them automatically).

---

## Step 6: Open the draft PR

**Before opening the PR, confirm the docs repo's own requirements are met.** `warpdotdev/docs` gates incoming pages on two things, and a PR that skips them will be sent back:

1. **Gate 0 of `.agents/references/docs-worthiness-criteria.md`** in the docs repo: is the feature shipped and GA, on a public surface? If not, do not open a PR — tell the engineer why and stop. This is worth checking even though the engineer asked for the page, because drafting for something that has not shipped yet is the most common failure, and an engineer close to the work can easily be a release ahead of their users.

   The remaining gates in that reference are judgment calls about whether a change warrants docs. They govern the automated pipeline, not you — an engineer asking for docs on their own shipped feature has context the gate cannot see. Do not decline on those grounds.
2. **The content design plan** the engineer confirmed in Step 3, included in the PR body as a `## Content design plan` section.

Prefer updating an existing page over creating a new one whenever a page already covers the surface.

After generating the draft, submit it to `warpdotdev/docs`:

1. Clone `warpdotdev/docs` to a temp directory (or use the local clone if available)
2. Write the MDX file to `src/content/docs/<proposed-section>/<filename>.mdx`
3. Add a placeholder entry to `src/sidebar.ts` under the appropriate section. Example:
   ```ts
   // [TODO: docs reviewer — confirm placement]
   { label: '<Feature name>', link: '/<section>/<feature-name>/' },
   ```
4. Commit and push on a new branch named `docs/<spec-id>-feature-draft`
5. **Write the PR body to a temp file, then open a draft PR with `--body-file`**. The PR description must include:
   - The feature name and spec ID
   - A link to the original spec PR
   - A list of all `[UNVERIFIED]` and `[TODO]` items in the draft for reviewer attention

   Write the body to `/tmp/pr-body.md` using whatever file-writing method is available (a file-creation tool, a Python `open()` call, or a shell `cat` with a quoted heredoc), then pass it to `gh`:
   ```bash
   gh pr create --draft --body-file /tmp/pr-body.md ...
   ```

   **Never pass the PR body inline** (via `--body "..."`, `echo`, or `printf` piped directly to `gh`). Shell string interpolation expands backticks, `$vars`, and `[ ]` glob patterns before the string reaches `gh`, corrupting any markdown that contains those characters. Writing to a file first avoids all shell interpretation of the content.

   **In the "Docs outline" section of the PR body, use plain bullet points** (`-`) for agent-verified items, not `- [x]` checkboxes. Reserve `- [ ]` checkboxes only for the "Items needing review" section so reviewers know exactly which items require their action.

6. In the PR body, notify the spec author using the handle from Step 2:
   - If a valid GitHub handle was found: include `/cc @<engineer-handle>`
   - If the fallback placeholder was produced: include the literal text `[TODO: tag spec author]` — do not wrap it in `/cc @`, as that would produce a malformed mention
   Request review from `@rachaelrenk` and `@hongyi-chen`.

---

## No-spec fallback

If `specs/<id>/PRODUCT.md` and `specs/<id>/TECH.md` don't exist, research the codebase first before interviewing the engineer.

**Research steps:**
1. Search `warpdotdev/warp-internal` (or `warp-server` depending on context) for the feature name and related terms: `gh search code "<feature-name>" --repo warpdotdev/warp-internal`
2. Read the most relevant source files to understand what the feature does
3. Check for spec files under a different ID: `gh api repos/warpdotdev/warp-internal/contents/specs`
4. Review recent merged PRs related to the feature: `gh pr list --search "<feature-name>" --state merged --repo warpdotdev/warp-internal --limit 10`

**After research,** build as complete a picture as possible, then use `ask_user_question` only for specific gaps you couldn't fill from the code — not as a broad interview. Frame the questions concretely: "I found the feature in `app/src/ai/`. Based on the code, here's what I understand: [summary]. I couldn't determine these two things: [specific questions]."

Build the plan and outline from your research and the engineer's targeted answers, then work through Step 3 (plan confirmation) and Step 4 (outline confirmation) before drafting.

---

## Interactive only — there is no unattended mode

This skill previously had an "ambient mode" that let `scan-new-specs` drive it headlessly, skipping the confirmations in Steps 3 and 4 and embedding the outline in the PR description as a checklist instead. **That mode is removed, and `scan-new-specs` is retired.**

It produced draft PRs for features that had not shipped, because a merged spec is not a shipped feature and no unattended run could tell the difference. Skipping outline confirmation also removed the one checkpoint where a human could redirect the draft before the prose was written.

Do not re-add an unattended path here:

- **For automated, release-triggered docs**, use `missing_docs` in the `warpdotdev/docs` repo. It gates every candidate on `.agents/references/docs-worthiness-criteria.md` before drafting and only runs when a new stable release has shipped.
- **For an engineer who wants docs for their feature**, this skill is the right tool — invoked directly, with the engineer present to confirm the outline and the `TECH.md` boundary.

If you are running without an interactive session, stop and report that this skill requires one, rather than drafting anyway.

---

## Related skills

- `write-product-spec` — produces the `PRODUCT.md` this skill reads
- `write-tech-spec` — produces the `TECH.md` this skill reads
- `missing_docs` (in `warpdotdev/docs`) — the release-triggered, worthiness-gated pipeline for docs on newly shipped features
- `scan-new-specs` — retired; see its deprecation notice
