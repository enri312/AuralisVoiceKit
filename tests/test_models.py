import unittest

from auralis_voicekit import AudioChunk, AudioFormat


class ModelTests(unittest.TestCase):
    def test_audio_chunk_duration(self):
        audio_format = AudioFormat(sample_rate=16000, channels=1, sample_width=2)
        chunk = AudioChunk(data=b"\x00" * 32000, format=audio_format)

        self.assertEqual(chunk.duration_seconds, 1.0)


if __name__ == "__main__":
    unittest.main()
