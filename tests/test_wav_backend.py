import os
import tempfile
import unittest

from auralis_voicekit import AudioChunk, AudioFormat, AuralisVoiceKit, VoiceKitConfig, write_wav
from auralis_voicekit.backends import create_default_registry


class WavBackendTests(unittest.TestCase):
    def test_wav_backend_is_registered(self):
        registry = create_default_registry()

        backend = registry.create_capture("wav")

        self.assertEqual(backend.info().name, "wav")
        self.assertEqual(list(backend.list_devices())[0].id, "wav-file")

    def test_wav_backend_emits_chunks_through_kit(self):
        audio_format = AudioFormat(sample_rate=1000, channels=1, sample_width=2)
        chunks = [AudioChunk(data=b"\x00\x00" * 50, format=audio_format)]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "source.wav")
            write_wav(path, chunks)
            captured = []
            kit = AuralisVoiceKit(
                VoiceKitConfig(
                    capture_backend="wav",
                    input_file=path,
                    sample_rate=1000,
                    capture_block_ms=50,
                )
            )

            kit.start_capture(captured.append)

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].format, audio_format)
        self.assertEqual(captured[0].metadata["chunk_index"], 0)


if __name__ == "__main__":
    unittest.main()
