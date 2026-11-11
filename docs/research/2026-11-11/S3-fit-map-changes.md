# S3. Proposed fit-map changes (evidence as of 2026-11-11)

Target: `skills/jev/references/fit-map.md` (snapshot 2026-09-21). IDs point to S1.
Rule applied strictly: GOOD needs an independent measured result where Jev matched or beat the
alternative. Partner or vendor evidence alone never makes GOOD. No measurement = UNKNOWN.

## 0. Header and invariants

- Snapshot line: change "2026-09-21, about a week after launch" to "2026-11-11 (first map 2026-09-21)".
  Evidence base is now 186 records, many with n in the hundreds or thousands (S1).
- Add one line: "jev-1.14.0 exists (2026-10-14); `jev-latest` now points to it (N-174). Independent
  tests show 1.14 vs 1.13 swings of +41.6 pts on one phishing set and -3.9 pts on RAGTruth, not in
  the release notes (N-62). Results below are mostly 1.13; re-calibrate before switching." Keep the
  repo pin on `jev-1.13.0`.
- Section heading "The map (22 placements)": becomes 31 placements if all new rows below are accepted.

## 1. Changes to existing rows

| # | Current text (quote) | Proposed verdict | Evidence IDs | One-line reason |
|---|---|---|---|---|
| 1 | "Bounded pass/fail and rubric evals of agent outputs \| **GOOD (bounded)**" | **GOOD (bounded)**, evidence replaced | N-110, N-111, N-109, N-118, N-113 | Now an independent 27-comparison study (matches LLM judges in >= 21/27) and a clinical one (0.50 vs Opus 0.49). Add: errors overlap LLM judges > 85%, so it is not a second opinion; accepts "almost right" answers (MLflow 64/72). Note danielgshea repo copies the LangChain numbers, not new. |
| 2 | "Online eval / monitoring every production trace \| **HYBRID** (cost-enabled, unproven in prod) \| Only partner cost projections" | **HYBRID**, evidence updated | N-33, N-112, N-114 | First independent production log: six weeks of real agent gates with per-gate counts (e.g. "done" replies 30/30, 1 FP) and failures. Replay drift: 1 of 7,242 crossed 0.5 (N-114). |
| 3 | "Pairwise judging of complex LLM outputs, code review \| **BAD (opinion-based)** \| ... No measured failure rate found." | **BAD (as one holistic question)**, now measured | N-118, N-33, N-31 | Measured: "is this test useless?" AUC 0.54 vs 0.72 with eight factual questions; "does the founder need to know" cleared 19/174. A decomposed review pipeline exists but is unmeasured (N-31). |
| 4 | "Intent / model / skill routing \| **GOOD** \| ... model routing Jev 61/69 = LLM 61/69 (tie) ... oh-my-pi ... 0 misses at 39 skills." | Split into three rows (4a-4c) | see below | Model routing and skill routing now have different evidence. |
| 4a | (same row, intent and skill/tool part) | **GOOD (tie-level vs small LLMs; trails frontier; roster up to ~130)** | N-3, N-71, N-4, N-2, N-5, N-9 | Independent: 97.6% at 126 skills (n=500); CLINC150 92.2% vs Luna/Haiku 93.6%; 87.6% vs glm 90.6% (n=299). Scale gotcha: at 84 skills with upstream thresholds top-1 53.6%, silent 36.2%, wrong 10.1% (84.1% right when it answers). Trails Claude 143 vs 158 of 162. How to use: tune the abstain threshold on your own roster. |
| 4b | (same row, model routing part: "model routing Jev 61/69 = LLM 61/69 (tie)") | **HYBRID (only with labelled, task-specific calibration; zero-shot is at chance)** | N-1, N-10, N-11, N-12 | arXiv 2610.02267 (indep, n=13,923): "neither model beats chance on zero-shot model routing". Conflicts with the earlier independent 61/69 tie; keep both, cite both. Savings claims (40-70%) are 12-prompt tests with no quality check, and Claude Code has no per-message model switch. |
| 4c | (new split) Skill hints inside an agent harness that already sees the skill list | **UNKNOWN** | N-6, N-7, N-8 | Vendor cookbook helps a weak agent with a 60-char index (wrong loads 15.7% -> 7.9%, n=452, vendor). Independent author found no measured benefit inside Claude Code. Our test n=8 synthetic (5 right, 0 wrong). No independent with-vs-without measurement. |
| 5 | "Agent control flow (done? retry? hand off? which tool?) \| **HYBRID**" | **HYBRID**, evidence strengthened | N-19, N-20, N-22, N-23, N-158 | Independent +9.5 pts on Terminal-Bench (N-19) and independent -19.0 pts when delegating tool choices without a fitted threshold (N-20). Weak points: permission approval 53.7, progress 61.6 (N-19); still decided 44% with evidence missing (N-22). The "ate at hunger 0" case is likely Tyler Folkman's villagers (N-158, unconfirmed). |
| 6 | "Agent context compaction / memory-write decisions \| **HYBRID** \| Selection-based compaction plugins exist and are fast" | **HYBRID** for context filtering and memory save; split out memory retire (new row R5) | N-19, N-28, N-96, N-98, N-99 | Context: test-log trimming cut 40.2% and lost 0 of 72 required lines (N-19). Save: raw-turn selection non-inferior to LLM extraction (pre-registered, N-98); jevmem stopped rule breaks 0/18 vs 10/18 but trailed Claude auto memory 40/54 vs 47/54 (N-96). Mixed, so not GOOD. |
| 7 | "Dangerous tool-call / shell-command gate \| **HYBRID**" | **HYBRID**, add a warning | N-23, N-41, N-55, N-183 | Counterfeit policy text in state dropped mean is_risky 0.893 -> 0.290 (N-41, partner). Wording matters: force-push scored 0.77 under one phrasing (N-23). OpenAI's Datadog claim (40x faster p95) is a vendor-published customer claim. |
| 8 | "Content / UGC moderation \| **GOOD (tie-level)**" | **GOOD (tie-level)**, add strict-FPR caveat | N-43, N-45, N-44, N-52 | Independent: content safety 86.20%, best of the field (N-43); moderation blocks survived forged structure (N-45); 48/51 vs LLM 46/51 (N-52). Partner caveat: at a 0.5% false-positive budget recall 34% vs 61% for a 1B classifier (N-44). |
| 9 | "Prompt-injection / jailbreak detection \| **UNKNOWN** \| No published adversarial research." | **BAD as the only defence** (one layer at most) | N-43, N-46, N-42, N-41, N-48, N-50, N-72 | Now measured. Independent: 86.35% vs a 54 ms deberta classifier 89.01% (N-43); at a 1% false-negative target any gate needs > 91.8% escalation (N-46). Partner: 76.2% vs 95.4% (N-42); counterfeit policy cut recall to 3.9-9.7% (N-41); 25/27 runs broken (N-48). Followed planted labels 6/20 (N-72). |
| 10 | "PII detection \| **UNKNOWN** \| Demos only." | **UNKNOWN**, one tiny data point | N-33, N-64 | Private-leak check 16/16 caught at a 0.3 cut with 6 false alarms in 24 (indep, n=16). Splunk redaction is design only. |
| 11 | "Spam / email / ticket / lead triage \| **HYBRID** \| ... in another test 62.6% vs Haiku 81.3%. **Decomposed into 5 atomic questions weighted in code: 95%.**" | **HYBRID**, evidence updated; fix source label | N-72, N-71, N-66, N-61, N-62, N-60 | Real tickets 84.9% vs Haiku 88.2% (n=272); real phishing 97.1-97.5% (n=848); scam SMS AUROC 0.995 (n=500). The 62.6%/95% figures now appear in a partner post (Trustle, 2026-10-30). The fit-map labelled them independent on 2026-09-21. Re-check the original source before keeping "independent". |
| 12 | "Log / alert / incident triage \| **HYBRID**" | **HYBRID**, evidence updated | N-69, N-70, N-29 | On-call paging: all incidents caught, 1 false page in 136, precision 0.63 -> 0.92 once the CPU value was passed (N-69). CI triage lost to regex 18/20 vs 14/18 and was rejected (N-70). BGL triage F1 54% vs Claude 23% (N-29). |
| 13 | "Replacing a fine-tuned small classifier in a stable domain \| **HYBRID**" | **HYBRID**, evidence updated | N-43, N-44, N-81, N-79 | More cases where trained small models win: deberta injection 89.01% at 54 ms (N-43); classical models won on Banking77 and tabular data (N-81, cached). |
| 14 | "Lead scoring / prioritising \| **HYBRID (low stakes only)** \| ... no accuracy measurement" | **HYBRID (low stakes only)**, first number | N-87, N-10 | First measurement, synthetic: 89/100 exact vs Haiku 84, Fable 97; all 15/15 hot leads found. Still no real-data result. |
| 15 | "Compliance / legal / contract clause review \| **UNKNOWN** \| ... no accuracy against legal ground truth." | **HYBRID (first-pass flagging for human review only)** | N-152, N-153, N-155, N-154 | Measured now. Partner: MAUD AUPR 0.656 vs Gemini 0.699; CUAD 0.553 vs 0.644 (N-152). Independent synthetic: ToS traps F1 89% vs regex 57% (N-155). 96.4% confidence on a fabricated statute (N-154). Never the final word. |
| 16 | "Reranking / relevance filtering \| **GOOD** \| ... Use the per-document probability as a keep/drop cut." | **GOOD**, change the how-to | N-120, N-121, N-122, N-127 | Independent: ahead of FLAN-UL2 and 3 cross-encoders (N-120); Recall@5 equal to Cohere at 60.6% lower cost (N-121). But > 0.9 scores were only 66% relevant: calibrate (2-parameter fit on ~2,000 labelled pairs) before an absolute keep/drop cut. |
| 17 | "Grounding / faithfulness / citation checks \| **HYBRID**" | **HYBRID**, evidence updated | N-123, N-129, N-131, N-62 | Cascade with a frontier model: same accuracy, but Jev admitted 23.2% of unsupported claims vs 14.1% (N-123). 1.14 regressed 3.9 pts on RAGTruth vs 1.13 (N-62). Three narrow checks caught "may" -> "must" where one broad one missed (N-131). |
| 18 | "Post-call QA / outcome classification / escalation audit \| **GOOD (provisional, post-call only)** \| ... anecdotal plus synthetic." | **HYBRID (provisional)** | N-136, our 6/6 synthetic probe | Strict GOOD rule: no independent measured comparison on real transcripts exists. Only a partner citing 27 of 34 metrics >= 96% (source not read) and our synthetic n=6. Keep the battery advice. |
| 19 | "In-call decisions: end-of-turn, barge-in, live routing \| **UNKNOWN** (latency-bound) \| Only proposals ... On partial transcripts our outcome question fell to `other`" | **UNKNOWN**, with one working independent demo | N-133, N-134, N-135, N-183 | Voice browser decides on every partial transcript ("is the command complete?" >= 0.6), p50 ~300 ms, 34/34 author fixtures (N-133). It is browser commands, not a phone agent. STT errors invert answers (N-135). OpenAI Decisions API now integrates natively with GPT-Live (vendor). |
| 20 | "Voicemail detection \| **UNKNOWN** \| No evidence found." | No change | none | Nothing new found. |
| 21 | "Bulk labelling / dataset filtering / review-queue clearing \| **GOOD**" | **GOOD (cost-led)**, add accuracy caveat | N-78, N-79, N-80, N-86 | Beats Qwen on 27/37 and Gemma on 37/37 datasets (N-78, indep) so GOOD holds, but trails the best LLM on 14/15 annotation tasks by a median 11.6 macro-F1 (N-79). Audit a sample. |
| 22 | "Feature extraction for ML models \| **GOOD (vendor cookbook + independent)**" | No verdict change; update vendor numbers | N-168 | Autoresearch cookbook now n=800 held-out, RMSE 0.788 (mean) -> 0.456 (vendor). |
| 23 | "Anything that writes text ... \| **BAD**" | No change; add workaround | N-163, N-157 | Selection from pre-written candidates works as a pattern, not generation. |
| 24 | "Resume screening / credit / hiring decisions \| **BAD** \| ... no fairness audit. Indirect warning signs: a 69% preference for one of six equivalent options" | **BAD**, wording updated | N-150, N-151, N-148, N-162 | One independent name-swap audit found a 0.0 pp white-minus-black callback gap (n=1,824, one domain, one prompt), smaller than four LLMs. That is not a fairness audit of your process. Cue bias in health triage was 47.6 pts (N-148). The 69% figure seems to come from a secondhand trading video (N-162): re-source it. Vendor case study claims parity at 88% lower cost (N-151). |
| 25 | "Trading / market calls \| **BAD** \| Independent backtest: -17 bps per trade" | **BAD**, add live result | N-161, N-162 | 17 days on a live account: -4.5R vs an LLM's -1.2R; confidence ran backwards on direction. |
| 26 | "Arithmetic, counting, date windows as the decision itself \| **BAD as asked**" | **BAD as asked**, add evidence | N-146, N-157, N-107 | Numeric physiology 35.9-39.4% vs Gemma 58.1%; date arithmetic failed ~4 of 5; moving the watt comparison into code lifted separation 0.21 -> 0.69. |

## 2. Proposed new rows (fit-map table format)

Under **Routing and control flow**:
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Browser / computer-use action choice from a list of controls | **HYBRID** | Partner: 137/138 vs Browser Use 133/138 at 10.7x lower cost, with LLM fallback (N-24). Independent small n: 21-23 decisions all right (N-26); 49/49 via WebMCP (N-25, single thread). | Jev picks from indexed controls; an LLM types text and plans; code enforces spend, credentials and irreversible steps. |

Under **Guardrails and safety**:
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Fraud / transaction-risk final call | **HYBRID** | Partner: one ring, 27/29 caught vs rules 26 and Sonnet 18 (N-63). Independent: scam SMS AUROC 0.995, n=500 (N-66); fraud email cascade 96/100 with 31 escalated (N-65, Self). | Code computes the facts (shared cards, velocity); Jev answers narrow questions; decompose; feed answers into the rule engine. |
| AML / sanctions / KYC triage | **UNKNOWN** | Designs only (Splunk, illustrative thresholds, N-64; hackathon, N-67). | Shadow mode; backtest before any auto-clear; redact account numbers before the API. |

Under **Retrieval (RAG)**:
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Search-loop stop / evidence sufficiency | **HYBRID** | Partner: stop decision Recall@5 93.25% equal to DeepSeek, 0.55 s vs 2.23 s (N-34). Independent warning: with evidence missing Jev still decided 44% (N-22); asking sufficiency separately raised recall but over-triggered (N-147). | Ask about the retrieved text ("does passage X state Y?"), never "do you have enough?". Cap loop steps in code. |

Under **Agent memory** (new heading, or under Routing and control flow):
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Memory retire / overwrite (does a new fact replace an old one?) | **BAD (as a yes/no gate)** | Independent, pre-registered, 500 pairs: binary gate retired 39.2% of only-suggested changes; 3-way choice 15.5% but lost 15.3 pts detection, missing its budget (N-97). | Never retire automatically. Use a 3-way choice (changed / suggested / same) and send "changed" to a human or an LLM. |

Under **Vision** (new heading; jev-1.14 preview):
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Image presence check, then box | **HYBRID (preview, not production)** | Independent: presence 96/96 yes and 96/96 no on 32 thumbnails; small targets 23-69% until cropped (N-142); doorbell 23/23 vs old pipeline 14/23 (N-144); review band 48% stated vs 34% actual (N-141). Partner: tie with YOLOX on 20 objects, lower IoU (N-143). Vendor: preview, needs the images header (N-145). | Ask a presence Noul first; crop and re-ask for small targets; never trust a box alone. Pin the version. |

Under **Triage and classification** / regulated:
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| Clinical triage / medical decisions | **BAD (as a decision); research-only as a paired signal** | Independent: 62.3% on 8,742 medical items, numeric physiology 35.9-39.4% (N-146); clinician-advice cues shifted Jev's decisions 47.6 pts, pairing with an LLM cut excess 42-48% held-out (N-148); 4th of 5 by macro-F1 (N-147). | Do not deploy. For research, use Noul per option with a high cut (N-146) and pair with an LLM. |

Under **Data work**:
| Placement | Verdict | Evidence | How to use it |
|---|---|---|---|
| No-code workflow routing (n8n / Zapier / Make Switch replacement) | **UNKNOWN** | Official n8n node 0.10.0, official Zapier and Make apps, community nodes (N-101 to N-105). No workflow outcome published. | Route low confidence to a "needs review" branch; pin the model id; shadow next to the existing Switch first. |

## 3. Decisions asked for, in one line each

- **Model routing:** GOOD -> HYBRID (zero-shot at chance, N-1; conflicts with the 61/69 tie, both cited).
- **Skill routing at scale:** GOOD at 39 (oh-my-pi) and 126 skills (97.6%, N-3); at 84 skills with
  default thresholds it mostly abstains (36.2% silent, 10.1% wrong, N-2); 194 vendor only (N-7). Keep
  GOOD (tie-level) for the router itself; skill hints inside Claude Code: UNKNOWN (new 4c).
- **Resume screening / bias:** stays BAD; wording now cites the one name-swap audit (N-150) and the
  health cue-bias result (N-148).
- **In-call voice on partial transcripts:** stays UNKNOWN; one independent working demo (N-133).
- **Memory gates:** save/select HYBRID (N-96, N-98); retire BAD as yes/no (N-97, new row).
- **Vision / box:** new row HYBRID (preview, not production) (N-141 to N-145).
- **Fraud:** new row HYBRID (partner + one independent SMS result); AML/KYC UNKNOWN.

## 4. Anti-pattern additions (section 5 of the fit-map)

- **Absolute cuts on raw probabilities**: 0.9-1.0 bucket 98.9% stated vs 84.3% right (N-73, n=2,319);
  > 0.9 rerank scores 66% relevant (N-120). Replace "right 64% in its 80-95% band" with these.
- **Holistic questions** ("is this good / useless / important?"): AUC 0.54 (N-118).
- **Arrays of items in one request**: 96% -> 72% at 20 items (N-157).
- **Option order**: the vendor now lists it as failure mode #8 (N-171).
- **Taking `choice` as the argmax in near-ties**: compute argmax yourself (N-172).
- **`curl https://...` in state**: Cloudflare 403 before the API (N-54).
- **Switching 1.13 -> 1.14 without re-calibrating** (N-62).
