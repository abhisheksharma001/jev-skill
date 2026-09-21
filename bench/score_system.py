#!/usr/bin/env python3
"""Score every setup on the SAME held-out cases. Reads cached Jev answers (bench/work) and a
strong-model prediction file; prints docs/benchmarks/system/results.md content.
Usage: python3 score_system.py --fable-dir <dir with voice_fable_preds.json, b77_fable_preds.json>"""
import argparse, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "jev", "scripts"))
from calibrate import split_of, load_jsonl, fit_noul  # noqa: E402
import ensemble as E  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--fable-dir", required=True); a = ap.parse_args()
W = os.path.join(HERE, "work")
USD = 0.042 / 1e6

def cache(path): return {r["id"]: r for r in load_jsonl(path)}

# ---------- voice (binary) ----------
cases = load_jsonl(os.path.join(W, "voice_cases.jsonl"))
ans = cache(os.path.join(W, "voice.cache.jsonl"))
ens = json.load(open(os.path.join(W, "voice_ensemble.json")))
fable = json.load(open(os.path.join(a.fable_dir, "voice_fable_preds.json")))
opt = {}
for f in glob.glob(os.path.join(W, ".jev_cache", "*.cache.jsonl")):
    opt[os.path.basename(f)] = cache(f)
train = [c for c in cases if split_of(c["id"], 0.3) == "train"]
ev = [c for c in cases if split_of(c["id"], 0.3) == "eval"]
y = {c["id"]: c["labels"]["missed_booking"] for c in cases}

def ens_p(cid):
    z = ens["bias"] + sum(w * E._logit(E.feature(ans[cid]["answers"][m])) for m, w in ens["weights"].items())
    return E._sigmoid(z)

def acc(pred): return sum(1 for c in ev if pred(c["id"]) == y[c["id"]]) / len(ev)
single = lambda cid: int(ans[cid]["answers"]["broad_single"]["noul"] >= 0.53)
# the optimised single question lives in the cache whose answers differ from the baseline's
base_key, cand_key = sorted(opt, key=lambda k: sum(1 for c in train if (opt[k][c["id"]]["answers"]["broad_single"]["noul"] >= 0.5) == bool(y[c["id"]])))
thr_rw = fit_noul([(opt[cand_key][c["id"]]["answers"]["broad_single"]["noul"], bool(y[c["id"]])) for c in train], {"fn": 1, "fp": 1})
rewritten = lambda cid: int(opt[cand_key][cid]["answers"]["broad_single"]["noul"] >= thr_rw)  # threshold fitted on train
multi = lambda cid: int(ens_p(cid) >= ens["threshold"])
def cascade(low, high):
    esc = [c["id"] for c in ev if low < ens_p(c["id"]) < high]
    return acc(lambda cid: fable[cid] if cid in esc else multi(cid)), len(esc) / len(ev)
# band fitted on TRAIN: widest zone with zero train errors outside it
ps = sorted((ens_p(c["id"]), y[c["id"]]) for c in train)
low = max([p for p, t in ps if not any(tt for pp, tt in ps if pp <= p)] or [0.0])
high = min([p for p, t in ps if all(tt for pp, tt in ps if pp >= p)] or [1.0])
c_acc, c_share = cascade(low, high)
tok = sum(ans[c["id"]]["input_tokens"] for c in ev) / len(ev)
print(f"## Voice calls: was this a missed booking? (synthetic, written by a separate agent; held-out n={len(ev)})\n")
print("| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k calls |\n|---|---|---|---|")
print(f"| Jev, one broad question (first draft) | {acc(single):.1%} | 0% | ${tok * USD * 1000 / 6:.3f} |")
print(f"| Jev, same single question rewritten by Fable via `optimize_questions.py` | {acc(rewritten):.1%} | 0% | ${tok * USD * 1000 / 6:.3f} |")
print(f"| Multi-Jev: 6 narrow questions, fitted weights (`ensemble.py`) | {acc(multi):.1%} | 0% | ${tok * USD * 1000:.3f} |")
print(f"| Multi-Jev + Fable on the unsure band ({low:.2f}-{high:.2f}, fitted on train) | {c_acc:.1%} | {c_share:.0%} | ${tok * USD * 1000:.3f} |")
print(f"| Fable alone | {acc(lambda cid: fable[cid]):.1%} | 100% | n/a |\n")

# ---------- banking77 (choice) ----------
cases = load_jsonl(os.path.join(W, "b77_cases.jsonl"))
ans = cache(os.path.join(W, "b77.cache.jsonl"))
fable = json.load(open(os.path.join(a.fable_dir, "b77_fable_preds.json")))
ev = [c for c in cases if split_of(c["id"], 0.3) == "eval"]
train = [c for c in cases if split_of(c["id"], 0.3) == "train"]
y = {c["id"]: c["labels"]["intent"] for c in cases}
def member(m): return lambda cid: ans[cid]["answers"][m]["choice"]
def margin(cid):
    p = sorted(ans[cid]["answers"]["described"]["probabilities"].values(), reverse=True)
    return p[0] - p[1]
def acc(pred, rows=None):
    rows = rows or ev
    return sum(1 for c in rows if pred(c["id"]) == y[c["id"]]) / len(rows)
tok = sum(ans[c["id"]]["input_tokens"] for c in ev) / len(ev) / 3  # three members shared each call
print(f"## Banking77 intent routing, 77 options (public, PolyAI, CC-BY-4.0; seeded 400-row sample; held-out n={len(ev)})\n")
print("| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k messages |\n|---|---|---|---|")
print(f"| Jev, option names only (first draft) | {acc(member('names_only')):.1%} | 0% | ${tok * USD * 1000:.3f} |")
print(f"| Jev, options described by Fable at design time | {acc(member('described')):.1%} | 0% | ${tok * USD * 1000:.3f} |")
for target in (0.10, 0.20, 0.30):
    cut = sorted(margin(c["id"]) for c in train)[int(len(train) * target)]  # cut chosen on TRAIN
    esc = {c["id"] for c in ev if margin(c["id"]) < cut}
    print(f"| Described + Fable when top-2 margin < {cut:.2f} (cut set on train for ~{target:.0%}) | "
          f"{acc(lambda cid: fable[cid] if cid in esc else member('described')(cid)):.1%} | {len(esc) / len(ev):.0%} | ${tok * USD * 1000:.3f} |")
print(f"| Fable alone | {acc(lambda cid: fable[cid]):.1%} | 100% | n/a |")
