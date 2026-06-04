"""Offline capture backend that emits chunks from a PCM16 WAV file."""

from __future__ import annotations

from typing import Callable, Sequence

from ..audio import iter_wav_chunks
from ..config import VoiceKitConfig
from ..exceptions import AudioSourceError
from ..models import AudioChunk, AudioDevice
from .base import BackendInfo


class WavFileCaptureBackend:
    name = "wav"

    def __init__(self) -> None:
        self.is_running = False

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="capture")

    def list_devices(self) -> Sequence[AudioDevice]:
        return [
            AudioDevice(
                id="wav-file",
                name="PCM16 WAV file",
                kind="input",
                is_default=True,
            )
        ]

    def start(self, config: VoiceKitConfig, on_audio: Callable[[AudioChunk], None]) -> None:
        path = config.input_file
        if path is None and isinstance(config.input_device, str):
            path = config.input_device
        if path is None:
            raise AudioSourceError("The wav capture backend requires config.input_file")

        self.is_running = True
        try:
            for chunk in iter_wav_chunks(path, chunk_duration_ms=config.capture_block_ms):
                if not self.is_running:
                    break
                on_audio(chunk)
        finally:
            self.is_running = False

    def stop(self) -> None:
        self.is_running = False
