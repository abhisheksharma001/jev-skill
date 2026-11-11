# Jev ecosystem, terms and pricing re-check

Run: 2026-11-11 (IST). Baseline: ~/jev-skill/skills/jev/references/facts.md (checked 2026-09-21).
Read-only. Wheels were downloaded to a scratch folder and listed, never installed.

Source labels: "live" = fetched 2026-11-11 with Keenable live:true, TinyFish, or a registry API (npm view, PyPI JSON, gh api). "cached" = Keenable search-index copy; the acquired date is given and the page may be older.

## 1. Table

| Item | Value as of 2026-11-11 | Changed vs facts.md? | Source URL + date read + live/cached | Confidence |
|---|---|---|---|---|
| Endpoint, auth, body shape | POST https://api.typesafe.ai/v1/systemone; GET /v1/models; Bearer auth; body {model, state, questions}; response {model, answers, usage} | No | https://docs.typesafe.ai/models.md (live 2026-11-11); https://docs.typesafe.ai/api/errors.md (live 2026-11-11) | High |
| Question primitives | noul, choice, score, plus NEW box (locates something in an image; needs Jev 1.14) | Yes: box added | https://docs.typesafe.ai/models.md (live 2026-11-11); https://docs.typesafe.ai/changelog.md (live 2026-11-11) | High |
| Confidence | Returned for choice and score. Box also returns confidence per OpenRouter docs. noul returns a probability only | Partly: box added | https://openrouter.ai/docs/guides/community/jev (cached, acquired 2026-11-09) | Medium |
| Error codes | 400 (includes max_tokens_exceeded), 401, 413 (body over 32 MiB), 415 (bad Content-Encoding), 422, 429, 529 | Yes: 400, 413, 415 added | https://docs.typesafe.ai/api/errors.md (live 2026-11-11) | High |
| Model IDs and aliases | jev-1.14.0 is current (released 2026-10-14). jev-1.13.0 still accepted. jev-latest and jev-preview both point to jev-1.14.0. Docs warn jev-preview currently equals jev-latest | Yes: aliases moved from 1.13.0 to 1.14.0 | https://docs.typesafe.ai/models.md (live 2026-11-11) | High |
| Input price | $42 per Btok = $0.042 per Mtok input. Output free | No | https://docs.typesafe.ai/models.md (live 2026-11-11); https://typesafe.ai/ (live 2026-11-11, "$42 Per Billion input tokens") | High |
| Rate limits | Set per organization. Docs name tokens/s and requests/s but print no numbers. Console page is login-gated (target_paywalled). The facts.md values (250,000 tokens/s, 1,200 req/min) cannot be re-verified | Yes: numbers no longer public | https://docs.typesafe.ai/models.md (live 2026-11-11); https://console.typesafe.ai/rate-limits (fetch 2026-11-11, paywalled) | Low for the numbers |
| Context | Default 64k tokens per request and 32k per question. Opt-in header TypeSafe-Danger-Zone-Long-Context: true raises both to 262k on 1.13 and 1.14 | Yes: long-context mode added | https://docs.typesafe.ai/models.md (live 2026-11-11) | High |
| Input modalities | Text (string, JSON object or array) plus PNG/JPEG images on 1.13 and 1.14, gated by header TypeSafe-Danger-Zone-Images: true. Audio and video "not natively accepted (yet)" | Yes: images added | https://docs.typesafe.ai/models.md and changelog.md (live 2026-11-11); SDK changelog for the header (live 2026-11-11) | High |
| Languages | 1.14 "Better multilingual support." Vendor claim, not measured | Yes: claim changed | https://docs.typesafe.ai/changelog.md (live 2026-11-11) | Medium |
| Latency | Not re-measured. OpenRouter reports P50 0.12 s for jev-1.14 (best provider). Not comparable to facts.md India probes | Not re-measured | https://openrouter.ai/typesafe/jev-1.14 (live 2026-11-11) | Medium |
| Version pinning | Keep jev-1.13.0 for tuned thresholds (repo invariant 6). Vendor advice unchanged: send the versioned ID once thresholds are tuned | No | https://docs.typesafe.ai/models.md (live 2026-11-11) | High |
| Failure modes ("jaggedness") | Now nine modes. New #8 "Choice option order": Jev "leans toward the option that comes first". "Generation" is now #9 | Yes | https://docs.typesafe.ai/model-jaggedness.md (live 2026-11-11) | High |
| parallel_questions cookbook | Index now says "12.2x cheaper and 11.8x faster" (facts.md says 10x faster). Cookbook body not re-fetched | Yes: minor | https://docs.typesafe.ai/llms.txt (live 2026-11-11) | Medium |
| skill_suggestion cookbook | "194" options in Hermes catalog (facts.md: 182) | Yes | https://docs.typesafe.ai/llms.txt (live 2026-11-11) | High |
| PyPI typesafe-sdk | 0.7.5, uploaded 2026-10-14. Requires Python >=3.10. Breaking change in 0.7.0 (2026-09-18): msgspec replaced by pydantic | Yes: 0.7.0 to 0.7.5 | https://pypi.org/pypi/typesafe-sdk/json (read 2026-11-11); https://docs.typesafe.ai/sdk/python/changelog.md (live 2026-11-11) | High |
| npm @typesafe-ai/sdk | 0.7.0, published 2026-10-14. Engines: node >=22 (facts.md said >=20). Breaking in 0.7.0: Node 22 required, request payload types no longer exported | Yes: 0.6.0 to 0.7.0; Node floor raised | npm view @typesafe-ai/sdk (read 2026-11-11); https://docs.typesafe.ai/sdk/javascript/changelog.md (live 2026-11-11) | High |
| PyPI langchain-typesafe | 0.0.2, uploaded 2026-11-05. 0.0.1 (non-alpha) on 2026-11-04. Requires Python >=3.10,<4 | Yes: was 0.0.1a3 alpha (2026-09-20) | https://pypi.org/pypi/langchain-typesafe/json (read 2026-11-11); wheel langchain_typesafe-0.0.2 listed 2026-11-11 | High |
| langchain-typesafe API | invoke() takes state and questions together (older versions set questions on the classifier). Experimental ModelRouterMiddleware and AutoModeMiddleware are present in the 0.0.2 wheel and need the [experimental] extra | Yes | Wheel listing (2026-11-11); https://docs.langchain.com/oss/python/integrations/providers/typesafe (cached, acquired 2026-10-16) | High (wheel), Medium (docs) |
| @langchain/typesafe (LangChain.js) | 0.0.2, modified 2026-10-01. Middleware at @langchain/typesafe/middleware | New | npm view @langchain/typesafe (read 2026-11-11); https://github.com/langchain-ai/langchainjs/tree/main/libs/providers/langchain-typesafe (cached, acquired 2026-10-21) | High |
| Official agent skill | typesafe-ai/skills, SKILL.md at skills/typesafe-ai/SKILL.md. Installable as a Claude Code plugin: `claude plugin marketplace add typesafe-ai/skills` | Yes: install path added | gh api repos/typesafe-ai/skills/readme (read 2026-11-11) | High |
| typesafe-ai GitHub org | 12 public repos. Jev-related: typesafe-sdk-python, typesafe-sdk-js, skills, n8n-nodes-typesafe-ai, system-one-adapter-python (drop-in TypeSafeClient replacement backed by LLM APIs), WorkflowEvals, typesafe-public-examples. No MCP repo | New | gh api orgs/typesafe-ai and orgs/typesafe-ai/repos (read 2026-11-11) | High |
| LiteLLM | Pass-through at /typesafe/v1/systemone. Unified /v1/systemone and /v1/decisions with a typesafe/ model in model_list. SDK litellm.systemone. Auto Router classifier jev. Day-0 Jev 1.14 support (2026-10-15). Stable 1.103.0 uploaded to PyPI 2026-09-27 | Expanded | https://docs.litellm.ai/docs/decisions (cached, acquired 2026-11-06); https://docs.litellm.ai/docs/pass_through/typesafe (cached, acquired 2026-10-16); https://docs.litellm.ai/blog/typesafe_jev_images (cached, acquired 2026-10-15); pypi litellm 1.103.0 (read 2026-11-11) | Medium |
| Braintrust | Two routes. (a) Your own TypeSafe key. (b) Built-in Jev: Settings > AI providers > "Enable Jev", free for scorers and classifiers, not through the AI gateway. The blog says access must be requested, which conflicts with the docs. SDK tracing: wrapTypeSafe() in JS, wrap_typesafe() in Python | Yes: built-in Jev and Python wrapper | https://braintrust.dev/docs/integrations/ai-providers/typesafe (cached, acquired 2026-10-21); https://braintrust.dev/blog/evaluate-agent-responses-with-jev (cached, acquired 2026-10-17) | Medium |
| Vercel AI Gateway | typesafe-ai/jev. Jev 1.14 added 2026-10-15. experimental_evaluate needs AI SDK >=7.0.105. Per-request ZDR and no-training via providerOptions.gateway.zeroDataRetention. HTTP POST https://ai-gateway.vercel.sh/v1/evaluate. Evaluation fallbacks (beta). Provider package @ai-sdk/typesafe-ai 3.0.38 | Yes: 1.14, HTTP endpoint, fallbacks, provider package | https://vercel.com/changelog/typesafe-ais-jev-1-14-is-now-available-on-ai-gateway (cached, acquired 2026-10-18); https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk (cached, acquired 2026-09-24); npm view @ai-sdk/typesafe-ai (read 2026-11-11) | High (existence), Medium (details) |
| OpenRouter | typesafe/jev-1.14: $0.042 per Mtok input, output $0, context shown as 262,144. typesafe/jev-1.13 still listed. ~typesafe/jev-latest tracks the newest release (docs). Live jev-latest page no longer names its target. Jev 1.14 not available through EU in-region routing. Beta label not seen on live pages | Yes | https://openrouter.ai/typesafe/jev-1.14 (live 2026-11-11); https://openrouter.ai/~typesafe/jev-latest (live 2026-11-11); https://openrouter.ai/docs/guides/community/jev (cached, acquired 2026-11-09). Old cached copy, acquired 2026-09-21, said jev-latest redirects to 1.13 | High |
| Cloudflare Workers AI | typesafe/jev still maps to Jev 1.13 (32k context, zero data retention "Yes", $0.042 per Mtok input). typesafe/jev-1.14.0 added: 32k context, image and box beta, "not recommended for production" | Yes: 1.14.0 added; alias still 1.13 | https://developers.cloudflare.com/ai/models/typesafe/jev/ (live 2026-11-11); https://developers.cloudflare.com/ai/models/typesafe/jev-1.14.0 (cached, acquired 2026-11-07) | High |
| AI/ML API | typesafe/jev is a floating ID that now resolves to Jev 1.14. Pins typesafe/jev-1.14 and typesafe/jev-1.13. Context window stated as 262,144 tokens, which differs from TypeSafe's 64k default. Price not stated on the page. The ~$0.0578/M figure in facts.md is not re-verified | Yes: alias moved; price unverified | https://docs.aimlapi.com/api-references/decision-models/typesafe/jev (live 2026-11-11, "last updated 1 day ago") | Medium (price Low) |
| Pydantic AI | TypeSafeModel is in released pydantic-ai-slim. Found in 2.50.0 (uploaded 2026-09-25) and 2.67.0 (latest, uploaded 2026-11-11). Files: pydantic_ai/models/typesafe.py, providers/typesafe.py, profiles/typesafe.py. Install: pip install "pydantic-ai-slim[typesafe]" | Yes: release status now verified | pypi pydantic-ai-slim JSON (read 2026-11-11); wheel listings for 2.50.0 and 2.67.0 (read 2026-11-11); https://pydantic.dev/docs/ai/models/typesafe (cached, acquired 2026-09-22 to 2026-10-29) | High |
| DSPy | Now shipped. dspy 3.5.0 (uploaded 2026-11-10) includes dspy/_vendor/lm15/providers/typesafe.py and dspy/adapters/decision.py. Use dspy.LM("typesafe:jev-latest"). dspy.experimental exposes Noul, Score, Choice. Tutorial added in commit 9c900c7 (2026-09-27). dspy.experimental.TypeSafe was removed (API break) | Yes: was "not found" | pip download of dspy 3.5.0 wheel (read 2026-11-11); gh api repos/stanfordnlp/dspy/commits/9c900c7 (read 2026-11-11); gh code search in stanfordnlp/dspy (read 2026-11-11) | High |
| Mastra | Classifier with evaluation models. Needs @mastra/core >=1.69.0 and @ai-sdk/typesafe-ai. Question types choice, score, boolean | New | https://mastra.ai/blog/introducing-classifiers-with-jev (cached, acquired 2026-10-14) | Medium |
| n8n, official | @typesafe-ai/n8n-nodes-typesafe-ai 0.10.0 on npm (modified 2026-10-20). package.json author "TypeSafe AI". Operations: Evaluate and Route. Credential key from console.typesafe.ai/keys. Repo pushed 2026-11-10 | New | npm view (read 2026-11-11); gh api repos/typesafe-ai/n8n-nodes-typesafe-ai/contents/package.json (read 2026-11-11); https://github.com/typesafe-ai/n8n-nodes-typesafe-ai (cached, acquired 2026-11-09) | High |
| n8n, community | npm n8n-nodes-typesafe 0.3.3 (2026-09-23), repo zampierid4p, MIT, unofficial. Also @n3ndor/n8n-nodes-typesafe-jev 0.4.1, unofficial, no runtime dependencies | Yes: 0.2.0 to 0.3.3; @n3ndor package is new | npm view (read 2026-11-11); https://npmjs.com/package/n8n-nodes-typesafe (cached, acquired 2026-10-16) | High |
| Zapier | Official app "TypeSafe Jev" (zapier.com/apps/typesafe-jev). Action ask_questions with content, yes/no, pick-one, scale, minimum confidence, and unsure handling. Also reachable via Zapier MCP and Zapier SDK. The Zapier blog of 2026-09-24 said no native integration existed; the live listing supersedes it | New | https://zapier.com/apps/typesafe-jev/integrations (live 2026-11-11); https://zapier.com/blog/jev (cached, acquired 2026-11-11) | High (listing), blog superseded |
| Make | Official TypeSafe app. Modules "Evaluate a state" and "Make an API call". Connection uses the TypeSafe API key. Community post (2026-09-29) says new account creation and Jev API key availability "may be limited due to demand" | New | https://apps.make.com/typesafe (live 2026-11-11); https://community.make.com/t/feature-spotlight-new-typesafe-app-and-jev-ai-model-in-make/116185 (cached, acquired 2026-11-10) | High |
| MCP servers | No official TypeSafe MCP server (no MCP repo in the typesafe-ai org). Community: typesafe-mcp 0.4.0 (npm, 2026-10-17), mcp-server-jev 0.1.0 (npm, 2026-09-24), jev-mcp 0.5.1 (npm, 2026-09-26), a .NET TypeSafe.Mcp (blog, 2026-10-10) | Unchanged on "no official"; community list grew | npm view for each (read 2026-11-11); gh org repos (read 2026-11-11) | High |
| Google Sheets | Official Airbnb demo: copyable sheet with Apps Script custom function JEV_TOP10 (not a Marketplace add-on). Key in Script properties. Shortlist via Choice over 100 IDs per group, then a Score over the shortlist; about 1 s. Third-party add-ons: "Jev for Sheets" by JevMade (independent Marketplace add-on, bring-your-own key) and an OSS jev-sheets project | Yes: clarified | https://docs.typesafe.ai/demos/airbnb-listing-search.md (live 2026-11-11); https://jevmade.com/e/jev-sheets (cached, acquired 2026-10-09) | High |
| Other integrations (new) | TrueFoundry AI Gateway native TypeSafe integration and custom endpoint (cached, acquired 2026-10-20). Maia Foundation connector and shared pipelines (cached, acquired 2026-10-10 to 10-20). Cloudflare, AI/ML API, OpenRouter and Vercel are listed above | New | https://truefoundry.com/docs/ai-gateway/jev (cached, acquired 2026-10-20); https://maia.ai/resources/blog/building-typesafe-jev-connector-shared-pipelines-maia (cached, acquired 2026-10-10) | Medium |
| Third-party wrapper sites | jevtypesafeai.com, jev-typesafe.org, jev-ai.org, jevaiguide.com. Not TypeSafe-operated per the evidence. jevtypesafeai.com claims "jv_live_" keys and "no waitlist", neither of which appears in TypeSafe's own docs. Do not cite these as facts | Not a source | Cached index copies (acquired 2026-10-07 to 2026-11-10) | Low |
| Free tier / credits | TypeSafe home page (live 2026-11-11) states no free-credit information. Zapier blog (cached, acquired 2026-11-11) says "$5 worth of free credits every month". Unverified, secondhand | Unknown | https://typesafe.ai/ (live 2026-11-11); https://zapier.com/blog/jev (cached, acquired 2026-11-11) | Low |
| Enterprise plan | Page says "Talk to us about higher limits, data requirements, or getting started." Enterprise gets ZDR and a SOC 2 report on request. Enterprise price and BAA answers are not visible in the extracted text | New | https://typesafe.ai/enterprise (live 2026-11-11). Rate-limit increase form: https://docs.typesafe.ai/models.md (live 2026-11-11) | High (quote), Medium (scope) |
| Signup status | No primary statement found. Make community post (cached, acquired 2026-11-10) says account creation and key availability "may be limited due to demand". A cached blog (acquired 2026-10-06) says direct API signups were paused in late September | Unverified | As listed above | Low |

## 2. Data and legal (exact quotes, as of 2026-11-11)

Documents read live on 2026-11-11: Privacy Policy (https://typesafe.ai/legal/privacy-policy, document dated 2025-11-19); Master Customer Agreement (MCA) (https://typesafe.ai/legal/mca, published 2026-09-23); Data Processing Addendum (DPA) (https://typesafe.ai/legal/data-processing, published 2026-04-24); Legal index (https://docs.typesafe.ai/legal.md); Models page (https://docs.typesafe.ai/models.md); Enterprise page (https://typesafe.ai/enterprise).

### 2a. Training on customer data

- Privacy Policy: "We (1) will not train or fine tune any artificial intelligence or machine learning models on Input, and (2) will not disclose any Input to a third party other than our service providers."
- MCA section 4.1 (consent exception): "The foregoing license does not grant TypeSafe the right to, and TypeSafe will not, include Customer Data in a dataset used to train (i.e., to modify the model weights of) any artificial intelligence or machine learning models without Customer’s prior consent."
- Enterprise FAQ: "Do you train on our inputs or outputs?" Answer: "No. We don’t use your inputs or outputs to train our models."
- Models page: "Jev is not trained on customer requests or responses." and "Jev is not fine-tuned or LoRA-adapted with customer data."

Conflict to note: the Privacy Policy and the Enterprise FAQ are absolute. The MCA allows training on Customer Data with prior consent. The MCA is the contract. Ask TypeSafe to confirm in writing that no consent has been given and none is requested.

### 2b. Telemetry and derived data (new, not in facts.md)

- MCA section 4.1(c): the license covers "in perpetuity, any Customer Data (i) to derive and generate Telemetry, (ii) to monitor for fraud and abuse of the Services, and (iii) as necessary to comply with applicable Laws."
- MCA section 4.3: "“Telemetry” means information generated in connection with the Services, such as technical logs, hashes, summary statistics and classifications, metrics, and learnings related to Customer’s use of the Services. TypeSafe may Process Telemetry without restriction, including to improve the Services or TypeSafe’s other products and services."
- Privacy Policy, purposes list: "To generate anonymized or aggregated data that we may use for lawful purposes;"

Note: "learnings related to Customer's use" is broad. Under the MCA, derived data is not limited to the Customer Data itself.

### 2c. Retention

- No retention period in days was found in any document read.
- DPA Schedule I, section 8: "Customer Personal Data will be retained for as long as necessary taking into account the purpose of the Processing, and in compliance with applicable laws, including laws on the statute of limitations and Data Protection Law."
- Privacy Policy: "We retain personal data about you for as long as reasonably necessary to provide you with the Services, or otherwise in support of our business or commercial purposes."
- MCA section 10.3: "For avoidance of doubt, both during the Term, and following the date of expiration or earlier termination of the Agreement, TypeSafe will be under no obligation to store or retain Customer Data and may delete Customer Data at any time in its sole discretion."

### 2d. Zero data retention (ZDR)

- Legal index: "We also offer zero data retention (ZDR) for enterprise customers. To learn more, fill out the support request form."
- Enterprise page: "Zero data retention is available for enterprise customers. Ask about the setup for your account."
- Route-level ZDR exists elsewhere. Vercel AI Gateway: per request via providerOptions.gateway.zeroDataRetention (Vercel changelog and KB, cached 2026-09-22 to 2026-10-18). Cloudflare Workers AI jev model page lists "Zero data retention: Yes" (live 2026-11-11). These are separate from a direct TypeSafe contract.

### 2e. Hosting, subprocessors, security

- Privacy Policy: "The Services are hosted in the United States (“U.S.”)."
- DPA section 3.1: subprocessors are "described in https://trust.typesafe.ai/subprocessors". That page could not be read on 2026-11-11. TinyFish returned "Something went wrong ... Error Id: 4zSKKhS3K-et8izv0wlpU". Keenable returned content_not_extracted. The Trust Center root (https://trust.typesafe.ai/) failed the same way.
- MCA section 16.10: "TypeSafe may use subcontractors and permit them to exercise TypeSafe’s rights, but TypeSafe remains responsible for their compliance with this Agreement and for its overall performance under this Agreement."
- DPA section 5.2: "Typesafe will notify Customer without undue delay and in any case within 72 hours after becoming aware of any accidental or unauthorized access to, or disclosure or use of, Customer Personal Data".
- DPA section 5.3: audit "no more than once every 12 months".
- DPA sections 6.2 and 6.3: EU SCCs Module 2 and the UK Addendum.
- Enterprise page: "Visit our Trust Center to request access to the SOC 2 Type II report." This is the vendor's claim. The report was not reviewed.
- ISO 27001: not found. The firmbees article (cached, acquired 2026-11-01) says "Not publicly specified".
- HIPAA BAA: the FAQ answer to "Will you sign a BAA?" is not visible in the extracted page text. Third-party sources (VTI, cached 2026-10-19; net-kings, cached 2026-10-20) say no BAA was found. Treat as unverified.

### 2f. Contract terms (MCA, live 2026-11-11)

- Governing law, section 16.2: "governed by the laws of the State of California and the United States" with venue in San Francisco.
- Liability cap, section 12.2: the greater of fees paid in the prior 12 months or $50 USD.
- Distillation ban, section 2.3(b): no use "to perform model distillation, train a model to imitate the output of the Services, or develop (or to facilitate the development of) a similar or competing product or service".
- API changes, section 2.5: TypeSafe "may from time to time update the Services" and "may result in the API’s becoming incompatible with a Customer Application". Notice is by "commercially reasonable efforts".
- Credits, section 8.2(a): Purchased Credits expire on the earlier of end of Term or 12 months after purchase. The credit consumption rate "may vary based on account settings, including the model used".
- Link inconsistency: MCA section 4.4 links the DPA at https://typesafe.ai/data-processing. The live DPA is at https://typesafe.ai/legal/data-processing.
- The early Terms copy with "solely for the purpose of evaluating" (facts.md) was not found in the current MCA sections read (1 to 14.4, 16.2, 16.10). Sections 15 and 16 were read only through extraction. It appears superseded by the 2026-09-23 MCA.

## 3. New things not in facts.md (as of 2026-11-11)

- Jev 1.14.0, released 2026-10-14. Adds the box primitive, images on input, multilingual claim, and the long-context header. Source: https://docs.typesafe.ai/changelog.md (live 2026-11-11).
- Long-context mode: header TypeSafe-Danger-Zone-Long-Context: true raises both limits to 262k tokens. Works on 1.13 and 1.14. Source: https://docs.typesafe.ai/models.md (live 2026-11-11).
- Image gate: header TypeSafe-Danger-Zone-Images: true. Source: https://docs.typesafe.ai/sdk/javascript/changelog.md (live 2026-11-11).
- Enterprise page with ZDR, SOC 2 report request, and "Talk to us about higher limits, data requirements". Source: https://typesafe.ai/enterprise (live 2026-11-11).
- DPA is readable at https://typesafe.ai/legal/data-processing (published 2026-04-24). facts.md said it did not render.
- MCA published 2026-09-23 at https://typesafe.ai/legal/mca. It replaces the early terms copy.
- Official TypeSafe n8n node, @typesafe-ai/n8n-nodes-typesafe-ai 0.10.0 on npm. Source: npm view (read 2026-11-11).
- Official Zapier app (ask_questions action). Source: https://zapier.com/apps/typesafe-jev/integrations (live 2026-11-11).
- Official Make app (Evaluate a state, Make an API call). Source: https://apps.make.com/typesafe (live 2026-11-11).
- DSPy 3.5.0 ships a TypeSafe provider and a decision adapter. Source: wheel listing (read 2026-11-11).
- Pydantic AI TypeSafeModel is in released pydantic-ai-slim (2.50.0 and later). Source: wheel listings (read 2026-11-11).
- LangChain: langchain-typesafe 0.0.2 (non-alpha) and @langchain/typesafe 0.0.2 on npm. Experimental middleware (ModelRouterMiddleware, AutoModeMiddleware). Sources: PyPI JSON and npm view (read 2026-11-11).
- Mastra classifier support with evaluation models (cached, acquired 2026-10-14).
- Vercel: HTTP evaluate endpoint, evaluation fallbacks (beta), provider package @ai-sdk/typesafe-ai 3.0.38, Jev 1.14 on the gateway (2026-10-15). Sources: Vercel changelog (cached, acquired 2026-10-18); npm view (read 2026-11-11).
- Braintrust: built-in Jev for scorers, and Python wrap_typesafe(). Source: Braintrust docs (cached, acquired 2026-10-21).
- Cloudflare typesafe/jev-1.14.0 (beta image and box). Source: Cloudflare docs (cached, acquired 2026-11-07).
- AI/ML API typesafe/jev floating alias, with 262,144-token context stated. Source: https://docs.aimlapi.com (live 2026-11-11).
- Community MCP servers: typesafe-mcp, mcp-server-jev, jev-mcp (npm), plus a .NET TypeSafe.Mcp. No official MCP server. Sources: npm view (read 2026-11-11).
- Community Google Sheets add-ons: Jev for Sheets by JevMade, jev-sheets OSS. Official demo uses an Apps Script function JEV_TOP10. Source: https://docs.typesafe.ai/demos/airbnb-listing-search.md (live 2026-11-11).
- Jaggedness page: new failure mode #8 "Choice option order". Source: https://docs.typesafe.ai/model-jaggedness.md (live 2026-11-11).
- Official agent skill installable as a Claude Code plugin (typesafe-ai/skills). Source: gh api (read 2026-11-11).
- typesafe-ai GitHub org repos: system-one-adapter-python (drop-in TypeSafeClient replacement backed by LLM APIs). Source: gh api (read 2026-11-11).
- TrueFoundry AI Gateway and Maia Foundation integrations (cached, acquired 2026-10-10 to 10-20).

## 4. Could not verify (as of 2026-11-11)

- Rate-limit numbers (250,000 tokens/s, 1,200 req/min). Console is login-gated. Docs no longer print numbers.
- Trust Center and subprocessor list. Both pages error. Subprocessor names (Modal, AWS, Nebius, CoreWeave, Slack, Google Workspace) come only from third-party sites.
- BAA. The enterprise FAQ answer is not extracted. Third parties say no BAA.
- SOC 2 report contents. Vendor says available on request. Not reviewed.
- ISO 27001: not found.
- Free credits: "$5 worth of free credits every month" appears only in a Zapier blog (cached). TypeSafe's home page does not state it.
- Signup status: conflicting secondhand reports (Make community: "may be limited due to demand"; cached blog: direct API signups paused). No primary statement found.
- AI/ML API price: not on the page. The $0.0578/M figure from facts.md is not re-verified.
- OpenRouter "beta" label: not seen on live pages.
- Cloudflare alias: typesafe/jev still maps to 1.13 on the live page, while TypeSafe's alias now points to 1.14. Treat as a mismatch to watch.
- Braintrust access route: docs say "Enable Jev" in settings, blog says access must be requested. Unresolved.
- Latency: not re-measured. Facts.md India probes stand as historical data only.
- Cookbook bodies (other than the index descriptions) were not re-fetched.
- Third-party wrapper sites were not evaluated beyond noting them. Do not cite as facts.
