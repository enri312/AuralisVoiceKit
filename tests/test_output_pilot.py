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
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["hardware_output_tested"])
        self.assertEqual(report["text_characters"], len(private_text))
        self.assertIn("<text-redacted>", report_text)
        self.assertNotIn(private_text, report_text)
        self.assertIn("System output pilot findings", findings)
        self.assertIn("Real audio requested: False", findings)
        self.assertNotIn(private_text, findings)

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
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["real_audio_requested"])
        self.assertEqual(payload["voice"], "spanish")
        self.assertEqual(payload["commands_count"], 2)


if __name__ == "__main__":
    unittest.main()
