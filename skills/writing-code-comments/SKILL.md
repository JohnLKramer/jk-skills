---
name: writing-code-comments
description: Use when writing or editing comments in source — inline // # --, KDoc, Javadoc, SQL comments, or Liquibase notes beside SQL.
---

# Writing Code Comments

A comment is living documentation of the code in the tree. A reader six months from now, who never saw the ticket or plan, still needs whatever it says.

Sentence-level prose follows plain-english: active voice, concrete words, complete sentences, every word tells. Do not open that skill. Do not apply its document-structure rules (headers, plan vs spec tense, explain-every-concept-first) to comments.

## What a comment is

Primary: why this is done, and which assumptions are not obvious from the code.

Secondary: complex logic the code cannot make obvious. Example: a loop invariant.

If the names are enough, there is no comment. Public visibility does not justify KDoc.

If the same shape already exists elsewhere in the codebase, the copy does not need its own comment. Name the canonical example once when the pattern is new; after that, readers learn it from any instance (`VenueAccountCreationDao#markRetryableFailure` and `PlaylistVenueAccountCreationDao#markRetryableFailure` need not both be documented).

## Shape

One point. Complete sentence. Name other code (`ReservationClient#getReservations requires validated keys`). Do not link it. No GitHub URLs, Jira keys, plan IDs, or PR numbers.

## Do not write

- `TODO` or `FIXME`. Raise the concern in chat.
- A restatement of the next line (`// Default to CLASS_PASS if null` on a `?:`).
- Process notes: ticket keys, plan step IDs (`DDL-4`), "type only; columns come later." No process notes anywhere in the file, including the lines above a Liquibase `--changeset`.
- Comments someone just removed.

Liquibase `--changeset` lines are identifiers, not documentation. Do not hang notes on the next line.

## Excuses that still fail

- "Breadcrumb for the next changeset" — process, not living documentation.
- "The ticket/reviewer asked for comments" — still no process notes, restating, or obligatory KDoc.
- "TODO is standard" — unfinished work goes in chat.
- "Public API requires KDoc" — only if the signature is not enough.
- "This copy should be documented too" — a repeated pattern is one pattern; comment the first canonical instance if needed, not every mirror.
- "I'm documenting the work" — document the code, not the change. Naming the prior class and giving the reason for switching off it is the change, not the code:
  `// Uses EventProcessor (not PaymentsQueueProcessor) so a task failure logs the actual exception with its stack trace.`
  A reader with no memory of `PaymentsQueueProcessor` gets nothing from this once the migration is old news. Drop it, or state the current class's own invariant with no comparison: `// Failures log with the exception's stack trace, not just its toString().`
- "The file's untracked, so the link can't resolve yet" — pasting the URL anyway doesn't make it resolve; name the code, don't guess at a future URL.
- "I'm explaining why the skip happens" — a reason for the same branch is still that branch in prose (`// Skipped so a rerun doesn't post twice` beside `if (status != ENQUEUED) continue`). State the invariant the code doesn't show, not a rationale for the visible condition.

## Six-month test

If it only helps someone carrying the current ticket, delete it.
