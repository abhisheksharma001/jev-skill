## Where a decision model is the best tool

Evidence as of 2026-11-11: 186 public records, sorted by who ran the test. Only independent results
are listed as wins below. Shapes and gotchas: `skills/jev/references/use-cases.md`; every source: `docs/research/2026-11-11/evidence.md`.

**Who should use one.** Anyone whose system already asks an LLM to return a label, a yes/no or a
rating, at volume. If the answer must be written, counted, or reasoned out step by step, keep the LLM.
If you have thousands of stable labelled examples, train a small classifier first.

**The best-evidenced uses** (independent tests; one number each):

| Use | Result | Source, n |
|---|---|---|
| Rerank search results | Recall@5 99.4%, same as Cohere Rerank 3.5, at 60.6% lower cost | erendikmenn, Turkish RAG, n=1,044 questions |
| Ticket and intent triage | 92.2% vs 93.6% for GPT-6 Luna and Haiku, about 35x cheaper per call | suraj, CLINC150, 3 x 300 tickets per load rate |
| Cascade in front of a bigger model | kept answers 76.7% -> 84.3% right, with 22.6% sent on | monumei, n=2,319 labelled GitHub issues |
| Judging other models' output | matched LLM judges in at least 21 of 27 comparisons, 16-357x cheaper | arXiv 2609.29769, 7 benchmarks |
| Skill routing from a list | 97.6% strict at 126 skills | keta1930, n=500 tasks |
| Gates inside a coding agent | 180/264 vs 155/264 tasks solved (+9.5 pts) | qybaihe/mu, Terminal-Bench 2.1, 88 tasks x 3 (author also sells a rival judge) |

**Where it loses:**
- **Prompt injection as the only defence.** 86.35% vs 89.01% for a small deberta classifier that runs in
  54 ms (Red Hat, 9 public datasets, n not given). At a 1% miss target any gate escalated over 91.8%
  of inputs (arXiv 2610.20907, n=47,611).
- **Zero-shot model routing.** "Neither model beats chance" (arXiv 2610.02267, n=13,923).
- **Trading.** -4.5R vs an LLM's -1.2R over 17 days on a live account (trAIde, 15 trades).
- **Numbers and broad taste questions.** Numeric medical items 35.9-39.4% (arXiv 2610.18529,
  n=8,742); "is this test useless?" AUC 0.54 (GC AI, one hackathon).

Its raw confidence runs high: answers scored 0.9-1.0 were right 84.3% of the time, not 98.9%
(monumei, n=1,794 answers). Calibrate before you trust a cut.

**Alternatives.** OpenAI's Decisions API (GA 2026-10-22) does the same job on gpt-6-luna at $0.10 per
million input tokens vs Jev's $0.042, with US/EU residency and HIPAA for eligible customers. We found no
independent head-to-head yet, so measure both on your own cases.
