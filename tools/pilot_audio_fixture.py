"""Generate public synthetic audio fixtures for transcription pilots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
from typing import Any

from auralis_voicekit import (
    generate_synthetic_audio_chunks,
    read_audio_as_chunk,
    resolve_ffmpeg_executable,
    write_wav,
)


SUPPORTED_FORMATS = ("wav", "mp3", "flac")
MP3_FIXTURE_NAME = "pilot-sample.mp3"
ENCODER_ARGS = {
    "mp3": ("-codec:a", "libmp3lame", "-q:a", "4"),
    "flac": ("-codec:a", "flac", "-compression_level", "5"),
}


def generate_pilot_audio_fixture(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = None,
    formats: tuple[str, ...] = ("wav", "mp3"),
    duration_seconds: float = 1.0,
    sample_rate: int = 16_000,
    ffmpeg: str = "ffmpeg",
) -> dict[str, Any]:
    """Generate a non-sensitive synthetic fixture and write sanitized artifacts."""

    requested_formats = _normalize_formats(formats)
    _validate_audio_shape(duration_seconds=duration_seconds, sample_rate=sample_rate)

    workspace = Path(root).resolve()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output = Path(output_dir) if output_dir is not None else workspace / "pilot_runs" / "transcription" / "fixture"
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    chunks = generate_synthetic_audio_chunks(
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=1,
        chunk_duration_ms=100,
    )
    source_wav = output / "pilot-sample.wav"
    write_wav(str(source_wav), chunks)

    needs_ffmpeg = any(format_name != "wav" for format_name in requested_formats)
    ffmpeg_path = resolve_ffmpeg_executable(ffmpeg) if needs_ffmpeg else None
    files: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {"source_wav": str(source_wav)}

    if "wav" in requested_formats:
        files.append(_file_report("wav", source_wav, generated=True, decoded=True, duration_seconds=duration_seconds))
        artifacts["wav"] = str(source_wav)

    for format_name in requested_formats:
        if format_name == "wav":
            continue
        file_name = MP3_FIXTURE_NAME if format_name == "mp3" else f"pilot-sample.{format_name}"
        output_path = output / file_name
        entry = _encode_fixture(
            source_wav=source_wav,
            output_path=output_path,
            format_name=format_name,
            ffmpeg_path=ffmpeg_path,
            sample_rate=sample_rate,
        )
        files.append(entry)
        if entry["passed"]:
            artifacts[format_name] = str(output_path)

    findings_path = output / "pilot-audio-fixture-findings.md"
    report_path = output / "pilot-audio-fixture-report.json"
    report: dict[str, Any] = {
        "project": "AuralisVoiceKit",
        "created_at": timestamp,
        "system": platform.system(),
        "generated_public_fixture": True,
        "contains_private_audio": False,
        "usable_as_beta_evidence": False,
        "formats_requested": list(requested_formats),
        "duration_seconds": duration_seconds,
        "sample_rate": sample_rate,
        "ffmpeg": {
            "requested": needs_ffmpeg,
            "available": ffmpeg_path is not None,
            "executable_name": Path(ffmpeg_path).name if ffmpeg_path is not None else None,
        },
        "files": files,
        "passed": all(file_report["passed"] for file_report in files),
        "artifacts": {
            **artifacts,
            "fixture_findings": str(findings_path),
            "fixture_report": str(report_path),
        },
        "next_step": (
            "Use the generated MP3 for a local ffmpeg preflight, then replace it with "
            "your own non-sensitive MP3 for real beta evidence."
        ),
    }

    findings_path.write_text(_build_findings_markdown(report), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate public synthetic audio fixtures for pilot preflights.")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output-dir", help="directory for generated fixtures")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=SUPPORTED_FORMATS,
        help="format to generate; may be passed more than once (default: wav and mp3)",
    )
    parser.add_argument("--duration", type=float, default=1.0, help="synthetic fixture duration in seconds")
    parser.add_argument("--sample-rate", type=int, default=16000, help="synthetic fixture sample rate")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for compressed fixtures")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    try:
        report = generate_pilot_audio_fixture(
            root=args.root,
            output_dir=args.output_dir,
            formats=tuple(args.formats) if args.formats else ("wav", "mp3"),
            duration_seconds=args.duration,
            sample_rate=args.sample_rate,
            ffmpeg=args.ffmpeg,
        )
    except ValueError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"Error: {exc}")
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Pilot fixture passed: {report['passed']}")
        print(f"Generated public fixture: {report['generated_public_fixture']}")
        print(f"Beta evidence: {report['usable_as_beta_evidence']}")
        for file_report in report["files"]:
            status = "ok" if file_report["passed"] else "failed"
            print(f"- {file_report['file_name']}: {status}")
    return 0 if report["passed"] else 1


def _normalize_formats(formats: tuple[str, ...]) -> tuple[str, ...]:
    if not formats:
        raise ValueError("At least one --format must be requested.")
    normalized: list[str] = []
    for format_name in formats:
        clean = format_name.lower().lstrip(".")
        if clean not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported fixture format: {format_name}.")
        if clean not in normalized:
            normalized.append(clean)
    return tuple(normalized)


def _validate_audio_shape(*, duration_seconds: float, sample_rate: int) -> None:
    if duration_seconds <= 0:
        raise ValueError("--duration must be greater than 0.")
    if sample_rate <= 0:
        raise ValueError("--sample-rate must be greater than 0.")


def _encode_fixture(
    *,
    source_wav: Path,
    output_path: Path,
    format_name: str,
    ffmpeg_path: str | None,
    sample_rate: int,
) -> dict[str, Any]:
    if ffmpeg_path is None:
        return {
            "format": format_name,
            "file_name": output_path.name,
            "passed": False,
            "generated": False,
            "decoded": False,
            "error": "ffmpeg was not found; install ffmpeg or pass --ffmpeg.",
        }

    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_wav),
        *ENCODER_ARGS[format_name],
        str(output_path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True)
    if completed.returncode != 0:
        fallback = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source_wav),
            str(output_path),
        ]
        completed = subprocess.run(fallback, check=False, capture_output=True)
    if completed.returncode != 0:
        return {
            "format": format_name,
            "file_name": output_path.name,
            "passed": False,
            "generated": False,
            "decoded": False,
            "error": completed.stderr.decode("utf-8", "replace").strip() or "ffmpeg encode failed.",
        }

    try:
        decoded = read_audio_as_chunk(
            str(output_path),
            ffmpeg_executable=ffmpeg_path,
            sample_rate=sample_rate,
            channels=1,
        )
    except Exception as exc:  # noqa: BLE001 - converted into a public-safe report entry.
        return {
            "format": format_name,
            "file_name": output_path.name,
            "passed": False,
            "generated": True,
            "decoded": False,
            "bytes": output_path.stat().st_size if output_path.exists() else None,
            "error": str(exc),
        }

    return _file_report(
        format_name,
        output_path,
        generated=True,
        decoded=True,
        duration_seconds=decoded.duration_seconds,
    )


def _file_report(
    format_name: str,
    path: Path,
    *,
    generated: bool,
    decoded: bool,
    duration_seconds: float | None,
) -> dict[str, Any]:
    return {
        "format": format_name,
        "file_name": path.name,
        "file_extension": path.suffix.lower(),
        "passed": path.exists() and path.stat().st_size > 0 and (decoded or format_name == "wav"),
        "generated": generated,
        "decoded": decoded,
        "duration_seconds": round(duration_seconds, 6) if duration_seconds is not None else None,
        "bytes": path.stat().st_size if path.exists() else None,
        "error": None,
    }


def _build_findings_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Pilot audio fixture findings",
        "",
        "This artifact uses generated synthetic audio only. It does not close beta evidence blockers.",
        "",
        f"- Project: `{report['project']}`",
        f"- System: `{report['system']}`",
        f"- Generated public fixture: `{str(report['generated_public_fixture']).lower()}`",
        f"- Contains private audio: `{str(report['contains_private_audio']).lower()}`",
        f"- Usable as beta evidence: `{str(report['usable_as_beta_evidence']).lower()}`",
        f"- Sample rate: `{report['sample_rate']}`",
        f"- Duration seconds: `{report['duration_seconds']}`",
        f"- ffmpeg requested: `{str(report['ffmpeg']['requested']).lower()}`",
        f"- ffmpeg available: `{str(report['ffmpeg']['available']).lower()}`",
        "",
        "## Files",
        "",
    ]
    for file_report in report["files"]:
        lines.extend(
            [
                f"- `{file_report['file_name']}`",
                f"  - Format: `{file_report['format']}`",
                f"  - Passed: `{str(file_report['passed']).lower()}`",
                f"  - Decoded: `{str(file_report['decoded']).lower()}`",
                f"  - Duration seconds: `{file_report['duration_seconds']}`",
            ]
        )
        if file_report["error"]:
            lines.append(f"  - Error: `{file_report['error']}`")
    lines.extend(
        [
            "",
            "## Next step",
            "",
            "- Run `tools/transcription_pilot.py --preflight-only` against the generated MP3 to test ffmpeg locally.",
            "- Replace the fixture with your own non-sensitive MP3 before collecting beta evidence.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
