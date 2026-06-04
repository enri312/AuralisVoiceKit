"""Command line helpers for AuralisVoiceKit."""

from __future__ import annotations

import argparse
import json

from ._version import __version__
from .audio import VoiceActivityConfig, read_audio_as_chunk, read_wav_metadata
from .backends import create_default_registry
from .config import VoiceKitConfig
from .diagnostics import DiagnosticStatus, run_doctor
from .exceptions import AudioSourceError, BackendNotAvailable, TranscriptionError
from .kit import AuralisVoiceKit
from .models import AudioDevice
from .session import VoiceSession, VoiceSessionConfig


def _print_device(device: AudioDevice) -> None:
    marker = " default" if device.is_default else ""
    channels = f", channels={device.channels}" if device.channels is not None else ""
    host_api = f", host_api={device.host_api}" if device.host_api else ""
    print(f"  [{device.id}] {device.name}{marker} ({device.kind}{channels}{host_api})")


def _print_devices(backend_name: str) -> int:
    registry = create_default_registry()
    try:
        backend = registry.create_capture(backend_name)
        devices = list(backend.list_devices())
    except BackendNotAvailable as exc:
        print(f"Cannot list devices for capture backend {backend_name!r}: {exc}")
        return 1

    print(f"Input devices from capture backend {backend_name!r}:")
    if not devices:
        print("  No input devices found.")
        return 0
    for device in devices:
        _print_device(device)
    return 0


def _print_doctor(
    show_devices: bool = False,
    device_backend: str = "sounddevice",
    json_output: bool = False,
    wav_path: str | None = None,
) -> int:
    report = run_doctor(
        include_devices=show_devices,
        capture_backend=device_backend,
        wav_path=wav_path,
    )

    if json_output:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 1 if report.status is DiagnosticStatus.ERROR else 0

    print(f"AuralisVoiceKit {report.version}")
    print(f"Python: {report.python}")
    print(f"Platform: {report.platform}")
    print(f"Implementation: {report.implementation}")
    print(f"Status: {report.status.value}")
    print()
    print("Checks:")
    for check in report.checks:
        print(f"  [{check.status.value}] {check.name}: {check.message}")
        if check.hint:
            print(f"      hint: {check.hint}")
        if check.name.startswith("devices:"):
            for device in check.details.get("devices", []):
                marker = " default" if device.get("is_default") else ""
                channels = (
                    f", channels={device.get('channels')}"
                    if device.get("channels") is not None
                    else ""
                )
                host_api = f", host_api={device.get('host_api')}" if device.get("host_api") else ""
                print(
                    f"      [{device.get('id')}] {device.get('name')}{marker} "
                    f"({device.get('kind')}{channels}{host_api})"
                )
    return 1 if report.status is DiagnosticStatus.ERROR else 0


def _print_backends() -> int:
    for info in create_default_registry().backend_info():
        deps = ", ".join(info.dependencies) if info.dependencies else "none"
        status = "available" if info.available else "unavailable"
        print(f"{info.kind}:{info.name} - {status} - deps: {deps}")
    return 0


def _print_wav_info(path: str) -> int:
    try:
        metadata = read_wav_metadata(path)
    except AudioSourceError as exc:
        print(str(exc))
        return 1

    audio_format = metadata.format
    print(f"Path: {metadata.path}")
    print(f"Sample rate: {audio_format.sample_rate}")
    print(f"Channels: {audio_format.channels}")
    print(f"Sample width: {audio_format.sample_width}")
    print(f"Encoding: {audio_format.encoding.value}")
    print(f"Frames: {metadata.frames}")
    print(f"Duration: {metadata.duration_seconds:.3f}s")
    return 0


def _transcribe_audio(
    path: str,
    *,
    backend_name: str,
    model: str,
    language: str,
    prompt: str | None,
    response_format: str,
    ffmpeg_executable: str,
    json_output: bool,
) -> int:
    try:
        config = VoiceKitConfig(
            transcription_backend=backend_name,
            transcription_model=model,
            language=language,
            transcription_prompt=prompt,
            transcription_response_format=response_format,
        )
        chunk = read_audio_as_chunk(
            path,
            sample_rate=config.sample_rate,
            channels=config.channels,
            ffmpeg_executable=ffmpeg_executable,
        )
        result = AuralisVoiceKit(config=config).transcribe(chunk)
    except (AudioSourceError, BackendNotAvailable, TranscriptionError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        print(
            json.dumps(
                {
                    "text": result.text,
                    "language": result.language,
                    "confidence": result.confidence,
                    "is_final": result.is_final,
                    "source": result.source,
                    "metadata": result.metadata,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(result.text)
    return 0


def _transcribe_audio_segments(
    path: str,
    *,
    backend_name: str,
    model: str,
    language: str,
    prompt: str | None,
    response_format: str,
    chunk_duration_ms: int,
    threshold: float,
    min_voice_ms: int,
    max_silence_ms: int,
    pre_speech_ms: int,
    max_turns: int | None,
    ffmpeg_executable: str,
    json_output: bool,
) -> int:
    try:
        kit_config = VoiceKitConfig(
            transcription_backend=backend_name,
            transcription_model=model,
            language=language,
            transcription_prompt=prompt,
            transcription_response_format=response_format,
        )
        session_config = VoiceSessionConfig(
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=VoiceActivityConfig(
                threshold=threshold,
                min_voice_ms=min_voice_ms,
                max_silence_ms=max_silence_ms,
                pre_speech_ms=pre_speech_ms,
            ),
            max_turns=max_turns,
            ffmpeg_executable=ffmpeg_executable,
        )
        turns = VoiceSession(
            AuralisVoiceKit(config=kit_config),
            session_config,
        ).transcribe_file(path)
    except (AudioSourceError, BackendNotAvailable, TranscriptionError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        print(json.dumps({"turns": [turn.to_dict() for turn in turns]}, indent=2, sort_keys=True))
        return 0

    if not turns:
        print("No voice segments detected.")
        return 0
    for turn in turns:
        print(turn.text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="auralis")
    parser.add_argument("--version", action="version", version=f"AuralisVoiceKit {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    doctor_parser = subparsers.add_parser("doctor", help="show runtime compatibility information")
    doctor_parser.add_argument(
        "--devices",
        action="store_true",
        help="list input devices after the compatibility report",
    )
    doctor_parser.add_argument(
        "--backend",
        default="sounddevice",
        help="capture backend used when listing devices",
    )
    doctor_parser.add_argument("--json", action="store_true", help="print a JSON report")
    doctor_parser.add_argument("--wav", help="validate a PCM16 WAV file")
    subparsers.add_parser("backends", help="list registered backends")
    devices_parser = subparsers.add_parser("devices", help="list input devices")
    devices_parser.add_argument("--backend", default="sounddevice", help="capture backend to inspect")
    wav_info_parser = subparsers.add_parser("wav-info", help="show PCM16 WAV metadata")
    wav_info_parser.add_argument("path", help="path to a WAV file")
    transcribe_parser = subparsers.add_parser("transcribe", help="transcribe an audio file")
    transcribe_parser.add_argument("path", help="path to a WAV or ffmpeg-supported audio file")
    transcribe_parser.add_argument(
        "--backend",
        default="openai",
        help="transcription backend to use",
    )
    transcribe_parser.add_argument(
        "--model",
        default="gpt-4o-mini-transcribe",
        help="model used by API transcription backends",
    )
    transcribe_parser.add_argument("--language", default="es", help="audio language hint")
    transcribe_parser.add_argument("--prompt", help="optional transcription prompt")
    transcribe_parser.add_argument(
        "--response-format",
        default="json",
        help="backend response format",
    )
    transcribe_parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    transcribe_parser.add_argument("--json", action="store_true", help="print a JSON result")
    segments_parser = subparsers.add_parser(
        "transcribe-segments",
        help="segment and transcribe an audio file",
    )
    segments_parser.add_argument("path", help="path to a WAV or ffmpeg-supported audio file")
    segments_parser.add_argument(
        "--backend",
        default="openai",
        help="transcription backend to use",
    )
    segments_parser.add_argument(
        "--model",
        default="gpt-4o-mini-transcribe",
        help="model used by API transcription backends",
    )
    segments_parser.add_argument("--language", default="es", help="audio language hint")
    segments_parser.add_argument("--prompt", help="optional transcription prompt")
    segments_parser.add_argument(
        "--response-format",
        default="json",
        help="backend response format",
    )
    segments_parser.add_argument("--chunk-ms", type=int, default=50, help="WAV chunk size")
    segments_parser.add_argument(
        "--threshold",
        type=float,
        default=0.01,
        help="voice RMS threshold",
    )
    segments_parser.add_argument(
        "--min-voice-ms",
        type=int,
        default=120,
        help="minimum voice duration",
    )
    segments_parser.add_argument(
        "--max-silence-ms",
        type=int,
        default=350,
        help="silence duration that closes a segment",
    )
    segments_parser.add_argument(
        "--pre-speech-ms",
        type=int,
        default=100,
        help="silence kept before speech",
    )
    segments_parser.add_argument("--max-turns", type=int, help="maximum turns to transcribe")
    segments_parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    segments_parser.add_argument("--json", action="store_true", help="print a JSON result")
    args = parser.parse_args(argv)

    if args.command is None:
        return _print_doctor()
    if args.command == "doctor":
        return _print_doctor(
            show_devices=args.devices,
            device_backend=args.backend,
            json_output=args.json,
            wav_path=args.wav,
        )
    if args.command == "backends":
        return _print_backends()
    if args.command == "devices":
        return _print_devices(args.backend)
    if args.command == "wav-info":
        return _print_wav_info(args.path)
    if args.command == "transcribe":
        return _transcribe_audio(
            args.path,
            backend_name=args.backend,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            response_format=args.response_format,
            ffmpeg_executable=args.ffmpeg,
            json_output=args.json,
        )
    if args.command == "transcribe-segments":
        return _transcribe_audio_segments(
            args.path,
            backend_name=args.backend,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            response_format=args.response_format,
            chunk_duration_ms=args.chunk_ms,
            threshold=args.threshold,
            min_voice_ms=args.min_voice_ms,
            max_silence_ms=args.max_silence_ms,
            pre_speech_ms=args.pre_speech_ms,
            max_turns=args.max_turns,
            ffmpeg_executable=args.ffmpeg,
            json_output=args.json,
        )
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
