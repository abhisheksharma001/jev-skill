"""Offline tests for claude_code_router.py: fake urlopen, temp data dir, no network, no real key."""
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "jev", "scripts")
sys.path.insert(0, SCRIPTS)
import claude_code_router as router  # noqa: E402

FAKE_KEY = "test-key-not-real"


def wide_answer(which, acts=0.9, proc=0.9, prose=0.1, named=0.2, tier="hard", tier_p=0.8):
    """A fake request-1 reply: `which` is {skill: prob}, tier gets tier_p, rest split evenly."""
    others = [t for t in router.TIERS if t != tier]
    tier_probs = {tier: tier_p, **{t: (1 - tier_p) / len(others) for t in others}}
    top = max(which, key=which.get)
    return {"model": "jev-1.14.0", "usage": {"input_tokens": 100}, "answers": {
        "which": {"choice": top, "probabilities": which},
        "gate_acts": {"noul": acts}, "gate_procedure": {"noul": proc}, "gate_prose": {"noul": prose},
        "named": {"noul": named},
        "tier": {"choice": tier, "probabilities": tier_probs}}}


def rerank_answer(fits, pick, pick_p):
    others = [n for n in fits if n != pick]
    probs = {pick: pick_p, **{n: (1 - pick_p) / max(len(others), 1) for n in others}}
    ans = {"which": {"choice": pick, "probabilities": probs}}
    ans.update({f"fits::{n}": {"noul": f} for n, f in fits.items()})
    return {"usage": {"input_tokens": 50}, "answers": ans}


class FakeUrlopen:
    """Stands in for urllib.request.urlopen; replays canned replies and records every request."""

    def __init__(self, *replies, error=None):
        self.replies, self.error, self.requests = list(replies), error, []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        if self.error:
            raise self.error
        body = json.dumps(self.replies.pop(0)).encode()
        resp = mock.MagicMock()
        resp.read.return_value = body
        resp.__enter__.return_value = resp
        return resp


IDX = {n: {"short": f"{n} short", "full": f"{n} full", "body": f"{n} body"} for n in ("alpha", "beta", "gamma", "delta")}


class RouterCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.data = Path(tmp.name)
        for name, value in (("DATA", self.data), ("LOG_FILE", self.data / "log.jsonl"),
                            ("INDEX_FILE", self.data / "skill_index.json"), ("MODE_FILE", self.data / "mode"),
                            ("SKILLS_DIR", self.data / "skills")):
            p = mock.patch.object(router, name, value)
            p.start()
            self.addCleanup(p.stop)
        env = mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": FAKE_KEY}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("JEV_ROUTER_MODE", None)
        idx = mock.patch.object(router, "skill_index", return_value=IDX)
        idx.start()
        self.addCleanup(idx.stop)

    def patch_net(self, fake):
        p = mock.patch.object(router.urllib.request, "urlopen", fake)
        p.start()
        self.addCleanup(p.stop)
        return fake


class Redaction(unittest.TestCase):
    def test_email(self):
        out = router.redact("mail jane.doe+x@example.co.uk about it")
        self.assertIn("<email>", out)
        self.assertNotIn("example.co.uk", out)

    def test_phone(self):
        out = router.redact("call +1 (415) 555-0132 tomorrow")
        self.assertIn("<number>", out)
        self.assertNotIn("555", out)

    def test_five_plus_digit_run(self):
        out = router.redact("order 123456 and zip 90210 but room 42")
        self.assertEqual(out.count("<number>"), 2)
        self.assertIn("room 42", out)

    def test_key_like(self):
        out = router.redact("use sk-abcdef1234567890 and ghp_ABCDEFGH12345678 now")
        self.assertEqual(out.count("<key>"), 2)
        self.assertNotIn("abcdef1234567890", out)

    def test_long_opaque_token(self):
        self.assertIn("<token>", router.redact("secret " + "A1b2C3d4" * 5))

    def test_truncated_to_max_chars(self):
        self.assertEqual(len(router.redact("word " * 500)), router.MAX_CHARS)


class Skips(RouterCase):
    def test_short_prompt_makes_no_call(self):
        fake = self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        self.assertEqual(router.route("x" * (router.MIN_CHARS - 1), "on"), (None, ""))
        self.assertEqual(fake.requests, [])

    def test_slash_command_makes_no_call(self):
        fake = self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        self.assertEqual(router.route("/compact please summarise everything", "on"), (None, ""))
        self.assertEqual(fake.requests, [])

    def test_mode_off_makes_no_call(self):
        fake = self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        self.assertEqual(router.route("Build a RAG pipeline over our PDFs", "off"), (None, ""))
        self.assertEqual(fake.requests, [])
        self.assertFalse(router.LOG_FILE.exists())

    def test_no_key_makes_no_call(self):
        fake = self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        with mock.patch.object(router, "_key", return_value=""):
            self.assertEqual(router.route("Build a RAG pipeline over our PDFs", "on"), (None, ""))
        self.assertEqual(fake.requests, [])


class Mode(RouterCase):
    def test_default_is_shadow_without_file_or_env(self):
        self.assertFalse(router.MODE_FILE.exists())
        self.assertEqual(router.mode(), "shadow")

    def test_file_value_used(self):
        router.MODE_FILE.write_text("on\n")
        self.assertEqual(router.mode(), "on")

    def test_env_overrides_file(self):
        router.MODE_FILE.write_text("on\n")
        with mock.patch.dict(os.environ, {"JEV_ROUTER_MODE": "off"}):
            self.assertEqual(router.mode(), "off")

    def test_garbage_never_becomes_on(self):
        router.MODE_FILE.write_text("enabled\n")
        self.assertEqual(router.mode(), "shadow")
        with mock.patch.dict(os.environ, {"JEV_ROUTER_MODE": "yes"}):
            self.assertEqual(router.mode(), "shadow")


class Decide(RouterCase):
    def test_gate_stops_when_no_skill_wanted(self):
        fake = self.patch_net(FakeUrlopen(wide_answer({"alpha": 0.5, "beta": 0.3, "gamma": 0.2},
                                                     acts=0.0, proc=0.0, prose=1.0, named=0.1)))
        d = router.decide("explain how a hash map works", IDX)
        self.assertEqual(d["stop"], "no skill wanted")
        self.assertEqual(d["action"], 0.0)
        self.assertEqual(len(fake.requests), 1)  # no rerank request

    def test_named_tool_passes_gate_even_when_action_low(self):
        self.patch_net(FakeUrlopen(
            wide_answer({"alpha": 0.6, "beta": 0.3, "gamma": 0.1}, acts=0.0, proc=0.0, prose=1.0, named=0.5),
            rerank_answer({"alpha": 0.9, "beta": 0.1, "gamma": 0.1}, "alpha", 0.8)))
        d = router.decide("use the alpha template for this note", IDX)
        self.assertEqual(d["skill"], "alpha")

    def test_stops_when_nothing_fits(self):
        self.patch_net(FakeUrlopen(
            wide_answer({"alpha": 0.6, "beta": 0.3, "gamma": 0.1}),
            rerank_answer({"alpha": 0.29, "beta": 0.1, "gamma": 0.1}, "alpha", 0.5)))
        d = router.decide("deploy the thing to the server", IDX)
        self.assertEqual(d["stop"], "no shortlisted skill fits")
        self.assertIsNone(d["skill"])

    def test_pick_returned_and_shortlist_is_top_three(self):
        fake = self.patch_net(FakeUrlopen(
            wide_answer({"alpha": 0.4, "beta": 0.3, "gamma": 0.2, "delta": 0.1}),
            rerank_answer({"alpha": 0.9, "beta": 0.5, "gamma": 0.4}, "alpha", 0.75)))
        d = router.decide("deploy the thing to the server", IDX)
        self.assertEqual((d["skill"], d["pick_p"]), ("alpha", 0.75))
        self.assertEqual(set(d["fits"]), {"alpha", "beta", "gamma"})
        sent = json.loads(fake.requests[1].data)
        self.assertEqual(sent["model"], router.MODEL)
        self.assertNotIn("delta", json.dumps(sent["questions"]))

    def test_request_carries_key_only_in_header(self):
        fake = self.patch_net(FakeUrlopen(wide_answer({"alpha": 0.6, "beta": 0.3, "gamma": 0.1},
                                                     acts=0.0, proc=0.0, prose=1.0, named=0.0)))
        router.decide("explain how a hash map works", IDX)
        req = fake.requests[0]
        self.assertEqual(req.get_header("Authorization"), f"Bearer {FAKE_KEY}")
        self.assertNotIn(FAKE_KEY.encode(), req.data)


class Hint(unittest.TestCase):
    def d(self, **kw):
        base = {"skill": "alpha", "fits": {"alpha": 0.9, "beta": 0.2}, "pick_p": 0.8,
                "action": 0.9, "tier": "hard", "tier_p": 0.8}
        base.update(kw)
        return base

    def test_confident_pick_and_tier(self):
        h = router.hint(self.d())
        self.assertIn("`alpha`", h)
        self.assertIn("opus", h)

    def test_fits_just_under_floor_gives_no_skill_hint(self):
        h = router.hint(self.d(fits={"alpha": router.HINT_FITS_MIN - 0.01, "beta": 0.2}, tier_p=0.1))
        self.assertEqual(h, "")

    def test_pick_just_under_floor_gives_no_skill_hint(self):
        h = router.hint(self.d(pick_p=router.HINT_PICK_MIN - 0.01, tier_p=0.1))
        self.assertEqual(h, "")

    def test_exactly_at_floors_gives_hint(self):
        h = router.hint(self.d(fits={"alpha": router.HINT_FITS_MIN}, pick_p=router.HINT_PICK_MIN, tier_p=0.1))
        self.assertIn("`alpha`", h)

    def test_near_duplicates_are_all_named(self):
        h = router.hint(self.d(fits={"alpha": 0.95, "beta": 0.9}, pick_p=0.5, tier_p=0.1))
        self.assertIn("`alpha`", h)
        self.assertIn("`beta`", h)
        self.assertIn("several fit", h)

    def test_tier_hint_needs_action_and_confidence(self):
        self.assertIn("haiku", router.hint(self.d(skill=None, tier="lookup")))
        self.assertEqual(router.hint(self.d(skill=None, action=router.ACTION_MIN - 0.01)), "")
        self.assertEqual(router.hint(self.d(skill=None, tier_p=router.HINT_TIER_MIN - 0.01)), "")


class RouteAndHook(RouterCase):
    def two_replies(self):
        return FakeUrlopen(wide_answer({"alpha": 0.6, "beta": 0.3, "gamma": 0.1}),
                           rerank_answer({"alpha": 0.9, "beta": 0.1, "gamma": 0.1}, "alpha", 0.8))

    def test_sent_text_is_redacted_and_logged_without_key(self):
        fake = self.patch_net(self.two_replies())
        prompt = "Send the report, call 415 555 0132, key sk-abcdef1234567890"
        d, h = router.route(prompt, "shadow")
        self.assertEqual(h, "")  # shadow never hints
        for req in fake.requests:
            state = json.loads(req.data)["state"]["request"]
            self.assertIn("<number>", state)
            self.assertIn("<key>", state)
        logged = router.LOG_FILE.read_text()
        self.assertNotIn(FAKE_KEY, logged)
        self.assertNotIn("Authorization", logged)
        self.assertNotIn("sk-abcdef1234567890", logged)
        self.assertEqual(json.loads(logged)["mode"], "shadow")

    def test_on_mode_returns_hint(self):
        self.patch_net(self.two_replies())
        _, h = router.route("Build a RAG pipeline over our PDFs", "on")
        self.assertTrue(h.startswith("Jev router hint"))

    def run_main(self, stdin_text):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["router"]), mock.patch.object(sys, "stdin", io.StringIO(stdin_text)), \
                mock.patch.object(sys, "stdout", out):
            rc = router.main()
        return rc, out.getvalue()

    def test_hook_api_error_exits_zero_with_no_output(self):
        router.MODE_FILE.write_text("on\n")
        self.patch_net(FakeUrlopen(error=router.urllib.error.URLError("boom")))
        rc, out = self.run_main(json.dumps({"prompt": "Build a RAG pipeline over our PDFs"}))
        self.assertEqual((rc, out), (0, ""))

    def test_hook_bad_stdin_exits_zero_with_no_output(self):
        self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        self.assertEqual(self.run_main("not json{"), (0, ""))

    def test_hook_prints_hint_in_on_mode(self):
        router.MODE_FILE.write_text("on\n")
        self.patch_net(self.two_replies())
        rc, out = self.run_main(json.dumps({"prompt": "Build a RAG pipeline over our PDFs"}))
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("Jev router hint"))

    def test_hook_env_off_overrides_file_on(self):
        router.MODE_FILE.write_text("on\n")
        fake = self.patch_net(FakeUrlopen(error=AssertionError("network used")))
        with mock.patch.dict(os.environ, {"JEV_ROUTER_MODE": "off"}):
            rc, out = self.run_main(json.dumps({"prompt": "Build a RAG pipeline over our PDFs"}))
        self.assertEqual((rc, out, fake.requests), (0, "", []))


class Defaults(unittest.TestCase):
    def test_model_default_is_pinned_not_latest(self):
        env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_DEFAULT_MODEL"}
        import importlib
        with mock.patch.dict(os.environ, env, clear=True):
            fresh = importlib.reload(router)
            self.assertEqual(fresh.MODEL, "jev-1.14.0")
        importlib.reload(router)


if __name__ == "__main__":
    unittest.main()
