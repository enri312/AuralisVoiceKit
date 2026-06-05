import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from auralis_voicekit import AudioChunk, AudioFormat, write_wav


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

    def test_transcription_pilot_calculates_redacted_quality_metrics(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_text="Hola desde AuralisVoiceKit",
                min_word_accuracy=0.0,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["quality"]["enabled"])
        self.assertTrue(report["quality"]["expected_text_redacted"])
        self.assertEqual(report["quality"]["expected_text_source"], "argument")
        self.assertEqual(report["quality"]["word_accuracy"], 0.0)
        self.assertEqual(report["quality"]["word_error_rate"], 1.0)
        self.assertTrue(report["quality"]["passed"])
        self.assertNotIn("Hola desde AuralisVoiceKit", report_text)
        self.assertIn("Quality reference provided: True", findings)
        self.assertIn("Word accuracy: 0.0", findings)

    def test_transcription_pilot_quality_gate_can_fail(self):
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
                        "--expected-text",
                        "Hola desde AuralisVoiceKit",
                        "--min-word-accuracy",
                        "0.5",
                        "--duration",
                        "0.3",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["passed"])
        self.assertFalse(payload["quality"]["passed"])
        self.assertEqual(payload["quality"]["word_accuracy"], 0.0)

    def test_transcription_pilot_rejects_multiple_expected_text_sources(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            reference = Path(tmpdir) / "reference.txt"
            reference.write_text("Hola", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    expected_text="Hola",
                    expected_text_file=reference,
                )

    def test_transcription_pilot_expected_text_file_reports_only_file_name(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            reference = Path(tmpdir) / "reference.txt"
            reference.write_text("Hola desde archivo", encoding="utf-8")
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_text_file=reference,
                min_word_accuracy=0.0,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            report_text = report_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertEqual(report["quality"]["expected_text_source"], "file")
        self.assertEqual(report["quality"]["expected_text_file_name"], "reference.txt")
        self.assertNotIn("Hola desde archivo", report_text)

    def test_transcription_pilot_preflight_decodes_audio_without_backend(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                audio=audio_path,
                backend="whisper",
                preflight_only=True,
                audio_confirmed_non_sensitive=True,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["preflight_only"])
        self.assertFalse(report["real_transcription_requested"])
        self.assertIsNone(report["transcript"])
        self.assertTrue(report["audio"]["decoded"])
        self.assertEqual(report["audio"]["audio_file_name"], "sample.wav")
        self.assertEqual(report["audio"]["source_format"], "wav")
        self.assertNotIn(str(audio_path), report_text)
        self.assertIn("Preflight only: True", findings)
        self.assertIn("Audio decode passed: True", findings)

    def test_transcription_pilot_cli_preflight_allows_target_backend(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        str(Path(tmpdir) / "pilot"),
                        "--audio",
                        str(audio_path),
                        "--backend",
                        "whisper",
                        "--preflight-only",
                        "--audio-non-sensitive",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["preflight_only"])
        self.assertTrue(payload["audio"]["decoded"])
        self.assertIsNone(payload["transcript"])

    def test_transcription_pilot_preflight_rejects_quality_flags(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=Path(tmpdir) / "pilot",
                    audio=audio_path,
                    preflight_only=True,
                    audio_confirmed_non_sensitive=True,
                    expected_text="Hola",
                )


if __name__ == "__main__":
    unittest.main()
