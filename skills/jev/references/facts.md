# Jev facts snapshot

**Checked 2026-11-11** (first snapshot 2026-09-21). Jev launched 2026-09-15 and the vendor says limits
"can change without notice". Anything older than ~30 days here should be re-checked against the live docs
before it goes into a PRD or a cost estimate: fetch `https://docs.typesafe.ai/llms.txt` (every docs page also
serves Markdown when you append `.md`) and `GET /v1/models`.

**What was re-read on 2026-11-11 (live):** the docs pages models, changelog, api/errors, images, box,
model-jaggedness and legal; the privacy policy, MCA and DPA; the enterprise page; four cookbooks
(parallel_questions, consistency_choice_cookbook, classification_using_confidence, skill_suggestion); PyPI and npm
versions; `gh` for the official skill repo.
**Not re-read (marked "unverified" where they appear):** third-party integration pages (Zapier, Make, Mastra,
LiteLLM, Braintrust, Vercel, OpenRouter, Cloudflare, AI/ML API), rival-model pages, independent test reports.
Those come from the research run in `docs/research/2026-11-11/evidence.md` (IDs `N-nn`), where a small model
extracted them from the page. Rows without a date in their source column were last measured 2026-09-21.

Every row names its source and the date it was read. A table with a single source says so above the table.

## Identity
Source for this section: https://typesafe.ai/blog/dont-call-it-a-decision-model (2026-11-03; read 2026-11-11,
unverified: extracted by a small model) and https://docs.typesafe.ai/models.md (read 2026-11-11, live).
- Vendor: **TypeSafe AI**. "System One" is the model *class*; **Jev** is the first model in it. The vendor now
  says "System One model", not "decision model": "Jev makes judgments, code makes decisions".
- Non-generative: fills typed answers with probabilities in one pass; it cannot write text or explain.
- Same weights for every account; no fine-tuning or per-customer adapters ("not fine-tuned or LoRA-adapted").
- Closed hosted API; no open weights, no self-hosting.
- Not the only hosted option any more: OpenAI Decisions API (GA 2026-10-22) and several Jev-compatible rivals.
  See "Alternatives" below.

## API
| Item | Value | Source (read) |
|---|---|---|
| Endpoint | `POST https://api.typesafe.ai/v1/systemone`; `GET /v1/models` | models.md (live 2026-11-11) |
| Auth | `Authorization: Bearer $TYPESAFE_API_KEY` | models.md (live 2026-11-11) |
| Shape | `{model, state, questions}` in; `{model, answers, usage}` out. **Not OpenAI-compatible** | 2026-09-21 snapshot |
| Primitives | `noul` (P true), `choice` (up to 255 options; 256 rejected, N-128), `score` (2-10 ordered levels), and `box` (finds where something is in an image; needs jev-1.14; preview) | models.md, box.md (live 2026-11-11); N-128 (cookbook, 2026-11-11) |
| Confidence | Returned for Choice, Score and Box; Noul returns a probability only. Measures how concentrated the distribution is, not correctness. Reported: `choice` can sit 0.01 below another option's probability in a near-tie, so compute the argmax yourself | box.md (live 2026-11-11); typesafe-sdk-python issue #15 (N-172, unverified) |
| Errors | 400 (bad body, or `max_tokens_exceeded`), 401, 413 (body over 32 MiB), 415 (bad `Content-Encoding`), 422 (validation detail), 429 (+ `retry-after`), 529 Overloaded. Reported, not reproduced: Cloudflare returns an HTML 403 before the API when `state` contains `curl ... https://...` | api/errors.md (live 2026-11-11); typesafe-sdk-js issue #15 (N-54, open, unverified) |
| Model ids | `jev-1.14.0` is newest (2026-10-14). `jev-latest` and `jev-preview` both resolve to `jev-1.14.0` (on 2026-09-21 they resolved to 1.13.0). `jev-1.13.0` is still listed and accepted; this skill still pins `jev-1.13.0` until S-13 decides. `GET /v1/models` lists only the aliases, but dated ids are accepted. Reported: 1.14 vs 1.13 moved +41.6 pts on one phishing set and -3.9 pts on RAGTruth, neither in the release notes | models.md, changelog.md (live 2026-11-11); sammy143/decision-models-eval (N-62, unverified) |
| Price | **$0.042 per 1M input tokens; output free** (both versions) | models.md (live 2026-11-11) |
| Price note | Reported, not verified: one independent test found Jev bills ~38% more tokens than SubQ Snap for identical short text; one plugin lists output at $0.13/M against the docs' "free" (question open in typesafe-ai/skills issue #12) | N-62; github.com/typesafe-ai/skills/issues/12 (open, read 2026-11-11) |
| Rate limits | Set per organisation, measured in tokens per second and requests per second; the docs print no numbers and point to a login-gated console. The 2026-09-21 figures (250,000 tokens/s, 1,200 requests per **minute**) could not be re-verified, and the docs now state requests per **second**, so do not compare the two or build capacity math on either. Higher limits on custom and enterprise plans | models.md (live 2026-11-11) |
| Context | 64k per request (state + all questions) and 32k per question (state + one question) by default. Header `TypeSafe-Danger-Zone-Long-Context: true` raises both to 262k on 1.13 and 1.14; same price per token, slower and less accurate | models.md (live 2026-11-11) |
| Input | Text, a JSON object or an array. PNG and JPEG images on 1.13 and 1.14, but only with header `TypeSafe-Danger-Zone-Images: true` (without it: 400); the docs call images and Box "not yet up to our standards... for production". Each side 280-1568 px; 78,400-2,458,624 total pixels. Audio and video "not natively accept[ed] (yet)" | models.md, images.md (live 2026-11-11) |
| Languages | English strongest; others (incl. CJK) work less well. The 1.14 release notes say "better multilingual support" (vendor, unmeasured). Reported by independents: 86.7% on Belebele (122 languages) but weaker on low-resource ones (N-78); negation failed in Italian and Portuguese, Arabic and Korean least sure (N-89) | changelog.md (live 2026-11-11); N-78, N-89 (unverified) |

Cost rule of thumb: a 600-token battery call is about $0.000025; 1M such calls is about $25.

## Measured latency (client-side, includes network)
Rows without a source date were measured on or before 2026-09-21 and not repeated.
| Where | State size | p50 | p95 | Source |
|---|---|---|---|---|
| India (our probe) | ~300-420 tokens, 1 or 10 questions | ~890 ms | ~920 ms | our probe, 2026-09-21 |
| India | ~7k tokens | ~1,450 ms | ~1,500 ms | our probe, 2026-09-21 |
| India | ~23k tokens | ~2,030 ms | ~2,040 ms | our probe, 2026-09-21 |
| India, Claude Code router test | 2 requests, 94-skill roster | ~0.9-1.0 s | n/a | N-8 (n=8, synthetic, 2026-11-11) |
| Ellavox worker run | notification batteries | 373 ms | 1,189 ms | Ellavox run, 2026-09-21 |
| oh-my-pi (independent) | 39-skill route | ~330 ms | ~372 ms | 2026-09-21 |
| LiteLLM benchmark (partner) | router classification | 127 ms median | n/a | 2026-09-21 |
| Japan (independent) | not stated | 1.9-2.4 s range | n/a | 2026-09-21 |
| Israel (independent) | 84-skill roster | 0.59-3.11 s | n/a | N-2 (unverified) |
| OpenRouter provider stat | jev-1.14 | 0.12 s P50 | n/a | openrouter.ai/typesafe/jev-1.14 (N-177, unverified) |
| Independent adopters | short state | 177-330 ms median | 371 ms (jevals) | N-52, N-133, N-32, N-112 (unverified) |

Latency scales with state size and distance from US hosting, **not** with question count. The first request of
a process adds ~700 ms (TLS), reported in N-133.

## SDKs and integrations
Versions below were checked on PyPI / npm on 2026-11-11 (live). Rows marked "unverified" come from the
research run and were not re-read.
| Package | Version (date) | Notes | Source (read) |
|---|---|---|---|
| PyPI `typesafe-sdk` | 0.7.5 (2026-10-14) | Python >= 3.10; pydantic; `response_model` arg; default model `jev-latest`, so override it | PyPI JSON (live 2026-11-11) |
| npm `@typesafe-ai/sdk` | 0.7.0 (2026-10-14) | **Node >= 22**; `noul()/choice()/score()` helpers; request payload types no longer exported (breaking); `debug` log level prints bodies | npm view (live 2026-11-11); breaking-change note unverified |
| PyPI `langchain-typesafe` | 0.0.2 (2026-11-05), no longer alpha | `TypeSafeClassifier`; `invoke()` takes state and questions together; experimental `ModelRouterMiddleware`, `AutoModeMiddleware` (needs `[experimental]`; refuses risky calls, does not ask approval) | PyPI JSON (live 2026-11-11); API detail from a wheel listing, unverified |
| npm `@langchain/typesafe` | 0.0.2 | middleware at `@langchain/typesafe/middleware`; Node >= 20 | npm view (live 2026-11-11) |
| Official agent skill | `typesafe-ai/skills` (2,892 stars, pushed 2026-10-23) | Patterns and question design pointing to live docs; installable as a Claude Code plugin (`claude plugin marketplace add typesafe-ai/skills`). No fit test, calibration method, brownfield playbook or PRD | gh api (N-178, read 2026-11-11) |
| n8n (official) | `@typesafe-ai/n8n-nodes-typesafe-ai` 0.10.0 (2026-10-20); repo `typesafe-ai/n8n-nodes-typesafe-ai` | operations Evaluate and Route | npm view (live 2026-11-11) |
| n8n (community) | `n8n-nodes-typesafe` 0.3.3 (unofficial, MIT); `@n3ndor/n8n-nodes-typesafe-jev` 0.4.1; `n8n-nodes-jev-classification` (needsReview output) | unofficial | npm view, N-102 (unverified) |
| Pydantic AI | `TypeSafeModel` released in `pydantic-ai-slim` (found in 2.50.0 and 2.67.0) | `pip install "pydantic-ai-slim[typesafe]"` | wheel listing of 2.67.0 (read 2026-11-11) |
| DSPy | 3.5.0 (2026-11-10) ships `dspy/_vendor/lm15/providers/typesafe.py` and `dspy/adapters/decision.py` | `dspy.LM("typesafe:jev-latest")` per docs (pin a version instead); call syntax unverified | wheel listing of dspy 3.5.0 (read 2026-11-11) |
| Vercel AI Gateway | `typesafe-ai/jev` | 1.14 added 2026-10-15; AI SDK >= 7.0.105 `experimental_evaluate`; `POST https://ai-gateway.vercel.sh/v1/evaluate`; provider package `@ai-sdk/typesafe-ai` 3.0.38; per-request ZDR and no-training. Unverified | vercel.com changelog (cached 2026-10-18); npm view (2026-11-11) |
| OpenRouter | listed (no beta label seen) | ids `typesafe/jev-1.14` ($0.042/M, output $0, 262,144 context shown), `typesafe/jev-1.13`, `~typesafe/jev-latest`; 1.14 not on EU in-region routing; rejected a 9-question request in one independent kit. Unverified | openrouter.ai/typesafe/jev-1.14 (read 2026-11-11); N-62 |
| Cloudflare AI | `typesafe/jev` still maps to **1.13** (32k, ZDR "Yes"); `typesafe/jev-1.14.0` beta (image and box, "not recommended for production"). Alias differs from TypeSafe's own `jev-latest`. Unverified | developers.cloudflare.com/ai/models/typesafe/jev (read 2026-11-11); jev-1.14.0 page (cached 2026-11-07) |
| AI/ML API | `typesafe/jev` floats to 1.14; pins `typesafe/jev-1.14`, `typesafe/jev-1.13`; 262,144 context. Price not shown: the earlier ~$0.0578/M figure is unverified | docs.aimlapi.com (read 2026-11-11) |
| Braintrust | Jev judge scorer | Own key, or built-in Jev for scorers (docs: "Enable Jev" in settings; blog says access on request: the two disagree); `wrapTypeSafe()` JS, `wrap_typesafe()` Python. Unverified | braintrust.dev docs (cached 2026-10-21), blog (cached 2026-10-17) |
| LiteLLM | pass-through `/typesafe/v1/systemone`; unified `/v1/systemone` and `/v1/decisions`; `litellm.systemone`; Auto Router classifier; day-0 Jev 1.14 (2026-10-15). Unverified | docs.litellm.ai (cached 2026-10-16 to 2026-11-06) |
| Mastra | classifiers with evaluation models; `@mastra/core` >= 1.69.0 + `@ai-sdk/typesafe-ai`. Unverified | mastra.ai blog (cached 2026-10-14) |
| Zapier (official) | app "TypeSafe Jev", action `ask_questions` (yes/no, pick-one, scale, minimum confidence, unsure handling); also via Zapier MCP and SDK. Replaces Zapier's 2026-09-24 blog saying there was no native app. Unverified, re-read before relying on it | zapier.com/apps/typesafe-jev/integrations (read 2026-11-11) |
| Make (official) | TypeSafe app: "Evaluate a state", "Make an API call"; API key connection. Unverified | apps.make.com/typesafe (read 2026-11-11) |
| Google Sheets | vendor demo Apps Script `JEV_TOP10` (not a Marketplace add-on); third-party "Jev for Sheets" and jev-sheets OSS | docs.typesafe.ai/demos/airbnb-listing-search.md (read 2026-11-11) |
| MCP | No official MCP server found. Community: `typesafe-mcp` 0.4.0, `mcp-server-jev` 0.1.0, `jev-mcp` 0.5.1, a .NET TypeSafe.Mcp. Unverified | npm view, gh org repos (read 2026-11-11) |
| Other | TrueFoundry AI Gateway, Maia Foundation connectors (cached 2026-10-10 to 10-20); `typesafe-ai/system-one-adapter-python` (drop-in client backed by LLM APIs). Unverified | N-184 |

## Vendor-documented failure modes (jaggedness page)
Source for this table: https://docs.typesafe.ai/model-jaggedness.md, read live 2026-11-11. The page numbers
**9** modes (the 2026-09-21 copy listed 8; "choice option order" is new).
| # | Failure mode | Do instead |
|---|---|---|
| 1 | Literal reading | Write the exact condition and criteria for each option |
| 2 | Math and numbers (incl. counting, numeric representations, score magnitudes) | Keep arithmetic in code |
| 3 | Date/time comparison | Extract components; compare in code |
| 4 | Indirection (multi-hop) | Reduce hops; point at the relevant state |
| 5 | Large state full of irrelevant detail | Filter first |
| 6 | Adversarial content ("State is data... can move the answer") | Precise prompts; test edge cases; don't rely on it alone |
| 7 | Contradictory instructions and criteria | Align them |
| 8 | **Choice option order**: Jev "leans toward the option that comes first" | Reorder the options and check the answer stays consistent |
| 9 | Generation | Use a generative model |

Independent evidence on option order is mixed and unverified (N-171): about 0 flips up to 8 options, ~3% at
128-150, 0.130 argmax flips at 28 options, ~10% probability shift.

## Official cookbooks (docs.typesafe.ai/cookbooks/<slug>)
Source for this table: the cookbook pages, read live 2026-11-11 where the row says "re-read"; other rows were
read 2026-09-21. The four re-read pages run on `jev-1.14.0`; the Airbnb demo still uses `jev-latest`. Treat
every threshold as an example.

| Slug | What it shows |
|---|---|
| `parallel_questions` | 13 questions in one request: 12.2x cheaper, 11.8x faster (re-read) |
| `consistency_noul_cookbook`, `consistency_choice_cookbook` | Choice cookbook: a post's least stable decision changes 4.0% of the time on average over 15 repeats of 40 post versions (re-read). Consistency, not accuracy. The Noul figure was not re-read |
| `classification_using_confidence` | n=60 filings: the 28 at confidence >= 0.9 were right 93% of the time, the other 32 50%; fall back to the parent label below 0.9 (re-read) |
| `hierarchical_classification` | Beam search through deep taxonomies |
| `rerank_typesafe` | Reranking BM25 shortlists |
| `classifying_rag_passages` | Keep / flag contradicting / drop injected passages |
| `citation_check` | Citation support check |
| `llm_guardrails` | Inbound and outbound screening with severity |
| `sde_cascade` | Small LLM, then Jev verify, then big LLM only when needed |
| `function_calling` | Function names and arguments as questions |
| `skill_suggestion` | 1 of 194 skills, two requests; n=452: wrong skill loads 15.7% -> 7.9%, needless loads 14.0% -> 5.2% (re-read) |
| `semantic_find` | Line-by-line search |
| `autoformat` | Structure recovery |
| `entity_alignment` | 3-level Score mapped to merge / leave / curator |
| `date_extraction_cookbook` | Extract date parts, resolve in code |
| `pre_parsed_value_extraction_cookbook` | Regex finds candidates, Jev selects |
| `autoresearch_feature_discovery` | Jev answers as ML features |
| `verify_llm_outputs`, `infinite_cardinality_choice`, `feeder_watch`, `reading_scanned_documents`, `ocr_confidence_bounding_boxes`, `twitch_chat_filter`, `basic_memory`, `cart_from_primitives`, `intelliprompter` | New since 2026-09-21 (listed in the docs index; not re-read: N-129, N-128, N-145, N-57, N-95, N-168, N-139) |

Patterns pages: a companion Noul (YES 0.7 / NO 0.3) is now recommended over an `other` option
(docs.typesafe.ai/patterns/companion-noul, read 2026-11-11). This is a fact about the vendor's advice; whether
this skill adopts it is decision D-4.

## Data and legal (quotes checked against the live pages on 2026-11-11; a named person should still read the current text)
Sources: https://typesafe.ai/legal/privacy-policy, https://typesafe.ai/legal/mca (last updated Sep 23, 2026),
https://typesafe.ai/legal/data-processing (last updated Apr 24, 2026), https://typesafe.ai/enterprise,
https://docs.typesafe.ai/legal.md; all read live 2026-11-11.
- **Privacy Policy:** "We (1) will not train or fine tune any artificial intelligence or machine learning
  models on Input". **MCA s4.1 (the contract):** TypeSafe will not "include Customer Data in a dataset used to
  train (i.e., to modify the model weights of) any artificial intelligence or machine learning models without
  Customer's prior consent". So the contract has a consent exception; ask for written confirmation that no
  consent is given or requested.
- **MCA s4.1(c)** licenses "in perpetuity, any Customer Data (i) to derive and generate Telemetry". **s4.3:**
  Telemetry includes "summary statistics and classifications, metrics, and learnings related to Customer's use
  of the Services" and "TypeSafe may Process Telemetry without restriction".
- **Zero data retention:** "available for enterprise customers" (enterprise page); the legal index says to ask
  through the support request form. Route-level ZDR: Vercel per request, Cloudflare lists "Yes" (both unverified).
- US hosting ("The Services are hosted in the United States", 2026-09-21 snapshot).
- **SOC 2 Type II:** the enterprise page says to "visit our Trust Center to request access to the SOC 2 Type II
  report" (vendor claim, report not reviewed). ISO 27001 not found. The Trust Center and subprocessor pages
  errored on 2026-11-11 and could not be read.
- **Retention:** no period in days. DPA: retained "for as long as necessary taking into account the purpose of
  the Processing". MCA s10.3: TypeSafe is "under no obligation to store or retain Customer Data and may delete
  Customer Data at any time in its sole discretion".
- **DPA:** breach notice "within 72 hours" (s5.2); audits "no more than once every 12 months" (s5.3); EU SCCs
  Module 2 (and Module 3 where the customer is a processor) plus the UK Addendum.
- **Other MCA terms:** liability cap is the greater of 12 months' fees or $50 USD (s12); s2.3(b) bans using the
  Services or Output for "model distillation" or to "develop... a similar or competing product or service"; s2.5
  says API updates may break compatibility and TypeSafe "will use commercially reasonable efforts to provide
  advance notice"; purchased credits expire after 12 months at the latest; disputes go to arbitration (s15),
  with hearings by telephone, video or in San Francisco. Governing law was not found in the text read.
- The earlier early-Terms wording ("solely for the purpose of evaluating", indexed May 2026) was not found in
  the MCA, which replaces it.

## Alternatives (as of 2026-11-11)
| Option | Facts | Source (read) |
|---|---|---|
| OpenAI Decisions API | GA 2026-10-22 (beta 2026-10-06); `POST /v1/decisions`; gpt-6-luna only; predicate / choice / score; $0.10 per 1M input tokens, $0.01 cached, output free; up to 400 questions per request; ZDR and HIPAA for eligible customers; US/EU residency; native GPT-Live voice. Vendor claims: 10x faster than Responses API; Datadog 40x faster p95 on risky shell commands (customer claim published by the vendor). No independent head-to-head found | openai.com/index/decisions-api, community.openai.com (read 2026-11-11, N-183) |
| Jev-compatible rivals | Laya, Kev, SubQ Snap, Solar Decide, Clef (Cloudflare), Decis, ollaya server. Some beat Jev on single suites (N-83, N-85, N-62); Jev beat Laya on 9/11 agent points (N-1). Unverified | N-184 |
| Small trained classifier | deberta injection classifier 89.01% at 54 ms vs Jev 86.35% at 348 ms (Red Hat). Unverified | N-43 |

## Headline numbers and how much to trust them
Rows were read 2026-09-21 unless a source says 2026-11-11.
| Claim | Source | Trust |
|---|---|---|
| 100% binary agreement, 92-913x lower variance than LLM judges | LangChain (partner) | 5 examples x 100 reps; "low variance does not mean high accuracy" is their own caveat |
| 193.6x faster / 444.6x cheaper | Vendor workflow evals | Self-reported; scored against two frontier models' averaged answers. A secondhand test found 3.2-5x, not 193x (N-162, low confidence, 2026-11-11) |
| 95% vs Haiku 73.75% routing, 5.43x faster | LiteLLM (partner) | n not stated |
| Spam 98.3% zero-shot vs 98.4% trained TF-IDF | Independent | One dataset |
| Phishing single question 62.6-89.4%, decomposed 95% | Independent (two tests) | Strong signal for decomposition; whether the 62.6% / 95% source is the partner Trustle post is unverified (N-60) |
| 0.9-1.0 confidence bucket: 98.9% mean confidence, 84.3% accurate | Independent (monumei, n=1,794 of 2,319; jev-1.14; 2026-11-11) | Raw probabilities are overconfident; one partner test (AnthusAI, n=8,801) reports isotonic calibration cut ECE 0.117 -> 0.008. Replaces the 2026-09-21 row "right 64% in the 80-95% band" (one dataset) |
| Zero-shot model routing at chance | Independent (arXiv 2610.02267, n=13,923; 2026-11-11) | Jev beat Laya on 9 of 11 decision points in another test (N-1) |

## Still unverified (do not use as fact)
- Rate-limit numbers (console is login-gated).
- Whether output tokens are free in every channel (skills issue #12 is open; one plugin charges $0.13/M).
- BAA availability; Trust Center contents; subprocessor names.
- Free credits ("$5 per month" appears only in a cached Zapier blog) and signup status ("may be limited due to
  demand" / "paused in late September", both secondhand).
- AI/ML API price; Braintrust access route (docs and blog disagree).
- Governing law of the MCA (not found in the text read).
- Zapier, Make, Mastra, LiteLLM, Vercel, OpenRouter and Cloudflare details (research-run extraction only).
- DSPy usage syntax (`dspy.LM("typesafe:...")`): the files ship, the call syntax was not run.
- OpenAI Decisions API latency: vendor claims only; no independent measurement.
- The Noul half of the consistency cookbook; the nine newer cookbooks' numbers.
- Independent test reports cited as `N-nn` (languages, option order, near-ties, price per token, rival wins).
