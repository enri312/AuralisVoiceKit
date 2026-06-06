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
            command_pack_path = Path(report["artifacts"]["real_pilot_command_pack"])
            environment_checklist_path = Path(report["artifacts"]["real_pilot_environment_checklist"])
            fixture_preflight_path = Path(report["artifacts"]["real_pilot_fixture_preflight"])
            transcription_readiness_path = Path(report["artifacts"]["real_pilot_transcription_readiness"])
            system_output_readiness_path = Path(report["artifacts"]["real_pilot_system_output_readiness"])
            evidence_manifest_path = Path(report["artifacts"]["real_pilot_evidence_manifest"])
            decision_gate_path = Path(report["artifacts"]["real_pilot_decision_gate"])

            self.assertTrue(report_path.exists())
            self.assertTrue(plan_path.exists())
            self.assertTrue(findings_template_path.exists())
            self.assertTrue(handoff_path.exists())
            self.assertTrue(command_pack_path.exists())
            self.assertTrue(environment_checklist_path.exists())
            self.assertTrue(fixture_preflight_path.exists())
            self.assertTrue(transcription_readiness_path.exists())
            self.assertTrue(system_output_readiness_path.exists())
            self.assertTrue(evidence_manifest_path.exists())
            self.assertTrue(decision_gate_path.exists())
            self.assertTrue(Path(report["artifacts"]["assistant_log"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_json"]).exists())
            self.assertTrue(Path(report["artifacts"]["benchmark_csv"]).exists())
            persisted = json.loads(report_path.read_text(encoding="utf-8"))
            plan = plan_path.read_text(encoding="utf-8")
            findings_template = findings_template_path.read_text(encoding="utf-8")
            handoff = handoff_path.read_text(encoding="utf-8")
            command_pack = command_pack_path.read_text(encoding="utf-8")
            environment_checklist = environment_checklist_path.read_text(encoding="utf-8")
            fixture_preflight = fixture_preflight_path.read_text(encoding="utf-8")
            transcription_readiness = transcription_readiness_path.read_text(encoding="utf-8")
            system_output_readiness = system_output_readiness_path.read_text(encoding="utf-8")
            evidence_manifest = evidence_manifest_path.read_text(encoding="utf-8")
            decision_gate = decision_gate_path.read_text(encoding="utf-8")

        self.assertTrue(report["safe_automated_pilot"]["passed"])
        self.assertFalse(report["safe_automated_pilot"]["hardware_used"])
        self.assertEqual(persisted["version"], report["version"])
        self.assertIn("real_pilot_handoff", persisted)
        self.assertIn("real_pilot_findings_template", persisted)
        self.assertIn("real_pilot_command_pack", persisted)
        self.assertIn("real_pilot_environment_checklist", persisted)
        self.assertIn("real_pilot_fixture_preflight", persisted)
        self.assertIn("real_pilot_transcription_readiness", persisted)
        self.assertIn("real_pilot_system_output_readiness", persisted)
        self.assertIn("real_pilot_evidence_manifest", persisted)
        self.assertIn("real_pilot_decision_gate", persisted)
        self.assertIn("evidence_manifest", persisted)
        self.assertIn("fixture_preflight_card", persisted)
        self.assertIn("transcription_readiness_card", persisted)
        self.assertIn("system_output_readiness_card", persisted)
        self.assertIn("pilot_decision_gate", persisted)
        self.assertIn("blocker_summaries", persisted["beta_readiness"])
        self.assertIn("blocker_summaries", persisted["evidence_manifest"])
        self.assertIn("real_pilot_handoff", persisted["artifacts"])
        self.assertIn("real_pilot_findings_template", persisted["artifacts"])
        self.assertIn("real_pilot_command_pack", persisted["artifacts"])
        self.assertIn("real_pilot_environment_checklist", persisted["artifacts"])
        self.assertIn("real_pilot_fixture_preflight", persisted["artifacts"])
        self.assertIn("real_pilot_transcription_readiness", persisted["artifacts"])
        self.assertIn("real_pilot_system_output_readiness", persisted["artifacts"])
        self.assertIn("real_pilot_evidence_manifest", persisted["artifacts"])
        self.assertIn("real_pilot_decision_gate", persisted["artifacts"])
        self.assertIn("environment_checklist", persisted)
        self.assertTrue(persisted["real_pilot_handoff"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_findings_template"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_command_pack"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_environment_checklist"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_fixture_preflight"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_transcription_readiness"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_system_output_readiness"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_evidence_manifest"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_decision_gate"]["safe_to_share"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["usable_as_beta_evidence"])
        self.assertTrue(persisted["real_pilot_fixture_preflight"]["prepares_real_transcription"])
        self.assertTrue(persisted["real_pilot_transcription_readiness"]["prepares_real_transcription"])
        self.assertTrue(persisted["real_pilot_system_output_readiness"]["prepares_audible_output"])
        self.assertTrue(persisted["real_pilot_evidence_manifest"]["tracks_pending_and_closed_blockers"])
        self.assertTrue(persisted["real_pilot_decision_gate"]["declares_real_world_pilot_scope"])
        self.assertTrue(persisted["real_pilot_decision_gate"]["declares_beta_and_stable_blockers"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_platform_commands"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_required_fields"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_strict_audit_command"])
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
        self.assertFalse(persisted["real_pilot_command_pack"]["records_audio"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_command_pack"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_audio"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_audio"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_audio"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_audio"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_audio"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_audio"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["records_operator_identity"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_audio"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_transcripts"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_spoken_text"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_expected_text"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_local_paths"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_device_names"])
        self.assertFalse(persisted["evidence_manifest"]["content_policy"]["records_operator_identity"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_audio"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_transcripts"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_spoken_text"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_expected_text"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_local_paths"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_device_names"])
        self.assertFalse(persisted["pilot_decision_gate"]["content_policy"]["records_operator_identity"])
        self.assertIn("pilot_plan", persisted["artifacts"])
        self.assertIn("Plan de pilotos AuralisVoiceKit", plan)
        self.assertIn("real-pilot-findings-template.md", plan)
        self.assertIn("real-pilot-handoff.md", plan)
        self.assertIn("real-pilot-command-pack.md", plan)
        self.assertIn("real-pilot-environment-checklist.md", plan)
        self.assertIn("real-pilot-fixture-preflight.md", plan)
        self.assertIn("real-pilot-transcription-readiness.md", plan)
        self.assertIn("real-pilot-system-output-readiness.md", plan)
        self.assertIn("real-pilot-evidence-manifest.md", plan)
        self.assertIn("real-pilot-decision-gate.md", plan)
        self.assertIn("Manifiesto de evidencias", plan)
        self.assertIn("Compuerta go/no-go", plan)
        self.assertIn("Preflight de fixture de transcripcion", plan)
        self.assertIn("Readiness de transcripcion real", plan)
        self.assertIn("Readiness de salida system", plan)
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
        self.assertIn("real-pilot-command-pack.md", handoff)
        self.assertIn("real-pilot-environment-checklist.md", handoff)
        self.assertIn("real-pilot-fixture-preflight.md", handoff)
        self.assertIn("real-pilot-transcription-readiness.md", handoff)
        self.assertIn("real-pilot-system-output-readiness.md", handoff)
        self.assertIn("real-pilot-evidence-manifest.md", handoff)
        self.assertIn("real-pilot-decision-gate.md", handoff)
        self.assertIn("real_transcription_quality", handoff)
        self.assertIn("system_output_audible", handoff)
        self.assertIn("ubuntu_linux_capture", handoff)
        self.assertIn("macos_capture", handoff)
        self.assertIn("--fail-on-audit-gaps", handoff)
        self.assertIn("<public-spoken-text>", handoff)
        self.assertIn("<audio-path>", handoff)
        self.assertIn("Guard backend estricto", handoff)
        self.assertIn("Flag de guard backend", handoff)
        self.assertIn("Campo JSON del guard", handoff)
        self.assertNotIn(str(tmpdir), handoff)
        self.assertIn("Paquete de comandos para pilotos reales AuralisVoiceKit", command_pack)
        self.assertIn("Comandos por plataforma", command_pack)
        self.assertIn("Auditoria y cierre", command_pack)
        self.assertIn("Windows - windows-wasapi-capture", command_pack)
        self.assertIn("Ubuntu/Linux - ubuntu-linux-capture", command_pack)
        self.assertIn("macOS - macos-capture", command_pack)
        self.assertIn("Windows / Ubuntu/Linux / macOS - system-output-audible", command_pack)
        self.assertIn("Windows / Ubuntu/Linux / macOS - real-transcription-quality", command_pack)
        self.assertIn("transcription-audio-fixture-openai", command_pack)
        self.assertIn("transcription-openai-mp3-preflight", command_pack)
        self.assertIn("--preflight-backend openai", command_pack)
        self.assertIn("--preflight-timeout-seconds 30", command_pack)
        self.assertIn("--backend openai", command_pack)
        self.assertIn("--require-openai-api-key", command_pack)
        self.assertIn("Campos condicionales", command_pack)
        self.assertIn("target_backend.name", command_pack)
        self.assertIn("credentials.checked", command_pack)
        self.assertIn("credentials.openai_api_key_required", command_pack)
        self.assertIn("credentials.openai_api_key_present", command_pack)
        self.assertIn("credentials.records_openai_api_key", command_pack)
        self.assertIn("gpt-4o-mini-transcribe", command_pack)
        self.assertIn("--confirm-input-reviewed", command_pack)
        self.assertIn("--confirm-text-reviewed", command_pack)
        self.assertIn("--confirm-voice-reviewed", command_pack)
        self.assertIn("--confirm-audio-reviewed", command_pack)
        self.assertIn("--confirm-reference-reviewed", command_pack)
        self.assertIn("--confirm-quality-reviewed", command_pack)
        self.assertIn("--require-output-backend-ready", command_pack)
        self.assertIn("--require-target-backend-ready", command_pack)
        self.assertIn("target_backend_ready_required", command_pack)
        self.assertIn("output_backend_ready_required", command_pack)
        self.assertIn("Campos requeridos", command_pack)
        self.assertIn("Guard backend estricto", command_pack)
        self.assertIn("--fail-on-audit-gaps", command_pack)
        self.assertIn("BETA_CHECKLIST.md", command_pack)
        self.assertIn("<public-spoken-text>", command_pack)
        self.assertIn("<audio-path>", command_pack)
        self.assertIn("real-pilot-environment-checklist.md", command_pack)
        self.assertIn("real-pilot-fixture-preflight.md", command_pack)
        self.assertIn("real-pilot-transcription-readiness.md", command_pack)
        self.assertIn("real-pilot-system-output-readiness.md", command_pack)
        self.assertIn("real-pilot-evidence-manifest.md", command_pack)
        self.assertIn("real-pilot-decision-gate.md", command_pack)
        self.assertNotIn(str(tmpdir), command_pack)
        self.assertIn("Checklist de entorno para pilotos reales AuralisVoiceKit", environment_checklist)
        self.assertIn("Usable como evidencia beta: `false`", environment_checklist)
        self.assertIn("ffmpeg-compressed-audio", environment_checklist)
        self.assertIn("system-output-backend", environment_checklist)
        self.assertIn("whisper-transcription-backend", environment_checklist)
        self.assertIn("openai-transcription-backend", environment_checklist)
        self.assertIn("windows-wasapi-capture", environment_checklist)
        self.assertIn("linux-sounddevice-capture", environment_checklist)
        self.assertIn("macos-sounddevice-capture", environment_checklist)
        self.assertIn("target-system-required", environment_checklist)
        self.assertIn("--fail-on-audit-gaps", environment_checklist)
        self.assertNotIn(str(tmpdir), environment_checklist)
        self.assertIn("Tarjeta de preflight de fixture de transcripcion AuralisVoiceKit", fixture_preflight)
        self.assertIn("Usable como evidencia beta: `false`", fixture_preflight)
        self.assertIn("Prepara transcripcion real: `true`", fixture_preflight)
        self.assertIn("pilot_audio_fixture.py", fixture_preflight)
        self.assertIn("--run-preflight", fixture_preflight)
        self.assertIn("Fixture OpenAI", fixture_preflight)
        self.assertIn("MP3 propio OpenAI", fixture_preflight)
        self.assertIn("--preflight-backend openai", fixture_preflight)
        self.assertIn("--preflight-timeout-seconds 30", fixture_preflight)
        self.assertIn("--require-openai-api-key", fixture_preflight)
        self.assertIn("transcription_pilot.py --preflight-only", fixture_preflight)
        self.assertIn("pilot-audio-fixture-report.json", fixture_preflight)
        self.assertIn("pilot-audio-fixture-findings.md", fixture_preflight)
        self.assertIn("transcription-review-checklist.md", fixture_preflight)
        self.assertIn("real-transcription-next-step.md", fixture_preflight)
        self.assertIn("ffmpeg estado", fixture_preflight)
        self.assertIn("Do not treat the synthetic fixture as beta evidence.", fixture_preflight)
        self.assertNotIn(str(tmpdir), fixture_preflight)
        self.assertIn("Tarjeta de readiness de transcripcion real AuralisVoiceKit", transcription_readiness)
        self.assertIn("Usable como evidencia beta: `false`", transcription_readiness)
        self.assertIn("Prepara transcripcion real: `true`", transcription_readiness)
        self.assertIn("tools/transcription_pilot.py", transcription_readiness)
        self.assertIn("Preflight MP3 propio OpenAI", transcription_readiness)
        self.assertIn("Transcripcion real OpenAI", transcription_readiness)
        self.assertIn("--backend openai", transcription_readiness)
        self.assertIn("--require-openai-api-key", transcription_readiness)
        self.assertIn("--timeout-seconds 30", transcription_readiness)
        self.assertIn("gpt-4o-mini-transcribe", transcription_readiness)
        self.assertIn("transcription-review-checklist.md", transcription_readiness)
        self.assertIn("real-transcription-next-step.md", transcription_readiness)
        self.assertIn("--real-transcription", transcription_readiness)
        self.assertIn("--confirm-audio-reviewed", transcription_readiness)
        self.assertIn("--confirm-reference-reviewed", transcription_readiness)
        self.assertIn("--confirm-quality-reviewed", transcription_readiness)
        self.assertIn("--require-target-backend-ready", transcription_readiness)
        self.assertIn("--timeout-seconds 30", transcription_readiness)
        self.assertIn("target_backend.available", transcription_readiness)
        self.assertIn("preflight_decision", transcription_readiness)
        self.assertIn("preflight_decision.decision", transcription_readiness)
        self.assertIn("reference_privacy_scan.passed", transcription_readiness)
        self.assertIn("Do not run a real transcription model with private or unreviewed audio.", transcription_readiness)
        self.assertNotIn(str(tmpdir), transcription_readiness)
        self.assertIn("Tarjeta de readiness de salida system AuralisVoiceKit", system_output_readiness)
        self.assertIn("Usable como evidencia beta: `false`", system_output_readiness)
        self.assertIn("Prepara salida audible: `true`", system_output_readiness)
        self.assertIn("tools/output_pilot.py", system_output_readiness)
        self.assertIn("output-operator-checklist.md", system_output_readiness)
        self.assertIn("system-output-next-step.md", system_output_readiness)
        self.assertIn("--confirm-audible", system_output_readiness)
        self.assertIn("--confirm-text-reviewed", system_output_readiness)
        self.assertIn("--confirm-voice-reviewed", system_output_readiness)
        self.assertIn("--require-output-backend-ready", system_output_readiness)
        self.assertIn("Do not run real system output without an operator present.", system_output_readiness)
        self.assertNotIn(str(tmpdir), system_output_readiness)
        self.assertIn("Manifiesto de evidencias para pilotos reales AuralisVoiceKit", evidence_manifest)
        self.assertIn("Usable como evidencia beta: `false`", evidence_manifest)
        self.assertIn("Tabla de evidencias", evidence_manifest)
        self.assertIn("real_transcription_quality", evidence_manifest)
        self.assertIn("system_output_audible", evidence_manifest)
        self.assertIn("ubuntu_linux_capture", evidence_manifest)
        self.assertIn("macos_capture", evidence_manifest)
        self.assertIn("Resumen por blocker", evidence_manifest)
        self.assertIn("Candidato mas cercano", evidence_manifest)
        self.assertIn("transcription-pilot-report.json", evidence_manifest)
        self.assertIn("output-pilot-report.json", evidence_manifest)
        self.assertIn("manual-pilot-report.json", evidence_manifest)
        self.assertIn("--fail-on-audit-gaps", evidence_manifest)
        self.assertIn("target_backend_ready_required", evidence_manifest)
        self.assertIn("output_backend_ready_required", evidence_manifest)
        self.assertNotIn(str(tmpdir), evidence_manifest)
        self.assertIn("Compuerta go/no-go para pilotos reales AuralisVoiceKit", decision_gate)
        self.assertIn("Pilotos reales: `go`", decision_gate)
        self.assertIn("Beta: `blocked`", decision_gate)
        self.assertIn("Estable: `blocked`", decision_gate)
        self.assertIn("Siguiente paso recomendado", decision_gate)
        self.assertIn("transcription-audio-fixture", decision_gate)
        self.assertIn("Condiciones de alto", decision_gate)
        self.assertIn("real-pilot-environment-checklist.md", decision_gate)
        self.assertIn("real-pilot-fixture-preflight.md", decision_gate)
        self.assertIn("real-pilot-transcription-readiness.md", decision_gate)
        self.assertIn("real-pilot-system-output-readiness.md", decision_gate)
        self.assertIn("real-pilot-evidence-manifest.md", decision_gate)
        self.assertNotIn(str(tmpdir), decision_gate)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Resumen por blocker", plan)
        self.assertIn("Candidato mas cercano", plan)
        self.assertIn("Proximas evidencias beta", plan)
        self.assertIn("--confirm-audible", plan)
        self.assertIn("--confirm-voice-reviewed", plan)
        self.assertIn("--require-output-backend-ready", plan)
        self.assertIn("Guard backend estricto", plan)
        self.assertIn("Flag de guard backend", plan)
        self.assertIn("Campo JSON del guard", plan)
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
        self.assertIn("--require-target-backend-ready", plan)
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
        manifest_rows = {row["blocker"]: row for row in report["evidence_manifest"]["rows"]}
        self.assertIn("real_transcription_quality", manifest_rows)
        self.assertIn("system_output_audible", manifest_rows)
        self.assertIn("ubuntu_linux_capture", manifest_rows)
        self.assertIn("macos_capture", manifest_rows)
        self.assertEqual(manifest_rows["real_transcription_quality"]["status"], "pending")
        self.assertEqual(manifest_rows["real_transcription_quality"]["artifact"], "transcription-pilot-report.json")
        self.assertIn("target_backend.available", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.generated_synthetic_audio", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.decoded", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.duration_gate.enabled", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.duration_gate.passed", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("transcript.text_redacted", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn(
            "transcription_checklist.redacts_transcript_text",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertEqual(
            manifest_rows["real_transcription_quality"]["conditional_required_fields"][0]["when"]["path"],
            "target_backend.name",
        )
        self.assertIn(
            "credentials.checked",
            manifest_rows["real_transcription_quality"]["conditional_required_fields"][0]["fields"],
        )
        self.assertIn(
            "credentials.openai_api_key_required",
            manifest_rows["real_transcription_quality"]["conditional_required_fields"][0]["fields"],
        )
        self.assertTrue(manifest_rows["real_transcription_quality"]["strict_backend_guard_required"])
        self.assertEqual(
            manifest_rows["real_transcription_quality"]["strict_backend_guard_flag"],
            "--require-target-backend-ready",
        )
        self.assertEqual(manifest_rows["system_output_audible"]["status"], "pending")
        self.assertEqual(manifest_rows["system_output_audible"]["artifact"], "output-pilot-report.json")
        self.assertIn(
            "operator_checklist.redacts_spoken_text",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertIn(
            "next_system_output.records_spoken_text",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertTrue(manifest_rows["system_output_audible"]["strict_backend_guard_required"])
        self.assertEqual(
            manifest_rows["system_output_audible"]["strict_backend_guard_flag"],
            "--require-output-backend-ready",
        )
        self.assertEqual(report["evidence_manifest"]["pending_count"], len(report["evidence_manifest"]["pending_blockers"]))
        self.assertIn("--fail-on-audit-gaps", report["evidence_manifest"]["strict_audit_command"])
        self.assertEqual(report["pilot_decision_gate"]["real_world_pilot"]["decision"], "go")
        self.assertEqual(report["pilot_decision_gate"]["beta"]["decision"], "blocked")
        self.assertIn("real_transcription_quality", report["pilot_decision_gate"]["beta"]["blockers"])
        self.assertEqual(report["pilot_decision_gate"]["stable"]["decision"], "blocked")
        self.assertIn("version_is_pre_1_0", report["pilot_decision_gate"]["stable"]["blockers"])
        self.assertEqual(report["pilot_decision_gate"]["next_recommended_step"]["name"], "transcription-audio-fixture")
        self.assertFalse(report["pilot_decision_gate"]["next_recommended_step"]["requires_hardware"])
        self.assertIn("local-real-transcription-ready", report["pilot_decision_gate"]["local_environment_warnings"])
        self.assertEqual(report["fixture_preflight_card"]["status"], "recommended")
        self.assertFalse(report["fixture_preflight_card"]["usable_as_beta_evidence"])
        self.assertIn("pilot-audio-fixture-report.json", report["fixture_preflight_card"]["expected_artifacts"])
        self.assertIn("preflight.passed", report["fixture_preflight_card"]["required_fields"])
        self.assertIn("--preflight-backend openai", report["fixture_preflight_card"]["openai_fixture_command"])
        self.assertIn("--preflight-timeout-seconds 30", report["fixture_preflight_card"]["openai_fixture_command"])
        self.assertIn("--backend openai", report["fixture_preflight_card"]["openai_own_audio_preflight_command"])
        self.assertIn(
            "preflight.transcription_timeout_seconds",
            report["fixture_preflight_card"]["openai_fixture_required_fields"],
        )
        self.assertIn("audio.decoded", report["fixture_preflight_card"]["own_audio_required_fields"])
        self.assertIn(
            "transcription_timeout_seconds",
            report["fixture_preflight_card"]["openai_own_audio_required_fields"],
        )
        self.assertIn(
            "credentials.checked",
            report["fixture_preflight_card"]["openai_own_audio_required_fields"],
        )
        self.assertIn(
            "credentials.openai_api_key_present",
            report["fixture_preflight_card"]["openai_own_audio_required_fields"],
        )
        self.assertIn(
            "credentials.records_openai_api_key",
            report["fixture_preflight_card"]["openai_own_audio_required_fields"],
        )
        self.assertIn("status", report["fixture_preflight_card"]["ffmpeg"])
        self.assertFalse(report["fixture_preflight_card"]["content_policy"]["records_audio"])
        self.assertEqual(report["transcription_readiness_card"]["status"], "recommended")
        self.assertFalse(report["transcription_readiness_card"]["usable_as_beta_evidence"])
        self.assertIn("transcription-pilot-report.json", report["transcription_readiness_card"]["expected_artifacts"])
        self.assertIn("--preflight-backend openai", report["transcription_readiness_card"]["openai_fixture_command"])
        self.assertIn("--backend openai", report["transcription_readiness_card"]["openai_preflight_command"])
        self.assertIn("--backend openai", report["transcription_readiness_card"]["openai_real_command"])
        self.assertIn(
            "--require-openai-api-key",
            report["transcription_readiness_card"]["openai_preflight_command"],
        )
        self.assertIn("--require-openai-api-key", report["transcription_readiness_card"]["openai_real_command"])
        self.assertIn("--timeout-seconds 30", report["transcription_readiness_card"]["openai_real_command"])
        self.assertIn("target_backend.available", report["transcription_readiness_card"]["real_required_fields"])
        self.assertIn("audio.generated_synthetic_audio", report["transcription_readiness_card"]["real_required_fields"])
        self.assertIn("audio.decoded", report["transcription_readiness_card"]["real_required_fields"])
        self.assertIn(
            "target_backend_ready_required",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn("transcript.text_redacted", report["transcription_readiness_card"]["real_required_fields"])
        self.assertIn(
            "transcription_checklist.redacts_transcript_text",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn(
            "reference_privacy_scan.passed",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        real_conditional_fields = report["transcription_readiness_card"]["real_conditional_required_fields"]
        self.assertEqual(real_conditional_fields[0]["when"]["path"], "target_backend.name")
        self.assertEqual(real_conditional_fields[0]["when"]["expected"], "openai")
        self.assertIn("credentials.checked", real_conditional_fields[0]["fields"])
        self.assertIn("credentials.openai_api_key_required", real_conditional_fields[0]["fields"])
        self.assertIn("credentials.openai_api_key_present", real_conditional_fields[0]["fields"])
        self.assertIn("credentials.records_openai_api_key", real_conditional_fields[0]["fields"])
        self.assertIn("status", report["transcription_readiness_card"]["ffmpeg"])
        self.assertIn("status", report["transcription_readiness_card"]["local_transcription"])
        self.assertFalse(report["transcription_readiness_card"]["content_policy"]["records_audio"])
        self.assertFalse(report["transcription_readiness_card"]["content_policy"]["records_transcripts"])
        self.assertFalse(report["transcription_readiness_card"]["content_policy"]["records_expected_text"])
        self.assertEqual(report["system_output_readiness_card"]["status"], "recommended")
        self.assertFalse(report["system_output_readiness_card"]["usable_as_beta_evidence"])
        self.assertIn("output-pilot-report.json", report["system_output_readiness_card"]["expected_artifacts"])
        self.assertIn("operator_checklist.ready_for_beta_evidence", report["system_output_readiness_card"]["required_fields"])
        self.assertIn("target_output_backend.available", report["system_output_readiness_card"]["audible_required_fields"])
        self.assertIn(
            "operator_checklist.redacts_spoken_text",
            report["system_output_readiness_card"]["audible_required_fields"],
        )
        self.assertIn(
            "next_system_output.records_spoken_text",
            report["system_output_readiness_card"]["audible_required_fields"],
        )
        self.assertIn("status", report["system_output_readiness_card"]["output_backend"])
        self.assertFalse(report["system_output_readiness_card"]["content_policy"]["records_spoken_text"])
        decision_environment_rows = {row["name"]: row for row in report["environment_checklist"]}
        expected_target_system_checks = {
            name
            for name, row in decision_environment_rows.items()
            if row["status"] == "target-system-required"
        }
        self.assertEqual(set(report["pilot_decision_gate"]["target_system_checks"]), expected_target_system_checks)
        self.assertTrue(report["pilot_decision_gate"]["target_system_checks"])
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
        self.assertIn(
            "target_backend.available",
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
        self.assertTrue(transcription_step["strict_backend_guard_required"])
        self.assertEqual(transcription_step["strict_backend_guard_flag"], "--require-target-backend-ready")
        self.assertEqual(transcription_step["strict_backend_guard_field"], "target_backend_ready_required")
        self.assertIn("--confirm-quality-reviewed", transcription_step["command"])
        self.assertIn("--confirm-audio-reviewed", transcription_step["command"])
        self.assertIn("--confirm-reference-reviewed", transcription_step["command"])
        self.assertIn("--require-target-backend-ready", transcription_step["command"])
        self.assertIn("target_backend.available", transcription_step["required_fields"])
        self.assertIn("target_backend_ready_required", transcription_step["required_fields"])
        self.assertIn("audio.generated_synthetic_audio", transcription_step["required_fields"])
        self.assertIn("audio.audio_confirmed_non_sensitive", transcription_step["required_fields"])
        self.assertIn("audio.decoded", transcription_step["required_fields"])
        self.assertIn("audio.duration_gate.enabled", transcription_step["required_fields"])
        self.assertIn("audio.duration_gate.passed", transcription_step["required_fields"])
        self.assertIn("transcript.text_redacted", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.audio_review_confirmed", transcription_step["required_fields"])
        self.assertIn("audio.audio_file_name_redacted", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.records_audio_file_name", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.records_expected_text_file_name", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.redacts_transcript_text", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.redacts_expected_text", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.reference_review_confirmed", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", transcription_step["required_fields"])
        self.assertIn("transcription_checklist.quality_review_confirmed", transcription_step["required_fields"])
        self.assertEqual(transcription_step["conditional_required_fields"][0]["when"]["path"], "target_backend.name")
        self.assertIn("credentials.checked", transcription_step["conditional_required_fields"][0]["fields"])
        self.assertIn("credentials.openai_api_key_required", transcription_step["conditional_required_fields"][0]["fields"])
        self.assertIn("--confirm-voice-reviewed", output_step["command"])
        self.assertIn("--confirm-text-reviewed", output_step["command"])
        self.assertIn("--require-output-backend-ready", output_step["command"])
        self.assertTrue(output_step["strict_backend_guard_required"])
        self.assertEqual(output_step["strict_backend_guard_flag"], "--require-output-backend-ready")
        self.assertEqual(output_step["strict_backend_guard_field"], "output_backend_ready_required")
        self.assertIn('--expected-system "Windows|Linux|Darwin"', output_step["command"])
        self.assertIn("system_guard.expected_system_matched", output_step["required_fields"])
        self.assertIn("target_output_backend.available", output_step["required_fields"])
        self.assertIn("output_backend_ready_required", output_step["required_fields"])
        self.assertIn("text_review_confirmed", output_step["required_fields"])
        self.assertIn("spoken_text_privacy_scan.passed", output_step["required_fields"])
        self.assertIn("operator_checklist.expected_system_matched", output_step["required_fields"])
        self.assertIn("operator_checklist.text_review_confirmed", output_step["required_fields"])
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", output_step["required_fields"])
        self.assertIn("operator_checklist.voice_review_confirmed", output_step["required_fields"])
        self.assertIn("operator_checklist.records_operator_identity", output_step["required_fields"])
        self.assertIn("operator_checklist.redacts_spoken_text", output_step["required_fields"])
        self.assertIn("operator_checklist.commands_available", output_step["required_fields"])
        self.assertIn("operator_checklist.ready_for_real_audio", output_step["required_fields"])
        self.assertIn("next_system_output.uses_placeholders", output_step["required_fields"])
        self.assertIn("next_system_output.records_spoken_text", output_step["required_fields"])
        self.assertIn("next_system_output.records_operator_identity", output_step["required_fields"])
        self.assertFalse(checklist_step["requires_hardware"])
        self.assertFalse(checklist_step["requires_operator"])
        self.assertFalse(checklist_step["strict_backend_guard_required"])
        self.assertIn("operator_checklist.ready_for_beta_evidence", checklist_step["required_fields"])
        self.assertIn("artifacts.system_output_next_step", checklist_step["required_fields"])
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertIn("--confirm-input-reviewed", matrix["ubuntu-linux-capture"]["command"])
        self.assertIn("--confirm-input-reviewed", matrix["macos-capture"]["command"])
        self.assertEqual(matrix["windows-wasapi-capture"]["status"], "closed")
        self.assertEqual(matrix["ubuntu-linux-capture"]["status"], "pending")
        self.assertEqual(matrix["macos-capture"]["status"], "pending")
        self.assertEqual(matrix["transcription-audio-fixture"]["status"], "recommended")
        self.assertEqual(matrix["transcription-audio-fixture-openai"]["status"], "recommended")
        self.assertEqual(matrix["transcription-mp3-preflight"]["status"], "recommended")
        self.assertEqual(matrix["transcription-openai-mp3-preflight"]["status"], "recommended")
        self.assertIn("--preflight-backend openai", matrix["transcription-audio-fixture-openai"]["command"])
        self.assertIn("--preflight-timeout-seconds 30", matrix["transcription-audio-fixture-openai"]["command"])
        self.assertIn("--backend openai", matrix["transcription-openai-mp3-preflight"]["command"])
        self.assertIn("--require-openai-api-key", matrix["transcription-openai-mp3-preflight"]["command"])
        self.assertIn("--timeout-seconds 30", matrix["transcription-openai-mp3-preflight"]["command"])
        self.assertIn("preflight.passed", matrix["transcription-audio-fixture"]["required_fields"])
        self.assertNotIn("preflight.model", matrix["transcription-audio-fixture"]["required_fields"])
        self.assertIn("preflight.model", matrix["transcription-audio-fixture-openai"]["required_fields"])
        self.assertIn(
            "preflight.transcription_timeout_seconds",
            matrix["transcription-audio-fixture-openai"]["required_fields"],
        )
        self.assertNotIn("model", matrix["transcription-mp3-preflight"]["required_fields"])
        self.assertIn("model", matrix["transcription-openai-mp3-preflight"]["required_fields"])
        self.assertIn(
            "transcription_timeout_seconds",
            matrix["transcription-openai-mp3-preflight"]["required_fields"],
        )
        self.assertIn(
            "credentials.checked",
            matrix["transcription-openai-mp3-preflight"]["required_fields"],
        )
        self.assertIn(
            "credentials.openai_api_key_present",
            matrix["transcription-openai-mp3-preflight"]["required_fields"],
        )
        self.assertIn(
            "credentials.records_openai_api_key",
            matrix["transcription-openai-mp3-preflight"]["required_fields"],
        )
        preflight_step = {
            step["name"]: step for step in report["recommended_pilot_sequence"]
        }["transcription-audio-preflight"]
        self.assertIn("preflight_decision.decision", preflight_step["required_fields"])
        self.assertIn("preflight_decision.blocking_reasons", preflight_step["required_fields"])
        self.assertIn("preflight_decision.backend_ready", preflight_step["required_fields"])
        self.assertIn("target_backend.available=true", matrix["real-transcription-quality"]["notes"])
        self.assertIn("target_backend_ready_required=true", matrix["real-transcription-quality"]["notes"])
        self.assertIn("audio.generated_synthetic_audio=false", matrix["real-transcription-quality"]["notes"])
        self.assertIn("audio.decoded=true", matrix["real-transcription-quality"]["notes"])
        self.assertIn("--timeout-seconds 30", matrix["real-transcription-quality"]["notes"])
        self.assertIn("transcript.text_redacted=true", matrix["real-transcription-quality"]["notes"])
        self.assertTrue(matrix["real-transcription-quality"]["strict_backend_guard_required"])
        self.assertEqual(
            matrix["real-transcription-quality"]["strict_backend_guard_flag"],
            "--require-target-backend-ready",
        )
        self.assertTrue(matrix["system-output-audible"]["requires_operator"])
        self.assertTrue(matrix["system-output-audible"]["strict_backend_guard_required"])
        self.assertIn("--confirm-voice-reviewed", matrix["system-output-audible"]["command"])
        self.assertIn("--confirm-text-reviewed", matrix["system-output-audible"]["command"])
        self.assertIn('--expected-system "Windows|Linux|Darwin"', matrix["system-output-audible"]["command"])
        self.assertIn("output_backend_ready_required=true", matrix["system-output-audible"]["notes"])
        self.assertIn("operator_checklist.redacts_spoken_text=true", matrix["system-output-audible"]["notes"])
        self.assertIn("next_system_output.records_spoken_text=false", matrix["system-output-audible"]["notes"])
        self.assertIn("--fail-on-audit-gaps", report["beta_readiness"]["strict_audit_command"])
        self.assertIn("Campos condicionales", evidence_manifest)
        self.assertIn("target_backend.name", evidence_manifest)
        self.assertIn("credentials.checked", evidence_manifest)
        self.assertIn("credentials.openai_api_key_required", evidence_manifest)
        environment_rows = {row["name"]: row for row in report["environment_checklist"]}
        self.assertIn("python-runtime", environment_rows)
        self.assertIn("ffmpeg-compressed-audio", environment_rows)
        self.assertIn("local-real-transcription-ready", environment_rows)
        self.assertIn("local-system-output-ready", environment_rows)
        self.assertIn(environment_rows["python-runtime"]["status"], {"ok", "warning", "error"})
        self.assertIsInstance(environment_rows["local-real-transcription-ready"]["ready"], bool)
        self.assertIsInstance(environment_rows["local-system-output-ready"]["ready"], bool)
        self.assertEqual(environment_rows["linux-sounddevice-capture"]["target_system"], "Linux")
        self.assertEqual(environment_rows["macos-sounddevice-capture"]["target_system"], "Darwin")
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
        self.assertIn("real_pilot_command_pack", payload)
        self.assertIn("real_pilot_environment_checklist", payload)
        self.assertIn("real_pilot_fixture_preflight", payload)
        self.assertIn("real_pilot_transcription_readiness", payload)
        self.assertIn("real_pilot_system_output_readiness", payload)
        self.assertIn("real_pilot_evidence_manifest", payload)
        self.assertIn("real_pilot_decision_gate", payload)
        self.assertIn("environment_checklist", payload)
        self.assertIn("evidence_manifest", payload)
        self.assertIn("fixture_preflight_card", payload)
        self.assertIn("transcription_readiness_card", payload)
        self.assertIn("system_output_readiness_card", payload)
        self.assertIn("pilot_decision_gate", payload)
        self.assertIn("beta_readiness", payload)
        self.assertIn("real_pilot_handoff", payload["artifacts"])
        self.assertIn("real_pilot_findings_template", payload["artifacts"])
        self.assertIn("real_pilot_command_pack", payload["artifacts"])
        self.assertIn("real_pilot_environment_checklist", payload["artifacts"])
        self.assertIn("real_pilot_fixture_preflight", payload["artifacts"])
        self.assertIn("real_pilot_transcription_readiness", payload["artifacts"])
        self.assertIn("real_pilot_system_output_readiness", payload["artifacts"])
        self.assertIn("real_pilot_evidence_manifest", payload["artifacts"])
        self.assertIn("real_pilot_decision_gate", payload["artifacts"])
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
                    "capture_backend": "pyaudio",
                    "target_capture_backend": {
                        "name": "pyaudio",
                        "kind": "capture",
                        "available": True,
                        "dependencies": ["pyaudio"],
                        "reason": None,
                    },
                    "capture_backend_ready_required": True,
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
            evidence_manifest = Path(report["artifacts"]["real_pilot_evidence_manifest"]).read_text(encoding="utf-8")
            decision_gate = Path(report["artifacts"]["real_pilot_decision_gate"]).read_text(encoding="utf-8")

        self.assertEqual(report["beta_readiness"]["evidence_count"], 1)
        self.assertEqual(report["beta_readiness"]["ignored_evidence_count"], 1)
        self.assertEqual(report["beta_readiness"]["satisfied_json_blockers"], ["ubuntu_linux_capture"])
        self.assertEqual(report["beta_readiness"]["accepted_json_artifacts"][0]["artifact"], "manual-pilot-report.json")
        self.assertEqual(report["beta_readiness"]["ignored_json_artifacts"][0]["reason"], "missing_project")
        summaries = {summary["name"]: summary for summary in report["beta_readiness"]["blocker_summaries"]}
        self.assertEqual(summaries["ubuntu_linux_capture"]["status"], "closed")
        self.assertEqual(summaries["ubuntu_linux_capture"]["accepted_sources"], ["linux/manual-pilot-report.json"])
        self.assertEqual(report["evidence_manifest"]["blocker_summaries"], report["beta_readiness"]["blocker_summaries"])
        focus = report["beta_readiness"]["next_evidence_focus"]
        self.assertEqual(focus["status"], "pending")
        self.assertEqual(focus["name"], "real_transcription_quality")
        self.assertEqual(report["evidence_manifest"]["next_evidence_focus"], focus)
        self.assertEqual(report["pilot_decision_gate"]["next_evidence_focus"], focus)
        self.assertNotIn("ubuntu_linux_capture", report["beta_readiness"]["blockers"])
        self.assertNotIn("ubuntu_linux_capture", {step["name"] for step in report["next_beta_evidence_steps"]})
        sequence_names = {step["name"] for step in report["recommended_pilot_sequence"]}
        self.assertNotIn("ubuntu_linux_capture", sequence_names)
        self.assertIn("audit-evidence", sequence_names)
        self.assertIn("refresh-beta-checklist", sequence_names)
        self.assertIn("Evidencias JSON", plan)
        self.assertIn("Resumen por blocker", plan)
        self.assertIn("Siguiente foco de evidencia", plan)
        self.assertIn("Blocker: `real_transcription_quality`", plan)
        self.assertIn("Fuentes que cierran: `linux/manual-pilot-report.json`", plan)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Blockers cerrados: `ubuntu_linux_capture`", plan)
        self.assertIn("real-pilot-evidence-manifest.md", plan)
        self.assertIn("real-pilot-decision-gate.md", plan)
        self.assertIn("missing_project", plan)
        self.assertNotIn(str(evidence_root), plan)
        self.assertNotIn("Ubuntu/Linux capture pilot", plan)
        manifest_rows = {row["blocker"]: row for row in report["evidence_manifest"]["rows"]}
        self.assertEqual(manifest_rows["ubuntu_linux_capture"]["status"], "closed")
        self.assertEqual(
            manifest_rows["ubuntu_linux_capture"]["accepted_json_artifact"],
            "linux/manual-pilot-report.json",
        )
        self.assertIn("missing_project", evidence_manifest)
        self.assertIn("ubuntu_linux_capture", evidence_manifest)
        self.assertIn("Resumen por blocker", evidence_manifest)
        self.assertIn("Siguiente foco de evidencia", evidence_manifest)
        self.assertIn("Fuentes que cierran: `linux/manual-pilot-report.json`", evidence_manifest)
        self.assertIn("closed-by-accepted-json", evidence_manifest)
        self.assertNotIn(str(evidence_root), evidence_manifest)
        self.assertIn("Compuerta go/no-go", decision_gate)
        self.assertIn("Siguiente foco de evidencia", decision_gate)
        self.assertIn("Beta: `blocked`", decision_gate)
        self.assertNotIn(str(evidence_root), decision_gate)
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertEqual(matrix["ubuntu-linux-capture"]["status"], "closed")


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
