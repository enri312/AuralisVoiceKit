import sys
import types
import unittest
from unittest.mock import patch

from auralis_voicekit import AudioDeviceNotFound, BackendNotAvailable, VoiceKitConfig
from auralis_voicekit.backends import WasapiCaptureBackend, create_default_registry


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


def _fake_sounddevice(*, include_wasapi: bool = True):
    hostapis = [{"name": "Windows WASAPI"}, {"name": "MME"}] if include_wasapi else [{"name": "MME"}]
    fake_sounddevice = types.SimpleNamespace()
    fake_sounddevice.default = types.SimpleNamespace(device=(1, -1))
    fake_sounddevice.query_hostapis = lambda: hostapis
    fake_sounddevice.query_devices = lambda: [
        {
            "name": "MME microphone",
            "max_input_channels": 1,
            "hostapi": 1,
            "default_samplerate": 44100.0,
        },
        {
            "name": "WASAPI microphone",
            "max_input_channels": 2,
            "hostapi": 0,
            "default_samplerate": 48000.0,
        },
        {
            "name": "WASAPI output",
            "max_input_channels": 0,
            "hostapi": 0,
            "default_samplerate": 48000.0,
        },
    ]
    fake_sounddevice.RawInputStream = FakeRawInputStream
    return fake_sounddevice


class WasapiBackendTests(unittest.TestCase):
    def setUp(self):
        FakeRawInputStream.instances = []

    def test_registry_includes_wasapi_capture_backend(self):
        registry = create_default_registry()
        backend = registry.create_capture("wasapi")

        self.assertIsInstance(backend, WasapiCaptureBackend)

    def test_info_reports_non_windows_unavailable(self):
        info = WasapiCaptureBackend(system="Linux").info()

        self.assertFalse(info.available)
        self.assertIn("only available on Windows", info.reason)

    def test_info_reports_missing_wasapi_host_api(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice(include_wasapi=False)}):
            info = WasapiCaptureBackend(system="Windows").info()

        self.assertFalse(info.available)
        self.assertIn("WASAPI host API", info.reason)

    def test_list_devices_filters_to_wasapi_inputs(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            devices = list(WasapiCaptureBackend(system="Windows").list_devices())

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "WASAPI microphone")
        self.assertEqual(devices[0].host_api, "Windows WASAPI")
        self.assertTrue(devices[0].is_default)

    def test_resolve_default_chooses_wasapi_device(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            backend = WasapiCaptureBackend(system="Windows")

            self.assertEqual(backend.resolve_input_device(None), 1)
            self.assertEqual(backend.resolve_input_device("default"), 1)
            self.assertEqual(backend.resolve_input_device(1), 1)
            self.assertEqual(backend.resolve_input_device("1"), 1)
            self.assertEqual(backend.resolve_input_device("WASAPI"), 1)

    def test_resolve_rejects_non_wasapi_device_name(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            backend = WasapiCaptureBackend(system="Windows")

            with self.assertRaises(AudioDeviceNotFound):
                backend.resolve_input_device("MME microphone")
            with self.assertRaises(AudioDeviceNotFound):
                backend.resolve_input_device(0)

    def test_start_passes_wasapi_device_to_sounddevice(self):
        captured = []

        with patch.dict(sys.modules, {"sounddevice": _fake_sounddevice()}):
            backend = WasapiCaptureBackend(system="Windows")
            backend.start(
                VoiceKitConfig(
                    capture_backend="wasapi",
                    input_device="default",
                    sample_rate=16000,
                    channels=1,
                    capture_block_ms=25,
                ),
                captured.append,
            )
            stream = FakeRawInputStream.instances[0]
            stream.kwargs["callback"](b"\x00\x00", 1, None, None)
            backend.stop()

        self.assertEqual(stream.kwargs["device"], 1)
        self.assertEqual(stream.kwargs["blocksize"], 400)
        self.assertTrue(stream.started)
        self.assertTrue(stream.closed)
        self.assertEqual(captured[0].data, b"\x00\x00")

    def test_list_devices_rejects_non_windows(self):
        with self.assertRaises(BackendNotAvailable):
            WasapiCaptureBackend(system="Darwin").list_devices()


if __name__ == "__main__":
    unittest.main()
