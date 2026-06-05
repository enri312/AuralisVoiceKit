import os
import sys
import tempfile
import types
import unittest
from importlib.machinery import ModuleSpec
from unittest.mock import patch

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    DiagnosticStatus,
    run_doctor,
    write_wav,
)


def _fake_wasapi_sounddevice():
    fake_sounddevice = types.SimpleNamespace()
    fake_sounddevice.__spec__ = ModuleSpec("sounddevice", loader=None)
    fake_sounddevice.default = types.SimpleNamespace(device=(1, -1))
    fake_sounddevice.query_hostapis = lambda: [
        {"name": "Windows WASAPI", "device_count": 1, "default_input_device": 1},
        {"name": "MME", "device_count": 1, "default_input_device": 0},
    ]
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
    ]
    return fake_sounddevice


class DiagnosticsTests(unittest.TestCase):
    def test_run_doctor_returns_structured_report(self):
        report = run_doctor(include_devices=True, capture_backend="wav")

        self.assertEqual(report.version.split(".")[0], "0")
        self.assertIn(report.status, {DiagnosticStatus.OK, DiagnosticStatus.WARNING})
        self.assertIn("checks", report.to_dict())
        self.assertTrue(any(check.name == "python" for check in report.checks))
        self.assertTrue(any(check.name == "dependency:openai" for check in report.checks))
        self.assertTrue(any(check.name == "dependency:faster_whisper" for check in report.checks))
        self.assertTrue(any(check.name == "executable:ffmpeg" for check in report.checks))
        self.assertTrue(any(check.name == "backend:capture:wasapi" for check in report.checks))
        self.assertTrue(any(check.name == "backend:output:system" for check in report.checks))
        self.assertTrue(any(check.name == "devices:wav" for check in report.checks))

    def test_run_doctor_includes_ffmpeg_search_details(self):
        report = run_doctor()

        checks = {check.name: check for check in report.checks}
        check = checks["executable:ffmpeg"]
        self.assertIn("search", check.details)
        self.assertTrue(check.details["search"])

    def test_run_doctor_includes_wasapi_snapshot_for_devices(self):
        with patch.dict(sys.modules, {"sounddevice": _fake_wasapi_sounddevice()}):
            with patch("auralis_voicekit.backends.wasapi.platform.system", return_value="Windows"):
                report = run_doctor(include_devices=True, capture_backend="wasapi")

        checks = {check.name: check for check in report.checks}
        check = checks["devices:wasapi"]
        self.assertEqual(check.status, DiagnosticStatus.OK)
        self.assertIn("wasapi", check.details)
        self.assertEqual(check.details["wasapi"]["selected_input_device_id"], 1)
        self.assertEqual(check.details["wasapi"]["wasapi_input_device_count"], 1)

    def test_run_doctor_can_test_null_capture_opening(self):
        report = run_doctor(
            include_capture_test=True,
            capture_backend="null",
            capture_test_seconds=0.001,
        )

        checks = {check.name: check for check in report.checks}
        check = checks["capture-test:null"]
        self.assertEqual(check.status, DiagnosticStatus.OK)
        self.assertEqual(check.details["backend"], "null")
        self.assertEqual(check.details["chunks_received"], 0)

    def test_run_doctor_reports_capture_test_failure(self):
        report = run_doctor(
            include_capture_test=True,
            capture_backend="missing",
            capture_test_seconds=0.001,
        )

        self.assertEqual(report.status, DiagnosticStatus.ERROR)
        self.assertTrue(
            any(
                check.name == "capture-test:missing"
                and check.status is DiagnosticStatus.ERROR
                for check in report.checks
            )
        )

    def test_run_doctor_adds_windows_audio_hint_for_capture_failure(self):
        with patch("auralis_voicekit.diagnostics.platform.system", return_value="Windows"):
            report = run_doctor(
                include_capture_test=True,
                capture_backend="missing",
                capture_test_seconds=0.001,
                capture_device="default",
            )

        checks = {check.name: check for check in report.checks}
        check = checks["capture-test:missing"]
        self.assertEqual(check.status, DiagnosticStatus.ERROR)
        self.assertIn("backend selection failed", check.hint)
        self.assertIn("windows_audio_hint", check.details)
        self.assertEqual(check.details["windows_audio_hint"]["category"], "backend_selection")
        self.assertEqual(check.details["windows_audio_hint"]["device"], "default")

    def test_run_doctor_rejects_invalid_capture_test_duration(self):
        report = run_doctor(
            include_capture_test=True,
            capture_backend="null",
            capture_test_seconds=0,
        )

        self.assertEqual(report.status, DiagnosticStatus.ERROR)
        self.assertTrue(
            any(
                check.name == "capture-test:null"
                and check.status is DiagnosticStatus.ERROR
                for check in report.checks
            )
        )

    def test_run_doctor_validates_wav_file(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)])
            report = run_doctor(wav_path=path)

        self.assertIn(DiagnosticStatus.OK, {check.status for check in report.checks if check.name == "wav"})

    def test_run_doctor_reports_invalid_wav_file(self):
        report = run_doctor(wav_path="missing.wav")

        self.assertEqual(report.status, DiagnosticStatus.ERROR)
        self.assertTrue(any(check.name == "wav" and check.status is DiagnosticStatus.ERROR for check in report.checks))


if __name__ == "__main__":
    unittest.main()
