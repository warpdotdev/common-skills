---
name: write-pr-description
description: Writes the body of a pull request - the summary, the repository template sections, and reviewer guidance such as a recommended reading order and focus areas. Use whenever drafting or revising a PR description, filling in a repository's PR template, refreshing a description that no longer matches the branch, or preparing a branch for review. Use it even when the user only says "open a PR", "put this up for review", or "write this up" without naming the description.
---

# write-pr-description

A pull request description has one job: give the reviewer what the diff cannot.

The diff already states what changed. The description states why it changed, what it
affects, which decisions were made along the way, and where the author wants attention.
Everything below follows from that. When a rule here conflicts with what a specific
reviewer needs, serve the reviewer.

`create-pr` covers the mechanics of opening the PR. This skill covers what goes in the body.

## 1. Collect the facts before drafting

Usually you did the work and already know most of this. When you are describing a branch
you did not write, or a PR you have just been handed, start here.

```bash
# From a checkout of the branch
git --no-pager log <base>..HEAD            # commit bodies first, they carry the why
git --no-pager diff <base>...HEAD --stat

# From a PR number, with no local branch
gh pr view <n> --repo <owner/repo> --json title,commits,files,baseRefName
gh pr diff <n> --repo <owner/repo>
```

Read the commit bodies before the diff. They are usually the richest source of
motivation. Then verify what they claim: a commit message saying "matches the existing
pattern in this file" is an assertion about code, and it is often wrong. Do not forward a
claim you have not checked.

Verify by looking, not by reasoning. The checks worth making are cheap and specific:

- Read what the change deletes. When a change exists to fix something, the defect is
  usually visible in the removed code.
- Ask the system what a thing means, rather than inferring it: `gcloud iam roles
  describe` for a role's permission set, the provider or API schema for a resource's
  fields, the parser for what a marker does.
- Grep a flag across the environment files before claiming it is on or off.
- Open the file a comment or commit message points at, and confirm it says what the
  pointer claims.

One check of this kind usually produces the best sentence in the description.

Gather what the diff cannot tell the reviewer:

- The motivation. What breaks, costs, or stays impossible without this change.
- The linked issue, spec, or design doc, and any spec files committed on the branch.
- Decisions with a real alternative, and why the alternative lost.
- The blast radius: what this can break beyond the files it touches.
- The validation you ran, and what it showed.
- Anything you are unsure of.

## 2. Follow the repository's template

Check the repository for a PR template. Where there are several, pick the one matching
the change. Templates differ per repository, so check every time rather than reusing the
shape from your last PR.

**The template's own instructions outrank this skill.** A template that says "remove this
section if it is not relevant" is telling you what this repository's reviewers want.
Follow it. The guidance below applies where the template is silent.

- Keep the headings, their wording, and their order. Reviewers and tooling both scan for
  them.
- Answer every section, in your own words, under the heading. Do not reproduce the
  template's question text, its explanatory links, or its examples. A template with four
  gate sections can otherwise cost two hundred words to say "no" four times.
- Where a section does not apply, say so in a clause that shows you considered it ("No
  new tables"), rather than deleting it or leaving it bare.
- Tick a box only when its statement is true. Otherwise leave it unticked with a short
  reason on the same line. Do not delete the box, do not tick it with a caveat attached,
  and do not restate the box's own text back to the reader.
- Preserve machine-read content: changelog markers, artifact or media markers, issue
  linking keys. Check that the marker is live where the template puts it. Some templates
  show a marker inside an HTML comment that the parser strips, which means a marker left
  in place is silently ignored. Confirm against the parser or a merged PR.
- Instructional HTML comments can go once you have answered them.

When no template exists, use this shape, which is the same shape a template would give
you:

1. The opening paragraph from step 3, with no heading above it. It carries both what and
   why, so there is no separate `Why` section.
2. `## Review guide`, when step 4 calls for one.
3. `## What changed`
4. `## Validation`

This shape collapses on a small change. A heading over a single line is the same ceremony
step 4 warns about, so drop any section that would hold one and let the opening carry it.

## 3. Write the body

Open with one to three sentences covering what the change does and why. A reviewer who
reads only the first paragraph should be able to tell whether they are the right
reviewer.

Where the repository has a template, this paragraph goes inside its first content
section, whatever that section is called. Do not add a lead above the template's first
heading, and do not repeat it once inside.

Then give the substance:

- Explain the mechanism only where it is not obvious from the code. A new abstraction, a
  non-local invariant, or an unusual control flow needs a paragraph. A renamed field does
  not.
- Name behavior changes explicitly, including ones that are side effects of the main
  change. These are what break other people. For a permissions change, state the
  direction: what is now allowed that was not, and what is now refused that was allowed.
- Record decisions with their rejected alternatives. This is the highest-value content in
  most descriptions and it cannot be recovered from the diff. Where there was no real
  alternative, state the decision plainly. Do not manufacture one to fill the slot.
- Include visual evidence for a user-visible change: a screenshot, or before and after
  where the change is a modification. Reference only captures that exist.
- Link the issue, spec, or conversation once. Where there is none, say so only if the
  repository asks for one, through a template section or a contributing guide.
  Announcing "no linked issue" in a repository that does not use them is lint compliance
  rather than information. Never invent a plausible ticket ID to fill the gap; a wrong
  link costs more than no link.

### Validation

You normally ran the work, so report it: the command and what it showed.

Where you did not, or only partly did, these are the honest shapes. More than one can
apply at once: you may have verified a fact yourself and still be waiting on CI for the
rest.

- **Nothing ran.** State it plainly and name the command the reviewer or CI should run.
- **CI produces the result**, because the check needs credentials or an environment you
  should not use. Name the job, and say what you expect it to show, marked as an
  expectation rather than an observation. "Expect one destroy and one create, nothing
  else" gives the reviewer something to check the run against, which is more useful than
  silence. Phrase it so it cannot be misread as output you saw.
- **The branch adds tests but no run is recorded.** Say the tests are added and unrun, so
  nobody reads the test list as evidence they passed.
- **You could not run it**, for want of a device, credentials, or an environment. Say so,
  and name it as a check you are asking the reviewer to make. This does not cover
  something you skipped; if you could have run it, run it.
- **Someone else recorded the result**, such as a verification noted in an earlier commit.
  Attribute it or leave it out. Never restate it as your own observation.

Whichever apply, state each once. Repeating "this was not run" in three sections reads as
hedging, and buries the one line that says what to run instead.

Never write intent as though it were a result.

### Prose

Use ASD-STE100 as the baseline: active voice, one topic per sentence, sentences under
about 25 words, simple tenses, one term per concept for the whole description. Code
identifiers, command lines, and established repository jargon are technical names; leave
them alone. See [references/plain-language.md](references/plain-language.md) for the
rules and the exemptions.

## 4. Add reviewer guidance when it is warranted

Add a review guide when the reading order is not obvious, when you have a specific place
you want attention, or when the change can break things well beyond the files it touches.
Skip it when a competent reviewer will know where to look without being told.

Put it high, directly after the summary. A reviewer should not have to scroll past
compliance checklists to find where to start. `## Review guide` is a reasonable default
heading when the template does not supply one.

On a small PR, guidance is a sentence or two, not a section. Fold it into the opening
rather than raising a heading over it. A heading on two paragraphs is ceremony, and so is
a reading order for six files.

A review guide contains some or all of:

- A recommended reading order, for PRs large enough that the order matters.
- Focus areas: what you are unsure of, security-relevant surfaces, decisions with a
  meaningful alternative, and one-way doors where the ambiguity is genuine.

Write it for a competent engineer. Point at the code and the open question; never explain
how to review code. See [references/review-guide.md](references/review-guide.md), which
opens with a short map of which of its sections you need.

## 5. Cut

Drafts run long, and the excess is almost never in the thinking. It collects in the parts
that feel obligatory: the checklist answers, the inventory of tests, the second statement
of something you already said. Those parts are also the easiest to delete, which makes
this pass cheap and worth doing every time.

Rough anchors for the whole body, before you start cutting:

- A test-only, config, or mechanical change with no behavior change: a short paragraph.
- A small change with a real risk surface: a few hundred words, nearly all of them about
  the risk rather than the diff.
- A focused fix or feature: four or five hundred words.
- A new mechanism with consumers: under a thousand.
- A very large or foundational change: around a thousand, with most of the extra spent on
  the reading order and the focus areas.

These are anchors, not limits. Being over one means look harder at the list below; it
never means cut a decision.

Then take each paragraph and name the decision it helps the reviewer make. If you cannot
name one, delete it. The usual finds:

- Anything the diff shows at a glance. "The hash-scroll logic was generalized", "the
  field was renamed", one bullet per changed line, a restatement of the lockfile. The
  exception is something that looks unintended, such as a name that disagrees with what
  it binds to. The reviewer can see it but cannot tell it is wrong, so it stays.
- Paraphrases of comments this diff adds. The reviewer reads them in place, one scroll
  away.
- Inventories of the tests you added. Name what is *not* covered, and roughly how much of
  the change is tested. A list of test function names reads as padding, especially with
  no result attached to it.
- Explanations of how standard tools behave. Terraform replacing a renamed resource, how
  a test macro polls, when a React effect fires, how a library spawns a child process.
  Explain this change, not the reviewer's tools.
- The second statement of a fact. Count them: "no linked issue" and "nothing was run"
  each belong in exactly one place, and a fact worth stating twice is usually a fact
  stated badly the first time.
- Sentences whose only job is to point at another part of the description. Cross
  references inside one page mean the content is in the wrong place.
- Sentences about the description itself. "A review guide is included because this change
  has a wide blast radius." Write the guide; do not justify it.
- Commit trailers. `Co-Authored-By` belongs in the commit, not in the PR body.

Keep, even when cutting hard: the motivation, the behavior changes, the decisions and
their rejected alternatives, the open questions, and the blast radius. These are the
reason the description exists. When something has to go, cut mechanism before you cut a
decision.

## 6. Self-check

- Does the first paragraph let a reviewer decide whether the PR is theirs?
- Does every claim about testing describe something that ran, or say plainly that it did
  not?
- Have you verified every factual claim carried over from a commit message?
- Did the cut take a decision, a rejected alternative, or an open question with it? Those
  are the first things to go when you compress, and the last things you should lose. Put
  them back.
- Does the description match the branch as it stands now, rather than the path you took
  to get there?
- If there is reviewer guidance, is it near the top?

## Anti-patterns

**Narrating the branch's own history.** The most common failure. Sentences like "this PR
previously included unit tests, which were removed after review feedback", or "the
description above overstated this and has been corrected", describe a transition that
does not exist in the diff the reviewer is reading. The reviewer sees one state against
the base. Describe that state.

Note what survives the rule: the reasoning usually still matters, only the transition
goes. "The tests were removed because they only reasserted the match arms" becomes "there
are no unit tests here, because a test at this layer would only reassert the match arms".

This holds however long the branch is. A branch with thirty commits still reaches the
reviewer as one state against the base.

**Restating the diff.** A file-by-file inventory is the standard way to write something
long that carries no information.

**Unverified claims, about anything.** Inflated test claims are the familiar case ("fully
tested", "no regressions"), but a confident wrong claim about mechanism is more
dangerous, because a reviewer is less likely to check it. Before asserting what a role
permits, what a flag gates, or what a function guarantees, verify it.

**Grading your own work.** "Comprehensive", "robust", "clean", "properly". Padding that
costs credibility.

**Lecturing the reviewer.** "Please check for edge cases and make sure the error handling
is correct." A competent reviewer already does this, and it displaces the specific
pointers only you can give.

**Leaving a stale description.** After a rework or a force-push, rewrite the body to
describe the current branch. Do not append a revision log to the bottom.
