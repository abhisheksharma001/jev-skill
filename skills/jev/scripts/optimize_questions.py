#!/usr/bin/env python3
"""Let a strong model improve Jev's questions, and let held-out data decide if it worked.

Jev has no fine-tuning, so the question text IS the model you ship. A frontier model is good at
reading failures and rewriting wording; Jev is cheap at answering. This script is the referee
between them. The strong model's intelligence is spent once, at design time, and every later
Jev call benefits at no extra cost.

The script never calls an LLM. The agent running the skill is the rewriter:

  1. misses    run the current questions on TRAIN cases only and write a packet: each question's
               wording, its fitted threshold, and the train cases it got wrong (false alarms and
               misses), plus a few it got right for contrast. Eval cases never appear in the packet,
               so the rewriter cannot overfit to them.
  2. (agent)   read the packet, write a candidate questions file. Change wording, criteria, split a
               question into parts, add a checker question. Keep question names stable.
  3. compare   run baseline and candidate on the same cases. Per question, the candidate wins only if
               its TRAIN loss drops by more than run-to-run noise. Eval numbers are printed for both
               so you can see whether the win held. Accepted questions are written to --out.

Loss = cost-weighted errors at the best train threshold, tie-broken by log-loss (small sets saturate
at zero errors quickly; log-loss still tells a confident right answer from a lucky one).

Usage
  python3 optimize_questions.py misses  --cases c.jsonl --questions q.json --out packet.json
  python3 optimize_questions.py compare --cases c.jsonl --baseline q.json --candidate q2.json --out accepted.json
Options: --costs costs.json, --eval-fraction 0.3, --cache-dir .jev_cache, --offline, --max-examples 8
Only noul questions are optimised here; use ensemble.py for choice members.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate import confusion, fit_noul, get_answers, load_jsonl, split_of  # noqa: E402

NOISE = 0.02  # observed run-to-run jitter of a Jev probability; a win smaller than this is not a win


def qhash(questions: dict) -> str:
    return hashlib.sha256(json.dumps(questions, sort_keys=True).encode()).hexdigest()[:12]


def answers_for(cases, questions, a):
    os.makedirs(a.cache_dir, exist_ok=True)
    cache = os.path.join(a.cache_dir, f"{qhash(questions)}.cache.jsonl")  # new wording -> new cache
    return get_answers(cases, questions, cache, a.offline, a.model)


def logloss(pairs) -> float:
    if not pairs:
        return float("nan")
    return -sum(math.log(min(max(p if t else 1 - p, 0.01), 0.99)) for p, t in pairs) / len(pairs)


def score(pairs, cost):
    """(cost-weighted error rate, log-loss, threshold) on the given pairs, threshold fitted on them."""
    thr = fit_noul(pairs, cost)
    tp, fp, fn, tn = confusion(pairs, thr)
    return (cost["fn"] * fn + cost["fp"] * fp) / max(1, len(pairs)), logloss(pairs), thr


def pairs_for(cases, answers, name, split, want):
    return [(answers[c["id"]]["answers"][name]["noul"], bool(c["labels"][name]))
            for c in cases if name in c.get("labels", {}) and split[c["id"]] == want]


def trim(state, limit=1500):
    text = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + " ...[trimmed]"


def cmd_misses(a):
    cases = load_jsonl(a.cases)
    questions = json.load(open(a.questions, encoding="utf-8"))
    costs = json.load(open(a.costs, encoding="utf-8")) if a.costs else {}
    split = {c["id"]: split_of(c["id"], a.eval_fraction) for c in cases}
    answers = answers_for(cases, questions, a)
    packet = {"note": "TRAIN cases only. Rewrite wording/criteria, split questions, or add checker questions. "
                      "Keep names stable. Jev reads literally, cannot count or compare dates, and sees no question names.",
              "questions": {}}
    for name, q in questions.items():
        if q["type"] != "noul":
            continue
        cost = {"fn": 1, "fp": 1, **costs.get(name, {})}
        train = [c for c in cases if name in c.get("labels", {}) and split[c["id"]] == "train"]
        pairs = pairs_for(cases, answers, name, split, "train")
        if not pairs:
            continue
        loss, ll, thr = score(pairs, cost)
        rows = [(answers[c["id"]]["answers"][name]["noul"], bool(c["labels"][name]), c) for c in train]
        fps = sorted([r for r in rows if r[0] >= thr and not r[1]], key=lambda r: -r[0])[:a.max_examples]
        fns = sorted([r for r in rows if r[0] < thr and r[1]], key=lambda r: r[0])[:a.max_examples]
        shaky = sorted([r for r in rows if abs(r[0] - thr) < 0.15 and ((r[0] >= thr) == r[1])],
                       key=lambda r: abs(r[0] - thr))[:a.max_examples // 2]
        packet["questions"][name] = {
            "current": q, "threshold": thr, "train_n": len(pairs), "train_loss": round(loss, 4),
            "train_logloss": round(ll, 4), "costs": cost,
            "false_alarms": [{"id": c["id"], "p": p, "state": trim(c["state"])} for p, _, c in fps],
            "misses": [{"id": c["id"], "p": p, "state": trim(c["state"])} for p, _, c in fns],
            "right_but_shaky": [{"id": c["id"], "p": p, "truth": t, "state": trim(c["state"])} for p, t, c in shaky],
        }
        print(f"{name}: train n={len(pairs)} loss={loss:.4f} logloss={ll:.4f} thr={thr} "
              f"false_alarms={len(fps)} misses={len(fns)}")
    json.dump(packet, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"packet written to {a.out} (eval cases withheld)")


def cmd_compare(a):
    cases = load_jsonl(a.cases)
    base = json.load(open(a.baseline, encoding="utf-8"))
    cand = json.load(open(a.candidate, encoding="utf-8"))
    costs = json.load(open(a.costs, encoding="utf-8")) if a.costs else {}
    split = {c["id"]: split_of(c["id"], a.eval_fraction) for c in cases}
    ans_b, ans_c = answers_for(cases, base, a), answers_for(cases, cand, a)
    accepted, any_win = dict(base), False
    print("| question | version | train loss | train logloss | eval errors (FP/FN of n) | verdict |\n|---|---|---|---|---|---|")
    for name in base:
        if base[name]["type"] != "noul" or name not in cand or cand[name] == base[name]:
            continue
        cost = {"fn": 1, "fp": 1, **costs.get(name, {})}
        rows = {}
        for tag, ans in (("baseline", ans_b), ("candidate", ans_c)):
            tr, ev = pairs_for(cases, ans, name, split, "train"), pairs_for(cases, ans, name, split, "eval")
            loss, ll, thr = score(tr, cost)
            _, fp, fn, _ = confusion(ev, thr)
            rows[tag] = (loss, ll, fp, fn, len(ev))
        (bl, bll, *_), (cl, cll, *_) = rows["baseline"], rows["candidate"]
        win = cl < bl - 1e-9 or (abs(cl - bl) <= 1e-9 and cll < bll - NOISE)
        if win:
            accepted[name], any_win = cand[name], True
        for tag in ("baseline", "candidate"):
            loss, ll, fp, fn, n = rows[tag]
            verdict = ("ACCEPT" if win else "reject (no train gain beyond noise)") if tag == "candidate" else ""
            print(f"| `{name}` | {tag} | {loss:.4f} | {ll:.4f} | {fp}/{fn} of {n} | {verdict} |")
        _, _, bfp, bfn, _ = rows["baseline"]
        _, _, cfp, cfn, _ = rows["candidate"]
        if win and (cfp + cfn) > (bfp + bfn):
            print(f"> WARNING `{name}`: accepted on train but WORSE on eval ({bfp + bfn} -> {cfp + cfn} errors). "
                  "Likely overfit to the packet; add cases or revert.")
    for name in cand:  # brand-new questions (checkers, split parts) ride along; ensemble.py decides their weight
        if name not in base:
            accepted[name] = cand[name]
            print(f"| `{name}` | new | n/a | n/a | n/a | added (weigh it with ensemble.py) |")
    json.dump(accepted, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\n{'accepted questions' if any_win else 'no rewrite beat the baseline; baseline kept'} written to {a.out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("misses", "compare"):
        p = sub.add_parser(name)
        p.add_argument("--cases", required=True)
        p.add_argument("--costs")
        p.add_argument("--eval-fraction", type=float, default=0.3)
        p.add_argument("--cache-dir", default=".jev_cache")
        p.add_argument("--offline", action="store_true")
        p.add_argument("--model", default=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-1.13.0"))
        p.add_argument("--out", required=True)
        if name == "misses":
            p.add_argument("--questions", required=True)
            p.add_argument("--max-examples", type=int, default=8)
        else:
            p.add_argument("--baseline", required=True)
            p.add_argument("--candidate", required=True)
    a = ap.parse_args(argv)
    (cmd_misses if a.cmd == "misses" else cmd_compare)(a)


if __name__ == "__main__":
    main()
