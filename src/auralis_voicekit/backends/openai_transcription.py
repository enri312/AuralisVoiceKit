"""Optional transcription backend using the OpenAI Audio API."""

from __future__ import annotations

import io
from typing import Any

from ..audio import chunk_to_wav_bytes
from ..config import VoiceKitConfig
from ..exceptions import BackendNotAvailable, TranscriptionError
from ..models import AudioChunk, TranscriptResult
from .base import BackendInfo


OPENAI_AUDIO_UPLOAD_LIMIT_BYTES = 25 * 1024 * 1024


def _load_openai_client_class():
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendNotAvailable(
            "The openai transcription backend requires: pip install auralisvoicekit[openai]"
        ) from exc
    return OpenAI


def _response_text(response: object) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return str(response.get("text", ""))
    text = getattr(response, "text", "")
    return str(text or "")


def _response_metadata(response: object) -> dict[str, Any]:
    if isinstance(response, dict):
        return dict(response)
    if hasattr(response, "model_dump"):
        try:
            return response.model_dump()
        except Exception:
            return {}
    return {}


def _openai_model_name(config: VoiceKitConfig) -> str:
    if config.transcription_model in {"auto", "default", ""}:
        return "gpt-4o-mini-transcribe"
    return config.transcription_model


class OpenAITranscriptionBackend:
    name = "openai"

    def info(self) -> BackendInfo:
        try:
            _load_openai_client_class()
        except BackendNotAvailable as exc:
            return BackendInfo(
                name=self.name,
                kind="transcription",
                available=False,
                reason=str(exc),
                dependencies=("openai",),
            )
        return BackendInfo(
            name=self.name,
            kind="transcription",
            dependencies=("openai",),
        )

    def transcribe(self, chunk: AudioChunk, config: VoiceKitConfig) -> TranscriptResult:
        OpenAI = _load_openai_client_class()
        model_name = _openai_model_name(config)
        wav_bytes = chunk_to_wav_bytes(chunk)
        if len(wav_bytes) > OPENAI_AUDIO_UPLOAD_LIMIT_BYTES:
            raise TranscriptionError("OpenAI transcription audio must be 25 MB or smaller")

        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "audio.wav"
        request: dict[str, Any] = {
            "model": model_name,
            "file": audio_file,
            "response_format": config.transcription_response_format,
        }
        if config.language:
            request["language"] = config.language
        if config.transcription_prompt:
            request["prompt"] = config.transcription_prompt

        try:
            client = OpenAI()
            response = client.audio.transcriptions.create(**request)
        except Exception as exc:
            raise TranscriptionError(f"OpenAI transcription failed: {exc}") from exc

        metadata = _response_metadata(response)
        metadata.update(
            {
                "model": model_name,
                "response_format": config.transcription_response_format,
                "duration_seconds": chunk.duration_seconds,
            }
        )
        return TranscriptResult(
            text=_response_text(response),
            language=config.language,
            source=self.name,
            metadata=metadata,
        )
