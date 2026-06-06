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
import re
import sys
from typing import Any

from auralis_voicekit.backends import SystemSpeechOutputBackend


DEFAULT_TEXT = "Hola desde AuralisVoiceKit"
SPOKEN_TEXT_PRIVACY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("url", re.compile(r"\b(?:https?://|www\.)\S+\b", re.IGNORECASE)),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    (
        "credential_keyword",
        re.compile(r"\b(?:api[_-]?key|bearer|password|passwd|secret|token)\b\s*[:=]", re.IGNORECASE),
    ),
    (
        "secret_token",
        re.compile(r"\b(?:sk|pk|rk|ghp|gho|ghu|github_pat|hf)[_-][A-Za-z0-9_-]{12,}\b"),
    ),
    ("long_number", re.compile(r"\b\d{8,}\b")),
    ("phone_like_number", re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")),
)


def run_output_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    text: str = DEFAULT_TEXT,
    voice: str | None = None,
    rate: int | None = None,
    volume: int | None = None,
    system: str | None = None,
    expected_system: str | None = None,
    speak: bool = False,
    operator_present: bool = False,
    operator_confirmed_audio: bool = False,
    text_review_confirmed: bool = False,
    voice_review_confirmed: bool = False,
    require_output_backend_ready: bool = False,
    include_voices: bool = True,
) -> dict[str, Any]:
    """Run a safe system-output pilot and write shareable artifacts."""

    _validate_operator_flags(
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
        text_review_confirmed=text_review_confirmed,
        voice_review_confirmed=voice_review_confirmed,
    )
    _validate_system_flags(system_override=system, speak=speak)
    spoken_text_privacy_scan = _spoken_text_privacy_scan(text)
    if speak and spoken_text_privacy_scan["passed"] is False:
        raise ValueError("Real system output text privacy scan failed; use public non-sensitive text.")
    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    actual_system = platform.system()
    system_name = system or actual_system
    target_output_backend = _output_backend_status(system_name)
    _validate_output_backend_ready(
        target_output_backend=target_output_backend,
        required=require_output_backend_ready,
    )
    system_guard = _system_guard(expected_system, actual_system)
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
    passed = passed and system_guard["expected_system_matched"] is not False
    if spoken_text_privacy_scan["passed"] is False:
        passed = False
    confirmation_status = _operator_confirmation_status(
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
    )
    operator_checklist = _operator_checklist(
        system=system_name,
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
        text_review_confirmed=text_review_confirmed,
        voice_review_confirmed=voice_review_confirmed,
        voice=voice,
        rate=rate,
        volume=volume,
        expected_system_matched=system_guard["expected_system_matched"],
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        payload=sanitized_payload,
    )

    findings_path = output / "output-pilot-findings.md"
    checklist_path = output / "output-operator-checklist.md"
    next_step_path = output / "system-output-next-step.md"
    report_path = output / "output-pilot-report.json"
    command_template = _system_output_command_template(
        expected_system=expected_system,
    )
    findings = _build_findings_markdown(
        timestamp=timestamp,
        system=system_name,
        system_guard=system_guard,
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
        text_review_confirmed=text_review_confirmed,
        voice_review_confirmed=voice_review_confirmed,
        target_output_backend=target_output_backend,
        confirmation_status=confirmation_status,
        passed=passed,
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        payload=sanitized_payload,
        operator_checklist=operator_checklist,
        report_path=report_path,
        checklist_path=checklist_path,
        next_step_path=next_step_path,
    )
    checklist = _build_operator_checklist_markdown(
        timestamp=timestamp,
        system=system_name,
        operator_checklist=operator_checklist,
    )
    next_step = _build_system_output_next_step_markdown(
        timestamp=timestamp,
        system=system_name,
        system_guard=system_guard,
        speak=speak,
        operator_present=operator_present,
        operator_confirmed_audio=operator_confirmed_audio,
        text_review_confirmed=text_review_confirmed,
        voice_review_confirmed=voice_review_confirmed,
        require_output_backend_ready=require_output_backend_ready,
        target_output_backend=target_output_backend,
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        operator_checklist=operator_checklist,
        command_template=command_template,
        checklist_path=checklist_path,
    )

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": system_name,
        "system_guard": system_guard,
        "backend": "system",
        "target_output_backend": target_output_backend,
        "output_backend_ready_required": require_output_backend_ready,
        "dry_run": not speak,
        "real_audio_requested": speak,
        "hardware_output_tested": speak,
        "operator_present": operator_present,
        "operator_confirmed_audio": operator_confirmed_audio,
        "text_review_confirmed": text_review_confirmed,
        "voice_review_confirmed": voice_review_confirmed,
        "operator_confirmation_status": confirmation_status,
        "spoken_text_privacy_scan": spoken_text_privacy_scan,
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
        "operator_checklist": operator_checklist,
        "next_system_output": {
            "artifact": str(next_step_path),
            "command_template": command_template,
            "target_output_backend": target_output_backend,
            "uses_placeholders": True,
            "records_spoken_text": False,
            "records_operator_identity": False,
            "requires_operator": True,
        },
        "output": sanitized_payload,
        "artifacts": {
            "operator_checklist": str(checklist_path),
            "system_output_next_step": str(next_step_path),
            "pilot_findings": str(findings_path),
            "output_pilot_report": str(report_path),
        },
    }
    findings_path.write_text(findings, encoding="utf-8")
    checklist_path.write_text(checklist, encoding="utf-8")
    next_step_path.write_text(next_step, encoding="utf-8")
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
        "--expected-system",
        help="expected real platform for this pilot, for example Windows, Linux, Darwin or Windows|Linux|Darwin",
    )
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
    parser.add_argument(
        "--confirm-text-reviewed",
        action="store_true",
        help="record that the spoken text was reviewed for privacy before playback",
    )
    parser.add_argument(
        "--confirm-voice-reviewed",
        action="store_true",
        help="record that the operator reviewed voice, volume and pronunciation quality",
    )
    parser.add_argument(
        "--require-output-backend-ready",
        action="store_true",
        help="fail before playback when the selected system output command is unavailable",
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
            expected_system=args.expected_system,
            speak=args.speak,
            operator_present=args.operator_present,
            operator_confirmed_audio=args.confirm_audible,
            text_review_confirmed=args.confirm_text_reviewed,
            voice_review_confirmed=args.confirm_voice_reviewed,
            require_output_backend_ready=args.require_output_backend_ready,
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


def _spoken_text_privacy_scan(text: str) -> dict[str, Any]:
    risk_types: list[str] = []
    risk_count = 0
    for risk_type, pattern in SPOKEN_TEXT_PRIVACY_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            risk_types.append(risk_type)
            risk_count += len(matches)

    passed = risk_count == 0
    return {
        "enabled": True,
        "passed": passed,
        "status": "passed" if passed else "blocked",
        "text_redacted": True,
        "risk_count": risk_count,
        "risk_types": risk_types,
    }


def _validate_operator_flags(
    *,
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
    text_review_confirmed: bool,
    voice_review_confirmed: bool,
) -> None:
    if speak and not operator_present:
        raise ValueError("Real system output requires --operator-present with --speak.")
    if speak and not text_review_confirmed:
        raise ValueError("Real system output requires --confirm-text-reviewed with --speak.")
    if operator_present and not speak:
        raise ValueError("--operator-present is only valid with --speak.")
    if operator_confirmed_audio and not speak:
        raise ValueError("--confirm-audible is only valid with --speak.")
    if text_review_confirmed and not speak:
        raise ValueError("--confirm-text-reviewed is only valid with --speak.")
    if operator_confirmed_audio and not operator_present:
        raise ValueError("--confirm-audible requires --operator-present.")
    if voice_review_confirmed and not speak:
        raise ValueError("--confirm-voice-reviewed is only valid with --speak.")
    if voice_review_confirmed and not operator_confirmed_audio:
        raise ValueError("--confirm-voice-reviewed requires --confirm-audible.")


def _validate_system_flags(*, system_override: str | None, speak: bool) -> None:
    if speak and system_override:
        raise ValueError("--system is only valid for dry-run command examples, not with --speak.")


def _output_backend_status(system: str) -> dict[str, Any]:
    info = SystemSpeechOutputBackend(system=system).info()
    return {
        "name": info.name,
        "kind": info.kind,
        "available": info.available,
        "dependencies": list(info.dependencies),
        "reason": info.reason,
    }


def _validate_output_backend_ready(*, target_output_backend: dict[str, Any], required: bool) -> None:
    if not required or target_output_backend["available"]:
        return
    dependencies = _format_list(target_output_backend["dependencies"])
    reason = target_output_backend["reason"] or "backend dependency check failed"
    raise ValueError(
        f"System output backend {target_output_backend['name']!r} is not available. "
        f"Dependencies: {dependencies}. Reason: {reason}"
    )


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


def _operator_checklist(
    *,
    system: str,
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
    text_review_confirmed: bool,
    voice_review_confirmed: bool,
    voice: str | None,
    rate: int | None,
    volume: int | None,
    expected_system_matched: bool | None,
    spoken_text_privacy_scan: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    before = [
        _checklist_item(
            "operator_present",
            "Confirm a human operator is present before enabling --speak.",
            ok=operator_present if speak else None,
            required=True,
        ),
        _checklist_item(
            "safe_volume",
            "Set OS volume to a comfortable level and avoid headphones at high volume.",
            ok=None,
            required=True,
        ),
        _checklist_item(
            "quiet_environment",
            "Run the audible pilot in a place where private conversations will not be captured in notes.",
            ok=None,
            required=True,
        ),
        _checklist_item(
            "voice_selected",
            "Review the selected voice/rate/volume before playback.",
            ok=voice is not None or rate is not None or volume is not None,
            required=False,
        ),
        _checklist_item(
            "expected_system_matched",
            "Use --expected-system so output evidence is collected only on the intended OS family.",
            ok=expected_system_matched,
            required=True,
        ),
        _checklist_item(
            "text_review_confirmed",
            "Use --confirm-text-reviewed only after reviewing spoken text privacy locally.",
            ok=text_review_confirmed if speak else None,
            required=True,
        ),
        _checklist_item(
            "spoken_text_privacy_scan_passed",
            "Use only public/non-sensitive spoken text; review risk types locally if this scan blocks playback.",
            ok=spoken_text_privacy_scan["passed"],
            required=True,
        ),
    ]
    after = [
        _checklist_item(
            "audible_confirmed",
            "Use --confirm-audible only after the operator confirms hearing the output.",
            ok=operator_confirmed_audio if speak else None,
            required=True,
        ),
        _checklist_item(
            "voice_quality_reviewed",
            "Use --confirm-voice-reviewed only after reviewing voice, volume and pronunciation quality.",
            ok=voice_review_confirmed if speak else None,
            required=True,
        ),
    ]
    commands_available = len(payload.get("commands", [])) > 0 or bool(
        speak and payload.get("spoken") and payload.get("error") is None
    )
    return {
        "system": system,
        "records_operator_identity": False,
        "redacts_spoken_text": True,
        "text_review_confirmed": text_review_confirmed,
        "spoken_text_privacy_scan_passed": spoken_text_privacy_scan["passed"],
        "spoken_text_privacy_risk_count": spoken_text_privacy_scan["risk_count"],
        "spoken_text_privacy_risk_types": spoken_text_privacy_scan["risk_types"],
        "voice_review_confirmed": voice_review_confirmed,
        "expected_system_matched": expected_system_matched,
        "commands_available": commands_available,
        "ready_for_real_audio": bool(speak and operator_present and commands_available),
        "ready_for_beta_evidence": bool(
            speak
            and operator_present
            and operator_confirmed_audio
            and text_review_confirmed
            and spoken_text_privacy_scan["passed"] is True
            and voice_review_confirmed
            and commands_available
            and expected_system_matched is True
        ),
        "before_playback": before,
        "after_playback": after,
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


def _build_findings_markdown(
    *,
    timestamp: str,
    system: str,
    system_guard: dict[str, Any],
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
    text_review_confirmed: bool,
    voice_review_confirmed: bool,
    target_output_backend: dict[str, Any],
    confirmation_status: str,
    passed: bool,
    spoken_text_privacy_scan: dict[str, Any],
    payload: dict[str, Any],
    operator_checklist: dict[str, Any],
    report_path: Path,
    checklist_path: Path,
    next_step_path: Path,
) -> str:
    lines = [
        "# System output pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Expected system: {_format_nullable(system_guard['expected_system'])}",
        f"- Expected system matched: {_format_nullable(system_guard['expected_system_matched'])}",
        f"- Backend: system",
        f"- Target output backend available: {target_output_backend['available']}",
        f"- Target output backend dependencies: {_format_list(target_output_backend['dependencies'])}",
        f"- Target output backend reason: {_format_optional(target_output_backend['reason'])}",
        f"- Dry run: {not speak}",
        f"- Real audio requested: {speak}",
        f"- Operator present: {operator_present}",
        f"- Operator confirmed audio: {operator_confirmed_audio}",
        f"- Text review confirmed: {text_review_confirmed}",
        f"- Spoken text privacy scan passed: {_format_nullable(spoken_text_privacy_scan['passed'])}",
        f"- Spoken text privacy risk count: {spoken_text_privacy_scan['risk_count']}",
        f"- Spoken text privacy risk types: {_format_list(spoken_text_privacy_scan['risk_types'])}",
        f"- Voice review confirmed: {voice_review_confirmed}",
        f"- Operator confirmation status: {confirmation_status}",
        f"- Passed: {passed}",
        f"- Voices reported: {len(payload.get('voices', []))}",
        f"- Commands observed: {len(payload.get('commands', []))}",
        f"- Operator checklist ready for beta evidence: {operator_checklist['ready_for_beta_evidence']}",
        f"- Report: {report_path.name}",
        f"- Operator checklist: {checklist_path.name}",
        f"- System output next step: {next_step_path.name}",
        "",
        "## Privacy",
        "",
        "- The full text is not written to this findings file.",
        "- Command arguments that match the requested text are written as <text-redacted>.",
        "- Spoken text privacy scanning reports only risk types and counts, not matched text.",
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


def _system_output_command_template(*, expected_system: str | None) -> str:
    expected = expected_system or "Windows|Linux|Darwin"
    return (
        "python tools/output_pilot.py --speak --operator-present --confirm-audible "
        "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
        f"--expected-system \"{expected}\" --output-dir pilot_runs/output/system-real "
        "--text <public-spoken-text> --json"
    )


def _build_system_output_next_step_markdown(
    *,
    timestamp: str,
    system: str,
    system_guard: dict[str, Any],
    speak: bool,
    operator_present: bool,
    operator_confirmed_audio: bool,
    text_review_confirmed: bool,
    voice_review_confirmed: bool,
    require_output_backend_ready: bool,
    target_output_backend: dict[str, Any],
    spoken_text_privacy_scan: dict[str, Any],
    operator_checklist: dict[str, Any],
    command_template: str,
    checklist_path: Path,
) -> str:
    lines = [
        "# System output next step",
        "",
        "This artifact is safe to share: it uses placeholders and does not include spoken text, operator identity or local paths.",
        "",
        "## Status",
        "",
        f"- Created at: {timestamp}",
        f"- System from current run: {system}",
        f"- Expected system: {_format_nullable(system_guard['expected_system'])}",
        f"- Expected system matched: {_format_nullable(system_guard['expected_system_matched'])}",
        f"- Target output backend available: {target_output_backend['available']}",
        f"- Target output backend dependencies: {_format_list(target_output_backend['dependencies'])}",
        f"- Target output backend reason: {_format_optional(target_output_backend['reason'])}",
        f"- Output backend readiness required: {require_output_backend_ready}",
        f"- Dry run: {not speak}",
        f"- Real audio requested: {speak}",
        f"- Operator present: {operator_present}",
        f"- Operator confirmed audio: {operator_confirmed_audio}",
        f"- Text review confirmed: {text_review_confirmed}",
        f"- Spoken text privacy scan passed: {_format_nullable(spoken_text_privacy_scan['passed'])}",
        f"- Spoken text privacy risk count: {spoken_text_privacy_scan['risk_count']}",
        f"- Spoken text privacy risk types: {_format_list(spoken_text_privacy_scan['risk_types'])}",
        f"- Voice review confirmed: {voice_review_confirmed}",
        f"- Ready for real audio: {operator_checklist['ready_for_real_audio']}",
        f"- Ready for beta evidence: {operator_checklist['ready_for_beta_evidence']}",
        f"- Operator checklist: {checklist_path.name}",
        "",
        "## Command Template",
        "",
        "Replace `<public-spoken-text>` locally after confirming the text is public/non-sensitive:",
        "",
        "```powershell",
        command_template,
        "```",
        "",
        "## Required Review",
        "",
        "- Review `output-operator-checklist.md` before enabling `--speak`.",
        "- Keep the spoken text public/non-sensitive; do not paste private text into public findings.",
        "- Confirm `spoken_text_privacy_scan.passed=true` before playback.",
        "- Confirm `target_output_backend.available=true` before enabling `--speak`.",
        "- Confirm `system_guard.expected_system_matched=true` on the target OS.",
        "- Confirm `operator_checklist.text_review_confirmed=true`.",
        "- Confirm `operator_checklist.voice_review_confirmed=true` after hearing the output.",
        "- Confirm `operator_checklist.ready_for_beta_evidence=true` only after audible output and human review.",
        "",
    ]
    return "\n".join(lines)


def _build_operator_checklist_markdown(
    *,
    timestamp: str,
    system: str,
    operator_checklist: dict[str, Any],
) -> str:
    lines = [
        "# System output operator checklist",
        "",
        f"- Created at: {timestamp}",
        f"- System: {system}",
        f"- Records operator identity: {operator_checklist['records_operator_identity']}",
        f"- Redacts spoken text: {operator_checklist['redacts_spoken_text']}",
        f"- Text review confirmed: {operator_checklist['text_review_confirmed']}",
        f"- Spoken text privacy scan passed: {_format_nullable(operator_checklist['spoken_text_privacy_scan_passed'])}",
        f"- Spoken text privacy risk count: {operator_checklist['spoken_text_privacy_risk_count']}",
        f"- Spoken text privacy risk types: {_format_list(operator_checklist['spoken_text_privacy_risk_types'])}",
        f"- Voice review confirmed: {operator_checklist['voice_review_confirmed']}",
        f"- Expected system matched: {_format_nullable(operator_checklist['expected_system_matched'])}",
        f"- Commands available: {operator_checklist['commands_available']}",
        f"- Ready for real audio: {operator_checklist['ready_for_real_audio']}",
        f"- Ready for beta evidence: {operator_checklist['ready_for_beta_evidence']}",
        "",
        "## Before Playback",
        "",
    ]
    for item in operator_checklist["before_playback"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## After Playback",
            "",
        ]
    )
    for item in operator_checklist["after_playback"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Do not write private spoken text, operator names or local paths in shared findings.",
            "- Use system-output-next-step.md for a sanitized real-audio command template.",
            "- A dry-run checklist is preparation only; beta evidence requires real audio with --confirm-audible.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_checklist_item(item: dict[str, Any]) -> str:
    marker = "x" if item["ok"] is True else " "
    state = "unknown" if item["ok"] is None else str(item["ok"]).lower()
    return f"- [{marker}] `{item['id']}` ok={state} required={item['required']} - {item['instruction']}"


def _pilot_notes(speak: bool) -> str:
    if speak:
        return "Real system speech output was requested explicitly for this pilot."
    return "System speech output was dry-run only; rerun with --speak to play audio."


def _format_optional(value: object | None) -> str:
    return "none" if value in (None, "") else str(value)


def _format_nullable(value: object | None) -> str:
    return "not-set" if value is None else str(value)


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


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


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit system output pilot")
    print(f"System: {report['system']}")
    print(f"Expected system matched: {report['system_guard']['expected_system_matched']}")
    print(f"Target output backend available: {report['target_output_backend']['available']}")
    print(f"Dry run: {report['dry_run']}")
    print(f"Real audio requested: {report['real_audio_requested']}")
    print(f"Operator present: {report['operator_present']}")
    print(f"Operator confirmation: {report['operator_confirmation_status']}")
    print(f"Text review confirmed: {report['text_review_confirmed']}")
    print(f"Spoken text privacy scan passed: {report['spoken_text_privacy_scan']['passed']}")
    print(f"Voice review confirmed: {report['voice_review_confirmed']}")
    print(f"Passed: {report['passed']}")
    print(f"Voices: {report['voices_count']}")
    print(f"Commands: {report['commands_count']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
