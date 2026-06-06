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
PILOTS = ROOT / "PILOTS.md"
PILOT_FINDINGS = ROOT / "PILOT_FINDINGS.md"
BETA_CHECKLIST = ROOT / "BETA_CHECKLIST.md"
PILOT_RUN = ROOT / "tools" / "pilot_run.py"
MANUAL_PILOT = ROOT / "tools" / "manual_pilot.py"
OUTPUT_PILOT = ROOT / "tools" / "output_pilot.py"
TRANSCRIPTION_PILOT = ROOT / "tools" / "transcription_pilot.py"
BETA_READINESS = ROOT / "tools" / "beta_readiness.py"


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

    def test_pilot_runbook_and_runner_are_linked_from_public_docs(self):
        self.assertTrue(PILOTS.exists())
        self.assertTrue(PILOT_FINDINGS.exists())
        self.assertTrue(BETA_CHECKLIST.exists())
        self.assertTrue(PILOT_RUN.exists())
        self.assertTrue(MANUAL_PILOT.exists())
        self.assertTrue(OUTPUT_PILOT.exists())
        self.assertTrue(TRANSCRIPTION_PILOT.exists())
        self.assertTrue(BETA_READINESS.exists())
        self.assertIn("PILOTS.md", README.read_text(encoding="utf-8"))
        self.assertIn("PILOT_FINDINGS.md", README.read_text(encoding="utf-8"))
        self.assertIn("BETA_CHECKLIST.md", README.read_text(encoding="utf-8"))
        self.assertIn("PILOTS.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("PILOT_FINDINGS.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("BETA_CHECKLIST.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("PILOTS.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("BETA_CHECKLIST.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools\\pilot_run.py", README.read_text(encoding="utf-8"))
        self.assertIn("tools\\manual_pilot.py", README.read_text(encoding="utf-8"))
        self.assertIn("tools\\output_pilot.py", README.read_text(encoding="utf-8"))
        self.assertIn("tools\\pilot_audio_fixture.py", README.read_text(encoding="utf-8"))
        self.assertIn("tools\\transcription_pilot.py", README.read_text(encoding="utf-8"))
        self.assertIn("tools\\beta_readiness.py", README.read_text(encoding="utf-8"))
        self.assertIn("--evidence", README.read_text(encoding="utf-8"))
        self.assertIn("pilot-plan.md", README.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-findings-template.md", README.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-handoff.md", README.read_text(encoding="utf-8"))
        self.assertIn("recommended_pilot_sequence", README.read_text(encoding="utf-8"))
        self.assertIn("platform_pilot_matrix", README.read_text(encoding="utf-8"))
        self.assertIn("--run-preflight", README.read_text(encoding="utf-8"))
        self.assertIn("--preflight-only", README.read_text(encoding="utf-8"))
        self.assertIn("--max-audio-seconds", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-audio-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-reference-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-quality-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn("transcription-review-checklist.md", README.read_text(encoding="utf-8"))
        self.assertIn("real-transcription-next-step.md", README.read_text(encoding="utf-8"))
        self.assertIn("audio.audio_file_name_redacted", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_audio_file_name", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_expected_text_file_name", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.audio_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("reference_privacy_scan.passed", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.quality_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.ready_for_beta_evidence", README.read_text(encoding="utf-8"))
        self.assertIn("output-operator-checklist.md", README.read_text(encoding="utf-8"))
        self.assertIn("system-output-next-step.md", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-text-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn("text_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("spoken_text_privacy_scan.passed", README.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.text_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-voice-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn('"Windows|Linux|Darwin"', README.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.expected_system_matched", README.read_text(encoding="utf-8"))
        self.assertIn("--confirm-input-reviewed", README.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.voice_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.ready_for_beta_evidence", README.read_text(encoding="utf-8"))
        self.assertIn("manual-capture-checklist.md", README.read_text(encoding="utf-8"))
        self.assertIn("input_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.input_review_confirmed", README.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.ready_for_beta_evidence", README.read_text(encoding="utf-8"))
        self.assertIn("--expected-system", README.read_text(encoding="utf-8"))
        self.assertIn("system_guard.expected_system_matched", README.read_text(encoding="utf-8"))
        self.assertIn("tools/pilot_run.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/manual_pilot.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/output_pilot.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/pilot_audio_fixture.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/transcription_pilot.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/beta_readiness.py", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--evidence", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("pilot-plan.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-findings-template.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-handoff.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("recommended_pilot_sequence", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("platform_pilot_matrix", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--run-preflight", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--preflight-only", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--max-audio-seconds", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-audio-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-reference-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-quality-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription-review-checklist.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-transcription-next-step.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("audio.audio_file_name_redacted", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_audio_file_name", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_expected_text_file_name", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.audio_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("reference_privacy_scan.passed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.quality_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.ready_for_beta_evidence", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("output-operator-checklist.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("system-output-next-step.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-text-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("text_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("spoken_text_privacy_scan.passed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.text_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-voice-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn('"Windows|Linux|Darwin"', MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.expected_system_matched", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-input-reviewed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.voice_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.ready_for_beta_evidence", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("manual-capture-checklist.md", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("input_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.input_review_confirmed", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.ready_for_beta_evidence", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("--expected-system", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("system_guard.expected_system_matched", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/pilot_run.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/manual_pilot.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/output_pilot.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/pilot_audio_fixture.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/transcription_pilot.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("tools/beta_readiness.py", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--evidence", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("pilot-plan.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-findings-template.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-pilot-handoff.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("recommended_pilot_sequence", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("platform_pilot_matrix", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--run-preflight", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--preflight-only", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--max-audio-seconds", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-audio-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-reference-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-quality-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription-review-checklist.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("real-transcription-next-step.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("audio.audio_file_name_redacted", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_audio_file_name", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.records_expected_text_file_name", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.audio_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("reference_privacy_scan.passed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.quality_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("transcription_checklist.ready_for_beta_evidence", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("output-operator-checklist.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("system-output-next-step.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-text-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("text_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("spoken_text_privacy_scan.passed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.text_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-voice-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn('"Windows|Linux|Darwin"', API_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.expected_system_matched", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--confirm-input-reviewed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.voice_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("operator_checklist.ready_for_beta_evidence", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("manual-capture-checklist.md", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("input_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.input_review_confirmed", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("capture_checklist.ready_for_beta_evidence", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("--expected-system", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("system_guard.expected_system_matched", API_DOC.read_text(encoding="utf-8"))

    def test_doctor_bundle_is_documented(self):
        self.assertIn("--bundle", README.read_text(encoding="utf-8"))
        self.assertIn("--bundle", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("write_doctor_bundle", API_DOC.read_text(encoding="utf-8"))
        self.assertIn("doctor-bundles", README.read_text(encoding="utf-8"))
        self.assertIn("doctor-bundles", MAIN_DOC.read_text(encoding="utf-8"))
        self.assertIn("analyze_doctor_bundles", API_DOC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
