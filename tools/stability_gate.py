"""Project readiness gate for roadmap automation."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any


STAGE_ORDER = {
    "alpha": 0,
    "pilot": 1,
    "stable": 2,
}


PILOT_CHECKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("readme", "README.md", ("AuralisVoiceKit", "Roadmap")),
    ("roadmap", "ROADMAP.md", ("Prioridad inmediata", "Criterio de salida")),
    ("compatibility", "COMPATIBILITY.md", ("Windows", "Ubuntu/Linux", "macOS")),
    ("privacy_guide", "PRIVACY.md", ("PrivacyEventLogger", "AURALIS_PRIVACY_MODE")),
    ("custom_output_guide", "CUSTOM_OUTPUT_BACKENDS.md", ("SpeechOutputBackend", "register_output")),
    ("pilot_runbook", "PILOTS.md", ("tools\\pilot_run.py", "Checklist manual")),
    ("pypi_guide", "PYPI.md", ("Trusted Publishing", "auralisvoicekit")),
    ("api_reference", "docs/auralisvoicekit-api.html", ("Backends personalizados", "PrivacyEventLogger")),
    ("main_documentation", "docs/auralisvoicekit-documentacion.html", ("Privacidad y logs", "Salida de voz")),
    ("pypi_quickstart", "examples/pypi_quickstart.py", ("run_demo", "transcription_backend")),
    ("custom_output_example", "examples/custom_output_backend.py", ("MemorySpeechOutputBackend", "run_demo")),
    ("system_output_example", "examples/system_output_demo.py", ("DryRunSystemRunner", "--speak")),
    (
        "pyaudio_capture_backend",
        "src/auralis_voicekit/backends/pyaudio_capture.py",
        (
            "PyAudioCaptureBackend",
            "auralisvoicekit[pyaudio]",
            "resolve_input_device",
            "stream_callback",
            "stop_stream",
        ),
    ),
    ("local_assistant_privacy_example", "examples/local_assistant_privacy_demo.py", ("PrivacyEventLogger", "privacy_checks")),
    (
        "safe_pilot_runner",
        "tools/pilot_run.py",
        (
            "run_safe_pilot",
            "manual_pilot_steps",
            "next_beta_evidence_steps",
            "recommended_pilot_sequence",
            "platform_pilot_matrix",
            "transcription-audio-fixture",
            "transcription-audio-preflight",
            "transcription-review-checklist.md",
            "real-transcription-next-step.md",
            "system-output-operator-checklist",
            "output-operator-checklist.md",
            "system-output-next-step.md",
            "accepted_json_artifacts",
            "ignored_json_artifacts",
            "real_pilot_findings_template",
            "real-pilot-findings-template.md",
            "real_pilot_handoff",
            "real-pilot-handoff.md",
            "pilot-plan.md",
            "Secuencia recomendada",
            "Matriz por plataforma",
        ),
    ),
    (
        "pilot_audio_fixture_runner",
        "tools/pilot_audio_fixture.py",
        (
            "generate_pilot_audio_fixture",
            "--format",
            "--run-preflight",
            "generated_public_fixture",
            "usable_as_beta_evidence",
            "preflight",
            "pilot-sample.mp3",
            "fixture_preflight_checklist",
            "fixture_preflight_next_step",
            "transcription-review-checklist.md",
            "real-transcription-next-step.md",
        ),
    ),
    (
        "manual_pilot_runner",
        "tools/manual_pilot.py",
        (
            "run_manual_pilot",
            "--capture-test",
            "--sample-rate",
            "--expected-system",
            "--confirm-input-reviewed",
            "system_guard",
            "input_review_confirmed",
            "capture_checklist",
        ),
    ),
    (
        "output_pilot_runner",
        "tools/output_pilot.py",
        (
            "run_output_pilot",
            "--speak",
            "--operator-present",
            "--confirm-audible",
            "--confirm-text-reviewed",
            "--confirm-voice-reviewed",
            "--expected-system",
            "system_guard",
            "expected_system_matched",
            "operator_checklist",
            "output-operator-checklist.md",
            "system-output-next-step.md",
            "next_system_output",
            "system_output_next_step",
            "spoken_text_privacy_scan",
            "text_review_confirmed",
            "voice_review_confirmed",
            "ready_for_beta_evidence",
            "<text-redacted>",
        ),
    ),
    (
        "transcription_pilot_runner",
        "tools/transcription_pilot.py",
        (
            "run_transcription_pilot",
            "--real-transcription",
            "--audio-non-sensitive",
            "--confirm-audio-reviewed",
            "--confirm-reference-reviewed",
            "--expected-text",
            "--preflight-only",
            "--confirm-quality-reviewed",
            "--max-audio-seconds",
            "preflight_only",
            "duration_gate",
            "decoded",
            "reference_privacy_scan",
            "transcription_checklist",
            "audio_review_confirmed",
            "reference_review_confirmed",
            "reference_privacy_scan_passed",
            "quality_review_confirmed",
            "audio_file_name_redacted",
            "records_audio_file_name",
            "records_expected_text_file_name",
            "transcription-review-checklist.md",
            "real-transcription-next-step.md",
            "next_real_transcription",
            "real_transcription_next_step",
            "ready_for_beta_evidence",
        ),
    ),
    (
        "beta_readiness_runner",
        "tools/beta_readiness.py",
        (
            "build_beta_readiness_report",
            "build_evidence_requirements_report",
            "build_evidence_audit_report",
            "--fail-on-blockers",
            "--evidence",
            "--requirements",
            "--audit-evidence",
            "--fail-on-audit-gaps",
            "missing_blockers",
            "ready_for_beta_by_evidence",
            "quality.min_word_accuracy",
            "audio.audio_file_name_redacted",
            "audio_review_confirmed",
            "transcription_checklist.audio_review_confirmed",
            "transcription_checklist.records_audio_file_name",
            "transcription_checklist.records_expected_text_file_name",
            "reference_review_confirmed",
            "reference_privacy_scan.passed",
            "transcription_checklist.reference_review_confirmed",
            "transcription_checklist.reference_privacy_scan_passed",
            "quality_review_confirmed",
            "spoken_text_privacy_scan.passed",
            "text_review_confirmed",
            "voice_review_confirmed",
            "operator_checklist.spoken_text_privacy_scan_passed",
            "operator_checklist.text_review_confirmed",
            "operator_checklist.expected_system_matched",
            "input_review_confirmed",
            "capture_checklist.input_review_confirmed",
            "system_guard.expected_system_matched",
            "ignored_count",
            "ignored_details",
            "missing_project",
            "BETA_CHECKLIST.md",
        ),
    ),
    ("beta_checklist", "BETA_CHECKLIST.md", ("Checklist de beta", "Bloqueadores para beta", "tools\\beta_readiness.py")),
    (
        "beta_evidence_requirements",
        "BETA_EVIDENCE_REQUIREMENTS.md",
        (
            "Requisitos de evidencias beta",
            "manual-pilot-report.json",
            "output-pilot-report.json",
            "transcription-pilot-report.json",
            "No audio bytes",
            "audio.audio_file_name_redacted",
            "operator_checklist.ready_for_beta_evidence",
        ),
    ),
    ("pilot_findings", "PILOT_FINDINGS.md", ("Windows manual seguro", "sounddevice")),
    ("doctor_bundle_api", "src/auralis_voicekit/diagnostics.py", ("create_doctor_bundle", "write_doctor_bundle")),
    ("doctor_bundle_analysis", "src/auralis_voicekit/diagnostics.py", ("analyze_doctor_bundles", "DoctorBundleAnalysis")),
    ("ci", ".github/workflows/ci.yml", ("stability_gate.py", "unittest discover", "windows-2025-vs2026", "PIP_NO_CACHE_DIR")),
    ("pyproject_pyaudio_extra", "pyproject.toml", ("pyaudio", "PyAudio>=0.2.14")),
    ("release_workflow", ".github/workflows/release.yml", ("python -m build", "actions/upload-artifact@v7.0.1", "gh release create")),
    (
        "release_batch_guard",
        "tools/release_batch_status.py",
        ("build_release_batch_status", "--fail-if-not-ready", "ready_for_tag"),
    ),
)


def build_report(root: str | Path) -> dict[str, Any]:
    workspace = Path(root)
    version = _read_version(workspace)
    release_batch = _build_release_batch_status(workspace)
    checks = [_run_check(workspace, name, relative_path, required_terms) for name, relative_path, required_terms in PILOT_CHECKS]
    pilot_blockers = [check["name"] for check in checks if not check["ok"]]
    ready_for_pilots = not pilot_blockers
    stable_blockers = []
    if not ready_for_pilots:
        stable_blockers.extend(pilot_blockers)
    if _major_version(version) < 1:
        stable_blockers.append("version_is_pre_1_0")

    if not stable_blockers:
        stage = "stable"
    elif ready_for_pilots:
        stage = "pilot"
    else:
        stage = "alpha"

    return {
        "project": "AuralisVoiceKit",
        "version": version,
        "stage": stage,
        "ready_for_real_world_pilots": ready_for_pilots,
        "ready_for_stable_release": not stable_blockers,
        "checks": checks,
        "pilot_blockers": pilot_blockers,
        "stable_blockers": stable_blockers,
        "release_batch": release_batch,
        "next_actions": _next_actions(stage, pilot_blockers, release_batch),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check AuralisVoiceKit roadmap readiness.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument(
        "--min-stage",
        choices=tuple(STAGE_ORDER),
        default="alpha",
        help="minimum required stage",
    )
    args = parser.parse_args(argv)

    report = build_report(args.root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)

    return 0 if STAGE_ORDER[report["stage"]] >= STAGE_ORDER[args.min_stage] else 1


def _run_check(
    workspace: Path,
    name: str,
    relative_path: str,
    required_terms: tuple[str, ...],
) -> dict[str, Any]:
    path = workspace / relative_path
    if not path.exists():
        return {
            "name": name,
            "path": relative_path,
            "ok": False,
            "reason": "missing",
            "missing_terms": list(required_terms),
        }

    content = path.read_text(encoding="utf-8")
    missing_terms = [term for term in required_terms if term not in content]
    return {
        "name": name,
        "path": relative_path,
        "ok": not missing_terms,
        "reason": "ok" if not missing_terms else "missing required terms",
        "missing_terms": missing_terms,
    }


def _read_version(workspace: Path) -> str:
    version_file = workspace / "src" / "auralis_voicekit" / "_version.py"
    content = version_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match is None:
        return "0.0.0"
    return match.group(1)


def _major_version(version: str) -> int:
    try:
        return int(version.split(".", 1)[0])
    except ValueError:
        return 0


def _build_release_batch_status(workspace: Path) -> dict[str, Any]:
    guard_path = workspace / "tools" / "release_batch_status.py"
    if not guard_path.exists():
        return {
            "available": False,
            "ready_for_tag": False,
            "commit_count": 0,
            "threshold": 5,
            "remaining": 5,
            "next_action_es": "Agregar tools/release_batch_status.py antes de publicar tags.",
        }

    spec = importlib.util.spec_from_file_location("release_batch_status", guard_path)
    if spec is None or spec.loader is None:
        return {
            "available": False,
            "ready_for_tag": False,
            "commit_count": 0,
            "threshold": 5,
            "remaining": 5,
            "next_action_es": "No se pudo cargar el guard de releases por lote.",
        }

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_release_batch_status(workspace)
    report["available"] = True
    return report


def _next_actions(stage: str, pilot_blockers: list[str], release_batch: dict[str, Any]) -> list[str]:
    release_action = release_batch.get("next_action_es")
    if stage == "stable":
        actions = ["Mantener compatibilidad, pruebas reales y politica de cambios."]
        if release_action:
            actions.append(str(release_action))
        return actions
    if stage == "pilot":
        actions = [
            "Probar con microfono real en Windows, Ubuntu/Linux y macOS.",
            "Probar salida system con voces reales disponibles por sistema.",
            (
                "Probar transcripcion real con Whisper local usando audio propio; "
                "usar OpenAI solo como integracion propietaria opt-in si el proyecto ya eligio esa API."
            ),
            "Registrar hallazgos antes de declarar beta o version 1.0.",
        ]
        if release_action:
            actions.append(str(release_action))
        return actions
    return [f"Completar check faltante: {name}" for name in pilot_blockers]


def _print_text_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit stability gate")
    print(f"Version: {report['version']}")
    print(f"Stage: {report['stage']}")
    print(f"Ready for real-world pilots: {report['ready_for_real_world_pilots']}")
    print(f"Ready for stable release: {report['ready_for_stable_release']}")
    release_batch = report["release_batch"]
    print(
        "Release batch: "
        f"{release_batch['commit_count']}/{release_batch['threshold']} "
        f"(ready_for_tag={str(release_batch['ready_for_tag']).lower()})"
    )
    print("Checks:")
    for check in report["checks"]:
        marker = "ok" if check["ok"] else "fail"
        print(f"- [{marker}] {check['name']} ({check['path']})")
    print("Next actions:")
    for action in report["next_actions"]:
        print(f"- {action}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
