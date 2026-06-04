"""Null backends that make the core usable without hardware."""

from __future__ import annotations

from typing import Callable, Sequence

from ..config import VoiceKitConfig
from ..models import AudioChunk, AudioDevice, TranscriptResult
from .base import BackendInfo


class NullCaptureBackend:
    name = "null"

    def __init__(self) -> None:
        self.is_running = False
        self._on_audio: Callable[[AudioChunk], None] | None = None

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="capture")

    def list_devices(self) -> Sequence[AudioDevice]:
        return [
            AudioDevice(
                id="null-input",
                name="Null input",
                kind="input",
                channels=1,
                is_default=True,
            )
        ]

    def start(self, config: VoiceKitConfig, on_audio: Callable[[AudioChunk], None]) -> None:
        self.is_running = True
        self._on_audio = on_audio

    def push(self, chunk: AudioChunk) -> None:
        if self._on_audio is not None:
            self._on_audio(chunk)

    def stop(self) -> None:
        self.is_running = False
        self._on_audio = None


class NullTranscriptionBackend:
    name = "null"

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="transcription")

    def transcribe(self, chunk: AudioChunk, config: VoiceKitConfig) -> TranscriptResult:
        return TranscriptResult(
            text="",
            language=config.language,
            source=self.name,
            metadata={"duration_seconds": chunk.duration_seconds},
        )


class NullSpeechOutputBackend:
    name = "null"

    def __init__(self) -> None:
        self.utterances: list[str] = []

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="output")

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        self.utterances.append(text)
