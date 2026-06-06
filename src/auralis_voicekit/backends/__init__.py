"""Backend implementations and registry helpers."""

from .base import BackendInfo, CaptureBackend, SpeechOutputBackend, TranscriptionBackend
from .null import NullCaptureBackend, NullSpeechOutputBackend, NullTranscriptionBackend
from .openai_transcription import OpenAITranscriptionBackend
from .pyaudio_capture import PyAudioCaptureBackend
from .registry import BackendRegistry, create_default_registry
from .system_output import SystemSpeechOutputBackend, SystemVoice
from .wasapi import WasapiCaptureBackend, WasapiDiagnosticSnapshot, inspect_wasapi_environment
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
    "PyAudioCaptureBackend",
    "SpeechOutputBackend",
    "SystemSpeechOutputBackend",
    "SystemVoice",
    "TranscriptionBackend",
    "WasapiCaptureBackend",
    "WasapiDiagnosticSnapshot",
    "WavFileCaptureBackend",
    "WhisperTranscriptionBackend",
    "create_default_registry",
    "inspect_wasapi_environment",
]
