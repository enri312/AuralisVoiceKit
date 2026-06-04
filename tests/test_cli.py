import contextlib
import io
import json
import os
import tempfile
import unittest

from auralis_voicekit import AudioChunk, AudioFormat, __version__, write_wav
from auralis_voicekit.cli import main


class CliTests(unittest.TestCase):
    def test_version_flag(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn(__version__, output.getvalue())

    def test_backends_command(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["backends"])

        self.assertEqual(exit_code, 0)
        self.assertIn("capture:null", output.getvalue())

    def test_devices_command_can_use_null_backend(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["devices", "--backend", "null"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Null input", output.getvalue())

    def test_doctor_can_include_devices(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--devices", "--backend", "null"])

        self.assertEqual(exit_code, 0)
        self.assertIn("AuralisVoiceKit", output.getvalue())
        self.assertIn("Null input", output.getvalue())

    def test_doctor_json_output(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--devices", "--backend", "wav", "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["version"], __version__)
        self.assertTrue(any(check["name"] == "devices:wav" for check in payload["checks"]))

    def test_doctor_wav_error_returns_nonzero(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["doctor", "--wav", "missing.wav"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot read WAV file", output.getvalue())

    def test_wav_info_command(self):
        audio_format = AudioFormat(sample_rate=8000, channels=1, sample_width=2)
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.wav")
            write_wav(path, [AudioChunk(data=b"\x00\x00" * 8, format=audio_format)])
            with contextlib.redirect_stdout(output):
                exit_code = main(["wav-info", path])

        self.assertEqual(exit_code, 0)
        self.assertIn("Sample rate: 8000", output.getvalue())
        self.assertIn("Encoding: pcm16", output.getvalue())


if __name__ == "__main__":
    unittest.main()
