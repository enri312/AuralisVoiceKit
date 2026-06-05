"""Windows audio troubleshooting helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import platform
from typing import Any


@dataclass(frozen=True, slots=True)
class WindowsAudioErrorHint:
    """Actionable hint for common Windows audio failures."""

    category: str
    title: str
    message: str
    actions: tuple[str, ...] = field(default_factory=tuple)
    backend: str | None = None
    device: str | int | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "actions": list(self.actions),
            "backend": self.backend,
            "device": self.device,
            "error": self.error,
        }

    def format_hint(self) -> str:
        actions = " ".join(f"{index}. {action}" for index, action in enumerate(self.actions, 1))
        if actions:
            return f"{self.title}: {self.message} Actions: {actions}"
        return f"{self.title}: {self.message}"


def windows_audio_error_hint(
    error: object,
    *,
    backend: str | None = None,
    device: str | int | None = None,
    system: str | None = None,
) -> WindowsAudioErrorHint:
    """Classify a Windows audio error and return concrete recovery steps."""

    active_system = system or platform.system()
    text = _error_text(error)
    normalized = text.casefold()

    if active_system != "Windows":
        return WindowsAudioErrorHint(
            category="not_windows",
            title="Windows audio hint unavailable",
            message="This helper is specific to Windows audio capture failures.",
            actions=("Run auralis doctor for platform-specific diagnostics.",),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(normalized, ("unknown capture backend", "unknown output backend", "unknown transcription backend")):
        return WindowsAudioErrorHint(
            category="backend_selection",
            title="Auralis backend selection failed",
            message="The requested backend name is not registered.",
            actions=(
                "Run auralis backends to inspect available backends.",
                "Use --backend wasapi or --backend sounddevice for live Windows microphone capture.",
                "Use --backend wav or --backend null for offline checks.",
                "Check spelling if you registered a custom backend.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(normalized, ("winerror 5", "access is denied", "permission", "privacy")):
        return WindowsAudioErrorHint(
            category="microphone_permission",
            title="Windows microphone permission may be blocked",
            message="Windows can block desktop Python processes from opening the microphone.",
            actions=(
                "Open Settings > Privacy & security > Microphone.",
                "Enable Microphone access and Let desktop apps access your microphone.",
                "Restart the terminal or app running Python after changing permissions.",
                "Run auralis doctor --capture-test --backend wasapi --device default --json.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(
        normalized,
        ("invalid device", "device unavailable", "no input device", "no default input", "paerrorcode -9996", "paerrorcode -9985"),
    ):
        return WindowsAudioErrorHint(
            category="input_device",
            title="Windows input device selection failed",
            message="The selected microphone may be disconnected, disabled or not exposed through the requested host API.",
            actions=(
                "Run auralis doctor --devices --backend wasapi --json to inspect WASAPI devices.",
                "Try --device default or choose an id from auralis devices --backend wasapi.",
                "Check Windows Sound settings and confirm the input device is enabled.",
                "Unplug and reconnect USB or Bluetooth microphones before retrying.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(normalized, ("sample rate", "invalid sample rate", "paerrorcode -9997")):
        return WindowsAudioErrorHint(
            category="sample_rate",
            title="Windows rejected the requested sample rate",
            message="The microphone or shared-mode driver may not accept the configured sample rate.",
            actions=(
                "Try sample_rate=48000 or sample_rate=44100 in VoiceKitConfig.",
                "Check the device Default Format in Windows Sound > More sound settings.",
                "Run a short capture test with --capture-seconds 0.25.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(normalized, ("channel", "channels", "paerrorcode -9998")):
        return WindowsAudioErrorHint(
            category="channels",
            title="Windows rejected the requested channel count",
            message="The selected input may not support the configured number of channels.",
            actions=(
                "Use channels=1 for microphone capture.",
                "Inspect device channel counts with auralis doctor --devices --backend wasapi --json.",
                "Select a different input device if the reported channel count is zero.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(
        normalized,
        ("wasapi host api", "unanticipated host error", "paerrorcode -9999", "exclusive mode", "host api"),
    ):
        return WindowsAudioErrorHint(
            category="host_api",
            title="Windows audio host API failed",
            message="WASAPI or PortAudio reported a host-level error while opening the input stream.",
            actions=(
                "Close apps that may be using the microphone in exclusive mode.",
                "Try --backend wasapi first, then --backend sounddevice if needed.",
                "Disable exclusive control in Windows Sound > Recording device > Advanced.",
                "Run auralis doctor --devices --backend wasapi --json and review host APIs.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    if _contains_any(normalized, ("sounddevice", "portaudio", "no module named")):
        return WindowsAudioErrorHint(
            category="dependency",
            title="Windows audio dependency is missing",
            message="The selected capture backend needs the optional sounddevice dependency.",
            actions=(
                "Install with: python -m pip install \"auralisvoicekit[sounddevice]\".",
                "Run python -m auralis_voicekit.cli doctor after installing.",
                "Use the wav backend for offline tests while audio dependencies are missing.",
            ),
            backend=backend,
            device=device,
            error=text,
        )

    return WindowsAudioErrorHint(
        category="generic",
        title="Windows audio capture failed",
        message="The error did not match a known Windows audio pattern, but doctor can collect the next useful details.",
        actions=(
            "Run auralis doctor --devices --backend wasapi --json.",
            "Run auralis doctor --capture-test --backend wasapi --device default --json.",
            "Try the wav backend to confirm the core works without live audio.",
        ),
        backend=backend,
        device=device,
        error=text,
    )


def _error_text(error: object) -> str:
    if isinstance(error, BaseException):
        text = str(error)
        if not text:
            text = error.__class__.__name__
        return text
    return str(error)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)
