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


def run_manual_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    capture_backend: str | None = None,
    capture_test: bool = False,
    capture_seconds: float = 0.25,
    capture_device: str | int | None = "default",
) -> dict[str, Any]:
    """Run a manual-pilot diagnostic pass and write shareable artifacts."""

    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    system = platform.system()
    backend = capture_backend or _default_capture_backend(system)
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / "manual" / _slug(timestamp)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    doctor = run_doctor(
        include_devices=True,
        capture_backend=backend,
        include_capture_test=capture_test,
        capture_test_seconds=capture_seconds,
        capture_device=capture_device,
    )
    bundle_path = output / "doctor-bundle.json"
    analysis_path = output / "doctor-analysis.json"
    findings_path = output / "pilot-findings.md"

    write_doctor_bundle(bundle_path, doctor)
    analysis = analyze_doctor_bundles([bundle_path])
    write_doctor_bundle_analysis(analysis_path, analysis)
    findings = _build_findings_markdown(
        timestamp=timestamp,
        system=system,
        backend=backend,
        capture_test=capture_test,
        doctor_status=doctor.status.value,
        analysis=analysis.to_dict(),
        bundle_path=bundle_path,
        analysis_path=analysis_path,
    )
    findings_path.write_text(findings, encoding="utf-8")

    high_priority_issues = analysis.priority_counts.get("high", 0)
    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": system,
        "capture_backend": backend,
        "capture_test_requested": capture_test,
        "capture_device": capture_device,
        "doctor_status": doctor.status.value,
        "passed": doctor.status is not DiagnosticStatus.ERROR and high_priority_issues == 0,
        "hardware_capture_tested": capture_test,
        "notes": _pilot_notes(capture_test),
        "analysis": analysis.to_dict(),
        "artifacts": {
            "doctor_bundle": str(bundle_path),
            "doctor_analysis": str(analysis_path),
            "pilot_findings": str(findings_path),
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
    parser.add_argument("--capture-seconds", type=float, default=0.25, help="duration for --capture-test")
    parser.add_argument("--device", default="default", help="input device selector for --capture-test")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    report = run_manual_pilot(
        root=args.root,
        output_dir=args.output_dir,
        capture_backend=args.backend,
        capture_test=args.capture_test,
        capture_seconds=args.capture_seconds,
        capture_device=args.device,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0 if report["passed"] else 1


def _default_capture_backend(system: str) -> str:
    return "wasapi" if system == "Windows" else "sounddevice"


def _build_findings_markdown(
    *,
    timestamp: str,
    system: str,
    backend: str,
    capture_test: bool,
    doctor_status: str,
    analysis: dict[str, Any],
    bundle_path: Path,
    analysis_path: Path,
) -> str:
    lines = [
        "# Manual pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Capture backend: {backend}",
        f"- Capture test requested: {capture_test}",
        f"- Doctor status: {doctor_status}",
        f"- Bundle: {bundle_path.name}",
        f"- Analysis: {analysis_path.name}",
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
            "- Re-run with --capture-test only when a human is ready to open the microphone briefly.",
            "- Keep doctor bundle JSON sanitized; do not attach audio unless intentionally sharing that file.",
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


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit manual pilot")
    print(f"System: {report['system']}")
    print(f"Capture backend: {report['capture_backend']}")
    print(f"Capture test requested: {report['capture_test_requested']}")
    print(f"Doctor status: {report['doctor_status']}")
    print(f"Passed: {report['passed']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
