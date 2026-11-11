#!/usr/bin/env python3
"""Audit round-5 transcripts (Cursor stream-json or Codex --json events).

Fails a run when it touched anything outside its own work dir (an attempt; most are blocked by the sandbox),
when a successful tool result shows a path outside the run (LEAK: the agent saw it), when a without_skill run touched a
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


# Phrases found only in the skill's own files. A tool result that contains one means the run SAW skill content.
SKILL_TEXT = ("You are the expensive part", "fit_check.py --template", "Where Jev pays off most",
              "Non-negotiables (each one traces", "Fit assessment (always first)")


def saw_skill_text(events):
    for line in open(events, errors="replace"):
        if '"tool_call"' in line and '"completed"' in line and any(t in line for t in SKILL_TEXT):
            return True
    return False


# Paths outside the run that may legitimately appear in a successful result: Cursor's own install, pyenv, and
# macOS xcrun cache names printed by the python3 shim.
QUIET = (HOME + "/.local/share/cursor-agent", HOME + "/.pyenv")
TEMP = re.compile(r"/(?:private/)?(?:var/folders|var/tmp|tmp)/[^\s\"'\\`]*")


def leaks(events, own):
    """Paths outside this run that came back in a SUCCESSFUL tool result: the agent saw something of ours.
    For shell calls only stdout counts (stderr carries 'Operation not permitted' for blocked reads)."""
    for line in open(events, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "tool_call" or e.get("subtype") != "completed":
            continue
        for name, body in (e.get("tool_call") or {}).items():
            ok = (body.get("result") or {}).get("success") if isinstance(body, dict) else None
            if not isinstance(ok, dict):
                continue
            text = ok.get("stdout", "") if name == "shellToolCall" else json.dumps(ok)
            for p in re.findall(re.escape(HOME) + r"/[^\s\"'\\`]*", text):
                if not p.startswith(QUIET):
                    yield name, p.replace(HOME, "~")[:80]
            for p in TEMP.findall(text):
                q = p.replace("/private/var/", "/var/").replace("/private/tmp/", "/tmp/")
                if own and not q.startswith(own) and "xcrun_db-" not in q and q.rstrip("/") != "/var/tmp/jev-r5":
                    yield name, p[-60:]


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
        for tool, p in leaks(run / "events.jsonl", own):
            issues.add(f"LEAK {tool}: {p}")
        if cfg == "without_skill" and saw_skill_text(run / "events.jsonl"):
            issues.add("CONTENT: a tool result contained skill text")
        print(("FAIL " if issues else "ok   ") + str(run.relative_to(ws)), *sorted(issues)[:4], sep="\n     " if issues else "")
        bad += bool(issues)
    print(f"{bad} run(s) failed the audit")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
