# jev-skill — project rules

Open-source agent skill for TypeSafe AI's Jev decision model. Standard: `~/.claude/skills/mystandard/SKILL.md`.

## Invariants
1. No secret in the repo, ever. Keys come from `TYPESAFE_API_KEY` in the environment only.
2. Scripts under `skills/jev/scripts/` use the Python standard library only.
3. Every number in the skill or README names its source and sample size, or is labelled synthetic.
4. A verdict of GOOD needs independent measured evidence. Vendor or partner-only evidence is never GOOD.
5. Benchmarks publish held-out numbers only, with n, and say synthetic vs public data.
6. Pin `jev-1.13.0` in anything with tuned thresholds. Never `jev-latest`.
7. No client data or PII goes to any API from this repo. Synthetic or public datasets only.

## Verify
```bash
python3 -m unittest discover -s tests -v
python3 ~/research-council/scripts/validate_skill.py skills/jev   # if research-council is checked out
```

## Layout
- `skills/jev/` the skill (SKILL.md, references/, assets/, scripts/, evals/)
- `tests/` unit tests and the `support-bot` fixture repo
- `docs/steps.md` step register, `docs/research.md` research flags, `docs/benchmarks/` published results
- `AGI_Research/` and `skills/jev-workspace/` are local only (gitignored)
