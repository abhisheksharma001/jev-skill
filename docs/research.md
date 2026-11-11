# Research flags

### R-1 — Can skill-side techniques bring a Jev system within 3 points of Fable at under 10% of its cost?

**Where:** S-4 · docs/benchmarks · decision: README headline claim
**Find out:** held-out accuracy and cost of four setups on the same cases: Jev single question, multi-Jev (S-3), multi-Jev + Fable on the middle band, Fable alone. If the gap stays above 3 points, the README says so and the skill recommends the cascade only.
**Confidence:** medium — independent reports show 62-89% to 95% from decomposition alone (phishing), but not on our data.
**Review:** none.
**Status:** answered 2026-09-21.
**Answer:** Voice (synthetic, n=44): met, 100% with 0% escalated vs Fable 100%. Banking77 (public, n=134): 89.6% at 13% escalated vs Fable 91.8%: within 3 points, escalation share 3 points over the 10% bar; parity at 32%. Largest gain on both came from design-time rewriting (84.1 to 100, 76.1 to 83.6). Paraphrase voting added nothing. Source: docs/benchmarks/system/results.md, bench/score_system.py. Confidence now medium: single run, small n.

### R-2 — Which public labelled dataset is licence-clean and hard enough for the headline benchmark?

**Where:** S-4 · scripts/bench · dataset choice
**Find out:** name, licence, size, and whether a single-question Jev baseline leaves headroom (below ~92%).
**Confidence:** high — licence file read at source, headroom measured.
**Review:** none (running model is Fable, the strongest available).
**Status:** answered 2026-09-21.
**Answer:** BANKING77 (PolyAI), CC-BY-4.0 per https://github.com/PolyAI-LDN/task-specific-datasets/blob/master/LICENSE (read 2026-09-21) and the Hugging Face card. 3,084 test rows, 77 intents. Names-only Jev baseline 76.1% on a seeded 400-row sample, so headroom exists. Known label noise caps all setups.

### R-3 — Does the benchmark hold on real (non-synthetic) voice transcripts and with a reproducible frontier baseline?

**Where:** docs/benchmarks/system/results.md · voice table · README headline
**Find out:** same four setups on redacted real calls with human labels, and a Fable baseline run from an API key so others can re-run it. Decides whether the "met" verdict on voice survives.
**Confidence:** low — the voice set is synthetic, n=44, and label definitions were shared with the question author.
**Review:** higher model — running model (Fable 5.1) is already the strongest available; Abhishek decides.
**Status:** open.
**Answer:**

### R-4 — Does the router hold at 94 skills on real prompts?

**Where:** S-18.
**Find out:** wrong-hint and missed-hint rates on 30-50 labelled shadow-log lines, held-out split.
**Confidence:** low (n=8; independent 84-skill bench 53.6% top-1).
**Review:** none.
**Status:** open (raised 2026-11-11).
**Answer:**

### R-5 — Does DSPy 3.5.0 ship a TypeSafe adapter?

**Where:** facts.md.
**Find out:** Does DSPy 3.5.0 ship a TypeSafe adapter?
**Confidence:** low (version seen, adapter not read).
**Review:** none.
**Status:** open (raised 2026-11-11).
**Answer:**

### R-6 — Are output tokens really free?

**Where:** facts.md price row; typesafe-ai/skills issue #12 open.
**Find out:** Are output tokens really free?
**Confidence:** medium.
**Review:** none.
**Status:** open (raised 2026-11-11).
**Answer:**

### R-7 — Jev vs OpenAI Decisions API (gpt-6-luna, $0.10/M) on Banking77 + voice set.

**Where:** S-17 alternatives table, README.
**Find out:** Jev vs OpenAI Decisions API (gpt-6-luna, $0.10/M) on Banking77 + voice set.
**Confidence:** none measured.
**Review:** none.
**Status:** open (raised 2026-11-11).
**Answer:**

### R-8 — Does TypeSafe confirm in writing that no MCA 4.1 training consent is given or requested? Owner question to TypeSafe. Confidence: medium (privacy policy and FAQ say no training; contract allows it with consent).

**Where:** 
**Find out:** Does TypeSafe confirm in writing that no MCA 4.1 training consent is given or requested? Owner question to TypeSafe. Confidence: medium (privacy policy and FAQ say no training; contract allows it with consent).
**Confidence:** 
**Review:** none.
**Status:** open (raised 2026-11-11).
**Answer:**
