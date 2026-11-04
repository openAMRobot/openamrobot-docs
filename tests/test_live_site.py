"""Offline regression tests for the post-deployment live-site smoke script.

Uses a fake curl binary; no network or GitHub Pages deployment is performed.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_live_site.sh"
FAKE_CURL = r'''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

args = sys.argv[1:]
if "--head" in args:
    if os.getenv("MOCK_HTTP") == "invalid":
        print("HTTP/1.1 200 OK")
    else:
        print("HTTP/1.1 301 Moved Permanently")
        print("location: https://docs.openamrobot.ai/")
    sys.exit(0)
if "-o" not in args:
    # Regression: a curl | grep -q pipeline can report exit 23 on SIGPIPE.
    sys.exit(23)
path = urlparse(next(x for x in args if x.startswith("https://"))).path
if path == os.getenv("MOCK_FAIL_PATH"):
    sys.exit(22)
body = {
    "/": "Build robots. Train them for real work.\n",
    "/start-here/": "Start with the task in front of you\n",
    "/paths/": "Domain Expert\n",
    "/reference/": "API reference\n",
    "/robots.txt": "User-agent: *\n",
    "/sitemap.xml": "<urlset/>\n",
    "/llms.txt": "Machine-readable docs\n",
}.get(path)
if body is None:
    sys.exit(22)
if os.getenv("MOCK_MISSING_TEXT") == path:
    body = "expected text missing\n"
Path(args[args.index("-o") + 1]).write_text(body)
'''


class LiveSiteSmokeTest(unittest.TestCase):
    def run_checker(self, **overrides):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "curl"
            executable.write_text(FAKE_CURL, encoding="utf-8")
            executable.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = folder + os.pathsep + env.get("PATH", "")
            env.update(overrides)
            return subprocess.run(
                ["bash", str(CHECKER), "https://docs.openamrobot.ai"],
                capture_output=True, text=True, env=env, check=False,
            )

    def test_downloaded_pages_pass_without_pipe_sigpipe(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Live documentation smoke test passed", result.stdout)

    def test_required_phrase_missing_fails(self):
        result = self.run_checker(MOCK_MISSING_TEXT="/start-here/")
        self.assertNotEqual(result.returncode, 0)

    def test_http_redirect_must_be_permanent(self):
        result = self.run_checker(MOCK_HTTP="invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not redirect permanently", result.stdout)

    def test_missing_page_fails_curl(self):
        result = self.run_checker(MOCK_FAIL_PATH="/sitemap.xml")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
