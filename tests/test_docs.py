from pathlib import Path
import unittest

import auralis_voicekit


ROOT = Path(__file__).resolve().parents[1]
API_DOC = ROOT / "docs" / "auralisvoicekit-api.html"
MAIN_DOC = ROOT / "docs" / "auralisvoicekit-documentacion.html"
README = ROOT / "README.md"
PRIVACY = ROOT / "PRIVACY.md"
CUSTOM_OUTPUT = ROOT / "CUSTOM_OUTPUT_BACKENDS.md"
SYSTEM_OUTPUT_DEMO = ROOT / "examples" / "system_output_demo.py"
LOCAL_ASSISTANT_PRIVACY_DEMO = ROOT / "examples" / "local_assistant_privacy_demo.py"


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

    def test_custom_output_guide_and_stability_gate_are_linked(self):
        custom_output_name = "CUSTOM_OUTPUT_BACKENDS.md"

        self.assertTrue(CUSTOM_OUTPUT.exists())
        self.assertIn(custom_output_name, README.read_text(encoding="utf-8"))
        self.assertIn(custom_output_name, MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn(custom_output_name, API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/stability_gate.py", README.read_text(encoding="utf-8"))

    def test_system_output_demo_is_linked_from_public_docs(self):
        system_output_name = "system_output_demo.py"

        self.assertTrue(SYSTEM_OUTPUT_DEMO.exists())
        self.assertIn(system_output_name, README.read_text(encoding="utf-8"))
        self.assertIn(system_output_name, MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn(system_output_name, API_DOC.read_text(encoding="utf-8"))

    def test_local_assistant_privacy_demo_is_linked_from_public_docs(self):
        demo_name = "local_assistant_privacy_demo.py"

        self.assertTrue(LOCAL_ASSISTANT_PRIVACY_DEMO.exists())
        self.assertIn(demo_name, README.read_text(encoding="utf-8"))
        self.assertIn(demo_name, MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn(demo_name, API_DOC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
