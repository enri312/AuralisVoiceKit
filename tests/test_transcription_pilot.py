import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from auralis_voicekit import AudioChunk, AudioFormat, write_wav


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTION_PILOT = ROOT / "tools" / "transcription_pilot.py"


def _load_transcription_pilot():
    spec = importlib.util.spec_from_file_location("transcription_pilot", TRANSCRIPTION_PILOT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _reference_privacy_scan(*, passed: bool = True) -> dict:
    return {
        "enabled": True,
        "passed": passed,
        "risk_count": 0 if passed else 1,
        "risk_types": [] if passed else ["email"],
    }


class TranscriptionPilotTests(unittest.TestCase):
    def test_transcription_pilot_writes_sanitized_synthetic_report(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["transcription_review_checklist"])
            next_step_path = Path(report["artifacts"]["real_transcription_next_step"])
            synthetic_audio = Path(report["artifacts"]["synthetic_audio"])
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")
            next_step = next_step_path.read_text(encoding="utf-8")
            synthetic_audio_exists = synthetic_audio.exists()
            report_text = report_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertEqual(report["backend"], "null")
        self.assertFalse(report["real_transcription_requested"])
        self.assertTrue(report["generated_synthetic_audio"])
        self.assertTrue(synthetic_audio_exists)
        self.assertEqual(payload["transcript"]["text_characters"], 0)
        self.assertTrue(payload["transcript"]["text_redacted"])
        self.assertFalse(payload["audio_review_confirmed"])
        self.assertFalse(payload["reference_review_confirmed"])
        self.assertFalse(payload["reference_privacy_scan"]["enabled"])
        self.assertIsNone(payload["reference_privacy_scan"]["passed"])
        self.assertFalse(payload["transcription_checklist"]["audio_review_confirmed"])
        self.assertFalse(payload["transcription_checklist"]["reference_review_confirmed"])
        self.assertIsNone(payload["transcription_checklist"]["reference_privacy_scan_passed"])
        self.assertFalse(payload["quality_review_confirmed"])
        self.assertFalse(payload["transcription_checklist"]["quality_review_confirmed"])
        self.assertFalse(payload["transcription_checklist"]["records_audio_path"])
        self.assertFalse(payload["transcription_checklist"]["records_audio_file_name"])
        self.assertFalse(payload["transcription_checklist"]["records_transcript_text"])
        self.assertFalse(payload["transcription_checklist"]["records_expected_text"])
        self.assertFalse(payload["transcription_checklist"]["records_expected_text_file_name"])
        self.assertIn("transcription_review_checklist", report["artifacts"])
        self.assertIn("real_transcription_next_step", report["artifacts"])
        self.assertNotIn("text\": \"", report_text)
        self.assertIn("Transcription pilot findings", findings)
        self.assertIn("Generated synthetic audio: True", findings)
        self.assertIn("Real transcription next step: real-transcription-next-step.md", findings)
        self.assertIn("Transcription checklist ready for beta evidence: False", findings)
        self.assertIn("Transcription review checklist", checklist)
        self.assertIn("Records transcript text: False", checklist)
        self.assertIn("real-transcription-next-step.md", checklist)
        self.assertIn("--audio <audio-path>", next_step)
        self.assertIn("--expected-text-file <expected-text-path>", next_step)

    def test_transcription_pilot_cli_outputs_json(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--duration",
                        "0.3",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["backend"], "null")
        self.assertTrue(payload["generated_synthetic_audio"])
        self.assertFalse(payload["real_transcription_requested"])
        self.assertFalse(payload["audio_review_confirmed"])
        self.assertFalse(payload["reference_review_confirmed"])
        self.assertFalse(payload["reference_privacy_scan"]["enabled"])
        self.assertFalse(payload["quality_review_confirmed"])
        self.assertIn("transcription_review_checklist", payload["artifacts"])
        self.assertFalse(payload["transcription_checklist"]["ready_for_beta_evidence"])

    def test_transcription_pilot_rejects_real_backend_without_guard(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--backend",
                        "whisper",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("--real-transcription", payload["error"])

    def test_transcription_pilot_rejects_real_transcription_without_audio_confirmation(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    backend="whisper",
                    audio="sample.wav",
                    real_transcription=True,
                )

    def test_transcription_pilot_calculates_redacted_quality_metrics(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_text="Hola desde AuralisVoiceKit",
                min_word_accuracy=0.0,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["transcription_review_checklist"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["quality"]["enabled"])
        self.assertTrue(report["quality"]["expected_text_redacted"])
        self.assertTrue(report["reference_privacy_scan"]["passed"])
        self.assertEqual(report["reference_privacy_scan"]["risk_count"], 0)
        self.assertEqual(report["quality"]["expected_text_source"], "argument")
        self.assertEqual(report["quality"]["word_accuracy"], 0.0)
        self.assertEqual(report["quality"]["word_error_rate"], 1.0)
        self.assertTrue(report["quality"]["passed"])
        self.assertNotIn("Hola desde AuralisVoiceKit", report_text)
        self.assertIn("Quality reference provided: True", findings)
        self.assertIn("Reference privacy scan passed: True", findings)
        self.assertIn("Word accuracy: 0.0", findings)
        self.assertIn("Reference privacy scan passed: True", checklist)
        self.assertIn("quality_review_confirmed", checklist)

    def test_transcription_pilot_blocks_beta_reference_with_sensitive_patterns(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            reference = "Contactar a persona@example.com con el codigo 123456789."
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_text=reference,
                min_word_accuracy=0.0,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["transcription_review_checklist"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")

        self.assertFalse(report["passed"])
        self.assertTrue(report["reference_privacy_scan"]["enabled"])
        self.assertFalse(report["reference_privacy_scan"]["passed"])
        self.assertIn("email", report["reference_privacy_scan"]["risk_types"])
        self.assertIn("long_number", report["reference_privacy_scan"]["risk_types"])
        self.assertFalse(report["transcription_checklist"]["reference_privacy_scan_passed"])
        self.assertFalse(report["transcription_checklist"]["ready_for_beta_evidence"])
        self.assertNotIn("persona@example.com", report_text)
        self.assertNotIn("123456789", report_text)
        self.assertIn("Reference privacy scan passed: False", findings)
        self.assertIn("Reference privacy risk types: email", findings)
        self.assertIn("reference_privacy_scan_passed", checklist)

    def test_transcription_pilot_quality_gate_can_fail(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        tmpdir,
                        "--expected-text",
                        "Hola desde AuralisVoiceKit",
                        "--min-word-accuracy",
                        "0.5",
                        "--duration",
                        "0.3",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["passed"])
        self.assertFalse(payload["quality"]["passed"])
        self.assertEqual(payload["quality"]["word_accuracy"], 0.0)

    def test_transcription_pilot_rejects_multiple_expected_text_sources(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            reference = Path(tmpdir) / "reference.txt"
            reference.write_text("Hola", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    expected_text="Hola",
                    expected_text_file=reference,
                )

    def test_transcription_pilot_expected_text_file_redacts_file_name(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            reference = Path(tmpdir) / "secret-reference.txt"
            reference.write_text("Hola desde archivo", encoding="utf-8")
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=tmpdir,
                expected_text_file=reference,
                min_word_accuracy=0.0,
                duration_seconds=0.3,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = Path(report["artifacts"]["pilot_findings"]).read_text(encoding="utf-8")
            checklist = Path(report["artifacts"]["transcription_review_checklist"]).read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertEqual(report["quality"]["expected_text_source"], "file")
        self.assertEqual(report["quality"]["expected_text_file_name"], "<expected-text-file-redacted>")
        self.assertTrue(report["quality"]["expected_text_file_name_redacted"])
        self.assertEqual(report["quality"]["expected_text_file_extension"], ".txt")
        self.assertNotIn("Hola desde archivo", report_text)
        self.assertNotIn("secret-reference.txt", report_text)
        self.assertNotIn("secret-reference.txt", findings)
        self.assertNotIn("secret-reference.txt", checklist)
        self.assertIn("Expected text file name redacted: True", findings)
        self.assertIn("Records expected text file name: False", checklist)

    def test_transcription_pilot_preflight_decodes_audio_without_backend(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "private-meeting.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                audio=audio_path,
                backend="whisper",
                preflight_only=True,
                audio_confirmed_non_sensitive=True,
                min_audio_seconds=0.05,
                max_audio_seconds=1.0,
                sample_rate=8000,
            )
            report_path = Path(report["artifacts"]["transcription_pilot_report"])
            findings_path = Path(report["artifacts"]["pilot_findings"])
            checklist_path = Path(report["artifacts"]["transcription_review_checklist"])
            next_step_path = Path(report["artifacts"]["real_transcription_next_step"])
            report_text = report_path.read_text(encoding="utf-8")
            findings = findings_path.read_text(encoding="utf-8")
            checklist = checklist_path.read_text(encoding="utf-8")
            next_step = next_step_path.read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertTrue(report["preflight_only"])
        self.assertFalse(report["real_transcription_requested"])
        self.assertIsNone(report["transcript"])
        self.assertEqual(report["target_backend"]["name"], "whisper")
        self.assertEqual(report["target_backend"]["kind"], "transcription")
        self.assertIsInstance(report["target_backend"]["available"], bool)
        self.assertIn("faster-whisper", report["target_backend"]["dependencies"])
        self.assertEqual(report["target_backend"]["install_command"], 'python -m pip install "auralisvoicekit[whisper]"')
        self.assertEqual(report["target_backend"]["install_plan"]["extra"], "whisper")
        self.assertIn("--require-target-backend-ready", report["target_backend"]["install_plan"]["post_install_check"])
        self.assertTrue(report["audio"]["decoded"])
        self.assertEqual(report["audio"]["audio_file_name"], "<audio-file-redacted>")
        self.assertTrue(report["audio"]["audio_file_name_redacted"])
        self.assertEqual(report["audio"]["source_format"], "wav")
        self.assertTrue(report["audio"]["duration_gate"]["enabled"])
        self.assertTrue(report["audio"]["duration_gate"]["passed"])
        expected_preflight_decision = (
            "ready_for_real_transcription"
            if report["target_backend"]["available"]
            else "install_backend_then_retry_preflight"
        )
        self.assertEqual(report["preflight_decision"]["decision"], expected_preflight_decision)
        self.assertTrue(report["preflight_decision"]["safe_to_share"])
        self.assertFalse(report["preflight_decision"]["usable_as_beta_evidence"])
        self.assertFalse(report["preflight_decision"]["records_audio"])
        self.assertFalse(report["preflight_decision"]["records_audio_file_name"])
        self.assertEqual(report["preflight_decision"]["blocking_reasons"], [])
        self.assertNotIn(str(audio_path), report_text)
        self.assertNotIn("private-meeting.wav", report_text)
        self.assertNotIn("private-meeting.wav", findings)
        self.assertNotIn("private-meeting.wav", checklist)
        self.assertNotIn("private-meeting.wav", next_step)
        self.assertNotIn(str(audio_path), next_step)
        self.assertIn("Preflight only: True", findings)
        self.assertIn("Target backend available:", findings)
        self.assertIn("Target backend dependencies: faster-whisper", findings)
        self.assertIn('Target backend install command: python -m pip install "auralisvoicekit[whisper]"', findings)
        self.assertIn("Audio file name redacted: True", findings)
        self.assertIn("Audio decode passed: True", findings)
        self.assertIn("Duration gate passed: True", findings)
        self.assertIn(f"Preflight decision: {expected_preflight_decision}", findings)
        self.assertIn("Review checklist: transcription-review-checklist.md", findings)
        self.assertIn("Real transcription next step: real-transcription-next-step.md", findings)
        self.assertIn("--real-transcription", next_step)
        self.assertIn("--audio <audio-path>", next_step)
        self.assertIn("--expected-text-file <expected-text-path>", next_step)
        self.assertIn("--require-target-backend-ready", next_step)
        self.assertIn("Target backend dependencies: faster-whisper", next_step)
        self.assertIn("target_backend.install_plan.pip_command", next_step)
        self.assertIn("target_backend.install_plan.post_install_check", next_step)
        self.assertIn("audio.audio_file_name_redacted=true", next_step)
        self.assertIn("target_backend.available=true", next_step)
        self.assertIn(f"Preflight decision: {expected_preflight_decision}", next_step)
        self.assertIn("preflight_decision.decision=ready_for_real_transcription", next_step)
        self.assertIn("transcription_checklist.records_audio_file_name=false", next_step)
        self.assertIn("transcription_checklist.records_expected_text_file_name=false", next_step)
        self.assertEqual(report["next_real_transcription"]["uses_placeholders"], True)
        self.assertEqual(report["next_real_transcription"]["target_backend"]["name"], "whisper")
        self.assertFalse(report["next_real_transcription"]["records_audio_path"])
        self.assertFalse(report["next_real_transcription"]["records_audio_file_name"])
        self.assertFalse(report["transcription_checklist"]["ready_for_beta_evidence"])
        self.assertIn("Ready for beta evidence: False", checklist)

    def test_transcription_pilot_preflight_decision_blocks_without_duration_gate(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "private-meeting.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                audio=audio_path,
                backend="whisper",
                preflight_only=True,
                audio_confirmed_non_sensitive=True,
                sample_rate=8000,
            )
            findings = Path(report["artifacts"]["pilot_findings"]).read_text(encoding="utf-8")
            next_step = Path(report["artifacts"]["real_transcription_next_step"]).read_text(encoding="utf-8")

        self.assertTrue(report["passed"])
        self.assertFalse(report["audio"]["duration_gate"]["enabled"])
        self.assertEqual(report["preflight_decision"]["decision"], "blocked")
        self.assertIn("duration_gate_enabled", report["preflight_decision"]["blocking_reasons"])
        self.assertIn("Preflight decision: blocked", findings)
        self.assertIn("Preflight decision: blocked", next_step)

    def test_transcription_pilot_cli_preflight_allows_target_backend(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        str(Path(tmpdir) / "pilot"),
                        "--audio",
                        str(audio_path),
                        "--backend",
                        "whisper",
                        "--preflight-only",
                        "--audio-non-sensitive",
                        "--min-audio-seconds",
                        "0.05",
                        "--max-audio-seconds",
                        "1",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["preflight_only"])
        self.assertEqual(payload["target_backend"]["name"], "whisper")
        self.assertEqual(payload["target_backend"]["kind"], "transcription")
        self.assertIsInstance(payload["target_backend"]["available"], bool)
        self.assertIn("faster-whisper", payload["target_backend"]["dependencies"])
        self.assertEqual(payload["target_backend"]["install_command"], 'python -m pip install "auralisvoicekit[whisper]"')
        self.assertEqual(payload["target_backend"]["install_plan"]["extra"], "whisper")
        self.assertEqual(payload["next_real_transcription"]["target_backend"]["name"], "whisper")
        self.assertIn("post_install_check", payload["next_real_transcription"]["target_backend"]["install_plan"])
        self.assertTrue(payload["audio"]["decoded"])
        self.assertTrue(payload["audio"]["duration_gate"]["passed"])
        self.assertIsNone(payload["transcript"])

    def test_transcription_pilot_cli_can_require_target_backend_ready(self):
        module = _load_transcription_pilot()

        def unavailable_backend(backend: str) -> dict:
            return {
                "name": backend,
                "kind": "transcription",
                "available": False,
                "dependencies": ["faster-whisper"],
                "reason": "missing test dependency",
                "install_command": 'python -m pip install "auralisvoicekit[whisper]"',
                "install_plan": {
                    "pip_command": 'python -m pip install "auralisvoicekit[whisper]"',
                    "post_install_check": "python tools/transcription_pilot.py --preflight-only --audio <audio-path> --audio-non-sensitive --backend whisper --require-target-backend-ready --json",
                },
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "private-sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            original_status = module._transcription_backend_status
            module._transcription_backend_status = unavailable_backend
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    exit_code = module.main(
                        [
                            "--root",
                            str(ROOT),
                            "--output-dir",
                            str(Path(tmpdir) / "pilot"),
                            "--audio",
                            str(audio_path),
                            "--backend",
                            "whisper",
                            "--preflight-only",
                            "--audio-non-sensitive",
                            "--require-target-backend-ready",
                            "--sample-rate",
                            "8000",
                            "--json",
                        ]
                    )
            finally:
                module._transcription_backend_status = original_status
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("Transcription backend 'whisper' is not available", payload["error"])
        self.assertIn("faster-whisper", payload["error"])
        self.assertIn("missing test dependency", payload["error"])
        self.assertIn('python -m pip install "auralisvoicekit[whisper]"', payload["error"])
        self.assertNotIn(str(audio_path), payload["error"])
        self.assertNotIn("private-sample.wav", payload["error"])

    def test_transcription_backend_install_plan_supports_real_backends(self):
        module = _load_transcription_pilot()

        whisper = module._target_backend_install_plan("whisper", ["faster-whisper"])
        openai = module._target_backend_install_plan("openai", ["openai"])
        null_backend = module._target_backend_install_plan("null", [])

        self.assertEqual(whisper["pip_command"], 'python -m pip install "auralisvoicekit[whisper]"')
        self.assertEqual(openai["pip_command"], 'python -m pip install "auralisvoicekit[openai]"')
        self.assertIsNone(null_backend["pip_command"])
        self.assertTrue(whisper["keeps_base_package_light"])
        self.assertIn("Ubuntu/Linux", " ".join(whisper["platform_notes"]))
        self.assertIn("macOS", " ".join(openai["platform_notes"]))

    def test_transcription_pilot_cli_preflight_rejects_unknown_target_backend(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = module.main(
                    [
                        "--root",
                        str(ROOT),
                        "--output-dir",
                        str(Path(tmpdir) / "pilot"),
                        "--audio",
                        str(audio_path),
                        "--backend",
                        "missing",
                        "--preflight-only",
                        "--audio-non-sensitive",
                        "--sample-rate",
                        "8000",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertIn("Unknown transcription backend 'missing'", payload["error"])
        self.assertIn("Available: null, openai, whisper", payload["error"])

    def test_transcription_checklist_marks_beta_ready_real_quality(self):
        module = _load_transcription_pilot()

        checklist = module._transcription_checklist(
            backend="whisper",
            preflight_only=False,
            real_transcription=True,
            quality_review_confirmed=True,
            passed=True,
            audio={
                "generated_synthetic_audio": False,
                "audio_confirmed_non_sensitive": True,
                "audio_review_confirmed": True,
                "decoded": True,
                "duration_gate": {"enabled": True, "passed": True},
            },
            transcript={"text_redacted": True, "text_characters": 26},
            quality={
                "enabled": True,
                "passed": True,
                "min_word_accuracy": 0.75,
            },
            reference_privacy_scan=_reference_privacy_scan(),
            audio_review_confirmed=True,
            reference_review_confirmed=True,
        )
        markdown = module._build_transcription_checklist_markdown(
            timestamp="2026-06-05T00:00:00+00:00",
            backend="whisper",
            transcription_checklist=checklist,
        )

        self.assertTrue(checklist["ready_for_real_transcription"])
        self.assertTrue(checklist["ready_for_beta_evidence"])
        self.assertTrue(checklist["audio_review_confirmed"])
        self.assertTrue(checklist["reference_review_confirmed"])
        self.assertTrue(checklist["reference_privacy_scan_passed"])
        self.assertTrue(checklist["quality_review_confirmed"])
        self.assertFalse(checklist["records_audio_file_name"])
        self.assertFalse(checklist["records_transcript_text"])
        self.assertFalse(checklist["records_expected_text"])
        self.assertFalse(checklist["records_expected_text_file_name"])
        self.assertIn("Quality review confirmed: True", markdown)
        self.assertIn("Audio review confirmed: True", markdown)
        self.assertIn("Records audio file name: False", markdown)
        self.assertIn("Records expected text file name: False", markdown)
        self.assertIn("Reference review confirmed: True", markdown)
        self.assertIn("Reference privacy scan passed: True", markdown)
        self.assertIn("Ready for beta evidence: True", markdown)

    def test_transcription_checklist_requires_audio_review_confirmation_for_beta(self):
        module = _load_transcription_pilot()

        checklist = module._transcription_checklist(
            backend="whisper",
            preflight_only=False,
            real_transcription=True,
            quality_review_confirmed=True,
            passed=True,
            audio={
                "generated_synthetic_audio": False,
                "audio_confirmed_non_sensitive": True,
                "audio_review_confirmed": False,
                "decoded": True,
                "duration_gate": {"enabled": True, "passed": True},
            },
            transcript={"text_redacted": True, "text_characters": 26},
            quality={
                "enabled": True,
                "passed": True,
                "min_word_accuracy": 0.75,
            },
            reference_privacy_scan=_reference_privacy_scan(),
            audio_review_confirmed=False,
            reference_review_confirmed=True,
        )

        self.assertFalse(checklist["ready_for_real_transcription"])
        self.assertFalse(checklist["ready_for_beta_evidence"])
        self.assertFalse(checklist["audio_review_confirmed"])

    def test_transcription_checklist_requires_reference_review_confirmation_for_beta(self):
        module = _load_transcription_pilot()

        checklist = module._transcription_checklist(
            backend="whisper",
            preflight_only=False,
            real_transcription=True,
            quality_review_confirmed=True,
            passed=True,
            audio={
                "generated_synthetic_audio": False,
                "audio_confirmed_non_sensitive": True,
                "audio_review_confirmed": True,
                "reference_review_confirmed": False,
                "decoded": True,
                "duration_gate": {"enabled": True, "passed": True},
            },
            transcript={"text_redacted": True, "text_characters": 26},
            quality={
                "enabled": True,
                "passed": True,
                "min_word_accuracy": 0.75,
            },
            reference_privacy_scan=_reference_privacy_scan(),
            audio_review_confirmed=True,
            reference_review_confirmed=False,
        )

        self.assertTrue(checklist["ready_for_real_transcription"])
        self.assertFalse(checklist["ready_for_beta_evidence"])
        self.assertFalse(checklist["reference_review_confirmed"])

    def test_transcription_checklist_requires_reference_privacy_scan_for_beta(self):
        module = _load_transcription_pilot()

        checklist = module._transcription_checklist(
            backend="whisper",
            preflight_only=False,
            real_transcription=True,
            quality_review_confirmed=True,
            passed=True,
            audio={
                "generated_synthetic_audio": False,
                "audio_confirmed_non_sensitive": True,
                "audio_review_confirmed": True,
                "decoded": True,
                "duration_gate": {"enabled": True, "passed": True},
            },
            transcript={"text_redacted": True, "text_characters": 26},
            quality={
                "enabled": True,
                "passed": True,
                "min_word_accuracy": 0.75,
            },
            reference_privacy_scan=_reference_privacy_scan(passed=False),
            audio_review_confirmed=True,
            reference_review_confirmed=True,
        )

        self.assertTrue(checklist["ready_for_real_transcription"])
        self.assertFalse(checklist["ready_for_beta_evidence"])
        self.assertFalse(checklist["reference_privacy_scan_passed"])

    def test_transcription_checklist_requires_quality_review_confirmation_for_beta(self):
        module = _load_transcription_pilot()

        checklist = module._transcription_checklist(
            backend="whisper",
            preflight_only=False,
            real_transcription=True,
            passed=True,
            audio={
                "generated_synthetic_audio": False,
                "audio_confirmed_non_sensitive": True,
                "audio_review_confirmed": True,
                "decoded": True,
                "duration_gate": {"enabled": True, "passed": True},
            },
            transcript={"text_redacted": True, "text_characters": 26},
            quality={
                "enabled": True,
                "passed": True,
                "min_word_accuracy": 0.75,
            },
            reference_privacy_scan=_reference_privacy_scan(),
            audio_review_confirmed=True,
            reference_review_confirmed=True,
            quality_review_confirmed=False,
        )

        self.assertTrue(checklist["ready_for_real_transcription"])
        self.assertFalse(checklist["ready_for_beta_evidence"])
        self.assertFalse(checklist["quality_review_confirmed"])

    def test_transcription_pilot_rejects_quality_review_confirmation_without_real_transcription(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    quality_review_confirmed=True,
                )

    def test_transcription_pilot_rejects_audio_review_confirmation_without_audio_guard(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    audio="sample.wav",
                    audio_review_confirmed=True,
                )

    def test_transcription_pilot_rejects_reference_review_confirmation_without_reference_text(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=tmpdir,
                    reference_review_confirmed=True,
                )

    def test_transcription_pilot_preflight_rejects_quality_flags(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            with self.assertRaises(ValueError):
                module.run_transcription_pilot(
                    root=ROOT,
                    output_dir=Path(tmpdir) / "pilot",
                    audio=audio_path,
                    preflight_only=True,
                    audio_confirmed_non_sensitive=True,
                    expected_text="Hola",
                )

    def test_transcription_pilot_duration_gate_can_fail_preflight(self):
        module = _load_transcription_pilot()

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "sample.wav"
            write_wav(
                str(audio_path),
                [AudioChunk(data=b"\x00\x00" * 800, format=AudioFormat(sample_rate=8000, channels=1))],
            )
            report = module.run_transcription_pilot(
                root=ROOT,
                output_dir=Path(tmpdir) / "pilot",
                audio=audio_path,
                backend="whisper",
                preflight_only=True,
                audio_confirmed_non_sensitive=True,
                min_audio_seconds=1.0,
                sample_rate=8000,
            )
            findings = Path(report["artifacts"]["pilot_findings"]).read_text(encoding="utf-8")

        self.assertFalse(report["passed"])
        self.assertTrue(report["audio"]["decoded"])
        self.assertFalse(report["audio"]["duration_gate"]["passed"])
        self.assertEqual(report["audio"]["duration_gate"]["reason"], "below_minimum")
        self.assertIn("--min-audio-seconds", report["error"])
        self.assertIn("Duration gate passed: False", findings)

    def test_transcription_pilot_rejects_invalid_duration_limits(self):
        module = _load_transcription_pilot()

        with self.assertRaises(ValueError):
            module.run_transcription_pilot(root=ROOT, min_audio_seconds=2.0, max_audio_seconds=1.0)


if __name__ == "__main__":
    unittest.main()
