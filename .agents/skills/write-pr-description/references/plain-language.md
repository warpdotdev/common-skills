# Plain language for PR descriptions

ASD-STE100 (Simplified Technical English) is a controlled-language standard for technical
writing that is read fast, under load, by someone who did not write the thing being
described. That describes a PR description. Use it as a baseline, not a compliance
target: the goal is prose a reviewer parses correctly on the first pass.

The rules below are the whole of it. The [exemptions](#what-is-exempt) matter as much as
the rules, because a rule applied to an identifier does damage.

## The rules

**Use the active voice.** Name the actor. "The parser rejects unknown keys", not
"unknown keys are rejected". Passive voice hides who does the work, which is exactly
what a reviewer of a permissions or validation change needs to know.

**One topic per sentence.** If a sentence carries a fact and its consequence and a
caveat, it needs to be two or three sentences.

**Keep sentences under about 25 words.** Long sentences in a PR description almost
always turn out to be two facts joined by a comma.

**Use simple tenses.** Prefer "the gate rejected the request" over "the gate had been
rejecting requests". Simple past, simple present, simple future cover nearly everything.

**Keep the articles and the connecting words.** "Fix for case where config is nil" reads
as a telegram. "This fixes the case where the config is nil" costs three words and one
less reparse. Keep "that" and "which" rather than dropping them.

**Use one term per concept, for the whole description.** If you call it a tenant in the
first paragraph, it is a tenant in the last. Switching between tenant, organization, and
account makes a reviewer wonder whether you mean three things. The same applies in
reverse: do not use one word for two concepts.

**Do not stack more than three nouns.** "Consumer retry backoff configuration override"
forces the reader to guess the bracketing. Break it up with prepositions: "the override
for the retry backoff on the consumer".

**Use a vertical list when there is more than one condition or step.** Prose that
carries three conditions in one paragraph hides at least one of them.

**Prefer the specific word.** "Handles", "supports", "manages", and "processes" are
placeholders for a verb you have not chosen yet. "Validates", "retries", "rejects",
"caches" tell the reviewer what the code does.

**Keep paragraphs to about six sentences.** Past that, split them or make them a list.

## What is exempt

STE's approved-word list is for controlled documentation, not code review. These are
technical names and stay exactly as they are:

- Code identifiers, type names, field names, and file paths: `FactoryConfig`,
  `spawn_server_impl`, `logic/factories.go`.
- Command lines and their flags, verbatim.
- Established repository and domain jargon: merge queue, feature flag, migration,
  presubmit, one-way door.
- Product and service names.

Do not paraphrase an identifier into prose to satisfy a word rule. `nil` is `nil`, not
"an empty value".

## Two rewrites

**Passive and vague:**

> The cache layer was updated so that stale entries can be handled appropriately.

**Active and specific:**

> Each cache entry now records the version of the pricing table it was built from. The
> lookup compares that version against the current one, and rebuilds the entry when they
> differ.

---

**Intent stated as result:**

> Added tests to make sure the migration is safe to roll back.

**Result stated as result:**

> `migrate down` drops the index and leaves no other residue. The integration test
> asserts this against a local PostgreSQL instance.

## Words that add nothing

Cut these unless they carry weight: comprehensive, robust, cleanly, properly, simply,
just, basically, essentially, in order to, it should be noted that, a number of.

"Simply" and "just" are worth singling out. They tell a reviewer that the thing they are
about to read is easy, which is either redundant or wrong, and occasionally insulting.
