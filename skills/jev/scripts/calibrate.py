#!/usr/bin/env python3
"""Calibrate Jev thresholds on YOUR labelled cases, with a held-out split.

Why: a Jev probability is not a decision. 0.5 is a knife edge (answers jitter
about +-0.02 run to run), wording and threshold interact, and the right cut
depends on what a miss costs versus a false alarm. This script turns
probabilities into per-question decision rules you can defend.

Input
  --cases cases.jsonl   one JSON object per line:
                        {"id": "c1", "state": <string or object>, "labels": {"<question>": <truth>}}
                        truth: 0/1 for noul, option name for choice, level index for score
  --questions q.json    the API `questions` object (name -> question)
  --costs costs.json    optional {"<question>": {"fn": 5, "fp": 1}}  (default fn=1, fp=1)
  --answers cache.jsonl answers are cached here; rerun with --offline to re-score without calls
  --eval-fraction 0.3   held-out share, split deterministically by case id (stable across runs)
  --band                also fit a three-way band per noul: <= low = confident no,
                        >= high = confident yes, between = send to fallback (LLM / human)

Output: a Markdown report on stdout and --out thresholds.json.
The published numbers are the EVAL split. Train numbers are shown only to spot overfitting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GRID = [round(x / 100, 2) for x in range(5, 96, 1)]


def split_of(case_id: str, eval_fraction: float) -> str:
    h = int(hashlib.sha256(case_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "eval" if h < eval_fraction else "train"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def get_answers(cases, questions, cache_path, offline, model):
    cache = {}
    if cache_path and os.path.exists(cache_path):
        for row in load_jsonl(cache_path):
            cache[row["id"]] = row
    missing = [c for c in cases if c["id"] not in cache]
    if missing and offline:
        sys.exit(f"--offline but {len(missing)} cases have no cached answers")
    if missing:
        from jev_client import ask  # imported lazily so --offline needs no key
        with open(cache_path, "a", encoding="utf-8") as out:
            for c in missing:
                r = ask(c["state"], questions, model=model)  # one battery call per case
                row = {"id": c["id"], "model": r["model"], "answers": r["answers"],
                       "input_tokens": r["usage"]["input_tokens"], "latency_ms": r["_latency_ms"]}
                cache[c["id"]] = row
                out.write(json.dumps(row) + "\n")
    return cache


def confusion(pairs, thr):
    tp = sum(1 for p, t in pairs if p >= thr and t)
    fp = sum(1 for p, t in pairs if p >= thr and not t)
    fn = sum(1 for p, t in pairs if p < thr and t)
    tn = sum(1 for p, t in pairs if p < thr and not t)
    return tp, fp, fn, tn


def rates(tp, fp, fn, tn):
    tpr = tp / (tp + fn) if tp + fn else None
    tnr = tn / (tn + fp) if tn + fp else None
    prec = tp / (tp + fp) if tp + fp else None
    return tpr, tnr, prec


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


def fit_noul(train, cost):
    best = None
    for thr in GRID:
        tp, fp, fn, tn = confusion(train, thr)
        loss = cost["fn"] * fn + cost["fp"] * fp
        # tie-break toward the middle of the flat region: prefer thresholds nearer 0.5
        key = (loss, abs(thr - 0.5))
        if best is None or key < best[0]:
            best = (key, thr)
    return best[1]


def fit_band(train, max_err=0.02):
    """Three-way routing: p <= low -> confident no, p >= high -> confident yes,
    in between -> fallback (LLM or human). `high` is the lowest cut whose yes-zone
    error rate on train stays <= max_err; `low` the highest cut whose no-zone does.
    If the zones meet or overlap, train separates cleanly at one cut: use it for both."""
    def zone_ok(zone, wrong):
        return bool(zone) and sum(1 for _, y in zone if y == wrong) / len(zone) <= max_err

    highs = [t for t in GRID if zone_ok([(p, y) for p, y in train if p >= t], False)]
    lows = [t for t in GRID if zone_ok([(p, y) for p, y in train if p <= t], True)]
    if not highs or not lows:
        return None, None
    high, low = min(highs), max(lows)
    if low >= high:  # clean separation: any cut in [high, low] works; take the middle
        mid = round((low + high) / 2, 2)
        return mid, mid
    return low, high


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--costs")
    ap.add_argument("--answers", default="jev_answers.cache.jsonl")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--eval-fraction", type=float, default=0.3)
    ap.add_argument("--band", action="store_true")
    ap.add_argument("--model", default=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-1.13.0"))
    ap.add_argument("--out", default="thresholds.json")
    a = ap.parse_args(argv)

    cases = load_jsonl(a.cases)
    questions = json.load(open(a.questions, encoding="utf-8"))
    costs = json.load(open(a.costs, encoding="utf-8")) if a.costs else {}
    answers = get_answers(cases, questions, a.answers, a.offline, a.model)
    split = {c["id"]: split_of(c["id"], a.eval_fraction) for c in cases}

    n_eval = sum(1 for s in split.values() if s == "eval")
    tokens = sum(answers[c["id"]]["input_tokens"] for c in cases)
    models_seen = sorted({answers[c["id"]]["model"] for c in cases})
    print(f"# Jev calibration report\n\ncases: {len(cases)} (train {len(cases) - n_eval}, eval {n_eval}) | "
          f"model(s): {', '.join(models_seen)} | input tokens: {tokens} (~${tokens * 0.042 / 1e6:.5f})\n")
    if n_eval < 20:
        print(f"> WARNING: only {n_eval} eval cases. Treat every number below as direction only.\n")
    if len(models_seen) > 1:
        print("> WARNING: answers came from more than one model version; recalibrate on one pinned model.\n")

    result = {"model": models_seen[0] if len(models_seen) == 1 else models_seen, "questions": {}}
    for name, q in questions.items():
        rows = [(answers[c["id"]]["answers"][name], c["labels"][name], split[c["id"]])
                for c in cases if name in c.get("labels", {})]
        if not rows:
            print(f"## {name}\n\nno labels, skipped\n")
            continue
        t = q["type"]
        print(f"## {name} ({t})\n")
        if t == "noul":
            train = [(r[0]["noul"], bool(r[1])) for r in rows if r[2] == "train"]
            ev = [(r[0]["noul"], bool(r[1])) for r in rows if r[2] == "eval"]
            cost = {"fn": 1, "fp": 1, **costs.get(name, {})}
            thr = fit_noul(train, cost) if train else 0.5
            entry = {"type": "noul", "threshold": thr, "costs": cost}
            print(f"costs fn={cost['fn']} fp={cost['fp']} -> threshold **{thr}** (fitted on train)\n")
            print("| split | n | TP | FP | FN | TN | TPR | TNR | precision |\n|---|---|---|---|---|---|---|---|---|")
            for label, s in (("train", train), ("eval", ev), ("eval @0.5", ev)):
                th = 0.5 if label == "eval @0.5" else thr
                tp, fp, fn, tn = confusion(s, th)
                tpr, tnr, prec = rates(tp, fp, fn, tn)
                print(f"| {label} | {len(s)} | {tp} | {fp} | {fn} | {tn} | {fmt(tpr)} | {fmt(tnr)} | {fmt(prec)} |")
                if label == "eval":
                    entry["eval"] = {"n": len(s), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "tpr": tpr, "tnr": tnr}
            mid = sum(1 for p, _ in train + ev if 0.35 <= p <= 0.65)
            print(f"\nanswers in the 0.35-0.65 middle band: {mid}/{len(train) + len(ev)}")
            if a.band and train:
                low, high = fit_band(train)
                entry["band"] = {"low": low, "high": high}
                if low is None:
                    print("band: no safe confident zones on train; route everything to fallback or rewrite the question")
                else:
                    auto = sum(1 for p, _ in ev if p <= low or p >= high)
                    wrong = sum(1 for p, y in ev if (p <= low and y) or (p >= high and not y))
                    print(f"band: <= {low} confident no, >= {high} confident yes; eval automated {auto}/{len(ev)}, wrong {wrong}")
            print()
        elif t == "choice":
            for sp in ("train", "eval"):
                s = [(r[0]["choice"], r[1], r[0]["confidence"]) for r in rows if r[2] == sp]
                if not s:
                    continue
                acc = sum(1 for c, y, _ in s if c == y) / len(s)
                hi = [(c, y) for c, y, conf in s if conf >= 0.9]
                hi_acc = (sum(1 for c, y in hi if c == y) / len(hi)) if hi else None
                print(f"- {sp}: accuracy {acc:.2f} on {len(s)}; confidence>=0.9 covers {len(hi)} with accuracy {fmt(hi_acc)}")
                if sp == "eval":
                    wrong = [(y, c) for c, y, _ in s if c != y]
                    if wrong:
                        print(f"- eval confusions (truth -> predicted): {wrong[:10]}")
                    entry = {"type": "choice", "eval_accuracy": acc, "eval_high_conf_accuracy": hi_acc}
            result["questions"][name] = entry
            print()
            continue
        elif t == "score":
            for sp in ("train", "eval"):
                s = [(r[0]["score"], float(r[1])) for r in rows if r[2] == sp]
                if s:
                    mae = sum(abs(p - y) for p, y in s) / len(s)
                    exact = sum(1 for p, y in s if round(p) == y) / len(s)
                    print(f"- {sp}: MAE {mae:.2f}, rounded-exact {exact:.2f} on {len(s)}")
                    if sp == "eval":
                        entry = {"type": "score", "eval_mae": mae, "eval_rounded_exact": exact}
            print()
        result["questions"][name] = entry

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"thresholds written to {a.out}")


if __name__ == "__main__":
    main()
