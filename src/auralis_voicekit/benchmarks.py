"""Deterministic latency benchmarks for offline voice workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import os
import struct
import tempfile
import time
from statistics import fmean, median
from typing import Callable, TypeVar

from ._version import __version__
from .audio import VoiceActivityConfig, VoiceSegment, segment_voice_pcm16, write_wav
from .config import VoiceKitConfig
from .kit import AuralisVoiceKit
from .models import AudioChunk, AudioEncoding, AudioFormat
from .session import VoiceSession, VoiceSessionConfig


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Timing summary for one benchmarked operation."""

    name: str
    iterations: int
    samples_ms: tuple[float, ...]
    min_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    max_ms: float
    total_ms: float
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "samples_ms": list(self.samples_ms),
            "min_ms": self.min_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "max_ms": self.max_ms,
            "total_ms": self.total_ms,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Structured benchmark report that can be printed or serialized."""

    version: str
    created_at: str
    duration_seconds: float
    sample_rate: int
    channels: int
    chunk_duration_ms: int
    iterations: int
    warmup_iterations: int
    chunks: int
    segments: int
    transcription_backend: str
    results: tuple[BenchmarkResult, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration_ms": self.chunk_duration_ms,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "chunks": self.chunks,
            "segments": self.segments,
            "transcription_backend": self.transcription_backend,
            "results": [result.to_dict() for result in self.results],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkComparisonEntry:
    """One comparable benchmark run inside a benchmark suite."""

    name: str
    model: str
    device: str
    compute_type: str
    beam_size: int
    vad_filter: bool
    report: BenchmarkReport
    transcription_mean_ms: float
    transcription_p95_ms: float

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "model": self.model,
            "device": self.device,
            "compute_type": self.compute_type,
            "beam_size": self.beam_size,
            "vad_filter": self.vad_filter,
            "transcription_mean_ms": self.transcription_mean_ms,
            "transcription_p95_ms": self.transcription_p95_ms,
            "report": self.report.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkComparisonReport:
    """Comparable benchmark report for several backend configurations."""

    version: str
    created_at: str
    benchmark: str
    iterations: int
    warmup_iterations: int
    duration_seconds: float
    sample_rate: int
    channels: int
    chunk_duration_ms: int
    entries: tuple[BenchmarkComparisonEntry, ...]
    warnings: tuple[str, ...] = ()

    @property
    def fastest(self) -> BenchmarkComparisonEntry | None:
        if not self.entries:
            return None
        return min(self.entries, key=lambda entry: entry.transcription_mean_ms)

    def to_dict(self) -> dict[str, object]:
        fastest = self.fastest
        return {
            "version": self.version,
            "created_at": self.created_at,
            "benchmark": self.benchmark,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration_ms": self.chunk_duration_ms,
            "fastest": fastest.name if fastest is not None else None,
            "entries": [entry.to_dict() for entry in self.entries],
            "rankings": [
                {
                    "rank": index + 1,
                    "name": entry.name,
                    "model": entry.model,
                    "device": entry.device,
                    "compute_type": entry.compute_type,
                    "beam_size": entry.beam_size,
                    "vad_filter": entry.vad_filter,
                    "transcription_mean_ms": entry.transcription_mean_ms,
                    "transcription_p95_ms": entry.transcription_p95_ms,
                }
                for index, entry in enumerate(
                    sorted(self.entries, key=lambda item: item.transcription_mean_ms)
                )
            ],
            "warnings": list(self.warnings),
        }


def generate_synthetic_audio_chunks(
    *,
    duration_seconds: float = 2.0,
    sample_rate: int = 16_000,
    channels: int = 1,
    chunk_duration_ms: int = 50,
    voice_amplitude: int = 6_000,
) -> list[AudioChunk]:
    """Generate deterministic PCM16 chunks with alternating silence and voice-like audio."""

    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than zero")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than zero")
    if channels <= 0:
        raise ValueError("channels must be greater than zero")
    if chunk_duration_ms <= 0:
        raise ValueError("chunk_duration_ms must be greater than zero")
    if voice_amplitude <= 0 or voice_amplitude > 32_767:
        raise ValueError("voice_amplitude must be between 1 and 32767")

    audio_format = AudioFormat(
        sample_rate=sample_rate,
        channels=channels,
        sample_width=2,
        encoding=AudioEncoding.PCM16,
    )
    frames_per_chunk = max(1, int(sample_rate * chunk_duration_ms / 1000))
    samples_per_chunk = frames_per_chunk * channels
    total_chunks = max(1, math.ceil(duration_seconds / (chunk_duration_ms / 1000)))
    silence = b"\x00\x00" * samples_per_chunk
    voice = struct.pack("<h", voice_amplitude) * samples_per_chunk

    chunks: list[AudioChunk] = []
    for index in range(total_chunks):
        pattern_position = index % 10
        is_voice = 2 <= pattern_position <= 6
        chunks.append(
            AudioChunk(
                data=voice if is_voice else silence,
                format=audio_format,
                metadata={
                    "synthetic": True,
                    "chunk_index": index,
                    "voice": is_voice,
                },
            )
        )
    return chunks


def run_offline_benchmarks(
    *,
    iterations: int = 5,
    warmup_iterations: int = 1,
    duration_seconds: float = 2.0,
    sample_rate: int = 16_000,
    channels: int = 1,
    chunk_duration_ms: int = 50,
    voice_activity: VoiceActivityConfig | None = None,
    transcription_backend: str = "null",
    transcription_model: str = "auto",
    language: str = "es",
    transcription_device: str = "auto",
    transcription_compute_type: str = "default",
    transcription_beam_size: int = 5,
    transcription_vad_filter: bool = False,
) -> BenchmarkReport:
    """Run basic offline latency benchmarks for capture, segmentation and transcription."""

    _validate_benchmark_settings(iterations, warmup_iterations)
    chunks = generate_synthetic_audio_chunks(
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=channels,
        chunk_duration_ms=chunk_duration_ms,
    )
    activity_config = voice_activity or VoiceActivityConfig()
    segments = segment_voice_pcm16(chunks, config=activity_config)
    warnings: list[str] = []
    if not segments:
        warnings.append("No synthetic voice segments were detected.")

    capture_result = _benchmark_wav_capture(
        chunks,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        chunk_duration_ms=chunk_duration_ms,
        sample_rate=sample_rate,
        channels=channels,
    )
    segmentation_result = _measure_operation(
        "segmentation:rms",
        lambda: segment_voice_pcm16(chunks, config=activity_config),
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        metadata={
            "input_chunks": len(chunks),
            "segments": len(segments),
            "threshold": activity_config.threshold,
            "min_voice_ms": activity_config.min_voice_ms,
            "max_silence_ms": activity_config.max_silence_ms,
            "pre_speech_ms": activity_config.pre_speech_ms,
        },
    )
    transcription_result = _benchmark_transcription(
        segments,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        chunk_duration_ms=chunk_duration_ms,
        sample_rate=sample_rate,
        channels=channels,
        voice_activity=activity_config,
        transcription_backend=transcription_backend,
        transcription_model=transcription_model,
        language=language,
        transcription_device=transcription_device,
        transcription_compute_type=transcription_compute_type,
        transcription_beam_size=transcription_beam_size,
        transcription_vad_filter=transcription_vad_filter,
    )

    return BenchmarkReport(
        version=__version__,
        created_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=channels,
        chunk_duration_ms=chunk_duration_ms,
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        chunks=len(chunks),
        segments=len(segments),
        transcription_backend=transcription_backend,
        results=(capture_result, segmentation_result, transcription_result),
        warnings=tuple(warnings),
    )


def run_whisper_comparison_benchmarks(
    *,
    models: tuple[str, ...] = ("tiny", "base"),
    devices: tuple[str, ...] = ("auto",),
    compute_types: tuple[str, ...] = ("default",),
    beam_sizes: tuple[int, ...] = (1, 5),
    vad_filter: bool = False,
    max_combinations: int = 8,
    iterations: int = 3,
    warmup_iterations: int = 1,
    duration_seconds: float = 2.0,
    sample_rate: int = 16_000,
    channels: int = 1,
    chunk_duration_ms: int = 50,
    voice_activity: VoiceActivityConfig | None = None,
    language: str = "es",
) -> BenchmarkComparisonReport:
    """Compare several faster-whisper configurations on the local machine."""

    _validate_benchmark_settings(iterations, warmup_iterations)
    combinations = _whisper_configurations(
        models=models,
        devices=devices,
        compute_types=compute_types,
        beam_sizes=beam_sizes,
        vad_filter=vad_filter,
        max_combinations=max_combinations,
    )
    entries = []
    warnings: list[str] = []
    for model, device, compute_type, beam_size, use_vad in combinations:
        report = run_offline_benchmarks(
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            channels=channels,
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=voice_activity,
            transcription_backend="whisper",
            transcription_model=model,
            language=language,
            transcription_device=device,
            transcription_compute_type=compute_type,
            transcription_beam_size=beam_size,
            transcription_vad_filter=use_vad,
        )
        warnings.extend(report.warnings)
        transcription_result = _find_result(report, "transcription:whisper")
        entries.append(
            BenchmarkComparisonEntry(
                name=_whisper_entry_name(
                    model=model,
                    device=device,
                    compute_type=compute_type,
                    beam_size=beam_size,
                    vad_filter=use_vad,
                ),
                model=model,
                device=device,
                compute_type=compute_type,
                beam_size=beam_size,
                vad_filter=use_vad,
                report=report,
                transcription_mean_ms=transcription_result.mean_ms,
                transcription_p95_ms=transcription_result.p95_ms,
            )
        )

    return BenchmarkComparisonReport(
        version=__version__,
        created_at=datetime.now(timezone.utc).isoformat(),
        benchmark="whisper-comparison",
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=channels,
        chunk_duration_ms=chunk_duration_ms,
        entries=tuple(sorted(entries, key=lambda entry: entry.transcription_mean_ms)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _validate_benchmark_settings(iterations: int, warmup_iterations: int) -> None:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")
    if warmup_iterations < 0:
        raise ValueError("warmup_iterations must be greater than or equal to zero")


def _whisper_configurations(
    *,
    models: tuple[str, ...],
    devices: tuple[str, ...],
    compute_types: tuple[str, ...],
    beam_sizes: tuple[int, ...],
    vad_filter: bool,
    max_combinations: int,
) -> tuple[tuple[str, str, str, int, bool], ...]:
    if not models:
        raise ValueError("at least one whisper model is required")
    if not devices:
        raise ValueError("at least one whisper device is required")
    if not compute_types:
        raise ValueError("at least one whisper compute type is required")
    if not beam_sizes:
        raise ValueError("at least one whisper beam size is required")
    if any(beam_size <= 0 for beam_size in beam_sizes):
        raise ValueError("whisper beam sizes must be greater than zero")
    if max_combinations <= 0:
        raise ValueError("max_combinations must be greater than zero")

    combinations = tuple(
        (model, device, compute_type, beam_size, vad_filter)
        for model in models
        for device in devices
        for compute_type in compute_types
        for beam_size in beam_sizes
    )
    if len(combinations) > max_combinations:
        raise ValueError(
            f"whisper benchmark requested {len(combinations)} combinations; "
            f"raise max_combinations above {max_combinations} to run them"
        )
    return combinations


def _whisper_entry_name(
    *,
    model: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
) -> str:
    vad = "vad-on" if vad_filter else "vad-off"
    return (
        f"whisper:model={model}:device={device}:"
        f"compute={compute_type}:beam={beam_size}:{vad}"
    )


def _find_result(report: BenchmarkReport, name: str) -> BenchmarkResult:
    for result in report.results:
        if result.name == name:
            return result
    raise ValueError(f"benchmark report did not include result {name!r}")


def _benchmark_wav_capture(
    chunks: list[AudioChunk],
    *,
    iterations: int,
    warmup_iterations: int,
    chunk_duration_ms: int,
    sample_rate: int,
    channels: int,
) -> BenchmarkResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "benchmark.wav")
        write_wav(path, chunks)

        def capture_once() -> int:
            captured: list[AudioChunk] = []
            kit = AuralisVoiceKit(
                VoiceKitConfig(
                    capture_backend="wav",
                    input_file=path,
                    capture_block_ms=chunk_duration_ms,
                    sample_rate=sample_rate,
                    channels=channels,
                )
            )
            kit.start_capture(captured.append)
            return len(captured)

        return _measure_operation(
            "capture:wav",
            capture_once,
            iterations=iterations,
            warmup_iterations=warmup_iterations,
            metadata={
                "source": "synthetic-wav",
                "expected_chunks": len(chunks),
                "backend": "wav",
            },
        )


def _benchmark_transcription(
    segments: list[VoiceSegment],
    *,
    iterations: int,
    warmup_iterations: int,
    chunk_duration_ms: int,
    sample_rate: int,
    channels: int,
    voice_activity: VoiceActivityConfig,
    transcription_backend: str,
    transcription_model: str,
    language: str,
    transcription_device: str,
    transcription_compute_type: str,
    transcription_beam_size: int,
    transcription_vad_filter: bool,
) -> BenchmarkResult:
    kit = AuralisVoiceKit(
        VoiceKitConfig(
            sample_rate=sample_rate,
            channels=channels,
            transcription_backend=transcription_backend,
            transcription_model=transcription_model,
            language=language,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_beam_size=transcription_beam_size,
            transcription_vad_filter=transcription_vad_filter,
        )
    )
    session = VoiceSession(
        kit,
        VoiceSessionConfig(
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=voice_activity,
        ),
    )

    return _measure_operation(
        f"transcription:{transcription_backend}",
        lambda: session.transcribe_segments(segments),
        iterations=iterations,
        warmup_iterations=warmup_iterations,
        metadata={
            "segments": len(segments),
            "backend": transcription_backend,
            "model": transcription_model,
            "language": language,
        },
    )


def _measure_operation(
    name: str,
    operation: Callable[[], T],
    *,
    iterations: int,
    warmup_iterations: int,
    metadata: dict[str, object] | None = None,
) -> BenchmarkResult:
    for _ in range(warmup_iterations):
        operation()

    samples = []
    for _ in range(iterations):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1000)

    return _result_from_samples(
        name,
        tuple(samples),
        metadata=metadata or {},
    )


def _result_from_samples(
    name: str,
    samples_ms: tuple[float, ...],
    *,
    metadata: dict[str, object],
) -> BenchmarkResult:
    ordered = tuple(sorted(samples_ms))
    return BenchmarkResult(
        name=name,
        iterations=len(samples_ms),
        samples_ms=samples_ms,
        min_ms=ordered[0],
        mean_ms=fmean(samples_ms),
        median_ms=median(samples_ms),
        p95_ms=_percentile(ordered, 0.95),
        max_ms=ordered[-1],
        total_ms=sum(samples_ms),
        metadata=dict(metadata),
    )


def _percentile(sorted_values: tuple[float, ...], percentile: float) -> float:
    if not sorted_values:
        raise ValueError("at least one sample is required")
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * percentile
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    return lower + (upper - lower) * (position - lower_index)
