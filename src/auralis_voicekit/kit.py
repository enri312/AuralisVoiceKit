"""Main facade for AuralisVoiceKit."""

from __future__ import annotations

from typing import Callable

from .backends import BackendRegistry, create_default_registry
from .config import VoiceKitConfig
from .events import EventBus, VoiceEventType
from .models import AudioChunk, TranscriptResult


class AuralisVoiceKit:
    """High-level entry point for capture, transcription and output."""

    def __init__(
        self,
        config: VoiceKitConfig | None = None,
        registry: BackendRegistry | None = None,
        events: EventBus | None = None,
    ) -> None:
        self.config = config or VoiceKitConfig()
        self.registry = registry or create_default_registry()
        self.events = events or EventBus()
        self.capture = self.registry.create_capture(self.config.capture_backend)
        self.transcriber = self.registry.create_transcription(self.config.transcription_backend)
        self.output = self.registry.create_output(self.config.output_backend)

    def start_capture(self, on_audio: Callable[[AudioChunk], None] | None = None) -> None:
        def handle_audio(chunk: AudioChunk) -> None:
            payload = {"duration_seconds": chunk.duration_seconds}
            if not self.config.privacy_mode:
                payload["bytes"] = len(chunk.data)
            self.events.emit(VoiceEventType.AUDIO_CHUNK, payload)
            if on_audio is not None:
                on_audio(chunk)

        self.capture.start(self.config, handle_audio)
        self.events.emit(
            VoiceEventType.CAPTURE_STARTED,
            {"backend": self.config.capture_backend},
        )

    def stop_capture(self) -> None:
        self.capture.stop()
        self.events.emit(
            VoiceEventType.CAPTURE_STOPPED,
            {"backend": self.config.capture_backend},
        )

    def transcribe(self, chunk: AudioChunk) -> TranscriptResult:
        self.events.emit(
            VoiceEventType.TRANSCRIPTION_STARTED,
            {"backend": self.config.transcription_backend},
        )
        result = self.transcriber.transcribe(chunk, self.config)
        payload = {
            "backend": self.config.transcription_backend,
            "is_final": result.is_final,
        }
        if not self.config.privacy_mode:
            payload["text"] = result.text
        self.events.emit(VoiceEventType.TRANSCRIPTION_COMPLETED, payload)
        return result

    def speak(self, text: str) -> None:
        self.events.emit(VoiceEventType.OUTPUT_STARTED, {"backend": self.config.output_backend})
        self.output.speak(text, self.config)
        self.events.emit(VoiceEventType.OUTPUT_COMPLETED, {"backend": self.config.output_backend})

    def backend_report(self):
        return self.registry.backend_info()
