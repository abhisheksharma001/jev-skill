# Calibration: turning probabilities into decisions you can defend

Jev returns a probability. Your system needs a decision. The gap between them is calibration, and it
is where accuracy is won or lost: the official skill says "thresholds evaluated on the user's data"
but gives no method. This is the method.

## Why you can't skip it
- **0.5 is a knife edge.** Answers jitter about ±0.02 between identical runs.
- **Confidence is not correctness.**
  - One independent test found Jev right only 64% of the time when it said 80-95% (ECE 0.121 vs 0.062
    for a frontier LLM).
  - Another found 3 of 4 mistakes had confidence above 0.8.
  - A vendor cookbook reports 90% accuracy above a 0.9 cut (n=30).
  - These conflict, so measure your own.
- **Wording and threshold interact.** A "clearly and explicitly" suffix cut false positives 11 to 5
  on one dataset and dropped true positives from 0.96 to 0.37 on another.
- **Noul(P) + Noul(not P) need not equal 1** (0.8 observed on ambiguous items). Never carry a
  threshold from one phrasing to another.
- **No fine-tuning exists.** Questions, criteria, state and thresholds are the only knobs you have.

## The procedure

1. **Decide the scoring rule before looking at results.** Write down the bar per question (e.g.
   "TPR >= 0.95 at TNR >= 0.90") and what a miss costs vs a false alarm.
2. **Build the labelled set.** One JSON line per case:
   `{"id": "c1", "state": {...}, "labels": {"<question>": 1}}`.
   - **Size:** 50+ to steer, 200+ to publish numbers, stratified so every class has at least 20 examples.
   - **Hard negatives:** include the near-misses you fear, e.g. past-tense mentions, "booked then
     cancelled", third-party complaints, quoted instructions.
   - **Label quality:** two people label a sample. Label disagreement caps your achievable accuracy,
     so fix ambiguous label definitions first. In our own runs the residual "errors" were mostly
     debatable labels.
   - **Data:** use synthetic or redacted data until data terms are cleared.
3. **Run:**
   ```bash
   python3 scripts/calibrate.py --cases cases.jsonl --questions questions.json \
           --costs costs.json --band --answers answers.cache.jsonl --out thresholds.json
   ```
   - The split is deterministic by case id (default 70/30), so it is stable across runs.
   - Thresholds are fitted on **train** by cost-weighted error.
   - The published numbers are the **eval** rows.
   - `--band` fits three-way routing: confident no, confident yes, and a middle band for fallback.
   - Answers are cached, so re-scoring with new costs is free (`--offline`).
4. **Read the report:**
   - **Eval TPR/TNR vs your bar.** Below bar: fix the question first (see question-design.md), then re-run.
   - **Train much better than eval** means overfit or too few cases, so add cases.
   - **Many answers in the 0.35-0.65 band** means the question is ambiguous to the model. Add
     `criteria.true/false`, split the question, or filter state.
   - **`eval @0.5` row** shows what you would have got with the naive default.
   - **Fewer than 20 eval cases:** the script warns. Treat results as direction only.
5. **Iterate on wording with a frozen eval split.** Change one thing at a time. If you tune wording on
   the eval split, it is no longer held out, so add fresh cases before publishing.
6. **Choice and Score.** The script reports Choice accuracy overall and above confidence 0.9, plus the
   confusions. Lookalike options show up here, so merge or re-describe them. For Score it reports MAE
   and rounded-exact.
7. **Ship `thresholds.json` as config**, next to the questions, with the model version inside it.

## Picking costs
| Situation | fn : fp | Effect |
|---|---|---|
| Missing it is dangerous (incident, human-handoff request, safety flag) | 5 : 1 or more | Lower threshold, more false alarms |
| False alarm is expensive (pages a human, blocks a user, sends an SMS) | 1 : 5 or more | Higher threshold |
| Jev only skips an expensive call on "confident no" | fn high | Only very low probabilities skip |

## When to recalibrate
- `response.model` changes (alias moved, or you changed the pin)
- Question or criteria wording changes, including "harmless" suffixes
- You switch gateway or provider
- New language, new client, new channel
- Input distribution shifts (middle-band share or fallback disagreement rate rises)
- A fixed interval otherwise (monthly is a sane default)

## Honest reporting rules
- Report eval-split numbers with n. Never report train numbers as accuracy.
- Say whether cases are synthetic or real.
- Say who labelled them.
- "Valid shape" is not "correct answer": measure agreement with labels, not parse success.
- Compare against the incumbent *on the same cases*: an LLM, a rule, or a small trained classifier.
  If 250 labels fine-tune a small encoder that beats Jev on your stable task, use the encoder.
