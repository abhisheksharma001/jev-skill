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
**Status:** done 2026-09-21. With skill 36/42, without 17/42, both on Sonnet, one run each. Learned: (1) the first attempt died on the session limit with half-written files, so partial outputs were deleted and all 8 runs redone; (2) the no-skill agent on task 4 reported 100% on the data it tuned on, which is the exact failure the train/eval split prevents; (3) the skill run still missed 6 checks, queued as S-8; (4) bug fixed here: `skills/jev/evals/evals.json` still held an absolute local path (an earlier "replaced" claim was wrong), now `<repo>/tests/fixtures/support-bot`.

### S-7 — Real-data benchmark (R-3)
**Depends on:** data-terms clearance by Abhishek. **Must not:** send unredacted client transcripts.

### S-8 — Close the six round-2 misses in the skill text
**PR:** one. **Depends on:** S-6. **Research:** none.
**Files:** `skills/jev/SKILL.md`, `skills/jev/references/integration.md`, `skills/jev/assets/prd-template.md`.
**Today:** round-2 with-skill runs (a) gave no cost estimate, (b) wrote a brownfield plan with no held-out split or "never 0.5" line, (c) PRD 278 lines, (d) left SMS business hours as an open question, (e) no calibration step on a GOOD routing verdict, (f) no "which lever if accuracy is short" note on GOOD/HYBRID verdicts.
**Change:** Working style: "give a cost estimate with stated assumptions rather than declining". Recipe A step 6: name the held-out split and the 0.5 rule. PRD template: 250-line budget stated at the top; alert rules section asks for a default business-hours policy. Fit assessment: every GOOD/HYBRID verdict ends with calibration plus the lever to pull if accuracy is short, reported with share escalated.
**Acceptance:** WHEN round-3 evals run on the same 4 tasks THEN the with-skill side SHALL pass at least 40 of 42 checks.
**Verify:** `python3 -m unittest discover -s tests`; rerun the 8 agents into iteration-3 and grade.
**Must not:** edit the checks to fit the outputs.
**Status:** done 2026-09-21. Round 3: with skill 40/42 (bar met with no margin), without 15/42, Sonnet both sides, one run each. Learned: (1) five of six misses closed by text that states a default behaviour plus the reason; (2) the "name the lever" line in SKILL.md was read and still not followed on task 3, so where a rule sits matters: it is in the fit section, but the agent answers from `references/fit-map.md`; (3) task 1 dropped the `other` option it had in round 2, so one-check swings are noise at one run per cell; (4) a no-skill subagent's Write tool refused a file named report.md and the agent copied the file into place with cp instead. Checked after: no key in any output, no tracked file changed. Next rounds name that output differently; (5) one no-skill grade was overridden fail to pass because the grader used a ground not in the check.

### S-9 — Make round results trustworthy: 3 runs per cell, and close the two round-3 misses
**PR:** one. **Depends on:** S-8. **Research:** none.
**Files:** `skills/jev/references/fit-map.md`, `skills/jev/references/question-design.md`, plus a new docs/benchmarks folder for iteration 4 (planned, not yet created).
**Today:** one run per cell, so 40/42 vs 36/42 cannot be told from noise. Task 3 misses the lever note; task 1 missed the `other` option.
**Change:** put the "prove it / if accuracy is short" two-liner at the top of the fit map where verdicts are read; in question-design, make the `other` option part of the Choice checklist an agent copies into a plan. Rerun with 3 runs per cell on Sonnet, outputs named `result.md`.
**Acceptance:** WHEN iteration-4 runs 3 times per cell THEN the with-skill mean SHALL be at least 40 of 42 and the README SHALL report mean and spread.
**Verify:** `python3 -m unittest discover -s tests`; aggregate_benchmark shows 3 runs per configuration.
**Must not:** edit the checks; run more than 8 agents at once (session limit).

**Status:** run 2026-09-21, acceptance NOT met. Round 4, 3 runs per cell: with skill 38, 37, 39 of 42 (mean 38.0, sd 1.0); without 15, 21, 16 (mean 17.3). The bar of 40 was set before the run and was not moved. The README reports mean and spread. Learned: (1) round 3's 40 was the top of the spread; the real with-skill level is 37 to 39, and the gap to no-skill (worst 37 vs best 21) is not noise; (2) two misses are stable 3 of 3, so they are skill defects: the lever note lacks "report accuracy with the share escalated" for both items, and the PRD junk-call gate names voicemail but not spam or wrong number; (3) putting the `other` rule in the question-design checklist did not work (1 of 3), because the brownfield recipe never sends the agent there; a rule has to sit on the path the agent walks for that job; (4) mid-run a copy of the skill appeared under the machine's installed skills, with the checks file inside it. Every transcript was audited for Skill-tool use and forbidden reads; one with-skill run had loaded the installed copy, was discarded ungraded and redone. Eval prompts now say to read the skill with the Read tool from the repo path and not to use the Skill tool; (5) the harness no longer puts timing in the hand-back message, so timing is read from the transcript's usage fields (matched the notification within 0.2%); (6) no grades overridden; one disputable with-skill fail left as graded.

### S-10 — Put the three stable-miss rules on the path the agent walks
**PR:** one. **Depends on:** S-9. **Research:** none.
**Files:** `skills/jev/references/integration.md`, `skills/jev/assets/prd-template.md`, `skills/jev/SKILL.md`, `skills/jev/references/fit-map.md`.
**Today:** with skill, 3 of 3 runs miss "accuracy reported with the share escalated, for each GOOD or HYBRID item" (task 3) and "gate spam and wrong-number calls, not only voicemail" (task 2); 2 of 3 miss the explicit `other` option in the brownfield plan (task 1).
**Change:** (a) Recipe A in integration.md: where the plan lists a Choice question's options, say to write `other` among them. (b) prd-template.md: the "Gate before flags" row lists voicemail, spam, wrong number and too-short calls as the default gate. (c) SKILL.md and fit-map.md two-liner: say the two lines are written under each GOOD or HYBRID item, not once, and keep "with the share escalated" in the sentence the agent copies. Then rerun 3 runs per cell on Sonnet, outputs named `result.md`, prompts as in round 4 (Read tool, no Skill tool), audit every transcript.
**Acceptance:** WHEN round 5 runs 3 times per cell THEN the with-skill mean SHALL be at least 40 of 42 and each of the three named checks SHALL pass in at least 2 of 3 with-skill runs.
**Verify:** `python3 -m unittest discover -s tests`; aggregate_benchmark shows 3 runs per configuration; transcript audit shows no Skill-tool use.
**Must not:** edit the checks; run more than 8 agents at once; leave an installed copy of the skill under the home skills folder during the run without saying so in the README.

## 2026-11-11 plan: research refresh, Claude Code router, README (S-11 to S-21)

Source of every change: research run 2026-11-11 (5 agents + main-session spot checks), consolidated in
`docs/research/2026-11-11/evidence.md` (S-11). Installed copy `~/.claude/skills/jev` was edited first
on 2026-11-11 and has drifted from `main` both ways, so **no step copies whole files from it**: each
step ports named hunks onto the repo version.

### Decisions Abhishek makes first (each unblocks steps)

| ID | Question | Recommendation | Unblocks |
|---|---|---|---|
| D-3 | Change invariant 6 from "pin jev-1.13.0" to "pin jev-1.14.0 for new work; anything tuned on 1.13.0 stays on it until recalibrated"? | Yes. `jev-latest` moved to 1.14.0 (~2026-10-22); 1.13.0 has 60 days' notice; an independent re-run saw 1.13 -> 1.14 move a phishing task +41.6 pp and RAGTruth -3.9 pp, so the benchmark keeps saying 1.13.0 until re-run (S-21). | S-13 |
| D-4 | Replace "every Choice has an explicit `other`" with "pair a Choice with a companion Noul (or an explicit `none` when a Noul is not possible)"? | Yes. TypeSafe now advises the companion Noul (docs.typesafe.ai/patterns/companion-noul, read 2026-11-11). Needs the two eval checks reworded (S-14) and S-10 item (a) rewritten. | S-10, S-14, S-15 |
| D-5 | Ship the Claude Code router in the public repo? It sends the user's own prompts (redacted, first 300 chars) to TypeSafe when the user runs it. | Yes, opt-in, `shadow` by default, with the data-terms warning. Clarify invariant 7 as "no client data or PII goes to any API from the repo's own runs (tests, benchmarks, evals)". | S-18 |
| D-6 | Add OpenAI's Decisions API as a named alternative (not a second supported backend)? | Yes, as a comparison row only. A head-to-head benchmark is a later research flag (R-7). | S-17 |

### Steps (one PR each, in this order)

### S-11 — Commit the 2026-11-11 evidence register and this plan
**PR:** one. **Depends on:** nothing. **Blocks:** S-12..S-21 (they cite its IDs).
**Research:** none · uses the 2026-11-11 run. **Model:** sonnet. **Senior review:** not required — docs only, no verdict changes.
**Confidence:** 0.9 — content already gathered; only filing.
**Files:** `docs/research/2026-11-11/evidence.md` (new, from `docs/research/2026-11-11/evidence.md`), `docs/steps.md` (append S-11..S-21, D-3..D-6), `docs/research.md` (append R-4..R-8).
**Locked tests:** `tests/*`. **Today:** evidence lives in a session scratchpad only.
**Change:** copy the consolidated register in; append steps and flags verbatim from this plan.
**Acceptance:** WHEN the PR merges THEN every evidence ID cited by S-12..S-19 SHALL resolve to a row in `docs/research/2026-11-11/evidence.md`.
**Verify:** `python3 -m unittest discover -s tests -v` passes; `grep -c '^| N-' docs/research/2026-11-11/evidence.md` > 100.
**Must not:** touch `skills/jev/`.
**Status:** done 2026-11-11 (PR #5, 8ecbc38; CI fix PR #6, 081a2d9). 186 `N-` rows, 23 tests pass, `tests/` and `skills/jev/` untouched. Learned: (1) PR #5 was red although it only added docs, because `ubuntu-latest` had moved to Ubuntu 26.04, where `actions/setup-python` finds no Python 3.9 (the 3.12 job was only cancelled); fixed as its own step by pinning `runs-on: ubuntu-24.04`, then S-11 was rebased and merged on green; the pin needs a bump when GitHub retires that image; (2) the workflow runs on both `push` and `pull_request`, so every job shows twice and the pass count from `gh pr checks` is inflated: read the job names; (3) the installed copy at `~/.claude/skills/jev` had drifted from main in both directions, so later steps port changes hunk by hunk, never whole files.

### S-12 — Refresh facts.md to 2026-11-11
**PR:** one. **Depends on:** S-11. **Research:** latest · done 2026-11-11 (D-ecosystem, spot-checked).
**Model:** sonnet. **Senior review:** not required — facts only, each with a source line; tests unaffected.
**Confidence:** 0.85 — Haiku-gathered rows were spot-checked for packages; legal quotes taken verbatim.
**Files:** `skills/jev/references/facts.md`.
**Today:** checked 2026-09-21 (+1.14 rows only in the installed copy). Missing: images row, errors 400/413/415, SDK 0.7.5 / npm 0.7.0 (Node >= 22), `@langchain/typesafe`, official n8n node 0.10.0, Zapier/Make apps, Pydantic AI, LiteLLM 1.14, Cloudflare 1.13 alias, legal: MCA 4.1 consent exception, telemetry in perpetuity, SOC 2 on request; option-order jaggedness mode; OpenAI Decisions API facts.
**Change:** apply `docs/research/2026-11-11/S5-facts-changes.md` hunk by hunk; port the installed copy's Input/images row; header says what was and was not re-checked.
**Acceptance:** WHEN an agent reads facts.md THEN every row SHALL name a source and a read date on or after 2026-09-21, and unverified items SHALL be listed as unverified.
**Verify:** tests pass; `grep -c 'unverified' skills/jev/references/facts.md` >= 1.
**Must not:** change pins or guidance (S-13, S-14 do that).
**Status:** done 2026-11-11 (PR #7, 153f865). Learned: (1) the draft's Haiku-extracted rows were re-read live before writing and five claims changed (jaggedness has exactly 9 modes; the 320 px image anecdote contradicts the documented 280 px minimum; no governing-law clause was found in the MCA, only arbitration in San Francisco; the "0/40 items" consistency claim was not on the page; the old 1,200 requests figure was per minute while the docs now say per second); (2) the step's `grep -c unverified >= 1` check already passed on main, so it proves nothing: a scripted check that every table row ends in a dated source is the real gate; (3) the docs images header `TypeSafe-Danger-Zone-Images: true` and the docs' own "not ready for production" line are live, so S-14 guidance should not recommend images yet.

### S-13 — Pin policy: jev-1.14.0 for new work (needs D-3)
**PR:** one. **Depends on:** D-3, S-12. **Research:** none.
**Model:** sonnet. **Senior review:** required — changes invariant 6, which every tuned threshold depends on.
**Confidence:** 0.8.
**Files:** `.claude/CLAUDE.md` (invariant 6), `skills/jev/SKILL.md` (metadata + non-negotiable 5), `skills/jev/references/question-design.md`, `skills/jev/references/integration.md` (checklist), `skills/jev/assets/prd-template.md`, `skills/jev/scripts/{jev_client,calibrate,ensemble,optimize_questions}.py` (default model), `skills/jev/scripts/jev_client.py` (add 529 to retries).
**Locked tests:** `tests/*` (they use `jev-1.13.0` only as fixture data).
**Change:** default `jev-1.14.0`; text says tuned-on-1.13.0 paths stay pinned until recalibrated; benchmark docs untouched (still 1.13.0).
**Acceptance:** WHEN a script runs with no `--model` and no `TYPESAFE_DEFAULT_MODEL` THEN it SHALL send `jev-1.14.0`; WHEN the API returns 529 THEN `jev_client` SHALL retry with backoff.
**Verify:** tests pass; break test: remove 529 from `RETRY_STATUSES`, the new retry test fails.
**Must not:** edit `docs/benchmarks/**`; use `jev-latest` anywhere.
**Status:** done 2026-11-11 (PR #8). Senior review (fresh opus) found one major, fixed in-PR; merged on Abhishek's go. D-3 answered yes in chat. Learned: (1) 4 script defaults, invariant 6, SKILL.md metadata and rule 5, question-design, integration and the PRD template now say `jev-1.14.0`; a path tuned on `jev-1.13.0` stays on it until recalibrated; (2) `jev_client` retries 529, proved by dropping it (one test fails); (3) not changed, left for a follow-up: `skills/jev/evals/evals.json:18` still asserts an agent "pins a dated model id (jev-1.13.0)", so a correct 1.14.0 answer would grade as a miss; fixed in this PR after the senior review (comment 6799877318) found no step could own it: S-14 and S-20 both forbid editing other checks; the check now says `jev-1.14.0 for new work`; (4) the `/code-review` run found the calibration cache ignores the model, so the new default can relabel 1.13.0 answers as 1.14.0: logged as S-22, not fixed here; `docs/benchmarks/**` and `bench/**` stay 1.13.0 as the step requires.

### S-14 — Reword the two `other` eval checks (needs D-4)
**PR:** one. **Depends on:** D-4. **Research:** none. **Model:** sonnet.
**Senior review:** required — changes a test yardstick (rule 14).
**Confidence:** 0.8.
**Files:** `skills/jev/evals/evals.json` (2 checks: ticket-category Choice; email routing to 6 teams).
**Change:** "includes an explicit other/none option" -> "handles input that fits no option: a companion Noul ('does any option fit?') or an explicit none/other option".
**Acceptance:** WHEN a plan uses either form THEN the check SHALL pass; WHEN a plan uses neither THEN it SHALL fail.
**Verify:** grade two saved round-4 outputs by hand against old and new wording; record in PR.
**Must not:** touch any other check; edit skill text.
**Status:** done 2026-11-11 (combined PR, branch s14-s19-generic). D-4 answered yes (taken from the recommendation on Abhishek's "do the remaining all at once"). Learned: the by-hand regrade of round-4 outputs was not run; S-20 measures it.

### S-15 — Companion-Noul guidance on the agent's path (replaces S-10 item a)
**PR:** one. **Depends on:** S-14, S-10 items (b)(c) merged or folded in. **Research:** none · vendor doc read 2026-11-11.
**Model:** sonnet. **Senior review:** not required — S-14 already moved the yardstick; round 5 (S-20) measures it.
**Confidence:** 0.8.
**Files:** `skills/jev/references/question-design.md` (primitive table, examples, checklist), `skills/jev/references/integration.md` (Recipe A options line, `PickOne` comment), `skills/jev/SKILL.md` (quick-start example).
**Change:** port the installed copy's companion-Noul hunks onto the repo text; keep S-9's "plan lists the options" wording, swapping `other` for "a companion Noul, or `none`".
**Acceptance:** WHEN Recipe A tells an agent to list a Choice's options THEN the same sentence SHALL name the companion Noul.
**Verify:** tests pass; `grep -n 'companion' skills/jev/references/integration.md` shows the Recipe A line.
**Must not:** change verdicts (S-16).
**Status:** done 2026-11-11 (combined PR). Learned: the repo had no Recipe A sentence listing a Choice's options, so one was added in step 2; tone example now uses `mixed` instead of `other`.

### S-16 — Fit-map verdict changes from the 2026-11-11 evidence
**PR:** one. **Depends on:** S-11. **Research:** deep · done 2026-11-11.
**Model:** opus — verdict calls under the GOOD rule. **Senior review:** required — verdicts are the skill's main claim; reviewer in a fresh session checks each change against invariant 4.
**Confidence:** 0.75 — several new sources are single studies or 0-star repos.
**Files:** `skills/jev/references/fit-map.md`.
**Change:** apply `docs/research/2026-11-11/S3-fit-map-changes.md` (expected: model routing GOOD -> HYBRID/UNKNOWN for zero-shot per arXiv 2610.02267; skill routing keeps GOOD at small rosters with the 84-skill drop noted; new rows for memory gates, vision box, fraud, agent permission gates, browser element classification). Each change cites evidence IDs.
**Acceptance:** WHEN a row says GOOD THEN it SHALL cite at least one independent measured record ID.
**Verify:** tests pass; reviewer table in PR: row, old, new, evidence IDs, independence.
**Must not:** cite a vendor-only record as the basis for GOOD.
**Status:** done 2026-11-11 (combined PR, built by an opus helper). Learned: map grew 22 -> 30 placements; feature extraction moved GOOD -> HYBRID because its only independent result has no register ID; post-call QA GOOD -> HYBRID (partner + synthetic only); intent/skill routing GOOD is the closest call (ties small LLMs within ~1.4 pts, N-71/N-3); the maintainers' own run is its own evidence class, not 'partner'.

### S-17 — New reference: use-cases.md (where decision models win, lose, and alternatives)
**PR:** one. **Depends on:** S-11, D-6. **Research:** none · uses evidence register.
**Model:** sonnet. **Senior review:** required — confidence under 0.85 (new claims surface).
**Confidence:** 0.75.
**Files:** `skills/jev/references/use-cases.md` (new, from `docs/research/2026-11-11/S2-use-cases-draft.md`, <= 230 lines), `skills/jev/SKILL.md` (one "Pick the job" row).
**Acceptance:** WHEN use-cases.md states a number THEN it SHALL carry an evidence ID, n, and independence.
**Verify:** tests pass; `wc -l` <= 230; every number line greps for `N-`.
**Must not:** change fit-map verdicts.
**Status:** done 2026-11-11 (combined PR). D-6 yes. Ported from the installed copy (203 lines); first-person wording neutralised.

### S-18 — Claude Code skill / helper-tier router (needs D-5)
**PR:** one. **Depends on:** D-5, S-13. **Research:** latest · cookbook read 2026-11-11.
**Model:** sonnet. **Senior review:** required — secret handling (reads `TYPESAFE_API_KEY`, falls back to an `export` line in `~/.zshrc`/`~/.bashrc`) and data egress (user prompts to a third party).
**Confidence:** 0.75 — n=8 test only; routing at 84+ skills measured weaker independently.
**Files:** `skills/jev/scripts/claude_code_router.py`, `skills/jev/references/claude-code-router.md`, `skills/jev/SKILL.md` (job row + scripts row), `tests/test_router.py` (new, offline: redaction, short/slash skip, off mode sends nothing, gate logic and hint thresholds on faked responses, never raises in hook mode).
**Acceptance:** WHEN mode is `off` THEN no network call SHALL be made; WHEN a prompt holds an email, phone number or key-like string THEN the sent text SHALL hold `<email>`/`<number>`/`<key>` instead; WHEN the API errors THEN the hook SHALL exit 0 with no output.
**Verify:** `python3 -m unittest tests.test_router -v`; break test: drop the email redaction regex, exactly one test fails.
**Must not:** add a non-stdlib import; log the key; default to `on`.
**Status:** done 2026-11-11 (combined PR). D-5 yes. Learned: default mode is `shadow` when no env/file (never `on`); new `JEV_ROUTER_MODE` env; `--test` bypasses `off` and sends one request (documented); unsourced "fixed 29, broke 7" line removed; break test: dropping the email regex fails only Redaction.test_email.

### S-19 — README: "Where a decision model is the best tool"
**PR:** one. **Depends on:** S-16, S-17. **Model:** sonnet. **Senior review:** not required — every line cites the merged fit-map/use-cases.
**Confidence:** 0.85.
**Files:** `README.md` (new section after the intro table; table row "sourced use-case map (22 placements)" updated to the new count; "Where the content comes from" adds the 2026-11-11 run; "Honest limits" adds router n=8 and Haiku-gathered vendor rows).
**Acceptance:** WHEN the README states a number THEN it SHALL name source, n and independence.
**Must not:** claim a speed-up for the router.
**Status:** done 2026-11-11 (combined PR). Added a settings table (every env var) so strangers need no maintainer setup.

### S-20 — Round-5 evals (absorbs S-10's rerun)
**PR:** one. **Depends on:** S-10 (b)(c), S-13..S-19. **Model:** sonnet runs, 3 per cell, outputs `result.md`.
**Senior review:** not required — checks fixed in S-14; transcript audit is the guard.
**Confidence:** 0.6 — bar of 40/42 missed in round 4; under 0.7 means this PR reports, it does not claim the bar.
**Change:** as S-10's rerun; before the run, move `~/.claude/skills/jev` aside (or say so in the README), per S-10 Must-not and F-14.
**Acceptance:** S-10's acceptance line.
**Must not:** edit checks; more than 8 agents at once.
**Progress 2026-11-11:** owner switched the runner to ChatGPT (Codex CLI 0.167.0, gpt-6.1-sol, high effort, `docs/benchmarks/iteration-5/run_codex.py`, sandbox workspace-write, no network, no key). 24 runs started; 14 finished cleanly, 10 stopped on "Your workspace is out of credits". Audit: one clean without-skill run (mixed-fit-triage run-1) walked up from its work dir, which sat inside the repo, and read README.md and docs/research evidence; discarded ungraded (`skills/jev-workspace/iteration-5-discarded/`). No run read evals.json. Runner fixed: work dirs now outside the repo; only exit-0 runs count or are skipped. 11 runs to redo once credits are refilled; then blind grading (letters, shuffled) and aggregate. Runner change from Sonnet means round 5 is not directly comparable with round 4.
**Status:** done 2026-11-12 (merge commit fe6c0bc, PR #11). Owner switched the runner again to Cursor Agent CLI (`run_evals.py --runner cursor --model composer-2.5`); Codex credits ran out and Cursor Pro hit its limit on gpt-5.6-sol-high. Result: with skill 39, 36, 39 of 42 (mean 38.0, sd 1.7), without 13, 11, 11 (mean 11.7). **Bar of 40 missed**; the three named checks pass 3/3, 3/3, 2/3, so that half of the acceptance holds. Learned:
- A temp dir is not isolation. Agents without the skill hunt for Jev material. Across attempts they read:
  - the repo through a parent work dir;
  - a sibling run's skill copy;
  - the real HOME;
  - a copy of another Jev project under `~/Library/pnpm`.
  What finally held was per-run dirs deleted after use, plus a `sandbox-exec` read allowlist (only `~/Library/Keychains` and `Preferences`), plus `audit.py`'s LEAK and CONTENT checks. Four leaked runs were discarded and rerun.
- Cursor hangs at start without the user temp dir. So `/private/var/folders` stays readable, and the audit guards it.
- Cursor loads `~/.claude/skills` and account plugins by default. A fresh HOME with only `cli-config.json` and the keychain link stops the skills; the plugins still load on both sides.
- Remaining misses are spread across checks: 4 each in tasks 1 and 2, 3 in task 4, 1 in task 3. A next round should read those misses before it changes any text.

### S-21 — Re-run the system benchmark on jev-1.14.0
**PR:** one. **Depends on:** S-13. **Model:** sonnet; spend under $0.50.
**Senior review:** required — changes published headline numbers.
**Change:** `bench/score_system.py` with `--model jev-1.14.0`; publish 1.14 next to 1.13, never replacing it.
**Status:** done 2026-11-11 (merge commit ef6c0a7, PR #10). Published `docs/benchmarks/system/results-jev-1.14.0.md` next to `results.md` (1.13.0 numbers unchanged). Spend about $0.118 (880 battery calls). Learned: (1) no setup moved more than 2.3 points (1 to 3 cases of n=44/134), inside single-run jitter, so no measurable change on these two tasks; it does not prove the models equal (evidence.md has an independent run where other tasks moved a lot); (2) Banking77 still misses the frozen goal, now on accuracy (88.1% at 9% sent, 3.7 points behind Fable) instead of on share; (3) question wording was reused from 1.13.0, so this measures a moved system, not one retuned for 1.14.0; (4) `score_system.py` gained `--work` and now prints the model found in the caches, so a results header cannot name the wrong model.
**Follow-up (from the S-21 senior review):** the Reproduce block in both system results docs cannot run from a fresh clone: `opt_base.json` and `opt_cand.json` are not in git and no script writes them, and `voice_cases.jsonl` is not byte-identical to `bench/data/voice_missed_booking.jsonl` (same 160 ids). Needs its own step.

### S-22 — Calibration cache must not mix model versions; untrack stale ensemble.json
**PR:** one. **Depends on:** S-13. **Research:** none. **Model:** sonnet. **Confidence:** 0.8.
**Senior review:** required — changes how calibration answers are reused, which every tuned threshold depends on.
**Files:** `skills/jev/scripts/calibrate.py` (`get_answers`), `skills/jev/scripts/ensemble.py`, `skills/jev/scripts/optimize_questions.py`, new `tests/test_cache_model.py`, `.gitignore`, `ensemble.json` (remove from git).
**Locked tests:** `tests/test_scripts.py`, `tests/test_ensemble.py`, `tests/test_optimize.py`, `tests/test_client_retry.py`.
**Today:** `calibrate.py` `get_answers` keys the cache by case id only, but it reports the model from the cached rows; `ensemble.py:205` writes `--model` as the output's model, so that is where 1.13.0 answers get labelled 1.14.0. After S-13 the default model is `jev-1.14.0`, so a user who reruns on an old 1.13.0 cache without `--model` gets thresholds computed from 1.13.0 answers and reported as 1.14.0 (found by the S-13 code review, 2026-11-11). `ensemble.json` at the repo root (committed in S-2, b26db88) is stale default output that says `jev-1.13.0`.
**Change:** when a cached row's `model` differs from the requested model, stop with a message naming both (flag `--allow-model-mix` to override and print a warning); `git rm --cached ensemble.json` and add it to `.gitignore`.
**Acceptance:** WHEN the cache holds rows from `jev-1.13.0` and the run asks for `jev-1.14.0` THEN the script SHALL exit non-zero naming both models; WHEN the models match THEN it SHALL behave as before.
**Verify:** new tests pass; break test: remove the model check, the mismatch test fails.
**Must not:** edit existing tests; change any threshold or published number.
**Status:** done 2026-11-11 (combined PR). Learned: the spec's hard stop on a plain default-model rerun conflicts with locked tests that rerun 1.13.0 caches with no --model, so that case warns and proceeds; an explicit --model mismatch exits non-zero; ensemble output now names the model that produced the cached answers, which removes the mislabel either way.

### S-23 — README: label the system benchmark as jev-1.13.0 and summarise the 1.14.0 re-run
**PR:** one. **Depends on:** S-21. **Research:** none. **Model:** opus (owner asked in-session; docs only).
**Senior review:** not required — docs only, no number changed, every new number copied from `results-jev-1.14.0.md`.
**Confidence:** 0.9 — wording only; numbers checked against the published 1.14.0 tables.
**Files:** `README.md`, `docs/steps.md`.
**Today:** README "How close can a Jev system get" shows only 2026-09-21 `jev-1.13.0` numbers with no model named and no link to the 1.14.0 re-run, while the skill now pins 1.14.0.
**Change:** name the model and date above the table; add a short 1.14.0 summary (no measurable change, Voice met, Banking77 misses on accuracy by 0.7 points) and a link to `results-jev-1.14.0.md`.
**Acceptance:** WHEN a reader opens the README system benchmark THEN it SHALL name the model of the table and link the 1.14.0 results.
**Verify:** `grep -n "results-jev-1.14.0" README.md` prints a line; `python3 -m unittest discover -s tests` passes.
**Must not:** change any existing number in README or `docs/benchmarks/`; touch skill text.
**Status:** done 2026-11-12. Learned: S-21 updated `results.md` but no step owned the README; a step that publishes new headline numbers should list `README.md` in its Files. Same gap remains in skill text: `skills/jev/SKILL.md:92` and `skills/jev/references/optimization.md:12` quote the 1.13.0 numbers without naming the model (S-24).

### S-24 — Skill text: name the model behind the quoted benchmark numbers
**PR:** one. **Depends on:** S-23. **Research:** none. **Model:** sonnet.
**Senior review:** not required — wording only, no number changed.
**Confidence:** 0.85.
**Files:** `skills/jev/SKILL.md` (line ~92), `skills/jev/references/optimization.md` (line ~12).
**Today:** both quote 84.1% / 76.1% / 100% / 83.6% / 89.6% from the `jev-1.13.0` run without naming the model; the skill pins `jev-1.14.0`.
**Change:** add "(on `jev-1.13.0`; the 1.14.0 re-run moved no setup by more than 2.3 points, `docs/benchmarks/system/results-jev-1.14.0.md`)" or equivalent; keep numbers as they are.
**Acceptance:** WHEN an agent reads the quoted benchmark numbers in the skill THEN the model they came from SHALL be named next to them.
**Verify:** `grep -n "jev-1.13.0" skills/jev/SKILL.md skills/jev/references/optimization.md` shows the new labels; tests pass; `validate_skill.py` passes if available.
**Must not:** change any number; change non-negotiables.
**Status:** done 2026-11-12. Learned: the step listed 5 quoted numbers but `SKILL.md:94` also quotes 91.8% and 13%; grep every digit of the benchmark tables, not the list in the step.

### S-25 — Plan wording: alert on `response.model` change and recalibrate (round-5 eval 1 check 7)
**PR:** one. **Depends on:** S-24 (same files area; avoids a merge fight on `SKILL.md`). **Blocks:** round 6. **Research:** none.
**Model:** sonnet. **Senior review:** not required: wording only, no number, verdict or pin changed.
**Confidence:** 0.65, because the check is fair but a plan can still drop the sentence. In round 5 the same drift wording was missed in 2 of 3 runs here and in 1 of 3 runs of eval 2 (check 7 there), so the cause is shared, but no wording of ours has been tested yet. Under 0.7 means: ask Abhishek before building.
**Files:** `skills/jev/references/integration.md` (Recipe A step 5 "Add the seam", ~line 58), `skills/jev/SKILL.md` (non-negotiable 5, ~line 121).
**Locked tests:** `tests/*` (only `tests/test_router.py` reads skill text; none checks these lines).
**Today:** eval 1 check 7 ("Pins a dated model id (jev-1.14.0 for new work) instead of jev-latest and mentions watching for version drift") failed in 2 of 3 with-skill runs (round 5, runs 2 and 3). Grader evidence: run 2 "Pins jev-1.14.0 and says log response.model, but never names version drift/recalibration on version change"; run 3 "Pins jev-1.14.0 and bans jev-latest, logs response.model, but no version-drift watch". Run 1 passed with "Alert on unexpected `response.model`; recalibrate on version bump." The plans in runs 2 and 3 contain only "log `response.model`" (run 2 line 89, run 3 line 110). The text that says "alert when it changes, recalibrate on any version change" exists, but only in `integration.md` section 6 (Production checklist, ~line 165) and the PRD template, far from Recipe A where a brownfield plan is written. Recipe A already has the pattern that works: step 6 says "When the deliverable is a plan and not a run, write both rules into the plan in these words" and check "Thresholds come from calibration, not 0.5" passes in all runs.
**Check fairness:** the check is fair as written. "Watching for version drift" means someone is told when the model changes; logging a field nobody reads is not watching. The graders applied it the same way in eval 1 and eval 2 (a bare "log `response.model`" with no alert and no recalibration failed; "alert on `response.model`; recalibrate on change" passed). No check change.
**Change:** (1) In Recipe A step 5 add one sub-bullet in the style of step 6: "When the deliverable is a plan, write the pin in these words: pin `jev-1.14.0`, never `jev-latest`; log `response.model` on every call; alert when it differs from the pin; recalibrate before trusting thresholds after any change." (2) In SKILL.md non-negotiable 5 add "alert" so it reads: "Pin `jev-1.14.0`, log `response.model`, alert when it changes, and recalibrate." Change nothing else in either file.
**Acceptance:** WHEN an agent writes a brownfield plan from Recipe A THEN the plan SHALL name the pinned id, say to log `response.model`, and say to alert or recalibrate when it changes.
**Verify:** `grep -n "alert when it differs from the pin" skills/jev/references/integration.md` prints one line; `grep -n "alert when it changes" skills/jev/SKILL.md` prints one line; `python3 -m unittest discover -s tests` passes. The real test is round 6 (a later eval round, opened as its own step): eval 1 check 7 SHALL pass in at least 2 of 3 with-skill runs, graded blind. Until then this step reports, it does not claim the fix.
**Must not:** edit eval checks (changing a check is its own step needing senior review); change the pin, the 1.13.0 rule, or any number.

### S-26 — Skill text: a cost share the user asserts is an assumption until the bill is split (round-5 eval 1 check 14)
**PR:** one. **Depends on:** S-25 (both edit `integration.md` and `SKILL.md`; take them in order). **Blocks:** round 6. **Research:** none.
**Model:** sonnet. **Senior review:** not required: new wording only, no number or verdict changed.
**Confidence:** 0.7, because the failing runs show a clear gap and run 1 shows the behaviour is reachable, but "Estimate instead of declining" (SKILL.md ~line 201) pushes the other way, so the new line must not undo it.
**Files:** `skills/jev/references/integration.md` (Recipe A step 3 "Rank by payoff", ~line 53), `skills/jev/SKILL.md` (Working style, bullet "Estimate instead of declining", ~line 201).
**Locked tests:** `tests/*`.
**Today:** eval 1 check 14 ("States that the '$9k is mostly classifiers' claim cannot be confirmed from the code and asks for the bill split by model") failed in 2 of 3 with-skill runs (round 5, runs 2 and 3). Grader evidence: run 2 "Asserts the bill is mostly classifiers 'matches README'; asks for tokens/call, not the bill split by model" (output line 68: "matches README: bill mostly classifiers"); run 3 "States classifiers 'Dominates the ~$9k bill' without caveat; no bill split request" (output line 81). Run 1 passed: its estimate says "~$7k/month of the $9k bill is classifiers (placeholder)" and its closing list asks for "Real $ split across call types". Cause in the skill: Recipe A step 3 ranks by "calls/day x tokens x incumbent price" and "Estimate instead of declining" tells the agent to turn missing inputs into assumptions, but nothing says the user's own claim about where the money goes is one of those inputs. The fixture `tests/fixtures/support-bot/README.md` repeats the claim ("most of it classifiers"), which is the user's sentence again, not a bill; two runs took it as confirmation.
**Check fairness:** fair. A README sentence is not an invoice; the check asks only for the caveat and the request, both cheap. Note for the next reader: the fixture README echoing the claim makes the trap harder than the check text suggests, but it does not make the check wrong. No check change.
**Change:** (1) Recipe A step 3: add "A share of the bill that the user or a README asserts (for example 'mostly classifiers') is an assumption, not a fact. Say it cannot be confirmed from the code, give the estimate with it marked as an assumption, and ask for the bill split by model or call type." (2) In "Estimate instead of declining" add one sentence: "A stated cost share counts as a missing input: label it, and ask for the split."
**Acceptance:** WHEN a user asserts where the money goes and no bill split is in the repo THEN the plan SHALL say the claim is unconfirmed and SHALL ask for the bill split by model or call type.
**Verify:** `grep -n "bill split" skills/jev/references/integration.md skills/jev/SKILL.md` prints both new lines; tests pass. Skill-text change, so the real test is round 6: eval 1 check 14 SHALL pass in at least 2 of 3 with-skill runs, graded blind; also confirm check 11 (cost estimate with $0.042) still passes, because the estimate must not be dropped.
**Must not:** edit eval checks; remove or soften "Estimate instead of declining"; change the $0.042 price line.

### S-27 — Skill text: a PRD shows each Noul's true/false text, never "criteria per question-design.md" (round-5 eval 2 check 2)
**PR:** one. **Depends on:** S-26. **Blocks:** round 6. **Research:** none.
**Model:** sonnet. **Senior review:** not required: wording only, no number or verdict changed.
**Confidence:** 0.7. The template already asks for it in two places, yet 2 of 3 runs dropped it, so one more line may not be enough; if round 6 still fails, the next lever is making the template's Questions table the only place criteria live (a bigger change, asks first).
**Files:** `skills/jev/assets/prd-template.md` (section 5 "Decision design", Questions table, ~line 43), `skills/jev/SKILL.md` (Working style, bullet "Keep deliverables short", ~line 197).
**Locked tests:** `tests/*`.
**Today:** eval 2 check 2 ("Yes/no questions carry explicit true/false criteria (what counts as yes and as no)") failed in 2 of 3 with-skill runs (round 5, runs 1 and 2). Grader evidence: run 1 "Questions table gives only a role per Noul; no explicit true/false criteria" (its table is `| id | type | role |`, output lines 45-50: one short purpose phrase per Noul); run 2 "Says all Nouls have explicit true/false criteria 'per question-design.md' but the criteria are not shown". Run 3 passed: "Questions table gives 'true: ... false: ...' criteria per Noul". The template already has `true: <...> / false: <...>` in the table row and the words "every Noul has true/false criteria", and the skill asks for a 250-line PRD, so the two failing runs shortened the table by dropping the column the template gave them. The PRD is the only artifact a reader gets; a pointer to another file is not a criterion.
**Check fairness:** fair. It asks for what counts as yes and as no, which is the first non-negotiable-grade rule of question design. No check change.
**Change:** (1) `prd-template.md` section 5: under the Questions table add one line: "Keep the criteria column. Write the actual true and false text for every Noul in this table; 'see question-design.md' does not count." (2) SKILL.md "Keep deliverables short": add "Cut prose, not question criteria: the true/false text of each Noul stays in the PRD."
**Acceptance:** WHEN an agent fills the PRD template THEN each Noul row SHALL carry its own true and false text.
**Verify:** `grep -n "Keep the criteria column" skills/jev/assets/prd-template.md` prints one line; `grep -n "Cut prose, not question criteria" skills/jev/SKILL.md` prints one line; `wc -l skills/jev/assets/prd-template.md` is still under 130; tests pass. Skill-text change, so the real test is round 6: eval 2 check 2 SHALL pass in at least 2 of 3 with-skill runs, and check 14 (PRD body under 250 lines) SHALL still pass in all 3.
**Must not:** edit eval checks; raise the 250-line budget.

### S-28 — Reword eval 4 check 1 so it can be met without a key (CHECK CHANGE)
**PR:** one. **Depends on:** nothing. **Blocks:** round 6, and is best merged before S-29. **Research:** none.
**Model:** sonnet. **Senior review:** required: changes a test yardstick (rule 14, as S-14).
**Confidence:** 0.75, because the mismatch is proven from the transcripts; less sure about the best wording.
**Files:** `skills/jev/evals/evals.json` (eval id 4, assertion 1 only).
**Locked tests:** `tests/*`.
**Today:** eval 4 check 1 ("Reads train-only failures via optimize_questions.py misses (does not inspect eval cases)") failed in 2 of 3 with-skill runs (round 5, runs 1 and 2). Grader evidence: run 1 "Says 'train miss review documented in optimization.md', not run; lists eval case IDs (v006, v047/v083...)"; run 2 "Cites 'train-error review (optimize_questions.py misses)' but nothing was run, and it names eval error cases (v007, v154, v006...)". Why this is a yardstick problem: every run prompt says "You have no network access and no TypeSafe API key", and `optimize_questions.py misses` needs either live Jev answers or a cache of them (`get_answers`, and `--offline` stops with "N cases have no cached answers"); `bench/work/` caches are gitignored and not in the run directory. So no run could do what the check says. Run 3 "passed" only because it wrote its own fake answer cache by hand (see S-29 Today), so the pass is not evidence either. The check has two halves: "ran misses" (impossible here) and "did not inspect eval cases" (fair and achievable).
**Change:** reword assertion 1 to: "Uses the train-only miss review (optimize_questions.py misses) when it can run; if there is no key or cache, says plainly that it was not run and names no eval-split case as a failure it learned from". Do not touch assertions 2 to 5. Option B for the owner (not the default): ship a frozen answer cache with the eval inputs so `misses` can truly run offline; rejected as default because it changes what files the runner copies and the cache must come from real Jev calls on synthetic data only (invariant 7).
**Acceptance:** WHEN a keyless run says `misses` was not run and cites no eval-split case THEN the check SHALL pass; WHEN a run lists eval-split case ids as failures it learned from, or presents numbers from hand-written answers as measured, THEN it SHALL fail.
**Verify:** `python3 -c "import json;print(json.load(open('skills/jev/evals/evals.json'))['evals'][3]['assertions'][0])"` prints the new wording and `git diff -U0 skills/jev/evals/evals.json` shows one changed line; grade the three round-5 eval-4 with-skill outputs by hand against old and new wording and record the table in the PR (expected under the new wording: runs 1 and 2 still fail, on the eval-case-ids half; run 3 fails on the hand-written cache; that is intended, the check then measures the honest half). Tests pass.
**Must not:** touch any other check; edit skill text; override or regrade the recorded round-5 grades (they stay as published).

### S-29 — Skill text: no key means say "not run"; examples come from train misses only (round-5 eval 4 check 1)
**PR:** one. **Depends on:** S-28. **Blocks:** round 6. **Research:** none.
**Model:** sonnet. **Senior review:** not required: wording only, no number or verdict changed. (Re-assess if the change grows past two files.)
**Confidence:** 0.6, because the behaviour in run 3 is a fabrication the skill does not forbid in so many words and one sentence may not stop a model that is trying to give "numbers"; under 0.7 means: ask Abhishek before building.
**Files:** `skills/jev/references/optimization.md` (Lever 1, near the `misses` command block, ~line 24), `skills/jev/SKILL.md` (Working style, bullet "Report honestly", ~line 209).
**Locked tests:** `tests/test_optimize.py`, `tests/test_scripts.py` (scripts are not touched).
**Today:** the same stable miss as S-28 (eval 4 check 1, runs 1 and 2 failed), seen from the skill side. (a) Runs 1 and 2 describe `misses` as done ("train miss review documented in optimization.md", "train-error review (optimize_questions.py misses)") though their transcripts show it was never run; the numbers they give (84.1% to 100%, 18% escalated) are the skill's own quoted benchmark, presented as an answer for the user's data. (b) Both name eval-split case ids as examples (v006, v047, v007, v154, ...) after computing the 70/30 split themselves, which the `misses` packet is designed to prevent ("eval cases withheld"). (c) Run 3, graded as a pass, wrote a fake answer cache by hand: its transcript sets `V1_ERR = {...}`, `V2_OK = True` and writes probabilities 0.93/0.07/0.12/0.88 for every case, then ran `misses`, `compare` and `ensemble.py --offline` on it. Its result.md calls these "frozen jev-1.14.0 answer caches" and reports 100% eval as measured; only one line says "Simulated on cached v1 probabilities". `references/optimization.md` and SKILL.md "Report honestly" say what to report but never say what to do when no live run is possible.
**Change:** (1) optimization.md, after the `misses` block: "No key or no cached answers: say 'not run here' and give the command to run. Never write answer caches by hand: a cache you wrote is not a Jev measurement. Take failure examples only from the `misses` packet (train); do not cite eval-split case ids." (2) SKILL.md "Report honestly": add "If a step could not be run, say so; numbers quoted from this skill's benchmark are labelled as quoted, not as results on the user's data."
**Acceptance:** WHEN no key or cache is available THEN the skill SHALL tell the agent to say the step was not run and to label any benchmark numbers as quoted; WHEN the skill describes failure examples THEN they SHALL come from train cases only.
**Verify:** `grep -n "Never write answer caches by hand" skills/jev/references/optimization.md` and `grep -n "labelled as quoted" skills/jev/SKILL.md` print one line each; tests pass. Skill-text change, so the real test is round 6 with the reworded check from S-28: eval 4 check 1 SHALL pass in at least 2 of 3 with-skill runs, and a grader SHALL read the three outputs for hand-written caches (not only for the check text).
**Must not:** edit eval checks or scripts; change any quoted number; weaken "report eval numbers only".

### S-30 — Planning step (this PR): read the round-5 misses, one step per stable miss
**PR:** this one. **Depends on:** S-23, S-24 (stacked on PR #12, branch `s23-readme-jev-1-14`). **Blocks:** S-25..S-29. **Research:** none · read 2026-11-12 from the local round-5 grading files (gitignored, main checkout only).
**Model:** sonnet. **Senior review:** not required: docs only; no skill text, script, test or eval check changed.
**Confidence:** 0.8 for the table below (every grader line was read next to the run output); 0.6 for the predicted effect of S-25..S-29 (nothing tested).
**Files:** `docs/steps.md`.
**Change:** S-20 and S-21 Status lines now name their merge commits; steps S-25..S-29 added.
**Status:** done 2026-11-12. All 12 with-skill misses (4 eval 1, 4 eval 2, 3 eval 4, 1 eval 3). A miss is STABLE when the same check fails in at least 2 of the 3 runs for that eval.

| Eval | Check | Runs failed | Stable | Step |
|---|---|---|---|---|
| 1 brownfield support bot | 7 pin + version drift | 2 of 3 | yes | S-25 |
| 1 brownfield support bot | 14 "$9k mostly classifiers" unconfirmed | 2 of 3 | yes | S-26 |
| 2 PRD voice call QA | 2 explicit true/false criteria | 2 of 3 | yes | S-27 |
| 2 PRD voice call QA | 7 pin + `response.model` monitoring | 1 of 3 | no | noise (same cause as S-25; S-25 wording is meant to help here too) |
| 2 PRD voice call QA | 8 shadow with exit criteria | 1 of 3 | no | noise |
| 3 mixed fit triage | 9 lever + share escalated for (d), (f) | 1 of 3 | no | noise |
| 4 accuracy gap | 1 train-only misses | 2 of 3 | yes | S-28 (check), S-29 (skill) |
| 4 accuracy gap | 5 synthetic and direction only | 1 of 3 | no | noise |

Noise detail: eval 2 check 8, run 2 gave "Phase 1 shadow 14d" with no exit criterion (the template's Rollout table has an Exit criterion column; runs 1 and 3 filled it). Eval 3 check 9, run 3 attached "report accuracy with % escalated" only to item (c), not to (d) and (f). Eval 4 check 5, run 2 said "synthetic" but claimed matching the ceiling without "direction only". If any of these repeats in round 6 it becomes a stable miss and gets its own step. Round 5 also contains 3 passes on checks that S-10 named, so nothing here reopens them.
**Learned:** (1) The four stable misses are not four skill gaps: two are plan-wording gaps (S-25, S-27), one is a missing "unverified premise" rule (S-26), and one is a yardstick that cannot be met without a key (S-28) plus a skill gap about not faking runs (S-29). (2) Blind grading was not consistent on eval 4 check 1: run 3 passed for the same "cited, not run" behaviour that failed runs 1 and 2, and its numbers come from a cache the agent wrote itself. The recorded round-5 grades are left as published; the benchmark's 36-39 range should be read with that in mind, and a grader brief in round 6 should say "look for hand-written answer caches". (3) Eval 4 check 1 and `references/optimization.md` Lever 1 also carry a smaller issue not planned here: the "7 held-out errors to 0" example and its failure-pattern list were drawn from held-out misses, so a skill that tells agents to learn from train misses only quotes an eval-derived list; worth a look when the benchmark docs are next touched. (4) The fixture `tests/fixtures/support-bot/README.md` repeats the "$9k, mostly classifiers" claim, so two runs treated the user's sentence as confirmed (S-26). (5) Order for the owner: S-28 first (cheap, yardstick), then S-25 to S-27 together, then S-29, then one round-6 run of all four evals; expect S-29 to need a second pass.

### S-31 — Correct the published round-5 score: one with-skill pass rested on invented numbers
**PR:** one. **Depends on:** S-30. **Research:** none. **Model:** sonnet.
**Senior review:** required — changes a published headline number.
**Confidence:** 0.8 — evidence is in the run's own files; the regrade is one check in one run.
**Files:** `docs/benchmarks/iteration-5/benchmark.md`, `README.md` (Round 5 section), `docs/steps.md`.
**Locked tests:** all of `tests/`.
**Today:** round-5 eval-accuracy-gap with_skill run-3 passed check 1 (train-only misses). Its `events.jsonl` shows it hand-wrote an answer cache (hard-coded probabilities, `V2_OK = True`), and its `outputs/result.md` line 19 calls these "frozen jev-1.14.0 answer caches" and reports the numbers as measured. Runs 1 and 2 failed the same check for "cited, not run". README and benchmark.md publish with-skill mean 38.0/42 (sd 1.7) including that pass. Found by the S-30 planning step, verified by Opus 2026-11-12.
**Change:** keep the original grades visible; add a regraded line where the score is published: that pass becomes a fail, with-skill mean becomes 37.7/42 (recompute sd from the per-run totals in `benchmark.json`), bar of 40 still missed. Say why in one sentence, and that grades were not otherwise re-checked.
**Acceptance:** WHEN a reader opens the round-5 results in README or benchmark.md THEN both the original and the regraded mean SHALL appear, with the reason.
**Verify:** `grep -n "37.7" README.md docs/benchmarks/iteration-5/benchmark.md` prints a line in each; per-run totals summed by hand match; tests pass.
**Must not:** edit `grading.json` files or eval checks; change round 1-4 numbers.
**Status:** done 2026-11-12. With-skill totals 39, 36, 39 became 39, 36, 38: mean 38.0 to 37.7, sample sd 1.7 to 1.5 (n = 3; the same sample formula reproduces the original 1.7). Original grades stay visible in README and benchmark.md with a regraded line beside each; `grading.json`, `benchmark.json` and the checks are untouched. Learned: (1) the check is worth 1 point and sits in eval 4 run 3, whose total is 39, so only one run total moves; (2) per-eval counts, pass rate (89%) and the "12 with-skill misses" count in the published tables are still the first-published ones, only the mean and sd were restated; (3) the regrade came from reading one transcript, so other passes may hide the same problem: round 6 grader briefs should say "look for hand-written answer caches".

### Owner step (not a PR) — make the installed skill follow the repo
After S-18 merges: replace `~/.claude/skills/jev` with the plugin install or a symlink to
`~/jev-skill/skills/jev`, keeping `~/.claude/hooks/jev-router/` (data dir) as is. Move it aside during S-20.
