"""Windows WASAPI capture backend built on the optional sounddevice backend."""

from __future__ import annotations

from dataclasses import dataclass, field
import platform
from typing import Any, Callable, Sequence

from ..config import VoiceKitConfig
from ..exceptions import AudioDeviceNotFound, BackendNotAvailable
from ..models import AudioChunk, AudioDevice
from .base import BackendInfo
from .sounddevice import SoundDeviceCaptureBackend, _default_input_device_id, _load_sounddevice


@dataclass(frozen=True, slots=True)
class WasapiDiagnosticSnapshot:
    """Serializable snapshot of the Windows WASAPI capture environment."""

    system: str
    available: bool
    reason: str | None = None
    host_apis: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    wasapi_host_api_indices: tuple[int, ...] = field(default_factory=tuple)
    default_input_device_id: int | None = None
    selected_input_device_id: int | None = None
    input_devices: tuple[AudioDevice, ...] = field(default_factory=tuple)
    wasapi_input_devices: tuple[AudioDevice, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "available": self.available,
            "reason": self.reason,
            "host_apis": [dict(host_api) for host_api in self.host_apis],
            "wasapi_host_api_indices": list(self.wasapi_host_api_indices),
            "default_input_device_id": self.default_input_device_id,
            "selected_input_device_id": self.selected_input_device_id,
            "input_device_count": len(self.input_devices),
            "wasapi_input_device_count": len(self.wasapi_input_devices),
            "input_devices": [_device_summary(device) for device in self.input_devices],
            "wasapi_input_devices": [
                _device_summary(device) for device in self.wasapi_input_devices
            ],
        }


class WasapiCaptureBackend(SoundDeviceCaptureBackend):
    name = "wasapi"

    def __init__(self, *, system: str | None = None) -> None:
        super().__init__()
        self._system = system or platform.system()

    def info(self) -> BackendInfo:
        if self._system != "Windows":
            return BackendInfo(
                name=self.name,
                kind="capture",
                available=False,
                reason="WASAPI capture is only available on Windows.",
                dependencies=("sounddevice",),
            )
        try:
            sd = _load_sounddevice()
        except BackendNotAvailable as exc:
            return BackendInfo(
                name=self.name,
                kind="capture",
                available=False,
                reason=str(exc),
                dependencies=("sounddevice",),
            )
        if not _wasapi_host_api_indices(sd):
            return BackendInfo(
                name=self.name,
                kind="capture",
                available=False,
                reason="sounddevice did not report a WASAPI host API.",
                dependencies=("sounddevice",),
            )
        return BackendInfo(
            name=self.name,
            kind="capture",
            dependencies=("sounddevice",),
        )

    def list_devices(self) -> Sequence[AudioDevice]:
        self._ensure_windows()
        sd = _load_sounddevice()
        wasapi_indices = set(_wasapi_host_api_indices(sd))
        if not wasapi_indices:
            raise BackendNotAvailable("sounddevice did not report a WASAPI host API.")
        return [
            device
            for device in super().list_devices()
            if device.metadata.get("host_api_index") in wasapi_indices
        ]

    def resolve_input_device(self, selector: str | int | None) -> int | None:
        self._ensure_windows()
        if selector is None or (isinstance(selector, str) and selector.strip().casefold() == "default"):
            devices = list(self.list_devices())
            if not devices:
                raise AudioDeviceNotFound("No WASAPI input devices were reported by sounddevice.")
            default = next((device for device in devices if device.is_default), devices[0])
            return int(default.id)
        if isinstance(selector, int) or (isinstance(selector, str) and selector.strip().isdigit()):
            device_id = int(selector)
            if any(int(device.id) == device_id for device in self.list_devices()):
                return device_id
            raise AudioDeviceNotFound(f"Input device id {device_id} is not a WASAPI input device.")
        return super().resolve_input_device(selector)

    def start(self, config: VoiceKitConfig, on_audio: Callable[[AudioChunk], None]) -> None:
        self._ensure_windows()
        super().start(config, on_audio)

    def _ensure_windows(self) -> None:
        if self._system != "Windows":
            raise BackendNotAvailable("WASAPI capture is only available on Windows.")


def _wasapi_host_api_indices(sd) -> tuple[int, ...]:
    indices = []
    for index, host_api in enumerate(sd.query_hostapis()):
        name = str(host_api.get("name", ""))
        if "wasapi" in name.casefold():
            indices.append(index)
    return tuple(indices)


def inspect_wasapi_environment(*, system: str | None = None) -> WasapiDiagnosticSnapshot:
    """Inspect WASAPI host APIs and input devices without opening a stream."""

    system_name = system or platform.system()
    if system_name != "Windows":
        return WasapiDiagnosticSnapshot(
            system=system_name,
            available=False,
            reason="WASAPI capture is only available on Windows.",
        )

    try:
        sd = _load_sounddevice()
    except BackendNotAvailable as exc:
        return WasapiDiagnosticSnapshot(
            system=system_name,
            available=False,
            reason=str(exc),
        )

    try:
        host_apis = _host_api_summaries(sd)
        wasapi_indices = _wasapi_host_api_indices(sd)
        default_input = _default_input_device_id(sd)
    except Exception as exc:
        return WasapiDiagnosticSnapshot(
            system=system_name,
            available=False,
            reason=f"Could not inspect sounddevice host APIs: {exc}",
        )

    if not wasapi_indices:
        return WasapiDiagnosticSnapshot(
            system=system_name,
            available=False,
            reason="sounddevice did not report a WASAPI host API.",
            host_apis=host_apis,
            wasapi_host_api_indices=wasapi_indices,
            default_input_device_id=default_input,
        )

    try:
        input_devices = tuple(SoundDeviceCaptureBackend().list_devices())
    except Exception as exc:
        return WasapiDiagnosticSnapshot(
            system=system_name,
            available=False,
            reason=f"Could not inspect sounddevice input devices: {exc}",
            host_apis=host_apis,
            wasapi_host_api_indices=wasapi_indices,
            default_input_device_id=default_input,
        )

    wasapi_devices = tuple(
        device
        for device in input_devices
        if device.metadata.get("host_api_index") in set(wasapi_indices)
    )
    selected_default = next(
        (device for device in wasapi_devices if device.is_default),
        wasapi_devices[0] if wasapi_devices else None,
    )

    return WasapiDiagnosticSnapshot(
        system=system_name,
        available=bool(wasapi_devices),
        reason=None if wasapi_devices else "No WASAPI input devices were reported by sounddevice.",
        host_apis=host_apis,
        wasapi_host_api_indices=wasapi_indices,
        default_input_device_id=default_input,
        selected_input_device_id=int(selected_default.id) if selected_default is not None else None,
        input_devices=input_devices,
        wasapi_input_devices=wasapi_devices,
    )


def _host_api_summaries(sd) -> tuple[dict[str, Any], ...]:
    summaries = []
    for index, host_api in enumerate(sd.query_hostapis()):
        summaries.append(
            {
                "index": index,
                "name": str(host_api.get("name", index)),
                "device_count": host_api.get("device_count"),
                "default_input_device": host_api.get("default_input_device"),
                "default_output_device": host_api.get("default_output_device"),
            }
        )
    return tuple(summaries)


def _device_summary(device: AudioDevice) -> dict[str, Any]:
    return {
        "id": device.id,
        "name": device.name,
        "kind": device.kind,
        "channels": device.channels,
        "host_api": device.host_api,
        "is_default": device.is_default,
        "default_samplerate": device.metadata.get("default_samplerate"),
        "host_api_index": device.metadata.get("host_api_index"),
    }
