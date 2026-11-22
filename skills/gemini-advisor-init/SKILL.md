---
name: gemini-advisor-init
description: Use when setting up the Gemini advisor for a project, when .advisor/guidance.json is missing, or when the human wants to revise the advisor's principles, escalation rules, or confidence threshold.
---

# Gemini Advisor Init

Turns the human's stated ethos into a small structured guidance file that the advisor reads on every call. Also the way to amend that file later.

Output: `.advisor/guidance.json`. Prose guidance is not accepted; the script validates the shape.

```json
{
  "mandate": "One paragraph: who the advisor is and what it optimizes for.",
  "principles": [
    {"id": "low-visual-weight", "statement": "Prefer ghost over solid buttons in secondary surfaces.", "why": "Clutter hides primary actions."}
  ],
  "escalate_always": ["schema or data deletion", "new runtime dependencies"],
  "confidence_threshold": 0.9,
  "escalation_mode": "stop"
}
```

Write each principle statement as a decision rule that names both sides: what to prefer, and when the alternative applies ("Prefer ghost outline buttons in secondary modals; reserve solid fills for the single primary action on a page"). A one-sided preference leaves the advisor unsure and it escalates; the two-sided rule moved a live test from 0.53 to 0.98 confidence.

Keep it small: a mandate, roughly 5 to 10 principles, each one statement with a reason. `escalation_mode` is `stop` (halt and ask the human) or `defer` (use the advisor's best choice, review later); the gemini-advisor skill defines both. Optional `model` and `endpoint` keys override the API defaults.

## Create

1. Take the human's prompt as the seed. Read the repo's AGENTS.md/CLAUDE.md for conventions so you do not ask what is already answered.
2. Draft the mandate and principles from the seed. Do not invent principles the human did not state or imply.
3. Run a survey with `mcp__nimbalyst__PromptForUserInput` (or AskUserQuestion). One batched round, multiple choice, covering the gaps you found:
   - **Incomplete**: principles with no `why`, undefined terms ("touch data", "reversible"), no `escalate_always` entries, no stated threshold or escalation mode. Offer concrete candidate definitions.
   - **Undefined escalation**: ask which default mode applies, and what the human means by each `escalate_always` entry (does restyling a delete button count as "data deletion"?). Offer concrete examples on each side.
   - **Inconsistent**: pairs that collide (e.g. "move fast on reversible things" vs "never touch data without a plan"). Name both, propose a precedence, ask.
4. Fold the answers in. Show the final file and get confirmation.
5. Write `.advisor/guidance.json`, then run `python3 -I <gemini-advisor-dir>/scripts/advisor.py validate`. Fix every reported problem.
6. Add `.advisor/decisions.jsonl` to version control only if the human wants the audit trail shared; ask once.

## Update

Read the existing file, apply the change, and rerun steps 3 (only for the changed parts), 4, and 5. Keep principle `id`s stable; edit statements in place. When two principles now conflict, ask which wins.

`confidence_threshold` default is 0.9. Raise it to ask the human more often.
