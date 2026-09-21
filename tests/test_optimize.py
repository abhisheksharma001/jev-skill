"""Offline tests for optimize_questions.py. Caches are pre-seeded by question hash, so no network."""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "jev", "scripts")
sys.path.insert(0, SCRIPTS)
import optimize_questions as oq  # noqa: E402
from calibrate import split_of  # noqa: E402


def seed(d, questions, quality, n=200):
    """quality = how far apart yes and no answers sit; higher is a better question."""
    rnd = random.Random(5)
    cache_dir = os.path.join(d, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, oq.qhash(questions) + ".cache.jsonl"), "w") as f:
        for i in range(n):
            t = i % 2
            p = min(0.99, max(0.01, rnd.gauss(0.5 + quality if t else 0.5 - quality, 0.15)))
            f.write(json.dumps({"id": f"c{i}", "model": "jev-1.13.0", "input_tokens": 1, "latency_ms": 0,
                                "answers": {"q": {"type": "noul", "noul": p}}}) + "\n")
    return cache_dir


def write_cases(d, n=200):
    path = os.path.join(d, "cases.jsonl")
    with open(path, "w") as f:
        for i in range(n):
            f.write(json.dumps({"id": f"c{i}", "state": f"state-{i}", "labels": {"q": i % 2}}) + "\n")
    return path


def run(args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "optimize_questions.py")] + args, capture_output=True, text=True)


class Optimize(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.cases = write_cases(self.d)
        self.base = {"q": {"type": "noul", "instructions": "vague"}}
        self.good = {"q": {"type": "noul", "instructions": "precise", "criteria": {"true": "a", "false": "b"}}}
        self.bad = {"q": {"type": "noul", "instructions": "worse"}}
        self.cache = seed(self.d, self.base, 0.12)
        seed(self.d, self.good, 0.35)
        seed(self.d, self.bad, 0.03)
        for name, q in (("base", self.base), ("good", self.good), ("bad", self.bad)):
            json.dump(q, open(os.path.join(self.d, name + ".json"), "w"))

    def tearDown(self):
        self.tmp.cleanup()

    def p(self, name):
        return os.path.join(self.d, name)

    def test_packet_never_contains_eval_cases(self):
        r = run(["misses", "--cases", self.cases, "--questions", self.p("base.json"), "--cache-dir", self.cache,
                 "--offline", "--out", self.p("packet.json")])
        self.assertEqual(r.returncode, 0, r.stderr)
        q = json.load(open(self.p("packet.json")))["questions"]["q"]
        shown = [e["id"] for k in ("false_alarms", "misses", "right_but_shaky") for e in q[k]]
        self.assertTrue(shown)
        self.assertTrue(all(split_of(i, 0.3) == "train" for i in shown))

    def test_better_candidate_is_accepted(self):
        r = run(["compare", "--cases", self.cases, "--baseline", self.p("base.json"), "--candidate", self.p("good.json"),
                 "--cache-dir", self.cache, "--offline", "--out", self.p("acc.json")])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.load(open(self.p("acc.json")))["q"]["instructions"], "precise")

    def test_worse_candidate_is_rejected(self):
        r = run(["compare", "--cases", self.cases, "--baseline", self.p("base.json"), "--candidate", self.p("bad.json"),
                 "--cache-dir", self.cache, "--offline", "--out", self.p("acc.json")])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.load(open(self.p("acc.json")))["q"]["instructions"], "vague")


if __name__ == "__main__":
    unittest.main()
