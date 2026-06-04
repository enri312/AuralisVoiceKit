"""Optional capture backend based on python-sounddevice."""

from __future__ import annotations

from typing import Callable, Sequence

from ..config import VoiceKitConfig
from ..exceptions import AudioDeviceNotFound, BackendNotAvailable
from ..models import AudioChunk, AudioDevice, AudioEncoding
from .base import BackendInfo


def _load_sounddevice():
    try:
        import sounddevice as sd  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendNotAvailable(
            "The sounddevice backend requires: pip install auralisvoicekit[sounddevice]"
        ) from exc
    return sd


def _default_input_device_id(sd) -> int | None:
    default_device = getattr(sd.default, "device", None)
    if isinstance(default_device, (list, tuple)):
        default_device = default_device[0] if default_device else None
    if default_device in {None, -1}:
        return None
    try:
        return int(default_device)
    except (TypeError, ValueError):
        return None


def _host_api_name(sd, host_api_index: object) -> str | None:
    if host_api_index is None:
        return None
    try:
        index = int(host_api_index)
        host_api = sd.query_hostapis()[index]
        return str(host_api.get("name", index))
    except (IndexError, TypeError, ValueError, AttributeError):
        return str(host_api_index)


def _device_matches(device: AudioDevice, selector: str) -> bool:
    normalized = selector.strip().casefold()
    return (
        device.id.casefold() == normalized
        or device.name.casefold() == normalized
        or normalized in device.name.casefold()
    )


class SoundDeviceCaptureBackend:
    name = "sounddevice"

    def __init__(self) -> None:
        self._stream = None

    def info(self) -> BackendInfo:
        try:
            _load_sounddevice()
        except BackendNotAvailable as exc:
            return BackendInfo(
                name=self.name,
                kind="capture",
                available=False,
                reason=str(exc),
                dependencies=("sounddevice",),
            )
        return BackendInfo(
            name=self.name,
            kind="capture",
            dependencies=("sounddevice",),
        )

    def list_devices(self) -> Sequence[AudioDevice]:
        sd = _load_sounddevice()
        devices = []
        default_input = _default_input_device_id(sd)
        for index, raw in enumerate(sd.query_devices()):
            max_input_channels = int(raw.get("max_input_channels", 0))
            if max_input_channels <= 0:
                continue
            host_api_index = raw.get("hostapi")
            devices.append(
                AudioDevice(
                    id=str(index),
                    name=str(raw.get("name", f"Input {index}")),
                    kind="input",
                    channels=max_input_channels,
                    host_api=_host_api_name(sd, host_api_index),
                    is_default=index == default_input,
                    metadata={
                        "default_samplerate": raw.get("default_samplerate"),
                        "host_api_index": host_api_index,
                        "raw": dict(raw),
                    },
                )
            )
        return devices

    def resolve_input_device(self, selector: str | int | None) -> int | None:
        """Resolve a user-facing device selector to a sounddevice device id."""

        if selector is None:
            return None
        if isinstance(selector, int):
            return selector

        value = selector.strip()
        if not value or value.casefold() == "default":
            return None
        if value.isdigit():
            return int(value)

        matches = [device for device in self.list_devices() if _device_matches(device, value)]
        if not matches:
            raise AudioDeviceNotFound(f"No input device matched {selector!r}")
        if len(matches) > 1:
            names = ", ".join(f"{device.id}:{device.name}" for device in matches)
            raise AudioDeviceNotFound(f"Input device selector {selector!r} is ambiguous: {names}")
        return int(matches[0].id)

    def start(self, config: VoiceKitConfig, on_audio: Callable[[AudioChunk], None]) -> None:
        sd = _load_sounddevice()
        audio_format = config.audio_format()
        if audio_format.encoding is not AudioEncoding.PCM16 or audio_format.sample_width != 2:
            raise ValueError("sounddevice capture currently supports PCM16 audio only")
        if self._stream is not None:
            raise RuntimeError("sounddevice capture is already running")

        def callback(indata, frames, time_info, status) -> None:
            metadata = {"frames": frames}
            if status:
                metadata["status"] = str(status)
            chunk = AudioChunk(
                data=bytes(indata),
                format=audio_format,
                metadata=metadata,
            )
            on_audio(chunk)

        stream = sd.RawInputStream(
            samplerate=config.sample_rate,
            channels=config.channels,
            dtype="int16",
            device=self.resolve_input_device(config.input_device),
            blocksize=config.capture_block_frames,
            latency=config.capture_latency,
            callback=callback,
        )
        self._stream = stream
        try:
            stream.start()
        except Exception:
            stream.close()
            self._stream = None
            raise

    def stop(self) -> None:
        if self._stream is None:
            return
        stream = self._stream
        self._stream = None
        try:
            stream.stop()
        finally:
            stream.close()
