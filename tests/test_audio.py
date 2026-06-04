import io
import os
import struct
import tempfile
import unittest
from unittest.mock import patch
import wave

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    VoiceActivityConfig,
    VoiceActivityDetector,
    apply_gain_pcm16,
    calibrate_noise_pcm16,
    chunk_audio,
    chunk_to_wav_bytes,
    decode_audio_with_ffmpeg,
    ffmpeg_available,
    iter_wav_chunks,
    is_silent_pcm16,
    normalize_chunks_pcm16,
    normalize_pcm16,
    peak_pcm16,
    read_audio,
    read_audio_as_chunk,
    read_wav,
    read_wav_as_chunk,
    read_wav_metadata,
    resolve_ffmpeg_executable,
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

    def test_chunk_to_wav_bytes(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        chunk = AudioChunk(data=b"\x00\x00" * 8, format=audio_format)

        payload = chunk_to_wav_bytes(chunk)

        self.assertTrue(payload.startswith(b"RIFF"))
        with wave.open(io.BytesIO(payload), "rb") as wav_file:
            self.assertEqual(wav_file.getframerate(), 8000)
            self.assertEqual(wav_file.getnframes(), 8)

    def test_apply_gain_pcm16_scales_and_clips(self):
        chunk = AudioChunk(
            data=struct.pack("<hhh", 1000, -1000, 20000),
            format=AudioFormat(sample_rate=8000, channels=1, sample_width=2),
        )

        amplified = apply_gain_pcm16(chunk, 2.0)

        samples = struct.unpack("<hhh", amplified.data)
        self.assertEqual(samples, (2000, -2000, 32767))
        self.assertEqual(amplified.metadata["gain"], 2.0)

    def test_normalize_pcm16_reaches_target_peak(self):
        chunk = _constant_chunk(1000, samples=100, sample_rate=1000)

        normalized = normalize_pcm16(chunk, target_peak=0.5, max_gain=100.0)

        self.assertAlmostEqual(peak_pcm16(normalized), 0.5, places=3)
        self.assertGreater(normalized.metadata["normalization_gain"], 1.0)
        self.assertAlmostEqual(normalized.metadata["normalization_target_peak"], 0.5)

    def test_normalize_pcm16_respects_max_gain(self):
        chunk = _constant_chunk(1000, samples=100, sample_rate=1000)

        normalized = normalize_pcm16(chunk, target_peak=0.9, max_gain=2.0)

        self.assertAlmostEqual(normalized.metadata["normalization_gain"], 2.0)
        self.assertLess(peak_pcm16(normalized), 0.9)

    def test_normalize_pcm16_keeps_silence_silent(self):
        chunk = _constant_chunk(0, samples=100, sample_rate=1000)

        normalized = normalize_pcm16(chunk)

        self.assertEqual(normalized.data, chunk.data)
        self.assertEqual(normalized.metadata["normalization_gain"], 1.0)

    def test_normalize_chunks_pcm16_uses_shared_gain(self):
        chunks = [
            _constant_chunk(1000, samples=100, sample_rate=1000),
            _constant_chunk(2000, samples=100, sample_rate=1000),
        ]

        normalized = normalize_chunks_pcm16(chunks, target_peak=0.5, max_gain=100.0)

        self.assertEqual(len(normalized), 2)
        self.assertAlmostEqual(peak_pcm16(normalized[1]), 0.5, places=3)
        self.assertLess(peak_pcm16(normalized[0]), peak_pcm16(normalized[1]))
        self.assertEqual(
            normalized[0].metadata["normalization_gain"],
            normalized[1].metadata["normalization_gain"],
        )

    def test_chunk_audio_splits_pcm16_chunk(self):
        chunk = _constant_chunk(1000, samples=100, sample_rate=1000)

        chunks = list(chunk_audio(chunk, chunk_duration_ms=50))

        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0].data), 100)
        self.assertEqual(chunks[1].metadata["frame_offset"], 50)

    def test_read_wav_metadata_and_chunks(self):
        audio_format = AudioFormat(sample_rate=1000, channels=1, sample_width=2)
        chunks = [
            _constant_chunk(1000, samples=50, sample_rate=1000),
            _constant_chunk(2000, samples=50, sample_rate=1000),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, chunks)

            metadata = read_wav_metadata(path)
            read_chunks = read_wav(path, chunk_duration_ms=50)
            iter_chunks = list(iter_wav_chunks(path, chunk_duration_ms=50))

        self.assertEqual(metadata.format, audio_format)
        self.assertEqual(metadata.frames, 100)
        self.assertAlmostEqual(metadata.duration_seconds, 0.1)
        self.assertEqual(len(read_chunks), 2)
        self.assertEqual(len(iter_chunks), 2)
        self.assertEqual(read_chunks[0].metadata["chunk_index"], 0)
        self.assertEqual(read_chunks[1].metadata["frame_offset"], 50)

    def test_read_wav_as_chunk(self):
        chunks = [
            _constant_chunk(1000, samples=50, sample_rate=1000),
            _constant_chunk(2000, samples=50, sample_rate=1000),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, chunks)

            chunk = read_wav_as_chunk(path)

        self.assertEqual(chunk.format.sample_rate, 1000)
        self.assertEqual(len(chunk.data), 200)
        self.assertEqual(chunk.metadata["chunks"], 2)

    def test_read_audio_as_chunk_uses_wav_reader_for_wav(self):
        chunks = [_constant_chunk(1000, samples=50, sample_rate=1000)]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, chunks)

            chunk = read_audio_as_chunk(path)

        self.assertEqual(chunk.format.sample_rate, 1000)
        self.assertEqual(chunk.metadata["path"], path)

    def test_decode_audio_with_ffmpeg_returns_pcm16_chunk(self):
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": b"\x00\x00" * 8, "stderr": b""},
        )()

        with patch("auralis_voicekit.audio.shutil.which", return_value="ffmpeg.exe"):
            with patch("auralis_voicekit.audio.subprocess.run", return_value=completed) as run:
                chunk = decode_audio_with_ffmpeg("sample.mp3", sample_rate=8000, channels=1)

        self.assertEqual(chunk.data, b"\x00\x00" * 8)
        self.assertEqual(chunk.format.sample_rate, 8000)
        self.assertEqual(chunk.metadata["decoder"], "ffmpeg")
        self.assertEqual(chunk.metadata["source_format"], "mp3")
        self.assertIn("-i", run.call_args.args[0])

    def test_decode_audio_with_ffmpeg_reports_missing_executable(self):
        with patch("auralis_voicekit.audio.resolve_ffmpeg_executable", return_value=None):
            with self.assertRaisesRegex(Exception, "ffmpeg is required"):
                decode_audio_with_ffmpeg("sample.mp3")

    def test_read_audio_chunks_decoded_audio(self):
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": b"\x00\x00" * 100, "stderr": b""},
        )()

        with patch("auralis_voicekit.audio.shutil.which", return_value="ffmpeg.exe"):
            with patch("auralis_voicekit.audio.subprocess.run", return_value=completed):
                chunks = read_audio("sample.mp3", chunk_duration_ms=50, sample_rate=1000)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["decoder"], "ffmpeg")

    def test_ffmpeg_available_checks_path(self):
        with patch("auralis_voicekit.audio.shutil.which", return_value="ffmpeg.exe"):
            self.assertTrue(ffmpeg_available())

    def test_resolve_ffmpeg_executable_checks_portable_install(self):
        portable = os.path.join("C:\\Users\\test", "AuralisTools", "ffmpeg", "bin", "ffmpeg.exe")

        with patch("auralis_voicekit.audio.shutil.which", return_value=None):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test"}, clear=True):
                with patch("auralis_voicekit.audio.os.path.exists", return_value=True):
                    self.assertEqual(resolve_ffmpeg_executable(), portable)

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
