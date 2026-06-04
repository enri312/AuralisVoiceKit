import os
import struct
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

    def test_capture_for_starts_and_stops_null_capture(self):
        kit = AuralisVoiceKit()
        session = VoiceSession(kit)

        chunks = session.capture_for(0)

        self.assertEqual(chunks, [])
        self.assertFalse(kit.capture.is_running)


if __name__ == "__main__":
    unittest.main()
