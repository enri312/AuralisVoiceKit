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

    def test_cli_rejects_invalid_preflight_timeout(self):
        module = _load_pilot_audio_fixture()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(
                [
                    "--format",
                    "wav",
                    "--preflight-timeout-seconds",
                    "0",
                    "--json",
                ]
            )
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 2)
        self.assertIn("--preflight-timeout-seconds", payload["error"])

    def test_preflight_auto_adds_mp3_and_fails_safely_without_ffmpeg(self):
        module = _load_pilot_audio_fixture()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.generate_pilot_audio_fixture(
                root=ROOT,
                output_dir=tmpdir,
                formats=("wav",),
                duration_seconds=0.2,
                sample_rate=8000,
                ffmpeg="missing-auralis-ffmpeg",
                run_preflight=True,
            )
            findings = Path(report["artifacts"]["fixture_findings"]).read_text(encoding="utf-8")

        self.assertFalse(report["passed"])
        self.assertEqual(report["formats_requested"], ["wav", "mp3"])
        self.assertTrue(report["preflight"]["requested"])
        self.assertFalse(report["preflight"]["passed"])
        self.assertEqual(report["preflight"]["reason"], "missing_mp3_fixture")
        self.assertEqual(report["preflight"]["backend"], "whisper")
        self.assertEqual(report["preflight"]["model"], "auto")
        self.assertIsNone(report["preflight"]["transcription_timeout_seconds"])
        self.assertIsNone(report["preflight"]["review_checklist"])
        self.assertIsNone(report["preflight"]["real_transcription_next_step"])
        self.assertEqual(report["preflight"]["preflight_readiness"]["status"], "blocked")
        self.assertFalse(report["preflight"]["preflight_readiness"]["ready_for_model_run"])
        self.assertTrue(report["preflight"]["preflight_readiness"]["must_rerun_preflight"])
        self.assertFalse(report["preflight"]["preflight_readiness"]["records_audio_file_name"])
        self.assertFalse(report["usable_as_beta_evidence"])
        self.assertIn("your own non-sensitive MP3", report["next_step"])
        self.assertIn("Fixture preflight passed: `False`", findings)
        self.assertIn("Fixture preflight readiness status: `blocked`", findings)

    def test_fixture_preflight_surfaces_readiness_summary(self):
        module = _load_pilot_audio_fixture()
        if module.resolve_ffmpeg_executable("ffmpeg") is None:
            self.skipTest("ffmpeg is required for MP3 fixture preflight")

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.generate_pilot_audio_fixture(
                root=ROOT,
                output_dir=tmpdir,
                formats=("mp3",),
                duration_seconds=0.3,
                sample_rate=8000,
                run_preflight=True,
                min_audio_seconds=0.05,
                max_audio_seconds=1.0,
            )
            report_path = Path(report["artifacts"]["fixture_report"])
            findings = Path(report["artifacts"]["fixture_findings"]).read_text(encoding="utf-8")
            payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertTrue(report["preflight"]["requested"])
        self.assertTrue(report["preflight"]["audio_decoded"])
        self.assertIn(report["preflight"]["preflight_readiness"]["status"], {"ready", "needs_backend_install"})
        self.assertEqual(
            report["preflight"]["preflight_readiness"],
            payload["preflight"]["preflight_readiness"],
        )
        self.assertFalse(report["preflight"]["preflight_readiness"]["usable_as_beta_evidence"])
        self.assertFalse(report["preflight"]["preflight_readiness"]["records_audio_file_name"])
        self.assertFalse(report["preflight"]["preflight_readiness"]["records_local_paths"])
        self.assertIn("Fixture preflight readiness status:", findings)
        self.assertIn("Preflight ready for model run:", findings)

    def test_rejects_invalid_audio_shape(self):
        module = _load_pilot_audio_fixture()

        with self.assertRaisesRegex(ValueError, "--duration"):
            module.generate_pilot_audio_fixture(root=ROOT, formats=("wav",), duration_seconds=0)
