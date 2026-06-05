import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYPI_QUICKSTART = ROOT / "examples" / "pypi_quickstart.py"


def _load_pypi_quickstart():
    spec = importlib.util.spec_from_file_location("pypi_quickstart", PYPI_QUICKSTART)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExampleTests(unittest.TestCase):
    def test_pypi_quickstart_run_demo_writes_wav_and_turns(self):
        module = _load_pypi_quickstart()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "quickstart.wav"
            payload = module.run_demo(output=str(output), duration_seconds=0.5, chunk_duration_ms=100)

            self.assertTrue(output.exists())
            self.assertEqual(payload["output"], str(output))
            self.assertGreaterEqual(payload["chunks"], 1)
            self.assertGreaterEqual(len(payload["turns"]), 1)
            self.assertEqual(payload["transcription_backend"], "null")

    def test_pypi_quickstart_script_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "quickstart.wav"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PYPI_QUICKSTART),
                    "--output",
                    str(output),
                    "--duration",
                    "0.5",
                    "--chunk-ms",
                    "100",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["transcription_backend"], "null")
        self.assertGreaterEqual(len(payload["turns"]), 1)


if __name__ == "__main__":
    unittest.main()
