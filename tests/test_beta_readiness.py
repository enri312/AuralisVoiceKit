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

    def test_evidence_json_can_close_beta_blockers(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "hardware_capture_tested": True,
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "sounddevice",
                    "hardware_capture_tested": True,
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {
                        "enabled": True,
                        "passed": True,
                        "min_word_accuracy": 0.75,
                        "word_accuracy": 0.92,
                    },
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_root])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertTrue(report["ready_for_beta"])
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["evidence"]["count"], 4)
        self.assertTrue(checks["real_transcription_quality"]["ok"])
        self.assertTrue(checks["system_output_audible"]["ok"])
        self.assertTrue(checks["ubuntu_linux_capture"]["ok"])
        self.assertTrue(checks["macos_capture"]["ok"])
        self.assertIn("transcription/transcription-pilot-report.json", checks["real_transcription_quality"]["evidence_sources"])

    def test_evidence_requires_meaningful_transcription_threshold(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {
                        "enabled": True,
                        "passed": True,
                        "min_word_accuracy": 0.1,
                        "word_accuracy": 1.0,
                    },
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_cli_evidence_allows_strict_beta_pass(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {"system": "Linux", "hardware_capture_tested": True, "passed": True},
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {"system": "Darwin", "hardware_capture_tested": True, "passed": True},
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.8},
                },
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    ["--root", str(ROOT), "--evidence", str(evidence_root), "--fail-on-blockers", "--json"]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ready_for_beta"])
        self.assertEqual(payload["blockers"], [])


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
