"""Beta readiness checklist for AuralisVoiceKit.

The report is intentionally conservative: the project can be ready for real
pilots while still blocked for a public beta until real-world evidence exists.
The default Markdown target is BETA_CHECKLIST.md. Use --evidence with
AuralisVoiceKit pilot JSON artifacts to close blockers without copying private
content into Markdown.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


BETA_MIN_WORD_ACCURACY = 0.75
CROSS_PLATFORM_CAPTURE_BACKENDS = ("sounddevice", "pyaudio")


def build_evidence_requirements_report() -> dict[str, Any]:
    """Build the public-safe contract for beta evidence JSON artifacts."""

    return {
        "project": "AuralisVoiceKit",
        "minimums": {
            "transcription_min_word_accuracy": BETA_MIN_WORD_ACCURACY,
        },
        "accepted_artifacts": [
            "manual-pilot-report.json",
            "output-pilot-report.json",
            "transcription-pilot-report.json",
        ],
        "requirements": [
            {
                "name": "windows_wasapi_capture",
                "title": "Windows WASAPI capture pilot",
                "artifact": "manual-pilot-report.json",
                "command": (
                    "python tools/manual_pilot.py --capture-test --backend wasapi "
                    "--device default --sample-rate 48000 --expected-system Windows "
                    "--confirm-input-reviewed --require-capture-backend-ready --json"
                ),
                "fields": [
                    _required_field("project", "AuralisVoiceKit"),
                    _required_field("system", "Windows"),
                    _required_field("system_guard.expected_system_matched", True),
                    _required_field("capture_backend", "wasapi"),
                    _required_field("target_capture_backend.available", True),
                    _required_field("capture_backend_ready_required", True),
                    _required_field("hardware_capture_tested", True),
                    _required_field("input_review_confirmed", True),
                    _required_field("capture_checklist.input_review_confirmed", True),
                    _required_field("capture_checklist.ready_for_beta_evidence", True),
                    *_manual_capture_command_card_required_fields("windows_wasapi_capture"),
                    _required_field("passed", True),
                ],
            },
            {
                "name": "real_transcription_quality",
                "title": "Real transcription quality pilot",
                "artifact": "transcription-pilot-report.json",
                "command": (
                    "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
                    "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
                    "--backend whisper --model base --normalize "
                    "--expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 "
                    "--min-audio-seconds 0.2 --max-audio-seconds 60 "
                    "--confirm-quality-reviewed --require-target-backend-ready --json"
                ),
                "fields": [
                    _required_field("project", "AuralisVoiceKit"),
                    _required_field("real_transcription_requested", True),
                    _required_field("target_backend.available", True),
                    _required_field("target_backend_ready_required", True),
                    _required_field("preflight_readiness.status", "ready"),
                    _required_field("preflight_readiness.decision", "ready_for_real_transcription"),
                    _required_field("preflight_readiness.ready_for_model_run", True),
                    _required_field("preflight_readiness.must_rerun_preflight", False),
                    _required_field("preflight_readiness.safe_to_share", True),
                    _required_field("preflight_readiness.usable_as_beta_evidence", False),
                    _required_field("preflight_readiness.records_audio", False),
                    _required_field("preflight_readiness.records_transcripts", False),
                    _required_field("preflight_readiness.records_expected_text", False),
                    _required_field("preflight_readiness.records_audio_file_name", False),
                    _required_field("preflight_readiness.records_local_paths", False),
                    _required_field("preflight_readiness.backend_ready", True),
                    _required_field("preflight_readiness.audio_decoded", True),
                    _required_field("preflight_readiness.duration_gate_enabled", True),
                    _required_field("preflight_readiness.duration_gate_passed", True),
                    _required_field("audio_confirmed_non_sensitive", True),
                    _required_field("audio.generated_synthetic_audio", False),
                    _required_field("audio.audio_confirmed_non_sensitive", True),
                    _required_field("audio.decoded", True),
                    _required_field("audio.audio_file_name_redacted", True),
                    _required_field("audio.duration_gate.enabled", True),
                    _required_field("audio.duration_gate.passed", True),
                    _required_field("audio_review_confirmed", True),
                    _required_field("reference_review_confirmed", True),
                    _required_field("reference_privacy_scan.passed", True),
                    _required_field("quality_review_confirmed", True),
                    _required_field("passed", True),
                    _required_field("transcript.text_redacted", True),
                    _required_field("quality.enabled", True),
                    _required_field("quality.passed", True),
                    _required_field("quality.min_word_accuracy", f">= {BETA_MIN_WORD_ACCURACY}"),
                    _required_field("transcription_checklist.audio_review_confirmed", True),
                    _required_field("transcription_checklist.records_audio_path", False),
                    _required_field("transcription_checklist.records_audio_file_name", False),
                    _required_field("transcription_checklist.records_transcript_text", False),
                    _required_field("transcription_checklist.records_expected_text", False),
                    _required_field("transcription_checklist.records_expected_text_file_name", False),
                    _required_field("transcription_checklist.redacts_transcript_text", True),
                    _required_field("transcription_checklist.redacts_expected_text", True),
                    _required_field("transcription_checklist.reference_review_confirmed", True),
                    _required_field("transcription_checklist.reference_privacy_scan_passed", True),
                    _required_field("transcription_checklist.quality_review_confirmed", True),
                    _required_field("transcription_checklist.ready_for_beta_evidence", True),
                ],
                "conditional_fields": [
                    {
                        "when": _required_field("target_backend.name", "openai"),
                        "fields": [
                            _required_field("credentials.checked", True),
                            _required_field("credentials.openai_api_key_required", True),
                            _required_field("credentials.openai_api_key_present", True),
                            _required_field("credentials.records_openai_api_key", False),
                        ],
                    }
                ],
            },
            {
                "name": "system_output_audible",
                "title": "Audible system output pilot",
                "artifact": "output-pilot-report.json",
                "command": (
                    "python tools/output_pilot.py --speak --operator-present "
                    "--confirm-audible --confirm-text-reviewed --confirm-voice-reviewed "
                    "--require-output-backend-ready "
                    "--expected-system \"Windows|Linux|Darwin\" "
                    "--output-dir pilot_runs/output/system-real "
                    "--text \"Hola desde AuralisVoiceKit\" --json"
                ),
                "fields": [
                    _required_field("project", "AuralisVoiceKit"),
                    _required_field("backend", "system"),
                    _required_field("system_guard.expected_system_matched", True),
                    _required_field("target_output_backend.available", True),
                    _required_field("output_backend_ready_required", True),
                    _required_field("real_audio_requested", True),
                    _required_field("operator_confirmation_status", "confirmed"),
                    _required_field("text_review_confirmed", True),
                    _required_field("spoken_text_privacy_scan.passed", True),
                    _required_field("voice_review_confirmed", True),
                    _required_field("operator_checklist.expected_system_matched", True),
                    _required_field("operator_checklist.records_operator_identity", False),
                    _required_field("operator_checklist.redacts_spoken_text", True),
                    _required_field("operator_checklist.text_review_confirmed", True),
                    _required_field("operator_checklist.spoken_text_privacy_scan_passed", True),
                    _required_field("operator_checklist.voice_review_confirmed", True),
                    _required_field("operator_checklist.commands_available", True),
                    _required_field("operator_checklist.ready_for_real_audio", True),
                    _required_field("operator_checklist.ready_for_beta_evidence", True),
                    _required_field("next_system_output.uses_placeholders", True),
                    _required_field("next_system_output.records_spoken_text", False),
                    _required_field("next_system_output.records_operator_identity", False),
                    _required_field("passed", True),
                ],
            },
            {
                "name": "ubuntu_linux_capture",
                "title": "Ubuntu/Linux capture pilot",
                "artifact": "manual-pilot-report.json",
                "command": (
                    "python tools/manual_pilot.py --capture-test --backend sounddevice "
                    "--device default --expected-system Linux --confirm-input-reviewed "
                    "--require-capture-backend-ready --json"
                ),
                "notes": "If PyAudio is the installed capture stack, use --backend pyaudio with the same flags.",
                "fields": [
                    _required_field("project", "AuralisVoiceKit"),
                    _required_field("system", "Linux | Ubuntu/Linux | Ubuntu"),
                    _required_field("system_guard.expected_system_matched", True),
                    _required_field("capture_backend", "sounddevice | pyaudio"),
                    _required_field("target_capture_backend.available", True),
                    _required_field("capture_backend_ready_required", True),
                    _required_field("hardware_capture_tested", True),
                    _required_field("input_review_confirmed", True),
                    _required_field("capture_checklist.input_review_confirmed", True),
                    _required_field("capture_checklist.ready_for_beta_evidence", True),
                    *_manual_capture_command_card_required_fields("ubuntu_linux_capture"),
                    _required_field("passed", True),
                ],
            },
            {
                "name": "macos_capture",
                "title": "macOS capture pilot",
                "artifact": "manual-pilot-report.json",
                "command": (
                    "python tools/manual_pilot.py --capture-test --backend sounddevice "
                    "--device default --expected-system Darwin --confirm-input-reviewed "
                    "--require-capture-backend-ready --json"
                ),
                "notes": "If PyAudio is the installed capture stack, use --backend pyaudio with the same flags.",
                "fields": [
                    _required_field("project", "AuralisVoiceKit"),
                    _required_field("system", "Darwin | macOS | Mac"),
                    _required_field("system_guard.expected_system_matched", True),
                    _required_field("capture_backend", "sounddevice | pyaudio"),
                    _required_field("target_capture_backend.available", True),
                    _required_field("capture_backend_ready_required", True),
                    _required_field("hardware_capture_tested", True),
                    _required_field("input_review_confirmed", True),
                    _required_field("capture_checklist.input_review_confirmed", True),
                    _required_field("capture_checklist.ready_for_beta_evidence", True),
                    *_manual_capture_command_card_required_fields("macos_capture"),
                    _required_field("passed", True),
                ],
            },
        ],
        "privacy": [
            "No audio bytes are required in beta evidence.",
            "No full transcript or expected text is required in beta readiness evidence.",
            "User audio file names and expected-text file names must be redacted.",
            "OpenAI evidence records credential presence only, never the API key value.",
            "Reference privacy scans expose only pass/fail, risk counts and risk types.",
            "Spoken text privacy scans expose only pass/fail, risk counts and risk types.",
            "Manual capture command cards must use placeholders and must not record audio, device names or local paths.",
            "Only structured fields and sanitized artifact names are used.",
        ],
    }


def build_evidence_audit_report(
    root: str | Path = ".",
    evidence_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Audit pilot evidence against beta requirements without exposing private content."""

    workspace = Path(root).resolve()
    evidence = _load_evidence_reports(workspace, evidence_paths or [])
    requirements = build_evidence_requirements_report()["requirements"]
    accepted_reports = evidence["accepted"]
    artifacts = []
    for report in accepted_reports:
        evidence_path = Path(report["_evidence_path"])
        candidate_requirements = [item for item in requirements if item["artifact"] == evidence_path.name]
        candidates = [_audit_requirement(report, requirement) for requirement in candidate_requirements]
        artifacts.append(
            {
                "file": _public_evidence_source(report),
                "artifact": evidence_path.name,
                "satisfied_blockers": [candidate["name"] for candidate in candidates if candidate["ok"]],
                "candidate_count": len(candidates),
                "candidates": candidates,
            }
        )
    blocker_summaries = _evidence_blocker_summaries(requirements, artifacts)
    required_blockers = [requirement["name"] for requirement in requirements]
    satisfied_blockers = _ordered_unique(
        blocker for artifact in artifacts for blocker in artifact["satisfied_blockers"]
    )
    missing_blockers = [blocker for blocker in required_blockers if blocker not in satisfied_blockers]
    focus_blockers = missing_blockers
    active_beta_blockers = [
        blocker
        for blocker in build_beta_readiness_report(workspace, evidence_paths=evidence_paths or [])["blockers"]
        if blocker in missing_blockers
    ]
    if active_beta_blockers:
        focus_blockers = active_beta_blockers
    next_evidence_focus = _next_evidence_focus(requirements, blocker_summaries, focus_blockers)

    return {
        "project": "AuralisVoiceKit",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "accepted_count": len(accepted_reports),
        "accepted_details": [
            {
                "file": _public_evidence_source(report),
                "artifact": Path(report["_evidence_path"]).name,
            }
            for report in accepted_reports
        ],
        "ignored_count": len(evidence["ignored"]),
        "ignored_details": evidence["ignored"],
        "required_blockers": required_blockers,
        "satisfied_blockers": satisfied_blockers,
        "missing_blockers": missing_blockers,
        "blocker_summaries": blocker_summaries,
        "next_evidence_focus": next_evidence_focus,
        "ready_for_beta_by_evidence": not missing_blockers,
        "artifacts": artifacts,
        "notes": (
            "Evidence audit uses only structured fields needed for beta blockers. "
            "It does not require audio, transcripts, expected text or full local paths. "
            "It audits JSON evidence only; existing PILOT_FINDINGS.md text is not counted here."
        ),
    }


def build_beta_readiness_report(
    root: str | Path = ".",
    evidence_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Build a deterministic report with beta blockers and known issues."""

    workspace = Path(root).resolve()
    gate = _load_stability_gate(workspace).build_report(workspace)
    findings = _read_text(workspace / "PILOT_FINDINGS.md")
    evidence = _load_evidence_reports(workspace, evidence_paths or [])
    evidence_reports = evidence["accepted"]
    checks = [
        _gate_check(gate),
        _evidence_or_terms_check(
            name="windows_wasapi_capture",
            title="Windows WASAPI capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_windows_wasapi_capture_evidence,
            required_terms=(
                "Windows WASAPI captura real a 48000 Hz",
                "Piloto manual: `passed=true`",
                "Check `capture-test:wasapi`: `ok`",
                "Expected system matched: True",
                "Target capture backend available: True",
                "Capture backend readiness required: True",
                "Input review confirmed: True",
                "Manual capture command: manual-capture-command.md",
            ),
            next_action=(
                "Repeat the Windows WASAPI pilot with --sample-rate 48000, --expected-system Windows, "
                "--confirm-input-reviewed and --require-capture-backend-ready after checking permissions, "
                "input device and room privacy, then keep manual-capture-checklist.md, "
                "manual-capture-command.md and only sanitized findings."
            ),
        ),
        _evidence_or_terms_check(
            name="real_transcription_quality",
            title="Real transcription quality pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_real_transcription_quality_evidence,
            required_terms=(
                "Real transcription requested: True",
                "Target backend available: True",
                "Target backend readiness required: True",
                "Generated synthetic audio: False",
                "Audio decode passed: True",
                "Audio duration gate enabled: True",
                "Audio duration gate passed: True",
                "Transcript text redacted: True",
                "Audio review confirmed: True",
                "Reference review confirmed: True",
                "Reference privacy scan passed: True",
                "Quality gate passed: `true`",
                "Quality review confirmed: True",
                "Transcription checklist ready for beta evidence: True",
            ),
            next_action=(
                "Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, "
                "--expected-text or --expected-text-file, a meaningful --min-word-accuracy, "
                "--min-audio-seconds/--max-audio-seconds duration guards and "
                "--confirm-audio-reviewed before model use plus --confirm-reference-reviewed before scoring "
                "with reference_privacy_scan.passed=true, "
                "preflight_decision.decision=ready_for_real_transcription or a repeated preflight after backend install, "
                "preflight_readiness.status=ready, preflight_readiness.ready_for_model_run=true, "
                "preflight_readiness.must_rerun_preflight=false and public-safe preflight_readiness redaction flags, "
                "--require-target-backend-ready before model execution, "
                "--timeout-seconds 30 when using --backend openai, "
                "--require-openai-api-key when using --backend openai, "
                "and --confirm-quality-reviewed after human review, "
                "then keep target_backend.available=true, target_backend_ready_required=true, "
                "credentials.checked=true, credentials.openai_api_key_required=true, "
                "credentials.openai_api_key_present=true and credentials.records_openai_api_key=false for OpenAI, "
                "transcription-review-checklist.md and real-transcription-next-step.md."
            ),
        ),
        _evidence_or_terms_check(
            name="system_output_audible",
            title="Audible system output pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_system_output_audible_evidence,
            required_terms=(
                "Real audio requested: True",
                "Output backend readiness required: True",
                "Operator confirmation status: confirmed",
                "Text review confirmed: True",
                "Spoken text privacy scan passed: True",
                "Voice review confirmed: True",
                "Records operator identity: False",
                "Redacts spoken text: True",
                "Commands available: True",
                "Ready for real audio: True",
                "Operator checklist ready for beta evidence: True",
            ),
            next_action=(
                "Run tools/output_pilot.py --speak --operator-present --confirm-audible "
                "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
                "--expected-system \"Windows|Linux|Darwin\" "
                "--output-dir pilot_runs/output/system-real with a human operator, then keep "
                "output-operator-checklist.md, system-output-next-step.md, "
                "system_guard.expected_system_matched=true, "
                "target_output_backend.available=true, output_backend_ready_required=true, "
                "operator_checklist.expected_system_matched=true, "
                "spoken_text_privacy_scan.passed=true, "
                "operator_checklist.redacts_spoken_text=true, "
                "operator_checklist.records_operator_identity=false, "
                "operator_checklist.commands_available=true, "
                "operator_checklist.ready_for_real_audio=true, "
                "next_system_output.records_spoken_text=false "
                "and only sanitized findings."
            ),
        ),
        _evidence_or_terms_check(
            name="ubuntu_linux_capture",
            title="Ubuntu/Linux capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_ubuntu_linux_capture_evidence,
            required_terms=(
                "Sistema: Ubuntu/Linux",
                "Piloto manual: `passed=true`",
                "Target capture backend available: True",
                "Capture backend readiness required: True",
            ),
            next_action=(
                "Run the manual capture pilot on Ubuntu/Linux with real hardware and "
                "--backend sounddevice or --backend pyaudio, --expected-system Linux "
                "--confirm-input-reviewed and --require-capture-backend-ready, then keep "
                "manual-capture-checklist.md, manual-capture-command.md, "
                "system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, "
                "target_capture_backend.available=true, capture_backend_ready_required=true, "
                "input_review_confirmed=true, "
                "capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true "
                "and manual_capture_command_card safe-to-share redaction flags."
            ),
        ),
        _evidence_or_terms_check(
            name="macos_capture",
            title="macOS capture pilot",
            blocker=True,
            content=findings,
            evidence_reports=evidence_reports,
            evidence_predicate=_is_macos_capture_evidence,
            required_terms=(
                "Sistema: macOS",
                "Piloto manual: `passed=true`",
                "Target capture backend available: True",
                "Capture backend readiness required: True",
            ),
            next_action=(
                "Run the manual capture pilot on macOS with real hardware and --backend sounddevice "
                "or --backend pyaudio, --expected-system Darwin --confirm-input-reviewed and "
                "--require-capture-backend-ready, then keep "
                "manual-capture-checklist.md, manual-capture-command.md, "
                "system_guard.expected_system_matched=true, "
                "capture_backend=sounddevice|pyaudio, target_capture_backend.available=true, "
                "capture_backend_ready_required=true, input_review_confirmed=true, "
                "capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true "
                "and manual_capture_command_card safe-to-share redaction flags."
            ),
        ),
    ]
    blockers = [check for check in checks if check["blocker"] and not check["ok"]]
    known_issues = _known_issues(findings)
    ready_for_beta = not blockers

    return {
        "project": "AuralisVoiceKit",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "version": gate["version"],
        "status": "beta-ready" if ready_for_beta else "pilot",
        "ready_for_beta": ready_for_beta,
        "gate": {
            "stage": gate["stage"],
            "ready_for_real_world_pilots": gate["ready_for_real_world_pilots"],
            "ready_for_stable_release": gate["ready_for_stable_release"],
            "stable_blockers": gate["stable_blockers"],
        },
        "checks": checks,
        "blockers": [check["name"] for check in blockers],
        "evidence": {
            "files": [_public_evidence_source(report) for report in evidence_reports],
            "accepted_details": [
                {
                    "file": _public_evidence_source(report),
                    "artifact": Path(report["_evidence_path"]).name,
                }
                for report in evidence_reports
            ],
            "count": len(evidence_reports),
            "ignored_files": [item["file"] for item in evidence["ignored"]],
            "ignored_details": evidence["ignored"],
            "ignored_count": len(evidence["ignored"]),
        },
        "known_issues": known_issues,
        "next_actions": [check["next_action"] for check in checks if not check["ok"]],
        "notes": (
            "Beta requires documented real-world evidence. Dry-runs prove safety paths, "
            "but they do not replace real transcription, audible output or cross-platform capture pilots."
        ),
    }


def write_beta_readiness_report(report: dict[str, Any], output: str | Path) -> None:
    """Write JSON or Markdown depending on the output extension."""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        output_path.write_text(format_markdown(report), encoding="utf-8")


def write_evidence_requirements_report(report: dict[str, Any], output: str | Path) -> None:
    """Write beta evidence requirements as JSON or Markdown."""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        output_path.write_text(format_requirements_markdown(report), encoding="utf-8")


def write_evidence_audit_report(report: dict[str, Any], output: str | Path) -> None:
    """Write beta evidence audit as JSON or Markdown."""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        output_path.write_text(format_audit_markdown(report), encoding="utf-8")


def format_audit_markdown(report: dict[str, Any]) -> str:
    """Format an evidence audit without private pilot content."""

    lines = [
        "# Auditoria de evidencias beta",
        "",
        "Este reporte valida artifacts JSON contra los requisitos de beta. No muestra audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Estado",
        "",
        f"- Evidencias aceptadas: `{report['accepted_count']}`",
        f"- Evidencias ignoradas: `{report['ignored_count']}`",
        f"- Listo para beta segun evidencias JSON: `{str(report['ready_for_beta_by_evidence']).lower()}`",
        "",
        "## Resumen de blockers",
        "",
        "- Cerrados por evidencias JSON: "
        + (_format_name_list(report["satisfied_blockers"]) if report["satisfied_blockers"] else "`ninguno`"),
        "- Pendientes segun evidencias JSON: "
        + (_format_name_list(report["missing_blockers"]) if report["missing_blockers"] else "`ninguno`"),
        "",
    ]
    if report["ignored_details"]:
        lines.extend(["## Evidencias ignoradas", ""])
        for item in report["ignored_details"]:
            lines.append(f"- `{item['file']}`: {item['message_es']} / {item['message_en']}.")
        lines.append("")
    lines.extend(["## Resumen por blocker", ""])
    for blocker in report["blocker_summaries"]:
        accepted_sources = _format_name_list(blocker["accepted_sources"]) if blocker["accepted_sources"] else "`ninguna`"
        closest = blocker.get("closest_candidate")
        lines.append(f"### {blocker['name']}")
        lines.append("")
        lines.append(f"- Estado: `{blocker['status']}`")
        lines.append(f"- Artifact esperado: `{blocker['artifact']}`")
        lines.append(f"- Fuentes que cierran: {accepted_sources}")
        lines.append(f"- Candidatos evaluados: `{blocker['candidate_count']}`")
        if closest is None:
            lines.append("- Candidato mas cercano: `ninguno`")
        else:
            missing_fields = (
                _format_name_list(closest["missing_fields"]) if closest["missing_fields"] else "`ninguno`"
            )
            lines.append(f"- Candidato mas cercano: `{closest['file']}`")
            lines.append(f"- Campos faltantes del candidato mas cercano: {missing_fields}")
        lines.append("")
    lines.extend(["## Siguiente foco de evidencia", ""])
    _append_next_evidence_focus_lines(lines, report.get("next_evidence_focus", {}))
    lines.extend(["## Evidencias aceptadas", ""])
    if not report["artifacts"]:
        lines.append("- Ninguna.")
        lines.append("")
    for artifact in report["artifacts"]:
        satisfied = ", ".join(f"`{name}`" for name in artifact["satisfied_blockers"]) or "`ninguno`"
        lines.append(f"### {artifact['file']}")
        lines.append("")
        lines.append(f"- Artifact: `{artifact['artifact']}`")
        lines.append(f"- Blockers cerrados: {satisfied}")
        lines.append("")
        for candidate in artifact["candidates"]:
            marker = "x" if candidate["ok"] else " "
            lines.append(f"- [{marker}] `{candidate['name']}`")
            for field in candidate["fields"]:
                field_marker = "x" if field["ok"] else " "
                lines.append(
                    f"  - [{field_marker}] `{field['path']}` esperado `{field['expected']}`, actual `{field['actual']}`"
                )
        lines.append("")
    lines.extend(["## Nota", "", f"- {report['notes']}", ""])
    return "\n".join(lines)


def format_requirements_markdown(report: dict[str, Any]) -> str:
    """Format required evidence fields without private pilot content."""

    lines = [
        "# Requisitos de evidencias beta",
        "",
        "Este documento describe los campos JSON que pueden cerrar blockers de beta. No requiere audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Artifacts aceptados",
        "",
    ]
    for artifact in report["accepted_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(
        [
            "",
            "## Requisitos por blocker",
            "",
        ]
    )
    for requirement in report["requirements"]:
        lines.append(f"### {requirement['name']}")
        lines.append("")
        lines.append(f"- Artifact: `{requirement['artifact']}`")
        lines.append(f"- Comando sugerido: `{requirement['command']}`")
        if requirement.get("notes"):
            lines.append(f"- Nota: {requirement['notes']}")
        lines.append("- Campos requeridos:")
        for field in requirement["fields"]:
            lines.append(f"  - `{field['path']}` = `{field['expected']}`")
        if requirement.get("conditional_fields"):
            lines.append("- Campos condicionales:")
            for conditional in requirement["conditional_fields"]:
                condition = conditional["when"]
                lines.append(f"  - Si `{condition['path']}` = `{condition['expected']}`:")
                for field in conditional["fields"]:
                    lines.append(f"    - `{field['path']}` = `{field['expected']}`")
        lines.append("")
    lines.extend(
        [
            "## Privacidad",
            "",
        ]
    )
    for note in report["privacy"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def format_markdown(report: dict[str, Any]) -> str:
    """Format a report as a public-safe Markdown checklist."""

    lines = [
        "# Checklist de beta",
        "",
        "Este documento se genera con `tools\\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Estado: `{report['status']}`",
        f"- Listo para beta: `{str(report['ready_for_beta']).lower()}`",
        f"- Gate de pilotos reales: `{str(report['gate']['ready_for_real_world_pilots']).lower()}`",
        f"- Evidencias JSON: `{report['evidence']['count']}`",
        f"- Evidencias ignoradas: `{report['evidence']['ignored_count']}`",
        "",
        "## Bloqueadores para beta",
        "",
    ]
    accepted_details = report["evidence"].get("accepted_details", [])
    ignored_details = report["evidence"].get("ignored_details", [])
    if accepted_details or ignored_details:
        lines = lines[:-2]
        if accepted_details:
            lines.extend(
                [
                    "## Evidencias aceptadas",
                    "",
                ]
            )
            for item in accepted_details:
                lines.append(f"- `{item['file']}` (`{item['artifact']}`)")
            lines.append("")
        lines.extend(
            [
                "## Evidencias ignoradas",
                "",
            ]
        )
        if ignored_details:
            for item in ignored_details:
                lines.append(f"- `{item['file']}`: {item['message_es']} / {item['message_en']}.")
        else:
            lines.append("- Ninguna.")
        lines.extend(
            [
                "",
                "## Bloqueadores para beta",
                "",
            ]
        )
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- Ninguno.")

    lines.extend(
        [
            "",
            "## Checklist",
            "",
        ]
    )
    for check in report["checks"]:
        marker = "x" if check["ok"] else " "
        blocker_label = "blocker" if check["blocker"] else "informativo"
        lines.append(f"- [{marker}] `{check['name']}` ({blocker_label}) - {check['title']}")
        if not check["ok"]:
            lines.append(f"  - Accion: {check['next_action']}")
            if check["missing_terms"]:
                terms = ", ".join(_format_missing_term(term) for term in check["missing_terms"])
                lines.append(f"  - Evidencia faltante: {terms}")
        if check["evidence_sources"]:
            sources = ", ".join(f"`{source}`" for source in check["evidence_sources"])
            lines.append(f"  - Evidencia JSON: {sources}")

    lines.extend(
        [
            "",
            "## Bugs conocidos",
            "",
        ]
    )
    if report["known_issues"]:
        for issue in report["known_issues"]:
            lines.append(f"- `{issue['id']}`: {issue['status']} - {issue['summary']}")
    else:
        lines.append("- No hay bugs criticos documentados; los blockers actuales son pilotos pendientes.")

    lines.extend(
        [
            "",
            "## Siguientes acciones",
            "",
        ]
    )
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the AuralisVoiceKit beta readiness checklist.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output", help="write report to .md or .json, for example BETA_CHECKLIST.md")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="AuralisVoiceKit pilot JSON evidence file or directory; can be passed more than once",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="exit with code 1 when beta blockers remain",
    )
    parser.add_argument(
        "--requirements",
        action="store_true",
        help="print beta evidence requirements instead of readiness status",
    )
    parser.add_argument(
        "--audit-evidence",
        action="store_true",
        help="audit --evidence artifacts against beta requirements instead of readiness status",
    )
    parser.add_argument(
        "--fail-on-audit-gaps",
        action="store_true",
        help="exit with code 1 when --audit-evidence has missing blockers or ignored artifacts",
    )
    args = parser.parse_args(argv)

    if args.requirements:
        report = build_evidence_requirements_report()
        if args.output:
            write_evidence_requirements_report(report, args.output)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        elif not args.output:
            print(format_requirements_markdown(report))
        return 0

    if args.audit_evidence:
        report = build_evidence_audit_report(args.root, evidence_paths=args.evidence)
        if args.output:
            write_evidence_audit_report(report, args.output)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        elif not args.output:
            print(format_audit_markdown(report))
        if args.fail_on_audit_gaps and (report["missing_blockers"] or report["ignored_count"]):
            return 1
        return 0

    report = build_beta_readiness_report(args.root, evidence_paths=args.evidence)
    if args.output:
        write_beta_readiness_report(report, args.output)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.output:
        print(format_markdown(report))

    if args.fail_on_blockers and not report["ready_for_beta"]:
        return 1
    return 0


def _load_stability_gate(workspace: Path):
    path = workspace / "tools" / "stability_gate.py"
    spec = importlib.util.spec_from_file_location("auralis_stability_gate_for_beta", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load stability gate from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _gate_check(gate: dict[str, Any]) -> dict[str, Any]:
    ok = bool(gate["ready_for_real_world_pilots"])
    return {
        "name": "stability_gate_pilot",
        "title": "Stability gate allows real-world pilots",
        "ok": ok,
        "blocker": True,
        "missing_terms": [] if ok else ["ready_for_real_world_pilots"],
        "evidence_sources": [],
        "next_action": "Run tools/stability_gate.py --min-stage pilot and fix any missing checks.",
    }


def _terms_check(
    *,
    name: str,
    title: str,
    blocker: bool,
    content: str,
    required_terms: tuple[str, ...],
    next_action: str,
) -> dict[str, Any]:
    missing_terms = [term for term in required_terms if term not in content]
    return {
        "name": name,
        "title": title,
        "ok": not missing_terms,
        "blocker": blocker,
        "missing_terms": missing_terms,
        "evidence_sources": [],
        "next_action": next_action,
    }


def _evidence_or_terms_check(
    *,
    name: str,
    title: str,
    blocker: bool,
    content: str,
    evidence_reports: list[dict[str, Any]],
    evidence_predicate,
    required_terms: tuple[str, ...],
    next_action: str,
) -> dict[str, Any]:
    evidence_sources = [
        _public_evidence_source(report) for report in evidence_reports if evidence_predicate(report)
    ]
    if evidence_sources:
        return {
            "name": name,
            "title": title,
            "ok": True,
            "blocker": blocker,
            "missing_terms": [],
            "evidence_sources": evidence_sources,
            "next_action": next_action,
        }
    return _terms_check(
        name=name,
        title=title,
        blocker=blocker,
        content=content,
        required_terms=required_terms,
        next_action=next_action,
    )


def _load_evidence_reports(workspace: Path, evidence_paths: list[str | Path]) -> dict[str, Any]:
    accepted = []
    ignored = []
    for evidence_path in evidence_paths:
        path = Path(evidence_path)
        if not path.is_absolute():
            path = workspace / path
        for report_path in _expand_evidence_path(path):
            public_source = _public_evidence_source_for_input(report_path, path)
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid evidence JSON: {report_path.name}") from exc
            if not isinstance(payload, dict):
                ignored.append(_ignored_evidence(public_source, "not_json_object"))
                continue
            payload = dict(payload)
            payload["_evidence_path"] = str(report_path)
            payload["_evidence_source"] = public_source
            project = payload.get("project")
            if project == "AuralisVoiceKit":
                accepted.append(payload)
            elif project is None:
                ignored.append(_ignored_evidence(public_source, "missing_project"))
            else:
                ignored.append(_ignored_evidence(public_source, "wrong_project"))
    return {"accepted": accepted, "ignored": ignored}


def _required_field(path: str, expected: Any) -> dict[str, Any]:
    return {"path": path, "expected": expected}


def _manual_capture_command_card_required_fields(blocker: str) -> list[dict[str, Any]]:
    return [
        _required_field("manual_capture_command_card.artifact", "manual-capture-command.md"),
        _required_field("manual_capture_command_card.blocker", blocker),
        _required_field("manual_capture_command_card.ready_for_beta_evidence", True),
        _required_field("manual_capture_command_card.safe_to_share", True),
        _required_field("manual_capture_command_card.uses_placeholders", True),
        _required_field("manual_capture_command_card.preflight_uses_microphone", False),
        _required_field("manual_capture_command_card.real_capture_requires_microphone", True),
        _required_field("manual_capture_command_card.records_audio", False),
        _required_field("manual_capture_command_card.records_audio_bytes", False),
        _required_field("manual_capture_command_card.records_device_name", False),
        _required_field("manual_capture_command_card.records_local_paths", False),
    ]


def _audit_requirement(report: dict[str, Any], requirement: dict[str, Any]) -> dict[str, Any]:
    required_fields = list(requirement["fields"]) + _applicable_conditional_fields(report, requirement)
    fields = [_audit_field(report, field) for field in required_fields]
    return {
        "name": requirement["name"],
        "title": requirement["title"],
        "ok": all(field["ok"] for field in fields),
        "fields": fields,
    }


def _evidence_blocker_summaries(
    requirements: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for requirement in requirements:
        candidates = []
        for artifact in artifacts:
            for candidate in artifact["candidates"]:
                if candidate["name"] != requirement["name"]:
                    continue
                missing_fields = [field["path"] for field in candidate["fields"] if not field["ok"]]
                candidates.append(
                    {
                        "file": artifact["file"],
                        "artifact": artifact["artifact"],
                        "ok": candidate["ok"],
                        "missing_count": len(missing_fields),
                        "missing_fields": missing_fields,
                    }
                )
        accepted_sources = [candidate["file"] for candidate in candidates if candidate["ok"]]
        closest = min(candidates, key=lambda candidate: candidate["missing_count"]) if candidates else None
        summaries.append(
            {
                "name": requirement["name"],
                "title": requirement["title"],
                "artifact": requirement["artifact"],
                "status": "closed" if accepted_sources else "pending",
                "accepted_sources": accepted_sources,
                "candidate_count": len(candidates),
                "closest_candidate": closest,
            }
        )
    return summaries


def _next_evidence_focus(
    requirements: list[dict[str, Any]],
    blocker_summaries: list[dict[str, Any]],
    missing_blockers: list[str],
) -> dict[str, Any]:
    """Choose the next beta evidence blocker to close with public-safe details."""

    if not missing_blockers:
        return {
            "status": "complete",
            "name": None,
            "title": None,
            "artifact": None,
            "command": None,
            "candidate_count": 0,
            "closest_candidate": None,
            "missing_fields": [],
            "required_fields": [],
            "conditional_required_fields": [],
            "reason_es": "Todas las evidencias JSON requeridas para beta estan cerradas.",
            "reason_en": "All JSON evidence required for beta is closed.",
        }

    requirements_by_name = {requirement["name"]: requirement for requirement in requirements}
    summary_by_name = {summary["name"]: summary for summary in blocker_summaries}
    missing_order = {name: index for index, name in enumerate(missing_blockers)}
    pending_summaries = [
        summary_by_name[name]
        for name in missing_blockers
        if name in summary_by_name and summary_by_name[name].get("status") != "closed"
    ]
    if not pending_summaries:
        pending_summaries = [
            summary
            for summary in blocker_summaries
            if summary["name"] in missing_order and summary.get("status") != "closed"
        ]
    selected = pending_summaries[0]

    requirement = requirements_by_name[selected["name"]]
    closest = selected.get("closest_candidate")
    required_fields = [field["path"] for field in requirement["fields"]]
    missing_fields = closest["missing_fields"] if closest is not None else required_fields
    return {
        "status": "pending",
        "name": selected["name"],
        "title": selected["title"],
        "artifact": selected["artifact"],
        "command": requirement["command"],
        "candidate_count": selected["candidate_count"],
        "closest_candidate": closest,
        "missing_fields": missing_fields,
        "required_fields": required_fields,
        "conditional_required_fields": _conditional_required_fields_for_focus(requirement),
        "reason_es": (
            "Prioriza el primer blocker pendiente del checklist beta activo "
            "y muestra su candidato mas cercano cuando existe."
        ),
        "reason_en": (
            "Prioritizes the first pending blocker from the active beta checklist "
            "and shows its closest candidate when available."
        ),
    }


def _conditional_required_fields_for_focus(requirement: dict[str, Any]) -> list[dict[str, Any]]:
    conditional_fields: list[dict[str, Any]] = []
    for conditional in requirement.get("conditional_fields", []):
        condition = conditional["when"]
        conditional_fields.append(
            {
                "when": {
                    "path": condition["path"],
                    "expected": condition["expected"],
                },
                "fields": [field["path"] for field in conditional["fields"]],
            }
        )
    return conditional_fields


def _applicable_conditional_fields(report: dict[str, Any], requirement: dict[str, Any]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for conditional in requirement.get("conditional_fields", []):
        condition = conditional["when"]
        found, actual = _get_nested_value(report, condition["path"])
        if found and _field_matches(actual, condition["expected"]):
            fields.extend(conditional["fields"])
    return fields


def _audit_field(report: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    found, actual = _get_nested_value(report, field["path"])
    expected = field["expected"]
    return {
        "path": field["path"],
        "expected": expected,
        "actual": _public_field_value(actual) if found else "<missing>",
        "ok": found and _field_matches(actual, expected),
    }


def _get_nested_value(payload: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    value: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _field_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, str) and expected.startswith(">= "):
        try:
            return float(actual) >= float(expected.removeprefix(">= ").strip())
        except (TypeError, ValueError):
            return False
    if isinstance(expected, str) and " | " in expected:
        choices = {choice.strip().lower() for choice in expected.split("|")}
        return str(actual).strip().lower() in choices
    return actual == expected


def _public_field_value(value: Any) -> Any:
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, str):
        return value if len(value) <= 80 else "<redacted>"
    return "<redacted>"


def _ordered_unique(values) -> list[str]:
    seen = set()
    unique = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _format_name_list(names: list[str]) -> str:
    return ", ".join(f"`{name}`" for name in names)


def _append_next_evidence_focus_lines(lines: list[str], focus: dict[str, Any]) -> None:
    if not focus:
        lines.extend(["- No hay foco de evidencia disponible.", ""])
        return
    lines.append(f"- Estado: `{focus['status']}`")
    if focus["status"] == "complete":
        lines.append(f"- Motivo: {focus['reason_es']} / {focus['reason_en']}.")
        lines.append("")
        return
    closest = focus.get("closest_candidate")
    missing_fields = _format_name_list(focus.get("missing_fields", [])) if focus.get("missing_fields") else "`ninguno`"
    required_fields = _format_name_list(focus.get("required_fields", [])) if focus.get("required_fields") else "`ninguno`"
    lines.extend(
        [
            f"- Blocker: `{focus['name']}`",
            f"- Titulo: {focus['title']}",
            f"- Artifact esperado: `{focus['artifact']}`",
            f"- Comando base: `{focus['command']}`",
            f"- Candidatos evaluados: `{focus['candidate_count']}`",
            f"- Campos faltantes a cerrar: {missing_fields}",
            f"- Campos requeridos base: {required_fields}",
        ]
    )
    if closest is None:
        lines.append("- Candidato mas cercano: `ninguno`")
    else:
        lines.append(f"- Candidato mas cercano: `{closest['file']}`")
    conditional_fields = focus.get("conditional_required_fields") or []
    if conditional_fields:
        lines.append("- Campos condicionales:")
        for item in conditional_fields:
            condition = item["when"]
            fields = _format_name_list(item["fields"]) if item["fields"] else "`ninguno`"
            lines.append(f"  - Si `{condition['path']}` = `{condition['expected']}`: {fields}")
    lines.append(f"- Motivo: {focus['reason_es']} / {focus['reason_en']}.")
    lines.append("")


def _ignored_evidence(public_source: str, reason: str) -> dict[str, str]:
    messages = {
        "missing_project": {
            "message_es": "falta `project: AuralisVoiceKit`",
            "message_en": "missing `project: AuralisVoiceKit`",
        },
        "wrong_project": {
            "message_es": "declara otro proyecto",
            "message_en": "declares a different project",
        },
        "not_json_object": {
            "message_es": "la raiz JSON no es un objeto",
            "message_en": "JSON root is not an object",
        },
    }
    detail = messages[reason]
    return {
        "file": public_source,
        "reason": reason,
        "message_es": detail["message_es"],
        "message_en": detail["message_en"],
    }


def _expand_evidence_path(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(item for item in path.rglob("*.json") if _looks_like_pilot_report(item))
    if not path.exists():
        raise ValueError(f"Evidence path was not found: {path.name}")
    return [path]


def _looks_like_pilot_report(path: Path) -> bool:
    return path.name in {
        "manual-pilot-report.json",
        "output-pilot-report.json",
        "transcription-pilot-report.json",
    }


def _public_evidence_source(report: dict[str, Any]) -> str:
    source = report.get("_evidence_source")
    if isinstance(source, str) and source:
        return source
    return _safe_evidence_source(str(report.get("_evidence_path", "")))


def _public_evidence_source_for_input(report_path: Path, requested_path: Path) -> str:
    if requested_path.is_dir():
        try:
            return report_path.relative_to(requested_path).as_posix()
        except ValueError:
            return _safe_evidence_source(str(report_path))
    return report_path.name


def _is_windows_wasapi_capture_evidence(report: dict[str, Any]) -> bool:
    capture_checklist = report.get("capture_checklist", {})
    system_guard = report.get("system_guard", {})
    target_capture_backend = report.get("target_capture_backend", {})
    return (
        report.get("system") == "Windows"
        and isinstance(system_guard, dict)
        and system_guard.get("expected_system_matched") is True
        and report.get("capture_backend") == "wasapi"
        and isinstance(target_capture_backend, dict)
        and target_capture_backend.get("available") is True
        and report.get("capture_backend_ready_required") is True
        and report.get("hardware_capture_tested") is True
        and report.get("input_review_confirmed") is True
        and isinstance(capture_checklist, dict)
        and capture_checklist.get("input_review_confirmed") is True
        and capture_checklist.get("ready_for_beta_evidence") is True
        and _has_safe_manual_capture_command_card(report, "windows_wasapi_capture")
        and report.get("passed") is True
    )


def _has_safe_manual_capture_command_card(report: dict[str, Any], blocker: str) -> bool:
    card = report.get("manual_capture_command_card", {})
    if not isinstance(card, dict):
        return False
    command_templates = (
        card.get("preflight_command_template"),
        card.get("real_capture_command_template"),
        card.get("audit_command_template"),
    )
    return (
        card.get("artifact") == "manual-capture-command.md"
        and card.get("blocker") == blocker
        and card.get("ready_for_beta_evidence") is True
        and card.get("safe_to_share") is True
        and card.get("uses_placeholders") is True
        and card.get("preflight_uses_microphone") is False
        and card.get("real_capture_requires_microphone") is True
        and card.get("records_audio") is False
        and card.get("records_audio_bytes") is False
        and card.get("records_device_name") is False
        and card.get("records_local_paths") is False
        and all(isinstance(command, str) and "<pilot-output-dir>" in command for command in command_templates)
    )


def _is_cross_platform_capture_backend(value: object) -> bool:
    return str(value).casefold() in CROSS_PLATFORM_CAPTURE_BACKENDS


def _is_ubuntu_linux_capture_evidence(report: dict[str, Any]) -> bool:
    system = str(report.get("system", "")).lower()
    capture_checklist = report.get("capture_checklist", {})
    system_guard = report.get("system_guard", {})
    target_capture_backend = report.get("target_capture_backend", {})
    return (
        system in {"linux", "ubuntu/linux", "ubuntu"}
        and isinstance(system_guard, dict)
        and system_guard.get("expected_system_matched") is True
        and _is_cross_platform_capture_backend(report.get("capture_backend"))
        and isinstance(target_capture_backend, dict)
        and target_capture_backend.get("available") is True
        and report.get("capture_backend_ready_required") is True
        and report.get("hardware_capture_tested") is True
        and report.get("input_review_confirmed") is True
        and isinstance(capture_checklist, dict)
        and capture_checklist.get("input_review_confirmed") is True
        and capture_checklist.get("ready_for_beta_evidence") is True
        and _has_safe_manual_capture_command_card(report, "ubuntu_linux_capture")
        and report.get("passed") is True
    )


def _is_macos_capture_evidence(report: dict[str, Any]) -> bool:
    system = str(report.get("system", "")).lower()
    capture_checklist = report.get("capture_checklist", {})
    system_guard = report.get("system_guard", {})
    target_capture_backend = report.get("target_capture_backend", {})
    return (
        system in {"darwin", "macos", "mac"}
        and isinstance(system_guard, dict)
        and system_guard.get("expected_system_matched") is True
        and _is_cross_platform_capture_backend(report.get("capture_backend"))
        and isinstance(target_capture_backend, dict)
        and target_capture_backend.get("available") is True
        and report.get("capture_backend_ready_required") is True
        and report.get("hardware_capture_tested") is True
        and report.get("input_review_confirmed") is True
        and isinstance(capture_checklist, dict)
        and capture_checklist.get("input_review_confirmed") is True
        and capture_checklist.get("ready_for_beta_evidence") is True
        and _has_safe_manual_capture_command_card(report, "macos_capture")
        and report.get("passed") is True
    )


def _is_system_output_audible_evidence(report: dict[str, Any]) -> bool:
    next_system_output = report.get("next_system_output", {})
    operator_checklist = report.get("operator_checklist", {})
    system_guard = report.get("system_guard", {})
    spoken_text_privacy_scan = report.get("spoken_text_privacy_scan", {})
    target_output_backend = report.get("target_output_backend", {})
    return (
        report.get("backend") == "system"
        and isinstance(system_guard, dict)
        and system_guard.get("expected_system_matched") is True
        and isinstance(target_output_backend, dict)
        and target_output_backend.get("available") is True
        and report.get("output_backend_ready_required") is True
        and report.get("real_audio_requested") is True
        and report.get("operator_confirmation_status") == "confirmed"
        and report.get("text_review_confirmed") is True
        and isinstance(spoken_text_privacy_scan, dict)
        and spoken_text_privacy_scan.get("passed") is True
        and report.get("voice_review_confirmed") is True
        and isinstance(next_system_output, dict)
        and next_system_output.get("uses_placeholders") is True
        and next_system_output.get("records_spoken_text") is False
        and next_system_output.get("records_operator_identity") is False
        and isinstance(operator_checklist, dict)
        and operator_checklist.get("expected_system_matched") is True
        and operator_checklist.get("records_operator_identity") is False
        and operator_checklist.get("redacts_spoken_text") is True
        and operator_checklist.get("text_review_confirmed") is True
        and operator_checklist.get("spoken_text_privacy_scan_passed") is True
        and operator_checklist.get("voice_review_confirmed") is True
        and operator_checklist.get("commands_available") is True
        and operator_checklist.get("ready_for_real_audio") is True
        and operator_checklist.get("ready_for_beta_evidence") is True
        and report.get("passed") is True
    )


def _is_real_transcription_quality_evidence(report: dict[str, Any]) -> bool:
    audio = report.get("audio", {})
    quality = report.get("quality", {})
    reference_privacy_scan = report.get("reference_privacy_scan", {})
    preflight_readiness = report.get("preflight_readiness", {})
    target_backend = report.get("target_backend", {})
    transcript = report.get("transcript", {})
    transcription_checklist = report.get("transcription_checklist", {})
    return (
        report.get("real_transcription_requested") is True
        and isinstance(target_backend, dict)
        and target_backend.get("available") is True
        and report.get("target_backend_ready_required") is True
        and isinstance(preflight_readiness, dict)
        and preflight_readiness.get("status") == "ready"
        and preflight_readiness.get("decision") == "ready_for_real_transcription"
        and preflight_readiness.get("ready_for_model_run") is True
        and preflight_readiness.get("must_rerun_preflight") is False
        and preflight_readiness.get("safe_to_share") is True
        and preflight_readiness.get("usable_as_beta_evidence") is False
        and preflight_readiness.get("records_audio") is False
        and preflight_readiness.get("records_transcripts") is False
        and preflight_readiness.get("records_expected_text") is False
        and preflight_readiness.get("records_audio_file_name") is False
        and preflight_readiness.get("records_local_paths") is False
        and preflight_readiness.get("backend_ready") is True
        and preflight_readiness.get("audio_decoded") is True
        and preflight_readiness.get("duration_gate_enabled") is True
        and preflight_readiness.get("duration_gate_passed") is True
        and report.get("audio_confirmed_non_sensitive") is True
        and isinstance(audio, dict)
        and audio.get("generated_synthetic_audio") is False
        and audio.get("audio_confirmed_non_sensitive") is True
        and audio.get("decoded") is True
        and audio.get("audio_file_name_redacted") is True
        and isinstance(audio.get("duration_gate"), dict)
        and audio["duration_gate"].get("enabled") is True
        and audio["duration_gate"].get("passed") is True
        and report.get("audio_review_confirmed") is True
        and report.get("reference_review_confirmed") is True
        and isinstance(reference_privacy_scan, dict)
        and reference_privacy_scan.get("passed") is True
        and report.get("quality_review_confirmed") is True
        and report.get("passed") is True
        and isinstance(transcript, dict)
        and transcript.get("text_redacted") is True
        and isinstance(quality, dict)
        and quality.get("enabled") is True
        and quality.get("passed") is True
        and float(quality.get("min_word_accuracy") or 0.0) >= BETA_MIN_WORD_ACCURACY
        and isinstance(transcription_checklist, dict)
        and transcription_checklist.get("audio_review_confirmed") is True
        and transcription_checklist.get("records_audio_path") is False
        and transcription_checklist.get("records_audio_file_name") is False
        and transcription_checklist.get("records_transcript_text") is False
        and transcription_checklist.get("records_expected_text") is False
        and transcription_checklist.get("records_expected_text_file_name") is False
        and transcription_checklist.get("redacts_transcript_text") is True
        and transcription_checklist.get("redacts_expected_text") is True
        and transcription_checklist.get("reference_review_confirmed") is True
        and transcription_checklist.get("reference_privacy_scan_passed") is True
        and transcription_checklist.get("quality_review_confirmed") is True
        and transcription_checklist.get("ready_for_beta_evidence") is True
        and _openai_credential_evidence_ok(report, target_backend)
    )


def _openai_credential_evidence_ok(report: dict[str, Any], target_backend: Any) -> bool:
    backend_name = ""
    if isinstance(target_backend, dict):
        backend_name = str(target_backend.get("name") or "").strip().lower()
    if not backend_name:
        backend_name = str(report.get("backend") or "").strip().lower()
    if backend_name != "openai":
        return True

    credentials = report.get("credentials", {})
    return (
        isinstance(credentials, dict)
        and credentials.get("checked") is True
        and credentials.get("openai_api_key_required") is True
        and credentials.get("openai_api_key_present") is True
        and credentials.get("records_openai_api_key") is False
    )


def _safe_evidence_source(path: str) -> str:
    evidence_path = Path(path)
    parts = evidence_path.parts
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return evidence_path.name


def _known_issues(findings: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if "windows_audio:sample_rate" in findings and "reintento con `--sample-rate 48000` paso correctamente" in findings:
        issues.append(
            {
                "id": "windows-wasapi-sample-rate",
                "status": "resolved",
                "summary": "Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.",
            }
        )
    return issues


def _format_missing_term(term: str) -> str:
    if "`" in term:
        return term
    return f"`{term}`"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
