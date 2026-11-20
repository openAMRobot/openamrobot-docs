# SPDX-License-Identifier: MIT
"""Tests of scripts/digital_twin_quickstart.py: the extractor of the digital twin headless quick start."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import digital_twin_quickstart as qs  # noqa: E402

M = qs.MARKER


class ExtractTests(unittest.TestCase):
    def test_marked_blocks_in_order_and_unmarked_ignored(self):
        text = f"a\n{M}\n```bash\necho one\n```\n```bash\necho skipped\n```\n{M}\n```bash\necho two\n```\n"
        blocks = qs.extract(text)
        self.assertEqual([b for _, b in blocks], ["echo one", "echo two"])
        self.assertEqual(blocks[0][0], 3)

    def test_no_marked_block_is_an_error(self):
        with self.assertRaises(qs.QuickstartError):
            qs.extract("```bash\necho hi\n```\n")

    def test_marker_without_bash_fence_is_an_error(self):
        with self.assertRaises(qs.QuickstartError):
            qs.extract(f"{M}\n```text\necho hi\n```\n")

    def test_unclosed_fence_is_an_error(self):
        with self.assertRaises(qs.QuickstartError):
            qs.extract(f"{M}\n```bash\necho hi\n")

    def test_empty_block_is_an_error(self):
        with self.assertRaises(qs.QuickstartError):
            qs.extract(f"{M}\n```bash\n\n```\n")


class ScriptTests(unittest.TestCase):
    def run_script(self, page_text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.md"
            page.write_text(page_text, encoding="utf-8")
            out = Path(tmp) / "qs.sh"
            self.assertEqual(qs.main(["--page", str(page), "--write", str(out)]), 0)
            return subprocess.run(["bash", str(out)], capture_output=True, text=True)

    def test_failing_command_fails_the_script(self):
        result = self.run_script(f"{M}\n```bash\necho before\nfalse\necho after\n```\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("before", result.stdout)
        self.assertNotIn("after", result.stdout)

    def test_failure_inside_a_pipeline_fails_the_script(self):
        result = self.run_script(f"{M}\n```bash\nfalse | cat\necho after\n```\n")
        self.assertNotEqual(result.returncode, 0)

    def test_state_carries_across_blocks(self):
        result = self.run_script(f"{M}\n```bash\nexport X=7\nf() {{ echo f$1; }}\n```\n{M}\n```bash\nf $X\n```\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("f7", result.stdout)
        self.assertIn("all 2 blocks passed", result.stdout)


class PageTests(unittest.TestCase):
    def test_install_page_has_the_quick_start(self):
        blocks = qs.extract(qs.DEFAULT_PAGE.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(blocks), 7)
        joined = "\n".join(b for _, b in blocks)
        for needed in ("UB_SHA=", "colcon build", "setup_vcan_all.sh", "test_scn14_drive_fast"):
            self.assertIn(needed, joined)

    def test_install_page_pin_is_a_full_hash(self):
        joined = "\n".join(b for _, b in qs.extract(qs.DEFAULT_PAGE.read_text(encoding="utf-8")))
        line = next(l for l in joined.splitlines() if l.startswith("export UB_SHA="))
        sha = line.split("=", 1)[1]
        self.assertRegex(sha, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
