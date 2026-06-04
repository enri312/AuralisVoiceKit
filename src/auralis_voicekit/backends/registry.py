"""Registry for optional backend factories."""

from __future__ import annotations

from typing import Callable

from ..exceptions import BackendNotAvailable
from .base import BackendInfo, CaptureBackend, SpeechOutputBackend, TranscriptionBackend
from .null import NullCaptureBackend, NullSpeechOutputBackend, NullTranscriptionBackend


CaptureFactory = Callable[[], CaptureBackend]
TranscriptionFactory = Callable[[], TranscriptionBackend]
OutputFactory = Callable[[], SpeechOutputBackend]


class BackendRegistry:
    def __init__(self) -> None:
        self._capture: dict[str, CaptureFactory] = {}
        self._transcription: dict[str, TranscriptionFactory] = {}
        self._output: dict[str, OutputFactory] = {}

    def register_capture(self, name: str, factory: CaptureFactory) -> None:
        self._capture[name] = factory

    def register_transcription(self, name: str, factory: TranscriptionFactory) -> None:
        self._transcription[name] = factory

    def register_output(self, name: str, factory: OutputFactory) -> None:
        self._output[name] = factory

    def create_capture(self, name: str) -> CaptureBackend:
        return self._create(name, self._capture, "capture")

    def create_transcription(self, name: str) -> TranscriptionBackend:
        return self._create(name, self._transcription, "transcription")

    def create_output(self, name: str) -> SpeechOutputBackend:
        return self._create(name, self._output, "output")

    def backend_info(self) -> list[BackendInfo]:
        infos: list[BackendInfo] = []
        for kind, factories in (
            ("capture", self._capture),
            ("transcription", self._transcription),
            ("output", self._output),
        ):
            for name, factory in factories.items():
                try:
                    infos.append(factory().info())
                except BackendNotAvailable as exc:
                    infos.append(BackendInfo(name=name, kind=kind, available=False, reason=str(exc)))
        return infos

    @staticmethod
    def _create(name: str, factories: dict[str, Callable[[], object]], kind: str):
        try:
            return factories[name]()
        except KeyError as exc:
            available = ", ".join(sorted(factories)) or "none"
            raise BackendNotAvailable(
                f"Unknown {kind} backend {name!r}. Available: {available}."
            ) from exc


def _create_sounddevice_capture() -> CaptureBackend:
    from .sounddevice import SoundDeviceCaptureBackend

    return SoundDeviceCaptureBackend()


def create_default_registry() -> BackendRegistry:
    registry = BackendRegistry()
    registry.register_capture("null", NullCaptureBackend)
    registry.register_capture("sounddevice", _create_sounddevice_capture)
    registry.register_transcription("null", NullTranscriptionBackend)
    registry.register_output("null", NullSpeechOutputBackend)
    return registry
