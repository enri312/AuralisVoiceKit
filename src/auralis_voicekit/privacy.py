"""Privacy helpers for event logging."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Callable, TextIO

from .events import EventBus, VoiceEvent, VoiceEventType


DEFAULT_SENSITIVE_KEYS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "audio",
    "audio_bytes",
    "audio_data",
    "authorization",
    "bearer",
    "data",
    "file",
    "filename",
    "input_file",
    "output_file",
    "password",
    "path",
    "prompt",
    "raw",
    "samples",
    "secret",
    "text",
    "token",
    "transcript",
    "transcription",
)


@dataclass(frozen=True, slots=True)
class PrivacyLogConfig:
    """Configuration for sanitized event log records."""

    privacy_mode: bool = True
    sensitive_keys: tuple[str, ...] = DEFAULT_SENSITIVE_KEYS
    redaction: str = "[redacted]"
    max_string_length: int = 512
    max_sequence_items: int = 50
    max_depth: int = 6

    def __post_init__(self) -> None:
        if self.max_string_length <= 0:
            raise ValueError("max_string_length must be greater than zero")
        if self.max_sequence_items <= 0:
            raise ValueError("max_sequence_items must be greater than zero")
        if self.max_depth <= 0:
            raise ValueError("max_depth must be greater than zero")


def sanitize_event_payload(
    payload: Mapping[str, Any],
    config: PrivacyLogConfig | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe event payload with sensitive fields redacted."""

    active_config = config or PrivacyLogConfig()
    return {
        str(key): _sanitize_value(
            value,
            active_config,
            key=str(key),
            depth=0,
        )
        for key, value in payload.items()
    }


def event_to_log_record(
    event: VoiceEvent,
    config: PrivacyLogConfig | None = None,
) -> dict[str, Any]:
    """Convert a voice event to a sanitized JSON-serializable log record."""

    event_type = event.type.value if isinstance(event.type, Enum) else str(event.type)
    return {
        "type": event_type,
        "source": event.source,
        "timestamp": event.timestamp.isoformat(),
        "payload": sanitize_event_payload(event.payload, config),
    }


class PrivacyEventLogger:
    """JSON Lines event logger that sanitizes payloads before writing."""

    def __init__(
        self,
        target: str | Path | TextIO,
        config: PrivacyLogConfig | None = None,
        *,
        flush: bool = True,
    ) -> None:
        self.config = config or PrivacyLogConfig()
        self.flush = flush
        self._owns_stream = not hasattr(target, "write")
        if self._owns_stream:
            path = Path(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._stream: TextIO = path.open("a", encoding="utf-8")
        else:
            self._stream = target  # type: ignore[assignment]

    def write_event(self, event: VoiceEvent) -> dict[str, Any]:
        """Write one event as sanitized JSONL and return the record."""

        record = event_to_log_record(event, self.config)
        self._stream.write(json.dumps(record, sort_keys=True) + "\n")
        if self.flush:
            self._stream.flush()
        return record

    def subscribe(
        self,
        events: EventBus,
        event_type: VoiceEventType = VoiceEventType.ANY,
    ) -> Callable[[], None]:
        """Subscribe this logger to an event bus and return an unsubscribe handle."""

        return events.subscribe(event_type, self.write_event)

    def close(self) -> None:
        """Close the underlying stream when this logger opened it."""

        if self._owns_stream:
            self._stream.close()

    def __enter__(self) -> "PrivacyEventLogger":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _sanitize_value(
    value: Any,
    config: PrivacyLogConfig,
    *,
    key: str | None,
    depth: int,
) -> Any:
    if config.privacy_mode and key is not None and _is_sensitive_key(key, config.sensitive_keys):
        return config.redaction
    if depth >= config.max_depth:
        return "[max-depth]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate_string(value, config.max_string_length)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {
            "type": "bytes",
            "length": len(value),
            "content": config.redaction,
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return _truncate_string(str(value), config.max_string_length)
    if isinstance(value, Mapping):
        return {
            str(child_key): _sanitize_value(
                child_value,
                config,
                key=str(child_key),
                depth=depth + 1,
            )
            for child_key, child_value in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        sanitized = [
            _sanitize_value(item, config, key=None, depth=depth + 1)
            for item in items[: config.max_sequence_items]
        ]
        if len(items) > config.max_sequence_items:
            sanitized.append({"truncated_items": len(items) - config.max_sequence_items})
        return sanitized
    return _truncate_string(str(value), config.max_string_length)


def _is_sensitive_key(key: str, sensitive_keys: tuple[str, ...]) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    if normalized in {item.lower().replace("-", "_") for item in sensitive_keys}:
        return True
    return any(
        marker in normalized
        for marker in (
            "api_key",
            "apikey",
            "authorization",
            "password",
            "secret",
            "token",
        )
    )


def _truncate_string(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[:max_length] + "...[truncated]"
