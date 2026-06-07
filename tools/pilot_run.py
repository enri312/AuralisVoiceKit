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


OPENAI_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
OPENAI_TIMEOUT_SECONDS = 30
SYSTEM_OUTPUT_NO_PIP_EXTRA_CONTRACT = [
    "target_output_backend.readiness_plan.uses_pip_extra=false",
    "target_output_backend.readiness_plan.python_extra=null",
    "target_output_backend.readiness_plan.pip_command=null",
    "system_output_command_card.uses_pip_extra=false",
    "system_output_command_card.python_extra=null",
    "system_output_command_card.pip_command=null",
    "system_output_command_card.system_dependency_plan.safe_to_share=true",
    "system_output_command_card.system_dependency_plan.post_install_check_plays_audio=false",
    "system_output_command_card.system_dependency_plan.records_local_paths=false",
]


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
    release_batch = dict(gate.get("release_batch", {}))
    beta_module = _load_module(workspace / "tools" / "beta_readiness.py", "auralis_beta_readiness_for_pilot")
    beta_readiness = beta_module.build_beta_readiness_report(workspace, evidence_paths=evidence_paths or [])
    beta_audit = beta_module.build_evidence_audit_report(workspace, evidence_paths=evidence_paths or [])
    beta_next_evidence_focus = _with_policy_required_fields(beta_audit["next_evidence_focus"])
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
    environment_checklist = _real_pilot_environment_checklist(doctor)
    all_safe_steps_passed = all(step["status"] == "passed" for step in steps)
    safe_pilot_passed = bool(gate["ready_for_real_world_pilots"]) and all_safe_steps_passed

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "version": gate["version"],
        "stage": gate["stage"],
        "release_batch": release_batch,
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
            "release_batch": release_batch,
        },
        "beta_readiness": {
            "ready_for_beta": beta_readiness["ready_for_beta"],
            "blockers": beta_readiness["blockers"],
            "evidence_count": beta_readiness["evidence"]["count"],
            "ignored_evidence_count": beta_readiness["evidence"]["ignored_count"],
            "ready_for_beta_by_json_evidence": beta_audit["ready_for_beta_by_evidence"],
            "satisfied_json_blockers": beta_audit["satisfied_blockers"],
            "missing_json_blockers": beta_audit["missing_blockers"],
            "blocker_summaries": beta_audit["blocker_summaries"],
            "next_evidence_focus": beta_next_evidence_focus,
            "privacy_audit": beta_audit["privacy_audit"],
            "privacy_remediation_plan": beta_audit["privacy_remediation_plan"],
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
        "environment_checklist": environment_checklist,
        "artifacts": artifacts,
    }
    report["next_evidence_focus_preparation_sequence"] = _next_evidence_focus_preparation_sequence(
        recommended_pilot_sequence,
        report["beta_readiness"]["next_evidence_focus"],
    )
    report["evidence_manifest"] = _real_pilot_evidence_manifest(
        report["beta_readiness"],
        beta_audit,
        next_beta_evidence_steps,
    )
    report["pilot_decision_gate"] = _real_pilot_decision_gate(report)
    findings_template_path = output / "real-pilot-findings-template.md"
    handoff_path = output / "real-pilot-handoff.md"
    command_pack_path = output / "real-pilot-command-pack.md"
    environment_checklist_path = output / "real-pilot-environment-checklist.md"
    fixture_preflight_path = output / "real-pilot-fixture-preflight.md"
    transcription_readiness_path = output / "real-pilot-transcription-readiness.md"
    system_output_readiness_path = output / "real-pilot-system-output-readiness.md"
    evidence_manifest_path = output / "real-pilot-evidence-manifest.md"
    decision_gate_path = output / "real-pilot-decision-gate.md"
    next_focus_path = output / "real-pilot-next-evidence-focus.md"
    hard_stop_path = output / "real-pilot-hard-stop-card.md"
    evidence_intake_path = output / "real-pilot-evidence-intake-card.md"
    execution_card_path = output / "real-pilot-execution-card.md"
    consent_card_path = output / "real-pilot-consent-card.md"
    audit_closure_path = output / "real-pilot-audit-closure.md"
    rehearsal_card_path = output / "real-pilot-rehearsal-card.md"
    evidence_package_path = output / "real-pilot-evidence-package.md"
    operator_brief_path = output / "real-pilot-operator-brief.md"
    run_sheet_path = output / "real-pilot-run-sheet.md"
    final_go_no_go_path = output / "real-pilot-final-go-no-go.md"
    local_receipt_path = output / "real-pilot-local-receipt.md"
    plan_path = output / "pilot-plan.md"
    report_path = output / "pilot-report.json"
    report["fixture_preflight_card"] = _real_pilot_fixture_preflight_card(report)
    report["transcription_readiness_card"] = _real_pilot_transcription_readiness_card(report)
    report["system_output_readiness_card"] = _real_pilot_system_output_readiness_card(report)
    report["real_pilot_findings_template"] = {
        "artifact": str(findings_template_path),
        "safe_to_share": True,
        "target_document": "PILOT_FINDINGS.md",
        "uses_placeholders": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_handoff"] = {
        "artifact": str(handoff_path),
        "safe_to_share": True,
        "pending_blockers": beta_readiness["blockers"],
        "strict_audit_command": report["beta_readiness"]["strict_audit_command"],
        "content_policy": {
            "uses_placeholders": True,
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_local_paths": False,
            "records_operator_identity": False,
        },
    }
    report["real_pilot_command_pack"] = {
        "artifact": str(command_pack_path),
        "safe_to_share": True,
        "source": "platform_pilot_matrix",
        "includes_platform_commands": True,
        "includes_required_fields": True,
        "includes_strict_audit_command": True,
        "includes_system_output_no_pip_extra_contract": True,
        "system_output_no_pip_extra_contract": SYSTEM_OUTPUT_NO_PIP_EXTRA_CONTRACT,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_environment_checklist"] = {
        "artifact": str(environment_checklist_path),
        "safe_to_share": True,
        "source": "doctor:wav",
        "usable_as_beta_evidence": False,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_fixture_preflight"] = {
        "artifact": str(fixture_preflight_path),
        "safe_to_share": True,
        "source": "recommended_pilot_sequence + environment_checklist",
        "usable_as_beta_evidence": False,
        "prepares_real_transcription": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_transcription_readiness"] = {
        "artifact": str(transcription_readiness_path),
        "safe_to_share": True,
        "source": "recommended_pilot_sequence + environment_checklist",
        "usable_as_beta_evidence": False,
        "prepares_real_transcription": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_system_output_readiness"] = {
        "artifact": str(system_output_readiness_path),
        "safe_to_share": True,
        "source": "recommended_pilot_sequence + environment_checklist",
        "usable_as_beta_evidence": False,
        "prepares_audible_output": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_evidence_manifest"] = {
        "artifact": str(evidence_manifest_path),
        "safe_to_share": True,
        "source": "beta_readiness + evidence_audit",
        "usable_as_beta_evidence": False,
        "tracks_pending_and_closed_blockers": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_decision_gate"] = {
        "artifact": str(decision_gate_path),
        "safe_to_share": True,
        "source": "stability_gate + beta_readiness + environment_checklist + evidence_manifest",
        "usable_as_beta_evidence": False,
        "declares_real_world_pilot_scope": True,
        "declares_beta_and_stable_blockers": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_next_evidence_focus"] = {
        "artifact": str(next_focus_path),
        "safe_to_share": True,
        "source": "beta_readiness.next_evidence_focus + pilot_decision_gate",
        "usable_as_beta_evidence": False,
        "tracks_next_evidence_focus": True,
        "tracks_preparation_sequence": True,
        "preparation_sequence": report["next_evidence_focus_preparation_sequence"],
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_hard_stop_card"] = {
        "artifact": str(hard_stop_path),
        "safe_to_share": True,
        "source": "pilot_decision_gate.hard_stop_conditions + operator_actions",
        "usable_as_beta_evidence": False,
        "declares_hard_stop_conditions": True,
        "declares_operator_actions": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_evidence_intake_card"] = {
        "artifact": str(evidence_intake_path),
        "safe_to_share": True,
        "source": "evidence_manifest + strict_audit_command",
        "usable_as_beta_evidence": False,
        "tracks_expected_artifacts": True,
        "tracks_audit_commands": True,
        "suggested_roots": [
            "pilot_runs/manual/windows",
            "pilot_runs/manual/linux",
            "pilot_runs/manual/macos",
            "pilot_runs/output/system-real",
            "pilot_runs/transcription/real",
        ],
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_execution_card"] = {
        "artifact": str(execution_card_path),
        "safe_to_share": True,
        "source": "next_evidence_focus_preparation_sequence + pilot_decision_gate + evidence_intake_card",
        "usable_as_beta_evidence": False,
        "tracks_execution_order": True,
        "tracks_human_confirmations": True,
        "tracks_audit_closure": True,
        "focus": report["beta_readiness"]["next_evidence_focus"].get("name") or "ninguno",
        "operator_gate": _real_pilot_execution_operator_gate(report),
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }
    report["real_pilot_consent_card"] = _real_pilot_consent_card(report, consent_card_path)
    report["real_pilot_audit_closure_card"] = _real_pilot_audit_closure_card(report, audit_closure_path)
    report["real_pilot_rehearsal_card"] = _real_pilot_rehearsal_card(report, rehearsal_card_path)
    report["real_pilot_evidence_package_card"] = _real_pilot_evidence_package_card(
        report,
        evidence_package_path,
    )
    report["real_pilot_operator_brief_card"] = _real_pilot_operator_brief_card(report, operator_brief_path)
    report["real_pilot_run_sheet_card"] = _real_pilot_run_sheet_card(report, run_sheet_path)
    report["real_pilot_final_go_no_go_card"] = _real_pilot_final_go_no_go_card(report, final_go_no_go_path)
    report["real_pilot_local_receipt_card"] = _real_pilot_local_receipt_card(report, local_receipt_path)
    artifacts["real_pilot_findings_template"] = str(findings_template_path)
    artifacts["real_pilot_handoff"] = str(handoff_path)
    artifacts["real_pilot_command_pack"] = str(command_pack_path)
    artifacts["real_pilot_environment_checklist"] = str(environment_checklist_path)
    artifacts["real_pilot_fixture_preflight"] = str(fixture_preflight_path)
    artifacts["real_pilot_transcription_readiness"] = str(transcription_readiness_path)
    artifacts["real_pilot_system_output_readiness"] = str(system_output_readiness_path)
    artifacts["real_pilot_evidence_manifest"] = str(evidence_manifest_path)
    artifacts["real_pilot_decision_gate"] = str(decision_gate_path)
    artifacts["real_pilot_next_evidence_focus"] = str(next_focus_path)
    artifacts["real_pilot_hard_stop_card"] = str(hard_stop_path)
    artifacts["real_pilot_evidence_intake_card"] = str(evidence_intake_path)
    artifacts["real_pilot_execution_card"] = str(execution_card_path)
    artifacts["real_pilot_consent_card"] = str(consent_card_path)
    artifacts["real_pilot_audit_closure_card"] = str(audit_closure_path)
    artifacts["real_pilot_rehearsal_card"] = str(rehearsal_card_path)
    artifacts["real_pilot_evidence_package_card"] = str(evidence_package_path)
    artifacts["real_pilot_operator_brief_card"] = str(operator_brief_path)
    artifacts["real_pilot_run_sheet_card"] = str(run_sheet_path)
    artifacts["real_pilot_final_go_no_go_card"] = str(final_go_no_go_path)
    artifacts["real_pilot_local_receipt_card"] = str(local_receipt_path)
    artifacts["pilot_plan"] = str(plan_path)
    artifacts["pilot_report"] = str(report_path)
    findings_template_path.write_text(_format_real_pilot_findings_template_markdown(report), encoding="utf-8")
    handoff_path.write_text(_format_real_pilot_handoff_markdown(report), encoding="utf-8")
    command_pack_path.write_text(_format_real_pilot_command_pack_markdown(report), encoding="utf-8")
    environment_checklist_path.write_text(_format_real_pilot_environment_checklist_markdown(report), encoding="utf-8")
    fixture_preflight_path.write_text(_format_real_pilot_fixture_preflight_markdown(report), encoding="utf-8")
    transcription_readiness_path.write_text(_format_real_pilot_transcription_readiness_markdown(report), encoding="utf-8")
    system_output_readiness_path.write_text(
        _format_real_pilot_system_output_readiness_markdown(report),
        encoding="utf-8",
    )
    evidence_manifest_path.write_text(_format_real_pilot_evidence_manifest_markdown(report), encoding="utf-8")
    decision_gate_path.write_text(_format_real_pilot_decision_gate_markdown(report), encoding="utf-8")
    next_focus_path.write_text(_format_real_pilot_next_evidence_focus_markdown(report), encoding="utf-8")
    hard_stop_path.write_text(_format_real_pilot_hard_stop_card_markdown(report), encoding="utf-8")
    evidence_intake_path.write_text(_format_real_pilot_evidence_intake_card_markdown(report), encoding="utf-8")
    execution_card_path.write_text(_format_real_pilot_execution_card_markdown(report), encoding="utf-8")
    consent_card_path.write_text(_format_real_pilot_consent_card_markdown(report), encoding="utf-8")
    audit_closure_path.write_text(_format_real_pilot_audit_closure_markdown(report), encoding="utf-8")
    rehearsal_card_path.write_text(_format_real_pilot_rehearsal_markdown(report), encoding="utf-8")
    evidence_package_path.write_text(_format_real_pilot_evidence_package_markdown(report), encoding="utf-8")
    operator_brief_path.write_text(_format_real_pilot_operator_brief_markdown(report), encoding="utf-8")
    run_sheet_path.write_text(_format_real_pilot_run_sheet_markdown(report), encoding="utf-8")
    final_go_no_go_path.write_text(_format_real_pilot_final_go_no_go_markdown(report), encoding="utf-8")
    local_receipt_path.write_text(_format_real_pilot_local_receipt_markdown(report), encoding="utf-8")
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
                "--sample-rate 48000 --expected-system Windows --confirm-input-reviewed --json"
            ),
            "reason": "Requires real microphone hardware plus reviewed OS permissions, input device and room privacy.",
        },
        {
            "name": "system-speech",
            "command": (
                "python tools/output_pilot.py --speak --operator-present --confirm-audible "
                "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
                "--expected-system \"Windows|Linux|Darwin\" "
                "--output-dir pilot_runs/output/system-real --text \"Hola desde AuralisVoiceKit\" --json"
            ),
            "reason": "Plays real audio and requires the operator to review text privacy, audibility and voice quality.",
        },
        {
            "name": "real-transcription",
            "command": (
                "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
                "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
                "--backend whisper --model base --normalize "
                "--expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 "
                "--min-audio-seconds 0.2 --max-audio-seconds 60 "
                "--confirm-quality-reviewed --require-target-backend-ready "
                "--output-dir <pilot-output-dir> --json"
            ),
            "reason": (
                "Uses a real non-sensitive audio file and requires audio review, reference review, "
                "a passing reference privacy scan and quality review before beta evidence."
            ),
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
        required_fields = [field["path"] for field in requirement["fields"]]
        conditional_required_fields = _conditional_required_fields(requirement)
        steps.append(
            {
                "name": blocker,
                "title": requirement["title"],
                "artifact": requirement["artifact"],
                "command": requirement["command"],
                "required_fields": required_fields,
                "conditional_required_fields": conditional_required_fields,
                "policy_required_fields": _policy_required_fields(required_fields, conditional_required_fields),
                "reason": "Evidencia real requerida antes de beta publica.",
                **_strict_backend_guard_metadata(blocker),
            }
        )
    return steps


def _conditional_required_fields(requirement: dict[str, Any]) -> list[dict[str, Any]]:
    fields = []
    for conditional in requirement.get("conditional_fields", []):
        condition = conditional["when"]
        fields.append(
            {
                "when": {
                    "path": condition["path"],
                    "expected": condition["expected"],
                },
                "fields": [field["path"] for field in conditional["fields"]],
            }
        )
    return fields


def _policy_required_fields(
    required_fields: list[str],
    conditional_required_fields: list[dict[str, Any]] | None = None,
) -> list[str]:
    policy_fields: list[str] = []
    for field in required_fields:
        if ".freedom_policy." in field:
            policy_fields.append(field)
    for conditional in conditional_required_fields or []:
        for field in conditional.get("fields", []):
            if ".freedom_policy." in field:
                policy_fields.append(field)
    return _ordered_unique(policy_fields)


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _with_policy_required_fields(focus: dict[str, Any]) -> dict[str, Any]:
    if not focus:
        return focus
    enriched = dict(focus)
    required_fields = list(enriched.get("required_fields", []))
    conditional_required_fields = list(enriched.get("conditional_required_fields", []))
    enriched["policy_required_fields"] = _policy_required_fields(required_fields, conditional_required_fields)
    return enriched


def _strict_backend_guard_metadata(step_name: str) -> dict[str, Any]:
    if step_name in {"real_transcription_quality", "real-transcription-quality"}:
        return {
            "strict_backend_guard_required": True,
            "strict_backend_guard_flag": "--require-target-backend-ready",
            "strict_backend_guard_field": "target_backend_ready_required",
        }
    if step_name in {"system_output_audible", "system-output-audible"}:
        return {
            "strict_backend_guard_required": True,
            "strict_backend_guard_flag": "--require-output-backend-ready",
            "strict_backend_guard_field": "output_backend_ready_required",
        }
    if step_name in {
        "windows_wasapi_capture",
        "windows-wasapi-capture",
        "ubuntu_linux_capture",
        "ubuntu-linux-capture",
        "macos_capture",
        "macos-capture",
    }:
        return {
            "strict_backend_guard_required": True,
            "strict_backend_guard_flag": "--require-capture-backend-ready",
            "strict_backend_guard_field": "capture_backend_ready_required",
        }
    return {
        "strict_backend_guard_required": False,
        "strict_backend_guard_flag": None,
        "strict_backend_guard_field": None,
    }


def _recommended_pilot_sequence(
    next_beta_evidence_steps: list[dict[str, Any]],
    *,
    ready_for_beta: bool,
) -> list[dict[str, Any]]:
    hardware_required_blockers = {
        "windows_wasapi_capture",
        "system_output_audible",
        "ubuntu_linux_capture",
        "macos_capture",
    }
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
                "conditional_required_fields": step.get("conditional_required_fields", []),
                "policy_required_fields": step.get("policy_required_fields", []),
                "requires_hardware": step["name"] in hardware_required_blockers,
                "requires_operator": step["name"] == "system_output_audible",
                "requires_non_sensitive_audio": step["name"] == "real_transcription_quality",
                "review_required": True,
                "reason": step["reason"],
                **_strict_backend_guard_metadata(step["name"]),
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
                **_strict_backend_guard_metadata("audit-evidence"),
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
                **_strict_backend_guard_metadata("refresh-beta-checklist"),
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
        **_strict_backend_guard_metadata("transcription-audio-fixture"),
    }


def _transcription_audio_fixture_openai_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "transcription-audio-fixture-openai",
        "title": "Transcription audio fixture for OpenAI",
        "command": (
            "python tools/pilot_audio_fixture.py --output-dir pilot_runs/transcription/fixture-openai "
            "--format mp3 --duration 1.0 --sample-rate 16000 --run-preflight "
            f"--preflight-backend openai --preflight-model {OPENAI_TRANSCRIPTION_MODEL} "
            f"--preflight-timeout-seconds {OPENAI_TIMEOUT_SECONDS} "
            "--min-audio-seconds 0.2 --max-audio-seconds 60 --json"
        ),
        "artifact": "pilot-audio-fixture-report.json",
        "required_fields": [
            "project",
            "generated_public_fixture",
            "contains_private_audio",
            "usable_as_beta_evidence",
            "files",
            "preflight.backend",
            "preflight.model",
            "preflight.transcription_timeout_seconds",
            "preflight.passed",
            "passed",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": False,
        "review_required": False,
        "reason": (
            "Genera un MP3 sintetico publico y una plantilla OpenAI con timeout explicito "
            "sin ejecutar red ni modelo."
        ),
        **_strict_backend_guard_metadata("transcription-audio-fixture-openai"),
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
            "audio.duration_gate.enabled",
            "audio.duration_gate.passed",
            "target_backend.available",
            "preflight_decision.decision",
            "preflight_decision.blocking_reasons",
            "preflight_decision.backend_ready",
            "preflight_decision.next_action",
            "audio.audio_file_name_redacted",
            "audio.audio_file_extension",
            "audio.audio_confirmed_non_sensitive",
            "transcription_checklist.records_audio_file_name",
            "transcription_checklist.records_transcript_text",
            "transcription_checklist.redacts_expected_text",
            "transcription_checklist.records_expected_text_file_name",
            "artifacts.transcription_review_checklist",
            "artifacts.real_transcription_next_step",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": True,
        "review_required": True,
        "reason": (
            "Confirma que el MP3 propio se decodifica con ffmpeg y genera "
            "preflight_decision, transcription-review-checklist.md y real-transcription-next-step.md antes de ejecutar un modelo real."
        ),
        **_strict_backend_guard_metadata("transcription-audio-preflight"),
    }


def _transcription_openai_audio_preflight_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "transcription-openai-mp3-preflight",
        "title": "OpenAI transcription MP3 preflight",
        "command": (
            "python tools/transcription_pilot.py --preflight-only --audio sample.mp3 "
            "--audio-non-sensitive --backend openai "
            f"--model {OPENAI_TRANSCRIPTION_MODEL} --normalize "
            f"--timeout-seconds {OPENAI_TIMEOUT_SECONDS} "
            "--require-openai-api-key "
            "--min-audio-seconds 0.2 --max-audio-seconds 60 --json"
        ),
        "artifact": "transcription-pilot-report.json",
        "required_fields": [
            "project",
            "preflight_only",
            "backend",
            "model",
            "transcription_timeout_seconds",
            "credentials.checked",
            "credentials.openai_api_key_required",
            "credentials.openai_api_key_present",
            "credentials.records_openai_api_key",
            "audio.decoded",
            "audio.duration_gate.enabled",
            "audio.duration_gate.passed",
            "target_backend.available",
            "preflight_decision.decision",
            "preflight_decision.blocking_reasons",
            "preflight_decision.backend_ready",
            "preflight_decision.next_action",
            "audio.audio_file_name_redacted",
            "audio.audio_file_extension",
            "audio.audio_confirmed_non_sensitive",
            "artifacts.transcription_review_checklist",
            "artifacts.real_transcription_next_step",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": True,
        "review_required": True,
        "reason": (
            "Prepara el MP3 propio para OpenAI sin ejecutar red ni modelo; confirma ffmpeg, "
            "timeout, presencia sanitizada de OPENAI_API_KEY, target_backend e instrucciones de instalacion "
            "antes de la transcripcion real."
        ),
        **_strict_backend_guard_metadata("transcription-openai-mp3-preflight"),
    }


def _real_openai_transcription_command() -> str:
    return (
        "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
        "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
        f"--backend openai --model {OPENAI_TRANSCRIPTION_MODEL} "
        f"--timeout-seconds {OPENAI_TIMEOUT_SECONDS} "
        "--expected-text-file <expected-text-path> --min-word-accuracy 0.75 "
        "--min-audio-seconds 0.2 --max-audio-seconds 60 "
        "--confirm-quality-reviewed --require-target-backend-ready --require-openai-api-key "
        "--output-dir <pilot-output-dir> --json"
    )


def _system_output_operator_checklist_step(order: int) -> dict[str, Any]:
    return {
        "order": order,
        "name": "system-output-operator-checklist",
        "title": "System output operator checklist",
        "command": "python tools/output_pilot.py --output-dir pilot_runs/output/system-dry-run --json",
        "artifact": "output-operator-checklist.md",
        "required_fields": [
            "target_output_backend.available",
            "target_output_backend.readiness_plan.uses_pip_extra",
            "target_output_backend.readiness_plan.python_extra",
            "target_output_backend.readiness_plan.pip_command",
            "operator_checklist.records_operator_identity",
            "operator_checklist.redacts_spoken_text",
            "operator_checklist.ready_for_beta_evidence",
            "system_output_command_card.safe_to_share",
            "system_output_command_card.uses_placeholders",
            "system_output_command_card.uses_pip_extra",
            "system_output_command_card.python_extra",
            "system_output_command_card.pip_command",
            "system_output_command_card.system_dependency_plan.safe_to_share",
            "system_output_command_card.system_dependency_plan.post_install_check_plays_audio",
            "system_output_command_card.system_dependency_plan.records_local_paths",
            "artifacts.operator_checklist",
            "artifacts.system_output_next_step",
        ],
        "requires_hardware": False,
        "requires_operator": False,
        "requires_non_sensitive_audio": False,
        "review_required": True,
        "reason": (
            "Prepara el checklist redactado y system-output-next-step.md antes de ejecutar "
            "salida audible real con operador presente."
        ),
        **_strict_backend_guard_metadata("system-output-operator-checklist"),
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
                "--device default --sample-rate 48000 --expected-system Windows "
                "--confirm-input-reviewed --require-capture-backend-ready --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("windows-wasapi-capture"),
            "notes": (
                "Repetir con el guard actual, revisar permisos/dispositivo de entrada y conservar "
                "manual-capture-checklist.md y manual-capture-command.md."
            ),
        },
        {
            "name": "ubuntu-linux-capture",
            "platform": "Ubuntu/Linux",
            "blocker": "ubuntu_linux_capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend sounddevice "
                "--device default --expected-system Linux --confirm-input-reviewed "
                "--require-capture-backend-ready --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("ubuntu-linux-capture"),
            "notes": (
                "Requiere microfono, permisos de audio, dispositivo de entrada revisado, "
                "PortAudio con sounddevice o PyAudio, manual-capture-checklist.md y "
                "manual-capture-command.md. "
                "Si el stack disponible es PyAudio, repetir el comando con --backend pyaudio."
            ),
        },
        {
            "name": "macos-capture",
            "platform": "macOS",
            "blocker": "macos_capture",
            "command": (
                "python tools/manual_pilot.py --capture-test --backend sounddevice "
                "--device default --expected-system Darwin --confirm-input-reviewed "
                "--require-capture-backend-ready --json"
            ),
            "artifact": "manual-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("macos-capture"),
            "notes": (
                "Requiere permiso de microfono en macOS, revisar el dispositivo default, confirmar "
                "entorno no sensible y conservar manual-capture-checklist.md y manual-capture-command.md. "
                "Usar --backend sounddevice o --backend pyaudio segun el stack instalado."
            ),
        },
        {
            "name": "system-output-audible",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": "system_output_audible",
            "command": (
                "python tools/output_pilot.py --speak --operator-present "
                "--confirm-audible --confirm-text-reviewed --confirm-voice-reviewed "
                "--require-output-backend-ready "
                "--expected-system \"Windows|Linux|Darwin\" "
                "--output-dir pilot_runs/output/system-real "
                "--text \"Hola desde AuralisVoiceKit\" --json"
            ),
            "artifact": "output-pilot-report.json",
            "requires_hardware": True,
            "requires_operator": True,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("system-output-audible"),
            "notes": (
                "Ejecutar solo con operador presente; confirmar privacidad del texto, audibilidad, "
                "plataforma esperada, output_backend_ready_required=true, revision de voz "
                f"{', '.join(SYSTEM_OUTPUT_NO_PIP_EXTRA_CONTRACT)}, "
                "operator_checklist.redacts_spoken_text=true, "
                "next_system_output.records_spoken_text=false, "
                "system_output_command_card.records_spoken_text=false y "
                "system-output-next-step.md antes de beta."
            ),
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
            "required_fields": _transcription_audio_fixture_step(1)["required_fields"],
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("transcription-audio-fixture"),
            "notes": "Fixture sintetico y publico para validar ffmpeg; no cuenta como evidencia beta.",
        },
        {
            "name": "transcription-audio-fixture-openai",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": None,
            "command": _transcription_audio_fixture_openai_step(1)["command"],
            "artifact": "pilot-audio-fixture-report.json",
            "required_fields": _transcription_audio_fixture_openai_step(1)["required_fields"],
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": False,
            **_strict_backend_guard_metadata("transcription-audio-fixture-openai"),
            "notes": (
                "Fixture sintetico y publico para preparar OpenAI con "
                f"--preflight-timeout-seconds {OPENAI_TIMEOUT_SECONDS}; no usa red ni modelo y no cuenta como evidencia beta."
            ),
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
            "required_fields": _transcription_audio_preflight_step(1)["required_fields"],
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": True,
            **_strict_backend_guard_metadata("transcription-mp3-preflight"),
            "notes": (
                "Paso previo: valida ffmpeg y metadata, luego revisa "
                "real-transcription-next-step.md antes de transcribir con un modelo."
            ),
        },
        {
            "name": "transcription-openai-mp3-preflight",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": None,
            "command": _transcription_openai_audio_preflight_step(1)["command"],
            "artifact": "transcription-pilot-report.json",
            "required_fields": _transcription_openai_audio_preflight_step(1)["required_fields"],
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": True,
            **_strict_backend_guard_metadata("transcription-openai-mp3-preflight"),
            "notes": (
                "Paso previo OpenAI: valida ffmpeg, guardas de duracion, "
                f"modelo {OPENAI_TRANSCRIPTION_MODEL}, timeout {OPENAI_TIMEOUT_SECONDS}, "
                "target_backend.available y real-transcription-next-step.md sin ejecutar red ni modelo."
            ),
        },
        {
            "name": "real-transcription-quality",
            "platform": "Windows / Ubuntu/Linux / macOS",
            "blocker": "real_transcription_quality",
            "command": (
                "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 "
                "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
                "--backend whisper --model base --normalize "
                "--expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 "
                "--min-audio-seconds 0.2 --max-audio-seconds 60 "
                "--confirm-quality-reviewed --require-target-backend-ready "
                "--output-dir <pilot-output-dir> --json"
            ),
            "artifact": "transcription-pilot-report.json",
            "requires_hardware": False,
            "requires_operator": False,
            "requires_non_sensitive_audio": True,
            **_strict_backend_guard_metadata("real-transcription-quality"),
            "notes": (
                "Usar un MP3 propio no sensible, revisar privacidad del audio y referencia, "
                "confirmar target_backend.available=true, target_backend_ready_required=true, "
                "usar --timeout-seconds 30 si el backend real es openai, "
                "audio.generated_synthetic_audio=false, audio.decoded=true, "
                "audio.duration_gate.enabled=true, audio.duration_gate.passed=true, "
                "transcript.text_redacted=true, reference_privacy_scan.passed=true "
                "real_transcription_command_card.safe_to_share=true, "
                "real_transcription_command_card.uses_placeholders=true "
                "y confirmar revision humana de calidad."
            ),
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


def _real_pilot_environment_checklist(doctor: Any) -> list[dict[str, Any]]:
    checks = {check.name: check for check in doctor.checks}
    ffmpeg_ready = _doctor_check_ready(checks, "executable:ffmpeg")
    whisper_ready = _doctor_check_ready(checks, "backend:transcription:whisper")
    openai_ready = _doctor_check_ready(checks, "backend:transcription:openai")
    output_ready = _doctor_check_ready(checks, "backend:output:system")
    system = getattr(doctor, "system", "unknown")

    rows = [
        _environment_row(
            checks,
            name="python-runtime",
            source="python",
            required_for="todos los pilotos",
            action_when_missing="Instalar una version de Python soportada por el paquete.",
        ),
        _environment_row(
            checks,
            name="ffmpeg-compressed-audio",
            source="executable:ffmpeg",
            required_for="preflight MP3/FLAC y transcripcion real con audio comprimido",
            action_when_missing="Instalar ffmpeg o definir AURALIS_FFMPEG_PATH antes de usar MP3/FLAC.",
        ),
        _environment_row(
            checks,
            name="windows-wasapi-capture",
            source="backend:capture:wasapi",
            required_for="captura real Windows",
            action_when_missing="Instalar el extra sounddevice y probar en Windows con --expected-system Windows.",
            target_system="Windows",
            current_system=system,
        ),
        _environment_row(
            checks,
            name="linux-sounddevice-capture",
            source="backend:capture:sounddevice",
            required_for="captura real Ubuntu/Linux",
            action_when_missing="Instalar PortAudio/sounddevice o usar el fallback pyaudio en Ubuntu/Linux.",
            target_system="Linux",
            current_system=system,
        ),
        _environment_row(
            checks,
            name="linux-pyaudio-capture",
            source="backend:capture:pyaudio",
            required_for="captura real Ubuntu/Linux como alternativa",
            action_when_missing="Instalar PortAudio y el extra pyaudio si sounddevice no es viable.",
            target_system="Linux",
            current_system=system,
        ),
        _environment_row(
            checks,
            name="macos-sounddevice-capture",
            source="backend:capture:sounddevice",
            required_for="captura real macOS",
            action_when_missing="Instalar sounddevice y revisar permisos de microfono en macOS.",
            target_system="Darwin",
            current_system=system,
        ),
        _environment_row(
            checks,
            name="macos-pyaudio-capture",
            source="backend:capture:pyaudio",
            required_for="captura real macOS como alternativa",
            action_when_missing="Instalar PortAudio/PyAudio y revisar permisos de microfono en macOS.",
            target_system="Darwin",
            current_system=system,
        ),
        _environment_row(
            checks,
            name="system-output-backend",
            source="backend:output:system",
            required_for="salida audible real",
            action_when_missing="Instalar o habilitar el comando de voz del sistema antes del piloto audible.",
        ),
        _environment_row(
            checks,
            name="whisper-transcription-backend",
            source="backend:transcription:whisper",
            required_for="transcripcion real local",
            action_when_missing="Instalar auralisvoicekit[whisper] antes de usar --backend whisper.",
        ),
        _environment_row(
            checks,
            name="openai-transcription-backend",
            source="backend:transcription:openai",
            required_for="transcripcion real por API",
            action_when_missing="Instalar auralisvoicekit[openai] y configurar credenciales antes de usar --backend openai.",
        ),
    ]
    rows.extend(
        [
            {
                "name": "local-real-transcription-ready",
                "source": "executable:ffmpeg + transcription backend",
                "required_for": "piloto real de transcripcion en esta maquina",
                "status": "ok" if ffmpeg_ready and (whisper_ready or openai_ready) else "warning",
                "ready": ffmpeg_ready and (whisper_ready or openai_ready),
                "target_system": None,
                "current_system": system,
                "action": (
                    "Ejecutar preflight MP3 y luego transcripcion real con audio no sensible."
                    if ffmpeg_ready and (whisper_ready or openai_ready)
                    else "Instalar ffmpeg y al menos un backend real: auralisvoicekit[whisper] u [openai]."
                ),
            },
            {
                "name": "local-system-output-ready",
                "source": "backend:output:system",
                "required_for": "piloto audible en esta maquina",
                "status": "ok" if output_ready else "warning",
                "ready": output_ready,
                "target_system": None,
                "current_system": system,
                "action": (
                    "Ejecutar piloto audible solo con operador presente y texto publico."
                    if output_ready
                    else "Habilitar un comando de voz del sistema antes del piloto audible."
                ),
            },
        ]
    )
    return rows


def _environment_row(
    checks: dict[str, Any],
    *,
    name: str,
    source: str,
    required_for: str,
    action_when_missing: str,
    target_system: str | None = None,
    current_system: str | None = None,
) -> dict[str, Any]:
    check = checks.get(source)
    if target_system is not None and current_system != target_system:
        return {
            "name": name,
            "source": source,
            "required_for": required_for,
            "status": "target-system-required",
            "ready": False,
            "target_system": target_system,
            "current_system": current_system,
            "action": f"Ejecutar este check en {target_system}; este artifact local viene de {current_system}.",
        }
    if check is None:
        return {
            "name": name,
            "source": source,
            "required_for": required_for,
            "status": "missing-check",
            "ready": False,
            "target_system": target_system,
            "current_system": current_system,
            "action": action_when_missing,
        }
    ready = check.status is DiagnosticStatus.OK
    return {
        "name": name,
        "source": source,
        "required_for": required_for,
        "status": check.status.value,
        "ready": ready,
        "target_system": target_system,
        "current_system": current_system,
        "action": "Listo para este preflight local." if ready else check.hint or action_when_missing,
    }


def _doctor_check_ready(checks: dict[str, Any], name: str) -> bool:
    check = checks.get(name)
    return bool(check is not None and check.status is DiagnosticStatus.OK)


def _real_pilot_evidence_manifest(
    beta_readiness: dict[str, Any],
    beta_audit: dict[str, Any],
    next_beta_evidence_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    closed_by_blocker: dict[str, dict[str, Any]] = {}
    for artifact in beta_audit["artifacts"]:
        for candidate in artifact["candidates"]:
            if not candidate["ok"]:
                continue
            closed_by_blocker[candidate["name"]] = {
                "file": artifact["file"],
                "artifact": artifact["artifact"],
                "title": candidate["title"],
                "required_fields": [field["path"] for field in candidate["fields"]],
                "policy_required_fields": _policy_required_fields([field["path"] for field in candidate["fields"]]),
            }

    rows: list[dict[str, Any]] = []
    pending_names = set()
    for step in next_beta_evidence_steps:
        pending_names.add(step["name"])
        rows.append(
            {
                "status": "pending",
                "blocker": step["name"],
                "title": step["title"],
                "artifact": step["artifact"],
                "command": step["command"],
                "required_fields": step["required_fields"],
                "conditional_required_fields": step.get("conditional_required_fields", []),
                "policy_required_fields": step.get("policy_required_fields", []),
                "accepted_json_artifact": None,
                "review_state": "real-evidence-required",
                **_strict_backend_guard_metadata(step["name"]),
            }
        )
    for blocker in beta_audit["satisfied_blockers"]:
        if blocker in pending_names:
            continue
        closed = closed_by_blocker.get(blocker, {})
        rows.append(
            {
                "status": "closed",
                "blocker": blocker,
                "title": closed.get("title", blocker),
                "artifact": closed.get("artifact", "unknown"),
                "command": None,
                "required_fields": closed.get("required_fields", []),
                "conditional_required_fields": [],
                "policy_required_fields": closed.get("policy_required_fields", []),
                "accepted_json_artifact": closed.get("file"),
                "review_state": "closed-by-accepted-json",
                **_strict_backend_guard_metadata(blocker),
            }
        )

    return {
        "ready_for_beta_by_json_evidence": beta_audit["ready_for_beta_by_evidence"],
        "ready_for_beta": beta_readiness["ready_for_beta"],
        "pending_blockers": beta_readiness["blockers"],
        "missing_json_blockers": beta_audit["missing_blockers"],
        "closed_blockers": beta_audit["satisfied_blockers"],
        "blocker_summaries": beta_audit["blocker_summaries"],
        "next_evidence_focus": _with_policy_required_fields(beta_audit["next_evidence_focus"]),
        "privacy_audit": beta_audit["privacy_audit"],
        "privacy_remediation_plan": beta_audit["privacy_remediation_plan"],
        "accepted_json_artifacts": _pilot_plan_artifact_summary(beta_audit["artifacts"]),
        "ignored_json_artifacts": beta_audit["ignored_details"],
        "pending_count": len(beta_readiness["blockers"]),
        "missing_json_count": len(beta_audit["missing_blockers"]),
        "closed_count": len(beta_audit["satisfied_blockers"]),
        "ignored_count": beta_audit["ignored_count"],
        "rows": rows,
        "strict_audit_command": beta_readiness["strict_audit_command"],
        "refresh_checklist_command": (
            "python tools/beta_readiness.py --evidence pilot_runs/manual "
            "--evidence pilot_runs/output --evidence pilot_runs/transcription "
            "--output BETA_CHECKLIST.md --fail-on-blockers --json"
        ),
        "content_policy": {
            "usable_as_beta_evidence": False,
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_fixture_preflight_card(report: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe card for the synthetic transcription fixture preflight."""

    sequence = {step["name"]: step for step in report["recommended_pilot_sequence"]}
    fixture_step = sequence.get("transcription-audio-fixture", _transcription_audio_fixture_step(1))
    openai_fixture_step = _transcription_audio_fixture_openai_step(1)
    own_audio_step = sequence.get("transcription-audio-preflight", _transcription_audio_preflight_step(2))
    openai_own_audio_step = _transcription_openai_audio_preflight_step(2)
    environment = {row["name"]: row for row in report["environment_checklist"]}
    ffmpeg_check = environment.get("ffmpeg-compressed-audio")
    backend_checks = [
        row
        for row in report["environment_checklist"]
        if row["name"] in {"whisper-transcription-backend", "openai-transcription-backend"}
    ]

    return {
        "status": "recommended" if "real_transcription_quality" in report["beta_readiness"]["blockers"] else "complete",
        "usable_as_beta_evidence": False,
        "fixture_command": fixture_step["command"],
        "fixture_artifact": fixture_step["artifact"],
        "openai_fixture_command": openai_fixture_step["command"],
        "openai_fixture_artifact": openai_fixture_step["artifact"],
        "own_audio_preflight_command": own_audio_step["command"],
        "own_audio_preflight_artifact": own_audio_step["artifact"],
        "openai_own_audio_preflight_command": openai_own_audio_step["command"],
        "openai_own_audio_preflight_artifact": openai_own_audio_step["artifact"],
        "expected_artifacts": [
            "pilot-audio-fixture-report.json",
            "pilot-audio-fixture-findings.md",
            "transcription-review-checklist.md",
            "real-transcription-next-step.md",
        ],
        "required_fields": fixture_step["required_fields"],
        "openai_fixture_required_fields": openai_fixture_step["required_fields"],
        "own_audio_required_fields": own_audio_step["required_fields"],
        "openai_own_audio_required_fields": openai_own_audio_step["required_fields"],
        "ffmpeg": {
            "status": ffmpeg_check["status"] if ffmpeg_check else "unknown",
            "ready": bool(ffmpeg_check["ready"]) if ffmpeg_check else False,
            "action": ffmpeg_check["action"] if ffmpeg_check else "Run auralis doctor before fixture preflight.",
        },
        "target_backend_checks": [
            {
                "name": row["name"],
                "status": row["status"],
                "ready": row["ready"],
                "action": row["action"],
            }
            for row in backend_checks
        ],
        "operator_actions": [
            "Run the synthetic fixture command before using private or real audio.",
            "Use the OpenAI fixture command when the real backend will be openai; it prepares timeout and model placeholders without network.",
            "Use the OpenAI MP3 preflight with --require-openai-api-key to check credential presence without recording the key.",
            "Confirm the fixture report says generated_public_fixture=true and usable_as_beta_evidence=false.",
            "Review transcription-review-checklist.md and real-transcription-next-step.md from the preflight artifacts.",
            "Replace sample.mp3 with your own non-sensitive MP3 only after the synthetic preflight is understood.",
        ],
        "hard_stop_conditions": [
            "Do not treat the synthetic fixture as beta evidence.",
            "Do not run real transcription if ffmpeg cannot decode the MP3 or the duration gate fails.",
            "Do not pass --confirm-audio-reviewed, --confirm-reference-reviewed or --confirm-quality-reviewed before local review.",
            "Do not paste audio names, transcript text, expected text or local paths into public findings.",
        ],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_transcription_readiness_card(report: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe card for the real transcription pilot."""

    sequence = {step["name"]: step for step in report["recommended_pilot_sequence"]}
    fixture_step = sequence.get("transcription-audio-fixture", _transcription_audio_fixture_step(1))
    openai_fixture_step = _transcription_audio_fixture_openai_step(1)
    preflight_step = sequence.get("transcription-audio-preflight", _transcription_audio_preflight_step(2))
    openai_preflight_step = _transcription_openai_audio_preflight_step(2)
    real_step = sequence.get(
        "real_transcription_quality",
        {
            "command": (
                "python tools/transcription_pilot.py --real-transcription --audio <audio-path> "
                "--audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed "
                "--backend whisper --model base --normalize --expected-text-file <expected-text-path> "
                "--min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 "
                "--confirm-quality-reviewed --require-target-backend-ready "
                "--output-dir <pilot-output-dir> --json"
            ),
            "artifact": "transcription-pilot-report.json",
            "required_fields": [
                "real_transcription_requested",
                "target_backend.available",
                "target_backend_ready_required",
                "audio.generated_synthetic_audio",
                "audio.audio_confirmed_non_sensitive",
                "audio.decoded",
                "audio.audio_file_name_redacted",
                "audio.duration_gate.enabled",
                "audio.duration_gate.passed",
                "transcript.text_redacted",
                "audio_review_confirmed",
                "reference_review_confirmed",
                "reference_privacy_scan.passed",
                "quality_review_confirmed",
                "transcription_checklist.redacts_transcript_text",
                "transcription_checklist.redacts_expected_text",
                "transcription_checklist.ready_for_beta_evidence",
                "real_transcription_command_card.safe_to_share",
                "real_transcription_command_card.uses_placeholders",
                "real_transcription_command_card.records_transcript_text",
                "real_transcription_command_card.records_expected_text",
            ],
        },
    )
    environment = {row["name"]: row for row in report["environment_checklist"]}
    ffmpeg_check = environment.get("ffmpeg-compressed-audio")
    local_transcription = environment.get("local-real-transcription-ready")
    backend_checks = [
        row
        for row in report["environment_checklist"]
        if row["name"] in {"whisper-transcription-backend", "openai-transcription-backend"}
    ]

    return {
        "status": "recommended" if "real_transcription_quality" in report["beta_readiness"]["blockers"] else "complete",
        "usable_as_beta_evidence": False,
        "fixture_command": fixture_step["command"],
        "fixture_artifact": fixture_step["artifact"],
        "openai_fixture_command": openai_fixture_step["command"],
        "openai_fixture_artifact": openai_fixture_step["artifact"],
        "preflight_command": preflight_step["command"],
        "preflight_artifact": preflight_step["artifact"],
        "openai_preflight_command": openai_preflight_step["command"],
        "openai_preflight_artifact": openai_preflight_step["artifact"],
        "real_command": real_step["command"],
        "real_artifact": real_step["artifact"],
        "openai_real_command": _real_openai_transcription_command(),
        "openai_real_artifact": "transcription-pilot-report.json",
        "expected_artifacts": [
            "pilot-audio-fixture-report.json",
            "transcription-pilot-report.json",
            "transcription-pilot-findings.md",
            "transcription-review-checklist.md",
            "real-transcription-next-step.md",
            "real-transcription-command.md",
        ],
        "fixture_required_fields": fixture_step["required_fields"],
        "openai_fixture_required_fields": openai_fixture_step["required_fields"],
        "preflight_required_fields": preflight_step["required_fields"],
        "openai_preflight_required_fields": openai_preflight_step["required_fields"],
        "real_required_fields": real_step["required_fields"],
        "real_conditional_required_fields": real_step.get("conditional_required_fields", []),
        "ffmpeg": {
            "status": ffmpeg_check["status"] if ffmpeg_check else "unknown",
            "ready": bool(ffmpeg_check["ready"]) if ffmpeg_check else False,
            "action": ffmpeg_check["action"] if ffmpeg_check else "Run auralis doctor before real transcription.",
        },
        "local_transcription": {
            "status": local_transcription["status"] if local_transcription else "unknown",
            "ready": bool(local_transcription["ready"]) if local_transcription else False,
            "action": (
                local_transcription["action"]
                if local_transcription
                else "Run auralis doctor before real transcription."
            ),
        },
        "target_backend_checks": [
            {
                "name": row["name"],
                "status": row["status"],
                "ready": row["ready"],
                "action": row["action"],
            }
            for row in backend_checks
        ],
        "operator_actions": [
            "Run the synthetic fixture command first; it proves the path without private audio.",
            "If the target backend is OpenAI, run the OpenAI fixture command and OpenAI preflight command before the real model call.",
            "Run the preflight with your own non-sensitive MP3 and review transcription-review-checklist.md.",
            "Use --require-target-backend-ready so the real pilot fails before model execution if the backend is missing.",
            "Use --timeout-seconds 30 when running the real pilot with --backend openai.",
            "Use --require-openai-api-key with --backend openai; artifacts only record credential presence.",
            "Pass --confirm-audio-reviewed only after privacy review of the audio is complete.",
            "Pass --confirm-reference-reviewed only after the expected text or expected text file is public-safe.",
            "Pass --confirm-quality-reviewed only after local human review of quality metrics and redacted artifacts.",
        ],
        "hard_stop_conditions": [
            "Do not run a real transcription model with private or unreviewed audio.",
            "Do not run real transcription if ffmpeg fails, the duration gate fails or no target backend is available.",
            "Do not use --confirm-audio-reviewed, --confirm-reference-reviewed or --confirm-quality-reviewed before local review.",
            "Do not publish transcript text, expected text, audio file names, reference file names or local paths.",
            "Do not count this readiness artifact as beta evidence; only sanitized JSON from the real pilot can close the blocker.",
        ],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_system_output_readiness_card(report: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe card for the audible system output pilot."""

    sequence = {step["name"]: step for step in report["recommended_pilot_sequence"]}
    checklist_step = sequence.get("system-output-operator-checklist", _system_output_operator_checklist_step(1))
    audible_step = sequence.get(
        "system_output_audible",
        {
            "command": (
                "python tools/output_pilot.py --speak --operator-present --confirm-audible "
                "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
                "--expected-system \"Windows|Linux|Darwin\" --output-dir pilot_runs/output/system-real "
                "--text \"<public-spoken-text>\" --json"
            ),
            "artifact": "output-pilot-report.json",
            "required_fields": [
                "system_guard.expected_system_matched",
                "target_output_backend.available",
                "target_output_backend.readiness_plan.uses_pip_extra",
                "target_output_backend.readiness_plan.python_extra",
                "target_output_backend.readiness_plan.pip_command",
                "output_backend_ready_required",
                "text_review_confirmed",
                "spoken_text_privacy_scan.passed",
                "voice_review_confirmed",
                "operator_checklist.records_operator_identity",
                "operator_checklist.redacts_spoken_text",
                "operator_checklist.commands_available",
                "operator_checklist.ready_for_real_audio",
                "operator_checklist.ready_for_beta_evidence",
                "next_system_output.uses_placeholders",
                "next_system_output.records_spoken_text",
                "next_system_output.records_operator_identity",
                "system_output_command_card.safe_to_share",
                "system_output_command_card.uses_placeholders",
                "system_output_command_card.uses_pip_extra",
                "system_output_command_card.python_extra",
                "system_output_command_card.pip_command",
                "system_output_command_card.system_dependency_plan.safe_to_share",
                "system_output_command_card.system_dependency_plan.post_install_check_plays_audio",
                "system_output_command_card.system_dependency_plan.records_local_paths",
                "system_output_command_card.records_spoken_text",
                "system_output_command_card.records_operator_identity",
            ],
        },
    )
    environment = {row["name"]: row for row in report["environment_checklist"]}
    output_backend = environment.get("system-output-backend")
    local_output = environment.get("local-system-output-ready")

    return {
        "status": "recommended" if "system_output_audible" in report["beta_readiness"]["blockers"] else "complete",
        "usable_as_beta_evidence": False,
        "dry_run_command": checklist_step["command"],
        "dry_run_artifact": checklist_step["artifact"],
        "audible_command": audible_step["command"],
        "audible_artifact": audible_step["artifact"],
        "expected_artifacts": [
            "output-pilot-report.json",
            "output-pilot-findings.md",
            "output-operator-checklist.md",
            "system-output-next-step.md",
        ],
        "required_fields": checklist_step["required_fields"],
        "audible_required_fields": audible_step["required_fields"],
        "no_pip_extra_contract": SYSTEM_OUTPUT_NO_PIP_EXTRA_CONTRACT,
        "output_backend": {
            "status": output_backend["status"] if output_backend else "unknown",
            "ready": bool(output_backend["ready"]) if output_backend else False,
            "action": output_backend["action"] if output_backend else "Run auralis doctor before audible output.",
        },
        "local_output": {
            "status": local_output["status"] if local_output else "unknown",
            "ready": bool(local_output["ready"]) if local_output else False,
            "action": local_output["action"] if local_output else "Run auralis doctor before audible output.",
        },
        "operator_actions": [
            "Run the dry-run command before any audible output.",
            "Review output-operator-checklist.md and system-output-next-step.md.",
            "Replace <public-spoken-text> only with public, non-sensitive text.",
            "Use --speak only when an operator is present and ready to hear the system voice.",
            "Keep --require-output-backend-ready so the pilot fails before playback if the backend is missing.",
        ],
        "hard_stop_conditions": [
            "Do not run real system output without an operator present.",
            "Do not use --confirm-audible before the operator actually hears the output.",
            "Do not use --confirm-text-reviewed before the spoken text privacy scan and local review pass.",
            "Do not use --confirm-voice-reviewed before voice, volume and pronunciation are reviewed.",
            "Do not publish spoken text, local paths, voice names tied to a private machine or operator identity.",
        ],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_decision_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe go/no-go summary for the next operator."""

    privacy_audit = report["beta_readiness"].get(
        "privacy_audit",
        {"status": "unknown", "finding_count": 0, "findings": [], "blocking": False},
    )
    privacy_blocked = bool(privacy_audit.get("blocking"))
    pilot_go = bool(
        report["safe_automated_pilot"]["passed"]
        and report["gate"]["ready_for_real_world_pilots"]
        and not report["gate"]["pilot_blockers"]
    )
    beta_go = bool(report["beta_readiness"]["ready_for_beta"] and not privacy_blocked)
    stable_go = bool(report["gate"]["ready_for_stable_release"])
    recommended = report["recommended_pilot_sequence"][0] if report["recommended_pilot_sequence"] else None
    local_warnings = [
        row["name"]
        for row in report["environment_checklist"]
        if row["target_system"] is None and not row["ready"]
    ]
    target_system_checks = [
        row["name"]
        for row in report["environment_checklist"]
        if row["status"] == "target-system-required"
    ]

    return {
        "real_world_pilot": {
            "decision": "go" if pilot_go else "blocked",
            "reason": (
                "Safe automated pilot passed and stability gate allows real-world pilots."
                if pilot_go
                else "Safe automated pilot or stability gate is not ready for real-world pilots."
            ),
            "allowed_scope": [
                "Run only the recommended real-pilot sequence with reviewed hardware/audio/text.",
                "Use public or non-sensitive audio/text only.",
                "Keep artifacts generated by the tools; do not paste private content into public docs.",
            ],
        },
        "beta": {
            "decision": "go" if beta_go else "blocked",
            "blockers": report["beta_readiness"]["blockers"],
            "reason": (
                "All beta blockers are closed."
                if beta_go
                else "Evidence privacy audit found suspicious raw fields; beta remains blocked."
                if privacy_blocked
                else "Beta remains blocked until real evidence closes the pending blockers."
            ),
        },
        "stable": {
            "decision": "go" if stable_go else "blocked",
            "blockers": report["gate"]["stable_blockers"],
            "reason": (
                "Stable release gate is clear."
                if stable_go
                else "Stable release remains blocked until the gate reports ready_for_stable_release=true."
            ),
        },
        "next_recommended_step": {
            "name": recommended["name"] if recommended else None,
            "title": recommended["title"] if recommended else None,
            "command": recommended["command"] if recommended else None,
            "artifact": recommended["artifact"] if recommended else None,
            "requires_hardware": recommended["requires_hardware"] if recommended else False,
            "requires_operator": recommended["requires_operator"] if recommended else False,
            "requires_non_sensitive_audio": recommended["requires_non_sensitive_audio"] if recommended else False,
            "strict_backend_guard_required": recommended["strict_backend_guard_required"] if recommended else False,
            "strict_backend_guard_flag": recommended["strict_backend_guard_flag"] if recommended else None,
            "strict_backend_guard_field": recommended["strict_backend_guard_field"] if recommended else None,
        },
        "next_evidence_focus": report["beta_readiness"].get("next_evidence_focus", {}),
        "privacy_audit": privacy_audit,
        "privacy_remediation_plan": report["beta_readiness"].get("privacy_remediation_plan", {}),
        "release_batch": report.get("release_batch", {}),
        "local_environment_warnings": local_warnings,
        "target_system_checks": target_system_checks,
        "operator_actions": [
            "Review real-pilot-environment-checklist.md before touching hardware or real audio.",
            "Review real-pilot-fixture-preflight.md before replacing the synthetic fixture with your own MP3.",
            "Review real-pilot-transcription-readiness.md before running a real transcription backend.",
            "Review real-pilot-system-output-readiness.md before audible system output.",
            "Review real-pilot-evidence-manifest.md to know which JSON artifact closes each blocker.",
            "Review privacy_audit before treating any JSON artifact as beta-ready.",
            "Run the strict audit after collecting real artifacts.",
            "Refresh BETA_CHECKLIST.md only after the audit is reviewed.",
            "Check release_batch before tagging; do not create a tag until the configured batch is ready.",
        ],
        "hard_stop_conditions": [
            "Do not run real audio if the room, input, reference text or spoken text contains private content.",
            "Do not use --confirm-* flags before local human review is complete.",
            "Do not declare beta while privacy_audit.blocking=true.",
            "Do not declare beta while beta.decision is blocked.",
            "Do not declare stable while stable.decision is blocked.",
            "Do not create a Git tag or GitHub Release while release_batch.ready_for_tag is false.",
        ],
        "content_policy": {
            "usable_as_beta_evidence": False,
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_execution_operator_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Build a structured, public-safe operator gate for the next real pilot."""

    gate = report["pilot_decision_gate"]
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    focus_name = focus.get("name") or ""
    focus_status = focus.get("status") or "unknown"
    focus_command = focus.get("command") or ""
    focus_artifact = focus.get("artifact") or "ninguno"
    sequence = report.get("next_evidence_focus_preparation_sequence", [])
    strict_guard_required = any(bool(step.get("strict_backend_guard_required")) for step in sequence)
    requires_local_review = any(
        bool(step.get("review_required") or step.get("requires_hardware") or step.get("requires_operator"))
        for step in sequence
    )
    human_confirmations = _operator_gate_human_confirmations(focus_command, focus, sequence)
    command_audit = _operator_gate_command_audit(focus_command, human_confirmations, sequence)
    evidence_contract = _operator_gate_evidence_contract(focus, report)
    blocking_reasons: list[str] = []
    if gate["real_world_pilot"]["decision"] != "go":
        blocking_reasons.append("real_world_pilot_gate_blocked")
    if gate.get("privacy_audit", {}).get("blocking"):
        blocking_reasons.append("privacy_audit_blocking")
    if not focus_name:
        blocking_reasons.append("no_next_evidence_focus")
    if focus_status == "complete":
        blocking_reasons.append("next_evidence_focus_complete")
    if not sequence:
        blocking_reasons.append("no_preparation_sequence")
    if command_audit["status"] != "passed":
        blocking_reasons.append("operator_command_audit_failed")
    allowed_to_run = not blocking_reasons

    return {
        "decision": "ready_for_local_operator" if allowed_to_run else "blocked",
        "allowed_to_run": allowed_to_run,
        "blocking_reasons": blocking_reasons,
        "requires_local_operator_review": requires_local_review,
        "focus": focus_name or "ninguno",
        "focus_status": focus_status,
        "focus_artifact": focus_artifact,
        "pre_run_reviews": [
            "real-pilot-decision-gate.md",
            "real-pilot-hard-stop-card.md",
            "real-pilot-evidence-intake-card.md",
            "real-pilot-command-pack.md",
            "real-pilot-environment-checklist.md",
            "real-pilot-next-evidence-focus.md",
            "real-pilot-consent-card.md",
        ],
        "human_confirmations": human_confirmations,
        "strict_backend_guard_required": strict_guard_required,
        "command_audit": command_audit,
        "evidence_contract": evidence_contract,
        "audit_closure": {
            "required": True,
            "strict_audit_command": report["evidence_manifest"]["strict_audit_command"],
            "refresh_checklist_command": report["evidence_manifest"]["refresh_checklist_command"],
            "expected_json_artifact": focus_artifact,
            "suggested_roots": report["real_pilot_evidence_intake_card"]["suggested_roots"],
            "findings_template": "real-pilot-findings-template.md",
        },
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
    }


def _real_pilot_consent_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe consent template for the local operator."""

    gate = report["real_pilot_execution_card"]["operator_gate"]
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    sequence = report.get("next_evidence_focus_preparation_sequence", [])
    consent_items = [
        {
            "id": "hard_stop_reviewed",
            "required": True,
            "confirmed": False,
            "source": "real-pilot-hard-stop-card.md",
            "instruction": "Review hard-stop conditions before touching hardware, real audio or confirm flags.",
        },
        {
            "id": "execution_card_reviewed",
            "required": True,
            "confirmed": False,
            "source": "real-pilot-execution-card.md",
            "instruction": "Review the ordered command, required fields and audit closure.",
        },
        {
            "id": "evidence_intake_reviewed",
            "required": True,
            "confirmed": False,
            "source": "real-pilot-evidence-intake-card.md",
            "instruction": "Review where sanitized JSON evidence will be stored and audited.",
        },
        {
            "id": "public_non_sensitive_scope",
            "required": True,
            "confirmed": False,
            "source": "local operator review",
            "instruction": "Confirm the room, input device, audio, reference and spoken text are public or non-sensitive.",
        },
        {
            "id": "placeholders_replaced_locally",
            "required": True,
            "confirmed": False,
            "source": "local operator shell",
            "instruction": "Replace placeholders only on the local machine and keep private values out of shared artifacts.",
        },
        {
            "id": "confirm_flags_after_review",
            "required": True,
            "confirmed": False,
            "source": "local operator review",
            "instruction": "Use --confirm-* flags only after the matching human review actually happened.",
        },
        {
            "id": "strict_backend_guard_kept",
            "required": gate["strict_backend_guard_required"],
            "confirmed": False,
            "source": gate["command_audit"].get("present_required_flags", []),
            "instruction": "Keep the strict backend guard so missing real backends fail before model, audio or capture work.",
        },
        {
            "id": "audit_closure_accepted",
            "required": True,
            "confirmed": False,
            "source": gate["audit_closure"]["strict_audit_command"],
            "instruction": "Run strict evidence audit before refreshing beta status or publishing findings.",
        },
    ]
    required_items = [item for item in consent_items if item["required"]]
    missing_consent_ids = [item["id"] for item in required_items if item["confirmed"] is not True]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_execution_card.operator_gate + hard_stop + evidence_intake",
        "usable_as_beta_evidence": False,
        "focus": gate["focus"],
        "focus_artifact": gate["focus_artifact"],
        "focus_command": focus.get("command") or "ninguno",
        "decision": "requires_local_operator_consent" if gate["allowed_to_run"] else "blocked",
        "allowed_to_run_after_consent": gate["allowed_to_run"],
        "requires_local_operator": True,
        "requires_operator_consent": True,
        "requires_pre_run_reviews": True,
        "can_execute_without_operator": False,
        "records_consent_identity": False,
        "records_signature": False,
        "records_timestamped_identity": False,
        "missing_consent_count": len(missing_consent_ids),
        "missing_consent_ids": missing_consent_ids,
        "consent_items": consent_items,
        "pre_run_reviews": list(gate["pre_run_reviews"]),
        "human_confirmations": list(gate["human_confirmations"]),
        "sequence_names": [step["name"] for step in sequence],
        "strict_audit_command": gate["audit_closure"]["strict_audit_command"],
        "refresh_checklist_command": gate["audit_closure"]["refresh_checklist_command"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_audit_closure_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe checklist for closing a real pilot with audit evidence."""

    gate = report["real_pilot_execution_card"]["operator_gate"]
    closure = gate["audit_closure"]
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    closure_items = [
        {
            "id": "real_pilot_completed_locally",
            "required": True,
            "status": "pending_real_pilot",
            "source": "local operator",
        },
        {
            "id": "sanitized_json_saved",
            "required": True,
            "status": "pending_real_pilot",
            "source": closure["expected_json_artifact"],
        },
        {
            "id": "strict_audit_passed",
            "required": True,
            "status": "pending_audit",
            "source": closure["strict_audit_command"],
        },
        {
            "id": "beta_checklist_refreshed",
            "required": True,
            "status": "pending_audit",
            "source": closure["refresh_checklist_command"],
        },
        {
            "id": "findings_sanitized",
            "required": True,
            "status": "pending_local_operator",
            "source": "real-pilot-findings-template.md",
        },
    ]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "operator_gate.audit_closure + evidence_manifest + findings_template",
        "usable_as_beta_evidence": False,
        "focus": gate["focus"],
        "focus_status": focus.get("status") or "unknown",
        "expected_json_artifact": closure["expected_json_artifact"],
        "suggested_roots": list(closure["suggested_roots"]),
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "finding_template": "real-pilot-findings-template.md",
        "evidence_intake_card": "real-pilot-evidence-intake-card.md",
        "execution_card": "real-pilot-execution-card.md",
        "consent_card": "real-pilot-consent-card.md",
        "closure_status": "waiting_for_real_evidence" if gate["allowed_to_run"] else "blocked",
        "audit_required": True,
        "can_close_without_audit": False,
        "can_refresh_beta_without_audit": False,
        "requires_sanitized_json": True,
        "requires_privacy_audit": True,
        "requires_findings_update": True,
        "closure_items": closure_items,
        "closure_item_count": len(closure_items),
        "pending_closure_ids": [item["id"] for item in closure_items],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_rehearsal_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe rehearsal card before a local operator touches hardware."""

    gate = report["real_pilot_execution_card"]["operator_gate"]
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    sequence = report.get("next_evidence_focus_preparation_sequence", [])
    rehearsal_items = [
        {
            "id": "safe_pilot_refreshed",
            "required": True,
            "status": "pending_local_rehearsal",
            "source": "python tools/pilot_run.py --output-dir pilot_runs/safe --json",
            "requires_hardware": False,
            "requires_operator": False,
        },
        {
            "id": "beta_requirements_reviewed",
            "required": True,
            "status": "pending_local_rehearsal",
            "source": "python tools/beta_readiness.py --requirements",
            "requires_hardware": False,
            "requires_operator": False,
        },
        {
            "id": "support_cards_reviewed",
            "required": True,
            "status": "pending_local_rehearsal",
            "source": "real-pilot-hard-stop-card.md + real-pilot-execution-card.md",
            "requires_hardware": False,
            "requires_operator": True,
        },
        {
            "id": "command_placeholders_reviewed",
            "required": True,
            "status": "pending_local_rehearsal",
            "source": gate["command_audit"]["command"],
            "requires_hardware": False,
            "requires_operator": True,
        },
        {
            "id": "strict_backend_guard_preserved",
            "required": gate["strict_backend_guard_required"],
            "status": "pending_local_rehearsal",
            "source": gate["command_audit"].get("present_required_flags", []),
            "requires_hardware": False,
            "requires_operator": True,
        },
        {
            "id": "no_real_command_executed_during_rehearsal",
            "required": True,
            "status": "pending_local_rehearsal",
            "source": "local operator",
            "requires_hardware": False,
            "requires_operator": True,
        },
    ]
    support_artifacts = [
        "real-pilot-command-pack.md",
        "real-pilot-hard-stop-card.md",
        "real-pilot-evidence-intake-card.md",
        "real-pilot-execution-card.md",
        "real-pilot-consent-card.md",
        "real-pilot-audit-closure.md",
        "real-pilot-evidence-package.md",
        "real-pilot-operator-brief.md",
        "real-pilot-run-sheet.md",
    ]
    pending_rehearsal_ids = [item["id"] for item in rehearsal_items if item["required"]]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_execution_card.operator_gate + beta_readiness.next_evidence_focus",
        "usable_as_beta_evidence": False,
        "focus": gate["focus"],
        "focus_status": focus.get("status") or "unknown",
        "focus_artifact": gate["focus_artifact"],
        "focus_command": focus.get("command") or "ninguno",
        "rehearsal_status": "ready_for_local_rehearsal" if gate["allowed_to_run"] else "blocked",
        "tracks_rehearsal_before_real_run": True,
        "requires_local_operator": True,
        "requires_real_hardware": any(step.get("requires_hardware") for step in sequence),
        "requires_non_sensitive_audio": any(step.get("requires_non_sensitive_audio") for step in sequence),
        "requires_audible_output": any(step.get("name") == "system_output_audible" for step in sequence),
        "can_execute_real_command_from_card": False,
        "real_command_copy_allowed_after_rehearsal": False,
        "copy_requires_consent_card": True,
        "copy_requires_audit_closure": True,
        "safe_rehearsal_commands": [
            "python tools/pilot_run.py --output-dir pilot_runs/safe --json",
            "python tools/beta_readiness.py --requirements",
        ],
        "support_artifacts": support_artifacts,
        "rehearsal_items": rehearsal_items,
        "rehearsal_item_count": len(rehearsal_items),
        "pending_rehearsal_ids": pending_rehearsal_ids,
        "pending_rehearsal_count": len(pending_rehearsal_ids),
        "strict_audit_command": gate["audit_closure"]["strict_audit_command"],
        "refresh_checklist_command": gate["audit_closure"]["refresh_checklist_command"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_evidence_package_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe evidence package checklist after a real pilot run."""

    gate = report["real_pilot_execution_card"]["operator_gate"]
    evidence_contract = gate["evidence_contract"]
    closure = report["real_pilot_audit_closure_card"]
    expected_artifacts = [
        evidence_contract["expected_artifact"],
        closure["finding_template"],
        "BETA_CHECKLIST.md",
    ]
    support_artifacts = [
        "real-pilot-run-sheet.md",
        "real-pilot-final-go-no-go.md",
        "real-pilot-operator-brief.md",
        "real-pilot-rehearsal-card.md",
        "real-pilot-execution-card.md",
        "real-pilot-consent-card.md",
        "real-pilot-evidence-intake-card.md",
        "real-pilot-local-receipt.md",
        "real-pilot-audit-closure.md",
    ]
    package_items = [
        {
            "id": "sanitized_json_present",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": evidence_contract["expected_artifact"],
        },
        {
            "id": "json_project_matches",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": "project: AuralisVoiceKit",
        },
        {
            "id": "required_fields_reviewed",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": "evidence_contract.required_fields",
        },
        {
            "id": "strict_audit_saved",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": closure["strict_audit_command"],
        },
        {
            "id": "beta_checklist_refreshed",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": closure["refresh_checklist_command"],
        },
        {
            "id": "sanitized_findings_prepared",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": closure["finding_template"],
        },
        {
            "id": "no_private_values_copied",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": "content_policy",
        },
    ]
    pending_package_ids = [item["id"] for item in package_items if item["required"]]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "operator_gate.evidence_contract + real_pilot_audit_closure_card",
        "usable_as_beta_evidence": False,
        "focus": evidence_contract["blocker"],
        "focus_artifact": evidence_contract["expected_artifact"],
        "package_status": "waiting_for_real_evidence",
        "tracks_sanitized_evidence_package": True,
        "package_requires_strict_audit": True,
        "package_requires_beta_refresh": True,
        "can_close_beta_from_package_card": False,
        "expected_artifacts": expected_artifacts,
        "support_artifacts": support_artifacts,
        "suggested_roots": closure["suggested_roots"],
        "required_json_fields": evidence_contract["required_fields"],
        "missing_json_fields": evidence_contract["missing_fields"],
        "required_field_count": evidence_contract["required_field_count"],
        "missing_field_count": evidence_contract["missing_field_count"],
        "conditional_required_fields": evidence_contract["conditional_required_fields"],
        "package_items": package_items,
        "package_item_count": len(package_items),
        "pending_package_ids": pending_package_ids,
        "pending_package_count": len(pending_package_ids),
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_operator_brief_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe one-page brief for the local real-pilot operator."""

    focus = report["beta_readiness"].get("next_evidence_focus", {})
    execution = report["real_pilot_execution_card"]
    gate = execution["operator_gate"]
    consent = report["real_pilot_consent_card"]
    rehearsal = report["real_pilot_rehearsal_card"]
    package = report["real_pilot_evidence_package_card"]
    closure = report["real_pilot_audit_closure_card"]
    before_run_artifacts = [
        "real-pilot-decision-gate.md",
        "real-pilot-hard-stop-card.md",
        "real-pilot-command-pack.md",
        "real-pilot-environment-checklist.md",
        "real-pilot-rehearsal-card.md",
        "real-pilot-consent-card.md",
        "real-pilot-execution-card.md",
        "real-pilot-run-sheet.md",
        "real-pilot-final-go-no-go.md",
    ]
    after_run_artifacts = [
        package["artifact"],
        "real-pilot-local-receipt.md",
        closure["artifact"],
        closure["finding_template"],
        "BETA_CHECKLIST.md",
    ]
    brief_items = [
        {
            "id": "hard_stop_reviewed",
            "required": True,
            "status": "pending_local_operator_review",
            "source": "real-pilot-hard-stop-card.md",
        },
        {
            "id": "rehearsal_completed",
            "required": True,
            "status": rehearsal["rehearsal_status"],
            "source": rehearsal["artifact"],
        },
        {
            "id": "consent_scope_confirmed",
            "required": True,
            "status": consent["decision"],
            "source": consent["artifact"],
        },
        {
            "id": "command_placeholders_replaced_locally",
            "required": True,
            "status": "pending_local_operator_review",
            "source": gate["command_audit"]["command"],
        },
        {
            "id": "human_confirmations_completed",
            "required": True,
            "status": "pending_local_operator_review",
            "source": gate["human_confirmations"] or ["ninguno"],
        },
        {
            "id": "sanitized_json_target_chosen",
            "required": True,
            "status": "pending_real_pilot",
            "source": gate["focus_artifact"],
        },
        {
            "id": "post_run_audit_planned",
            "required": True,
            "status": "pending_real_pilot",
            "source": closure["strict_audit_command"],
        },
        {
            "id": "evidence_package_prepared",
            "required": True,
            "status": package["package_status"],
            "source": package["artifact"],
        },
    ]
    pending_brief_ids = [item["id"] for item in brief_items if item["required"]]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_execution_card + real_pilot_consent_card + real_pilot_evidence_package_card",
        "usable_as_beta_evidence": False,
        "brief_status": "ready_for_local_operator_review" if gate["allowed_to_run"] else "blocked",
        "focus": gate["focus"],
        "focus_title": focus.get("title") or "ninguno",
        "focus_artifact": gate["focus_artifact"],
        "local_run_allowed": gate["allowed_to_run"],
        "command_safe_to_copy_for_local_operator": gate["command_audit"]["safe_to_copy_for_local_operator"],
        "copy_safety_status": gate["command_audit"]["copy_safety"]["status"],
        "requires_local_operator_review": gate["requires_local_operator_review"],
        "requires_consent_card": True,
        "requires_rehearsal_card": True,
        "requires_evidence_package": True,
        "local_command_template": focus.get("command") or "ninguno",
        "pre_run_reviews": gate["pre_run_reviews"],
        "human_confirmations": gate["human_confirmations"],
        "copy_pending_ids": gate["command_audit"]["copy_safety"]["pending_local_review_ids"],
        "before_run_artifacts": before_run_artifacts,
        "after_run_artifacts": after_run_artifacts,
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "brief_items": brief_items,
        "brief_item_count": len(brief_items),
        "pending_brief_ids": pending_brief_ids,
        "pending_brief_count": len(pending_brief_ids),
        "hard_stop_conditions": report["pilot_decision_gate"]["hard_stop_conditions"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_run_sheet_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a phase-by-phase local run sheet for the next real pilot."""

    focus = report["beta_readiness"].get("next_evidence_focus", {})
    execution = report["real_pilot_execution_card"]
    gate = execution["operator_gate"]
    consent = report["real_pilot_consent_card"]
    rehearsal = report["real_pilot_rehearsal_card"]
    package = report["real_pilot_evidence_package_card"]
    brief = report["real_pilot_operator_brief_card"]
    closure = report["real_pilot_audit_closure_card"]
    phases = [
        {
            "id": "pre_run_review",
            "required": True,
            "status": "pending_local_operator_review",
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": brief["artifact"],
            "artifacts": brief["before_run_artifacts"],
        },
        {
            "id": "local_rehearsal",
            "required": True,
            "status": rehearsal["rehearsal_status"],
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": rehearsal["artifact"],
            "commands": rehearsal["safe_rehearsal_commands"],
        },
        {
            "id": "consent_and_copy_review",
            "required": True,
            "status": consent["decision"],
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": consent["artifact"],
            "copy_pending_ids": brief["copy_pending_ids"],
        },
        {
            "id": "final_go_no_go_review",
            "required": True,
            "status": "pending_local_operator_review",
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": "real-pilot-final-go-no-go.md",
            "go_no_go_required": True,
        },
        {
            "id": "real_execution",
            "required": True,
            "status": "pending_real_pilot",
            "requires_hardware": True,
            "requires_local_operator": True,
            "source": "real-pilot-execution-card.md",
            "command": focus.get("command") or "ninguno",
            "human_confirmations": gate["human_confirmations"],
        },
        {
            "id": "local_receipt",
            "required": True,
            "status": "waiting_for_local_receipt",
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": "real-pilot-local-receipt.md",
            "expected_receipt_items": [
                "final_decision_recorded",
                "real_run_outcome_recorded",
                "sanitized_json_saved",
                "strict_audit_result_recorded",
            ],
        },
        {
            "id": "sanitized_evidence_package",
            "required": True,
            "status": package["package_status"],
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": package["artifact"],
            "expected_artifacts": package["expected_artifacts"],
            "required_json_fields": package["required_json_fields"],
            "missing_json_fields": package["missing_json_fields"],
        },
        {
            "id": "strict_audit_and_refresh",
            "required": True,
            "status": closure["closure_status"],
            "requires_hardware": False,
            "requires_local_operator": True,
            "source": closure["artifact"],
            "strict_audit_command": closure["strict_audit_command"],
            "refresh_checklist_command": closure["refresh_checklist_command"],
        },
    ]
    pending_phase_ids = [phase["id"] for phase in phases if phase["required"]]
    prerequisite_artifacts = [
        brief["artifact"],
        "real-pilot-decision-gate.md",
        "real-pilot-hard-stop-card.md",
        "real-pilot-rehearsal-card.md",
        "real-pilot-consent-card.md",
        "real-pilot-execution-card.md",
        "real-pilot-final-go-no-go.md",
    ]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_operator_brief_card + real_pilot_execution_card + real_pilot_audit_closure_card",
        "usable_as_beta_evidence": False,
        "sheet_status": "ready_for_local_operator_review" if gate["allowed_to_run"] else "blocked",
        "focus": gate["focus"],
        "focus_title": focus.get("title") or "ninguno",
        "focus_artifact": gate["focus_artifact"],
        "local_run_allowed": gate["allowed_to_run"],
        "command_safe_to_copy_for_local_operator": gate["command_audit"]["safe_to_copy_for_local_operator"],
        "requires_local_operator_review": gate["requires_local_operator_review"],
        "local_command_template": focus.get("command") or "ninguno",
        "prerequisite_artifacts": prerequisite_artifacts,
        "human_confirmations": gate["human_confirmations"],
        "copy_pending_ids": brief["copy_pending_ids"],
        "suggested_roots": package["suggested_roots"],
        "required_json_fields": package["required_json_fields"],
        "missing_json_fields": package["missing_json_fields"],
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "phases": phases,
        "phase_count": len(phases),
        "required_phase_count": len(pending_phase_ids),
        "pending_phase_ids": pending_phase_ids,
        "requires_final_go_no_go": True,
        "final_go_no_go_artifact": "real-pilot-final-go-no-go.md",
        "hard_stop_conditions": report["pilot_decision_gate"]["hard_stop_conditions"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_final_go_no_go_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build the final public-safe local go/no-go review before real hardware use."""

    focus = report["beta_readiness"].get("next_evidence_focus", {})
    execution = report["real_pilot_execution_card"]
    gate = execution["operator_gate"]
    sheet = report["real_pilot_run_sheet_card"]
    brief = report["real_pilot_operator_brief_card"]
    consent = report["real_pilot_consent_card"]
    rehearsal = report["real_pilot_rehearsal_card"]
    package = report["real_pilot_evidence_package_card"]
    closure = report["real_pilot_audit_closure_card"]
    command_audit = gate["command_audit"]
    copy_safety = command_audit["copy_safety"]
    review_items = [
        {
            "id": "hard_stop_conditions_checked",
            "required": True,
            "status": "pending_local_operator_review",
            "source": "real-pilot-hard-stop-card.md",
        },
        {
            "id": "run_sheet_phases_reviewed",
            "required": True,
            "status": "pending_local_operator_review",
            "source": sheet["artifact"],
        },
        {
            "id": "rehearsal_completed",
            "required": True,
            "status": rehearsal["rehearsal_status"],
            "source": rehearsal["artifact"],
        },
        {
            "id": "consent_scope_confirmed",
            "required": True,
            "status": consent["decision"],
            "source": consent["artifact"],
        },
        {
            "id": "command_template_safe",
            "required": True,
            "status": command_audit["status"],
            "source": "operator_gate.command_audit",
        },
        {
            "id": "copy_pending_items_reviewed_locally",
            "required": True,
            "status": copy_safety["status"],
            "source": "operator_gate.command_audit.copy_safety",
        },
        {
            "id": "human_confirmations_ready",
            "required": True,
            "status": "pending_local_operator_review",
            "source": gate["human_confirmations"] or ["ninguno"],
        },
        {
            "id": "sanitized_evidence_destination_ready",
            "required": True,
            "status": package["package_status"],
            "source": package["artifact"],
        },
        {
            "id": "strict_audit_planned",
            "required": True,
            "status": closure["closure_status"],
            "source": closure["artifact"],
        },
    ]
    pending_review_ids = [item["id"] for item in review_items if item["required"]]
    go_conditions = [
        "all_run_sheet_phases_reviewed_locally",
        "no_hard_stop_condition_applies",
        "local_placeholders_replaced_without_committing_private_values",
        "required_human_confirmations_completed_before_confirm_flags",
        "sanitized_json_destination_selected",
        "strict_audit_and_beta_refresh_planned",
    ]
    no_go_conditions = [
        "any_hard_stop_condition_applies",
        "command_template_not_safe_to_copy",
        "missing_required_confirmations",
        "private_audio_transcript_text_path_device_or_identity_would_be_recorded",
        "operator_cannot_run_strict_audit_after_execution",
    ]
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_run_sheet_card + operator_gate.command_audit + real_pilot_consent_card",
        "usable_as_beta_evidence": False,
        "go_no_go_status": "ready_for_local_operator_review" if gate["allowed_to_run"] else "blocked",
        "focus": gate["focus"],
        "focus_title": focus.get("title") or "ninguno",
        "focus_artifact": gate["focus_artifact"],
        "local_run_allowed": gate["allowed_to_run"],
        "command_safe_to_copy_for_local_operator": command_audit["safe_to_copy_for_local_operator"],
        "copy_safety_status": copy_safety["status"],
        "requires_local_operator_review": True,
        "requires_final_operator_decision": True,
        "can_execute_without_final_decision": False,
        "decision_options": ["go_after_local_checks", "no_go_stop_and_fix"],
        "local_command_template": focus.get("command") or "ninguno",
        "support_artifacts": [
            brief["artifact"],
            sheet["artifact"],
            "real-pilot-hard-stop-card.md",
            rehearsal["artifact"],
            consent["artifact"],
            "real-pilot-execution-card.md",
            package["artifact"],
            closure["artifact"],
            "real-pilot-local-receipt.md",
        ],
        "local_receipt_artifact": "real-pilot-local-receipt.md",
        "human_confirmations": gate["human_confirmations"],
        "copy_pending_ids": brief["copy_pending_ids"],
        "missing_required_flags": command_audit["missing_required_flags"],
        "required_flags": command_audit["required_flags"],
        "go_conditions": go_conditions,
        "no_go_conditions": no_go_conditions,
        "review_items": review_items,
        "review_item_count": len(review_items),
        "pending_review_ids": pending_review_ids,
        "pending_review_count": len(pending_review_ids),
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "hard_stop_conditions": report["pilot_decision_gate"]["hard_stop_conditions"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _real_pilot_local_receipt_card(report: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    """Build a public-safe local receipt template after the real pilot attempt."""

    final_gate = report["real_pilot_final_go_no_go_card"]
    sheet = report["real_pilot_run_sheet_card"]
    package = report["real_pilot_evidence_package_card"]
    closure = report["real_pilot_audit_closure_card"]
    receipt_items = [
        {
            "id": "final_decision_recorded",
            "required": True,
            "status": "waiting_for_local_receipt",
            "source": final_gate["artifact"],
        },
        {
            "id": "real_run_outcome_recorded",
            "required": True,
            "status": "waiting_for_local_receipt",
            "source": "real_execution",
        },
        {
            "id": "sanitized_json_saved",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": package["focus_artifact"],
        },
        {
            "id": "strict_audit_result_recorded",
            "required": True,
            "status": closure["closure_status"],
            "source": closure["strict_audit_command"],
        },
        {
            "id": "beta_refresh_result_recorded",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": closure["refresh_checklist_command"],
        },
        {
            "id": "sanitized_findings_ready",
            "required": True,
            "status": "waiting_for_real_evidence",
            "source": closure["finding_template"],
        },
        {
            "id": "no_private_values_written",
            "required": True,
            "status": "waiting_for_local_receipt",
            "source": "content_policy",
        },
    ]
    pending_receipt_ids = [item["id"] for item in receipt_items if item["required"]]
    receipt_placeholders = {
        "final_decision": "<go_after_local_checks|no_go_stop_and_fix>",
        "run_outcome": "<completed|stopped|blocked>",
        "sanitized_json_artifact": package["focus_artifact"],
        "strict_audit_result": "<passed|failed|not-run>",
        "beta_refresh_result": "<refreshed|not-refreshed>",
        "findings_status": "<prepared|not-prepared>",
    }
    return {
        "artifact": artifact_path.name,
        "safe_to_share": True,
        "source": "real_pilot_final_go_no_go_card + real_pilot_evidence_package_card + real_pilot_audit_closure_card",
        "usable_as_beta_evidence": False,
        "receipt_status": "waiting_for_local_receipt",
        "focus": final_gate["focus"],
        "focus_artifact": final_gate["focus_artifact"],
        "local_run_allowed": final_gate["local_run_allowed"],
        "requires_local_operator_review": True,
        "requires_final_go_no_go": True,
        "final_go_no_go_artifact": final_gate["artifact"],
        "run_sheet_artifact": sheet["artifact"],
        "evidence_package_artifact": package["artifact"],
        "audit_closure_artifact": closure["artifact"],
        "finding_template": closure["finding_template"],
        "decision_options": final_gate["decision_options"],
        "receipt_placeholders": receipt_placeholders,
        "support_artifacts": [
            final_gate["artifact"],
            sheet["artifact"],
            package["artifact"],
            closure["artifact"],
            closure["finding_template"],
            "BETA_CHECKLIST.md",
        ],
        "receipt_items": receipt_items,
        "receipt_item_count": len(receipt_items),
        "pending_receipt_ids": pending_receipt_ids,
        "pending_receipt_count": len(pending_receipt_ids),
        "strict_audit_command": closure["strict_audit_command"],
        "refresh_checklist_command": closure["refresh_checklist_command"],
        "hard_stop_conditions": report["pilot_decision_gate"]["hard_stop_conditions"],
        "content_policy": {
            "records_audio": False,
            "records_transcripts": False,
            "records_spoken_text": False,
            "records_expected_text": False,
            "records_local_paths": False,
            "records_device_names": False,
            "records_operator_identity": False,
            "records_signature": False,
        },
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
        "records_signature": False,
    }


def _operator_gate_evidence_contract(focus: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    required_fields = list(focus.get("required_fields", []))
    missing_fields = list(focus.get("missing_fields", []))
    conditional_required_fields = list(focus.get("conditional_required_fields", []))
    policy_required_fields = _policy_required_fields(required_fields, conditional_required_fields)
    return {
        "safe_to_share": True,
        "blocker": focus.get("name") or "ninguno",
        "title": focus.get("title") or "ninguno",
        "expected_artifact": focus.get("artifact") or "ninguno",
        "required_fields": required_fields,
        "required_field_count": len(required_fields),
        "missing_fields": missing_fields,
        "missing_field_count": len(missing_fields),
        "conditional_required_fields": conditional_required_fields,
        "conditional_required_field_count": len(conditional_required_fields),
        "policy_required_fields": policy_required_fields,
        "policy_required_field_count": len(policy_required_fields),
        "suggested_roots": report["real_pilot_evidence_intake_card"]["suggested_roots"],
        "strict_audit_command": report["evidence_manifest"]["strict_audit_command"],
        "refresh_checklist_command": report["evidence_manifest"]["refresh_checklist_command"],
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _operator_gate_human_confirmations(
    command: str,
    focus: dict[str, Any],
    sequence: list[dict[str, Any]],
) -> list[str]:
    confirmations: list[str] = []
    required_fields = set(focus.get("required_fields", []))
    if "--expected-system" in command or "system_guard.expected_system_matched" in required_fields:
        confirmations.append("expected_system_review")
    if "--confirm-input-reviewed" in command or "input_review_confirmed" in required_fields:
        confirmations.append("input_review_confirmed")
    if "--operator-present" in command or any(step.get("requires_operator") for step in sequence):
        confirmations.append("operator_present")
    if "--confirm-audible" in command:
        confirmations.append("audible_output_confirmed")
    if "--confirm-text-reviewed" in command or "text_review_confirmed" in required_fields:
        confirmations.append("spoken_text_reviewed")
    if "--confirm-voice-reviewed" in command or "voice_review_confirmed" in required_fields:
        confirmations.append("voice_reviewed")
    if "--confirm-audio-reviewed" in command or "audio_review_confirmed" in required_fields:
        confirmations.append("audio_privacy_reviewed")
    if "--confirm-reference-reviewed" in command or "reference_review_confirmed" in required_fields:
        confirmations.append("reference_reviewed")
    if "--confirm-quality-reviewed" in command or "quality_review_confirmed" in required_fields:
        confirmations.append("quality_reviewed")
    if any(step.get("requires_non_sensitive_audio") for step in sequence):
        confirmations.append("non_sensitive_audio_confirmed")
    if any(step.get("strict_backend_guard_required") for step in sequence):
        confirmations.append("strict_backend_guard_enabled")
    return confirmations


def _operator_gate_command_audit(
    command: str,
    human_confirmations: list[str],
    sequence: list[dict[str, Any]],
) -> dict[str, Any]:
    required_flags: list[str] = []
    for confirmation, flag in [
        ("expected_system_review", "--expected-system"),
        ("input_review_confirmed", "--confirm-input-reviewed"),
        ("operator_present", "--operator-present"),
        ("audible_output_confirmed", "--confirm-audible"),
        ("spoken_text_reviewed", "--confirm-text-reviewed"),
        ("voice_reviewed", "--confirm-voice-reviewed"),
        ("audio_privacy_reviewed", "--confirm-audio-reviewed"),
        ("reference_reviewed", "--confirm-reference-reviewed"),
        ("quality_reviewed", "--confirm-quality-reviewed"),
        ("non_sensitive_audio_confirmed", "--audio-non-sensitive"),
    ]:
        if confirmation in human_confirmations and flag not in required_flags:
            required_flags.append(flag)
    for step in sequence:
        flag = step.get("strict_backend_guard_flag")
        if step.get("strict_backend_guard_required") and flag and flag not in required_flags:
            required_flags.append(flag)

    present_flags = [flag for flag in required_flags if flag in command]
    missing_flags = [flag for flag in required_flags if flag not in command]
    status = "passed" if command and not missing_flags else "failed"
    records_private_values = False
    return {
        "status": status,
        "safe_to_copy_for_local_operator": status == "passed",
        "command": command,
        "required_flags": required_flags,
        "present_required_flags": present_flags,
        "missing_required_flags": missing_flags,
        "records_private_values": records_private_values,
        "copy_safety": _operator_gate_copy_safety(
            status=status,
            missing_flags=missing_flags,
            records_private_values=records_private_values,
            human_confirmations=human_confirmations,
            sequence=sequence,
        ),
    }


def _operator_gate_copy_safety(
    *,
    status: str,
    missing_flags: list[str],
    records_private_values: bool,
    human_confirmations: list[str],
    sequence: list[dict[str, Any]],
) -> dict[str, Any]:
    strict_guard_required = any(bool(step.get("strict_backend_guard_required")) for step in sequence)
    blocking_reasons: list[str] = []
    if status != "passed":
        blocking_reasons.append("command_audit_failed")
    if missing_flags:
        blocking_reasons.append("missing_required_flags")
    if records_private_values:
        blocking_reasons.append("records_private_values")

    review_items: list[dict[str, Any]] = [
        {
            "id": "command_audit_passed",
            "required": True,
            "status": "passed" if status == "passed" else "blocked",
            "source": "operator_gate.command_audit.status",
        },
        {
            "id": "required_flags_present",
            "required": True,
            "status": "passed" if not missing_flags else "blocked",
            "source": "operator_gate.command_audit.missing_required_flags",
        },
        {
            "id": "no_private_values_recorded",
            "required": True,
            "status": "passed" if not records_private_values else "blocked",
            "source": "operator_gate.command_audit.records_private_values",
        },
        {
            "id": "local_placeholders_reviewed",
            "required": True,
            "status": "pending_local_operator",
            "source": "real-pilot-consent-card.md",
        },
    ]
    if human_confirmations:
        review_items.append(
            {
                "id": "human_confirmations_reviewed",
                "required": True,
                "status": "pending_local_operator",
                "source": "operator_gate.human_confirmations",
            }
        )
    if strict_guard_required:
        review_items.append(
            {
                "id": "strict_backend_guard_reviewed",
                "required": True,
                "status": "pending_local_operator",
                "source": "operator_gate.strict_backend_guard_required",
            }
        )
    pending_local_review_ids = [
        item["id"] for item in review_items if item["status"] == "pending_local_operator"
    ]
    return {
        "status": "blocked" if blocking_reasons else "ready_for_local_review",
        "safe_template": not blocking_reasons,
        "safe_to_copy_for_local_operator": not blocking_reasons,
        "copy_requires_local_operator_review": True,
        "copy_requires_consent_card": True,
        "copy_requires_human_confirmations": bool(human_confirmations),
        "copy_requires_strict_backend_guard_review": strict_guard_required,
        "blocking_reasons": blocking_reasons,
        "review_items": review_items,
        "review_item_count": len(review_items),
        "pending_local_review_ids": pending_local_review_ids,
        "records_private_values": records_private_values,
        "records_audio": False,
        "records_transcripts": False,
        "records_spoken_text": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_device_names": False,
        "records_operator_identity": False,
    }


def _pilot_plan_artifact_summary(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "file": artifact["file"],
            "artifact": artifact["artifact"],
            "satisfied_blockers": artifact["satisfied_blockers"],
            "privacy_finding_count": artifact.get("privacy_finding_count", 0),
        }
        for artifact in artifacts
    ]


def _next_evidence_focus_preparation_sequence(
    recommended_pilot_sequence: list[dict[str, Any]],
    focus: dict[str, Any],
) -> list[dict[str, Any]]:
    focus_name = focus.get("name")
    if not focus_name or focus.get("status") == "complete":
        return []
    focus_names = {focus_name, focus_name.replace("_", "-")}
    steps: list[dict[str, Any]] = []
    for step in recommended_pilot_sequence:
        step_names = {step["name"], step["name"].replace("_", "-")}
        steps.append(
            {
                "order": step["order"],
                "name": step["name"],
                "title": step["title"],
                "command": step["command"],
                "artifact": step["artifact"],
                "required_fields": list(step.get("required_fields", [])),
                "conditional_required_fields": list(step.get("conditional_required_fields", [])),
                "policy_required_fields": list(step.get("policy_required_fields", [])),
                "requires_hardware": bool(step.get("requires_hardware", False)),
                "requires_operator": bool(step.get("requires_operator", False)),
                "requires_non_sensitive_audio": bool(step.get("requires_non_sensitive_audio", False)),
                "review_required": bool(step.get("review_required", False)),
                **_strict_backend_guard_metadata(step["name"]),
            }
        )
        if step_names & focus_names:
            return steps
    return []


def _format_pilot_plan_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    release_batch = report.get("release_batch", {})
    release_batch_threshold = release_batch.get("threshold", release_batch.get("tag_every", 5))
    findings_template_name = Path(
        report["artifacts"].get("real_pilot_findings_template", "real-pilot-findings-template.md")
    ).name
    handoff_name = Path(report["artifacts"].get("real_pilot_handoff", "real-pilot-handoff.md")).name
    command_pack_name = Path(
        report["artifacts"].get("real_pilot_command_pack", "real-pilot-command-pack.md")
    ).name
    environment_checklist_name = Path(
        report["artifacts"].get("real_pilot_environment_checklist", "real-pilot-environment-checklist.md")
    ).name
    fixture_preflight_name = Path(
        report["artifacts"].get("real_pilot_fixture_preflight", "real-pilot-fixture-preflight.md")
    ).name
    transcription_readiness_name = Path(
        report["artifacts"].get("real_pilot_transcription_readiness", "real-pilot-transcription-readiness.md")
    ).name
    system_output_readiness_name = Path(
        report["artifacts"].get("real_pilot_system_output_readiness", "real-pilot-system-output-readiness.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    next_focus_name = Path(
        report["artifacts"].get("real_pilot_next_evidence_focus", "real-pilot-next-evidence-focus.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    evidence_package_name = Path(
        report["artifacts"].get("real_pilot_evidence_package_card", "real-pilot-evidence-package.md")
    ).name
    operator_brief_name = Path(
        report["artifacts"].get("real_pilot_operator_brief_card", "real-pilot-operator-brief.md")
    ).name
    run_sheet_name = Path(
        report["artifacts"].get("real_pilot_run_sheet_card", "real-pilot-run-sheet.md")
    ).name
    final_go_no_go_name = Path(
        report["artifacts"].get("real_pilot_final_go_no_go_card", "real-pilot-final-go-no-go.md")
    ).name
    local_receipt_name = Path(
        report["artifacts"].get("real_pilot_local_receipt_card", "real-pilot-local-receipt.md")
    ).name
    lines = [
        "# Plan de pilotos AuralisVoiceKit",
        "",
        "Este artefacto resume el siguiente piloto real sin incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Ultimo tag: `{release_batch.get('latest_tag') or 'ninguno'}`",
        f"- Mejoras desde ultimo tag: `{release_batch.get('commit_count', 0)}/{release_batch_threshold}`",
        f"- Crear tag ahora: `{_format_bool(release_batch.get('ready_for_tag', False))}`",
        f"- Mejoras restantes antes de tag: `{release_batch.get('remaining', 0)}`",
        f"- Piloto seguro paso: `{str(report['safe_automated_pilot']['passed']).lower()}`",
        f"- Listo para pilotos reales: `{str(report['gate']['ready_for_real_world_pilots']).lower()}`",
        f"- Listo para beta: `{str(beta['ready_for_beta']).lower()}`",
        f"- Evidencias JSON aceptadas: `{beta['evidence_count']}`",
        f"- Evidencias JSON ignoradas: `{beta['ignored_evidence_count']}`",
        f"- Auditoria de privacidad: `{beta['privacy_audit']['status']}`",
        f"- Hallazgos de privacidad: `{beta['privacy_audit']['finding_count']}`",
        f"- Blockers beta: {_format_inline_list(beta['blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(beta['satisfied_json_blockers'])}",
        f"- Blockers JSON pendientes: {_format_inline_list(beta['missing_json_blockers'])}",
        f"- Handoff seguro: `{handoff_name}`",
        f"- Paquete de comandos: `{command_pack_name}`",
        f"- Checklist de entorno: `{environment_checklist_name}`",
        f"- Preflight de fixture: `{fixture_preflight_name}`",
        f"- Readiness de transcripcion real: `{transcription_readiness_name}`",
        f"- Readiness de salida system: `{system_output_readiness_name}`",
        f"- Manifiesto de evidencias: `{evidence_manifest_name}`",
        f"- Compuerta go/no-go: `{decision_gate_name}`",
        f"- Tarjeta de foco: `{next_focus_name}`",
        f"- Tarjeta de alto operativo: `{hard_stop_name}`",
        f"- Ingesta de evidencia: `{evidence_intake_name}`",
        f"- Tarjeta de ejecucion: `{execution_card_name}`",
        f"- Tarjeta de consentimiento: `{consent_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Paquete de evidencia: `{evidence_package_name}`",
        f"- Brief del operador: `{operator_brief_name}`",
        f"- Run sheet: `{run_sheet_name}`",
        f"- Go/no-go final: `{final_go_no_go_name}`",
        f"- Recibo local: `{local_receipt_name}`",
        f"- Plantilla de hallazgos: `{findings_template_name}`",
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
                    f"  - Hallazgos de privacidad: `{artifact['privacy_finding_count']}`",
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
    lines.extend(["## Escaneo de privacidad", ""])
    _append_privacy_audit_lines(lines, beta.get("privacy_audit", {}))
    lines.extend(["## Plan de remediacion de privacidad", ""])
    _append_privacy_remediation_plan_lines(lines, beta.get("privacy_remediation_plan", {}))
    lines.extend(["## Resumen por blocker", ""])
    _append_blocker_summary_lines(lines, beta.get("blocker_summaries", []))
    lines.extend(
        [
            "## Siguiente foco de evidencia",
            "",
        ]
    )
    _append_next_evidence_focus_lines(lines, beta.get("next_evidence_focus", {}))
    lines.extend(
        [
            "## Manifiesto de evidencias",
            "",
            f"- Artifact: `{evidence_manifest_name}`",
            f"- Pendientes: `{report['evidence_manifest']['pending_count']}`",
            f"- Cerradas por JSON: `{report['evidence_manifest']['closed_count']}`",
            f"- Ignoradas: `{report['evidence_manifest']['ignored_count']}`",
            f"- Auditoria: `{report['evidence_manifest']['strict_audit_command']}`",
            "",
            "## Compuerta go/no-go",
            "",
            f"- Artifact: `{decision_gate_name}`",
            f"- Pilotos reales: `{report['pilot_decision_gate']['real_world_pilot']['decision']}`",
            f"- Beta: `{report['pilot_decision_gate']['beta']['decision']}`",
            f"- Estable: `{report['pilot_decision_gate']['stable']['decision']}`",
            f"- Release batch listo para tag: `{_format_bool(report['pilot_decision_gate']['release_batch'].get('ready_for_tag', False))}`",
            f"- Siguiente paso: `{report['pilot_decision_gate']['next_recommended_step']['name'] or 'ninguno'}`",
            "",
            "## Tarjeta de alto operativo",
            "",
            f"- Artifact: `{hard_stop_name}`",
            f"- Condiciones de alto: `{len(report['pilot_decision_gate']['hard_stop_conditions'])}`",
            f"- Acciones del operador: `{len(report['pilot_decision_gate']['operator_actions'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_hard_stop_card']['usable_as_beta_evidence'])}`",
            "",
            "## Ingesta de evidencia real",
            "",
            f"- Artifact: `{evidence_intake_name}`",
            f"- Directorios sugeridos: {_format_inline_list(report['real_pilot_evidence_intake_card']['suggested_roots'])}",
            f"- Auditoria estricta: `{report['evidence_manifest']['strict_audit_command']}`",
            f"- Refrescar checklist: `{report['evidence_manifest']['refresh_checklist_command']}`",
            "",
            "## Ejecucion guiada del piloto real",
            "",
            f"- Artifact: `{execution_card_name}`",
            f"- Foco: `{report['real_pilot_execution_card']['focus']}`",
            f"- Orden de ejecucion: `{_format_bool(report['real_pilot_execution_card']['tracks_execution_order'])}`",
            f"- Confirmaciones humanas: `{_format_bool(report['real_pilot_execution_card']['tracks_human_confirmations'])}`",
            f"- Cierre por auditoria: `{_format_bool(report['real_pilot_execution_card']['tracks_audit_closure'])}`",
            f"- Compuerta operador: `{report['real_pilot_execution_card']['operator_gate']['decision']}`",
            f"- Permitido ejecutar localmente: `{_format_bool(report['real_pilot_execution_card']['operator_gate']['allowed_to_run'])}`",
            "",
            "## Consentimiento local",
            "",
            f"- Artifact: `{consent_card_name}`",
            f"- Decision: `{report['real_pilot_consent_card']['decision']}`",
            f"- Requiere operador local: `{_format_bool(report['real_pilot_consent_card']['requires_local_operator'])}`",
            f"- Faltantes de consentimiento: `{report['real_pilot_consent_card']['missing_consent_count']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_consent_card']['usable_as_beta_evidence'])}`",
            "",
            "## Cierre de auditoria",
            "",
            f"- Artifact: `{audit_closure_name}`",
            f"- Estado de cierre: `{report['real_pilot_audit_closure_card']['closure_status']}`",
            f"- Artifact JSON esperado: `{report['real_pilot_audit_closure_card']['expected_json_artifact']}`",
            f"- Auditoria requerida: `{_format_bool(report['real_pilot_audit_closure_card']['audit_required'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_audit_closure_card']['usable_as_beta_evidence'])}`",
            "",
            "## Ensayo local previo",
            "",
            f"- Artifact: `{rehearsal_card_name}`",
            f"- Estado de ensayo: `{report['real_pilot_rehearsal_card']['rehearsal_status']}`",
            f"- Requiere operador local: `{_format_bool(report['real_pilot_rehearsal_card']['requires_local_operator'])}`",
            f"- Ejecuta comando real: `{_format_bool(report['real_pilot_rehearsal_card']['can_execute_real_command_from_card'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_rehearsal_card']['usable_as_beta_evidence'])}`",
            "",
            "## Paquete de evidencia sanitizada",
            "",
            f"- Artifact: `{evidence_package_name}`",
            f"- Estado del paquete: `{report['real_pilot_evidence_package_card']['package_status']}`",
            f"- Artifact JSON esperado: `{report['real_pilot_evidence_package_card']['focus_artifact']}`",
            f"- Requiere auditoria estricta: `{_format_bool(report['real_pilot_evidence_package_card']['package_requires_strict_audit'])}`",
            f"- Puede cerrar beta desde esta tarjeta: `{_format_bool(report['real_pilot_evidence_package_card']['can_close_beta_from_package_card'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_evidence_package_card']['usable_as_beta_evidence'])}`",
            "",
            "## Brief del operador local",
            "",
            f"- Artifact: `{operator_brief_name}`",
            f"- Estado del brief: `{report['real_pilot_operator_brief_card']['brief_status']}`",
            f"- Permitido ejecutar localmente: `{_format_bool(report['real_pilot_operator_brief_card']['local_run_allowed'])}`",
            f"- Comando seguro para copia local: `{_format_bool(report['real_pilot_operator_brief_card']['command_safe_to_copy_for_local_operator'])}`",
            f"- Pendientes locales: `{report['real_pilot_operator_brief_card']['pending_brief_count']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_operator_brief_card']['usable_as_beta_evidence'])}`",
            "",
            "## Run sheet del piloto real",
            "",
            f"- Artifact: `{run_sheet_name}`",
            f"- Estado de la hoja: `{report['real_pilot_run_sheet_card']['sheet_status']}`",
            f"- Fases requeridas: `{report['real_pilot_run_sheet_card']['required_phase_count']}`",
            f"- Permitido ejecutar localmente: `{_format_bool(report['real_pilot_run_sheet_card']['local_run_allowed'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_run_sheet_card']['usable_as_beta_evidence'])}`",
            "",
            "## Go/no-go final del operador",
            "",
            f"- Artifact: `{final_go_no_go_name}`",
            f"- Estado go/no-go: `{report['real_pilot_final_go_no_go_card']['go_no_go_status']}`",
            f"- Requiere decision final: `{_format_bool(report['real_pilot_final_go_no_go_card']['requires_final_operator_decision'])}`",
            f"- Puede ejecutar sin decision final: `{_format_bool(report['real_pilot_final_go_no_go_card']['can_execute_without_final_decision'])}`",
            f"- Pendientes finales: `{report['real_pilot_final_go_no_go_card']['pending_review_count']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_final_go_no_go_card']['usable_as_beta_evidence'])}`",
            "",
            "## Recibo local del piloto real",
            "",
            f"- Artifact: `{local_receipt_name}`",
            f"- Estado del recibo: `{report['real_pilot_local_receipt_card']['receipt_status']}`",
            f"- Pendientes del recibo: `{report['real_pilot_local_receipt_card']['pending_receipt_count']}`",
            f"- Registra identidad del operador: `{_format_bool(report['real_pilot_local_receipt_card']['records_operator_identity'])}`",
            f"- Usable como evidencia beta: `{_format_bool(report['real_pilot_local_receipt_card']['usable_as_beta_evidence'])}`",
            "",
            "## Preflight de fixture de transcripcion",
            "",
            f"- Artifact: `{fixture_preflight_name}`",
            f"- Estado: `{report['fixture_preflight_card']['status']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['fixture_preflight_card']['usable_as_beta_evidence'])}`",
            f"- ffmpeg: `{report['fixture_preflight_card']['ffmpeg']['status']}`",
            f"- Comando fixture: `{report['fixture_preflight_card']['fixture_command']}`",
            f"- Comando MP3 propio: `{report['fixture_preflight_card']['own_audio_preflight_command']}`",
            f"- Artifacts esperados: {_format_inline_list(report['fixture_preflight_card']['expected_artifacts'])}",
            "",
            "## Readiness de transcripcion real",
            "",
            f"- Artifact: `{transcription_readiness_name}`",
            f"- Estado: `{report['transcription_readiness_card']['status']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['transcription_readiness_card']['usable_as_beta_evidence'])}`",
            f"- ffmpeg: `{report['transcription_readiness_card']['ffmpeg']['status']}`",
            f"- Transcripcion local: `{report['transcription_readiness_card']['local_transcription']['status']}`",
            f"- Comando preflight: `{report['transcription_readiness_card']['preflight_command']}`",
            f"- Comando real: `{report['transcription_readiness_card']['real_command']}`",
            f"- Artifacts esperados: {_format_inline_list(report['transcription_readiness_card']['expected_artifacts'])}",
            "",
            "## Readiness de salida system",
            "",
            f"- Artifact: `{system_output_readiness_name}`",
            f"- Estado: `{report['system_output_readiness_card']['status']}`",
            f"- Usable como evidencia beta: `{_format_bool(report['system_output_readiness_card']['usable_as_beta_evidence'])}`",
            f"- Backend system: `{report['system_output_readiness_card']['output_backend']['status']}`",
            f"- Comando dry-run: `{report['system_output_readiness_card']['dry_run_command']}`",
            f"- Comando audible: `{report['system_output_readiness_card']['audible_command']}`",
            f"- Artifacts esperados: {_format_inline_list(report['system_output_readiness_card']['expected_artifacts'])}",
            "",
        ]
    )
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
            ]
        )
        _append_conditional_required_field_lines(lines, step)
        _append_strict_backend_guard_lines(lines, step)
        lines.extend([f"- Motivo: {step['reason']}", ""])
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
                ]
            )
            _append_conditional_required_field_lines(lines, step)
            _append_strict_backend_guard_lines(lines, step)
            lines.extend([f"- Motivo: {step['reason']}", ""])
    else:
        lines.extend(["- No quedan evidencias beta pendientes segun los artifacts JSON actuales.", ""])
    lines.extend(
        [
            "## Auditoria estricta",
            "",
            f"- Comando: `{beta['strict_audit_command']}`",
            f"- Auditoria de privacidad: `{beta['privacy_audit']['status']}`",
            f"- Hallazgos de privacidad: `{beta['privacy_audit']['finding_count']}`",
            f"- Checklist de entorno previo: `{environment_checklist_name}`",
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
            ]
        )
        _append_strict_backend_guard_lines(lines, row)
        lines.extend([f"- Nota: {row['notes']}", ""])
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


def _format_real_pilot_findings_template_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    template = report["real_pilot_findings_template"]
    lines = [
        "# Plantilla de hallazgos de pilotos reales",
        "",
        "Copiar esta plantilla a `PILOT_FINDINGS.md` despues de ejecutar pilotos reales. Mantener placeholders hasta tener datos publicos y sanitizados.",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(template['safe_to_share'])}`",
        f"- Usa placeholders: `{_format_bool(template['uses_placeholders'])}`",
        f"- Registra audio: `{_format_bool(template['records_audio'])}`",
        f"- Registra transcripciones completas: `{_format_bool(template['records_transcripts'])}`",
        f"- Registra texto hablado real: `{_format_bool(template['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(template['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(template['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(template['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(template['records_operator_identity'])}`",
        "",
        "## Resumen",
        "",
        "- Fecha: `<YYYY-MM-DD>`",
        "- Version AuralisVoiceKit: `" + str(report["version"]) + "`",
        "- Sistema operativo: `<Windows|Linux|Darwin>`",
        "- Python: `<major.minor.patch>`",
        "- Hardware revisado: `<microfono|salida-system|audio-transcripcion>`",
        "- Resultado general: `<passed|warning|failed>`",
        "- Blockers beta pendientes antes del piloto: " + _format_inline_list(beta["blockers"]),
        "- Blockers cerrados por este piloto: `<ninguno|blocker-id-list>`",
        "",
        "## Evidencias JSON",
        "",
        "- `manual-pilot-report.json`: `<presente|no-aplica>`",
        "- `output-pilot-report.json`: `<presente|no-aplica>`",
        "- `transcription-pilot-report.json`: `<presente|no-aplica>`",
        "- Auditoria estricta: `python tools/beta_readiness.py --audit-evidence --evidence pilot_runs/manual --evidence pilot_runs/output --evidence pilot_runs/transcription --fail-on-audit-gaps --json`",
        "",
        "## Captura real",
        "",
        "- Sistema esperado coincidio: `<true|false|no-aplica>`",
        "- Entrada revisada: `<true|false|no-aplica>`",
        "- Checklist listo para beta: `<true|false|no-aplica>`",
        "- Hallazgo sanitizado: `<resumen sin nombres de dispositivos ni rutas locales>`",
        "",
        "## Salida audible",
        "",
        "- Texto revisado y publico/no sensible: `<true|false|no-aplica>`",
        "- Scan de privacidad del texto hablado paso: `<true|false|no-aplica>`",
        "- Operador confirmo audio audible: `<true|false|no-aplica>`",
        "- Voz/volumen/pronunciacion revisados: `<true|false|no-aplica>`",
        "- Hallazgo sanitizado: `<resumen sin texto hablado real ni identidad del operador>`",
        "",
        "## Transcripcion real",
        "",
        "- Audio confirmado no sensible: `<true|false|no-aplica>`",
        "- Nombre del archivo de audio redactado: `<true|false|no-aplica>`",
        "- Referencia revisada: `<true|false|no-aplica>`",
        "- Scan de privacidad de referencia paso: `<true|false|no-aplica>`",
        "- Calidad revisada: `<true|false|no-aplica>`",
        "- Word accuracy: `<valor-agregado-o-no-aplica>`",
        "- Hallazgo sanitizado: `<resumen sin transcripcion, referencia, rutas ni nombres de archivos>`",
        "",
        "## Seguimiento",
        "",
        "- Issue o tarea sugerida: `<titulo-sanitizado>`",
        "- Severidad: `<baja|media|alta>`",
        "- Reproducible con artifact publico: `<si|no>`",
        "- Proximo paso: `<accion-sin-datos-privados>`",
        "",
    ]
    return "\n".join(lines)


def _format_real_pilot_command_pack_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    pack = report["real_pilot_command_pack"]
    environment_checklist_name = Path(
        report["artifacts"].get("real_pilot_environment_checklist", "real-pilot-environment-checklist.md")
    ).name
    fixture_preflight_name = Path(
        report["artifacts"].get("real_pilot_fixture_preflight", "real-pilot-fixture-preflight.md")
    ).name
    transcription_readiness_name = Path(
        report["artifacts"].get("real_pilot_transcription_readiness", "real-pilot-transcription-readiness.md")
    ).name
    system_output_readiness_name = Path(
        report["artifacts"].get("real_pilot_system_output_readiness", "real-pilot-system-output-readiness.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    lines = [
        "# Paquete de comandos para pilotos reales AuralisVoiceKit",
        "",
        "Este artefacto agrupa comandos por plataforma sin incluir audio, transcripciones, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(beta['ready_for_beta'])}`",
        f"- Blockers pendientes: {_format_inline_list(beta['blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(beta['satisfied_json_blockers'])}",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(pack['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(pack['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(pack['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(pack['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(pack['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(pack['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(pack['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(pack['records_operator_identity'])}`",
        "",
        "## Uso rapido",
        "",
        "- Ejecutar primero los comandos con estado `recommended` que preparan fixtures, checklists o preflights.",
        "- Ejecutar comandos `pending` solo con hardware/audio no sensible y revision humana completada.",
        "- Conservar los artifacts JSON/Markdown generados por las herramientas; no copiar contenido privado al reporte publico.",
        f"- Revisar `{environment_checklist_name}` antes de usar audio real.",
        f"- Revisar `{fixture_preflight_name}` antes de reemplazar el fixture por un MP3 propio.",
        f"- Revisar `{transcription_readiness_name}` antes de ejecutar transcripcion real con Whisper/OpenAI.",
        f"- Revisar `{system_output_readiness_name}` antes de salida audible real.",
        f"- Revisar `{evidence_manifest_name}` para saber que artifact JSON cierra cada blocker.",
        f"- Revisar `{decision_gate_name}` para confirmar si el siguiente paso esta permitido.",
        "- Cerrar con la auditoria estricta y luego refrescar `BETA_CHECKLIST.md`.",
        "",
        "## Contrato de salida system sin extra pip",
        "",
    ]
    for item in pack["system_output_no_pip_extra_contract"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Comandos por plataforma",
            "",
        ]
    )
    for row in report["platform_pilot_matrix"]:
        required_fields = _command_pack_required_fields(report, row)
        conditional_required_fields = _command_pack_conditional_required_fields(report, row)
        lines.extend(
            [
                f"### {row['platform']} - {row['name']}",
                "",
                f"- Estado: `{row['status']}`",
                f"- Blocker: `{row['blocker'] or 'ninguno'}`",
                f"- Comando: `{row['command']}`",
                f"- Artifact esperado: `{row['artifact']}`",
                f"- Campos requeridos: {_format_inline_list(required_fields)}",
                f"- Requiere hardware: `{_format_bool(row['requires_hardware'])}`",
                f"- Requiere operador: `{_format_bool(row['requires_operator'])}`",
                f"- Requiere audio no sensible: `{_format_bool(row['requires_non_sensitive_audio'])}`",
            ]
        )
        _append_conditional_required_field_lines(lines, {"conditional_required_fields": conditional_required_fields})
        _append_strict_backend_guard_lines(lines, row)
        lines.extend([f"- Nota: {row['notes']}", ""])
    lines.extend(
        [
            "## Auditoria y cierre",
            "",
            f"- Auditoria estricta: `{beta['strict_audit_command']}`",
            f"- Preflight de fixture: `{fixture_preflight_name}`",
            f"- Readiness de transcripcion real: `{transcription_readiness_name}`",
            f"- Readiness de salida system: `{system_output_readiness_name}`",
            f"- Manifiesto de evidencias: `{evidence_manifest_name}`",
            f"- Compuerta go/no-go: `{decision_gate_name}`",
            "- Refrescar checklist: `python tools/beta_readiness.py --evidence pilot_runs/manual --evidence pilot_runs/output --evidence pilot_runs/transcription --output BETA_CHECKLIST.md --fail-on-blockers --json`",
            "- Publicar hallazgos solo con la plantilla sanitizada `real-pilot-findings-template.md`.",
            "",
            "## Placeholders",
            "",
            "- Reemplazar `sample.mp3`, `<audio-path>`, `<expected-text-path>` y `<public-spoken-text>` solo en la maquina del operador.",
            "- No subir archivos de audio, referencias privadas, transcripciones completas ni texto hablado real.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_fixture_preflight_markdown(report: dict[str, Any]) -> str:
    card = report["fixture_preflight_card"]
    policy = report["real_pilot_fixture_preflight"]
    lines = [
        "# Tarjeta de preflight de fixture de transcripcion AuralisVoiceKit",
        "",
        "Este artefacto prepara el primer paso de transcripcion real con audio sintetico publico. No usa microfono, no usa red, no descarga modelos y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Estado: `{card['status']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(report['beta_readiness']['ready_for_beta'])}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        f"- Prepara transcripcion real: `{_format_bool(policy['prepares_real_transcription'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Comandos",
        "",
        f"- Fixture sintetico: `{card['fixture_command']}`",
        f"- Artifact fixture: `{card['fixture_artifact']}`",
        f"- Fixture OpenAI: `{card['openai_fixture_command']}`",
        f"- Artifact fixture OpenAI: `{card['openai_fixture_artifact']}`",
        f"- MP3 propio no sensible: `{card['own_audio_preflight_command']}`",
        f"- Artifact MP3 propio: `{card['own_audio_preflight_artifact']}`",
        f"- MP3 propio OpenAI: `{card['openai_own_audio_preflight_command']}`",
        f"- Artifact MP3 propio OpenAI: `{card['openai_own_audio_preflight_artifact']}`",
        f"- Artifacts esperados: {_format_inline_list(card['expected_artifacts'])}",
        "",
        "## Checks locales",
        "",
        f"- ffmpeg estado: `{card['ffmpeg']['status']}`",
        f"- ffmpeg listo: `{_format_bool(card['ffmpeg']['ready'])}`",
        f"- ffmpeg accion: {card['ffmpeg']['action']}",
        "",
    ]
    if card["target_backend_checks"]:
        lines.extend(["## Backends objetivo", ""])
        for row in card["target_backend_checks"]:
            lines.extend(
                [
                    f"### {row['name']}",
                    "",
                    f"- Estado: `{row['status']}`",
                    f"- Listo: `{_format_bool(row['ready'])}`",
                    f"- Accion: {row['action']}",
                    "",
                ]
            )
    lines.extend(["## Acciones del operador", ""])
    for item in card["operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Condiciones de alto", ""])
    for item in card["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## English",
            "",
            "- Run the synthetic fixture preflight before using private or real audio.",
            "- The fixture is public-safe preparation only; it does not close beta evidence.",
            "- Replace `sample.mp3` with your own non-sensitive MP3 only after reviewing the generated checklist.",
            "- Do not publish audio names, transcripts, expected text or local paths.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_transcription_readiness_markdown(report: dict[str, Any]) -> str:
    card = report["transcription_readiness_card"]
    policy = report["real_pilot_transcription_readiness"]
    lines = [
        "# Tarjeta de readiness de transcripcion real AuralisVoiceKit",
        "",
        "Este artefacto prepara el piloto de transcripcion real con audio propio no sensible. No ejecuta modelos, no usa red, no guarda audio, transcripciones, texto esperado ni rutas locales y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Estado: `{card['status']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(report['beta_readiness']['ready_for_beta'])}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        f"- Prepara transcripcion real: `{_format_bool(policy['prepares_real_transcription'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Comandos",
        "",
        f"- Fixture sintetico: `{card['fixture_command']}`",
        f"- Artifact fixture: `{card['fixture_artifact']}`",
        f"- Fixture OpenAI: `{card['openai_fixture_command']}`",
        f"- Artifact fixture OpenAI: `{card['openai_fixture_artifact']}`",
        f"- Preflight MP3 propio: `{card['preflight_command']}`",
        f"- Artifact preflight: `{card['preflight_artifact']}`",
        f"- Preflight MP3 propio OpenAI: `{card['openai_preflight_command']}`",
        f"- Artifact preflight OpenAI: `{card['openai_preflight_artifact']}`",
        f"- Transcripcion real: `{card['real_command']}`",
        f"- Artifact real: `{card['real_artifact']}`",
        f"- Transcripcion real OpenAI: `{card['openai_real_command']}`",
        f"- Artifact real OpenAI: `{card['openai_real_artifact']}`",
        f"- Artifacts esperados: {_format_inline_list(card['expected_artifacts'])}",
        "",
        "## Checks locales",
        "",
        f"- ffmpeg estado: `{card['ffmpeg']['status']}`",
        f"- ffmpeg listo: `{_format_bool(card['ffmpeg']['ready'])}`",
        f"- ffmpeg accion: {card['ffmpeg']['action']}",
        f"- Transcripcion local estado: `{card['local_transcription']['status']}`",
        f"- Transcripcion local lista: `{_format_bool(card['local_transcription']['ready'])}`",
        f"- Transcripcion local accion: {card['local_transcription']['action']}",
        "",
    ]
    if card["target_backend_checks"]:
        lines.extend(["## Backends objetivo", ""])
        for row in card["target_backend_checks"]:
            lines.extend(
                [
                    f"### {row['name']}",
                    "",
                    f"- Estado: `{row['status']}`",
                    f"- Listo: `{_format_bool(row['ready'])}`",
                    f"- Accion: {row['action']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Campos requeridos",
            "",
            f"- Fixture: {_format_inline_list(card['fixture_required_fields'])}",
            f"- Fixture OpenAI: {_format_inline_list(card['openai_fixture_required_fields'])}",
            f"- Preflight: {_format_inline_list(card['preflight_required_fields'])}",
            f"- Preflight OpenAI: {_format_inline_list(card['openai_preflight_required_fields'])}",
            f"- Real: {_format_inline_list(card['real_required_fields'])}",
            f"- Real condicional: {_format_conditional_required_fields_inline(card['real_conditional_required_fields'])}",
            "",
            "## Acciones del operador",
            "",
        ]
    )
    for item in card["operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Condiciones de alto", ""])
    for item in card["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## English",
            "",
            "- This readiness card prepares real transcription with your own non-sensitive audio; it does not execute a model.",
            "- Run the synthetic fixture and MP3 preflight before using Whisper/OpenAI or any other real backend.",
            "- Keep `--require-target-backend-ready` so missing backends fail before model execution.",
            "- Do not publish transcripts, expected text, audio file names, reference file names or local paths.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_system_output_readiness_markdown(report: dict[str, Any]) -> str:
    card = report["system_output_readiness_card"]
    policy = report["real_pilot_system_output_readiness"]
    lines = [
        "# Tarjeta de readiness de salida system AuralisVoiceKit",
        "",
        "Este artefacto prepara el piloto audible de salida `system`. No reproduce audio, no usa microfono, no guarda texto hablado real y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Estado: `{card['status']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(report['beta_readiness']['ready_for_beta'])}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        f"- Prepara salida audible: `{_format_bool(policy['prepares_audible_output'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Comandos",
        "",
        f"- Dry-run: `{card['dry_run_command']}`",
        f"- Artifact dry-run: `{card['dry_run_artifact']}`",
        f"- Salida audible: `{card['audible_command']}`",
        f"- Artifact audible: `{card['audible_artifact']}`",
        f"- Artifacts esperados: {_format_inline_list(card['expected_artifacts'])}",
        "",
        "## Checks locales",
        "",
        f"- Backend system estado: `{card['output_backend']['status']}`",
        f"- Backend system listo: `{_format_bool(card['output_backend']['ready'])}`",
        f"- Backend system accion: {card['output_backend']['action']}",
        f"- Salida local estado: `{card['local_output']['status']}`",
        f"- Salida local lista: `{_format_bool(card['local_output']['ready'])}`",
        f"- Salida local accion: {card['local_output']['action']}",
        "",
        "## Campos requeridos",
        "",
        f"- Dry-run: {_format_inline_list(card['required_fields'])}",
        f"- Audible: {_format_inline_list(card['audible_required_fields'])}",
        "",
        "## Contrato sin extra pip",
        "",
    ]
    for item in card["no_pip_extra_contract"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Acciones del operador",
            "",
        ]
    )
    for item in card["operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Condiciones de alto", ""])
    for item in card["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## English",
            "",
            "- Run the dry-run first and review the generated operator checklist.",
            "- Real system output requires an operator present, public spoken text and explicit confirmation flags.",
            "- Keep `--require-output-backend-ready` so missing voice commands fail before playback.",
            "- Do not publish spoken text, local paths, private voice/device details or operator identity.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_environment_checklist_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    checklist = report["real_pilot_environment_checklist"]
    lines = [
        "# Checklist de entorno para pilotos reales AuralisVoiceKit",
        "",
        "Este artefacto prepara la maquina local antes de un piloto real. No ejecuta microfono, no reproduce audio, no usa red, no descarga modelos y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(beta['ready_for_beta'])}`",
        f"- Usable como evidencia beta: `{_format_bool(checklist['usable_as_beta_evidence'])}`",
        f"- Blockers pendientes: {_format_inline_list(beta['blockers'])}",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(checklist['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(checklist['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(checklist['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(checklist['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(checklist['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(checklist['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(checklist['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(checklist['records_operator_identity'])}`",
        "",
        "## Checks",
        "",
    ]
    for item in report["environment_checklist"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- Fuente: `{item['source']}`",
                f"- Requerido para: {item['required_for']}",
                f"- Estado: `{item['status']}`",
                f"- Listo: `{_format_bool(item['ready'])}`",
                f"- Sistema objetivo: `{item['target_system'] or 'local'}`",
                f"- Sistema actual: `{item['current_system'] or 'local'}`",
                f"- Accion: {item['action']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Cierre",
            "",
            "- Si falta un backend real, instalar el extra opcional correspondiente antes del piloto.",
            "- Si el sistema objetivo no coincide, ejecutar el mismo command pack en la maquina Windows, Ubuntu/Linux o macOS correcta.",
            "- Despues del piloto real, auditar artifacts con `python tools/beta_readiness.py --audit-evidence --evidence pilot_runs/manual --evidence pilot_runs/output --evidence pilot_runs/transcription --fail-on-audit-gaps --json`.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_evidence_manifest_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    artifact_policy = report["real_pilot_evidence_manifest"]
    manifest = report["evidence_manifest"]
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    lines = [
        "# Manifiesto de evidencias para pilotos reales AuralisVoiceKit",
        "",
        "Este artefacto cruza blockers beta, artifacts JSON esperados y auditoria estricta. No es evidencia beta; es una guia publica para no perder que falta cerrar.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(beta['ready_for_beta'])}`",
        f"- Listo para beta por evidencias JSON: `{_format_bool(manifest['ready_for_beta_by_json_evidence'])}`",
        f"- Usable como evidencia beta: `{_format_bool(artifact_policy['usable_as_beta_evidence'])}`",
        f"- Blockers beta pendientes: {_format_inline_list(manifest['pending_blockers'])}",
        f"- Blockers pendientes solo por auditoria JSON: {_format_inline_list(manifest['missing_json_blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(manifest['closed_blockers'])}",
        f"- Evidencias ignoradas: `{manifest['ignored_count']}`",
        f"- Auditoria de privacidad: `{manifest['privacy_audit']['status']}`",
        f"- Hallazgos de privacidad: `{manifest['privacy_audit']['finding_count']}`",
        f"- Ingesta de evidencia: `{evidence_intake_name}`",
        f"- Ejecucion guiada: `{execution_card_name}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(artifact_policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(artifact_policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(artifact_policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(artifact_policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(artifact_policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(artifact_policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(artifact_policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(artifact_policy['records_operator_identity'])}`",
        "",
        "## Resumen por blocker",
        "",
    ]
    _append_blocker_summary_lines(lines, manifest.get("blocker_summaries", []))
    lines.extend(["## Escaneo de privacidad", ""])
    _append_privacy_audit_lines(lines, manifest.get("privacy_audit", {}))
    lines.extend(["## Plan de remediacion de privacidad", ""])
    _append_privacy_remediation_plan_lines(lines, manifest.get("privacy_remediation_plan", {}))
    lines.extend(["## Siguiente foco de evidencia", ""])
    _append_next_evidence_focus_lines(lines, manifest.get("next_evidence_focus", {}))
    lines.extend(
        [
            "## Tabla de evidencias",
            "",
        ]
    )
    if not manifest["rows"]:
        lines.extend(["- No hay blockers pendientes o cerrados por JSON.", ""])
    for row in manifest["rows"]:
        lines.extend(
            [
                f"### {row['blocker']}",
                "",
                f"- Estado: `{row['status']}`",
                f"- Titulo: {row['title']}",
                f"- Artifact esperado: `{row['artifact']}`",
                f"- JSON aceptado: `{row['accepted_json_artifact'] or 'pendiente'}`",
                f"- Comando: `{row['command'] or 'cerrado por evidencia JSON aceptada'}`",
                f"- Campos requeridos: {_format_inline_list(row['required_fields'])}",
                f"- Campos de politica backend: {_format_inline_list(row.get('policy_required_fields', []))}",
                f"- Revision: `{row['review_state']}`",
            ]
        )
        _append_conditional_required_field_lines(lines, row)
        _append_strict_backend_guard_lines(lines, row)
        lines.append("")
    lines.extend(["## Evidencias aceptadas", ""])
    if manifest["accepted_json_artifacts"]:
        for artifact in manifest["accepted_json_artifacts"]:
            lines.extend(
                [
                    f"- `{artifact['file']}`",
                    f"  - Artifact: `{artifact['artifact']}`",
                    f"  - Blockers cerrados: {_format_inline_list(artifact['satisfied_blockers'])}",
                    f"  - Hallazgos de privacidad: `{artifact['privacy_finding_count']}`",
                ]
            )
        lines.append("")
    else:
        lines.extend(["- Ninguna todavia.", ""])
    lines.extend(["## Evidencias ignoradas", ""])
    if manifest["ignored_json_artifacts"]:
        for artifact in manifest["ignored_json_artifacts"]:
            lines.append(
                f"- `{artifact['file']}`: `{artifact['reason']}` - {artifact['message_es']} / {artifact['message_en']}."
            )
        lines.append("")
    else:
        lines.extend(["- Ninguna.", ""])
    lines.extend(
        [
            "## Auditoria",
            "",
            f"- Auditoria estricta: `{manifest['strict_audit_command']}`",
            f"- Refrescar checklist: `{manifest['refresh_checklist_command']}`",
            "- Si la auditoria sigue marcando blockers, no declarar beta ni estable.",
            "",
            "## Privacidad",
            "",
            "- Mantener solo nombres de artifacts y campos estructurados.",
            "- No copiar audio, transcripciones completas, texto esperado completo, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador.",
            "- Revisar localmente audio propio, referencia y texto hablado antes de confirmar flags de evidencia.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_decision_gate_markdown(report: dict[str, Any]) -> str:
    gate = report["pilot_decision_gate"]
    artifact_policy = report["real_pilot_decision_gate"]
    release_batch = gate.get("release_batch", {})
    release_batch_threshold = release_batch.get("threshold", release_batch.get("tag_every", 5))
    next_step = gate["next_recommended_step"]
    privacy_audit = gate.get("privacy_audit", {})
    privacy_remediation_plan = gate.get("privacy_remediation_plan", {})
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    lines = [
        "# Compuerta go/no-go para pilotos reales AuralisVoiceKit",
        "",
        "Este artefacto resume si el operador puede avanzar con pilotos reales, beta o estable. No ejecuta hardware y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Ultimo tag: `{release_batch.get('latest_tag') or 'ninguno'}`",
        f"- Mejoras desde ultimo tag: `{release_batch.get('commit_count', 0)}/{release_batch_threshold}`",
        f"- Crear tag ahora: `{_format_bool(release_batch.get('ready_for_tag', False))}`",
        f"- Mejoras restantes antes de tag: `{release_batch.get('remaining', 0)}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Motivo pilotos reales: {gate['real_world_pilot']['reason']}",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Motivo beta: {gate['beta']['reason']}",
        f"- Blockers beta: {_format_inline_list(gate['beta']['blockers'])}",
        f"- Estable: `{gate['stable']['decision']}`",
        f"- Motivo estable: {gate['stable']['reason']}",
        f"- Blockers estable: {_format_inline_list(gate['stable']['blockers'])}",
        f"- Auditoria de privacidad: `{privacy_audit.get('status', 'unknown')}`",
        f"- Hallazgos de privacidad: `{privacy_audit.get('finding_count', 0)}`",
        f"- Tarjeta de alto operativo: `{hard_stop_name}`",
        f"- Tarjeta de ingesta de evidencia: `{evidence_intake_name}`",
        f"- Tarjeta de ejecucion: `{execution_card_name}`",
        f"- Tarjeta de consentimiento: `{consent_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Usable como evidencia beta: `{_format_bool(artifact_policy['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(artifact_policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(artifact_policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(artifact_policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(artifact_policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(artifact_policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(artifact_policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(artifact_policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(artifact_policy['records_operator_identity'])}`",
        "",
        "## Siguiente paso recomendado",
        "",
        f"- Nombre: `{next_step['name'] or 'ninguno'}`",
        f"- Titulo: `{next_step['title'] or 'ninguno'}`",
        f"- Comando: `{next_step['command'] or 'ninguno'}`",
        f"- Artifact esperado: `{next_step['artifact'] or 'ninguno'}`",
        f"- Requiere hardware: `{_format_bool(next_step['requires_hardware'])}`",
        f"- Requiere operador: `{_format_bool(next_step['requires_operator'])}`",
        f"- Requiere audio no sensible: `{_format_bool(next_step['requires_non_sensitive_audio'])}`",
        "",
        "## Escaneo de privacidad",
        "",
    ]
    _append_privacy_audit_lines(lines, privacy_audit)
    lines.extend(["## Plan de remediacion de privacidad", ""])
    _append_privacy_remediation_plan_lines(lines, privacy_remediation_plan)
    lines.extend(
        [
        "## Siguiente foco de evidencia",
        "",
        ]
    )
    _append_next_evidence_focus_lines(lines, gate.get("next_evidence_focus", {}))
    lines.extend(
        [
            "## Alcance permitido",
            "",
        ]
    )
    for item in gate["real_world_pilot"]["allowed_scope"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Acciones del operador", ""])
    for item in gate["operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Condiciones de alto", ""])
    for item in gate["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Advertencias de entorno", ""])
    lines.append(f"- Entorno local: {_format_inline_list(gate['local_environment_warnings'])}")
    lines.append(f"- Checks que requieren otro sistema: {_format_inline_list(gate['target_system_checks'])}")
    lines.extend(
        [
            "",
            "## Cierre",
            "",
            "- Si `pilotos reales` es `blocked`, volver al gate de estabilidad antes de tocar hardware.",
            "- Si `beta` es `blocked`, ejecutar solo pilotos reales y auditoria; no declarar beta publica.",
            "- Si `estable` es `blocked`, mantener version pre-1.0 aunque la preparacion de pilotos avance.",
            "- Si `crear tag ahora` es `false`, acumular mejoras publicables y no crear GitHub Release.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_next_evidence_focus_markdown(report: dict[str, Any]) -> str:
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    policy = report["real_pilot_next_evidence_focus"]
    gate = report["pilot_decision_gate"]
    command_pack_name = Path(
        report["artifacts"].get("real_pilot_command_pack", "real-pilot-command-pack.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    transcription_readiness_name = Path(
        report["artifacts"].get("real_pilot_transcription_readiness", "real-pilot-transcription-readiness.md")
    ).name
    system_output_readiness_name = Path(
        report["artifacts"].get("real_pilot_system_output_readiness", "real-pilot-system-output-readiness.md")
    ).name
    environment_checklist_name = Path(
        report["artifacts"].get("real_pilot_environment_checklist", "real-pilot-environment-checklist.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    lines = [
        "# Siguiente foco de evidencia AuralisVoiceKit",
        "",
        "Esta tarjeta resume el proximo blocker beta a cerrar. No ejecuta hardware, no cuenta como evidencia beta y no incluye contenido privado.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Foco",
        "",
    ]
    _append_next_evidence_focus_lines(lines, focus)
    lines.extend(["## Secuencia de preparacion", ""])
    _append_focus_preparation_sequence_lines(
        lines,
        report.get("next_evidence_focus_preparation_sequence", []),
    )
    lines.extend(
        [
            "## Artifacts de apoyo",
            "",
            f"- Paquete de comandos: `{command_pack_name}`",
            f"- Manifiesto de evidencias: `{evidence_manifest_name}`",
            f"- Compuerta go/no-go: `{decision_gate_name}`",
            f"- Readiness de transcripcion real: `{transcription_readiness_name}`",
            f"- Readiness de salida system: `{system_output_readiness_name}`",
            f"- Checklist de entorno: `{environment_checklist_name}`",
            f"- Alto operativo: `{hard_stop_name}`",
            f"- Ingesta de evidencia: `{evidence_intake_name}`",
            f"- Ejecucion guiada: `{execution_card_name}`",
            f"- Ensayo local: `{rehearsal_card_name}`",
            "",
            "## Antes de ejecutar",
            "",
            "- Revisar la compuerta go/no-go y mantener beta bloqueada si `Beta` sigue en `blocked`.",
            "- Revisar el alto operativo antes de tocar hardware, audio real o flags `--confirm-*`.",
            "- Usar solo audio/texto no sensible y confirmar revisiones humanas antes de pasar flags `--confirm-*`.",
            "- Conservar solo artifacts JSON/Markdown generados por las herramientas; no pegar audio, transcripciones, rutas locales ni identidad del operador.",
            "- Colocar solo reportes JSON sanitizados en los directorios sugeridos por la tarjeta de ingesta.",
            f"- Ensayar sin hardware con `{rehearsal_card_name}` antes del comando real.",
            f"- Seguir `{execution_card_name}` como checklist local de ejecucion y cierre.",
            "- Correr la auditoria estricta despues de recolectar evidencia real.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_hard_stop_card_markdown(report: dict[str, Any]) -> str:
    gate = report["pilot_decision_gate"]
    policy = report["real_pilot_hard_stop_card"]
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    next_focus_name = Path(
        report["artifacts"].get("real_pilot_next_evidence_focus", "real-pilot-next-evidence-focus.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    lines = [
        "# Alto operativo para pilotos reales AuralisVoiceKit",
        "",
        "Esta tarjeta resume cuando detenerse antes de tocar hardware, audio real, texto hablado real o flags `--confirm-*`. No ejecuta hardware y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Estable: `{gate['stable']['decision']}`",
        f"- Foco actual: `{gate['next_recommended_step']['name'] or 'ninguno'}`",
        f"- Compuerta go/no-go: `{decision_gate_name}`",
        f"- Tarjeta de foco: `{next_focus_name}`",
        f"- Manifiesto de evidencias: `{evidence_manifest_name}`",
        f"- Ingesta de evidencia: `{evidence_intake_name}`",
        f"- Ejecucion guiada: `{execution_card_name}`",
        f"- Consentimiento local: `{consent_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Condiciones de alto",
        "",
    ]
    for item in gate["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Acciones minimas antes de ejecutar", ""])
    for item in gate["operator_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Alcance permitido", ""])
    for item in gate["real_world_pilot"]["allowed_scope"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Antes de confirmar",
            "",
            "- Usar flags `--confirm-*` solo despues de revision humana local.",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            f"- Guardar reportes reales solo segun `{evidence_intake_name}`.",
            f"- Revisar `{execution_card_name}` antes de iniciar el comando real.",
            f"- Ensayar con `{rehearsal_card_name}` antes de tocar hardware real.",
            f"- Revisar `{consent_card_name}` antes de usar cualquier flag `--confirm-*`.",
            f"- Usar `{audit_closure_name}` despues de generar el JSON real sanitizado.",
            "- Mantener beta y estable bloqueados mientras sus decisiones sigan en `blocked`.",
            "- Volver a correr la auditoria estricta despues de cada piloto real.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_evidence_intake_card_markdown(report: dict[str, Any]) -> str:
    manifest = report["evidence_manifest"]
    policy = report["real_pilot_evidence_intake_card"]
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    findings_template_name = Path(
        report["artifacts"].get("real_pilot_findings_template", "real-pilot-findings-template.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    expected_artifacts = sorted({row["artifact"] for row in manifest["rows"] if row.get("artifact")})
    lines = [
        "# Ingesta de evidencia para pilotos reales AuralisVoiceKit",
        "",
        "Esta tarjeta indica donde colocar reportes reales generados por las herramientas y como auditarlos antes de tocar `BETA_CHECKLIST.md`. No copia audio, transcripciones, texto hablado real, rutas locales ni identidad del operador.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Blockers pendientes: {_format_inline_list(manifest['pending_blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(manifest['closed_blockers'])}",
        f"- Artifacts esperados: {_format_inline_list(expected_artifacts)}",
        f"- Manifiesto: `{evidence_manifest_name}`",
        f"- Compuerta go/no-go: `{decision_gate_name}`",
        f"- Alto operativo: `{hard_stop_name}`",
        f"- Ejecucion guiada: `{execution_card_name}`",
        f"- Consentimiento local: `{consent_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Plantilla de hallazgos: `{findings_template_name}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Directorios sugeridos",
        "",
    ]
    for root in policy["suggested_roots"]:
        lines.append(f"- `{root}`")
    lines.extend(
        [
            "",
            "## Artifacts que puede ingerir la auditoria",
            "",
        ]
    )
    for row in manifest["rows"]:
        lines.extend(
            [
                f"- `{row['artifact']}` para `{row['blocker']}`",
                f"  - Estado actual: `{row['status']}`",
                f"  - Revision: `{row['review_state']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Auditoria",
            "",
            f"- Auditoria estricta: `{manifest['strict_audit_command']}`",
            f"- Refrescar checklist: `{manifest['refresh_checklist_command']}`",
            "- Ejecutar la auditoria estricta antes de declarar cualquier blocker cerrado.",
            "- Si aparecen hallazgos de privacidad, corregir los artifacts localmente y repetir la auditoria.",
            "- Refrescar `BETA_CHECKLIST.md` solo despues de revisar que la auditoria no expone contenido privado.",
            "",
            "## Reglas de ingesta",
            "",
            "- Copiar solo reportes JSON generados por `tools/manual_pilot.py`, `tools/output_pilot.py` o `tools/transcription_pilot.py`.",
            "- Mantener audio, transcripciones completas, texto esperado completo y texto hablado real fuera del repositorio.",
            "- Usar nombres de carpetas publicos por plataforma o tipo de piloto; no usar nombres de personas, dispositivos ni rutas locales.",
            "- Conservar Markdown operativo generado por las herramientas solo si mantiene placeholders y politica publica segura.",
            f"- Usar `{rehearsal_card_name}` para ensayar sin hardware antes de copiar el comando real.",
            f"- Usar `{execution_card_name}` para cerrar cada corrida con auditoria antes de refrescar beta.",
            f"- Usar `{consent_card_name}` como checklist local antes de pasar flags `--confirm-*`.",
            f"- Usar `{audit_closure_name}` para auditar, refrescar checklist y actualizar hallazgos.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_execution_card_markdown(report: dict[str, Any]) -> str:
    focus = report["beta_readiness"].get("next_evidence_focus", {})
    gate = report["pilot_decision_gate"]
    policy = report["real_pilot_execution_card"]
    operator_gate = policy["operator_gate"]
    evidence_manifest = report["evidence_manifest"]
    command_pack_name = Path(
        report["artifacts"].get("real_pilot_command_pack", "real-pilot-command-pack.md")
    ).name
    environment_checklist_name = Path(
        report["artifacts"].get("real_pilot_environment_checklist", "real-pilot-environment-checklist.md")
    ).name
    next_focus_name = Path(
        report["artifacts"].get("real_pilot_next_evidence_focus", "real-pilot-next-evidence-focus.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    findings_template_name = Path(
        report["artifacts"].get("real_pilot_findings_template", "real-pilot-findings-template.md")
    ).name
    sequence = report.get("next_evidence_focus_preparation_sequence", [])
    focus_name = focus.get("name") or "ninguno"
    focus_command = focus.get("command") or "ninguno"
    focus_artifact = focus.get("artifact") or "ninguno"
    lines = [
        "# Tarjeta de ejecucion de piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta ordena una corrida real permitida por la compuerta sin copiar audio, transcripciones, texto esperado, texto hablado real, rutas locales ni identidad del operador. No ejecuta hardware y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{focus_name}`",
        f"- Artifact esperado: `{focus_artifact}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        f"- Orden de ejecucion: `{_format_bool(policy['tracks_execution_order'])}`",
        f"- Confirmaciones humanas: `{_format_bool(policy['tracks_human_confirmations'])}`",
        f"- Cierre por auditoria: `{_format_bool(policy['tracks_audit_closure'])}`",
        f"- Compuerta operador: `{operator_gate['decision']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(operator_gate['allowed_to_run'])}`",
        f"- Requiere revision humana local: `{_format_bool(operator_gate['requires_local_operator_review'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Compuerta del operador",
        "",
        f"- Decision: `{operator_gate['decision']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(operator_gate['allowed_to_run'])}`",
        f"- Razones de bloqueo: {_format_inline_list(operator_gate['blocking_reasons'])}",
        f"- Guard backend estricto requerido: `{_format_bool(operator_gate['strict_backend_guard_required'])}`",
        f"- Artifact JSON esperado: `{operator_gate['focus_artifact']}`",
        "",
        "## Revisiones previas",
        "",
    ]
    for item in operator_gate["pre_run_reviews"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Confirmaciones humanas requeridas",
            "",
        ]
    )
    if operator_gate["human_confirmations"]:
        for item in operator_gate["human_confirmations"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `ninguno`")
    lines.extend(
        [
            "",
            "## Auditoria del comando local",
            "",
            f"- Estado: `{operator_gate['command_audit']['status']}`",
            f"- Seguro para copiar por operador local: `{_format_bool(operator_gate['command_audit']['safe_to_copy_for_local_operator'])}`",
            f"- Flags requeridos: {_format_inline_list(operator_gate['command_audit']['required_flags'])}",
            f"- Flags presentes: {_format_inline_list(operator_gate['command_audit']['present_required_flags'])}",
            f"- Flags faltantes: {_format_inline_list(operator_gate['command_audit']['missing_required_flags'])}",
            f"- Registra valores privados: `{_format_bool(operator_gate['command_audit']['records_private_values'])}`",
            "",
            "## Seguridad de copia del comando",
            "",
            f"- Estado: `{operator_gate['command_audit']['copy_safety']['status']}`",
            f"- Plantilla segura: `{_format_bool(operator_gate['command_audit']['copy_safety']['safe_template'])}`",
            f"- Requiere revision local: `{_format_bool(operator_gate['command_audit']['copy_safety']['copy_requires_local_operator_review'])}`",
            f"- Requiere tarjeta de consentimiento: `{_format_bool(operator_gate['command_audit']['copy_safety']['copy_requires_consent_card'])}`",
            f"- Requiere confirmaciones humanas: `{_format_bool(operator_gate['command_audit']['copy_safety']['copy_requires_human_confirmations'])}`",
            f"- Requiere revisar guard backend estricto: `{_format_bool(operator_gate['command_audit']['copy_safety']['copy_requires_strict_backend_guard_review'])}`",
            f"- Razones de bloqueo: {_format_inline_list(operator_gate['command_audit']['copy_safety']['blocking_reasons'])}",
            f"- Items pendientes locales: {_format_inline_list(operator_gate['command_audit']['copy_safety']['pending_local_review_ids'])}",
            "",
            "### Checklist de copia",
            "",
        ]
    )
    for item in operator_gate["command_audit"]["copy_safety"]["review_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(
        [
            "",
            "## Artifacts de apoyo",
            "",
            f"- Compuerta go/no-go: `{decision_gate_name}`",
            f"- Foco de evidencia: `{next_focus_name}`",
            f"- Alto operativo: `{hard_stop_name}`",
            f"- Ingesta de evidencia: `{evidence_intake_name}`",
            f"- Consentimiento local: `{consent_card_name}`",
            f"- Cierre de auditoria: `{audit_closure_name}`",
            f"- Ensayo local: `{rehearsal_card_name}`",
            f"- Paquete de comandos: `{command_pack_name}`",
            f"- Checklist de entorno: `{environment_checklist_name}`",
            f"- Plantilla de hallazgos: `{findings_template_name}`",
            "",
            "## Antes de iniciar",
            "",
            "- Confirmar que `Pilotos reales` este en `go` y que `Beta` siga en `blocked` hasta cerrar evidencias reales.",
            "- Revisar el alto operativo y detenerse si el audio, texto hablado, referencia, dispositivo o entorno no son publicos/no sensibles.",
            f"- Ejecutar ensayo local con `{rehearsal_card_name}` antes de copiar el comando real.",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            "- No pasar flags `--confirm-*` hasta que la revision humana correspondiente haya ocurrido.",
            "",
            "## Orden local",
            "",
        ]
    )
    if sequence:
        for step in sequence:
            lines.extend(
                [
                    f"### {step['order']}. {step['title']}",
                    "",
                    f"- Paso: `{step['name']}`",
                    f"- Comando: `{step['command']}`",
                    f"- Artifact esperado: `{step['artifact']}`",
                    f"- Campos requeridos: {_format_inline_list(step['required_fields'])}",
                    f"- Campos de politica backend: {_format_inline_list(step.get('policy_required_fields', []))}",
                    f"- Requiere hardware: `{_format_bool(step['requires_hardware'])}`",
                    f"- Requiere operador: `{_format_bool(step['requires_operator'])}`",
                    f"- Requiere audio no sensible: `{_format_bool(step['requires_non_sensitive_audio'])}`",
                    f"- Revision requerida: `{_format_bool(step['review_required'])}`",
                ]
            )
            _append_conditional_required_field_lines(lines, step)
            _append_strict_backend_guard_lines(lines, step)
            lines.append("")
    else:
        lines.extend(["- No hay foco pendiente; no ejecutar pilotos reales adicionales sin refrescar la compuerta.", ""])
    lines.extend(
        [
            "## Contrato de evidencia beta",
            "",
            f"- Seguro para compartir: `{_format_bool(operator_gate['evidence_contract']['safe_to_share'])}`",
            f"- Blocker: `{operator_gate['evidence_contract']['blocker']}`",
            f"- Artifact esperado: `{operator_gate['evidence_contract']['expected_artifact']}`",
            f"- Campos requeridos: `{operator_gate['evidence_contract']['required_field_count']}`",
            f"- Campos faltantes actuales: `{operator_gate['evidence_contract']['missing_field_count']}`",
            f"- Campos requeridos actuales: {_format_inline_list(operator_gate['evidence_contract']['required_fields'])}",
            f"- Campos condicionales: `{operator_gate['evidence_contract']['conditional_required_field_count']}`",
            f"- Campos de politica backend: {_format_inline_list(operator_gate['evidence_contract']['policy_required_fields'])}",
            f"- Campos de politica backend requeridos: `{operator_gate['evidence_contract']['policy_required_field_count']}`",
            f"- Directorios sugeridos: {_format_inline_list(operator_gate['evidence_contract']['suggested_roots'])}",
            f"- Auditoria estricta: `{operator_gate['evidence_contract']['strict_audit_command']}`",
            f"- Refrescar checklist: `{operator_gate['evidence_contract']['refresh_checklist_command']}`",
            f"- Registra audio: `{_format_bool(operator_gate['evidence_contract']['records_audio'])}`",
            f"- Registra transcripciones: `{_format_bool(operator_gate['evidence_contract']['records_transcripts'])}`",
            f"- Registra rutas locales: `{_format_bool(operator_gate['evidence_contract']['records_local_paths'])}`",
            "",
            "## Comando del foco",
            "",
            f"- Comando: `{focus_command}`",
            f"- Campos requeridos: {_format_inline_list(focus.get('required_fields', []))}",
            f"- Campos de politica backend: {_format_inline_list(focus.get('policy_required_fields', []))}",
            f"- Campos faltantes actuales: {_format_inline_list(focus.get('missing_fields', []))}",
            f"- Candidato mas cercano: `{focus.get('closest_candidate') or 'ninguno'}`",
            "",
            "## Despues de ejecutar",
            "",
            f"- Guardar solo `{focus_artifact}` sanitizado en uno de estos directorios: {_format_inline_list(report['real_pilot_evidence_intake_card']['suggested_roots'])}.",
            "- Mantener fuera del repositorio audio, transcripciones completas, texto esperado completo, texto hablado real, rutas locales, nombres reales de dispositivos e identidad del operador.",
            f"- Correr auditoria estricta: `{operator_gate['audit_closure']['strict_audit_command']}`",
            f"- Refrescar checklist solo si la auditoria no expone contenido privado: `{operator_gate['audit_closure']['refresh_checklist_command']}`",
            f"- Usar cierre de auditoria: `{audit_closure_name}`",
            f"- Registrar hallazgos publicos con `{operator_gate['audit_closure']['findings_template']}`.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in gate["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _format_real_pilot_consent_card_markdown(report: dict[str, Any]) -> str:
    policy = report["real_pilot_consent_card"]
    gate = report["pilot_decision_gate"]
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    findings_template_name = Path(
        report["artifacts"].get("real_pilot_findings_template", "real-pilot-findings-template.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    lines = [
        "# Consentimiento local para piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta es una plantilla publica para el operador local. No registra nombres, firmas, identidad, audio, rutas, transcripciones, texto esperado ni texto hablado real. No ejecuta hardware y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Decision consentimiento: `{policy['decision']}`",
        f"- Foco: `{policy['focus']}`",
        f"- Artifact esperado: `{policy['focus_artifact']}`",
        f"- Permitido despues de consentimiento: `{_format_bool(policy['allowed_to_run_after_consent'])}`",
        f"- Requiere operador local: `{_format_bool(policy['requires_local_operator'])}`",
        f"- Requiere consentimiento del operador: `{_format_bool(policy['requires_operator_consent'])}`",
        f"- Faltantes de consentimiento: `{policy['missing_consent_count']}`",
        f"- Usable como evidencia beta: `{_format_bool(policy['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(policy['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(policy['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(policy['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        f"- Registra firma: `{_format_bool(policy['records_signature'])}`",
        "",
        "## Artifacts que debe revisar el operador",
        "",
        f"- Compuerta go/no-go: `{decision_gate_name}`",
        f"- Alto operativo: `{hard_stop_name}`",
        f"- Ejecucion guiada: `{execution_card_name}`",
        f"- Ingesta de evidencia: `{evidence_intake_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Plantilla de hallazgos: `{findings_template_name}`",
        "",
        "## Checklist de consentimiento local",
        "",
    ]
    for item in policy["consent_items"]:
        marker = "x" if item["confirmed"] is True else " "
        lines.append(
            f"- [{marker}] `{item['id']}` required={str(item['required']).lower()} "
            f"source={item['source']} - {item['instruction']}"
        )
    lines.extend(
        [
            "",
            "## Revisiones previas",
            "",
        ]
    )
    for item in policy["pre_run_reviews"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Confirmaciones humanas del foco", ""])
    if policy["human_confirmations"]:
        for item in policy["human_confirmations"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `ninguno`")
    lines.extend(
        [
            "",
            "## Comando del foco",
            "",
            f"- Comando: `{policy['focus_command']}`",
            "- Reemplazar placeholders solo localmente.",
            "- No compartir comandos con valores locales reales.",
            "",
            "## Cierre obligatorio",
            "",
            f"- Ensayo previo: `{rehearsal_card_name}`",
            f"- Auditoria estricta: `{policy['strict_audit_command']}`",
            f"- Refrescar checklist: `{policy['refresh_checklist_command']}`",
            f"- Revisar cierre de auditoria: `{audit_closure_name}`",
            "- Registrar hallazgos publicos solo con la plantilla sanitizada.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in gate["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _format_real_pilot_audit_closure_markdown(report: dict[str, Any]) -> str:
    closure = report["real_pilot_audit_closure_card"]
    gate = report["pilot_decision_gate"]
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    evidence_package_name = Path(
        report["artifacts"].get("real_pilot_evidence_package_card", "real-pilot-evidence-package.md")
    ).name
    operator_brief_name = Path(
        report["artifacts"].get("real_pilot_operator_brief_card", "real-pilot-operator-brief.md")
    ).name
    run_sheet_name = Path(
        report["artifacts"].get("real_pilot_run_sheet_card", "real-pilot-run-sheet.md")
    ).name
    final_go_no_go_name = Path(
        report["artifacts"].get("real_pilot_final_go_no_go_card", "real-pilot-final-go-no-go.md")
    ).name
    local_receipt_name = Path(
        report["artifacts"].get("real_pilot_local_receipt_card", "real-pilot-local-receipt.md")
    ).name
    lines = [
        "# Cierre de auditoria para piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta guia el cierre posterior a un piloto real. No ejecuta hardware, no lee audio y no cuenta como evidencia beta por si sola; solo ordena auditoria, refresco de checklist y hallazgos sanitizados.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{closure['focus']}`",
        f"- Estado de cierre: `{closure['closure_status']}`",
        f"- Artifact JSON esperado: `{closure['expected_json_artifact']}`",
        f"- Auditoria requerida: `{_format_bool(closure['audit_required'])}`",
        f"- Puede cerrar sin auditoria: `{_format_bool(closure['can_close_without_audit'])}`",
        f"- Puede refrescar beta sin auditoria: `{_format_bool(closure['can_refresh_beta_without_audit'])}`",
        f"- Usable como evidencia beta: `{_format_bool(closure['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(closure['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(closure['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(closure['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(closure['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(closure['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(closure['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(closure['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(closure['records_operator_identity'])}`",
        "",
        "## Artifacts de apoyo",
        "",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Paquete de evidencia: `{evidence_package_name}`",
        f"- Brief del operador: `{operator_brief_name}`",
        f"- Run sheet: `{run_sheet_name}`",
        f"- Go/no-go final: `{final_go_no_go_name}`",
        f"- Recibo local: `{local_receipt_name}`",
        f"- Ejecucion guiada: `{closure['execution_card']}`",
        f"- Consentimiento local: `{closure['consent_card']}`",
        f"- Ingesta de evidencia: `{closure['evidence_intake_card']}`",
        f"- Plantilla de hallazgos: `{closure['finding_template']}`",
        "",
        "## Directorios sugeridos",
        "",
    ]
    for root in closure["suggested_roots"]:
        lines.append(f"- `{root}`")
    lines.extend(["", "## Checklist de cierre", ""])
    for item in closure["closure_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(
        [
            "",
            "## Comandos",
            "",
            f"- Auditoria estricta: `{closure['strict_audit_command']}`",
            f"- Refrescar checklist: `{closure['refresh_checklist_command']}`",
            "",
            "## Reglas",
            "",
            "- No copiar audio, transcripciones, texto esperado, texto hablado real, rutas locales ni nombres de dispositivos en hallazgos compartidos.",
            "- Ejecutar la auditoria estricta antes de refrescar beta o publicar hallazgos.",
            "- Si la auditoria reporta gaps, corregir artifacts sanitizados antes de declarar avance beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_rehearsal_markdown(report: dict[str, Any]) -> str:
    rehearsal = report["real_pilot_rehearsal_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Ensayo local antes del piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta guia un ensayo publico antes del piloto real. No ejecuta hardware, no abre microfono, no reproduce audio, no ejecuta modelos y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{rehearsal['focus']}`",
        f"- Estado de ensayo: `{rehearsal['rehearsal_status']}`",
        f"- Artifact esperado: `{rehearsal['focus_artifact']}`",
        f"- Requiere operador local: `{_format_bool(rehearsal['requires_local_operator'])}`",
        f"- Requiere hardware real: `{_format_bool(rehearsal['requires_real_hardware'])}`",
        f"- Puede ejecutar comando real desde esta tarjeta: `{_format_bool(rehearsal['can_execute_real_command_from_card'])}`",
        f"- Copia del comando real permitida tras ensayo: `{_format_bool(rehearsal['real_command_copy_allowed_after_rehearsal'])}`",
        f"- Usable como evidencia beta: `{_format_bool(rehearsal['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(rehearsal['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(rehearsal['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(rehearsal['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(rehearsal['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(rehearsal['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(rehearsal['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(rehearsal['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(rehearsal['records_operator_identity'])}`",
        "",
        "## Comandos seguros de ensayo",
        "",
    ]
    for command in rehearsal["safe_rehearsal_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Artifacts de apoyo", ""])
    for artifact in rehearsal["support_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Checklist de ensayo", ""])
    for item in rehearsal["rehearsal_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} hardware={str(item['requires_hardware']).lower()} "
            f"operator={str(item['requires_operator']).lower()} source={item['source']}"
        )
    lines.extend(
        [
            "",
            "## Comando real",
            "",
            f"- Comando del foco: `{rehearsal['focus_command']}`",
            "- No ejecutar este comando durante el ensayo.",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            "- Copiar o ejecutar el comando real solo despues de revisar consentimiento, alto operativo y guards estrictos.",
            "",
            "## Cierre posterior",
            "",
            f"- Auditoria estricta: `{rehearsal['strict_audit_command']}`",
            f"- Refrescar checklist: `{rehearsal['refresh_checklist_command']}`",
            "- Preparar `real-pilot-evidence-package.md` con los artifacts sanitizados antes de auditar beta.",
            "- Ejecutar estas acciones solo despues de generar el JSON real sanitizado.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_evidence_package_markdown(report: dict[str, Any]) -> str:
    package = report["real_pilot_evidence_package_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Paquete de evidencia sanitizada para piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta organiza que debe quedar junto al JSON real sanitizado antes de auditar beta. No ejecuta hardware, no lee audio, no registra rutas locales y no cuenta como evidencia beta por si sola.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{package['focus']}`",
        f"- Artifact JSON esperado: `{package['focus_artifact']}`",
        f"- Estado del paquete: `{package['package_status']}`",
        f"- Requiere auditoria estricta: `{_format_bool(package['package_requires_strict_audit'])}`",
        f"- Requiere refrescar beta: `{_format_bool(package['package_requires_beta_refresh'])}`",
        f"- Puede cerrar beta desde esta tarjeta: `{_format_bool(package['can_close_beta_from_package_card'])}`",
        f"- Usable como evidencia beta: `{_format_bool(package['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(package['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(package['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(package['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(package['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(package['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(package['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(package['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(package['records_operator_identity'])}`",
        "",
        "## Artifacts esperados",
        "",
    ]
    for artifact in package["expected_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Artifacts de apoyo", ""])
    for artifact in package["support_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Directorios sugeridos", ""])
    for root in package["suggested_roots"]:
        lines.append(f"- `{root}`")
    lines.extend(["", "## Campos JSON requeridos", ""])
    for field in package["required_json_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "## Campos faltantes actuales", ""])
    if package["missing_json_fields"]:
        for field in package["missing_json_fields"]:
            lines.append(f"- `{field}`")
    else:
        lines.append("- `ninguno`")
    lines.extend(["", "## Checklist del paquete", ""])
    for item in package["package_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(
        [
            "",
            "## Comandos",
            "",
            f"- Auditoria estricta: `{package['strict_audit_command']}`",
            f"- Refrescar checklist: `{package['refresh_checklist_command']}`",
            "",
            "## Reglas",
            "",
            "- Guardar solo JSON/Markdown sanitizados junto al paquete.",
            "- No copiar audio, transcripciones, texto hablado real, texto esperado completo, rutas locales, dispositivos ni identidad.",
            "- Si la auditoria falla, corregir artifacts sanitizados antes de refrescar beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_operator_brief_markdown(report: dict[str, Any]) -> str:
    brief = report["real_pilot_operator_brief_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Brief del operador local para piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta resume la ejecucion local permitida por la compuerta. No ejecuta hardware, no copia valores privados y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{brief['focus']}`",
        f"- Artifact esperado: `{brief['focus_artifact']}`",
        f"- Estado del brief: `{brief['brief_status']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(brief['local_run_allowed'])}`",
        f"- Comando seguro para copia local: `{_format_bool(brief['command_safe_to_copy_for_local_operator'])}`",
        f"- Estado de seguridad de copia: `{brief['copy_safety_status']}`",
        f"- Requiere revision local: `{_format_bool(brief['requires_local_operator_review'])}`",
        f"- Usable como evidencia beta: `{_format_bool(brief['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(brief['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(brief['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(brief['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(brief['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(brief['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(brief['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(brief['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(brief['records_operator_identity'])}`",
        "",
        "## Lectura previa",
        "",
    ]
    for artifact in brief["before_run_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(
        [
            "",
            "## Comando plantilla",
            "",
            f"- `{brief['local_command_template']}`",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            "- No ejecutar si algun item de alto operativo aplica.",
            "- No pasar flags `--confirm-*` hasta completar la revision humana correspondiente.",
            "",
            "## Confirmaciones humanas",
            "",
        ]
    )
    if brief["human_confirmations"]:
        for item in brief["human_confirmations"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `ninguno`")
    lines.extend(["", "## Pendientes de copia local", ""])
    if brief["copy_pending_ids"]:
        for item in brief["copy_pending_ids"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `ninguno`")
    lines.extend(["", "## Checklist del brief", ""])
    for item in brief["brief_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(["", "## Despues del piloto", ""])
    for artifact in brief["after_run_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(
        [
            "",
            f"- Auditoria estricta: `{brief['strict_audit_command']}`",
            f"- Refrescar checklist: `{brief['refresh_checklist_command']}`",
            "- Guardar solo JSON/Markdown sanitizados antes de auditar beta.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in brief["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Reglas",
            "",
            "- Mantener fuera del repositorio audio, transcripciones, texto esperado completo, texto hablado real, rutas locales, dispositivos e identidad.",
            "- Si la auditoria estricta falla, corregir artifacts sanitizados antes de refrescar beta.",
            "- Esta tarjeta puede compartirse como guia operativa, pero no como evidencia beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_run_sheet_markdown(report: dict[str, Any]) -> str:
    sheet = report["real_pilot_run_sheet_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Run sheet del piloto real AuralisVoiceKit",
        "",
        "Esta hoja ordena la corrida local por fases. No ejecuta hardware, no copia valores privados y no cuenta como evidencia beta.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{sheet['focus']}`",
        f"- Artifact esperado: `{sheet['focus_artifact']}`",
        f"- Estado de la hoja: `{sheet['sheet_status']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(sheet['local_run_allowed'])}`",
        f"- Comando seguro para copia local: `{_format_bool(sheet['command_safe_to_copy_for_local_operator'])}`",
        f"- Fases requeridas: `{sheet['required_phase_count']}`",
        f"- Usable como evidencia beta: `{_format_bool(sheet['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(sheet['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(sheet['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(sheet['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(sheet['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(sheet['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(sheet['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(sheet['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(sheet['records_operator_identity'])}`",
        "",
        "## Artifacts previos",
        "",
    ]
    for artifact in sheet["prerequisite_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Fases", ""])
    for index, phase in enumerate(sheet["phases"], start=1):
        lines.extend(
            [
                f"### {index}. {phase['id']}",
                "",
                f"- Estado: `{phase['status']}`",
                f"- Requerida: `{_format_bool(phase['required'])}`",
                f"- Requiere hardware: `{_format_bool(phase['requires_hardware'])}`",
                f"- Requiere operador local: `{_format_bool(phase['requires_local_operator'])}`",
                f"- Fuente: `{phase['source']}`",
            ]
        )
        if phase.get("artifacts"):
            lines.append(f"- Artifacts: {_format_inline_list(phase['artifacts'])}")
        if phase.get("commands"):
            lines.append(f"- Comandos seguros: {_format_inline_list(phase['commands'])}")
        if phase.get("copy_pending_ids"):
            lines.append(f"- Pendientes de copia: {_format_inline_list(phase['copy_pending_ids'])}")
        if phase.get("go_no_go_required"):
            lines.append(f"- Requiere decision go/no-go local: `{_format_bool(phase['go_no_go_required'])}`")
        if phase.get("command"):
            lines.append(f"- Comando: `{phase['command']}`")
        if phase.get("human_confirmations"):
            lines.append(f"- Confirmaciones humanas: {_format_inline_list(phase['human_confirmations'])}")
        if phase.get("expected_receipt_items"):
            lines.append(f"- Items de recibo: {_format_inline_list(phase['expected_receipt_items'])}")
        if phase.get("expected_artifacts"):
            lines.append(f"- Artifacts esperados: {_format_inline_list(phase['expected_artifacts'])}")
        if phase.get("required_json_fields"):
            lines.append(f"- Campos JSON requeridos: {_format_inline_list(phase['required_json_fields'])}")
        if phase.get("missing_json_fields"):
            lines.append(f"- Campos JSON faltantes actuales: {_format_inline_list(phase['missing_json_fields'])}")
        if phase.get("strict_audit_command"):
            lines.append(f"- Auditoria estricta: `{phase['strict_audit_command']}`")
        if phase.get("refresh_checklist_command"):
            lines.append(f"- Refrescar checklist: `{phase['refresh_checklist_command']}`")
        lines.append("")
    lines.extend(
        [
            "## Comando local",
            "",
            f"- `{sheet['local_command_template']}`",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            "- No ejecutar si quedan fases previas sin revisar.",
            "- No pasar flags `--confirm-*` hasta completar la revision humana correspondiente.",
            "",
            "## Evidencia sanitizada",
            "",
            f"- Artifact JSON esperado: `{sheet['focus_artifact']}`",
            f"- Directorios sugeridos: {_format_inline_list(sheet['suggested_roots'])}",
            f"- Campos requeridos: {_format_inline_list(sheet['required_json_fields'])}",
            f"- Campos faltantes actuales: {_format_inline_list(sheet['missing_json_fields'])}",
            "",
            "## Auditoria y cierre",
            "",
            f"- Auditoria estricta: `{sheet['strict_audit_command']}`",
            f"- Refrescar checklist: `{sheet['refresh_checklist_command']}`",
            "- Guardar solo JSON/Markdown sanitizados antes de auditar beta.",
            "- Si la auditoria falla, corregir artifacts sanitizados antes de refrescar beta.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in sheet["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Reglas",
            "",
            "- Mantener fuera del repositorio audio, transcripciones, texto esperado completo, texto hablado real, rutas locales, dispositivos e identidad.",
            "- Esta hoja puede compartirse como guia operativa, pero no como evidencia beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_final_go_no_go_markdown(report: dict[str, Any]) -> str:
    card = report["real_pilot_final_go_no_go_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Go/no-go final del piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta resume la ultima revision local antes de tocar hardware o ejecutar el comando real. No guarda audio, rutas, dispositivos, textos privados ni identidad del operador.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{card['focus']}`",
        f"- Artifact esperado: `{card['focus_artifact']}`",
        f"- Estado go/no-go: `{card['go_no_go_status']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(card['local_run_allowed'])}`",
        f"- Comando seguro para copia local: `{_format_bool(card['command_safe_to_copy_for_local_operator'])}`",
        f"- Estado de seguridad de copia: `{card['copy_safety_status']}`",
        f"- Requiere decision final del operador: `{_format_bool(card['requires_final_operator_decision'])}`",
        f"- Puede ejecutar sin decision final: `{_format_bool(card['can_execute_without_final_decision'])}`",
        f"- Usable como evidencia beta: `{_format_bool(card['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(card['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(card['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(card['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(card['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(card['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(card['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(card['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(card['records_operator_identity'])}`",
        "",
        "## Artifacts de apoyo",
        "",
    ]
    for artifact in card["support_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Decision local", ""])
    for option in card["decision_options"]:
        lines.append(f"- `{option}`")
    lines.extend(["", "## Condiciones GO", ""])
    for item in card["go_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Condiciones NO-GO", ""])
    for item in card["no_go_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Checklist final", ""])
    for item in card["review_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(["", "## Comando local", ""])
    lines.extend(
        [
            f"- `{card['local_command_template']}`",
            f"- Flags requeridos: {_format_inline_list(card['required_flags'])}",
            f"- Flags faltantes: {_format_inline_list(card['missing_required_flags'])}",
            f"- Confirmaciones humanas: {_format_inline_list(card['human_confirmations'])}",
            f"- Pendientes de copia: {_format_inline_list(card['copy_pending_ids'])}",
            "- Reemplazar placeholders solo en la maquina local del operador.",
            "- No pasar flags `--confirm-*` hasta completar la revision humana correspondiente.",
            "",
            "## Auditoria posterior",
            "",
            f"- Auditoria estricta: `{card['strict_audit_command']}`",
            f"- Refrescar checklist: `{card['refresh_checklist_command']}`",
            "- Guardar solo JSON/Markdown sanitizados antes de auditar beta.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in card["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Reglas",
            "",
            "- Decision `go_after_local_checks` solo si no queda ninguna condicion NO-GO.",
            "- Decision `no_go_stop_and_fix` si aparece cualquier duda de privacidad, permisos, backend o auditoria.",
            "- Esta tarjeta puede compartirse como guia operativa, pero no como evidencia beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_local_receipt_markdown(report: dict[str, Any]) -> str:
    receipt = report["real_pilot_local_receipt_card"]
    gate = report["pilot_decision_gate"]
    lines = [
        "# Recibo local del piloto real AuralisVoiceKit",
        "",
        "Esta tarjeta documenta el resultado local con placeholders publicos. No guarda identidad, firma, audio, rutas, nombres de dispositivos, transcripciones ni texto hablado real.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Pilotos reales: `{gate['real_world_pilot']['decision']}`",
        f"- Beta: `{gate['beta']['decision']}`",
        f"- Foco: `{receipt['focus']}`",
        f"- Artifact esperado: `{receipt['focus_artifact']}`",
        f"- Estado del recibo: `{receipt['receipt_status']}`",
        f"- Permitido ejecutar localmente: `{_format_bool(receipt['local_run_allowed'])}`",
        f"- Requiere go/no-go final: `{_format_bool(receipt['requires_final_go_no_go'])}`",
        f"- Usable como evidencia beta: `{_format_bool(receipt['usable_as_beta_evidence'])}`",
        "",
        "## Politica de contenido",
        "",
        f"- Seguro para compartir: `{_format_bool(receipt['safe_to_share'])}`",
        f"- Registra audio: `{_format_bool(receipt['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(receipt['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(receipt['records_spoken_text'])}`",
        f"- Registra texto esperado completo: `{_format_bool(receipt['records_expected_text'])}`",
        f"- Registra rutas locales: `{_format_bool(receipt['records_local_paths'])}`",
        f"- Registra nombres reales de dispositivos: `{_format_bool(receipt['records_device_names'])}`",
        f"- Registra identidad del operador: `{_format_bool(receipt['records_operator_identity'])}`",
        f"- Registra firma: `{_format_bool(receipt['records_signature'])}`",
        "",
        "## Artifacts de apoyo",
        "",
    ]
    for artifact in receipt["support_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Campos del recibo local", ""])
    for key, value in receipt["receipt_placeholders"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Opciones de decision", ""])
    for option in receipt["decision_options"]:
        lines.append(f"- `{option}`")
    lines.extend(["", "## Checklist del recibo", ""])
    for item in receipt["receipt_items"]:
        lines.append(
            f"- `{item['id']}` required={str(item['required']).lower()} "
            f"status={item['status']} source={item['source']}"
        )
    lines.extend(
        [
            "",
            "## Auditoria posterior",
            "",
            f"- Auditoria estricta: `{receipt['strict_audit_command']}`",
            f"- Refrescar checklist: `{receipt['refresh_checklist_command']}`",
            "- Registrar solo si la auditoria y los hallazgos usan JSON/Markdown sanitizados.",
            "",
            "## Condiciones de alto",
            "",
        ]
    )
    for item in receipt["hard_stop_conditions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Reglas",
            "",
            "- Usar `no_go_stop_and_fix` si el resultado local requiere copiar audio, rutas, texto privado, nombres de dispositivos o identidad.",
            "- Si la auditoria estricta falla, dejar `strict_audit_result` como `failed` y no refrescar beta.",
            "- Esta tarjeta puede compartirse como recibo operativo, pero no como evidencia beta.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_real_pilot_handoff_markdown(report: dict[str, Any]) -> str:
    beta = report["beta_readiness"]
    release_batch = report.get("release_batch", {})
    release_batch_threshold = release_batch.get("threshold", release_batch.get("tag_every", 5))
    policy = report["real_pilot_handoff"]["content_policy"]
    command_pack_name = Path(
        report["artifacts"].get("real_pilot_command_pack", "real-pilot-command-pack.md")
    ).name
    environment_checklist_name = Path(
        report["artifacts"].get("real_pilot_environment_checklist", "real-pilot-environment-checklist.md")
    ).name
    fixture_preflight_name = Path(
        report["artifacts"].get("real_pilot_fixture_preflight", "real-pilot-fixture-preflight.md")
    ).name
    transcription_readiness_name = Path(
        report["artifacts"].get("real_pilot_transcription_readiness", "real-pilot-transcription-readiness.md")
    ).name
    system_output_readiness_name = Path(
        report["artifacts"].get("real_pilot_system_output_readiness", "real-pilot-system-output-readiness.md")
    ).name
    evidence_manifest_name = Path(
        report["artifacts"].get("real_pilot_evidence_manifest", "real-pilot-evidence-manifest.md")
    ).name
    decision_gate_name = Path(
        report["artifacts"].get("real_pilot_decision_gate", "real-pilot-decision-gate.md")
    ).name
    next_focus_name = Path(
        report["artifacts"].get("real_pilot_next_evidence_focus", "real-pilot-next-evidence-focus.md")
    ).name
    hard_stop_name = Path(
        report["artifacts"].get("real_pilot_hard_stop_card", "real-pilot-hard-stop-card.md")
    ).name
    evidence_intake_name = Path(
        report["artifacts"].get("real_pilot_evidence_intake_card", "real-pilot-evidence-intake-card.md")
    ).name
    execution_card_name = Path(
        report["artifacts"].get("real_pilot_execution_card", "real-pilot-execution-card.md")
    ).name
    consent_card_name = Path(
        report["artifacts"].get("real_pilot_consent_card", "real-pilot-consent-card.md")
    ).name
    audit_closure_name = Path(
        report["artifacts"].get("real_pilot_audit_closure_card", "real-pilot-audit-closure.md")
    ).name
    rehearsal_card_name = Path(
        report["artifacts"].get("real_pilot_rehearsal_card", "real-pilot-rehearsal-card.md")
    ).name
    evidence_package_name = Path(
        report["artifacts"].get("real_pilot_evidence_package_card", "real-pilot-evidence-package.md")
    ).name
    operator_brief_name = Path(
        report["artifacts"].get("real_pilot_operator_brief_card", "real-pilot-operator-brief.md")
    ).name
    run_sheet_name = Path(
        report["artifacts"].get("real_pilot_run_sheet_card", "real-pilot-run-sheet.md")
    ).name
    final_go_no_go_name = Path(
        report["artifacts"].get("real_pilot_final_go_no_go_card", "real-pilot-final-go-no-go.md")
    ).name
    local_receipt_name = Path(
        report["artifacts"].get("real_pilot_local_receipt_card", "real-pilot-local-receipt.md")
    ).name
    lines = [
        "# Handoff de pilotos reales AuralisVoiceKit",
        "",
        "Este artefacto es seguro para compartir: usa placeholders y no incluye audio, transcripciones, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador.",
        "",
        "## Estado",
        "",
        f"- Version: `{report['version']}`",
        f"- Stage: `{report['stage']}`",
        f"- Ultimo tag: `{release_batch.get('latest_tag') or 'ninguno'}`",
        f"- Mejoras desde ultimo tag: `{release_batch.get('commit_count', 0)}/{release_batch_threshold}`",
        f"- Crear tag ahora: `{_format_bool(release_batch.get('ready_for_tag', False))}`",
        f"- Piloto seguro paso: `{_format_bool(report['safe_automated_pilot']['passed'])}`",
        f"- Listo para pilotos reales: `{_format_bool(report['gate']['ready_for_real_world_pilots'])}`",
        f"- Listo para beta: `{_format_bool(beta['ready_for_beta'])}`",
        f"- Blockers pendientes: {_format_inline_list(beta['blockers'])}",
        f"- Blockers cerrados por JSON: {_format_inline_list(beta['satisfied_json_blockers'])}",
        f"- Paquete de comandos: `{command_pack_name}`",
        f"- Checklist de entorno: `{environment_checklist_name}`",
        f"- Preflight de fixture: `{fixture_preflight_name}`",
        f"- Readiness de transcripcion real: `{transcription_readiness_name}`",
        f"- Readiness de salida system: `{system_output_readiness_name}`",
        f"- Manifiesto de evidencias: `{evidence_manifest_name}`",
        f"- Compuerta go/no-go: `{decision_gate_name}`",
        f"- Tarjeta de foco: `{next_focus_name}`",
        f"- Tarjeta de alto operativo: `{hard_stop_name}`",
        f"- Ingesta de evidencia: `{evidence_intake_name}`",
        f"- Ejecucion guiada: `{execution_card_name}`",
        f"- Consentimiento local: `{consent_card_name}`",
        f"- Cierre de auditoria: `{audit_closure_name}`",
        f"- Ensayo local: `{rehearsal_card_name}`",
        f"- Brief del operador: `{operator_brief_name}`",
        f"- Run sheet: `{run_sheet_name}`",
        f"- Go/no-go final: `{final_go_no_go_name}`",
        f"- Recibo local: `{local_receipt_name}`",
        "",
        "## Politica de contenido",
        "",
        f"- Usa placeholders: `{_format_bool(policy['uses_placeholders'])}`",
        f"- Registra audio: `{_format_bool(policy['records_audio'])}`",
        f"- Registra transcripciones: `{_format_bool(policy['records_transcripts'])}`",
        f"- Registra texto hablado: `{_format_bool(policy['records_spoken_text'])}`",
        f"- Registra rutas locales: `{_format_bool(policy['records_local_paths'])}`",
        f"- Registra identidad del operador: `{_format_bool(policy['records_operator_identity'])}`",
        "",
        "## Orden recomendado",
        "",
    ]
    for step in report["recommended_pilot_sequence"]:
        lines.extend(
            [
                f"### {step['order']}. {step['name']}",
                "",
                f"- Titulo: {step['title']}",
                f"- Comando: `{step['command']}`",
                f"- Artifact esperado: `{step['artifact']}`",
                f"- Campos requeridos: {_format_inline_list(step['required_fields'])}",
                f"- Requiere hardware: `{_format_bool(step['requires_hardware'])}`",
                f"- Requiere operador: `{_format_bool(step['requires_operator'])}`",
                f"- Requiere audio no sensible: `{_format_bool(step['requires_non_sensitive_audio'])}`",
                f"- Revision requerida: `{_format_bool(step['review_required'])}`",
            ]
        )
        _append_conditional_required_field_lines(lines, step)
        _append_strict_backend_guard_lines(lines, step)
        lines.append("")
    lines.extend(
        [
            "## Auditoria",
            "",
            f"- Comando estricto: `{beta['strict_audit_command']}`",
            f"- Revisar manifiesto: `{evidence_manifest_name}`",
            f"- Revisar compuerta: `{decision_gate_name}`",
            "- Guardar solo artifacts JSON/Markdown sanitizados generados por las herramientas.",
            "- Ejecutar el refresco de `BETA_CHECKLIST.md` despues de auditar evidencias reales.",
            "- Crear tag/GitHub Release solo cuando el lote de 5 mejoras este listo o el usuario lo pida explicitamente.",
            "",
            "## Antes de ejecutar",
            "",
            f"- Revisar `{environment_checklist_name}` para confirmar Python, ffmpeg y backends opcionales disponibles.",
            f"- Revisar `{fixture_preflight_name}` para confirmar el fixture sintetico y el siguiente preflight con MP3 propio no sensible.",
            f"- Revisar `{transcription_readiness_name}` para confirmar backend objetivo, guard estricto, privacidad de audio/referencia y calidad.",
            f"- Revisar `{system_output_readiness_name}` para confirmar backend de salida, texto publico y operador presente.",
            f"- Revisar `{hard_stop_name}` antes de usar hardware, audio real, texto hablado real o flags `--confirm-*`.",
            f"- Revisar `{evidence_intake_name}` antes de mover artifacts reales al lote de auditoria.",
            f"- Revisar `{rehearsal_card_name}` para ensayar sin hardware antes de copiar el comando real.",
            f"- Revisar `{execution_card_name}` para ejecutar el foco actual en orden y cerrar con auditoria.",
            f"- Revisar `{consent_card_name}` antes de usar hardware, audio real o flags `--confirm-*`.",
            f"- Revisar `{audit_closure_name}` despues de generar el JSON real sanitizado.",
            f"- Revisar `{evidence_package_name}` para reunir solo JSON/Markdown sanitizados antes de auditar beta.",
            f"- Revisar `{operator_brief_name}` como resumen de una pagina antes de ejecutar localmente.",
            f"- Seguir `{run_sheet_name}` como hoja local por fases durante la corrida real.",
            f"- Revisar `{final_go_no_go_name}` como ultima decision local antes de tocar hardware.",
            f"- Completar `{local_receipt_name}` solo con placeholders y resultado sanitizado despues del intento real.",
            "- Reemplazar `sample.mp3`, `<audio-path>`, `<expected-text-path>` y `<public-spoken-text>` solo localmente.",
            "- Usar audio propio no sensible y texto hablado publico/no sensible.",
            "- Revisar `manual-capture-checklist.md`, `transcription-review-checklist.md`, `real-transcription-next-step.md`, `output-operator-checklist.md` y `system-output-next-step.md` segun el piloto.",
            "- No pegar audio, transcripciones completas, texto esperado completo, texto hablado real, rutas locales ni nombres reales de dispositivos en reportes publicos.",
            "",
        ]
    )
    return "\n".join(lines)


def _command_pack_required_fields(report: dict[str, Any], row: dict[str, Any]) -> list[str]:
    if row.get("required_fields"):
        return list(row["required_fields"])
    row_names = {row["name"]}
    blocker = row.get("blocker")
    if blocker:
        row_names.add(str(blocker))
        row_names.add(str(blocker).replace("_", "-"))
    for step in report["recommended_pilot_sequence"]:
        step_names = {step["name"], step["name"].replace("_", "-")}
        if row_names & step_names:
            return step["required_fields"]
    for step in report["next_beta_evidence_steps"]:
        step_names = {step["name"], step["name"].replace("_", "-")}
        if row_names & step_names:
            return step["required_fields"]
    return []


def _command_pack_conditional_required_fields(report: dict[str, Any], row: dict[str, Any]) -> list[dict[str, Any]]:
    if row.get("conditional_required_fields"):
        return list(row["conditional_required_fields"])
    row_names = {row["name"]}
    blocker = row.get("blocker")
    if blocker:
        row_names.add(str(blocker))
        row_names.add(str(blocker).replace("_", "-"))
    for step in report["recommended_pilot_sequence"]:
        step_names = {step["name"], step["name"].replace("_", "-")}
        if row_names & step_names:
            return list(step.get("conditional_required_fields", []))
    for step in report["next_beta_evidence_steps"]:
        step_names = {step["name"], step["name"].replace("_", "-")}
        if row_names & step_names:
            return list(step.get("conditional_required_fields", []))
    return []


def _format_inline_list(values: list[str]) -> str:
    if not values:
        return "`ninguno`"
    return ", ".join(f"`{value}`" for value in values)


def _format_conditional_required_fields_inline(conditional_fields: list[dict[str, Any]]) -> str:
    if not conditional_fields:
        return "`ninguno`"
    parts = []
    for item in conditional_fields:
        condition = item["when"]
        parts.append(
            f"si `{condition['path']}` = `{condition['expected']}`: "
            f"{_format_inline_list(item['fields'])}"
        )
    return "; ".join(parts)


def _format_bool(value: bool) -> str:
    return str(value).lower()


def _append_blocker_summary_lines(lines: list[str], summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        lines.extend(["- No hay resumen de blockers disponible.", ""])
        return
    for summary in summaries:
        accepted_sources = _format_inline_list(summary.get("accepted_sources", []))
        closest = summary.get("closest_candidate")
        lines.extend(
            [
                f"### {summary['name']}",
                "",
                f"- Estado: `{summary['status']}`",
                f"- Artifact esperado: `{summary['artifact']}`",
                f"- Fuentes que cierran: {accepted_sources}",
                f"- Candidatos evaluados: `{summary['candidate_count']}`",
            ]
        )
        if closest is None:
            lines.append("- Candidato mas cercano: `ninguno`")
        else:
            missing_fields = _format_inline_list(closest.get("missing_fields", []))
            lines.append(f"- Candidato mas cercano: `{closest['file']}`")
            lines.append(f"- Campos faltantes del candidato mas cercano: {missing_fields}")
        lines.append("")


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
    missing_fields = _format_inline_list(focus.get("missing_fields", []))
    required_fields = _format_inline_list(focus.get("required_fields", []))
    policy_required_fields = _format_inline_list(focus.get("policy_required_fields", []))
    lines.extend(
        [
            f"- Blocker: `{focus['name']}`",
            f"- Titulo: {focus['title']}",
            f"- Artifact esperado: `{focus['artifact']}`",
            f"- Comando base: `{focus['command']}`",
            f"- Candidatos evaluados: `{focus['candidate_count']}`",
            f"- Campos faltantes a cerrar: {missing_fields}",
            f"- Campos requeridos base: {required_fields}",
            f"- Campos de politica backend: {policy_required_fields}",
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
            lines.append(
                f"  - Si `{condition['path']}` = `{condition['expected']}`: "
                f"{_format_inline_list(item['fields'])}"
            )
    lines.append(f"- Motivo: {focus['reason_es']} / {focus['reason_en']}.")
    lines.append("")


def _append_privacy_audit_lines(lines: list[str], privacy_audit: dict[str, Any]) -> None:
    if not privacy_audit:
        lines.extend(["- Auditoria de privacidad no disponible.", ""])
        return
    lines.extend(
        [
            f"- Estado: `{privacy_audit.get('status', 'unknown')}`",
            f"- Hallazgos: `{privacy_audit.get('finding_count', 0)}`",
            f"- Bloquea beta: `{_format_bool(bool(privacy_audit.get('blocking', False)))}`",
        ]
    )
    findings = privacy_audit.get("findings", [])
    if not findings:
        lines.append("- No se detectaron campos crudos sospechosos.")
        lines.append("")
        return
    for finding in findings:
        lines.append(
            f"- `{finding['file']}` campo `{finding['field']}`: `{finding['reason']}`. "
            f"Accion: {finding.get('action_es', 'Revisar y redactar el campo localmente.')}"
        )
    lines.append("")


def _append_privacy_remediation_plan_lines(lines: list[str], plan: dict[str, Any]) -> None:
    if not plan:
        lines.extend(["- Plan de remediacion no disponible.", ""])
        return
    lines.extend(
        [
            f"- Estado: `{plan.get('status', 'unknown')}`",
            f"- Pasos: `{plan.get('step_count', 0)}`",
            f"- Seguro para compartir: `{_format_bool(bool(plan.get('safe_to_share', False)))}`",
            f"- Registra valores privados: `{_format_bool(bool(plan.get('records_private_values', True)))}`",
            f"- Siguiente accion: {plan.get('next_action_es', 'Revisar la auditoria localmente.')}",
        ]
    )
    steps = plan.get("steps", [])
    if not steps:
        lines.append("- No hay pasos de remediacion pendientes.")
        lines.append("")
        return
    for step in steps:
        lines.append(
            f"- {step['order']}. `{step['file']}` campo `{step['field']}`: "
            f"{step['action_es']} Reemplazo seguro: `{step['safe_replacement']}`."
        )
    lines.append("")


def _append_focus_preparation_sequence_lines(lines: list[str], steps: list[dict[str, Any]]) -> None:
    if not steps:
        lines.extend(["- No hay secuencia de preparacion pendiente.", ""])
        return
    for step in steps:
        lines.extend(
            [
                f"### {step['order']}. {step['name']}",
                "",
                f"- Titulo: {step['title']}",
                f"- Comando: `{step['command']}`",
                f"- Artifact esperado: `{step['artifact']}`",
                f"- Campos requeridos: {_format_inline_list(step.get('required_fields', []))}",
                f"- Campos de politica backend: {_format_inline_list(step.get('policy_required_fields', []))}",
                f"- Requiere hardware: `{_format_bool(step.get('requires_hardware', False))}`",
                f"- Requiere operador: `{_format_bool(step.get('requires_operator', False))}`",
                f"- Requiere audio no sensible: `{_format_bool(step.get('requires_non_sensitive_audio', False))}`",
                f"- Revision requerida: `{_format_bool(step.get('review_required', False))}`",
            ]
        )
        _append_conditional_required_field_lines(lines, step)
        _append_strict_backend_guard_lines(lines, step)
        lines.append("")


def _append_conditional_required_field_lines(lines: list[str], item: dict[str, Any]) -> None:
    conditional_fields = item.get("conditional_required_fields") or []
    if not conditional_fields:
        return
    lines.append("- Campos condicionales:")
    for conditional in conditional_fields:
        condition = conditional["when"]
        lines.append(
            f"  - Si `{condition['path']}` = `{condition['expected']}`: "
            f"{_format_inline_list(conditional['fields'])}"
        )


def _append_strict_backend_guard_lines(lines: list[str], item: dict[str, Any]) -> None:
    if not item.get("strict_backend_guard_required"):
        return
    lines.extend(
        [
            "- Guard backend estricto: `true`",
            f"- Flag de guard backend: `{item['strict_backend_guard_flag']}`",
            f"- Campo JSON del guard: `{item['strict_backend_guard_field']}`",
        ]
    )


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
