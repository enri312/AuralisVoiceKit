import unittest

import auralis_voicekit
from auralis_voicekit._version import __version__


class VersionTests(unittest.TestCase):
    def test_version_is_exported_from_package(self):
        self.assertEqual(auralis_voicekit.__version__, __version__)
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
