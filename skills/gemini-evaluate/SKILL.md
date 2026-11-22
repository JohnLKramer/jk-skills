---
name: gemini-evaluate
description: Use when the human wants to review the advisor's recent decisions after the fact, check whether the advisor is calibrated, or teach it from past choices; also when .advisor/decisions.jsonl has many unreviewed applied decisions.
---

# Gemini Evaluate

Lets the human re-rule on decisions the advisor already applied. Each ruling is appended to the log, and the most recent rulings are injected into the advisor's input on every later call, so corrections change its behavior immediately.

## Procedure

1. Select: `python3 -I <gemini-advisor-dir>/scripts/advisor.py queue -n 8`. It returns every unruled `deferred` decision first (the human has not yet decided those), then unreviewed applied decisions: mostly the lowest-confidence ones, plus a random sample of confident ones to catch confident mistakes. If it returns `[]`, report that and stop.
2. Brief the human before asking anything. Reviewers have not internalized the guidance, so print, in the chat, the mandate and every principle from `.advisor/guidance.json`. Then, for each decision, show the full context, the full question, every option with its probability (`raw.probabilities` for choices), and the advisor's pick. Never show only a short label.
3. Survey with `mcp__nimbalyst__PromptForUserInput`, one singleSelect per decision. Options: each of the decision's options, plus **"Depends / can't tell"** and **"Guidance conflicts or is incomplete here"**. Always include both of those last two options.
4. For every disagreement or "depends", ask for the reason in the human's words, and ask whether the advisor misread clear guidance, or the guidance conflicts or is incomplete. Do not assume the guidance is wrong; the human may say it is fine and merely unclear.
5. Record each answer, agreements included: `advisor.py record <id> <choice> --source review --note "<reason>"`. Agreements record the advisor's own choice. For "Depends / can't tell", record `depends` with a note saying what it depends on; it is never injected into the advisor's input. For "Guidance conflicts or is incomplete", add `--guidance-gap` (with the human's preferred option, or `depends` if they have none) and a note naming the conflict or the missing rule; each one feeds step 7.
6. Report `advisor.py stats`: overrides vs reviewed, and agreement by confidence band. If the 0.9 band is overridden often, or the 0.7-0.9 band almost never, propose a new `confidence_threshold` (set thresholds from labeled outcomes, not guesses).
7. Find patterns: two or more overrides in the same area, or a reason that states a general rule. Propose a guidance change (new or edited principle, or an `escalate_always` entry for areas where the advisor was confidently wrong). Apply it only after the human confirms, using the update flow in gemini-advisor-init.

Do not edit past log lines, and do not create other state files. The log is the only record.
