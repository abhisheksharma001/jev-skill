#!/usr/bin/env python3
"""Minimal, dependency-free client for TypeSafe AI's Jev (POST /v1/systemone).

Standard library only, so it runs anywhere Python 3.9+ runs. Use the official
SDKs (`typesafe-sdk` for Python, `@typesafe-ai/sdk` for JS) inside real
applications; this file exists so the skill's probes, fit tests and
calibration runs work before anything is installed.

CLI:
  python3 jev_client.py models
  python3 jev_client.py ask --state state.txt --questions questions.json [--model jev-1.13.0]
      questions.json is the `questions` object of the API (name -> question).
      state may be a .txt file (sent as a string) or a .json file (sent as structured JSON).

Library:
  from jev_client import ask
  resp = ask(state, {"is_billing": {"type": "noul", "instructions": "..."}})
  resp["answers"], resp["usage"], resp["_latency_ms"], resp["_cost_usd"]

Key: read from TYPESAFE_API_KEY. Never printed, never written anywhere.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
# Pin a dated model for anything with tuned thresholds; `jev-latest` moves.
DEFAULT_MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-1.13.0")
USD_PER_M_INPUT = 0.042  # docs.typesafe.ai/models, checked 2026-09-21; output is free
RETRY_STATUSES = {408, 429, 500, 502, 503, 504}


class JevError(RuntimeError):
    pass


def _key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise JevError("TYPESAFE_API_KEY is not set")
    return key


def _request(method: str, path: str, body: dict | None = None, timeout: float = 30.0,
             retries: int = 2) -> dict:
    data = None if body is None else json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            BASE_URL + path, data=data, method=method,
            headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:2000]
            if e.code in RETRY_STATUSES and attempt < retries:
                wait = float(e.headers.get("retry-after") or 2 ** attempt)
                time.sleep(min(wait, 30))
                continue
            raise JevError(f"HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise JevError(f"network error: {e.reason}") from None
    raise JevError("unreachable")


def validate_questions(questions: dict) -> list[str]:
    """Catch the mistakes the API would reject or silently mis-answer."""
    problems = []
    if not questions:
        problems.append("no questions: the API needs at least one")
    for name, q in questions.items():
        t = q.get("type")
        instr = q.get("instructions")
        if t not in ("noul", "choice", "score"):
            problems.append(f"{name}: type must be noul, choice or score")
            continue
        if isinstance(instr, str) and not instr.strip():
            problems.append(f"{name}: empty instructions")
        crit = q.get("criteria")
        if t == "choice":
            if not isinstance(crit, dict) or len(crit) < 2:
                problems.append(f"{name}: choice needs criteria with >= 2 options")
            elif len(crit) > 255:
                problems.append(f"{name}: choice allows at most 255 options")
        if t == "score" and (not isinstance(crit, list) or len(crit) < 2):
            problems.append(f"{name}: score needs an ordered criteria list with >= 2 levels")
    return problems


def ask(state, questions: dict, model: str = DEFAULT_MODEL, timeout: float = 30.0) -> dict:
    """One call = one state + many questions (batch them; state is billed once)."""
    problems = validate_questions(questions)
    if problems:
        raise JevError("; ".join(problems))
    t0 = time.perf_counter()
    resp = _request("POST", "/v1/systemone",
                    {"state": state, "model": model, "questions": questions}, timeout)
    resp["_latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    tokens = resp.get("usage", {}).get("input_tokens", 0)
    resp["_cost_usd"] = tokens * USD_PER_M_INPUT / 1_000_000
    return resp


def models() -> dict:
    return _request("GET", "/v1/models")


def _load_state(path: str):
    text = open(path, encoding="utf-8").read()
    return json.loads(text) if path.endswith(".json") else text


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models")
    a = sub.add_parser("ask")
    a.add_argument("--state", required=True)
    a.add_argument("--questions", required=True)
    a.add_argument("--model", default=DEFAULT_MODEL)
    args = p.parse_args(argv)
    try:
        if args.cmd == "models":
            out = models()
        else:
            qs = json.load(open(args.questions, encoding="utf-8"))
            out = ask(_load_state(args.state), qs, args.model)
    except JevError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
