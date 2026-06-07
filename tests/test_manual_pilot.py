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
            command_path = Path(report["artifacts"]["manual_capture_command"])
            report_path = Path(report["artifacts"]["manual_pilot_report"])

            self.assertTrue(bundle_path.exists())
            self.assertTrue(analysis_path.exists())
            self.assertTrue(findings_path.exists())
            self.assertTrue(checklist_path.exists())
            self.assertTrue(command_path.exists())
            self.assertTrue(report_path.exists())
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")
            command_card = command_path.read_text(encoding="utf-8")

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
        self.assertIn("beta_evidence_gap", report)
        self.assertIn("manual_capture_command_card", report)
        self.assertIn("capture_operator_gate", report)
        self.assertEqual(report["capture_readiness_plan"]["backend"], "wav")
        self.assertFalse(report["capture_readiness_plan"]["uses_pip_extra"])
        self.assertIsNone(report["capture_readiness_plan"]["python_extra"])
        self.assertEqual(report["target_capture_backend"]["name"], "wav")
        self.assertTrue(report["target_capture_backend"]["available"])
        self.assertEqual(report["target_capture_backend"]["freedom_policy"]["category"], "free-local")
        self.assertFalse(report["target_capture_backend"]["freedom_policy"]["proprietary"])
        self.assertIn("Target capture backend freedom policy: free-local", findings)
        self.assertIn("Target capture backend freedom policy: free-local", checklist)
        self.assertIn("Target capture backend freedom policy: free-local", command_card)
        self.assertFalse(report["capture_backend_ready_required"])
        self.assertFalse(report["capture_readiness_plan"]["post_install_check_uses_microphone"])
        self.assertFalse(report["capture_checklist"]["records_audio_bytes"])
        self.assertFalse(report["capture_checklist"]["ready_for_beta_evidence"])
        self.assertFalse(report["beta_evidence_gap"]["ready_for_beta_evidence"])
        self.assertGreater(report["beta_evidence_gap"]["missing_count"], 0)
        self.assertIn("capture_backend", report["beta_evidence_gap"]["missing_fields"])
        self.assertFalse(report["beta_evidence_gap"]["records_audio"])
        self.assertFalse(report["beta_evidence_gap"]["records_audio_bytes"])
        self.assertFalse(report["beta_evidence_gap"]["records_device_name"])
        self.assertFalse(report["beta_evidence_gap"]["records_local_paths"])
        command = report["manual_capture_command_card"]
        self.assertEqual(command["artifact"], "manual-capture-command.md")
        self.assertFalse(command["uses_pip_extra"])
        self.assertIsNone(command["python_extra"])
        self.assertIn("<pilot-output-dir>", command["preflight_command_template"])
        self.assertIn("<pilot-output-dir>", command["real_capture_command_template"])
        self.assertIn("<pilot-output-dir>", command["audit_command_template"])
        self.assertFalse(command["records_audio"])
        self.assertFalse(command["records_audio_bytes"])
        self.assertFalse(command["records_device_name"])
        self.assertFalse(command["records_local_paths"])
        operator_gate = report["capture_operator_gate"]
        self.assertTrue(operator_gate["safe_to_share"])
        self.assertEqual(operator_gate["decision"], "blocked")
        self.assertFalse(operator_gate["ready_for_beta_audit"])
        self.assertTrue(operator_gate["command_safe_to_copy"])
        self.assertEqual(operator_gate["expected_artifact"], "manual-pilot-report.json")
        self.assertIn("real_capture_explicitly_requested", operator_gate["missing_confirmations"])
        self.assertIn("input_reviewed", operator_gate["missing_confirmations"])
        self.assertIn("expected_system_matched", operator_gate["missing_confirmations"])
        self.assertIn("capture_backend_ready_guarded", operator_gate["missing_confirmations"])
        self.assertFalse(operator_gate["records_audio"])
        self.assertFalse(operator_gate["records_audio_bytes"])
        self.assertFalse(operator_gate["records_device_name"])
        self.assertFalse(operator_gate["records_local_paths"])
        self.assertFalse(operator_gate["records_operator_identity"])
        self.assertEqual(analysis["bundle_count"], 1)
        self.assertIn("Manual pilot findings", findings)
        self.assertIn("Capture test requested: False", findings)
        self.assertIn("Input review confirmed: False", findings)
        self.assertIn("Expected system matched: not-set", findings)
        self.assertIn("Capture checklist ready for beta evidence: False", findings)
        self.assertIn("Target capture backend available: True", findings)
        self.assertIn("Capture backend readiness required: False", findings)
        self.assertIn("Capture readiness post-install check", findings)
        self.assertIn("Beta evidence gap ready: False", findings)
        self.assertIn("Beta Evidence Gap", findings)
        self.assertIn("Capture operator gate decision: blocked", findings)
        self.assertIn("Capture Operator Gate", findings)
        self.assertIn("Sample rate: 48000", findings)
        self.assertIn("Bundle: doctor-bundle.json", findings)
        self.assertIn("Capture checklist: manual-capture-checklist.md", findings)
        self.assertIn("Manual capture command: manual-capture-command.md", findings)
        self.assertIn("Checklist de captura manual / Manual capture checklist", checklist)
        self.assertIn("Target capture backend available: True", checklist)
        self.assertIn("Capture backend readiness required: False", checklist)
        self.assertIn("Readiness post-install uses microphone: False", checklist)
        self.assertIn("Input review confirmed: False", checklist)
        self.assertIn("Ready for beta evidence: False", checklist)
        self.assertIn("Beta evidence gap ready: False", checklist)
        self.assertIn("Beta Evidence Gap", checklist)
        self.assertIn("Capture operator gate decision: blocked", checklist)
        self.assertIn("Capture Operator Gate", checklist)
        self.assertIn("Manual capture command", command_card)
        self.assertIn("Preflight Command", command_card)
        self.assertIn("Real Capture Command", command_card)
        self.assertIn("Audit Command", command_card)
        self.assertIn("Capture operator gate decision: blocked", command_card)
        self.assertIn("Capture Operator Gate", command_card)
        self.assertIn("<pilot-output-dir>", command_card)
        self.assertNotIn(str(Path(tempfile.gettempdir())), findings)
        self.assertNotIn(str(Path(tempfile.gettempdir())), checklist)
        self.assertNotIn(str(Path(tempfile.gettempdir())), command_card)

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
        self.assertIn("beta_evidence_gap", payload)
        self.assertIn("manual_capture_command_card", payload)
        self.assertIn("capture_operator_gate", payload)
        self.assertEqual(payload["capture_readiness_plan"]["backend"], "wav")
        self.assertFalse(payload["capture_readiness_plan"]["uses_pip_extra"])
        self.assertIsNone(payload["capture_readiness_plan"]["python_extra"])
        self.assertEqual(payload["target_capture_backend"]["name"], "wav")
        self.assertFalse(payload["capture_backend_ready_required"])
        self.assertFalse(payload["capture_readiness_plan"]["post_install_check_uses_microphone"])
        self.assertIn("capture_checklist", payload["artifacts"])
        self.assertIn("manual_capture_command", payload["artifacts"])
        self.assertFalse(payload["system_guard"]["enabled"])
        self.assertFalse(payload["beta_evidence_gap"]["ready_for_beta_evidence"])
        self.assertTrue(payload["manual_capture_command_card"]["uses_placeholders"])
        self.assertEqual(payload["capture_operator_gate"]["decision"], "blocked")
        self.assertFalse(payload["capture_operator_gate"]["ready_for_beta_audit"])

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
        self.assertEqual(payload["beta_evidence_gap"]["blocker"], "ubuntu_linux_capture")
        self.assertIn("system_guard.expected_system_matched", payload["beta_evidence_gap"]["missing_fields"])
        if module.platform.system() != "Linux":
            self.assertIn("system", payload["beta_evidence_gap"]["missing_fields"])
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
        self.assertTrue(report["capture_readiness_plan"]["uses_pip_extra"])
        self.assertEqual(report["capture_readiness_plan"]["python_extra"], "sounddevice")
        self.assertTrue(report["manual_capture_command_card"]["uses_pip_extra"])
        self.assertEqual(report["manual_capture_command_card"]["python_extra"], "sounddevice")
        self.assertEqual(report["beta_evidence_gap"]["blocker"], "ubuntu_linux_capture")

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
        beta_evidence_gap = module._capture_beta_evidence_gap(
            system="Linux",
            evidence_system="Linux",
            backend="sounddevice",
            system_guard={"expected_system_matched": True},
            target_capture_backend={"available": True},
            require_capture_backend_ready=True,
            capture_test=True,
            input_review_confirmed=True,
            passed=True,
            capture_checklist=checklist,
        )
        capture_readiness_plan = module._capture_readiness_plan(system="Linux", backend="sounddevice")
        command_card = module._manual_capture_command_card(
            capture_readiness_plan=capture_readiness_plan,
            beta_evidence_gap=beta_evidence_gap,
        )
        operator_gate = module._capture_operator_gate(
            system_guard={"expected_system_matched": True},
            target_capture_backend={"available": True},
            require_capture_backend_ready=True,
            capture_test=True,
            input_review_confirmed=True,
            capture_checklist=checklist,
            beta_evidence_gap=beta_evidence_gap,
            manual_capture_command_card=command_card,
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
            capture_readiness_plan=capture_readiness_plan,
            capture_checklist=checklist,
            beta_evidence_gap=beta_evidence_gap,
            capture_operator_gate=operator_gate,
        )

        self.assertTrue(checklist["ready_for_real_capture"])
        self.assertTrue(checklist["ready_for_beta_evidence"])
        self.assertEqual(beta_evidence_gap["blocker"], "ubuntu_linux_capture")
        self.assertTrue(beta_evidence_gap["ready_for_beta_evidence"])
        self.assertEqual(beta_evidence_gap["missing_count"], 0)
        self.assertEqual(beta_evidence_gap["missing_fields"], [])
        self.assertFalse(beta_evidence_gap["records_audio_bytes"])
        self.assertFalse(beta_evidence_gap["records_device_name"])
        self.assertTrue(checklist["expected_system_matched"])
        self.assertTrue(checklist["input_review_confirmed"])
        self.assertFalse(checklist["records_audio_bytes"])
        self.assertIn("Ready for beta evidence: True", markdown)
        self.assertIn("Beta evidence gap ready: True", markdown)
        self.assertIn("Expected system matched: True", markdown)
        self.assertIn("Input review confirmed: True", markdown)
        self.assertEqual(operator_gate["decision"], "ready_for_beta_audit")
        self.assertTrue(operator_gate["ready_for_beta_audit"])
        self.assertEqual(operator_gate["missing_confirmations"], [])
        self.assertIn("Run the strict beta evidence audit", operator_gate["next_action"])
        self.assertIn("Capture operator gate decision: ready_for_beta_audit", markdown)

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

    def test_capture_beta_evidence_gap_accepts_macos_pyaudio(self):
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
        gap = module._capture_beta_evidence_gap(
            system="Darwin",
            evidence_system="Darwin",
            backend="pyaudio",
            system_guard={"expected_system_matched": True},
            target_capture_backend={"available": True},
            require_capture_backend_ready=True,
            capture_test=True,
            input_review_confirmed=True,
            passed=True,
            capture_checklist=checklist,
        )

        self.assertEqual(gap["blocker"], "macos_capture")
        self.assertTrue(gap["ready_for_beta_evidence"])
        self.assertEqual(gap["missing_fields"], [])
        self.assertTrue(gap["safe_to_share"])

    def test_capture_beta_evidence_gap_accepts_guarded_windows_wasapi(self):
        module = _load_manual_pilot()

        checklist = module._capture_checklist(
            system="Windows",
            backend="wasapi",
            capture_test=True,
            sample_rate=48000,
            passed=True,
            hardware_capture_tested=True,
            input_review_confirmed=True,
            device_redacted=True,
            expected_system_matched=True,
        )
        gap = module._capture_beta_evidence_gap(
            system="Windows",
            evidence_system="Windows",
            backend="wasapi",
            system_guard={"expected_system_matched": True},
            target_capture_backend={"available": True},
            require_capture_backend_ready=True,
            capture_test=True,
            input_review_confirmed=True,
            passed=True,
            capture_checklist=checklist,
        )

        self.assertEqual(gap["blocker"], "windows_wasapi_capture")
        self.assertTrue(gap["ready_for_beta_evidence"])
        self.assertEqual(gap["missing_fields"], [])
        self.assertTrue(gap["safe_to_share"])

    def test_capture_readiness_plan_supports_linux_and_macos_backends(self):
        module = _load_manual_pilot()

        linux_sounddevice = module._capture_readiness_plan(system="Linux", backend="sounddevice")
        macos_pyaudio = module._capture_readiness_plan(system="Darwin", backend="pyaudio")

        self.assertIn("auralisvoicekit[sounddevice]", linux_sounddevice["pip_command"])
        self.assertTrue(linux_sounddevice["uses_pip_extra"])
        self.assertEqual(linux_sounddevice["python_extra"], "sounddevice")
        self.assertIn("libportaudio2", " ".join(linux_sounddevice["setup_commands"]))
        self.assertIn("--target-system Linux", linux_sounddevice["post_install_check"])
        self.assertIn("--require-capture-backend-ready", linux_sounddevice["post_install_check"])
        self.assertFalse(linux_sounddevice["post_install_check_uses_microphone"])
        self.assertTrue(linux_sounddevice["real_capture_check_requires_microphone"])
        self.assertIn("--capture-test", linux_sounddevice["real_capture_check_template"])
        self.assertIn("--require-capture-backend-ready", linux_sounddevice["real_capture_check_template"])
        self.assertIn("auralisvoicekit[pyaudio]", macos_pyaudio["pip_command"])
        self.assertTrue(macos_pyaudio["uses_pip_extra"])
        self.assertEqual(macos_pyaudio["python_extra"], "pyaudio")
        self.assertIn("brew install portaudio", " ".join(macos_pyaudio["setup_commands"]))
        self.assertIn("--expected-system Darwin", macos_pyaudio["real_capture_check_template"])

    def test_capture_readiness_plan_documents_wasapi_sample_rate(self):
        module = _load_manual_pilot()

        plan = module._capture_readiness_plan(system="Windows", backend="wasapi")

        self.assertIn("auralisvoicekit[sounddevice]", plan["pip_command"])
        self.assertTrue(plan["uses_pip_extra"])
        self.assertEqual(plan["python_extra"], "sounddevice")
        self.assertIn("--sample-rate 48000", plan["real_capture_check_template"])
        self.assertFalse(plan["post_install_check_uses_microphone"])

    def test_capture_backend_status_reports_unknown_backend(self):
        module = _load_manual_pilot()

        readiness_plan = module._capture_readiness_plan(system="Linux", backend="unknown")
        status = module._capture_backend_status("unknown", readiness_plan)

        self.assertFalse(readiness_plan["uses_pip_extra"])
        self.assertIsNone(readiness_plan["python_extra"])
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
