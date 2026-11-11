"""S-13: default model is jev-1.14.0 everywhere, and HTTP 529 is retried.

Offline: urlopen and sleep are faked, no network, no key needed.
"""
import email.message
import io
import json
import os
import subprocess
import sys
import unittest
import urllib.error
from unittest import mock

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "skills", "jev", "scripts")
sys.path.insert(0, SCRIPTS)
import jev_client  # noqa: E402


def _http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", email.message.Message(),
                                  io.BytesIO(b"overloaded"))


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Retry529(unittest.TestCase):
    def test_529_is_retried_then_succeeds(self):
        calls = []

        def fake_urlopen(req, timeout=None):
            calls.append(1)
            if len(calls) == 1:
                raise _http_error(529)
            return _Resp({"ok": True})

        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-not-a-key"}), \
                mock.patch.object(jev_client.urllib.request, "urlopen", fake_urlopen), \
                mock.patch.object(jev_client.time, "sleep") as slept:
            out = jev_client._request("POST", "/v1/systemone", {"a": 1})
        self.assertEqual(out, {"ok": True})
        self.assertEqual(len(calls), 2)
        slept.assert_called_once()

    def test_529_gives_up_after_retries(self):
        def always_529(req, timeout=None):
            raise _http_error(529)

        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-not-a-key"}), \
                mock.patch.object(jev_client.urllib.request, "urlopen", always_529), \
                mock.patch.object(jev_client.time, "sleep"):
            with self.assertRaises(jev_client.JevError) as cm:
                jev_client._request("POST", "/v1/systemone", {}, retries=2)
        self.assertIn("529", str(cm.exception))


class DefaultModel(unittest.TestCase):
    def test_client_default_is_1_14_0(self):
        env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_DEFAULT_MODEL"}
        code = "import jev_client; print(jev_client.DEFAULT_MODEL)"
        out = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); " + code,
                              SCRIPTS], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "jev-1.14.0")

    def test_other_scripts_default_is_1_14_0(self):
        for name in ("calibrate", "ensemble", "optimize_questions"):
            with open(os.path.join(SCRIPTS, name + ".py")) as f:
                src = f.read()
            self.assertIn('"TYPESAFE_DEFAULT_MODEL", "jev-1.14.0"', src, name)
            self.assertNotIn("jev-1.13.0", src, name)


if __name__ == "__main__":
    unittest.main()
