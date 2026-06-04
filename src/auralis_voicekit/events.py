"""Small event system used by the voice kit."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class VoiceEventType(str, Enum):
    ANY = "*"
    CAPTURE_STARTED = "capture.started"
    CAPTURE_STOPPED = "capture.stopped"
    AUDIO_CHUNK = "audio.chunk"
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    OUTPUT_STARTED = "output.started"
    OUTPUT_COMPLETED = "output.completed"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class VoiceEvent:
    type: VoiceEventType
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "auralis"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


Listener = Callable[[VoiceEvent], None]


class EventBus:
    """In-process event bus with unsubscribe handles."""

    def __init__(self) -> None:
        self._listeners: dict[VoiceEventType, list[Listener]] = defaultdict(list)

    def subscribe(self, event_type: VoiceEventType, listener: Listener) -> Callable[[], None]:
        self._listeners[event_type].append(listener)

        def unsubscribe() -> None:
            listeners = self._listeners[event_type]
            if listener in listeners:
                listeners.remove(listener)

        return unsubscribe

    def emit(
        self,
        event_type: VoiceEventType,
        payload: dict[str, Any] | None = None,
        source: str = "auralis",
    ) -> VoiceEvent:
        event = VoiceEvent(type=event_type, payload=payload or {}, source=source)
        listeners = [*self._listeners[event_type], *self._listeners[VoiceEventType.ANY]]
        for listener in listeners:
            listener(event)
        return event

    def listener_count(self, event_type: VoiceEventType) -> int:
        return len(self._listeners[event_type])
