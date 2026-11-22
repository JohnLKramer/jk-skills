#!/usr/bin/env python3
"""Advisor CLI: guidance validation, decision calls, audit log, review queue.

Stdlib only. State lives in <project>/.advisor/:
  guidance.json    project guidance (see GUIDANCE_KEYS)
  decisions.jsonl  append-only log; one JSON object per line, kind = decision | ruling

Run with --help for subcommands.
"""
import argparse
import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/decisions"
DEFAULT_MODEL = "gemini-decision-1"
GUIDANCE_KEYS = {"mandate", "principles", "escalate_always", "confidence_threshold", "escalation_mode"}
ESCALATION_MODES = ("stop", "defer")
QUESTION_TYPES = {"choice", "noul", "score"}
RECENT_RULINGS = 8


def die(msg):
    print(f"advisor: {msg}", file=sys.stderr)
    sys.exit(1)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def paths(root):
    base = Path(root) / ".advisor"
    return base, base / "guidance.json", base / "decisions.jsonl"


def load_guidance(root):
    _, gpath, _ = paths(root)
    if not gpath.exists():
        die(f"{gpath} missing. Run the gemini-advisor-init skill first.")
    guidance = json.loads(gpath.read_text())
    problems = validate_guidance(guidance)
    if problems:
        die("guidance invalid:\n  " + "\n  ".join(problems))
    return guidance


def validate_guidance(g):
    problems = []
    for key in sorted(GUIDANCE_KEYS - g.keys()):
        problems.append(f"missing key: {key}")
    if problems:
        return problems
    if not str(g["mandate"]).strip():
        problems.append("mandate is empty")
    if not isinstance(g["principles"], list) or not g["principles"]:
        problems.append("principles must be a non-empty list")
    ids = set()
    for i, p in enumerate(g["principles"] if isinstance(g["principles"], list) else []):
        for k in ("id", "statement", "why"):
            if not str(p.get(k, "")).strip():
                problems.append(f"principles[{i}] missing {k}")
        if p.get("id") in ids:
            problems.append(f"duplicate principle id: {p.get('id')}")
        ids.add(p.get("id"))
    if not isinstance(g["escalate_always"], list) or not g["escalate_always"]:
        problems.append("escalate_always must list at least one category the human always decides")
    t = g["confidence_threshold"]
    if not isinstance(t, (int, float)) or not 0 < t <= 1:
        problems.append("confidence_threshold must be a number in (0, 1]")
    if g["escalation_mode"] not in ESCALATION_MODES:
        problems.append(f"escalation_mode must be one of {ESCALATION_MODES}")
    return problems


def read_log(root):
    _, _, lpath = paths(root)
    if not lpath.exists():
        return []
    return [json.loads(line) for line in lpath.read_text().splitlines() if line.strip()]


def append_log(root, entries):
    base, _, lpath = paths(root)
    base.mkdir(exist_ok=True)
    with lpath.open("a") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def rulings_by_ref(log):
    """Latest ruling per decision id."""
    out = {}
    for e in log:
        if e["kind"] == "ruling":
            out[e["ref"]] = e
    return out


def render_input(guidance, context, log, mode="stop"):
    lines = ["ADVISOR MANDATE:", guidance["mandate"].strip(), "", "PRINCIPLES:"]
    for p in guidance["principles"]:
        lines.append(f"- {p['statement']} (because {p['why']})")
    if mode == "defer":
        lines += ["", "THE HUMAN WILL REVIEW THESE AFTER THE FACT (still give your best choice):"]
    else:
        lines += ["", "THE HUMAN ALWAYS DECIDES (never rule on these):"]
    lines += [f"- {c}" for c in guidance["escalate_always"]]
    rulings = rulings_by_ref(log)
    decisions = {e["id"]: e for e in log if e["kind"] == "decision"}
    recent = sorted((r for r in rulings.values() if r["final_choice"] is not None),
                    key=lambda r: r["ts"])[-RECENT_RULINGS:]
    if recent:
        lines += ["", "RECENT HUMAN RULINGS (these override your prior tendencies):"]
        for r in recent:
            d = decisions.get(r["ref"])
            if d is None:
                continue
            note = f" Note: {r['note']}" if r.get("note") else ""
            lines.append(f"- {d['question']} -> human chose {r['final_choice']}.{note}")
    lines += ["", "CURRENT CONTEXT:", context.strip()]
    return "\n".join(lines)


def check_questions(spec):
    if not str(spec.get("context", "")).strip():
        die("questions file needs a non-empty 'context'")
    qs = spec.get("questions")
    if not isinstance(qs, dict) or not qs:
        die("questions file needs a non-empty 'questions' object")
    for key, q in qs.items():
        if q.get("type") not in QUESTION_TYPES:
            die(f"{key}: type must be one of {sorted(QUESTION_TYPES)}")
        if not str(q.get("instructions", "")).strip():
            die(f"{key}: instructions required (the model never sees the key)")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key):
            die(f"{key}: question keys must match [A-Za-z0-9_-]{{1,64}}")
        if q["type"] == "choice" and not isinstance(q.get("criteria"), dict):
            die(f"{key}: choice needs criteria as an object of option -> description")
        if q["type"] == "score":
            c = q.get("criteria")
            if not isinstance(c, list) or len(c) < 2 or not all(isinstance(x, str) and x.strip() for x in c):
                die(f"{key}: score needs criteria as a list of 2+ non-empty strings, lowest level first")
        if q["type"] == "noul" and "criteria" in q and not (
                isinstance(q["criteria"], dict) and set(q["criteria"]) <= {"true_description", "false_description"}):
            die(f"{key}: noul criteria may only hold true_description and false_description")
        if q["type"] == "choice" and "other" not in q["criteria"]:
            die(f"{key}: choice criteria must include a catch-all named 'other'")
        if q.get("scope") not in ("minor", "major"):
            die(f"{key}: scope is required: 'minor' or 'major'")


def options_for(q):
    if q["type"] == "choice":
        return list(q["criteria"])
    if q["type"] == "noul":
        return ["yes", "no"]
    return [str(i) for i in range(len(q["criteria"]))]


def interpret(q, a):
    """Reduce an API answer to (choice, confidence, raw).

    noul is P(yes), so yes at >= 0.5. score is a probability-weighted mean level,
    which can sit between levels, so the discrete level is the most probable one.
    """
    if a["type"] == "choice":
        return a["choice"], a["confidence"], {"probabilities": a["probabilities"]}
    if a["type"] == "noul":
        return ("yes" if a["noul"] >= 0.5 else "no"), a["confidence"], {"p_yes": a["noul"]}
    probs = a["probabilities"]
    return max(probs, key=probs.get), a["confidence"], {"mean_level": a["score"], "probabilities": probs}


def cmd_validate(args):
    g = json.loads(paths(args.root)[1].read_text()) if paths(args.root)[1].exists() else None
    if g is None:
        die("guidance.json missing")
    problems = validate_guidance(g)
    if problems:
        die("guidance invalid:\n  " + "\n  ".join(problems))
    print(f"ok: {len(g['principles'])} principles, threshold {g['confidence_threshold']}")


def cmd_ask(args):
    spec = json.loads(Path(args.questions).read_text())
    check_questions(spec)
    guidance = load_guidance(args.root)
    mode = args.escalation or guidance["escalation_mode"]
    log = read_log(args.root)
    ts = now()
    stamp = ts.replace("-", "").replace(":", "").replace(".", "")[:17]

    entries, sendable = [], {}
    for key, q in spec["questions"].items():
        base = {
            "kind": "decision", "id": f"d-{stamp}-{key}", "ts": ts, "key": key,
            "context": spec["context"], "question": q["instructions"],
            "type": q["type"],
            "options": options_for(q),
            "task": spec.get("task", ""),
        }
        if q["scope"] == "major" and mode == "stop":
            entries.append({**base, "status": "escalated", "reason": "major scope, never sent to advisor"})
        else:
            sendable[key] = (q, {**base, "major": q["scope"] == "major"})

    body = None
    if sendable:
        body = {
            "model": guidance.get("model", DEFAULT_MODEL),
            "input": render_input(guidance, spec["context"], log, mode),
            "questions": {
                k: {f: v for f, v in q.items() if f in ("type", "instructions", "criteria")}
                for k, (q, _) in sendable.items()
            },
        }
    if args.dry_run:
        print(json.dumps(body, indent=2) if body else "no minor questions to send")
        return

    answers = call_api(guidance, body)["answers"] if body else {}
    threshold = guidance["confidence_threshold"]
    for key, (q, base) in sendable.items():
        a = answers.get(key)
        if a is None:
            die(f"no answer returned for {key}; nothing logged for this call")
        value, conf, raw = interpret(q, a)
        if base["major"]:
            status, reason = "escalated", "major scope"
        elif q["type"] == "choice" and value == "other":
            status, reason = "escalated", "advisor chose 'other'"
        elif conf < threshold:
            status, reason = "escalated", f"confidence {conf:.2f} below {threshold}"
        else:
            status, reason = "applied", ""
        if status == "escalated" and mode == "defer":
            status = "deferred"
            if value == "other":
                probs = {k: v for k, v in raw["probabilities"].items() if k != "other"}
                value = max(probs, key=probs.get)
        entries.append({**base, "model_choice": value, "confidence": conf, "raw": raw,
                        "legend": q["criteria"] if q["type"] == "score" else None,
                        "status": status, "reason": reason})
    append_log(args.root, entries)

    result = [
        {"id": e["id"], "key": e["key"], "status": e["status"], "choice": e.get("model_choice"),
         "confidence": e.get("confidence"), "reason": e["reason"]}
        for e in entries
    ]
    print(json.dumps(result, indent=2))


def call_api(guidance, body):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        die("GEMINI_API_KEY is not set; ask the human instead of guessing")
    req = urllib.request.Request(
        guidance.get("endpoint", DEFAULT_ENDPOINT),
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        die(f"API error {e.code}: {e.read().decode(errors='replace')[:500]}")
    except urllib.error.URLError as e:
        die(f"API unreachable: {e.reason}")


def cmd_record(args):
    log = read_log(args.root)
    decisions = {e["id"]: e for e in log if e["kind"] == "decision"}
    if args.id not in decisions:
        die(f"unknown decision id {args.id}")
    d = decisions[args.id]
    if args.guidance_gap and not args.note:
        die("--guidance-gap needs --note saying what conflicts or is missing")
    if args.choice == "depends":
        if not args.note:
            die("a 'depends' ruling needs --note saying what it depends on")
        final, overridden = None, False
    else:
        if args.choice not in d["options"]:
            die(f"choice must be one of {d['options']} (or 'depends' with --note)")
        final = args.choice
        overridden = d.get("model_choice") is not None and final != d.get("model_choice")
    append_log(args.root, [{
        "kind": "ruling", "ref": args.id, "ts": now(), "final_choice": final,
        "source": args.source, "note": args.note or "", "overridden": overridden,
        "guidance_gap": args.guidance_gap,
    }])
    print(f"recorded {args.id} -> {final or 'depends'}")


def cmd_queue(args):
    """Pick decisions for after-the-fact human review."""
    log = read_log(args.root)
    ruled = rulings_by_ref(log)
    pending = [e for e in log
               if e["kind"] == "decision" and e["status"] in ("applied", "deferred") and e["id"] not in ruled]
    if not pending:
        print("[]")
        return
    # Cheapest signal first: least confident applied decisions, then a random audit
    # sample of confident ones, since a confident wrong answer is the costly miss.
    # Deferred forks still need a human ruling, so they go first.
    deferred = sorted((e for e in pending if e["status"] == "deferred"), key=lambda e: e["confidence"])
    pending = [e for e in pending if e["status"] == "applied"]
    pending.sort(key=lambda e: e["confidence"])
    n_low = max(1, round((args.n - len(deferred)) * 0.6))
    picked = deferred[: args.n] + pending[:n_low]
    rest = pending[n_low:]
    random.shuffle(rest)
    picked += rest[: args.n - len(picked)]
    print(json.dumps([
        {k: e.get(k) for k in ("id", "ts", "status", "major", "context", "question", "options", "legend", "model_choice", "confidence", "raw")}
        for e in picked
    ], indent=2))


def cmd_stats(args):
    log = read_log(args.root)
    decisions = [e for e in log if e["kind"] == "decision"]
    ruled = rulings_by_ref(log)
    applied = [d for d in decisions if d["status"] == "applied"]
    reviewed = [d for d in applied if d["id"] in ruled]
    overridden = [d for d in reviewed if ruled[d["id"]]["overridden"]]
    bands = {"<0.7": [0, 0], "0.7-0.9": [0, 0], ">=0.9": [0, 0]}
    for d in decisions:
        if d["id"] in ruled and d.get("model_choice") is not None and ruled[d["id"]]["final_choice"] is not None:
            band = "<0.7" if d["confidence"] < 0.7 else "0.7-0.9" if d["confidence"] < 0.9 else ">=0.9"
            bands[band][0] += 1
            bands[band][1] += 0 if ruled[d["id"]]["overridden"] else 1
    calibration = {b: {"ruled": n, "agreed": ok} for b, (n, ok) in bands.items()}
    print(json.dumps({
        "calibration_by_confidence": calibration,
        "decisions": len(decisions), "applied": len(applied),
        "escalated": len(decisions) - len(applied),
        "applied_reviewed": len(reviewed), "applied_overridden": len(overridden),
        "unreviewed_applied": len(applied) - len(reviewed),
        "deferred_awaiting_ruling": sum(1 for d in decisions if d["status"] == "deferred" and d["id"] not in ruled),
        "guidance_gaps": sum(1 for r in ruled.values() if r.get("guidance_gap")),
    }, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".", help="project root holding .advisor/ (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="check .advisor/guidance.json").set_defaults(fn=cmd_validate)

    a = sub.add_parser("ask", help="send minor questions to the advisor and log the outcome")
    a.add_argument("questions", help="JSON file: {context, task?, questions:{key:{type,instructions,criteria,scope}}}")
    a.add_argument("--escalation", choices=ESCALATION_MODES,
                   help="stop: escalated forks go to the human now. defer: use the advisor's best choice, "
                        "mark it deferred, and review later. Default: guidance escalation_mode")
    a.add_argument("--dry-run", action="store_true", help="print the request; call nothing, log nothing")
    a.set_defaults(fn=cmd_ask)

    r = sub.add_parser("record", help="log a human ruling for a decision id")
    r.add_argument("id")
    r.add_argument("choice")
    r.add_argument("--note", default="")
    r.add_argument("--guidance-gap", action="store_true",
                   help="the guidance conflicts or is incomplete for this fork; needs --note")
    r.add_argument("--source", choices=["live", "review"], default="live")
    r.set_defaults(fn=cmd_record)

    q = sub.add_parser("queue", help="select applied, unreviewed decisions for human review")
    q.add_argument("-n", type=int, default=8)
    q.set_defaults(fn=cmd_queue)

    sub.add_parser("stats", help="counts of decisions, escalations, overrides").set_defaults(fn=cmd_stats)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
