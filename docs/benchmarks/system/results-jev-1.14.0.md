# System benchmark on jev-1.14.0 (re-run of the 1.13.0 benchmark)

Run 2026-11-11, model `jev-1.14.0`. This sits NEXT TO [`results.md`](results.md) (run 2026-09-21, `jev-1.13.0`); the
1.13.0 numbers there are unchanged. Same held-out cases, same questions and option descriptions, same committed
Fable predictions (Claude Fable 5.1, labels hidden, run through Claude Code subagents; not reproducible from an API
key). Every Jev answer was regenerated with `--model jev-1.14.0`; all caches hold only that model. Thresholds,
weights and escalation cuts were refitted on the train split only. Every number below is held-out.

The question wording was NOT rewritten for 1.14.0. The voice rewrite (`opt_cand.json`) and the Banking77 option
descriptions were written for 1.13.0 and reused as they were, so this measures "what happens to a system tuned on
1.13.0 when you move the model and refit only the numbers".

## Voice calls: was this a missed booking? (synthetic, written by a separate agent; held-out n=44)

| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k calls |
|---|---|---|---|
| Jev, one broad question (first draft) | 86.4% | 0% | $0.006 |
| Jev, same single question rewritten by Fable via `optimize_questions.py` | 97.7% | 0% | $0.006 |
| Multi-Jev: 6 narrow questions, fitted weights (`ensemble.py`) | 100.0% | 0% | $0.039 |
| Multi-Jev + Fable on the unsure band (0.17-0.87, fitted on train) | 100.0% | 14% | $0.039 |
| Fable alone | 100.0% | 100% | n/a |

## Banking77 intent routing, 77 options (public, PolyAI, CC-BY-4.0; seeded 400-row sample; held-out n=134)

| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k messages |
|---|---|---|---|
| Jev, option names only (first draft) | 73.9% | 0% | $0.087 |
| Jev, options described by Fable at design time | 82.8% | 0% | $0.087 |
| Described + Fable when top-2 margin < 0.32 (cut set on train for ~10%) | 88.1% | 9% | $0.087 |
| Described + Fable when top-2 margin < 0.65 (cut set on train for ~20%) | 90.3% | 23% | $0.087 |
| Described + Fable when top-2 margin < 0.86 (cut set on train for ~30%) | 91.8% | 35% | $0.087 |
| Fable alone | 91.8% | 100% | n/a |

## 1.13.0 vs 1.14.0 (held-out; voice n=44, Banking77 n=134)

One voice case is 2.3 points; one Banking77 case is 0.7 points. "Cases" is the signed change in correct answers.

| Setup | 1.13.0 | 1.14.0 | Change (points) | Change (cases) |
|---|---|---|---|---|
| Voice: one broad question (first draft) | 84.1% | 86.4% | +2.3 | +1 of 44 |
| Voice: single question rewritten by Fable | 100.0% | 97.7% | -2.3 | -1 of 44 |
| Voice: multi-Jev, 6 narrow questions | 97.7% | 100.0% | +2.3 | +1 of 44 |
| Voice: multi-Jev + Fable on unsure band (share sent) | 100.0% (18%) | 100.0% (14%) | 0.0 | 0 of 44 |
| Banking77: option names only | 76.1% | 73.9% | -2.2 | -3 of 134 |
| Banking77: options described | 83.6% | 82.8% | -0.7 | -1 of 134 |
| Banking77: described + Fable, cut for ~10% (share sent) | 89.6% (13%) | 88.1% (9%) | -1.5 | -2 of 134 |
| Banking77: described + Fable, cut for ~20% (share sent) | 90.3% (24%) | 90.3% (23%) | 0.0 | 0 of 134 |
| Banking77: described + Fable, cut for ~30% (share sent) | 91.8% (32%) | 91.8% (35%) | 0.0 | 0 of 134 |
| Fable alone (same predictions, same cases) | 100.0% / 91.8% | 100.0% / 91.8% | 0.0 | 0 |

No setup moved by more than 2.3 points. Every change is 1 to 3 cases, which is inside the run-to-run jitter of a
single run on sets this small, so this run shows no measurable regression or gain from 1.13.0 to 1.14.0 on these two
tasks. It does not say the two models are equal: an independent re-run elsewhere saw other tasks move by much more
(see `docs/research/2026-11-11/evidence.md`).

## Against the frozen goal (within 3 points of Fable, at most 10% of cases sent to Fable)

| Dataset | 1.14.0 result | Verdict | 1.13.0 verdict (for comparison) |
|---|---|---|---|
| Voice (synthetic) | 100.0% at 0% sent (multi-Jev), 97.7% at 0% (rewritten single) vs Fable 100% | met | met |
| Banking77 (public) | 88.1% at 9% sent vs Fable 91.8% (3.7 points behind) | share met, accuracy missed by 0.7 points | accuracy met, share missed by 3 points |

On Banking77 the 1.13.0 and 1.14.0 runs each miss the goal in a different way, by about the same size of margin
(1 to 3 cases of 134). Neither run clears both limits at once.

## Read with care

- Small held-out sets: n=44 and n=134. One case is 2.3 and 0.7 points.
- The voice set is synthetic. A separate agent wrote the cases; the label definitions were shared with the
  question author, which flatters every setup including Fable.
- The rewritten voice question was written after reading 1.13.0 train misses only; eval cases were withheld by the
  script. It was reused unchanged on 1.14.0. The same holds for the Banking77 option descriptions.
- The "first draft" voice row uses the fixed 0.53 cut from the 1.13.0 script, not a refit; the other rows refit on
  1.14.0 train answers.
- Banking77 labels are noisy (known issue with this dataset), which caps every setup.
- Cost column is Jev input tokens only at $0.042 per million (the 1.13.0 price used in `results.md`; not re-checked
  for 1.14.0 in this run). Fable cost is shown as the share of cases escalated, because no Fable API price was
  measured here.
- Single run. Jev answers jitter about +/-0.02, so cases near a cut can flip. The Fable predictions were made once, for the
  1.13.0 run, and are shared by both tables.

## Reproduce

```bash
export TYPESAFE_API_KEY=...
python3 bench/prep_banking77.py          # writes bench/work/ (cases and questions; voice cases come from bench/data)
mkdir -p bench/work-jev-1.14.0           # gitignored (bench/work-*/)
# copy voice_cases.jsonl b77_cases.jsonl b77_questions.json opt_base.json opt_cand.json into it; copy NO *.cache.jsonl
cd bench/work-jev-1.14.0
python3 ../../skills/jev/scripts/ensemble.py --cases voice_cases.jsonl --questions ../voice_questions.json --target missed_booking --answers voice.cache.jsonl --model jev-1.14.0 --out voice_ensemble.json
python3 ../../skills/jev/scripts/optimize_questions.py compare --cases voice_cases.jsonl --baseline opt_base.json --candidate opt_cand.json --cache-dir .jev_cache --model jev-1.14.0 --out opt_accepted_114.json
python3 ../../skills/jev/scripts/ensemble.py --cases b77_cases.jsonl --questions b77_questions.json --target intent --answers b77.cache.jsonl --model jev-1.14.0 --out b77_ensemble.json
cd ../..
python3 bench/score_system.py --fable-dir docs/benchmarks/system --work bench/work-jev-1.14.0
```
`score_system.py` prints the model it finds in the caches on its first line.

Spend: 880 Jev battery calls (voice 160, optimize baseline 160, optimize candidate 160, Banking77 400), 2,800,397 input tokens in all (voice 147,312; optimize 75,792 + 102,832; Banking77 2,474,461), which is
about $0.118 at $0.042 per million. The 1.13.0 run cost about $0.12.
