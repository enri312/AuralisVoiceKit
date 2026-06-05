from pathlib import Path
import unittest

import auralis_voicekit


ROOT = Path(__file__).resolve().parents[1]
API_DOC = ROOT / "docs" / "auralisvoicekit-api.html"
MAIN_DOC = ROOT / "docs" / "auralisvoicekit-documentacion.html"
README = ROOT / "README.md"
PRIVACY = ROOT / "PRIVACY.md"


class DocumentationTests(unittest.TestCase):
    def test_api_reference_documents_public_exports(self):
        content = API_DOC.read_text(encoding="utf-8")

        missing = [name for name in auralis_voicekit.__all__ if name not in content]

        self.assertEqual(missing, [])

    def test_public_docs_link_api_reference(self):
        api_name = "auralisvoicekit-api.html"

        self.assertIn(api_name, MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn(api_name, README.read_text(encoding="utf-8"))

    def test_api_reference_has_pypi_install_and_custom_backend_sections(self):
        content = API_DOC.read_text(encoding="utf-8")

        self.assertIn("python -m pip install auralisvoicekit", content)
        self.assertIn("Backends personalizados", content)
        self.assertIn("ffmpeg_search_locations", content)
        self.assertIn("run_offline_benchmarks", content)

    def test_privacy_guide_is_linked_from_public_docs(self):
        privacy_name = "PRIVACY.md"

        self.assertTrue(PRIVACY.exists())
        self.assertIn(privacy_name, README.read_text(encoding="utf-8"))
        self.assertIn(privacy_name, MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("PrivacyEventLogger", API_DOC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
