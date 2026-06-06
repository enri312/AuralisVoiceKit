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
        self.assertTrue(checks["windows_wasapi_capture"]["ok"])
        self.assertFalse(checks["real_transcription_quality"]["ok"])
        self.assertFalse(checks["system_output_audible"]["ok"])
        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertFalse(checks["macos_capture"]["ok"])
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
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
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
        self.assertEqual(report["evidence"]["count"], 4)
        self.assertTrue(checks["real_transcription_quality"]["ok"])
        self.assertTrue(checks["system_output_audible"]["ok"])
        self.assertTrue(checks["ubuntu_linux_capture"]["ok"])
        self.assertTrue(checks["macos_capture"]["ok"])
        self.assertIn("transcription/transcription-pilot-report.json", checks["real_transcription_quality"]["evidence_sources"])

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
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
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
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "capture_checklist": {
                        "ready_for_beta_evidence": True,
                        "input_review_confirmed": False,
                    },
                    "passed": True,
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
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "wav",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )

            report = module.build_beta_readiness_report(ROOT, evidence_paths=[evidence_path])
            checks = {check["name"]: check for check in report["checks"]}

        self.assertFalse(checks["ubuntu_linux_capture"]["ok"])
        self.assertIn("ubuntu_linux_capture", report["blockers"])

    def test_cli_evidence_allows_strict_beta_pass(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
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
        output_fields = {field["path"] for field in requirements["system_output_audible"]["fields"]}
        linux_fields = {
            field["path"]: field["expected"] for field in requirements["ubuntu_linux_capture"]["fields"]
        }
        macos_fields = {field["path"]: field["expected"] for field in requirements["macos_capture"]["fields"]}
        self.assertEqual(transcription_fields["audio_confirmed_non_sensitive"], True)
        self.assertEqual(transcription_fields["target_backend.available"], True)
        self.assertEqual(transcription_fields["audio.audio_file_name_redacted"], True)
        self.assertEqual(transcription_fields["audio_review_confirmed"], True)
        self.assertEqual(transcription_fields["reference_review_confirmed"], True)
        self.assertEqual(transcription_fields["reference_privacy_scan.passed"], True)
        self.assertEqual(transcription_fields["quality.min_word_accuracy"], ">= 0.75")
        self.assertEqual(transcription_fields["quality_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.audio_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.records_audio_path"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_audio_file_name"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_transcript_text"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_expected_text"], False)
        self.assertEqual(transcription_fields["transcription_checklist.records_expected_text_file_name"], False)
        self.assertEqual(transcription_fields["transcription_checklist.reference_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.reference_privacy_scan_passed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.quality_review_confirmed"], True)
        self.assertEqual(transcription_fields["transcription_checklist.ready_for_beta_evidence"], True)
        self.assertIn("system_guard.expected_system_matched", output_fields)
        self.assertIn("target_output_backend.available", output_fields)
        self.assertIn("text_review_confirmed", output_fields)
        self.assertIn("spoken_text_privacy_scan.passed", output_fields)
        self.assertIn("voice_review_confirmed", output_fields)
        self.assertIn("operator_checklist.expected_system_matched", output_fields)
        self.assertIn("operator_checklist.text_review_confirmed", output_fields)
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", output_fields)
        self.assertIn("operator_checklist.voice_review_confirmed", output_fields)
        self.assertIn("operator_checklist.ready_for_beta_evidence", output_fields)
        self.assertIn("system_guard.expected_system_matched", linux_fields)
        self.assertEqual(linux_fields["capture_backend"], "sounddevice | pyaudio")
        self.assertIn("input_review_confirmed", linux_fields)
        self.assertIn("capture_checklist.input_review_confirmed", linux_fields)
        self.assertIn("capture_checklist.ready_for_beta_evidence", linux_fields)
        self.assertEqual(macos_fields["capture_backend"], "sounddevice | pyaudio")

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
        self.assertIn("input_review_confirmed", content)
        self.assertIn("capture_checklist.input_review_confirmed", content)
        self.assertIn("capture_checklist.ready_for_beta_evidence", content)
        self.assertIn("quality.min_word_accuracy", content)
        self.assertIn("target_backend.available", content)
        self.assertIn("audio.audio_file_name_redacted", content)
        self.assertIn("audio_review_confirmed", content)
        self.assertIn("transcription_checklist.audio_review_confirmed", content)
        self.assertIn("transcription_checklist.records_audio_file_name", content)
        self.assertIn("transcription_checklist.records_expected_text_file_name", content)
        self.assertIn("reference_review_confirmed", content)
        self.assertIn("reference_privacy_scan.passed", content)
        self.assertIn("transcription_checklist.reference_review_confirmed", content)
        self.assertIn("transcription_checklist.reference_privacy_scan_passed", content)
        self.assertIn("quality_review_confirmed", content)
        self.assertIn("text_review_confirmed", content)
        self.assertIn("spoken_text_privacy_scan.passed", content)
        self.assertIn("voice_review_confirmed", content)
        self.assertIn("operator_checklist.expected_system_matched", content)
        self.assertIn("operator_checklist.text_review_confirmed", content)
        self.assertIn("operator_checklist.spoken_text_privacy_scan_passed", content)
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

    def test_cli_audit_evidence_markdown_is_public_safe(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            evidence_path = tmpdir_path / "manual-pilot-report.json"
            _write_json(
                evidence_path,
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(["--root", str(ROOT), "--audit-evidence", "--evidence", str(evidence_path)])
            content = output.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Auditoria de evidencias beta", content)
        self.assertIn("Resumen de blockers", content)
        self.assertIn("Listo para beta segun evidencias JSON", content)
        self.assertIn("ubuntu_linux_capture", content)
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

    def test_evidence_audit_can_mark_all_json_blockers_satisfied(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Windows",
                    "system_guard": _system_guard(),
                    "capture_backend": "wasapi",
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
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
        self.assertEqual(report["missing_blockers"], [])
        self.assertEqual(set(report["satisfied_blockers"]), set(report["required_blockers"]))

    def test_cli_audit_evidence_strict_passes_when_all_json_blockers_are_satisfied(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "windows" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Windows",
                    "system_guard": _system_guard(),
                    "capture_backend": "wasapi",
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "capture_backend": "sounddevice",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "pyaudio",
                    "system_guard": _system_guard(),
                    "hardware_capture_tested": True,
                    "input_review_confirmed": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
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
        self.assertEqual(payload["missing_blockers"], [])
        self.assertEqual(payload["ignored_count"], 0)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _capture_checklist() -> dict[str, bool]:
    return {"input_review_confirmed": True, "ready_for_beta_evidence": True}


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
            "text_review_confirmed": True,
            "spoken_text_privacy_scan_passed": True,
            "voice_review_confirmed": True,
            "ready_for_beta_evidence": True,
        },
        "passed": True,
    }


def _transcription_evidence(*, min_word_accuracy: float = 0.75, word_accuracy: float = 0.92) -> dict:
    return {
        "project": "AuralisVoiceKit",
        "real_transcription_requested": True,
        "target_backend": {
            "name": "whisper",
            "kind": "transcription",
            "available": True,
            "dependencies": ["faster-whisper"],
            "reason": None,
        },
        "audio_confirmed_non_sensitive": True,
        "audio": {
            "audio_file_name": "<audio-file-redacted>",
            "audio_file_name_redacted": True,
            "audio_file_extension": ".mp3",
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
            "reference_review_confirmed": True,
            "reference_privacy_scan_passed": True,
            "quality_review_confirmed": True,
            "ready_for_beta_evidence": True,
        },
    }


def _system_guard() -> dict[str, bool]:
    return {"expected_system_matched": True}


if __name__ == "__main__":
    unittest.main()
