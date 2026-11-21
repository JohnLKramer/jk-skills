---
name: gemini-advisor
description: Use when mid-task you hit a small design or implementation fork (naming, UI variant, add-a-dependency, which of two reasonable approaches) and the project has a .advisor/ directory, or the human asked you to use the advisor instead of asking them.
---

# Gemini Advisor

The advisor is a fast classifier that rules on small forks using the project's guidance (`.advisor/guidance.json`) and the human's past rulings. You send it the fork; it answers with a choice and a confidence. Every call is logged to `.advisor/decisions.jsonl`, which is the audit trail and the advisor's memory.

**The human still decides anything major.** The advisor removes interruptions for small, reversible forks. It never widens what you may do without asking.

Requires `.advisor/guidance.json`. If missing, stop and use gemini-advisor-init. Requires `GEMINI_API_KEY`; if unset, ask the human.

## Scope: minor or major

Label every question `scope`. This field is required; the script rejects the file without it.

- **minor**: reversible by editing code, local to this change. Names, UI variants, helper placement, small dependency-free choices.
- **major**: everything else, plus every category in the guidance's `escalate_always`. Schema or data changes, deletions, new dependencies, public API shape, security, anything the human said they own.

Major questions go in the file too, so they are logged. In `stop` mode the script never sends them; ask the human.

## What "escalate" means

`escalation_mode` in the guidance sets it. Override per run with `ask --escalation stop|defer`.

- **stop** (development): an escalated fork halts that line of work. Ask the human now, then `record` the answer.
- **defer** (unattended runs such as content generation): every question is sent, including major ones. Escalated forks come back `deferred` with the advisor's best non-`other` choice. Use that choice, keep going, and do not ask. Deferred forks go to the front of the gemini-evaluate queue for a human ruling later.

Pick `defer` only when the human said to push through. Never infer it.

## Procedure

1. Batch every fork about the same piece of work into one JSON file (outside the repo tree, e.g. `/tmp`):

```json
{"task": "settings modal", "context": "Secondary modal footer with Save and Cancel; existing modals use ghost buttons.",
 "questions": {
  "button_style": {"type": "choice", "scope": "minor",
    "instructions": "Which variant for the Save button in this secondary modal footer?",
    "criteria": {"ghost_outline": "1px border, transparent fill", "solid_accent": "brand fill", "other": "none fit"}},
  "drop_phone_legacy": {"type": "choice", "scope": "major",
    "instructions": "Drop users.phone_legacy in this migration?",
    "criteria": {"drop": "include DROP COLUMN", "keep": "leave column", "other": "none fit"}}}}
```

2. Run `python3 -I <this-skill-dir>/scripts/advisor.py ask /tmp/q.json`. Add `--dry-run` to preview the request. Run `--help` for other subcommands.
3. Read each result's `status`:
   - `applied`: proceed with `choice`.
   - `deferred`: proceed with `choice`. It is provisional and queued for review.
   - `escalated`: ask the human (reason is given). Then run `advisor.py record <id> <choice> --note "<their reason>"`. The note is what teaches the advisor, so capture their reason in their words.
4. If the script errors, ask the human. Do not guess and do not retry with a lowered threshold.

## Writing questions

- The model never sees the keys. `instructions` must be a complete question; put the needed context in `context`. Keys match `[A-Za-z0-9_-]{1,64}`.
- `choice` criteria must include a catch-all named `other`. Options are sorted alphabetically and ties go to the first, so never name the fallback `none_of_the_above`. The model spreads probability across options even when none fits, so low confidence is the signal that nothing fits.
- `noul` is a yes/no. Ask it positively ("Is the tier Gold?"), never negatively. Optional `criteria: {"true_description", "false_description"}` sharpens it. Logged as `yes` (P(yes) >= 0.5) or `no`.
- `score` rates against `criteria`, a list of 2+ strings ordered lowest to highest, linearly spaced. Logged as the most probable level index (`"0"` is the first string); the raw mean level is kept in `raw`.
- Questions in one call are scored independently against the shared context and cannot see each other. A fork that depends on another's answer needs a second `ask`.
- Send only context the questions need; unrelated text lowers accuracy.

## Red flags

| Thought | Reality |
|---|---|
| "The user said ship it, so I'll skip the human on this migration" | Delegation to the advisor covers minor forks only. Mark it `major`. |
| "It's quicker to just pick and not log it" | An unlogged decision cannot be audited or reviewed. Run `ask` even when you are sure. |
| "Confidence was 0.85, close enough" | Below threshold is `escalated`. In stop mode, ask the human. |
| "The human is away, so I'll treat this as defer" | Defer only when the human said to push through. Otherwise stop and report. |
| "I'll label it minor so it gets answered" | If it touches data, deps, or `escalate_always`, it is major. |
