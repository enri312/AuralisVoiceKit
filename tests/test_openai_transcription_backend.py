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
from auralis_voicekit.backends.openai_transcription import OpenAITranscriptionBackend


class FakeTranscriptionResponse:
    text = "hola mundo"

    def model_dump(self):
        return {"text": self.text, "request_id": "test-request"}


class OpenAITranscriptionBackendTests(unittest.TestCase):
    def test_transcribe_sends_wav_file_to_openai_client(self):
        captured = {}

        class FakeTranscriptions:
            def create(self, **request):
                captured.update(request)
                return FakeTranscriptionResponse()

        class FakeOpenAI:
            def __init__(self):
                self.audio = types.SimpleNamespace(transcriptions=FakeTranscriptions())

        openai_module = types.ModuleType("openai")
        openai_module.OpenAI = FakeOpenAI
        chunk = AudioChunk(
            data=b"\x00\x00" * 8,
            format=AudioFormat(sample_rate=8000, channels=1, sample_width=2),
        )
        config = VoiceKitConfig(
            transcription_model="gpt-4o-transcribe",
            language="es",
            transcription_prompt="audio claro",
            transcription_response_format="json",
        )

        with patch.dict(sys.modules, {"openai": openai_module}):
            result = OpenAITranscriptionBackend().transcribe(chunk, config)

        self.assertEqual(result.text, "hola mundo")
        self.assertEqual(result.language, "es")
        self.assertEqual(result.source, "openai")
        self.assertEqual(captured["model"], "gpt-4o-transcribe")
        self.assertEqual(captured["language"], "es")
        self.assertEqual(captured["prompt"], "audio claro")
        self.assertEqual(captured["response_format"], "json")
        self.assertEqual(captured["file"].name, "audio.wav")
        self.assertTrue(captured["file"].getvalue().startswith(b"RIFF"))
        self.assertEqual(result.metadata["request_id"], "test-request")

    def test_info_reports_missing_openai_dependency(self):
        with patch(
            "auralis_voicekit.backends.openai_transcription._load_openai_client_class",
            side_effect=BackendNotAvailable("missing openai"),
        ):
            info = OpenAITranscriptionBackend().info()

        self.assertFalse(info.available)
        self.assertEqual(info.dependencies, ("openai",))

    def test_transcribe_rejects_large_payloads(self):
        openai_module = types.ModuleType("openai")
        openai_module.OpenAI = object
        chunk = AudioChunk(
            data=b"\x00\x00" * 8,
            format=AudioFormat(sample_rate=8000, channels=1, sample_width=2),
        )

        with patch.dict(sys.modules, {"openai": openai_module}):
            with patch(
                "auralis_voicekit.backends.openai_transcription.OPENAI_AUDIO_UPLOAD_LIMIT_BYTES",
                8,
            ):
                with self.assertRaises(TranscriptionError):
                    OpenAITranscriptionBackend().transcribe(chunk, VoiceKitConfig())


if __name__ == "__main__":
    unittest.main()
