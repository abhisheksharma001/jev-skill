# System benchmark: how close can a Jev system get to a frontier model?

Run 2026-09-21, model `jev-1.13.0`. "Fable" = Claude Fable 5.1 judging the same held-out cases, labels hidden,
run through Claude Code subagents (predictions are committed beside this file; not reproducible from an API key).
Thresholds, weights and escalation cuts were fitted on the train split only. Every number below is held-out.

## Voice calls: was this a missed booking? (synthetic, written by a separate agent; held-out n=44)

| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k calls |
|---|---|---|---|
| Jev, one broad question (first draft) | 84.1% | 0% | $0.006 |
| Jev, same single question rewritten by Fable via `optimize_questions.py` | 100.0% | 0% | $0.006 |
| Multi-Jev: 6 narrow questions, fitted weights (`ensemble.py`) | 97.7% | 0% | $0.039 |
| Multi-Jev + Fable on the unsure band (0.21-0.89, fitted on train) | 100.0% | 18% | $0.039 |
| Fable alone | 100.0% | 100% | n/a |

## Banking77 intent routing, 77 options (public, PolyAI, CC-BY-4.0; seeded 400-row sample; held-out n=134)

| Setup | Held-out accuracy | Share of cases sent to Fable | Jev cost per 1k messages |
|---|---|---|---|
| Jev, option names only (first draft) | 76.1% | 0% | $0.087 |
| Jev, options described by Fable at design time | 83.6% | 0% | $0.087 |
| Described + Fable when top-2 margin < 0.48 (cut set on train for ~10%) | 89.6% | 13% | $0.087 |
| Described + Fable when top-2 margin < 0.76 (cut set on train for ~20%) | 90.3% | 24% | $0.087 |
| Described + Fable when top-2 margin < 0.90 (cut set on train for ~30%) | 91.8% | 32% | $0.087 |
| Fable alone | 91.8% | 100% | n/a |

## What this shows

- **Most of the gap was the question, not the model.** A first-draft question scored 84.1% (voice) and
  76.1% (Banking77). Wording written by a strong model at design time lifted those to 100% and 83.6% with no
  extra run-time cost. That intelligence is paid for once.
- **Multi-Jev helps on composite judgements** (voice: 97.7% from six narrow questions) and **did not help on
  paraphrase voting** (Banking77: three phrasings averaged to the same 83.6%; their errors are correlated).
- **A margin-based cascade closes the rest.** On Banking77, sending 13% of messages to Fable reached 89.6%
  against Fable's 91.8%; sending 32% matched it.

## Against the frozen goal (within 3 points of Fable, at most 10% of cases sent to Fable)

| Dataset | Result | Verdict |
|---|---|---|
| Voice (synthetic) | 100% with 0% sent to Fable vs Fable 100% | met |
| Banking77 (public) | 89.6% at 13% sent (2.2 points behind) | accuracy met, escalation share missed by 3 points |

## Read with care

- Small held-out sets: n=44 and n=134. One case is 2.3 and 0.7 points.
- The voice set is synthetic. A separate agent wrote the cases; the label definitions were shared with the
  question author, which flatters every setup including Fable.
- The rewritten voice question was written after reading train misses only; eval cases were withheld by the script.
- Banking77 labels are noisy (known issue with this dataset), which caps every setup.
- Cost column is Jev input tokens only at $0.042 per million. Fable cost is shown as the share of cases
  escalated, because no Fable API price was measured here.
- Single run. Jev answers jitter about ±0.02, so cases near a cut can flip.

## Reproduce

```bash
export TYPESAFE_API_KEY=...
python3 bench/prep_banking77.py
cd bench/work
python3 ../../skills/jev/scripts/ensemble.py --cases b77_cases.jsonl --questions b77_questions.json --target intent --answers b77.cache.jsonl --out b77_ensemble.json
python3 ../../skills/jev/scripts/ensemble.py --cases voice_cases.jsonl --questions ../voice_questions.json --target missed_booking --answers voice.cache.jsonl --out voice_ensemble.json
python3 ../score_system.py --fable-dir ../../docs/benchmarks/system
```
Total TypeSafe spend for this benchmark: about $0.12.
