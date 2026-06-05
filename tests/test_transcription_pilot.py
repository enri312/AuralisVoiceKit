import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTION_PILOT = ROOT / "tools" / "transcription_pilot.py"


def _load_transcription_pilot():
    spec = importlib.util.spec_from_file_location("transcription_pilot", TRANSCRIPTION_PILOT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TranscriptionPilotTests(unittest.TestCase):
    def test_transcription_pilot_writes_sanitized_synthetic_report(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            synthetic_audio = Path(report["artifacts"]["synthetic_audio"])
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            findings = findings_path.read_text(encoding="utf-8")
            synthetic_audio_exists = synthetic_audio.exists()
            report_text = report_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertEqual(report["backend"], "null")
        self.assertFalse(report["real_transcription_requested"])
        self.assertTrue(report["generated_synthetic_audio"])
        self.assertTrue(synthetic_audio_exists)
        self.assertEqual(payload["transcript"]["text_characters"], 0)
        self.assertTrue(payload["transcript"]["text_redacted"])
        self.assertNotIn("text\": \"", report_text)
        self.assertIn("Transcription pilot findings", findings)
        self.assertIn("Generated synthetic audio: True", findings)

    def test_transcription_pilot_cli_outputs_json(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--duration",
                        "0.3",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["backend"], "null")
        self.assertTrue(payload["generated_synthetic_audio"])
        self.assertFalse(payload["real_transcription_requested"])

    def test_transcription_pilot_rejects_real_backend_without_guard(self):
        module = _load_transcription_pilot()

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
                        "whisper",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("--real-transcription", payload["error"])

    def test_transcription_pilot_rejects_real_transcription_without_audio_confirmation(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    backend="whisper",
                    audio="sample.wav",
                    real_transcription=True,
                )


if __name__ == "__main__":
    unittest.main()
