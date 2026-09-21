---
name: jev
description: Decide where TypeSafe AI's Jev decision model (System One; typed yes/no, pick-one and rating answers with probabilities, no text generation) fits in a system, then design, integrate, calibrate and ship it. Use whenever the user mentions Jev, TypeSafe, System One, decision models, or wants to cut the cost, latency or inconsistency of LLM calls that only classify, route, gate, triage, moderate, rerank, score or judge (LLM-as-judge, evals, guardrails, intent routing, call QA, log or ticket triage), whether adding it to an existing codebase, mid-project, building from scratch, wiring it into n8n-style workflows, or writing a PRD for it. Also use for "should this be an LLM call at all?" questions. Complements TypeSafe's official skill, which covers API usage but not fit assessment, calibration, brownfield rollout or PRDs.
license: MIT
compatibility: Scripts need Python 3.9+ (standard library only). Live calls need TYPESAFE_API_KEY and network access to api.typesafe.ai. Everything except live calls works offline.
metadata:
  facts_checked: "2026-09-21"
  benchmark: "docs/benchmarks/system/results.md"
  pinned_model: "jev-1.13.0"
---

# jev

Jev answers typed questions about text and returns a probability with each answer. It is roughly
100x cheaper than a frontier LLM call and its answers barely vary between runs, but it cannot write,
reason in steps, count, or compare dates, and it can be confidently wrong.

So the work is not "call the API". The work has four parts:
1. Find the decisions in a system.
2. Check that each one suits Jev.
3. Word the questions literally.
4. Set thresholds on real labelled cases, with a fallback for the uncertain middle.

This skill exists to make those four things routine.

Evidence base: a research-council run on 2026-09-21. It used 190+ sourced records, mostly from
independent adopters, plus about 250 live probe calls. See `references/fit-map.md` for the sourced map.
Jev launched 2026-09-15, so everything is early: prefer measuring on the user's own cases over
quoting anyone's numbers, including the ones in this skill.

## Pick the job

| The user wants | Do this | Read |
|---|---|---|
| "Would Jev help here?" / "where should we use it?" | Fit assessment (below) | `references/fit-map.md` |
| Add Jev to an existing codebase | Recipe A: scan, fit-check, seam, offline measure, shadow, cascade | `references/integration.md` |
| Add a decision to a project in flight | Recipe B: list decisions, questions before code, synthetic cases, fallback in the first PR | `references/integration.md` |
| Build something new around Jev | Recipe C: pipeline of decisions and generations, judge everything cheap, thresholds as config | `references/integration.md` |
| Write or fix questions | One judgement per question, literal wording, criteria on both sides | `references/question-design.md` |
| "What threshold?" / false alarms | Calibrate on labelled cases with a held-out split | `references/calibration.md` |
| Accuracy is poor / "make it as good as a frontier model" / "multi-Jev" | Three levers: rewrite the question from its misses, multi-Jev with fitted weights, cascade on the unsure share | `references/optimization.md` |
| A PRD or spec for a Jev integration | Fill the template from fit verdict and calibration plan | `assets/prd-template.md` |
| Price, limits, versions, SDKs, gateways, data terms | Snapshot, then re-check if older than ~30 days | `references/facts.md` |
| Raw API/SDK syntax beyond the examples here | Live docs: `https://docs.typesafe.ai/llms.txt` (any docs page + `.md`) | n/a |

If TypeSafe's official skill (`typesafe-ai/skills`) is installed, let it handle API syntax and its
pattern catalogue. This skill decides *whether and where*, then *how to prove it works*.

## Fit assessment (always first)

Skipping this is how teams end up with a Jev call that loses to a two-line rule. Separate every
candidate into one of three owners. Try them in this order, because each is cheaper than the next:

1. **Code**: anything a rule, regex, lookup or arithmetic can decide exactly.
2. **Jev**: a judgement about text with a closed answer set (yes/no, 1 of up to 255 options, or 2-10
   levels).
3. **LLM or human**: writing, multi-step reasoning, comparing complex outputs, irreversible calls.

Then run the deterministic check. It asks 13 true/false questions about the task and prints a
verdict, the reasons, and the patterns to use:

```bash
python3 scripts/fit_check.py --template > answers.json   # fill with true/false from what is known
python3 scripts/fit_check.py --answers answers.json      # exit 0 GO, 4 GO WITH GUARDS, 3 NO-GO
```

Answer from facts about the task, and ask the user when you don't know (data sensitivity, labelled
data and the latency budget are the usual unknowns). Then place the task in `references/fit-map.md`
and tell the user the verdict **and how strong the evidence is**. Many placements are UNKNOWN
(proposals only). For those, the honest answer is "run a shadow experiment", not yes or no.

A GOOD or HYBRID verdict is a claim that still has to be proved on the user's data, so never end
one at "good fit". Close each with two lines:
- **Prove it:** calibrate on labelled cases and report the held-out split (`references/calibration.md`).
- **If accuracy is short:** name the lever to pull first (rewrite the question from its train misses,
  multi-Jev, or a cascade on the unsure share; `references/optimization.md`), and say that any
  cascade number is reported together with the share escalated.

Where Jev pays off most: an LLM already making a decision, at high volume, with several independent
questions about the same input, where consistency or a usable probability matters and mistakes are
reversible. The strongest shape is a **pre-filter or cascade in front of an expensive model**.

## You are the expensive part; spend yourself at design time

The agent running this skill is a frontier model. Jev is not, and cannot be fine-tuned. The way to
get frontier-level results at Jev prices is to put your own reading and judgement into the *question
text, the criteria and the composition*, where it is paid for once, and to keep yourself out of the
per-item loop except for the unsure share.

On this repo's benchmark a first-draft question scored 84.1% (voice calls) and 76.1% (Banking77).
A rewrite made after reading the train misses scored 100% and 83.6%, at the same run-time cost. A
cascade on the 13% least certain Banking77 messages reached 89.6% against 91.8% for the frontier
model alone. These are small held-out sets, a single run, and the voice set is synthetic.

So when accuracy matters:
1. Get a first result.
2. Run `optimize_questions.py misses`.
3. Read the failures like a reviewer.
4. Rewrite.
5. Let `compare` referee.

Then try `ensemble.py`, then a cascade. `references/optimization.md` has the method and what did
not work (paraphrase voting added nothing).

## Non-negotiables (each one traces to a measured failure)

1. **One judgement per question; combine in code.**
   - A single "is this phishing?" question scored 62-89% in two independent tests.
   - Five atomic questions weighted in code scored 95%.
2. **Never ship 0.5 by default.**
   - Answers jitter about ±0.02 between runs.
   - Thresholds come from `scripts/calibrate.py` on the user's cases, and they are reported on the
     held-out split.
3. **Confidence is not correctness.**
   - Route the middle band to a fallback.
   - Audit a sample of the confident answers.
4. **Numbers, counting and dates live in code.**
   - Compute them, pass the result into `state`, and ask Jev only the semantic remainder.
5. **Pin `jev-1.13.0`, log `response.model`, and recalibrate when it changes.**
   - The SDK default is `jev-latest`, which moves.
6. **Fallback from day one.**
   - Single closed vendor, limits "can change without notice".
   - The seam in `references/integration.md` makes the fallback cheap.
7. **Shadow before gating.**
   - No automated action on Jev's answer until calibrated numbers exist.
8. **Nothing sensitive leaves without clearance.**
   - US-hosted third party; zero data retention is enterprise-only.
   - Use synthetic or redacted cases until a named person has read the current terms.
   - This applies in shadow mode too.
9. **Never ask Jev to write, explain, or judge itself.**

## Bundled scripts

All are Python standard library only and have `--help`. Treat them as black boxes unless a change is
needed.

| Script | Purpose |
|---|---|
| `scripts/fit_check.py` | Go / no-go verdict with reasons and patterns. No model call, so it is repeatable. |
| `scripts/find_decision_calls.py <repo>` | Brownfield scan. Ranks LLM call sites whose output is a label/bool/rating, marks mixed decision+generation sites, and flags nearby numbers/dates. It is a ranking to review, not a verdict. |
| `scripts/jev_client.py` | Dependency-free client and CLI (`models`, `ask --state f --questions q.json`). Validates questions and reports latency and cost. Use the official SDKs inside real apps. |
| `scripts/calibrate.py` | Labelled cases in; cost-weighted thresholds, three-way bands, and train/eval TPR/TNR out. Caches answers so re-scoring is free. Warns when n is too small. |
| `scripts/optimize_questions.py` | `misses` writes a packet of TRAIN-only failures for you to read and rewrite from; `compare` accepts a rewrite only if train loss drops beyond noise, and prints eval for both. It never calls an LLM: you are the rewriter. |
| `scripts/ensemble.py` | Multi-Jev. Several questions in one call vote on one label; weights are fitted on train (logistic, stdlib). For Choice members it prints accuracy by top-2 margin, which sets the cascade cut. |

The key is read from `TYPESAFE_API_KEY`.
- Never write it to a file in the repo.
- Never echo it.
- Never put it in a workflow export.
- If the user pastes a key into chat, use it via the environment only and remind them to rotate it.

## Quick start (first live call)

```bash
export TYPESAFE_API_KEY=...        # user supplies; do not store
cat > q.json <<'JSON'
{"billing": {"type": "noul", "instructions": "The message is about a billing problem.",
             "criteria": {"true": "Charges, refunds, invoices, failed payments.", "false": "Anything else."}},
 "tone":    {"type": "choice", "instructions": "Tone of the customer's message.",
             "criteria": {"angry": "hostile", "calm": "neutral or polite", "other": "none of these"}},
 "urgency": {"type": "score", "instructions": "How soon does this need a human?",
             "criteria": ["can wait", "needs attention this week", "needs attention today"]}}
JSON
echo "I was charged twice for May. Please refund one." > state.txt
python3 scripts/jev_client.py ask --state state.txt --questions q.json
```
Three answers cost one call of about 390 input tokens (about $0.000016). All independent questions
about one state go in one call, because state is billed once and question count does not move latency.

## Working style

- **Explain the verdict in the user's terms.** Say which decisions go to code, which to Jev, and which
  stay on the LLM, and what each choice saves or risks. Many users come from workflow tools: a Jev
  call is a Switch node that returns a probability instead of a branch.
- **Show evidence strength with every claim** ("independent, n=50", "partner, n=5", "proposal only").
  Do not repeat vendor multipliers (200x / 400x) as facts.
- **Make small labelled sets early.**
  - 30-50 synthetic cases with hard negatives catch most wording problems for well under a cent.
  - Say clearly that synthetic results are direction only.
- **When a result looks bad, fix in this order:**
  1. Label quality.
  2. Question wording and criteria.
  3. State filtering.
  4. Threshold.
  5. Only then "Jev can't do this".
- **When a result looks perfect, be suspicious.**
  - Easy negatives prove nothing, so add near-misses.
- **In a brownfield repo, read the incumbent call's output parsing.**
  - Fragile parsing is often a bigger bug than the model choice.
  - Examples: exact-match on `"true"`, a default of "no" on a garbled reply, an enum parse that throws.
  - Report these even though nobody asked.
- **Keep deliverables short.**
  - A PRD or plan the reader finishes beats a complete one they skim.
  - Budget: 250 lines for a PRD. Count before handing over (`wc -l`), and cut until it fits.
  - Cut any section that restates another.
- **Estimate instead of declining.**
  - When asked what it will cost or save, give a number with the assumptions written next to it
    (calls per day x tokens per call x $0.042 per 1M input tokens, with the check date).
  - Missing inputs become stated assumptions plus "send me X to tighten this", not a refusal. A
    reader can correct a wrong assumption; they cannot act on "it depends".
- **Decide defaults; do not park them as open questions.**
  - For a rule the user did not specify (business hours, rate limits, retention), write a sensible
    default into the design and list only "confirm the default" as the open item.
- **Report honestly.** Give eval-split numbers with n, say whether data is synthetic or real, say
  what was not tested, and compare with the incumbent on the same cases.
