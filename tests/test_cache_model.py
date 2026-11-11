"""S-22: a cache of answers from one Jev model must not silently feed a run on another. Offline, no key."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "jev", "scripts")
sys.path.insert(0, SCRIPTS)
import optimize_questions as oq  # noqa: E402

OLD, NEW = "jev-1.13.0", "jev-1.14.0"
Q = {"q": {"type": "noul", "instructions": "x"}}


def run(script, args):
    env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_DEFAULT_MODEL"}
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + args, capture_output=True, text=True, env=env)


def write(d, cache_model, n=40):
    """cases + questions + a cache (by explicit path and in the optimize cache dir) from cache_model."""
    cases, q = os.path.join(d, "c.jsonl"), os.path.join(d, "q.json")
    cache_dir = os.path.join(d, "cache")
    os.makedirs(cache_dir)
    json.dump(Q, open(q, "w"))
    cache = os.path.join(d, "a.jsonl")
    opt_cache = os.path.join(cache_dir, oq.qhash(Q) + ".cache.jsonl")
    with open(cases, "w") as c, open(cache, "w") as a, open(opt_cache, "w") as o:
        for i in range(n):
            y = i % 2
            c.write(json.dumps({"id": f"k{i}", "state": "x", "labels": {"q": y}}) + "\n")
            row = json.dumps({"id": f"k{i}", "model": cache_model, "input_tokens": 1, "latency_ms": 0,
                              "answers": {"q": {"type": "noul", "noul": 0.9 if y else 0.1}}}) + "\n"
            a.write(row)
            o.write(row)
    return cases, q, cache, cache_dir


class CacheModel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def calls(self, cache_model, extra, sub_name):
        """The three scripts that reuse the cache, each as (script, argv)."""
        sub = os.path.join(self.d, sub_name)
        os.makedirs(sub)
        cases, q, cache, cache_dir = write(sub, cache_model)

        def out(n):
            return os.path.join(sub, n)

        return [
            ("calibrate.py", ["--cases", cases, "--questions", q, "--answers", cache, "--offline",
                              "--out", out("t.json")] + extra),
            ("ensemble.py", ["--cases", cases, "--questions", q, "--target", "q", "--answers", cache, "--offline",
                             "--out", out("e.json")] + extra),
            ("optimize_questions.py", ["misses", "--cases", cases, "--questions", q, "--cache-dir", cache_dir,
                                       "--offline", "--out", out("p.json")] + extra),
        ]

    def test_mismatch_exits_nonzero_naming_both_models(self):
        for script, argv in self.calls(OLD, ["--model", NEW], "mismatch"):
            with self.subTest(script=script):
                p = run(script, argv)
                self.assertNotEqual(p.returncode, 0, p.stdout)
                self.assertIn(OLD, p.stderr)
                self.assertIn(NEW, p.stderr)
                self.assertIn("--allow-model-mix", p.stderr)

    def test_matching_models_behave_as_before(self):
        for script, argv in self.calls(NEW, ["--model", NEW], "match"):
            with self.subTest(script=script):
                p = run(script, argv)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertNotIn("WARNING", p.stderr)

    def test_allow_model_mix_proceeds_with_warning(self):
        for script, argv in self.calls(OLD, ["--model", NEW, "--allow-model-mix"], "mix"):
            with self.subTest(script=script):
                p = run(script, argv)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn("WARNING", p.stderr)
                self.assertIn(OLD, p.stderr)
                self.assertIn(NEW, p.stderr)

    def test_env_default_is_not_a_refusal(self):
        """TYPESAFE_DEFAULT_MODEL is a standing default: an old cache warns, it does not stop the run."""
        for script, argv in self.calls(OLD, [], "envdefault"):
            with self.subTest(script=script):
                env = dict(os.environ, TYPESAFE_DEFAULT_MODEL=NEW)
                p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + argv,
                                   capture_output=True, text=True, env=env)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn("WARNING", p.stderr)

    def test_unnamed_default_reuses_cache_model(self):
        """No --model: the run keeps the cache's own model, so the cache never becomes mixed."""
        import calibrate
        sub = os.path.join(self.d, "reuse")
        os.makedirs(sub)
        cases, _, cache, _ = write(sub, OLD, n=4)
        rows = [json.loads(l) for l in open(cases)]
        rows.append({"id": "new1", "state": "x", "labels": {"q": 1}})
        fake = lambda state, questions, model: {"model": model, "answers": {"q": {"type": "noul", "noul": 0.9}},
                                                "usage": {"input_tokens": 1}, "_latency_ms": 0}
        import jev_client
        orig = jev_client.ask
        jev_client.ask = fake
        try:
            calibrate.get_answers(rows, Q, cache, False, NEW, explicit=False)
        finally:
            jev_client.ask = orig
        models = {json.loads(l)["model"] for l in open(cache)}
        self.assertEqual(models, {OLD})

    def test_unnamed_default_model_warns_but_proceeds(self):
        """No --model and no env: the built-in default was never asked for, so an old cache is reported, not refused."""
        for script, argv in self.calls(OLD, [], "default"):
            with self.subTest(script=script):
                p = run(script, argv)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn("WARNING", p.stderr)


if __name__ == "__main__":
    unittest.main()
