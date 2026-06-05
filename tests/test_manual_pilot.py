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
            )
            bundle_path = Path(report["artifacts"]["doctor_bundle"])
            analysis_path = Path(report["artifacts"]["doctor_analysis"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            report_path = Path(report["artifacts"]["manual_pilot_report"])

            self.assertTrue(bundle_path.exists())
            self.assertTrue(analysis_path.exists())
            self.assertTrue(findings_path.exists())
            self.assertTrue(report_path.exists())
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            findings = findings_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertFalse(report["hardware_capture_tested"])
        self.assertEqual(analysis["bundle_count"], 1)
        self.assertIn("Manual pilot findings", findings)
        self.assertIn("Capture test requested: False", findings)
        self.assertIn("Bundle: doctor-bundle.json", findings)
        self.assertNotIn(str(Path(tempfile.gettempdir())), findings)

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
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["capture_backend"], "wav")
        self.assertFalse(payload["capture_test_requested"])


if __name__ == "__main__":
    unittest.main()
