"""Segment a PCM16 WAV file without recording from a microphone."""

from __future__ import annotations

import argparse
import os

from auralis_voicekit import VoiceActivityConfig, read_wav, segment_voice_pcm16, write_wav


def main() -> int:
    parser = argparse.ArgumentParser(description="Segment a PCM16 WAV file into speech-like clips.")
    parser.add_argument("path", help="input WAV path")
    parser.add_argument("--output-dir", default="wav_segments")
    parser.add_argument("--chunk-ms", type=int, default=50)
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument("--min-voice-ms", type=int, default=120)
    parser.add_argument("--max-silence-ms", type=int, default=350)
    args = parser.parse_args()

    chunks = read_wav(args.path, chunk_duration_ms=args.chunk_ms)
    config = VoiceActivityConfig(
        threshold=args.threshold,
        min_voice_ms=args.min_voice_ms,
        max_silence_ms=args.max_silence_ms,
    )
    segments = segment_voice_pcm16(chunks, config=config)

    os.makedirs(args.output_dir, exist_ok=True)
    for index, segment in enumerate(segments, start=1):
        path = os.path.join(args.output_dir, f"segment_{index:02d}.wav")
        write_wav(path, list(segment.chunks))
        print(f"Wrote {path} ({segment.duration_seconds:.2f}s, rms={segment.rms:.4f})")

    if not segments:
        print("No speech-like segments detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
