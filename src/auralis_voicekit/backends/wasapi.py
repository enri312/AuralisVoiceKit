"""Windows WASAPI capture backend built on the optional sounddevice backend."""

from __future__ import annotations

import platform
from typing import Callable, Sequence

from ..config import VoiceKitConfig
from ..exceptions import AudioDeviceNotFound, BackendNotAvailable
from ..models import AudioChunk, AudioDevice
from .base import BackendInfo
from .sounddevice import SoundDeviceCaptureBackend, _load_sounddevice


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
