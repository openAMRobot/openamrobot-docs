import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "documentation_watchdog.py"
spec = importlib.util.spec_from_file_location("documentation_watchdog", SCRIPT)
watchdog = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(watchdog)


class RepositoryMappingTests(unittest.TestCase):
    def test_reads_existing_mapping_without_importing_hook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "hooks").mkdir()
            (root / "hooks" / "page_context.py").write_text(
                'REPOSITORIES = {"foundations/": "openamr-platform-sw", '
                '"reference/openamr-platform-sw/": "openamr-platform-sw", '
                '"use/": "openamrobot-ui"}\n'
                'raise RuntimeError("must not execute hook")\n',
                encoding="utf-8",
            )
            self.assertEqual(
                watchdog.load_repository_mapping(root),
                {
                    "openamr-platform-sw": ["foundations/", "reference/openamr-platform-sw/"],
                    "openamrobot-ui": ["use/"],
                },
            )

    def test_rejects_missing_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "hooks").mkdir()
            (root / "hooks" / "page_context.py").write_text("PATHS = {}\n", encoding="utf-8")
            with self.assertRaises(watchdog.AuditError):
                watchdog.load_repository_mapping(root)

    def test_pages_for_prefixes_lists_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs" / "foundations" / "navigation").mkdir(parents=True)
            (root / "docs" / "foundations" / "navigation" / "index.md").write_text("# Navigation\n")
            (root / "docs" / "foundations" / "navigation" / "slam.md").write_text("# SLAM\n")
            result = watchdog.pages_for_prefixes(root, ["foundations/navigation/"])
            self.assertEqual(result, [
                "docs/foundations/navigation/index.md",
                "docs/foundations/navigation/slam.md",
            ])


class ReportTests(unittest.TestCase):
    def test_report_labels_candidate_pages_as_review_not_defects(self):
        report = {
            "generated_at": "2026-10-24T00:00:00Z",
            "since": "2026-10-17T00:00:00Z",
            "window_basis": "test",
            "repositories_checked": 1,
            "repositories_with_errors": 0,
            "total_commits": 1,
            "total_candidate_pages": 1,
            "repositories": [{
                "repository": "openamr-platform-sw",
                "doc_prefixes": ["foundations/"],
                "candidate_pages": ["docs/foundations/navigation/index.md"],
                "commits": [{
                    "short_sha": "123456789abc", "url": "https://example.test/commit/123",
                    "message": "Update navigation", "date": "2026-10-23T10:00:00Z",
                    "files": ["config/nav.yaml"], "files_truncated": False,
                }],
                "head_sha": "123456789abcdef", "error": None,
            }],
        }
        output = watchdog.markdown_report(report)
        self.assertIn("Potential documentation review candidates", output)
        self.assertIn("review candidates", output.lower())
        self.assertIn("not proof that documentation is incorrect", output)
        self.assertIn("config/nav.yaml", output)


if __name__ == "__main__":
    unittest.main()
