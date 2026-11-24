import ast
import importlib.util
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch
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


class ScheduledCoverageCursorTests(unittest.TestCase):
    def _run(self, run_id, event, branch, started, conclusion):
        return {
            "id": run_id,
            "event": event,
            "head_branch": branch,
            "run_started_at": started,
            "created_at": started,
            "conclusion": conclusion,
        }

    @patch.object(watchdog, "request_json")
    def test_ignores_newer_manual_dispatch_and_feature_branch(self, request):
        request.return_value = ({
            "workflow_runs": [
                self._run(30, "workflow_dispatch", "feature/docs", "2026-11-04T01:00:00Z", "success"),
                self._run(29, "schedule", "main", "2026-11-03T13:00:00Z", "success"),
            ]
        }, {})
        cursor, basis = watchdog.previous_scheduled_coverage_start(
            "openAMRobot", "openamrobot-docs", "31", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-11-03T13:00:00Z")
        self.assertIn("scheduled run", basis)
        requested_url = request.call_args.args[0]
        self.assertIn("event=schedule", requested_url)
        self.assertIn("branch=main", requested_url)

    @patch.object(watchdog, "request_json")
    def test_failed_scheduled_run_reuses_last_successful_cursor(self, request):
        request.return_value = ({
            "workflow_runs": [
                self._run(30, "schedule", "main", "2026-11-05T13:00:00Z", "failure"),
                self._run(29, "schedule", "main", "2026-10-29T13:00:00Z", "success"),
            ]
        }, {})
        cursor, basis = watchdog.previous_scheduled_coverage_start(
            "openAMRobot", "openamrobot-docs", "31", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-10-29T13:00:00Z")
        self.assertIn("re-audited", basis)

    @patch.object(watchdog, "request_json")
    def test_no_success_uses_oldest_scheduled_run(self, request):
        request.return_value = ({
            "workflow_runs": [
                self._run(30, "schedule", "main", "2026-11-05T13:00:00Z", "failure"),
                self._run(29, "schedule", "main", "2026-10-29T13:00:00Z", "cancelled"),
            ]
        }, {})
        cursor, basis = watchdog.previous_scheduled_coverage_start(
            "openAMRobot", "openamrobot-docs", "31", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-10-29T13:00:00Z")
        self.assertIn("no successful", basis)

    @patch.object(watchdog, "previous_scheduled_coverage_start")
    def test_manual_explicit_since_is_honoured(self, previous):
        args = Namespace(since="2026-10-01T00:00:00Z", initial_days=7)
        cursor, basis = watchdog.resolve_audit_window(
            args, "openAMRobot", "openamrobot-docs", "42",
            "workflow_dispatch", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-10-01T00:00:00Z")
        self.assertIn("manual", basis)
        previous.assert_not_called()

    @patch.object(watchdog, "previous_scheduled_coverage_start")
    def test_scheduled_run_ignores_manual_since_input(self, previous):
        previous.return_value = (
            watchdog.parse_time("2026-10-29T13:00:00Z"),
            "most recent successful scheduled run on the default branch",
        )
        args = Namespace(since="2026-11-04T00:00:00Z", initial_days=7)
        cursor, _ = watchdog.resolve_audit_window(
            args, "openAMRobot", "openamrobot-docs", "42",
            "schedule", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-10-29T13:00:00Z")

    @patch.object(watchdog, "previous_scheduled_coverage_start")
    def test_manual_without_since_uses_clear_fallback_label(self, previous):
        args = Namespace(since=None, initial_days=5)
        cursor, basis = watchdog.resolve_audit_window(
            args, "openAMRobot", "openamrobot-docs", "42",
            "workflow_dispatch", "main", "token"
        )
        self.assertLessEqual(cursor, watchdog.utc_now())
        self.assertIn("manual-dispatch fallback", basis)
        self.assertNotIn("no prior scheduled run", basis)
        previous.assert_not_called()

    @patch.object(watchdog, "request_json")
    def test_current_run_is_excluded(self, request):
        request.return_value = ({
            "workflow_runs": [
                self._run(31, "schedule", "main", "2026-11-06T13:00:00Z", "success"),
                self._run(30, "schedule", "main", "2026-11-05T13:00:00Z", "success"),
            ]
        }, {})
        cursor, _ = watchdog.previous_scheduled_coverage_start(
            "openAMRobot", "openamrobot-docs", "31", "main", "token"
        )
        self.assertEqual(watchdog.isoformat(cursor), "2026-11-05T13:00:00Z")


if __name__ == "__main__":
    unittest.main()
