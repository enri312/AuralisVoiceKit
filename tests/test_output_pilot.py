import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PILOT = ROOT / "tools" / "output_pilot.py"


def _load_output_pilot():
    spec = importlib.util.spec_from_file_location("output_pilot", OUTPUT_PILOT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _spoken_text_privacy_scan(*, passed: bool = True) -> dict:
    return {
        "enabled": True,
        "passed": passed,
        "risk_count": 0 if passed else 1,
        "risk_types": [] if passed else ["email"],
    }


class OutputPilotTests(unittest.TestCase):
    def test_output_pilot_writes_sanitized_report_and_findings(self):
        module = _load_output_pilot()
        private_text = "Texto privado de prueba"

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_output_pilot(
                root=ROOT,
                output_dir=tmpdir,
                text=private_text,
                system="Darwin",
                voice="Monica",
                rate=180,
            )
            report_path = Path(report["artifacts"]["output_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["operator_checklist"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["hardware_output_tested"])
        self.assertFalse(report["operator_present"])
        self.assertFalse(report["system_guard"]["enabled"])
        self.assertIsNone(report["system_guard"]["expected_system_matched"])
        self.assertEqual(report["operator_confirmation_status"], "not-required")
        self.assertFalse(report["text_review_confirmed"])
        self.assertTrue(report["spoken_text_privacy_scan"]["passed"])
        self.assertFalse(report["voice_review_confirmed"])
        self.assertEqual(report["text_characters"], len(private_text))
        self.assertIn("<text-redacted>", report_text)
        self.assertNotIn(private_text, report_text)
        self.assertFalse(report["operator_checklist"]["records_operator_identity"])
        self.assertTrue(report["operator_checklist"]["redacts_spoken_text"])
        self.assertFalse(report["operator_checklist"]["text_review_confirmed"])
        self.assertTrue(report["operator_checklist"]["spoken_text_privacy_scan_passed"])
        self.assertFalse(report["operator_checklist"]["voice_review_confirmed"])
        self.assertIsNone(report["operator_checklist"]["expected_system_matched"])
        self.assertFalse(report["operator_checklist"]["ready_for_beta_evidence"])
        self.assertIn("operator_checklist", report["artifacts"])
        self.assertIn("System output pilot findings", findings)
        self.assertIn("Real audio requested: False", findings)
        self.assertIn("Spoken text privacy scan passed: True", findings)
        self.assertIn("Expected system matched: not-set", findings)
        self.assertIn("Operator checklist ready for beta evidence: False", findings)
        self.assertNotIn(private_text, findings)
        self.assertIn("System output operator checklist", checklist)
        self.assertIn("Records operator identity: False", checklist)
        self.assertIn("Spoken text privacy scan passed: True", checklist)
        self.assertIn("Expected system matched: not-set", checklist)
        self.assertIn("Ready for beta evidence: False", checklist)
        self.assertNotIn(private_text, checklist)

    def test_output_pilot_cli_outputs_json(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--system",
                        "Linux",
                        "--text",
                        "Hola salida",
                        "--voice",
                        "spanish",
                        "--rate",
                        "160",
                        "--volume",
                        "80",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["system"], "Linux")
        self.assertFalse(payload["system_guard"]["enabled"])
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["real_audio_requested"])
        self.assertIn("operator_checklist", payload["artifacts"])
        self.assertFalse(payload["text_review_confirmed"])
        self.assertTrue(payload["spoken_text_privacy_scan"]["passed"])
        self.assertFalse(payload["voice_review_confirmed"])
        self.assertFalse(payload["operator_checklist"]["text_review_confirmed"])
        self.assertFalse(payload["operator_checklist"]["voice_review_confirmed"])
        self.assertFalse(payload["operator_checklist"]["ready_for_beta_evidence"])
        self.assertEqual(payload["voice"], "spanish")
        self.assertEqual(payload["commands_count"], 2)

    def test_output_pilot_operator_checklist_marks_confirmed_real_audio(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            text_review_confirmed=True,
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
            spoken_text_privacy_scan=_spoken_text_privacy_scan(),
            payload={"commands": [], "spoken": True, "error": None},
        )
        checklist = module._build_operator_checklist_markdown(
            timestamp="2026-06-05T00:00:00+00:00",
            system="Linux",
            operator_checklist=operator_checklist,
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertTrue(operator_checklist["ready_for_beta_evidence"])
        self.assertTrue(operator_checklist["commands_available"])
        self.assertTrue(operator_checklist["text_review_confirmed"])
        self.assertTrue(operator_checklist["spoken_text_privacy_scan_passed"])
        self.assertTrue(operator_checklist["voice_review_confirmed"])
        self.assertTrue(operator_checklist["expected_system_matched"])
        self.assertIn("Expected system matched: True", checklist)
        self.assertIn("Text review confirmed: True", checklist)
        self.assertIn("Spoken text privacy scan passed: True", checklist)
        self.assertIn("Voice review confirmed: True", checklist)
        self.assertIn("Ready for beta evidence: True", checklist)

    def test_output_pilot_operator_checklist_requires_voice_review_for_beta(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            text_review_confirmed=True,
            voice_review_confirmed=False,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
            spoken_text_privacy_scan=_spoken_text_privacy_scan(),
            payload={"commands": [], "spoken": True, "error": None},
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertFalse(operator_checklist["ready_for_beta_evidence"])
        self.assertFalse(operator_checklist["voice_review_confirmed"])

    def test_output_pilot_operator_checklist_requires_expected_system_for_beta(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            text_review_confirmed=True,
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=False,
            spoken_text_privacy_scan=_spoken_text_privacy_scan(),
            payload={"commands": [], "spoken": True, "error": None},
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertFalse(operator_checklist["expected_system_matched"])
        self.assertFalse(operator_checklist["ready_for_beta_evidence"])

    def test_output_pilot_operator_checklist_requires_text_review_for_beta(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            text_review_confirmed=False,
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
            spoken_text_privacy_scan=_spoken_text_privacy_scan(),
            payload={"commands": [], "spoken": True, "error": None},
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertFalse(operator_checklist["text_review_confirmed"])
        self.assertFalse(operator_checklist["ready_for_beta_evidence"])

    def test_output_pilot_operator_checklist_requires_text_privacy_scan_for_beta(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            text_review_confirmed=True,
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
            spoken_text_privacy_scan=_spoken_text_privacy_scan(passed=False),
            payload={"commands": [], "spoken": True, "error": None},
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertFalse(operator_checklist["spoken_text_privacy_scan_passed"])
        self.assertFalse(operator_checklist["ready_for_beta_evidence"])

    def test_output_pilot_blocks_risky_spoken_text_in_dry_run(self):
        module = _load_output_pilot()
        risky_text = "Contacto persona@example.com codigo 123456789"

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_output_pilot(
                root=ROOT,
                output_dir=tmpdir,
                text=risky_text,
                system="Linux",
            )
            report_path = Path(report["artifacts"]["output_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["operator_checklist"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")

        self.assertFalse(report["passed"])
        self.assertFalse(report["spoken_text_privacy_scan"]["passed"])
        self.assertIn("email", report["spoken_text_privacy_scan"]["risk_types"])
        self.assertIn("long_number", report["spoken_text_privacy_scan"]["risk_types"])
        self.assertFalse(report["operator_checklist"]["spoken_text_privacy_scan_passed"])
        self.assertNotIn("persona@example.com", report_text)
        self.assertNotIn("123456789", report_text)
        self.assertIn("Spoken text privacy scan passed: False", findings)
        self.assertIn("spoken_text_privacy_scan_passed", checklist)

    def test_output_pilot_expected_system_guard_matches_current_system(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_output_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_system=module.platform.system(),
            )

        self.assertTrue(report["system_guard"]["enabled"])
        self.assertTrue(report["system_guard"]["expected_system_matched"])
        self.assertTrue(report["operator_checklist"]["expected_system_matched"])
        self.assertTrue(report["passed"])

    def test_output_pilot_expected_system_guard_detects_mismatch(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_output_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_system="Darwin" if module.platform.system() != "Darwin" else "Windows",
            )

        self.assertTrue(report["system_guard"]["enabled"])
        self.assertFalse(report["system_guard"]["expected_system_matched"])
        self.assertFalse(report["operator_checklist"]["expected_system_matched"])
        self.assertFalse(report["passed"])

    def test_output_pilot_requires_operator_for_real_audio(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--system",
                        "Linux",
                        "--speak",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("--operator-present", payload["error"])

    def test_output_pilot_rejects_confirmation_without_speak(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_output_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    operator_present=True,
                )

    def test_output_pilot_rejects_text_review_without_speak(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_output_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    text_review_confirmed=True,
                )

    def test_output_pilot_rejects_real_audio_without_text_review(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--speak",
                        "--operator-present",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("--confirm-text-reviewed", payload["error"])

    def test_output_pilot_rejects_real_audio_with_risky_text(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_output_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    text="Contacto persona@example.com",
                    speak=True,
                    operator_present=True,
                    operator_confirmed_audio=True,
                    text_review_confirmed=True,
                    voice_review_confirmed=True,
                    expected_system=module.platform.system(),
                )

    def test_output_pilot_rejects_system_override_with_real_audio(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_output_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    system="Linux",
                    speak=True,
                    operator_present=True,
                    text_review_confirmed=True,
                )

    def test_output_pilot_rejects_voice_review_without_audible_confirmation(self):
        module = _load_output_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_output_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    speak=True,
                    operator_present=True,
                    text_review_confirmed=True,
                    voice_review_confirmed=True,
                )


if __name__ == "__main__":
    unittest.main()
