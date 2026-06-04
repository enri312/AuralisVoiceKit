"""Data models shared by the core and optional backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AudioEncoding(str, Enum):
    PCM16 = "pcm16"
    FLOAT32 = "float32"


@dataclass(frozen=True, slots=True)
class AudioFormat:
    sample_rate: int = 16_000
    channels: int = 1
    sample_width: int = 2
    encoding: AudioEncoding = AudioEncoding.PCM16

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")
        if self.channels <= 0:
            raise ValueError("channels must be greater than zero")
        if self.sample_width <= 0:
            raise ValueError("sample_width must be greater than zero")

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate * self.channels * self.sample_width


@dataclass(frozen=True, slots=True)
class AudioChunk:
    data: bytes
    format: AudioFormat = field(default_factory=AudioFormat)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return len(self.data) / self.format.bytes_per_second


@dataclass(frozen=True, slots=True)
class TranscriptResult:
    text: str
    confidence: float | None = None
    language: str | None = None
    is_final: bool = True
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudioDevice:
    id: str
    name: str
    kind: str
    channels: int | None = None
    host_api: str | None = None
    is_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
