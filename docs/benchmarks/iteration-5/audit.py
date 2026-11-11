#!/usr/bin/env python3
"""Audit round-5 transcripts (Cursor stream-json or Codex --json events).

Fails a run when it touched anything outside its own work dir, when a without_skill run touched a
skill, or when any run touched the eval checks (evals.json). Prints one line per run.
Usage: python3 audit.py <workspace>/iteration-5
"""
import json, re, sys
from pathlib import Path

HOME = str(Path.home())
SKILLISH = re.compile(r"SKILL\.md|/skills?/jev|skill/jev|jev-skill|\.claude/skills|\.agents/skills|\.cursor/skills|fit[-_]map|fit_check")


def touched(events):
    """Every path or command string the agent used in a tool call."""
    for line in open(events, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "tool_call" and e.get("subtype") == "started":  # cursor
            for name, body in (e.get("tool_call") or {}).items():
                yield name, json.dumps(body.get("args", body) if isinstance(body, dict) else body)
        it = e.get("item") or {}
        if e.get("type") == "item.started" and it.get("type") == "command_execution":  # codex
            yield "shell", it.get("command", "")


def main(ws):
    bad = 0
    for run in sorted(Path(ws).glob("*/*/run-*")):
        cfg = run.parent.name
        issues = set()
        wd = run / "workdir.txt"
        own = tuple(x.replace("/private/var/", "/var/") for x in wd.read_text().split()) if wd.exists() else ()
        for tool, s in touched(run / "events.jsonl"):
            if "evals.json" in s or re.search(r"/evals/", s):
                issues.add(f"{tool}: eval checks")
            for p in re.findall(re.escape(HOME) + r"[^\s\"']*", s):
                issues.add(f"{tool}: outside work dir {p.replace(HOME, '~')[:80]}")
            if own:  # a temp path that is neither this run's work dir nor its own Cursor home
                for p in re.findall(r"/(?:private/)?(?:var/folders|var/tmp|tmp)/[^\s\"']*", s):
                    q = p.replace("/private/var/", "/var/").replace("/private/tmp/", "/tmp/")
                    if not q.startswith(own):
                        issues.add(f"{tool}: another run's dir ...{p[-60:]}")
            if cfg == "without_skill" and SKILLISH.search(s):
                issues.add(f"{tool}: skill access {SKILLISH.search(s).group(0)}")
        print(("FAIL " if issues else "ok   ") + str(run.relative_to(ws)), *sorted(issues)[:4], sep="\n     " if issues else "")
        bad += bool(issues)
    print(f"{bad} run(s) failed the audit")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
