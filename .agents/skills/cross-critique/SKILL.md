---
name: cross-critique
description: Run a second round on a contested question by circulating each subagent's independent proposal to the other authors and asking for structured pros and cons, then synthesize. Use this skill whenever you have multiple independent proposals or opinions on a contested decision — architecture tradeoffs, code review disagreements, design choices, competing root-cause theories — and want sharper analysis than you'd produce by synthesizing alone. Pairs naturally with the council and research skills; reach for it liberally whenever proposals diverge.
---

# Cross-Critique

Use this skill to run a **second round** after several subagents have independently produced proposals or opinions on the same contested question. Instead of synthesizing their reports yourself, you circulate each proposal to the *other* authors and ask them to critique it — pros and cons — and then you synthesize the richer set of analyses that results.

## Why this matters

When you generate independent proposals (different models, different angles), each author ends up with deep context on the question — often deeper than yours, since they did the investigation. If you jump straight to synthesizing their reports alone, you're the bottleneck: you can only see the tradeoffs *you* happen to notice.

Asking the authors to critique each other is what a good leader does when seeking advice: get a few people with differing perspectives in a room, let them poke holes in each other's reasoning, and you walk away with a far more complete picture than any one of them — or you — would produce alone. The authors will surface failure modes, hidden assumptions, and tradeoffs that neither you nor the original proposer flagged.

## When to use it

Use cross-critique when a decision is **contested** — i.e. independent agents produced genuinely divergent proposals, or the question is subjective enough that reasonable approaches disagree. Good fits:

- Architecture and design tradeoffs.
- Code review where reviewers reached different conclusions.
- Competing root-cause theories for a bug.
- Code-structure or API-shape decisions with no single right answer.

Don't bother when the proposals already strongly agree, or when the question has an objective answer you can verify directly — critique adds latency and tokens, and its value comes specifically from resolving genuine disagreement. Within that scope, use it freely; you don't need a high-stakes justification, just real divergence worth resolving.

## Prerequisite: you need independent proposals first

This skill is the *second* round. It assumes you already have N independent proposals in hand. If you don't yet:

- For a judgment-heavy decision, generate them with the **council** skill (model-diverse subagents on the same question).
- For an investigation-heavy question, generate them by spawning parallel subagents (see the **research** skill).
- Or use any ad-hoc set of independent subagent proposals you've already collected.

Critically, the first round must be **independent** — do not let the authors see each other's work during round one, or you lose the diversity that makes round two valuable.

## How to do it

### 1. Assemble the proposals

Collect each author's proposal. Keep them concise — the core recommendation and its reasoning, not the full transcript. Consider labeling them neutrally (Proposal A, B, C) and, where practical, anonymizing authorship to reduce bandwagon bias toward whichever model sounds most confident.

### 2. Circulate and ask for structured critique

Reuse the **same subagents** from round one rather than spawning fresh ones — they retain their context and can critique from a position of understanding. Send each author the *other* proposals (not their own) and ask each for:

- For each alternative: its **pros** (what it gets right, where it's stronger than my approach) and its **cons** (risks, edge cases, hidden costs, wrong assumptions).
- Whether, having seen the alternatives, they would **revise their own** recommendation — and why or why not.
- A final ranking or recommendation with confidence.

Insist on *both* pros and cons for each alternative. An honest critique that credits a rival's strengths is far more useful than a reflexive defense of one's own proposal.

### 3. Synthesize

Now bring it together yourself. Compare critiques by **evidence quality, not vote count**. In your final answer:

- Lead with the recommendation.
- Note where the authors converged after seeing each other's work — convergence in round two is a strong signal.
- Surface the most incisive cons raised against each option.
- Explain why the recommended option survives critique best against the decision criteria.
- Call out remaining disagreement, confidence, and material unknowns.

## Final answer template

Use this shape unless the task calls for something different:

```markdown
## Recommendation
[One or two sentences with the decision.]

## How the critiques shifted things
- [Where authors converged or changed their minds after seeing alternatives]
- [The strongest objection raised, and whether it's decisive]

## Why this option wins
- [Reason grounded in the critiques]

## Remaining risks and unknowns
- [Open question or caveat]
```

## Practical notes

- Keep the critique round read-only unless the underlying task explicitly involves making changes.
- Don't expose internal subagent IDs in user-facing summaries unless the user asks.
- If a critique is thin or unsupported, send a focused follow-up to that same author rather than discarding it.
