"""Structured diagnostics for local AuralisVoiceKit environments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from importlib.util import find_spec
import json
import platform
from pathlib import Path
import re
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
from .windows_audio import windows_audio_error_hint


DOCTOR_BUNDLE_SCHEMA = "auralisvoicekit.doctor-bundle.v1"
_REDACTED_DEVICE = "[redacted-device]"
_REDACTED_PATH = "[redacted-path]"
_PATHLIKE_KEYS = {
    "file",
    "filename",
    "ffmpeg_executable",
    "input_file",
    "output_file",
    "path",
    "search",
}
_PATH_PATTERN = re.compile(
    r"[A-Za-z]:\\[^\s,;]+|"
    r"(?:^|(?<=[\s\"']))/[^\s,;]+|"
    r"(?:^|(?<=[\s\"']))~[\\/][^\s,;]+"
)


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


def sanitize_doctor_report(report: DoctorReport) -> dict[str, Any]:
    """Return a shareable doctor report with local paths and device names redacted."""

    return _sanitize_doctor_value(report.to_dict())


def create_doctor_bundle(report: DoctorReport) -> dict[str, Any]:
    """Create a sanitized diagnostic bundle for pilot reports."""

    return {
        "schema": DOCTOR_BUNDLE_SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "redacted": True,
        "share_safety": {
            "paths": "redacted",
            "device_names": "redacted",
            "audio_bytes": "not_collected",
            "transcripts": "not_collected",
        },
        "report": sanitize_doctor_report(report),
        "next_steps": [
            "Attach this JSON when reporting a capture, backend, ffmpeg or platform issue.",
            "If the problem is audio capture, also include the exact command that failed.",
            "Do not attach real audio unless you intentionally want to share that file.",
        ],
    }


def write_doctor_bundle(path: str | Path, report: DoctorReport) -> str:
    """Write a sanitized diagnostic bundle and return the written path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(create_doctor_bundle(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(output_path)


def _platform_hint(system: str) -> str:
    if system == "Windows":
        return "Check Windows microphone privacy settings if real capture cannot start."
    if system == "Linux":
        return "On Ubuntu/Linux, install PortAudio system packages if sounddevice cannot open audio."
    if system == "Darwin":
        return "On macOS, grant microphone permission to the terminal or app running Python."
    return "Use the wav backend for offline tests when real audio devices are unavailable."


def _sanitize_doctor_value(
    value: Any,
    *,
    key: str | None = None,
    inside_device: bool = False,
) -> Any:
    if isinstance(value, dict):
        looks_like_device = _looks_like_device_summary(value)
        return {
            str(child_key): _sanitize_doctor_value(
                child_value,
                key=str(child_key),
                inside_device=looks_like_device,
            )
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        if key is not None and key.lower() in _PATHLIKE_KEYS:
            return [_REDACTED_PATH for _ in value]
        return [_sanitize_doctor_value(item) for item in value]
    if isinstance(value, tuple):
        if key is not None and key.lower() in _PATHLIKE_KEYS:
            return tuple(_REDACTED_PATH for _ in value)
        return tuple(_sanitize_doctor_value(item) for item in value)
    if isinstance(value, str):
        if key is not None:
            normalized_key = key.lower()
            if normalized_key in _PATHLIKE_KEYS and value:
                return _REDACTED_PATH
            if inside_device and normalized_key == "name" and value:
                return _REDACTED_DEVICE
        return _redact_pathlike_text(value)
    if key is not None:
        normalized_key = key.lower()
        if normalized_key in _PATHLIKE_KEYS and value not in {None, ""}:
            return _REDACTED_PATH
        if inside_device and normalized_key == "name" and value not in {None, ""}:
            return _REDACTED_DEVICE
    return value


def _looks_like_device_summary(value: dict[str, Any]) -> bool:
    keys = set(value)
    return {"id", "name", "kind", "channels"}.issubset(keys)


def _redact_pathlike_text(value: str) -> str:
    return _PATH_PATTERN.sub(_REDACTED_PATH, value)


def _capture_failure_hint(
    exc: Exception,
    *,
    system: str,
    capture_backend: str,
    input_device: str | int | None,
) -> tuple[str, dict[str, Any]]:
    if system == "Windows":
        hint = windows_audio_error_hint(
            exc,
            backend=capture_backend,
            device=input_device,
            system=system,
        )
        return hint.format_hint(), {"windows_audio_hint": hint.to_dict()}
    return _platform_hint(system), {}


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


def _capture_backend_details(capture_backend: str) -> dict[str, Any]:
    if capture_backend != "wasapi":
        return {}
    from .backends.wasapi import inspect_wasapi_environment

    return {"wasapi": inspect_wasapi_environment().to_dict()}


def _device_check(capture_backend: str) -> DiagnosticCheck:
    registry = create_default_registry()
    backend_details = _capture_backend_details(capture_backend)
    try:
        backend = registry.create_capture(capture_backend)
        devices = list(backend.list_devices())
    except BackendNotAvailable as exc:
        return DiagnosticCheck(
            name=f"devices:{capture_backend}",
            status=DiagnosticStatus.WARNING,
            message=f"Cannot inspect devices for {capture_backend!r}: {exc}",
            hint="Use --backend wav for offline checks or install the requested backend.",
            details=backend_details,
        )

    if not devices:
        return DiagnosticCheck(
            name=f"devices:{capture_backend}",
            status=DiagnosticStatus.WARNING,
            message=f"No input devices were reported by {capture_backend!r}.",
            hint="Use the wav backend for offline tests or check OS audio permissions.",
            details=backend_details,
        )
    details = {
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
    }
    details.update(backend_details)
    return DiagnosticCheck(
        name=f"devices:{capture_backend}",
        status=DiagnosticStatus.OK,
        message=f"{len(devices)} input device(s) reported by {capture_backend!r}.",
        details=details,
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
    backend_details = _capture_backend_details(capture_backend)
    config_details = {
        "sample_rate": config.sample_rate,
        "channels": config.channels,
        "capture_block_ms": config.capture_block_ms,
        "capture_block_frames": config.capture_block_frames,
    }
    started = False
    started_at = time.monotonic()
    try:
        kit = AuralisVoiceKit(config)
        kit.start_capture(handle_chunk)
        started = True
        time.sleep(seconds)
    except Exception as exc:
        system = platform.system()
        hint, hint_details = _capture_failure_hint(
            exc,
            system=system,
            capture_backend=capture_backend,
            input_device=input_device,
        )
        return DiagnosticCheck(
            name=name,
            status=DiagnosticStatus.ERROR,
            message=f"Capture backend {capture_backend!r} could not be opened: {exc}",
            hint=hint,
            details={
                "backend": capture_backend,
                "input_device": input_device,
                "requested_seconds": seconds,
                "elapsed_seconds": round(time.monotonic() - started_at, 6),
                "error_type": type(exc).__name__,
                **config_details,
                **backend_details,
                **hint_details,
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
            **config_details,
            **backend_details,
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
