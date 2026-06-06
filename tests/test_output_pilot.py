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
        self.assertFalse(report["voice_review_confirmed"])
        self.assertEqual(report["text_characters"], len(private_text))
        self.assertIn("<text-redacted>", report_text)
        self.assertNotIn(private_text, report_text)
        self.assertFalse(report["operator_checklist"]["records_operator_identity"])
        self.assertTrue(report["operator_checklist"]["redacts_spoken_text"])
        self.assertFalse(report["operator_checklist"]["voice_review_confirmed"])
        self.assertIsNone(report["operator_checklist"]["expected_system_matched"])
        self.assertFalse(report["operator_checklist"]["ready_for_beta_evidence"])
        self.assertIn("operator_checklist", report["artifacts"])
        self.assertIn("System output pilot findings", findings)
        self.assertIn("Real audio requested: False", findings)
        self.assertIn("Expected system matched: not-set", findings)
        self.assertIn("Operator checklist ready for beta evidence: False", findings)
        self.assertNotIn(private_text, findings)
        self.assertIn("System output operator checklist", checklist)
        self.assertIn("Records operator identity: False", checklist)
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
        self.assertFalse(payload["voice_review_confirmed"])
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
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
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
        self.assertTrue(operator_checklist["voice_review_confirmed"])
        self.assertTrue(operator_checklist["expected_system_matched"])
        self.assertIn("Expected system matched: True", checklist)
        self.assertIn("Voice review confirmed: True", checklist)
        self.assertIn("Ready for beta evidence: True", checklist)

    def test_output_pilot_operator_checklist_requires_voice_review_for_beta(self):
        module = _load_output_pilot()

        operator_checklist = module._operator_checklist(
            system="Linux",
            speak=True,
            operator_present=True,
            operator_confirmed_audio=True,
            voice_review_confirmed=False,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=True,
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
            voice_review_confirmed=True,
            voice=None,
            rate=None,
            volume=None,
            expected_system_matched=False,
            payload={"commands": [], "spoken": True, "error": None},
        )

        self.assertTrue(operator_checklist["ready_for_real_audio"])
        self.assertFalse(operator_checklist["expected_system_matched"])
        self.assertFalse(operator_checklist["ready_for_beta_evidence"])

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
                    voice_review_confirmed=True,
                )


if __name__ == "__main__":
    unittest.main()
