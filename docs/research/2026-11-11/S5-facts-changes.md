# S5. Proposed changes to `references/facts.md` (as of 2026-11-11)

Diff style: `-` current line, `+` proposed line. Sources: S1 IDs, plus URL + date read + live/cached.
"Haiku file" = extracted by a small model from a vendor or registry page and not re-checked by the main
session; quote those carefully, or re-read before merging.

## Header

```diff
- **Checked 2026-09-21.** Jev launched 2026-09-15 ...
+ **Checked 2026-11-11** (first snapshot 2026-09-21). Jev launched 2026-09-15; jev-1.14.0 shipped 2026-10-14 ...
```

## Identity

```diff
+ - TypeSafe now calls it a "System One model", not a "decision model": "Jev makes judgments, code makes
+   decisions" (blog "Don't Call It a Decision Model", 2026-11-03; https://typesafe.ai/blog/dont-call-it-a-decision-model, live 2026-11-11, Haiku file).
+ - Not the only hosted option any more: OpenAI Decisions API (GA 2026-10-22) and several Jev-compatible
+   rivals (Laya, Kev, SubQ Snap, Solar Decide, Clef). See "Alternatives" below (N-183, N-184).
```

## API table

```diff
- | Primitives | `noul` (P true), `choice` (up to 255 options), `score` (2-10 ordered levels) |
+ | Primitives | `noul`, `choice` (up to 255 options; 256 rejected), `score` (2-10 levels), and `box` (locate a thing in an image; jev-1.14 only, preview) |
  source: https://docs.typesafe.ai/models.md, /changelog.md (live 2026-11-11, Haiku file, N-174); 255 cap: infinite_cardinality_choice cookbook (live 2026-11-11, N-128)

- | Confidence | Returned for Choice and Score only; ... |
+ | Confidence | Returned for Choice, Score and Box; Noul returns a probability only. `choice` can sit 0.01 below another option's probability in near-ties: compute argmax yourself |
  sources: https://openrouter.ai/docs/guides/community/jev (cached 2026-11-09, N-177); typesafe-sdk-python issue #15 (live 2026-11-11, N-172)

- | Errors | 401, 422 (validation detail), 429 (+ `retry-after`), 529 overload |
+ | Errors | 400 (incl. `max_tokens_exceeded`), 401, 413 (body over 32 MiB), 415 (bad Content-Encoding), 422, 429 (+ `retry-after`), 529 Overloaded. Also: Cloudflare returns an HTML 403 before the API when state contains `curl ... https://...` |
  sources: https://docs.typesafe.ai/api/errors.md (live 2026-11-11; 529 verified by main session; others Haiku file, N-174); typesafe-sdk-js issue #15, open (live 2026-11-11, N-54)

- | Model ids | `jev-1.13.0` (pin this). `jev-latest` and `jev-preview` both resolved to 1.13.0 on 2026-09-21 ... |
+ | Model ids | `jev-1.14.0` is newest (2026-10-14). `jev-latest` and `jev-preview` now resolve to `jev-1.14.0`. `jev-1.13.0` still accepted: keep pinning it in tuned paths until re-calibrated. 1.14 vs 1.13 moved +41.6 pts on one phishing set and -3.9 pts on RAGTruth, neither in the release notes |
  sources: https://docs.typesafe.ai/models.md (live 2026-11-11; alias verified by main session, N-174); sammy143/decision-models-eval (live 2026-11-11, N-62)

  | Price | $0.042 per 1M input tokens; output free |   (unchanged)
+ | Price note | Cost per decision is not just the rate: one independent test found Jev bills ~38% more tokens than SubQ Snap for identical short text. A plugin prices output at $0.13/M vs the docs' "free"; asked in typesafe-ai/skills #12, unanswered |
  sources: N-62 (live 2026-11-11); https://github.com/typesafe-ai/skills/issues/12 (open, verified by main session)

- | Rate limits | 250,000 tokens/s; 1,200 requests/min; "adjusting dynamically" |
+ | Rate limits | Set per organisation; docs no longer print numbers; console is login-gated. The 2026-09-21 numbers cannot be re-verified |
  source: https://docs.typesafe.ai/models.md (live 2026-11-11, Haiku file)

- | Context | 64k tokens per request (state + all questions); 32k for state + longest single question |
+ | Context | 64k per request / 32k per question by default. Header `TypeSafe-Danger-Zone-Long-Context: true` raises both to 262k on 1.13 and 1.14 |
  source: https://docs.typesafe.ai/models.md (live 2026-11-11, Haiku file)

- | Input | Text, JSON object or array. No image/audio/video |
+ | Input | Text, JSON object or array; PNG/JPEG images on 1.13 and 1.14 behind header `TypeSafe-Danger-Zone-Images: true` (preview; vendor says jaggedness too high for production). Audio and video "not natively accepted (yet)". Frames 280-1568 px per side; 320 px wide gave a 400 in one test |
  sources: models.md, changelog.md, SDK changelog (live 2026-11-11, Haiku file); https://typesafe.ai/blog/jev-1-14 (N-145); feeder_watch cookbook; N-142

- | Languages | English strongest; others (incl. CJK) work less well |
+ | Languages | English strongest. 1.14 claims "better multilingual support" (vendor, unmeasured). Independent: 86.7% on Belebele (122 languages) but weaker on low-resource languages (N-78); negation failed in Italian/Portuguese, Arabic and Korean least sure (N-89) |
```

## Latency

```diff
+ | OpenRouter (provider stat) | jev-1.14 | 0.12 s P50 | n/a |   https://openrouter.ai/typesafe/jev-1.14 (live 2026-11-11, N-177)
+ | Independent adopters | short state | 177-330 ms median (jev-guardrails, voice-browser, JevHarness, jevals) | 371 ms p95 (jevals) |   N-52, N-133, N-32, N-112
+ | Our Claude Code router test (India) | 2 requests, 94-skill roster | ~0.9-1.0 s | n/a |   N-8 (n=8 synthetic)
+ First request of a process ~700 ms extra (TLS) (N-133). Israel, 84-skill roster: 0.59-3.11 s (N-2).
```

## SDKs and integrations table

```diff
- | PyPI `typesafe-sdk` | 0.7.0 (2026-09-18) | Python >= 3.10; pydantic; ... default model `jev-latest`, so override it |
+ | PyPI `typesafe-sdk` | 0.7.5 (2026-10-14) | Python >= 3.10; pydantic (since 0.7.0); default model `jev-latest`, so override it |
  source: PyPI JSON (verified by main session 2026-11-11)

- | npm `@typesafe-ai/sdk` | 0.6.0 (2026-09-15) | Node >= 20; ... |
+ | npm `@typesafe-ai/sdk` | 0.7.0 (2026-10-14) | **Node >= 22**; request payload types no longer exported (breaking) |
  source: npm view (verified by main session 2026-11-11)

- | PyPI `langchain-typesafe` | 0.0.1a3 (2026-09-20), alpha | ... |
+ | PyPI `langchain-typesafe` | 0.0.2 (2026-11-05), no longer alpha | `invoke()` takes state and questions together; experimental `ModelRouterMiddleware`, `AutoModeMiddleware` (needs `[experimental]`) |
+ | npm `@langchain/typesafe` | 0.0.2 | middleware at `@langchain/typesafe/middleware` |
  source: PyPI JSON, npm view (verified by main session 2026-11-11); API detail from wheel listing (Haiku file)

- | Official agent skill | `typesafe-ai/skills` | One SKILL.md pointing to live docs ... |
+ | Official agent skill | `typesafe-ai/skills` (2,892 stars, pushed 2026-10-23) | installable as a Claude Code plugin: `claude plugin marketplace add typesafe-ai/skills` |
  source: gh api (live 2026-11-11, N-178)

- | Braintrust | Jev judge scorer | Own key or native access on request; `wrapTypeSafe()` tracing |
+ | Braintrust | Jev judge scorer | Own key, or built-in Jev for scorers (docs: "Enable Jev" in settings; blog: access on request, unresolved); `wrapTypeSafe()` JS and `wrap_typesafe()` Python |
  source: braintrust.dev docs (cached 2026-10-21) and blog (cached 2026-10-17), Haiku file

- | Vercel AI Gateway | `typesafe-ai/jev` | AI SDK >= 7.0.105 `experimental_evaluate`; per-request ZDR and no-training |
+ | Vercel AI Gateway | `typesafe-ai/jev` | 1.14 added 2026-10-15; AI SDK >= 7.0.105 `experimental_evaluate`; HTTP `POST https://ai-gateway.vercel.sh/v1/evaluate`; evaluation fallbacks (beta); provider package `@ai-sdk/typesafe-ai` 3.0.38; per-request ZDR and no-training |
  source: vercel.com changelog (cached 2026-10-18); npm view (live 2026-11-11), Haiku file

- | OpenRouter | beta | `TYPESAFE_BASE_URL=https://openrouter.ai/api`; ids `typesafe/jev-1.13`, `~typesafe/jev-latest` |
+ | OpenRouter | listed (no beta label seen) | ids `typesafe/jev-1.14` ($0.042/M, output $0, 262,144 context shown), `typesafe/jev-1.13`, `~typesafe/jev-latest`. 1.14 not on EU in-region routing. Rejected a 9-question request in one independent kit |
  source: https://openrouter.ai/typesafe/jev-1.14 (live 2026-11-11); N-62

- | Cloudflare AI | `typesafe/jev` | lists 32k context |
+ | Cloudflare AI | `typesafe/jev` still maps to **1.13** (32k, ZDR "Yes"); `typesafe/jev-1.14.0` added as beta (image and box, "not recommended for production"). Alias mismatch with TypeSafe's own `jev-latest` |
  source: https://developers.cloudflare.com/ai/models/typesafe/jev/ (live 2026-11-11); jev-1.14.0 page (cached 2026-11-07)

- | AI/ML API | `typesafe/jev` | `POST /v1/decisions`, ~$0.0578/M (about 38% markup) |
+ | AI/ML API | `typesafe/jev` now floats to 1.14; pins `typesafe/jev-1.14`, `typesafe/jev-1.13`; states 262,144 context. Price not shown: the $0.0578/M figure is unverified |
  source: https://docs.aimlapi.com/api-references/decision-models/typesafe/jev (live 2026-11-11)

+ | LiteLLM | pass-through `/typesafe/v1/systemone`; unified `/v1/systemone` and `/v1/decisions`; `litellm.systemone`; Auto Router classifier; day-0 Jev 1.14 (2026-10-15) |
  source: docs.litellm.ai (cached 2026-10-16 to 2026-11-06), Haiku file

- | Pydantic AI | `TypeSafeModel` merged | release status unverified |
+ | Pydantic AI | `TypeSafeModel` released in `pydantic-ai-slim` (found in 2.50.0 and 2.67.0); `pip install "pydantic-ai-slim[typesafe]"` |
  source: pydantic-ai-slim 2.67.0 wheel listing shows models/providers/profiles `typesafe.py` (checked by this synthesis, 2026-11-11 live)

+ | DSPy | 3.5.0 (2026-11-10) ships `dspy/_vendor/lm15/providers/typesafe.py` and `dspy/adapters/decision.py`; `dspy.LM("typesafe:jev-latest")` per docs (pin a version instead) |
  source: dspy-3.5.0 wheel listing (checked by this synthesis, 2026-11-11 live). Brief said "NOT verified"; now verified that the files ship. Usage syntax is from the Haiku file only.

+ | Mastra | classifiers with evaluation models; `@mastra/core` >= 1.69.0 + `@ai-sdk/typesafe-ai` |   mastra.ai blog (cached 2026-10-14)

- | n8n | community `n8n-nodes-typesafe` 0.2.0 | unofficial, MIT |
+ | n8n (official) | `@typesafe-ai/n8n-nodes-typesafe-ai` 0.10.0 (2026-10-20), repo `typesafe-ai/n8n-nodes-typesafe-ai`; operations Evaluate and Route |
+ | n8n (community) | `n8n-nodes-typesafe` 0.3.3 (unofficial, MIT); `@n3ndor/n8n-nodes-typesafe-jev` 0.4.1; `n8n-nodes-jev-classification` (needsReview output) |
  sources: npm view (official node verified by main session 2026-11-11); community: npm view (Haiku file), N-102

+ | Zapier (official) | app "TypeSafe Jev", action `ask_questions` (yes/no, pick-one, scale, minimum confidence, unsure handling); also via Zapier MCP and SDK. Supersedes Zapier's 2026-09-24 blog saying there was no native app |
  source: https://zapier.com/apps/typesafe-jev/integrations (live 2026-11-11, Haiku file; re-check before merging)

+ | Make (official) | TypeSafe app: "Evaluate a state", "Make an API call"; API key connection |
  source: https://apps.make.com/typesafe (live 2026-11-11, Haiku file)

+ | Google Sheets | vendor demo Apps Script `JEV_TOP10` (not a Marketplace add-on); third-party "Jev for Sheets" (JevMade), jev-sheets OSS |
  source: https://docs.typesafe.ai/demos/airbnb-listing-search.md (live 2026-11-11)

- | Not found | DSPy, Mastra, official n8n/Zapier/Make, official MCP server | community MCP toolkits exist |
+ | Not found | official MCP server. Community: `typesafe-mcp` 0.4.0, `mcp-server-jev` 0.1.0, `jev-mcp` 0.5.1, a .NET TypeSafe.Mcp |
  source: npm view, gh org repos (live 2026-11-11, Haiku file)

+ | Other | TrueFoundry AI Gateway, Maia Foundation connectors (cached 2026-10-10 to 10-20); `typesafe-ai/system-one-adapter-python` (drop-in client backed by LLM APIs) |
```

## Failure modes ("jaggedness")

```diff
- ## Vendor-documented failure modes (jev-1.13 "jaggedness" page)
+ ## Vendor-documented failure modes (jaggedness page, read 2026-11-11)
  ...
- | 8 | Generation | Use a generative model |
+ | 8 | **Choice option order**: Jev "leans toward the option that comes first" | Shuffle options in tests; average across orders; put no default option first |
+ | 9 | Generation | Use a generative model |
```
Source: https://docs.typesafe.ai/model-jaggedness.md (live 2026-11-11, Haiku file, N-173). The C file
lists finer-grained items (scoping words and negations, counting long lists, numeric representations,
score magnitudes); D counts 9 numbered modes. Re-read the page to fix the exact count.
Independent option-order evidence is mixed: ~0 flips up to 8 options, ~3% at 128-150 (cached), 0.130
argmax flips at 28 options (cached), ~10% probability shift (cached) (N-171).

## Cookbooks table

```diff
- Several still use jev-1.12, and one quotes stale pricing.
+ As of 2026-11-11 the cookbooks read live run on jev-1.14.0; the Airbnb demo still uses `jev-latest`.
- | `parallel_questions` | Batching: 13 questions, 12.2x cheaper, 10x faster |
+ | `parallel_questions` | 13 questions in one request: 12.2x cheaper, 11.8x faster, n=5 runs (N-186) |
- | `consistency_noul_cookbook`, `consistency_choice_cookbook` | Run-to-run standard deviation ~0.01 |
+ | `consistency_*` | 40 items x 15 repeats: decision change 3.8-4.0% on average, 0/40 items above 1-in-10 (LLMs up to 40/40). Consistency, not accuracy (N-58) |
- | `classification_using_confidence` | Confidence cut: 90% accurate above 0.9, n=30 |
+ | `classification_using_confidence` | n=60 filings: 28 at >= 0.9 were 93% right; fall back to the parent label below 0.9 (N-91) |
- | `skill_suggestion` | 1 of 182 options, two-stage |
+ | `skill_suggestion` | 1 of 194, two-stage; n=452: wrong loads 15.7% -> 7.9%, needless 14.0% -> 5.2%; fixed 29, broke 7 of 280 (N-7, verified) |
+ | `verify_llm_outputs`, `infinite_cardinality_choice`, `feeder_watch`, `reading_scanned_documents`, `ocr_confidence_bounding_boxes`, `twitch_chat_filter`, `basic_memory`, `cart_from_primitives`, `intelliprompter` | new since 2026-09-21 (N-129, N-128, N-145, N-57, N-95, N-168, N-139) |
+ Patterns pages: companion Noul (YES 0.7 / NO 0.3) is now recommended over an `other` option (verified by main session 2026-11-11).
```

## Data and legal (exact quotes, Haiku file; re-read before merging)

```diff
- - No training on customer requests or responses.
+ - Privacy Policy: "We (1) will not train or fine tune any artificial intelligence or machine learning
+   models on Input". MCA s4.1 (the contract): TypeSafe will not "include Customer Data in a dataset used
+   to train ... without Customer's prior consent" (a consent exception). Ask for written confirmation
+   that no consent is given or requested.
+ - MCA s4.1(c): licence covers "in perpetuity, any Customer Data (i) to derive and generate Telemetry";
+   s4.3: Telemetry includes "classifications, metrics, and learnings related to Customer's use" and
+   "TypeSafe may Process Telemetry without restriction".
- - Zero data retention: enterprise, via privacy@typesafe.ai.
+ - ZDR: "available for enterprise customers" (enterprise page; legal index says via the support form).
+   Route-level ZDR: Vercel per request; Cloudflare lists ZDR "Yes".
  - US hosting. ("The Services are hosted in the United States")
- - No SOC 2 / ISO attestation found.
+ - SOC 2 Type II report "on request" via the Trust Center (vendor claim, not reviewed). ISO 27001 not found.
- - No retention period in days found (the DPA page did not render).
+ - No retention period in days. DPA now renders (https://typesafe.ai/legal/data-processing, published
+   2026-04-24): retained "for as long as necessary". MCA s10.3: no obligation to retain; may delete at any time.
+   DPA: breach notice within 72 hours; audit at most once per 12 months; EU SCCs Module 2 + UK Addendum.
- - The MCA was not reviewed.
- - An early Terms copy ... "solely for the purpose of evaluating" ...
+ - MCA (published 2026-09-23, https://typesafe.ai/legal/mca) replaces the early terms; the "solely for
+   evaluating" wording was not found. Liability cap: greater of 12-month fees or $50. Distillation and
+   competing-product ban (s2.3(b)). API changes may break compatibility, "commercially reasonable efforts"
+   notice (s2.5). Credits expire at 12 months. California law, San Francisco venue.
+ - Subprocessor list and Trust Center: pages errored on 2026-11-11 (unreadable).
```
Sources: privacy policy, MCA, DPA, enterprise page, legal index, all live 2026-11-11 (D file, N-181, N-182).

## Alternatives (new section)

```diff
+ ## Alternatives (as of 2026-11-11)
+ | Option | Facts | Source |
+ |---|---|---|
+ | OpenAI Decisions API | GA 2026-10-22 (beta 2026-10-06); `POST /v1/decisions`; gpt-6-luna only; predicate/choice/score; $0.10/M input, $0.01 cached, output free; up to 400 questions/request; ZDR + HIPAA for eligible customers; US/EU residency; native GPT-Live voice. Vendor: 10x faster than Responses API; Datadog: 40x faster p95 on risky shell commands (vendor-published customer claim) | openai.com/index/decisions-api, community.openai.com (live 2026-11-11, verified by main session, N-183) |
+ | Jev-compatible rivals | Laya, Kev, SubQ Snap, Solar Decide, Clef (Cloudflare), Decis, ollaya server. Some beat Jev on single suites (N-83, N-85, N-62); Jev beat Laya on 9/11 agent points (N-1) | N-184 |
+ | Small trained classifier | deberta injection 89.01% at 54 ms vs Jev 86.35% at 348 ms (Red Hat) | N-43 |
```

## Headline numbers table

```diff
- | Right 64% of the time in the 80-95% confidence band | Independent | One dataset; no vendor calibration curve exists |
+ | 0.9-1.0 bucket: 98.9% mean confidence, 84.3% accurate | Independent (monumei, n=1,794 of 2,319) | jev-1.14; raw probabilities overconfident, fixable with isotonic (ECE 0.117 -> 0.008, AnthusAI, partner, n=8,801) |
+ | Zero-shot model routing at chance | Independent (arXiv 2610.02267, n=13,923) | Jev better than Laya on 9/11 decision points |
- | 193.6x faster / 444.6x cheaper | Vendor workflow evals | ... |
+ | 193.6x faster / 444.6x cheaper | Vendor workflow evals | Self-reported; a secondhand test found 3.2-5x, not 193x (N-162, low confidence) |
```

## Still unverified (do not merge as fact)

- Rate-limit numbers (console login-gated).
- Whether output tokens are free in every channel (skills #12 open; one plugin charges $0.13/M).
- BAA availability; Trust Center contents; subprocessor names (third-party lists only).
- Free credits ("$5 per month" only in a cached Zapier blog) and signup status ("may be limited due to
  demand" / "paused in late September", both secondhand).
- AI/ML API price; Braintrust access route (docs vs blog).
- Exact jaggedness mode count and wording (Haiku extraction; C and D disagree).
- Zapier, Make, Mastra, LiteLLM, Vercel details: Haiku file only; re-read before merging.
- DSPy usage syntax (`dspy.LM("typesafe:...")`): files confirmed, call syntax not.
- OpenAI Decisions API latency: vendor claims only; no independent measurement in our evidence.
- Whether the fit-map's phishing "62.6% / 95%" source is the partner Trustle post (N-60).
