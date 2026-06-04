"""Optional local transcription backend using faster-whisper."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from ..audio import chunk_to_wav_bytes
from ..config import VoiceKitConfig
from ..exceptions import BackendNotAvailable, TranscriptionError
from ..models import AudioChunk, TranscriptResult
from .base import BackendInfo


def _load_whisper_model_class():
    try:
        from faster_whisper import WhisperModel  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendNotAvailable(
            "The whisper transcription backend requires: pip install auralisvoicekit[whisper]"
        ) from exc
    return WhisperModel


def _segment_metadata(segment: object) -> dict[str, Any]:
    return {
        "start": getattr(segment, "start", None),
        "end": getattr(segment, "end", None),
        "text": str(getattr(segment, "text", "") or ""),
        "avg_logprob": getattr(segment, "avg_logprob", None),
        "no_speech_prob": getattr(segment, "no_speech_prob", None),
    }


def _info_metadata(info: object) -> dict[str, Any]:
    return {
        "detected_language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "whisper_duration_seconds": getattr(info, "duration", None),
        "duration_after_vad_seconds": getattr(info, "duration_after_vad", None),
    }


class WhisperTranscriptionBackend:
    name = "whisper"

    def __init__(self) -> None:
        self._model = None
        self._model_key: tuple[str, str, str] | None = None

    def info(self) -> BackendInfo:
        try:
            _load_whisper_model_class()
        except BackendNotAvailable as exc:
            return BackendInfo(
                name=self.name,
                kind="transcription",
                available=False,
                reason=str(exc),
                dependencies=("faster-whisper",),
            )
        return BackendInfo(
            name=self.name,
            kind="transcription",
            dependencies=("faster-whisper",),
        )

    def _get_model(self, config: VoiceKitConfig):
        model_name = _whisper_model_name(config)
        key = (model_name, config.transcription_device, config.transcription_compute_type)
        if self._model is not None and self._model_key == key:
            return self._model

        WhisperModel = _load_whisper_model_class()
        try:
            self._model = WhisperModel(
                model_name,
                device=config.transcription_device,
                compute_type=config.transcription_compute_type,
            )
        except Exception as exc:
            raise TranscriptionError(f"Whisper model could not be loaded: {exc}") from exc
        self._model_key = key
        return self._model

    def transcribe(self, chunk: AudioChunk, config: VoiceKitConfig) -> TranscriptResult:
        model = self._get_model(config)
        wav_bytes = chunk_to_wav_bytes(chunk)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                audio_file.write(wav_bytes)
                temp_path = audio_file.name

            request: dict[str, Any] = {
                "language": config.language or None,
                "beam_size": config.transcription_beam_size,
                "initial_prompt": config.transcription_prompt,
                "vad_filter": config.transcription_vad_filter,
            }
            request = {key: value for key, value in request.items() if value is not None}
            segments_iter, info = model.transcribe(temp_path, **request)
            segments = list(segments_iter)
        except Exception as exc:
            raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc
        finally:
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        text = "".join(str(getattr(segment, "text", "") or "") for segment in segments).strip()
        metadata = {
            "model": _whisper_model_name(config),
            "device": config.transcription_device,
            "compute_type": config.transcription_compute_type,
            "beam_size": config.transcription_beam_size,
            "vad_filter": config.transcription_vad_filter,
            "duration_seconds": chunk.duration_seconds,
            "segments": [_segment_metadata(segment) for segment in segments],
        }
        metadata.update(_info_metadata(info))
        return TranscriptResult(
            text=text,
            language=getattr(info, "language", config.language) or config.language,
            confidence=getattr(info, "language_probability", None),
            source=self.name,
            metadata=metadata,
        )


def _whisper_model_name(config: VoiceKitConfig) -> str:
    if config.transcription_model in {
        "auto",
        "default",
        "",
        "gpt-4o-mini-transcribe",
        "gpt-4o-transcribe",
        "whisper-1",
    }:
        return "base"
    return config.transcription_model
