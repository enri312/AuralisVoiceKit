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
from auralis_voicekit.backends import create_default_registry


REAL_CAPTURE_BACKENDS = {"sounddevice", "wasapi", "pyaudio"}
CROSS_PLATFORM_CAPTURE_BACKENDS = {"sounddevice", "pyaudio"}


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
    require_capture_backend_ready: bool = False,
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
    target_capture_backend = _capture_backend_status(backend, capture_readiness_plan)
    _validate_capture_backend_ready(
        target_capture_backend=target_capture_backend,
        required=require_capture_backend_ready,
    )
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
    beta_evidence_gap = _capture_beta_evidence_gap(
        system=system,
        evidence_system=readiness_system,
        backend=backend,
        system_guard=system_guard,
        target_capture_backend=target_capture_backend,
        require_capture_backend_ready=require_capture_backend_ready,
        capture_test=capture_test,
        input_review_confirmed=input_review_confirmed,
        passed=passed,
        capture_checklist=capture_checklist,
    )
    findings = _build_findings_markdown(
        timestamp=timestamp,
        system=system,
        system_guard=system_guard,
        backend=backend,
        target_capture_backend=target_capture_backend,
        require_capture_backend_ready=require_capture_backend_ready,
        capture_readiness_plan=capture_readiness_plan,
        capture_test=capture_test,
        input_review_confirmed=input_review_confirmed,
        sample_rate=sample_rate,
        doctor_status=doctor.status.value,
        passed=passed,
        capture_checklist=capture_checklist,
        beta_evidence_gap=beta_evidence_gap,
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
        target_capture_backend=target_capture_backend,
        require_capture_backend_ready=require_capture_backend_ready,
        capture_readiness_plan=capture_readiness_plan,
        capture_checklist=capture_checklist,
        beta_evidence_gap=beta_evidence_gap,
    )
    checklist_path.write_text(checklist, encoding="utf-8")

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": system,
        "system_guard": system_guard,
        "capture_backend": backend,
        "target_capture_backend": target_capture_backend,
        "capture_backend_ready_required": require_capture_backend_ready,
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
        "beta_evidence_gap": beta_evidence_gap,
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
    parser.add_argument(
        "--require-capture-backend-ready",
        action="store_true",
        help="fail before microphone access when the selected capture backend is unavailable",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)
    if args.confirm_input_reviewed and not args.capture_test:
        parser.error("--confirm-input-reviewed requires --capture-test")

    try:
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
            require_capture_backend_ready=args.require_capture_backend_ready,
        )
    except ValueError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1
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
        f"--device default --expected-system {system_arg} --confirm-input-reviewed "
        "--require-capture-backend-ready --json"
    )
    if normalized_backend == "wasapi":
        real_capture_command = (
            f"python tools/manual_pilot.py --capture-test --backend wasapi "
            f"--device default --sample-rate 48000 --expected-system {system_arg} "
            "--confirm-input-reviewed --require-capture-backend-ready --json"
        )

    return {
        "backend": normalized_backend,
        "system": system,
        "pip_command": pip_command,
        "setup_commands": setup_commands,
        "requires_package_manager": bool(setup_commands),
        "post_install_check": (
            f"python tools/manual_pilot.py --backend {normalized_backend} "
            f"--target-system {system_arg} --require-capture-backend-ready --json"
        ),
        "post_install_check_uses_microphone": False,
        "real_capture_check_template": real_capture_command,
        "real_capture_check_requires_microphone": True,
        "platform_notes": platform_notes,
        "dependency_notes": dependency_notes,
    }


def _capture_backend_status(backend: str, readiness_plan: dict[str, Any]) -> dict[str, Any]:
    registry = create_default_registry()
    infos = registry.backend_info()
    info = next(
        (candidate for candidate in infos if candidate.kind == "capture" and candidate.name == backend),
        None,
    )
    if info is not None:
        return {
            "name": info.name,
            "kind": info.kind,
            "available": info.available,
            "dependencies": list(info.dependencies),
            "reason": info.reason,
            "readiness_plan": readiness_plan,
        }

    capture_backends = sorted(candidate.name for candidate in infos if candidate.kind == "capture")
    available = ", ".join(capture_backends) or "none"
    return {
        "name": backend,
        "kind": "capture",
        "available": False,
        "dependencies": [],
        "reason": f"Unknown capture backend {backend!r}. Available: {available}.",
        "readiness_plan": readiness_plan,
    }


def _validate_capture_backend_ready(*, target_capture_backend: dict[str, Any], required: bool) -> None:
    if not required or target_capture_backend["available"]:
        return
    dependencies = _format_list(target_capture_backend["dependencies"])
    reason = target_capture_backend["reason"] or "capture backend dependency check failed"
    readiness_plan = target_capture_backend.get("readiness_plan", {})
    pip_command = readiness_plan.get("pip_command")
    pip_hint = f" Install with: {pip_command}." if pip_command else ""
    setup_commands = readiness_plan.get("setup_commands", [])
    setup_hint = f" Setup commands: {_format_list(setup_commands)}." if setup_commands else ""
    post_install_check = readiness_plan.get("post_install_check")
    check_hint = f" Recheck with: {post_install_check}." if post_install_check else ""
    raise ValueError(
        f"Capture backend {target_capture_backend['name']!r} is not available. "
        f"Dependencies: {dependencies}. Reason: {reason}.{pip_hint}{setup_hint}{check_hint}"
    )


def _build_findings_markdown(
    *,
    timestamp: str,
    system: str,
    system_guard: dict[str, Any],
    backend: str,
    target_capture_backend: dict[str, Any],
    require_capture_backend_ready: bool,
    capture_readiness_plan: dict[str, Any],
    capture_test: bool,
    input_review_confirmed: bool,
    sample_rate: int | None,
    doctor_status: str,
    passed: bool,
    capture_checklist: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
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
        f"- Target capture backend available: {target_capture_backend['available']}",
        f"- Target capture backend dependencies: {_format_list(target_capture_backend['dependencies'])}",
        f"- Capture backend readiness required: {require_capture_backend_ready}",
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
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
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
            "## Beta Evidence Gap",
            "",
            f"- Blocker: `{beta_evidence_gap['blocker']}`",
            f"- Evidence target system: `{beta_evidence_gap['evidence_system']}`",
            f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
            f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
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


def _capture_beta_evidence_gap(
    *,
    system: str,
    evidence_system: str,
    backend: str,
    system_guard: dict[str, Any],
    target_capture_backend: dict[str, Any],
    require_capture_backend_ready: bool,
    capture_test: bool,
    input_review_confirmed: bool,
    passed: bool,
    capture_checklist: dict[str, Any],
) -> dict[str, Any]:
    """Summarize why this capture report does or does not close beta evidence."""

    blocker, expected_system, accepted_backends = _capture_beta_blocker_metadata(evidence_system)
    normalized_backend = backend.strip().lower()
    checks = [
        _beta_gap_check("project", "AuralisVoiceKit", "AuralisVoiceKit", True),
        _beta_gap_check(
            "system",
            expected_system,
            system,
            _system_matches_capture_blocker(system=system, blocker=blocker),
        ),
        _beta_gap_check(
            "system_guard.expected_system_matched",
            True,
            system_guard["expected_system_matched"],
            system_guard["expected_system_matched"] is True,
        ),
        _beta_gap_check(
            "capture_backend",
            " | ".join(accepted_backends),
            backend,
            normalized_backend in accepted_backends,
        ),
    ]
    if blocker in {"ubuntu_linux_capture", "macos_capture"}:
        checks.extend(
            [
                _beta_gap_check(
                    "target_capture_backend.available",
                    True,
                    target_capture_backend["available"],
                    target_capture_backend["available"] is True,
                ),
                _beta_gap_check(
                    "capture_backend_ready_required",
                    True,
                    require_capture_backend_ready,
                    require_capture_backend_ready,
                ),
            ]
        )
    checks.extend(
        [
            _beta_gap_check("hardware_capture_tested", True, capture_test, capture_test),
            _beta_gap_check("input_review_confirmed", True, input_review_confirmed, input_review_confirmed),
            _beta_gap_check(
                "capture_checklist.input_review_confirmed",
                True,
                capture_checklist["input_review_confirmed"],
                capture_checklist["input_review_confirmed"] is True,
            ),
            _beta_gap_check(
                "capture_checklist.ready_for_beta_evidence",
                True,
                capture_checklist["ready_for_beta_evidence"],
                capture_checklist["ready_for_beta_evidence"] is True,
            ),
            _beta_gap_check("passed", True, passed, passed),
        ]
    )
    missing_fields = [item["path"] for item in checks if item["ok"] is not True]
    return {
        "blocker": blocker,
        "evidence_system": evidence_system,
        "ready_for_beta_evidence": not missing_fields,
        "missing_count": len(missing_fields),
        "missing_fields": missing_fields,
        "checks": checks,
        "safe_to_share": True,
        "records_audio": False,
        "records_audio_bytes": False,
        "records_device_name": False,
        "records_local_paths": False,
        "next_action": _capture_beta_evidence_gap_next_action(
            missing_fields=missing_fields,
            blocker=blocker,
            accepted_backends=accepted_backends,
        ),
    }


def _capture_beta_blocker_metadata(evidence_system: str) -> tuple[str, str, list[str]]:
    normalized = evidence_system.strip().lower()
    if normalized in {"linux", "ubuntu", "ubuntu/linux"}:
        return "ubuntu_linux_capture", "Linux | Ubuntu/Linux | Ubuntu", sorted(CROSS_PLATFORM_CAPTURE_BACKENDS)
    if normalized in {"darwin", "mac", "macos"}:
        return "macos_capture", "Darwin | macOS | Mac", sorted(CROSS_PLATFORM_CAPTURE_BACKENDS)
    return "windows_wasapi_capture", "Windows", ["wasapi"]


def _system_matches_capture_blocker(*, system: str, blocker: str) -> bool:
    normalized = system.strip().lower()
    if blocker == "ubuntu_linux_capture":
        return normalized in {"linux", "ubuntu/linux", "ubuntu"}
    if blocker == "macos_capture":
        return normalized in {"darwin", "macos", "mac"}
    return normalized == "windows"


def _beta_gap_check(path: str, expected: object, actual: object, ok: bool) -> dict[str, Any]:
    return {
        "path": path,
        "expected": expected,
        "actual": actual,
        "ok": bool(ok),
    }


def _capture_beta_evidence_gap_next_action(
    *,
    missing_fields: list[str],
    blocker: str,
    accepted_backends: list[str],
) -> str:
    if not missing_fields:
        return "Audit this report with tools/beta_readiness.py --audit-evidence before closing beta."
    if "system" in missing_fields or any(field.startswith("system_guard.") for field in missing_fields):
        return "Rerun on the intended OS with --expected-system matching the actual platform."
    if "capture_backend" in missing_fields:
        backends = " or ".join(f"--backend {backend}" for backend in accepted_backends)
        return f"Rerun the capture pilot with {backends} for this platform."
    if "target_capture_backend.available" in missing_fields or "capture_backend_ready_required" in missing_fields:
        return "Follow the readiness plan, require the capture backend and rerun before opening the microphone."
    if "hardware_capture_tested" in missing_fields:
        return "Run the manual capture pilot with --capture-test only when a human is ready to open the microphone."
    if "input_review_confirmed" in missing_fields or "capture_checklist.input_review_confirmed" in missing_fields:
        return "Review microphone permissions, selected input and room privacy, then rerun with --confirm-input-reviewed."
    if blocker == "windows_wasapi_capture" and "capture_checklist.ready_for_beta_evidence" in missing_fields:
        return "Review the WASAPI sample rate, commonly --sample-rate 48000, then rerun the capture pilot."
    return "Complete the missing capture confirmations and rerun the beta evidence audit."


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
    target_capture_backend: dict[str, Any],
    require_capture_backend_ready: bool,
    capture_readiness_plan: dict[str, Any],
    capture_checklist: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
) -> str:
    lines = [
        "# Checklist de captura manual / Manual capture checklist",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Capture backend: {backend}",
        f"- Target capture backend available: {target_capture_backend['available']}",
        f"- Target capture backend dependencies: {_format_list(target_capture_backend['dependencies'])}",
        f"- Capture backend readiness required: {require_capture_backend_ready}",
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
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
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
            "## Beta Evidence Gap",
            "",
            f"- Blocker: `{beta_evidence_gap['blocker']}`",
            f"- Evidence target system: `{beta_evidence_gap['evidence_system']}`",
            f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
            f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
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
    target_capture_backend = report["target_capture_backend"]
    print(f"Target capture backend available: {target_capture_backend['available']}")
    print(f"Capture backend readiness required: {report['capture_backend_ready_required']}")
    readiness_plan = report["capture_readiness_plan"]
    print(f"Capture readiness target: {readiness_plan['system']}")
    print(f"Capture readiness pip: {readiness_plan['pip_command']}")
    print(f"Capture readiness post-install check: {readiness_plan['post_install_check']}")
    print(f"Capture test requested: {report['capture_test_requested']}")
    print(f"Input review confirmed: {report['input_review_confirmed']}")
    beta_evidence_gap = report["beta_evidence_gap"]
    print(f"Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}")
    print(f"Beta evidence gap missing count: {beta_evidence_gap['missing_count']}")
    print(f"Doctor status: {report['doctor_status']}")
    print(f"Passed: {report['passed']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
