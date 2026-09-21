# Integrating Jev: brownfield, mid-project, greenfield

Every recipe ends in a verify step with a pass/fail check. Don't skip it: a typed answer guarantees
the *shape* of the output, never its truth.

## Contents
1. The seam (do this in every recipe)
2. Recipe A: existing codebase (brownfield)
3. Recipe B: mid-project (a decision is about to be built)
4. Recipe C: from scratch (greenfield)
5. The patterns (pick per decision), and 5b: rules for outward actions
6. Production checklist
7. Workflow platforms (n8n, Zapier, Make)

## 1. The seam

Put one small interface between your app and any decision model, so Jev is an adapter and not a
dependency scattered through the code:

```ts
// decision-model.ts: the only file that knows a provider exists
export type YesNo   = { kind: "yesno";  id: string; instructions: string; yesMeans?: string; noMeans?: string };
export type PickOne = { kind: "pick";   id: string; instructions: string; options: Record<string, string> }; // include "other"
export type Rate    = { kind: "rate";   id: string; instructions: string; levels: string[] };               // 2-10, fully described
export type Answer  = { id: string; p?: number; choice?: string; score?: number; confidence?: number;
                        probabilities?: Record<string, number> };
export interface DecisionModel {
  decide(state: unknown, questions: Array<YesNo | PickOne | Rate>): Promise<{ answers: Answer[]; model: string; inputTokens: number; ms: number }>;
}
```
The Jev adapter maps `yesMeans`/`noMeans` to `criteria.true`/`criteria.false`, pins the model, refuses
empty questions, and returns `model` from the response so drift is visible. Tests inject a fake
`DecisionModel`, so no network is needed. A second adapter (an LLM) gives you the fallback for free.

Official SDKs:
- Python: `pip install typesafe-sdk` (0.7.0, Python >= 3.10).
  `TypeSafeClient().system_one(state, questions, model="jev-1.13.0")`.
- JS: `npm i @typesafe-ai/sdk` (0.6.0, Node >= 20).
  `client.systemOne({ state, questions: { billing: noul("...") } })`.
- Both read `TYPESAFE_API_KEY` and retry 408/429/5xx.
- Warning: the JS `debug` log level prints request bodies, so never enable it with real data.

## 2. Recipe A: existing codebase (brownfield)

Goal: replace or pre-screen LLM calls that make *decisions*, without changing behaviour until numbers say so.

1. **Find candidates.** `python3 scripts/find_decision_calls.py <repo>` ranks LLM call sites whose output
   is a label, bool or rating. It marks mixed sites ("split decision from generation") and flags nearby
   numbers and dates. Review by hand: it is a ranking, not a verdict.
2. **Fit-check each candidate.** `python3 scripts/fit_check.py --answers -`. Drop NO-GOs; note the
   guards for the rest.
3. **Rank by payoff** = calls/day x tokens x incumbent price. Start with the highest-volume, most
   reversible decision.
4. **Build a labelled set from history.** Export past inputs plus the outcome you now know was right.
   Aim for 50+ to start, 200+ before publishing accuracy. Redact PII or use synthetic cases until data
   terms are cleared.
5. **Add the seam** (section 1) behind a flag that defaults to off. No behaviour change yet.
6. **Offline measure.** Run `scripts/calibrate.py` on the labelled set. Run the incumbent on the same
   cases. Compare on the *eval split* only.
7. **Shadow mode.** In production, call Jev beside the incumbent, log both answers plus probabilities,
   and act only on the incumbent. Disagreements become new labels. Shadow still sends data to a third
   party, so the egress guard applies.
8. **Cut over per path with a cascade:**
   - Jev answers when confident (band from calibration).
   - The incumbent answers the middle band and whenever Jev errors or times out.
   - Add a kill switch per path and a circuit breaker after consecutive failures.
9. **Blind fallback for high-stakes paths.** When Jev is unsure, the incumbent prompt runs *unchanged*
   and never sees Jev's answer. A model shown a first opinion tends to agree with it, which would
   corrupt your measurement. On such paths let Jev say only "confident no, skip the expensive call".

**While you are in there** (round-1 lesson: a no-skill agent caught these and the skill run did not):
- Read how the incumbent call's reply is parsed. Flag exact-match checks (`out === "true"` silently fails
  on `True.`), defaults that hide failures (garbled reply becomes "no", so nobody is paged), and enum
  parses that throw on an unexpected label. Moving to typed answers removes these; say so in the plan.
- Look for time-dependent logic evaluated at processing time instead of event time (a 30-day window
  measured from "now" flips while a ticket waits in a queue).

**Ramp deterministically.** Cut over 5% -> 25% -> 50% -> 100%, keyed on a hash of a stable id (ticket
id, call id), so the same item always takes the same path and before/after comparisons are clean. For
miss-critical gates, run a period where the action fires if *either* Jev or the incumbent says yes.

**Verify (pass/fail):**
- With the flag off, the test suite and outputs are byte-identical to before.
- Shadow agreement and held-out TPR/TNR meet the bar you wrote down *before* looking.
- Killing the Jev key mid-run degrades to the incumbent with no user-visible error.

## 3. Recipe B: mid-project (the decision isn't built yet)

1. **List the decisions in the design**, separate from the text generation. Any place the spec says
   "the system decides / detects / routes / flags / scores" is a candidate.
2. **Fit-check each one**, then choose per decision: code rule, Jev, or LLM. Decide in that order,
   because code is free, Jev is cheap, and an LLM is for words and reasoning.
3. **Write questions before code** (`references/question-design.md`). Put questions and thresholds in
   one reviewed file.
4. **Write 30-50 synthetic cases with hard negatives** while the feature is still fresh in your head.
   Include the near-misses you are afraid of. Run `calibrate.py`.
5. **Build behind the seam, with the fallback path in the first PR**, not as a later "hardening" task.
6. **Ship in annotate-only mode:** log decisions and don't act on them until real labelled data
   confirms the thresholds.

**Verify:**
- Every decision in the spec has an owner (code, Jev or LLM) and a threshold source.
- Synthetic eval split passes your bar.
- The fallback is exercised by a test that simulates a Jev outage.

## 4. Recipe C: from scratch (greenfield)

Design the product around cheap decisions instead of retrofitting them:

1. **Draw the pipeline as decisions and generations.** Typical shape:
   `input -> rules -> Jev battery (route / flag / score) -> [LLM only where words or reasoning are needed] -> Jev checks on the LLM output -> action`.
2. **Judge everything that is cheap to judge.** At $0.042 per million input tokens you can score every
   item, every trace and every tool call, so design for "decide on all, act on the confident".
3. **One battery per state.** Group all the questions about the same input into one call.
4. **Thresholds are config, per action, scaled to reversibility:** auto-act on reversible actions at a
   lower bar; require a human or stronger model for irreversible ones.
5. **Log for calibration from day one:** state hash, question-set version, probabilities,
   `response.model`, and final outcome. This becomes your labelled set.
6. **Plan the exit.** Single closed vendor, no self-hosting, and limits "can change without notice".
   The seam plus the LLM adapter is your portability.

**Verify:**
- Replaying a day of logged inputs through the pipeline reproduces the same decisions (Jev's
  run-to-run jitter is about ±0.02, so nothing should sit on a threshold; if it does, widen the band).
- Cost per 1k items matches your estimate within 2x.
- Outage drill passes.

## 5. The patterns

| Pattern | Use when | How |
|---|---|---|
| **Shadow mode** | Any incumbent exists | Run beside it, log both, act on the incumbent. Review disagreements weekly. |
| **Confidence-floor cascade** | You have a fallback model or human | Band from `calibrate.py --band`: `p <= low` is no, `p >= high` is yes, the middle goes to fallback. |
| **Blind fallback** | High-stakes path | Fallback never sees Jev's answer. Jev may only skip work on a confident no. |
| **Rules first** | Obvious cases exist, or input can be adversarial | Deny-lists and allow-lists settle the obvious for free; Jev sees only the ambiguous remainder. |
| **Pre-filter** | An expensive LLM or human reads everything today | Jev scores all items; only the high-value or uncertain ones go on. Keep everything in the archive. |
| **Decompose and weight** | One broad judgement underperforms | 3-7 atomic questions in one call; combine in code; fit weights on labels. |
| **Threshold in code** | A rare, costly class must not be missed | Read the class probability and cut in code, instead of trusting Choice argmax. |
| **Jev as features** | You already have a trained classifier | Add Jev answers as input features (F1 0.880 to 0.897 in one report). |
| **Two-stage Choice** | More than 255 options, or lookalike options | Stage 1 ranks or shortlists; stage 2 reads the top 3 and may reject all. |
| **Verify-done** | Agents claim completion | Noul: "the update claims X, and the tool-call log contains a matching successful call". |
| **Async sidecar** | Latency-critical loops (voice) | Decide during TTS playback or after the turn; never block the turn. |

## 5b. When a Jev answer triggers an outward action (SMS, page, email, CRM write)

The decision is only half the design. Specify the action's own rules, in code, not in the question:
- **Gate first:** skip voicemail, spam, wrong numbers and sub-N-second calls with a call-type Choice or
  a rule, before any flag is computed.
- **Suppress when already handled:** no "asked for a human" alert if the transfer actually connected.
- **Rate-limit per subject** (one alert per caller per 30 minutes) and respect business hours.
- **Make delivery idempotent:** webhooks retry; key the action on the event id.
- **Opt-in per client**, and disable a flag for clients whose data cannot support it (no booking signal
  means no missed-booking flag, not a guess).
- **Long inputs:** chunk, ask per chunk, and combine in code (max for "did X ever happen").
- **Stricter bar than dashboards:** an outward action uses the blind-fallback cascade; a dashboard flag
  can use the plain threshold.

## 6. Production checklist

- [ ] **Pin the model** (`jev-1.13.0`). `jev-latest` and `jev-preview` both resolved to 1.13.0 on
      2026-09-21, but aliases move. Log `response.model` and alert when it changes. Recalibrate on
      any version change.
- [ ] **Egress guard:** refuse to send secrets, emails, phone numbers or client identifiers unless
      terms allow it. Applies in shadow mode too.
- [ ] **Data terms:** no training on customer data; zero data retention is enterprise-only (via
      privacy@typesafe.ai); US hosting; no SOC 2 evidence found. A named person re-reads the *current*
      terms before production PII. Through Vercel AI Gateway, ZDR and no-training are per-request options.
- [ ] **Timeouts and retries:** set a client timeout (a near-64k request once stalled silently); retry
      408/429/5xx with backoff; treat 529 as overload.
- [ ] **Rate limits:** 250k tokens/s and 1,200 req/min at time of writing, "adjusting dynamically".
      Build backpressure.
- [ ] **Fallback stays warm:** periodic cheap health call so an outage isn't discovered mid-escalation.
- [ ] **Keys server-side only.** Never in a browser bundle or a workflow export.
- [ ] **Gateways** (OpenRouter `TYPESAFE_BASE_URL=https://openrouter.ai/api`, Vercel AI Gateway,
      Cloudflare, AI/ML API) differ in model ids, context limits (Cloudflare lists 32k) and price
      (AI/ML API is about 38% above direct). Recalibrate if you switch.
- [ ] **Monitoring:** share of answers in the middle band, disagreement rate vs fallback, p95 latency,
      cost per 1k decisions.

## 7. Workflow platforms (n8n, Zapier, Make)

There is no official node.

- **n8n:** an unofficial MIT community node, `n8n-nodes-typesafe` (0.2.0), exposes Choice, Noul and
  Score. It is untested here, so review it before use.
- **Any platform:** an **HTTP Request node** is enough:
  - `POST https://api.typesafe.ai/v1/systemone`
  - Header `Authorization: Bearer {{credential}}`
  - JSON body with `model`, `state`, `questions`

Wiring:
- Branch with an IF/Switch node on `answers.<name>.noul >= <threshold>`. Set the threshold in the
  workflow, not by "true/false" from the model.
- Use three branches for a cascade: confident yes, confident no, and middle (send to an LLM node or a
  human approval step).
- Keep the questions JSON in one Set node so it is reviewable.
