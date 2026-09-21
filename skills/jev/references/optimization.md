# Closing the gap to a frontier model

Jev's weights are fixed and there is no fine-tuning. You cannot make Jev smarter. You can make the
**system** around it score close to a frontier model, because most of a first draft's error is in
the question and the composition, not in the model. Three levers, in the order to try them. Each has
a script, and each reports held-out numbers so you can see whether it worked.

Measured on this repo's benchmark (`docs/benchmarks/system/results.md`, held-out, single run, small n):

| Lever | Voice: missed booking (synthetic, n=44) | Banking77 routing (public, n=134) |
|---|---|---|
| First-draft single question | 84.1% | 76.1% |
| 1. Strong model rewrites the question | **100%** | **83.6%** |
| 2. Multi-Jev with fitted weights | 97.7% | 83.6% (no gain) |
| 3. Cascade: frontier model on the unsure share | 100% at 18% escalated | 89.6% at 13%, 91.8% at 32% |
| Frontier model alone | 100% | 91.8% |

## Lever 1: spend the strong model's intelligence on the question, once

A frontier model is good at reading failures and rewriting wording. Jev is cheap at answering. So
the agent running this skill (you) rewrites, and held-out data referees.

```bash
python3 scripts/optimize_questions.py misses  --cases cases.jsonl --questions q.json --out packet.json
# read packet.json: false alarms, misses, right-but-shaky cases. TRAIN cases only.
# write q2.json
python3 scripts/optimize_questions.py compare --cases cases.jsonl --baseline q.json --candidate q2.json --out accepted.json
```

How to rewrite well:
- **Name the failure patterns you see** and put each one into `criteria.true` or `criteria.false` as a
  concrete situation. In the voice benchmark the misses were "date but no time", "book it, then the
  agent ends the call" and "transferred"; the false alarms were all "caller says they'll call back".
  Listing those situations took the question from 7 held-out errors to 0.
- **Describe options as policies.** On Banking77, adding a one-sentence "when this applies" to each of
  77 option names gave +7.5 points. Say what separates lookalike options ("a timing question" vs "has
  not arrived yet").
- **Do not add strictness suffixes** ("only if clearly true"). They move probabilities, not understanding.
- **One change at a time**, and let `compare` decide. It accepts a rewrite only when train loss drops
  by more than run-to-run noise, and it warns when an accepted rewrite did worse on eval (overfit to
  the packet).
- The packet never contains eval cases. Do not go and read them. Once you have looked at eval
  failures, that split is no longer held out: add fresh cases before publishing a number.

## Lever 2: multi-Jev (several questions vote, weights learned from labels)

```bash
python3 scripts/ensemble.py --cases cases.jsonl --questions members.json --target <label> --out ensemble.json
```
All members ride in one call, so the extra cost is a few tokens per question and no extra latency.

What to put in the ensemble:
- **Parts of a composite judgement.** "Missed booking" = wanted to book AND NOT confirmed AND NOT
  withdrew. Ask each part, and let the fit learn the weights (it learned negative weights for the two
  NOT parts on its own).
- **Checker questions** that see the same situation from another side ("the agent deferred scheduling",
  "the call ended abruptly").
- **The broad question too.** It is a useful member even when it is a weak judge alone.

What does not help: **paraphrases of the same question.** On Banking77, three phrasings averaged to
exactly the best single member. Their errors are correlated. Members must look at *different evidence*,
not say the same thing differently.

The script prints each member's held-out accuracy, the plain mean, and the fitted ensemble, and names
members whose weight is near zero so you can drop them. For Choice members it prints a
coverage-vs-accuracy table by top-2 margin, which is the input to lever 3.

Need at least ~100 labelled cases for stable weights; with fewer, prefer the plain mean or code-side
AND/OR (`min`, `max`).

## Lever 3: cascade to the frontier model on the unsure share only

Jev answers when it is sure; the frontier model (or a human) answers the rest.
- Binary: the unsure band is `low < p < high`, fitted on train by `calibrate.py --band` or from the
  ensemble probability.
- Choice: the unsure cases are those whose **top-2 probability margin** is below a cut. Pick the cut on
  train for the escalation share you can afford. On Banking77, answering only at margin >= 0.7 gave
  94.7% on the 71% answered.
- The fallback must not see Jev's answer on high-stakes paths (a model shown a first opinion tends to
  agree with it).
- Report two numbers together, always: **system accuracy** and **share escalated**. Accuracy without
  the escalation share is meaningless, because 100% escalation trivially equals the frontier model.

Rule of thumb from the benchmark: design-time rewriting is free at run time and gave the largest
single gain on both datasets, so exhaust lever 1 before paying for lever 3.

## When the gap will not close
- The label itself is noisy or disputed (Banking77 has known label noise; it caps every setup).
- The judgement needs arithmetic, dates, counting or several reasoning hops. Move those to code.
- The input needs knowledge outside the state. Put that knowledge into the state or the criteria.
- Non-English input. Calibrate per language and expect a larger escalation share.

## Honest reporting for these levers
- Fit on train, report on eval, say n. Say which lever produced which gain.
- Say whether data is synthetic. Say who wrote cases and who wrote questions.
- A lever that did not help is a result. Publish it (see lever 2 on Banking77).
