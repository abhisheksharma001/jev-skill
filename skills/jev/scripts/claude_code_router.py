#!/usr/bin/env python3
"""Jev skill + helper-tier router for Claude Code (UserPromptSubmit hook). Standard library only.

Method follows TypeSafe's skill-suggestion cookbook (docs.typesafe.ai/cookbooks/skill_suggestion,
read 2026-11-11) and the Companion Noul pattern (docs.typesafe.ai/patterns/companion-noul):

  Request 1 (wide, every prompt that passes the local filters)
    which      Choice over every skill (short descriptions). No `none` option: a `none`
               option competes with real options for probability.
    gate_*     Nouls: is a skill wanted at all? (acts on the user's system / follows a documented
               procedure / prose suffices, inverted) and `named` (asks for a named tool or method).
    tier       Choice: lookup / everyday / hard  -> haiku / sonnet / opus helper agents.
  Request 2 (rerank, only when a skill is wanted)
    which      Choice over the top 3, with full descriptions and a SKILL.md excerpt.
    fits::<n>  One Noul per candidate: does it do the specific thing asked? (companion Nouls)

Modes (env JEV_ROUTER_MODE, else file `mode` in the data dir): off (sends nothing) | shadow (log
only, default) | on (log + one-line hint into Claude's context). A missing file, an empty value or
anything unrecognised means shadow, never on. The hook never blocks a prompt: any error exits 0
silently.

Privacy: only the first MAX_CHARS characters are sent, after emails, phone numbers, long digit
runs and key-like strings are replaced. Slash commands and very short replies are not sent.

Install: see references/claude-code-router.md. Data dir: $JEV_ROUTER_HOME or ~/.claude/hooks/jev-router.
Skills:  $JEV_ROUTER_SKILLS or ~/.claude/skills.  Key: $TYPESAFE_API_KEY (never logged or printed).
Test:    python3 claude_code_router.py --test "your prompt"   (sends one real request, even if mode is off)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(os.environ.get("JEV_ROUTER_HOME", Path.home() / ".claude" / "hooks" / "jev-router"))
SKILLS_DIR = Path(os.environ.get("JEV_ROUTER_SKILLS", Path.home() / ".claude" / "skills"))
INDEX_FILE = DATA / "skill_index.json"
LOG_FILE = DATA / "log.jsonl"
MODE_FILE = DATA / "mode"
VERSION = "v2"

MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-1.14.0")  # pinned dated id, never jev-latest; recalibrate when it changes
URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai") + "/v1/systemone"
TIMEOUT_S = 2.0                # per request; two requests must fit the hook's 5 s timeout
MAX_CHARS = 300
MIN_CHARS = 15
SHORT_DESC = 220               # wide-rank criteria
FULL_DESC = 600                # rerank criteria
BODY_CHARS = 600               # rerank SKILL.md excerpt (cookbook allows up to 1600)
SHORTLIST = 3

# Cookbook gates (request 1) and fit floor (request 2).
ACTION_MIN = 0.30
NAMED_MIN = 0.50
FITS_MIN = 0.30
# Stricter bar for injecting a hint in "on" mode. Placeholders until calibrated on labelled logs.
HINT_FITS_MIN = 0.70
HINT_PICK_MIN = 0.60
HINT_TIER_MIN = 0.60

TIERS = {
    "lookup": "Only reading, searching, summarising or pulling facts out of files or output, or one mechanical edit. No design and no judgement call.",
    "everyday": "Ordinary coding or file edits, explaining something, or fixing a bug whose cause the message already shows.",
    "hard": "Designing a new system, debugging with no visible cause, choosing between options with trade-offs, or writing a prompt, rule or guard that must be right.",
}
TIER_HINT = os.environ.get("JEV_ROUTER_TIER", "").strip().lower() == "on"  # zero-shot tier hint: log-only unless opted in
TIER_TO_MODEL = {"lookup": "haiku", "everyday": "sonnet", "hard": "opus"}


# ---------- key ----------
def _key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key
    # Hooks may not load the shell profile; fall back to an export line in ~/.zshrc or ~/.bashrc.
    for rc in (".zshrc", ".bashrc"):
        try:
            for line in (Path.home() / rc).read_text().splitlines():
                m = re.match(r"\s*export\s+TYPESAFE_API_KEY=(['\"]?)(\S+?)\1\s*$", line)
                if m:
                    return m.group(2)
        except OSError:
            pass
    return ""


# ---------- redaction ----------
_REDACTIONS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]*"), "<token>"),  # JWT
    (re.compile(r"\b(sk|pk|ghp|gho|xox[bp]|AKIA)[-_A-Za-z0-9]{8,}\b"), "<key>"),
    (re.compile(r"\b[A-Za-z0-9_-]{32,}\b"), "<token>"),
    (re.compile(r"\+?\d[\d\s().-]{7,}\d"), "<number>"),
    (re.compile(r"\b\d{5,}\b"), "<number>"),
]


def redact_all(text: str) -> str:
    """Redact the whole text. Never cut before redacting: a cut can split a key below the token length."""
    for pat, repl in _REDACTIONS:
        text = pat.sub(repl, text)
    return text


def redact(text: str) -> str:
    return redact_all(text)[:MAX_CHARS]


# ---------- skill index ----------
def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    out, key, buf = {}, None, []
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key:
                out[key] = " ".join(buf).strip()
            key, val = m.group(1), m.group(2).strip()
            buf = [] if val in (">", "|", ">-", "|-") else [val]
        elif key:
            buf.append(line.strip())
    if key:
        out[key] = " ".join(buf).strip()
    fm = {k: v.strip().strip('"').strip("'") for k, v in out.items()}
    return fm, text[end + 4:]


def skill_index() -> dict:
    """{folder_name: {short, full, body}}; rebuilt when any SKILL.md is newer than the cache."""
    files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    newest = max((f.stat().st_mtime for f in files), default=0)
    if INDEX_FILE.exists() and INDEX_FILE.stat().st_mtime >= newest:
        try:
            idx = json.loads(INDEX_FILE.read_text())
            if idx and isinstance(next(iter(idx.values())), dict):
                return idx
        except ValueError:
            pass
    idx = {}
    for f in files:
        try:
            fm, body = _split_frontmatter(f.read_text(errors="replace"))
        except OSError:
            continue
        desc = fm.get("description", "")
        if not desc:
            continue
        desc = redact_all(desc)
        body = redact_all(re.sub(r"\s+", " ", body).strip()[: BODY_CHARS * 4])[:BODY_CHARS]
        idx[f.parent.name] = {"short": desc[:SHORT_DESC], "full": desc[:FULL_DESC], "body": body}
    DATA.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(idx, indent=1, sort_keys=True))
    return idx


# ---------- Jev ----------
def _call(state: dict, questions: dict) -> dict:
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        resp = json.loads(r.read().decode())
    resp["_ms"] = round((time.perf_counter() - t0) * 1000)
    return resp


def wide_questions(idx: dict) -> dict:
    return {
        "which": {"type": "choice",
                  "instructions": "Which of these skills, if any, is the right one to load to help with the user's latest `request`?",
                  "criteria": {n: v["short"] for n, v in idx.items()}},
        "gate_acts": {"type": "noul",
                      "instructions": "Is the assistant being asked to act on the user's files, accounts, devices, or online services, rather than only to explain or advise?"},
        "gate_procedure": {"type": "noul",
                           "instructions": "Would a careful expert answering this consult a specific documented procedure or set of commands, rather than answering from general understanding?"},
        "gate_prose": {"type": "noul",
                       "instructions": "Could a knowledgeable generalist fully satisfy this request in prose, with no tools, no documentation, and no access to the user's files or accounts?"},
        "named": {"type": "noul",
                  "instructions": "Does the request ask for a specific named tool, format, template, or method to be used, rather than for general help?"},
        "tier": {"type": "choice",
                 "instructions": "How much reasoning does the work in the `request` need?",
                 "criteria": TIERS},
    }


def rerank_questions(idx: dict, names: list[str]) -> dict:
    qs = {"which": {"type": "choice",
                    "instructions": ("Exactly one of these skills is the right one to load for the user's latest `request`. "
                                     "Which one? Read what each actually does, not just its name."),
                    "criteria": {n: f"{idx[n]['full']} — {idx[n]['body']}" for n in names}}}
    for n in names:
        qs[f"fits::{n}"] = {"type": "noul",
                            "instructions": (f"Does the skill '{n}' do the specific thing the user's `request` asks for? "
                                             f"It is described as: {idx[n]['full']}")}
    return qs


def _ranked(probs: dict) -> list[tuple[str, float]]:
    return sorted(probs.items(), key=lambda kv: kv[1], reverse=True)


def decide(request_text: str, idx: dict) -> dict:
    state = {"request": request_text, "recent_context": ""}
    r1 = _call(state, wide_questions(idx))
    a = r1["answers"]
    action = (a["gate_acts"]["noul"] + a["gate_procedure"]["noul"] + (1 - a["gate_prose"]["noul"])) / 3
    named = a["named"]["noul"]
    wide = _ranked(a["which"]["probabilities"])
    tier, tier_p = _ranked(a["tier"]["probabilities"])[0]
    out = {"v": VERSION, "action": round(action, 3), "named": round(named, 3),
           "wide_top": [[n, round(p, 3)] for n, p in wide[:SHORTLIST]],
           "tier": tier, "tier_p": round(tier_p, 3),
           "skill": None, "pick_p": None, "fits": None,
           "tokens": r1.get("usage", {}).get("input_tokens", 0), "ms": r1["_ms"], "model": r1.get("model")}
    if action < ACTION_MIN and named < NAMED_MIN:
        out["stop"] = "no skill wanted"
        return out
    names = [n for n, _ in wide[:SHORTLIST]]
    r2 = _call(state, rerank_questions(idx, names))
    b = r2["answers"]
    fits = {n: round(b[f"fits::{n}"]["noul"], 3) for n in names}
    out.update(fits=fits, tokens=out["tokens"] + r2.get("usage", {}).get("input_tokens", 0),
               ms=out["ms"] + r2["_ms"])
    if max(fits.values()) < FITS_MIN:
        out["stop"] = "no shortlisted skill fits"
        return out
    pick = b["which"]["choice"]
    out.update(skill=pick, pick_p=round(b["which"]["probabilities"][pick], 3))
    return out


def hint(d: dict) -> str:
    parts = []
    if d.get("skill"):
        fitting = [n for n, f in sorted(d["fits"].items(), key=lambda kv: -kv[1]) if f >= HINT_FITS_MIN]
        if d["fits"][d["skill"]] >= HINT_FITS_MIN and d["pick_p"] >= HINT_PICK_MIN:
            parts.append(f"suggested skill `{d['skill']}` (fits={d['fits'][d['skill']]}, pick={d['pick_p']})")
        elif len(fitting) >= 2:
            # Near-duplicate skills: each fits, so the rerank Choice splits between them. Name them all.
            parts.append("suggested skills " + " or ".join(f"`{n}`" for n in fitting) + " (several fit)")
    if TIER_HINT and d.get("action", 0) >= ACTION_MIN and d["tier_p"] >= HINT_TIER_MIN:
        parts.append(f"helper-agent tier {TIER_TO_MODEL[d['tier']]} (p={d['tier_p']})")
    if not parts:
        return ""
    return "Jev router hint (cheap classifier, may be wrong; your own judgement wins): " + "; ".join(parts) + "."


def mode() -> str:
    m = os.environ.get("JEV_ROUTER_MODE", "").strip().lower()
    if not m:
        try:
            m = MODE_FILE.read_text().strip().lower()
        except OSError:
            m = "shadow"
    return m if m in ("off", "shadow", "on") else "shadow"


def route(prompt: str, current_mode: str) -> tuple[dict | None, str]:
    p = prompt.strip()
    if current_mode == "off" or len(p) < MIN_CHARS or p.startswith("/") or not _key():
        return None, ""
    sent = redact(p)
    d = decide(sent, skill_index())
    d.update(ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"), mode=current_mode, sent=sent)
    DATA.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(d) + "\n")
    return d, (hint(d) if current_mode in ("on", "test") else "")


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        d, h = route(" ".join(sys.argv[2:]), "test")
        print(json.dumps(d, indent=1))
        print("hint:", h or "(none)")
        return 0
    try:
        data = json.loads(sys.stdin.read() or "{}")
        _, h = route(data.get("prompt", ""), mode())
        if h:
            print(h)  # UserPromptSubmit: stdout is added to Claude's context
    except Exception:
        pass  # never block or break the user's prompt
    return 0


if __name__ == "__main__":
    sys.exit(main())
