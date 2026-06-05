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
import unicodedata

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
    preflight_only: bool = False,
    real_transcription: bool = False,
    audio_confirmed_non_sensitive: bool = False,
    include_transcript_hash: bool = False,
    expected_text: str | None = None,
    expected_text_file: str | Path | None = None,
    min_word_accuracy: float | None = None,
    duration_seconds: float = 1.0,
    sample_rate: int = 16_000,
) -> dict[str, Any]:
    """Run a transcription pilot and write sanitized artifacts."""

    _validate_quality_flags(
        expected_text=expected_text,
        expected_text_file=expected_text_file,
        min_word_accuracy=min_word_accuracy,
        preflight_only=preflight_only,
    )
    _validate_real_transcription_flags(
        audio=audio,
        backend=backend,
        preflight_only=preflight_only,
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

    expected_reference = _load_expected_reference(expected_text, expected_text_file)
    config = VoiceKitConfig(
        transcription_backend=backend,
        transcription_model=model or "auto",
        transcription_prompt=prompt,
        language=language,
        privacy_mode=True,
    )
    result = None
    error = None
    chunk = None
    try:
        chunk = read_audio_as_chunk(
            str(source_audio_path),
            ffmpeg_executable=ffmpeg,
            sample_rate=sample_rate,
            channels=1,
        )
        if normalize:
            chunk = normalize_pcm16(chunk)
        if not preflight_only:
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
    audio_payload = {
        "generated_synthetic_audio": generated_synthetic_audio,
        "audio_file_name": source_audio_path.name,
        "audio_file_extension": source_audio_path.suffix.lower(),
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "decoded": chunk is not None,
        "decoder": audio_decoder,
        "source_format": audio_source_format,
        "normalized": bool(normalize and chunk is not None),
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
        preflight_only=preflight_only,
        real_transcription=real_transcription,
        passed=passed,
        error=error,
        audio=audio_payload,
        transcript=result_payload,
        quality=quality_report,
        report_path=report_path,
    )

    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": platform.system(),
        "backend": backend,
        "model": model or "auto",
        "language": language,
        "preflight_only": preflight_only,
        "real_transcription_requested": real_transcription,
        "audio_confirmed_non_sensitive": audio_confirmed_non_sensitive,
        "generated_synthetic_audio": generated_synthetic_audio,
        "normalize": normalize,
        "passed": passed,
        "error": error,
        "audio": audio_payload,
        "transcript": result_payload,
        "quality": quality_report,
        "notes": _pilot_notes(real_transcription, preflight_only),
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
        "--audio-non-sensitive",
        action="store_true",
        help="confirm the supplied audio is safe to process and summarize",
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
        help="optional file containing reference text; only the file name is reported",
    )
    parser.add_argument(
        "--min-word-accuracy",
        type=float,
        help="optional pass threshold from 0.0 to 1.0 for reference text quality",
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
            preflight_only=args.preflight_only,
            real_transcription=args.real_transcription,
            audio_confirmed_non_sensitive=args.audio_non_sensitive,
            include_transcript_hash=args.include_transcript_hash,
            expected_text=args.expected_text,
            expected_text_file=args.expected_text_file,
            min_word_accuracy=args.min_word_accuracy,
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


def _validate_quality_flags(
    *,
    expected_text: str | None,
    expected_text_file: str | Path | None,
    min_word_accuracy: float | None,
    preflight_only: bool,
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
        file_name = path.name
    else:
        return None

    if not text.strip():
        raise ValueError("Expected text must not be empty.")
    return {
        "text": text,
        "source": source,
        "file_name": file_name,
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


def _build_findings_markdown(
    *,
    timestamp: str,
    backend: str,
    preflight_only: bool,
    real_transcription: bool,
    passed: bool,
    error: str | None,
    audio: dict[str, Any],
    transcript: dict[str, Any] | None,
    quality: dict[str, Any],
    report_path: Path,
) -> str:
    transcript_characters = transcript.get("text_characters") if transcript is not None else 0
    lines = [
        "# Transcription pilot findings",
        "",
        f"- Created at: {timestamp}",
        f"- Backend: {backend}",
        f"- Preflight only: {preflight_only}",
        f"- Real transcription requested: {real_transcription}",
        f"- Passed: {passed}",
        f"- Audio file name: {audio['audio_file_name']}",
        f"- Audio extension: {audio['audio_file_extension'] or 'none'}",
        f"- Generated synthetic audio: {audio['generated_synthetic_audio']}",
        f"- Audio confirmed non-sensitive: {audio['audio_confirmed_non_sensitive']}",
        f"- Audio decode passed: {audio['decoded']}",
        f"- Decoder: {_format_optional(audio['decoder'])}",
        f"- Source format: {_format_optional(audio['source_format'])}",
        f"- Normalized: {audio['normalized']}",
        f"- Duration seconds: {_format_optional(audio['duration_seconds'])}",
        f"- Transcript characters: {transcript_characters}",
        f"- Quality reference provided: {quality['enabled']}",
        f"- Quality gate passed: {_format_optional(quality['passed'])}",
        f"- Report: {report_path.name}",
        "",
        "## Privacy",
        "",
        "- The full transcript is not written to findings or JSON artifacts.",
        "- The full audio path is not written to findings.",
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


def _pilot_notes(real_transcription: bool, preflight_only: bool) -> str:
    if preflight_only:
        return "Preflight only decoded a user-provided non-sensitive audio file without running transcription."
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
    print(f"Preflight only: {report['preflight_only']}")
    print(f"Real transcription requested: {report['real_transcription_requested']}")
    print(f"Generated synthetic audio: {report['generated_synthetic_audio']}")
    print(f"Passed: {report['passed']}")
    print(f"Transcript characters: {report['transcript']['text_characters'] if report['transcript'] else 0}")
    if report["quality"]["enabled"]:
        print(f"Word accuracy: {report['quality']['word_accuracy']}")
    print("Artifacts:")
    for name, path in report["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
