import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PILOT_AUDIO_FIXTURE = ROOT / "tools" / "pilot_audio_fixture.py"


def _load_pilot_audio_fixture():
    spec = importlib.util.spec_from_file_location("pilot_audio_fixture", PILOT_AUDIO_FIXTURE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PilotAudioFixtureTests(unittest.TestCase):
    def test_generates_public_wav_fixture(self):
        module = _load_pilot_audio_fixture()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.generate_pilot_audio_fixture(
                root=ROOT,
                output_dir=tmpdir,
                formats=("wav",),
                duration_seconds=0.2,
                sample_rate=8000,
            )
            wav_path = Path(report["artifacts"]["wav"])
            wav_exists = wav_path.exists()
            findings = Path(report["artifacts"]["fixture_findings"]).read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["generated_public_fixture"])
        self.assertFalse(report["contains_private_audio"])
        self.assertFalse(report["usable_as_beta_evidence"])
        self.assertEqual(report["files"][0]["format"], "wav")
        self.assertTrue(report["files"][0]["passed"])
        self.assertTrue(wav_exists)
        self.assertIn("pilot-sample.wav", findings)
        self.assertNotIn(tmpdir, findings)

    def test_cli_outputs_json_for_wav_fixture(self):
        module = _load_pilot_audio_fixture()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--format",
                        "wav",
                        "--duration",
                        "0.2",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["formats_requested"], ["wav"])

    def test_rejects_invalid_audio_shape(self):
        module = _load_pilot_audio_fixture()

        with self.assertRaisesRegex(ValueError, "--duration"):
            module.generate_pilot_audio_fixture(root=ROOT, formats=("wav",), duration_seconds=0)
