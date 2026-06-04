import json
import unittest

from auralis_voicekit import (
    BenchmarkReport,
    BenchmarkResult,
    VoiceActivityConfig,
    generate_synthetic_audio_chunks,
    run_offline_benchmarks,
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

    def test_benchmark_rejects_invalid_settings(self):
        with self.assertRaises(ValueError):
            run_offline_benchmarks(iterations=0)

        with self.assertRaises(ValueError):
            run_offline_benchmarks(warmup_iterations=-1)

        with self.assertRaises(ValueError):
            generate_synthetic_audio_chunks(duration_seconds=0)


if __name__ == "__main__":
    unittest.main()
