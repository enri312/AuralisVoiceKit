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
from pathlib import Path
import platform
import sys
from typing import Any

from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceKitConfig,
    generate_synthetic_audio_chunks,
    normalize_pcm16,
    read_audio_as_chunk,
    write_wav,
)
from auralis_voicekit.exceptions import AudioSourceError, BackendNotAvailable, TranscriptionError


def run_transcription_pilot(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    audio: str | Path | None = None,
    backend: str = "null",
    model: str | None = None,
    language: str = "es",
    prompt: str | None = None,
    ffmpeg: str = "ffmpeg",
    normalize: bool = False,
    real_transcription: bool = False,
    audio_confirmed_non_sensitive: bool = False,
    include_transcript_hash: bool = False,
    duration_seconds: float = 1.0,
    sample_rate: int = 16_000,
) -> dict[str, Any]:
    """Run a transcription pilot and write sanitized artifacts."""

    _validate_real_transcription_flags(
        audio=audio,
        backend=backend,
        real_transcription=real_transcription,
        audio_confirmed_non_sensitive=audio_confirmed_non_sensitive,
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

    config = VoiceKitConfig(
        transcription_backend=backend,
        transcription_model=model or "auto",
        transcription_prompt=prompt,
        language=language,
        privacy_mode=True,
    )
    result = None
    error = None
    try:
        chunk = read_audio_as_chunk(
            str(source_audio_path),
            ffmpeg_executable=ffmpeg,
            sample_rate=sample_rate,
            channels=1,
        )
        if normalize:
            chunk = normalize_pcm16(chunk)
        result = AuralisVoiceKit(config).transcribe(chunk)
    except (AudioSourceError, BackendNotAvailable, TranscriptionError, ValueError) as exc:
        chunk = None
        error = str(exc)

    passed = error is None
    transcript_text = result.text if result is not None else ""
    transcript_report = _transcript_report(
        transcript_text,
        include_hash=include_transcript_hash,
    )
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
    audio_payload = {
        "generated_synthetic_audio": generated_synthetic_audio,
        "audio_file_name": source_audio_path.name,
        "audio_file_extension": source_audio_path.suffix.lower(),
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "duration_seconds": chunk.duration_seconds if chunk is not None else None,
        "sample_rate": chunk.format.sample_rate if chunk is not None else sample_rate,
        "channels": chunk.format.channels if chunk is not None else 1,
        "bytes": len(chunk.data) if chunk is not None else None,
    }

    findings_path = output / "transcription-pilot-findings.md"
    report_path = output / "transcription-pilot-report.json"
    findings = _build_findings_markdown(
        timestamp=timestamp,
        backend=backend,
        real_transcription=real_transcription,
        passed=passed,
        error=error,
        audio=audio_payload,
        transcript=result_payload,
        report_path=report_path,
    )

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": platform.system(),
        "backend": backend,
        "model": model or "auto",
        "language": language,
        "real_transcription_requested": real_transcription,
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "generated_synthetic_audio": generated_synthetic_audio,
        "normalize": normalize,
        "passed": passed,
        "error": error,
        "audio": audio_payload,
        "transcript": result_payload,
        "notes": _pilot_notes(real_transcription),
        "artifacts": {
            "pilot_findings": str(findings_path),
            "transcription_pilot_report": str(report_path),
        },
    }
    if generated_synthetic_audio:
        report["artifacts"]["synthetic_audio"] = str(source_audio_path)

    findings_path.write_text(findings, encoding="utf-8")
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
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for compressed audio")
    parser.add_argument("--normalize", action="store_true", help="normalize audio before transcription")
    parser.add_argument(
        "--real-transcription",
        action="store_true",
        help="allow a real transcription backend; requires --audio and --audio-non-sensitive",
    )
    parser.add_argument(
        "--audio-non-sensitive",
        action="store_true",
        help="confirm the supplied audio is safe to process and summarize",
    )
    parser.add_argument(
        "--include-transcript-hash",
        action="store_true",
        help="include sha256 of the transcript text without storing the text",
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
            ffmpeg=args.ffmpeg,
            normalize=args.normalize,
            real_transcription=args.real_transcription,
            audio_confirmed_non_sensitive=args.audio_non_sensitive,
            include_transcript_hash=args.include_transcript_hash,
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
    real_transcription: bool,
    audio_confirmed_non_sensitive: bool,
) -> None:
    if backend != "null" and not real_transcription:
        raise ValueError("Real transcription backends require --real-transcription.")
    if real_transcription and backend == "null":
        raise ValueError("--real-transcription requires --backend whisper or --backend openai.")
    if real_transcription and audio is None:
        raise ValueError("--real-transcription requires --audio with a user-provided file.")
    if real_transcription and not audio_confirmed_non_sensitive:
        raise ValueError("--real-transcription requires --audio-non-sensitive.")
    if audio_confirmed_non_sensitive and audio is None:
        raise ValueError("--audio-non-sensitive is only valid with --audio.")


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


def _transcript_report(text: str, *, include_hash: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "text_redacted": True,
        "text_characters": len(text),
        "text_words_estimate": len(text.split()) if text else 0,
    }
    if include_hash:
        payload["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return payload


def _build_findings_markdown(
    *,
    timestamp: str,
    backend: str,
    real_transcription: bool,
    passed: bool,
    error: str | None,
    audio: dict[str, Any],
    transcript: dict[str, Any] | None,
    report_path: Path,
) -> str:
    transcript_characters = transcript.get("text_characters") if transcript is not None else 0
    lines = [
        "# Transcription pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- Backend: {backend}",
        f"- Real transcription requested: {real_transcription}",
        f"- Passed: {passed}",
        f"- Audio file name: {audio['audio_file_name']}",
        f"- Audio extension: {audio['audio_file_extension'] or 'none'}",
        f"- Generated synthetic audio: {audio['generated_synthetic_audio']}",
        f"- Audio confirmed non-sensitive: {audio['audio_confirmed_non_sensitive']}",
        f"- Duration seconds: {_format_optional(audio['duration_seconds'])}",
        f"- Transcript characters: {transcript_characters}",
        f"- Report: {report_path.name}",
        "",
        "## Privacy",
        "",
        "- The full transcript is not written to findings or JSON artifacts.",
        "- The full audio path is not written to findings.",
        "- Prompt-like metadata is redacted.",
        "",
        "## Result",
        "",
        f"- Error: {_format_optional(error)}",
        "",
        "## Follow-up",
        "",
    ]
    if real_transcription:
        lines.append("- Review transcript quality manually without attaching sensitive audio or text to public reports.")
    else:
        lines.append("- Re-run with --real-transcription --audio PATH --audio-non-sensitive and backend whisper/openai for a real pilot.")
    lines.append("- Record backend/model, audio type and high-level quality findings in PILOT_FINDINGS.md.")
    lines.append("")
    return "\n".join(lines)


def _pilot_notes(real_transcription: bool) -> str:
    if real_transcription:
        return "Real transcription was requested with a user-provided non-sensitive audio file."
    return "Safe dry-run with synthetic audio and the null transcription backend."


def _format_optional(value: object | None) -> str:
    return "none" if value in (None, "") else str(value)


def _slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "z")


def _print_report(report: dict[str, Any]) -> None:
    print("AuralisVoiceKit transcription pilot")
    print(f"Backend: {report['backend']}")
    print(f"Real transcription requested: {report['real_transcription_requested']}")
    print(f"Generated synthetic audio: {report['generated_synthetic_audio']}")
    print(f"Passed: {report['passed']}")
    print(f"Transcript characters: {report['transcript']['text_characters'] if report['transcript'] else 0}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
