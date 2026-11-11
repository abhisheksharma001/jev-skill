# Where a decision model fits: use cases and shapes

Evidence as of 2026-11-11. IDs (N-x) point to the evidence register,
`docs/research/2026-11-11/evidence.md` in github.com/abhisheksharma001/jev-skill. Strength labels:
- **indep n=...**: independent measured result, with sample size.
- **partner** / **vendor**: measured, but by someone with a stake. Never enough for GOOD.
- **none**: designs and demos only.

Read `fit-map.md` for verdicts. This file is for picking a shape and spotting the gotcha.

## Contents
1. The shapes that win
2. Use cases by area
3. Creative patterns worth teaching
4. Where it lost, and why
5. Choosing a decision API

## 1. The shapes that win

**Pre-filter / cascade.** Jev answers; low-confidence cases go to a bigger model or a person.
- Best evidence: N-73 (indep, n=2,319 GitHub issues): kept-answer accuracy 76.7% with no gate,
  84.3% at a 0.9 gate with 22.6% escalated.
- Build: `monumei/typesafe-cascade`. Take the label if confidence >= cut, else escalate. SDK retries off.
- Always report accuracy together with the share escalated.

**Fan-out battery.** Ask every question you might need about one input in one request.
- Best evidence: N-107 (indep): 3 questions 712 ms, 100 questions 714 ms.
- Build: HA-Jev turns each question into a Home Assistant sensor.
- One document per request. Many questions on one input, not many inputs in one array:
  20-item arrays dropped 96% to 72% (N-157, indep).

**Companion Noul.** A Choice always names a winner. Pair it with a yes/no "does any option fit?".
- Best evidence: N-146 (indep, 8,742 medical items): a Noul per option at a 0.90 cut kept
  90.3-97.0% accuracy vs 79.4-80.3% under plain Choice.
- Build: Slashly scores relevance as 1 - P(none) (N-166). TypeSafe's docs now recommend a
  companion Noul over an `other` option (vendor, read 2026-11-11).

**Screen, then act.** A cheap gate decides whether the expensive or risky step runs at all.
- Best evidence: N-33 (indep, six weeks of real agent jobs): "done" replies 30/30 with 1 false
  alarm; run notices 46/49 vs a word list 31/49.
- Build: pi-jev gates bash/write/edit with 4 Nouls per call (N-23). Fails open, user confirms.

**Judge / verify another model's output.**
- Best evidence: N-110 (indep, 27 comparisons, 7 benchmarks): matches LLM judges in all but at
  most 6 of 27, 16-357x cheaper. But the errors overlap with LLM judges (> 85%).
- Build: GC AI streaming citation check, three narrow Nouls per sentence (N-131).

**Rerank a shortlist.**
- Best evidence: N-120 (indep, 8 BEIR sets + DL19/21): ranks ahead of FLAN-UL2 and 3
  cross-encoders. Raw scores > 0.9 were only 66% relevant; a 2-parameter fit fixed it.
- Build: hybrid BM25 + vectors, then Jev on the top 30-100 (N-121, N-122).

**Memory gate.** Decide what to save, recall or retire.
- Best evidence: N-96 (indep): sessions that broke a project rule 0/18 with the gate vs 10/18
  without. Caution N-97 (indep, pre-registered, 500 pairs): a yes/no retire gate retired 39.2%
  of claims whose change was only "suggested".
- Build: jevmem. Save cheaply, retire with a 3-way choice and a human check.

**Agent control points.** Many small typed decisions inside an agent, each with a mode.
- Best evidence: N-19 (indep author who also sells a rival judge): Terminal-Bench 180/264 vs
  155/264 (+9.5 pts, 95% CI +3.8 to +15.2).
- Counter-evidence: N-20 (indep): delegating tool choices without a fitted threshold cut task
  success by 19.0 pts. Each point needs active/shadow/off, and code keeps the final call.

**Vision: presence, then box.** Box always returns a box, even for things that are not there.
- Best evidence: N-142 (indep, 32 thumbnails x 3): presence right 96/96 yes and 96/96 no;
  small badges fell to 23% at 500 px wide until cropped (back to 96/96).
- Build: doorbell cam, Noul "person present?" over 4 frames, then Box to crop (N-144, 23/23).
- jev-1.14 preview only; vendor says not for production (N-145).

## 2. Use cases by area

Format: what works / strength / the gotcha.

**Routing**
- Skill or tool routing from a list: indep n=500 at 126 skills, 97.6% (N-3); indep n=299 at 19
  skills, 87.6% vs glm 90.6% (N-4); indep n=81 at 84 skills, right 37/69, silent 25/69 (N-2).
- Gotcha: accuracy falls and silence rises as rosters grow and thresholds stay default. Inside
  Claude Code, no one has shown a hint beats the full listing (N-6). This repo's test: n=8 synthetic,
  5 right, 0 wrong, 1 miss (N-8).
- Model routing (which LLM gets the prompt): indep n=13,923 found neither model beats chance
  zero-shot (N-1). Claims of 40-70% savings are 12-prompt tests with no quality check (N-10).
- Gotcha: route on observable task facts you can label, then calibrate. Do not route on "difficulty".

**Triage (tickets, issues, alerts, logs)**
- indep n=272 real tickets: type 84.9% vs Haiku 88.2%, 6x faster, ~190x cheaper (N-72).
- indep CLINC150 n=900 per rate: 92.2% vs 93.6% (N-71). indep n=2,319 issues with cascade (N-73).
- Gotcha: fine-grained label sets drop sharply: 10 product areas 53.8% (N-72); Banking77 all 77
  intents 76% vs 88% (N-82, cached). Pass computed facts: paging precision 0.63 -> 0.92 once the
  CPU value was in the state (N-69).

**Moderation and guardrails**
- Content safety: indep, best of field at 86.20% (N-43, n not given). Support-bot rules: indep
  n=51, 48/51 vs LLM 46/51 (N-52). Moderation blocks survived forged structure (N-45).
- Gotcha: at a strict 0.5% false-positive budget recall was 34% vs 61% for a 1B classifier
  (N-44, partner). Prompt injection: see section 4.

**Fraud and spam**
- Scam SMS: indep n=500, AUROC 0.995 (N-66). Fraud ring: partner n=29, 27 caught vs rules 26 (N-63).
- Real phishing corpus: indep n=848, 97.1-97.5% (N-62).
- Gotcha: one broad question fails; decompose into signals and weight in code (62.6% -> 95.0%,
  N-60, partner). False alarms on bank alerts and sign-in codes: 12.7% of legit mail (N-61, partner).

**Evals and judging**
- indep: N-110 (27 comparisons), N-111 (118 clinical answers, agreement 0.50 vs Opus 0.49).
- partner: MLflow 30/30 on an easy set, 64/72 on a harder one (N-109).
- Gotcha: it accepts "almost right" answers with one material error (N-109); its errors match
  LLM judges, so it is not a second opinion (N-110). Never ask a holistic "is this good?":
  AUC 0.54; eight factual questions AUC 0.72 (N-118).

**RAG**
- Rerank: indep (N-120, N-121 Turkish n=1,044: Recall@5 equal to Cohere at 60.6% lower cost).
- Index + rerank beats full scan: 94.1% vs 88.7% evidence coverage (N-122, indep n=396).
- Claim verification cascade: same accuracy, different errors; Jev let through 23.2% of
  unsupported claims vs 14.1% (N-123, indep n=495).
- Gotcha: calibrate scores before a fixed cut (N-120). 1.14 regressed on RAGTruth by 3.9 pts vs
  1.13 (N-62). Rerank cannot add a passage the search missed.

**Memory**
- Save gate: indep (N-96, N-99 synthetic n=100: 39/50 vs Luna 41/50). Raw-turn selection
  non-inferior to LLM extraction and 3,061x cheaper to write (N-98, indep).
- Gotcha: retire/overwrite decisions are risky (N-97). Hand-kept CLAUDE.md did as well (67/72, N-96).

**Agents**
- Control points: N-19 (indep), browser action choice (N-24 partner, 137/138).
- Gotcha: N-20 (minus 19 pts without fitted thresholds); asked "is there enough evidence?"
  Jev still decided 44% of the time (N-22, indep 25,000 calls); permission approval scored 53.7
  on mubench (N-19). Keep authorization in code.

**Voice**
- Post-call QA: partner only (27 of 34 metrics >= 96%, N-136; source not read). No indep n.
- In-call: one indep demo decides on partial transcripts with p50 ~300 ms, 34/34 author fixtures
  (N-133). Phone designs use 1.0-1.2 s timeouts with fallbacks (N-134, N-135, partner).
- Gotcha: STT errors flip meaning ("know nothing works", N-135). Text only, no tone.
  OpenAI's Decisions API now has native GPT-Live voice integration (N-183, vendor).

**Vision**
- See shape above. indep: N-141, N-142, N-144. Gotcha: the review band was 48% stated but 34%
  actual accuracy (N-141); Box boxes absent objects (N-142, N-143).

**Automations (n8n, Zapier, Make, Sheets)**
- Official n8n node 0.10.0, official Zapier and Make apps, community n8n nodes (N-101 to N-106).
- Strength: none. No workflow outcome has been published.
- Gotcha: route the low-confidence output to a "needs review" branch; pin the model id in the
  credential. Home Assistant is the one measured automation build (N-107).

**Apps and creative builds**
- Games, sims, filters, selection-not-generation (N-157 to N-166). Mostly self-reported.
- Gotcha: options must be conditions, not labels: villagers ate at hunger 0 (N-158). Moving
  state makes answers late (N-159).

**Regulated domains (health, hiring, legal, finance)**
- Health: indep and large. Text clinical judgment 74.9-76.8%, numbers 35.9-39.4% (N-146);
  clinician-advice cues moved Jev decisions by 47.6 pts (N-148).
- Hiring: one indep name-swap audit, gap 0.0 pp (N-150, n=1,824, one domain). Vendor case study
  says quality parity at 88% lower cost (N-151).
- Legal: partner, AUPR 0.553-0.656, below Gemini and fine-tuned Laya (N-152); 96.4% confidence
  on a fabricated statute (N-154).
- Finance/AML: designs only (N-64).
- Gotcha: high stakes, bias under pressure, no reasons to audit; data residency (N-156, N-182).

## 3. Creative patterns worth teaching

1. Typed switch in front of code: Jev classifies, code and templates reply (N-157, N-164).
2. Selection instead of generation: score 400 pre-written replies and pick one (N-163).
3. Compile once, run free: pay Jev per page template, store deterministic hide rules (N-165).
4. "None of these" as a relevance dial: 1 - P(none) feeds a user slider (N-166).
5. Verifier beside a streaming generator: check each sentence before the next lands (N-131).
6. Decision as a sensor: a probability becomes an automation input (N-107).
7. Tick loop with legal moves in code and preference in the model (N-159).
8. Fewer gates, one choice: many semantic gates created cliffs; one Choice fixed it (N-164).
9. Measure before building, and publish the negative result (N-70, N-5, N-161).

## 4. Where it lost, and why

| Where | What happened | Why | IDs |
|---|---|---|---|
| CI failure triage | Regex 18/20 right vs Jev 14/18; rejected | The answer was in a rerun, not the log; rules were enough | N-70 |
| Routing vs a strong LLM | 143/162 vs Claude 158/162; 87.6% vs glm 90.6% | Fuzzy neighbouring routes | N-5, N-4 |
| Zero-shot model routing | At chance | "Which model?" is not observable from the prompt | N-1 |
| Trading | -4.5R vs LLM -1.2R in 17 days; -17 bp/trade backtest | Confidence ran backwards; no edge | N-161, N-162 |
| Phishing, one question | 62% detection vs judges 77-81%; 27% of benign flagged | Overall judgment, not rule checks | N-45, N-60, N-61 |
| Prompt injection | 76.2% vs 95.4% dedicated classifier; counterfeit policy cut recall to 3.9-9.7%; 25/27 runs broken | Policy-looking text in state steers it | N-42, N-41, N-48, N-46 |
| Fake legal facts | 96.4% confidence affirming a fabricated statute | No lookup; knowledge, not checking | N-154 |
| Overconfidence | 0.9-1.0 bucket: 98.9% stated, 84.3% right; review band 48% stated, 34% right; > 0.9 rerank only 66% relevant | Raw probabilities are not accuracy | N-73, N-141, N-120, N-169 |
| Numbers and dates | Physiology 35.9-39.4%; date math failed ~4 of 5 | Vendor-listed weak spot | N-146, N-157 |
| Holistic quality | "Is this test useless?" AUC 0.54; "does the founder need to know" cleared 19/174 | Taste, not facts | N-118, N-33 |
| Version drift | 1.14 vs 1.13: +41.6 on one phishing set, -3.9 on RAGTruth; not in release notes | Hosted model changes | N-62 |

## 5. Choosing a decision API (as of 2026-11-11)

| | Jev (TypeSafe) | OpenAI Decisions API | Small trained classifier | General LLM |
|---|---|---|---|---|
| Price | $0.042/M input, output free (N-174); bills ~38% more tokens than one rival on the same text (N-62) | $0.10/M input, $0.01 cached, output free (N-183) | Your compute; needs labels | ~35x Jev per call for Haiku-class (N-71) |
| Data terms | US hosting; ZDR enterprise only; MCA allows training with consent and telemetry "in perpetuity" (N-181, N-182) | ZDR + HIPAA for eligible customers; US/EU residency (N-183) | Stays on your machines | Depends on vendor |
| Latency | ~0.12-0.33 s p50 reported (N-177, N-133, N-52); ~0.9-1.0 s from India (N-8) | Vendor: 10x faster than Responses API; no indep measurement | ~54 ms (deberta, N-43) | 1-10 s (N-61, N-72) |
| Calibration evidence | Many indep studies: overconfident raw, fixable with isotonic/2-param fits (N-169, N-120, N-73) | None independent found | You fit it | Mixed; Fable ECE 0.027 vs Jev 0.118 in one test (N-22) |
| Ecosystem | n8n, Zapier, Make, LiteLLM, Vercel, OpenRouter, Cloudflare, LangChain, DSPy, Pydantic AI (N-101 to N-178) | gpt-6-luna only, up to 400 questions, native GPT-Live voice (N-183) | Standard ML stack | Everything |
| Best when | High volume, many questions per input, need probabilities | Already on OpenAI, need EU residency or HIPAA, or voice on GPT-Live | Stable labels, lots of data, strict latency | Reasoning, numbers, writing |

No independent head-to-head of Jev vs the OpenAI Decisions API exists in this repo's evidence register. One small
suite (n likely 48) scored GPT-6 Luna Decisions 95.8% vs Jev 89.6% (N-83, low confidence).
Measure both on your own labelled cases before choosing.
