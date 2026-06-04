"""Transcribe an audio file with an optional transcription backend."""

from __future__ import annotations

import argparse

from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, read_audio_as_chunk
from auralis_voicekit.exceptions import AuralisError


def _default_model(backend: str, model: str | None) -> str:
    if model:
        return model
    if backend == "whisper":
        return "base"
    if backend == "openai":
        return "gpt-4o-mini-transcribe"
    return "auto"


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe a WAV or ffmpeg-supported audio file.")
    parser.add_argument("path", help="input audio path")
    parser.add_argument("--backend", default="null", help="transcription backend")
    parser.add_argument("--model", default=None, help="transcription model")
    parser.add_argument("--language", default="es", help="language hint")
    parser.add_argument("--prompt", default=None, help="optional transcription prompt")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    args = parser.parse_args()

    config = VoiceKitConfig(
        transcription_backend=args.backend,
        transcription_model=_default_model(args.backend, args.model),
        transcription_prompt=args.prompt,
        language=args.language,
    )

    try:
        chunk = read_audio_as_chunk(
            args.path,
            sample_rate=config.sample_rate,
            channels=config.channels,
            ffmpeg_executable=args.ffmpeg,
        )
        result = AuralisVoiceKit(config).transcribe(chunk)
    except AuralisError as exc:
        print(str(exc))
        return 1

    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
