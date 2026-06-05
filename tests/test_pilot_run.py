import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PILOT_RUN = ROOT / "tools" / "pilot_run.py"


def _load_pilot_run():
    spec = importlib.util.spec_from_file_location("pilot_run", PILOT_RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PilotRunTests(unittest.TestCase):
    def test_safe_pilot_writes_report_and_artifacts(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_safe_pilot(root=ROOT, output_dir=tmpdir)
            report_path = Path(report["artifacts"]["pilot_report"])
            plan_path = Path(report["artifacts"]["pilot_plan"])

            self.assertTrue(report_path.exists())
            self.assertTrue(plan_path.exists())
            self.assertTrue(Path(report["artifacts"]["assistant_log"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_json"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_csv"]).exists())
            persisted = json.loads(report_path.read_text(encoding="utf-8"))
            plan = plan_path.read_text(encoding="utf-8")

        self.assertTrue(report["safe_automated_pilot"]["passed"])
        self.assertFalse(report["safe_automated_pilot"]["hardware_used"])
        self.assertEqual(persisted["version"], report["version"])
        self.assertIn("pilot_plan", persisted["artifacts"])
        self.assertIn("Plan de pilotos AuralisVoiceKit", plan)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Proximas evidencias beta", plan)
        self.assertIn("--confirm-audible", plan)
        self.assertIn("audit-evidence", plan)
        self.assertIn("refresh-beta-checklist", plan)
        self.assertIn("--fail-on-audit-gaps", plan)
        self.assertIn("pilot_audio_fixture.py", plan)
        self.assertIn("--preflight-only", plan)
        self.assertIn("--max-audio-seconds 60", plan)
        self.assertIn("sample.mp3", plan)
        self.assertIn("Ubuntu/Linux - ubuntu-linux-capture", plan)
        self.assertIn("macOS - macos-capture", plan)
        self.assertNotIn(str(tmpdir), plan)
        self.assertEqual({step["status"] for step in report["steps"]}, {"passed"})
        self.assertFalse(report["beta_readiness"]["ready_for_beta"])
        self.assertIn("real_transcription_quality", report["beta_readiness"]["blockers"])
        self.assertIn("real_transcription_quality", {step["name"] for step in report["next_beta_evidence_steps"]})
        sequence_names = [step["name"] for step in report["recommended_pilot_sequence"]]
        self.assertEqual(sequence_names[0], "transcription-audio-fixture")
        self.assertEqual(sequence_names[1], "transcription-audio-preflight")
        self.assertEqual(sequence_names[2], "real_transcription_quality")
        self.assertIn("audit-evidence", sequence_names)
        self.assertIn("refresh-beta-checklist", sequence_names)
        self.assertFalse(report["recommended_pilot_sequence"][0]["requires_hardware"])
        self.assertFalse(report["recommended_pilot_sequence"][0]["requires_non_sensitive_audio"])
        self.assertTrue(report["recommended_pilot_sequence"][1]["requires_non_sensitive_audio"])
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertEqual(matrix["windows-wasapi-capture"]["status"], "closed")
        self.assertEqual(matrix["ubuntu-linux-capture"]["status"], "pending")
        self.assertEqual(matrix["macos-capture"]["status"], "pending")
        self.assertEqual(matrix["transcription-audio-fixture"]["status"], "recommended")
        self.assertEqual(matrix["transcription-mp3-preflight"]["status"], "recommended")
        self.assertTrue(matrix["system-output-audible"]["requires_operator"])
        self.assertIn("--fail-on-audit-gaps", report["beta_readiness"]["strict_audit_command"])
        self.assertIn("microphone-capture", {step["name"] for step in report["manual_pilot_steps"]})
        self.assertIn("beta-readiness", {step["name"] for step in report["manual_pilot_steps"]})

    def test_safe_pilot_cli_outputs_json(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(["--root", str(ROOT), "--output-dir", tmpdir, "--json"])
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["safe_automated_pilot"]["passed"])
        self.assertIn("next_beta_evidence_steps", payload)
        self.assertIn("recommended_pilot_sequence", payload)
        self.assertIn("platform_pilot_matrix", payload)
        self.assertIn("beta_readiness", payload)
        self.assertIn("pilot_plan", payload["artifacts"])

    def test_safe_pilot_accepts_beta_evidence_paths(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {"project": "AuralisVoiceKit", "system": "Linux", "hardware_capture_tested": True, "passed": True},
            )
            _write_json(
                evidence_root / "ignored" / "output-pilot-report.json",
                {"backend": "system", "real_audio_requested": True, "passed": True},
            )
            report = module.run_safe_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                evidence_paths=[evidence_root],
            )
            plan = Path(report["artifacts"]["pilot_plan"]).read_text(encoding="utf-8")

        self.assertEqual(report["beta_readiness"]["evidence_count"], 1)
        self.assertEqual(report["beta_readiness"]["ignored_evidence_count"], 1)
        self.assertEqual(report["beta_readiness"]["satisfied_json_blockers"], ["ubuntu_linux_capture"])
        self.assertEqual(report["beta_readiness"]["accepted_json_artifacts"][0]["artifact"], "manual-pilot-report.json")
        self.assertEqual(report["beta_readiness"]["ignored_json_artifacts"][0]["reason"], "missing_project")
        self.assertNotIn("ubuntu_linux_capture", report["beta_readiness"]["blockers"])
        self.assertNotIn("ubuntu_linux_capture", {step["name"] for step in report["next_beta_evidence_steps"]})
        sequence_names = {step["name"] for step in report["recommended_pilot_sequence"]}
        self.assertNotIn("ubuntu_linux_capture", sequence_names)
        self.assertIn("audit-evidence", sequence_names)
        self.assertIn("refresh-beta-checklist", sequence_names)
        self.assertIn("Evidencias JSON", plan)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Blockers cerrados: `ubuntu_linux_capture`", plan)
        self.assertIn("missing_project", plan)
        self.assertNotIn(str(evidence_root), plan)
        self.assertNotIn("Ubuntu/Linux capture pilot", plan)
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertEqual(matrix["ubuntu-linux-capture"]["status"], "closed")


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
