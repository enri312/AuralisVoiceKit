import sys
import types
import unittest
from unittest.mock import patch

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    BackendNotAvailable,
    TranscriptionError,
    VoiceKitConfig,
)
from auralis_voicekit.backends.whisper_transcription import WhisperTranscriptionBackend


class FakeSegment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
        self.avg_logprob = -0.1
        self.no_speech_prob = 0.01


class FakeInfo:
    language = "es"
    language_probability = 0.98
    duration = 1.0
    duration_after_vad = 0.8


class WhisperTranscriptionBackendTests(unittest.TestCase):
    def test_transcribe_uses_faster_whisper_model(self):
        calls = {}

        class FakeWhisperModel:
            def __init__(self, model_name, device, compute_type):
                calls["model_name"] = model_name
                calls["device"] = device
                calls["compute_type"] = compute_type

            def transcribe(self, path, **request):
                calls["path"] = path
                calls["request"] = request
                return [FakeSegment(0.0, 0.5, "hola "), FakeSegment(0.5, 1.0, "mundo")], FakeInfo()

        module = types.ModuleType("faster_whisper")
        module.WhisperModel = FakeWhisperModel
        chunk = AudioChunk(
            data=b"\x00\x00" * 16000,
            format=AudioFormat(sample_rate=16000, channels=1, sample_width=2),
        )
        config = VoiceKitConfig(
            transcription_backend="whisper",
            transcription_model="tiny",
            transcription_device="cpu",
            transcription_compute_type="int8",
            transcription_beam_size=3,
            transcription_vad_filter=True,
            transcription_prompt="audio en espanol",
        )

        with patch.dict(sys.modules, {"faster_whisper": module}):
            result = WhisperTranscriptionBackend().transcribe(chunk, config)

        self.assertEqual(result.text, "hola mundo")
        self.assertEqual(result.language, "es")
        self.assertEqual(result.confidence, 0.98)
        self.assertEqual(result.source, "whisper")
        self.assertEqual(calls["model_name"], "tiny")
        self.assertEqual(calls["device"], "cpu")
        self.assertEqual(calls["compute_type"], "int8")
        self.assertEqual(calls["request"]["beam_size"], 3)
        self.assertTrue(calls["request"]["vad_filter"])
        self.assertEqual(calls["request"]["initial_prompt"], "audio en espanol")
        self.assertEqual(result.metadata["segments"][0]["text"], "hola ")

    def test_info_reports_missing_faster_whisper_dependency(self):
        with patch(
            "auralis_voicekit.backends.whisper_transcription._load_whisper_model_class",
            side_effect=BackendNotAvailable("missing faster-whisper"),
        ):
            info = WhisperTranscriptionBackend().info()

        self.assertFalse(info.available)
        self.assertEqual(info.dependencies, ("faster-whisper",))

    def test_auto_model_maps_to_base_for_whisper(self):
        calls = {}

        class FakeWhisperModel:
            def __init__(self, model_name, device, compute_type):
                calls["model_name"] = model_name

            def transcribe(self, path, **request):
                return [], FakeInfo()

        module = types.ModuleType("faster_whisper")
        module.WhisperModel = FakeWhisperModel
        chunk = AudioChunk(data=b"\x00\x00" * 10, format=AudioFormat())

        with patch.dict(sys.modules, {"faster_whisper": module}):
            WhisperTranscriptionBackend().transcribe(chunk, VoiceKitConfig())

        self.assertEqual(calls["model_name"], "base")

    def test_model_load_errors_become_transcription_errors(self):
        class FakeWhisperModel:
            def __init__(self, model_name, device, compute_type):
                raise RuntimeError("cannot load")

        module = types.ModuleType("faster_whisper")
        module.WhisperModel = FakeWhisperModel
        chunk = AudioChunk(data=b"\x00\x00" * 10, format=AudioFormat())

        with patch.dict(sys.modules, {"faster_whisper": module}):
            with self.assertRaises(TranscriptionError):
                WhisperTranscriptionBackend().transcribe(chunk, VoiceKitConfig(transcription_model="tiny"))


if __name__ == "__main__":
    unittest.main()
