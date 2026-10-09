---
name: upload-screenshot
description: Upload one or more screenshots to a stable image host and embed them in a GitHub PR description and/or post to a Slack thread. Use when visual evidence of a UI change needs to be attached to a PR or shared in Slack. Works in both local and cloud (sandboxed) environments.
---

# upload-screenshot

## Overview

Uploads PNG/JPEG screenshots to a stable public image host and returns embeddable URLs. Supports two output targets: updating a GitHub PR description and posting to a Slack thread. Either or both targets can be used in a single invocation.

## Image Hosting

Try hosts in this order, moving to the next on failure:

### 1. Imgur (preferred)

Imgur anonymous upload works reliably from cloud environments without an account.

```bash
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Client-ID 546c25a59c58ad7" \
  -F "image=@/path/to/screenshot.png" \
  "https://api.imgur.com/3/image")

IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['link'])")
echo "$IMAGE_URL"
```

Check that `IMAGE_URL` starts with `https://i.imgur.com/`. If the response contains `{"success":false,...}` or is empty, fall through to the next host.

### 2. Fallback: upload the image locally and reference it

If external hosting is unavailable, save the image as a conversation artifact using the `upload_artifact` tool (available in Oz agents) and note the limitation in the PR comment.

## Output Target: GitHub PR description

Fetch the current PR body and inject a `### Screenshots / Videos` section before the Agent Mode section (or at the end of the Testing section). Use `gh api` to patch the PR:

```bash
# Get current body
CURRENT_BODY=$(gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '.body')

# Append screenshots section (or insert before existing section)
NEW_BODY="${CURRENT_BODY}

### Screenshots / Videos

![Screenshot](${IMAGE_URL})"

# Patch
gh api repos/{owner}/{repo}/pulls/{pr_number} -X PATCH -F body="$NEW_BODY"
```

For multiple screenshots, use a `<details>` block for the full view:

```markdown
### Screenshots / Videos

![Close-up](https://i.imgur.com/XXXX.png)

<details>
<summary>Full screenshot</summary>

![Full view](https://i.imgur.com/YYYY.png)

</details>
```

## Output Target: Slack thread

Post the image URL as a chat message using `chat.postMessage`. Use the appropriate bot token from the environment (e.g. `FEEDBACK_TRIAGE_SLACK_BOT_TOKEN` for feedback channels):

```bash
curl -s -X POST \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$CHANNEL_ID\",
    \"thread_ts\": \"$THREAD_TS\",
    \"text\": \"$MESSAGE_TEXT\",
    \"unfurl_links\": true,
    \"unfurl_media\": true
  }" \
  https://slack.com/api/chat.postMessage
```

Slack will unfurl the Imgur URL into an inline image preview. If `files:write` scope is available on the token, prefer a native file upload via `files.getUploadURLExternal` → upload → `files.completeUploadExternal`.

## Usage in computer use (cloud agent) context

When running as a cloud agent with computer use:

1. Take the screenshot using the computer use tool's screenshot capability
2. Save it to `/tmp/screenshot-<name>.png`
3. Upload using the Imgur method above
4. Post to the target(s)

Return the hosted URL(s) to the parent orchestrator in your completion message so they can be referenced without re-uploading.

## Notes

- `0x0.st` is currently disabled (as of mid-2026).
- `litter.catbox.moe` has 72-hour expiry — do not use for PR descriptions.
- For GitHub PR descriptions, prefer the Imgur URL directly in the markdown body rather than a PR comment, so the image appears in the main description.
