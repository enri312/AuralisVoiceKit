"""Configuration primitives for AuralisVoiceKit."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any

from .models import AudioFormat


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(slots=True)
class VoiceKitConfig:
    """Runtime configuration for capture, transcription and voice events."""

    sample_rate: int = 16_000
    channels: int = 1
    sample_width: int = 2
    language: str = "es"
    capture_backend: str = "null"
    transcription_backend: str = "null"
    transcription_model: str = "auto"
    transcription_prompt: str | None = None
    transcription_response_format: str = "json"
    transcription_device: str = "auto"
    transcription_compute_type: str = "default"
    transcription_beam_size: int = 5
    transcription_vad_filter: bool = False
    output_backend: str = "null"
    input_device: str | int | None = None
    output_device: str | int | None = None
    input_file: str | None = None
    capture_block_ms: int = 50
    capture_latency: str | float | None = None
    privacy_mode: bool = True
    log_level: str = "INFO"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")
        if self.channels <= 0:
            raise ValueError("channels must be greater than zero")
        if self.sample_width <= 0:
            raise ValueError("sample_width must be greater than zero")
        if self.capture_block_ms <= 0:
            raise ValueError("capture_block_ms must be greater than zero")
        if self.transcription_beam_size <= 0:
            raise ValueError("transcription_beam_size must be greater than zero")

    @classmethod
    def from_env(cls, prefix: str = "AURALIS_") -> "VoiceKitConfig":
        """Create config from environment variables."""

        return cls(
            sample_rate=_env_int(os.getenv(prefix + "SAMPLE_RATE"), 16_000),
            channels=_env_int(os.getenv(prefix + "CHANNELS"), 1),
            sample_width=_env_int(os.getenv(prefix + "SAMPLE_WIDTH"), 2),
            language=os.getenv(prefix + "LANGUAGE", "es"),
            capture_backend=os.getenv(prefix + "CAPTURE_BACKEND", "null"),
            transcription_backend=os.getenv(prefix + "TRANSCRIPTION_BACKEND", "null"),
            transcription_model=os.getenv(prefix + "TRANSCRIPTION_MODEL", "auto"),
            transcription_prompt=os.getenv(prefix + "TRANSCRIPTION_PROMPT") or None,
            transcription_response_format=os.getenv(prefix + "TRANSCRIPTION_RESPONSE_FORMAT", "json"),
            transcription_device=os.getenv(prefix + "TRANSCRIPTION_DEVICE", "auto"),
            transcription_compute_type=os.getenv(prefix + "TRANSCRIPTION_COMPUTE_TYPE", "default"),
            transcription_beam_size=_env_int(os.getenv(prefix + "TRANSCRIPTION_BEAM_SIZE"), 5),
            transcription_vad_filter=_env_bool(os.getenv(prefix + "TRANSCRIPTION_VAD_FILTER"), False),
            output_backend=os.getenv(prefix + "OUTPUT_BACKEND", "null"),
            input_device=os.getenv(prefix + "INPUT_DEVICE") or None,
            output_device=os.getenv(prefix + "OUTPUT_DEVICE") or None,
            input_file=os.getenv(prefix + "INPUT_FILE") or None,
            capture_block_ms=_env_int(os.getenv(prefix + "CAPTURE_BLOCK_MS"), 50),
            capture_latency=os.getenv(prefix + "CAPTURE_LATENCY") or None,
            privacy_mode=_env_bool(os.getenv(prefix + "PRIVACY_MODE"), True),
            log_level=os.getenv(prefix + "LOG_LEVEL", "INFO"),
        )

    def audio_format(self) -> AudioFormat:
        """Return the current PCM audio format."""

        return AudioFormat(
            sample_rate=self.sample_rate,
            channels=self.channels,
            sample_width=self.sample_width,
        )

    @property
    def capture_block_frames(self) -> int:
        """Return the number of frames per capture callback."""

        return max(1, int(self.sample_rate * self.capture_block_ms / 1000))
