import unittest

from auralis_voicekit import AuralisVoiceKit, AudioChunk, AudioFormat, VoiceEventType


class AuralisVoiceKitTests(unittest.TestCase):
    def test_null_transcription_returns_empty_result(self):
        kit = AuralisVoiceKit()
        chunk = AudioChunk(
            data=b"\x00\x00" * 16000,
            format=AudioFormat(sample_rate=16000, channels=1, sample_width=2),
        )

        result = kit.transcribe(chunk)

        self.assertEqual(result.text, "")
        self.assertEqual(result.source, "null")
        self.assertAlmostEqual(result.metadata["duration_seconds"], 1.0)

    def test_capture_emits_privacy_safe_audio_event(self):
        kit = AuralisVoiceKit()
        seen = []
        kit.events.subscribe(VoiceEventType.AUDIO_CHUNK, lambda event: seen.append(event.payload))

        kit.start_capture()
        kit.capture.push(AudioChunk(data=b"\x00\x00", format=AudioFormat()))
        kit.stop_capture()

        self.assertIn("duration_seconds", seen[0])
        self.assertNotIn("bytes", seen[0])


if __name__ == "__main__":
    unittest.main()
