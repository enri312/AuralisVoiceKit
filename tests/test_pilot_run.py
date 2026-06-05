import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PILOT_RUN = ROOT / "tools" / "pilot_run.py"


def _load_pilot_run():
    spec = importlib.util.spec_from_file_location("pilot_run", PILOT_RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PilotRunTests(unittest.TestCase):
    def test_safe_pilot_writes_report_and_artifacts(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_safe_pilot(root=ROOT, output_dir=tmpdir)
            report_path = Path(report["artifacts"]["pilot_report"])

            self.assertTrue(report_path.exists())
            self.assertTrue(Path(report["artifacts"]["assistant_log"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_json"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_csv"]).exists())
            persisted = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertTrue(report["safe_automated_pilot"]["passed"])
        self.assertFalse(report["safe_automated_pilot"]["hardware_used"])
        self.assertEqual(persisted["version"], report["version"])
        self.assertEqual({step["status"] for step in report["steps"]}, {"passed"})
        self.assertIn("microphone-capture", {step["name"] for step in report["manual_pilot_steps"]})
        self.assertIn("beta-readiness", {step["name"] for step in report["manual_pilot_steps"]})

    def test_safe_pilot_cli_outputs_json(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(["--root", str(ROOT), "--output-dir", tmpdir, "--json"])
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["safe_automated_pilot"]["passed"])


if __name__ == "__main__":
    unittest.main()
