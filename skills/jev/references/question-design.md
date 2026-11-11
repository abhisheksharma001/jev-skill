# Designing Jev questions

Question wording is the main lever on accuracy: Jev has shared weights and no fine-tuning, so you
adapt it only through `state`, `instructions` and `criteria`. Treat questions like code: keep them
in one reviewed file (questions + thresholds together), under version control.

## Contents
1. Request shape
2. Pick the primitive
3. Wording rules (literal reading)
4. State: what to send
5. Batching
6. Worked example: one battery
7. Checklist before the first real call

## 1. Request shape (verified against the live API, 2026-09-21)

```json
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
{
  "model": "jev-1.14.0",
  "state": "<string>  or  {structured JSON}  or  [array]",
  "questions": {
    "billing":  {"type": "noul",   "instructions": "The message is about a billing problem.",
                 "criteria": {"true": "Charges, refunds, invoices, payment failures.",
                              "false": "Anything else, including general account questions."}},
    "tone":     {"type": "choice", "instructions": "Tone of the customer's message.",
                 "criteria": {"angry": "hostile or threatening", "calm": "neutral or polite",
                              "mixed": "both hostile and polite parts"}},
    "urgency":  {"type": "score",  "instructions": "How soon does this need a human?",
                 "criteria": ["can wait", "needs attention this week", "needs attention today"]}
  }
}
```
Response: `answers.<name>`:
- `noul` returns `{"noul": 0.99}`.
- `choice` returns `{"choice", "confidence", "probabilities"}`.
- `score` returns `{"score", "confidence", "legend", "probabilities"}`.
- `usage` has `input_tokens` and `output_tokens`.
- `model` is the version that actually answered, so log it.

Question **names are not sent to the model**. Put everything the model needs in `instructions` and
`criteria`. The yes/no meanings go in `criteria.true` and `criteria.false`. Some wrappers call these
`yesMeans`/`noMeans`, but the API field is `criteria`. `instructions` and every criterion can be a string or
structured JSON.

## 2. Pick the primitive

| You need | Use | Watch out |
|---|---|---|
| Is X true? (gate, flag, pass/fail) | **Noul**: P(true), 0-1 | No `confidence` field. P(X) + P(not X) need not sum to 1 (0.8 seen on ambiguous items), so don't carry thresholds across phrasings. |
| Which one of these? (route, category, outcome) | **Choice**: up to 255 options | A Choice always picks something, even when nothing fits. Pair it with a **companion Noul** ("does any option fit?") and read the Choice only when that Noul is a clear yes; TypeSafe now advises this over an `other`/`none` option, which competes with real options for probability (docs.typesafe.ai/patterns/companion-noul, read 2026-11-11). Use an explicit `none` only where a Noul is not possible. Near-synonym options split the vote: add one Noul per close candidate. Reordering options changed 7/120 answers in one test. When top-2 are within ~0.1, treat as uncertain. |
| How much / how severe? (quality, urgency, relevance) | **Score**: 2-10 ordered levels | Each level is judged on its own; the model never sees level numbers or neighbours, so "worse than the previous level" means nothing. Describe each level fully. |

Don't yes/no everything: a Noul at 0.5 means "unsure", not "medium severity". Use Score for severity.

## 3. Wording rules (Jev reads literally)

1. **One judgement per question.** Hiding several judgements in one question is a documented failure
   mode. Ask A and B separately and combine in code (`min(pA, pB)`). You also learn *which* part fired.
2. **Write the exact condition** you mean, with `criteria` for both yes and no. Adding true/false
   criteria cut false alarms from 11 to 5 on a partner's production notification set.
3. **Options are policies, not labels.** "eat: Drink and eat at the well" made an agent eat at hunger 0.
   Say *when* each option applies; any numeric condition gets computed in code and passed in state.
4. **No arithmetic, counting, dates or multi-hop inside the question.** Compute `days_overdue`,
   `error_count` and `amount_after_discount` in code and put the results in state. Simple cases can pass
   (28/28 in our easy probe), but the vendor documents these as unreliable and errors grow with size.
5. **Don't ask Jev about itself** ("Do you have enough information?"). It said yes about 85% of the time.
6. **Avoid contradictory instructions and criteria.** Align the question text with every option description.
7. **Beware "strictness" suffixes.** "Answer yes only if clearly and explicitly true" cut false
   positives on one dataset but pushed true positives down (0.96 to 0.37) on another. Calibrate wording
   and threshold together; never add a suffix without re-running calibration.
8. **English is strongest.** Calibrate each language separately.

## 4. State: send only what the question needs

- **Filter first.** Accuracy falls as irrelevant detail grows (context rot). Send the fields each
  question needs, not the whole record.
- **Structure beats a flattened blob.** Send JSON with named fields (`{"transcript": [...turns],
  "tool_calls": [...], "claim": "..."}`) and point questions at them ("the `claim` field...").
- **Label untrusted text.** Put user, email or web content in a clearly named field. Jev does not treat
  state as hostile, and fake delimiters were the weakest injection vector in testing.
- **Limits:** 64k tokens per request (state plus all questions); 32k for state plus the longest single
  question. Keep a margin: one request near 58k tokens stalled with no error. Always set a client
  timeout.
- **Text only.** Transcribe audio and describe images before the call.

## 5. Batching (the cost lever)

State is billed once per call, and answers are evaluated per question. So put **every independent
question about one state in one call**:
- In TypeSafe's cookbook (jev-1.12), 13 questions batched were 12.2x cheaper and 10x faster, with the
  same answers.
- In our probe, 1 question and 10 questions both took ~0.89 s.

Split into a second request only when a later question depends on an earlier answer (e.g. route first,
then ask the chosen branch's questions).

## 6. Worked example: post-call QA battery (voice agent)

```json
{
  "model": "jev-1.14.0",
  "state": {"transcript": [{"speaker": "agent", "text": "..."}, {"speaker": "caller", "text": "..."}],
            "call_meta": {"duration_s": 212, "transferred": false}},
  "questions": {
    "booked": {"type": "noul", "instructions": "An appointment was successfully booked during the call.",
               "criteria": {"true": "The agent confirms a specific booked date and time.",
                            "false": "No booking was confirmed, or it failed, or it was only discussed."}},
    "wants_human": {"type": "noul", "instructions": "The caller asked to speak to a human or a live person."},
    "outcome": {"type": "choice", "instructions": "Final outcome of the call.",
                "criteria": {"booked": "appointment confirmed", "callback": "caller will be called back",
                             "info_only": "caller only got information", "transferred": "handed to a human",
                             "abandoned": "caller hung up or call dropped before resolution"}},
    "outcome_listed": {"type": "noul", "instructions": "The call ended in one of these outcomes: booked, callback, information only, transferred to a human, or abandoned.",
                       "criteria": {"true": "One of those five clearly happened.", "false": "The call ended some other way, or the transcript does not show how it ended."}},
    "agent_quality": {"type": "score", "instructions": "How well did the voice agent handle the caller's request?",
                      "criteria": ["failed the caller", "partially helped", "fully resolved the request"]}
  }
}
```
Four answers cost one ~600-token call (about $0.000025). Durations and counts come from `call_meta` in
code, not from questions.

## 7. Checklist before the first real call
- [ ] Every question is one judgement, and its name is not needed to understand it
- [ ] Every Noul has `criteria.true`/`criteria.false`
- [ ] Every Choice whose input can fit no option has a companion Noul ("does any option fit?"), or an
      explicit `none` where a Noul is not possible, and any plan or PRD that lists the options names the
      companion Noul with them (without it, input that fits no option is forced into a wrong one at high confidence)
- [ ] Every Score level is described fully, without relying on its neighbours
- [ ] No arithmetic, dates or counting inside questions; those values are precomputed into state
- [ ] State is filtered, structured, with untrusted text in a labelled field
- [ ] All independent questions share one call
- [ ] Model pinned (`jev-1.14.0` for new work; `jev-1.13.0` only where already tuned on it), not `jev-latest`, anywhere thresholds are tuned
- [ ] Questions and thresholds live together in one reviewed file
