import os
import struct
import tempfile
import unittest
import wave

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    VoiceActivityConfig,
    VoiceActivityDetector,
    calibrate_noise_pcm16,
    is_silent_pcm16,
    peak_pcm16,
    rms_pcm16,
    segment_voice_pcm16,
    write_wav,
)


def _constant_chunk(amplitude: int, samples: int = 100, sample_rate: int = 1000) -> AudioChunk:
    data = struct.pack("<" + "h" * samples, *([amplitude] * samples))
    audio_format = AudioFormat(sample_rate=sample_rate, channels=1, sample_width=2)
    return AudioChunk(data=data, format=audio_format)


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

    def test_calibrate_noise_profile(self):
        chunks = [_constant_chunk(100), _constant_chunk(120), _constant_chunk(80)]

        profile = calibrate_noise_pcm16(chunks, multiplier=3.0, min_threshold=0.01)

        self.assertEqual(profile.chunks, 3)
        self.assertAlmostEqual(profile.duration_seconds, 0.3)
        self.assertGreater(profile.noise_floor, 0)
        self.assertEqual(profile.threshold, 0.01)

    def test_voice_activity_detector_uses_noise_profile_threshold(self):
        profile = calibrate_noise_pcm16([_constant_chunk(400)], multiplier=3.0, min_threshold=0.01)
        detector = VoiceActivityDetector(noise_profile=profile)

        self.assertFalse(detector.is_voice(_constant_chunk(500)))
        self.assertTrue(detector.is_voice(_constant_chunk(5000)))

    def test_segment_voice_pcm16_groups_voice_with_preroll_and_trailing_silence(self):
        chunks = [
            _constant_chunk(0),
            _constant_chunk(0),
            _constant_chunk(5000),
            _constant_chunk(5000),
            _constant_chunk(5000),
            _constant_chunk(0),
            _constant_chunk(0),
        ]
        config = VoiceActivityConfig(
            threshold=0.01,
            min_voice_ms=150,
            max_silence_ms=200,
            pre_speech_ms=100,
        )

        segments = segment_voice_pcm16(chunks, config=config)

        self.assertEqual(len(segments), 1)
        self.assertEqual(len(segments[0].chunks), 6)
        self.assertAlmostEqual(segments[0].duration_seconds, 0.6)
        self.assertGreater(segments[0].rms, 0.01)

    def test_segment_voice_pcm16_ignores_short_spikes(self):
        chunks = [_constant_chunk(0), _constant_chunk(5000), _constant_chunk(0)]
        config = VoiceActivityConfig(threshold=0.01, min_voice_ms=200)

        self.assertEqual(segment_voice_pcm16(chunks, config=config), [])


if __name__ == "__main__":
    unittest.main()
