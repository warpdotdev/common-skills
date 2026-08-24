# Writing guides for reviewers

A review guide says where to start and where to concentrate. The author knows which parts
were hard; the reviewer does not. That gap is the whole value.

## Which part of this file you need

- Deciding whether to write a guide at all: [When a guide is warranted](#when-a-guide-is-warranted).
- Small or medium PR, a few files: [Focus areas](#focus-areas). Skip the reading order.
- Large PR, or one where order matters: [Focus areas](#focus-areas) and
  [Recommended reading order](#recommended-reading-order).
- Checking tone before you post: [Tone](#tone).

## When a guide is warranted

Three questions. Any one is enough.

**Is the reading order non-obvious?** If understanding file B requires having read file A
first, say so. This is about structure, not size.

**Do you have a specific place you want attention?** Something you are unsure of, a
decision that went one of two ways, a surface where a mistake is expensive. One real
pointer justifies a guide on a PR of any size.

**Can this break something well beyond the files it touches?** See below.

If none of the three holds, skip the guide. A large but mechanical PR usually needs one
sentence saying it is mechanical and naming the one file that is not.

### Blast radius, calibrated

Blast radius is how far a change can break things beyond the code it touches. It is not
the same as user visibility, and not the same as importance.

Wide, and worth a guide even when the diff is tiny:

- Permissions, authorization, IAM grants, tenancy boundaries
- Network and firewall rules, exposure of an endpoint
- Schema migrations, stored data formats, retention and deletion behavior
- Public API contracts and anything an external consumer parses
- Feature-flag defaults
- Foundational shared components, and architecture-level changes such as reworking
  client-side routing or navigation
- Anything that changes a contract other code already depends on

Narrow, even when the change is user-visible and worth doing well:

- A small UI change, or a change to a lightly-shared component
- Adding or moving a few routes, as opposed to reworking how routing works
- Copy changes
- A new endpoint or a new component that nothing else depends on yet
- A test-only change

The test is what else can break, not how many people will see it. A visible tweak to one
row of one page has a narrow blast radius. An invisible change to how every page resolves
its navigation state does not.

## Focus areas

Point at specific places. A focus area that does not name a file, a symbol, or a decision
is not a focus area.

**Where you are unsure.** The single most valuable line an author can write. State the
call you made, why you think it is right, and what you are unsure about. This applies to
agent-authored changes too: if you inferred an intent that is written down nowhere, that
inference is exactly what needs a human.

**Discrepancies that look unintended.** A name, a value, or a comment that does not match
its surroundings. A resource named for one group but bound to another. A comment claiming
parity with a setting that is ten times different. A threshold that disagrees with the
constant it derives from.

These are visible in the diff, and that is exactly why they get missed: nothing marks
them as wrong, so a reviewer reads them as intended. You are usually the only person who
knows whether it was deliberate. Say which you think it is, and ask. Do not suppress one
because the reviewer could technically have spotted it, and do not quietly fix an
unrelated one either, since that buries it in the diff.

**Security-relevant surfaces.** Authentication, authorization, tenancy, secrets, network
exposure, user data. Say what the change permits that was not permitted before, and who
is now inside the boundary. Reviewers routinely miss a widened permission arriving as a
one-line role change.

**Decisions with a meaningful alternative.** Where a reasonable engineer would have gone
the other way, name the alternative and why it lost. The reviewer can then disagree with
the reasoning instead of reverse-engineering it. Skip non-decisions; a list of them
dilutes the real ones.

**One-way doors, where the ambiguity is genuine.** Persisted schema, stored formats,
public API shape, anything with a migration cost or an external consumer. The test is
whether reversing later would be expensive *and* you are not certain. A one-way door you
are confident about is worth a sentence of documentation, not a focus area.

Useful shape: the location, the decision, the reason, the question.

> `billing/invoice.go` treats a zero-amount line item as a deletion rather than a no-op,
> so it disappears from the rendered invoice. I think that is right, because the upstream
> system only emits zero for removed items. Worth a second opinion.

## Recommended reading order

Only for PRs large enough that the reviewer must choose an order. Below roughly ten
non-generated files, focus areas alone are usually better.

Order by dependency, not by directory and not by the order you wrote it. The reviewer
should meet each piece after the thing it depends on. The usual shape:

1. The new contract or mechanism: the type, the schema, the interface, the migration.
2. Its first real consumer, so the mechanism has a purpose before it has details.
3. The wiring: handlers, callers, registration.
4. The mechanical remainder, called out as such.

What makes an order worth reading:

- One clause of rationale per step. "Start with the store interface, because everything
  else is an application of it." A bare list of paths is a table of contents.
- Three to six steps. Past that it becomes a file listing.
- Name what can be skimmed, and why. Generated code, mocks, snapshots, lockfiles:
  "`types.gen.go` is generated from `openapi.yaml`; review the yaml." This buys real time.
- If the order needs a paragraph of preamble to make sense, the PR probably wants
  splitting. Consider it, and say so if you cannot.

## Tone

Assume a competent engineer who reviews code regularly.

Do not explain the practice of code review. "Please check for edge cases", "make sure the
tests are meaningful", "verify error handling is correct" describe the reviewer's job back
to them, and displace the pointer only you could have given.

Do not explain the reviewer's own tools or your language's semantics. Explain this change.

Avoid:

> Please review carefully, especially the tests and error handling. Let me know if you
> have any questions!

Prefer:

> The retry path in `uploader.go` is the part I am least sure of: a retry reuses the same
> object key, so a partial write from the previous attempt is overwritten rather than
> appended. That is intentional, but it depends on the key being deterministic.

## Worked examples

**Small diff, wide blast radius** (one line added to a CORS origin allowlist):

> This puts a third-party domain inside the browser trust boundary for the authenticated
> API, so any XSS on that domain can read authenticated responses. The entry is
> exact-match rather than a wildcard subdomain, which is the part worth confirming.

**Medium PR, one real decision:**

> The decision worth checking is what happens to a poison message. I chose to dead-letter
> after three attempts rather than retry indefinitely, because an unparseable payload
> never becomes parseable and the retry loop blocks the partition. The cost is that a
> transient parse failure now lands in the dead-letter queue.

**Large PR:**

> Reading order:
>
> 1. `cache/entitlements` - the mechanism. Everything else applies it.
> 2. `model/plans` - the invalidation key each field declares. Most worth disagreeing
>    with, since it encodes policy rather than mechanism.
> 3. `logic/checkout.go` and its tests - the first consumer, and the only behavior change
>    users will notice.
> 4. `handlers/` - wiring, mechanical apart from the cold-start path.
>
> `model/mocks/` is generated by mockery.
>
> Focus areas:
>
> - A field with no declared invalidation key fails at construction, so every new plan
>   field forces a decision. Deliberate, and it will stop the next person who adds a field
>   without reading this. Worth agreeing on now.
> - The cache is keyed by tenant rather than by user, so a permission change takes effect
>   for the whole tenant at once. I traded granularity for hit rate here.
