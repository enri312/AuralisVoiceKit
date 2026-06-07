import contextlib
import importlib.util
import io
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_BATCH_STATUS = ROOT / "tools" / "release_batch_status.py"


def _load_release_batch_status():
    spec = importlib.util.spec_from_file_location("release_batch_status", RELEASE_BATCH_STATUS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseBatchStatusTests(unittest.TestCase):
    def test_report_blocks_tag_when_batch_is_not_full(self):
        module = _load_release_batch_status()

        def runner(root, args):
            if tuple(args) == ("describe", "--tags", "--abbrev=0"):
                return "v0.167.0"
            if tuple(args) == ("log", "v0.167.0..HEAD", "--oneline"):
                return "abc1234 First improvement\n"
            self.fail(f"unexpected git args: {args}")

        report = module.build_release_batch_status(ROOT, runner=runner)

        self.assertEqual(report["latest_tag"], "v0.167.0")
        self.assertEqual(report["commit_count"], 1)
        self.assertEqual(report["remaining"], 4)
        self.assertEqual(report["batch_state"], "collecting")
        self.assertEqual(report["publishable_commits_needed"], 4)
        self.assertEqual(report["next_tag_after_commit_count"], 5)
        self.assertIn("Lote en progreso", report["batch_summary_es"])
        self.assertFalse(report["ready_for_tag"])
        self.assertFalse(report["should_create_release"])
        self.assertEqual(report["compare_command"], "git log v0.167.0..HEAD --oneline")
        self.assertIn("No crear tag todavia", report["next_action_es"])
        self.assertFalse(report["policy"]["creates_github_release_each_improvement"])

    def test_report_marks_fresh_batch_after_latest_tag(self):
        module = _load_release_batch_status()

        def runner(root, args):
            if tuple(args) == ("describe", "--tags", "--abbrev=0"):
                return "v0.169.0"
            if tuple(args) == ("log", "v0.169.0..HEAD", "--oneline"):
                return ""
            self.fail(f"unexpected git args: {args}")

        report = module.build_release_batch_status(ROOT, runner=runner)

        self.assertEqual(report["latest_tag"], "v0.169.0")
        self.assertEqual(report["commit_count"], 0)
        self.assertEqual(report["remaining"], 5)
        self.assertEqual(report["batch_state"], "fresh")
        self.assertEqual(report["publishable_commits_needed"], 5)
        self.assertIn("Lote reiniciado", report["batch_summary_es"])
        self.assertFalse(report["ready_for_tag"])

    def test_report_allows_tag_when_batch_reaches_threshold(self):
        module = _load_release_batch_status()
        lines = "\n".join(f"abc123{i} Improvement {i}" for i in range(5))

        def runner(root, args):
            if tuple(args) == ("describe", "--tags", "--abbrev=0"):
                return "v0.167.0"
            if tuple(args) == ("log", "v0.167.0..HEAD", "--oneline"):
                return lines
            self.fail(f"unexpected git args: {args}")

        report = module.build_release_batch_status(ROOT, runner=runner)

        self.assertEqual(report["commit_count"], 5)
        self.assertEqual(report["remaining"], 0)
        self.assertEqual(report["batch_state"], "ready")
        self.assertEqual(report["publishable_commits_needed"], 0)
        self.assertIn("Lote listo", report["batch_summary_es"])
        self.assertTrue(report["ready_for_tag"])
        self.assertTrue(report["should_create_release"])
        self.assertIn("Ya corresponde", report["next_action_es"])

    def test_cli_fail_if_not_ready_returns_one(self):
        module = _load_release_batch_status()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--threshold", "999", "--fail-if-not-ready"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Ready for tag: false", output.getvalue())
        self.assertIn("Batch state:", output.getvalue())
        self.assertIn("Publishable commits needed:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
