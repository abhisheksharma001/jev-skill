"""Offline tests for the bundled scripts. No network, no key."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "jev", "scripts")
sys.path.insert(0, SCRIPTS)

import calibrate  # noqa: E402
import find_decision_calls  # noqa: E402
import fit_check  # noqa: E402
import jev_client  # noqa: E402

GO = {k: False for k in fit_check.QUESTIONS}
GO.update(output_is_decision=True, text_input=True, fits_state_budget=True, high_volume=True,
          can_send_data=True, has_labels=True, incumbent_exists=True)


class FitCheck(unittest.TestCase):
    def test_go(self):
        self.assertEqual(fit_check.verdict(GO)[0], 0)

    def test_generation_is_no_go(self):
        self.assertEqual(fit_check.verdict({**GO, "output_is_decision": False})[0], 3)

    def test_code_wins_over_jev(self):
        self.assertEqual(fit_check.verdict({**GO, "code_can_decide": True})[0], 3)

    def test_blocked_data_is_no_go(self):
        self.assertEqual(fit_check.verdict({**GO, "can_send_data": False})[0], 3)

    def test_math_needs_guards(self):
        code, _, why, patterns = fit_check.verdict({**GO, "needs_math_dates_counting": True})
        self.assertEqual(code, 4)
        self.assertIn("precompute-in-code", patterns)

    def test_cli_rejects_missing_answers(self):
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fit_check.py"), "--answers", "-"],
                           input="{}", text=True, capture_output=True)
        self.assertEqual(p.returncode, 1)


class Scanner(unittest.TestCase):
    def setUp(self):
        self.hits = find_decision_calls.scan(os.path.join(ROOT, "tests", "fixtures", "support-bot"), 40, 2)
        self.by_file = {h["file"]: h for h in self.hits}

    def test_finds_wrapped_decision_calls(self):
        for f in ("src/classify-ticket.ts", "src/should-escalate.ts", "src/refund-eligibility.ts"):
            self.assertEqual(self.by_file[f]["verdict"], "candidate", f)

    def test_marks_grader_as_mixed(self):
        self.assertTrue(self.by_file["workers/qa-sampler.ts"]["verdict"].startswith("mixed"))

    def test_skips_generation_and_rules(self):
        self.assertNotIn("src/draft-reply.ts", self.by_file)
        self.assertNotIn("src/route-to-team.ts", self.by_file)

    def test_warns_on_numbers_only_where_present(self):
        self.assertTrue(self.by_file["src/refund-eligibility.ts"]["warning"])
        self.assertFalse(self.by_file["src/should-escalate.ts"]["warning"])


class Client(unittest.TestCase):
    def test_validation(self):
        bad = {"a": {"type": "choice", "criteria": {"only": "one"}}, "b": {"type": "score", "criteria": ["x"]},
               "c": {"type": "nope"}, "d": {"type": "noul", "instructions": "  "}}
        self.assertEqual(len(jev_client.validate_questions(bad)), 4)
        self.assertEqual(jev_client.validate_questions({"ok": {"type": "noul", "instructions": "x"}}), [])

    def test_no_key_fails_loudly(self):
        old = os.environ.pop("TYPESAFE_API_KEY", None)
        try:
            with self.assertRaises(jev_client.JevError):
                jev_client.ask("s", {"q": {"type": "noul", "instructions": "x"}})
        finally:
            if old:
                os.environ["TYPESAFE_API_KEY"] = old


class Calibrate(unittest.TestCase):
    def test_split_is_deterministic(self):
        self.assertEqual(calibrate.split_of("case-1", 0.3), calibrate.split_of("case-1", 0.3))

    def test_cost_moves_threshold(self):
        train = [(0.2, False), (0.3, False), (0.4, True), (0.6, False), (0.7, True), (0.9, True)]
        miss_heavy = calibrate.fit_noul(train, {"fn": 10, "fp": 1})
        alarm_heavy = calibrate.fit_noul(train, {"fn": 1, "fp": 10})
        self.assertLess(miss_heavy, alarm_heavy)

    def test_band_meets_on_clean_data_and_opens_on_noisy(self):
        clean = [(0.05, False)] * 10 + [(0.95, True)] * 10
        low, high = calibrate.fit_band(clean)
        self.assertEqual(low, high)
        noisy = clean + [(0.5, True), (0.5, False), (0.45, True), (0.55, False)]
        low, high = calibrate.fit_band(noisy)
        self.assertLess(low, 0.45)
        self.assertGreater(high, 0.55)

    def test_offline_report_runs(self):
        with tempfile.TemporaryDirectory() as d:
            cases, cache = os.path.join(d, "c.jsonl"), os.path.join(d, "a.jsonl")
            with open(cases, "w") as c, open(cache, "w") as a:
                for i in range(40):
                    y = i % 2
                    c.write(json.dumps({"id": f"k{i}", "state": "x", "labels": {"q": y}}) + "\n")
                    a.write(json.dumps({"id": f"k{i}", "model": "jev-1.13.0", "input_tokens": 10, "latency_ms": 0,
                                        "answers": {"q": {"type": "noul", "noul": 0.9 if y else 0.1}}}) + "\n")
            q = os.path.join(d, "q.json")
            json.dump({"q": {"type": "noul", "instructions": "x"}}, open(q, "w"))
            out = os.path.join(d, "t.json")
            p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "calibrate.py"), "--cases", cases, "--questions", q,
                                "--answers", cache, "--offline", "--band", "--out", out], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.load(open(out))["questions"]["q"]["eval"]["fn"], 0)


if __name__ == "__main__":
    unittest.main()
