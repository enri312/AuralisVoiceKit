import os
import unittest
from unittest.mock import patch

from auralis_voicekit import VoiceKitConfig


class VoiceKitConfigTests(unittest.TestCase):
    def test_defaults_are_portable(self):
        config = VoiceKitConfig()

        self.assertEqual(config.sample_rate, 16000)
        self.assertEqual(config.channels, 1)
        self.assertEqual(config.capture_backend, "null")
        self.assertEqual(config.transcription_backend, "null")
        self.assertEqual(config.transcription_model, "auto")
        self.assertTrue(config.privacy_mode)

    def test_from_env(self):
        env = {
            "AURALIS_SAMPLE_RATE": "48000",
            "AURALIS_CHANNELS": "2",
            "AURALIS_CAPTURE_BACKEND": "sounddevice",
            "AURALIS_TRANSCRIPTION_BACKEND": "openai",
            "AURALIS_TRANSCRIPTION_MODEL": "gpt-4o-transcribe",
            "AURALIS_TRANSCRIPTION_PROMPT": "Spanish customer support audio",
            "AURALIS_TRANSCRIPTION_RESPONSE_FORMAT": "text",
            "AURALIS_TRANSCRIPTION_DEVICE": "cpu",
            "AURALIS_TRANSCRIPTION_COMPUTE_TYPE": "int8",
            "AURALIS_TRANSCRIPTION_BEAM_SIZE": "3",
            "AURALIS_TRANSCRIPTION_VAD_FILTER": "true",
            "AURALIS_OUTPUT_VOICE": "Monica",
            "AURALIS_OUTPUT_RATE": "180",
            "AURALIS_OUTPUT_VOLUME": "70",
            "AURALIS_CAPTURE_BLOCK_MS": "25",
            "AURALIS_PRIVACY_MODE": "false",
        }

        with patch.dict(os.environ, env, clear=False):
            config = VoiceKitConfig.from_env()

        self.assertEqual(config.sample_rate, 48000)
        self.assertEqual(config.channels, 2)
        self.assertEqual(config.capture_backend, "sounddevice")
        self.assertEqual(config.transcription_backend, "openai")
        self.assertEqual(config.transcription_model, "gpt-4o-transcribe")
        self.assertEqual(config.transcription_prompt, "Spanish customer support audio")
        self.assertEqual(config.transcription_response_format, "text")
        self.assertEqual(config.transcription_device, "cpu")
        self.assertEqual(config.transcription_compute_type, "int8")
        self.assertEqual(config.transcription_beam_size, 3)
        self.assertTrue(config.transcription_vad_filter)
        self.assertEqual(config.output_voice, "Monica")
        self.assertEqual(config.output_rate, 180)
        self.assertEqual(config.output_volume, 70)
        self.assertEqual(config.capture_block_ms, 25)
        self.assertEqual(config.capture_block_frames, 1200)
        self.assertFalse(config.privacy_mode)

    def test_rejects_invalid_output_volume(self):
        with self.assertRaises(ValueError):
            VoiceKitConfig(output_volume=101)


if __name__ == "__main__":
    unittest.main()
