import os
import struct
import threading
import time
import tempfile
import unittest
from unittest.mock import patch

from auralis_voicekit import (
    AuralisVoiceKit,
    AudioChunk,
    AudioFormat,
    VoiceActivityConfig,
    VoiceSession,
    VoiceSessionConfig,
    write_wav,
)


def _constant_chunk(amplitude: int, samples: int = 100, sample_rate: int = 1000) -> AudioChunk:
    data = struct.pack("<" + "h" * samples, *([amplitude] * samples))
    audio_format = AudioFormat(sample_rate=sample_rate, channels=1, sample_width=2)
    return AudioChunk(data=data, format=audio_format)


def _session() -> VoiceSession:
    return VoiceSession(
        AuralisVoiceKit(),
        VoiceSessionConfig(
            chunk_duration_ms=100,
            voice_activity=VoiceActivityConfig(
                threshold=0.01,
                min_voice_ms=100,
                max_silence_ms=200,
                pre_speech_ms=0,
            ),
        ),
    )


class VoiceSessionTests(unittest.TestCase):
    def test_transcribe_chunks_returns_voice_turns(self):
        chunks = [
            _constant_chunk(0),
            _constant_chunk(6000),
            _constant_chunk(6000),
            _constant_chunk(0),
        ]

        turns = _session().transcribe_chunks(chunks)

        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].index, 1)
        self.assertEqual(turns[0].text, "")
        self.assertEqual(turns[0].transcript.source, "null")
        self.assertEqual(turns[0].transcript.metadata["segment_index"], 1)
        self.assertEqual(turns[0].transcript.metadata["segment_chunks"], 3)
        self.assertGreater(turns[0].duration_seconds, 0)
        self.assertGreater(turns[0].rms, 0)

    def test_on_turn_callback_receives_turns(self):
        seen = []
        chunks = [_constant_chunk(6000), _constant_chunk(0)]

        turns = _session().transcribe_chunks(chunks, on_turn=seen.append)

        self.assertEqual(turns, seen)

    def test_transcribe_wav_uses_chunk_duration(self):
        chunks = [_constant_chunk(6000), _constant_chunk(6000), _constant_chunk(0)]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "turn.wav")
            write_wav(path, chunks)
            turns = _session().transcribe_wav(path)

        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].transcript.metadata["path"], path)

    def test_transcribe_file_uses_generic_audio_reader(self):
        chunks = [_constant_chunk(6000), _constant_chunk(6000), _constant_chunk(0)]

        with patch("auralis_voicekit.session.read_audio", return_value=chunks) as read_audio:
            turns = _session().transcribe_file("sample.mp3")

        self.assertEqual(len(turns), 1)
        read_audio.assert_called_once()
        self.assertEqual(read_audio.call_args.kwargs["ffmpeg_executable"], "ffmpeg")

    def test_transcribe_chunks_can_normalize_segments(self):
        chunks = [_constant_chunk(1000), _constant_chunk(1000), _constant_chunk(0)]
        session = VoiceSession(
            AuralisVoiceKit(),
            VoiceSessionConfig(
                voice_activity=VoiceActivityConfig(
                    threshold=0.01,
                    min_voice_ms=100,
                    max_silence_ms=200,
                    pre_speech_ms=0,
                ),
                normalize_segments=True,
                normalization_target_peak=0.5,
                normalization_max_gain=100.0,
            ),
        )

        turns = session.transcribe_chunks(chunks)

        self.assertEqual(len(turns), 1)
        self.assertIn("normalization_gain", turns[0].transcript.metadata)
        self.assertAlmostEqual(turns[0].transcript.metadata["normalization_target_peak"], 0.5)

    def test_max_turns_limits_transcription(self):
        chunks = [
            _constant_chunk(6000),
            _constant_chunk(0),
            _constant_chunk(0),
            _constant_chunk(6000),
            _constant_chunk(0),
        ]
        session = VoiceSession(
            AuralisVoiceKit(),
            VoiceSessionConfig(
                voice_activity=VoiceActivityConfig(
                    threshold=0.01,
                    min_voice_ms=100,
                    max_silence_ms=100,
                    pre_speech_ms=0,
                ),
                max_turns=1,
            ),
        )

        turns = session.transcribe_chunks(chunks)

        self.assertEqual(len(turns), 1)

    def test_on_turn_can_cancel_remaining_transcriptions(self):
        chunks = [
            _constant_chunk(6000),
            _constant_chunk(0),
            _constant_chunk(0),
            _constant_chunk(6000),
            _constant_chunk(0),
        ]
        session = VoiceSession(
            AuralisVoiceKit(),
            VoiceSessionConfig(
                voice_activity=VoiceActivityConfig(
                    threshold=0.01,
                    min_voice_ms=100,
                    max_silence_ms=100,
                    pre_speech_ms=0,
                ),
            ),
        )

        turns = session.transcribe_chunks(chunks, on_turn=lambda turn: False)

        self.assertEqual(len(turns), 1)
        self.assertTrue(session.is_cancelled)

    def test_cancelled_session_skips_transcription_until_reset(self):
        session = _session()
        chunks = [_constant_chunk(6000), _constant_chunk(0)]

        session.cancel()
        self.assertEqual(session.transcribe_chunks(chunks), [])

        session.reset_cancel()
        self.assertEqual(len(session.transcribe_chunks(chunks)), 1)

    def test_capture_for_starts_and_stops_null_capture(self):
        kit = AuralisVoiceKit()
        session = VoiceSession(kit)

        chunks = session.capture_for(0)

        self.assertEqual(chunks, [])
        self.assertFalse(kit.capture.is_running)

    def test_capture_for_can_be_cancelled_from_another_thread(self):
        kit = AuralisVoiceKit()
        session = VoiceSession(
            kit,
            VoiceSessionConfig(capture_poll_interval_ms=5),
        )
        result = []

        worker = threading.Thread(target=lambda: result.extend(session.capture_for(5.0)))
        worker.start()
        self._wait_for(lambda: kit.capture.is_running)

        session.cancel()
        worker.join(timeout=1.0)

        self.assertFalse(worker.is_alive())
        self.assertEqual(result, [])
        self.assertFalse(kit.capture.is_running)
        self.assertTrue(session.is_cancelled)

    def test_capture_for_callback_can_request_cancel(self):
        kit = AuralisVoiceKit()
        session = VoiceSession(
            kit,
            VoiceSessionConfig(capture_poll_interval_ms=5),
        )
        result = []

        worker = threading.Thread(
            target=lambda: result.extend(
                session.capture_for(5.0, on_chunk=lambda chunk: False)
            )
        )
        worker.start()
        self._wait_for(lambda: kit.capture.is_running)
        kit.capture.push(_constant_chunk(6000))
        worker.join(timeout=1.0)

        self.assertFalse(worker.is_alive())
        self.assertEqual(len(result), 1)
        self.assertFalse(kit.capture.is_running)
        self.assertTrue(session.is_cancelled)

    def test_close_stops_active_capture(self):
        kit = AuralisVoiceKit()
        session = VoiceSession(
            kit,
            VoiceSessionConfig(capture_poll_interval_ms=5),
        )
        worker = threading.Thread(target=lambda: session.capture_for(5.0))
        worker.start()
        self._wait_for(lambda: kit.capture.is_running)

        session.close()
        worker.join(timeout=1.0)

        self.assertFalse(worker.is_alive())
        self.assertFalse(kit.capture.is_running)
        self.assertTrue(session.is_closed)

    def test_context_manager_closes_session(self):
        with VoiceSession() as session:
            self.assertFalse(session.is_closed)

        self.assertTrue(session.is_closed)
        with self.assertRaises(RuntimeError):
            session.capture_for(0)

    def test_session_config_rejects_invalid_capture_poll_interval(self):
        with self.assertRaises(ValueError):
            VoiceSessionConfig(capture_poll_interval_ms=0)

    @staticmethod
    def _wait_for(predicate, timeout: float = 1.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.005)
        raise AssertionError("condition was not met before timeout")


if __name__ == "__main__":
    unittest.main()
