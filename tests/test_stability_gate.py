import contextlib
import importlib.util
import io
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STABILITY_GATE = ROOT / "tools" / "stability_gate.py"


def _load_stability_gate():
    spec = importlib.util.spec_from_file_location("stability_gate", STABILITY_GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StabilityGateTests(unittest.TestCase):
    def test_report_marks_project_ready_for_real_world_pilots(self):
        module = _load_stability_gate()

        report = module.build_report(ROOT)

        self.assertEqual(report["stage"], "pilot")
        self.assertTrue(report["ready_for_real_world_pilots"])
        self.assertFalse(report["ready_for_stable_release"])
        self.assertIn("version_is_pre_1_0", report["stable_blockers"])
        release_batch = report["release_batch"]
        self.assertTrue(release_batch["available"])
        self.assertEqual(release_batch["threshold"], 5)
        self.assertGreaterEqual(release_batch["commit_count"], 1)
        if release_batch["ready_for_tag"]:
            self.assertEqual(release_batch["remaining"], 0)
        else:
            self.assertGreaterEqual(release_batch["remaining"], 1)
        check_names = {check["name"] for check in report["checks"]}
        self.assertIn("pilot_runbook", check_names)
        self.assertIn("safe_pilot_runner", check_names)
        self.assertIn("manual_pilot_runner", check_names)
        self.assertIn("pyaudio_capture_backend", check_names)
        self.assertIn("pyproject_pyaudio_extra", check_names)
        self.assertIn("beta_readiness_runner", check_names)
        self.assertIn("beta_checklist", check_names)
        self.assertIn("beta_evidence_requirements", check_names)
        self.assertIn("pilot_findings", check_names)
        self.assertIn("doctor_bundle_api", check_names)
        self.assertIn("doctor_bundle_analysis", check_names)
        self.assertIn("release_workflow", check_names)
        self.assertIn("release_batch_guard", check_names)
        ci_check = next(check for check in report["checks"] if check["name"] == "ci")
        self.assertTrue(ci_check["ok"])
        next_actions = "\n".join(report["next_actions"])
        self.assertIn("Whisper local", next_actions)
        self.assertIn("OpenAI solo como integracion propietaria opt-in", next_actions)
        if release_batch["ready_for_tag"]:
            self.assertIn("Ya corresponde preparar tag", next_actions)
        else:
            self.assertIn("No crear tag todavia", next_actions)
        self.assertNotIn("openai o whisper", next_actions)

    def test_min_stage_pilot_exits_successfully(self):
        module = _load_stability_gate()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--min-stage", "pilot"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Release batch:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
