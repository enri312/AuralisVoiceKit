"""Safe pilot runner for AuralisVoiceKit.

This runner exercises the project without microphone access, real speech
playback, network calls or model downloads. It prepares artifacts that make the
next manual pilot easier to inspect.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import sys
from typing import Any

from auralis_voicekit import (
    DiagnosticStatus,
    VoiceActivityConfig,
    run_doctor,
    run_offline_benchmarks,
    write_benchmark_report,
)


def run_safe_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    benchmark_iterations: int = 1,
    evidence_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Run the safe automated pilot and return a structured report."""

    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / _slug(timestamp)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    gate_module = _load_module(workspace / "tools" / "stability_gate.py", "auralis_stability_gate")
    gate = gate_module.build_report(workspace)
    beta_module = _load_module(workspace / "tools" / "beta_readiness.py", "auralis_beta_readiness_for_pilot")
    beta_readiness = beta_module.build_beta_readiness_report(workspace, evidence_paths=evidence_paths or [])
    beta_audit = beta_module.build_evidence_audit_report(workspace, evidence_paths=evidence_paths or [])
    next_beta_evidence_steps = _next_beta_evidence_steps(beta_module, beta_readiness["blockers"])
    recommended_pilot_sequence = _recommended_pilot_sequence(
        next_beta_evidence_steps,
        ready_for_beta=beta_readiness["ready_for_beta"],
    )
    platform_pilot_matrix = _platform_pilot_matrix(beta_readiness["blockers"])
    steps: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {}

    doctor = run_doctor(include_devices=True, capture_backend="wav")
    _add_step(
        steps,
        "doctor:wav",
        doctor.status is not DiagnosticStatus.ERROR,
        {
            "status": doctor.status.value,
            "checks": len(doctor.checks),
            "hardware": False,
        },
    )

    assistant_module = _load_module(
        workspace / "examples" / "local_assistant_privacy_demo.py",
        "local_assistant_privacy_demo",
    )
    assistant_output = output / "local_assistant"
    assistant_payload = assistant_module.run_demo(
        output_dir=str(assistant_output),
        duration_seconds=0.5,
        chunk_duration_ms=100,
    )
    artifacts["assistant_input_wav"] = assistant_payload["input_wav"]
    artifacts["assistant_log"] = assistant_payload["log_path"]
    _add_step(
        steps,
        "local-assistant:privacy",
        bool(assistant_payload["turns"]) and all(assistant_payload["privacy_checks"].values()),
        {
            "turns": len(assistant_payload["turns"]),
            "log_records": assistant_payload["log_records"],
            "privacy_checks": assistant_payload["privacy_checks"],
            "hardware": False,
        },
    )

    system_module = _load_module(
        workspace / "examples" / "system_output_demo.py",
        "system_output_demo",
    )
    system_payload = system_module.run_demo(
        "Hola desde AuralisVoiceKit",
        system=platform.system(),
        dry_run=True,
        include_voices=True,
    )
    _add_step(
        steps,
        "system-output:dry-run",
        bool(system_payload["spoken"]) and system_payload["error"] is None,
        {
            "system": system_payload["system"],
            "commands": len(system_payload["commands"]),
            "voices": len(system_payload["voices"]),
            "hardware": False,
        },
    )

    benchmark = run_offline_benchmarks(
        iterations=benchmark_iterations,
        warmup_iterations=0,
        duration_seconds=0.5,
        sample_rate=1_000,
        chunk_duration_ms=100,
        voice_activity=VoiceActivityConfig(
            min_voice_ms=100,
            max_silence_ms=100,
            pre_speech_ms=0,
        ),
    )
    benchmark_json = output / "offline-benchmark.json"
    benchmark_csv = output / "offline-benchmark.csv"
    write_benchmark_report(benchmark, benchmark_json)
    write_benchmark_report(benchmark, benchmark_csv)
    artifacts["benchmark_json"] = str(benchmark_json)
    artifacts["benchmark_csv"] = str(benchmark_csv)
    _add_step(
        steps,
        "benchmark:offline-export",
        benchmark_json.exists() and benchmark_csv.exists(),
        {
            "results": len(benchmark.results),
            "iterations": benchmark.iterations,
            "hardware": False,
        },
    )

    manual_pilot_steps = _manual_pilot_steps()
    all_safe_steps_passed = all(step["status"] == "passed" for step in steps)
    safe_pilot_passed = bool(gate["ready_for_real_world_pilots"]) and all_safe_steps_passed

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "version": gate["version"],
        "stage": gate["stage"],
        "safe_automated_pilot": {
            "passed": safe_pilot_passed,
            "hardware_used": False,
            "network_used": False,
            "notes": "Microphone, real speech playback and real transcription remain manual pilot steps.",
        },
        "gate": {
            "ready_for_real_world_pilots": gate["ready_for_real_world_pilots"],
            "ready_for_stable_release": gate["ready_for_stable_release"],
            "pilot_blockers": gate["pilot_blockers"],
            "stable_blockers": gate["stable_blockers"],
        },
        "beta_readiness": {
            "ready_for_beta": beta_readiness["ready_for_beta"],
            "blockers": beta_readiness["blockers"],
            "evidence_count": beta_readiness["evidence"]["count"],
            "ignored_evidence_count": beta_readiness["evidence"]["ignored_count"],
            "ready_for_beta_by_json_evidence": beta_audit["ready_for_beta_by_evidence"],
            "satisfied_json_blockers": beta_audit["satisfied_blockers"],
            "missing_json_blockers": beta_audit["missing_blockers"],
            "accepted_json_artifacts": _pilot_plan_artifact_summary(beta_audit["artifacts"]),
            "ignored_json_artifacts": beta_audit["ignored_details"],
            "strict_audit_command": (
                "python tools/beta_readiness.py --audit-evidence "
                "--evidence pilot_runs/manual --evidence pilot_runs/output "
                "--evidence pilot_runs/transcription --fail-on-audit-gaps --json"
            ),
        },
        "steps": steps,
        "manual_pilot_steps": manual_pilot_steps,
        "next_beta_evidence_steps": next_beta_evidence_steps,
        "recommended_pilot_sequence": recommended_pilot_sequence,
        "platform_pilot_matrix": platform_pilot_matrix,
        "artifacts": artifacts,
    }
    plan_path = output / "pilot-plan.md"
    report_path = output / "pilot-report.json"
    artifacts["pilot_plan"] = str(plan_path)
    artifacts["pilot_report"] = str(report_path)
    plan_path.write_text(_format_pilot_plan_markdown(report), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the safe AuralisVoiceKit pilot.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output-dir", help="directory for pilot artifacts")
    parser.add_argument("--benchmark-iterations", type=int, default=1, help="offline benchmark iterations")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="AuralisVoiceKit pilot JSON evidence file or directory; can be passed more than once",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    report = run_safe_pilot(
        root=args.root,
        output_dir=args.output_dir,
        benchmark_iterations=args.benchmark_iterations,
        evidence_paths=args.evidence,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0 if report["safe_automated_pilot"]["passed"] else 1


def _manual_pilot_steps() -> list[dict[str, str]]:
    return [
        {
            "name": "microphone-capture-checklist",
            "command": "python tools/manual_pilot.py --output-dir pilot_runs/manual/capture-dry-run --json",
            "reason": "Writes manual-capture-checklist.md before any real microphone access.",
        },
        {
            "name": "microphone-capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend wasapi --device default "
                "--sample-rate 48000 --expected-system Windows --json"
            ),
            "reason": "Requires real microphone hardware and OS permissions.",
        },
        {
            "name": "system-speech",
            "command": (
                "python tools/output_pilot.py --speak --operator-present --confirm-audible "
                "--output-dir pilot_runs/output/system-real --text \"Hola desde AuralisVoiceKit\" --json"
            ),
            "reason": "Plays real audio and should be run intentionally by a human.",
        },
        {
            "name": "real-transcription",
            "command": (
                "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
                "--audio-non-sensitive --backend whisper --model base --normalize "
                "--expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 "
                "--min-audio-seconds 0.2 --max-audio-seconds 60 "
                "--confirm-quality-reviewed --json"
            ),
            "reason": "Uses a real non-sensitive audio file and requires human quality review before beta evidence.",
        },
        {
            "name": "record-findings",
            "command": "Update PILOT_FINDINGS.md with OS, Python, hardware, command output and follow-up issues.",
            "reason": "Turns pilot observations into actionable project work.",
        },
        {
            "name": "beta-readiness",
            "command": (
                "python tools/beta_readiness.py --evidence pilot_runs/manual "
                "--evidence pilot_runs/output --evidence pilot_runs/transcription "
                "--output BETA_CHECKLIST.md --fail-on-blockers --json"
            ),
            "reason": "Keeps public beta blocked until the real pilot evidence is documented.",
        },
    ]


def _next_beta_evidence_steps(beta_module: Any, blockers: list[str]) -> list[dict[str, Any]]:
    requirements = {
        requirement["name"]: requirement
        for requirement in beta_module.build_evidence_requirements_report()["requirements"]
    }
    steps = []
    for blocker in blockers:
        requirement = requirements.get(blocker)
        if requirement is None:
            continue
        steps.append(
            {
                "name": blocker,
                "title": requirement["title"],
                "artifact": requirement["artifact"],
                "command": requirement["command"],
                "required_fields": [field["path"] for field in requirement["fields"]],
                "reason": "Evidencia real requerida antes de beta publica.",
            }
        )
    return steps


def _recommended_pilot_sequence(
    next_beta_evidence_steps: list[dict[str, Any]],
    *,
    ready_for_beta: bool,
) -> list[dict[str, Any]]:
    hardware_required_blockers = {"system_output_audible", "ubuntu_linux_capture", "macos_capture"}
    sequence = []
    for step in next_beta_evidence_steps:
        if step["name"] == "real_transcription_quality":
            sequence.append(_transcription_audio_fixture_step(len(sequence) + 1))
            sequence.append(_transcription_audio_preflight_step(len(sequence) + 1))
        if step["name"] == "system_output_audible":
            sequence.append(_system_output_operator_checklist_step(len(sequence) + 1))
        sequence.append(
            {
                "order": len(sequence) + 1,
                "name": step["name"],
                "title": step["title"],
                "command": step["command"],
                "artifact": step["artifact"],
                "required_fields": step["required_fields"],
                "requires_hardware": step["name"] in hardware_required_blockers,
                "requires_operator": step["name"] == "system_output_audible",
                "requires_non_sensitive_audio": step["name"] == "real_transcription_quality",
                "review_required": True,
                "reason": step["reason"],
            }
        )

    next_order = len(sequence) + 1
    sequence.extend(
        [
            {
                "order": next_order,
                "name": "audit-evidence",
                "title": "Auditoria estricta de evidencias",
                "command": (
                    "python tools/beta_readiness.py --audit-evidence "
                    "--evidence pilot_runs/manual --evidence pilot_runs/output "
                    "--evidence pilot_runs/transcription --fail-on-audit-gaps --json"
                ),
                "artifact": "beta-readiness-audit.json",
                "required_fields": ["satisfied_blockers", "missing_blockers", "ready_for_beta_by_evidence"],
                "requires_hardware": False,
                "requires_operator": False,
                "requires_non_sensitive_audio": False,
                "review_required": True,
                "reason": "Verifica que los artifacts reales cierren blockers sin exponer contenido privado.",
            },
            {
                "order": next_order + 1,
                "name": "refresh-beta-checklist",
                "title": "Actualizar checklist beta",
                "command": (
                    "python tools/beta_readiness.py --evidence pilot_runs/manual "
                    "--evidence pilot_runs/output --evidence pilot_runs/transcription "
                    "--output BETA_CHECKLIST.md --fail-on-blockers --json"
                ),
                "artifact": "BETA_CHECKLIST.md",
                "required_fields": ["ready_for_beta", "blockers", "evidence.count"],
                "requires_hardware": False,
                "requires_operator": False,
                "requires_non_sensitive_audio": False,
                "review_required": not ready_for_beta,
                "reason": "Mantiene visible si beta sigue bloqueada o si ya puede evaluarse publicamente.",
            },
        ]
    )
    return sequence


def _transcription_audio_fixture_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "transcription-audio-fixture",
        "title": "Transcription audio fixture",
        "command": (
            "python tools/pilot_audio_fixture.py --output-dir pilot_runs/transcription/fixture "
            "--format wav --format mp3 --duration 1.0 --sample-rate 16000 "
            "--run-preflight --min-audio-seconds 0.2 --max-audio-seconds 60 --json"
        ),
        "artifact": "pilot-audio-fixture-report.json",
        "required_fields": [
            "project",
            "generated_public_fixture",
            "contains_private_audio",
            "usable_as_beta_evidence",
            "files",
            "preflight.passed",
            "passed",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": False,
        "review_required": False,
        "reason": "Genera un MP3 sintetico publico para ensayar ffmpeg antes de usar audio propio no sensible.",
    }


def _transcription_audio_preflight_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "transcription-audio-preflight",
        "title": "Transcription audio preflight",
        "command": (
            "python tools/transcription_pilot.py --preflight-only --audio sample.mp3 "
            "--audio-non-sensitive --backend whisper --normalize "
            "--min-audio-seconds 0.2 --max-audio-seconds 60 --json"
        ),
        "artifact": "transcription-pilot-report.json",
        "required_fields": [
            "project",
            "preflight_only",
            "audio.decoded",
            "audio.duration_gate.passed",
            "audio.audio_file_extension",
            "audio.audio_confirmed_non_sensitive",
            "transcription_checklist.records_transcript_text",
            "transcription_checklist.redacts_expected_text",
            "artifacts.transcription_review_checklist",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": True,
        "review_required": True,
        "reason": (
            "Confirma que el MP3 propio se decodifica con ffmpeg y genera "
            "transcription-review-checklist.md antes de ejecutar un modelo real."
        ),
    }


def _system_output_operator_checklist_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "system-output-operator-checklist",
        "title": "System output operator checklist",
        "command": "python tools/output_pilot.py --output-dir pilot_runs/output/system-dry-run --json",
        "artifact": "output-operator-checklist.md",
        "required_fields": [
            "operator_checklist.records_operator_identity",
            "operator_checklist.redacts_spoken_text",
            "operator_checklist.ready_for_beta_evidence",
            "artifacts.operator_checklist",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": False,
        "review_required": True,
        "reason": "Prepara el checklist redactado antes de ejecutar salida audible real con operador presente.",
    }


def _platform_pilot_matrix(blockers: list[str]) -> list[dict[str, Any]]:
    pending = set(blockers)
    rows = [
        {
            "name": "windows-wasapi-capture",
            "platform": "Windows",
            "blocker": "windows_wasapi_capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend wasapi "
                "--device default --sample-rate 48000 --expected-system Windows --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            "notes": "Captura Windows ya esta documentada; repetir si cambia hardware o driver y conservar manual-capture-checklist.md.",
        },
        {
            "name": "ubuntu-linux-capture",
            "platform": "Ubuntu/Linux",
            "blocker": "ubuntu_linux_capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend sounddevice "
                "--device default --expected-system Linux --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            "notes": "Requiere microfono, permisos de audio, PortAudio/sounddevice y manual-capture-checklist.md.",
        },
        {
            "name": "macos-capture",
            "platform": "macOS",
            "blocker": "macos_capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend sounddevice "
                "--device default --expected-system Darwin --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            "notes": "Requiere permiso de microfono en macOS, revisar el dispositivo default y conservar manual-capture-checklist.md.",
        },
        {
            "name": "system-output-audible",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": "system_output_audible",
            "command": (
                "python tools/output_pilot.py --speak --operator-present "
                "--confirm-audible --output-dir pilot_runs/output/system-real "
                "--text \"Hola desde AuralisVoiceKit\" --json"
            ),
            "artifact": "output-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": True,
            "requires_non_sensitive_audio": False,
            "notes": "Ejecutar solo con operador presente; el reporte redacta el texto completo.",
        },
        {
            "name": "transcription-audio-fixture",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": None,
            "command": (
                "python tools/pilot_audio_fixture.py --output-dir pilot_runs/transcription/fixture "
                "--format wav --format mp3 --duration 1.0 --sample-rate 16000 "
                "--run-preflight --min-audio-seconds 0.2 --max-audio-seconds 60 --json"
            ),
            "artifact": "pilot-audio-fixture-report.json",
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            "notes": "Fixture sintetico y publico para validar ffmpeg; no cuenta como evidencia beta.",
        },
        {
            "name": "transcription-mp3-preflight",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": None,
            "command": (
                "python tools/transcription_pilot.py --preflight-only --audio sample.mp3 "
                "--audio-non-sensitive --backend whisper --normalize "
                "--min-audio-seconds 0.2 --max-audio-seconds 60 --json"
            ),
            "artifact": "transcription-pilot-report.json",
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": True,
            "notes": "Paso previo: valida ffmpeg y metadata antes de transcribir con un modelo.",
        },
        {
            "name": "real-transcription-quality",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": "real_transcription_quality",
            "command": (
                "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
                "--audio-non-sensitive --backend whisper --model base --normalize "
                "--expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 "
                "--min-audio-seconds 0.2 --max-audio-seconds 60 "
                "--confirm-quality-reviewed --json"
            ),
            "artifact": "transcription-pilot-report.json",
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": True,
            "notes": "Usar un MP3 propio no sensible, una referencia redactable y confirmar revision humana de calidad.",
        },
    ]
    for row in rows:
        blocker = row["blocker"]
        if blocker is None:
            row["status"] = "recommended"
        elif blocker in pending:
            row["status"] = "pending"
        else:
            row["status"] = "closed"
    return rows


def _pilot_plan_artifact_summary(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "file": artifact["file"],
            "artifact": artifact["artifact"],
            "satisfied_blockers": artifact["satisfied_blockers"],
        }
        for artifact in artifacts
    ]


def _format_pilot_plan_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    lines = [
        "# Plan de pilotos AuralisVoiceKit",
        "",
        "Este artefacto resume el siguiente piloto real sin incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Piloto seguro paso: `{str(report['safe_automated_pilot']['passed']).lower()}`",
        f"- Listo para pilotos reales: `{str(report['gate']['ready_for_real_world_pilots']).lower()}`",
        f"- Listo para beta: `{str(beta['ready_for_beta']).lower()}`",
        f"- Evidencias JSON aceptadas: `{beta['evidence_count']}`",
        f"- Evidencias JSON ignoradas: `{beta['ignored_evidence_count']}`",
        f"- Blockers beta: {_format_inline_list(beta['blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(beta['satisfied_json_blockers'])}",
        f"- Blockers JSON pendientes: {_format_inline_list(beta['missing_json_blockers'])}",
        "",
        "## Checks seguros",
        "",
    ]
    for step in report["steps"]:
        marker = "x" if step["status"] == "passed" else " "
        lines.append(f"- [{marker}] `{step['name']}`")
    lines.extend(
        [
            "",
            "## Evidencias JSON",
            "",
        ]
    )
    if beta["accepted_json_artifacts"]:
        lines.append("### Aceptadas")
        lines.append("")
        for artifact in beta["accepted_json_artifacts"]:
            lines.extend(
                [
                    f"- `{artifact['file']}`",
                    f"  - Artifact: `{artifact['artifact']}`",
                    f"  - Blockers cerrados: {_format_inline_list(artifact['satisfied_blockers'])}",
                ]
            )
        lines.append("")
    else:
        lines.append("- No hay artifacts JSON aceptados todavia.")
        lines.append("")
    if beta["ignored_json_artifacts"]:
        lines.append("### Ignoradas")
        lines.append("")
        for artifact in beta["ignored_json_artifacts"]:
            lines.append(
                f"- `{artifact['file']}`: `{artifact['reason']}` - {artifact['message_es']} / {artifact['message_en']}."
            )
        lines.append("")
    lines.extend(
        [
            "## Secuencia recomendada",
            "",
        ]
    )
    for step in report["recommended_pilot_sequence"]:
        lines.extend(
            [
                f"### {step['order']}. {step['title']}",
                "",
                f"- Paso: `{step['name']}`",
                f"- Comando: `{step['command']}`",
                f"- Artifact esperado: `{step['artifact']}`",
                f"- Campos requeridos: {_format_inline_list(step['required_fields'])}",
                f"- Requiere hardware: `{_format_bool(step['requires_hardware'])}`",
                f"- Requiere operador: `{_format_bool(step['requires_operator'])}`",
                f"- Requiere audio no sensible: `{_format_bool(step['requires_non_sensitive_audio'])}`",
                f"- Revision requerida: `{_format_bool(step['review_required'])}`",
                f"- Motivo: {step['reason']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Proximas evidencias beta",
            "",
        ]
    )
    if report["next_beta_evidence_steps"]:
        for step in report["next_beta_evidence_steps"]:
            lines.extend(
                [
                    f"### {step['title']}",
                    "",
                    f"- Blocker: `{step['name']}`",
                    f"- Artifact esperado: `{step['artifact']}`",
                    f"- Comando: `{step['command']}`",
                    f"- Campos requeridos: {_format_inline_list(step['required_fields'])}",
                    f"- Motivo: {step['reason']}",
                    "",
                ]
            )
    else:
        lines.extend(["- No quedan evidencias beta pendientes segun los artifacts JSON actuales.", ""])
    lines.extend(
        [
            "## Auditoria estricta",
            "",
            f"- Comando: `{beta['strict_audit_command']}`",
            "",
            "## Matriz por plataforma",
            "",
        ]
    )
    for row in report["platform_pilot_matrix"]:
        lines.extend(
            [
                f"### {row['platform']} - {row['name']}",
                "",
                f"- Estado: `{row['status']}`",
                f"- Blocker: `{row['blocker'] or 'ninguno'}`",
                f"- Comando: `{row['command']}`",
                f"- Artifact esperado: `{row['artifact']}`",
                f"- Requiere hardware: `{_format_bool(row['requires_hardware'])}`",
                f"- Requiere operador: `{_format_bool(row['requires_operator'])}`",
                f"- Requiere audio no sensible: `{_format_bool(row['requires_non_sensitive_audio'])}`",
                f"- Nota: {row['notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Pasos manuales",
            "",
        ]
    )
    for step in report["manual_pilot_steps"]:
        lines.extend(
            [
                f"### {step['name']}",
                "",
                f"- Comando: `{step['command']}`",
                f"- Motivo: {step['reason']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Privacidad",
            "",
            "- Este plan usa nombres de artifacts y campos estructurados.",
            "- No copia audio, transcripciones, texto esperado real completo, rutas locales completas ni nombres reales de dispositivos.",
            "- Reemplaza `sample.mp3` por un archivo propio no sensible antes de ejecutar transcripcion real.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_inline_list(values: list[str]) -> str:
    if not values:
        return "`ninguno`"
    return ", ".join(f"`{value}`" for value in values)


def _format_bool(value: bool) -> str:
    return str(value).lower()


def _add_step(
    steps: list[dict[str, Any]],
    name: str,
    passed: bool,
    details: dict[str, Any],
) -> None:
    steps.append(
        {
            "name": name,
            "status": "passed" if passed else "failed",
            "details": details,
        }
    )


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit safe pilot")
    print(f"Version: {report['version']}")
    print(f"Stage: {report['stage']}")
    print(f"Passed: {report['safe_automated_pilot']['passed']}")
    print(f"Ready for beta: {report['beta_readiness']['ready_for_beta']}")
    if report["beta_readiness"]["blockers"]:
        print("Beta blockers:")
        for blocker in report["beta_readiness"]["blockers"]:
            print(f"- {blocker}")
    print("Steps:")
    for step in report["steps"]:
        print(f"- [{step['status']}] {step['name']}")
    print("Next beta evidence steps:")
    for step in report["next_beta_evidence_steps"]:
        print(f"- {step['name']}: {step['command']}")
    print("Recommended pilot sequence:")
    for step in report["recommended_pilot_sequence"]:
        print(f"- {step['order']}. {step['name']}: {step['command']}")
    print("Platform pilot matrix:")
    for row in report["platform_pilot_matrix"]:
        print(f"- [{row['status']}] {row['platform']} {row['name']}: {row['command']}")
    print(f"Pilot plan: {Path(report['artifacts']['pilot_plan']).name}")
    print("Manual pilot steps:")
    for step in report["manual_pilot_steps"]:
        print(f"- {step['name']}: {step['command']}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
