import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANUAL_PILOT = ROOT / "tools" / "manual_pilot.py"


def _load_manual_pilot():
    spec = importlib.util.spec_from_file_location("manual_pilot", MANUAL_PILOT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ManualPilotTests(unittest.TestCase):
    def test_manual_pilot_writes_bundle_analysis_and_findings(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_manual_pilot(
                root=ROOT,
                output_dir=tmpdir,
                capture_backend="wav",
                sample_rate=48000,
            )
            bundle_path = Path(report["artifacts"]["doctor_bundle"])
            analysis_path = Path(report["artifacts"]["doctor_analysis"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["capture_checklist"])
            report_path = Path(report["artifacts"]["manual_pilot_report"])

            self.assertTrue(bundle_path.exists())
            self.assertTrue(analysis_path.exists())
            self.assertTrue(findings_path.exists())
            self.assertTrue(checklist_path.exists())
            self.assertTrue(report_path.exists())
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["diagnostic_passed"])
        self.assertFalse(report["hardware_capture_tested"])
        self.assertFalse(report["input_review_confirmed"])
        self.assertEqual(report["sample_rate"], 48000)
        self.assertFalse(report["system_guard"]["enabled"])
        self.assertIsNone(report["system_guard"]["expected_system_matched"])
        self.assertIn("capture_checklist", report)
        self.assertFalse(report["capture_checklist"]["records_audio_bytes"])
        self.assertFalse(report["capture_checklist"]["ready_for_beta_evidence"])
        self.assertEqual(analysis["bundle_count"], 1)
        self.assertIn("Manual pilot findings", findings)
        self.assertIn("Capture test requested: False", findings)
        self.assertIn("Input review confirmed: False", findings)
        self.assertIn("Expected system matched: not-set", findings)
        self.assertIn("Capture checklist ready for beta evidence: False", findings)
        self.assertIn("Sample rate: 48000", findings)
        self.assertIn("Bundle: doctor-bundle.json", findings)
        self.assertIn("Capture checklist: manual-capture-checklist.md", findings)
        self.assertIn("Checklist de captura manual / Manual capture checklist", checklist)
        self.assertIn("Input review confirmed: False", checklist)
        self.assertIn("Ready for beta evidence: False", checklist)
        self.assertNotIn(str(Path(tempfile.gettempdir())), findings)
        self.assertNotIn(str(Path(tempfile.gettempdir())), checklist)

    def test_manual_pilot_cli_outputs_json(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--backend",
                        "wav",
                        "--sample-rate",
                        "48000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["capture_backend"], "wav")
        self.assertEqual(payload["sample_rate"], 48000)
        self.assertFalse(payload["capture_test_requested"])
        self.assertFalse(payload["input_review_confirmed"])
        self.assertIn("capture_checklist", payload)
        self.assertIn("capture_checklist", payload["artifacts"])
        self.assertFalse(payload["system_guard"]["enabled"])

    def test_manual_pilot_redacts_named_device_selector(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_manual_pilot(
                root=ROOT,
                output_dir=tmpdir,
                capture_backend="wav",
                capture_device="Studio Microphone 7",
            )

        self.assertEqual(report["capture_device"], "<device-redacted>")
        self.assertTrue(report["capture_device_redacted"])

    def test_manual_pilot_expected_system_guard_matches_current_system(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_manual_pilot(
                root=ROOT,
                output_dir=tmpdir,
                capture_backend="wav",
                expected_system=module.platform.system(),
            )

        self.assertTrue(report["system_guard"]["enabled"])
        self.assertTrue(report["system_guard"]["expected_system_matched"])

    def test_manual_pilot_expected_system_guard_detects_mismatch(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_manual_pilot(
                root=ROOT,
                output_dir=tmpdir,
                capture_backend="wav",
                expected_system="Darwin" if module.platform.system() != "Darwin" else "Windows",
            )

        self.assertTrue(report["system_guard"]["enabled"])
        self.assertFalse(report["system_guard"]["expected_system_matched"])
        self.assertFalse(report["passed"])
        self.assertTrue(report["diagnostic_passed"])

    def test_capture_checklist_marks_beta_ready_for_real_capture(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Linux",
            backend="sounddevice",
            capture_test=True,
            sample_rate=None,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=True,
            device_redacted=False,
            expected_system_matched=True,
        )
        markdown = module._build_capture_checklist_markdown(
            timestamp="2026-06-05T00:00:00+00:00",
            system="Linux",
            backend="sounddevice",
            capture_checklist=checklist,
        )

        self.assertTrue(checklist["ready_for_real_capture"])
        self.assertTrue(checklist["ready_for_beta_evidence"])
        self.assertTrue(checklist["expected_system_matched"])
        self.assertTrue(checklist["input_review_confirmed"])
        self.assertFalse(checklist["records_audio_bytes"])
        self.assertIn("Ready for beta evidence: True", markdown)
        self.assertIn("Expected system matched: True", markdown)
        self.assertIn("Input review confirmed: True", markdown)

    def test_capture_checklist_accepts_pyaudio_for_cross_platform_capture(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Darwin",
            backend="pyaudio",
            capture_test=True,
            sample_rate=None,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=True,
            device_redacted=False,
            expected_system_matched=True,
        )

        self.assertTrue(checklist["ready_for_real_capture"])
        self.assertTrue(checklist["ready_for_beta_evidence"])

    def test_capture_checklist_requires_sample_rate_for_windows_wasapi(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Windows",
            backend="wasapi",
            capture_test=True,
            sample_rate=None,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=True,
            device_redacted=False,
            expected_system_matched=True,
        )

        self.assertFalse(checklist["ready_for_real_capture"])
        self.assertFalse(checklist["ready_for_beta_evidence"])

    def test_capture_checklist_requires_expected_system_for_beta_evidence(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Linux",
            backend="sounddevice",
            capture_test=True,
            sample_rate=None,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=True,
            device_redacted=False,
            expected_system_matched=False,
        )

        self.assertTrue(checklist["ready_for_real_capture"])
        self.assertFalse(checklist["ready_for_beta_evidence"])

    def test_capture_checklist_requires_input_review_for_beta_evidence(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Linux",
            backend="sounddevice",
            capture_test=True,
            sample_rate=None,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=False,
            device_redacted=False,
            expected_system_matched=True,
        )

        self.assertTrue(checklist["ready_for_real_capture"])
        self.assertFalse(checklist["input_review_confirmed"])
        self.assertFalse(checklist["ready_for_beta_evidence"])

    def test_input_review_confirmation_requires_real_capture(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_manual_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    capture_backend="wav",
                    input_review_confirmed=True,
                )

    def test_manual_pilot_cli_rejects_input_review_without_capture_test(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    module.main(
                        [
                            "--root",
                            str(ROOT),
                            "--output-dir",
                            tmpdir,
                            "--backend",
                            "wav",
                            "--confirm-input-reviewed",
                            "--json",
                        ]
                    )

        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
