import subprocess
import unittest

from auralis_voicekit import BackendNotAvailable, VoiceKitConfig
from auralis_voicekit.backends import SystemSpeechOutputBackend, create_default_registry


class SystemSpeechOutputBackendTests(unittest.TestCase):
    def test_registry_includes_system_output_backend(self):
        registry = create_default_registry()
        backend = registry.create_output("system")

        self.assertIsInstance(backend, SystemSpeechOutputBackend)

    def test_info_reports_missing_command_without_raising(self):
        backend = SystemSpeechOutputBackend(system="Linux", which=lambda name: None)

        info = backend.info()

        self.assertFalse(info.available)
        self.assertEqual(info.dependencies, ("spd-say", "espeak"))
        with self.assertRaisesRegex(BackendNotAvailable, "Expected one of"):
            backend.speak("Hola", VoiceKitConfig())

    def test_macos_uses_say_command(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_device="Monica"))

        self.assertEqual(calls[0][0], ["/usr/bin/say", "-v", "Monica", "Hola"])
        self.assertTrue(calls[0][1]["capture_output"])

    def test_linux_uses_espeak_voice_when_selected(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Linux",
            runner=runner,
            which=lambda name: "/usr/bin/espeak" if name == "espeak" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_device="es"))

        self.assertEqual(calls[0], ["/usr/bin/espeak", "-v", "es", "Hola"])

    def test_windows_uses_powershell_sapi(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Windows",
            runner=runner,
            which=lambda name: "C:\\Windows\\System32\\powershell.exe"
            if name == "powershell.exe"
            else None,
        )

        backend.speak("Hola", VoiceKitConfig())

        command = calls[0]
        self.assertEqual(command[0], "C:\\Windows\\System32\\powershell.exe")
        self.assertIn("-Command", command)
        self.assertEqual(command[-1], "Hola")

    def test_runner_failure_raises_backend_error(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="boom")

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        with self.assertRaisesRegex(BackendNotAvailable, "boom"):
            backend.speak("Hola", VoiceKitConfig())

    def test_blank_text_is_noop(self):
        calls = []
        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=lambda command, **kwargs: calls.append(command),
            which=lambda name: "/usr/bin/say",
        )

        backend.speak("   ", VoiceKitConfig())

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
