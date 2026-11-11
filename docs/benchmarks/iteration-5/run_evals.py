#!/usr/bin/env python3
"""Round-5 eval runner: a non-Claude agent CLI answers each eval with and without the skill.

Runners: `cursor` (Cursor Agent CLI, default; HOME is a private temp dir so no personal skill,
including an installed jev, is visible; env stripped of keys; sandbox on) or `codex` (Codex CLI).

Each run gets its own empty directory holding only the fixture files the prompt names, plus, for
with_skill, a copy of skills/jev under ./skill/jev. Codex runs with `--sandbox workspace-write`
(no network) and `--ephemeral`. Output: <out>/<eval-name>/<config>/run-<n>/outputs/result.md.

Usage: python3 run_evals.py --out <workspace>/iteration-5 [--runner cursor|codex] [--runs 3] [--parallel 8] [--model M]
"""
import argparse, concurrent.futures as cf, json, os, shutil, subprocess, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
NAMES = {1: "eval-brownfield-support-bot", 2: "eval-prd-voice-call-qa", 3: "eval-mixed-fit-triage", 4: "eval-accuracy-gap"}
SKILL_LINE = ("A skill for this task is in ./skill/jev. Before answering, read ./skill/jev/SKILL.md and the "
              "references and scripts it points you to, and follow it.\n\n")
TAIL = ("\n\nRepository files mentioned above are under ./repo (paths relative to the repo root). "
        "You have no network access and no TypeSafe API key. Write your complete answer to ./result.md.")


def cursor_env():
    """A fresh HOME per run with only Cursor's auth and CLI config: no ~/.claude/skills, ~/.agents/skills or
    ~/.cursor/skills, and no other run's transcripts."""
    h = Path(tempfile.mkdtemp(prefix="r5h-"))
    (h / ".cursor").mkdir(parents=True, exist_ok=True)
    (h / "Library").mkdir(exist_ok=True)
    shutil.copy2(Path.home() / ".cursor" / "cli-config.json", h / ".cursor" / "cli-config.json")
    kc = h / "Library" / "Keychains"
    if not kc.exists():
        kc.symlink_to(Path.home() / "Library" / "Keychains")  # macOS login keychain holds the Cursor login
    keep = {k: os.environ[k] for k in ("PATH", "USER", "LOGNAME", "LANG", "TERM", "SHELL", "TMPDIR") if k in os.environ}
    return dict(keep, HOME=str(h))


def one(ev, config, n, out, model, runner="cursor"):
    run = out / NAMES[ev["id"]] / config / f"run-{n}"
    # work dir lives OUTSIDE the repo: inside it, round-5 run 1 walked up and read the repo's README and research notes
    # and each run gets its own random dir: with shared sibling dirs, a without_skill run read a with_skill run's skill copy
    try:  # skip only a run that finished cleanly; an errored run (e.g. out of credits) is redone
        if json.load(open(run / "timing.json"))["exit"] == 0 and (run / "outputs" / "result.md").exists():
            return run, "skip"
    except (OSError, ValueError, KeyError):
        pass
    shutil.rmtree(run / "outputs", ignore_errors=True)
    work = Path(tempfile.mkdtemp(prefix="r5w-"))
    run.mkdir(parents=True, exist_ok=True)
    for f in ev.get("files", []):
        src, dst = REPO / f, work / "repo" / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
    prompt = ev["prompt"].replace("<repo>", "./repo") + TAIL
    if config == "with_skill":
        shutil.copytree(REPO / "skills" / "jev", work / "skill" / "jev", ignore=shutil.ignore_patterns("evals", "__pycache__"))
        prompt = SKILL_LINE + prompt
    env = None
    if runner == "cursor":
        cmd = ["cursor-agent", "-p", "--trust", "--force", "--sandbox", "enabled", "--output-format", "stream-json",
               "--workspace", str(work)] + (["--model", model] if model else [])
        env = cursor_env()
    else:
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--sandbox", "workspace-write",
               "-C", str(work), "--json", "-o", str(run / "last_message.txt")] + (["-m", model] if model else [])
    t0 = time.time()
    with open(run / "events.jsonl", "w") as log:
        try:
            p = subprocess.run(cmd + [prompt], stdout=log, stderr=subprocess.STDOUT, timeout=1800, cwd=work, env=env)
        except subprocess.TimeoutExpired:
            p = subprocess.CompletedProcess(cmd, 124)
    (run / "outputs").mkdir(exist_ok=True)
    res = work / "result.md"
    if res.exists() and p.returncode == 0:  # a result written before an error is not graded
        shutil.copy2(res, run / "outputs" / "result.md")
    tokens = 0
    for line in open(run / "events.jsonl", errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        u = (e.get("usage") or (e.get("msg") or {}).get("usage") or {})
        if e.get("type") == "result" and e.get("is_error"):
            p = subprocess.CompletedProcess(cmd, p.returncode or 1)  # cursor can exit 0 on an errored turn
        t = sum(int(u.get(k, 0) or 0) for k in ("input_tokens", "output_tokens", "inputTokens", "outputTokens",
                                                "cacheReadTokens", "cacheWriteTokens"))
        tokens = max(tokens, t)
    json.dump({"runner": runner, "model": model or "default", "total_tokens": tokens, "total_duration_seconds": round(time.time() - t0, 1), "exit": p.returncode},
              open(run / "timing.json", "w"))
    (run / "prompt.txt").write_text(prompt)
    (run / "workdir.txt").write_text(str(work) + ("\n" + env["HOME"] if env else ""))  # audit allows only these temp dirs
    return run, "ok" if res.exists() and p.returncode == 0 else f"failed (exit {p.returncode}, result.md {'written' if res.exists() else 'missing'})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--parallel", type=int, default=8)
    ap.add_argument("--runner", choices=("cursor", "codex"), default="cursor")
    ap.add_argument("--model", default="")
    a = ap.parse_args()
    out = Path(a.out)
    evals = json.load(open(REPO / "skills/jev/evals/evals.json"))["evals"]
    for ev in evals:
        d = out / NAMES[ev["id"]]
        d.mkdir(parents=True, exist_ok=True)
        json.dump({"eval_id": ev["id"], "eval_name": NAMES[ev["id"]], "prompt": ev["prompt"],
                   "assertions": ev["assertions"]}, open(d / "eval_metadata.json", "w"), indent=1)
    jobs = [(ev, c, n) for n in range(1, a.runs + 1) for ev in evals for c in ("with_skill", "without_skill")]
    with cf.ThreadPoolExecutor(max_workers=min(a.parallel, 8)) as pool:
        for fut in cf.as_completed([pool.submit(one, ev, c, n, out, a.model, a.runner) for ev, c, n in jobs]):
            run, status = fut.result()
            print(status, run.relative_to(out), flush=True)


if __name__ == "__main__":
    main()
