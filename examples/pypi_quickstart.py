"""PyPI quickstart that works without optional dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceActivityConfig,
    VoiceKitConfig,
    VoiceSession,
    VoiceSessionConfig,
    generate_synthetic_audio_chunks,
    write_wav,
)


def run_demo(
    *,
    output: str,
    duration_seconds: float = 1.0,
    chunk_duration_ms: int = 100,
    sample_rate: int = 16_000,
) -> dict[str, object]:
    """Create a synthetic WAV and run it through the base pipeline."""

    chunks = generate_synthetic_audio_chunks(
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=1,
        chunk_duration_ms=chunk_duration_ms,
    )
    output_path = Path(output)
    write_wav(str(output_path), chunks)

    kit = AuralisVoiceKit(
        VoiceKitConfig(
            sample_rate=sample_rate,
            channels=1,
            transcription_backend="null",
            privacy_mode=True,
        )
    )
    session = VoiceSession(
        kit,
        VoiceSessionConfig(
            chunk_duration_ms=chunk_duration_ms,
            voice_activity=VoiceActivityConfig(
                threshold=0.01,
                min_voice_ms=chunk_duration_ms,
                max_silence_ms=chunk_duration_ms,
                pre_speech_ms=0,
            ),
        ),
    )
    turns = session.transcribe_wav(str(output_path))

    return {
        "output": str(output_path),
        "chunks": len(chunks),
        "turns": [turn.to_dict() for turn in turns],
        "transcription_backend": kit.config.transcription_backend,
        "message": "Base pipeline ready. Install extras to use real microphone or transcription.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PyPI quickstart without optional extras.")
    parser.add_argument("--output", default="auralis_pypi_quickstart.wav", help="output WAV path")
    parser.add_argument("--duration", type=float, default=1.0, help="synthetic audio duration")
    parser.add_argument("--chunk-ms", type=int, default=100, help="chunk size in milliseconds")
    parser.add_argument("--sample-rate", type=int, default=16000, help="sample rate")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()

    payload = run_demo(
        output=args.output,
        duration_seconds=args.duration,
        chunk_duration_ms=args.chunk_ms,
        sample_rate=args.sample_rate,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Wrote {payload['output']}")
    print(f"Chunks: {payload['chunks']}")
    print(f"Turns: {len(payload['turns'])}")
    print(str(payload["message"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
