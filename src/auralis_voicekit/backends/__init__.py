"""Backend implementations and registry helpers."""

from .base import BackendInfo, CaptureBackend, SpeechOutputBackend, TranscriptionBackend
from .null import NullCaptureBackend, NullSpeechOutputBackend, NullTranscriptionBackend
from .registry import BackendRegistry, create_default_registry
from .wav_file import WavFileCaptureBackend

__all__ = [
    "BackendInfo",
    "BackendRegistry",
    "CaptureBackend",
    "NullCaptureBackend",
    "NullSpeechOutputBackend",
    "NullTranscriptionBackend",
    "SpeechOutputBackend",
    "TranscriptionBackend",
    "WavFileCaptureBackend",
    "create_default_registry",
]
