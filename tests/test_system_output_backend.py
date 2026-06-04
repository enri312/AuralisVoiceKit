import subprocess
import unittest

from auralis_voicekit import BackendNotAvailable, VoiceKitConfig
from auralis_voicekit.backends import SystemSpeechOutputBackend, SystemVoice, create_default_registry


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

    def test_macos_uses_say_command_with_voice_and_rate(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_voice="Monica", output_rate=180))

        self.assertEqual(calls[0][0], ["/usr/bin/say", "-v", "Monica", "-r", "180", "Hola"])
        self.assertTrue(calls[0][1]["capture_output"])

    def test_output_device_still_selects_voice_for_compatibility(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_device="Monica"))

        self.assertEqual(calls[0], ["/usr/bin/say", "-v", "Monica", "Hola"])

    def test_linux_uses_espeak_voice_rate_and_volume_when_selected(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Linux",
            runner=runner,
            which=lambda name: "/usr/bin/espeak" if name == "espeak" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_voice="es", output_rate=160, output_volume=80))

        self.assertEqual(calls[0], ["/usr/bin/espeak", "-v", "es", "-s", "160", "-a", "80", "Hola"])

    def test_linux_uses_spd_say_rate_and_volume_when_selected(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        backend = SystemSpeechOutputBackend(
            system="Linux",
            runner=runner,
            which=lambda name: "/usr/bin/spd-say" if name == "spd-say" else None,
        )

        backend.speak("Hola", VoiceKitConfig(output_rate=10, output_volume=90))

        self.assertEqual(calls[0], ["/usr/bin/spd-say", "-r", "10", "-i", "90", "Hola"])

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

        backend.speak("Hola", VoiceKitConfig(output_voice="Microsoft Helena", output_rate=2, output_volume=75))

        command = calls[0]
        self.assertEqual(command[0], "C:\\Windows\\System32\\powershell.exe")
        self.assertIn("-Command", command)
        self.assertIn("SelectVoice", command[4])
        self.assertEqual(command[-4:], ["Hola", "Microsoft Helena", "2", "75"])

    def test_windows_lists_installed_voices(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Microsoft Helena\tes-ES\tFemale\tAdult\nMicrosoft David\ten-US\tMale\tAdult\n",
                stderr="",
            )

        backend = SystemSpeechOutputBackend(
            system="Windows",
            runner=runner,
            which=lambda name: "powershell.exe" if name == "powershell.exe" else None,
        )

        voices = backend.list_voices()

        self.assertEqual(len(voices), 2)
        self.assertIsInstance(voices[0], SystemVoice)
        self.assertEqual(voices[0].id, "Microsoft Helena")
        self.assertEqual(voices[0].language, "es-ES")

    def test_macos_lists_say_voices(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Monica              es_ES    # Hola soy Monica\nAlex                en_US    # Hello\n",
                stderr="",
            )

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        voices = backend.list_voices()

        self.assertEqual(voices[0].id, "Monica")
        self.assertEqual(voices[0].language, "es_ES")
        self.assertEqual(voices[0].metadata["sample"], "Hola soy Monica")

    def test_linux_lists_espeak_voices(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "Pty Language Age/Gender VoiceName File Other Languages\n"
                    " 5  es             M  spanish  europe/es\n"
                    " 5  en-us          F  english-us  en/en-us\n"
                ),
                stderr="",
            )

        backend = SystemSpeechOutputBackend(
            system="Linux",
            runner=runner,
            which=lambda name: "/usr/bin/espeak" if name == "espeak" else None,
        )

        voices = backend.list_voices()

        self.assertEqual(voices[0].id, "spanish")
        self.assertEqual(voices[0].language, "es")
        self.assertEqual(voices[0].gender, "M")

    def test_voice_listing_failure_raises_backend_error(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="boom")

        backend = SystemSpeechOutputBackend(
            system="Darwin",
            runner=runner,
            which=lambda name: "/usr/bin/say" if name == "say" else None,
        )

        with self.assertRaisesRegex(BackendNotAvailable, "boom"):
            backend.list_voices()

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
