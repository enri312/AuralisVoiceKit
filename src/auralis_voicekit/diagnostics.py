"""Structured diagnostics for local AuralisVoiceKit environments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from importlib.util import find_spec
import platform
import shutil
import sys
import time
from typing import Any

from ._version import __version__
from .audio import (
    ffmpeg_install_hint,
    ffmpeg_search_locations,
    read_wav_metadata,
    resolve_ffmpeg_executable,
)
from .backends import create_default_registry
from .config import VoiceKitConfig
from .exceptions import AudioSourceError, BackendNotAvailable
from .kit import AuralisVoiceKit
from .models import AudioChunk


class DiagnosticStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    name: str
    status: DiagnosticStatus
    message: str
    hint: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True, slots=True)
class DoctorReport:
    version: str
    python: str
    implementation: str
    platform: str
    system: str
    checks: tuple[DiagnosticCheck, ...]

    @property
    def status(self) -> DiagnosticStatus:
        statuses = {check.status for check in self.checks}
        if DiagnosticStatus.ERROR in statuses:
            return DiagnosticStatus.ERROR
        if DiagnosticStatus.WARNING in statuses:
            return DiagnosticStatus.WARNING
        return DiagnosticStatus.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "python": self.python,
            "implementation": self.implementation,
            "platform": self.platform,
            "system": self.system,
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
        }


def _platform_hint(system: str) -> str:
    if system == "Windows":
        return "Check Windows microphone privacy settings if real capture cannot start."
    if system == "Linux":
        return "On Ubuntu/Linux, install PortAudio system packages if sounddevice cannot open audio."
    if system == "Darwin":
        return "On macOS, grant microphone permission to the terminal or app running Python."
    return "Use the wav backend for offline tests when real audio devices are unavailable."


def _check_python() -> DiagnosticCheck:
    version_info = sys.version_info
    if version_info < (3, 10):
        return DiagnosticCheck(
            name="python",
            status=DiagnosticStatus.ERROR,
            message=f"Python {version_info.major}.{version_info.minor} is not supported.",
            hint="Use Python 3.10 or newer.",
            details={"requires": ">=3.10"},
        )
    return DiagnosticCheck(
        name="python",
        status=DiagnosticStatus.OK,
        message=f"Python {sys.version.split()[0]} is supported.",
        details={"requires": ">=3.10"},
    )


def _check_optional_dependency(module_name: str, install_hint: str) -> DiagnosticCheck:
    if find_spec(module_name) is not None:
        return DiagnosticCheck(
            name=f"dependency:{module_name}",
            status=DiagnosticStatus.OK,
            message=f"Optional dependency {module_name!r} is available.",
        )
    return DiagnosticCheck(
        name=f"dependency:{module_name}",
        status=DiagnosticStatus.WARNING,
        message=f"Optional dependency {module_name!r} is not installed.",
        hint=install_hint,
    )


def _check_optional_executable(executable: str, install_hint: str) -> DiagnosticCheck:
    path = resolve_ffmpeg_executable(executable) if executable == "ffmpeg" else shutil.which(executable)
    if path is not None:
        return DiagnosticCheck(
            name=f"executable:{executable}",
            status=DiagnosticStatus.OK,
            message=f"Optional executable {executable!r} is available.",
            details={
                "path": path,
                "search": list(ffmpeg_search_locations(executable)) if executable == "ffmpeg" else [],
            },
        )
    hint = ffmpeg_install_hint() if executable == "ffmpeg" else install_hint
    return DiagnosticCheck(
        name=f"executable:{executable}",
        status=DiagnosticStatus.WARNING,
        message=f"Optional executable {executable!r} is not installed or could not be resolved.",
        hint=hint,
        details={"search": list(ffmpeg_search_locations(executable)) if executable == "ffmpeg" else []},
    )


def _backend_checks() -> list[DiagnosticCheck]:
    checks = []
    for info in create_default_registry().backend_info():
        status = DiagnosticStatus.OK if info.available else DiagnosticStatus.WARNING
        hint = None
        if not info.available and info.dependencies:
            deps = ", ".join(info.dependencies)
            hint = f"Install optional dependencies for {info.name}: {deps}."
        checks.append(
            DiagnosticCheck(
                name=f"backend:{info.kind}:{info.name}",
                status=status,
                message=info.reason or f"{info.kind} backend {info.name!r} is available.",
                hint=hint,
                details={"dependencies": list(info.dependencies)},
            )
        )
    return checks


def _device_check(capture_backend: str) -> DiagnosticCheck:
    registry = create_default_registry()
    try:
        backend = registry.create_capture(capture_backend)
        devices = list(backend.list_devices())
    except BackendNotAvailable as exc:
        return DiagnosticCheck(
            name=f"devices:{capture_backend}",
            status=DiagnosticStatus.WARNING,
            message=f"Cannot inspect devices for {capture_backend!r}: {exc}",
            hint="Use --backend wav for offline checks or install the requested backend.",
        )

    if not devices:
        return DiagnosticCheck(
            name=f"devices:{capture_backend}",
            status=DiagnosticStatus.WARNING,
            message=f"No input devices were reported by {capture_backend!r}.",
            hint="Use the wav backend for offline tests or check OS audio permissions.",
        )
    return DiagnosticCheck(
        name=f"devices:{capture_backend}",
        status=DiagnosticStatus.OK,
        message=f"{len(devices)} input device(s) reported by {capture_backend!r}.",
        details={
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "kind": device.kind,
                    "channels": device.channels,
                    "host_api": device.host_api,
                    "is_default": device.is_default,
                }
                for device in devices
            ]
        },
    )


def _wav_check(path: str) -> DiagnosticCheck:
    try:
        metadata = read_wav_metadata(path)
    except AudioSourceError as exc:
        return DiagnosticCheck(
            name="wav",
            status=DiagnosticStatus.ERROR,
            message=str(exc),
            hint="Use an uncompressed PCM16 WAV file.",
        )
    return DiagnosticCheck(
        name="wav",
        status=DiagnosticStatus.OK,
        message=f"WAV file is readable ({metadata.duration_seconds:.3f}s).",
        details={
            "path": metadata.path,
            "sample_rate": metadata.format.sample_rate,
            "channels": metadata.format.channels,
            "sample_width": metadata.format.sample_width,
            "frames": metadata.frames,
            "duration_seconds": metadata.duration_seconds,
        },
    )


def _capture_test_check(
    capture_backend: str,
    *,
    seconds: float,
    input_device: str | int | None,
) -> DiagnosticCheck:
    name = f"capture-test:{capture_backend}"
    if seconds <= 0:
        return DiagnosticCheck(
            name=name,
            status=DiagnosticStatus.ERROR,
            message="Capture test duration must be greater than zero.",
            hint="Use --capture-seconds with a positive value such as 0.25.",
            details={"requested_seconds": seconds},
        )

    chunks_received = 0
    bytes_received = 0

    def handle_chunk(chunk: AudioChunk) -> None:
        nonlocal chunks_received, bytes_received
        chunks_received += 1
        bytes_received += len(chunk.data)

    config = VoiceKitConfig(
        capture_backend=capture_backend,
        input_device=input_device,
        privacy_mode=True,
    )
    started = False
    started_at = time.monotonic()
    try:
        kit = AuralisVoiceKit(config)
        kit.start_capture(handle_chunk)
        started = True
        time.sleep(seconds)
    except Exception as exc:
        return DiagnosticCheck(
            name=name,
            status=DiagnosticStatus.ERROR,
            message=f"Capture backend {capture_backend!r} could not be opened: {exc}",
            hint=_platform_hint(platform.system()),
            details={
                "backend": capture_backend,
                "input_device": input_device,
                "requested_seconds": seconds,
                "elapsed_seconds": round(time.monotonic() - started_at, 6),
                "error_type": type(exc).__name__,
            },
        )
    finally:
        if started:
            try:
                kit.stop_capture()
            except Exception:
                pass

    return DiagnosticCheck(
        name=name,
        status=DiagnosticStatus.OK,
        message=f"Capture backend {capture_backend!r} opened for {seconds:.3f}s.",
        details={
            "backend": capture_backend,
            "input_device": input_device,
            "requested_seconds": seconds,
            "elapsed_seconds": round(time.monotonic() - started_at, 6),
            "chunks_received": chunks_received,
            "bytes_received": bytes_received,
        },
    )


def run_doctor(
    *,
    include_devices: bool = False,
    capture_backend: str = "sounddevice",
    include_capture_test: bool = False,
    capture_test_seconds: float = 0.25,
    capture_device: str | int | None = None,
    wav_path: str | None = None,
) -> DoctorReport:
    """Run environment diagnostics and return a structured report."""

    system = platform.system()
    checks: list[DiagnosticCheck] = [
        _check_python(),
        DiagnosticCheck(
            name="platform",
            status=DiagnosticStatus.OK,
            message=f"Running on {platform.platform()}.",
            hint=_platform_hint(system),
            details={"system": system},
        ),
        _check_optional_dependency(
            "sounddevice",
            "Install with: pip install auralisvoicekit[sounddevice]",
        ),
        _check_optional_dependency(
            "openai",
            "Install with: pip install auralisvoicekit[openai]",
        ),
        _check_optional_dependency(
            "faster_whisper",
            "Install with: pip install auralisvoicekit[whisper]",
        ),
        _check_optional_executable(
            "ffmpeg",
            "Install ffmpeg to decode MP3 and other compressed audio formats.",
        ),
    ]
    checks.extend(_backend_checks())

    if include_devices:
        checks.append(_device_check(capture_backend))
    if include_capture_test:
        checks.append(
            _capture_test_check(
                capture_backend,
                seconds=capture_test_seconds,
                input_device=capture_device,
            )
        )
    if wav_path:
        checks.append(_wav_check(wav_path))

    return DoctorReport(
        version=__version__,
        python=sys.version.split()[0],
        implementation=platform.python_implementation(),
        platform=platform.platform(),
        system=system,
        checks=tuple(checks),
    )
