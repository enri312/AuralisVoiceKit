import sys
import types
import unittest
from unittest.mock import patch

from auralis_voicekit import BackendNotAvailable, VoiceKitConfig
from auralis_voicekit.backends import PyAudioCaptureBackend, create_default_registry


class FakeStream:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.closed = False
        FakeStream.instances.append(self)

    def start_stream(self):
        self.started = True

    def stop_stream(self):
        self.stopped = True

    def close(self):
        self.closed = True


class FakePyAudioInstance:
    instances = []
    stream_class = FakeStream

    def __init__(self):
        self.terminated = False
        FakePyAudioInstance.instances.append(self)

    def get_device_count(self):
        return 2

    def get_default_input_device_info(self):
        return {"index": 1}

    def get_host_api_info_by_index(self, index):
        return {0: {"name": "Core Audio"}, 1: {"name": "ALSA"}}[index]

    def get_device_info_by_index(self, index):
        devices = [
            {
                "index": 0,
                "name": "Output only",
                "maxInputChannels": 0,
                "hostApi": 0,
                "defaultSampleRate": 48000.0,
            },
            {
                "index": 1,
                "name": "USB microphone",
                "maxInputChannels": 2,
                "hostApi": 1,
                "defaultSampleRate": 44100.0,
            },
        ]
        return devices[index]

    def open(self, **kwargs):
        return self.stream_class(**kwargs)

    def terminate(self):
        self.terminated = True


def _fake_pyaudio():
    return types.SimpleNamespace(
        PyAudio=FakePyAudioInstance,
        paContinue=0,
        paInt16=8,
    )


class PyAudioBackendTests(unittest.TestCase):
    def setUp(self):
        FakeStream.instances = []
        FakePyAudioInstance.instances = []
        FakePyAudioInstance.stream_class = FakeStream

    def test_registry_includes_pyaudio_capture_backend(self):
        backend_names = {
            (info.kind, info.name)
            for info in create_default_registry().backend_info()
        }

        self.assertIn(("capture", "pyaudio"), backend_names)

    def test_info_reports_missing_optional_dependency(self):
        with patch.dict(sys.modules, {"pyaudio": None}):
            info = PyAudioCaptureBackend().info()

        self.assertFalse(info.available)
        self.assertEqual(info.dependencies, ("pyaudio",))
        self.assertIn("auralisvoicekit[pyaudio]", info.reason)

    def test_list_devices_maps_host_api_and_default(self):
        with patch.dict(sys.modules, {"pyaudio": _fake_pyaudio()}):
            devices = list(PyAudioCaptureBackend().list_devices())

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].id, "1")
        self.assertEqual(devices[0].name, "USB microphone")
        self.assertEqual(devices[0].host_api, "ALSA")
        self.assertTrue(devices[0].is_default)
        self.assertEqual(devices[0].metadata["default_sample_rate"], 44100.0)
        self.assertTrue(FakePyAudioInstance.instances[-1].terminated)

    def test_resolve_input_device_by_name_or_default(self):
        with patch.dict(sys.modules, {"pyaudio": _fake_pyaudio()}):
            backend = PyAudioCaptureBackend()

            self.assertIsNone(backend.resolve_input_device(None))
            self.assertIsNone(backend.resolve_input_device("default"))
            self.assertEqual(backend.resolve_input_device("USB"), 1)
            self.assertEqual(backend.resolve_input_device("1"), 1)

    def test_start_passes_resolved_device_and_frames_per_buffer(self):
        captured = []

        with patch.dict(sys.modules, {"pyaudio": _fake_pyaudio()}):
            backend = PyAudioCaptureBackend()
            config = VoiceKitConfig(
                input_device="USB",
                sample_rate=16000,
                channels=1,
                capture_block_ms=25,
            )

            backend.start(config, captured.append)
            stream = FakeStream.instances[0]
            stream.kwargs["stream_callback"](b"\x00\x00", 1, None, 0)
            backend.stop()

        self.assertTrue(stream.started)
        self.assertTrue(stream.stopped)
        self.assertTrue(stream.closed)
        self.assertEqual(stream.kwargs["input_device_index"], 1)
        self.assertEqual(stream.kwargs["frames_per_buffer"], 400)
        self.assertEqual(stream.kwargs["format"], 8)
        self.assertFalse(stream.kwargs["start"])
        self.assertEqual(captured[0].data, b"\x00\x00")
        self.assertTrue(FakePyAudioInstance.instances[-1].terminated)

    def test_start_closes_stream_when_start_fails(self):
        class FailingStream(FakeStream):
            def start_stream(self):
                raise RuntimeError("cannot start")

        FakePyAudioInstance.stream_class = FailingStream

        with patch.dict(sys.modules, {"pyaudio": _fake_pyaudio()}):
            backend = PyAudioCaptureBackend()
            with self.assertRaises(RuntimeError):
                backend.start(VoiceKitConfig(), lambda chunk: None)

        self.assertTrue(FailingStream.instances[0].closed)
        self.assertTrue(FakePyAudioInstance.instances[-1].terminated)

    def test_start_requires_pyaudio_dependency(self):
        with patch.dict(sys.modules, {"pyaudio": None}):
            with self.assertRaises(BackendNotAvailable):
                PyAudioCaptureBackend().start(VoiceKitConfig(), lambda chunk: None)


if __name__ == "__main__":
    unittest.main()
