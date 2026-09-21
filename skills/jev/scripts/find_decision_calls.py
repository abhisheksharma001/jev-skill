#!/usr/bin/env python3
"""Find LLM calls in an existing codebase whose output is a DECISION, not text.

Those calls (classify, route, yes/no, pick-one, rate 1-5) are where Jev can
replace or pre-screen a generative model. Calls whose output is prose (write,
summarize, draft a reply) are flagged as generation and are NOT Jev candidates.

This is a heuristic ranking for a human (or agent) to review, not a verdict.
Each hit shows file:line, why it was flagged, and the likely Jev primitive.

Usage:
  python3 find_decision_calls.py <repo-path> [--json] [--min-score 2] [--context 40]
Standard library only. Skips node_modules, .git, venvs, build output.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "env", "dist", "build", ".next", "__pycache__",
             ".turbo", "coverage", "site-packages", ".mypy_cache", ".pytest_cache", "vendor", "target"}
EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rb", ".java", ".kt", ".cs", ".php", ".json", ".yaml", ".yml"}

# Where an LLM is called. Kept broad on purpose; precision comes from the signals below.
LLM_CALL = re.compile(
    r"chat\.completions\.create|responses\.create|messages\.create|generateText|generateObject|streamText|"
    r"\.invoke\(|\.ainvoke\(|ChatOpenAI|ChatAnthropic|litellm\.|completion\(|\bportkey\b|"
    r"gemini|generate_content|bedrock|converse\(|ollama|instructor\.|with_structured_output|"
    r"\"model\"\s*:\s*\"(gpt|claude|gemini|llama|mistral)|model\s*=\s*[\"'](gpt|claude|gemini|o\d)",
    re.IGNORECASE)

DECISION_SIGNALS = [
    (r"\b(classify|classification|categori[sz]e|category|label)\b", 2, "classification wording", "choice"),
    (r"\b(route|router|routing|intent|which (tool|agent|team|queue|department))\b", 2, "routing wording", "choice"),
    (r"(yes or no|yes/no|true or false|answer (only )?(with )?(yes|no|true|false))", 3, "yes/no answer requested", "noul"),
    (r"\b(is_[a-z_]+|should_[a-z_]+|has_[a-z_]+|needs_[a-z_]+)\b", 1, "boolean-named field", "noul"),
    (r"(z\.enum|Literal\[|enum\s+\w+|\"enum\"\s*:|oneOf|one of the following|respond with one of|choose (one|from))", 3, "closed set of options", "choice"),
    (r"(z\.boolean|:\s*bool\b|\"type\"\s*:\s*\"boolean\")", 2, "boolean output schema", "noul"),
    (r"(score (from|between)|rate (it |this )?(from|on a scale)|scale of \d|1-5|1 to 5|1-10|severity|priority|urgency)", 2, "rating / severity", "score"),
    (r"(max_tokens|maxTokens|max_output_tokens)\s*[:=]\s*([1-9]|[1-4]\d)\b", 3, "tiny max_tokens (short answer)", "noul/choice"),
    (r"(temperature\s*[:=]\s*0(\.0)?\b)", 1, "temperature 0 (deterministic decision)", "any"),
    (r"\b(spam|toxic|moderat|guardrail|safe|unsafe|allowed|block|flag|triage|escalat|handoff|relevan|grounded|supported)\b", 1, "gate/triage vocabulary", "noul"),
    (r"\b(sentiment|tone|emotion|satisf)\w*", 1, "sentiment-type judgement", "choice/score"),
]
GENERATION_SIGNALS = [
    (r"\b(summari[sz]e|summary|write (a|an|the)|draft|compose|rewrite|translate|generate (a|an) (reply|response|email|message)|explain)\b", 2, "text generation wording"),
    (r"\b(stream|streamText|stream=True)\b", 1, "streamed output"),
    (r"(max_tokens|maxTokens)\s*[:=]\s*([2-9]\d{2,}|\d{4,})", 1, "large max_tokens"),
]
NUMERIC_SIGNALS = re.compile(r"(how many|count of|\bsum\b|average|percent|days? (ago|since)|within \d+ (days|hours)|>=|<=|greater than|less than|\bdate\b|\bamount\b)", re.IGNORECASE)


TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?)/|\.(test|spec)\.[a-z]+$|(^|/)test_[^/]+\.py$")


def iter_files(root, include_tests=False):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if os.path.splitext(fn)[1] in EXTS:
                p = os.path.join(dirpath, fn)
                if not include_tests and TEST_FILE.search(os.path.relpath(p, root)):
                    continue
                try:
                    if os.path.getsize(p) < 2_000_000:
                        yield p
                except OSError:
                    pass


WRAPPER_DEF = re.compile(
    r"export\s+(?:async\s+)?function\s+(\w+)|export\s+const\s+(\w+)\s*=\s*(?:async\s*)?\(|"
    r"^\s*(?:async\s+)?def\s+(\w+)\s*\(|^func\s+(\w+)\s*\(", re.MULTILINE)


def find_wrappers(root, include_tests):
    """Most codebases call the provider in one helper (`complete()`, `generateCompletion()`), so the
    decision prompts live at the helper's call sites. Collect functions defined in files that call a
    provider directly; calls to them count as LLM call sites."""
    names = set()
    for path in iter_files(root, include_tests):
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if LLM_CALL.search(text):
            for m in WRAPPER_DEF.finditer(text):
                name = next(g for g in m.groups() if g)
                if len(name) > 3 and not name.startswith("_") and name not in {"main", "init", "setup"}:
                    names.add(name)
    return names


def scan(root, context, min_score, include_tests=False):
    hits = []
    wrappers = find_wrappers(root, include_tests)
    wrapper_call = re.compile(r"\b(" + "|".join(map(re.escape, sorted(wrappers))) + r")\s*\(") if wrappers else None
    for path in iter_files(root, include_tests):
        try:
            lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        seen_windows = set()
        for i, line in enumerate(lines):
            if not (LLM_CALL.search(line) or (wrapper_call and wrapper_call.search(line)
                                              and not WRAPPER_DEF.search(line))):
                continue
            lo, hi = max(0, i - context), min(len(lines), i + context)
            key = (lo // context, hi // context)
            if key in seen_windows:
                continue
            seen_windows.add(key)
            window = "\n".join(lines[lo:hi])
            score, why, prims = 0, [], []
            for pat, w, label, prim in DECISION_SIGNALS:
                if re.search(pat, window, re.IGNORECASE):
                    score += w; why.append(label); prims.append(prim)
            gen, gen_why = 0, []
            for pat, w, label in GENERATION_SIGNALS:
                if re.search(pat, window, re.IGNORECASE):
                    gen += w; gen_why.append(label)
            if score < min_score:
                continue
            verdict = "candidate" if score >= gen + 2 else ("mixed: split decision from generation" if score > 0 and gen else "weak")
            numeric = bool(NUMERIC_SIGNALS.search(window))
            hits.append({
                "file": os.path.relpath(path, root), "line": i + 1, "decision_score": score, "generation_score": gen,
                "verdict": verdict, "signals": why, "generation_signals": gen_why,
                "likely_primitive": sorted(set(prims)),
                "warning": "numbers/dates nearby: keep arithmetic and date comparison in code" if numeric else "",
                "snippet": line.strip()[:160],
            })
    hits.sort(key=lambda h: (h["verdict"] != "candidate", -(h["decision_score"] - h["generation_score"])))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-score", type=int, default=2)
    ap.add_argument("--context", type=int, default=40, help="lines before/after a call to inspect")
    ap.add_argument("--include-tests", action="store_true", help="also scan test/spec files (skipped by default)")
    a = ap.parse_args(argv)
    hits = scan(a.root, a.context, a.min_score, a.include_tests)
    if a.json:
        print(json.dumps(hits, indent=2))
        return 0
    if not hits:
        print("No decision-shaped LLM calls found. Either the codebase has none, or the LLM calls use a client this "
              "scanner does not recognise: grep for your provider's call name and review by hand.")
        return 0
    print(f"{len(hits)} LLM call sites with decision signals (review each; this is a ranking, not a verdict)\n")
    for h in hits:
        print(f"{h['file']}:{h['line']}  [{h['verdict']}] decision={h['decision_score']} generation={h['generation_score']}"
              f"  -> {', '.join(h['likely_primitive'])}")
        print(f"    signals: {', '.join(h['signals'])}" + (f" | generation: {', '.join(h['generation_signals'])}" if h['generation_signals'] else ""))
        if h["warning"]:
            print(f"    ! {h['warning']}")
        print(f"    {h['snippet']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
