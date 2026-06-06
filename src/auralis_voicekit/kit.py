"""Main facade for AuralisVoiceKit."""

from __future__ import annotations

from typing import Callable, Iterable

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
        self._output_queue: list[str] = []

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

    @property
    def output_queue_size(self) -> int:
        """Return the number of queued speech items waiting for playback."""

        return len(self._output_queue)

    def queue_speech(self, text: str) -> int:
        """Queue a single utterance and return the new queue size."""

        if text.strip():
            self._output_queue.append(text)
        return len(self._output_queue)

    def queue_speech_many(self, texts: Iterable[str]) -> int:
        """Queue multiple utterances in order and return the new queue size."""

        for text in texts:
            self.queue_speech(text)
        return len(self._output_queue)

    def drain_output_queue(self, *, limit: int | None = None) -> int:
        """Speak queued utterances in order.

        If the backend raises, the current utterance remains queued so callers
        can retry or inspect the failure without silently dropping speech.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero")

        spoken = 0
        while self._output_queue and (limit is None or spoken < limit):
            text = self._output_queue[0]
            self.speak(text)
            self._output_queue.pop(0)
            spoken += 1
        return spoken

    def clear_output_queue(self) -> int:
        """Drop queued speech items and return how many were removed."""

        cleared = len(self._output_queue)
        self._output_queue.clear()
        return cleared

    def backend_report(self):
        return self.registry.backend_info()
