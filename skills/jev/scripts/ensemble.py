#!/usr/bin/env python3
"""Multi-Jev: several questions vote on one judgement, with weights learned from YOUR labels.

Why: one broad question is Jev's weakest shape (62-89% on phishing in two independent tests),
while a handful of narrow questions combined in code reached 95%. Members cost almost nothing
extra, because every member rides in the SAME call: state is billed once and question count does
not move latency. This script learns how much to trust each member instead of guessing.

Two modes, picked by the target's member types:

  binary  members are noul/score questions (different angles, phrasings, checker questions).
          A logistic regression (standard library, gradient descent) maps member answers to
          the label. Reports eval accuracy for: best single member, plain mean, fitted ensemble.

  choice  members are choice questions over the SAME option names (different phrasings or
          descriptions). Probabilities are averaged with weights from each member's train
          accuracy. Reports eval accuracy for each member, plain average, weighted average.

Input
  --cases cases.jsonl      {"id","state","labels":{"<target>": 0/1 or option name}}
  --questions q.json       all member questions (API `questions` object)
  --target NAME            label key to predict
  --members a,b,c          member question names (default: every question in the file)
  --answers cache.jsonl    answer cache (one battery call per case; rerun with --offline for free)
  --eval-fraction 0.3      held-out share, deterministic by case id
  --out ensemble.json      weights + how to combine, for use in your app

Published numbers are the EVAL split. Weights are fitted on train only.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate import get_answers, load_jsonl, split_of  # noqa: E402


def feature(ans: dict) -> float:
    """One number per member answer. Noul: its probability. Score: expected score scaled to 0-1."""
    if ans["type"] == "noul":
        return float(ans["noul"])
    if ans["type"] == "score":
        top = max(1, len(ans.get("legend", {})) - 1)
        return float(ans["score"]) / top
    raise ValueError("binary mode takes noul or score members only")


def _logit(p: float) -> float:
    p = min(max(p, 0.01), 0.99)  # Jev saturates at 0.01/0.99; clip so one member cannot dominate
    return math.log(p / (1 - p))


def _sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-max(min(z, 30), -30)))


def fit_logistic(X, y, l2=0.1, steps=3000, lr=0.1):
    """X rows are member logits. L2 keeps weights sane on the small sets people actually have."""
    n, k = len(X), len(X[0])
    w, b = [0.0] * k, 0.0
    for _ in range(steps):
        gw, gb = [0.0] * k, 0.0
        for row, t in zip(X, y):
            err = _sigmoid(sum(wi * xi for wi, xi in zip(w, row)) + b) - t
            for j in range(k):
                gw[j] += err * row[j]
            gb += err
        for j in range(k):
            w[j] -= lr * (gw[j] / n + l2 * w[j])
        b -= lr * gb / n
    return w, b


def predict(w, b, row) -> float:
    return _sigmoid(sum(wi * xi for wi, xi in zip(w, row)) + b)


def acc(pairs, thr=0.5) -> float:
    return sum(1 for p, t in pairs if (p >= thr) == bool(t)) / len(pairs) if pairs else float("nan")


def best_threshold(pairs) -> float:
    grid = [x / 100 for x in range(5, 96)]
    return min(grid, key=lambda t: (-acc(pairs, t), abs(t - 0.5)))


def run_binary(rows, members, out):
    train = [r for r in rows if r["split"] == "train"]
    ev = [r for r in rows if r["split"] == "eval"]
    Xtr = [[_logit(feature(r["answers"][m])) for m in members] for r in train]
    ytr = [int(r["label"]) for r in train]
    w, b = fit_logistic(Xtr, ytr)

    print("| setup | threshold (train) | train acc | eval acc |\n|---|---|---|---|")
    results = {}
    for m in members:
        tr = [(feature(r["answers"][m]), r["label"]) for r in train]
        # a member may be phrased so that yes means the label is 0; flip it if that fits train better
        flip = acc(tr, 0.5) < 0.5
        f = (lambda p: 1 - p) if flip else (lambda p: p)
        tr = [(f(p), t) for p, t in tr]
        thr = best_threshold(tr)
        e = [(f(feature(r["answers"][m])), r["label"]) for r in ev]
        results[m] = {"threshold": thr, "eval_acc": acc(e, thr), "flipped": flip}
        print(f"| member `{m}`{' (inverted)' if flip else ''} | {thr} | {acc(tr, thr):.3f} | {acc(e, thr):.3f} |")
    def mean(r):  # inverted members count as 1 - p, or the mean would cancel itself out
        return sum((1 - feature(r["answers"][m])) if results[m]["flipped"] else feature(r["answers"][m])
                   for m in members) / len(members)

    mean_tr = [(mean(r), r["label"]) for r in train]
    mean_ev = [(mean(r), r["label"]) for r in ev]
    thr_mean = best_threshold(mean_tr)
    print(f"| plain mean of members | {thr_mean} | {acc(mean_tr, thr_mean):.3f} | {acc(mean_ev, thr_mean):.3f} |")
    ens_tr = [(predict(w, b, x), t) for x, t in zip(Xtr, ytr)]
    ens_ev = [(predict(w, b, [_logit(feature(r["answers"][m])) for m in members]), r["label"]) for r in ev]
    thr_ens = best_threshold(ens_tr)
    print(f"| **fitted ensemble** | {thr_ens} | {acc(ens_tr, thr_ens):.3f} | **{acc(ens_ev, thr_ens):.3f}** |")
    print("\nweights (on member logits): " + ", ".join(f"`{m}` {wi:+.2f}" for m, wi in zip(members, w)) + f", bias {b:+.2f}")
    near_zero = [m for m, wi in zip(members, w) if abs(wi) < 0.05]
    if near_zero:
        print("members adding almost nothing (drop or rewrite): " + ", ".join(near_zero))
    out.update(mode="binary", members=members, weights=dict(zip(members, w)), bias=b, threshold=thr_ens,
               eval={"n": len(ev), "ensemble_acc": acc(ens_ev, thr_ens), "mean_acc": acc(mean_ev, thr_mean),
                     "best_member_acc": max(v["eval_acc"] for v in results.values())},
               combine="p = sigmoid(bias + sum(weights[m] * logit(clip(answer_m, 0.01, 0.99))))")
    return ens_ev, thr_ens


def run_choice(rows, members, out):
    train = [r for r in rows if r["split"] == "train"]
    ev = [r for r in rows if r["split"] == "eval"]

    def member_acc(rs, m):
        return sum(1 for r in rs if r["answers"][m]["choice"] == r["label"]) / len(rs) if rs else float("nan")

    def combined(r, weights):
        tot = {}
        for m in members:
            for opt, p in r["answers"][m]["probabilities"].items():
                tot[opt] = tot.get(opt, 0.0) + weights[m] * p
        best = max(tot, key=tot.get)
        ranked = sorted(tot.values(), reverse=True)
        margin = (ranked[0] - ranked[1]) / sum(weights.values()) if len(ranked) > 1 else 1.0
        return best, margin

    print("| setup | train acc | eval acc |\n|---|---|---|")
    for m in members:
        print(f"| member `{m}` | {member_acc(train, m):.3f} | {member_acc(ev, m):.3f} |")
    flat = {m: 1.0 for m in members}
    # weight = how much better than chance-ish the member is on train; floor keeps every member alive
    fitted = {m: max(member_acc(train, m), 0.05) ** 2 for m in members}
    for name, wts in (("plain average", flat), ("**weighted average**", fitted)):
        tr = sum(1 for r in train if combined(r, wts)[0] == r["label"]) / len(train)
        e = sum(1 for r in ev if combined(r, wts)[0] == r["label"]) / len(ev)
        print(f"| {name} | {tr:.3f} | {e:.3f} |")
    margins = sorted(((combined(r, fitted)[1], combined(r, fitted)[0] == r["label"]) for r in ev), reverse=True)
    print("\ncoverage vs accuracy on eval (answer only when the top-2 margin is at least X; send the rest to a fallback):")
    print("| margin >= | share answered | accuracy on answered |\n|---|---|---|")
    for cut in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7):
        kept = [ok for mg, ok in margins if mg >= cut]
        if kept:
            print(f"| {cut} | {len(kept) / len(margins):.2f} | {sum(kept) / len(kept):.3f} |")
    out.update(mode="choice", members=members, weights=fitted,
               eval={"n": len(ev), "weighted_acc": sum(1 for r in ev if combined(r, fitted)[0] == r["label"]) / len(ev),
                     "best_member_acc": max(member_acc(ev, m) for m in members)},
               combine="score[option] = sum(weights[m] * probabilities_m[option]); pick the max; "
                       "margin = (top1 - top2) / sum(weights); low margin -> fallback")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--members")
    ap.add_argument("--answers", default="jev_ensemble.cache.jsonl")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--eval-fraction", type=float, default=0.3)
    ap.add_argument("--model", default=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-1.13.0"))
    ap.add_argument("--out", default="ensemble.json")
    a = ap.parse_args(argv)

    questions = json.load(open(a.questions, encoding="utf-8"))
    members = a.members.split(",") if a.members else list(questions)
    unknown = [m for m in members if m not in questions]
    if unknown:
        sys.exit("unknown members: " + ", ".join(unknown))
    cases = [c for c in load_jsonl(a.cases) if a.target in c.get("labels", {})]
    if len(cases) < 20:
        sys.exit(f"only {len(cases)} cases carry the label '{a.target}'; an ensemble needs at least 20, ideally 100+")
    answers = get_answers(cases, questions, a.answers, a.offline, a.model)
    rows = [{"id": c["id"], "label": c["labels"][a.target], "answers": answers[c["id"]]["answers"],
             "split": split_of(c["id"], a.eval_fraction)} for c in cases]
    n_eval = sum(1 for r in rows if r["split"] == "eval")
    tokens = sum(answers[c["id"]]["input_tokens"] for c in cases)
    print(f"# Multi-Jev ensemble for `{a.target}`\n\ncases {len(rows)} (train {len(rows) - n_eval}, eval {n_eval}) | "
          f"{len(members)} members in one call | input tokens {tokens} (~${tokens * 0.042 / 1e6:.4f})\n")
    if n_eval < 30:
        print(f"> WARNING: {n_eval} eval cases. Direction only.\n")
    types = {questions[m]["type"] for m in members}
    out = {"target": a.target, "model": a.model}
    if types <= {"noul", "score"}:
        run_binary(rows, members, out)
    elif types == {"choice"}:
        run_choice(rows, members, out)
    else:
        sys.exit("members must be all noul/score (binary mode) or all choice (choice mode)")
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"\nensemble written to {a.out}")


if __name__ == "__main__":
    main()
