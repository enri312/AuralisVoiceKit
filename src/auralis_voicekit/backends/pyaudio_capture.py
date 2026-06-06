"""Optional capture backend based on PyAudio."""

from __future__ import annotations

from typing import Callable, Sequence

from ..config import VoiceKitConfig
from ..exceptions import AudioDeviceNotFound, BackendNotAvailable
from ..models import AudioChunk, AudioDevice, AudioEncoding
from .base import BackendInfo


def _load_pyaudio_module():
    try:
        import pyaudio  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendNotAvailable(
            "The pyaudio backend requires: pip install auralisvoicekit[pyaudio]"
        ) from exc
    return pyaudio


def _new_pyaudio():
    module = _load_pyaudio_module()
    try:
        return module.PyAudio()
    except Exception as exc:
        raise BackendNotAvailable(f"Could not initialize PyAudio: {exc}") from exc


def _input_device_count(pyaudio_instance) -> int:
    try:
        return int(pyaudio_instance.get_device_count())
    except (TypeError, ValueError, AttributeError) as exc:
        raise BackendNotAvailable(f"Could not inspect PyAudio devices: {exc}") from exc


def _default_input_device_id(pyaudio_instance) -> int | None:
    try:
        default_info = pyaudio_instance.get_default_input_device_info()
    except Exception:
        return None
    try:
        return int(default_info.get("index"))
    except (AttributeError, TypeError, ValueError):
        return None


def _host_api_name(pyaudio_instance, host_api_index: object) -> str | None:
    if host_api_index is None:
        return None
    try:
        host_api = pyaudio_instance.get_host_api_info_by_index(int(host_api_index))
        return str(host_api.get("name", host_api_index))
    except (AttributeError, TypeError, ValueError, OSError):
        return str(host_api_index)


def _device_matches(device: AudioDevice, selector: str) -> bool:
    normalized = selector.strip().casefold()
    return (
        device.id.casefold() == normalized
        or device.name.casefold() == normalized
        or normalized in device.name.casefold()
    )


class PyAudioCaptureBackend:
    name = "pyaudio"

    def __init__(self) -> None:
        self._pyaudio = None
        self._stream = None

    def info(self) -> BackendInfo:
        try:
            _load_pyaudio_module()
        except BackendNotAvailable as exc:
            return BackendInfo(
                name=self.name,
                kind="capture",
                available=False,
                reason=str(exc),
                dependencies=("pyaudio",),
            )
        return BackendInfo(
            name=self.name,
            kind="capture",
            dependencies=("pyaudio",),
        )

    def list_devices(self) -> Sequence[AudioDevice]:
        pyaudio_instance = _new_pyaudio()
        try:
            devices = []
            default_input = _default_input_device_id(pyaudio_instance)
            for index in range(_input_device_count(pyaudio_instance)):
                raw = pyaudio_instance.get_device_info_by_index(index)
                max_input_channels = int(raw.get("maxInputChannels", 0))
                if max_input_channels <= 0:
                    continue
                host_api_index = raw.get("hostApi")
                devices.append(
                    AudioDevice(
                        id=str(int(raw.get("index", index))),
                        name=str(raw.get("name", f"Input {index}")),
                        kind="input",
                        channels=max_input_channels,
                        host_api=_host_api_name(pyaudio_instance, host_api_index),
                        is_default=int(raw.get("index", index)) == default_input,
                        metadata={
                            "default_sample_rate": raw.get("defaultSampleRate"),
                            "host_api_index": host_api_index,
                            "raw": dict(raw),
                        },
                    )
                )
            return devices
        finally:
            pyaudio_instance.terminate()

    def resolve_input_device(self, selector: str | int | None) -> int | None:
        """Resolve a user-facing device selector to a PyAudio device index."""

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
        module = _load_pyaudio_module()
        audio_format = config.audio_format()
        if audio_format.encoding is not AudioEncoding.PCM16 or audio_format.sample_width != 2:
            raise ValueError("pyaudio capture currently supports PCM16 audio only")
        if self._stream is not None:
            raise RuntimeError("pyaudio capture is already running")

        pyaudio_instance = _new_pyaudio()
        stream = None

        def callback(in_data, frame_count, time_info, status_flags):
            metadata = {"frames": frame_count}
            if status_flags:
                metadata["status_flags"] = status_flags
            chunk = AudioChunk(
                data=bytes(in_data or b""),
                format=audio_format,
                metadata=metadata,
            )
            on_audio(chunk)
            return (None, getattr(module, "paContinue", 0))

        try:
            stream = pyaudio_instance.open(
                format=getattr(module, "paInt16", 8),
                channels=config.channels,
                rate=config.sample_rate,
                input=True,
                input_device_index=self.resolve_input_device(config.input_device),
                frames_per_buffer=config.capture_block_frames,
                stream_callback=callback,
                start=False,
            )
            self._pyaudio = pyaudio_instance
            self._stream = stream
            stream.start_stream()
        except Exception:
            if stream is not None:
                stream.close()
            pyaudio_instance.terminate()
            self._pyaudio = None
            self._stream = None
            raise

    def stop(self) -> None:
        if self._stream is None:
            return
        stream = self._stream
        pyaudio_instance = self._pyaudio
        self._stream = None
        self._pyaudio = None
        try:
            try:
                stream.stop_stream()
            finally:
                stream.close()
        finally:
            if pyaudio_instance is not None:
                pyaudio_instance.terminate()
