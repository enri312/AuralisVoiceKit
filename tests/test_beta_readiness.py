import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BETA_READINESS = ROOT / "tools" / "beta_readiness.py"


def _load_beta_readiness():
    spec = importlib.util.spec_from_file_location("beta_readiness", BETA_READINESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaReadinessTests(unittest.TestCase):
    def test_report_keeps_beta_blocked_until_real_pilots_exist(self):
        module = _load_beta_readiness()

        report = module.build_beta_readiness_report(ROOT)
        checks = {check["name"]: check for check in report["checks"]}

        self.assertEqual(report["status"], "pilot")
        self.assertFalse(report["ready_for_beta"])
        self.assertTrue(checks["stability_gate_pilot"]["ok"])
        self.assertFalse(checks["windows_wasapi_capture"]["ok"])
        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertFalse(checks["macos_capture"]["ok"])
        self.assertIn("windows_wasapi_capture", report["blockers"])
        self.assertIn("real_transcription_quality", report["blockers"])
        self.assertIn("windows-wasapi-sample-rate", {issue["id"] for issue in report["known_issues"]})

    def test_cli_json_does_not_fail_by_default(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--json"])
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["ready_for_beta"])
        self.assertIn("system_output_audible", payload["blockers"])

    def test_cli_can_fail_on_beta_blockers(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--root", str(ROOT), "--json", "--fail-on-blockers"])

        self.assertEqual(exit_code, 1)

    def test_writes_markdown_checklist(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "BETA_CHECKLIST.md"
            exit_code = module.main(["--root", str(ROOT), "--output", str(output_path)])
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Checklist de beta", content)
        self.assertIn("Bloqueadores para beta", content)
        self.assertIn("real_transcription_quality", content)

    def test_evidence_json_can_close_beta_blockers(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                _transcription_evidence(word_accuracy=0.92),
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_root])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertTrue(report["ready_for_beta"])
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["evidence"]["count"], 5)
        self.assertTrue(checks["windows_wasapi_capture"]["ok"])
        self.assertTrue(checks["real_transcription_quality"]["ok"])
        self.assertTrue(checks["system_output_audible"]["ok"])
        self.assertTrue(checks["ubuntu_linux_capture"]["ok"])
        self.assertTrue(checks["macos_capture"]["ok"])
        self.assertIn("transcription/transcription-pilot-report.json", checks["real_transcription_quality"]["evidence_sources"])

    def test_evidence_sources_are_relative_to_the_evidence_directory(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            evidence_root = tmpdir_path / "pilot-batch"
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_root])
            audit = module.build_evidence_audit_report(ROOT, evidence_paths=[evidence_root])

        checks = {check["name"]: check for check in report["checks"]}

        self.assertIn("linux/manual-pilot-report.json", report["evidence"]["files"])
        self.assertIn("macos/manual-pilot-report.json", report["evidence"]["files"])
        self.assertIn(
            "linux/manual-pilot-report.json",
            checks["ubuntu_linux_capture"]["evidence_sources"],
        )
        self.assertIn(
            "macos/manual-pilot-report.json",
            checks["macos_capture"]["evidence_sources"],
        )
        self.assertIn("linux/manual-pilot-report.json", {item["file"] for item in audit["accepted_details"]})
        self.assertNotIn(str(tmpdir_path), json.dumps(report))
        self.assertNotIn(str(tmpdir_path), json.dumps(audit))

    def test_evidence_requires_meaningful_transcription_threshold(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            _write_json(
                evidence_path,
                _transcription_evidence(min_word_accuracy=0.1, word_accuracy=1.0),
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_target_backend_available(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["target_backend"]["available"] = False
            evidence["target_backend"]["reason"] = "missing optional backend"
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_target_backend_ready_guard(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["target_backend_ready_required"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_preflight_readiness_ready(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["preflight_readiness"]["status"] = "blocked"
            evidence["preflight_readiness"]["decision"] = "blocked"
            evidence["preflight_readiness"]["ready_for_model_run"] = False
            evidence["preflight_readiness"]["must_rerun_preflight"] = True
            evidence["preflight_readiness"]["blocking_reasons"] = ["duration_gate_enabled"]
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            audit = module.build_evidence_audit_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])
        transcription = audit["artifacts"][0]["candidates"][0]
        missing_fields = [field["path"] for field in transcription["fields"] if not field["ok"]]
        self.assertIn("preflight_readiness.status", missing_fields)
        self.assertIn("preflight_readiness.decision", missing_fields)
        self.assertIn("preflight_readiness.ready_for_model_run", missing_fields)
        self.assertIn("preflight_readiness.must_rerun_preflight", missing_fields)

    def test_openai_real_transcription_evidence_requires_sanitized_credential_check(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence(backend="openai")
            evidence.pop("credentials")
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_openai_real_transcription_evidence_accepts_sanitized_credential_presence(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            _write_json(evidence_path, _transcription_evidence(backend="openai"))

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertTrue(checks["real_transcription_quality"]["ok"])
        self.assertTrue(
            any(
                source.endswith("transcription-pilot-report.json")
                for source in checks["real_transcription_quality"]["evidence_sources"]
            )
        )

    def test_real_transcription_evidence_requires_duration_gate(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["audio"]["duration_gate"] = {
                "enabled": False,
                "passed": None,
                "min_seconds": None,
                "max_seconds": None,
            }
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_user_audio(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["audio"]["generated_synthetic_audio"] = True
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_audio_decode(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["audio"]["decoded"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_transcript_redaction(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["transcript"]["text_redacted"] = False
            evidence["transcription_checklist"]["redacts_transcript_text"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_review_checklist(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "audio_review_confirmed": True,
                    "reference_review_confirmed": True,
                    "quality_review_confirmed": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.75},
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_quality_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "audio_review_confirmed": True,
                    "quality_review_confirmed": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.75},
                    "transcription_checklist": {
                        "audio_review_confirmed": True,
                        "reference_review_confirmed": True,
                        "quality_review_confirmed": False,
                        "ready_for_beta_evidence": False,
                    },
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_audio_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["audio_review_confirmed"] = False
            evidence["transcription_checklist"]["audio_review_confirmed"] = False
            evidence["transcription_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_reference_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["reference_review_confirmed"] = False
            evidence["transcription_checklist"]["reference_review_confirmed"] = False
            evidence["transcription_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_reference_privacy_scan(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["reference_privacy_scan"]["passed"] = False
            evidence["reference_privacy_scan"]["risk_count"] = 1
            evidence["reference_privacy_scan"]["risk_types"] = ["email"]
            evidence["transcription_checklist"]["reference_privacy_scan_passed"] = False
            evidence["transcription_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_file_name_redaction(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence = _transcription_evidence()
            evidence["audio"]["audio_file_name_redacted"] = False
            evidence["transcription_checklist"]["records_audio_file_name"] = True
            evidence["transcription_checklist"]["records_expected_text_file_name"] = True
            evidence["transcription_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_safe_command_card(self):
        module = _load_beta_readiness()

        unsafe_cases = [
            ("safe_to_share", False),
            ("uses_placeholders", False),
            ("preflight_runs_model", True),
            ("real_transcription_requires_user_audio", False),
            ("real_transcription_requires_quality_review", False),
            ("records_audio", True),
            ("records_audio_path", True),
            ("records_audio_file_name", True),
            ("records_transcript_text", True),
            ("records_expected_text", True),
            ("records_expected_text_file_name", True),
            ("records_local_paths", True),
        ]
        for field, value in unsafe_cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmpdir:
                    evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
                    payload = _transcription_evidence()
                    payload["real_transcription_command_card"][field] = value
                    _write_json(evidence_path, payload)

                    report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
                    checks = {check["name"]: check for check in report["checks"]}

                self.assertFalse(checks["real_transcription_quality"]["ok"])
                self.assertIn("real_transcription_quality", report["blockers"])

    def test_real_transcription_evidence_requires_command_card_placeholders(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            payload = _transcription_evidence()
            payload["real_transcription_command_card"]["real_transcription_command_template"] = (
                "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 --json"
            )
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertIn("real_transcription_quality", report["blockers"])

    def test_system_output_evidence_requires_operator_checklist(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "passed": True,
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_output_backend_ready_guard(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["output_backend_ready_required"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_voice_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["voice_review_confirmed"] = False
            payload["operator_checklist"]["voice_review_confirmed"] = False
            payload["operator_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_text_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["text_review_confirmed"] = False
            payload["operator_checklist"]["text_review_confirmed"] = False
            payload["operator_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_spoken_text_privacy_scan(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["spoken_text_privacy_scan"]["passed"] = False
            payload["spoken_text_privacy_scan"]["risk_count"] = 1
            payload["spoken_text_privacy_scan"]["risk_types"] = ["email"]
            payload["operator_checklist"]["spoken_text_privacy_scan_passed"] = False
            payload["operator_checklist"]["ready_for_beta_evidence"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_spoken_text_redaction(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["operator_checklist"]["redacts_spoken_text"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_operator_identity_redaction(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["operator_checklist"]["records_operator_identity"] = True
            payload["next_system_output"]["records_operator_identity"] = True
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_placeholder_next_step(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["next_system_output"]["uses_placeholders"] = False
            payload["next_system_output"]["records_spoken_text"] = True
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_safe_command_card(self):
        module = _load_beta_readiness()

        unsafe_cases = [
            ("safe_to_share", False),
            ("uses_placeholders", False),
            ("preflight_plays_audio", True),
            ("real_output_requires_operator", False),
            ("records_audio", True),
            ("records_spoken_text", True),
            ("records_operator_identity", True),
            ("records_local_paths", True),
        ]
        for field, value in unsafe_cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmpdir:
                    evidence_path = Path(tmpdir) / "output-pilot-report.json"
                    payload = _output_evidence()
                    payload["system_output_command_card"][field] = value
                    _write_json(evidence_path, payload)

                    report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
                    checks = {check["name"]: check for check in report["checks"]}

                self.assertFalse(checks["system_output_audible"]["ok"])
                self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_command_card_placeholders(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["system_output_command_card"]["real_output_command_template"] = (
                "python tools/output_pilot.py --speak --text Hola --json"
            )
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_real_audio_readiness(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["operator_checklist"]["commands_available"] = False
            payload["operator_checklist"]["ready_for_real_audio"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_system_output_evidence_requires_expected_system_guard(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            payload = _output_evidence()
            payload["system_guard"] = {"expected_system_matched": False}
            payload["operator_checklist"]["expected_system_matched"] = False
            _write_json(evidence_path, payload)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertIn("system_output_audible", report["blockers"])

    def test_capture_evidence_requires_capture_checklist(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "hardware_capture_tested": True,
                    "passed": True,
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_capture_evidence_requires_expected_system_guard(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    **_capture_evidence("Linux", "sounddevice"),
                    "system_guard": {},
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_capture_evidence_requires_input_review_confirmation(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    **_capture_evidence("Linux", "pyaudio"),
                    "input_review_confirmed": False,
                    "capture_checklist": {
                        "ready_for_beta_evidence": True,
                        "input_review_confirmed": False,
                    },
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_cross_platform_capture_evidence_requires_supported_backend(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    **_capture_evidence("Linux", "wav"),
                    "target_capture_backend": _capture_backend_status("wav"),
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_cross_platform_capture_evidence_requires_backend_availability(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            evidence = _capture_evidence("Linux", "sounddevice")
            evidence["target_capture_backend"]["available"] = False
            evidence["target_capture_backend"]["reason"] = "missing optional backend"
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_cross_platform_capture_evidence_requires_backend_ready_guard(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "manual-pilot-report.json"
            evidence = _capture_evidence("Darwin", "pyaudio")
            evidence["capture_backend_ready_required"] = False
            _write_json(evidence_path, evidence)

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["macos_capture"]["ok"])
        self.assertIn("macos_capture", report["blockers"])

    def test_capture_evidence_requires_safe_manual_command_card(self):
        module = _load_beta_readiness()

        unsafe_cases = [
            ("safe_to_share", False),
            ("uses_placeholders", False),
            ("preflight_uses_microphone", True),
            ("real_capture_requires_microphone", False),
            ("records_audio", True),
            ("records_audio_bytes", True),
            ("records_device_name", True),
            ("records_local_paths", True),
            ("preflight_command_template", "python tools/manual_pilot.py --json"),
        ]
        for field, value in unsafe_cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmpdir:
                    evidence_path = Path(tmpdir) / "manual-pilot-report.json"
                    evidence = _capture_evidence("Linux", "sounddevice")
                    evidence["manual_capture_command_card"][field] = value
                    _write_json(evidence_path, evidence)

                    report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
                    checks = {check["name"]: check for check in report["checks"]}

                self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
                self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_cli_evidence_allows_strict_beta_pass(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                _transcription_evidence(min_word_accuracy=0.8),
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    ["--root", str(ROOT), "--evidence", str(evidence_root), "--fail-on-blockers", "--json"]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ready_for_beta"])
        self.assertEqual(payload["blockers"], [])

    def test_evidence_without_project_marker_is_ignored(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "output-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "voice_review_confirmed": True,
                    "operator_checklist": {
                        "voice_review_confirmed": True,
                        "ready_for_beta_evidence": True,
                    },
                    "passed": True,
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertEqual(report["evidence"]["count"], 0)
        self.assertEqual(report["evidence"]["ignored_count"], 1)
        self.assertIn("output-pilot-report.json", report["evidence"]["ignored_files"])
        self.assertEqual(report["evidence"]["ignored_details"][0]["reason"], "missing_project")
        self.assertIn("falta", report["evidence"]["ignored_details"][0]["message_es"])
        self.assertIn("missing", report["evidence"]["ignored_details"][0]["message_en"])
        self.assertFalse(checks["system_output_audible"]["ok"])

    def test_markdown_lists_ignored_evidence_reasons_without_local_paths(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            evidence_path = tmpdir_path / "output-pilot-report.json"
            output_path = tmpdir_path / "BETA_CHECKLIST.md"
            _write_json(
                evidence_path,
                {
                    "project": "OtherProject",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "voice_review_confirmed": True,
                    "operator_checklist": {
                        "voice_review_confirmed": True,
                        "ready_for_beta_evidence": True,
                    },
                    "passed": True,
                },
            )

            exit_code = module.main(
                ["--root", str(ROOT), "--evidence", str(evidence_path), "--output", str(output_path)]
            )
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("## Evidencias ignoradas", content)
        self.assertIn("declara otro proyecto", content)
        self.assertIn("declares a different project", content)
        self.assertIn("output-pilot-report.json", content)
        self.assertNotIn(str(tmpdir_path), content)

    def test_markdown_lists_accepted_evidence_without_local_paths(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            evidence_root = tmpdir_path / "batch"
            output_path = tmpdir_path / "BETA_CHECKLIST.md"
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )

            exit_code = module.main(
                ["--root", str(ROOT), "--evidence", str(evidence_root), "--output", str(output_path)]
            )
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("## Evidencias aceptadas", content)
        self.assertIn("linux/manual-pilot-report.json", content)
        self.assertIn("manual-pilot-report.json", content)
        self.assertNotIn(str(tmpdir_path), content)

    def test_non_object_evidence_is_ignored_with_reason(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = Path(tmpdir) / "transcription-pilot-report.json"
            evidence_path.write_text(json.dumps(["not", "a", "dict"]) + "\n", encoding="utf-8")

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])

        self.assertEqual(report["evidence"]["ignored_count"], 1)
        self.assertEqual(report["evidence"]["ignored_details"][0]["reason"], "not_json_object")

    def test_evidence_requirements_cover_beta_blockers(self):
        module = _load_beta_readiness()

        report = module.build_evidence_requirements_report()
        requirements = {item["name"]: item for item in report["requirements"]}

        self.assertEqual(report["project"], "AuralisVoiceKit")
        self.assertEqual(report["minimums"]["transcription_min_word_accuracy"], 0.75)
        self.assertIn("manual-pilot-report.json", report["accepted_artifacts"])
        self.assertIn("output-pilot-report.json", report["accepted_artifacts"])
        self.assertIn("transcription-pilot-report.json", report["accepted_artifacts"])
        for blocker in (
            "windows_wasapi_capture",
            "real_transcription_quality",
            "system_output_audible",
            "ubuntu_linux_capture",
            "macos_capture",
        ):
            self.assertIn(blocker, requirements)
            field_paths = {field["path"] for field in requirements[blocker]["fields"]}
            self.assertIn("project", field_paths)
            self.assertIn("passed", field_paths)
        transcription_fields = {
            field["path"]: field["expected"] for field in requirements["real_transcription_quality"]["fields"]
        }
        transcription_conditional_fields = {
            field["path"]: field["expected"]
            for conditional in requirements["real_transcription_quality"]["conditional_fields"]
            for field in conditional["fields"]
        }
        output_fields = {
            field["path"]: field["expected"] for field in requirements["system_output_audible"]["fields"]
        }
        windows_fields = {
            field["path"]: field["expected"] for field in requirements["windows_wasapi_capture"]["fields"]
        }
        linux_fields = {
            field["path"]: field["expected"] for field in requirements["ubuntu_linux_capture"]["fields"]
        }
        macos_fields = {field["path"]: field["expected"] for field in requirements["macos_capture"]["fields"]}
        self.assertEqual(transcription_fields["audio_confirmed_non_sensitive"], True)
        self.assertEqual(transcription_fields["target_backend.available"], True)
        self.assertEqual(transcription_fields["target_backend_ready_required"], True)
        self.assertEqual(transcription_fields["preflight_readiness.status"], "ready")
        self.assertEqual(transcription_fields["preflight_readiness.decision"], "ready_for_real_transcription")
        self.assertEqual(transcription_fields["preflight_readiness.ready_for_model_run"], True)
        self.assertEqual(transcription_fields["preflight_readiness.must_rerun_preflight"], False)
        self.assertEqual(transcription_fields["preflight_readiness.records_audio_file_name"], False)
        self.assertEqual(transcription_fields["preflight_readiness.records_local_paths"], False)
        self.assertEqual(transcription_fields["preflight_readiness.backend_ready"], True)
        self.assertEqual(transcription_fields["preflight_readiness.duration_gate_passed"], True)
        self.assertEqual(transcription_fields["audio.generated_synthetic_audio"], False)
        self.assertEqual(transcription_fields["audio.audio_confirmed_non_sensitive"], True)
        self.assertEqual(transcription_fields["audio.decoded"], True)
        self.assertEqual(transcription_fields["audio.audio_file_name_redacted"], True)
        self.assertEqual(transcription_fields["audio.duration_gate.enabled"], True)
        self.assertEqual(transcription_fields["audio.duration_gate.passed"], True)
        self.assertEqual(transcription_fields["audio_review_confirmed"], True)
        self.assertEqual(transcription_fields["reference_review_confirmed"], True)
        self.assertEqual(transcription_fields["reference_privacy_scan.passed"], True)
        self.assertEqual(transcription_fields["transcript.text_redacted"], True)
        self.assertEqual(transcription_fields["quality.min_word_accuracy"], ">= 0.75")
        self.assertEqual(transcription_fields["quality_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.audio_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.records_audio_path"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_audio_file_name"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_transcript_text"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_expected_text"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_expected_text_file_name"], False)
        self.assertEqual(transcription_fields["transcription_checklist.redacts_transcript_text"], True)
        self.assertEqual(transcription_fields["transcription_checklist.redacts_expected_text"], True)
        self.assertEqual(transcription_fields["transcription_checklist.reference_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.reference_privacy_scan_passed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.quality_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.ready_for_beta_evidence"], True)
        self.assertEqual(transcription_fields["real_transcription_command_card.artifact"], "real-transcription-command.md")
        self.assertEqual(transcription_fields["real_transcription_command_card.blocker"], "real_transcription_quality")
        self.assertEqual(transcription_fields["real_transcription_command_card.ready_for_beta_evidence"], True)
        self.assertEqual(transcription_fields["real_transcription_command_card.safe_to_share"], True)
        self.assertEqual(transcription_fields["real_transcription_command_card.uses_placeholders"], True)
        self.assertEqual(transcription_fields["real_transcription_command_card.preflight_runs_model"], False)
        self.assertEqual(
            transcription_fields["real_transcription_command_card.real_transcription_requires_user_audio"],
            True,
        )
        self.assertEqual(
            transcription_fields["real_transcription_command_card.real_transcription_requires_quality_review"],
            True,
        )
        self.assertEqual(transcription_fields["real_transcription_command_card.records_audio"], False)
        self.assertEqual(transcription_fields["real_transcription_command_card.records_audio_path"], False)
        self.assertEqual(transcription_fields["real_transcription_command_card.records_audio_file_name"], False)
        self.assertEqual(transcription_fields["real_transcription_command_card.records_transcript_text"], False)
        self.assertEqual(transcription_fields["real_transcription_command_card.records_expected_text"], False)
        self.assertEqual(
            transcription_fields["real_transcription_command_card.records_expected_text_file_name"],
            False,
        )
        self.assertEqual(transcription_fields["real_transcription_command_card.records_local_paths"], False)
        self.assertEqual(transcription_conditional_fields["credentials.checked"], True)
        self.assertEqual(transcription_conditional_fields["credentials.openai_api_key_required"], True)
        self.assertEqual(transcription_conditional_fields["credentials.openai_api_key_present"], True)
        self.assertEqual(transcription_conditional_fields["credentials.records_openai_api_key"], False)
        self.assertIn("system_guard.expected_system_matched", output_fields)
        self.assertIn("target_output_backend.available", output_fields)
        self.assertIn("output_backend_ready_required", output_fields)
        self.assertIn("text_review_confirmed", output_fields)
        self.assertIn("spoken_text_privacy_scan.passed", output_fields)
        self.assertIn("voice_review_confirmed", output_fields)
        self.assertIn("operator_checklist.expected_system_matched", output_fields)
        self.assertEqual(output_fields["operator_checklist.records_operator_identity"], False)
        self.assertEqual(output_fields["operator_checklist.redacts_spoken_text"], True)
        self.assertIn("operator_checklist.text_review_confirmed", output_fields)
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", output_fields)
        self.assertIn("operator_checklist.voice_review_confirmed", output_fields)
        self.assertEqual(output_fields["operator_checklist.commands_available"], True)
        self.assertEqual(output_fields["operator_checklist.ready_for_real_audio"], True)
        self.assertIn("operator_checklist.ready_for_beta_evidence", output_fields)
        self.assertEqual(output_fields["next_system_output.uses_placeholders"], True)
        self.assertEqual(output_fields["next_system_output.records_spoken_text"], False)
        self.assertEqual(output_fields["next_system_output.records_operator_identity"], False)
        self.assertEqual(output_fields["system_output_command_card.artifact"], "system-output-next-step.md")
        self.assertEqual(output_fields["system_output_command_card.blocker"], "system_output_audible")
        self.assertEqual(output_fields["system_output_command_card.ready_for_beta_evidence"], True)
        self.assertEqual(output_fields["system_output_command_card.safe_to_share"], True)
        self.assertEqual(output_fields["system_output_command_card.uses_placeholders"], True)
        self.assertEqual(output_fields["system_output_command_card.preflight_plays_audio"], False)
        self.assertEqual(output_fields["system_output_command_card.real_output_requires_operator"], True)
        self.assertEqual(output_fields["system_output_command_card.records_audio"], False)
        self.assertEqual(output_fields["system_output_command_card.records_spoken_text"], False)
        self.assertEqual(output_fields["system_output_command_card.records_operator_identity"], False)
        self.assertEqual(output_fields["system_output_command_card.records_local_paths"], False)
        self.assertEqual(windows_fields["target_capture_backend.available"], True)
        self.assertEqual(windows_fields["capture_backend_ready_required"], True)
        self.assertIn("system_guard.expected_system_matched", linux_fields)
        self.assertEqual(linux_fields["capture_backend"], "sounddevice | pyaudio")
        self.assertEqual(linux_fields["target_capture_backend.available"], True)
        self.assertEqual(linux_fields["capture_backend_ready_required"], True)
        self.assertIn("input_review_confirmed", linux_fields)
        self.assertIn("capture_checklist.input_review_confirmed", linux_fields)
        self.assertIn("capture_checklist.ready_for_beta_evidence", linux_fields)
        self.assertEqual(macos_fields["capture_backend"], "sounddevice | pyaudio")
        self.assertEqual(macos_fields["target_capture_backend.available"], True)
        self.assertEqual(macos_fields["capture_backend_ready_required"], True)
        for blocker, capture_fields in (
            ("windows_wasapi_capture", windows_fields),
            ("ubuntu_linux_capture", linux_fields),
            ("macos_capture", macos_fields),
        ):
            self.assertEqual(capture_fields["manual_capture_command_card.artifact"], "manual-capture-command.md")
            self.assertEqual(capture_fields["manual_capture_command_card.blocker"], blocker)
            self.assertEqual(capture_fields["manual_capture_command_card.ready_for_beta_evidence"], True)
            self.assertEqual(capture_fields["manual_capture_command_card.safe_to_share"], True)
            self.assertEqual(capture_fields["manual_capture_command_card.uses_placeholders"], True)
            self.assertEqual(capture_fields["manual_capture_command_card.preflight_uses_microphone"], False)
            self.assertEqual(capture_fields["manual_capture_command_card.real_capture_requires_microphone"], True)
            self.assertEqual(capture_fields["manual_capture_command_card.records_audio"], False)
            self.assertEqual(capture_fields["manual_capture_command_card.records_audio_bytes"], False)
            self.assertEqual(capture_fields["manual_capture_command_card.records_device_name"], False)
            self.assertEqual(capture_fields["manual_capture_command_card.records_local_paths"], False)

    def test_cli_requirements_markdown_is_public_safe(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--requirements"])
        content = output.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Requisitos de evidencias beta", content)
        self.assertIn("transcription-pilot-report.json", content)
        self.assertIn("system_guard.expected_system_matched", content)
        self.assertIn("credentials.openai_api_key_present", content)
        self.assertIn("credentials.records_openai_api_key", content)
        self.assertIn("input_review_confirmed", content)
        self.assertIn("target_capture_backend.available", content)
        self.assertIn("capture_backend_ready_required", content)
        self.assertIn("capture_checklist.input_review_confirmed", content)
        self.assertIn("capture_checklist.ready_for_beta_evidence", content)
        self.assertIn("manual_capture_command_card.safe_to_share", content)
        self.assertIn("manual_capture_command_card.uses_placeholders", content)
        self.assertIn("manual_capture_command_card.records_audio_bytes", content)
        self.assertIn("system_output_command_card.safe_to_share", content)
        self.assertIn("system_output_command_card.uses_placeholders", content)
        self.assertIn("system_output_command_card.records_spoken_text", content)
        self.assertIn("manual_capture_command_card.records_device_name", content)
        self.assertIn("manual_capture_command_card.records_local_paths", content)
        self.assertIn("quality.min_word_accuracy", content)
        self.assertIn("target_backend.available", content)
        self.assertIn("target_backend_ready_required", content)
        self.assertIn("preflight_readiness.status", content)
        self.assertIn("preflight_readiness.ready_for_model_run", content)
        self.assertIn("preflight_readiness.must_rerun_preflight", content)
        self.assertIn("preflight_readiness.records_audio_file_name", content)
        self.assertIn("audio.generated_synthetic_audio", content)
        self.assertIn("audio.audio_confirmed_non_sensitive", content)
        self.assertIn("audio.decoded", content)
        self.assertIn("audio.audio_file_name_redacted", content)
        self.assertIn("audio.duration_gate.enabled", content)
        self.assertIn("audio.duration_gate.passed", content)
        self.assertIn("audio_review_confirmed", content)
        self.assertIn("transcription_checklist.audio_review_confirmed", content)
        self.assertIn("transcription_checklist.records_audio_file_name", content)
        self.assertIn("transcription_checklist.records_expected_text_file_name", content)
        self.assertIn("reference_review_confirmed", content)
        self.assertIn("reference_privacy_scan.passed", content)
        self.assertIn("transcript.text_redacted", content)
        self.assertIn("transcription_checklist.reference_review_confirmed", content)
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", content)
        self.assertIn("transcription_checklist.redacts_transcript_text", content)
        self.assertIn("transcription_checklist.redacts_expected_text", content)
        self.assertIn("real_transcription_command_card.safe_to_share", content)
        self.assertIn("real_transcription_command_card.uses_placeholders", content)
        self.assertIn("real_transcription_command_card.records_audio_file_name", content)
        self.assertIn("real_transcription_command_card.records_transcript_text", content)
        self.assertIn("real_transcription_command_card.records_expected_text_file_name", content)
        self.assertIn("real_transcription_command_card.records_local_paths", content)
        self.assertIn("quality_review_confirmed", content)
        self.assertIn("text_review_confirmed", content)
        self.assertIn("spoken_text_privacy_scan.passed", content)
        self.assertIn("output_backend_ready_required", content)
        self.assertIn("voice_review_confirmed", content)
        self.assertIn("operator_checklist.expected_system_matched", content)
        self.assertIn("operator_checklist.records_operator_identity", content)
        self.assertIn("operator_checklist.redacts_spoken_text", content)
        self.assertIn("operator_checklist.text_review_confirmed", content)
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", content)
        self.assertIn("operator_checklist.commands_available", content)
        self.assertIn("operator_checklist.ready_for_real_audio", content)
        self.assertIn("next_system_output.uses_placeholders", content)
        self.assertIn("next_system_output.records_spoken_text", content)
        self.assertIn("next_system_output.records_operator_identity", content)
        self.assertIn("transcription_checklist.ready_for_beta_evidence", content)
        self.assertIn("No audio bytes", content)
        self.assertNotIn(str(ROOT), content)

    def test_cli_requirements_json_ignores_beta_blocker_failure(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--requirements", "--json", "--fail-on-blockers"])
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"], "AuralisVoiceKit")
        self.assertIn("requirements", payload)

    def test_evidence_audit_explains_satisfied_and_missing_fields(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                _transcription_evidence(min_word_accuracy=0.2),
            )
            _write_json(
                evidence_root / "ignored" / "manual-pilot-report.json",
                {"system": "Linux", "hardware_capture_tested": True, "passed": True},
            )

            report = module.build_evidence_audit_report(ROOT, evidence_paths=[evidence_root])

        self.assertEqual(report["accepted_count"], 2)
        self.assertEqual(report["ignored_count"], 1)
        self.assertEqual(report["ignored_details"][0]["reason"], "missing_project")
        self.assertEqual(report["privacy_audit"]["status"], "passed")
        self.assertEqual(report["privacy_audit"]["finding_count"], 0)
        self.assertFalse(report["ready_for_beta_by_evidence"])
        self.assertEqual(report["satisfied_blockers"], ["system_output_audible"])
        self.assertIn("real_transcription_quality", report["missing_blockers"])
        self.assertIn("ubuntu_linux_capture", report["missing_blockers"])

        artifacts = {artifact["artifact"]: artifact for artifact in report["artifacts"]}
        self.assertIn("system_output_audible", artifacts["output-pilot-report.json"]["satisfied_blockers"])

        transcription = artifacts["transcription-pilot-report.json"]
        self.assertEqual(transcription["satisfied_blockers"], [])
        field_checks = {
            field["path"]: field
            for candidate in transcription["candidates"]
            for field in candidate["fields"]
        }
        self.assertFalse(field_checks["quality.min_word_accuracy"]["ok"])
        self.assertEqual(field_checks["quality.min_word_accuracy"]["actual"], 0.2)

        summaries = {summary["name"]: summary for summary in report["blocker_summaries"]}
        transcription_summary = summaries["real_transcription_quality"]
        self.assertEqual(transcription_summary["status"], "pending")
        self.assertEqual(transcription_summary["candidate_count"], 1)
        self.assertEqual(
            transcription_summary["closest_candidate"]["file"],
            "transcription/transcription-pilot-report.json",
        )
        self.assertEqual(
            transcription_summary["closest_candidate"]["missing_fields"],
            ["quality.min_word_accuracy"],
        )
        output_summary = summaries["system_output_audible"]
        self.assertEqual(output_summary["status"], "closed")
        self.assertEqual(output_summary["accepted_sources"], ["output/output-pilot-report.json"])
        focus = report["next_evidence_focus"]
        self.assertEqual(focus["status"], "pending")
        self.assertEqual(focus["name"], "windows_wasapi_capture")
        self.assertEqual(focus["artifact"], "manual-pilot-report.json")
        self.assertIsNone(focus["closest_candidate"])
        self.assertIn("target_capture_backend.available", focus["missing_fields"])
        self.assertIn("manual_capture_command_card.safe_to_share", focus["required_fields"])

    def test_cli_audit_evidence_markdown_is_public_safe(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            evidence_path = tmpdir_path / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                _capture_evidence("Linux", "pyaudio"),
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(["--root", str(ROOT), "--audit-evidence", "--evidence", str(evidence_path)])
            content = output.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Auditoria de evidencias beta", content)
        self.assertIn("Resumen de blockers", content)
        self.assertIn("Resumen por blocker", content)
        self.assertIn("Escaneo de privacidad", content)
        self.assertIn("Siguiente foco de evidencia", content)
        self.assertIn("Listo para beta segun evidencias JSON", content)
        self.assertIn("ubuntu_linux_capture", content)
        self.assertIn("Candidato mas cercano", content)
        self.assertIn("Campos faltantes del candidato mas cercano", content)
        self.assertIn("Blockers cerrados", content)
        self.assertNotIn(str(tmpdir_path), content)

    def test_cli_audit_evidence_json_ignores_beta_blocker_failure(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--audit-evidence", "--json", "--fail-on-blockers"])
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["project"], "AuralisVoiceKit")
        self.assertEqual(payload["accepted_count"], 0)
        self.assertEqual(payload["artifacts"], [])
        self.assertFalse(payload["ready_for_beta_by_evidence"])
        self.assertIn("real_transcription_quality", payload["missing_blockers"])
        self.assertEqual(payload["privacy_audit"]["status"], "passed")
        self.assertEqual(payload["privacy_audit"]["finding_count"], 0)
        self.assertIn("blocker_summaries", payload)
        self.assertEqual(payload["blocker_summaries"][0]["candidate_count"], 0)
        self.assertEqual(payload["next_evidence_focus"]["status"], "pending")
        self.assertEqual(payload["next_evidence_focus"]["name"], "windows_wasapi_capture")
        self.assertIn("target_capture_backend.available", payload["next_evidence_focus"]["missing_fields"])

    def test_cli_audit_evidence_can_fail_on_missing_blockers(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--audit-evidence", "--json", "--fail-on-audit-gaps"])
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["accepted_count"], 0)
        self.assertFalse(payload["ready_for_beta_by_evidence"])
        self.assertIn("real_transcription_quality", payload["missing_blockers"])

    def test_cli_audit_evidence_can_fail_on_ignored_artifacts(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "manual-pilot-report.json",
                {"system": "Linux", "hardware_capture_tested": True, "passed": True},
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    ["--audit-evidence", "--evidence", str(evidence_root), "--json", "--fail-on-audit-gaps"]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["ignored_count"], 1)
        self.assertEqual(payload["ignored_details"][0]["reason"], "missing_project")

    def test_evidence_audit_blocks_raw_private_fields_without_printing_values(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            transcription = _transcription_evidence()
            transcription["transcript"]["text"] = "hola secreto interno"
            transcription["audio"]["path"] = "C:\\Users\\Private\\sample.mp3"
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                transcription,
            )

            report = module.build_evidence_audit_report(ROOT, evidence_paths=[evidence_root])

        self.assertEqual(report["missing_blockers"], [])
        self.assertFalse(report["ready_for_beta_by_evidence"])
        self.assertEqual(report["privacy_audit"]["status"], "failed")
        self.assertEqual(report["privacy_audit"]["finding_count"], 2)
        fields = {finding["field"] for finding in report["privacy_audit"]["findings"]}
        self.assertIn("transcript.text", fields)
        self.assertIn("audio.path", fields)
        findings = {finding["field"]: finding for finding in report["privacy_audit"]["findings"]}
        self.assertEqual(findings["transcript.text"]["safe_replacement"], "<text-redacted>")
        self.assertIn("Eliminar el texto crudo", findings["transcript.text"]["action_es"])
        self.assertEqual(findings["audio.path"]["safe_replacement"], "<path-redacted>")
        self.assertIn("Eliminar la ruta local completa", findings["audio.path"]["action_es"])
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn("hola secreto interno", serialized)
        self.assertNotIn("Private", serialized)

    def test_cli_audit_evidence_can_fail_on_privacy_findings(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            transcription = _transcription_evidence()
            transcription["expected_text"] = "texto esperado privado"
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                transcription,
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    ["--audit-evidence", "--evidence", str(evidence_root), "--json", "--fail-on-audit-gaps"]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["missing_blockers"], [])
        self.assertEqual(payload["privacy_audit"]["status"], "failed")
        self.assertEqual(payload["privacy_audit"]["findings"][0]["field"], "expected_text")
        self.assertIn("action_es", payload["privacy_audit"]["findings"][0])
        self.assertEqual(payload["privacy_audit"]["findings"][0]["safe_replacement"], "<text-redacted>")
        self.assertNotIn("texto esperado privado", output.getvalue())

    def test_evidence_audit_can_mark_all_json_blockers_satisfied(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                _transcription_evidence(),
            )

            report = module.build_evidence_audit_report(ROOT, evidence_paths=[evidence_root])

        self.assertTrue(report["ready_for_beta_by_evidence"])
        self.assertEqual(report["privacy_audit"]["status"], "passed")
        self.assertEqual(report["privacy_audit"]["finding_count"], 0)
        self.assertEqual(report["missing_blockers"], [])
        self.assertEqual(set(report["satisfied_blockers"]), set(report["required_blockers"]))

    def test_cli_audit_evidence_strict_passes_when_all_json_blockers_are_satisfied(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                _capture_evidence("Windows", "wasapi"),
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                _capture_evidence("Linux", "sounddevice"),
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                _capture_evidence("Darwin", "pyaudio"),
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                _output_evidence(),
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                _transcription_evidence(),
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    ["--audit-evidence", "--evidence", str(evidence_root), "--json", "--fail-on-audit-gaps"]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ready_for_beta_by_evidence"])
        self.assertEqual(payload["privacy_audit"]["status"], "passed")
        self.assertEqual(payload["missing_blockers"], [])
        self.assertEqual(payload["ignored_count"], 0)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _capture_checklist() -> dict[str, bool]:
    return {"input_review_confirmed": True, "ready_for_beta_evidence": True}


def _capture_backend_status(backend: str) -> dict:
    return {
        "name": backend,
        "kind": "capture",
        "available": True,
        "dependencies": [backend],
        "reason": None,
    }


def _manual_capture_command_card(system: str, backend: str) -> dict:
    if system == "Windows":
        blocker = "windows_wasapi_capture"
        expected_system = "Windows"
    elif system in {"Linux", "Ubuntu/Linux", "Ubuntu"}:
        blocker = "ubuntu_linux_capture"
        expected_system = "Linux | Ubuntu/Linux | Ubuntu"
    else:
        blocker = "macos_capture"
        expected_system = "Darwin | macOS | Mac"
    base_command = (
        f"python tools/manual_pilot.py --backend {backend} --device default "
        f"--expected-system {system} --require-capture-backend-ready --json"
    )
    return {
        "artifact": "manual-capture-command.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "blocker": blocker,
        "evidence_system": expected_system,
        "ready_for_beta_evidence": True,
        "missing_count": 0,
        "missing_fields": [],
        "setup_commands": [],
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


def _capture_evidence(system: str, backend: str) -> dict:
    return {
        "project": "AuralisVoiceKit",
        "system": system,
        "capture_backend": backend,
        "target_capture_backend": _capture_backend_status(backend),
        "capture_backend_ready_required": True,
        "system_guard": _system_guard(),
        "hardware_capture_tested": True,
        "input_review_confirmed": True,
        "capture_checklist": _capture_checklist(),
        "manual_capture_command_card": _manual_capture_command_card(system, backend),
        "passed": True,
    }


def _output_evidence() -> dict:
    return {
        "project": "AuralisVoiceKit",
        "backend": "system",
        "target_output_backend": {
            "name": "system",
            "kind": "output",
            "available": True,
            "dependencies": ["test-tts"],
            "reason": None,
        },
        "output_backend_ready_required": True,
        "system_guard": _system_guard(),
        "real_audio_requested": True,
        "operator_confirmation_status": "confirmed",
        "text_review_confirmed": True,
        "spoken_text_privacy_scan": {
            "enabled": True,
            "passed": True,
            "risk_count": 0,
            "risk_types": [],
        },
        "voice_review_confirmed": True,
        "operator_checklist": {
            "expected_system_matched": True,
            "records_operator_identity": False,
            "redacts_spoken_text": True,
            "text_review_confirmed": True,
            "spoken_text_privacy_scan_passed": True,
            "voice_review_confirmed": True,
            "commands_available": True,
            "ready_for_real_audio": True,
            "ready_for_beta_evidence": True,
        },
        "next_system_output": {
            "uses_placeholders": True,
            "records_spoken_text": False,
            "records_operator_identity": False,
        },
        "system_output_command_card": _system_output_command_card(),
        "passed": True,
    }


def _system_output_command_card() -> dict:
    return {
        "artifact": "system-output-next-step.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "blocker": "system_output_audible",
        "ready_for_beta_evidence": True,
        "preflight_command_template": (
            "python tools/output_pilot.py --system Linux --require-output-backend-ready "
            "--json --output-dir <pilot-output-dir>"
        ),
        "preflight_plays_audio": False,
        "real_output_command_template": (
            "python tools/output_pilot.py --speak --operator-present --confirm-audible "
            "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
            "--expected-system \"Windows|Linux|Darwin\" --output-dir <pilot-output-dir> "
            "--text <public-spoken-text> --json"
        ),
        "real_output_requires_operator": True,
        "audit_command_template": (
            "python tools/beta_readiness.py --audit-evidence --evidence <pilot-output-dir> --json"
        ),
        "records_audio": False,
        "records_spoken_text": False,
        "records_operator_identity": False,
        "records_local_paths": False,
    }


def _real_transcription_command_card() -> dict:
    return {
        "artifact": "real-transcription-command.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "blocker": "real_transcription_quality",
        "ready_for_beta_evidence": True,
        "missing_count": 0,
        "missing_fields": [],
        "preflight_command_template": (
            "python tools/transcription_pilot.py --preflight-only --audio <audio-path> "
            "--audio-non-sensitive --confirm-audio-reviewed --backend whisper --model base "
            "--require-target-backend-ready --output-dir <pilot-output-dir> --json"
        ),
        "preflight_runs_model": False,
        "real_transcription_command_template": (
            "python tools/transcription_pilot.py --real-transcription --audio <audio-path> "
            "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
            "--backend whisper --model base --expected-text-file <expected-text-path> "
            "--min-word-accuracy 0.75 --confirm-quality-reviewed "
            "--require-target-backend-ready --output-dir <pilot-output-dir> --json"
        ),
        "real_transcription_requires_user_audio": True,
        "real_transcription_requires_quality_review": True,
        "audit_command_template": (
            "python tools/beta_readiness.py --audit-evidence --evidence <pilot-output-dir> --json"
        ),
        "records_audio": False,
        "records_audio_path": False,
        "records_audio_file_name": False,
        "records_transcript_text": False,
        "records_expected_text": False,
        "records_expected_text_file_name": False,
        "records_local_paths": False,
    }


def _transcription_evidence(
    *, min_word_accuracy: float = 0.75, word_accuracy: float = 0.92, backend: str = "whisper"
) -> dict:
    evidence = {
        "project": "AuralisVoiceKit",
        "real_transcription_requested": True,
        "target_backend": {
            "name": backend,
            "kind": "transcription",
            "available": True,
            "dependencies": ["openai"] if backend == "openai" else ["faster-whisper"],
            "reason": None,
        },
        "target_backend_ready_required": True,
        "preflight_readiness": {
            "status": "ready",
            "decision": "ready_for_real_transcription",
            "ready_for_model_run": True,
            "must_rerun_preflight": False,
            "safe_to_share": True,
            "usable_as_beta_evidence": False,
            "records_audio": False,
            "records_transcripts": False,
            "records_expected_text": False,
            "records_audio_file_name": False,
            "records_local_paths": False,
            "backend_ready": True,
            "audio_decoded": True,
            "duration_gate_enabled": True,
            "duration_gate_passed": True,
            "blocking_reasons": [],
        },
        "audio_confirmed_non_sensitive": True,
        "audio": {
            "generated_synthetic_audio": False,
            "audio_file_name": "<audio-file-redacted>",
            "audio_file_name_redacted": True,
            "audio_file_extension": ".mp3",
            "audio_confirmed_non_sensitive": True,
            "decoded": True,
            "duration_gate": {
                "enabled": True,
                "passed": True,
                "min_seconds": 0.2,
                "max_seconds": 60,
                "duration_seconds": 1.0,
            },
        },
        "audio_review_confirmed": True,
        "reference_review_confirmed": True,
        "reference_privacy_scan": {
            "enabled": True,
            "passed": True,
            "risk_count": 0,
            "risk_types": [],
        },
        "quality_review_confirmed": True,
        "passed": True,
        "transcript": {
            "text_redacted": True,
            "text_characters": 24,
            "text_sha256": None,
        },
        "quality": {
            "enabled": True,
            "passed": True,
            "min_word_accuracy": min_word_accuracy,
            "word_accuracy": word_accuracy,
        },
        "transcription_checklist": {
            "audio_review_confirmed": True,
            "records_audio_path": False,
            "records_audio_file_name": False,
            "records_transcript_text": False,
            "records_expected_text": False,
            "records_expected_text_file_name": False,
            "redacts_transcript_text": True,
            "redacts_expected_text": True,
            "reference_review_confirmed": True,
            "reference_privacy_scan_passed": True,
            "quality_review_confirmed": True,
            "ready_for_beta_evidence": True,
        },
        "real_transcription_command_card": _real_transcription_command_card(),
    }
    if backend == "openai":
        evidence["credentials"] = {
            "checked": True,
            "status": "present",
            "openai_api_key_required": True,
            "openai_api_key_present": True,
            "records_openai_api_key": False,
        }
    return evidence


def _system_guard() -> dict[str, bool]:
    return {"expected_system_matched": True}


if __name__ == "__main__":
    unittest.main()
