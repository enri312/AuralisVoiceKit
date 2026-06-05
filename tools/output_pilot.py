"""System output pilot runner for AuralisVoiceKit.

The default run is a dry-run and does not play audio. Pass --speak only when an
operator is present and ready to hear the operating system speech backend.
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


DEFAULT_TEXT = "Hola desde AuralisVoiceKit"


def run_output_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    text: str = DEFAULT_TEXT,
    voice: str | None = None,
    rate: int | None = None,
    volume: int | None = None,
    system: str | None = None,
    speak: bool = False,
    operator_present: bool = False,
    operator_confirmed_audio: bool = False,
    include_voices: bool = True,
) -> dict[str, Any]:
    """Run a safe system-output pilot and write shareable artifacts."""

    _validate_operator_flags(
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
    )
    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    system_name = system or platform.system()
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / "output" / _slug(timestamp)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    demo = _load_system_output_demo(workspace)
    payload = demo.run_demo(
        text,
        voice=voice,
        rate=rate,
        volume=volume,
        system=system_name,
        dry_run=not speak,
        include_voices=include_voices,
    )
    sanitized_payload = _sanitize_payload(payload, text)
    passed = bool(payload.get("spoken")) and payload.get("error") is None
    confirmation_status = _operator_confirmation_status(
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
    )

    findings_path = output / "output-pilot-findings.md"
    report_path = output / "output-pilot-report.json"
    findings = _build_findings_markdown(
        timestamp=timestamp,
        system=system_name,
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
        confirmation_status=confirmation_status,
        passed=passed,
        payload=sanitized_payload,
        report_path=report_path,
    )

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": system_name,
        "backend": "system",
        "dry_run": not speak,
        "real_audio_requested": speak,
        "hardware_output_tested": speak,
        "operator_present": operator_present,
        "operator_confirmed_audio": operator_confirmed_audio,
        "operator_confirmation_status": confirmation_status,
        "text_characters": len(text),
        "voice": voice,
        "rate": rate,
        "volume": volume,
        "passed": passed,
        "spoken": bool(payload.get("spoken")),
        "error": payload.get("error"),
        "voice_error": payload.get("voice_error"),
        "voices_count": len(payload.get("voices", [])),
        "commands_count": len(payload.get("commands", [])),
        "notes": _pilot_notes(speak),
        "output": sanitized_payload,
        "artifacts": {
            "pilot_findings": str(findings_path),
            "output_pilot_report": str(report_path),
        },
    }
    findings_path.write_text(findings, encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe system-output pilot.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output-dir", help="directory for pilot artifacts")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="text to speak or simulate")
    parser.add_argument("--voice", help="system voice selector when supported")
    parser.add_argument("--rate", type=int, help="system speech rate when supported")
    parser.add_argument("--volume", type=int, help="system speech volume when supported")
    parser.add_argument("--system", help="override platform name for dry-run command examples")
    parser.add_argument(
        "--speak",
        action="store_true",
        help="play audio with the real system backend; default is dry-run",
    )
    parser.add_argument(
        "--operator-present",
        action="store_true",
        help="confirm a human operator is present before using --speak",
    )
    parser.add_argument(
        "--confirm-audible",
        action="store_true",
        help="record that the operator confirmed audible output",
    )
    parser.add_argument("--no-voices", action="store_true", help="skip voice listing")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    try:
        report = run_output_pilot(
            root=args.root,
            output_dir=args.output_dir,
            text=args.text,
            voice=args.voice,
            rate=args.rate,
            volume=args.volume,
            system=args.system,
            speak=args.speak,
            operator_present=args.operator_present,
            operator_confirmed_audio=args.confirm_audible,
            include_voices=not args.no_voices,
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


def _load_system_output_demo(workspace: Path):
    module_path = workspace / "examples" / "system_output_demo.py"
    spec = importlib.util.spec_from_file_location("system_output_demo", module_path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sanitize_payload(payload: dict[str, Any], text: str) -> dict[str, Any]:
    sanitized = dict(payload)
    sanitized["commands"] = [
        {"argv": ["<text-redacted>" if str(item) == text else item for item in command.get("argv", [])]}
        for command in payload.get("commands", [])
    ]
    sanitized["text_characters"] = len(text)
    return sanitized


def _validate_operator_flags(
    *,
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
) -> None:
    if speak and not operator_present:
        raise ValueError("Real system output requires --operator-present with --speak.")
    if operator_present and not speak:
        raise ValueError("--operator-present is only valid with --speak.")
    if operator_confirmed_audio and not speak:
        raise ValueError("--confirm-audible is only valid with --speak.")
    if operator_confirmed_audio and not operator_present:
        raise ValueError("--confirm-audible requires --operator-present.")


def _operator_confirmation_status(
    *,
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
) -> str:
    if not speak:
        return "not-required"
    if operator_confirmed_audio:
        return "confirmed"
    if operator_present:
        return "operator-present"
    return "missing-operator"


def _build_findings_markdown(
    *,
    timestamp: str,
    system: str,
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
    confirmation_status: str,
    passed: bool,
    payload: dict[str, Any],
    report_path: Path,
) -> str:
    lines = [
        "# System output pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Backend: system",
        f"- Dry run: {not speak}",
        f"- Real audio requested: {speak}",
        f"- Operator present: {operator_present}",
        f"- Operator confirmed audio: {operator_confirmed_audio}",
        f"- Operator confirmation status: {confirmation_status}",
        f"- Passed: {passed}",
        f"- Voices reported: {len(payload.get('voices', []))}",
        f"- Commands observed: {len(payload.get('commands', []))}",
        f"- Report: {report_path.name}",
        "",
        "## Privacy",
        "",
        "- The full text is not written to this findings file.",
        "- Command arguments that match the requested text are written as <text-redacted>.",
        "",
        "## Result",
        "",
        f"- Spoken flag: {payload.get('spoken')}",
        f"- Error: {_format_optional(payload.get('error'))}",
        f"- Voice listing error: {_format_optional(payload.get('voice_error'))}",
        "",
        "## Follow-up",
        "",
    ]
    if speak:
        if operator_confirmed_audio:
            lines.append("- Record selected voice and volume quality in PILOT_FINDINGS.md if anything sounded wrong.")
        else:
            lines.append("- Confirm audibility, selected voice and volume with the operator who heard the pilot.")
    else:
        lines.append("- Re-run with --speak --operator-present only when a human is ready to hear real audio.")
    lines.append("- Record any platform-specific voice or command failures in PILOT_FINDINGS.md.")
    lines.append("")
    return "\n".join(lines)


def _pilot_notes(speak: bool) -> str:
    if speak:
        return "Real system speech output was requested explicitly for this pilot."
    return "System speech output was dry-run only; rerun with --speak to play audio."


def _format_optional(value: object | None) -> str:
    return "none" if value in (None, "") else str(value)


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit system output pilot")
    print(f"System: {report['system']}")
    print(f"Dry run: {report['dry_run']}")
    print(f"Real audio requested: {report['real_audio_requested']}")
    print(f"Operator present: {report['operator_present']}")
    print(f"Operator confirmation: {report['operator_confirmation_status']}")
    print(f"Passed: {report['passed']}")
    print(f"Voices: {report['voices_count']}")
    print(f"Commands: {report['commands_count']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
