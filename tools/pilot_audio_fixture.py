"""Generate public synthetic audio fixtures for transcription pilots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
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
    run_preflight: bool = False,
    min_audio_seconds: float | None = 0.2,
    max_audio_seconds: float | None = 60.0,
    normalize_preflight: bool = True,
) -> dict[str, Any]:
    """Generate a non-sensitive synthetic fixture and write sanitized artifacts."""

    requested_formats = _normalize_formats(formats)
    if run_preflight and "mp3" not in requested_formats:
        requested_formats = (*requested_formats, "mp3")
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

    preflight = (
        _run_fixture_preflight(
            root=workspace,
            output=output,
            artifacts=artifacts,
            ffmpeg_path=ffmpeg_path,
            ffmpeg=ffmpeg,
            sample_rate=sample_rate,
            min_audio_seconds=min_audio_seconds,
            max_audio_seconds=max_audio_seconds,
            normalize=normalize_preflight,
        )
        if run_preflight
        else {
            "requested": False,
            "passed": None,
            "reason": "not_requested",
            "artifact": None,
            "audio_decoded": None,
            "duration_gate_passed": None,
            "error": None,
        }
    )
    if preflight["artifact"] is not None:
        artifacts["fixture_preflight_report"] = preflight["artifact"]

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
        "preflight": preflight,
        "passed": all(file_report["passed"] for file_report in files) and preflight["passed"] is not False,
        "artifacts": {
            **artifacts,
            "fixture_findings": str(findings_path),
            "fixture_report": str(report_path),
        },
        "next_step": _fixture_next_step(run_preflight=run_preflight),
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
    parser.add_argument(
        "--run-preflight",
        action="store_true",
        help="run a safe transcription preflight against the generated MP3 fixture",
    )
    parser.add_argument(
        "--min-audio-seconds",
        type=float,
        default=0.2,
        help="minimum decoded audio duration for the fixture preflight",
    )
    parser.add_argument(
        "--max-audio-seconds",
        type=float,
        default=60.0,
        help="maximum decoded audio duration for the fixture preflight",
    )
    parser.add_argument(
        "--no-normalize-preflight",
        action="store_true",
        help="disable normalization during the fixture preflight",
    )
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
            run_preflight=args.run_preflight,
            min_audio_seconds=args.min_audio_seconds,
            max_audio_seconds=args.max_audio_seconds,
            normalize_preflight=not args.no_normalize_preflight,
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
        print(f"Fixture preflight: {report['preflight']['passed']}")
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


def _run_fixture_preflight(
    *,
    root: Path,
    output: Path,
    artifacts: dict[str, str],
    ffmpeg_path: str | None,
    ffmpeg: str,
    sample_rate: int,
    min_audio_seconds: float | None,
    max_audio_seconds: float | None,
    normalize: bool,
) -> dict[str, Any]:
    mp3_path = artifacts.get("mp3")
    if mp3_path is None:
        return {
            "requested": True,
            "passed": False,
            "reason": "missing_mp3_fixture",
            "artifact": None,
            "audio_decoded": False,
            "duration_gate_passed": None,
            "error": "MP3 fixture was not generated; install ffmpeg or review the fixture file report.",
        }

    try:
        module = _load_transcription_pilot_module()
        report = module.run_transcription_pilot(
            root=root,
            output_dir=output / "preflight",
            audio=mp3_path,
            backend="whisper",
            ffmpeg=ffmpeg_path or ffmpeg,
            normalize=normalize,
            preflight_only=True,
            audio_confirmed_non_sensitive=True,
            min_audio_seconds=min_audio_seconds,
            max_audio_seconds=max_audio_seconds,
            sample_rate=sample_rate,
        )
    except Exception as exc:  # noqa: BLE001 - converted into a public-safe report entry.
        return {
            "requested": True,
            "passed": False,
            "reason": "preflight_error",
            "artifact": None,
            "audio_decoded": False,
            "duration_gate_passed": None,
            "error": str(exc),
        }

    duration_gate = report["audio"]["duration_gate"]
    return {
        "requested": True,
        "passed": report["passed"],
        "reason": "completed",
        "artifact": report["artifacts"]["transcription_pilot_report"],
        "audio_file_name": report["audio"]["audio_file_name"],
        "audio_decoded": report["audio"]["decoded"],
        "source_format": report["audio"]["source_format"],
        "duration_seconds": report["audio"]["duration_seconds"],
        "duration_gate_passed": duration_gate["passed"],
        "error": report["error"],
    }


def _load_transcription_pilot_module():
    module_name = "auralis_fixture_transcription_pilot"
    module_path = Path(__file__).resolve().with_name("transcription_pilot.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load tools/transcription_pilot.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fixture_next_step(*, run_preflight: bool) -> str:
    if run_preflight:
        return (
            "Replace the generated fixture with your own non-sensitive MP3 and run "
            "tools/transcription_pilot.py --preflight-only before collecting real beta evidence."
        )
    return (
        "Use the generated MP3 for a local ffmpeg preflight, then replace it with "
        "your own non-sensitive MP3 for real beta evidence."
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
        f"- Fixture preflight requested: `{str(report['preflight']['requested']).lower()}`",
        f"- Fixture preflight passed: `{report['preflight']['passed']}`",
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
                f"  - Duration seconds: `{file_report.get('duration_seconds')}`",
            ]
        )
        if file_report["error"]:
            lines.append(f"  - Error: `{file_report['error']}`")
    lines.extend(
        [
            "",
            "## Fixture preflight",
            "",
            f"- Requested: `{str(report['preflight']['requested']).lower()}`",
            f"- Passed: `{report['preflight']['passed']}`",
            f"- Audio decoded: `{report['preflight']['audio_decoded']}`",
            f"- Duration gate passed: `{report['preflight']['duration_gate_passed']}`",
            "",
            "## Next step",
            "",
            "- Run `tools/transcription_pilot.py --preflight-only` against your own non-sensitive MP3.",
            "- Replace the fixture with your own non-sensitive MP3 before collecting beta evidence.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
