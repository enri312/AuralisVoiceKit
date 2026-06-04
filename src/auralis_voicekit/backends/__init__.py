"""Backend implementations and registry helpers."""

from .base import BackendInfo, CaptureBackend, SpeechOutputBackend, TranscriptionBackend
from .null import NullCaptureBackend, NullSpeechOutputBackend, NullTranscriptionBackend
from .registry import BackendRegistry, create_default_registry

__all__ = [
    "BackendInfo",
    "BackendRegistry",
    "CaptureBackend",
    "NullCaptureBackend",
    "NullSpeechOutputBackend",
    "NullTranscriptionBackend",
    "SpeechOutputBackend",
    "TranscriptionBackend",
    "create_default_registry",
]
