import contextlib
import csv
import io
import json
import os
import struct
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    BenchmarkComparisonEntry,
    BenchmarkComparisonReport,
    BenchmarkReport,
    BenchmarkResult,
    __version__,
    write_wav,
)
from auralis_voicekit.backends import SystemVoice
from auralis_voicekit.audio import peak_pcm16, read_wav_as_chunk
from auralis_voicekit.cli import main


def _constant_chunk(amplitude: int, samples: int = 100, sample_rate: int = 1000) -> AudioChunk:
    data = struct.pack("<" + "h" * samples, *([amplitude] * samples))
    audio_format = AudioFormat(sample_rate=sample_rate, channels=1, sample_width=2)
    return AudioChunk(data=data, format=audio_format)


def _fake_whisper_comparison_report() -> BenchmarkComparisonReport:
    result = BenchmarkResult(
        name="transcription:whisper",
        iterations=1,
        samples_ms=(12.0,),
        min_ms=12.0,
        mean_ms=12.0,
        median_ms=12.0,
        p95_ms=12.0,
        max_ms=12.0,
        total_ms=12.0,
    )
    benchmark = BenchmarkReport(
        version=__version__,
        created_at="2026-01-01T00:00:00+00:00",
        duration_seconds=0.1,
        sample_rate=1000,
        channels=1,
        chunk_duration_ms=100,
        iterations=1,
        warmup_iterations=0,
        chunks=1,
        segments=1,
        transcription_backend="whisper",
        results=(result,),
    )
    entry = BenchmarkComparisonEntry(
        name="whisper:model=tiny:device=auto:compute=default:beam=1:vad-off",
        model="tiny",
        device="auto",
        compute_type="default",
        beam_size=1,
        vad_filter=False,
        report=benchmark,
        transcription_mean_ms=12.0,
        transcription_p95_ms=12.0,
    )
    return BenchmarkComparisonReport(
        version=__version__,
        created_at="2026-01-01T00:00:00+00:00",
        benchmark="whisper-comparison",
        iterations=1,
        warmup_iterations=0,
        duration_seconds=0.1,
        sample_rate=1000,
        channels=1,
        chunk_duration_ms=100,
        entries=(entry,),
    )


class CliTests(unittest.TestCase):
    def test_version_flag(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn(__version__, output.getvalue())

    def test_backends_command(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["backends"])

        self.assertEqual(exit_code, 0)
        self.assertIn("capture:null", output.getvalue())

    def test_devices_command_can_use_null_backend(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["devices", "--backend", "null"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Null input", output.getvalue())

    def test_doctor_can_include_devices(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--devices", "--backend", "null"])

        self.assertEqual(exit_code, 0)
        self.assertIn("AuralisVoiceKit", output.getvalue())
        self.assertIn("Null input", output.getvalue())

    def test_doctor_json_output(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--devices", "--backend", "wav", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["version"], __version__)
        self.assertTrue(any(check["name"] == "devices:wav" for check in payload["checks"]))

    def test_doctor_json_output_can_include_capture_test(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "doctor",
                    "--capture-test",
                    "--capture-seconds",
                    "0.001",
                    "--backend",
                    "null",
                    "--json",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        checks = {check["name"]: check for check in payload["checks"]}
        self.assertEqual(checks["capture-test:null"]["status"], "ok")
        self.assertEqual(checks["capture-test:null"]["details"]["chunks_received"], 0)

    def test_doctor_wav_error_returns_nonzero(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--wav", "missing.wav"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot read WAV file", output.getvalue())

    def test_wav_info_command(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)])
            with contextlib.redirect_stdout(output):
                exit_code = main(["wav-info", path])

        self.assertEqual(exit_code, 0)
        self.assertIn("Sample rate: 8000", output.getvalue())
        self.assertIn("Encoding: pcm16", output.getvalue())

    def test_normalize_command_writes_wav(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.wav")
            output_path = os.path.join(tmpdir, "output.wav")
            write_wav(input_path, [_constant_chunk(1000, samples=100, sample_rate=1000)])
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "normalize",
                        input_path,
                        output_path,
                        "--target-peak",
                        "0.5",
                        "--max-gain",
                        "100",
                        "--json",
                    ]
                )
            normalized = read_wav_as_chunk(output_path)

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertAlmostEqual(peak_pcm16(normalized), 0.5, places=3)
        self.assertGreater(payload["gain"], 1.0)

    def test_speak_command_can_use_null_backend(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["speak", "Hola", "--backend", "null", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["backend"], "null")
        self.assertTrue(payload["spoken"])

    def test_speak_command_can_use_system_backend(self):
        output = io.StringIO()

        with patch("auralis_voicekit.backends.system_output.SystemSpeechOutputBackend.speak") as speak:
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "speak",
                        "Hola",
                        "--backend",
                        "system",
                        "--voice",
                        "test-voice",
                        "--rate",
                        "180",
                        "--volume",
                        "70",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["backend"], "system")
        self.assertEqual(payload["voice"], "test-voice")
        self.assertEqual(payload["rate"], 180)
        self.assertEqual(payload["volume"], 70)
        speak.assert_called_once()
        self.assertEqual(speak.call_args.args[0], "Hola")
        self.assertEqual(speak.call_args.args[1].output_voice, "test-voice")
        self.assertEqual(speak.call_args.args[1].output_rate, 180)
        self.assertEqual(speak.call_args.args[1].output_volume, 70)

    def test_voices_command_outputs_json_report(self):
        output = io.StringIO()
        backend = SimpleNamespace(
            list_voices=lambda: (
                SystemVoice(id="Monica", name="Monica", language="es_ES"),
            )
        )
        registry = SimpleNamespace(create_output=lambda name: backend)

        with patch("auralis_voicekit.cli.create_default_registry", return_value=registry):
            with contextlib.redirect_stdout(output):
                exit_code = main(["voices", "--backend", "system", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["backend"], "system")
        self.assertEqual(payload["voices"][0]["id"], "Monica")
        self.assertEqual(payload["voices"][0]["language"], "es_ES")

    def test_voices_command_reports_unsupported_backend(self):
        output = io.StringIO()
        registry = SimpleNamespace(create_output=lambda name: SimpleNamespace())

        with patch("auralis_voicekit.cli.create_default_registry", return_value=registry):
            with contextlib.redirect_stdout(output):
                exit_code = main(["voices", "--backend", "null", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertIn("cannot list voices", payload["error"])

    def test_benchmark_command_outputs_json_report(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "benchmark",
                    "--iterations",
                    "1",
                    "--warmups",
                    "0",
                    "--duration",
                    "0.5",
                    "--sample-rate",
                    "1000",
                    "--chunk-ms",
                    "100",
                    "--min-voice-ms",
                    "100",
                    "--max-silence-ms",
                    "100",
                    "--pre-speech-ms",
                    "0",
                    "--json",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["transcription_backend"], "null")
        self.assertEqual(len(payload["results"]), 3)
        self.assertIn("capture:wav", {result["name"] for result in payload["results"]})

    def test_benchmark_command_outputs_text_report(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "benchmark",
                    "--iterations",
                    "1",
                    "--warmups",
                    "0",
                    "--duration",
                    "0.5",
                    "--sample-rate",
                    "1000",
                    "--chunk-ms",
                    "100",
                    "--min-voice-ms",
                    "100",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("AuralisVoiceKit", output.getvalue())
        self.assertIn("segmentation:rms", output.getvalue())

    def test_benchmark_command_writes_csv_report(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "offline.csv")
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "benchmark",
                        "--iterations",
                        "1",
                        "--warmups",
                        "0",
                        "--duration",
                        "0.5",
                        "--sample-rate",
                        "1000",
                        "--chunk-ms",
                        "100",
                        "--min-voice-ms",
                        "100",
                        "--max-silence-ms",
                        "100",
                        "--pre-speech-ms",
                        "0",
                        "--output",
                        report_path,
                    ]
                )
            with open(report_path, "r", encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote benchmark report", output.getvalue())
        self.assertEqual(len(rows), 3)
        self.assertIn("capture:wav", {row["result_name"] for row in rows})

    def test_benchmark_whisper_command_outputs_json_report(self):
        output = io.StringIO()

        with patch(
            "auralis_voicekit.cli.run_whisper_comparison_benchmarks",
            return_value=_fake_whisper_comparison_report(),
        ) as runner:
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "benchmark-whisper",
                        "--models",
                        "tiny,base",
                        "--beam-sizes",
                        "1",
                        "--iterations",
                        "1",
                        "--warmups",
                        "0",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["benchmark"], "whisper-comparison")
        self.assertEqual(payload["rankings"][0]["model"], "tiny")
        runner.assert_called_once()
        self.assertEqual(runner.call_args.kwargs["models"], ("tiny", "base"))
        self.assertEqual(runner.call_args.kwargs["beam_sizes"], (1,))

    def test_benchmark_whisper_command_writes_json_report(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "whisper.json")
            with patch(
                "auralis_voicekit.cli.run_whisper_comparison_benchmarks",
                return_value=_fake_whisper_comparison_report(),
            ):
                with contextlib.redirect_stdout(output):
                    exit_code = main(
                        [
                            "benchmark-whisper",
                            "--models",
                            "tiny",
                            "--beam-sizes",
                            "1",
                            "--iterations",
                            "1",
                            "--warmups",
                            "0",
                            "--output",
                            report_path,
                            "--output-format",
                            "json",
                        ]
                    )
            with open(report_path, "r", encoding="utf-8") as stream:
                payload = json.load(stream)

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote benchmark report", output.getvalue())
        self.assertEqual(payload["benchmark"], "whisper-comparison")
        self.assertEqual(payload["rankings"][0]["model"], "tiny")

    def test_transcribe_command_can_use_null_backend(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)])
            with contextlib.redirect_stdout(output):
                exit_code = main(["transcribe", path, "--backend", "null", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "null")
        self.assertEqual(payload["text"], "")

    def test_transcribe_command_defaults_to_null_backend(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)])
            with contextlib.redirect_stdout(output):
                exit_code = main(["transcribe", path, "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "null")
        self.assertEqual(payload["text"], "")

    def test_transcribe_command_reports_wav_errors(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["transcribe", "missing.wav", "--backend", "null"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot read WAV file", output.getvalue())

    def test_transcribe_command_reports_missing_ffmpeg_as_json(self):
        output = io.StringIO()

        with patch("auralis_voicekit.audio.shutil.which", return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                with contextlib.redirect_stdout(output):
                    exit_code = main(
                        [
                            "transcribe",
                            "sample.mp3",
                            "--backend",
                            "null",
                            "--ffmpeg",
                            "missing-ffmpeg",
                            "--json",
                        ]
                    )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertIn("ffmpeg is required", payload["error"])
        self.assertIn("missing-ffmpeg", payload["error"])
        self.assertIn("Search:", payload["error"])

    def test_transcribe_command_accepts_mp3_with_ffmpeg_decoder(self):
        output = io.StringIO()
        chunk = AudioChunk(
            data=b"\x00\x00" * 8,
            format=AudioFormat(sample_rate=16000, channels=1, sample_width=2),
            metadata={"decoder": "ffmpeg", "path": "sample.mp3"},
        )

        with patch("auralis_voicekit.cli.read_audio_as_chunk", return_value=chunk):
            with contextlib.redirect_stdout(output):
                exit_code = main(["transcribe", "sample.mp3", "--backend", "null", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "null")
        self.assertEqual(payload["metadata"]["duration_seconds"], 0.0005)

    def test_transcribe_command_can_normalize_before_transcribing(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [_constant_chunk(1000, samples=100, sample_rate=1000)])
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe",
                        path,
                        "--backend",
                        "null",
                        "--normalize",
                        "--target-peak",
                        "0.5",
                        "--max-gain",
                        "100",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertIn("normalization_gain", payload["metadata"])

    def test_normalize_command_reports_missing_ffmpeg(self):
        output = io.StringIO()

        with patch("auralis_voicekit.audio.shutil.which", return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                with contextlib.redirect_stdout(output):
                    exit_code = main(
                        [
                            "normalize",
                            "sample.flac",
                            "out.wav",
                            "--ffmpeg",
                            "missing-ffmpeg",
                        ]
                    )

        self.assertEqual(exit_code, 1)
        self.assertIn("ffmpeg is required", output.getvalue())
        self.assertIn("Search:", output.getvalue())

    def test_transcribe_segments_command_can_use_null_backend(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [_constant_chunk(6000), _constant_chunk(6000), _constant_chunk(0)])
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe-segments",
                        path,
                        "--backend",
                        "null",
                        "--chunk-ms",
                        "100",
                        "--min-voice-ms",
                        "100",
                        "--pre-speech-ms",
                        "0",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["source"], "null")
        self.assertEqual(payload["turns"][0]["metadata"]["segment_index"], 1)

    def test_transcribe_segments_command_defaults_to_null_backend(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [_constant_chunk(6000), _constant_chunk(6000), _constant_chunk(0)])
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe-segments",
                        path,
                        "--chunk-ms",
                        "100",
                        "--min-voice-ms",
                        "100",
                        "--pre-speech-ms",
                        "0",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["source"], "null")

    def test_transcribe_segments_command_can_normalize_turns(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [_constant_chunk(1000), _constant_chunk(1000), _constant_chunk(0)])
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe-segments",
                        path,
                        "--backend",
                        "null",
                        "--chunk-ms",
                        "100",
                        "--min-voice-ms",
                        "100",
                        "--pre-speech-ms",
                        "0",
                        "--normalize",
                        "--target-peak",
                        "0.5",
                        "--max-gain",
                        "100",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertIn("normalization_gain", payload["turns"][0]["metadata"])

    def test_transcribe_segments_command_accepts_mp3_with_ffmpeg_decoder(self):
        output = io.StringIO()
        chunks = [_constant_chunk(6000), _constant_chunk(6000), _constant_chunk(0)]

        with patch("auralis_voicekit.session.read_audio", return_value=chunks):
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "transcribe-segments",
                        "sample.mp3",
                        "--backend",
                        "null",
                        "--chunk-ms",
                        "100",
                        "--min-voice-ms",
                        "100",
                        "--pre-speech-ms",
                        "0",
                        "--json",
                    ]
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payload["turns"]), 1)


if __name__ == "__main__":
    unittest.main()
