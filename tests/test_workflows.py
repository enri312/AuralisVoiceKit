from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
PUBLISH_PYPI_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"


class WorkflowTests(unittest.TestCase):
    def test_release_upload_artifact_uses_node24_ready_action(self):
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/upload-artifact@v5", content)
        self.assertNotIn("actions/upload-artifact@v4", content)

    def test_publish_pypi_upload_artifact_uses_node24_ready_action(self):
        content = PUBLISH_PYPI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/upload-artifact@v5", content)
        self.assertNotIn("actions/upload-artifact@v4", content)


if __name__ == "__main__":
    unittest.main()
