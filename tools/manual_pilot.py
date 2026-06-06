"""Manual pilot runner for AuralisVoiceKit.

The default run does not open the microphone. Pass --capture-test explicitly
when a human is ready to test real microphone access.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from typing import Any

from auralis_voicekit import (
    DiagnosticStatus,
    analyze_doctor_bundles,
    run_doctor,
    write_doctor_bundle,
    write_doctor_bundle_analysis,
)


REAL_CAPTURE_BACKENDS = {"sounddevice", "wasapi", "pyaudio"}


def run_manual_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    capture_backend: str | None = None,
    capture_test: bool = False,
    input_review_confirmed: bool = False,
    capture_seconds: float = 0.25,
    capture_device: str | int | None = "default",
    sample_rate: int | None = None,
    expected_system: str | None = None,
    target_system: str | None = None,
) -> dict[str, Any]:
    """Run a manual-pilot diagnostic pass and write shareable artifacts."""

    if input_review_confirmed and not capture_test:
        raise ValueError("input_review_confirmed requires capture_test=True")

    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    system = platform.system()
    readiness_system = target_system or expected_system or system
    backend = capture_backend or _default_capture_backend(readiness_system)
    capture_readiness_plan = _capture_readiness_plan(system=readiness_system, backend=backend)
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / "manual" / _slug(timestamp)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    doctor = run_doctor(
        include_devices=True,
        capture_backend=backend,
        include_capture_test=capture_test,
        capture_test_seconds=capture_seconds,
        capture_device=capture_device,
        capture_sample_rate=sample_rate,
    )
    bundle_path = output / "doctor-bundle.json"
    analysis_path = output / "doctor-analysis.json"
    findings_path = output / "pilot-findings.md"
    checklist_path = output / "manual-capture-checklist.md"

    write_doctor_bundle(bundle_path, doctor)
    analysis = analyze_doctor_bundles([bundle_path])
    write_doctor_bundle_analysis(analysis_path, analysis)
    high_priority_issues = analysis.priority_counts.get("high", 0)
    public_device, device_redacted = _public_capture_device(capture_device)
    system_guard = _system_guard(expected_system, system)
    diagnostic_passed = doctor.status is not DiagnosticStatus.ERROR and high_priority_issues == 0
    passed = diagnostic_passed and system_guard["expected_system_matched"] is not False
    capture_checklist = _capture_checklist(
        system=system,
        backend=backend,
        capture_test=capture_test,
        sample_rate=sample_rate,
        passed=passed,
        hardware_capture_tested=capture_test,
        input_review_confirmed=input_review_confirmed,
        device_redacted=device_redacted,
        expected_system_matched=system_guard["expected_system_matched"],
    )
    findings = _build_findings_markdown(
        timestamp=timestamp,
        system=system,
        system_guard=system_guard,
        backend=backend,
        capture_readiness_plan=capture_readiness_plan,
        capture_test=capture_test,
        input_review_confirmed=input_review_confirmed,
        sample_rate=sample_rate,
        doctor_status=doctor.status.value,
        passed=passed,
        capture_checklist=capture_checklist,
        analysis=analysis.to_dict(),
        bundle_path=bundle_path,
        analysis_path=analysis_path,
        checklist_path=checklist_path,
    )
    findings_path.write_text(findings, encoding="utf-8")
    checklist = _build_capture_checklist_markdown(
        timestamp=timestamp,
        system=system,
        backend=backend,
        capture_readiness_plan=capture_readiness_plan,
        capture_checklist=capture_checklist,
    )
    checklist_path.write_text(checklist, encoding="utf-8")

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": system,
        "system_guard": system_guard,
        "capture_backend": backend,
        "capture_readiness_plan": capture_readiness_plan,
        "capture_test_requested": capture_test,
        "input_review_confirmed": input_review_confirmed,
        "capture_device": public_device,
        "capture_device_redacted": device_redacted,
        "sample_rate": sample_rate,
        "doctor_status": doctor.status.value,
        "diagnostic_passed": diagnostic_passed,
        "passed": passed,
        "hardware_capture_tested": capture_test,
        "capture_checklist": capture_checklist,
        "notes": _pilot_notes(capture_test),
        "analysis": analysis.to_dict(),
        "artifacts": {
            "doctor_bundle": str(bundle_path),
            "doctor_analysis": str(analysis_path),
            "pilot_findings": str(findings_path),
            "capture_checklist": str(checklist_path),
        },
    }
    report_path = output / "manual-pilot-report.json"
    report["artifacts"]["manual_pilot_report"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a manual-pilot diagnostic pass.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output-dir", help="directory for pilot artifacts")
    parser.add_argument("--backend", help="capture backend to diagnose; defaults to wasapi on Windows")
    parser.add_argument(
        "--capture-test",
        action="store_true",
        help="open the selected microphone backend briefly",
    )
    parser.add_argument(
        "--confirm-input-reviewed",
        action="store_true",
        help=(
            "confirm OS microphone permissions, selected input device and non-sensitive room were "
            "reviewed before real capture evidence"
        ),
    )
    parser.add_argument("--capture-seconds", type=float, default=0.25, help="duration for --capture-test")
    parser.add_argument("--device", default="default", help="input device selector for --capture-test")
    parser.add_argument(
        "--sample-rate",
        type=int,
        help="sample rate used by --capture-test, for example 48000 on many WASAPI devices",
    )
    parser.add_argument(
        "--expected-system",
        help="expected platform for this pilot, for example Windows, Linux or Darwin",
    )
    parser.add_argument(
        "--target-system",
        help=(
            "platform used only for capture readiness instructions, for example Linux or Darwin; "
            "does not override the actual doctor system"
        ),
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)
    if args.confirm_input_reviewed and not args.capture_test:
        parser.error("--confirm-input-reviewed requires --capture-test")

    report = run_manual_pilot(
        root=args.root,
        output_dir=args.output_dir,
        capture_backend=args.backend,
        capture_test=args.capture_test,
        input_review_confirmed=args.confirm_input_reviewed,
        capture_seconds=args.capture_seconds,
        capture_device=args.device,
        sample_rate=args.sample_rate,
        expected_system=args.expected_system,
        target_system=args.target_system,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0 if report["passed"] else 1


def _default_capture_backend(system: str) -> str:
    return "wasapi" if system.strip().lower() == "windows" else "sounddevice"


def _capture_readiness_plan(*, system: str, backend: str) -> dict[str, Any]:
    normalized_system = system.strip().lower()
    normalized_backend = backend.strip().lower()
    setup_commands: list[str] = []
    platform_notes: list[str] = []
    dependency_notes: list[str] = []

    if normalized_backend in {"sounddevice", "wasapi"}:
        pip_command = 'python -m pip install "auralisvoicekit[sounddevice]"'
        dependency_notes.append("Uses the optional sounddevice extra and PortAudio.")
    elif normalized_backend == "pyaudio":
        pip_command = 'python -m pip install "auralisvoicekit[pyaudio]"'
        dependency_notes.append("Uses the optional PyAudio extra and PortAudio.")
    else:
        pip_command = "python -m pip install auralisvoicekit"
        dependency_notes.append("No optional capture extra is required for this dry-run backend.")

    if normalized_system in {"linux", "ubuntu", "ubuntu/linux"}:
        if normalized_backend == "pyaudio":
            setup_commands = [
                "sudo apt-get update",
                "sudo apt-get install -y portaudio19-dev python3-dev",
            ]
        elif normalized_backend in {"sounddevice", "wasapi"}:
            setup_commands = [
                "sudo apt-get update",
                "sudo apt-get install -y libportaudio2",
            ]
        platform_notes = [
            "Ubuntu/Linux capture should use sounddevice or pyaudio for beta evidence.",
            "Review microphone permissions, input device and room privacy before --capture-test.",
        ]
    elif normalized_system in {"darwin", "mac", "macos"}:
        if normalized_backend in {"sounddevice", "pyaudio", "wasapi"}:
            setup_commands = ["brew install portaudio"]
        platform_notes = [
            "macOS capture should use sounddevice or pyaudio for beta evidence.",
            "Review System Settings microphone permissions before --capture-test.",
        ]
    elif normalized_system == "windows":
        platform_notes = [
            "Windows beta capture evidence should use wasapi plus --sample-rate, commonly 48000.",
            "Review Windows microphone privacy settings and selected input device before --capture-test.",
        ]
    else:
        platform_notes = ["Unsupported or unknown target system; verify capture dependencies manually."]

    if normalized_backend == "wasapi" and normalized_system != "windows":
        dependency_notes.append("wasapi is Windows-only; use sounddevice or pyaudio on Ubuntu/Linux and macOS.")

    system_arg = _quote_cli_argument(system)
    real_capture_command = (
        f"python tools/manual_pilot.py --capture-test --backend {normalized_backend} "
        f"--device default --expected-system {system_arg} --confirm-input-reviewed --json"
    )
    if normalized_backend == "wasapi":
        real_capture_command = (
            f"python tools/manual_pilot.py --capture-test --backend wasapi "
            f"--device default --sample-rate 48000 --expected-system {system_arg} "
            "--confirm-input-reviewed --json"
        )

    return {
        "backend": normalized_backend,
        "system": system,
        "pip_command": pip_command,
        "setup_commands": setup_commands,
        "requires_package_manager": bool(setup_commands),
        "post_install_check": (
            f"python tools/manual_pilot.py --backend {normalized_backend} "
            f"--target-system {system_arg} --json"
        ),
        "post_install_check_uses_microphone": False,
        "real_capture_check_template": real_capture_command,
        "real_capture_check_requires_microphone": True,
        "platform_notes": platform_notes,
        "dependency_notes": dependency_notes,
    }


def _build_findings_markdown(
    *,
    timestamp: str,
    system: str,
    system_guard: dict[str, Any],
    backend: str,
    capture_readiness_plan: dict[str, Any],
    capture_test: bool,
    input_review_confirmed: bool,
    sample_rate: int | None,
    doctor_status: str,
    passed: bool,
    capture_checklist: dict[str, Any],
    analysis: dict[str, Any],
    bundle_path: Path,
    analysis_path: Path,
    checklist_path: Path,
) -> str:
    lines = [
        "# Manual pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Expected system: {_format_nullable(system_guard['expected_system'])}",
        f"- Expected system matched: {_format_nullable(system_guard['expected_system_matched'])}",
        f"- Capture backend: {backend}",
        f"- Capture readiness target system: {capture_readiness_plan['system']}",
        f"- Capture readiness pip command: {capture_readiness_plan['pip_command']}",
        f"- Capture readiness setup commands: {_format_list(capture_readiness_plan['setup_commands'])}",
        f"- Capture readiness post-install check: {capture_readiness_plan['post_install_check']}",
        f"- Capture test requested: {capture_test}",
        f"- Input review confirmed: {input_review_confirmed}",
        f"- Sample rate: {_format_optional(sample_rate)}",
        f"- Doctor status: {doctor_status}",
        f"- Passed: {passed}",
        f"- Capture checklist ready for beta evidence: {capture_checklist['ready_for_beta_evidence']}",
        f"- Bundle: {bundle_path.name}",
        f"- Analysis: {analysis_path.name}",
        f"- Capture checklist: {checklist_path.name}",
        "",
        "## Privacy",
        "",
        "- The full device selector is redacted unless it is `default` or a numeric id.",
        "- No audio bytes are written to the JSON report or Markdown artifacts.",
        "",
        "## Summary",
        "",
        f"- Systems: {_format_counts(analysis.get('systems', {}))}",
        f"- Statuses: {_format_counts(analysis.get('statuses', {}))}",
        f"- Priorities: {_format_counts(analysis.get('priority_counts', {}))}",
        f"- Issue categories: {_format_counts(analysis.get('issue_categories', {}))}",
        "",
        "## Top issues",
        "",
    ]
    issues = analysis.get("issues", [])
    if not issues:
        lines.append("- No warning or error checks found.")
    for issue in issues[:10]:
        lines.append(
            f"- [{issue['priority']}/{issue['status']}] "
            f"{issue['category']} / {issue['check']}: {issue['message']}"
        )
    lines.extend(
        [
            "",
            "## Follow-up",
            "",
            "- Install optional extras before real microphone testing if dependency warnings block capture.",
            f"- Recheck capture readiness without opening the microphone: {capture_readiness_plan['post_install_check']}",
            "- Re-run with --capture-test only when a human is ready to open the microphone briefly.",
            "- Keep doctor bundle JSON sanitized; do not attach audio unless intentionally sharing that file.",
            "",
        ]
    )
    return "\n".join(lines)


def _capture_checklist(
    *,
    system: str,
    backend: str,
    capture_test: bool,
    sample_rate: int | None,
    passed: bool,
    hardware_capture_tested: bool,
    input_review_confirmed: bool,
    device_redacted: bool,
    expected_system_matched: bool | None,
) -> dict[str, Any]:
    real_capture_backend = backend in REAL_CAPTURE_BACKENDS
    needs_sample_rate_review = system == "Windows" and backend == "wasapi"
    before = [
        _checklist_item(
            "explicit_capture_test",
            "Use --capture-test only when a human is ready to open the microphone briefly.",
            ok=capture_test,
            required=True,
        ),
        _checklist_item(
            "real_backend_selected",
            "Use wasapi on Windows or sounddevice/pyaudio on Ubuntu/Linux and macOS for real capture evidence.",
            ok=real_capture_backend if capture_test else None,
            required=True,
        ),
        _checklist_item(
            "input_review_confirmed",
            (
                "Use --confirm-input-reviewed only after reviewing OS microphone permissions, "
                "selected input device and a non-sensitive room."
            ),
            ok=input_review_confirmed if capture_test else None,
            required=True,
        ),
        _checklist_item(
            "expected_system_matched",
            "Use --expected-system so Linux/macOS/Windows evidence cannot be collected on the wrong OS.",
            ok=expected_system_matched,
            required=True,
        ),
        _checklist_item(
            "sample_rate_reviewed",
            "Review --sample-rate for WASAPI devices; 48000 Hz is common on Windows.",
            ok=sample_rate is not None if needs_sample_rate_review and capture_test else None,
            required=needs_sample_rate_review,
        ),
    ]
    after = [
        _checklist_item(
            "hardware_capture_passed",
            "Confirm the doctor capture test passed with real hardware.",
            ok=passed if capture_test else None,
            required=True,
        ),
        _checklist_item(
            "doctor_bundle_written",
            "Keep the sanitized doctor bundle and analysis next to this report.",
            ok=True,
            required=True,
        ),
        _checklist_item(
            "audio_bytes_not_recorded",
            "Verify artifacts contain structured metadata only, not captured audio bytes.",
            ok=True,
            required=True,
        ),
        _checklist_item(
            "findings_public_safe",
            "Record OS, backend and high-level issues in PILOT_FINDINGS.md without private device names.",
            ok=None,
            required=True,
        ),
    ]
    sample_rate_ready = not needs_sample_rate_review or sample_rate is not None
    ready_for_real_capture = bool(capture_test and real_capture_backend and sample_rate_ready)
    ready_for_beta_evidence = bool(
        ready_for_real_capture
        and hardware_capture_tested
        and passed
        and expected_system_matched is True
        and input_review_confirmed
    )
    return {
        "system": system,
        "records_audio_bytes": False,
        "redacts_device_selector": device_redacted,
        "expected_system_matched": expected_system_matched,
        "input_review_confirmed": input_review_confirmed,
        "ready_for_real_capture": ready_for_real_capture,
        "ready_for_beta_evidence": ready_for_beta_evidence,
        "before_capture": before,
        "after_capture": after,
    }


def _checklist_item(
    item_id: str,
    instruction: str,
    *,
    ok: bool | None,
    required: bool,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "required": required,
        "ok": ok,
        "instruction": instruction,
    }


def _build_capture_checklist_markdown(
    *,
    timestamp: str,
    system: str,
    backend: str,
    capture_readiness_plan: dict[str, Any],
    capture_checklist: dict[str, Any],
) -> str:
    lines = [
        "# Checklist de captura manual / Manual capture checklist",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Capture backend: {backend}",
        f"- Readiness target system: {capture_readiness_plan['system']}",
        f"- Readiness pip command: `{capture_readiness_plan['pip_command']}`",
        f"- Readiness setup commands: {_format_list(capture_readiness_plan['setup_commands'])}",
        f"- Readiness post-install check: `{capture_readiness_plan['post_install_check']}`",
        f"- Readiness post-install uses microphone: {capture_readiness_plan['post_install_check_uses_microphone']}",
        f"- Real capture command template: `{capture_readiness_plan['real_capture_check_template']}`",
        f"- Records audio bytes: {capture_checklist['records_audio_bytes']}",
        f"- Redacts device selector: {capture_checklist['redacts_device_selector']}",
        f"- Expected system matched: {_format_nullable(capture_checklist['expected_system_matched'])}",
        f"- Input review confirmed: {capture_checklist['input_review_confirmed']}",
        f"- Ready for real capture: {capture_checklist['ready_for_real_capture']}",
        f"- Ready for beta evidence: {capture_checklist['ready_for_beta_evidence']}",
        "",
        "## Antes de capturar / Before Capture",
        "",
    ]
    for item in capture_checklist["before_capture"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## Despues de capturar / After Capture",
            "",
        ]
    )
    for item in capture_checklist["after_capture"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## Notas / Notes",
            "",
            "- No escribas nombres privados de dispositivos, rutas locales completas ni audio capturado en reportes compartidos.",
            "- The readiness post-install check does not open the microphone; beta evidence still requires a real --capture-test.",
            "- A dry run checklist is preparation only; beta evidence requires --capture-test on real hardware.",
            "",
        ]
    )
    return "\n".join(lines)


def _pilot_notes(capture_test: bool) -> str:
    if capture_test:
        return "Microphone capture was requested explicitly for this pilot."
    return "Microphone capture was not opened; rerun with --capture-test for a real hardware check."


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _format_optional(value: object | None) -> str:
    return "default" if value is None else str(value)


def _format_nullable(value: object | None) -> str:
    return "not-set" if value is None else str(value)


def _format_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(f"`{value}`" for value in values)


def _quote_cli_argument(value: str) -> str:
    if not value:
        return '""'
    if any(char.isspace() or char in '"&|<>' for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def _public_capture_device(value: str | int | None) -> tuple[str | int | None, bool]:
    if value is None or isinstance(value, int):
        return value, False
    normalized = str(value).strip()
    if normalized.lower() == "default" or normalized.isdigit():
        return normalized, False
    return "<device-redacted>", True


def _system_guard(expected_system: str | None, actual_system: str) -> dict[str, Any]:
    expected = expected_system.strip() if expected_system else None
    accepted_actual_systems = _accepted_actual_systems(expected)
    matched = None if expected is None else actual_system.lower() in accepted_actual_systems
    return {
        "enabled": expected is not None,
        "expected_system": expected,
        "actual_system": actual_system,
        "accepted_actual_systems": sorted(accepted_actual_systems),
        "expected_system_matched": matched,
    }


def _accepted_actual_systems(expected_system: str | None) -> set[str]:
    if expected_system is None:
        return set()
    aliases = {
        "windows": {"windows"},
        "linux": {"linux"},
        "ubuntu": {"linux"},
        "ubuntu/linux": {"linux"},
        "darwin": {"darwin"},
        "mac": {"darwin"},
        "macos": {"darwin"},
    }
    accepted = set()
    for part in expected_system.split("|"):
        normalized = part.strip().lower()
        if not normalized:
            continue
        accepted.update(aliases.get(normalized, {normalized}))
    return accepted


def _format_checklist_item(item: dict[str, Any]) -> str:
    marker = "x" if item["ok"] is True else " "
    state = "unknown" if item["ok"] is None else str(item["ok"]).lower()
    return f"- [{marker}] `{item['id']}` ok={state} required={item['required']} - {item['instruction']}"


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit manual pilot")
    print(f"System: {report['system']}")
    print(f"Capture backend: {report['capture_backend']}")
    readiness_plan = report["capture_readiness_plan"]
    print(f"Capture readiness target: {readiness_plan['system']}")
    print(f"Capture readiness pip: {readiness_plan['pip_command']}")
    print(f"Capture readiness post-install check: {readiness_plan['post_install_check']}")
    print(f"Capture test requested: {report['capture_test_requested']}")
    print(f"Input review confirmed: {report['input_review_confirmed']}")
    print(f"Doctor status: {report['doctor_status']}")
    print(f"Passed: {report['passed']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
