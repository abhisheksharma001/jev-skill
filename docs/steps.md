# Step register

**Goal (frozen 2026-09-21):** an open-source skill that tells an agent where Jev fits, and makes a Jev-based *system* score within 3 accuracy points of Fable-alone on the same labelled cases at under 10% of Fable's cost, with Jev-only numbers reported beside it.
**For whom:** builders adding Jev to an existing or new system (Ellavox first).
**Not doing:** changing Jev itself; any client data; a hosted service.
**Money ceiling:** TypeSafe spend under $1 per step; Fable baseline runs through Claude Code subagents, not a paid API key.

### S-1 — First commit, tests, CI, benchmark screenshot, public push
**PR:** none possible (empty repo): direct first commit on main. **Depends on:** nothing. **Research:** none.
**Files:** everything under `skills/jev/`, `tests/`, `docs/`, `.claude/CLAUDE.md`, `.github/workflows/test.yml`, `README.md`.
**Today:** local folder, zero commits, no remote.
**Change:** add unit tests for the four scripts, move the support-bot fixture to `tests/fixtures/`, publish iteration-1 benchmark table and viewer screenshot in README, create public GitHub repo, push.
**Acceptance:** WHEN a stranger opens github.com/abhisheksharma001/jev-skill THEN the README SHALL show the iteration-1 benchmark table and screenshot, and CI SHALL be green.
**Verify:** `python3 -m unittest discover -s tests -v` passes; `gh run list -L1` shows success; `git grep -n apikey_` prints nothing.
**Must not:** commit `AGI_Research/`, `skills/jev-workspace/`, any `.env`, any key.
**Status:** done locally 2026-09-21 (commit 6e8fbae). Public push blocked by the session's permission classifier; Abhishek runs the push command. Learned: aggregate_benchmark.py needs run-1/ folders; headless Chrome plus an injected switchView() call captures the Benchmark tab.

### S-2 — optimize_questions.py: a strong model rewrites questions from Jev's misses
**Depends on:** S-1. **Research:** none.
**Files:** `skills/jev/scripts/optimize_questions.py`, `skills/jev/references/optimization.md`, `tests/test_optimize.py`.
**Change:** loop = calibrate on train, export the misses as a packet for the agent (Fable) to rewrite questions, accept a rewrite only if train score improves and re-report on eval. Script never calls an LLM itself: the agent is the rewriter.
**Acceptance:** WHEN given cases, questions and a candidate rewrite THEN the script SHALL accept it only if cost-weighted train loss drops, and SHALL print eval numbers for both.
**Must not:** tune on the eval split.
**Status:** done 2026-09-21 (b26db88). Proved by breaking: removing the train-only filter fails exactly test_packet_never_contains_eval_cases. Learned on real data: one rewrite from train misses took the voice question from 7 held-out errors to 0.

### S-3 — ensemble.py: multi-Jev voting with fitted weights
**Depends on:** S-1. **Files:** `skills/jev/scripts/ensemble.py`, `tests/test_ensemble.py`, `skills/jev/references/optimization.md`.
**Change:** several phrasings and checker questions per judgement in ONE call; combine by logistic weights fitted on train (stdlib gradient descent); report eval.
**Acceptance:** WHEN members disagree THEN the combined probability SHALL come from fitted weights, and eval accuracy SHALL be reported next to the best single member.
**Status:** done 2026-09-21 (e11beaa). Proved by breaking: removing the mixed-type guard fails exactly one test. Learned: decomposition helps (84.1 to 97.7 on voice); paraphrase voting does not (Banking77 flat at 83.6).

### S-4 — bench: four setups on public + synthetic data, README headline
**Depends on:** S-2, S-3. **Research:** R-1, R-2.
**Files:** `bench/`, `docs/benchmarks/system/`, `README.md`.
**Acceptance:** WHEN the bench finishes THEN `docs/benchmarks/system/results.md` SHALL list accuracy, cost per 1k and n for all four setups on held-out cases.
**Must not:** exceed $1 TypeSafe spend; send non-public data.
**Status:** done 2026-09-21 (ea1822b). Spend about $0.12. Goal met on voice, near-miss on Banking77 (13% escalated vs 10% bar). See R-1, R-3.

### S-5 — Skill text refresh + fold in round-1 baseline wins
**Depends on:** S-4. **Files:** `skills/jev/SKILL.md`, `skills/jev/references/integration.md`, `skills/jev/assets/prd-template.md`, `skills/jev/evals/evals.json`.
**Change:** point SKILL.md at optimize/ensemble/cascade with measured numbers; **Status:** done 2026-09-21. Round-2 evals (4 tasks, harder assertions) not yet run: next step S-6.
Also: add "read the incumbent's output parsing for silent failures", hash-keyed ramp, alert-action rules (rate limit, business hours, suppress if resolved), call-type gate; harder eval assertions.

### S-6 — Run round-2 evals (4 tasks, harder assertions) and publish the viewer screenshot
**Depends on:** S-5. **Files:** `docs/benchmarks/iteration-2/`, `README.md`.
**Acceptance:** WHEN round 2 finishes THEN README SHALL show with-skill vs without-skill pass rates for the 4 tasks with the harder assertions.
**Must not:** reuse round-1 grades.

### S-7 — Real-data benchmark (R-3)
**Depends on:** data-terms clearance by Abhishek. **Must not:** send unredacted client transcripts.
