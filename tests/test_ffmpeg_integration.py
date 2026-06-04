import contextlib
import io
import json
import math
import os
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


if __name__ == "__main__":
    unittest.main()
