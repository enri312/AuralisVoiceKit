"""Public package surface for AuralisVoiceKit."""

from ._version import __version__
from .audio import (
    NoiseProfile,
    VoiceActivityConfig,
    VoiceActivityDetector,
    VoiceSegment,
    WavMetadata,
    calibrate_noise_pcm16,
    iter_wav_chunks,
    is_silent_pcm16,
    peak_pcm16,
    read_wav,
    read_wav_metadata,
    rms_pcm16,
    segment_voice_pcm16,
    write_wav,
)
from .config import VoiceKitConfig
from .events import EventBus, VoiceEvent, VoiceEventType
from .exceptions import (
    AuralisError,
    AudioDeviceNotFound,
    AudioSourceError,
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
    "AudioSourceError",
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
    "NoiseProfile",
    "VoiceActivityConfig",
    "VoiceActivityDetector",
    "VoiceSegment",
    "WavMetadata",
    "__version__",
    "calibrate_noise_pcm16",
    "iter_wav_chunks",
    "is_silent_pcm16",
    "peak_pcm16",
    "read_wav",
    "read_wav_metadata",
    "rms_pcm16",
    "segment_voice_pcm16",
    "write_wav",
]
