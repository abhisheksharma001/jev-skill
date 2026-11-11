# Jev as a skill and helper-model router inside Claude Code

Use this when the user wants Jev to make Claude Code cheaper or faster ("route tasks to the right
model", "pick the right skill"). Script: `scripts/claude_code_router.py` (standard library only).
Built and first tested 2026-11-11. **Opt-in, and `shadow` (log only) until you switch it on.**

## What it can and cannot do

- **Can:** on every prompt, suggest which installed skill fits, and whether helper agents should be
  `haiku`, `sonnet` or `opus`. The hint is one line of added context; Claude still decides.
- **Cannot:** switch the main session's model mid-conversation. A hook can only add context. Jev is
  not a coding model (docs.typesafe.ai/introduction/coding-agents, read 2026-11-11).
- **Realistic gain:** fewer wrong or needless skill loads, and cheaper helper agents. Claude already
  sees the skill list every turn, so do not promise big speed-ups.

Fit verdict: **UNKNOWN** (`fit-map.md`, row "Skill hints inside an agent harness": the one independent test, N-6,
found no gain inside Claude Code). The tier hint is a zero-shot model router, which the fit-map rates
HYBRID at best, so it stays log-only unless you set `JEV_ROUTER_TIER=on` after calibrating it.

## How it works (two requests, vendor cookbook method)

```
prompt --> local filters (off mode, < 15 chars, starts with "/") --> redact + first 300 chars
  Request 1: which (Choice over all skills, no "none")  + gate Nouls + named Noul + tier Choice
     action = mean(acts_on_system, follows_procedure, 1 - prose_suffices)
     stop if action < 0.30 and named < 0.50                       (no skill wanted)
  Request 2: rerank top 3 (full description + SKILL.md excerpt) + one fits:: Noul per candidate
     stop if max fits < 0.30                                      (nothing fits)
  log every decision; in "on" mode print a hint when fits >= 0.70 and pick >= 0.60,
  or name every candidate with fits >= 0.70 when near-duplicates split the pick
```

Why no `none` option: a `none` option competes with real options for probability; the vendor now
recommends a companion Noul instead (docs.typesafe.ai/patterns/companion-noul). Why one `fits` Noul
per candidate: near-duplicate skills (two skills that both cover RAG) each fit at ~0.97 while
the Choice splits 0.57 / 0.43 (N-8 run, n=8, synthetic), so the Choice alone would stay silent.

## Install (opt-in)

Nothing runs until **you** add a hook entry. Claude Code's auto mode refuses to edit `settings.json`
itself (self-modification), so you add it, via `/hooks` or by hand. Back the file up first.

1. Get the script to a stable path. Pick one:
   - **Plugin install:** the script ships inside the plugin at `skills/jev/scripts/claude_code_router.py`
     (find the plugin folder under `~/.claude/plugins/`). That folder can change on plugin update, so copy
     the script out, as below.
   - **Manual install:** clone this repo and use `skills/jev/scripts/claude_code_router.py` from the clone,
     or from `~/.claude/skills/jev/scripts/` if you copied the skill there.
2. Create the data dir and set the mode (replace `<path-to>` with where the script is):
   ```bash
   mkdir -p ~/.claude/hooks/jev-router && echo shadow > ~/.claude/hooks/jev-router/mode
   cp <path-to>/claude_code_router.py ~/.claude/hooks/jev-router/jev_router.py
   ```
3. Export `TYPESAFE_API_KEY` in your environment, then do one dry run. This sends one real request
   (it ignores `off`, because you asked for it):
   ```bash
   python3 ~/.claude/hooks/jev-router/jev_router.py --test "Build a RAG pipeline over our PDFs"
   ```
4. Add this to `~/.claude/settings.json` under `hooks.UserPromptSubmit[].hooks`:
   `{"type": "command", "command": "python3 ~/.claude/hooks/jev-router/jev_router.py", "timeout": 5}`.

Key: `TYPESAFE_API_KEY` from the environment, else an `export TYPESAFE_API_KEY=...` line in `~/.zshrc` or
`~/.bashrc` (hooks may not load the shell profile). The key is sent only in the request's
`Authorization` header; it is never printed and never written to the log (the log holds the decision and
the redacted text, no headers). Model: `TYPESAFE_DEFAULT_MODEL`, default `jev-1.14.0`. Never `jev-latest`.

## Modes and files (data dir `~/.claude/hooks/jev-router`, or `$JEV_ROUTER_HOME`)

The mode is `$JEV_ROUTER_MODE` if set, else the `mode` file. Missing file, empty value or an unknown word
means `shadow`; it never defaults to `on`. Skills are read from `~/.claude/skills`, or `$JEV_ROUTER_SKILLS`.

| File | Meaning |
|---|---|
| `mode` | `off` (sends nothing) / `shadow` (log only, the default) / `on` (log + hint) |
| `log.jsonl` | One line per routed prompt: gates, wide top 3, fits, pick, tier, tokens, ms, redacted text sent |
| `skill_index.json` | Cache of the skills folder's `*/SKILL.md`, rebuilt when any SKILL.md changes |

## Privacy and data terms (non-negotiable 8, "Nothing sensitive leaves without clearance", applies)

**Read this before you install.** Every routed prompt goes to TypeSafe AI, a US-hosted third party
(`facts.md`, data terms: hosting, retention and zero-data-retention are stated there, with dates).
`shadow` mode sends prompts too; it only withholds the hint. Only `off` sends nothing.

What leaves the machine on each routed prompt: the first 300 characters of the prompt, every installed
skill's name and description (up to 220 characters each), and for the top 3 skills up to 600 characters
of description plus 600 characters of SKILL.md body. All of it is redacted first, by replacing emails (`<email>`), phone numbers and
runs of 5+ digits (`<number>`), key-like strings (`<key>`) and long opaque tokens (`<token>`). That is a
filter, not a guarantee: client names, addresses and free-text secrets still pass. If you work with
client or regulated data, use `off` until someone has read TypeSafe's current terms, or enable it only
for non-client work. Local copy: `log.jsonl` holds the redacted text it sent; delete it when done.

## Rollout

1. **Shadow ~1 day** of normal use. No hint reaches Claude.
2. **Label the log.** For each line, write the right skill (or `none`) and the right tier. 30-50
   lines is enough for a first cut; include near-misses.
3. **Calibrate.** Pick `HINT_FITS_MIN`, `HINT_PICK_MIN`, `HINT_TIER_MIN` on a train split and report
   wrong hints, missed hints and silent-correct on the held-out split (`calibration.md`). A wrong
   confident hint costs more than a missed one.
4. **Switch on** (`echo on > mode`) only if held-out wrong hints are rare. Re-run 2-3 after any skill
   install, Jev version change, or a wording change to the questions.

## First results (2026-11-11, jev-1.14.0, 94 skills, one maintainer, from outside the US)

8 hand-written prompts, labelled by the agent: v1 (single Choice with `none`) gave 3 right hints,
2 misses, 0 wrong; v2 (this script) gave 5 right hints, 0 wrong, 1 miss (`multimodal-whisper` for
"find where the agent interrupted the caller": its description is about transcription, so Jev reading
literally is fair). Tier hint improved from "hard for everything" to plausible. Latency 0.5-0.6 s
(v1, one request) vs 0.9-1.0 s (v2, two requests); ~6-7k input tokens, about $0.0003 per prompt.
Direction only: n=8, synthetic, agent-labelled, one maintainer's skill set, not independent evidence.

## Known limits

- Independent evidence (as of 2026-11-11, `docs/research/2026-11-11/evidence.md`): 97.6% at 126 skills
  (n=500, N-3), but at 84 skills with default thresholds right 37/69 and silent 25/69 (n=81, N-2);
  zero-shot *model* routing at chance (arXiv 2610.02267, n=13,923, N-1). So keep the tier hint log-only until step 3 shows it works.
- Only the skills folder (default `~/.claude/skills`); plugin skills (`plugin:skill` names) are not indexed yet.
- Skills are listed alphabetically; jev-1.13 leaned toward first-listed options. If the log shows
  early-alphabet skills over-picked, shuffle or sort by usage and re-check.
- Two sequential requests add ~1 s to prompts that want a skill; the hook times out at 2 s per
  request and then says nothing.
- A hint that is confidently wrong can pull Claude off a right answer. Keep the hint wording humble and
  do not change it without re-running step 3.
