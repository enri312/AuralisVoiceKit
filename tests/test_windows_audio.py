import unittest

from auralis_voicekit import windows_audio_error_hint


class WindowsAudioHintTests(unittest.TestCase):
    def test_detects_windows_microphone_permission_error(self):
        hint = windows_audio_error_hint(
            "Error opening stream: [WinError 5] Access is denied",
            backend="wasapi",
            device="default",
            system="Windows",
        )

        self.assertEqual(hint.category, "microphone_permission")
        self.assertIn("Privacy", hint.format_hint())
        self.assertEqual(hint.backend, "wasapi")
        self.assertEqual(hint.device, "default")

    def test_detects_invalid_input_device_error(self):
        hint = windows_audio_error_hint(
            "PortAudioError: Invalid device [PaErrorCode -9996]",
            backend="sounddevice",
            system="Windows",
        )

        self.assertEqual(hint.category, "input_device")
        self.assertIn("doctor --devices --backend wasapi", hint.format_hint())

    def test_detects_host_api_error(self):
        hint = windows_audio_error_hint(
            "Unanticipated host error [PaErrorCode -9999]",
            backend="wasapi",
            system="Windows",
        )

        self.assertEqual(hint.category, "host_api")
        self.assertIn("exclusive", hint.format_hint())

    def test_detects_backend_selection_error_before_dependency_words(self):
        hint = windows_audio_error_hint(
            "Unknown capture backend 'missing'. Available: null, sounddevice, wasapi, wav.",
            backend="missing",
            system="Windows",
        )

        self.assertEqual(hint.category, "backend_selection")
        self.assertIn("auralis backends", hint.format_hint())

    def test_non_windows_returns_platform_note(self):
        hint = windows_audio_error_hint("Invalid device", system="Linux")

        self.assertEqual(hint.category, "not_windows")


if __name__ == "__main__":
    unittest.main()
