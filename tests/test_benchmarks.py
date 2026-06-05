import json
import unittest
from unittest.mock import patch

from auralis_voicekit import (
    BenchmarkComparisonReport,
    BenchmarkReport,
    BenchmarkResult,
    VoiceActivityConfig,
    generate_synthetic_audio_chunks,
    run_offline_benchmarks,
    run_whisper_comparison_benchmarks,
)


def _fake_whisper_report(model: str, beam_size: int, mean_ms: float) -> BenchmarkReport:
    result = BenchmarkResult(
        name="transcription:whisper",
        iterations=1,
        samples_ms=(mean_ms,),
        min_ms=mean_ms,
        mean_ms=mean_ms,
        median_ms=mean_ms,
        p95_ms=mean_ms,
        max_ms=mean_ms,
        total_ms=mean_ms,
        metadata={"model": model, "beam_size": beam_size},
    )
    return BenchmarkReport(
        version="0.test",
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


class BenchmarkTests(unittest.TestCase):
    def test_generate_synthetic_audio_chunks_creates_voice_and_silence(self):
        chunks = generate_synthetic_audio_chunks(
            duration_seconds=0.5,
            sample_rate=1000,
            chunk_duration_ms=100,
        )

        self.assertEqual(len(chunks), 5)
        self.assertTrue(any(chunk.metadata["voice"] for chunk in chunks))
        self.assertTrue(any(not chunk.metadata["voice"] for chunk in chunks))
        self.assertEqual(chunks[0].format.sample_rate, 1000)

    def test_run_offline_benchmarks_reports_capture_segmentation_and_transcription(self):
        report = run_offline_benchmarks(
            iterations=2,
            warmup_iterations=0,
            duration_seconds=0.5,
            sample_rate=1000,
            chunk_duration_ms=100,
            voice_activity=VoiceActivityConfig(
                threshold=0.01,
                min_voice_ms=100,
                max_silence_ms=100,
                pre_speech_ms=0,
            ),
        )

        self.assertIsInstance(report, BenchmarkReport)
        self.assertEqual(report.transcription_backend, "null")
        self.assertGreaterEqual(report.segments, 1)
        names = {result.name for result in report.results}
        self.assertEqual(names, {"capture:wav", "segmentation:rms", "transcription:null"})
        for result in report.results:
            self.assertIsInstance(result, BenchmarkResult)
            self.assertEqual(result.iterations, 2)
            self.assertEqual(len(result.samples_ms), 2)
            self.assertGreaterEqual(result.mean_ms, 0.0)
            self.assertGreaterEqual(result.p95_ms, result.min_ms)

    def test_report_to_dict_is_json_serializable(self):
        report = run_offline_benchmarks(
            iterations=1,
            warmup_iterations=0,
            duration_seconds=0.3,
            sample_rate=1000,
            chunk_duration_ms=100,
            voice_activity=VoiceActivityConfig(min_voice_ms=100, max_silence_ms=100),
        )

        payload = report.to_dict()

        self.assertEqual(payload["version"], report.version)
        self.assertEqual(len(payload["results"]), 3)
        json.dumps(payload)

    def test_run_whisper_comparison_benchmarks_ranks_configurations(self):
        def fake_runner(**kwargs):
            model = kwargs["transcription_model"]
            beam_size = kwargs["transcription_beam_size"]
            mean = 10.0 if model == "tiny" and beam_size == 1 else 25.0
            return _fake_whisper_report(model, beam_size, mean)

        with patch("auralis_voicekit.benchmarks.run_offline_benchmarks", side_effect=fake_runner):
            report = run_whisper_comparison_benchmarks(
                models=("base", "tiny"),
                beam_sizes=(5, 1),
                iterations=1,
                warmup_iterations=0,
                max_combinations=4,
            )

        self.assertIsInstance(report, BenchmarkComparisonReport)
        self.assertEqual(len(report.entries), 4)
        self.assertEqual(report.fastest.model, "tiny")
        self.assertEqual(report.fastest.beam_size, 1)
        payload = report.to_dict()
        self.assertEqual(payload["fastest"], report.fastest.name)
        self.assertEqual(payload["rankings"][0]["model"], "tiny")
        json.dumps(payload)

    def test_run_whisper_comparison_benchmarks_limits_large_matrices(self):
        with self.assertRaises(ValueError):
            run_whisper_comparison_benchmarks(
                models=("tiny", "base"),
                devices=("cpu", "cuda"),
                compute_types=("int8", "float16"),
                beam_sizes=(1, 5),
                max_combinations=4,
            )

    def test_benchmark_rejects_invalid_settings(self):
        with self.assertRaises(ValueError):
            run_offline_benchmarks(iterations=0)

        with self.assertRaises(ValueError):
            run_offline_benchmarks(warmup_iterations=-1)

        with self.assertRaises(ValueError):
            generate_synthetic_audio_chunks(duration_seconds=0)


if __name__ == "__main__":
    unittest.main()
