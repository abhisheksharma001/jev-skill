# Jev facts snapshot

**Checked 2026-09-21.** Jev launched 2026-09-15 and the vendor says limits "can change without
notice". Anything older than ~30 days here should be re-checked against the live docs before it goes
into a PRD or a cost estimate: fetch `https://docs.typesafe.ai/llms.txt` (every docs page also serves
Markdown when you append `.md`) and `GET /v1/models`.

## Identity
- Vendor: **TypeSafe AI**. "System One" is the model *class*; **Jev** is the first model in it.
- Non-generative: fills typed answers with probabilities in one pass; it cannot write text or explain.
- Same weights for every account; no fine-tuning or per-customer adapters.
- Closed hosted API; no open weights, no self-hosting.

## API
| Item | Value |
|---|---|
| Endpoint | `POST https://api.typesafe.ai/v1/systemone`; `GET /v1/models` |
| Auth | `Authorization: Bearer $TYPESAFE_API_KEY` |
| Shape | `{model, state, questions}` in; `{model, answers, usage}` out. **Not OpenAI-compatible** |
| Primitives | `noul` (P true), `choice` (up to 255 options), `score` (2-10 ordered levels) |
| Confidence | Returned for Choice and Score only; measures how concentrated the distribution is, not correctness |
| Errors | 401, 422 (validation detail), 429 (+ `retry-after`), 529 overload |
| Model ids | `jev-1.13.0` (pin this). `jev-latest` and `jev-preview` both resolved to 1.13.0 on 2026-09-21. `GET /v1/models` lists only the aliases, but the dated id is accepted |
| Price | **$0.042 per 1M input tokens; output free** |
| Rate limits | 250,000 tokens/s; 1,200 requests/min; "adjusting dynamically" |
| Context | 64k tokens per request (state + all questions); 32k for state + longest single question |
| Input | Text, JSON object or array. No image/audio/video |
| Languages | English strongest; others (incl. CJK) work less well |

Cost rule of thumb: a 600-token battery call is about $0.000025; 1M such calls is about $25.

## Measured latency (client-side, includes network)
| Where | State size | p50 | p95 |
|---|---|---|---|
| India (our probe) | ~300-420 tokens, 1 or 10 questions | ~890 ms | ~920 ms |
| India | ~7k tokens | ~1,450 ms | ~1,500 ms |
| India | ~23k tokens | ~2,030 ms | ~2,040 ms |
| Ellavox worker run | notification batteries | 373 ms | 1,189 ms |
| oh-my-pi (independent) | 39-skill route | ~330 ms | ~372 ms |
| LiteLLM benchmark (partner) | router classification | 127 ms median | n/a |
| Japan (independent) | not stated | 1.9-2.4 s range | n/a |

Latency scales with state size and distance from US hosting, **not** with question count.

## SDKs and integrations
| Package | Version (date) | Notes |
|---|---|---|
| PyPI `typesafe-sdk` | 0.7.0 (2026-09-18) | Python >= 3.10; pydantic; `response_model` arg; default model `jev-latest`, so override it |
| npm `@typesafe-ai/sdk` | 0.6.0 (2026-09-15) | Node >= 20; `noul()/choice()/score()` helpers; `debug` log level prints bodies |
| PyPI `langchain-typesafe` | 0.0.1a3 (2026-09-20), alpha | `TypeSafeClassifier`; experimental `ModelRouterMiddleware`, `AutoModeMiddleware` (needs `[experimental]`; refuses risky calls, does not ask approval) |
| Official agent skill | `typesafe-ai/skills` | One SKILL.md pointing to live docs: patterns and question design. No fit test, calibration method, brownfield playbook or PRD |
| Braintrust | Jev judge scorer | Own key or native access on request; `wrapTypeSafe()` tracing |
| Vercel AI Gateway | `typesafe-ai/jev` | AI SDK >= 7.0.105 `experimental_evaluate`; per-request ZDR and no-training |
| OpenRouter | beta | `TYPESAFE_BASE_URL=https://openrouter.ai/api`; ids `typesafe/jev-1.13`, `~typesafe/jev-latest` |
| Cloudflare AI | `typesafe/jev` | lists 32k context |
| AI/ML API | `typesafe/jev` | `POST /v1/decisions`, ~$0.0578/M (about 38% markup) |
| Pydantic AI | `TypeSafeModel` merged | release status unverified |
| n8n | community `n8n-nodes-typesafe` 0.2.0 | unofficial, MIT |
| Not found | DSPy, Mastra, official n8n/Zapier/Make, official MCP server | community MCP toolkits exist |

## Vendor-documented failure modes (jev-1.13 "jaggedness" page)
| # | Failure mode | Do instead |
|---|---|---|
| 1 | Literal reading | Write the exact condition and criteria for each option |
| 2 | Math and numbers (incl. counting) | Keep arithmetic in code |
| 3 | Date/time comparison | Extract components; compare in code |
| 4 | Indirection (multi-hop) | Reduce hops; point at the relevant state |
| 5 | Large state full of irrelevant detail | Filter first |
| 6 | Adversarial content ("State is data... can move the answer") | Precise prompts; test edge cases; don't rely on it alone |
| 7 | Contradictory instructions and criteria | Align them |
| 8 | Generation | Use a generative model |

## Official cookbooks (docs.typesafe.ai/cookbooks/<slug>)

Several still use jev-1.12, and one quotes stale pricing. Treat their thresholds as examples.

| Slug | What it shows |
|---|---|
| `parallel_questions` | Batching: 13 questions, 12.2x cheaper, 10x faster |
| `consistency_noul_cookbook`, `consistency_choice_cookbook` | Run-to-run standard deviation ~0.01 |
| `classification_using_confidence` | Confidence cut: 90% accurate above 0.9, n=30 |
| `hierarchical_classification` | Beam search through deep taxonomies |
| `rerank_typesafe` | Reranking BM25 shortlists |
| `classifying_rag_passages` | Keep / flag contradicting / drop injected passages |
| `citation_check` | Citation support check |
| `llm_guardrails` | Inbound and outbound screening with severity |
| `sde_cascade` | Small LLM, then Jev verify, then big LLM only when needed |
| `function_calling` | Function names and arguments as questions |
| `skill_suggestion` | 1 of 182 options, two-stage |
| `semantic_find` | Line-by-line search |
| `autoformat` | Structure recovery |
| `entity_alignment` | 3-level Score mapped to merge / leave / curator |
| `date_extraction_cookbook` | Extract date parts, resolve in code |
| `pre_parsed_value_extraction_cookbook` | Regex finds candidates, Jev selects |
| `autoresearch_feature_discovery` | Jev answers as ML features |

## Data and legal (verify the current text yourself)
- No training on customer requests or responses.
- Zero data retention: enterprise, via privacy@typesafe.ai.
- US hosting.
- No SOC 2 / ISO attestation found.
- No retention period in days found (the DPA page did not render).
- The MCA was not reviewed.
- An early Terms copy (indexed May 2026, pre-launch) granted access "solely for the purpose of
  evaluating". It may be outdated: a named person should read the current terms before production use.

## Headline numbers and how much to trust them
| Claim | Source | Trust |
|---|---|---|
| 100% binary agreement, 92-913x lower variance than LLM judges | LangChain (partner) | 5 examples x 100 reps; "low variance does not mean high accuracy" is their own caveat |
| 193.6x faster / 444.6x cheaper | Vendor workflow evals | Self-reported; scored against two frontier models' averaged answers |
| 95% vs Haiku 73.75% routing, 5.43x faster | LiteLLM (partner) | n not stated |
| Spam 98.3% zero-shot vs 98.4% trained TF-IDF | Independent | One dataset |
| Phishing single question 62.6-89.4%, decomposed 95% | Independent (two tests) | Strong signal for decomposition |
| Right 64% of the time in the 80-95% confidence band | Independent | One dataset; no vendor calibration curve exists |
