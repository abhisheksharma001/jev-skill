# Where Jev fits: the use-case map

Evidence snapshot: 2026-11-11 (first map 2026-09-21; Jev launched 2026-09-15). Many results are
still single studies or small adopter experiments. Re-check before quoting numbers as settled.

Model versions: jev-1.14.0 was released 2026-10-14 and `jev-latest` now points to it (vendor, N-174).
An independent test found 1.14-vs-1.13 swings the release notes do not mention: +41.6 pts on one
phishing set, -3.9 pts on RAGTruth (N-62). Most results below are on jev-1.13.0: re-calibrate before
moving a tuned path to 1.14.

**Every GOOD or HYBRID verdict you hand over ends with these two lines.** A verdict from this map is a
claim about other people's data, so the reader needs to know how to prove it and what to do if it
falls short:
- **Prove it:** calibrate on labelled cases and report the held-out split (`calibration.md`).
- **If accuracy is short:** name the lever to pull first (rewrite the question from its train misses,
  multi-Jev, or a cascade on the unsure share; `optimization.md`), and say that any cascade accuracy
  is reported together with the share escalated.

## Contents
1. The one-line test
2. Verdict rules
3. The map (30 placements)
4. The sweet spot: where Jev makes the MOST sense
5. Anti-patterns seen in the wild

## 1. The one-line test

> **Jev is for decisions, not words.** Use it where a system must pick from a closed set
> (yes/no, one of up to 255 options, or a rating on 2-10 levels) about text, where plain code can't decide,
> and where volume, latency, consistency or calibrated probabilities matter.

Run `scripts/fit_check.py` for the repeatable version of this test.

## 2. Verdict rules (applied uniformly)

| Verdict | Means |
|---|---|
| **GOOD** | Independent, measured result where Jev matched or beat the alternative |
| **HYBRID** | Works, but only with code, rules, thresholds or a fallback model around it |
| **BAD** | Measured failure, or a structural reason (generation, stakes with no audit) |
| **UNKNOWN** | Proposals and demos only; no measurement. Treat as an experiment: shadow mode first |

"Partner" = LangChain, Braintrust, Vercel, LiteLLM and other integrators, competitors and vendors with
a commercial stake. "Vendor" = TypeSafe. "Independent" = everyone else. A verdict resting only on
partner/vendor evidence is not GOOD.

`N-` numbers are record IDs in the repo's evidence register (`docs/research/2026-11-11/evidence.md`),
which gives the source URL, date, n and independence of each. Evidence without an ID is from the
2026-09-21 snapshot.

## 3. The map

### Evals and judging
| Placement | Verdict | Evidence (source, n) | How to use it |
|---|---|---|---|
| Bounded pass/fail and rubric evals of agent outputs | **GOOD (bounded)** | Independent: 27 comparisons over 7 benchmarks with human labels, matched LLM judges in all but at most 6, 16-357x cheaper (N-110); 118 pediatric answers, physician agreement 0.50 vs Claude Opus 5.5 0.49 (N-111). Caveats: > 85% of flash-tier LLM verdicts repeat Jev's most confident errors (N-110); it passed "almost right" answers, 64/72 vs 72/72 for a larger LLM judge (partner, 72 answers x2, N-109). LangChain: 500/500 binary agreement with a human oracle, 92-913x lower score variance than LLM judges (partner, **n=5 cases** x100 reps; N-113 repeats these numbers, not new data). | One atomic question per rubric line; Score for graded quality, Noul for pass/fail. Validate against ~50+ human labels. Do not use a flash-tier LLM judge as its cross-check: they fail in the same places (N-110). LangChain's own warning: "a consistently wrong evaluator can produce bad feedback at scale". |
| Online eval / monitoring every production trace | **HYBRID** (cost-enabled; one independent production log) | Independent: six weeks of real agent gates: "done" replies 30/30 with 1 false alarm, run notices 46/49 vs a word list 31/49, but "does the founder need to know?" cleared only 19/174 (N-33). Replay on pinned jev-1.13.0: 1 of 7,242 cell-questions crossed 0.5; hosted drift remains the concern (N-114). Partner: $0.03 vs $2.60 per 1k traces against Ragas + gpt-4.1-mini, verdicts agreed on 4 measured rows of 20; a gateway hang pushed p95 to ~1 min (N-112). | Sample first, route low confidence to a human, pin the model version, set client timeouts. |
| Pairwise judging of complex LLM outputs, code review | **BAD (as one holistic question)** | Measured, independent: "is this test useless?" AUC 0.54 vs 0.72 with eight factual structural questions (N-118); "does the founder need to know?" cleared 19/174 (N-33). An independent critic: "no reasoning, no tools, no codebase context; it will prefer the simpler output". A decomposed code-review pipeline exists but is unmeasured (N-31). | Keep a reasoning model. Jev may pre-filter obvious fails with narrow factual questions. |

### Routing and control flow
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Intent / skill / tool routing (pick a handler from a closed roster) | **GOOD (tie-level vs small LLMs; trails frontier LLMs)** | Independent: CLINC150, 3 trials x 300 tickets, in-scope 92.2% vs Luna and Haiku 93.6%, out-of-scope recall 97.3-100%, ~35x cheaper per call than Haiku (N-71); 126 skills, n=500, 97.6% strict (N-3); oh-my-pi: p50 ~330 ms, 0 misses at 39 skills. Trails: 299 real intents 87.6% vs glm-4-flash 90.6% (self-report, N-4); 162 cases 143 vs Claude 158 (N-5); UI routing 65% vs LLM 70% (shadow run). Scale gotcha: 84 real skills with upstream default thresholds, 69 skill turns: right 53.6%, silent 36.2%, wrong 10.1% (84.1% right when it answered) (N-2). Partner: LiteLLM auto-router 127 ms vs Haiku 688 ms median. | Choice plus a companion Noul ("does any option fit?"). Tune the abstain threshold on your own roster, not upstream defaults (N-2). When the top-2 probabilities are within ~0.1, ask a follow-up or stay quiet (oh-my-pi). Jev routes; it does not extract parameters (N-4). |
| Model routing (which LLM tier answers this prompt) | **HYBRID (only with labelled, task-specific calibration)** | Independent, arXiv 2610.02267, n=13,923 paired items: "neither model beats chance on zero-shot model routing" (N-1). An earlier independent shadow run tied an LLM, 61/69 each vs hand rules 23: the two results conflict, so both are cited. Savings claims of 40-70% come from 12 prompts with no quality check (N-10); Claude Code has no real per-message model switch (N-11); one hook design keeps money, migration and auth on the main model and fails open, with no accuracy reported (N-12). | Label a sample of your own traffic with the tier that was good enough, calibrate on it, shadow before switching. Fail open to the stronger model. Never ship a zero-shot model router. |
| Skill hints inside an agent harness that already sees the skill list | **UNKNOWN** | Vendor: helps a weak agent with a 60-char index, wrong loads 15.7% to 7.9% (n=452, N-7). Independent: an author found no measured benefit inside Claude Code and turned back (N-6). Ours: n=8 synthetic prompts, 5 right hints, 0 wrong (N-8). No independent with-vs-without measurement. | Measure with vs without on your own harness before keeping it; default off. |
| Agent control flow (done? retry? hand off? which tool?) | **HYBRID** | Adopted in oh-my-pi and Octomind. Independent: +9.5 pts on Terminal-Bench 2.1 (88 tasks x3, 95% CI +3.8 to +15.2), but weak on permission approval (53.7) and progress/completion (61.6) (N-19); delegating tool choices without a fitted confidence threshold cut task success 19.0 pts (N-20); with evidence missing it still decided 44% of the time (25,000 calls, N-22). Failures: "sure and wrong" when options were labels not policies (agent ate at hunger 0 of 100; likely the case in N-158, unconfirmed); "do you have enough info?" questions said yes about 85% of the time; reordering 4 options changed 7/120 answers. | Options must be **policies** ("eat: only when hunger > 70") but compute numbers in code. Fit a confidence threshold before delegating any step (N-20). Never ask Jev to self-assess. Keep the final call in code. |
| Agent context filtering / memory-save decisions | **HYBRID** | Independent: test-log trimming cut 40.2% of text and lost 0 of 72 required lines (N-19); raw turns picked by one Jev call were non-inferior to LLM extraction at a tight budget (pre-registered, N-98); a memory plugin stopped forbidden changes (0/18 vs 10/18 sessions without it) but trailed Claude auto memory, 40/54 vs 47/54 (N-96); 100 synthetic cases, kept 39/50 vs Luna 41/50 (N-99). Mixed, so not GOOD. Critics note dropped context can matter later. | Retain/drop decisions only with verbatim retention; keep synthesis on an LLM. For retiring old memories see the next row. |
| Memory retire / overwrite (does a new fact replace an old one?) | **BAD (as a yes/no gate)** | Independent, pre-registered, 500 pairs: a binary gate retired 39.2% of claims whose change was only suggested; a 3-way choice cut that to 15.5% but lost 15.3 pts of detection, missing its pre-registered 10-pt budget (N-97). | Never retire automatically. Use a 3-way choice (changed / suggested / same) and send "changed" to a human or an LLM. |
| Browser / computer-use action choice from a list of controls | **HYBRID** | Partner: 137/138 vs Browser Use 133/138 at 10.7x lower cost, with an LLM fallback, so the Jev-only rate is not given (46 tasks x3, N-24). Independent, small n: 21-23 decisions all right (N-26); 49/49 picking WebMCP tools (single thread, N-25). | Jev picks from indexed controls; an LLM types text and plans; code enforces spend, credentials and irreversible steps. |
| No-code workflow routing (n8n / Zapier / Make Switch replacement) | **UNKNOWN** | Official n8n node 0.10.0 (vendor, N-101), community nodes (N-102), official Zapier and Make apps (partner, N-104, N-105). No workflow outcome published. | Route low confidence to a "needs review" branch; pin the model id; shadow next to the existing Switch first. |

### Guardrails and safety
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Dangerous tool-call / shell-command gate | **HYBRID** | Independent certification: "Jev was the safest" shell classifier tested, but only after fixed rules settled the obvious commands. Wording matters: "cannot be recovered from version control" scored a force-push only 0.77, and the same state moved ±0.05 between runs (independent, 6 states, N-23). Policy-like text planted in untrusted state dropped mean is_risky 0.893 to 0.290 (partner, 40 calls, N-41). A replay of a day of real Claude Code commands caught an `rm -rf` (partner hackathon, N-55). LangChain `AutoModeMiddleware` (experimental) refuses risky calls but does not ask for approval. | Deny-lists and allow-lists first; Jev for the ambiguous remainder; label untrusted text in state; pair with human-in-the-loop for irreversible actions. |
| Content / UGC moderation | **GOOD (tie-level)** | Independent: content safety 86.20%, best in its field vs granite-guardian 80.27% (9 public datasets, n not given, N-43); 51 labelled cases, 48/51 vs Azure gpt-5.4-mini 46/51 (N-52); forged structured input bypassed none of its moderation blocks (50 attack variants, N-45); Near Here: 48/50 vs Gemini 43 and Mistral 42; on an earlier set Gemini 50/50 vs Jev 49/50; 129/132 across all prompt tests (n=50-132). Partner caveat: at a 0.5% false-positive budget, recall 34% vs 61% for a 1B purpose-built classifier (18k multi-turn, N-44). | Noul per policy, Score for severity. Calibrate per category. Under a very low false-positive budget, test a purpose-built classifier too (N-44). |
| Prompt-injection / jailbreak detection | **BAD as the only defence** (one layer at most) | Independent: injection accuracy 86.35% vs a 54 ms deberta classifier 89.01% (9 public datasets, N-43); at a 1% false-negative target every gate-reviewer system needed > 91.8% escalation (47,611 held-out, N-46); a fake blank `STATE:` header flipped an answer (N-50); followed planted labels on 6/20 tickets (N-72). Partner: 76.2% vs 95.4% for a competitor (3,669 attacks, N-42); policy-like text in untrusted state cut attack recall to 3.9-9.7% (N-41); a hostile paragraph broke 25/27 runs (N-48). Ours: 7/7 probe cases held; in a production worker run, 3/4 held, with a fake-delimiter injection moving two answers to 0.53/0.58. Fake delimiters and planted policy text were the weakest vectors. | Never the only defence; a trained injection classifier was faster and more accurate (N-43). Put untrusted text in a labelled state field; test your own injection set. |
| PII detection | **UNKNOWN** (one tiny data point) | Independent: a private-leak check caught 16/16 at a 0.3 cut with 6 false alarms in 24 (N-33). Otherwise demos and designs (redaction design, partner, N-64). The bigger risk runs the other way: sending PII to a third-party API. | Build an egress guard (see integration.md) before any shadow run. |
| Fraud / transaction-risk final call | **HYBRID** | Partner: one real ring, 29 fraudulent transactions: Jev caught 27 vs rules 26 and Claude Sonnet 18; its first broad question fixated on velocity (N-63). Independent: 500 SMS (98 scams), AUROC 0.995, 0 scams among the 369 scored below 20% (N-66); a fraud-email cascade got 96/100 with 31 sent to a bigger model (self-report, N-65). | Code computes the facts (shared cards, velocity); Jev answers narrow questions; decompose; feed answers into the rule engine. |
| AML / sanctions / KYC triage | **UNKNOWN** | Designs only: thresholds marked "illustrative" (partner, N-64); a hackathon KYC build with no numbers (partner event, N-67). | Shadow mode; backtest before any auto-clear; redact account numbers before the API. |

### Triage and classification
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Spam / email / ticket / lead triage | **HYBRID** | Independent: 272 real tickets, type 84.9% vs Haiku 4.5 88.2% (N-72); 848 real phishing emails 97.1% (1.13) and 97.5% (1.14) (N-62); 500 SMS scams AUROC 0.995 (N-66). Zero-shot spam 98.3% vs a TF-IDF model trained on ~14,800 labels 98.4%. But one big "is this phishing?" question: 89.4% vs a 2-line rule 91.8% and Haiku 94.2% (2,000 emails). Partner: 232 real emails, malicious caught 43 vs Opus 44, but 21/166 false alarms at 0.5 vs Opus 1 (N-61). In another test 62.6% vs Haiku 81.3%, and **decomposed into 5 atomic questions weighted in code: 95%**; the 62.6%/95% figures now appear in a partner post (N-60), so treat them as partner until the original source is re-checked. | Decompose; weight in code; rules first; set the threshold on your own false-alarm budget, not 0.5 (N-61). |
| Log / alert / incident triage | **HYBRID** | dev.to log triage: letting Choice decide missed replication lag (INFO-level logs); a 0.50 threshold set **in code** caught 500/500 incidents with 0 false alarms in 3,000 test logs. Independent: on-call paging replay, 136 alerts: every incident caught, 1 false page, precision 0.63 to 0.92 once the observed CPU value was passed (N-69); CI failure triage lost to regex rules (14/18 vs 18/20 routed right, 24 held-out) and was rejected (N-70); BGL log triage F1 54% vs Claude 23% (N-29). Cribl: 2-3x more errors than a purpose-built classifier on 28-way semi-structured log typing. | Pre-filter in front of a bigger LLM; pass observed numbers in state; thresholds in code on raw probabilities. |
| Replacing a fine-tuned small classifier in a stable domain | **HYBRID** | Zero-shot Jev beats zero-shot encoders (macro-F1 0.782 vs 0.712) and automates ~2x the traffic at 90% precision. But a 310M encoder fine-tuned on 250 labels beat Jev by 12 points on topic classification (Japanese text; tied on 2 polarity tasks) and was 4-20x faster. Independent: a 54 ms deberta classifier beat Jev on injection, 89.01% vs 86.35% (N-43); trained classical models won on Banking77 and tabular business data (8 datasets, N-81). | Jev wins cold start and fast-changing labels; a trained encoder wins stable, high-volume, labelled domains. Or feed Jev answers as features into your classifier (F1 0.880 to 0.897). |
| Lead scoring / prioritising | **HYBRID (low stakes only)** | First measurement, synthetic: 100 made-up emails, 89/100 exact vs Haiku 4.5 84 and Fable 5.1 97, all 15/15 hot leads found (independent, N-87). Adopter demos (e.g. 1,700 emails through 4 evaluations for about 18 cents); no real-data accuracy yet; systematic preference among equivalent options was observed elsewhere. | Only for reversible prioritisation; shadow first; audit which leads get deprioritised. |
| Compliance / legal / contract clause review | **HYBRID (first-pass flagging for human review only)** | Partner research lab: MAUD (152 agreements) AUPR 0.656 vs Gemini 3.8 Flash 0.699; CUAD (510 contracts) 0.553 vs 0.644 (N-152). Independent, synthetic held-out: ToS trap clauses F1 89% vs keyword regex 57% (N-155). Independent: 96.4% confidence affirming a fabricated statute (N-154). Partner: 64,000 court rules, 39/40 sampled right at high confidence, but 60%-confidence answers right 1 in 4 (N-153). Vendor-run workflow evals: weakest on invoice processing (61.8%), "it slips wherever numbers are involved". | First-pass ranking for human reviewers only, never the final word; numbers, dates and citation existence in code. |

### Retrieval (RAG)
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Reranking / relevance filtering | **GOOD** | Independent: across 8 BEIR sets plus DL19/DL21, reranks ahead of FLAN-UL2 and 3 cross-encoders on average (N-120); 1,044 questions, Recall@5 99.4% equal to Cohere Rerank 3.5 at $0.41 vs $1.04 (N-121); nDCG@10 0.501 vs Voyage 0.504 vs Cohere 0.486; BM25 top-1 11 to 18 of 24; golden-set relevance 22/25. Gains shrink when candidates are already plausible (89% scored >= 0.7). Raw scores run hot: of DL21 pairs scored > 0.9, only 66% were relevant (N-120). | Score or Noul per passage in one call. Rank by the probability; before using it as an absolute keep/drop cut, calibrate it (a 2-parameter fit on ~2,000 labelled pairs fixed most of the gap and transferred, N-120). |
| Grounding / faithfulness / citation checks | **HYBRID** | Our probe: supported claims 0.81-0.98 (including paraphrases), unsupported 0.01-0.04, up to ~5.7k tokens (n=27 textual). Independent 32-case test: "less convincing"; missed a >= vs > error; 3 of 4 mistakes had confidence > 0.8. Independent: in a cascade with a frontier model, accuracy matched (74.10 vs 73.83, 495 claims) but Jev admitted 23.2% of unsupported claims vs 14.1% (N-123); jev-1.14 scored 3.9 pts below 1.13 on RAGTruth (N-62); three narrow checks caught a "may" to "must" change one broad check missed (N-131). Vendor: on 1,000 answers, held back 84 of 115 wrong at a 0.2 risk cut; 31 wrong passed (N-129). Numeric-inference claims failed in our probe (0.26-0.36). | Textual support and contradiction: yes, split into narrow checks (explicit support, mismatched details, overstatement; N-131). Numbers and comparisons: code or an LLM. |

### Voice AI
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Post-call QA / outcome classification / escalation audit | **HYBRID (provisional, post-call only)** | No independent measured comparison on real transcripts yet. Partner: a competitor cites 27 of 34 voice-agent metrics at >= 96% accuracy (primary source not read), says whole-conversation questions fail, and notes Jev is not hosted in the UK/EU (N-136). Ours: 6/6 synthetic full transcripts correct on outcome, booked and wants-human (one battery call each, ~0.9 s). Practitioner reports of batch transcript reclassification. | Battery of atomic questions over the finished transcript (structured turns as JSON); no whole-conversation questions. |
| In-call decisions: end-of-turn, barge-in, live routing | **UNKNOWN** (latency-bound) | Mostly proposals. Voice budget is ~800 ms voice-to-voice; measured Jev round trips are 0.33-0.9 s short-state (region-dependent) and 1.9-2.4 s from Japan. On partial transcripts our outcome question fell to `other`: ask only what is already observable. One independent working demo: a voice browser asks ~12 questions on every partial transcript and acts when "is the command complete?" >= 0.6; p50 ~300 ms, 34/34 author fixtures; browser commands, not a phone agent (N-133). Partner: STT errors invert answers ("No, nothing works" heard as "know nothing works") (N-135); a framework design falls back to an LLM after 1,000 ms (N-134). | Async or speculative only (e.g. decide during TTS playback); never block the turn on it. Raise the bar when STT word confidence is low (N-135). |
| Voicemail detection | **UNKNOWN** | No evidence found. | Audio is out of scope; transcript-based checks need testing. |

### Data work
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Bulk labelling / dataset filtering / review-queue clearing | **GOOD (cost-led)** | Independent: 346,009 requests for under $10, beat Qwen on 27/37 and Gemma on 37/37 datasets (N-78); but trailed the best LLM on 14/15 annotation tasks by a median 11.6 macro-F1, at a median 44x lower cost (7,977 items, N-79); single run 89.0 vs Luna 91.1 (N-80). 9,081 entity-match pairs cleared for $0.32 in 13 minutes; 227 skills graded with 11,892 probabilities for $0.48. Gotcha: a request near 58k tokens stalled with no error and no timeout. | Audit a random sample by hand; where accuracy matters more than cost, compare with an LLM on that sample first (N-79). Cap request size well under 64k and set client timeouts. |
| Feature extraction for ML models | **HYBRID** | Jev answers as features lifted a logistic regression's F1 0.880 to 0.897 (independent, single test, 2026-09-21 snapshot; no record in the 2026-11-11 register, so it cannot carry GOOD). Vendor: 20 questions as features cut RMSE from 0.788 (mean baseline) to 0.456, vs 0.703 for CatBoost on raw text (n=800 held-out, N-168). | Each Noul becomes a numeric feature; the trained model around it decides, so measure the lift on your own held-out split. |

### Vision (jev-1.14 preview)
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Image presence check, then box | **HYBRID (preview, not production)** | Independent: 32 thumbnails x3 runs, presence 96/96 yes and 96/96 no; a small badge was found 69/51/23% at 800/640/500 px until cropped and re-asked (N-142); 23 motion events, 23/23 people vs an old pipeline 14/23 (self-report, N-144); 1,000 synthetic items, review band 48% stated vs 34% actual accuracy (N-141). Partner: 20 COCO objects, 14 on target, tie with YOLOX-S, lower median IoU 0.81 vs 0.91 (N-143). Vendor: images and box are a preview that needs an opt-in header, "not recommended for production" (N-145). | Ask a presence Noul first (the box always returns four edges); crop and re-ask for small targets; never trust a box alone. Pin the version. |

### Out of scope or harmful
| Placement | Verdict | Why |
|---|---|---|
| Anything that writes text (replies, summaries, drafts) | **BAD** | Jev does not generate. Split out any hidden decision ("should we reply?") and use an LLM for the words. Choosing among pre-written replies works as a pattern: code picks the reply, Jev never writes (N-157; 400 candidates with an LLM fallback, self-report, N-163). |
| Resume screening / credit / hiring decisions | **BAD** | High-stakes and regulated; needs a fairness audit of your own process. One independent name-swap audit found a 0.0 pp white-minus-black callback gap, smaller than four LLM screeners (1,824 evals, one domain, one prompt, N-150): that is not an audit of your process. Clinician-advice cues shifted health-triage decisions 47.6 pts (N-148). A vendor customer case claims parity at 88% lower cost (n=150 live roles, N-151). Option-order sensitivity (7/120); a 69% preference for one of six equivalent options, likely from a secondhand video (N-162), needs re-sourcing. |
| Clinical triage / medical decisions | **BAD (as a decision); research-only as a paired signal** | Independent: 62.3% on 8,742 medical items, numeric physiology 35.9-39.4% vs Gemma4-31B 58.1% (N-146); clinician-advice cues shifted decisions 47.6 pts, and pairing with an LLM cut the excess 42-48% held-out (2,134 cases, preprint, N-148); 4th of 5 by macro-F1 on 925 decision points (N-147). Do not deploy. For research, Noul per option with a 0.90 cut (N-146), paired with an LLM. |
| Trading / market calls | **BAD** | Independent backtest: -17 bps per trade, does not beat fees (secondhand summary, N-162). 17 days live: -4.5R vs an LLM's -1.2R; confidence ran backwards on direction (507 scored calls, N-161). |
| Arithmetic, counting, date windows as the decision itself | **BAD as asked** | Vendor-documented weak spots (N-173). Independent: numeric physiology 35.9-39.4% vs Gemma4-31B 58.1% (N-146); date arithmetic failed ~4 of 5 (N-157); moving a watt comparison into code lifted threshold separation 0.21 to 0.69 (N-107). Compute in code, then ask Jev the semantic remainder. |

## 4. The sweet spot: where Jev makes the MOST sense

Stack these properties. The more a task has, the bigger the payoff:

1. **An LLM is already doing a decision job** (a classifier prompt that returns a label or a bool).
   This is the easiest win: same decision, measured side by side (see integration.md, brownfield).
2. **High volume or inside a loop.** Cost is $0.042 per million input tokens and output is free, so
   judging everything becomes affordable (logs, emails, every trace, every tool call).
3. **Many independent questions about the same input.** Batching is the multiplier: 13 questions in
   one call were 12.2x cheaper and 10x faster than 13 calls (vendor cookbook, jev-1.12), and 1 vs 10
   questions took the same time in our probe.
4. **Consistency matters.** Evals, audits and QA, where an LLM judge's run-to-run variance hides real
   changes.
5. **You need a probability, not just a label.** For cascades: act when confident, escalate when not.
6. **Reversible actions.** Mistakes get caught downstream (ranking, routing, pre-filtering).

The best case is a **pre-filter or cascade in front of an expensive model**: Jev clears the
confident majority and the LLM or human sees only the uncertain middle band.

## 5. Anti-patterns seen in the wild
- **One big question** instead of several atomic ones (phishing 62-89% vs 95% decomposed).
- **Holistic questions** ("is this good / useless / important?"): AUC 0.54 vs 0.72 with eight factual questions (independent, N-118).
- **Letting argmax decide** where a code-side threshold on the risky class works better (log triage).
- **Taking `choice` as the argmax in near-ties**: it can sit 0.01 below another option's probability; compute the argmax yourself (independent, N-172).
- **Labels as options** instead of policies (the agent ate at hunger 0).
- **Asking Jev about itself** ("do you have enough information?"): it said yes about 85% of the time.
- **Near-synonym options** split the probability mass; an option you leave out can never be chosen.
- **Ignoring option order**: Jev leans toward the option that comes first (vendor failure mode, N-171); test both orders.
- **Arrays of items in one request**: accuracy dropped 96% to 72% at 20 items (independent, N-157); one item per question.
- **Treating 0.5 as a default threshold**: answers jitter about ±0.02 between runs; 0.5 is a knife edge.
- **Using `jev-latest` in tuned paths**: when the alias moves, your thresholds quietly go stale.
- **Switching 1.13 to 1.14 without re-calibrating**: one independent test moved +41.6 pts on one set and -3.9 on another (N-62).
- **Near-64k requests**: one stalled with no error and no timeout; keep a margin and set client timeouts.
- **`curl https://...` text in state**: Cloudflare returned a 403 before the request reached the API (independent, N-54).
- **Trusting confidence as correctness**: on 2,319 labelled issues the 0.9-1.0 bucket stated 98.9% but was right 84.3% (independent, N-73); rerank scores > 0.9 were 66% relevant (N-120). Calibrate before any absolute cut.
