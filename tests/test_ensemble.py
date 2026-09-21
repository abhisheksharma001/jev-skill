"""Offline tests for ensemble.py: synthetic cached answers, no network."""
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
import ensemble  # noqa: E402


def run(args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "ensemble.py")] + args, capture_output=True, text=True)


class Binary(unittest.TestCase):
    def test_logistic_learns_sign_and_ignores_noise(self):
        rnd = random.Random(3)
        X, y = [], []
        for _ in range(200):
            t = rnd.random() < 0.5
            X.append([ensemble._logit(0.8 if t else 0.2), ensemble._logit(0.2 if t else 0.8), ensemble._logit(rnd.random())])
            y.append(int(t))
        w, _ = ensemble.fit_logistic(X, y)
        self.assertGreater(w[0], 0.3)
        self.assertLess(w[1], -0.3)
        self.assertLess(abs(w[2]), abs(w[0]) / 3)

    def test_ensemble_beats_weak_members_on_eval(self):
        rnd = random.Random(7)
        with tempfile.TemporaryDirectory() as d:
            cases, cache, q = (os.path.join(d, n) for n in ("c.jsonl", "a.jsonl", "q.json"))
            names = ["m1", "m2", "m3", "m4"]
            json.dump({n: {"type": "noul", "instructions": n} for n in names}, open(q, "w"))
            with open(cases, "w") as c, open(cache, "w") as a:
                for i in range(400):
                    t = rnd.random() < 0.5
                    ans = {n: {"type": "noul", "noul": min(0.99, max(0.01, rnd.gauss(0.62 if t else 0.38, 0.2)))} for n in names}
                    c.write(json.dumps({"id": f"e{i}", "state": "x", "labels": {"y": int(t)}}) + "\n")
                    a.write(json.dumps({"id": f"e{i}", "model": "jev-1.13.0", "input_tokens": 5, "latency_ms": 0, "answers": ans}) + "\n")
            out = os.path.join(d, "o.json")
            p = run(["--cases", cases, "--questions", q, "--target", "y", "--answers", cache, "--offline", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr)
            res = json.load(open(out))["eval"]
            self.assertGreater(res["ensemble_acc"], res["best_member_acc"])


class Choice(unittest.TestCase):
    def test_weighted_average_and_margin_table(self):
        rnd = random.Random(11)
        opts = ["a", "b", "c", "other"]
        with tempfile.TemporaryDirectory() as d:
            cases, cache, q = (os.path.join(d, n) for n in ("c.jsonl", "a.jsonl", "q.json"))
            names = ["p1", "p2", "p3"]
            json.dump({n: {"type": "choice", "criteria": {o: o for o in opts}} for n in names}, open(q, "w"))
            with open(cases, "w") as c, open(cache, "w") as a:
                for i in range(300):
                    truth = rnd.choice(opts)
                    ans = {}
                    for n in names:
                        raw = {o: rnd.random() + (0.6 if o == truth else 0) for o in opts}
                        z = sum(raw.values())
                        probs = {o: v / z for o, v in raw.items()}
                        ans[n] = {"type": "choice", "choice": max(probs, key=probs.get), "confidence": 0.5, "probabilities": probs}
                    c.write(json.dumps({"id": f"k{i}", "state": "x", "labels": {"y": truth}}) + "\n")
                    a.write(json.dumps({"id": f"k{i}", "model": "jev-1.13.0", "input_tokens": 5, "latency_ms": 0, "answers": ans}) + "\n")
            out = os.path.join(d, "o.json")
            p = run(["--cases", cases, "--questions", q, "--target", "y", "--answers", cache, "--offline", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("share answered", p.stdout)
            res = json.load(open(out))["eval"]
            self.assertGreater(res["weighted_acc"], res["best_member_acc"])

    def test_mixed_member_types_refused(self):
        with tempfile.TemporaryDirectory() as d:
            cases, cache, q = (os.path.join(d, n) for n in ("c.jsonl", "a.jsonl", "q.json"))
            json.dump({"n": {"type": "noul", "instructions": "x"}, "c": {"type": "choice", "criteria": {"a": "a", "b": "b"}}}, open(q, "w"))
            with open(cases, "w") as c, open(cache, "w") as a:
                for i in range(25):
                    c.write(json.dumps({"id": f"k{i}", "state": "x", "labels": {"y": 1}}) + "\n")
                    a.write(json.dumps({"id": f"k{i}", "model": "m", "input_tokens": 1, "latency_ms": 0, "answers": {
                        "n": {"type": "noul", "noul": 0.5}, "c": {"type": "choice", "choice": "a", "confidence": 1, "probabilities": {"a": 1, "b": 0}}}}) + "\n")
            p = run(["--cases", cases, "--questions", q, "--target", "y", "--answers", cache, "--offline"])
            self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
