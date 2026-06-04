"""Pure-Python audio helpers for PCM chunks."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import fmean, median
import struct
from typing import Iterable
import wave

from .models import AudioChunk, AudioEncoding


PCM16_MAX = 32768.0


@dataclass(frozen=True, slots=True)
class NoiseProfile:
    """Measured ambient noise profile for PCM16 audio."""

    noise_floor: float
    threshold: float
    peak_floor: float
    chunks: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class VoiceActivityConfig:
    """Configuration for simple RMS-based voice activity detection."""

    threshold: float = 0.01
    min_voice_ms: int = 120
    max_silence_ms: int = 350
    pre_speech_ms: int = 100

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("threshold must be greater than or equal to zero")
        if self.min_voice_ms <= 0:
            raise ValueError("min_voice_ms must be greater than zero")
        if self.max_silence_ms <= 0:
            raise ValueError("max_silence_ms must be greater than zero")
        if self.pre_speech_ms < 0:
            raise ValueError("pre_speech_ms must be greater than or equal to zero")


@dataclass(frozen=True, slots=True)
class VoiceSegment:
    """A group of chunks that likely contains speech."""

    chunks: tuple[AudioChunk, ...]
    threshold: float

    def __post_init__(self) -> None:
        if not self.chunks:
            raise ValueError("VoiceSegment requires at least one chunk")

    @property
    def duration_seconds(self) -> float:
        return sum(chunk.duration_seconds for chunk in self.chunks)

    @property
    def data(self) -> bytes:
        return b"".join(chunk.data for chunk in self.chunks)

    @property
    def rms(self) -> float:
        values = [rms_pcm16(chunk) for chunk in self.chunks]
        return fmean(values) if values else 0.0


def _pcm16_samples(chunk: AudioChunk):
    if chunk.format.encoding is not AudioEncoding.PCM16 or chunk.format.sample_width != 2:
        raise ValueError("Only PCM16 chunks are supported")
    data = chunk.data
    if len(data) < 2:
        return ()
    usable = len(data) - (len(data) % 2)
    return (sample[0] for sample in struct.iter_unpack("<h", data[:usable]))


def rms_pcm16(chunk: AudioChunk) -> float:
    """Return normalized RMS energy for a PCM16 chunk."""

    total = 0
    count = 0
    for sample in _pcm16_samples(chunk):
        total += sample * sample
        count += 1
    if count == 0:
        return 0.0
    return min(1.0, sqrt(total / count) / PCM16_MAX)


def peak_pcm16(chunk: AudioChunk) -> float:
    """Return normalized peak amplitude for a PCM16 chunk."""

    peak = 0
    for sample in _pcm16_samples(chunk):
        peak = max(peak, abs(sample))
    return min(1.0, peak / PCM16_MAX)


def is_silent_pcm16(chunk: AudioChunk, threshold: float = 0.01) -> bool:
    """Return whether a PCM16 chunk is below the RMS silence threshold."""

    if threshold < 0:
        raise ValueError("threshold must be greater than or equal to zero")
    return rms_pcm16(chunk) < threshold


def calibrate_noise_pcm16(
    chunks: Iterable[AudioChunk],
    *,
    multiplier: float = 3.0,
    min_threshold: float = 0.01,
    max_threshold: float = 0.35,
) -> NoiseProfile:
    """Estimate ambient noise and derive a voice threshold from PCM16 chunks."""

    if multiplier <= 0:
        raise ValueError("multiplier must be greater than zero")
    if min_threshold < 0:
        raise ValueError("min_threshold must be greater than or equal to zero")
    if max_threshold < min_threshold:
        raise ValueError("max_threshold must be greater than or equal to min_threshold")

    chunk_list = list(chunks)
    if not chunk_list:
        raise ValueError("At least one chunk is required")

    rms_values = [rms_pcm16(chunk) for chunk in chunk_list]
    peak_values = [peak_pcm16(chunk) for chunk in chunk_list]
    noise_floor = median(rms_values)
    peak_floor = median(peak_values)
    threshold = max(min_threshold, noise_floor * multiplier)
    threshold = min(max_threshold, threshold)

    return NoiseProfile(
        noise_floor=noise_floor,
        threshold=threshold,
        peak_floor=peak_floor,
        chunks=len(chunk_list),
        duration_seconds=sum(chunk.duration_seconds for chunk in chunk_list),
    )


class VoiceActivityDetector:
    """Simple pure-Python RMS voice activity detector for PCM16 chunks."""

    def __init__(
        self,
        config: VoiceActivityConfig | None = None,
        noise_profile: NoiseProfile | None = None,
    ) -> None:
        self.config = config or VoiceActivityConfig()
        self.noise_profile = noise_profile
        self.threshold = noise_profile.threshold if noise_profile else self.config.threshold

    def is_voice(self, chunk: AudioChunk) -> bool:
        return rms_pcm16(chunk) >= self.threshold

    def segment(self, chunks: Iterable[AudioChunk]) -> list[VoiceSegment]:
        return segment_voice_pcm16(chunks, config=self.config, threshold=self.threshold)


def _append_limited_by_duration(
    chunks: list[AudioChunk],
    chunk: AudioChunk,
    max_duration_seconds: float,
) -> None:
    chunks.append(chunk)
    while chunks and sum(item.duration_seconds for item in chunks) > max_duration_seconds:
        chunks.pop(0)


def segment_voice_pcm16(
    chunks: Iterable[AudioChunk],
    *,
    config: VoiceActivityConfig | None = None,
    threshold: float | None = None,
) -> list[VoiceSegment]:
    """Split PCM16 chunks into speech-like segments using RMS energy."""

    detector_config = config or VoiceActivityConfig()
    active_threshold = detector_config.threshold if threshold is None else threshold
    if active_threshold < 0:
        raise ValueError("threshold must be greater than or equal to zero")

    segments: list[VoiceSegment] = []
    current_segment: list[AudioChunk] = []
    candidate_voice: list[AudioChunk] = []
    recent_silence: list[AudioChunk] = []
    in_segment = False
    voice_duration = 0.0
    silence_duration = 0.0
    min_voice_seconds = detector_config.min_voice_ms / 1000
    max_silence_seconds = detector_config.max_silence_ms / 1000
    pre_speech_seconds = detector_config.pre_speech_ms / 1000

    for chunk in chunks:
        chunk_is_voice = rms_pcm16(chunk) >= active_threshold
        duration = chunk.duration_seconds

        if in_segment:
            current_segment.append(chunk)
            if chunk_is_voice:
                silence_duration = 0.0
            else:
                silence_duration += duration
                if silence_duration >= max_silence_seconds:
                    segments.append(VoiceSegment(tuple(current_segment), active_threshold))
                    current_segment = []
                    in_segment = False
                    silence_duration = 0.0
            continue

        if chunk_is_voice:
            candidate_voice.append(chunk)
            voice_duration += duration
            if voice_duration >= min_voice_seconds:
                current_segment = [*recent_silence, *candidate_voice]
                candidate_voice = []
                recent_silence = []
                voice_duration = 0.0
                in_segment = True
            continue

        candidate_voice = []
        voice_duration = 0.0
        if pre_speech_seconds > 0:
            _append_limited_by_duration(recent_silence, chunk, pre_speech_seconds)

    if in_segment and current_segment:
        segments.append(VoiceSegment(tuple(current_segment), active_threshold))

    return segments


def write_wav(path: str, chunks: list[AudioChunk]) -> None:
    """Write PCM16 chunks to a WAV file."""

    if not chunks:
        raise ValueError("At least one chunk is required")

    audio_format = chunks[0].format
    if audio_format.encoding is not AudioEncoding.PCM16 or audio_format.sample_width != 2:
        raise ValueError("Only PCM16 WAV output is supported")

    for chunk in chunks:
        if chunk.format != audio_format:
            raise ValueError("All chunks must use the same audio format")

    with wave.open(path, "wb") as output:
        output.setnchannels(audio_format.channels)
        output.setsampwidth(audio_format.sample_width)
        output.setframerate(audio_format.sample_rate)
        for chunk in chunks:
            output.writeframes(chunk.data)
