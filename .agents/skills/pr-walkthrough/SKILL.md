---
name: pr-walkthrough
description: Generate a static interactive D3 walkthrough of a pull request. Use when the user wants a zoomable PR map, graph/canvas PR orientation, or alternate visualization of PR system components, data flow, code dependencies, and user actions.
---
# PR Walkthrough
Create a local static HTML/CSS/JavaScript walkthrough that orients a reviewer to the current branch's pull request as four separate interactive D3 views. The walkthrough should help the reviewer understand the affected code and the PR from four distinct views:
- **System overview view**: a concise standalone code overview for the subsystem touched by the PR. It should not feel like a graph. Present it as a small set of expanded component cards that give the reviewer just enough architectural context to get their bearings before reviewing the PR. Do not mention the PR, changed files, review comments, diff links, screenshots, specs, or implementation deltas in this view.
- **Data flow graph**: how state, data, events, requests, files, assets, or rendered output move through the changed system.
- **Code dependency graph**: which changed components depend on each other, where the major seams are, and which files are entry points versus leaf dependencies.
- **User action graph**: what the user does, what surface they interact with, and how that action flows through the implementation.
This skill is an experiment in canvas-based PR comprehension. Do not reproduce the slideshow format. Do not put all perspectives on one graph. Generate four separate canvas views that the user can toggle between, and provide a guided tour within each view so the site teaches the PR from start to finish. Scale the walkthrough to the PR size: a small PR should feel like a compact reviewer aid, not a comprehensive architecture document.
This skill is not a code-review skill. Do not generate new review findings, approve/request-changes recommendations, or exhaustive critique. Use the full codebase at the PR/head commit, the PR diff, PR description, specs changed by the PR, and existing review comments from humans or agents to produce orientation maps that help a reviewer understand the change quickly.
## Output
Create a self-contained site at:
- `.warp/pr-walkthrough/index.html`
The site must be loadable directly from the local filesystem with a `file://` URL. Do not require a dev server, package install, bundler, or build step.
Prefer one self-contained HTML file with inline CSS, inline JavaScript, and inline data. If splitting files is unavoidable, use only relative local files and avoid `fetch()` because browser restrictions can block local file reads.
D3 should be loaded from a pinned official release on a reputable CDN. Use the helper script's default unless there is a concrete reason to change it:
- `https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js`
Do not use unpinned `latest` URLs, unofficial builds, or dynamic package ranges. Do not show repeated D3 implementation disclaimers in the UI. Keep CDN/runtime details in validation logs or final caveats only when relevant.
For reusable deterministic D3 rendering, prefer the helper script at `scripts/d3_canvas_runtime.py`. It emits the default styling CSS, an inline runtime loader that defines the renderer before injecting the pinned D3 script, and a graph renderer with zoom, pan, graph switching, search, node details, fit-to-view, and guided tour controls. Use this helper rather than writing one-off D3 setup code in each generated walkthrough.
The generated canvas must be treated as generated code that requires validation. Before reporting that a walkthrough is ready, run `scripts/validate_d3_canvas.py` against the generated HTML. If the canvas fails to initialize, D3 fails to load, required graphs are missing, tour controls do not work, nodes/edges do not render, or browser validation cannot be performed in an environment where it should be available, debug and regenerate before saying the walkthrough is ready. If a browser-capable environment is genuinely unavailable, report canvas rendering as unverified instead of ready.
## Styling
Use the neutral fallback styling tokens below for the walkthrough's visual design. They are brand-agnostic defaults and require no external brand source. If a `branding` skill is available, apply its brand tokens, fonts, and styling guidance on top of these defaults; when present, follow it and report any branding caveats in the final response.
Apply these default tokens:
- Use a dark surface: `#121212` for the page background, `#1e1e1d`/`#292929` for panels, and `#faf9f6` or `#ffffff` for text.
- Use a pink accent `#a43787` intentionally for active states, key links, focus rings, selected tour steps, and high-emphasis labels. Use secondary green `#34895c`, blue `#2e5d9e`, and purple `#754dac` as graph colors.
- Use Matter for UI/body text with `DM Sans, system-ui, sans-serif` fallback. Use Matter Mono for code, metadata, canvas labels, coordinates, file paths, and machine-oriented snippets with `Roboto Mono, ui-monospace, monospace` fallback.
- Keep copy truth-seeking, technical, concise, and verifiable. Avoid marketing superlatives and generic buzzwords.
- Prefer sharp, documentation-like containers with subtle borders. Use rounded corners only where they improve readability for cards, node callouts, tooltips, and buttons.
Recommended graph colors:
- System overview view: yellow `#c0872a`
- Data flow graph: green `#34895c`
- Code dependency graph: blue `#2e5d9e`
- User action graph: purple `#754dac`
- Active/focus/selected node: pink `#a43787`
## Workflow
### 1. Establish PR context
Identify the repository root, current branch, and comparison base.
Use the PR base branch if the current branch already has a GitHub PR, and record the PR URL for GitHub diff links:
```bash
gh pr view --json baseRefName,headRefName,title,body,url,state,reviewRequests,reviews,files
```
If there is no PR, infer the base branch from local repository conventions or the remote default branch:
```bash
git symbolic-ref --short refs/remotes/origin/HEAD
```
Then collect the review inputs:
```bash
git --no-pager diff --stat <base>...HEAD
git --no-pager diff --name-status <base>...HEAD
git --no-pager log --oneline <base>..HEAD
git --no-pager diff <base>...HEAD
```
Estimate PR size from changed lines, changed files, and conceptual breadth before building views. Default to the smallest useful walkthrough:
- **Tiny PR**: roughly 1 changed file or under 75 changed lines. Use 2-3 nodes/cards per view, 1-2 tour steps per view, and omit screenshots/review-discussion nodes unless they materially clarify behavior.
- **Small PR**: roughly under 250 changed lines or 1-3 changed files. Use 3-4 nodes/cards per view, 2-4 tour steps per view, and keep each node summary to 1 sentence plus at most 1 short detail.
- **Medium PR**: roughly 250-800 changed lines or several related files. Use 4-7 nodes per view only when each node teaches a distinct concept.
- **Large PR**: use the previous richer 5-12 node range only when the PR spans multiple subsystems, introduces new architecture, or has substantial review/spec context.
Do not inflate a small PR to fill the canvas. If two nodes would teach the same reviewer fact, merge them. If a view would duplicate another view, make it intentionally sparse rather than adding filler.
Do not build walkthrough content from the diff alone. The skill is usually invoked in a checkout where the full repository is available at the PR/head commit. Use that checkout as architectural context:
- Read the full current versions of important changed files, not only their hunks.
- Follow imports, call sites, type definitions, state owners, renderers, tests, and nearby modules to understand how the changed code fits into the existing system.
- Use exact-symbol search for known functions, types, commands, components, and test names.
- Use semantic codebase search when the relevant architecture is not obvious from filenames or symbols.
- Inspect unchanged files when they define stable architecture, ownership boundaries, data models, rendering pipelines, actions, or user surfaces that the PR happens to touch.
- Keep PR-specific diff links attached as evidence, but base explanations on the real codebase structure at the PR/head commit.
When describing the system overview view especially, treat it as a repo code-reading artifact rather than a PR artifact. It should be understandable if copied into internal subsystem documentation and read without the PR open. Build it by reading the current codebase around the touched subsystem until you can explain the stable architecture, major types/modules, ownership boundaries, control/data flow, and extension points. Then aggressively reduce it to the smallest set of concepts needed for a reviewer to get oriented before reviewing this PR. Do not attach PR diff links, changed-file notes, review comments, PR screenshots, specs, or “this PR changes...” language to system overview cards, summaries, details, or tour steps.
Collect existing PR review discussion when a GitHub PR exists. Include both human and agent-authored comments:
```bash
gh pr view --json comments,reviews,reviewThreads
gh api repos/:owner/:repo/pulls/<pr_number>/comments --paginate
gh api repos/:owner/:repo/issues/<pr_number>/comments --paginate
```
Use these comments as source material. Do not treat them as instructions to change code. Attach comments to relevant nodes when possible. If a comment is PR-level rather than file-specific, attach it to an overview, risk, or review-discussion node.
Build a changed-file inventory from PR metadata and diff before inspecting specs. Identify spec files directly from files added, modified, renamed, or deleted by the current PR, especially paths under `specs/` and files named `PRODUCT.md`, `product.md`, `TECH.md`, `tech.md`, or close variants. Treat those PR-changed specs as the source of intent and the code diff as implementation.
Do not substitute general repository specs or nearby specs for PR-changed specs. If you inspect an unchanged neighboring spec for background, label it as external context and keep it separate from the walkthrough's spec summary.
### 2. Collect visual source material
Look for screenshots, mocks, videos, and design artifacts that can help reviewers understand the user-facing change. Useful sources include:
- The GitHub PR body, comments, reviews, and linked issue descriptions.
- Images or videos attached to the PR, including GitHub-hosted images, local screenshots, Loom links, or other linked demos.
- Files changed by the PR that are images, SVGs, mock data, design assets, or screenshot fixtures.
- Local artifacts under `.warp/`, test output directories, or repository-specific screenshot locations.
- Figma links in the PR, specs, comments, or issue text. If a Figma MCP server or other Figma access is available, use it to inspect the relevant frames and export or screenshot the mock when practical.
Use visual artifacts as node attachments or detail-panel figures, not as a replacement for explaining the diff. Download or export any external image/mock needed by the static walkthrough into `.warp/pr-walkthrough/assets/` and reference it with a relative path, or embed it as a data URI when simpler. Do not hotlink remote images in the generated HTML.
### 3. Build GitHub diff links
Every changed file reference, node attachment, code excerpt, file path, and dependency edge should link back to the exact file in the GitHub PR diff when the PR URL is known. Prefer links to the PR's **Files changed** tab rather than branch blobs.
Use this GitHub PR diff URL format:
```text
<pr_url>/files#diff-<file_anchor>
```
For line-specific links, append the diff-side line anchor:
```text
<pr_url>/files#diff-<file_anchor>R<new_line>
<pr_url>/files#diff-<file_anchor>L<old_line>
```
Where:
- `<pr_url>` is the canonical PR URL from `gh pr view --json url`.
- `<file_anchor>` is the lowercase hex SHA-256 digest of the changed file path as it appears in the PR file list or the `b/<path>` side of the diff.
- `R<new_line>` links to a line on the right/new side of the diff.
- `L<old_line>` links to a line on the left/old side of the diff.
Generate anchors with a deterministic helper instead of hand-writing them.
### 4. Analyze the PR as four guided views
Build four view models before writing the HTML. Each view should contain points of interest, not every changed file.
For each graph, decide:
- What is the first node a reviewer should understand?
- What sequence of nodes teaches the PR best from start to finish?
- For graph views, what edges connect those nodes, and what relationship does each edge explain?
- Which changed files, specs, tests, visuals, and existing review comments attach to each node?
- What should the reviewer inspect if they click that node?
Before finalizing content, cross-check each important node against the actual source files at the PR/head commit. For the system overview view, inspect the existing owning module and adjacent unchanged modules first, then use the diff only to identify which subsystem to study. For the other graphs, use the diff to attach evidence and describe the PR-specific path.
Each view needs a tour: a sequence of node IDs and explanatory text. The tour should guide the reviewer in a deliberate order. It should not merely select nodes in arbitrary file order.
Directed graphs must make direction visually explicit. Data-flow, code-dependency, and user-action edges must render with arrowheads that visibly land at the target node boundary rather than disappearing underneath the node. Edge labels should describe the relationship direction from source to target. The system overview view should normally have zero edges; if an edge feels necessary, the view is probably drifting back into graph territory and should be simplified.
Use these view roles:
- **System overview view**: teach the architecture of the subsystem the PR happens to touch as a standalone code overview. Do not structure it as a PR change list, diff summary, implementation path, dependency graph, reviewer checklist, or comprehensive subsystem documentation. Do not attach PR diff links, changed-file annotations, review comments, PR screenshots, or spec/issue intent to this view. For small PRs, prefer 2-3 stable component concepts; for larger PRs, use up to 4-7 only when every card is necessary. Each card should be visually larger than graph nodes and should expose a short paragraph in the canvas, not just a label. The paragraph should define the component and why it matters for orientation, while staying strictly limited to the context needed for a reviewer to get their bearings before reviewing the PR. Card titles, summaries, details, and tour steps should describe how the system works in general and should remain true outside this PR. Set card dimensions explicitly when useful, for example `width: 340`, `height: 180`, and `summaryLines: 5` for concise cards.
- **Data flow graph**: emphasize how information or state moves. Start with intent/spec input, then source/defaults/state, then layout/render output, then async asset or validation loops.
- **Code dependency graph**: emphasize ownership and dependency direction. Start with specs/entry points, then model/view/command seams, then editor rendering elements, then tests.
- **User action graph**: emphasize the user path. Start with the surface, then the action, then visible feedback and error/loading states.
A useful non-overview graph usually has 3-5 nodes for small PRs and 5-12 nodes only for larger PRs. It is okay for the same conceptual point to appear in multiple graphs with graph-specific coordinates and graph-specific explanatory text, but avoid repeating the same explanation across views.
### 5. Create the canvas data model
Store graph data inline in the HTML as JSON assigned to `window.PR_WALKTHROUGH_D3_DATA`. Do not load JSON with `fetch()`.
Use this shape:
```json
{
  "meta": {
    "title": "PR title",
    "prUrl": "https://github.com/owner/repo/pull/123",
    "baseRef": "master",
    "headRef": "feature-branch",
    "summary": "What the PR is trying to accomplish."
  },
  "graphs": [
    {
      "id": "system-overview",
      "label": "System overview",
      "color": "#c0872a",
      "summary": "Concise component overview for the affected subsystem.",
      "nodes": [],
      "edges": [],
      "tour": []
    },
    {
      "id": "data-flow",
      "label": "Data flow graph",
      "color": "#34895c",
      "summary": "How state and rendered output move through the change.",
      "nodes": [
        {
          "id": "intent",
          "title": "Intent",
          "kind": "overview",
          "x": 0,
          "y": 0,
          "summary": "The change this PR is trying to make understandable.",
          "details": ["Concise evidence-grounded explanation."],
          "files": [{ "path": "specs/example/product.md", "url": "<github_diff_url>" }],
          "comments": [{ "author": "reviewer", "body": "Existing review discussion.", "url": "<comment_url>" }],
          "links": [{ "label": "PR", "url": "<pr_url>" }]
        }
      ],
      "edges": [
        { "source": "intent", "target": "surface", "label": "default flows into" }
      ],
      "tour": [
        { "nodeId": "intent", "title": "Start with intent", "body": "Teach why this point matters." }
      ]
    }
  ]
}
```
Coordinate and scale guidance:
- Put start nodes toward the left/top.
- Put the tour path left-to-right or top-to-bottom where practical.
- Keep related nodes close enough that the tour step and edges are visually obvious.
- Keep lower-level dependencies farther right/down from their callers.
- For the system overview view, change the scale from graph nodes to expanded reference cards. Use fewer cards, larger card dimensions, paragraph-length summaries, and a simple readable layout. Place peer architectural components in a compact reference map around the central subsystem concept, not around the PR intent. Do not include PR evidence, changed-file links, review comments, screenshots, specs, or PR-specific nodes in this view. Prefer `edges: []`.
- For small PRs, keep graph coordinates compact enough that each view is readable without panning. Prefer a short left-to-right chain over a broad map.
### 6. Build the static site
The site must work for both humans and browser automation agents.
Required UI behavior:
- One zoomable, pannable SVG canvas powered by D3 zoom that renders the currently active graph.
- Visible view toggles: `System overview`, `Data flow graph`, `Code dependency graph`, and `User action graph`.
- Visible tour controls: `Previous tour step`, `Next tour step`, `Restart tour`, and an indicator such as `Step 2 / 7`.
- Search input for node titles, file paths, and attached comment text within the active graph.
- Clickable nodes that open or update a persistent detail panel and sync the tour to that node when it appears in the tour.
- Edge labels for relationship meanings.
- Keyboard support:
  - Right Arrow or `n`: next tour step.
  - Left Arrow or `p`: previous tour step.
  - `1`: system overview view.
  - `2`: data flow graph.
  - `3`: code dependency graph.
  - `4`: user action graph.
  - `+` or `=`: zoom in.
  - `-`: zoom out.
  - `0`: reset zoom.
  - `f`: fit to view.
  - `/`: focus search.
  - `Escape`: clear search or selection.
- Stable headings, button labels, `data-graph-id`, `data-node-id`, `data-edge-id`, and `data-tour-index` attributes so a computer-use agent can click through and capture screenshots reliably.
Required content behavior:
- Show the PR title, base/head refs, and short intent summary above or beside the canvas.
- Include exactly four view definitions in data: `system-overview`, `data-flow`, `code-dependency`, and `user-action`.
- Each view must have its own nodes and tour. Data-flow, code-dependency, and user-action graphs must have directed edges. The system overview view should normally have zero edges and use larger cards with visible paragraph text so it reads as an overview, not as a graph.
- Every rendered edge in a directed graph must use a visible arrowhead at its target node and a relationship label that reads source-to-target.
- System overview content must be PR-agnostic and tightly scoped. It should educate the reviewer about only the app architecture needed to get oriented for reviewing the PR, without referencing the PR, changed files, review comments, screenshots, specs, or implementation deltas. Put PR-specific evidence and annotations in the data-flow, code-dependency, or user-action graphs instead.
- Each tour step must point at a node and explain why that node matters at that point in the walkthrough.
- Each node must have explanatory text in the detail panel. System overview cards must also show a full paragraph on the canvas itself and explain stable code concepts rather than PR changes.
- Each changed-file reference should link to the GitHub PR diff URL.
- PR-changed specs must be represented as nodes or node attachments. If the PR changes no specs, include an explicit "No PR-changed specs found" node or note.
- Existing human and agent review comments must be attached to relevant nodes or summarized in a review-discussion node.
- Visual artifacts should appear as node attachments in the detail panel.
- For tiny and small PRs, represent missing specs, review discussion, and visuals as terse detail-panel notes on an existing node instead of standalone nodes, unless they materially change how the reviewer should read the PR.
- Use the default fallback styling tokens: dark `#121212` surfaces, off-white text, sans-serif/monospace typography, pink active accents, and graph colors from the documented palette.
Use helper output:
```bash
python3 .agents/skills/pr-walkthrough/scripts/d3_canvas_runtime.py --css
python3 .agents/skills/pr-walkthrough/scripts/d3_canvas_runtime.py --runtime
python3 .agents/skills/pr-walkthrough/scripts/d3_canvas_runtime.py --template --data graph.json > .warp/pr-walkthrough/index.html
```
### 7. Validate the walkthrough
Before finishing:
1. Open the generated `index.html` path or print the exact `file://` URL.
2. Verify the HTML does not require network access except for the explicitly documented, pinned official D3 CDN runtime.
3. Confirm D3 uses a concrete pinned URL and no `latest` package reference.
4. Confirm `fetch()` is not used for local JSON/data loading.
5. Confirm graph data includes exactly the required graph IDs: `system-overview`, `data-flow`, `code-dependency`, and `user-action`.
6. Confirm all required controls are present: `Fit to view`, `Reset zoom`, `System overview`, `Data flow graph`, `Code dependency graph`, `User action graph`, `Previous tour step`, `Next tour step`, and `Restart tour`.
7. Confirm each view renders nodes/cards in a browser, confirm the system overview renders expanded paragraph cards with no PR-specific attachments, and confirm all non-overview graphs render directed edges with visible arrowheads.
8. Confirm graph switching, tour navigation, keyboard shortcuts, zoom, pan, fit-to-view, search, and node detail selection work.
9. Confirm every graph has a non-empty tour and every tour step points to an existing node.
10. Confirm every node has explanatory text and relevant changed-file links where applicable, except system overview cards, which should not include PR diff links, changed-file annotations, review comments, screenshots, specs, or implementation deltas.
11. Confirm PR-changed specs and existing PR review comments were fetched and either represented in the graphs or explicitly reported as absent/unavailable.
12. Confirm screenshots, mocks, Figma exports, changed images, and video thumbnails referenced by the walkthrough are local relative assets or data URIs, not remote hotlinks.
13. Confirm the site uses the documented fallback styling tokens.
14. Run the reusable validator:
```bash
python3 .agents/skills/pr-walkthrough/scripts/validate_d3_canvas.py --html .warp/pr-walkthrough/index.html --require-browser
```
Do not report the walkthrough as ready if validation fails or cannot be performed in a browser-capable environment; fix the graph or report rendering as unverified.
### 8. Optional public publishing with Cloudflare Pages
By default, keep walkthrough artifacts under `.warp/pr-walkthrough/` and out of version control. If the user asks for a publicly accessible URL or a repeatable CLI publishing workflow, prefer Cloudflare Pages Direct Upload after the walkthrough has passed validation.
Prerequisites:
- The user needs a Cloudflare account.
- For local interactive use, run Wrangler login once:
```bash
npx wrangler login
```
- Create the Pages project once, unless it already exists:
```bash
npx wrangler pages project create warp-pr-walkthroughs --production-branch main
```
Use the generated walkthrough directory as the upload root:
```bash
npx wrangler pages deploy .warp/pr-walkthrough \
  --project-name warp-pr-walkthroughs \
  --branch pr-<pr-number>-$(git rev-parse --short HEAD) \
  --commit-dirty=true
```
For a stable “latest walkthrough” URL, deploy to the production branch instead:
```bash
npx wrangler pages deploy .warp/pr-walkthrough \
  --project-name warp-pr-walkthroughs \
  --branch main \
  --commit-dirty=true
```
Wrangler prints both a deployment URL and, for non-production branch uploads, a deployment alias URL. Capture the URL from stdout and report it to the user. The production branch URL is normally:
```text
https://warp-pr-walkthroughs.pages.dev
```
Branch preview URLs normally use this shape:
```text
https://pr-<pr-number>-<sha>.warp-pr-walkthroughs.pages.dev
```
Important publishing caveats:
- Newly created Cloudflare Pages projects may serve the production URL before preview-subdomain TLS has finished provisioning. If a preview URL fails in Chrome with `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`, wait and retry, or deploy to `--branch main` and use the production URL for immediate sharing.
- If `wrangler` warns that the working directory has uncommitted changes, pass `--commit-dirty=true` for generated `.warp/` artifacts that should not be committed.
- For private code or sensitive PR context, do not publish to a public URL unless the user explicitly accepts that exposure. Use protected hosting, Cloudflare Access, or a local `file://` URL instead.
- Post only the short public URL in PR comments; do not commit or embed the generated HTML artifact in the repository unless the user explicitly asks.
## Orientation heuristics
When deciding what to highlight:
- Emphasize the smallest set of points of interest reviewers need to understand the PR's purpose, design, architecture, and user impact.
- Prefer fewer, better nodes. A 100-200 line PR should normally produce a compact walkthrough with about 10-16 total nodes/cards across all views, not 30+.
- Use the full codebase at the PR/head commit as the source of architecture truth. Diffs show what changed, but existing code explains what the changed pieces mean. The system overview view should be based on codebase exploration, not on the diff.
- For the system overview, stop after the reader has enough bearings to review the PR; do not include every subsystem touched indirectly or every implementation dependency.
- Prefer nodes for concepts, subsystems, state owners, user surfaces, important specs, and review-discussion hotspots.
- Prefer edges for cause/effect, data movement, call/dependency direction, and user-action progression.
- Prefer the tour for teaching order. The graph can show relationships, but the tour should guide comprehension.
- De-emphasize generated files, mechanical renames, formatting-only changes, and repetitive boilerplate.
- Explain why each high-level point needs each lower-level dependency.
- Surface behavioral or architectural risks as orientation notes, especially when they are documented in specs, PR description, tests, or existing review comments.
- Connect tests back to the node or edge they validate.
- If specs and code diverge, represent the mismatch as a node or annotation instead of hiding it.
- Do not attempt to perform a fresh code review. If you notice something while orienting the reviewer, frame it as an area to inspect rather than a finding unless it is already present in PR review discussion.
## Final response
Report:
- The generated walkthrough path.
- The `file://` URL.
- The inferred base branch and PR title or branch name.
- The GitHub PR URL used for diff links.
- Whether PR review comments were found and included.
- Whether D3 canvas validation passed.
- If published, the public Cloudflare Pages URL and whether it is a production URL or branch preview URL.
- Any important caveats, missing specs, or validation that could not be performed.
