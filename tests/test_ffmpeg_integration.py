import contextlib
import io
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    peak_pcm16,
    read_audio,
    read_audio_as_chunk,
    read_wav_as_chunk,
    resolve_ffmpeg_executable,
    write_wav,
)
from auralis_voicekit.cli import main


RUN_INTEGRATION = os.getenv("AURALIS_RUN_FFMPEG_INTEGRATION") == "1"
ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTION_PILOT = ROOT / "tools" / "transcription_pilot.py"
PILOT_AUDIO_FIXTURE = ROOT / "tools" / "pilot_audio_fixture.py"


def _tone_chunk(
    *,
    sample_rate: int = 16_000,
    duration_seconds: float = 0.35,
    frequency: float = 440.0,
    amplitude: int = 12_000,
) -> AudioChunk:
    sample_count = int(sample_rate * duration_seconds)
    samples = []
    for index in range(sample_count):
        value = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
        samples.append(value)
    data = struct.pack("<" + "h" * len(samples), *samples)
    return AudioChunk(
        data=data,
        format=AudioFormat(sample_rate=sample_rate, channels=1, sample_width=2),
    )


def _load_transcription_pilot():
    spec = importlib.util.spec_from_file_location("transcription_pilot_for_ffmpeg", TRANSCRIPTION_PILOT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_pilot_audio_fixture():
    spec = importlib.util.spec_from_file_location("pilot_audio_fixture_for_ffmpeg", PILOT_AUDIO_FIXTURE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    RUN_INTEGRATION,
    "set AURALIS_RUN_FFMPEG_INTEGRATION=1 to run real compressed audio tests",
)
class FfmpegIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.ffmpeg = resolve_ffmpeg_executable()
        if self.ffmpeg is None:
            self.skipTest("ffmpeg executable is not available")

    def _encode_audio(self, tmpdir: str, extension: str, encoder_args: list[str]) -> str:
        wav_path = os.path.join(tmpdir, "tone.wav")
        output_path = os.path.join(tmpdir, f"tone.{extension}")
        write_wav(wav_path, [_tone_chunk()])

        command = [
            self.ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            wav_path,
            *encoder_args,
            output_path,
        ]
        completed = subprocess.run(command, check=False, capture_output=True)
        if completed.returncode != 0:
            fallback = [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                wav_path,
                output_path,
            ]
            completed = subprocess.run(fallback, check=False, capture_output=True)
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", "replace").strip()
            self.fail(f"ffmpeg could not encode {extension.upper()} fixture: {stderr}")
        return output_path

    def _make_mp3(self, tmpdir: str) -> str:
        return self._encode_audio(
            tmpdir,
            "mp3",
            ["-codec:a", "libmp3lame", "-q:a", "4"],
        )

    def _make_flac(self, tmpdir: str) -> str:
        return self._encode_audio(
            tmpdir,
            "flac",
            ["-codec:a", "flac", "-compression_level", "5"],
        )

    def test_read_audio_as_chunk_decodes_real_mp3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = self._make_mp3(tmpdir)

            chunk = read_audio_as_chunk(
                mp3_path,
                sample_rate=8000,
                channels=1,
                ffmpeg_executable=self.ffmpeg,
            )

        self.assertEqual(chunk.format.sample_rate, 8000)
        self.assertEqual(chunk.format.channels, 1)
        self.assertEqual(chunk.metadata["decoder"], "ffmpeg")
        self.assertEqual(chunk.metadata["source_format"], "mp3")
        self.assertGreater(len(chunk.data), 0)
        self.assertGreater(peak_pcm16(chunk), 0.01)

    def test_read_audio_splits_real_mp3_into_chunks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = self._make_mp3(tmpdir)

            chunks = read_audio(
                mp3_path,
                chunk_duration_ms=100,
                sample_rate=8000,
                channels=1,
                ffmpeg_executable=self.ffmpeg,
            )

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(all(chunk.format.sample_rate == 8000 for chunk in chunks))
        self.assertEqual(chunks[0].metadata["decoder"], "ffmpeg")
        self.assertEqual(chunks[0].metadata["source_format"], "mp3")

    def test_read_audio_as_chunk_decodes_real_flac(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            flac_path = self._make_flac(tmpdir)

            chunk = read_audio_as_chunk(
                flac_path,
                sample_rate=8000,
                channels=1,
                ffmpeg_executable=self.ffmpeg,
            )

        self.assertEqual(chunk.format.sample_rate, 8000)
        self.assertEqual(chunk.format.channels, 1)
        self.assertEqual(chunk.metadata["decoder"], "ffmpeg")
        self.assertEqual(chunk.metadata["source_format"], "flac")
        self.assertGreater(len(chunk.data), 0)
        self.assertGreater(peak_pcm16(chunk), 0.01)

    def test_read_audio_splits_real_flac_into_chunks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            flac_path = self._make_flac(tmpdir)

            chunks = read_audio(
                flac_path,
                chunk_duration_ms=100,
                sample_rate=8000,
                channels=1,
                ffmpeg_executable=self.ffmpeg,
            )

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(all(chunk.format.sample_rate == 8000 for chunk in chunks))
        self.assertEqual(chunks[0].metadata["decoder"], "ffmpeg")
        self.assertEqual(chunks[0].metadata["source_format"], "flac")

    def test_cli_transcribe_accepts_real_mp3_with_null_backend(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = self._make_mp3(tmpdir)

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe",
                        mp3_path,
                        "--backend",
                        "null",
                        "--ffmpeg",
                        self.ffmpeg,
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "null")
        self.assertEqual(payload["metadata"]["decoder"], "ffmpeg")
        self.assertEqual(payload["metadata"]["source_format"], "mp3")

    def test_cli_transcribe_accepts_real_flac_with_null_backend(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            flac_path = self._make_flac(tmpdir)

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe",
                        flac_path,
                        "--backend",
                        "null",
                        "--ffmpeg",
                        self.ffmpeg,
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "null")
        self.assertEqual(payload["metadata"]["decoder"], "ffmpeg")
        self.assertEqual(payload["metadata"]["source_format"], "flac")

    def test_normalize_command_writes_wav_from_real_mp3(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = self._make_mp3(tmpdir)
            wav_path = os.path.join(tmpdir, "normalized.wav")

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "normalize",
                        mp3_path,
                        wav_path,
                        "--ffmpeg",
                        self.ffmpeg,
                        "--target-peak",
                        "0.5",
                        "--json",
                    ]
                )
            normalized = read_wav_as_chunk(wav_path)

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["output"], wav_path)
        self.assertAlmostEqual(peak_pcm16(normalized), 0.5, places=2)

    def test_normalize_command_writes_wav_from_real_flac(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            flac_path = self._make_flac(tmpdir)
            wav_path = os.path.join(tmpdir, "normalized.wav")

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "normalize",
                        flac_path,
                        wav_path,
                        "--ffmpeg",
                        self.ffmpeg,
                        "--target-peak",
                        "0.5",
                        "--json",
                    ]
                )
            normalized = read_wav_as_chunk(wav_path)

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["output"], wav_path)
        self.assertAlmostEqual(peak_pcm16(normalized), 0.5, places=2)

    def test_transcription_pilot_preflight_decodes_real_mp3(self):
        module = _load_transcription_pilot()
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = self._make_mp3(tmpdir)

            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                audio=mp3_path,
                backend="whisper",
                ffmpeg=self.ffmpeg,
                preflight_only=True,
                audio_confirmed_non_sensitive=True,
                sample_rate=8000,
            )
            report_text = Path(report["artifacts"]["transcription_pilot_report"]).read_text(encoding="utf-8")
            checklist = Path(report["artifacts"]["transcription_review_checklist"]).read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["preflight_only"])
        self.assertTrue(report["audio"]["decoded"])
        self.assertEqual(report["audio"]["source_format"], "mp3")
        self.assertIsNone(report["transcript"])
        self.assertFalse(report["transcription_checklist"]["ready_for_beta_evidence"])
        self.assertIn("Transcription review checklist", checklist)
        self.assertNotIn(mp3_path, report_text)

    def test_pilot_audio_fixture_generates_decodable_mp3(self):
        module = _load_pilot_audio_fixture()
        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.generate_pilot_audio_fixture(
                root=ROOT,
                output_dir=tmpdir,
                formats=("mp3",),
                duration_seconds=0.35,
                sample_rate=8000,
                ffmpeg=self.ffmpeg,
                run_preflight=True,
                min_audio_seconds=0.2,
                max_audio_seconds=1.0,
            )
            mp3_path = Path(report["artifacts"]["mp3"])
            checklist_path = Path(report["artifacts"]["fixture_preflight_checklist"])
            next_step_path = Path(report["artifacts"]["fixture_preflight_next_step"])
            mp3_exists = mp3_path.exists()
            checklist_exists = checklist_path.exists()
            next_step_exists = next_step_path.exists()
            findings = Path(report["artifacts"]["fixture_findings"]).read_text(encoding="utf-8")
            next_step = next_step_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["ffmpeg"]["available"])
        self.assertTrue(report["preflight"]["passed"])
        self.assertTrue(report["preflight"]["audio_decoded"])
        self.assertTrue(report["preflight"]["duration_gate_passed"])
        self.assertTrue(report["generated_public_fixture"])
        self.assertFalse(report["usable_as_beta_evidence"])
        self.assertTrue(mp3_exists)
        self.assertTrue(checklist_exists)
        self.assertTrue(next_step_exists)
        self.assertIn("transcription-review-checklist.md", report["preflight"]["review_checklist"])
        self.assertIn("real-transcription-next-step.md", report["preflight"]["real_transcription_next_step"])
        self.assertIn("--audio <audio-path>", next_step)
        self.assertIn("--expected-text-file <expected-text-path>", next_step)
        self.assertEqual(report["files"][0]["format"], "mp3")
        self.assertTrue(report["files"][0]["decoded"])
        self.assertIn("pilot-sample.mp3", findings)
        self.assertIn("Review checklist:", findings)
        self.assertIn("Real transcription next step:", findings)

    def test_pilot_audio_fixture_preflight_can_target_openai_with_timeout(self):
        module = _load_pilot_audio_fixture()
        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.generate_pilot_audio_fixture(
                root=ROOT,
                output_dir=tmpdir,
                formats=("mp3",),
                duration_seconds=0.35,
                sample_rate=8000,
                ffmpeg=self.ffmpeg,
                run_preflight=True,
                preflight_backend="openai",
                preflight_model="gpt-4o-mini-transcribe",
                preflight_timeout_seconds=30,
                min_audio_seconds=0.2,
                max_audio_seconds=1.0,
            )
            next_step = Path(report["artifacts"]["fixture_preflight_next_step"]).read_text(encoding="utf-8")
            findings = Path(report["artifacts"]["fixture_findings"]).read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertEqual(report["preflight"]["backend"], "openai")
        self.assertEqual(report["preflight"]["model"], "gpt-4o-mini-transcribe")
        self.assertEqual(report["preflight"]["transcription_timeout_seconds"], 30)
        self.assertIsInstance(report["preflight"]["target_backend_available"], bool)
        self.assertIn("--backend openai", next_step)
        self.assertIn("--model gpt-4o-mini-transcribe", next_step)
        self.assertIn("--timeout-seconds 30", next_step)
        self.assertIn("Fixture preflight backend: `openai`", findings)
        self.assertIn("Fixture preflight timeout seconds: `30`", findings)


if __name__ == "__main__":
    unittest.main()
