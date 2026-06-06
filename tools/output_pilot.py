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
    next_system_output = {
        "artifact": str(next_step_path),
        "command_template": command_template,
        "target_output_backend": target_output_backend,
        "safe_to_share": True,
        "uses_placeholders": True,
        "records_spoken_text": False,
        "records_operator_identity": False,
        "records_local_paths": False,
        "requires_operator": True,
    }
    system_output_command_card = _system_output_command_card(
        command_template=command_template,
        target_output_backend=target_output_backend,
        require_output_backend_ready=require_output_backend_ready,
        speak=speak,
        confirmation_status=confirmation_status,
        text_review_confirmed=text_review_confirmed,
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        voice_review_confirmed=voice_review_confirmed,
        operator_checklist=operator_checklist,
        passed=passed,
    )
    beta_evidence_gap = _output_beta_evidence_gap(
        backend="system",
        system_guard=system_guard,
        target_output_backend=target_output_backend,
        require_output_backend_ready=require_output_backend_ready,
        speak=speak,
        confirmation_status=confirmation_status,
        text_review_confirmed=text_review_confirmed,
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        voice_review_confirmed=voice_review_confirmed,
        passed=passed,
        operator_checklist=operator_checklist,
        next_system_output=next_system_output,
        system_output_command_card=system_output_command_card,
    )
    system_output_operator_gate = _system_output_operator_gate(
        system_guard=system_guard,
        target_output_backend=target_output_backend,
        require_output_backend_ready=require_output_backend_ready,
        speak=speak,
        confirmation_status=confirmation_status,
        text_review_confirmed=text_review_confirmed,
        spoken_text_privacy_scan=spoken_text_privacy_scan,
        voice_review_confirmed=voice_review_confirmed,
        operator_checklist=operator_checklist,
        beta_evidence_gap=beta_evidence_gap,
        system_output_command_card=system_output_command_card,
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
        beta_evidence_gap=beta_evidence_gap,
        system_output_command_card=system_output_command_card,
        system_output_operator_gate=system_output_operator_gate,
        report_path=report_path,
        checklist_path=checklist_path,
        next_step_path=next_step_path,
    )
    checklist = _build_operator_checklist_markdown(
        timestamp=timestamp,
        system=system_name,
        operator_checklist=operator_checklist,
        system_output_operator_gate=system_output_operator_gate,
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
        beta_evidence_gap=beta_evidence_gap,
        system_output_command_card=system_output_command_card,
        system_output_operator_gate=system_output_operator_gate,
        command_template=command_template,
        checklist_path=checklist_path,
    )
    next_system_output["beta_evidence_gap"] = beta_evidence_gap

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
        "beta_evidence_gap": beta_evidence_gap,
        "next_system_output": next_system_output,
        "system_output_command_card": system_output_command_card,
        "system_output_operator_gate": system_output_operator_gate,
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
    dependencies = list(info.dependencies)
    readiness_plan = _output_backend_readiness_plan(system, dependencies)
    return {
        "name": info.name,
        "kind": info.kind,
        "available": info.available,
        "dependencies": dependencies,
        "reason": info.reason,
        "readiness_plan": readiness_plan,
    }


def _output_backend_readiness_plan(system: str, dependencies: list[str]) -> dict[str, Any]:
    normalized = system.lower()
    if normalized == "windows":
        setup_commands: list[str] = []
        platform_notes = [
            "Windows uses PowerShell plus the built-in System.Speech assembly.",
            "Run from the same session that will execute the audible pilot.",
        ]
    elif normalized in {"darwin", "macos", "mac"}:
        setup_commands = []
        platform_notes = [
            "macOS normally ships the say command with the operating system.",
            "Use System Settings to verify output device and volume before --speak.",
        ]
    elif normalized in {"linux", "ubuntu", "ubuntu/linux"}:
        setup_commands = [
            "sudo apt-get update",
            "sudo apt-get install -y speech-dispatcher espeak",
        ]
        platform_notes = [
            "Ubuntu/Linux needs either spd-say from speech-dispatcher or espeak on PATH.",
            "Check desktop audio routing and volume before asking an operator to confirm audible output.",
        ]
    else:
        setup_commands = []
        platform_notes = ["Unsupported system for the built-in system output backend."]
    post_install_check = (
        "python tools/output_pilot.py "
        f"--system {system} --require-output-backend-ready --json"
    )
    audible_check = (
        "python tools/output_pilot.py --speak --operator-present --confirm-audible "
        "--confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready "
        f"--expected-system \"{system}\" --output-dir <pilot-output-dir> "
        "--text <public-spoken-text> --json"
    )
    return {
        "backend": "system",
        "system": system,
        "candidate_commands": dependencies,
        "setup_commands": setup_commands,
        "requires_package_manager": bool(setup_commands),
        "post_install_check": post_install_check,
        "post_install_check_plays_audio": False,
        "audible_check_template": audible_check,
        "platform_notes": platform_notes,
    }


def _validate_output_backend_ready(*, target_output_backend: dict[str, Any], required: bool) -> None:
    if not required or target_output_backend["available"]:
        return
    dependencies = _format_list(target_output_backend["dependencies"])
    reason = target_output_backend["reason"] or "backend dependency check failed"
    readiness_plan = target_output_backend.get("readiness_plan", {})
    setup_commands = readiness_plan.get("setup_commands", [])
    setup_hint = f" Setup commands: {_format_list(setup_commands)}." if setup_commands else ""
    post_install_check = readiness_plan.get("post_install_check")
    check_hint = f" Recheck with: {post_install_check}." if post_install_check else ""
    raise ValueError(
        f"System output backend {target_output_backend['name']!r} is not available. "
        f"Dependencies: {dependencies}. Reason: {reason}.{setup_hint}{check_hint}"
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


def _output_beta_evidence_gap(
    *,
    backend: str,
    system_guard: dict[str, Any],
    target_output_backend: dict[str, Any],
    require_output_backend_ready: bool,
    speak: bool,
    confirmation_status: str,
    text_review_confirmed: bool,
    spoken_text_privacy_scan: dict[str, Any],
    voice_review_confirmed: bool,
    passed: bool,
    operator_checklist: dict[str, Any],
    next_system_output: dict[str, Any],
    system_output_command_card: dict[str, Any],
) -> dict[str, Any]:
    """Summarize why this output report does or does not close beta evidence."""

    checks = [
        _beta_gap_check("backend", "system", backend, backend == "system"),
        _beta_gap_check(
            "system_guard.expected_system_matched",
            True,
            system_guard["expected_system_matched"],
            system_guard["expected_system_matched"] is True,
        ),
        _beta_gap_check(
            "target_output_backend.available",
            True,
            target_output_backend["available"],
            target_output_backend["available"] is True,
        ),
        _beta_gap_check(
            "output_backend_ready_required",
            True,
            require_output_backend_ready,
            require_output_backend_ready,
        ),
        _beta_gap_check("real_audio_requested", True, speak, speak),
        _beta_gap_check(
            "operator_confirmation_status",
            "confirmed",
            confirmation_status,
            confirmation_status == "confirmed",
        ),
        _beta_gap_check("text_review_confirmed", True, text_review_confirmed, text_review_confirmed),
        _beta_gap_check(
            "spoken_text_privacy_scan.passed",
            True,
            spoken_text_privacy_scan["passed"],
            spoken_text_privacy_scan["passed"] is True,
        ),
        _beta_gap_check("voice_review_confirmed", True, voice_review_confirmed, voice_review_confirmed),
        _beta_gap_check(
            "operator_checklist.expected_system_matched",
            True,
            operator_checklist["expected_system_matched"],
            operator_checklist["expected_system_matched"] is True,
        ),
        _beta_gap_check(
            "operator_checklist.records_operator_identity",
            False,
            operator_checklist["records_operator_identity"],
            operator_checklist["records_operator_identity"] is False,
        ),
        _beta_gap_check(
            "operator_checklist.redacts_spoken_text",
            True,
            operator_checklist["redacts_spoken_text"],
            operator_checklist["redacts_spoken_text"],
        ),
        _beta_gap_check(
            "operator_checklist.text_review_confirmed",
            True,
            operator_checklist["text_review_confirmed"],
            operator_checklist["text_review_confirmed"],
        ),
        _beta_gap_check(
            "operator_checklist.spoken_text_privacy_scan_passed",
            True,
            operator_checklist["spoken_text_privacy_scan_passed"],
            operator_checklist["spoken_text_privacy_scan_passed"] is True,
        ),
        _beta_gap_check(
            "operator_checklist.voice_review_confirmed",
            True,
            operator_checklist["voice_review_confirmed"],
            operator_checklist["voice_review_confirmed"],
        ),
        _beta_gap_check(
            "operator_checklist.commands_available",
            True,
            operator_checklist["commands_available"],
            operator_checklist["commands_available"],
        ),
        _beta_gap_check(
            "operator_checklist.ready_for_real_audio",
            True,
            operator_checklist["ready_for_real_audio"],
            operator_checklist["ready_for_real_audio"],
        ),
        _beta_gap_check(
            "operator_checklist.ready_for_beta_evidence",
            True,
            operator_checklist["ready_for_beta_evidence"],
            operator_checklist["ready_for_beta_evidence"],
        ),
        _beta_gap_check(
            "next_system_output.uses_placeholders",
            True,
            next_system_output["uses_placeholders"],
            next_system_output["uses_placeholders"],
        ),
        _beta_gap_check(
            "next_system_output.records_spoken_text",
            False,
            next_system_output["records_spoken_text"],
            next_system_output["records_spoken_text"] is False,
        ),
        _beta_gap_check(
            "next_system_output.records_operator_identity",
            False,
            next_system_output["records_operator_identity"],
            next_system_output["records_operator_identity"] is False,
        ),
        _beta_gap_check(
            "system_output_command_card.artifact",
            "system-output-next-step.md",
            system_output_command_card["artifact"],
            system_output_command_card["artifact"] == "system-output-next-step.md",
        ),
        _beta_gap_check(
            "system_output_command_card.blocker",
            "system_output_audible",
            system_output_command_card["blocker"],
            system_output_command_card["blocker"] == "system_output_audible",
        ),
        _beta_gap_check(
            "system_output_command_card.ready_for_beta_evidence",
            True,
            system_output_command_card["ready_for_beta_evidence"],
            system_output_command_card["ready_for_beta_evidence"] is True,
        ),
        _beta_gap_check(
            "system_output_command_card.safe_to_share",
            True,
            system_output_command_card["safe_to_share"],
            system_output_command_card["safe_to_share"] is True,
        ),
        _beta_gap_check(
            "system_output_command_card.uses_placeholders",
            True,
            system_output_command_card["uses_placeholders"],
            system_output_command_card["uses_placeholders"] is True,
        ),
        _beta_gap_check(
            "system_output_command_card.preflight_plays_audio",
            False,
            system_output_command_card["preflight_plays_audio"],
            system_output_command_card["preflight_plays_audio"] is False,
        ),
        _beta_gap_check(
            "system_output_command_card.real_output_requires_operator",
            True,
            system_output_command_card["real_output_requires_operator"],
            system_output_command_card["real_output_requires_operator"] is True,
        ),
        _beta_gap_check(
            "system_output_command_card.records_audio",
            False,
            system_output_command_card["records_audio"],
            system_output_command_card["records_audio"] is False,
        ),
        _beta_gap_check(
            "system_output_command_card.records_spoken_text",
            False,
            system_output_command_card["records_spoken_text"],
            system_output_command_card["records_spoken_text"] is False,
        ),
        _beta_gap_check(
            "system_output_command_card.records_operator_identity",
            False,
            system_output_command_card["records_operator_identity"],
            system_output_command_card["records_operator_identity"] is False,
        ),
        _beta_gap_check(
            "system_output_command_card.records_local_paths",
            False,
            system_output_command_card["records_local_paths"],
            system_output_command_card["records_local_paths"] is False,
        ),
        _beta_gap_check("passed", True, passed, passed),
    ]
    missing_fields = [item["path"] for item in checks if item["ok"] is not True]
    ready = not missing_fields
    return {
        "blocker": "system_output_audible",
        "ready_for_beta_evidence": ready,
        "missing_count": len(missing_fields),
        "missing_fields": missing_fields,
        "checks": checks,
        "safe_to_share": True,
        "records_audio": False,
        "records_spoken_text": False,
        "records_operator_identity": False,
        "records_local_paths": False,
        "next_action": _output_beta_evidence_gap_next_action(missing_fields),
    }


def _beta_gap_check(path: str, expected: object, actual: object, ok: bool) -> dict[str, Any]:
    return {
        "path": path,
        "expected": expected,
        "actual": actual,
        "ok": bool(ok),
    }


def _output_beta_evidence_gap_next_action(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "Audit this report with tools/beta_readiness.py --audit-evidence before closing beta."
    if "real_audio_requested" in missing_fields or "operator_confirmation_status" in missing_fields:
        return "Run the audible system output pilot with --speak, an operator present and --confirm-audible."
    if "target_output_backend.available" in missing_fields or "output_backend_ready_required" in missing_fields:
        return "Follow the readiness plan, require the output backend and rerun before playback."
    if any(field.startswith("system_guard.") or field.endswith("expected_system_matched") for field in missing_fields):
        return "Rerun on the intended OS with --expected-system matching the actual platform."
    if any(field.startswith("spoken_text_privacy_scan") or field.endswith("text_review_confirmed") for field in missing_fields):
        return "Review public spoken text locally and rerun with --confirm-text-reviewed."
    if "voice_review_confirmed" in missing_fields or "operator_checklist.voice_review_confirmed" in missing_fields:
        return "After audible playback, review voice, volume and pronunciation, then rerun with --confirm-voice-reviewed."
    return "Complete the missing operator confirmations and rerun the beta evidence audit."


def _system_output_operator_gate(
    *,
    system_guard: dict[str, Any],
    target_output_backend: dict[str, Any],
    require_output_backend_ready: bool,
    speak: bool,
    confirmation_status: str,
    text_review_confirmed: bool,
    spoken_text_privacy_scan: dict[str, Any],
    voice_review_confirmed: bool,
    operator_checklist: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
    system_output_command_card: dict[str, Any],
) -> dict[str, Any]:
    confirmations = [
        _operator_gate_confirmation(
            "real_output_explicitly_requested",
            "--speak was used for this evidence report.",
            confirmed=speak,
            source="real_audio_requested",
        ),
        _operator_gate_confirmation(
            "operator_confirmed_audible",
            "The local operator confirmed audible output.",
            confirmed=confirmation_status == "confirmed",
            source="--confirm-audible",
        ),
        _operator_gate_confirmation(
            "text_reviewed",
            "Spoken text was reviewed locally and the public privacy scan passed.",
            confirmed=(
                text_review_confirmed
                and operator_checklist["text_review_confirmed"]
                and spoken_text_privacy_scan["passed"] is True
                and operator_checklist["spoken_text_privacy_scan_passed"] is True
            ),
            source="--confirm-text-reviewed + spoken_text_privacy_scan.passed",
        ),
        _operator_gate_confirmation(
            "voice_reviewed",
            "Voice, volume and pronunciation were reviewed after playback.",
            confirmed=voice_review_confirmed and operator_checklist["voice_review_confirmed"],
            source="--confirm-voice-reviewed",
        ),
        _operator_gate_confirmation(
            "expected_system_matched",
            "--expected-system matched the actual platform.",
            confirmed=system_guard["expected_system_matched"] is True,
            source="system_guard.expected_system_matched",
        ),
        _operator_gate_confirmation(
            "output_backend_ready_guarded",
            "The system output backend was available and --require-output-backend-ready was used.",
            confirmed=target_output_backend["available"] is True and require_output_backend_ready,
            source="target_output_backend.available + output_backend_ready_required",
        ),
        _operator_gate_confirmation(
            "operator_checklist_beta_ready",
            "The output operator checklist marked the audible run as beta-ready.",
            confirmed=operator_checklist["ready_for_beta_evidence"],
            source="operator_checklist.ready_for_beta_evidence",
        ),
    ]
    missing_confirmations = [item["id"] for item in confirmations if item["confirmed"] is not True]
    command_templates = (
        system_output_command_card["preflight_command_template"],
        system_output_command_card["real_output_command_template"],
        system_output_command_card["audit_command_template"],
    )
    command_safe_to_copy = bool(
        system_output_command_card["safe_to_share"]
        and system_output_command_card["uses_placeholders"]
        and system_output_command_card["preflight_plays_audio"] is False
        and system_output_command_card["real_output_requires_operator"] is True
        and system_output_command_card["records_audio"] is False
        and system_output_command_card["records_spoken_text"] is False
        and system_output_command_card["records_operator_identity"] is False
        and system_output_command_card["records_local_paths"] is False
        and all(isinstance(command, str) and "<pilot-output-dir>" in command for command in command_templates)
        and "<public-spoken-text>" in system_output_command_card["real_output_command_template"]
    )
    ready_for_beta_audit = bool(
        beta_evidence_gap["ready_for_beta_evidence"]
        and command_safe_to_copy
        and not missing_confirmations
    )
    return {
        "safe_to_share": True,
        "decision": "ready_for_beta_audit" if ready_for_beta_audit else "blocked",
        "blocker": beta_evidence_gap["blocker"],
        "expected_artifact": "output-pilot-report.json",
        "ready_for_beta_audit": ready_for_beta_audit,
        "command_safe_to_copy": command_safe_to_copy,
        "local_operator_required": True,
        "confirmations": confirmations,
        "missing_confirmations": missing_confirmations,
        "missing_confirmation_count": len(missing_confirmations),
        "missing_fields": list(beta_evidence_gap["missing_fields"]),
        "missing_field_count": beta_evidence_gap["missing_count"],
        "preflight_command_template": system_output_command_card["preflight_command_template"],
        "real_output_command_template": system_output_command_card["real_output_command_template"],
        "audit_command_template": system_output_command_card["audit_command_template"],
        "next_action": (
            "Run the strict beta evidence audit before closing this blocker."
            if ready_for_beta_audit
            else beta_evidence_gap["next_action"]
        ),
        "records_audio": False,
        "records_spoken_text": False,
        "records_operator_identity": False,
        "records_local_paths": False,
    }


def _operator_gate_confirmation(
    confirmation_id: str,
    instruction: str,
    *,
    confirmed: bool,
    source: str,
) -> dict[str, Any]:
    return {
        "id": confirmation_id,
        "required": True,
        "confirmed": bool(confirmed),
        "source": source,
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
    beta_evidence_gap: dict[str, Any],
    system_output_command_card: dict[str, Any],
    system_output_operator_gate: dict[str, Any],
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
        f"- Target output backend setup commands: {_format_list(target_output_backend['readiness_plan']['setup_commands'])}",
        f"- Target output backend post-install check: {target_output_backend['readiness_plan']['post_install_check']}",
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
        f"- System output command card ready for beta evidence: {system_output_command_card['ready_for_beta_evidence']}",
        f"- System output operator gate decision: {system_output_operator_gate['decision']}",
        f"- System output operator gate ready for beta audit: {system_output_operator_gate['ready_for_beta_audit']}",
        f"- System output operator gate missing confirmations: {system_output_operator_gate['missing_confirmation_count']}",
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
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
        "## Beta Evidence Gap",
        "",
        f"- Blocker: `{beta_evidence_gap['blocker']}`",
        f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
        f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
        "",
        "## System Output Operator Gate",
        "",
        f"- Decision: `{system_output_operator_gate['decision']}`",
        f"- Ready for beta audit: `{system_output_operator_gate['ready_for_beta_audit']}`",
        f"- Command safe to copy: `{system_output_operator_gate['command_safe_to_copy']}`",
        f"- Missing confirmations: {_format_list(system_output_operator_gate['missing_confirmations'])}",
        f"- Missing fields: {_format_list(system_output_operator_gate['missing_fields'])}",
        f"- Next action: {system_output_operator_gate['next_action']}",
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
        f"--expected-system \"{expected}\" --output-dir <pilot-output-dir> "
        "--text <public-spoken-text> --json"
    )


def _system_output_command_card(
    *,
    command_template: str,
    target_output_backend: dict[str, Any],
    require_output_backend_ready: bool,
    speak: bool,
    confirmation_status: str,
    text_review_confirmed: bool,
    spoken_text_privacy_scan: dict[str, Any],
    voice_review_confirmed: bool,
    operator_checklist: dict[str, Any],
    passed: bool,
) -> dict[str, Any]:
    preflight_command = _append_output_dir_placeholder(
        target_output_backend["readiness_plan"]["post_install_check"]
    )
    ready = (
        target_output_backend["available"] is True
        and require_output_backend_ready
        and speak
        and confirmation_status == "confirmed"
        and text_review_confirmed
        and spoken_text_privacy_scan["passed"] is True
        and voice_review_confirmed
        and operator_checklist["ready_for_beta_evidence"] is True
        and passed
    )
    return {
        "artifact": "system-output-next-step.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "blocker": "system_output_audible",
        "ready_for_beta_evidence": ready,
        "target_backend_available": target_output_backend["available"],
        "output_backend_ready_required": require_output_backend_ready,
        "preflight_command_template": preflight_command,
        "preflight_plays_audio": target_output_backend["readiness_plan"]["post_install_check_plays_audio"],
        "real_output_command_template": command_template,
        "real_output_requires_operator": True,
        "audit_command_template": (
            "python tools/beta_readiness.py --audit-evidence --evidence <pilot-output-dir> --json"
        ),
        "records_audio": False,
        "records_spoken_text": False,
        "records_operator_identity": False,
        "records_local_paths": False,
        "next_action": (
            "Audit this report with tools/beta_readiness.py --audit-evidence before closing beta."
            if ready
            else "Complete the audible output checklist and rerun before beta evidence audit."
        ),
    }


def _append_output_dir_placeholder(command: str) -> str:
    return f"{command} --output-dir <pilot-output-dir>"


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
    beta_evidence_gap: dict[str, Any],
    system_output_command_card: dict[str, Any],
    system_output_operator_gate: dict[str, Any],
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
        f"- Target output backend setup commands: {_format_list(target_output_backend['readiness_plan']['setup_commands'])}",
        f"- Target output backend post-install check: {target_output_backend['readiness_plan']['post_install_check']}",
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
        f"- Command card ready for beta evidence: {system_output_command_card['ready_for_beta_evidence']}",
        f"- Command card safe to share: {system_output_command_card['safe_to_share']}",
        f"- Command card uses placeholders: {system_output_command_card['uses_placeholders']}",
        f"- Command card records spoken text: {system_output_command_card['records_spoken_text']}",
        f"- Command card records operator identity: {system_output_command_card['records_operator_identity']}",
        f"- Command card records local paths: {system_output_command_card['records_local_paths']}",
        f"- Operator gate decision: {system_output_operator_gate['decision']}",
        f"- Operator gate ready for beta audit: {system_output_operator_gate['ready_for_beta_audit']}",
        f"- Operator gate command safe to copy: {system_output_operator_gate['command_safe_to_copy']}",
        f"- Operator gate missing confirmations: {system_output_operator_gate['missing_confirmation_count']}",
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
        f"- Operator checklist: {checklist_path.name}",
        "",
        "## Command Template",
        "",
        "Run the preflight command first. It does not play audio:",
        "",
        "```powershell",
        system_output_command_card["preflight_command_template"],
        "```",
        "",
        "Replace `<public-spoken-text>` locally after confirming the text is public/non-sensitive:",
        "",
        "```powershell",
        system_output_command_card["real_output_command_template"],
        "```",
        "",
        "Audit only the sanitized output directory:",
        "",
        "```powershell",
        system_output_command_card["audit_command_template"],
        "```",
        "",
        "## Beta Evidence Gap",
        "",
        f"- Blocker: `{beta_evidence_gap['blocker']}`",
        f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
        f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
        "",
        "## System Output Operator Gate",
        "",
        f"- Decision: `{system_output_operator_gate['decision']}`",
        f"- Ready for beta audit: `{system_output_operator_gate['ready_for_beta_audit']}`",
        f"- Command safe to copy: `{system_output_operator_gate['command_safe_to_copy']}`",
        f"- Missing confirmations: {_format_list(system_output_operator_gate['missing_confirmations'])}",
        f"- Missing fields: {_format_list(system_output_operator_gate['missing_fields'])}",
        "",
        "## Required Review",
        "",
        "- Review `output-operator-checklist.md` before enabling `--speak`.",
        "- Keep the spoken text public/non-sensitive; do not paste private text into public findings.",
        "- Confirm `spoken_text_privacy_scan.passed=true` before playback.",
        "- If the backend is unavailable, follow `target_output_backend.readiness_plan.setup_commands` on the target OS.",
        "- Run `target_output_backend.readiness_plan.post_install_check` before enabling `--speak`.",
        "- Confirm `target_output_backend.available=true` before enabling `--speak`.",
        "- Confirm `system_guard.expected_system_matched=true` on the target OS.",
        "- Confirm `operator_checklist.text_review_confirmed=true`.",
        "- Confirm `operator_checklist.voice_review_confirmed=true` after hearing the output.",
        "- Confirm `operator_checklist.ready_for_beta_evidence=true` only after audible output and human review.",
        "- Confirm `system_output_operator_gate.ready_for_beta_audit=true` only after the sanitized command card and all confirmations are complete.",
        "",
    ]
    return "\n".join(lines)


def _build_operator_checklist_markdown(
    *,
    timestamp: str,
    system: str,
    operator_checklist: dict[str, Any],
    system_output_operator_gate: dict[str, Any],
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
        f"- Operator gate decision: {system_output_operator_gate['decision']}",
        f"- Operator gate ready for beta audit: {system_output_operator_gate['ready_for_beta_audit']}",
        f"- Operator gate command safe to copy: {system_output_operator_gate['command_safe_to_copy']}",
        f"- Operator gate missing confirmations: {system_output_operator_gate['missing_confirmation_count']}",
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
            "## System Output Operator Gate",
            "",
            f"- Decision: `{system_output_operator_gate['decision']}`",
            f"- Ready for beta audit: `{system_output_operator_gate['ready_for_beta_audit']}`",
            f"- Missing confirmations: {_format_list(system_output_operator_gate['missing_confirmations'])}",
            f"- Missing fields: {_format_list(system_output_operator_gate['missing_fields'])}",
        ]
    )
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
    print(
        "Target output backend setup commands: "
        f"{_format_list(report['target_output_backend']['readiness_plan']['setup_commands'])}"
    )
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
