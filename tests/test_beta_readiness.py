import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BETA_READINESS = ROOT / "tools" / "beta_readiness.py"


def _load_beta_readiness():
    spec = importlib.util.spec_from_file_location("beta_readiness", BETA_READINESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaReadinessTests(unittest.TestCase):
    def test_report_keeps_beta_blocked_until_real_pilots_exist(self):
        module = _load_beta_readiness()

        report = module.build_beta_readiness_report(ROOT)
        checks = {check["name"]: check for check in report["checks"]}

        self.assertEqual(report["status"], "pilot")
        self.assertFalse(report["ready_for_beta"])
        self.assertTrue(checks["stability_gate_pilot"]["ok"])
        self.assertTrue(checks["windows_wasapi_capture"]["ok"])
        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertFalse(checks["macos_capture"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])
        self.assertIn("windows-wasapi-sample-rate", {issue["id"] for issue in report["known_issues"]})

    def test_cli_json_does_not_fail_by_default(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--json"])
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["ready_for_beta"])
        self.assertIn("system_output_audible", payload["blockers"])

    def test_cli_can_fail_on_beta_blockers(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--json", "--fail-on-blockers"])

        self.assertEqual(exit_code, 1)

    def test_writes_markdown_checklist(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "BETA_CHECKLIST.md"
            exit_code = module.main(["--root", str(ROOT), "--output", str(output_path)])
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Checklist de beta", content)
        self.assertIn("Bloqueadores para beta", content)
        self.assertIn("real_transcription_quality", content)


if __name__ == "__main__":
    unittest.main()
