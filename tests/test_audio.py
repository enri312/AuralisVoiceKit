import os
import tempfile
import unittest
import wave

from auralis_voicekit import AudioChunk, AudioFormat, is_silent_pcm16, peak_pcm16, rms_pcm16, write_wav


class AudioHelperTests(unittest.TestCase):
    def test_pcm16_energy_helpers(self):
        audio_format = AudioFormat(sample_rate=16000, channels=1, sample_width=2)
        chunk = AudioChunk(data=b"\x00\x00\xff\x7f\x00\x80", format=audio_format)

        self.assertGreater(rms_pcm16(chunk), 0.5)
        self.assertAlmostEqual(peak_pcm16(chunk), 1.0, places=4)
        self.assertFalse(is_silent_pcm16(chunk))

    def test_silent_chunk(self):
        chunk = AudioChunk(data=b"\x00\x00" * 100, format=AudioFormat())

        self.assertTrue(is_silent_pcm16(chunk))
        self.assertEqual(rms_pcm16(chunk), 0.0)
        self.assertEqual(peak_pcm16(chunk), 0.0)

    def test_write_wav(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        chunks = [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, chunks)

            with wave.open(path, "rb") as wav_file:
                self.assertEqual(wav_file.getframerate(), 8000)
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getsampwidth(), 2)
                self.assertEqual(wav_file.getnframes(), 8)


if __name__ == "__main__":
    unittest.main()
