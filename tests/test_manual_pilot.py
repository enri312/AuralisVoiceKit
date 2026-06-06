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
        self.assertIn("capture_readiness_plan", report)
        self.assertIn("target_capture_backend", report)
        self.assertIn("capture_backend_ready_required", report)
        self.assertEqual(report["capture_readiness_plan"]["backend"], "wav")
        self.assertEqual(report["target_capture_backend"]["name"], "wav")
        self.assertTrue(report["target_capture_backend"]["available"])
        self.assertFalse(report["capture_backend_ready_required"])
        self.assertFalse(report["capture_readiness_plan"]["post_install_check_uses_microphone"])
        self.assertFalse(report["capture_checklist"]["records_audio_bytes"])
        self.assertFalse(report["capture_checklist"]["ready_for_beta_evidence"])
        self.assertEqual(analysis["bundle_count"], 1)
        self.assertIn("Manual pilot findings", findings)
        self.assertIn("Capture test requested: False", findings)
        self.assertIn("Input review confirmed: False", findings)
        self.assertIn("Expected system matched: not-set", findings)
        self.assertIn("Capture checklist ready for beta evidence: False", findings)
        self.assertIn("Target capture backend available: True", findings)
        self.assertIn("Capture backend readiness required: False", findings)
        self.assertIn("Capture readiness post-install check", findings)
        self.assertIn("Sample rate: 48000", findings)
        self.assertIn("Bundle: doctor-bundle.json", findings)
        self.assertIn("Capture checklist: manual-capture-checklist.md", findings)
        self.assertIn("Checklist de captura manual / Manual capture checklist", checklist)
        self.assertIn("Target capture backend available: True", checklist)
        self.assertIn("Capture backend readiness required: False", checklist)
        self.assertIn("Readiness post-install uses microphone: False", checklist)
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
        self.assertIn("capture_readiness_plan", payload)
        self.assertIn("target_capture_backend", payload)
        self.assertEqual(payload["capture_readiness_plan"]["backend"], "wav")
        self.assertEqual(payload["target_capture_backend"]["name"], "wav")
        self.assertFalse(payload["capture_backend_ready_required"])
        self.assertFalse(payload["capture_readiness_plan"]["post_install_check_uses_microphone"])
        self.assertIn("capture_checklist", payload["artifacts"])
        self.assertFalse(payload["system_guard"]["enabled"])

    def test_manual_pilot_target_system_only_changes_readiness_plan(self):
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
                        "--target-system",
                        "Linux",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["capture_readiness_plan"]["system"], "Linux")
        self.assertEqual(payload["system"], module.platform.system())
        self.assertFalse(payload["system_guard"]["enabled"])
        self.assertIn("--target-system Linux", payload["capture_readiness_plan"]["post_install_check"])
        self.assertIn(
            "--require-capture-backend-ready",
            payload["capture_readiness_plan"]["post_install_check"],
        )
        self.assertEqual(payload["capture_backend"], "wav")

    def test_manual_pilot_target_system_changes_default_backend(self):
        module = _load_manual_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_manual_pilot(
                root=ROOT,
                output_dir=tmpdir,
                target_system="Linux",
            )

        self.assertEqual(report["capture_backend"], "sounddevice")
        self.assertEqual(report["capture_readiness_plan"]["system"], "Linux")

    def test_manual_pilot_cli_reports_unavailable_capture_backend_guard(self):
        module = _load_manual_pilot()

        def unavailable_backend(backend: str, readiness_plan: dict):
            return {
                "name": backend,
                "kind": "capture",
                "available": False,
                "dependencies": ["pyaudio"],
                "reason": "missing optional dependency",
                "readiness_plan": readiness_plan,
            }

        module._capture_backend_status = unavailable_backend
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--backend",
                        "pyaudio",
                        "--target-system",
                        "Linux",
                        "--require-capture-backend-ready",
                        "--json",
                    ]
                )
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("Capture backend 'pyaudio' is not available", payload["error"])
        self.assertIn("auralisvoicekit[pyaudio]", payload["error"])
        self.assertIn("--require-capture-backend-ready", payload["error"])

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
            target_capture_backend={
                "name": "sounddevice",
                "kind": "capture",
                "available": True,
                "dependencies": ["sounddevice"],
                "reason": None,
            },
            require_capture_backend_ready=True,
            capture_readiness_plan=module._capture_readiness_plan(system="Linux", backend="sounddevice"),
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

    def test_capture_readiness_plan_supports_linux_and_macos_backends(self):
        module = _load_manual_pilot()

        linux_sounddevice = module._capture_readiness_plan(system="Linux", backend="sounddevice")
        macos_pyaudio = module._capture_readiness_plan(system="Darwin", backend="pyaudio")

        self.assertIn("auralisvoicekit[sounddevice]", linux_sounddevice["pip_command"])
        self.assertIn("libportaudio2", " ".join(linux_sounddevice["setup_commands"]))
        self.assertIn("--target-system Linux", linux_sounddevice["post_install_check"])
        self.assertIn("--require-capture-backend-ready", linux_sounddevice["post_install_check"])
        self.assertFalse(linux_sounddevice["post_install_check_uses_microphone"])
        self.assertTrue(linux_sounddevice["real_capture_check_requires_microphone"])
        self.assertIn("--capture-test", linux_sounddevice["real_capture_check_template"])
        self.assertIn("--require-capture-backend-ready", linux_sounddevice["real_capture_check_template"])
        self.assertIn("auralisvoicekit[pyaudio]", macos_pyaudio["pip_command"])
        self.assertIn("brew install portaudio", " ".join(macos_pyaudio["setup_commands"]))
        self.assertIn("--expected-system Darwin", macos_pyaudio["real_capture_check_template"])

    def test_capture_readiness_plan_documents_wasapi_sample_rate(self):
        module = _load_manual_pilot()

        plan = module._capture_readiness_plan(system="Windows", backend="wasapi")

        self.assertIn("auralisvoicekit[sounddevice]", plan["pip_command"])
        self.assertIn("--sample-rate 48000", plan["real_capture_check_template"])
        self.assertFalse(plan["post_install_check_uses_microphone"])

    def test_capture_backend_status_reports_unknown_backend(self):
        module = _load_manual_pilot()

        readiness_plan = module._capture_readiness_plan(system="Linux", backend="unknown")
        status = module._capture_backend_status("unknown", readiness_plan)

        self.assertFalse(status["available"])
        self.assertEqual(status["name"], "unknown")
        self.assertIn("Unknown capture backend", status["reason"])

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
