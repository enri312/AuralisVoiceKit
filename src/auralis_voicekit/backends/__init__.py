"""Backend implementations and registry helpers."""

from .base import BackendInfo, CaptureBackend, SpeechOutputBackend, TranscriptionBackend
from .null import NullCaptureBackend, NullSpeechOutputBackend, NullTranscriptionBackend
from .openai_transcription import OpenAITranscriptionBackend
from .registry import BackendRegistry, create_default_registry
from .system_output import SystemSpeechOutputBackend
from .wasapi import WasapiCaptureBackend
from .wav_file import WavFileCaptureBackend
from .whisper_transcription import WhisperTranscriptionBackend

__all__ = [
    "BackendInfo",
    "BackendRegistry",
    "CaptureBackend",
    "NullCaptureBackend",
    "NullSpeechOutputBackend",
    "NullTranscriptionBackend",
    "OpenAITranscriptionBackend",
    "SpeechOutputBackend",
    "SystemSpeechOutputBackend",
    "TranscriptionBackend",
    "WasapiCaptureBackend",
    "WavFileCaptureBackend",
    "WhisperTranscriptionBackend",
    "create_default_registry",
]
