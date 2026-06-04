import contextlib
import io
import unittest

from auralis_voicekit import __version__
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


if __name__ == "__main__":
    unittest.main()
