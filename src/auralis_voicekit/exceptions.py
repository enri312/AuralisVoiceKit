"""Package-specific exceptions."""


class AuralisError(Exception):
    """Base exception for AuralisVoiceKit."""


class BackendNotAvailable(AuralisError):
    """Raised when a requested backend cannot be loaded."""


class PermissionRequired(AuralisError):
    """Raised when microphone or output permissions are required."""


class AudioDeviceNotFound(AuralisError):
    """Raised when a requested audio device cannot be found."""


class AudioSourceError(AuralisError):
    """Raised when an audio file or source cannot be used."""


class TranscriptionError(AuralisError):
    """Raised when transcription fails."""
