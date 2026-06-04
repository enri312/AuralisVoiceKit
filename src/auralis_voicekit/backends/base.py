"""Backend contracts for capture, transcription and output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, Sequence

from ..config import VoiceKitConfig
from ..models import AudioChunk, AudioDevice, TranscriptResult


@dataclass(frozen=True, slots=True)
class BackendInfo:
    name: str
    kind: str
    available: bool = True
    reason: str | None = None
    dependencies: tuple[str, ...] = field(default_factory=tuple)


class CaptureBackend(Protocol):
    name: str

    def info(self) -> BackendInfo:
        ...

    def list_devices(self) -> Sequence[AudioDevice]:
        ...

    def start(self, config: VoiceKitConfig, on_audio: Callable[[AudioChunk], None]) -> None:
        ...

    def stop(self) -> None:
        ...


class TranscriptionBackend(Protocol):
    name: str

    def info(self) -> BackendInfo:
        ...

    def transcribe(self, chunk: AudioChunk, config: VoiceKitConfig) -> TranscriptResult:
        ...


class SpeechOutputBackend(Protocol):
    name: str

    def info(self) -> BackendInfo:
        ...

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        ...
