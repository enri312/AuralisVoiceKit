"""Command line helpers for AuralisVoiceKit."""

from __future__ import annotations

import argparse
import json

from ._version import __version__
from .audio import (
    VoiceActivityConfig,
    normalize_pcm16,
    peak_pcm16,
    read_audio_as_chunk,
    read_wav_metadata,
    rms_pcm16,
    write_wav,
)
from .backends import create_default_registry
from .benchmarks import (
    BenchmarkComparisonReport,
    BenchmarkReport,
    run_offline_benchmarks,
    run_whisper_comparison_benchmarks,
    write_benchmark_report,
)
from .config import VoiceKitConfig
from .diagnostics import (
    DiagnosticStatus,
    analyze_doctor_bundles,
    run_doctor,
    write_doctor_bundle,
    write_doctor_bundle_analysis,
)
from .exceptions import AudioSourceError, BackendNotAvailable, TranscriptionError
from .kit import AuralisVoiceKit
from .models import AudioDevice
from .session import VoiceSession, VoiceSessionConfig


def _default_transcription_model(backend_name: str, model: str | None) -> str:
    if model:
        return model
    if backend_name == "whisper":
        return "base"
    if backend_name == "openai":
        return "gpt-4o-mini-transcribe"
    return "auto"


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


def _print_wasapi_details(details: dict) -> None:
    wasapi = details.get("wasapi")
    if not wasapi:
        return
    reason = f", reason={wasapi.get('reason')}" if wasapi.get("reason") else ""
    print(
        "      wasapi: "
        f"available={wasapi.get('available')}, "
        f"host_apis={len(wasapi.get('host_apis', []))}, "
        f"wasapi_inputs={wasapi.get('wasapi_input_device_count')}, "
        f"selected_input={wasapi.get('selected_input_device_id')}"
        f"{reason}"
    )
    for host_api in wasapi.get("host_apis", []):
        print(f"      host_api[{host_api.get('index')}]: {host_api.get('name')}")


def _print_doctor(
    show_devices: bool = False,
    device_backend: str = "sounddevice",
    capture_test: bool = False,
    capture_seconds: float = 0.25,
    capture_device: str | None = None,
    capture_sample_rate: int | None = None,
    json_output: bool = False,
    wav_path: str | None = None,
    bundle_path: str | None = None,
) -> int:
    report = run_doctor(
        include_devices=show_devices,
        capture_backend=device_backend,
        include_capture_test=capture_test,
        capture_test_seconds=capture_seconds,
        capture_device=capture_device,
        capture_sample_rate=capture_sample_rate,
        wav_path=wav_path,
    )
    written_bundle = write_doctor_bundle(bundle_path, report) if bundle_path else None

    if json_output:
        payload = report.to_dict()
        if written_bundle is not None:
            payload["bundle_path"] = written_bundle
        print(json.dumps(payload, indent=2, sort_keys=True))
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
            _print_wasapi_details(check.details)
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
        if check.name.startswith("capture-test:"):
            chunks = check.details.get("chunks_received")
            bytes_received = check.details.get("bytes_received")
            elapsed = check.details.get("elapsed_seconds")
            if chunks is not None and bytes_received is not None:
                print(
                    f"      chunks={chunks}, bytes={bytes_received}, "
                    f"elapsed={elapsed}s"
                )
            _print_wasapi_details(check.details)
    if written_bundle is not None:
        print()
        print(f"Wrote doctor bundle: {written_bundle}")
    return 1 if report.status is DiagnosticStatus.ERROR else 0


def _print_doctor_bundle_analysis(
    paths: list[str],
    *,
    json_output: bool = False,
    output_path: str | None = None,
) -> int:
    try:
        analysis = analyze_doctor_bundles(paths)
        written_path = (
            write_doctor_bundle_analysis(output_path, analysis)
            if output_path is not None
            else None
        )
    except (OSError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        payload = analysis.to_dict()
        if written_path is not None:
            payload["analysis_path"] = written_path
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("AuralisVoiceKit doctor bundle analysis")
    print(f"Bundles: {analysis.bundle_count}")
    print(f"Systems: {_format_counts(analysis.systems)}")
    print(f"Statuses: {_format_counts(analysis.statuses)}")
    print(f"Priorities: {_format_counts(analysis.priority_counts)}")
    if analysis.issue_categories:
        print("Issue categories:")
        for category, count in analysis.issue_categories.items():
            print(f"  {category}: {count}")
    if analysis.issues:
        print("Top issues:")
        for issue in analysis.issues[:10]:
            print(
                f"  [{issue.priority}/{issue.status}] "
                f"{issue.bundle} {issue.check}: {issue.message}"
            )
    else:
        print("No warning or error checks found.")
    if written_path is not None:
        print()
        print(f"Wrote doctor bundle analysis: {written_path}")
    return 0


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in counts.items())


def _public_dependency_name(value: str) -> str:
    normalized = value.replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if "/" in normalized else value


def _backend_info_payload() -> dict:
    infos = create_default_registry().backend_info()
    backends = [
        {
            "name": info.name,
            "kind": info.kind,
            "available": info.available,
            "reason": info.reason,
            "dependencies": [_public_dependency_name(dependency) for dependency in info.dependencies],
        }
        for info in infos
    ]
    by_kind: dict[str, dict[str, int]] = {}
    for info in infos:
        counts = by_kind.setdefault(info.kind, {"total": 0, "available": 0, "unavailable": 0})
        counts["total"] += 1
        if info.available:
            counts["available"] += 1
        else:
            counts["unavailable"] += 1
    return {
        "version": __version__,
        "backends": backends,
        "counts": {
            "total": len(infos),
            "available": sum(1 for info in infos if info.available),
            "unavailable": sum(1 for info in infos if not info.available),
            "by_kind": by_kind,
        },
        "content_policy": {
            "records_local_paths": False,
            "records_credentials": False,
        },
    }


def _print_backends(*, json_output: bool = False) -> int:
    payload = _backend_info_payload()
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    for info in payload["backends"]:
        deps = ", ".join(info["dependencies"]) if info["dependencies"] else "none"
        status = "available" if info["available"] else "unavailable"
        print(f"{info['kind']}:{info['name']} - {status} - deps: {deps}")
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
    model: str | None,
    language: str,
    prompt: str | None,
    response_format: str,
    timeout_seconds: float | None,
    ffmpeg_executable: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    normalize: bool,
    target_peak: float,
    max_gain: float,
    json_output: bool,
) -> int:
    try:
        config = VoiceKitConfig(
            transcription_backend=backend_name,
            transcription_model=_default_transcription_model(backend_name, model),
            language=language,
            transcription_prompt=prompt,
            transcription_response_format=response_format,
            transcription_device=device,
            transcription_compute_type=compute_type,
            transcription_beam_size=beam_size,
            transcription_vad_filter=vad_filter,
            transcription_timeout_seconds=timeout_seconds,
        )
        chunk = read_audio_as_chunk(
            path,
            sample_rate=config.sample_rate,
            channels=config.channels,
            ffmpeg_executable=ffmpeg_executable,
        )
        if normalize:
            chunk = normalize_pcm16(chunk, target_peak=target_peak, max_gain=max_gain)
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
                    "metadata": {**chunk.metadata, **result.metadata},
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
    model: str | None,
    language: str,
    prompt: str | None,
    response_format: str,
    timeout_seconds: float | None,
    chunk_duration_ms: int,
    threshold: float,
    min_voice_ms: int,
    max_silence_ms: int,
    pre_speech_ms: int,
    max_turns: int | None,
    ffmpeg_executable: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    normalize: bool,
    target_peak: float,
    max_gain: float,
    json_output: bool,
) -> int:
    try:
        kit_config = VoiceKitConfig(
            transcription_backend=backend_name,
            transcription_model=_default_transcription_model(backend_name, model),
            language=language,
            transcription_prompt=prompt,
            transcription_response_format=response_format,
            transcription_device=device,
            transcription_compute_type=compute_type,
            transcription_beam_size=beam_size,
            transcription_vad_filter=vad_filter,
            transcription_timeout_seconds=timeout_seconds,
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
            normalize_segments=normalize,
            normalization_target_peak=target_peak,
            normalization_max_gain=max_gain,
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


def _normalize_audio_file(
    input_path: str,
    output_path: str,
    *,
    ffmpeg_executable: str,
    target_peak: float,
    max_gain: float,
    json_output: bool,
) -> int:
    try:
        chunk = read_audio_as_chunk(input_path, ffmpeg_executable=ffmpeg_executable)
        normalized = normalize_pcm16(chunk, target_peak=target_peak, max_gain=max_gain)
        write_wav(output_path, [normalized])
    except (AudioSourceError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    payload = {
        "input": input_path,
        "output": output_path,
        "duration_seconds": normalized.duration_seconds,
        "input_peak": normalized.metadata.get("normalization_input_peak"),
        "output_peak": peak_pcm16(normalized),
        "rms": rms_pcm16(normalized),
        "gain": normalized.metadata.get("normalization_gain"),
        "target_peak": target_peak,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"Wrote {output_path} "
            f"(gain={payload['gain']:.3f}, peak={payload['output_peak']:.3f})"
        )
    return 0


def _speak_text(
    text: str,
    *,
    backend_name: str,
    voice: str | None,
    rate: int | None,
    volume: int | None,
    json_output: bool,
) -> int:
    try:
        config = VoiceKitConfig(
            output_backend=backend_name,
            output_voice=voice,
            output_rate=rate,
            output_volume=volume,
        )
        AuralisVoiceKit(config=config).speak(text)
    except (BackendNotAvailable, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    payload = {
        "backend": backend_name,
        "characters": len(text),
        "voice": voice,
        "rate": rate,
        "volume": volume,
        "spoken": True,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Spoken with output backend {backend_name!r}.")
    return 0


def _print_output_voices(
    *,
    backend_name: str,
    json_output: bool,
) -> int:
    try:
        backend = create_default_registry().create_output(backend_name)
        list_voices = getattr(backend, "list_voices", None)
        if list_voices is None:
            raise BackendNotAvailable(f"Output backend {backend_name!r} cannot list voices.")
        voices = tuple(list_voices())
    except BackendNotAvailable as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        print(
            json.dumps(
                {
                    "backend": backend_name,
                    "voices": [voice.to_dict() for voice in voices],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"Output voices from backend {backend_name!r}:")
    if not voices:
        print("  No voices were reported by this backend.")
        return 0
    for voice in voices:
        language = f", language={voice.language}" if voice.language else ""
        gender = f", gender={voice.gender}" if voice.gender else ""
        print(f"  [{voice.id}] {voice.name}{language}{gender}")
    return 0


def _print_benchmark_report(report: BenchmarkReport) -> None:
    print(f"AuralisVoiceKit {report.version} benchmark")
    print(
        f"Audio: {report.duration_seconds:.3f}s, "
        f"{report.sample_rate} Hz, {report.channels} channel(s), "
        f"chunk={report.chunk_duration_ms} ms"
    )
    print(
        f"Iterations: {report.iterations}, warmups: {report.warmup_iterations}, "
        f"chunks: {report.chunks}, segments: {report.segments}"
    )
    print(f"Transcription backend: {report.transcription_backend}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
    print()
    print("Results:")
    for result in report.results:
        print(
            f"  {result.name}: "
            f"mean={result.mean_ms:.3f}ms, "
            f"median={result.median_ms:.3f}ms, "
            f"p95={result.p95_ms:.3f}ms, "
            f"min={result.min_ms:.3f}ms, "
            f"max={result.max_ms:.3f}ms"
        )


def _print_comparison_report(report: BenchmarkComparisonReport) -> None:
    print(f"AuralisVoiceKit {report.version} {report.benchmark}")
    print(
        f"Audio: {report.duration_seconds:.3f}s, "
        f"{report.sample_rate} Hz, {report.channels} channel(s), "
        f"chunk={report.chunk_duration_ms} ms"
    )
    print(f"Iterations: {report.iterations}, warmups: {report.warmup_iterations}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
    print()
    print("Rankings:")
    for index, entry in enumerate(report.entries, start=1):
        print(
            f"  {index}. {entry.name}: "
            f"mean={entry.transcription_mean_ms:.3f}ms, "
            f"p95={entry.transcription_p95_ms:.3f}ms"
        )


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _parse_int_csv(value: str) -> tuple[int, ...]:
    items = _parse_csv(value)
    try:
        return tuple(int(item) for item in items)
    except ValueError as exc:
        raise ValueError(f"Expected comma-separated integers, got {value!r}") from exc


def _run_benchmark(
    *,
    iterations: int,
    warmups: int,
    duration_seconds: float,
    sample_rate: int,
    channels: int,
    chunk_duration_ms: int,
    threshold: float,
    min_voice_ms: int,
    max_silence_ms: int,
    pre_speech_ms: int,
    transcription_backend: str,
    model: str | None,
    language: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    json_output: bool,
    output: str | None,
    output_format: str | None,
) -> int:
    try:
        report = run_offline_benchmarks(
            iterations=iterations,
            warmup_iterations=warmups,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            channels=channels,
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=VoiceActivityConfig(
                threshold=threshold,
                min_voice_ms=min_voice_ms,
                max_silence_ms=max_silence_ms,
                pre_speech_ms=pre_speech_ms,
            ),
            transcription_backend=transcription_backend,
            transcription_model=model or _default_transcription_model(transcription_backend, model),
            language=language,
            transcription_device=device,
            transcription_compute_type=compute_type,
            transcription_beam_size=beam_size,
            transcription_vad_filter=vad_filter,
        )
        written_path = (
            write_benchmark_report(report, output, format=output_format)
            if output is not None
            else None
        )
    except (BackendNotAvailable, TranscriptionError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_benchmark_report(report)
        if written_path is not None:
            print(f"\nWrote benchmark report: {written_path}")
    return 0


def _run_whisper_benchmark(
    *,
    iterations: int,
    warmups: int,
    duration_seconds: float,
    sample_rate: int,
    channels: int,
    chunk_duration_ms: int,
    threshold: float,
    min_voice_ms: int,
    max_silence_ms: int,
    pre_speech_ms: int,
    models: str,
    devices: str,
    compute_types: str,
    beam_sizes: str,
    vad_filter: bool,
    max_combinations: int,
    language: str,
    json_output: bool,
    output: str | None,
    output_format: str | None,
) -> int:
    try:
        report = run_whisper_comparison_benchmarks(
            models=_parse_csv(models),
            devices=_parse_csv(devices),
            compute_types=_parse_csv(compute_types),
            beam_sizes=_parse_int_csv(beam_sizes),
            vad_filter=vad_filter,
            max_combinations=max_combinations,
            iterations=iterations,
            warmup_iterations=warmups,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            channels=channels,
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=VoiceActivityConfig(
                threshold=threshold,
                min_voice_ms=min_voice_ms,
                max_silence_ms=max_silence_ms,
                pre_speech_ms=pre_speech_ms,
            ),
            language=language,
        )
        written_path = (
            write_benchmark_report(report, output, format=output_format)
            if output is not None
            else None
        )
    except (BackendNotAvailable, TranscriptionError, ValueError) as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(str(exc))
        return 1

    if json_output:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_comparison_report(report)
        if written_path is not None:
            print(f"\nWrote benchmark report: {written_path}")
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
        help="capture backend used when listing devices or testing capture",
    )
    doctor_parser.add_argument(
        "--capture-test",
        action="store_true",
        help="try to open the selected capture backend briefly",
    )
    doctor_parser.add_argument(
        "--capture-seconds",
        type=float,
        default=0.25,
        help="duration for --capture-test",
    )
    doctor_parser.add_argument("--device", help="input device selector for --capture-test")
    doctor_parser.add_argument(
        "--sample-rate",
        type=int,
        help="sample rate used by --capture-test, for example 48000 on many WASAPI devices",
    )
    doctor_parser.add_argument("--json", action="store_true", help="print a JSON report")
    doctor_parser.add_argument("--wav", help="validate a PCM16 WAV file")
    doctor_parser.add_argument(
        "--bundle",
        help="write a sanitized diagnostic bundle JSON for support or pilot reports",
    )
    bundle_parser = subparsers.add_parser(
        "doctor-bundles",
        help="analyze sanitized doctor bundle JSON files",
    )
    bundle_parser.add_argument("paths", nargs="+", help="doctor bundle JSON files to analyze")
    bundle_parser.add_argument("--json", action="store_true", help="print a JSON analysis report")
    bundle_parser.add_argument("--output", help="write the analysis JSON to a file")
    backends_parser = subparsers.add_parser("backends", help="list registered backends")
    backends_parser.add_argument("--json", action="store_true", help="print a JSON report")
    devices_parser = subparsers.add_parser("devices", help="list input devices")
    devices_parser.add_argument("--backend", default="sounddevice", help="capture backend to inspect")
    wav_info_parser = subparsers.add_parser("wav-info", help="show PCM16 WAV metadata")
    wav_info_parser.add_argument("path", help="path to a WAV file")
    normalize_parser = subparsers.add_parser("normalize", help="normalize audio to a PCM16 WAV file")
    normalize_parser.add_argument("input", help="path to a WAV or ffmpeg-supported audio file")
    normalize_parser.add_argument("output", help="output WAV path")
    normalize_parser.add_argument("--target-peak", type=float, default=0.95, help="target normalized peak")
    normalize_parser.add_argument("--max-gain", type=float, default=8.0, help="maximum gain multiplier")
    normalize_parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    normalize_parser.add_argument("--json", action="store_true", help="print a JSON result")
    speak_parser = subparsers.add_parser("speak", help="speak text through an output backend")
    speak_parser.add_argument("text", help="text to speak")
    speak_parser.add_argument(
        "--backend",
        default="null",
        help="output backend to use (null, system)",
    )
    speak_parser.add_argument("--voice", help="system voice selector when supported")
    speak_parser.add_argument("--rate", type=int, help="system speech rate when supported")
    speak_parser.add_argument("--volume", type=int, help="system speech volume from 0 to 100 when supported")
    speak_parser.add_argument("--json", action="store_true", help="print a JSON result")
    voices_parser = subparsers.add_parser("voices", help="list output voices")
    voices_parser.add_argument("--backend", default="system", help="output backend to inspect")
    voices_parser.add_argument("--json", action="store_true", help="print a JSON result")
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="run offline latency benchmarks",
    )
    benchmark_parser.add_argument("--iterations", type=int, default=5, help="measured iterations")
    benchmark_parser.add_argument("--warmups", type=int, default=1, help="warmup iterations")
    benchmark_parser.add_argument("--duration", type=float, default=2.0, help="synthetic audio duration")
    benchmark_parser.add_argument("--sample-rate", type=int, default=16000, help="synthetic audio sample rate")
    benchmark_parser.add_argument("--channels", type=int, default=1, help="synthetic audio channels")
    benchmark_parser.add_argument("--chunk-ms", type=int, default=50, help="chunk size in milliseconds")
    benchmark_parser.add_argument("--threshold", type=float, default=0.01, help="voice RMS threshold")
    benchmark_parser.add_argument("--min-voice-ms", type=int, default=120, help="minimum voice duration")
    benchmark_parser.add_argument(
        "--max-silence-ms",
        type=int,
        default=350,
        help="silence duration that closes a segment",
    )
    benchmark_parser.add_argument("--pre-speech-ms", type=int, default=100, help="silence kept before speech")
    benchmark_parser.add_argument(
        "--transcription-backend",
        default="null",
        help="transcription backend to benchmark (null, whisper, openai)",
    )
    benchmark_parser.add_argument("--model", help="transcription model")
    benchmark_parser.add_argument("--language", default="es", help="audio language hint")
    benchmark_parser.add_argument("--device", default="auto", help="local whisper device")
    benchmark_parser.add_argument("--compute-type", default="default", help="local whisper compute type")
    benchmark_parser.add_argument("--beam-size", type=int, default=5, help="local whisper beam size")
    benchmark_parser.add_argument("--vad-filter", action="store_true", help="enable local whisper VAD filter")
    benchmark_parser.add_argument("--json", action="store_true", help="print a JSON report")
    benchmark_parser.add_argument("--output", help="write benchmark report to a JSON or CSV file")
    benchmark_parser.add_argument(
        "--output-format",
        choices=("json", "csv"),
        help="output file format; defaults to the file extension",
    )
    whisper_benchmark_parser = subparsers.add_parser(
        "benchmark-whisper",
        help="compare local faster-whisper configurations",
    )
    whisper_benchmark_parser.add_argument("--iterations", type=int, default=3, help="measured iterations")
    whisper_benchmark_parser.add_argument("--warmups", type=int, default=1, help="warmup iterations")
    whisper_benchmark_parser.add_argument("--duration", type=float, default=2.0, help="synthetic audio duration")
    whisper_benchmark_parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="synthetic audio sample rate",
    )
    whisper_benchmark_parser.add_argument("--channels", type=int, default=1, help="synthetic audio channels")
    whisper_benchmark_parser.add_argument("--chunk-ms", type=int, default=50, help="chunk size in milliseconds")
    whisper_benchmark_parser.add_argument("--threshold", type=float, default=0.01, help="voice RMS threshold")
    whisper_benchmark_parser.add_argument("--min-voice-ms", type=int, default=120, help="minimum voice duration")
    whisper_benchmark_parser.add_argument(
        "--max-silence-ms",
        type=int,
        default=350,
        help="silence duration that closes a segment",
    )
    whisper_benchmark_parser.add_argument("--pre-speech-ms", type=int, default=100, help="silence kept before speech")
    whisper_benchmark_parser.add_argument(
        "--models",
        default="tiny,base",
        help="comma-separated faster-whisper models to compare",
    )
    whisper_benchmark_parser.add_argument(
        "--devices",
        default="auto",
        help="comma-separated local whisper devices",
    )
    whisper_benchmark_parser.add_argument(
        "--compute-types",
        default="default",
        help="comma-separated local whisper compute types",
    )
    whisper_benchmark_parser.add_argument(
        "--beam-sizes",
        default="1,5",
        help="comma-separated local whisper beam sizes",
    )
    whisper_benchmark_parser.add_argument("--vad-filter", action="store_true", help="enable local whisper VAD filter")
    whisper_benchmark_parser.add_argument("--max-combinations", type=int, default=8, help="safety limit")
    whisper_benchmark_parser.add_argument("--language", default="es", help="audio language hint")
    whisper_benchmark_parser.add_argument("--json", action="store_true", help="print a JSON report")
    whisper_benchmark_parser.add_argument("--output", help="write benchmark report to a JSON or CSV file")
    whisper_benchmark_parser.add_argument(
        "--output-format",
        choices=("json", "csv"),
        help="output file format; defaults to the file extension",
    )
    transcribe_parser = subparsers.add_parser("transcribe", help="transcribe an audio file")
    transcribe_parser.add_argument("path", help="path to a WAV or ffmpeg-supported audio file")
    transcribe_parser.add_argument(
        "--backend",
        default="null",
        help="transcription backend to use (null, whisper, openai)",
    )
    transcribe_parser.add_argument(
        "--model",
        help="transcription model; defaults to auto, base for whisper, or gpt-4o-mini-transcribe for openai",
    )
    transcribe_parser.add_argument("--language", default="es", help="audio language hint")
    transcribe_parser.add_argument("--prompt", help="optional transcription prompt")
    transcribe_parser.add_argument(
        "--response-format",
        default="json",
        help="backend response format",
    )
    transcribe_parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="optional transcription timeout passed to supported backends",
    )
    transcribe_parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    transcribe_parser.add_argument("--device", default="auto", help="local whisper device")
    transcribe_parser.add_argument("--compute-type", default="default", help="local whisper compute type")
    transcribe_parser.add_argument("--beam-size", type=int, default=5, help="local whisper beam size")
    transcribe_parser.add_argument("--vad-filter", action="store_true", help="enable local whisper VAD filter")
    transcribe_parser.add_argument("--normalize", action="store_true", help="normalize audio before transcribing")
    transcribe_parser.add_argument("--target-peak", type=float, default=0.95, help="target normalized peak")
    transcribe_parser.add_argument("--max-gain", type=float, default=8.0, help="maximum gain multiplier")
    transcribe_parser.add_argument("--json", action="store_true", help="print a JSON result")
    segments_parser = subparsers.add_parser(
        "transcribe-segments",
        help="segment and transcribe an audio file",
    )
    segments_parser.add_argument("path", help="path to a WAV or ffmpeg-supported audio file")
    segments_parser.add_argument(
        "--backend",
        default="null",
        help="transcription backend to use (null, whisper, openai)",
    )
    segments_parser.add_argument(
        "--model",
        help="transcription model; defaults to auto, base for whisper, or gpt-4o-mini-transcribe for openai",
    )
    segments_parser.add_argument("--language", default="es", help="audio language hint")
    segments_parser.add_argument("--prompt", help="optional transcription prompt")
    segments_parser.add_argument(
        "--response-format",
        default="json",
        help="backend response format",
    )
    segments_parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="optional transcription timeout passed to supported backends",
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
    segments_parser.add_argument("--device", default="auto", help="local whisper device")
    segments_parser.add_argument("--compute-type", default="default", help="local whisper compute type")
    segments_parser.add_argument("--beam-size", type=int, default=5, help="local whisper beam size")
    segments_parser.add_argument("--vad-filter", action="store_true", help="enable local whisper VAD filter")
    segments_parser.add_argument("--normalize", action="store_true", help="normalize each segment before transcribing")
    segments_parser.add_argument("--target-peak", type=float, default=0.95, help="target normalized peak")
    segments_parser.add_argument("--max-gain", type=float, default=8.0, help="maximum gain multiplier")
    segments_parser.add_argument("--json", action="store_true", help="print a JSON result")
    args = parser.parse_args(argv)

    if args.command is None:
        return _print_doctor()
    if args.command == "doctor":
        return _print_doctor(
            show_devices=args.devices,
            device_backend=args.backend,
            capture_test=args.capture_test,
            capture_seconds=args.capture_seconds,
            capture_device=args.device,
            capture_sample_rate=args.sample_rate,
            json_output=args.json,
            wav_path=args.wav,
            bundle_path=args.bundle,
        )
    if args.command == "doctor-bundles":
        return _print_doctor_bundle_analysis(
            args.paths,
            json_output=args.json,
            output_path=args.output,
        )
    if args.command == "backends":
        return _print_backends(json_output=args.json)
    if args.command == "devices":
        return _print_devices(args.backend)
    if args.command == "wav-info":
        return _print_wav_info(args.path)
    if args.command == "normalize":
        return _normalize_audio_file(
            args.input,
            args.output,
            ffmpeg_executable=args.ffmpeg,
            target_peak=args.target_peak,
            max_gain=args.max_gain,
            json_output=args.json,
        )
    if args.command == "speak":
        return _speak_text(
            args.text,
            backend_name=args.backend,
            voice=args.voice,
            rate=args.rate,
            volume=args.volume,
            json_output=args.json,
        )
    if args.command == "voices":
        return _print_output_voices(
            backend_name=args.backend,
            json_output=args.json,
        )
    if args.command == "benchmark":
        return _run_benchmark(
            iterations=args.iterations,
            warmups=args.warmups,
            duration_seconds=args.duration,
            sample_rate=args.sample_rate,
            channels=args.channels,
            chunk_duration_ms=args.chunk_ms,
            threshold=args.threshold,
            min_voice_ms=args.min_voice_ms,
            max_silence_ms=args.max_silence_ms,
            pre_speech_ms=args.pre_speech_ms,
            transcription_backend=args.transcription_backend,
            model=args.model,
            language=args.language,
            device=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
            vad_filter=args.vad_filter,
            json_output=args.json,
            output=args.output,
            output_format=args.output_format,
        )
    if args.command == "benchmark-whisper":
        return _run_whisper_benchmark(
            iterations=args.iterations,
            warmups=args.warmups,
            duration_seconds=args.duration,
            sample_rate=args.sample_rate,
            channels=args.channels,
            chunk_duration_ms=args.chunk_ms,
            threshold=args.threshold,
            min_voice_ms=args.min_voice_ms,
            max_silence_ms=args.max_silence_ms,
            pre_speech_ms=args.pre_speech_ms,
            models=args.models,
            devices=args.devices,
            compute_types=args.compute_types,
            beam_sizes=args.beam_sizes,
            vad_filter=args.vad_filter,
            max_combinations=args.max_combinations,
            language=args.language,
            json_output=args.json,
            output=args.output,
            output_format=args.output_format,
        )
    if args.command == "transcribe":
        return _transcribe_audio(
            args.path,
            backend_name=args.backend,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            response_format=args.response_format,
            timeout_seconds=args.timeout_seconds,
            ffmpeg_executable=args.ffmpeg,
            device=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
            vad_filter=args.vad_filter,
            normalize=args.normalize,
            target_peak=args.target_peak,
            max_gain=args.max_gain,
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
            timeout_seconds=args.timeout_seconds,
            chunk_duration_ms=args.chunk_ms,
            threshold=args.threshold,
            min_voice_ms=args.min_voice_ms,
            max_silence_ms=args.max_silence_ms,
            pre_speech_ms=args.pre_speech_ms,
            max_turns=args.max_turns,
            ffmpeg_executable=args.ffmpeg,
            device=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
            vad_filter=args.vad_filter,
            normalize=args.normalize,
            target_peak=args.target_peak,
            max_gain=args.max_gain,
            json_output=args.json,
        )
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
