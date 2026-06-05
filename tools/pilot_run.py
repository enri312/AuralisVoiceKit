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
            "missing_json_blockers": beta_audit["missing_blockers"],
            "strict_audit_command": (
                "python tools/beta_readiness.py --audit-evidence "
                "--evidence pilot_runs/manual --evidence pilot_runs/output "
                "--evidence pilot_runs/transcription --fail-on-audit-gaps --json"
            ),
        },
        "steps": steps,
        "manual_pilot_steps": manual_pilot_steps,
        "next_beta_evidence_steps": next_beta_evidence_steps,
        "artifacts": artifacts,
    }
    report_path = output / "pilot-report.json"
    artifacts["pilot_report"] = str(report_path)
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
            "name": "microphone-capture",
            "command": "python tools/manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --json",
            "reason": "Requires real microphone hardware and OS permissions.",
        },
        {
            "name": "system-speech",
            "command": (
                "python tools/output_pilot.py --speak --operator-present --confirm-audible "
                "--text \"Hola desde AuralisVoiceKit\" --json"
            ),
            "reason": "Plays real audio and should be run intentionally by a human.",
        },
        {
            "name": "real-transcription",
            "command": "python tools/transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --expected-text \"Hola desde AuralisVoiceKit\" --min-word-accuracy 0.75 --json",
            "reason": "Uses a real non-sensitive audio file and may download or run a local model.",
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
                "reason": "Required real pilot evidence before public beta.",
            }
        )
    return steps


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
    print("Manual pilot steps:")
    for step in report["manual_pilot_steps"]:
        print(f"- {step['name']}: {step['command']}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
