"""Pure-Python audio helpers for PCM chunks."""

from __future__ import annotations

from math import sqrt
import struct
import wave

from .models import AudioChunk, AudioEncoding


PCM16_MAX = 32768.0


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
