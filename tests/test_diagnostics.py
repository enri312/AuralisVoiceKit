import os
import tempfile
import unittest

from auralis_voicekit import (
    AudioChunk,
    AudioFormat,
    DiagnosticStatus,
    run_doctor,
    write_wav,
)


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
        self.assertTrue(any(check.name == "devices:wav" for check in report.checks))

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
