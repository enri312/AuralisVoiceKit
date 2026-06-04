import sys
import types
import unittest
from unittest.mock import patch

from auralis_voicekit.backends.sounddevice import SoundDeviceCaptureBackend


class SoundDeviceBackendTests(unittest.TestCase):
    def test_list_devices_maps_host_api_names(self):
        fake_sounddevice = types.SimpleNamespace()
        fake_sounddevice.default = types.SimpleNamespace(device=(0, -1))
        fake_sounddevice.query_hostapis = lambda: [{"name": "WASAPI"}, {"name": "ALSA"}]
        fake_sounddevice.query_devices = lambda: [
            {
                "name": "Primary microphone",
                "max_input_channels": 2,
                "hostapi": 1,
                "default_samplerate": 48000.0,
            },
            {
                "name": "Output only",
                "max_input_channels": 0,
                "hostapi": 0,
                "default_samplerate": 48000.0,
            },
        ]

        with patch.dict(sys.modules, {"sounddevice": fake_sounddevice}):
            devices = list(SoundDeviceCaptureBackend().list_devices())

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "Primary microphone")
        self.assertEqual(devices[0].host_api, "ALSA")
        self.assertTrue(devices[0].is_default)
        self.assertEqual(devices[0].metadata["default_samplerate"], 48000.0)


if __name__ == "__main__":
    unittest.main()
