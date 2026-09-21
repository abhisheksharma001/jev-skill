# Where Jev fits: the use-case map

Evidence snapshot: 2026-09-21, about a week after launch (2026-09-15). Most results are small
experiments by early adopters. Re-check before quoting numbers as settled.

## Contents
1. The one-line test
2. Verdict rules
3. The map (22 placements)
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

"Partner" = LangChain, Braintrust, Vercel, LiteLLM and other integrators with a commercial stake.
"Independent" = everyone else. A verdict resting only on partner/vendor evidence is not GOOD.

## 3. The map

### Evals and judging
| Placement | Verdict | Evidence (source, n) | How to use it |
|---|---|---|---|
| Bounded pass/fail and rubric evals of agent outputs | **GOOD (bounded)** | LangChain: 500/500 binary agreement with a human oracle, 92-913x lower score variance than LLM judges, $0.00035/call, 0.44 s (partner, **n=5 cases** x100 reps). Dan Shipper: 12 passages with planted defects, median 0.35 s vs 8.83 s (independent, small n). | One atomic question per rubric line; Score for graded quality, Noul for pass/fail. Validate against ~50+ human labels. LangChain's own warning: "a consistently wrong evaluator can produce bad feedback at scale". |
| Online eval / monitoring every production trace | **HYBRID** (cost-enabled, unproven in prod) | Only partner cost projections; no independent production report yet. | Sample first, route low confidence to a human, pin the model version. |
| Pairwise judging of complex LLM outputs, code review | **BAD (opinion-based)** | An independent critic: "no reasoning, no tools, no codebase context; it will prefer the simpler output". No measured failure rate found. | Keep a reasoning model. Jev may pre-filter obvious fails. |

### Routing and control flow
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Intent / model / skill routing | **GOOD** | LiteLLM auto-router: 5.43x faster than Haiku (127 ms vs 688 ms median), 96% cheaper (partner). Independent shadow run: model routing Jev 61/69 = LLM 61/69 (tie), hand rules 23; UI routing Jev 65% vs LLM 70%. oh-my-pi skill routing: p50 ~330 ms, 0 misses at 39 skills. | Choice with an explicit `none`/`other` option. When the top-2 probabilities are within ~0.1, ask a follow-up or stay quiet (oh-my-pi). |
| Agent control flow (done? retry? hand off? which tool?) | **HYBRID** | Adopted in oh-my-pi and Octomind. Failures: "sure and wrong" when options were labels not policies (agent ate at hunger 0 of 100); "do you have enough info?" questions said yes about 85% of the time; reordering 4 options changed 7/120 answers. | Options must be **policies** ("eat: only when hunger > 70") but compute numbers in code. Never ask Jev to self-assess. Keep the final call in code. |
| Agent context compaction / memory-write decisions | **HYBRID** | Selection-based compaction plugins exist and are fast; critics note dropped context can matter later. | Retain/drop decisions only with verbatim retention; keep synthesis on an LLM. |

### Guardrails and safety
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Dangerous tool-call / shell-command gate | **HYBRID** | Independent certification: "Jev was the safest" shell classifier tested, but only after fixed rules settled the obvious commands. LangChain `AutoModeMiddleware` (experimental) refuses risky calls but does not ask for approval. | Deny-lists and allow-lists first; Jev for the ambiguous remainder; pair with human-in-the-loop for irreversible actions. |
| Content / UGC moderation | **GOOD (tie-level)** | Near Here: 48/50 vs Gemini 43 and Mistral 42; on an earlier set Gemini 50/50 vs Jev 49/50; 129/132 across all prompt tests (independent, n=50-132). | Noul per policy, Score for severity. Calibrate per category. |
| Prompt-injection / jailbreak detection | **UNKNOWN** | No published adversarial research. The vendor lists adversarial state as a failure mode. Our probes: 7/7 injection cases held; Ellavox: 3/4 held, with a fake-delimiter injection moving two answers to 0.53/0.58. Fake delimiters were the weakest vector in both. | Never the only defence. Put untrusted text in a labelled state field; test your own injection set. |
| PII detection | **UNKNOWN** | Demos only. The bigger risk runs the other way: sending PII to a third-party API. | Build an egress guard (see integration.md) before any shadow run. |

### Triage and classification
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Spam / email / ticket / lead triage | **HYBRID** | Zero-shot spam 98.3% vs a TF-IDF model trained on ~14,800 labels 98.4%. But one big "is this phishing?" question: 89.4% vs a 2-line rule 91.8% and Haiku 94.2% (2,000 emails); in another test 62.6% vs Haiku 81.3%. **Decomposed into 5 atomic questions weighted in code: 95%.** | Decompose; weight in code; rules first. |
| Log / alert / incident triage | **HYBRID** | dev.to log triage: letting Choice decide missed replication lag (INFO-level logs); a 0.50 threshold set **in code** caught 500/500 incidents with 0 false alarms in 3,000 test logs. Cribl: 2-3x more errors than a purpose-built classifier on 28-way semi-structured log typing. | Pre-filter in front of a bigger LLM; thresholds in code on raw probabilities. |
| Replacing a fine-tuned small classifier in a stable domain | **HYBRID** | Zero-shot Jev beats zero-shot encoders (macro-F1 0.782 vs 0.712) and automates ~2x the traffic at 90% precision. But a 310M encoder fine-tuned on 250 labels beat Jev by 12 points on topic classification (Japanese text; tied on 2 polarity tasks) and was 4-20x faster. | Jev wins cold start and fast-changing labels; a trained encoder wins stable, high-volume, labelled domains. Or feed Jev answers as features into your classifier (F1 0.880 to 0.897). |
| Lead scoring / prioritising | **HYBRID (low stakes only)** | Adopter demos (e.g. 1,700 emails through 4 evaluations for about 18 cents); no accuracy measurement; systematic preference among equivalent options was observed elsewhere. | Only for reversible prioritisation; shadow first; audit which leads get deprioritised. |
| Compliance / legal / contract clause review | **UNKNOWN** | Many demos and proposals; no accuracy against legal ground truth. Vendor-run workflow evals: weakest on invoice processing (61.8%), "it slips wherever numbers are involved". | First-pass ranking for human reviewers only; numbers and dates in code. |

### Retrieval (RAG)
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Reranking / relevance filtering | **GOOD** | nDCG@10 0.501 vs Voyage 0.504 vs Cohere 0.486 (independent); BM25 top-1 11 to 18 of 24; golden-set relevance 22/25. Gains shrink when candidates are already plausible (89% scored >= 0.7). | Score or Noul per passage in one call. Use the per-document probability as a keep/drop cut. |
| Grounding / faithfulness / citation checks | **HYBRID** | Our probe: supported claims 0.81-0.98 (including paraphrases), unsupported 0.01-0.04, up to ~5.7k tokens (n=27 textual). Independent 32-case test: "less convincing"; missed a >= vs > error; 3 of 4 mistakes had confidence > 0.8. Numeric-inference claims failed in our probe (0.26-0.36). | Textual support and contradiction: yes. Numbers and comparisons: code or an LLM. |

### Voice AI
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Post-call QA / outcome classification / escalation audit | **GOOD (provisional, post-call only)** | Practitioner reports of batch transcript reclassification; our probe: 6/6 synthetic full transcripts correct on outcome, booked and wants-human (one battery call each, ~0.9 s). Evidence is anecdotal plus synthetic. | Battery of atomic questions over the finished transcript (structured turns as JSON). |
| In-call decisions: end-of-turn, barge-in, live routing | **UNKNOWN** (latency-bound) | Only proposals. Voice budget is ~800 ms voice-to-voice; measured Jev round trips are 0.33-0.9 s short-state (region-dependent) and 1.9-2.4 s from Japan. On partial transcripts our outcome question fell to `other`: ask only what is already observable. | Async or speculative only (e.g. decide during TTS playback); never block the turn on it. |
| Voicemail detection | **UNKNOWN** | No evidence found. | Audio is out of scope; transcript-based checks need testing. |

### Data work
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Bulk labelling / dataset filtering / review-queue clearing | **GOOD** | 9,081 entity-match pairs cleared for $0.32 in 13 minutes; 227 skills graded with 11,892 probabilities for $0.48. Gotcha: a request near 58k tokens stalled with no error and no timeout. | Audit a random sample by hand; cap request size well under 64k and set client timeouts. |
| Feature extraction for ML models | **GOOD (vendor cookbook + independent)** | Jev answers as features lifted a logistic regression's F1 0.880 to 0.897 (independent); vendor "autoresearch feature discovery" cookbook. | Each Noul becomes a numeric feature. |

### Out of scope or harmful
| Placement | Verdict | Why |
|---|---|---|
| Anything that writes text (replies, summaries, drafts) | **BAD** | Jev does not generate. Split out any hidden decision ("should we reply?") and use an LLM for the words. |
| Resume screening / credit / hiring decisions | **BAD** | High-stakes and regulated with no fairness audit. Indirect warning signs: a 69% preference for one of six equivalent options, and option-order sensitivity (7/120). |
| Trading / market calls | **BAD** | Independent backtest: -17 bps per trade, does not beat fees. |
| Arithmetic, counting, date windows as the decision itself | **BAD as asked** | Vendor-documented weak spots. Compute in code, then ask Jev the semantic remainder. |

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
- **Letting argmax decide** where a code-side threshold on the risky class works better (log triage).
- **Labels as options** instead of policies (the agent ate at hunger 0).
- **Asking Jev about itself** ("do you have enough information?"): it said yes about 85% of the time.
- **Near-synonym options** split the probability mass; an option you leave out can never be chosen.
- **Treating 0.5 as a default threshold**: answers jitter about ±0.02 between runs; 0.5 is a knife edge.
- **Using `jev-latest` in tuned paths**: when the alias moves, your thresholds quietly go stale.
- **Near-64k requests**: one stalled with no error and no timeout; keep a margin and set client timeouts.
- **Trusting confidence as correctness**: in one test Jev was right 64% of the time in its 80-95% band.
