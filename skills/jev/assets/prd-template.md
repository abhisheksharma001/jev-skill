# PRD: <decision name> with Jev

> Fill every `<...>`. Delete nothing: write "n/a, because ..." instead, so a reviewer can see the
> question was considered. Numbers about Jev (price, limits, versions) must carry a check date.

## 1. Summary
- **Decision being made:** <one sentence: "decide whether / which / how much ...">
- **Where it sits:** <pipeline step; what happens before and after>
- **Who or what makes it today:** <LLM prompt | rules | human | trained classifier | nothing yet>
- **Why change:** <cost | latency | consistency | coverage ("judge every item") | new capability>
- **Entry point:** <brownfield | mid-project | greenfield>

## 2. Fit verdict
- `fit_check.py` result: <GO | GO WITH GUARDS | NO-GO> with the printed reasons.
- Closest placement in the fit map and its verdict: <placement: GOOD | HYBRID | BAD | UNKNOWN>,
  evidence quality <independent | partner | none>
- If UNKNOWN or HYBRID: what experiment settles it: <...>

## 3. Non-goals
- Text generation stays on <LLM>.
- Arithmetic, counting and date logic stay in code: <list the computed fields passed into state>.
- <anything irreversible Jev will NOT decide alone>

## 4. Users and success metrics
| Metric | Baseline (incumbent) | Target | How measured |
|---|---|---|---|
| Miss rate (1 - TPR) per question | <...> | <...> | held-out eval split, n=<...> |
| False-alarm rate (1 - TNR) | <...> | <...> | same |
| Share of traffic automated (outside the middle band) | <...> | <...> | production logs |
| Cost per 1k decisions | <...> | <...> | tokens x $0.042/M (checked <date>) |
| p95 latency | <...> | <...> | client-side, from <region> |

Bars are written **before** results are seen.

## 5. Decision design
**State** (filtered, structured; untrusted text in labelled fields):
```json
<state schema>
```
**Questions** (one judgement each; every Noul has true/false criteria; every Choice has `other`):
| id | type | instructions (exact wording) | criteria / options / levels | action it drives |
|---|---|---|---|---|
| <...> | noul | <...> | true: <...> / false: <...> | <...> |

**Composition in code:** <how answers combine: AND = min, OR = max, weights, precomputed fields>
**Batching:** <which questions share one call; expected tokens per call>

## 6. Thresholds and routing
| Question | Cost of a miss vs false alarm | Threshold / band | Source |
|---|---|---|---|
| <...> | fn:<..> fp:<..> | low <..> / high <..> | `thresholds.json` from calibrate.py, eval n=<..>, <date> |

- Middle band goes to <fallback LLM | human queue>.
- Blind fallback (fallback never sees Jev's answer) on: <high-stakes paths>.

## 7. Calibration plan
- Labelled set: <source>, n=<...>, per-class minimum <...>, hard negatives: <list>.
- Labellers: <who>; agreement check: <how>.
- Data class: <synthetic | redacted | real with terms cleared by <name> on <date>>.
- Split: deterministic 70/30 by id; published numbers = eval split.
- Incumbent runs on the same cases for a side-by-side.

## 8. Architecture
- Seam: `DecisionModel` interface; Jev adapter + <fallback adapter>; fake adapter for tests.
- Model pinned: `<jev-1.13.0>`; `response.model` logged and alerted on change.
- Flags: per-path enable, shadow-only mode, kill switch; circuit breaker after <n> consecutive failures.
- Timeouts <ms>, retries on 408/429/5xx, request size cap <tokens> (well under 64k).
- Egress guard: <what is blocked or redacted before any call, including shadow>.
- Access route: <direct | OpenRouter | Vercel AI Gateway | ...> and why.

## 9. Rollout
| Phase | What runs | Exit criterion |
|---|---|---|
| 0 Offline | calibrate.py on labelled set, incumbent side by side | eval bars met |
| 1 Shadow | Jev beside incumbent; act on incumbent | <n> days; disagreement reviewed; bars still met on real data |
| 2 Partial | cascade on <x>% or one tenant, reversible paths first | no regression in <metric> |
| 3 Full | all intended paths | monitoring green for <n> days |

Rollback: flip <flag>. Expected effect within <time>.

## 10. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Confidently wrong answers (confidence is not correctness) | Calibrated bands; sample audit of <n> confident answers per week |
| Alias or version drift invalidates thresholds | Pinned id; alert on `response.model`; recalibration runbook |
| Prompt injection in state (fake delimiters were the weakest case) | Rules first; labelled untrusted fields; own injection test set in CI |
| Vendor: single closed provider, limits "can change without notice", no SLA history | Seam + warm fallback adapter; backpressure; outage drill |
| Data terms / PII | Named owner re-reads current terms; ZDR or redaction; egress guard |
| Non-English inputs | Per-language calibration |
| Option-order / lookalike-option sensitivity | `other` option; merged lookalikes; order-shuffle test |
| Silent stall near context limit | Size cap + client timeout |
| Low cost amplifies a wrong judge at scale | Human-labelled audit sample each <period> |

## 11. Verification
- [ ] Flag off: behaviour byte-identical (test name: <...>)
- [ ] Eval-split numbers meet section 4 bars (report attached, n=<...>)
- [ ] Outage drill: Jev key revoked mid-run, fallback serves, no user-visible error
- [ ] Injection set: <n> cases, <pass bar>
- [ ] Replay test: same inputs, same decisions (no answer sitting within ±0.03 of a threshold)
- [ ] Cost check: measured cost per 1k within 2x of estimate

## 12. Open questions
| # | Question | Owner | Needed by |
|---|---|---|---|

## 13. Facts used (with check dates)
| Fact | Value | Source | Checked |
|---|---|---|---|
| Price | $0.042 per 1M input tokens, output free | docs.typesafe.ai/models | <date> |
| Context | 64k request / 32k state + longest question | docs.typesafe.ai/models | <date> |
| Model | jev-1.13.0 | GET /v1/models + response.model | <date> |
