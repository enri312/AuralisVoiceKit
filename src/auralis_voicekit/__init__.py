"""Public package surface for AuralisVoiceKit."""

from ._version import __version__
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
]
