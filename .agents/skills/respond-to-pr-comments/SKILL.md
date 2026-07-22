---
name: respond-to-pr-comments
description: Walk users through PR review comments, fetching and displaying them first when needed, collect per-comment response decisions, apply requested fixes, and preview GitHub replies and resolutions before posting. Use when responding to PR review comments on the current branch.
---

# Respond to PR comments

Use this skill to respond to PR comments on the current branch. If comments are already visible in the conversation, typically from the bundled `/pr-comments` skill when running inside the Warp terminal, continue from that context. If comments are not already visible, fetch and display them first, then guide the user through each actionable comment, collect an explicit decision, make requested code changes, and only then ask for approval before posting GitHub replies or resolving review threads.

Rendering comments into the Warp block list (via the bundled `/pr-comments` skill and the `insert_code_review_comments` tool) is only available inside the Warp terminal. Outside Warp, fall back to `gh` or plain-text display (see Preconditions); the rest of this workflow is unchanged.

## Preconditions

- Work in the repository checkout for the PR branch.
- Do not refetch comments unless the loaded context is missing essential fields such as comment body, author, URL, path, or line metadata.
- Do not post GitHub replies, submit reviews, or resolve threads until the final preview is approved by the user.

If no PR comments are present in context, fetch and display them before continuing. If you are running inside Warp and the built-in `/pr-comments` workflow is available, prefer invoking it. Otherwise, use the GitHub CLI fallback: identify the current PR, fetch PR-level comments, review comments, and review bodies, then display them. If the `insert_code_review_comments` tool is available, use it to render the comments; otherwise fall back to plain-text or `gh` display. After displaying fetched comments, ask the user whether to continue with this response workflow before making changes.

## Comment filtering

Before asking for response mode, filter the loaded comments down to actionable comments that still need the user's attention.

Skip these comments without asking the user about them:

- Automated PR-level overview or status comments from code-review bots (for example, CI or agent bots), especially comments with no attached file location that summarize review status, check progress, or say no code change is requested.
- Comments that have already been responded to by the current GitHub user.

To identify the current GitHub user, prefer:

```sh
GH_PAGER="" gh api user --jq .login
```

For review threads, use `reply_metadata.parent_comment_id`, thread metadata, resolution state, and comment ordering from the loaded context when available. Skip the original comment and thread only when the thread is already resolved or when the latest relevant reply in that thread was authored by the current GitHub user. If a reviewer added a newer follow-up after the current user's reply, keep the thread in the walkthrough. For PR-level comments without explicit thread metadata, skip only when the loaded context clearly shows a current-user response to that specific comment, such as a direct reply, quote, link, or immediately following response that references it.

If an automated or already-answered comment is skipped, keep a short internal skipped list with the comment URL and reason. Do not create decision records for skipped comments, do not include them in the per-comment walkthrough, and do not include them in the final GitHub reply/resolution preview except as a brief skipped-count summary.

When unsure whether a comment is automated, already answered, or still actionable, keep it in the walkthrough rather than skipping it.

## Structured question requirements

When a structured question tool such as `ask_user_question` is available, use it for mode selection, per-comment decisions, commit/push decisions, and posting approval. Every structured question should include an `Other...` option that uses the tool's freeform other field. Use that option to let the user enter a custom mode, response, rationale, posting instruction, or next step without returning control in normal chat solely to collect custom text.

Outside environments with a structured question tool, ask the same questions in normal chat with the same options and wait for the user's answer before continuing.

## Initial mode selection

Before discussing individual comments, ask exactly one mode question:

- `Respond one-by-one`
- `Collect all decisions, then address in a batch`
- `Other...`

Use the selected mode for the rest of the workflow.

### One-by-one mode

For each comment, collect the user's decision and immediately perform any requested code change before moving to the next comment. After each change, keep a note of:

- the comment being addressed
- what code or documentation changed
- what validation was run or still needs to run
- the draft GitHub reply and whether the thread should be resolved

### Batch mode

For each comment, interactively collect the user's decision without editing code yet. Batch mode does not batch or skip the information-gathering phase: the user must still be able to ask for more context, request an explanation, inspect the referenced code, or provide a custom approach for any individual comment before deciding. After all comments have a decision, apply the requested code changes in one batch, then validate and prepare the final GitHub reply preview.

## Per-comment walkthrough

Process comments in the order they were displayed. For each comment:

1. Restate the relevant context briefly:
   - author
   - file and line or PR-level location
   - a clickable file reference formatted as `path:line` for single-line comments or `path:start-end` for ranged comments when location metadata is available
   - a concise summary of the comment
   - any obvious code context needed to understand it
2. If the fix is not obvious from the loaded context, inspect the relevant files before presenting options.
3. Ask a structured question, when available, with options tailored to the specific comment. Otherwise ask the same options in chat.

When a comment is attached to code, print the file reference before asking the question so the user can quickly open the relevant section. Use repository-relative paths, for example `src/lib.rs:42` or `src/lib.rs:40-48`. For PR-level comments with no file location, state that there is no attached code location.

Always include options with these meanings:

- Apply the agent's recommended fix for this comment.
- Explain what this comment means before deciding.
- Acknowledge the comment but do not make code changes.
- `Other...`

Use the `Other...` option's freeform field for custom responses or approaches. Do not return control to the user in normal chat solely to collect custom freeform text.

When the user selects "explain", provide concise context about the comment, why the reviewer likely raised it, and what tradeoffs are involved. Then ask about the same comment again with updated options; do not skip the decision.

This explanation loop applies in both one-by-one mode and batch mode. In batch mode, only the eventual code edits and GitHub comment updates are deferred; per-comment information gathering remains interactive.

When the user selects "acknowledge without changes", give them the option to provide more information about why no code changes are being made. Preserve any provided rationale for the final GitHub reply draft.

## Decision records

Maintain an internal decision record for every comment. Each record should include:

- comment identifier or URL
- comment type: review-thread comment, thread reply, PR-level comment, or review body
- selected disposition: fix, explain-then-fix, acknowledge-without-changes, custom, or no-action
- planned code change, if any
- validation needed
- draft reply body
- whether to resolve the review thread

For draft replies, be concise and concrete. Prefer replies that say what changed or why the comment is intentionally not addressed. Prefix every draft reply that may be posted to GitHub with a clear agent attribution so reviewers can clearly see the response was agent-authored. If a team-specific `agent-attribution` skill is available, follow it for the exact reply prefix; otherwise use a clear generic prefix such as `[Your Agent]`. If the fix has already been committed and pushed before replies are posted, include a link to the commit that resolved the comment so the response is auditable.

## Applying fixes

Follow the user's selected mode:

- In one-by-one mode, edit and validate each accepted fix before continuing to the next comment.
- In batch mode, wait until all comment decisions are collected, then make all accepted edits together.

When making changes:

- Apply only changes related to the selected PR comments.
- Preserve unrelated local changes.
- Follow repository-specific coding, testing, and style rules.
- Run the narrowest useful validation after each one-by-one fix, and run final validation after all fixes are applied.
- If a requested fix is unsafe, ambiguous, or conflicts with another comment, stop and ask the user before editing.

## Final validation

After all accepted fixes are applied:

1. Review `git diff` to confirm the changes match the collected decisions.
2. Run relevant formatting, linting, typechecking, build, or tests based on the repository's conventions and the files changed.
3. If validation cannot be run, explain why in the final summary and include that caveat in the preview.

Do not commit changes unless the user explicitly asks.

## Commit and push before GitHub responses

After validation and before posting any GitHub replies or resolving review threads, ask whether the user wants to commit the changes and push them to `origin`. This order ensures reviewers see pushed code before they see agent-authored comment responses.

If there are no working tree changes from addressing comments, skip the commit/push question and continue to the GitHub reply preview.

Ask with options like:

- `Commit and push these changes to origin before posting replies`
- `Do not commit or push; continue to the GitHub reply preview`
- `Stop before posting GitHub replies`
- `Other...`

If the user chooses to commit and push:

1. Review `git status` and the final diff so only intended comment-response changes are included.
2. Ask for or propose a concise commit message if one is not already clear; preserve the `Other...` option for custom commit instructions.
3. Stage the intended changes, commit in a non-interactive command, and push the current branch to `origin`.
4. Include your agent's co-author attribution trailer in the commit message. If a team-specific `agent-attribution` skill is available, follow it for the exact trailer.
5. If commit or push fails, stop before posting GitHub replies and report the failure.

## GitHub reply and resolution preview

After the commit/push decision is complete, and before posting anything to GitHub, show a preview grouped by comment. For each comment include:

- comment URL or short identifier
- action: reply only, resolve only, reply and resolve, or no GitHub action
- reply body
- commit link, when a pushed commit exists for the fix
- validation relevant to that comment

Then ask whether to proceed:

- `Post replies and resolve approved threads`
- `Edit the draft responses first`
- `Do not post anything`
- `Other...`

If the user chooses to edit, collect their edits, update the preview, and ask for approval again. Do not post until the user selects the approval option.

## Posting with GitHub CLI

Use the GitHub CLI only after approval. Clear the pager for all `gh` commands.

Before running any GitHub CLI command that posts a reply or PR comment, verify the outgoing body begins with the selected agent attribution prefix. If it does not, add the prefix before posting.

For review comments, post replies with the REST API endpoint. Write the reply body to a temporary JSON file and pass it with `--input` instead of putting the response text directly in command-line arguments:

```sh
REPLY_BODY_FILE="$(mktemp)"
cat > "$REPLY_BODY_FILE"
REPLY_PAYLOAD_FILE="$(mktemp)"
python3 - "$REPLY_BODY_FILE" "$REPLY_PAYLOAD_FILE" <<'PY'
import json
import sys
from pathlib import Path

body_file = Path(sys.argv[1])
payload_file = Path(sys.argv[2])
payload_file.write_text(json.dumps({"body": body_file.read_text()}))
PY
GH_PAGER="" gh api \
  --method POST \
  /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies \
  --input "$REPLY_PAYLOAD_FILE"
rm -f "$REPLY_BODY_FILE" "$REPLY_PAYLOAD_FILE"
```

For PR-level comments or review-body comments that cannot be directly threaded, post a normal PR comment and quote or link to the original comment:

```sh
REPLY_BODY_FILE="$(mktemp)"
cat > "$REPLY_BODY_FILE"
GH_PAGER="" gh pr comment {pull_number} --body-file "$REPLY_BODY_FILE"
rm -f "$REPLY_BODY_FILE"
```

To resolve review threads, use GraphQL. If the thread node ID is not already known, query all review threads for the PR and map loaded comment IDs to their containing thread. Use pagination so threads beyond the first 100 can still be resolved:

```sh
GH_PAGER="" gh api graphql --paginate \
  -f owner="{owner}" \
  -f repo="{repo}" \
  -F number={pull_number} \
  -f query='
    query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
          reviewThreads(first: 100, after: $endCursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              isResolved
              comments(first: 100) {
                nodes {
                  databaseId
                  url
                }
              }
            }
          }
        }
      }
    }'
```

Resolve an approved thread with:

```sh
GH_PAGER="" gh api graphql \
  -f threadId="$THREAD_ID" \
  -f query='mutation($threadId: ID!) { resolveReviewThread(input: { threadId: $threadId }) { thread { id isResolved } } }'
```

If a comment cannot be replied to or resolved through the available metadata, report the limitation and suggest a manual GitHub action instead of guessing.

## Final response

After posting approved responses and resolving approved threads, summarize:

- comments addressed
- files changed
- validation results
- whether changes were committed and pushed to `origin`
- GitHub replies or resolutions posted
- anything left for the user
