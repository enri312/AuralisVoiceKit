import unittest

from auralis_voicekit import (
    AuralisVoiceKit,
    AudioChunk,
    AudioFormat,
    VoiceEventType,
    VoiceKitConfig,
    __version__,
    backend_inventory,
)
from auralis_voicekit.backends import BackendInfo, create_default_registry


class FailingOutputBackend:
    name = "failing"

    def __init__(self) -> None:
        self.utterances: list[str] = []

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="output")

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        self.utterances.append(text)
        raise RuntimeError("output failed")


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

    def test_speak_emits_output_events(self):
        kit = AuralisVoiceKit()
        seen = []
        kit.events.subscribe(VoiceEventType.OUTPUT_STARTED, lambda event: seen.append(event.payload))
        kit.events.subscribe(VoiceEventType.OUTPUT_COMPLETED, lambda event: seen.append(event.payload))

        kit.speak("Hola")

        self.assertEqual(seen, [{"backend": "null"}, {"backend": "null"}])
        self.assertEqual(kit.output.utterances, ["Hola"])

    def test_output_queue_drains_speech_in_order(self):
        kit = AuralisVoiceKit()
        seen = []
        kit.events.subscribe(VoiceEventType.OUTPUT_STARTED, lambda event: seen.append(event.payload))
        kit.events.subscribe(VoiceEventType.OUTPUT_COMPLETED, lambda event: seen.append(event.payload))

        size = kit.queue_speech_many(["Uno", "   ", "Dos"])
        spoken = kit.drain_output_queue()

        self.assertEqual(size, 2)
        self.assertEqual(spoken, 2)
        self.assertEqual(kit.output_queue_size, 0)
        self.assertEqual(kit.output.utterances, ["Uno", "Dos"])
        self.assertEqual(
            seen,
            [
                {"backend": "null"},
                {"backend": "null"},
                {"backend": "null"},
                {"backend": "null"},
            ],
        )
        self.assertTrue(all("text" not in payload for payload in seen))

    def test_output_queue_can_drain_with_limit_and_clear_remaining_items(self):
        kit = AuralisVoiceKit()
        kit.queue_speech_many(["Uno", "Dos", "Tres"])

        spoken = kit.drain_output_queue(limit=2)
        cleared = kit.clear_output_queue()

        self.assertEqual(spoken, 2)
        self.assertEqual(cleared, 1)
        self.assertEqual(kit.output_queue_size, 0)
        self.assertEqual(kit.output.utterances, ["Uno", "Dos"])

    def test_output_queue_rejects_negative_limit(self):
        kit = AuralisVoiceKit()
        kit.queue_speech("Uno")

        with self.assertRaises(ValueError):
            kit.drain_output_queue(limit=-1)

        self.assertEqual(kit.output_queue_size, 1)
        self.assertEqual(kit.output.utterances, [])

    def test_output_queue_keeps_current_item_when_backend_fails(self):
        registry = create_default_registry()
        registry.register_output("failing", FailingOutputBackend)
        kit = AuralisVoiceKit(VoiceKitConfig(output_backend="failing"), registry=registry)
        kit.queue_speech_many(["Uno", "Dos"])

        with self.assertRaisesRegex(RuntimeError, "output failed"):
            kit.drain_output_queue()

        self.assertEqual(kit.output_queue_size, 2)
        self.assertEqual(kit.output.utterances, ["Uno"])

    def test_backend_inventory_is_public_safe(self):
        kit = AuralisVoiceKit()

        inventory = kit.backend_inventory()
        function_inventory = backend_inventory()
        backend_keys = {
            f"{backend['kind']}:{backend['name']}" for backend in inventory["backends"]
        }
        backends = {
            f"{backend['kind']}:{backend['name']}": backend for backend in inventory["backends"]
        }

        self.assertEqual(inventory["version"], __version__)
        self.assertEqual(function_inventory["version"], __version__)
        self.assertIn("capture:null", backend_keys)
        self.assertIn("transcription:null", backend_keys)
        self.assertIn("output:system", backend_keys)
        self.assertEqual(inventory["counts"]["total"], len(inventory["backends"]))
        self.assertFalse(inventory["content_policy"]["records_local_paths"])
        self.assertFalse(inventory["content_policy"]["records_credentials"])
        self.assertEqual(backends["capture:pyaudio"]["install_plan"]["python_extra"], "pyaudio")
        self.assertEqual(backends["capture:wasapi"]["install_plan"]["python_extra"], "sounddevice")
        self.assertEqual(backends["transcription:whisper"]["install_plan"]["python_extra"], "whisper")
        self.assertEqual(
            backends["transcription:whisper"]["install_plan"]["pip_command"],
            'python -m pip install "auralisvoicekit[whisper]"',
        )
        self.assertEqual(backends["transcription:whisper"]["freedom_policy"]["category"], "free-local")
        self.assertTrue(backends["transcription:whisper"]["freedom_policy"]["free_default"])
        self.assertFalse(backends["transcription:whisper"]["freedom_policy"]["proprietary"])
        self.assertEqual(backends["transcription:openai"]["freedom_policy"]["category"], "proprietary-api")
        self.assertFalse(backends["transcription:openai"]["freedom_policy"]["free_default"])
        self.assertTrue(backends["transcription:openai"]["freedom_policy"]["network_required"])
        self.assertTrue(backends["transcription:openai"]["freedom_policy"]["proprietary"])
        self.assertIn("never installed or selected by default", backends["transcription:openai"]["freedom_policy"]["note"])
        self.assertEqual(backends["output:system"]["freedom_policy"]["category"], "system-local")
        self.assertFalse(backends["output:system"]["freedom_policy"]["network_required"])
        self.assertFalse(backends["output:null"]["install_plan"]["uses_pip_extra"])
        for backend in inventory["backends"]:
            for dependency in backend["dependencies"]:
                self.assertNotIn("\\", dependency)
                self.assertNotIn("/", dependency)


if __name__ == "__main__":
    unittest.main()
