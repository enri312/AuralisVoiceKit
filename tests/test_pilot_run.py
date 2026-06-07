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
            next_focus_path = Path(report["artifacts"]["real_pilot_next_evidence_focus"])
            hard_stop_path = Path(report["artifacts"]["real_pilot_hard_stop_card"])
            evidence_intake_path = Path(report["artifacts"]["real_pilot_evidence_intake_card"])
            execution_card_path = Path(report["artifacts"]["real_pilot_execution_card"])
            consent_card_path = Path(report["artifacts"]["real_pilot_consent_card"])
            audit_closure_path = Path(report["artifacts"]["real_pilot_audit_closure_card"])
            rehearsal_card_path = Path(report["artifacts"]["real_pilot_rehearsal_card"])
            evidence_package_path = Path(report["artifacts"]["real_pilot_evidence_package_card"])
            operator_brief_path = Path(report["artifacts"]["real_pilot_operator_brief_card"])
            run_sheet_path = Path(report["artifacts"]["real_pilot_run_sheet_card"])
            final_go_no_go_path = Path(report["artifacts"]["real_pilot_final_go_no_go_card"])
            local_receipt_path = Path(report["artifacts"]["real_pilot_local_receipt_card"])

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
            self.assertTrue(next_focus_path.exists())
            self.assertTrue(hard_stop_path.exists())
            self.assertTrue(evidence_intake_path.exists())
            self.assertTrue(execution_card_path.exists())
            self.assertTrue(consent_card_path.exists())
            self.assertTrue(audit_closure_path.exists())
            self.assertTrue(rehearsal_card_path.exists())
            self.assertTrue(evidence_package_path.exists())
            self.assertTrue(operator_brief_path.exists())
            self.assertTrue(run_sheet_path.exists())
            self.assertTrue(final_go_no_go_path.exists())
            self.assertTrue(local_receipt_path.exists())
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
            next_focus = next_focus_path.read_text(encoding="utf-8")
            hard_stop = hard_stop_path.read_text(encoding="utf-8")
            evidence_intake = evidence_intake_path.read_text(encoding="utf-8")
            execution_card = execution_card_path.read_text(encoding="utf-8")
            consent_card = consent_card_path.read_text(encoding="utf-8")
            audit_closure = audit_closure_path.read_text(encoding="utf-8")
            rehearsal_card = rehearsal_card_path.read_text(encoding="utf-8")
            evidence_package = evidence_package_path.read_text(encoding="utf-8")
            operator_brief = operator_brief_path.read_text(encoding="utf-8")
            run_sheet = run_sheet_path.read_text(encoding="utf-8")
            final_go_no_go = final_go_no_go_path.read_text(encoding="utf-8")
            local_receipt = local_receipt_path.read_text(encoding="utf-8")

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
        self.assertIn("real_pilot_next_evidence_focus", persisted)
        self.assertIn("real_pilot_hard_stop_card", persisted)
        self.assertIn("real_pilot_evidence_intake_card", persisted)
        self.assertIn("real_pilot_execution_card", persisted)
        self.assertIn("real_pilot_consent_card", persisted)
        self.assertIn("real_pilot_audit_closure_card", persisted)
        self.assertIn("real_pilot_rehearsal_card", persisted)
        self.assertIn("real_pilot_evidence_package_card", persisted)
        self.assertIn("real_pilot_operator_brief_card", persisted)
        self.assertIn("real_pilot_run_sheet_card", persisted)
        self.assertIn("real_pilot_final_go_no_go_card", persisted)
        self.assertIn("real_pilot_local_receipt_card", persisted)
        self.assertIn("next_evidence_focus_preparation_sequence", persisted)
        self.assertIn("evidence_manifest", persisted)
        self.assertIn("fixture_preflight_card", persisted)
        self.assertIn("transcription_readiness_card", persisted)
        self.assertIn("system_output_readiness_card", persisted)
        self.assertIn("release_batch", persisted)
        self.assertIn("release_batch", persisted["gate"])
        self.assertIn("release_batch", persisted["pilot_decision_gate"])
        self.assertEqual(persisted["release_batch"], persisted["gate"]["release_batch"])
        self.assertEqual(persisted["release_batch"], persisted["pilot_decision_gate"]["release_batch"])
        self.assertEqual(persisted["release_batch"]["threshold"], 5)
        self.assertEqual(persisted["release_batch"]["policy"]["tag_every_publishable_commits"], 5)
        self.assertIn("latest_tag", persisted["release_batch"])
        self.assertIn("commit_count", persisted["release_batch"])
        self.assertIn("ready_for_tag", persisted["release_batch"])
        self.assertIn("remaining", persisted["release_batch"])
        self.assertIn("Mejoras desde ultimo tag", plan)
        self.assertIn("Crear tag ahora", plan)
        self.assertIn("Release batch listo para tag", plan)
        self.assertIn("Mejoras desde ultimo tag", handoff)
        self.assertIn("Crear tag ahora", handoff)
        self.assertIn("Crear tag ahora", decision_gate)
        self.assertIn("Mejoras restantes antes de tag", decision_gate)
        self.assertIn("no crear GitHub Release", decision_gate)
        self.assertIn(
            "system_output_command_card.python_extra=null",
            persisted["system_output_readiness_card"]["no_pip_extra_contract"],
        )
        self.assertIn(
            "system_output_command_card.pip_command=null",
            persisted["system_output_readiness_card"]["no_pip_extra_contract"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
            persisted["system_output_readiness_card"]["no_pip_extra_contract"],
        )
        self.assertIn("## Contrato sin extra pip", system_output_readiness)
        self.assertIn("system_output_command_card.python_extra=null", system_output_readiness)
        self.assertIn("system_output_command_card.pip_command=null", system_output_readiness)
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
            system_output_readiness,
        )
        self.assertIn("pilot_decision_gate", persisted)
        self.assertIn("blocker_summaries", persisted["beta_readiness"])
        self.assertIn("blocker_summaries", persisted["evidence_manifest"])
        self.assertIn("privacy_audit", persisted["beta_readiness"])
        self.assertEqual(persisted["beta_readiness"]["privacy_audit"]["status"], "passed")
        self.assertEqual(persisted["beta_readiness"]["privacy_audit"]["finding_count"], 0)
        self.assertEqual(persisted["evidence_manifest"]["privacy_audit"]["status"], "passed")
        self.assertEqual(persisted["pilot_decision_gate"]["privacy_audit"]["status"], "passed")
        self.assertEqual(persisted["beta_readiness"]["privacy_remediation_plan"]["status"], "not_required")
        self.assertEqual(persisted["evidence_manifest"]["privacy_remediation_plan"]["status"], "not_required")
        self.assertEqual(persisted["pilot_decision_gate"]["privacy_remediation_plan"]["status"], "not_required")
        self.assertIn("real_pilot_handoff", persisted["artifacts"])
        self.assertIn("real_pilot_findings_template", persisted["artifacts"])
        self.assertIn("real_pilot_command_pack", persisted["artifacts"])
        self.assertIn("real_pilot_environment_checklist", persisted["artifacts"])
        self.assertIn("real_pilot_fixture_preflight", persisted["artifacts"])
        self.assertIn("real_pilot_transcription_readiness", persisted["artifacts"])
        self.assertIn("real_pilot_system_output_readiness", persisted["artifacts"])
        self.assertIn("real_pilot_evidence_manifest", persisted["artifacts"])
        self.assertIn("real_pilot_decision_gate", persisted["artifacts"])
        self.assertIn("real_pilot_next_evidence_focus", persisted["artifacts"])
        self.assertIn("real_pilot_hard_stop_card", persisted["artifacts"])
        self.assertIn("real_pilot_evidence_intake_card", persisted["artifacts"])
        self.assertIn("real_pilot_execution_card", persisted["artifacts"])
        self.assertIn("real_pilot_consent_card", persisted["artifacts"])
        self.assertIn("real_pilot_audit_closure_card", persisted["artifacts"])
        self.assertIn("real_pilot_rehearsal_card", persisted["artifacts"])
        self.assertIn("real_pilot_evidence_package_card", persisted["artifacts"])
        self.assertIn("real_pilot_operator_brief_card", persisted["artifacts"])
        self.assertIn("real_pilot_run_sheet_card", persisted["artifacts"])
        self.assertIn("real_pilot_final_go_no_go_card", persisted["artifacts"])
        self.assertIn("real_pilot_local_receipt_card", persisted["artifacts"])
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
        self.assertTrue(persisted["real_pilot_next_evidence_focus"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_hard_stop_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_evidence_intake_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_execution_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_consent_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_audit_closure_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_rehearsal_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_evidence_package_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_operator_brief_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_run_sheet_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_final_go_no_go_card"]["safe_to_share"])
        self.assertTrue(persisted["real_pilot_local_receipt_card"]["safe_to_share"])
        self.assertFalse(persisted["real_pilot_environment_checklist"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_fixture_preflight"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_transcription_readiness"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_system_output_readiness"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_evidence_manifest"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_decision_gate"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_execution_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_consent_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["usable_as_beta_evidence"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["usable_as_beta_evidence"])
        self.assertTrue(persisted["real_pilot_fixture_preflight"]["prepares_real_transcription"])
        self.assertTrue(persisted["real_pilot_transcription_readiness"]["prepares_real_transcription"])
        self.assertTrue(persisted["real_pilot_system_output_readiness"]["prepares_audible_output"])
        self.assertTrue(persisted["real_pilot_evidence_manifest"]["tracks_pending_and_closed_blockers"])
        self.assertTrue(persisted["real_pilot_decision_gate"]["declares_real_world_pilot_scope"])
        self.assertTrue(persisted["real_pilot_decision_gate"]["declares_beta_and_stable_blockers"])
        self.assertTrue(persisted["real_pilot_next_evidence_focus"]["tracks_next_evidence_focus"])
        self.assertTrue(persisted["real_pilot_next_evidence_focus"]["tracks_preparation_sequence"])
        self.assertTrue(persisted["real_pilot_hard_stop_card"]["declares_hard_stop_conditions"])
        self.assertTrue(persisted["real_pilot_hard_stop_card"]["declares_operator_actions"])
        self.assertTrue(persisted["real_pilot_evidence_intake_card"]["tracks_expected_artifacts"])
        self.assertTrue(persisted["real_pilot_evidence_intake_card"]["tracks_audit_commands"])
        self.assertIn("pilot_runs/manual/windows", persisted["real_pilot_evidence_intake_card"]["suggested_roots"])
        self.assertTrue(persisted["real_pilot_execution_card"]["tracks_execution_order"])
        self.assertTrue(persisted["real_pilot_execution_card"]["tracks_human_confirmations"])
        self.assertTrue(persisted["real_pilot_execution_card"]["tracks_audit_closure"])
        self.assertEqual(persisted["real_pilot_execution_card"]["focus"], "windows_wasapi_capture")
        operator_gate = persisted["real_pilot_execution_card"]["operator_gate"]
        self.assertEqual(operator_gate["decision"], "ready_for_local_operator")
        self.assertTrue(operator_gate["allowed_to_run"])
        self.assertTrue(operator_gate["requires_local_operator_review"])
        self.assertEqual(operator_gate["blocking_reasons"], [])
        self.assertEqual(operator_gate["focus"], "windows_wasapi_capture")
        self.assertEqual(operator_gate["focus_status"], "pending")
        self.assertEqual(operator_gate["focus_artifact"], "manual-pilot-report.json")
        self.assertIn("real-pilot-hard-stop-card.md", operator_gate["pre_run_reviews"])
        self.assertIn("real-pilot-evidence-intake-card.md", operator_gate["pre_run_reviews"])
        self.assertIn("real-pilot-consent-card.md", operator_gate["pre_run_reviews"])
        self.assertIn("expected_system_review", operator_gate["human_confirmations"])
        self.assertIn("input_review_confirmed", operator_gate["human_confirmations"])
        self.assertIn("strict_backend_guard_enabled", operator_gate["human_confirmations"])
        self.assertTrue(operator_gate["strict_backend_guard_required"])
        command_audit = operator_gate["command_audit"]
        self.assertEqual(command_audit["status"], "passed")
        self.assertTrue(command_audit["safe_to_copy_for_local_operator"])
        self.assertIn("--expected-system", command_audit["required_flags"])
        self.assertIn("--confirm-input-reviewed", command_audit["required_flags"])
        self.assertIn("--require-capture-backend-ready", command_audit["required_flags"])
        self.assertIn("--expected-system", command_audit["present_required_flags"])
        self.assertIn("--confirm-input-reviewed", command_audit["present_required_flags"])
        self.assertIn("--require-capture-backend-ready", command_audit["present_required_flags"])
        self.assertEqual(command_audit["missing_required_flags"], [])
        self.assertIn("--sample-rate 48000", command_audit["command"])
        self.assertFalse(command_audit["records_private_values"])
        copy_safety = command_audit["copy_safety"]
        self.assertEqual(copy_safety["status"], "ready_for_local_review")
        self.assertTrue(copy_safety["safe_template"])
        self.assertTrue(copy_safety["safe_to_copy_for_local_operator"])
        self.assertTrue(copy_safety["copy_requires_local_operator_review"])
        self.assertTrue(copy_safety["copy_requires_consent_card"])
        self.assertTrue(copy_safety["copy_requires_human_confirmations"])
        self.assertTrue(copy_safety["copy_requires_strict_backend_guard_review"])
        self.assertEqual(copy_safety["blocking_reasons"], [])
        self.assertIn("local_placeholders_reviewed", copy_safety["pending_local_review_ids"])
        self.assertIn("human_confirmations_reviewed", copy_safety["pending_local_review_ids"])
        self.assertIn("strict_backend_guard_reviewed", copy_safety["pending_local_review_ids"])
        copy_review_ids = [item["id"] for item in copy_safety["review_items"]]
        self.assertIn("command_audit_passed", copy_review_ids)
        self.assertIn("required_flags_present", copy_review_ids)
        self.assertIn("no_private_values_recorded", copy_review_ids)
        self.assertFalse(copy_safety["records_private_values"])
        self.assertFalse(copy_safety["records_audio"])
        self.assertFalse(copy_safety["records_local_paths"])
        evidence_contract = operator_gate["evidence_contract"]
        self.assertTrue(evidence_contract["safe_to_share"])
        self.assertEqual(evidence_contract["blocker"], "windows_wasapi_capture")
        self.assertEqual(evidence_contract["expected_artifact"], "manual-pilot-report.json")
        self.assertIn("project", evidence_contract["required_fields"])
        self.assertIn("system_guard.expected_system_matched", evidence_contract["required_fields"])
        self.assertIn("manual_capture_command_card.safe_to_share", evidence_contract["required_fields"])
        self.assertIn("project", evidence_contract["missing_fields"])
        self.assertEqual(evidence_contract["required_field_count"], len(evidence_contract["required_fields"]))
        self.assertEqual(evidence_contract["missing_field_count"], len(evidence_contract["missing_fields"]))
        self.assertIn("pilot_runs/manual/windows", evidence_contract["suggested_roots"])
        self.assertIn("--fail-on-audit-gaps", evidence_contract["strict_audit_command"])
        self.assertFalse(evidence_contract["records_audio"])
        self.assertFalse(evidence_contract["records_transcripts"])
        self.assertFalse(evidence_contract["records_spoken_text"])
        self.assertFalse(evidence_contract["records_expected_text"])
        self.assertFalse(evidence_contract["records_local_paths"])
        self.assertFalse(evidence_contract["records_device_names"])
        self.assertFalse(evidence_contract["records_operator_identity"])
        self.assertTrue(operator_gate["audit_closure"]["required"])
        self.assertIn("--fail-on-audit-gaps", operator_gate["audit_closure"]["strict_audit_command"])
        self.assertEqual(operator_gate["audit_closure"]["expected_json_artifact"], "manual-pilot-report.json")
        self.assertIn("pilot_runs/manual/windows", operator_gate["audit_closure"]["suggested_roots"])
        self.assertFalse(operator_gate["content_policy"]["records_audio"])
        self.assertFalse(operator_gate["content_policy"]["records_transcripts"])
        self.assertFalse(operator_gate["content_policy"]["records_spoken_text"])
        self.assertFalse(operator_gate["content_policy"]["records_expected_text"])
        self.assertFalse(operator_gate["content_policy"]["records_local_paths"])
        self.assertFalse(operator_gate["content_policy"]["records_device_names"])
        self.assertFalse(operator_gate["content_policy"]["records_operator_identity"])
        consent = persisted["real_pilot_consent_card"]
        self.assertEqual(consent["artifact"], "real-pilot-consent-card.md")
        self.assertEqual(consent["decision"], "requires_local_operator_consent")
        self.assertEqual(consent["focus"], "windows_wasapi_capture")
        self.assertEqual(consent["focus_artifact"], "manual-pilot-report.json")
        self.assertTrue(consent["allowed_to_run_after_consent"])
        self.assertTrue(consent["requires_local_operator"])
        self.assertTrue(consent["requires_operator_consent"])
        self.assertFalse(consent["can_execute_without_operator"])
        self.assertFalse(consent["records_consent_identity"])
        self.assertFalse(consent["records_signature"])
        self.assertFalse(consent["records_timestamped_identity"])
        self.assertGreater(consent["missing_consent_count"], 0)
        self.assertIn("hard_stop_reviewed", consent["missing_consent_ids"])
        self.assertIn("strict_backend_guard_kept", consent["missing_consent_ids"])
        consent_ids = [item["id"] for item in consent["consent_items"]]
        self.assertIn("public_non_sensitive_scope", consent_ids)
        self.assertIn("confirm_flags_after_review", consent_ids)
        self.assertIn("audit_closure_accepted", consent_ids)
        self.assertIn("expected_system_review", consent["human_confirmations"])
        self.assertIn("input_review_confirmed", consent["human_confirmations"])
        self.assertIn("windows_wasapi_capture", consent["sequence_names"])
        self.assertIn("--fail-on-audit-gaps", consent["strict_audit_command"])
        self.assertFalse(consent["content_policy"]["records_audio"])
        self.assertFalse(consent["content_policy"]["records_transcripts"])
        self.assertFalse(consent["content_policy"]["records_spoken_text"])
        self.assertFalse(consent["content_policy"]["records_expected_text"])
        self.assertFalse(consent["content_policy"]["records_local_paths"])
        self.assertFalse(consent["content_policy"]["records_device_names"])
        self.assertFalse(consent["content_policy"]["records_operator_identity"])
        audit_closure_policy = persisted["real_pilot_audit_closure_card"]
        self.assertEqual(audit_closure_policy["artifact"], "real-pilot-audit-closure.md")
        self.assertEqual(audit_closure_policy["source"], "operator_gate.audit_closure + evidence_manifest + findings_template")
        self.assertEqual(audit_closure_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(audit_closure_policy["focus_status"], "pending")
        self.assertEqual(audit_closure_policy["expected_json_artifact"], "manual-pilot-report.json")
        self.assertEqual(audit_closure_policy["closure_status"], "waiting_for_real_evidence")
        self.assertTrue(audit_closure_policy["audit_required"])
        self.assertFalse(audit_closure_policy["can_close_without_audit"])
        self.assertFalse(audit_closure_policy["can_refresh_beta_without_audit"])
        self.assertTrue(audit_closure_policy["requires_sanitized_json"])
        self.assertTrue(audit_closure_policy["requires_privacy_audit"])
        self.assertTrue(audit_closure_policy["requires_findings_update"])
        self.assertIn("--fail-on-audit-gaps", audit_closure_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", audit_closure_policy["refresh_checklist_command"])
        self.assertIn("pilot_runs/manual/windows", audit_closure_policy["suggested_roots"])
        self.assertEqual(audit_closure_policy["finding_template"], "real-pilot-findings-template.md")
        self.assertEqual(audit_closure_policy["evidence_intake_card"], "real-pilot-evidence-intake-card.md")
        self.assertEqual(audit_closure_policy["execution_card"], "real-pilot-execution-card.md")
        self.assertEqual(audit_closure_policy["consent_card"], "real-pilot-consent-card.md")
        self.assertIn("strict_audit_passed", audit_closure_policy["pending_closure_ids"])
        self.assertIn("beta_checklist_refreshed", audit_closure_policy["pending_closure_ids"])
        self.assertIn("findings_sanitized", audit_closure_policy["pending_closure_ids"])
        self.assertEqual(audit_closure_policy["closure_item_count"], len(audit_closure_policy["closure_items"]))
        self.assertFalse(audit_closure_policy["content_policy"]["records_audio"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_transcripts"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_expected_text"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_local_paths"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_device_names"])
        self.assertFalse(audit_closure_policy["content_policy"]["records_operator_identity"])
        rehearsal_policy = persisted["real_pilot_rehearsal_card"]
        self.assertEqual(rehearsal_policy["artifact"], "real-pilot-rehearsal-card.md")
        self.assertEqual(
            rehearsal_policy["source"],
            "real_pilot_execution_card.operator_gate + beta_readiness.next_evidence_focus",
        )
        self.assertEqual(rehearsal_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(rehearsal_policy["focus_status"], "pending")
        self.assertEqual(rehearsal_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertEqual(rehearsal_policy["rehearsal_status"], "ready_for_local_rehearsal")
        self.assertTrue(rehearsal_policy["tracks_rehearsal_before_real_run"])
        self.assertTrue(rehearsal_policy["requires_local_operator"])
        self.assertTrue(rehearsal_policy["requires_real_hardware"])
        self.assertFalse(rehearsal_policy["requires_non_sensitive_audio"])
        self.assertFalse(rehearsal_policy["can_execute_real_command_from_card"])
        self.assertFalse(rehearsal_policy["real_command_copy_allowed_after_rehearsal"])
        self.assertTrue(rehearsal_policy["copy_requires_consent_card"])
        self.assertTrue(rehearsal_policy["copy_requires_audit_closure"])
        self.assertIn(
            "python tools/pilot_run.py --output-dir pilot_runs/safe --json",
            rehearsal_policy["safe_rehearsal_commands"],
        )
        self.assertIn(
            "python tools/beta_readiness.py --requirements",
            rehearsal_policy["safe_rehearsal_commands"],
        )
        self.assertIn("real-pilot-execution-card.md", rehearsal_policy["support_artifacts"])
        self.assertIn("real-pilot-consent-card.md", rehearsal_policy["support_artifacts"])
        self.assertIn("real-pilot-audit-closure.md", rehearsal_policy["support_artifacts"])
        self.assertIn("safe_pilot_refreshed", rehearsal_policy["pending_rehearsal_ids"])
        self.assertIn("beta_requirements_reviewed", rehearsal_policy["pending_rehearsal_ids"])
        self.assertIn(
            "no_real_command_executed_during_rehearsal",
            rehearsal_policy["pending_rehearsal_ids"],
        )
        self.assertEqual(rehearsal_policy["rehearsal_item_count"], len(rehearsal_policy["rehearsal_items"]))
        self.assertIn("--fail-on-audit-gaps", rehearsal_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", rehearsal_policy["refresh_checklist_command"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_audio"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_transcripts"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_expected_text"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_local_paths"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_device_names"])
        self.assertFalse(rehearsal_policy["content_policy"]["records_operator_identity"])
        evidence_package_policy = persisted["real_pilot_evidence_package_card"]
        self.assertEqual(evidence_package_policy["artifact"], "real-pilot-evidence-package.md")
        self.assertEqual(
            evidence_package_policy["source"],
            "operator_gate.evidence_contract + real_pilot_audit_closure_card",
        )
        self.assertEqual(evidence_package_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(evidence_package_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertEqual(evidence_package_policy["package_status"], "waiting_for_real_evidence")
        self.assertTrue(evidence_package_policy["tracks_sanitized_evidence_package"])
        self.assertTrue(evidence_package_policy["package_requires_strict_audit"])
        self.assertTrue(evidence_package_policy["package_requires_beta_refresh"])
        self.assertFalse(evidence_package_policy["can_close_beta_from_package_card"])
        self.assertIn("manual-pilot-report.json", evidence_package_policy["expected_artifacts"])
        self.assertIn("real-pilot-findings-template.md", evidence_package_policy["expected_artifacts"])
        self.assertIn("BETA_CHECKLIST.md", evidence_package_policy["expected_artifacts"])
        self.assertIn("real-pilot-rehearsal-card.md", evidence_package_policy["support_artifacts"])
        self.assertIn("real-pilot-audit-closure.md", evidence_package_policy["support_artifacts"])
        self.assertIn("pilot_runs/manual/windows", evidence_package_policy["suggested_roots"])
        self.assertIn("project", evidence_package_policy["required_json_fields"])
        self.assertIn("manual_capture_command_card.safe_to_share", evidence_package_policy["required_json_fields"])
        self.assertIn("project", evidence_package_policy["missing_json_fields"])
        self.assertEqual(
            evidence_package_policy["package_item_count"],
            len(evidence_package_policy["package_items"]),
        )
        self.assertIn("sanitized_json_present", evidence_package_policy["pending_package_ids"])
        self.assertIn("strict_audit_saved", evidence_package_policy["pending_package_ids"])
        self.assertIn("no_private_values_copied", evidence_package_policy["pending_package_ids"])
        self.assertIn("--fail-on-audit-gaps", evidence_package_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", evidence_package_policy["refresh_checklist_command"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_audio"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_transcripts"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_expected_text"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_local_paths"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_device_names"])
        self.assertFalse(evidence_package_policy["content_policy"]["records_operator_identity"])
        operator_brief_policy = persisted["real_pilot_operator_brief_card"]
        self.assertEqual(operator_brief_policy["artifact"], "real-pilot-operator-brief.md")
        self.assertEqual(
            operator_brief_policy["source"],
            "real_pilot_execution_card + real_pilot_consent_card + real_pilot_evidence_package_card",
        )
        self.assertEqual(operator_brief_policy["brief_status"], "ready_for_local_operator_review")
        self.assertEqual(operator_brief_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(operator_brief_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertTrue(operator_brief_policy["local_run_allowed"])
        self.assertTrue(operator_brief_policy["command_safe_to_copy_for_local_operator"])
        self.assertEqual(operator_brief_policy["copy_safety_status"], "ready_for_local_review")
        self.assertTrue(operator_brief_policy["requires_consent_card"])
        self.assertTrue(operator_brief_policy["requires_rehearsal_card"])
        self.assertTrue(operator_brief_policy["requires_evidence_package"])
        self.assertIn("--sample-rate 48000", operator_brief_policy["local_command_template"])
        self.assertIn("real-pilot-hard-stop-card.md", operator_brief_policy["before_run_artifacts"])
        self.assertIn("real-pilot-final-go-no-go.md", operator_brief_policy["before_run_artifacts"])
        self.assertIn("real-pilot-evidence-package.md", operator_brief_policy["after_run_artifacts"])
        self.assertIn("input_review_confirmed", operator_brief_policy["human_confirmations"])
        self.assertIn("local_placeholders_reviewed", operator_brief_policy["copy_pending_ids"])
        self.assertIn("hard_stop_reviewed", operator_brief_policy["pending_brief_ids"])
        self.assertIn("evidence_package_prepared", operator_brief_policy["pending_brief_ids"])
        self.assertEqual(
            operator_brief_policy["brief_item_count"],
            len(operator_brief_policy["brief_items"]),
        )
        self.assertIn("--fail-on-audit-gaps", operator_brief_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", operator_brief_policy["refresh_checklist_command"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_audio"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_transcripts"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_expected_text"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_local_paths"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_device_names"])
        self.assertFalse(operator_brief_policy["content_policy"]["records_operator_identity"])
        run_sheet_policy = persisted["real_pilot_run_sheet_card"]
        self.assertEqual(run_sheet_policy["artifact"], "real-pilot-run-sheet.md")
        self.assertEqual(
            run_sheet_policy["source"],
            "real_pilot_operator_brief_card + real_pilot_execution_card + real_pilot_audit_closure_card",
        )
        self.assertEqual(run_sheet_policy["sheet_status"], "ready_for_local_operator_review")
        self.assertEqual(run_sheet_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(run_sheet_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertTrue(run_sheet_policy["local_run_allowed"])
        self.assertTrue(run_sheet_policy["command_safe_to_copy_for_local_operator"])
        self.assertIn("--sample-rate 48000", run_sheet_policy["local_command_template"])
        self.assertIn("real-pilot-operator-brief.md", run_sheet_policy["prerequisite_artifacts"])
        self.assertIn("input_review_confirmed", run_sheet_policy["human_confirmations"])
        self.assertIn("local_placeholders_reviewed", run_sheet_policy["copy_pending_ids"])
        self.assertIn("pilot_runs/manual/windows", run_sheet_policy["suggested_roots"])
        self.assertIn("manual_capture_command_card.safe_to_share", run_sheet_policy["required_json_fields"])
        self.assertIn("project", run_sheet_policy["missing_json_fields"])
        self.assertIn("--fail-on-audit-gaps", run_sheet_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", run_sheet_policy["refresh_checklist_command"])
        self.assertEqual(run_sheet_policy["phase_count"], len(run_sheet_policy["phases"]))
        self.assertEqual(run_sheet_policy["required_phase_count"], len(run_sheet_policy["pending_phase_ids"]))
        self.assertIn("pre_run_review", run_sheet_policy["pending_phase_ids"])
        self.assertIn("real_execution", run_sheet_policy["pending_phase_ids"])
        phase_ids = [phase["id"] for phase in run_sheet_policy["phases"]]
        self.assertEqual(
            phase_ids,
            [
                "pre_run_review",
                "local_rehearsal",
                "consent_and_copy_review",
                "final_go_no_go_review",
                "real_execution",
                "local_receipt",
                "sanitized_evidence_package",
                "strict_audit_and_refresh",
            ],
        )
        self.assertTrue(run_sheet_policy["requires_final_go_no_go"])
        self.assertEqual(run_sheet_policy["final_go_no_go_artifact"], "real-pilot-final-go-no-go.md")
        self.assertFalse(run_sheet_policy["content_policy"]["records_audio"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_transcripts"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_expected_text"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_local_paths"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_device_names"])
        self.assertFalse(run_sheet_policy["content_policy"]["records_operator_identity"])
        final_go_no_go_policy = persisted["real_pilot_final_go_no_go_card"]
        self.assertEqual(final_go_no_go_policy["artifact"], "real-pilot-final-go-no-go.md")
        self.assertEqual(
            final_go_no_go_policy["source"],
            "real_pilot_run_sheet_card + operator_gate.command_audit + real_pilot_consent_card",
        )
        self.assertEqual(final_go_no_go_policy["go_no_go_status"], "ready_for_local_operator_review")
        self.assertEqual(final_go_no_go_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(final_go_no_go_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertTrue(final_go_no_go_policy["local_run_allowed"])
        self.assertTrue(final_go_no_go_policy["command_safe_to_copy_for_local_operator"])
        self.assertEqual(final_go_no_go_policy["copy_safety_status"], "ready_for_local_review")
        self.assertTrue(final_go_no_go_policy["requires_final_operator_decision"])
        self.assertFalse(final_go_no_go_policy["can_execute_without_final_decision"])
        self.assertIn("go_after_local_checks", final_go_no_go_policy["decision_options"])
        self.assertIn("no_go_stop_and_fix", final_go_no_go_policy["decision_options"])
        self.assertIn("--sample-rate 48000", final_go_no_go_policy["local_command_template"])
        self.assertIn("real-pilot-run-sheet.md", final_go_no_go_policy["support_artifacts"])
        self.assertIn("real-pilot-hard-stop-card.md", final_go_no_go_policy["support_artifacts"])
        self.assertIn("input_review_confirmed", final_go_no_go_policy["human_confirmations"])
        self.assertIn("local_placeholders_reviewed", final_go_no_go_policy["copy_pending_ids"])
        self.assertIn("--expected-system", final_go_no_go_policy["required_flags"])
        self.assertEqual(final_go_no_go_policy["missing_required_flags"], [])
        self.assertIn("all_run_sheet_phases_reviewed_locally", final_go_no_go_policy["go_conditions"])
        self.assertIn("any_hard_stop_condition_applies", final_go_no_go_policy["no_go_conditions"])
        self.assertIn("hard_stop_conditions_checked", final_go_no_go_policy["pending_review_ids"])
        self.assertEqual(
            final_go_no_go_policy["review_item_count"],
            len(final_go_no_go_policy["review_items"]),
        )
        self.assertIn("--fail-on-audit-gaps", final_go_no_go_policy["strict_audit_command"])
        self.assertIn("BETA_CHECKLIST.md", final_go_no_go_policy["refresh_checklist_command"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_audio"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_transcripts"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_expected_text"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_local_paths"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_device_names"])
        self.assertFalse(final_go_no_go_policy["content_policy"]["records_operator_identity"])
        self.assertEqual(final_go_no_go_policy["local_receipt_artifact"], "real-pilot-local-receipt.md")
        local_receipt_policy = persisted["real_pilot_local_receipt_card"]
        self.assertEqual(local_receipt_policy["artifact"], "real-pilot-local-receipt.md")
        self.assertEqual(
            local_receipt_policy["source"],
            "real_pilot_final_go_no_go_card + real_pilot_evidence_package_card + real_pilot_audit_closure_card",
        )
        self.assertEqual(local_receipt_policy["receipt_status"], "waiting_for_local_receipt")
        self.assertEqual(local_receipt_policy["focus"], "windows_wasapi_capture")
        self.assertEqual(local_receipt_policy["focus_artifact"], "manual-pilot-report.json")
        self.assertTrue(local_receipt_policy["local_run_allowed"])
        self.assertTrue(local_receipt_policy["requires_final_go_no_go"])
        self.assertEqual(local_receipt_policy["final_go_no_go_artifact"], "real-pilot-final-go-no-go.md")
        self.assertEqual(local_receipt_policy["run_sheet_artifact"], "real-pilot-run-sheet.md")
        self.assertEqual(local_receipt_policy["evidence_package_artifact"], "real-pilot-evidence-package.md")
        self.assertEqual(local_receipt_policy["audit_closure_artifact"], "real-pilot-audit-closure.md")
        self.assertEqual(local_receipt_policy["receipt_placeholders"]["final_decision"], "<go_after_local_checks|no_go_stop_and_fix>")
        self.assertEqual(local_receipt_policy["receipt_placeholders"]["run_outcome"], "<completed|stopped|blocked>")
        self.assertEqual(local_receipt_policy["receipt_placeholders"]["sanitized_json_artifact"], "manual-pilot-report.json")
        self.assertIn("final_decision_recorded", local_receipt_policy["pending_receipt_ids"])
        self.assertIn("strict_audit_result_recorded", local_receipt_policy["pending_receipt_ids"])
        self.assertIn("real-pilot-final-go-no-go.md", local_receipt_policy["support_artifacts"])
        self.assertIn("real-pilot-findings-template.md", local_receipt_policy["support_artifacts"])
        self.assertEqual(
            local_receipt_policy["receipt_item_count"],
            len(local_receipt_policy["receipt_items"]),
        )
        self.assertFalse(local_receipt_policy["content_policy"]["records_audio"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_transcripts"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_spoken_text"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_expected_text"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_local_paths"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_device_names"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_operator_identity"])
        self.assertFalse(local_receipt_policy["content_policy"]["records_signature"])
        self.assertEqual(
            persisted["real_pilot_next_evidence_focus"]["preparation_sequence"],
            persisted["next_evidence_focus_preparation_sequence"],
        )
        preparation_names = [step["name"] for step in persisted["next_evidence_focus_preparation_sequence"]]
        self.assertEqual(
            preparation_names,
            ["windows_wasapi_capture"],
        )
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_platform_commands"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_required_fields"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_strict_audit_command"])
        self.assertTrue(persisted["real_pilot_command_pack"]["includes_system_output_no_pip_extra_contract"])
        self.assertIn(
            "system_output_command_card.python_extra=null",
            persisted["real_pilot_command_pack"]["system_output_no_pip_extra_contract"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
            persisted["real_pilot_command_pack"]["system_output_no_pip_extra_contract"],
        )
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
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_audio"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_next_evidence_focus"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_hard_stop_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_evidence_intake_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_execution_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_consent_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_audit_closure_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_rehearsal_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_evidence_package_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_operator_brief_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_run_sheet_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_final_go_no_go_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_audio"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_transcripts"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_spoken_text"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_expected_text"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_local_paths"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_device_names"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_operator_identity"])
        self.assertFalse(persisted["real_pilot_local_receipt_card"]["records_signature"])
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
        self.assertIn("real-pilot-next-evidence-focus.md", plan)
        self.assertIn("real-pilot-hard-stop-card.md", plan)
        self.assertIn("real-pilot-evidence-intake-card.md", plan)
        self.assertIn("real-pilot-execution-card.md", plan)
        self.assertIn("real-pilot-consent-card.md", plan)
        self.assertIn("real-pilot-audit-closure.md", plan)
        self.assertIn("real-pilot-rehearsal-card.md", plan)
        self.assertIn("real-pilot-evidence-package.md", plan)
        self.assertIn("real-pilot-operator-brief.md", plan)
        self.assertIn("real-pilot-final-go-no-go.md", plan)
        self.assertIn("real-pilot-local-receipt.md", plan)
        self.assertIn("Cierre de auditoria", plan)
        self.assertIn("Ensayo local previo", plan)
        self.assertIn("Paquete de evidencia sanitizada", plan)
        self.assertIn("Brief del operador local", plan)
        self.assertIn("real-pilot-run-sheet.md", plan)
        self.assertIn("Run sheet del piloto real", plan)
        self.assertIn("Go/no-go final del operador", plan)
        self.assertIn("Recibo local del piloto real", plan)
        self.assertIn("Manifiesto de evidencias", plan)
        self.assertIn("Compuerta go/no-go", plan)
        self.assertIn("Tarjeta de alto operativo", plan)
        self.assertIn("Ingesta de evidencia real", plan)
        self.assertIn("Ejecucion guiada del piloto real", plan)
        self.assertIn("Consentimiento local", plan)
        self.assertIn("Cierre de auditoria", plan)
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
        self.assertIn("real-pilot-next-evidence-focus.md", handoff)
        self.assertIn("real-pilot-hard-stop-card.md", handoff)
        self.assertIn("real-pilot-evidence-intake-card.md", handoff)
        self.assertIn("real-pilot-execution-card.md", handoff)
        self.assertIn("real-pilot-consent-card.md", handoff)
        self.assertIn("real-pilot-audit-closure.md", handoff)
        self.assertIn("real-pilot-rehearsal-card.md", handoff)
        self.assertIn("real-pilot-evidence-package.md", handoff)
        self.assertIn("real-pilot-operator-brief.md", handoff)
        self.assertIn("real-pilot-run-sheet.md", handoff)
        self.assertIn("real-pilot-final-go-no-go.md", handoff)
        self.assertIn("real-pilot-local-receipt.md", handoff)
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
        self.assertIn("Siguiente foco de evidencia AuralisVoiceKit", next_focus)
        self.assertIn("Foco", next_focus)
        self.assertIn("Secuencia de preparacion", next_focus)
        self.assertIn("windows_wasapi_capture", next_focus)
        self.assertIn("Blocker: `windows_wasapi_capture`", next_focus)
        self.assertIn("--sample-rate 48000", next_focus)
        self.assertIn("--require-capture-backend-ready", next_focus)
        self.assertIn("manual_capture_command_card.safe_to_share", next_focus)
        self.assertIn("real-pilot-command-pack.md", next_focus)
        self.assertIn("real-pilot-evidence-manifest.md", next_focus)
        self.assertIn("real-pilot-decision-gate.md", next_focus)
        self.assertIn("real-pilot-hard-stop-card.md", next_focus)
        self.assertIn("real-pilot-evidence-intake-card.md", next_focus)
        self.assertIn("real-pilot-execution-card.md", next_focus)
        self.assertIn("real-pilot-rehearsal-card.md", next_focus)
        self.assertIn("Registra audio: `false`", next_focus)
        self.assertIn("Usable como evidencia beta: `false`", next_focus)
        self.assertNotIn(str(tmpdir), next_focus)
        self.assertIn("Paquete de comandos para pilotos reales AuralisVoiceKit", command_pack)
        self.assertIn("Comandos por plataforma", command_pack)
        self.assertIn("Contrato de salida system sin extra pip", command_pack)
        self.assertIn("target_output_backend.readiness_plan.python_extra=null", command_pack)
        self.assertIn("target_output_backend.readiness_plan.pip_command=null", command_pack)
        self.assertIn("system_output_command_card.python_extra=null", command_pack)
        self.assertIn("system_output_command_card.pip_command=null", command_pack)
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
            command_pack,
        )
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
        self.assertIn("Escaneo de privacidad", evidence_manifest)
        self.assertIn("Plan de remediacion de privacidad", evidence_manifest)
        self.assertIn("real-pilot-evidence-intake-card.md", evidence_manifest)
        self.assertIn("real-pilot-execution-card.md", evidence_manifest)
        self.assertIn("Candidato mas cercano", evidence_manifest)
        self.assertIn("transcription-pilot-report.json", evidence_manifest)
        self.assertIn("output-pilot-report.json", evidence_manifest)
        self.assertIn("manual-pilot-report.json", evidence_manifest)
        self.assertIn("--fail-on-audit-gaps", evidence_manifest)
        self.assertIn("target_backend_ready_required", evidence_manifest)
        self.assertIn("output_backend_ready_required", evidence_manifest)
        self.assertNotIn(str(tmpdir), evidence_manifest)
        self.assertIn("Compuerta go/no-go para pilotos reales AuralisVoiceKit", decision_gate)
        self.assertIn("Escaneo de privacidad", decision_gate)
        self.assertIn("Plan de remediacion de privacidad", decision_gate)
        self.assertIn("real-pilot-hard-stop-card.md", decision_gate)
        self.assertIn("real-pilot-evidence-intake-card.md", decision_gate)
        self.assertIn("real-pilot-execution-card.md", decision_gate)
        self.assertIn("real-pilot-consent-card.md", decision_gate)
        self.assertIn("real-pilot-audit-closure.md", decision_gate)
        self.assertIn("real-pilot-rehearsal-card.md", decision_gate)
        self.assertIn("Pilotos reales: `go`", decision_gate)
        self.assertIn("Beta: `blocked`", decision_gate)
        self.assertIn("Estable: `blocked`", decision_gate)
        self.assertIn("Siguiente paso recomendado", decision_gate)
        self.assertIn("windows_wasapi_capture", decision_gate)
        self.assertIn("--sample-rate 48000", decision_gate)
        self.assertIn("--require-capture-backend-ready", decision_gate)
        self.assertIn("Condiciones de alto", decision_gate)
        self.assertIn("Alto operativo para pilotos reales AuralisVoiceKit", hard_stop)
        self.assertIn("Condiciones de alto", hard_stop)
        self.assertIn("Acciones minimas antes de ejecutar", hard_stop)
        self.assertIn("Alcance permitido", hard_stop)
        self.assertIn("Registra audio: `false`", hard_stop)
        self.assertIn("Usable como evidencia beta: `false`", hard_stop)
        self.assertIn("no cuenta como evidencia beta", hard_stop)
        self.assertIn("Do not run real audio", hard_stop)
        self.assertIn("real-pilot-decision-gate.md", hard_stop)
        self.assertIn("real-pilot-next-evidence-focus.md", hard_stop)
        self.assertIn("real-pilot-evidence-intake-card.md", hard_stop)
        self.assertIn("real-pilot-execution-card.md", hard_stop)
        self.assertIn("real-pilot-consent-card.md", hard_stop)
        self.assertIn("real-pilot-audit-closure.md", hard_stop)
        self.assertIn("real-pilot-rehearsal-card.md", hard_stop)
        self.assertNotIn(str(tmpdir), hard_stop)
        self.assertIn("Ingesta de evidencia para pilotos reales AuralisVoiceKit", evidence_intake)
        self.assertIn("Directorios sugeridos", evidence_intake)
        self.assertIn("Artifacts que puede ingerir la auditoria", evidence_intake)
        self.assertIn("Auditoria estricta", evidence_intake)
        self.assertIn("Refrescar checklist", evidence_intake)
        self.assertIn("pilot_runs/manual/windows", evidence_intake)
        self.assertIn("manual-pilot-report.json", evidence_intake)
        self.assertIn("output-pilot-report.json", evidence_intake)
        self.assertIn("transcription-pilot-report.json", evidence_intake)
        self.assertIn("--fail-on-audit-gaps", evidence_intake)
        self.assertIn("Registra audio: `false`", evidence_intake)
        self.assertIn("Usable como evidencia beta: `false`", evidence_intake)
        self.assertIn("real-pilot-execution-card.md", evidence_intake)
        self.assertIn("real-pilot-consent-card.md", evidence_intake)
        self.assertIn("real-pilot-audit-closure.md", evidence_intake)
        self.assertIn("real-pilot-rehearsal-card.md", evidence_intake)
        self.assertNotIn(str(tmpdir), evidence_intake)
        self.assertIn("Tarjeta de ejecucion de piloto real AuralisVoiceKit", execution_card)
        self.assertIn("Compuerta del operador", execution_card)
        self.assertIn("Decision: `ready_for_local_operator`", execution_card)
        self.assertIn("Permitido ejecutar localmente: `true`", execution_card)
        self.assertIn("Razones de bloqueo: `ninguno`", execution_card)
        self.assertIn("Guard backend estricto requerido: `true`", execution_card)
        self.assertIn("Artifact JSON esperado: `manual-pilot-report.json`", execution_card)
        self.assertIn("Revisiones previas", execution_card)
        self.assertIn("Confirmaciones humanas requeridas", execution_card)
        self.assertIn("expected_system_review", execution_card)
        self.assertIn("input_review_confirmed", execution_card)
        self.assertIn("strict_backend_guard_enabled", execution_card)
        self.assertIn("Auditoria del comando local", execution_card)
        self.assertIn("Estado: `passed`", execution_card)
        self.assertIn("Seguro para copiar por operador local: `true`", execution_card)
        self.assertIn("Flags faltantes: `ninguno`", execution_card)
        self.assertIn("Seguridad de copia del comando", execution_card)
        self.assertIn("Plantilla segura: `true`", execution_card)
        self.assertIn("Requiere revision local: `true`", execution_card)
        self.assertIn("Requiere tarjeta de consentimiento: `true`", execution_card)
        self.assertIn("Items pendientes locales", execution_card)
        self.assertIn("local_placeholders_reviewed", execution_card)
        self.assertIn("human_confirmations_reviewed", execution_card)
        self.assertIn("strict_backend_guard_reviewed", execution_card)
        self.assertIn("Contrato de evidencia beta", execution_card)
        self.assertIn("Blocker: `windows_wasapi_capture`", execution_card)
        self.assertIn("Campos requeridos actuales", execution_card)
        self.assertIn("manual_capture_command_card.safe_to_share", execution_card)
        self.assertIn("Orden local", execution_card)
        self.assertIn("Comando del foco", execution_card)
        self.assertIn("Despues de ejecutar", execution_card)
        self.assertIn("Condiciones de alto", execution_card)
        self.assertIn("windows_wasapi_capture", execution_card)
        self.assertIn("--sample-rate 48000", execution_card)
        self.assertIn("--require-capture-backend-ready", execution_card)
        self.assertIn("--fail-on-audit-gaps", execution_card)
        self.assertIn("pilot_runs/manual/windows", execution_card)
        self.assertIn("Registra audio: `false`", execution_card)
        self.assertIn("Usable como evidencia beta: `false`", execution_card)
        self.assertIn("No ejecuta hardware", execution_card)
        self.assertIn("real-pilot-consent-card.md", execution_card)
        self.assertIn("real-pilot-audit-closure.md", execution_card)
        self.assertIn("real-pilot-rehearsal-card.md", execution_card)
        self.assertNotIn(str(tmpdir), execution_card)
        self.assertIn("Consentimiento local para piloto real AuralisVoiceKit", consent_card)
        self.assertIn("Decision consentimiento: `requires_local_operator_consent`", consent_card)
        self.assertIn("Requiere operador local: `true`", consent_card)
        self.assertIn("Faltantes de consentimiento", consent_card)
        self.assertIn("Checklist de consentimiento local", consent_card)
        self.assertIn("hard_stop_reviewed", consent_card)
        self.assertIn("public_non_sensitive_scope", consent_card)
        self.assertIn("confirm_flags_after_review", consent_card)
        self.assertIn("strict_backend_guard_kept", consent_card)
        self.assertIn("audit_closure_accepted", consent_card)
        self.assertIn("Registra identidad del operador: `false`", consent_card)
        self.assertIn("Registra firma: `false`", consent_card)
        self.assertIn("Usable como evidencia beta: `false`", consent_card)
        self.assertIn("manual-pilot-report.json", consent_card)
        self.assertIn("--sample-rate 48000", consent_card)
        self.assertIn("--fail-on-audit-gaps", consent_card)
        self.assertIn("real-pilot-audit-closure.md", consent_card)
        self.assertIn("real-pilot-rehearsal-card.md", consent_card)
        self.assertNotIn(str(tmpdir), consent_card)
        self.assertIn("Cierre de auditoria para piloto real AuralisVoiceKit", audit_closure)
        self.assertIn("Estado de cierre: `waiting_for_real_evidence`", audit_closure)
        self.assertIn("Artifact JSON esperado: `manual-pilot-report.json`", audit_closure)
        self.assertIn("Auditoria requerida: `true`", audit_closure)
        self.assertIn("Puede cerrar sin auditoria: `false`", audit_closure)
        self.assertIn("Puede refrescar beta sin auditoria: `false`", audit_closure)
        self.assertIn("Usable como evidencia beta: `false`", audit_closure)
        self.assertIn("real-pilot-findings-template.md", audit_closure)
        self.assertIn("real-pilot-evidence-intake-card.md", audit_closure)
        self.assertIn("real-pilot-execution-card.md", audit_closure)
        self.assertIn("real-pilot-consent-card.md", audit_closure)
        self.assertIn("real-pilot-rehearsal-card.md", audit_closure)
        self.assertIn("real-pilot-evidence-package.md", audit_closure)
        self.assertIn("real-pilot-final-go-no-go.md", audit_closure)
        self.assertIn("real-pilot-local-receipt.md", audit_closure)
        self.assertIn("pilot_runs/manual/windows", audit_closure)
        self.assertIn("strict_audit_passed", audit_closure)
        self.assertIn("beta_checklist_refreshed", audit_closure)
        self.assertIn("findings_sanitized", audit_closure)
        self.assertIn("--fail-on-audit-gaps", audit_closure)
        self.assertIn("BETA_CHECKLIST.md", audit_closure)
        self.assertIn("Registra audio: `false`", audit_closure)
        self.assertIn("Registra rutas locales: `false`", audit_closure)
        self.assertIn("Registra identidad del operador: `false`", audit_closure)
        self.assertNotIn(str(tmpdir), audit_closure)
        self.assertIn("Ensayo local antes del piloto real AuralisVoiceKit", rehearsal_card)
        self.assertIn("Estado de ensayo: `ready_for_local_rehearsal`", rehearsal_card)
        self.assertIn("Puede ejecutar comando real desde esta tarjeta: `false`", rehearsal_card)
        self.assertIn("Usable como evidencia beta: `false`", rehearsal_card)
        self.assertIn("python tools/pilot_run.py --output-dir pilot_runs/safe --json", rehearsal_card)
        self.assertIn("python tools/beta_readiness.py --requirements", rehearsal_card)
        self.assertIn("no_real_command_executed_during_rehearsal", rehearsal_card)
        self.assertIn("real-pilot-execution-card.md", rehearsal_card)
        self.assertIn("real-pilot-consent-card.md", rehearsal_card)
        self.assertIn("real-pilot-audit-closure.md", rehearsal_card)
        self.assertIn("real-pilot-evidence-package.md", rehearsal_card)
        self.assertIn("real-pilot-operator-brief.md", rehearsal_card)
        self.assertIn("real-pilot-run-sheet.md", rehearsal_card)
        self.assertIn("manual-pilot-report.json", rehearsal_card)
        self.assertIn("--sample-rate 48000", rehearsal_card)
        self.assertIn("--fail-on-audit-gaps", rehearsal_card)
        self.assertIn("Registra audio: `false`", rehearsal_card)
        self.assertIn("Registra rutas locales: `false`", rehearsal_card)
        self.assertIn("Registra identidad del operador: `false`", rehearsal_card)
        self.assertNotIn(str(tmpdir), rehearsal_card)
        self.assertIn("Paquete de evidencia sanitizada para piloto real AuralisVoiceKit", evidence_package)
        self.assertIn("Estado del paquete: `waiting_for_real_evidence`", evidence_package)
        self.assertIn("Artifact JSON esperado: `manual-pilot-report.json`", evidence_package)
        self.assertIn("Requiere auditoria estricta: `true`", evidence_package)
        self.assertIn("Puede cerrar beta desde esta tarjeta: `false`", evidence_package)
        self.assertIn("Usable como evidencia beta: `false`", evidence_package)
        self.assertIn("manual-pilot-report.json", evidence_package)
        self.assertIn("real-pilot-findings-template.md", evidence_package)
        self.assertIn("BETA_CHECKLIST.md", evidence_package)
        self.assertIn("real-pilot-rehearsal-card.md", evidence_package)
        self.assertIn("real-pilot-audit-closure.md", evidence_package)
        self.assertIn("real-pilot-run-sheet.md", evidence_package)
        self.assertIn("real-pilot-final-go-no-go.md", evidence_package)
        self.assertIn("real-pilot-local-receipt.md", evidence_package)
        self.assertIn("pilot_runs/manual/windows", evidence_package)
        self.assertIn("manual_capture_command_card.safe_to_share", evidence_package)
        self.assertIn("sanitized_json_present", evidence_package)
        self.assertIn("strict_audit_saved", evidence_package)
        self.assertIn("no_private_values_copied", evidence_package)
        self.assertIn("--fail-on-audit-gaps", evidence_package)
        self.assertIn("Registra audio: `false`", evidence_package)
        self.assertIn("Registra rutas locales: `false`", evidence_package)
        self.assertIn("Registra identidad del operador: `false`", evidence_package)
        self.assertNotIn(str(tmpdir), evidence_package)
        self.assertIn("Brief del operador local para piloto real AuralisVoiceKit", operator_brief)
        self.assertIn("Estado del brief: `ready_for_local_operator_review`", operator_brief)
        self.assertIn("Permitido ejecutar localmente: `true`", operator_brief)
        self.assertIn("Comando seguro para copia local: `true`", operator_brief)
        self.assertIn("real-pilot-hard-stop-card.md", operator_brief)
        self.assertIn("real-pilot-evidence-package.md", operator_brief)
        self.assertIn("real-pilot-run-sheet.md", operator_brief)
        self.assertIn("real-pilot-final-go-no-go.md", operator_brief)
        self.assertIn("real-pilot-local-receipt.md", operator_brief)
        self.assertIn("manual-pilot-report.json", operator_brief)
        self.assertIn("--sample-rate 48000", operator_brief)
        self.assertIn("input_review_confirmed", operator_brief)
        self.assertIn("local_placeholders_reviewed", operator_brief)
        self.assertIn("hard_stop_reviewed", operator_brief)
        self.assertIn("evidence_package_prepared", operator_brief)
        self.assertIn("--fail-on-audit-gaps", operator_brief)
        self.assertIn("Registra audio: `false`", operator_brief)
        self.assertIn("Registra rutas locales: `false`", operator_brief)
        self.assertIn("Registra identidad del operador: `false`", operator_brief)
        self.assertNotIn(str(tmpdir), operator_brief)
        self.assertIn("Run sheet del piloto real AuralisVoiceKit", run_sheet)
        self.assertIn("Estado de la hoja: `ready_for_local_operator_review`", run_sheet)
        self.assertIn("Permitido ejecutar localmente: `true`", run_sheet)
        self.assertIn("Comando seguro para copia local: `true`", run_sheet)
        self.assertIn("pre_run_review", run_sheet)
        self.assertIn("local_rehearsal", run_sheet)
        self.assertIn("consent_and_copy_review", run_sheet)
        self.assertIn("real_execution", run_sheet)
        self.assertIn("sanitized_evidence_package", run_sheet)
        self.assertIn("strict_audit_and_refresh", run_sheet)
        self.assertIn("real-pilot-operator-brief.md", run_sheet)
        self.assertIn("manual-pilot-report.json", run_sheet)
        self.assertIn("--sample-rate 48000", run_sheet)
        self.assertIn("input_review_confirmed", run_sheet)
        self.assertIn("local_placeholders_reviewed", run_sheet)
        self.assertIn("manual_capture_command_card.safe_to_share", run_sheet)
        self.assertIn("pilot_runs/manual/windows", run_sheet)
        self.assertIn("--fail-on-audit-gaps", run_sheet)
        self.assertIn("BETA_CHECKLIST.md", run_sheet)
        self.assertIn("final_go_no_go_review", run_sheet)
        self.assertIn("real-pilot-final-go-no-go.md", run_sheet)
        self.assertIn("local_receipt", run_sheet)
        self.assertIn("real-pilot-local-receipt.md", run_sheet)
        self.assertIn("final_decision_recorded", run_sheet)
        self.assertIn("Registra audio: `false`", run_sheet)
        self.assertIn("Registra rutas locales: `false`", run_sheet)
        self.assertIn("Registra identidad del operador: `false`", run_sheet)
        self.assertNotIn(str(tmpdir), run_sheet)
        self.assertIn("Go/no-go final del piloto real AuralisVoiceKit", final_go_no_go)
        self.assertIn("Estado go/no-go: `ready_for_local_operator_review`", final_go_no_go)
        self.assertIn("Requiere decision final del operador: `true`", final_go_no_go)
        self.assertIn("Puede ejecutar sin decision final: `false`", final_go_no_go)
        self.assertIn("go_after_local_checks", final_go_no_go)
        self.assertIn("no_go_stop_and_fix", final_go_no_go)
        self.assertIn("all_run_sheet_phases_reviewed_locally", final_go_no_go)
        self.assertIn("any_hard_stop_condition_applies", final_go_no_go)
        self.assertIn("hard_stop_conditions_checked", final_go_no_go)
        self.assertIn("manual-pilot-report.json", final_go_no_go)
        self.assertIn("--sample-rate 48000", final_go_no_go)
        self.assertIn("--expected-system", final_go_no_go)
        self.assertIn("input_review_confirmed", final_go_no_go)
        self.assertIn("local_placeholders_reviewed", final_go_no_go)
        self.assertIn("--fail-on-audit-gaps", final_go_no_go)
        self.assertIn("BETA_CHECKLIST.md", final_go_no_go)
        self.assertIn("real-pilot-local-receipt.md", final_go_no_go)
        self.assertIn("Registra audio: `false`", final_go_no_go)
        self.assertIn("Registra rutas locales: `false`", final_go_no_go)
        self.assertIn("Registra identidad del operador: `false`", final_go_no_go)
        self.assertNotIn(str(tmpdir), final_go_no_go)
        self.assertIn("Recibo local del piloto real AuralisVoiceKit", local_receipt)
        self.assertIn("Estado del recibo: `waiting_for_local_receipt`", local_receipt)
        self.assertIn("Artifact esperado: `manual-pilot-report.json`", local_receipt)
        self.assertIn("real-pilot-final-go-no-go.md", local_receipt)
        self.assertIn("real-pilot-run-sheet.md", local_receipt)
        self.assertIn("real-pilot-evidence-package.md", local_receipt)
        self.assertIn("real-pilot-audit-closure.md", local_receipt)
        self.assertIn("real-pilot-findings-template.md", local_receipt)
        self.assertIn("<go_after_local_checks|no_go_stop_and_fix>", local_receipt)
        self.assertIn("<completed|stopped|blocked>", local_receipt)
        self.assertIn("final_decision_recorded", local_receipt)
        self.assertIn("real_run_outcome_recorded", local_receipt)
        self.assertIn("strict_audit_result_recorded", local_receipt)
        self.assertIn("--fail-on-audit-gaps", local_receipt)
        self.assertIn("BETA_CHECKLIST.md", local_receipt)
        self.assertIn("Registra audio: `false`", local_receipt)
        self.assertIn("Registra rutas locales: `false`", local_receipt)
        self.assertIn("Registra identidad del operador: `false`", local_receipt)
        self.assertIn("Registra firma: `false`", local_receipt)
        self.assertNotIn(str(tmpdir), local_receipt)
        self.assertIn("real-pilot-environment-checklist.md", decision_gate)
        self.assertIn("real-pilot-fixture-preflight.md", decision_gate)
        self.assertIn("real-pilot-transcription-readiness.md", decision_gate)
        self.assertIn("real-pilot-system-output-readiness.md", decision_gate)
        self.assertIn("real-pilot-evidence-manifest.md", decision_gate)
        self.assertNotIn(str(tmpdir), decision_gate)
        self.assertIn("Secuencia recomendada", plan)
        self.assertIn("Matriz por plataforma", plan)
        self.assertIn("Resumen por blocker", plan)
        self.assertIn("Escaneo de privacidad", plan)
        self.assertIn("Plan de remediacion de privacidad", plan)
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
        self.assertIn("real-transcription-command.md", plan)
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
        self.assertIn("Campos de politica backend", plan)
        self.assertIn("target_capture_backend.freedom_policy.category", plan)
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
        self.assertIn(
            "target_backend.freedom_policy.category",
            manifest_rows["real_transcription_quality"]["policy_required_fields"],
        )
        self.assertIn(
            "target_backend.freedom_policy.proprietary",
            manifest_rows["real_transcription_quality"]["policy_required_fields"],
        )
        self.assertIn(
            "target_backend.freedom_policy.network_required",
            manifest_rows["real_transcription_quality"]["policy_required_fields"],
        )
        self.assertIn("audio.generated_synthetic_audio", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.decoded", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.duration_gate.enabled", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("audio.duration_gate.passed", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn("transcript.text_redacted", manifest_rows["real_transcription_quality"]["required_fields"])
        self.assertIn(
            "transcription_checklist.redacts_transcript_text",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.safe_to_share",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.uses_placeholders",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.uses_pip_extra",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.python_extra",
            manifest_rows["real_transcription_quality"]["required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.pip_command",
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
        self.assertEqual(
            manifest_rows["system_output_audible"]["policy_required_fields"],
            [
                "target_output_backend.freedom_policy.category",
                "target_output_backend.freedom_policy.proprietary",
                "target_output_backend.freedom_policy.network_required",
            ],
        )
        self.assertIn(
            "operator_checklist.redacts_spoken_text",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertIn(
            "next_system_output.records_spoken_text",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.safe_to_share",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertIn(
            "target_output_backend.readiness_plan.uses_pip_extra",
            manifest_rows["system_output_audible"]["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.safe_to_share",
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
        self.assertEqual(report["pilot_decision_gate"]["next_recommended_step"]["name"], "windows_wasapi_capture")
        self.assertTrue(report["pilot_decision_gate"]["next_recommended_step"]["requires_hardware"])
        self.assertEqual(
            report["pilot_decision_gate"]["next_recommended_step"]["strict_backend_guard_flag"],
            "--require-capture-backend-ready",
        )
        operator_contract = report["real_pilot_execution_card"]["operator_gate"]["evidence_contract"]
        self.assertEqual(operator_contract["blocker"], "windows_wasapi_capture")
        self.assertEqual(operator_contract["policy_required_field_count"], 3)
        self.assertEqual(
            operator_contract["policy_required_fields"],
            [
                "target_capture_backend.freedom_policy.category",
                "target_capture_backend.freedom_policy.proprietary",
                "target_capture_backend.freedom_policy.network_required",
            ],
        )
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
        self.assertIn("real-transcription-command.md", report["transcription_readiness_card"]["expected_artifacts"])
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
            "real_transcription_command_card.safe_to_share",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.uses_placeholders",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.uses_pip_extra",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.python_extra",
            report["transcription_readiness_card"]["real_required_fields"],
        )
        self.assertIn(
            "real_transcription_command_card.pip_command",
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
        self.assertIn(
            "system_output_command_card.python_extra",
            report["system_output_readiness_card"]["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.pip_command",
            report["system_output_readiness_card"]["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio",
            report["system_output_readiness_card"]["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.python_extra=null",
            report["system_output_readiness_card"]["no_pip_extra_contract"],
        )
        self.assertIn("target_output_backend.available", report["system_output_readiness_card"]["audible_required_fields"])
        self.assertIn(
            "operator_checklist.redacts_spoken_text",
            report["system_output_readiness_card"]["audible_required_fields"],
        )
        self.assertIn(
            "next_system_output.records_spoken_text",
            report["system_output_readiness_card"]["audible_required_fields"],
        )
        self.assertIn(
            "system_output_command_card.records_spoken_text",
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
        self.assertEqual(sequence_names[0], "windows_wasapi_capture")
        self.assertEqual(sequence_names[1], "transcription-audio-fixture")
        self.assertEqual(sequence_names[2], "transcription-audio-preflight")
        self.assertEqual(sequence_names[3], "real_transcription_quality")
        self.assertIn("system-output-operator-checklist", sequence_names)
        self.assertIn("audit-evidence", sequence_names)
        self.assertIn("refresh-beta-checklist", sequence_names)
        sequence_by_name = {step["name"]: step for step in report["recommended_pilot_sequence"]}
        windows_step = sequence_by_name["windows_wasapi_capture"]
        fixture_step = sequence_by_name["transcription-audio-fixture"]
        preflight_step = sequence_by_name["transcription-audio-preflight"]
        self.assertTrue(windows_step["requires_hardware"])
        self.assertEqual(windows_step["strict_backend_guard_flag"], "--require-capture-backend-ready")
        self.assertIn("manual_capture_command_card.safe_to_share", windows_step["required_fields"])
        self.assertEqual(
            windows_step["policy_required_fields"],
            [
                "target_capture_backend.freedom_policy.category",
                "target_capture_backend.freedom_policy.proprietary",
                "target_capture_backend.freedom_policy.network_required",
            ],
        )
        self.assertFalse(fixture_step["requires_hardware"])
        self.assertFalse(fixture_step["requires_non_sensitive_audio"])
        self.assertIn("preflight.passed", fixture_step["required_fields"])
        self.assertTrue(preflight_step["requires_non_sensitive_audio"])
        self.assertIn(
            "artifacts.transcription_review_checklist",
            preflight_step["required_fields"],
        )
        self.assertIn(
            "artifacts.real_transcription_next_step",
            preflight_step["required_fields"],
        )
        self.assertIn(
            "audio.audio_file_name_redacted",
            preflight_step["required_fields"],
        )
        self.assertIn(
            "target_backend.available",
            preflight_step["required_fields"],
        )
        checklist_step = sequence_by_name["system-output-operator-checklist"]
        transcription_step = sequence_by_name["real_transcription_quality"]
        output_step = sequence_by_name["system_output_audible"]
        self.assertTrue(transcription_step["strict_backend_guard_required"])
        self.assertEqual(transcription_step["strict_backend_guard_flag"], "--require-target-backend-ready")
        self.assertEqual(transcription_step["strict_backend_guard_field"], "target_backend_ready_required")
        self.assertIn("--confirm-quality-reviewed", transcription_step["command"])
        self.assertIn("--confirm-audio-reviewed", transcription_step["command"])
        self.assertIn("--confirm-reference-reviewed", transcription_step["command"])
        self.assertIn("--require-target-backend-ready", transcription_step["command"])
        self.assertIn("target_backend.available", transcription_step["required_fields"])
        self.assertIn("target_backend.freedom_policy.category", transcription_step["policy_required_fields"])
        self.assertIn("target_backend.freedom_policy.proprietary", transcription_step["policy_required_fields"])
        self.assertIn("target_backend.freedom_policy.network_required", transcription_step["policy_required_fields"])
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
        self.assertIn("real_transcription_command_card.safe_to_share", transcription_step["required_fields"])
        self.assertIn("real_transcription_command_card.uses_placeholders", transcription_step["required_fields"])
        self.assertIn("real_transcription_command_card.uses_pip_extra", transcription_step["required_fields"])
        self.assertIn("real_transcription_command_card.python_extra", transcription_step["required_fields"])
        self.assertIn("real_transcription_command_card.pip_command", transcription_step["required_fields"])
        self.assertIn("real_transcription_operator_gate.ready_for_beta_audit", transcription_step["required_fields"])
        self.assertIn("real_transcription_operator_gate.command_safe_to_copy", transcription_step["required_fields"])
        self.assertIn("real_transcription_operator_gate.missing_confirmation_count", transcription_step["required_fields"])
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
        self.assertEqual(
            output_step["policy_required_fields"],
            [
                "target_output_backend.freedom_policy.category",
                "target_output_backend.freedom_policy.proprietary",
                "target_output_backend.freedom_policy.network_required",
            ],
        )
        self.assertIn("target_output_backend.readiness_plan.uses_pip_extra", output_step["required_fields"])
        self.assertIn("target_output_backend.readiness_plan.python_extra", output_step["required_fields"])
        self.assertIn("target_output_backend.readiness_plan.pip_command", output_step["required_fields"])
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
        self.assertIn("system_output_command_card.safe_to_share", output_step["required_fields"])
        self.assertIn("system_output_command_card.uses_placeholders", output_step["required_fields"])
        self.assertIn("system_output_command_card.uses_pip_extra", output_step["required_fields"])
        self.assertIn("system_output_command_card.python_extra", output_step["required_fields"])
        self.assertIn("system_output_command_card.pip_command", output_step["required_fields"])
        self.assertIn(
            "system_output_command_card.system_dependency_plan.safe_to_share",
            output_step["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio",
            output_step["required_fields"],
        )
        self.assertIn(
            "system_output_command_card.system_dependency_plan.records_local_paths",
            output_step["required_fields"],
        )
        self.assertIn("system_output_command_card.records_spoken_text", output_step["required_fields"])
        self.assertIn("system_output_command_card.records_operator_identity", output_step["required_fields"])
        self.assertFalse(checklist_step["requires_hardware"])
        self.assertFalse(checklist_step["requires_operator"])
        self.assertFalse(checklist_step["strict_backend_guard_required"])
        self.assertIn("operator_checklist.ready_for_beta_evidence", checklist_step["required_fields"])
        self.assertIn("target_output_backend.readiness_plan.python_extra", checklist_step["required_fields"])
        self.assertIn("target_output_backend.readiness_plan.pip_command", checklist_step["required_fields"])
        self.assertIn("system_output_command_card.python_extra", checklist_step["required_fields"])
        self.assertIn("system_output_command_card.pip_command", checklist_step["required_fields"])
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio",
            checklist_step["required_fields"],
        )
        self.assertIn("artifacts.system_output_next_step", checklist_step["required_fields"])
        matrix = {row["name"]: row for row in report["platform_pilot_matrix"]}
        self.assertIn("--require-capture-backend-ready", matrix["windows-wasapi-capture"]["command"])
        self.assertIn("--confirm-input-reviewed", matrix["ubuntu-linux-capture"]["command"])
        self.assertIn("--confirm-input-reviewed", matrix["macos-capture"]["command"])
        self.assertEqual(matrix["windows-wasapi-capture"]["status"], "pending")
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
        self.assertIn(
            "target_output_backend.readiness_plan.uses_pip_extra=false",
            matrix["system-output-audible"]["notes"],
        )
        self.assertIn(
            "target_output_backend.readiness_plan.python_extra=null",
            matrix["system-output-audible"]["notes"],
        )
        self.assertIn(
            "target_output_backend.readiness_plan.pip_command=null",
            matrix["system-output-audible"]["notes"],
        )
        self.assertIn("operator_checklist.redacts_spoken_text=true", matrix["system-output-audible"]["notes"])
        self.assertIn("next_system_output.records_spoken_text=false", matrix["system-output-audible"]["notes"])
        self.assertIn("system_output_command_card.uses_pip_extra=false", matrix["system-output-audible"]["notes"])
        self.assertIn("system_output_command_card.python_extra=null", matrix["system-output-audible"]["notes"])
        self.assertIn("system_output_command_card.pip_command=null", matrix["system-output-audible"]["notes"])
        self.assertIn(
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
            matrix["system-output-audible"]["notes"],
        )
        self.assertIn("system_output_command_card.records_spoken_text=false", matrix["system-output-audible"]["notes"])
        self.assertIn("--fail-on-audit-gaps", report["beta_readiness"]["strict_audit_command"])
        self.assertIn("Campos condicionales", evidence_manifest)
        self.assertIn("Campos de politica backend", evidence_manifest)
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
        self.assertIn("real_pilot_next_evidence_focus", payload)
        self.assertIn("real_pilot_hard_stop_card", payload)
        self.assertIn("real_pilot_evidence_intake_card", payload)
        self.assertIn("real_pilot_execution_card", payload)
        self.assertIn("real_pilot_consent_card", payload)
        self.assertIn("real_pilot_audit_closure_card", payload)
        self.assertIn("real_pilot_rehearsal_card", payload)
        self.assertIn("real_pilot_evidence_package_card", payload)
        self.assertIn("real_pilot_operator_brief_card", payload)
        self.assertIn("real_pilot_run_sheet_card", payload)
        self.assertIn("real_pilot_final_go_no_go_card", payload)
        self.assertIn("real_pilot_local_receipt_card", payload)
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
        self.assertIn("real_pilot_next_evidence_focus", payload["artifacts"])
        self.assertIn("real_pilot_hard_stop_card", payload["artifacts"])
        self.assertIn("real_pilot_evidence_intake_card", payload["artifacts"])
        self.assertIn("real_pilot_execution_card", payload["artifacts"])
        self.assertIn("real_pilot_consent_card", payload["artifacts"])
        self.assertIn("real_pilot_audit_closure_card", payload["artifacts"])
        self.assertIn("real_pilot_rehearsal_card", payload["artifacts"])
        self.assertIn("real_pilot_evidence_package_card", payload["artifacts"])
        self.assertIn("real_pilot_operator_brief_card", payload["artifacts"])
        self.assertIn("real_pilot_run_sheet_card", payload["artifacts"])
        self.assertIn("real_pilot_final_go_no_go_card", payload["artifacts"])
        self.assertIn("real_pilot_local_receipt_card", payload["artifacts"])
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
                        "freedom_policy": _free_local_policy(),
                    },
                    "capture_backend_ready_required": True,
                    "system_guard": {"expected_system_matched": True},
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": {
                        "input_review_confirmed": True,
                        "ready_for_beta_evidence": True,
                    },
                    "manual_capture_command_card": _manual_capture_command_card(
                        "ubuntu_linux_capture",
                        "Linux | Ubuntu/Linux | Ubuntu",
                        "pyaudio",
                    ),
                    "capture_operator_gate": _capture_operator_gate(
                        "ubuntu_linux_capture",
                        "pyaudio",
                    ),
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
        self.assertEqual(focus["name"], "windows_wasapi_capture")
        self.assertEqual(
            focus["policy_required_fields"],
            [
                "target_capture_backend.freedom_policy.category",
                "target_capture_backend.freedom_policy.proprietary",
                "target_capture_backend.freedom_policy.network_required",
            ],
        )
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
        self.assertIn("Blocker: `windows_wasapi_capture`", plan)
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
            manifest_rows["ubuntu_linux_capture"]["policy_required_fields"],
            [
                "target_capture_backend.freedom_policy.category",
                "target_capture_backend.freedom_policy.proprietary",
                "target_capture_backend.freedom_policy.network_required",
            ],
        )
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

    def test_safe_pilot_surfaces_privacy_audit_findings_without_values(self):
        module = _load_pilot_run()
        private_value = "texto privado no publicable"

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
                        "freedom_policy": _free_local_policy(),
                    },
                    "capture_backend_ready_required": True,
                    "system_guard": {"expected_system_matched": True},
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": {
                        "input_review_confirmed": True,
                        "ready_for_beta_evidence": True,
                    },
                    "manual_capture_command_card": _manual_capture_command_card(
                        "ubuntu_linux_capture",
                        "Linux | Ubuntu/Linux | Ubuntu",
                        "pyaudio",
                    ),
                    "passed": True,
                    "transcript": {"text": private_value},
                },
            )
            report = module.run_safe_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                evidence_paths=[evidence_root],
            )
            plan = Path(report["artifacts"]["pilot_plan"]).read_text(encoding="utf-8")
            evidence_manifest = Path(report["artifacts"]["real_pilot_evidence_manifest"]).read_text(encoding="utf-8")
            decision_gate = Path(report["artifacts"]["real_pilot_decision_gate"]).read_text(encoding="utf-8")

        privacy_audit = report["beta_readiness"]["privacy_audit"]
        self.assertEqual(privacy_audit["status"], "failed")
        self.assertEqual(privacy_audit["finding_count"], 1)
        self.assertTrue(privacy_audit["blocking"])
        self.assertEqual(privacy_audit["findings"][0]["field"], "transcript.text")
        self.assertEqual(privacy_audit["findings"][0]["reason"], "raw_text_field")
        self.assertEqual(privacy_audit["findings"][0]["safe_replacement"], "<text-redacted>")
        self.assertIn("Eliminar el texto crudo", privacy_audit["findings"][0]["action_es"])
        self.assertEqual(report["evidence_manifest"]["privacy_audit"], privacy_audit)
        self.assertEqual(report["pilot_decision_gate"]["privacy_audit"], privacy_audit)
        remediation_plan = report["beta_readiness"]["privacy_remediation_plan"]
        self.assertEqual(remediation_plan["status"], "required")
        self.assertEqual(remediation_plan["step_count"], 1)
        self.assertEqual(remediation_plan["steps"][0]["field"], "transcript.text")
        self.assertFalse(remediation_plan["records_private_values"])
        self.assertEqual(report["evidence_manifest"]["privacy_remediation_plan"], remediation_plan)
        self.assertEqual(report["pilot_decision_gate"]["privacy_remediation_plan"], remediation_plan)
        self.assertEqual(report["pilot_decision_gate"]["beta"]["decision"], "blocked")
        self.assertIn("privacy audit", report["pilot_decision_gate"]["beta"]["reason"])
        self.assertIn("Escaneo de privacidad", plan)
        self.assertIn("Escaneo de privacidad", evidence_manifest)
        self.assertIn("Escaneo de privacidad", decision_gate)
        combined = "\n".join([plan, evidence_manifest, decision_gate, json.dumps(report, sort_keys=True)])
        self.assertIn("transcript.text", combined)
        self.assertIn("raw_text_field", combined)
        self.assertIn("Eliminar el texto crudo", combined)
        self.assertIn("<text-redacted>", combined)
        self.assertIn("Plan de remediacion de privacidad", combined)
        self.assertNotIn(private_value, combined)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manual_capture_command_card(blocker: str, evidence_system: str, backend: str) -> dict:
    base_command = (
        f"python tools/manual_pilot.py --backend {backend} --device default "
        "--expected-system Linux --require-capture-backend-ready --json"
    )
    python_extra = _capture_python_extra(backend)
    return {
        "artifact": "manual-capture-command.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "blocker": blocker,
        "evidence_system": evidence_system,
        "ready_for_beta_evidence": True,
        "missing_count": 0,
        "missing_fields": [],
        "setup_commands": [],
        "uses_pip_extra": python_extra is not None,
        "python_extra": python_extra,
        "pip_command": f"python -m pip install .[{backend}]",
        "preflight_command_template": f"{base_command} --output-dir <pilot-output-dir>",
        "preflight_uses_microphone": False,
        "real_capture_command_template": (
            f"{base_command} --capture-test --confirm-input-reviewed --output-dir <pilot-output-dir>"
        ),
        "real_capture_requires_microphone": True,
        "audit_command_template": (
            "python tools/beta_readiness.py --audit-evidence --evidence <pilot-output-dir> --json"
        ),
        "records_audio": False,
        "records_audio_bytes": False,
        "records_device_name": False,
        "records_local_paths": False,
        "next_action": "Audit this report with tools/beta_readiness.py --audit-evidence before closing beta.",
    }


def _capture_operator_gate(blocker: str, backend: str) -> dict:
    command_card = _manual_capture_command_card(
        blocker,
        "Linux | Ubuntu/Linux | Ubuntu",
        backend,
    )
    return {
        "safe_to_share": True,
        "decision": "ready_for_beta_audit",
        "blocker": blocker,
        "expected_artifact": "manual-pilot-report.json",
        "ready_for_beta_audit": True,
        "command_safe_to_copy": True,
        "local_operator_required": True,
        "confirmations": [
            {
                "id": "real_capture_explicitly_requested",
                "required": True,
                "confirmed": True,
                "source": "capture_test_requested",
                "instruction": "--capture-test was used for this evidence report.",
            }
        ],
        "missing_confirmations": [],
        "missing_confirmation_count": 0,
        "missing_fields": [],
        "missing_field_count": 0,
        "real_capture_command_template": command_card["real_capture_command_template"],
        "audit_command_template": command_card["audit_command_template"],
        "next_action": "Run the strict beta evidence audit before closing this blocker.",
        "records_audio": False,
        "records_audio_bytes": False,
        "records_device_name": False,
        "records_local_paths": False,
        "records_operator_identity": False,
    }


def _capture_python_extra(backend: str) -> str | None:
    if backend in {"sounddevice", "wasapi"}:
        return "sounddevice"
    if backend == "pyaudio":
        return "pyaudio"
    return None


def _free_local_policy() -> dict:
    return {
        "category": "free-local",
        "free_default": True,
        "network_required": False,
        "proprietary": False,
    }


if __name__ == "__main__":
    unittest.main()
