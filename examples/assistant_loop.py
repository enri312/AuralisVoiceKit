"""Minimal listen -> segment -> transcribe loop."""

from __future__ import annotations

import argparse

from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceActivityConfig,
    VoiceKitConfig,
    VoiceSession,
    VoiceSessionConfig,
    VoiceTurn,
)
from auralis_voicekit.exceptions import AuralisError


def _default_model(backend: str, model: str | None) -> str:
    if model:
        return model
    if backend == "whisper":
        return "base"
    if backend == "openai":
        return "gpt-4o-mini-transcribe"
    return "auto"


def _print_turn(turn: VoiceTurn) -> None:
    text = turn.text or "<empty>"
    print(f"[{turn.index}] {turn.duration_seconds:.2f}s rms={turn.rms:.4f}: {text}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a simple voice assistant loop.")
    parser.add_argument("--file", help="process an audio file instead of recording")
    parser.add_argument("--wav", help="alias for --file, kept for compatibility")
    parser.add_argument("--seconds", type=float, default=5.0, help="recording duration")
    parser.add_argument("--device", default=None, help="input device id, name or 'default'")
    parser.add_argument("--capture-backend", default="sounddevice", help="capture backend")
    parser.add_argument("--transcription-backend", default="null", help="transcription backend")
    parser.add_argument("--model", default=None, help="transcription model")
    parser.add_argument("--language", default="es", help="language hint")
    parser.add_argument("--chunk-ms", type=int, default=50, help="chunk size used for WAV input")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    parser.add_argument("--threshold", type=float, default=0.01, help="voice RMS threshold")
    parser.add_argument("--min-voice-ms", type=int, default=120, help="minimum voice duration")
    parser.add_argument("--max-silence-ms", type=int, default=350, help="silence duration that closes a turn")
    parser.add_argument("--pre-speech-ms", type=int, default=100, help="silence kept before speech")
    args = parser.parse_args()

    kit = AuralisVoiceKit(
        VoiceKitConfig(
            capture_backend=args.capture_backend,
            transcription_backend=args.transcription_backend,
            transcription_model=_default_model(args.transcription_backend, args.model),
            language=args.language,
            input_device=args.device,
        )
    )
    session = VoiceSession(
        kit,
        VoiceSessionConfig(
            chunk_duration_ms=args.chunk_ms,
            voice_activity=VoiceActivityConfig(
                threshold=args.threshold,
                min_voice_ms=args.min_voice_ms,
                max_silence_ms=args.max_silence_ms,
                pre_speech_ms=args.pre_speech_ms,
            ),
            ffmpeg_executable=args.ffmpeg,
        ),
    )

    try:
        input_file = args.file or args.wav
        if input_file:
            turns = session.transcribe_file(input_file, on_turn=_print_turn)
        else:
            print(f"Listening for {args.seconds:.1f}s...")
            turns = session.listen_once(args.seconds, on_turn=_print_turn)
    except (AuralisError, ValueError) as exc:
        print(str(exc))
        return 1

    if not turns:
        print("No voice turns detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
