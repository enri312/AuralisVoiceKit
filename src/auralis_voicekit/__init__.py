"""Public package surface for AuralisVoiceKit."""

from ._version import __version__
from .audio import is_silent_pcm16, peak_pcm16, rms_pcm16, write_wav
from .config import VoiceKitConfig
from .events import EventBus, VoiceEvent, VoiceEventType
from .exceptions import (
    AuralisError,
    AudioDeviceNotFound,
    BackendNotAvailable,
    PermissionRequired,
    TranscriptionError,
)
from .kit import AuralisVoiceKit
from .models import AudioChunk, AudioDevice, AudioEncoding, AudioFormat, TranscriptResult

__all__ = [
    "AuralisError",
    "AuralisVoiceKit",
    "AudioChunk",
    "AudioDevice",
    "AudioDeviceNotFound",
    "AudioEncoding",
    "AudioFormat",
    "BackendNotAvailable",
    "EventBus",
    "PermissionRequired",
    "TranscriptResult",
    "TranscriptionError",
    "VoiceEvent",
    "VoiceEventType",
    "VoiceKitConfig",
    "__version__",
    "is_silent_pcm16",
    "peak_pcm16",
    "rms_pcm16",
    "write_wav",
]
