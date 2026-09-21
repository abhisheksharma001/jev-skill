#!/usr/bin/env python3
"""Deterministic go / no-go check: should THIS task use Jev, and in what shape?

Answer the questions from what you know about the task (not from hope), then run:
  python3 fit_check.py --answers answers.json        # or: --answers - (stdin)
  python3 fit_check.py --template                     # prints a blank answers file

Exit code: 0 = GO, 4 = GO WITH GUARDS (hybrid), 3 = NO-GO, 1 = bad input.
The rules encode the evidence in references/fit-map.md; each verdict line says why.
No model is called, so the verdict is repeatable and reviewable.
"""
from __future__ import annotations

import argparse
import json
import sys

QUESTIONS = {
    "output_is_decision": "Is the output a decision from a closed set (yes/no, one of <=255 options, or a rating on 2-10 levels) rather than free text?",
    "code_can_decide": "Could plain code, a regex, a lookup or a rule decide it exactly (no language understanding needed)?",
    "needs_math_dates_counting": "Does the decision itself hinge on arithmetic, counting, numeric/date comparison, or chaining several facts?",
    "text_input": "Is the input text or JSON (or can be turned into text before the call)?",
    "fits_state_budget": "After filtering to only what the question needs, does the input fit in ~32k tokens?",
    "high_volume": "Will it run often enough that per-call cost or latency matters (roughly >1k decisions/day, or inside a loop)?",
    "latency_under_300ms": "Must the answer arrive in under ~300 ms (e.g. inside a live voice turn)?",
    "irreversible_or_regulated": "Does a wrong answer trigger something irreversible, customer-facing, or regulated (money, hiring, credit, medical, legal, deleting data)?",
    "adversarial_input": "Can the input be written by someone who benefits from steering the answer (users, emails, web pages, agent tool output)?",
    "non_english": "Is a meaningful share of the input not in English?",
    "can_send_data": "Are you allowed to send this data to a US-hosted third-party API (check PII, client contracts; ZDR is enterprise-only)?",
    "has_labels": "Do you have, or can you collect, >=50 labelled examples (>=200 to publish accuracy numbers)?",
    "incumbent_exists": "Is something already making this decision today (an LLM call, rules, a human, a trained classifier)?",
}


def verdict(a: dict) -> tuple[int, str, list[str], list[str]]:
    why, patterns = [], []
    if not a["output_is_decision"]:
        return 3, "NO-GO", ["Output is free text. Jev does not generate. Use an LLM; if the text step hides a decision "
                            "(e.g. 'should we reply at all?'), split that decision out and re-run this check on it."], []
    if a["code_can_decide"]:
        return 3, "NO-GO", ["Code can decide it exactly. Code is free, instant and deterministic; keep it."], []
    if not a["text_input"]:
        return 3, "NO-GO", ["Jev is text-only. Transcribe/caption first, then re-run this check on the text."], []
    if not a["can_send_data"]:
        return 3, "NO-GO (for now)", ["Data may not leave for a US third-party API. Resolve terms/ZDR (or redact) first."], []

    level = 0  # 0 GO, 1 GUARDS
    if a["needs_math_dates_counting"]:
        level = 1
        why.append("Arithmetic/dates/counting/multi-hop are documented weak spots: compute those in code and pass "
                   "the result (e.g. 'days_overdue: 12') into state, then ask Jev only the semantic part.")
        patterns.append("precompute-in-code")
    if not a["fits_state_budget"]:
        level = 1
        why.append("Input too large: filter or chunk to what each question needs (context rot lowers accuracy).")
        patterns.append("filter-state / chunk-and-aggregate")
    if a["latency_under_300ms"]:
        level = 1
        why.append("Measured round trips are ~0.4-0.9 s for short state (more from outside the US / with big state). "
                   "Keep Jev out of the hard real-time path; run it async (post-turn, post-call) or speculatively.")
        patterns.append("async / post-call")
    if a["irreversible_or_regulated"]:
        level = 1
        why.append("High stakes: Jev may pre-screen or say 'confident no, skip', but a human, rules or a stronger "
                   "model must own the irreversible yes. For hiring/credit-style screening, do not use it as decider.")
        patterns.append("blind-fallback cascade (Jev says 'confident no' only)")
    if a["adversarial_input"]:
        level = 1
        why.append("State can steer answers (fake delimiters were the weakest case in tests): put deterministic "
                   "rules/deny-lists first, keep untrusted text in a clearly labelled field, and test injections.")
        patterns.append("rules-first, Jev for the ambiguous remainder")
    if a["non_english"]:
        level = 1
        why.append("Non-English is weaker: calibrate per language before trusting thresholds.")
    if not a["has_labels"]:
        level = 1
        why.append("No labelled set yet: start in shadow mode to collect disagreements as labels; no gating until "
                   "calibrate.py has eval-split numbers.")
        patterns.append("shadow mode first")
    if a["incumbent_exists"]:
        patterns.append("shadow beside the incumbent, then confidence-floor cascade behind a kill switch")
    else:
        patterns.append("greenfield: battery of atomic questions, thresholds from calibrate.py, fallback path from day one")
    if not a["high_volume"]:
        why.append("Low volume: Jev's cost/latency edge matters less; choose it for consistency (low variance) or "
                   "calibrated probabilities, not savings.")
    patterns.append("batch every question about one state into one call")
    if level == 0:
        why.insert(0, "Decision-shaped, text-in, needs language judgement, no blocking risks found.")
        return 0, "GO", why, patterns
    return 4, "GO WITH GUARDS", why, patterns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers")
    ap.add_argument("--template", action="store_true")
    a = ap.parse_args(argv)
    if a.template:
        print(json.dumps({k: None for k in QUESTIONS}, indent=2))
        print("\n# " + "\n# ".join(f"{k}: {v}" for k, v in QUESTIONS.items()), file=sys.stderr)
        return 0
    if not a.answers:
        ap.error("--answers is required (or --template)")
    raw = sys.stdin.read() if a.answers == "-" else open(a.answers, encoding="utf-8").read()
    try:
        ans = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"bad JSON: {e}", file=sys.stderr)
        return 1
    missing = [k for k in QUESTIONS if not isinstance(ans.get(k), bool)]
    if missing:
        print("answer every question with true/false; missing or not boolean: " + ", ".join(missing), file=sys.stderr)
        return 1
    code, label, why, patterns = verdict(ans)
    print(f"VERDICT: {label}")
    for w in why:
        print(f"- {w}")
    if patterns:
        print("PATTERNS: " + "; ".join(dict.fromkeys(patterns)))
    return code


if __name__ == "__main__":
    sys.exit(main())
