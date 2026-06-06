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
            findings_template_path = Path(report["artifacts"]["real_pilot_findings_template"])
            handoff_path = Path(report["artifacts"]["real_pilot_handoff"])

            self.assertTrue(report_path.exists())
            self.assertTrue(plan_path.exists())
            self.assertTrue(findings_template_path.exists())
            self.assertTrue(handoff_path.exists())
            self.assertTrue(Path(report["artifacts"]["assistant_log"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_json"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_csv"]).exists())
            persisted = json.loads(report_path.read_text(encoding="utf-8"))
            plan = plan_path.read_text(encoding="utf-8")
            findings_template = findings_template_path.read_text(encoding="utf-8")
            handoff = handoff_path.read_text(encoding="utf-8")

        self.assertTrue(report["safe_automated_pilot"]["passed"])
        self.assertFalse(report["safe_automated_pilot"]["hardware_used"])
        self.assertEqual(persisted["version"], report["version"])
        self.assertIn("real_pilot_handoff", persisted)
        self.assertIn("real_pilot_findings_template", persisted)
        self.assertIn("real_pilot_handoff", persisted["artifacts"])
        self.assertIn("real_pilot_findings_template", persisted["artifacts"])
        self.assertTrue(persisted["real_pilot_handoff"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_findings_template"]["safe_to_share"])
        self.assertEqual(persisted["real_pilot_findings_template"]["target_document"], "PILOT_FINDINGS.md")
        self.assertFalse(persisted["real_pilot_findings_template"]["records_audio"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_findings_template"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_handoff"]["content_policy"]["records_audio"])
        self.assertFalse(persisted["real_pilot_handoff"]["content_policy"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_handoff"]["content_policy"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_handoff"]["content_policy"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_handoff"]["content_policy"]["records_operator_identity"])
        self.assertIn("pilot_plan", persisted["artifacts"])
        self.assertIn("Plan de pilotos AuralisVoiceKit", plan)
        self.assertIn("real-pilot-findings-template.md", plan)
        self.assertIn("real-pilot-handoff.md", plan)
        self.assertIn("Plantilla de hallazgos de pilotos reales", findings_template)
        self.assertIn("PILOT_FINDINGS.md", findings_template)
        self.assertIn("manual-pilot-report.json", findings_template)
        self.assertIn("output-pilot-report.json", findings_template)
        self.assertIn("transcription-pilot-report.json", findings_template)
        self.assertIn("--fail-on-audit-gaps", findings_template)
        self.assertIn("<Windows|Linux|Darwin>", findings_template)
        self.assertIn("<resumen sin transcripcion", findings_template)
        self.assertIn("<resumen sin texto hablado real", findings_template)
        self.assertNotIn(str(tmpdir), findings_template)
        self.assertIn("Handoff de pilotos reales AuralisVoiceKit", handoff)
        self.assertIn("Politica de contenido", handoff)
        self.assertIn("Orden recomendado", handoff)
        self.assertIn("Auditoria", handoff)
        self.assertIn("real_transcription_quality", handoff)
        self.assertIn("system_output_audible", handoff)
        self.assertIn("ubuntu_linux_capture", handoff)
        self.assertIn("macos_capture", handoff)
        self.assertIn("--fail-on-audit-gaps", handoff)
        self.assertIn("<public-spoken-text>", handoff)
        self.assertIn("<audio-path>", handoff)
        self.assertNotIn(str(tmpdir), handoff)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Proximas evidencias beta", plan)
        self.assertIn("--confirm-audible", plan)
        self.assertIn("--confirm-voice-reviewed", plan)
        self.assertIn("audit-evidence", plan)
        self.assertIn("refresh-beta-checklist", plan)
        self.assertIn("--fail-on-audit-gaps", plan)
        self.assertIn("pilot_audio_fixture.py", plan)
        self.assertIn("--run-preflight", plan)
        self.assertIn("--preflight-only", plan)
        self.assertIn("--max-audio-seconds 60", plan)
        self.assertIn("--confirm-audio-reviewed", plan)
        self.assertIn("--confirm-reference-reviewed", plan)
        self.assertIn("--confirm-quality-reviewed", plan)
        self.assertIn("transcription-review-checklist.md", plan)
        self.assertIn("real-transcription-next-step.md", plan)
        self.assertIn("audio.audio_file_name_redacted", plan)
        self.assertIn("transcription_checklist.records_audio_file_name", plan)
        self.assertIn("transcription_checklist.records_expected_text_file_name", plan)
        self.assertIn("transcription_checklist.audio_review_confirmed", plan)
        self.assertIn("transcription_checklist.reference_review_confirmed", plan)
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", plan)
        self.assertIn("transcription_checklist.quality_review_confirmed", plan)
        self.assertIn("transcription_checklist.ready_for_beta_evidence", plan)
        self.assertIn("output-operator-checklist.md", plan)
        self.assertIn("system-output-next-step.md", plan)
        self.assertIn("--confirm-text-reviewed", plan)
        self.assertIn("text_review_confirmed", plan)
        self.assertIn("spoken_text_privacy_scan.passed", plan)
        self.assertIn("operator_checklist.text_review_confirmed", plan)
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", plan)
        self.assertIn("operator_checklist.voice_review_confirmed", plan)
        self.assertIn("operator_checklist.expected_system_matched", plan)
        self.assertIn("operator_checklist.ready_for_beta_evidence", plan)
        self.assertIn("manual-capture-checklist.md", plan)
        self.assertIn("--confirm-input-reviewed", plan)
        self.assertIn("input_review_confirmed", plan)
        self.assertIn("capture_checklist.input_review_confirmed", plan)
        self.assertIn("capture_checklist.ready_for_beta_evidence", plan)
        self.assertIn("system_guard.expected_system_matched", plan)
        self.assertIn("--expected-system Linux", plan)
        self.assertIn("--expected-system Darwin", plan)
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
        self.assertIn("system-output-operator-checklist", sequence_names)
        self.assertIn("audit-evidence", sequence_names)
        self.assertIn("refresh-beta-checklist", sequence_names)
        self.assertFalse(report["recommended_pilot_sequence"][0]["requires_hardware"])
        self.assertFalse(report["recommended_pilot_sequence"][0]["requires_non_sensitive_audio"])
        self.assertIn("preflight.passed", report["recommended_pilot_sequence"][0]["required_fields"])
        self.assertTrue(report["recommended_pilot_sequence"][1]["requires_non_sensitive_audio"])
        self.assertIn(
            "artifacts.transcription_review_checklist",
            report["recommended_pilot_sequence"][1]["required_fields"],
        )
        self.assertIn(
            "artifacts.real_transcription_next_step",
            report["recommended_pilot_sequence"][1]["required_fields"],
        )
        self.assertIn(
            "audio.audio_file_name_redacted",
            report["recommended_pilot_sequence"][1]["required_fields"],
        )
        checklist_step = {
            step["name"]: step for step in report["recommended_pilot_sequence"]
        }["system-output-operator-checklist"]
        transcription_step = {
            step["name"]: step for step in report["recommended_pilot_sequence"]
        }["real_transcription_quality"]
        output_step = {
            step["name"]: step for step in report["recommended_pilot_sequence"]
        }["system_output_audible"]
        self.assertIn("--confirm-quality-reviewed", transcription_step["command"])
        self.assertIn("--confirm-audio-reviewed", transcription_step["command"])
        self.assertIn("--confirm-reference-reviewed", transcription_step["command"])
        self.assertIn("transcription_checklist.audio_review_confirmed", transcription_step["required_fields"])
        self.assertIn("audio.audio_file_name_redacted", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.records_audio_file_name", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.records_expected_text_file_name", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.reference_review_confirmed", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.quality_review_confirmed", transcription_step["required_fields"])
        self.assertIn("--confirm-voice-reviewed", output_step["command"])
        self.assertIn("--confirm-text-reviewed", output_step["command"])
        self.assertIn('--expected-system "Windows|Linux|Darwin"', output_step["command"])
        self.assertIn("system_guard.expected_system_matched", output_step["required_fields"])
        self.assertIn("text_review_confirmed", output_step["required_fields"])
        self.assertIn("spoken_text_privacy_scan.passed", output_step["required_fields"])
        self.assertIn("operator_checklist.expected_system_matched", output_step["required_fields"])
        self.assertIn("operator_checklist.text_review_confirmed", output_step["required_fields"])
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", output_step["required_fields"])
        self.assertIn("operator_checklist.voice_review_confirmed", output_step["required_fields"])
        self.assertFalse(checklist_step["requires_hardware"])
        self.assertFalse(checklist_step["requires_operator"])
        self.assertIn("operator_checklist.ready_for_beta_evidence", checklist_step["required_fields"])
        self.assertIn("artifacts.system_output_next_step", checklist_step["required_fields"])
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertIn("--confirm-input-reviewed", matrix["ubuntu-linux-capture"]["command"])
        self.assertIn("--confirm-input-reviewed", matrix["macos-capture"]["command"])
        self.assertEqual(matrix["windows-wasapi-capture"]["status"], "closed")
        self.assertEqual(matrix["ubuntu-linux-capture"]["status"], "pending")
        self.assertEqual(matrix["macos-capture"]["status"], "pending")
        self.assertEqual(matrix["transcription-audio-fixture"]["status"], "recommended")
        self.assertEqual(matrix["transcription-mp3-preflight"]["status"], "recommended")
        self.assertTrue(matrix["system-output-audible"]["requires_operator"])
        self.assertIn("--confirm-voice-reviewed", matrix["system-output-audible"]["command"])
        self.assertIn("--confirm-text-reviewed", matrix["system-output-audible"]["command"])
        self.assertIn('--expected-system "Windows|Linux|Darwin"', matrix["system-output-audible"]["command"])
        self.assertIn("--fail-on-audit-gaps", report["beta_readiness"]["strict_audit_command"])
        self.assertIn("microphone-capture-checklist", {step["name"] for step in report["manual_pilot_steps"]})
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
        self.assertIn("real_pilot_handoff", payload)
        self.assertIn("real_pilot_findings_template", payload)
        self.assertIn("beta_readiness", payload)
        self.assertIn("real_pilot_handoff", payload["artifacts"])
        self.assertIn("real_pilot_findings_template", payload["artifacts"])
        self.assertIn("pilot_plan", payload["artifacts"])

    def test_safe_pilot_accepts_beta_evidence_paths(self):
        module = _load_pilot_run()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "system_guard": {"expected_system_matched": True},
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": {
                        "input_review_confirmed": True,
                        "ready_for_beta_evidence": True,
                    },
                    "passed": True,
                },
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
