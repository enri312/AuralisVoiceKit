"""Transcribe a PCM16 WAV file with an optional transcription backend."""

from __future__ import annotations

import argparse

from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, read_wav_as_chunk
from auralis_voicekit.exceptions import AuralisError


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe a PCM16 WAV file.")
    parser.add_argument("path", help="input WAV path")
    parser.add_argument("--backend", default="openai", help="transcription backend")
    parser.add_argument("--model", default="gpt-4o-mini-transcribe", help="transcription model")
    parser.add_argument("--language", default="es", help="language hint")
    parser.add_argument("--prompt", default=None, help="optional transcription prompt")
    args = parser.parse_args()

    config = VoiceKitConfig(
        transcription_backend=args.backend,
        transcription_model=args.model,
        transcription_prompt=args.prompt,
        language=args.language,
    )

    try:
        chunk = read_wav_as_chunk(args.path)
        result = AuralisVoiceKit(config).transcribe(chunk)
    except AuralisError as exc:
        print(str(exc))
        return 1

    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
