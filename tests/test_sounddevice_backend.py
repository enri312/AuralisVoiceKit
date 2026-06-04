import sys
import types
import unittest
from unittest.mock import patch

from auralis_voicekit import VoiceKitConfig
from auralis_voicekit.backends.sounddevice import SoundDeviceCaptureBackend


class FakeRawInputStream:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.closed = False
        FakeRawInputStream.instances.append(self)

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def _fake_sounddevice():
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
    fake_sounddevice.RawInputStream = FakeRawInputStream
    return fake_sounddevice


class SoundDeviceBackendTests(unittest.TestCase):
    def setUp(self):
        FakeRawInputStream.instances = []

    def test_list_devices_maps_host_api_names(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            devices = list(SoundDeviceCaptureBackend().list_devices())

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "Primary microphone")
        self.assertEqual(devices[0].host_api, "ALSA")
        self.assertTrue(devices[0].is_default)
        self.assertEqual(devices[0].metadata["default_samplerate"], 48000.0)

    def test_resolve_input_device_by_name_or_default(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            backend = SoundDeviceCaptureBackend()

            self.assertIsNone(backend.resolve_input_device(None))
            self.assertIsNone(backend.resolve_input_device("default"))
            self.assertEqual(backend.resolve_input_device("Primary"), 0)
            self.assertEqual(backend.resolve_input_device("0"), 0)

    def test_start_passes_resolved_device_and_blocksize(self):
        captured = []

        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            backend = SoundDeviceCaptureBackend()
            config = VoiceKitConfig(
                input_device="Primary",
                sample_rate=16000,
                channels=1,
                capture_block_ms=25,
            )

            backend.start(config, captured.append)
            stream = FakeRawInputStream.instances[0]
            stream.kwargs["callback"](b"\x00\x00", 1, None, None)
            backend.stop()

        self.assertTrue(stream.started)
        self.assertTrue(stream.stopped)
        self.assertTrue(stream.closed)
        self.assertEqual(stream.kwargs["device"], 0)
        self.assertEqual(stream.kwargs["blocksize"], 400)
        self.assertEqual(captured[0].data, b"\x00\x00")

    def test_start_closes_stream_when_start_fails(self):
        class FailingRawInputStream(FakeRawInputStream):
            def start(self):
                raise RuntimeError("cannot start")

        fake_sounddevice = _fake_sounddevice()
        fake_sounddevice.RawInputStream = FailingRawInputStream

        with patch.dict(sys.modules, {"sounddevice": fake_sounddevice}):
            backend = SoundDeviceCaptureBackend()
            with self.assertRaises(RuntimeError):
                backend.start(VoiceKitConfig(), lambda chunk: None)

        self.assertTrue(FailingRawInputStream.instances[0].closed)


if __name__ == "__main__":
    unittest.main()
