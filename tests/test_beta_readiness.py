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
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "capture_backend": "sounddevice",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "operator_checklist": {"ready_for_beta_evidence": True},
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {
                        "enabled": True,
                        "passed": True,
                        "min_word_accuracy": 0.75,
                        "word_accuracy": 0.92,
                    },
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
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
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {
                        "enabled": True,
                        "passed": True,
                        "min_word_accuracy": 0.1,
                        "word_accuracy": 1.0,
                    },
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
            )

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
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.75},
                },
            )

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

    def test_cli_evidence_allows_strict_beta_pass(self):
        module = _load_beta_readiness()

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir)
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "operator_checklist": {"ready_for_beta_evidence": True},
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.8},
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
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
                    "operator_checklist": {"ready_for_beta_evidence": True},
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
                    "operator_checklist": {"ready_for_beta_evidence": True},
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
        linux_fields = {field["path"] for field in requirements["ubuntu_linux_capture"]["fields"]}
        self.assertEqual(transcription_fields["quality.min_word_accuracy"], ">= 0.75")
        self.assertEqual(transcription_fields["transcription_checklist.ready_for_beta_evidence"], True)
        self.assertIn("operator_checklist.ready_for_beta_evidence", output_fields)
        self.assertIn("capture_checklist.ready_for_beta_evidence", linux_fields)

    def test_cli_requirements_markdown_is_public_safe(self):
        module = _load_beta_readiness()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = module.main(["--requirements"])
        content = output.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Requisitos de evidencias beta", content)
        self.assertIn("transcription-pilot-report.json", content)
        self.assertIn("capture_checklist.ready_for_beta_evidence", content)
        self.assertIn("quality.min_word_accuracy", content)
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
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "operator_checklist": {"ready_for_beta_evidence": True},
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.2},
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
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
                    "hardware_capture_tested": True,
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
                    "capture_backend": "wasapi",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "operator_checklist": {"ready_for_beta_evidence": True},
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.75},
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
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
                    "capture_backend": "wasapi",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "linux" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Linux",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "macos" / "manual-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "system": "Darwin",
                    "hardware_capture_tested": True,
                    "capture_checklist": _capture_checklist(),
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "output" / "output-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "backend": "system",
                    "real_audio_requested": True,
                    "operator_confirmation_status": "confirmed",
                    "operator_checklist": {"ready_for_beta_evidence": True},
                    "passed": True,
                },
            )
            _write_json(
                evidence_root / "transcription" / "transcription-pilot-report.json",
                {
                    "project": "AuralisVoiceKit",
                    "real_transcription_requested": True,
                    "audio_confirmed_non_sensitive": True,
                    "passed": True,
                    "quality": {"enabled": True, "passed": True, "min_word_accuracy": 0.75},
                    "transcription_checklist": {"ready_for_beta_evidence": True},
                },
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
    return {"ready_for_beta_evidence": True}


if __name__ == "__main__":
    unittest.main()
