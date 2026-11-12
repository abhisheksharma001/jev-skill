# Skill Benchmark: jev, round 5

**Runner**: Cursor Agent CLI, model `composer-2.5`, both configurations (headless, `--force`, no TypeSafe key)
**Date**: runs and grading 2026-11-11/12
**Evals**: 1, 2, 3, 4 from `skills/jev/evals/evals.json` (3 runs each per configuration, 24 runs)
**Graders**: four Claude Sonnet agents, one per eval, blind (answers shuffled to letters A to F, seed 20261111)

**Not comparable with round 4.** Round 4 ran on Claude Sonnet; round 5 runs on Cursor `composer-2.5`
(the owner switched the runner; see "Attempts" below). The checks are the same 42.

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 89% ± 12% | 27% ± 9% | +0.63 |
| Time | 756.6s ± 95.3s | 848.4s ± 485.3s | -91.8s |
| Tokens | 1434760 ± 1096224 | 1405134 ± 1112967 | +29625 |

The ± is spread across the 12 task runs per side, not across the 3 round totals. Tokens include
Cursor's cache reads, which dominate the count.

Totals out of 42 per round: **with skill 39, 36, 39 (mean 38.0, sd 1.7)**; without skill 13, 11, 11
(mean 11.7, sd 1.2). The bar set before the run (S-10) was a with-skill mean of 40. **It was missed.**
Graded by separate agents; no grades were overridden.

**Regraded after publication (S-31):** with-skill totals 39, 36, **38**, **mean 37.7, sd 1.5** (n = 3
runs; sample sd, the same formula as the 1.7 above). The grades above are kept as first published.
Why: eval 4 (accuracy gap) with-skill run 3 passed check 1 (train-only misses), but its transcript shows
it hand-wrote an answer cache with made-up probabilities and reported the results as measured "frozen
jev-1.14.0 answer caches"; that one check is now a fail (-1 point; run 3 on eval 4 is 4 of 5, not 5).
No other grade was re-checked, and the counts in the tables below are as first published. The bar of 40
is still missed.

## Per eval

| Eval | With skill (runs 1, 2, 3) | Without skill (runs 1, 2, 3) |
|---|---|---|
| 1 brownfield support bot (14) | 14, 12, 12 | 5, 6, 5 |
| 2 PRD voice call QA (14) | 12, 12, 14 | 4, 2, 2 |
| 3 mixed fit triage (9) | 9, 9, 8 | 3, 2, 3 |
| 4 accuracy gap (5) | 4, 3, 5 | 1, 1, 1 |

## The three checks S-10 named

S-10's acceptance also asks that each named check pass in at least 2 of 3 with-skill runs.

| Check | With skill | Without skill |
|---|---|---|
| Eval 1 #9: Choice handles input that fits no option (companion Noul or explicit none/other) | 3 of 3 | 0 of 3 |
| Eval 2 #12: gates out voicemail/spam/wrong-number calls before flags | 3 of 3 | 0 of 3 |
| Eval 3 #8: lever named, accuracy reported with the share escalated, for (d) and (f) | 2 of 3 | 0 of 3 |

All three meet 2 of 3. The S-10 fixes did their job on the named checks; the shortfall against 40 is
spread over other checks: of 12 with-skill misses, 4 in eval 1, 4 in eval 2, 3 in eval 4, 1 in eval 3.

## How the runs were isolated

Each run got a fresh work dir and a fresh HOME under `/private/var/tmp/jev-r5`, with copies of only
the eval's input files (and, for with-skill, `skills/jev` minus `evals/`). Both were deleted after the
run. Without-skill runs went first. Cursor ran inside a macOS `sandbox-exec` profile
(`run_evals.py`, `sandbox_profile`) that blocks reads of the real HOME, `/private/tmp` and every
other run's dirs. Only `~/Library/Keychains`, `~/Library/Preferences`, Cursor's install and pyenv
stay readable. `audit.py` checks every transcript for:
- attempts outside the run;
- successful results that show outside paths (LEAK);
- for without-skill runs, tool results containing text found only in the skill (CONTENT);
- any touch of `evals.json`.

Final audit: 0 CONTENT, 0 `evals.json`, and no LEAK beyond:
- directory names in the shared base dir;
- files an agent wrote to `/tmp` itself.

## Known limits

- **Cursor's own sandbox is off.** It cannot nest inside `sandbox-exec`, so network was not blocked.
  Prompts said there was no network and no key.
- **The user temp dir stays readable.** That is `/private/var/folders`, because Cursor hangs at start
  without it (tested 2026-11-12). The audit is the guard there; a scan found no Jev content in it.
- **Some names can leak, never contents.** Cursor's index and the shared base dir can show file and
  directory names.
- **Account-level Cursor plugins load in both configurations.** These include a memory plugin's
  start-up hook. No run called an MCP memory tool.
- **No-skill runs spend time hunting.** Without-skill agents often search for Jev material before
  answering, which inflates their time and tokens.
- **Grading is blind only by letter.** With-skill answers often name the skill's scripts, so a grader
  could guess the configuration.
- **The data is small and synthetic.** Single model, 3 runs per cell, synthetic eval prompts. Direction
  only.

## Attempts that are not in these numbers (kept locally, ungraded)

1. Codex CLI, gpt-6.1-sol: 10 of 24 runs stopped on "Your workspace is out of credits"; one run read
   the repo README from a work dir inside the repo.
2. Cursor, gpt-5.6-sol-high: stopped at the Cursor Pro usage limit.
3. Cursor, composer-2.5, no sandbox: a without-skill run grepped the real HOME and read the repo's
   skill.
4. This run, before the sandbox was tightened: 4 without-skill runs (accuracy gap run 2, mixed fit
   triage runs 1-3) read files under `~/Library` and `~/.local/share`, including a copy of another
   Jev project. They were discarded and rerun under the tighter profile; the numbers above use the
   reruns.
