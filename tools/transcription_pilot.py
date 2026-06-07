"""Transcription pilot runner for AuralisVoiceKit.

The default run uses synthetic audio and the safe ``null`` backend. Real
transcription requires --real-transcription, a user-provided --audio file and a
backend other than null.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
from typing import Any
import unicodedata

from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceKitConfig,
    backend_freedom_policy,
    generate_synthetic_audio_chunks,
    normalize_pcm16,
    read_audio_as_chunk,
    write_wav,
)
from auralis_voicekit.backends import create_default_registry
from auralis_voicekit.exceptions import AudioSourceError, BackendNotAvailable, TranscriptionError


BETA_MIN_WORD_ACCURACY = 0.75
REDACTED_AUDIO_FILE_NAME = "<audio-file-redacted>"
REDACTED_REFERENCE_FILE_NAME = "<expected-text-file-redacted>"
REFERENCE_PRIVACY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
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


def run_transcription_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    audio: str | Path | None = None,
    backend: str = "null",
    model: str | None = None,
    language: str = "es",
    prompt: str | None = None,
    timeout_seconds: float | None = None,
    ffmpeg: str = "ffmpeg",
    normalize: bool = False,
    preflight_only: bool = False,
    real_transcription: bool = False,
    require_target_backend_ready: bool = False,
    require_openai_api_key: bool = False,
    audio_confirmed_non_sensitive: bool = False,
    audio_review_confirmed: bool = False,
    reference_review_confirmed: bool = False,
    quality_review_confirmed: bool = False,
    include_transcript_hash: bool = False,
    expected_text: str | None = None,
    expected_text_file: str | Path | None = None,
    min_word_accuracy: float | None = None,
    min_audio_seconds: float | None = None,
    max_audio_seconds: float | None = None,
    duration_seconds: float = 1.0,
    sample_rate: int = 16_000,
) -> dict[str, Any]:
    """Run a transcription pilot and write sanitized artifacts."""

    _validate_quality_flags(
        expected_text=expected_text,
        expected_text_file=expected_text_file,
        min_word_accuracy=min_word_accuracy,
        preflight_only=preflight_only,
        reference_review_confirmed=reference_review_confirmed,
    )
    _validate_quality_review_flags(
        quality_review_confirmed=quality_review_confirmed,
        preflight_only=preflight_only,
        real_transcription=real_transcription,
    )
    _validate_real_transcription_flags(
        audio=audio,
        backend=backend,
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        audio_confirmed_non_sensitive=audio_confirmed_non_sensitive,
        audio_review_confirmed=audio_review_confirmed,
    )
    _validate_timeout_seconds(timeout_seconds)
    target_backend = _transcription_backend_status(backend)
    _validate_target_backend_ready(
        target_backend=target_backend,
        required=require_target_backend_ready,
    )
    credentials = _openai_credentials_status(
        backend=backend,
        required=require_openai_api_key,
    )
    _validate_duration_limits(
        min_audio_seconds=min_audio_seconds,
        max_audio_seconds=max_audio_seconds,
    )
    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / "transcription" / _slug(timestamp)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    source_audio_path: Path
    generated_synthetic_audio = audio is None
    if generated_synthetic_audio:
        chunks = generate_synthetic_audio_chunks(
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            channels=1,
            chunk_duration_ms=100,
        )
        source_audio_path = output / "synthetic-input.wav"
        write_wav(str(source_audio_path), chunks)
    else:
        source_audio_path = Path(audio).resolve()

    expected_reference = _load_expected_reference(expected_text, expected_text_file)
    reference_privacy_scan = _reference_privacy_scan(expected_reference)
    config = VoiceKitConfig(
        transcription_backend=backend,
        transcription_model=model or "auto",
        transcription_prompt=prompt,
        transcription_timeout_seconds=timeout_seconds,
        language=language,
        privacy_mode=True,
    )
    result = None
    error = _openai_credentials_error(credentials)
    chunk = None
    duration_gate = _audio_duration_gate(
        None,
        min_audio_seconds=min_audio_seconds,
        max_audio_seconds=max_audio_seconds,
    )
    try:
        chunk = read_audio_as_chunk(
            str(source_audio_path),
            ffmpeg_executable=ffmpeg,
            sample_rate=sample_rate,
            channels=1,
        )
        duration_gate = _audio_duration_gate(
            chunk.duration_seconds,
            min_audio_seconds=min_audio_seconds,
            max_audio_seconds=max_audio_seconds,
        )
        if duration_gate["passed"] is False:
            raise ValueError(duration_gate["message"])
        if normalize:
            chunk = normalize_pcm16(chunk)
        if not preflight_only and error is None:
            result = AuralisVoiceKit(config).transcribe(chunk)
    except (AudioSourceError, BackendNotAvailable, TranscriptionError, ValueError) as exc:
        error = str(exc)

    passed = error is None
    transcript_text = result.text if result is not None else ""
    transcript_report = _transcript_report(
        transcript_text,
        include_hash=include_transcript_hash,
    )
    quality_report = _quality_report(
        transcript_text,
        expected_reference=expected_reference,
        min_word_accuracy=min_word_accuracy,
    )
    quality_gate_passed = quality_report["passed"]
    if quality_gate_passed is False:
        passed = False
    if reference_privacy_scan["passed"] is False:
        passed = False
    audio_decoder = _audio_metadata_value(chunk, "decoder") if chunk is not None else None
    audio_source_format = _audio_metadata_value(chunk, "source_format") if chunk is not None else None
    if audio_source_format is None and source_audio_path.suffix:
        audio_source_format = source_audio_path.suffix.lower().lstrip(".")
    result_payload = (
        {
            "source": result.source,
            "language": result.language,
            "confidence": result.confidence,
            "is_final": result.is_final,
            "metadata": _sanitize_metadata(result.metadata),
            **transcript_report,
        }
        if result is not None
        else None
    )
    audio_file_name_redacted = not generated_synthetic_audio
    audio_payload = {
        "generated_synthetic_audio": generated_synthetic_audio,
        "audio_file_name": source_audio_path.name if generated_synthetic_audio else REDACTED_AUDIO_FILE_NAME,
        "audio_file_name_redacted": audio_file_name_redacted,
        "audio_file_extension": source_audio_path.suffix.lower(),
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "audio_review_confirmed": audio_review_confirmed,
        "reference_review_confirmed": reference_review_confirmed,
        "decoded": chunk is not None,
        "decoder": audio_decoder,
        "source_format": audio_source_format,
        "normalized": bool(normalize and chunk is not None),
        "duration_seconds": chunk.duration_seconds if chunk is not None else None,
        "duration_gate": duration_gate,
        "sample_rate": chunk.format.sample_rate if chunk is not None else sample_rate,
        "channels": chunk.format.channels if chunk is not None else 1,
        "bytes": len(chunk.data) if chunk is not None else None,
    }
    transcription_checklist = _transcription_checklist(
        backend=backend,
        credentials=credentials,
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        passed=passed,
        audio=audio_payload,
        transcript=result_payload,
        quality=quality_report,
        reference_privacy_scan=reference_privacy_scan,
        audio_review_confirmed=audio_review_confirmed,
        reference_review_confirmed=reference_review_confirmed,
        quality_review_confirmed=quality_review_confirmed,
    )
    preflight_decision = _preflight_decision(
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        require_target_backend_ready=require_target_backend_ready,
        target_backend=target_backend,
        credentials=credentials,
        audio=audio_payload,
    )
    command_template = _real_transcription_command_template(
        backend=backend,
        model=model,
        normalize=normalize,
        min_audio_seconds=min_audio_seconds,
        max_audio_seconds=max_audio_seconds,
        timeout_seconds=timeout_seconds,
    )
    preflight_command_template = _real_transcription_preflight_command_template(
        backend=backend,
        model=model,
        min_audio_seconds=min_audio_seconds,
        max_audio_seconds=max_audio_seconds,
        timeout_seconds=timeout_seconds,
    )
    audit_command_template = _beta_evidence_audit_command_template()
    preflight_readiness = _preflight_readiness(
        preflight_decision=preflight_decision,
        target_backend=target_backend,
        credentials=credentials,
        audio=audio_payload,
        preflight_command_template=preflight_command_template,
        command_template=command_template,
    )
    beta_evidence_gap = _transcription_beta_evidence_gap(
        real_transcription=real_transcription,
        require_target_backend_ready=require_target_backend_ready,
        target_backend=target_backend,
        credentials=credentials,
        audio_confirmed_non_sensitive=audio_confirmed_non_sensitive,
        audio_review_confirmed=audio_review_confirmed,
        reference_review_confirmed=reference_review_confirmed,
        quality_review_confirmed=quality_review_confirmed,
        passed=passed,
        audio=audio_payload,
        transcript=result_payload,
        quality=quality_report,
        reference_privacy_scan=reference_privacy_scan,
        transcription_checklist=transcription_checklist,
        preflight_readiness=preflight_readiness,
    )
    command_card_payload = _real_transcription_command_card(
        backend=backend,
        beta_evidence_gap=beta_evidence_gap,
        preflight_command_template=preflight_command_template,
        command_template=command_template,
        audit_command_template=audit_command_template,
    )
    operator_gate = _real_transcription_operator_gate(
        real_transcription=real_transcription,
        require_target_backend_ready=require_target_backend_ready,
        target_backend=target_backend,
        credentials=credentials,
        audio=audio_payload,
        audio_review_confirmed=audio_review_confirmed,
        reference_review_confirmed=reference_review_confirmed,
        quality_review_confirmed=quality_review_confirmed,
        reference_privacy_scan=reference_privacy_scan,
        transcription_checklist=transcription_checklist,
        preflight_readiness=preflight_readiness,
        beta_evidence_gap=beta_evidence_gap,
        real_transcription_command_card=command_card_payload,
    )

    findings_path = output / "transcription-pilot-findings.md"
    checklist_path = output / "transcription-review-checklist.md"
    next_step_path = output / "real-transcription-next-step.md"
    command_path = output / "real-transcription-command.md"
    report_path = output / "transcription-pilot-report.json"
    findings = _build_findings_markdown(
        timestamp=timestamp,
        backend=backend,
        target_backend=target_backend,
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        passed=passed,
        error=error,
        audio=audio_payload,
        transcript=result_payload,
        quality=quality_report,
        reference_privacy_scan=reference_privacy_scan,
        audio_review_confirmed=audio_review_confirmed,
        reference_review_confirmed=reference_review_confirmed,
        quality_review_confirmed=quality_review_confirmed,
        timeout_seconds=timeout_seconds,
        transcription_checklist=transcription_checklist,
        preflight_decision=preflight_decision,
        preflight_readiness=preflight_readiness,
        beta_evidence_gap=beta_evidence_gap,
        real_transcription_command_card=command_card_payload,
        real_transcription_operator_gate=operator_gate,
        credentials=credentials,
        report_path=report_path,
        checklist_path=checklist_path,
        next_step_path=next_step_path,
        command_path=command_path,
    )
    checklist = _build_transcription_checklist_markdown(
        timestamp=timestamp,
        backend=backend,
        transcription_checklist=transcription_checklist,
        real_transcription_operator_gate=operator_gate,
    )
    next_step = _build_real_transcription_next_step_markdown(
        timestamp=timestamp,
        backend=backend,
        target_backend=target_backend,
        model=model,
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        require_target_backend_ready=require_target_backend_ready,
        credentials=credentials,
        timeout_seconds=timeout_seconds,
        audio=audio_payload,
        quality=quality_report,
        reference_privacy_scan=reference_privacy_scan,
        transcription_checklist=transcription_checklist,
        preflight_decision=preflight_decision,
        preflight_readiness=preflight_readiness,
        beta_evidence_gap=beta_evidence_gap,
        real_transcription_operator_gate=operator_gate,
        preflight_command_template=preflight_command_template,
        command_template=command_template,
        audit_command_template=audit_command_template,
        command_path=command_path,
        checklist_path=checklist_path,
    )
    command_card = _build_real_transcription_command_markdown(
        timestamp=timestamp,
        backend=backend,
        target_backend=target_backend,
        credentials=credentials,
        preflight_readiness=preflight_readiness,
        beta_evidence_gap=beta_evidence_gap,
        real_transcription_operator_gate=operator_gate,
        preflight_command_template=preflight_command_template,
        command_template=command_template,
        audit_command_template=audit_command_template,
    )

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": platform.system(),
        "backend": backend,
        "target_backend": target_backend,
        "model": model or "auto",
        "language": language,
        "transcription_timeout_seconds": timeout_seconds,
        "preflight_only": preflight_only,
        "real_transcription_requested": real_transcription,
        "target_backend_ready_required": require_target_backend_ready,
        "credentials": credentials,
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "audio_review_confirmed": audio_review_confirmed,
        "reference_review_confirmed": reference_review_confirmed,
        "quality_review_confirmed": quality_review_confirmed,
        "generated_synthetic_audio": generated_synthetic_audio,
        "normalize": normalize,
        "passed": passed,
        "error": error,
        "audio": audio_payload,
        "transcript": result_payload,
        "quality": quality_report,
        "reference_privacy_scan": reference_privacy_scan,
        "transcription_checklist": transcription_checklist,
        "preflight_decision": preflight_decision,
        "preflight_readiness": preflight_readiness,
        "beta_evidence_gap": beta_evidence_gap,
        "next_real_transcription": {
            "artifact": str(next_step_path),
            "command_artifact": str(command_path),
            "command_template": command_template,
            "preflight_command_template": preflight_command_template,
            "audit_command_template": audit_command_template,
            "preflight_readiness": preflight_readiness,
            "beta_evidence_gap": beta_evidence_gap,
            "target_backend": target_backend,
            "safe_to_share": True,
            "uses_placeholders": True,
            "records_audio": False,
            "records_audio_path": False,
            "records_audio_file_name": False,
            "records_transcript_text": False,
            "records_expected_text": False,
            "records_expected_text_file_name": False,
            "records_local_paths": False,
            "operator_gate": operator_gate,
        },
        "real_transcription_command_card": command_card_payload,
        "real_transcription_operator_gate": operator_gate,
        "notes": _pilot_notes(real_transcription, preflight_only),
        "artifacts": {
            "pilot_findings": str(findings_path),
            "transcription_review_checklist": str(checklist_path),
            "real_transcription_next_step": str(next_step_path),
            "real_transcription_command": str(command_path),
            "transcription_pilot_report": str(report_path),
        },
    }
    if generated_synthetic_audio:
        report["artifacts"]["synthetic_audio"] = str(source_audio_path)

    findings_path.write_text(findings, encoding="utf-8")
    checklist_path.write_text(checklist, encoding="utf-8")
    next_step_path.write_text(next_step, encoding="utf-8")
    command_path.write_text(command_card, encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe transcription pilot.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output-dir", help="directory for pilot artifacts")
    parser.add_argument("--audio", help="user-provided audio path for real transcription")
    parser.add_argument("--backend", default="null", help="transcription backend: null, whisper or openai")
    parser.add_argument("--model", help="transcription model")
    parser.add_argument("--language", default="es", help="audio language hint")
    parser.add_argument("--prompt", help="optional transcription prompt; not written to findings")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="optional transcription timeout passed to supported backends",
    )
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for compressed audio")
    parser.add_argument("--normalize", action="store_true", help="normalize audio before transcription")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="decode and summarize a user-provided audio file without running a transcription backend",
    )
    parser.add_argument(
        "--real-transcription",
        action="store_true",
        help="allow a real transcription backend; requires --audio and --audio-non-sensitive",
    )
    parser.add_argument(
        "--require-target-backend-ready",
        action="store_true",
        help="fail before audio/model work when the selected transcription backend dependency is missing",
    )
    parser.add_argument(
        "--require-openai-api-key",
        action="store_true",
        help="for --backend openai, require OPENAI_API_KEY presence without storing the secret value",
    )
    parser.add_argument(
        "--audio-non-sensitive",
        action="store_true",
        help="confirm the supplied audio is safe to process and summarize",
    )
    parser.add_argument(
        "--confirm-audio-reviewed",
        action="store_true",
        help="confirm a human reviewed the supplied audio privacy before beta evidence",
    )
    parser.add_argument(
        "--confirm-reference-reviewed",
        action="store_true",
        help="confirm a human reviewed the expected text privacy before beta evidence",
    )
    parser.add_argument(
        "--confirm-quality-reviewed",
        action="store_true",
        help="confirm a human reviewed redacted transcript quality before counting beta evidence",
    )
    parser.add_argument(
        "--include-transcript-hash",
        action="store_true",
        help="include sha256 of the transcript text without storing the text",
    )
    parser.add_argument(
        "--expected-text",
        help="optional reference text for redacted quality metrics",
    )
    parser.add_argument(
        "--expected-text-file",
        help="optional file containing reference text; file name is redacted and only the extension is reported",
    )
    parser.add_argument(
        "--min-word-accuracy",
        type=float,
        help="optional pass threshold from 0.0 to 1.0 for reference text quality",
    )
    parser.add_argument(
        "--min-audio-seconds",
        type=float,
        help="optional minimum decoded audio duration for pilot safety",
    )
    parser.add_argument(
        "--max-audio-seconds",
        type=float,
        help="optional maximum decoded audio duration for pilot safety",
    )
    parser.add_argument("--duration", type=float, default=1.0, help="synthetic audio duration")
    parser.add_argument("--sample-rate", type=int, default=16000, help="pilot audio sample rate")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    try:
        report = run_transcription_pilot(
            root=args.root,
            output_dir=args.output_dir,
            audio=args.audio,
            backend=args.backend,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            timeout_seconds=args.timeout_seconds,
            ffmpeg=args.ffmpeg,
            normalize=args.normalize,
            preflight_only=args.preflight_only,
            real_transcription=args.real_transcription,
            require_target_backend_ready=args.require_target_backend_ready,
            require_openai_api_key=args.require_openai_api_key,
            audio_confirmed_non_sensitive=args.audio_non_sensitive,
            audio_review_confirmed=args.confirm_audio_reviewed,
            reference_review_confirmed=args.confirm_reference_reviewed,
            quality_review_confirmed=args.confirm_quality_reviewed,
            include_transcript_hash=args.include_transcript_hash,
            expected_text=args.expected_text,
            expected_text_file=args.expected_text_file,
            min_word_accuracy=args.min_word_accuracy,
            min_audio_seconds=args.min_audio_seconds,
            max_audio_seconds=args.max_audio_seconds,
            duration_seconds=args.duration,
            sample_rate=args.sample_rate,
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


def _validate_real_transcription_flags(
    *,
    audio: str | Path | None,
    backend: str,
    preflight_only: bool,
    real_transcription: bool,
    audio_confirmed_non_sensitive: bool,
    audio_review_confirmed: bool,
) -> None:
    if preflight_only and real_transcription:
        raise ValueError("--preflight-only cannot be combined with --real-transcription.")
    if preflight_only and audio is None:
        raise ValueError("--preflight-only requires --audio with a user-provided file.")
    if preflight_only and not audio_confirmed_non_sensitive:
        raise ValueError("--preflight-only requires --audio-non-sensitive.")
    if backend != "null" and not real_transcription and not preflight_only:
        raise ValueError("Real transcription backends require --real-transcription.")
    if real_transcription and backend == "null":
        raise ValueError("--real-transcription requires --backend whisper or --backend openai.")
    if real_transcription and audio is None:
        raise ValueError("--real-transcription requires --audio with a user-provided file.")
    if real_transcription and not audio_confirmed_non_sensitive:
        raise ValueError("--real-transcription requires --audio-non-sensitive.")
    if audio_confirmed_non_sensitive and audio is None:
        raise ValueError("--audio-non-sensitive is only valid with --audio.")
    if audio_review_confirmed and audio is None:
        raise ValueError("--confirm-audio-reviewed is only valid with --audio.")
    if audio_review_confirmed and not audio_confirmed_non_sensitive:
        raise ValueError("--confirm-audio-reviewed requires --audio-non-sensitive.")


def _validate_quality_flags(
    *,
    expected_text: str | None,
    expected_text_file: str | Path | None,
    min_word_accuracy: float | None,
    preflight_only: bool,
    reference_review_confirmed: bool,
) -> None:
    if preflight_only and (
        expected_text is not None or expected_text_file is not None or min_word_accuracy is not None
    ):
        raise ValueError("--preflight-only does not calculate quality metrics; remove expected text flags.")
    if expected_text is not None and expected_text_file is not None:
        raise ValueError("Use either --expected-text or --expected-text-file, not both.")
    if min_word_accuracy is not None and not 0.0 <= min_word_accuracy <= 1.0:
        raise ValueError("--min-word-accuracy must be between 0.0 and 1.0.")
    if min_word_accuracy is not None and expected_text is None and expected_text_file is None:
        raise ValueError("--min-word-accuracy requires --expected-text or --expected-text-file.")
    if reference_review_confirmed and expected_text is None and expected_text_file is None:
        raise ValueError("--confirm-reference-reviewed requires --expected-text or --expected-text-file.")


def _validate_quality_review_flags(
    *,
    quality_review_confirmed: bool,
    preflight_only: bool,
    real_transcription: bool,
) -> None:
    if quality_review_confirmed and preflight_only:
        raise ValueError("--confirm-quality-reviewed cannot be used with --preflight-only.")
    if quality_review_confirmed and not real_transcription:
        raise ValueError("--confirm-quality-reviewed requires --real-transcription.")


def _validate_timeout_seconds(timeout_seconds: float | None) -> None:
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("transcription_timeout_seconds must be greater than zero")


def _transcription_backend_status(backend: str) -> dict[str, Any]:
    try:
        info = create_default_registry().create_transcription(backend).info()
    except BackendNotAvailable as exc:
        raise ValueError(str(exc)) from exc
    dependencies = list(info.dependencies)
    install_plan = _target_backend_install_plan(info.name, dependencies)
    return {
        "name": info.name,
        "kind": info.kind,
        "available": info.available,
        "dependencies": dependencies,
        "reason": info.reason,
        "install_command": install_plan["pip_command"],
        "install_plan": install_plan,
        "freedom_policy": backend_freedom_policy(info.kind, info.name),
    }


def _target_backend_install_plan(backend: str, dependencies: list[str]) -> dict[str, Any]:
    extra = {
        "whisper": "whisper",
        "openai": "openai",
    }.get(backend)
    pip_command = f'python -m pip install "auralisvoicekit[{extra}]"' if extra else None
    post_install_check = (
        "python tools/transcription_pilot.py --preflight-only "
        "--audio <audio-path> --audio-non-sensitive "
        f"--backend {backend} --require-target-backend-ready"
        f"{' --require-openai-api-key' if backend == 'openai' else ''} --json"
    )
    return {
        "backend": backend,
        "uses_pip_extra": extra is not None,
        "python_extra": extra,
        "extra": extra,
        "pip_command": pip_command,
        "dependencies": dependencies,
        "requires_network": extra is not None,
        "keeps_base_package_light": True,
        "platform_notes": [
            "Windows: run the command in the same virtual environment used for the pilot.",
            "Ubuntu/Linux: install ffmpeg and system audio packages separately when needed.",
            "macOS: use Homebrew for ffmpeg or PortAudio packages when needed.",
        ],
        "post_install_check": post_install_check,
    }


def _openai_credentials_status(*, backend: str, required: bool) -> dict[str, Any]:
    checked = backend == "openai"
    present = bool(os.environ.get("OPENAI_API_KEY", "").strip()) if checked else None
    required_for_run = bool(checked and required)
    if not checked:
        status = "not_applicable"
        action = "No OpenAI credential check is needed for this backend."
    elif present:
        status = "present"
        action = "OPENAI_API_KEY is present; the value is not recorded."
    elif required_for_run:
        status = "missing_required"
        action = "Set OPENAI_API_KEY locally before the OpenAI pilot; do not write the value into artifacts."
    else:
        status = "missing_optional"
        action = "Set OPENAI_API_KEY locally before the real OpenAI model call."
    return {
        "checked": checked,
        "backend": backend,
        "env_var": "OPENAI_API_KEY" if checked else None,
        "openai_api_key_required": required_for_run,
        "openai_api_key_present": present,
        "records_openai_api_key": False,
        "records_secret_value": False,
        "safe_to_share": True,
        "status": status,
        "action": action,
    }


def _openai_credentials_error(credentials: dict[str, Any]) -> str | None:
    if credentials["openai_api_key_required"] and credentials["openai_api_key_present"] is not True:
        return "OPENAI_API_KEY is required for this OpenAI pilot but was not present."
    return None


def _validate_target_backend_ready(*, target_backend: dict[str, Any], required: bool) -> None:
    if not required or target_backend["available"]:
        return
    dependencies = _format_list(target_backend["dependencies"])
    reason = target_backend["reason"] or "backend dependency check failed"
    install_command = target_backend.get("install_command")
    install_hint = f" Install with: {install_command}." if install_command else ""
    raise ValueError(
        f"Transcription backend {target_backend['name']!r} is not available. "
        f"Dependencies: {dependencies}. Reason: {reason}.{install_hint}"
    )


def _validate_duration_limits(
    *,
    min_audio_seconds: float | None,
    max_audio_seconds: float | None,
) -> None:
    if min_audio_seconds is not None and min_audio_seconds < 0:
        raise ValueError("--min-audio-seconds must be greater than or equal to 0.")
    if max_audio_seconds is not None and max_audio_seconds <= 0:
        raise ValueError("--max-audio-seconds must be greater than 0.")
    if (
        min_audio_seconds is not None
        and max_audio_seconds is not None
        and min_audio_seconds > max_audio_seconds
    ):
        raise ValueError("--min-audio-seconds must be less than or equal to --max-audio-seconds.")


def _load_expected_reference(
    expected_text: str | None,
    expected_text_file: str | Path | None,
) -> dict[str, Any] | None:
    if expected_text is not None:
        text = expected_text
        source = "argument"
        file_name = None
    elif expected_text_file is not None:
        path = Path(expected_text_file).resolve()
        if not path.exists():
            raise ValueError("--expected-text-file was not found.")
        text = path.read_text(encoding="utf-8")
        source = "file"
        file_name = REDACTED_REFERENCE_FILE_NAME
        file_name_redacted = True
        file_extension = path.suffix.lower()
    else:
        return None
    if expected_text is not None:
        file_name_redacted = False
        file_extension = None

    if not text.strip():
        raise ValueError("Expected text must not be empty.")
    return {
        "text": text,
        "source": source,
        "file_name": file_name,
        "file_name_redacted": file_name_redacted,
        "file_extension": file_extension,
    }


def _reference_privacy_scan(expected_reference: dict[str, Any] | None) -> dict[str, Any]:
    if expected_reference is None:
        return {
            "enabled": False,
            "passed": None,
            "status": "not_provided",
            "text_redacted": True,
            "risk_count": 0,
            "risk_types": [],
        }

    text = str(expected_reference["text"])
    risk_types: list[str] = []
    risk_count = 0
    for risk_type, pattern in REFERENCE_PRIVACY_PATTERNS:
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


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_text = str(key)
            if "text" in key_text.lower() or "prompt" in key_text.lower():
                sanitized[key_text] = "<redacted>"
            else:
                sanitized[key_text] = _sanitize_metadata(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_metadata(item) for item in value]
    return value


def _audio_metadata_value(chunk, key: str) -> Any:
    value = chunk.metadata.get(key)
    if value is None and key == "source_format":
        return None
    return _sanitize_metadata(value)


def _audio_duration_gate(
    duration_seconds: float | None,
    *,
    min_audio_seconds: float | None,
    max_audio_seconds: float | None,
) -> dict[str, Any]:
    enabled = min_audio_seconds is not None or max_audio_seconds is not None
    report: dict[str, Any] = {
        "enabled": enabled,
        "passed": None,
        "min_seconds": min_audio_seconds,
        "max_seconds": max_audio_seconds,
        "reason": "not_configured",
        "message": None,
    }
    if not enabled:
        return report
    if duration_seconds is None:
        report["reason"] = "pending_decode"
        return report

    rounded_duration = round(duration_seconds, 6)
    report["duration_seconds"] = rounded_duration
    if min_audio_seconds is not None and duration_seconds < min_audio_seconds:
        report["passed"] = False
        report["reason"] = "below_minimum"
        report["message"] = (
            f"Decoded audio duration {rounded_duration}s is below --min-audio-seconds {min_audio_seconds}s."
        )
    elif max_audio_seconds is not None and duration_seconds > max_audio_seconds:
        report["passed"] = False
        report["reason"] = "above_maximum"
        report["message"] = (
            f"Decoded audio duration {rounded_duration}s is above --max-audio-seconds {max_audio_seconds}s."
        )
    else:
        report["passed"] = True
        report["reason"] = "within_range"
    return report


def _transcript_report(text: str, *, include_hash: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "text_redacted": True,
        "text_characters": len(text),
        "text_words_estimate": len(text.split()) if text else 0,
    }
    if include_hash:
        payload["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return payload


def _quality_report(
    text: str,
    *,
    expected_reference: dict[str, Any] | None,
    min_word_accuracy: float | None,
) -> dict[str, Any]:
    if expected_reference is None:
        return {
            "enabled": False,
            "passed": None,
            "min_word_accuracy": min_word_accuracy,
        }

    expected_text = str(expected_reference["text"])
    reference_words = _quality_words(expected_text)
    transcript_words = _quality_words(text)
    reference_characters = _quality_characters(expected_text)
    transcript_characters = _quality_characters(text)
    word_errors = _levenshtein_distance(reference_words, transcript_words)
    character_errors = _levenshtein_distance(reference_characters, transcript_characters)
    word_error_rate = _error_rate(word_errors, len(reference_words), len(transcript_words))
    character_error_rate = _error_rate(character_errors, len(reference_characters), len(transcript_characters))
    word_accuracy = max(0.0, 1.0 - word_error_rate)
    passed = None if min_word_accuracy is None else word_accuracy >= min_word_accuracy

    return {
        "enabled": True,
        "passed": passed,
        "expected_text_redacted": True,
        "expected_text_source": expected_reference["source"],
        "expected_text_file_name": expected_reference["file_name"],
        "expected_text_file_name_redacted": expected_reference["file_name_redacted"],
        "expected_text_file_extension": expected_reference["file_extension"],
        "expected_text_characters": len(expected_text),
        "expected_text_words_estimate": len(expected_text.split()),
        "reference_words": len(reference_words),
        "transcript_words": len(transcript_words),
        "word_errors": word_errors,
        "word_error_rate": round(word_error_rate, 6),
        "word_accuracy": round(word_accuracy, 6),
        "reference_characters": len(reference_characters),
        "transcript_characters": len(transcript_characters),
        "character_errors": character_errors,
        "character_error_rate": round(character_error_rate, 6),
        "normalized_exact_match": reference_words == transcript_words,
        "min_word_accuracy": min_word_accuracy,
    }


def _quality_words(text: str) -> list[str]:
    normalized = _normalize_quality_text(text)
    return normalized.split() if normalized else []


def _quality_characters(text: str) -> list[str]:
    normalized = _normalize_quality_text(text).replace(" ", "")
    return list(normalized)


def _normalize_quality_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    cleaned = []
    previous_space = True
    for character in without_marks:
        if character.isalnum():
            cleaned.append(character)
            previous_space = False
        elif not previous_space:
            cleaned.append(" ")
            previous_space = True
    return "".join(cleaned).strip()


def _levenshtein_distance(reference: list[str], hypothesis: list[str]) -> int:
    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous = list(range(len(hypothesis) + 1))
    for reference_index, reference_item in enumerate(reference, start=1):
        current = [reference_index]
        for hypothesis_index, hypothesis_item in enumerate(hypothesis, start=1):
            substitution_cost = 0 if reference_item == hypothesis_item else 1
            current.append(
                min(
                    current[hypothesis_index - 1] + 1,
                    previous[hypothesis_index] + 1,
                    previous[hypothesis_index - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def _error_rate(errors: int, reference_count: int, hypothesis_count: int) -> float:
    if reference_count > 0:
        return errors / reference_count
    return 0.0 if hypothesis_count == 0 else 1.0


def _transcription_checklist(
    *,
    backend: str,
    credentials: dict[str, Any] | None = None,
    preflight_only: bool,
    real_transcription: bool,
    passed: bool,
    audio: dict[str, Any],
    transcript: dict[str, Any] | None,
    quality: dict[str, Any],
    reference_privacy_scan: dict[str, Any],
    audio_review_confirmed: bool,
    reference_review_confirmed: bool,
    quality_review_confirmed: bool,
) -> dict[str, Any]:
    if credentials is None:
        credentials = _openai_credentials_status(backend=backend, required=False)
    duration_gate = audio["duration_gate"]
    meaningful_quality_threshold = quality["min_word_accuracy"] is not None and float(
        quality["min_word_accuracy"]
    ) >= BETA_MIN_WORD_ACCURACY
    quality_ready = bool(quality["enabled"] and quality["passed"] is True and meaningful_quality_threshold)
    reference_privacy_ready = bool(reference_privacy_scan["enabled"] and reference_privacy_scan["passed"] is True)
    transcript_redacted = transcript is not None and transcript.get("text_redacted") is True
    ready_for_real_transcription = bool(
        real_transcription
        and backend != "null"
        and (not credentials["openai_api_key_required"] or credentials["openai_api_key_present"] is True)
        and audio["audio_confirmed_non_sensitive"]
        and audio_review_confirmed
        and audio["decoded"]
        and duration_gate["passed"] is not False
    )
    ready_for_beta_evidence = bool(
        ready_for_real_transcription
        and passed
        and transcript_redacted
        and quality_ready
        and reference_privacy_ready
        and quality_review_confirmed
        and reference_review_confirmed
        and not preflight_only
    )
    before = [
        _checklist_item(
            "audio_non_sensitive_confirmed",
            "Confirm the audio is non-sensitive before using --audio-non-sensitive.",
            ok=audio["audio_confirmed_non_sensitive"] if not audio["generated_synthetic_audio"] else None,
            required=True,
        ),
        _checklist_item(
            "audio_review_confirmed",
            "Use --confirm-audio-reviewed only after reviewing the supplied audio privacy locally.",
            ok=audio_review_confirmed if not audio["generated_synthetic_audio"] else None,
            required=True,
        ),
        _checklist_item(
            "audio_decoded",
            "Decode the audio successfully before running a real backend.",
            ok=audio["decoded"],
            required=True,
        ),
        _checklist_item(
            "duration_gate_reviewed",
            "Use --min-audio-seconds and --max-audio-seconds for real pilot audio.",
            ok=duration_gate["passed"] if duration_gate["enabled"] else None,
            required=True,
        ),
        _checklist_item(
            "reference_text_ready",
            "Provide --expected-text or --expected-text-file for redacted quality metrics.",
            ok=quality["enabled"],
            required=True,
        ),
        _checklist_item(
            "reference_review_confirmed",
            "Use --confirm-reference-reviewed only after reviewing the expected text privacy locally.",
            ok=reference_review_confirmed if quality["enabled"] else None,
            required=True,
        ),
        _checklist_item(
            "reference_privacy_scan_passed",
            "Use only public/non-sensitive expected text; review risk types locally if this scan blocks beta evidence.",
            ok=reference_privacy_scan["passed"] if reference_privacy_scan["enabled"] else None,
            required=True,
        ),
        _checklist_item(
            "real_backend_selected",
            "Use whisper or openai with --real-transcription only after preflight passes.",
            ok=backend != "null" if real_transcription or preflight_only else None,
            required=True,
        ),
    ]
    if credentials["checked"]:
        before.append(
            _checklist_item(
                "openai_api_key_present",
                "Set OPENAI_API_KEY locally for OpenAI; artifacts must record only presence, never the value.",
                ok=credentials["openai_api_key_present"],
                required=credentials["openai_api_key_required"],
            )
        )
    after = [
        _checklist_item(
            "transcript_redacted",
            "Verify artifacts contain transcript metadata only, not full transcript text.",
            ok=transcript_redacted if transcript is not None else None,
            required=True,
        ),
        _checklist_item(
            "quality_threshold_reviewed",
            "Require a meaningful min_word_accuracy threshold before beta evidence.",
            ok=quality_ready if quality["enabled"] else None,
            required=True,
        ),
        _checklist_item(
            "quality_review_confirmed",
            "Use --confirm-quality-reviewed only after a human reviewed redacted quality metrics and transcript quality locally.",
            ok=quality_review_confirmed if real_transcription else None,
            required=True,
        ),
        _checklist_item(
            "findings_public_safe",
            "Record only backend, model, aggregate metrics and technical issues in public findings.",
            ok=None,
            required=True,
        ),
    ]
    return {
        "records_audio_path": False,
        "records_audio_file_name": False,
        "records_transcript_text": False,
        "records_expected_text": False,
        "records_expected_text_file_name": False,
        "records_openai_api_key": False,
        "redacts_transcript_text": True,
        "redacts_expected_text": True,
        "openai_api_key_checked": credentials["checked"],
        "openai_api_key_required": credentials["openai_api_key_required"],
        "openai_api_key_present": credentials["openai_api_key_present"],
        "audio_review_confirmed": audio_review_confirmed,
        "reference_review_confirmed": reference_review_confirmed,
        "reference_privacy_scan_passed": reference_privacy_scan["passed"],
        "reference_privacy_risk_count": reference_privacy_scan["risk_count"],
        "reference_privacy_risk_types": reference_privacy_scan["risk_types"],
        "quality_review_confirmed": quality_review_confirmed,
        "ready_for_real_transcription": ready_for_real_transcription,
        "ready_for_beta_evidence": ready_for_beta_evidence,
        "before_transcription": before,
        "after_transcription": after,
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


def _preflight_decision(
    *,
    preflight_only: bool,
    real_transcription: bool,
    require_target_backend_ready: bool,
    target_backend: dict[str, Any],
    credentials: dict[str, Any],
    audio: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        _checklist_item(
            "preflight_or_guarded_real_run",
            "Run --preflight-only or a guarded real run before accepting beta evidence.",
            ok=preflight_only or real_transcription,
            required=True,
        ),
        _checklist_item(
            "target_backend_ready_required",
            "Use --require-target-backend-ready for real transcription evidence.",
            ok=True if preflight_only else require_target_backend_ready,
            required=True,
        ),
        _checklist_item(
            "audio_non_sensitive_confirmed",
            "Confirm the supplied audio is non-sensitive before processing.",
            ok=audio["audio_confirmed_non_sensitive"],
            required=True,
        ),
        _checklist_item(
            "audio_file_name_redacted",
            "Shared artifacts must redact the audio file name.",
            ok=audio["audio_file_name_redacted"],
            required=True,
        ),
        _checklist_item(
            "audio_decoded",
            "Decode the audio before running a model.",
            ok=audio["decoded"],
            required=True,
        ),
        _checklist_item(
            "duration_gate_enabled",
            "Use --min-audio-seconds and --max-audio-seconds before real transcription.",
            ok=audio["duration_gate"]["enabled"],
            required=True,
        ),
        _checklist_item(
            "duration_gate_passed",
            "Confirm the decoded duration is inside the configured bounds.",
            ok=audio["duration_gate"]["passed"] if audio["duration_gate"]["enabled"] else None,
            required=True,
        ),
        _checklist_item(
            "target_backend_available",
            "Install the optional transcription extra before the real model run.",
            ok=target_backend["available"],
            required=True,
        ),
    ]
    if credentials["checked"]:
        checks.append(
            _checklist_item(
                "openai_api_key_present",
                "Set OPENAI_API_KEY locally before the OpenAI pilot; artifacts record only presence.",
                ok=credentials["openai_api_key_present"],
                required=credentials["openai_api_key_required"],
            )
        )
    failed_preflight_checks = [
        item["id"]
        for item in checks
        if item["id"] != "target_backend_available" and item["required"] and item["ok"] is not True
    ]
    backend_ready = target_backend["available"] is True
    if not preflight_only and not real_transcription:
        decision = "not_applicable"
        blocking_reasons: list[str] = []
        next_action = "Run a sanitized --preflight-only pass with the target audio before the real model."
    elif failed_preflight_checks:
        decision = "blocked"
        blocking_reasons = failed_preflight_checks
        next_action = (
            "Fix the blocking preflight checks before using the local Whisper path "
            "or an optional proprietary API integration."
        )
    elif not backend_ready:
        decision = "install_backend_then_retry_preflight"
        blocking_reasons = []
        next_action = "Install the optional backend extra and rerun --preflight-only with --require-target-backend-ready."
    else:
        decision = "ready_for_real_transcription"
        blocking_reasons = []
        next_action = "Run the real transcription command template locally after reviewing audio and reference privacy."
    return {
        "decision": decision,
        "safe_to_share": True,
        "usable_as_beta_evidence": False,
        "records_audio": False,
        "records_transcripts": False,
        "records_expected_text": False,
        "records_local_paths": False,
        "records_audio_file_name": False,
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "backend_ready": backend_ready,
        "next_action": next_action,
    }


def _preflight_readiness(
    *,
    preflight_decision: dict[str, Any],
    target_backend: dict[str, Any],
    credentials: dict[str, Any],
    audio: dict[str, Any],
    preflight_command_template: str,
    command_template: str,
) -> dict[str, Any]:
    decision = preflight_decision["decision"]
    status_by_decision = {
        "ready_for_real_transcription": "ready",
        "install_backend_then_retry_preflight": "needs_backend_install",
        "blocked": "blocked",
        "not_applicable": "needs_preflight",
    }
    status = status_by_decision.get(decision, "blocked")
    ready_for_model_run = status == "ready"
    return {
        "status": status,
        "decision": decision,
        "ready_for_model_run": ready_for_model_run,
        "must_rerun_preflight": not ready_for_model_run,
        "safe_to_share": True,
        "usable_as_beta_evidence": False,
        "records_audio": False,
        "records_transcripts": False,
        "records_expected_text": False,
        "records_audio_file_name": False,
        "records_local_paths": False,
        "blocking_reasons": list(preflight_decision["blocking_reasons"]),
        "backend_ready": preflight_decision["backend_ready"],
        "audio_decoded": audio["decoded"],
        "duration_gate_enabled": audio["duration_gate"]["enabled"],
        "duration_gate_passed": audio["duration_gate"]["passed"],
        "credentials_status": credentials["status"],
        "preflight_command": preflight_command_template,
        "backend_post_install_check": target_backend["install_plan"]["post_install_check"],
        "real_transcription_command_template": command_template,
        "next_action": preflight_decision["next_action"],
    }


def _transcription_beta_evidence_gap(
    *,
    real_transcription: bool,
    require_target_backend_ready: bool,
    target_backend: dict[str, Any],
    credentials: dict[str, Any],
    audio_confirmed_non_sensitive: bool,
    audio_review_confirmed: bool,
    reference_review_confirmed: bool,
    quality_review_confirmed: bool,
    passed: bool,
    audio: dict[str, Any],
    transcript: dict[str, Any] | None,
    quality: dict[str, Any],
    reference_privacy_scan: dict[str, Any],
    transcription_checklist: dict[str, Any],
    preflight_readiness: dict[str, Any],
) -> dict[str, Any]:
    """Summarize why this transcription report does or does not close beta evidence."""

    quality_threshold_ready = quality["min_word_accuracy"] is not None and float(
        quality["min_word_accuracy"]
    ) >= BETA_MIN_WORD_ACCURACY
    transcript_redacted = transcript is not None and transcript.get("text_redacted") is True
    checks = [
        _beta_gap_check("real_transcription_requested", True, real_transcription, real_transcription),
        _beta_gap_check("target_backend.available", True, target_backend["available"], target_backend["available"]),
        _beta_gap_check(
            "target_backend_ready_required",
            True,
            require_target_backend_ready,
            require_target_backend_ready,
        ),
        _beta_gap_check("preflight_readiness.status", "ready", preflight_readiness["status"], preflight_readiness["status"] == "ready"),
        _beta_gap_check(
            "preflight_readiness.decision",
            "ready_for_real_transcription",
            preflight_readiness["decision"],
            preflight_readiness["decision"] == "ready_for_real_transcription",
        ),
        _beta_gap_check("preflight_readiness.ready_for_model_run", True, preflight_readiness["ready_for_model_run"], preflight_readiness["ready_for_model_run"]),
        _beta_gap_check("preflight_readiness.must_rerun_preflight", False, preflight_readiness["must_rerun_preflight"], preflight_readiness["must_rerun_preflight"] is False),
        _beta_gap_check("preflight_readiness.safe_to_share", True, preflight_readiness["safe_to_share"], preflight_readiness["safe_to_share"]),
        _beta_gap_check("preflight_readiness.usable_as_beta_evidence", False, preflight_readiness["usable_as_beta_evidence"], preflight_readiness["usable_as_beta_evidence"] is False),
        _beta_gap_check("preflight_readiness.records_audio", False, preflight_readiness["records_audio"], preflight_readiness["records_audio"] is False),
        _beta_gap_check("preflight_readiness.records_transcripts", False, preflight_readiness["records_transcripts"], preflight_readiness["records_transcripts"] is False),
        _beta_gap_check("preflight_readiness.records_expected_text", False, preflight_readiness["records_expected_text"], preflight_readiness["records_expected_text"] is False),
        _beta_gap_check("preflight_readiness.records_audio_file_name", False, preflight_readiness["records_audio_file_name"], preflight_readiness["records_audio_file_name"] is False),
        _beta_gap_check("preflight_readiness.records_local_paths", False, preflight_readiness["records_local_paths"], preflight_readiness["records_local_paths"] is False),
        _beta_gap_check("preflight_readiness.backend_ready", True, preflight_readiness["backend_ready"], preflight_readiness["backend_ready"]),
        _beta_gap_check("preflight_readiness.audio_decoded", True, preflight_readiness["audio_decoded"], preflight_readiness["audio_decoded"]),
        _beta_gap_check("preflight_readiness.duration_gate_enabled", True, preflight_readiness["duration_gate_enabled"], preflight_readiness["duration_gate_enabled"]),
        _beta_gap_check("preflight_readiness.duration_gate_passed", True, preflight_readiness["duration_gate_passed"], preflight_readiness["duration_gate_passed"] is True),
        _beta_gap_check("audio_confirmed_non_sensitive", True, audio_confirmed_non_sensitive, audio_confirmed_non_sensitive),
        _beta_gap_check("audio.generated_synthetic_audio", False, audio["generated_synthetic_audio"], audio["generated_synthetic_audio"] is False),
        _beta_gap_check("audio.audio_confirmed_non_sensitive", True, audio["audio_confirmed_non_sensitive"], audio["audio_confirmed_non_sensitive"]),
        _beta_gap_check("audio.decoded", True, audio["decoded"], audio["decoded"]),
        _beta_gap_check("audio.audio_file_name_redacted", True, audio["audio_file_name_redacted"], audio["audio_file_name_redacted"]),
        _beta_gap_check("audio.duration_gate.enabled", True, audio["duration_gate"]["enabled"], audio["duration_gate"]["enabled"]),
        _beta_gap_check("audio.duration_gate.passed", True, audio["duration_gate"]["passed"], audio["duration_gate"]["passed"] is True),
        _beta_gap_check("audio_review_confirmed", True, audio_review_confirmed, audio_review_confirmed),
        _beta_gap_check("reference_review_confirmed", True, reference_review_confirmed, reference_review_confirmed),
        _beta_gap_check("reference_privacy_scan.passed", True, reference_privacy_scan["passed"], reference_privacy_scan["passed"] is True),
        _beta_gap_check("quality_review_confirmed", True, quality_review_confirmed, quality_review_confirmed),
        _beta_gap_check("passed", True, passed, passed),
        _beta_gap_check("transcript.text_redacted", True, transcript_redacted, transcript_redacted),
        _beta_gap_check("quality.enabled", True, quality["enabled"], quality["enabled"]),
        _beta_gap_check("quality.passed", True, quality["passed"], quality["passed"] is True),
        _beta_gap_check("quality.min_word_accuracy", f">={BETA_MIN_WORD_ACCURACY}", quality["min_word_accuracy"], quality_threshold_ready),
        _beta_gap_check("transcription_checklist.audio_review_confirmed", True, transcription_checklist["audio_review_confirmed"], transcription_checklist["audio_review_confirmed"]),
        _beta_gap_check("transcription_checklist.records_audio_path", False, transcription_checklist["records_audio_path"], transcription_checklist["records_audio_path"] is False),
        _beta_gap_check("transcription_checklist.records_audio_file_name", False, transcription_checklist["records_audio_file_name"], transcription_checklist["records_audio_file_name"] is False),
        _beta_gap_check("transcription_checklist.records_transcript_text", False, transcription_checklist["records_transcript_text"], transcription_checklist["records_transcript_text"] is False),
        _beta_gap_check("transcription_checklist.records_expected_text", False, transcription_checklist["records_expected_text"], transcription_checklist["records_expected_text"] is False),
        _beta_gap_check("transcription_checklist.records_expected_text_file_name", False, transcription_checklist["records_expected_text_file_name"], transcription_checklist["records_expected_text_file_name"] is False),
        _beta_gap_check("transcription_checklist.redacts_transcript_text", True, transcription_checklist["redacts_transcript_text"], transcription_checklist["redacts_transcript_text"]),
        _beta_gap_check("transcription_checklist.redacts_expected_text", True, transcription_checklist["redacts_expected_text"], transcription_checklist["redacts_expected_text"]),
        _beta_gap_check("transcription_checklist.reference_review_confirmed", True, transcription_checklist["reference_review_confirmed"], transcription_checklist["reference_review_confirmed"]),
        _beta_gap_check("transcription_checklist.reference_privacy_scan_passed", True, transcription_checklist["reference_privacy_scan_passed"], transcription_checklist["reference_privacy_scan_passed"] is True),
        _beta_gap_check("transcription_checklist.quality_review_confirmed", True, transcription_checklist["quality_review_confirmed"], transcription_checklist["quality_review_confirmed"]),
        _beta_gap_check("transcription_checklist.ready_for_beta_evidence", True, transcription_checklist["ready_for_beta_evidence"], transcription_checklist["ready_for_beta_evidence"]),
    ]
    if target_backend["name"] == "openai":
        checks.extend(
            [
                _beta_gap_check("credentials.checked", True, credentials["checked"], credentials["checked"]),
                _beta_gap_check("credentials.openai_api_key_required", True, credentials["openai_api_key_required"], credentials["openai_api_key_required"]),
                _beta_gap_check("credentials.openai_api_key_present", True, credentials["openai_api_key_present"], credentials["openai_api_key_present"] is True),
                _beta_gap_check("credentials.records_openai_api_key", False, credentials["records_openai_api_key"], credentials["records_openai_api_key"] is False),
            ]
        )
    missing_fields = [item["path"] for item in checks if item["ok"] is not True]
    ready = not missing_fields
    return {
        "blocker": "real_transcription_quality",
        "ready_for_beta_evidence": ready,
        "missing_count": len(missing_fields),
        "missing_fields": missing_fields,
        "checks": checks,
        "safe_to_share": True,
        "records_audio": False,
        "records_transcripts": False,
        "records_expected_text": False,
        "records_audio_file_name": False,
        "records_local_paths": False,
        "next_action": _beta_evidence_gap_next_action(missing_fields),
    }


def _beta_gap_check(path: str, expected: object, actual: object, ok: bool) -> dict[str, Any]:
    return {
        "path": path,
        "expected": expected,
        "actual": actual,
        "ok": bool(ok),
    }


def _beta_evidence_gap_next_action(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "Audit this report with tools/beta_readiness.py --audit-evidence before closing beta."
    if any(field.startswith("preflight_readiness.") for field in missing_fields):
        return "Rerun the guarded preflight or real transcription command until preflight_readiness is ready."
    if any(field.startswith("credentials.") for field in missing_fields):
        return "Set the required credential locally and rerun without writing secret values to artifacts."
    if any(field.startswith("audio.") or field == "audio_confirmed_non_sensitive" for field in missing_fields):
        return "Review the non-sensitive audio locally, keep duration guards enabled and rerun the pilot."
    if any(field.startswith("reference_") or field.startswith("quality.") for field in missing_fields):
        return "Review the expected text privacy and quality threshold locally, then rerun with quality review confirmed."
    return "Complete the missing review confirmations and rerun the beta evidence audit."


def _build_findings_markdown(
    *,
    timestamp: str,
    backend: str,
    target_backend: dict[str, Any],
    preflight_only: bool,
    real_transcription: bool,
    passed: bool,
    error: str | None,
    audio: dict[str, Any],
    transcript: dict[str, Any] | None,
    quality: dict[str, Any],
    reference_privacy_scan: dict[str, Any],
    audio_review_confirmed: bool,
    reference_review_confirmed: bool,
    quality_review_confirmed: bool,
    timeout_seconds: float | None,
    transcription_checklist: dict[str, Any],
    preflight_decision: dict[str, Any],
    preflight_readiness: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
    real_transcription_command_card: dict[str, Any],
    real_transcription_operator_gate: dict[str, Any],
    credentials: dict[str, Any],
    report_path: Path,
    checklist_path: Path,
    next_step_path: Path,
    command_path: Path,
) -> str:
    transcript_characters = transcript.get("text_characters") if transcript is not None else 0
    lines = [
        "# Transcription pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- Backend: {backend}",
        f"- Target backend available: {target_backend['available']}",
        f"- Target backend dependencies: {_format_list(target_backend['dependencies'])}",
        f"- Target backend reason: {_format_optional(target_backend['reason'])}",
        f"- Target backend freedom policy: {_backend_policy_value(target_backend, 'category')}",
        f"- Target backend proprietary: {_backend_policy_value(target_backend, 'proprietary')}",
        f"- Target backend network required: {_backend_policy_value(target_backend, 'network_required')}",
        f"- Target backend install command: {_format_optional(target_backend['install_command'])}",
        f"- Target backend post-install check: {target_backend['install_plan']['post_install_check']}",
        f"- OpenAI API key check: {credentials['status']}",
        f"- OpenAI API key required: {credentials['openai_api_key_required']}",
        f"- OpenAI API key present: {_format_optional(credentials['openai_api_key_present'])}",
        f"- Records OpenAI API key: {credentials['records_openai_api_key']}",
        f"- Preflight only: {preflight_only}",
        f"- Real transcription requested: {real_transcription}",
        f"- Transcription timeout seconds: {_format_optional(timeout_seconds)}",
        f"- Passed: {passed}",
        f"- Audio file name: {audio['audio_file_name']}",
        f"- Audio file name redacted: {audio['audio_file_name_redacted']}",
        f"- Audio extension: {audio['audio_file_extension'] or 'none'}",
        f"- Generated synthetic audio: {audio['generated_synthetic_audio']}",
        f"- Audio confirmed non-sensitive: {audio['audio_confirmed_non_sensitive']}",
        f"- Audio review confirmed: {audio_review_confirmed}",
        f"- Audio decode passed: {audio['decoded']}",
        f"- Decoder: {_format_optional(audio['decoder'])}",
        f"- Source format: {_format_optional(audio['source_format'])}",
        f"- Normalized: {audio['normalized']}",
        f"- Duration seconds: {_format_optional(audio['duration_seconds'])}",
        f"- Duration gate enabled: {audio['duration_gate']['enabled']}",
        f"- Duration gate passed: {_format_optional(audio['duration_gate']['passed'])}",
        f"- Transcript characters: {transcript_characters}",
        f"- Quality reference provided: {quality['enabled']}",
        f"- Reference review confirmed: {reference_review_confirmed}",
        f"- Reference privacy scan passed: {_format_optional(reference_privacy_scan['passed'])}",
        f"- Reference privacy risk count: {reference_privacy_scan['risk_count']}",
        f"- Reference privacy risk types: {_format_list(reference_privacy_scan['risk_types'])}",
        f"- Quality gate passed: {_format_optional(quality['passed'])}",
        f"- Quality review confirmed: {quality_review_confirmed}",
        f"- Transcription checklist ready for beta evidence: {transcription_checklist['ready_for_beta_evidence']}",
        f"- Preflight decision: {preflight_decision['decision']}",
        f"- Preflight readiness status: {preflight_readiness['status']}",
        f"- Preflight ready for model run: {preflight_readiness['ready_for_model_run']}",
        f"- Preflight must rerun: {preflight_readiness['must_rerun_preflight']}",
        f"- Preflight next action: {preflight_decision['next_action']}",
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
        f"- Real transcription command card ready for beta evidence: {real_transcription_command_card['ready_for_beta_evidence']}",
        f"- Real transcription command card uses pip extra: {real_transcription_command_card['uses_pip_extra']}",
        f"- Real transcription command card python extra: {_format_optional(real_transcription_command_card['python_extra'])}",
        f"- Real transcription command card pip command: {_format_optional(real_transcription_command_card['pip_command'])}",
        f"- Real transcription operator gate decision: {real_transcription_operator_gate['decision']}",
        f"- Real transcription operator gate ready for beta audit: {real_transcription_operator_gate['ready_for_beta_audit']}",
        f"- Real transcription operator gate command safe to copy: {real_transcription_operator_gate['command_safe_to_copy']}",
        f"- Real transcription operator gate missing confirmations: {real_transcription_operator_gate['missing_confirmation_count']}",
        f"- Report: {report_path.name}",
        f"- Review checklist: {checklist_path.name}",
        f"- Real transcription next step: {next_step_path.name}",
        f"- Real transcription command: {command_path.name}",
        "",
        "## Privacy",
        "",
        "- The full transcript is not written to findings or JSON artifacts.",
        "- The full audio path is not written to findings.",
        "- User audio and reference file names are redacted in shared artifacts.",
        "- Reference privacy scanning reports only risk types and counts, not matched text.",
        "- OpenAI credential checks report only whether OPENAI_API_KEY is present; the key value is never written.",
        "- Prompt-like metadata is redacted.",
        "",
        "## Quality",
        "",
    ]
    if quality["enabled"]:
        lines.extend(
            [
                f"- Expected text source: {quality['expected_text_source']}",
                f"- Expected text file name: {_format_optional(quality['expected_text_file_name'])}",
                f"- Expected text file name redacted: {quality['expected_text_file_name_redacted']}",
                f"- Expected text file extension: {_format_optional(quality['expected_text_file_extension'])}",
                f"- Expected text characters: {quality['expected_text_characters']}",
                f"- Word accuracy: {quality['word_accuracy']}",
                f"- Word error rate: {quality['word_error_rate']}",
                f"- Character error rate: {quality['character_error_rate']}",
                f"- Normalized exact match: {quality['normalized_exact_match']}",
                f"- Minimum word accuracy: {_format_optional(quality['min_word_accuracy'])}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- No expected text was provided, so quality metrics were not calculated.",
                "",
            ]
        )
    lines.extend(
        [
        "## Result",
        "",
        f"- Error: {_format_optional(error)}",
        "",
        "## Beta Evidence Gap",
        "",
        f"- Blocker: `{beta_evidence_gap['blocker']}`",
        f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
        f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
        "",
        "## Real Transcription Operator Gate",
        "",
        f"- Decision: `{real_transcription_operator_gate['decision']}`",
        f"- Ready for beta audit: `{real_transcription_operator_gate['ready_for_beta_audit']}`",
        f"- Command safe to copy: `{real_transcription_operator_gate['command_safe_to_copy']}`",
        f"- Missing confirmations: {_format_list(real_transcription_operator_gate['missing_confirmations'])}",
        f"- Missing fields: {_format_list(real_transcription_operator_gate['missing_fields'])}",
        f"- Next action: {real_transcription_operator_gate['next_action']}",
        "",
        "## Follow-up",
        "",
        ]
    )
    if preflight_only:
        lines.append(
            "- Re-run without --preflight-only and with --real-transcription once the audio, backend and reference text are ready."
        )
    elif real_transcription:
        lines.append("- Review transcript quality manually without attaching sensitive audio or text to public reports.")
    else:
        lines.append(
            "- Re-run with --real-transcription --audio PATH --audio-non-sensitive and backend whisper/openai for a real pilot."
        )
    lines.append("- Add --expected-text or --expected-text-file to calculate redacted quality metrics.")
    lines.append("- Record backend/model, audio type and high-level quality findings in PILOT_FINDINGS.md.")
    lines.append("")
    return "\n".join(lines)


def _real_transcription_command_template(
    *,
    backend: str,
    model: str | None,
    normalize: bool,
    min_audio_seconds: float | None,
    max_audio_seconds: float | None,
    timeout_seconds: float | None,
) -> str:
    real_backend = backend if backend != "null" else "whisper"
    if model:
        real_model = model
    elif real_backend == "openai":
        real_model = "gpt-4o-mini-transcribe"
    else:
        real_model = "base"
    min_seconds = 0.2 if min_audio_seconds is None else min_audio_seconds
    max_seconds = 60 if max_audio_seconds is None else max_audio_seconds
    normalize_flag = " --normalize" if normalize else ""
    default_timeout_seconds = 30 if real_backend == "openai" else None
    effective_timeout_seconds = timeout_seconds if timeout_seconds is not None else default_timeout_seconds
    timeout_flag = (
        f" --timeout-seconds {_format_cli_number(effective_timeout_seconds)}"
        if effective_timeout_seconds is not None
        else ""
    )
    credential_flag = " --require-openai-api-key" if real_backend == "openai" else ""
    return (
        "python tools/transcription_pilot.py --real-transcription "
        "--audio <audio-path> --audio-non-sensitive --confirm-audio-reviewed "
        "--confirm-reference-reviewed "
        f"--backend {real_backend} --model {real_model}{normalize_flag}{timeout_flag} "
        "--expected-text-file <expected-text-path> --min-word-accuracy 0.75 "
        f"--min-audio-seconds {_format_cli_number(min_seconds)} "
        f"--max-audio-seconds {_format_cli_number(max_seconds)} "
        f"--confirm-quality-reviewed --require-target-backend-ready{credential_flag} "
        "--output-dir <pilot-output-dir> --json"
    )


def _real_transcription_preflight_command_template(
    *,
    backend: str,
    model: str | None,
    min_audio_seconds: float | None,
    max_audio_seconds: float | None,
    timeout_seconds: float | None,
) -> str:
    real_backend = backend if backend != "null" else "whisper"
    if model:
        real_model = model
    elif real_backend == "openai":
        real_model = "gpt-4o-mini-transcribe"
    else:
        real_model = "base"
    min_seconds = 0.2 if min_audio_seconds is None else min_audio_seconds
    max_seconds = 60 if max_audio_seconds is None else max_audio_seconds
    default_timeout_seconds = 30 if real_backend == "openai" else None
    effective_timeout_seconds = timeout_seconds if timeout_seconds is not None else default_timeout_seconds
    timeout_flag = (
        f" --timeout-seconds {_format_cli_number(effective_timeout_seconds)}"
        if effective_timeout_seconds is not None
        else ""
    )
    credential_flag = " --require-openai-api-key" if real_backend == "openai" else ""
    return (
        "python tools/transcription_pilot.py --preflight-only "
        "--audio <audio-path> --audio-non-sensitive --confirm-audio-reviewed "
        f"--backend {real_backend} --model {real_model}{timeout_flag} "
        f"--min-audio-seconds {_format_cli_number(min_seconds)} "
        f"--max-audio-seconds {_format_cli_number(max_seconds)} "
        f"--require-target-backend-ready{credential_flag} --output-dir <pilot-output-dir> --json"
    )


def _beta_evidence_audit_command_template() -> str:
    return (
        "python tools/beta_readiness.py --audit-evidence "
        "--evidence <pilot-output-dir> --output <pilot-output-dir>/beta-evidence-audit.md --json"
    )


def _real_transcription_command_card(
    *,
    backend: str,
    beta_evidence_gap: dict[str, Any],
    preflight_command_template: str,
    command_template: str,
    audit_command_template: str,
) -> dict[str, Any]:
    python_extra = _real_transcription_python_extra(backend)
    pip_command = f'python -m pip install "auralisvoicekit[{python_extra}]"' if python_extra else None
    return {
        "artifact": "real-transcription-command.md",
        "safe_to_share": True,
        "uses_placeholders": True,
        "uses_pip_extra": python_extra is not None,
        "python_extra": python_extra,
        "pip_command": pip_command,
        "blocker": "real_transcription_quality",
        "ready_for_beta_evidence": beta_evidence_gap["ready_for_beta_evidence"],
        "missing_count": beta_evidence_gap["missing_count"],
        "missing_fields": beta_evidence_gap["missing_fields"],
        "preflight_command_template": preflight_command_template,
        "preflight_runs_model": False,
        "real_transcription_command_template": command_template,
        "real_transcription_requires_user_audio": True,
        "real_transcription_requires_quality_review": True,
        "audit_command_template": audit_command_template,
        "records_audio": False,
        "records_audio_path": False,
        "records_audio_file_name": False,
        "records_transcript_text": False,
        "records_expected_text": False,
        "records_expected_text_file_name": False,
        "records_local_paths": False,
    }


def _real_transcription_python_extra(backend: str) -> str | None:
    real_backend = backend if backend != "null" else "whisper"
    if real_backend in {"whisper", "openai"}:
        return real_backend
    return None


def _real_transcription_operator_gate(
    *,
    real_transcription: bool,
    require_target_backend_ready: bool,
    target_backend: dict[str, Any],
    credentials: dict[str, Any],
    audio: dict[str, Any],
    audio_review_confirmed: bool,
    reference_review_confirmed: bool,
    quality_review_confirmed: bool,
    reference_privacy_scan: dict[str, Any],
    transcription_checklist: dict[str, Any],
    preflight_readiness: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
    real_transcription_command_card: dict[str, Any],
) -> dict[str, Any]:
    confirmations = [
        _operator_gate_confirmation(
            "real_transcription_explicitly_requested",
            "--real-transcription was used for this evidence report.",
            confirmed=real_transcription,
            source="real_transcription_requested",
        ),
        _operator_gate_confirmation(
            "audio_reviewed",
            "The local operator reviewed audio privacy before model use.",
            confirmed=audio_review_confirmed and transcription_checklist["audio_review_confirmed"],
            source="--confirm-audio-reviewed",
        ),
        _operator_gate_confirmation(
            "reference_reviewed",
            "Expected text privacy was reviewed locally and the reference scan passed.",
            confirmed=(
                reference_review_confirmed
                and transcription_checklist["reference_review_confirmed"]
                and reference_privacy_scan["passed"] is True
                and transcription_checklist["reference_privacy_scan_passed"] is True
            ),
            source="--confirm-reference-reviewed + reference_privacy_scan.passed",
        ),
        _operator_gate_confirmation(
            "quality_reviewed",
            "A human reviewed redacted transcript quality before beta evidence.",
            confirmed=quality_review_confirmed and transcription_checklist["quality_review_confirmed"],
            source="--confirm-quality-reviewed",
        ),
        _operator_gate_confirmation(
            "target_backend_ready_guarded",
            "The target transcription backend was available and --require-target-backend-ready was used.",
            confirmed=target_backend["available"] is True and require_target_backend_ready,
            source="target_backend.available + target_backend_ready_required",
        ),
        _operator_gate_confirmation(
            "preflight_ready",
            "The guarded preflight state was ready for the real model run.",
            confirmed=(
                preflight_readiness["status"] == "ready"
                and preflight_readiness["decision"] == "ready_for_real_transcription"
                and preflight_readiness["ready_for_model_run"] is True
                and preflight_readiness["must_rerun_preflight"] is False
            ),
            source="preflight_readiness",
        ),
        _operator_gate_confirmation(
            "duration_gate_passed",
            "The decoded audio duration stayed inside the configured safe bounds.",
            confirmed=audio["duration_gate"]["enabled"] is True and audio["duration_gate"]["passed"] is True,
            source="audio.duration_gate",
        ),
        _operator_gate_confirmation(
            "credential_presence_recorded",
            "OpenAI credential presence was recorded without storing the API key when required.",
            confirmed=(
                target_backend["name"] != "openai"
                or (
                    credentials["checked"]
                    and credentials["openai_api_key_required"]
                    and credentials["openai_api_key_present"] is True
                    and credentials["records_openai_api_key"] is False
                )
            ),
            source="credentials.openai_api_key_present",
        ),
        _operator_gate_confirmation(
            "transcription_checklist_beta_ready",
            "The transcription checklist marked the real run as beta-ready.",
            confirmed=transcription_checklist["ready_for_beta_evidence"],
            source="transcription_checklist.ready_for_beta_evidence",
        ),
    ]
    missing_confirmations = [item["id"] for item in confirmations if item["confirmed"] is not True]
    preflight_command = real_transcription_command_card["preflight_command_template"]
    real_command = real_transcription_command_card["real_transcription_command_template"]
    audit_command = real_transcription_command_card["audit_command_template"]
    command_templates = (preflight_command, real_command, audit_command)
    command_safe_to_copy = bool(
        real_transcription_command_card["safe_to_share"]
        and real_transcription_command_card["uses_placeholders"]
        and real_transcription_command_card["uses_pip_extra"] is True
        and real_transcription_command_card["python_extra"] in {"whisper", "openai"}
        and isinstance(real_transcription_command_card["pip_command"], str)
        and real_transcription_command_card["preflight_runs_model"] is False
        and real_transcription_command_card["real_transcription_requires_user_audio"] is True
        and real_transcription_command_card["real_transcription_requires_quality_review"] is True
        and real_transcription_command_card["records_audio"] is False
        and real_transcription_command_card["records_audio_path"] is False
        and real_transcription_command_card["records_audio_file_name"] is False
        and real_transcription_command_card["records_transcript_text"] is False
        and real_transcription_command_card["records_expected_text"] is False
        and real_transcription_command_card["records_expected_text_file_name"] is False
        and real_transcription_command_card["records_local_paths"] is False
        and all(isinstance(command, str) and "<pilot-output-dir>" in command for command in command_templates)
        and isinstance(preflight_command, str)
        and "<audio-path>" in preflight_command
        and isinstance(real_command, str)
        and "<audio-path>" in real_command
        and "<expected-text-path>" in real_command
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
        "expected_artifact": "transcription-pilot-report.json",
        "ready_for_beta_audit": ready_for_beta_audit,
        "command_safe_to_copy": command_safe_to_copy,
        "local_operator_required": True,
        "confirmations": confirmations,
        "missing_confirmations": missing_confirmations,
        "missing_confirmation_count": len(missing_confirmations),
        "missing_fields": list(beta_evidence_gap["missing_fields"]),
        "missing_field_count": beta_evidence_gap["missing_count"],
        "preflight_command_template": preflight_command,
        "real_transcription_command_template": real_command,
        "audit_command_template": audit_command,
        "next_action": (
            "Run the strict beta evidence audit before closing this blocker."
            if ready_for_beta_audit
            else beta_evidence_gap["next_action"]
        ),
        "records_audio": False,
        "records_audio_path": False,
        "records_audio_file_name": False,
        "records_transcript_text": False,
        "records_expected_text": False,
        "records_expected_text_file_name": False,
        "records_local_paths": False,
        "records_operator_identity": False,
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


def _format_cli_number(value: float | int) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _build_real_transcription_command_markdown(
    *,
    timestamp: str,
    backend: str,
    target_backend: dict[str, Any],
    credentials: dict[str, Any],
    preflight_readiness: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
    real_transcription_operator_gate: dict[str, Any],
    preflight_command_template: str,
    command_template: str,
    audit_command_template: str,
) -> str:
    python_extra = _real_transcription_python_extra(backend)
    lines = [
        "# Real transcription command",
        "",
        "This artifact is safe to share. It contains placeholders only and does not include local audio paths, audio file names, full transcripts, expected text or secrets.",
        "",
        "## Status",
        "",
        f"- Created at: {timestamp}",
        f"- Backend from current run: {backend}",
        f"- Target backend: {target_backend['name']}",
        f"- Target backend available: {target_backend['available']}",
        f"- Target backend dependencies: {_format_list(target_backend['dependencies'])}",
        f"- Target backend install command: {_format_optional(target_backend['install_command'])}",
        f"- Target backend freedom policy: {_backend_policy_value(target_backend, 'category')}",
        f"- Target backend proprietary: {_backend_policy_value(target_backend, 'proprietary')}",
        f"- Backend post-install check: {target_backend['install_plan']['post_install_check']}",
        f"- Command card uses pip extra: {python_extra is not None}",
        f"- Command card python extra: {_format_optional(python_extra)}",
        f"- Preflight readiness status: {preflight_readiness['status']}",
        f"- Preflight ready for model run: {preflight_readiness['ready_for_model_run']}",
        f"- OpenAI API key check: {credentials['status']}",
        f"- OpenAI API key required: {credentials['openai_api_key_required']}",
        f"- OpenAI API key present: {_format_optional(credentials['openai_api_key_present'])}",
        f"- Records OpenAI API key: {credentials['records_openai_api_key']}",
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
        f"- Operator gate decision: {real_transcription_operator_gate['decision']}",
        f"- Operator gate ready for beta audit: {real_transcription_operator_gate['ready_for_beta_audit']}",
        f"- Operator gate command safe to copy: {real_transcription_operator_gate['command_safe_to_copy']}",
        f"- Operator gate missing confirmations: {real_transcription_operator_gate['missing_confirmation_count']}",
        "",
        "## 1. Preflight MP3/WAV/FLAC",
        "",
        "Run this locally with your reviewed audio before any real model call:",
        "",
        "```powershell",
        preflight_command_template,
        "```",
        "",
        "## 2. Real Transcription",
        "",
        "Run this only after the preflight reports `preflight_readiness.status=ready`:",
        "",
        "```powershell",
        command_template,
        "```",
        "",
        "## 3. Evidence Audit",
        "",
        "Audit the generated report before treating it as beta evidence:",
        "",
        "```powershell",
        audit_command_template,
        "```",
        "",
        "## Local Replacements",
        "",
        "- Replace `<audio-path>` with a reviewed, non-sensitive local MP3/WAV/FLAC path.",
        "- Replace `<expected-text-path>` with a reviewed, non-sensitive local reference text file.",
        "- Replace `<pilot-output-dir>` with the output folder that contains `transcription-pilot-report.json`.",
        "- Keep local paths, audio file names, transcript text, expected text and API keys out of public reports.",
        "",
        "## Required Confirmations",
        "",
        "- `--audio-non-sensitive` means the audio is safe to process locally.",
        "- `--confirm-audio-reviewed` means a human reviewed audio privacy before model use.",
        "- `--confirm-reference-reviewed` means a human reviewed expected text privacy before scoring.",
        "- `--confirm-quality-reviewed` means a human reviewed redacted quality metrics before beta evidence.",
        "- `--require-target-backend-ready` must stay enabled for beta evidence.",
        "- For OpenAI, keep `--require-openai-api-key` and store the key only in the local environment.",
        "",
        "## Beta Evidence Gap",
        "",
        f"- Blocker: `{beta_evidence_gap['blocker']}`",
        f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
        f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
        "",
        "## Operator Gate",
        "",
        f"- Decision: `{real_transcription_operator_gate['decision']}`",
        f"- Ready for beta audit: `{real_transcription_operator_gate['ready_for_beta_audit']}`",
        f"- Command safe to copy: `{real_transcription_operator_gate['command_safe_to_copy']}`",
        f"- Missing confirmations: {_format_list(real_transcription_operator_gate['missing_confirmations'])}",
        f"- Missing fields: {_format_list(real_transcription_operator_gate['missing_fields'])}",
        f"- Next action: {real_transcription_operator_gate['next_action']}",
        "",
        "## Privacy Contract",
        "",
        "- Records audio bytes: `False`",
        "- Records transcript text: `False`",
        "- Records expected text: `False`",
        "- Records audio file name: `False`",
        "- Records local paths: `False`",
        "- Records OpenAI API key: `False`",
        "",
    ]
    return "\n".join(lines)


def _build_real_transcription_next_step_markdown(
    *,
    timestamp: str,
    backend: str,
    target_backend: dict[str, Any],
    model: str | None,
    preflight_only: bool,
    real_transcription: bool,
    require_target_backend_ready: bool,
    credentials: dict[str, Any],
    timeout_seconds: float | None,
    audio: dict[str, Any],
    quality: dict[str, Any],
    reference_privacy_scan: dict[str, Any],
    transcription_checklist: dict[str, Any],
    preflight_decision: dict[str, Any],
    preflight_readiness: dict[str, Any],
    beta_evidence_gap: dict[str, Any],
    real_transcription_operator_gate: dict[str, Any],
    preflight_command_template: str,
    command_template: str,
    audit_command_template: str,
    command_path: Path,
    checklist_path: Path,
) -> str:
    lines = [
        "# Real transcription next step",
        "",
        "This artifact is safe to share: it uses placeholders and does not include local audio paths, user audio file names, full transcripts or expected text.",
        "",
        "## Status",
        "",
        f"- Created at: {timestamp}",
        f"- Backend from current run: {backend}",
        f"- Target backend available: {target_backend['available']}",
        f"- Target backend dependencies: {_format_list(target_backend['dependencies'])}",
        f"- Target backend reason: {_format_optional(target_backend['reason'])}",
        f"- Target backend freedom policy: {_backend_policy_value(target_backend, 'category')}",
        f"- Target backend proprietary: {_backend_policy_value(target_backend, 'proprietary')}",
        f"- Target backend network required: {_backend_policy_value(target_backend, 'network_required')}",
        f"- Target backend install command: {_format_optional(target_backend['install_command'])}",
        f"- Target backend post-install check: {target_backend['install_plan']['post_install_check']}",
        f"- OpenAI API key check: {credentials['status']}",
        f"- OpenAI API key required: {credentials['openai_api_key_required']}",
        f"- OpenAI API key present: {_format_optional(credentials['openai_api_key_present'])}",
        f"- Records OpenAI API key: {credentials['records_openai_api_key']}",
        f"- Model from current run: {_format_optional(model)}",
        f"- Preflight only: {preflight_only}",
        f"- Real transcription requested: {real_transcription}",
        f"- Target backend readiness required: {require_target_backend_ready}",
        f"- Transcription timeout seconds: {_format_optional(timeout_seconds)}",
        f"- Audio file name redacted: {audio['audio_file_name_redacted']}",
        f"- Audio extension: {audio['audio_file_extension'] or 'none'}",
        f"- Source format: {_format_optional(audio['source_format'])}",
        f"- Audio decoded: {audio['decoded']}",
        f"- Duration seconds: {_format_optional(audio['duration_seconds'])}",
        f"- Duration gate passed: {_format_optional(audio['duration_gate']['passed'])}",
        f"- Reference provided: {quality['enabled']}",
        f"- Reference privacy scan passed: {_format_optional(reference_privacy_scan['passed'])}",
        f"- Preflight decision: {preflight_decision['decision']}",
        f"- Preflight readiness status: {preflight_readiness['status']}",
        f"- Preflight ready for model run: {preflight_readiness['ready_for_model_run']}",
        f"- Preflight must rerun: {preflight_readiness['must_rerun_preflight']}",
        f"- Preflight next action: {preflight_decision['next_action']}",
        f"- Ready for real transcription: {transcription_checklist['ready_for_real_transcription']}",
        f"- Ready for beta evidence: {transcription_checklist['ready_for_beta_evidence']}",
        f"- Beta evidence gap ready: {beta_evidence_gap['ready_for_beta_evidence']}",
        f"- Beta evidence gap missing count: {beta_evidence_gap['missing_count']}",
        f"- Beta evidence gap next action: {beta_evidence_gap['next_action']}",
        f"- Operator gate decision: {real_transcription_operator_gate['decision']}",
        f"- Operator gate ready for beta audit: {real_transcription_operator_gate['ready_for_beta_audit']}",
        f"- Operator gate command safe to copy: {real_transcription_operator_gate['command_safe_to_copy']}",
        f"- Operator gate missing confirmations: {real_transcription_operator_gate['missing_confirmation_count']}",
        f"- Operator gate missing fields: {real_transcription_operator_gate['missing_field_count']}",
        f"- Review checklist: {checklist_path.name}",
        f"- Command card: {command_path.name}",
        "",
        "## Command Template",
        "",
        "Replace placeholders locally after confirming the audio and expected text are non-sensitive:",
        "",
        "```powershell",
        command_template,
        "```",
        "",
        "## Preflight Rerun Command",
        "",
        "Run this sanitized check until `preflight_readiness.status=ready`:",
        "",
        "```powershell",
        preflight_command_template,
        "```",
        "",
        "## Evidence Audit Command",
        "",
        "After the real run, audit the output directory before treating it as beta evidence:",
        "",
        "```powershell",
        audit_command_template,
        "```",
        "",
        "## Beta Evidence Gap",
        "",
        f"- Blocker: `{beta_evidence_gap['blocker']}`",
        f"- Ready for beta evidence: `{beta_evidence_gap['ready_for_beta_evidence']}`",
        f"- Missing fields: {_format_list(beta_evidence_gap['missing_fields'])}",
        "",
        "## Operator Gate",
        "",
        f"- Decision: `{real_transcription_operator_gate['decision']}`",
        f"- Ready for beta audit: `{real_transcription_operator_gate['ready_for_beta_audit']}`",
        f"- Command safe to copy: `{real_transcription_operator_gate['command_safe_to_copy']}`",
        f"- Missing confirmations: {_format_list(real_transcription_operator_gate['missing_confirmations'])}",
        f"- Missing fields: {_format_list(real_transcription_operator_gate['missing_fields'])}",
        f"- Next action: {real_transcription_operator_gate['next_action']}",
        "",
        "## Required Review",
        "",
        "- Replace `<audio-path>` locally; do not paste the real path into public findings.",
        "- Replace `<expected-text-path>` locally or use `--expected-text` only with public/non-sensitive text.",
        "- If the backend is unavailable, install only the optional extra shown in `target_backend.install_plan.pip_command`.",
        "- Run the `target_backend.install_plan.post_install_check` command before removing `--preflight-only`.",
        "- For OpenAI, set `OPENAI_API_KEY` locally and keep `--require-openai-api-key`; never paste the key into artifacts.",
        "- Confirm `audio.audio_file_name_redacted=true` in `transcription-pilot-report.json`.",
        "- Confirm `target_backend.available=true` before running without `--preflight-only`.",
        "- Confirm `transcription_checklist.records_audio_file_name=false`.",
        "- Confirm `transcription_checklist.records_expected_text_file_name=false`.",
        "- Confirm `preflight_decision.decision=ready_for_real_transcription` or rerun the preflight after installing the backend.",
        "- Confirm `reference_privacy_scan.passed=true` before accepting beta evidence.",
        "- Confirm `transcription_checklist.ready_for_beta_evidence=true` only after human quality review.",
        "- Confirm `real_transcription_operator_gate.ready_for_beta_audit=true` before closing beta evidence.",
        "- Confirm `real_transcription_operator_gate.command_safe_to_copy=true` before sharing commands.",
        "- Confirm `real_transcription_operator_gate.missing_confirmation_count=0` and `missing_field_count=0`.",
        "",
    ]
    return "\n".join(lines)


def _build_transcription_checklist_markdown(
    *,
    timestamp: str,
    backend: str,
    transcription_checklist: dict[str, Any],
    real_transcription_operator_gate: dict[str, Any],
) -> str:
    lines = [
        "# Transcription review checklist",
        "",
        f"- Created at: {timestamp}",
        f"- Backend: {backend}",
        f"- Records audio path: {transcription_checklist['records_audio_path']}",
        f"- Records audio file name: {transcription_checklist['records_audio_file_name']}",
        f"- Records transcript text: {transcription_checklist['records_transcript_text']}",
        f"- Records expected text: {transcription_checklist['records_expected_text']}",
        f"- Records expected text file name: {transcription_checklist['records_expected_text_file_name']}",
        f"- Records OpenAI API key: {transcription_checklist['records_openai_api_key']}",
        f"- Redacts transcript text: {transcription_checklist['redacts_transcript_text']}",
        f"- Redacts expected text: {transcription_checklist['redacts_expected_text']}",
        f"- OpenAI API key checked: {transcription_checklist['openai_api_key_checked']}",
        f"- OpenAI API key required: {transcription_checklist['openai_api_key_required']}",
        f"- OpenAI API key present: {_format_optional(transcription_checklist['openai_api_key_present'])}",
        f"- Audio review confirmed: {transcription_checklist['audio_review_confirmed']}",
        f"- Reference review confirmed: {transcription_checklist['reference_review_confirmed']}",
        f"- Reference privacy scan passed: {_format_optional(transcription_checklist['reference_privacy_scan_passed'])}",
        f"- Reference privacy risk count: {transcription_checklist['reference_privacy_risk_count']}",
        f"- Reference privacy risk types: {_format_list(transcription_checklist['reference_privacy_risk_types'])}",
        f"- Quality review confirmed: {transcription_checklist['quality_review_confirmed']}",
        f"- Ready for real transcription: {transcription_checklist['ready_for_real_transcription']}",
        f"- Ready for beta evidence: {transcription_checklist['ready_for_beta_evidence']}",
        f"- Operator gate decision: {real_transcription_operator_gate['decision']}",
        f"- Operator gate ready for beta audit: {real_transcription_operator_gate['ready_for_beta_audit']}",
        f"- Operator gate command safe to copy: {real_transcription_operator_gate['command_safe_to_copy']}",
        f"- Operator gate missing confirmations: {real_transcription_operator_gate['missing_confirmation_count']}",
        f"- Operator gate missing fields: {real_transcription_operator_gate['missing_field_count']}",
        "",
        "## Before Transcription",
        "",
    ]
    for item in transcription_checklist["before_transcription"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## After Transcription",
            "",
        ]
    )
    for item in transcription_checklist["after_transcription"]:
        lines.append(_format_checklist_item(item))
    lines.extend(
        [
            "",
            "## Real Transcription Operator Gate",
            "",
            f"- Decision: `{real_transcription_operator_gate['decision']}`",
            f"- Ready for beta audit: `{real_transcription_operator_gate['ready_for_beta_audit']}`",
            f"- Command safe to copy: `{real_transcription_operator_gate['command_safe_to_copy']}`",
            f"- Missing confirmations: {_format_list(real_transcription_operator_gate['missing_confirmations'])}",
            f"- Missing fields: {_format_list(real_transcription_operator_gate['missing_fields'])}",
            f"- Next action: {real_transcription_operator_gate['next_action']}",
            "",
            "### Confirmations",
            "",
        ]
    )
    for item in real_transcription_operator_gate["confirmations"]:
        marker = "x" if item["confirmed"] is True else " "
        lines.append(
            f"- [{marker}] `{item['id']}` confirmed={str(item['confirmed']).lower()} "
            f"source={item['source']} - {item['instruction']}"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Do not write private audio paths, full transcripts or full expected text in shared findings.",
            "- Do not write OpenAI API keys or other secrets in shared findings.",
            "- Use real-transcription-next-step.md for a sanitized command template after preflight.",
            "- A preflight checklist is preparation only; beta evidence requires a real backend and quality gate.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_checklist_item(item: dict[str, Any]) -> str:
    marker = "x" if item["ok"] is True else " "
    state = "unknown" if item["ok"] is None else str(item["ok"]).lower()
    return f"- [{marker}] `{item['id']}` ok={state} required={item['required']} - {item['instruction']}"


def _pilot_notes(real_transcription: bool, preflight_only: bool) -> str:
    if preflight_only:
        return "Preflight only decoded a user-provided non-sensitive audio file without running transcription."
    if real_transcription:
        return "Real transcription was requested with a user-provided non-sensitive audio file."
    return "Safe dry-run with synthetic audio and the null transcription backend."


def _format_optional(value: object | None) -> str:
    return "none" if value in (None, "") else str(value)


def _backend_policy_value(target_backend: dict[str, Any], key: str) -> object:
    policy = target_backend.get("freedom_policy")
    if not isinstance(policy, dict):
        return "unknown"
    value = policy.get(key)
    return "unknown" if value is None else value


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit transcription pilot")
    print(f"Backend: {report['backend']}")
    print(f"Target backend available: {report['target_backend']['available']}")
    print(f"Target backend install command: {_format_optional(report['target_backend']['install_command'])}")
    print(f"Transcription timeout seconds: {_format_optional(report['transcription_timeout_seconds'])}")
    print(f"OpenAI API key check: {report['credentials']['status']}")
    print(f"OpenAI API key present: {_format_optional(report['credentials']['openai_api_key_present'])}")
    print(f"Records OpenAI API key: {report['credentials']['records_openai_api_key']}")
    print(f"Preflight only: {report['preflight_only']}")
    print(f"Real transcription requested: {report['real_transcription_requested']}")
    print(f"Generated synthetic audio: {report['generated_synthetic_audio']}")
    print(f"Audio review confirmed: {report['audio_review_confirmed']}")
    print(f"Reference review confirmed: {report['reference_review_confirmed']}")
    print(f"Reference privacy scan passed: {report['reference_privacy_scan']['passed']}")
    print(f"Reference privacy risk count: {report['reference_privacy_scan']['risk_count']}")
    print(f"Quality review confirmed: {report['quality_review_confirmed']}")
    print(f"Preflight decision: {report['preflight_decision']['decision']}")
    print(f"Passed: {report['passed']}")
    print(f"Transcript characters: {report['transcript']['text_characters'] if report['transcript'] else 0}")
    if report["quality"]["enabled"]:
        print(f"Word accuracy: {report['quality']['word_accuracy']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
