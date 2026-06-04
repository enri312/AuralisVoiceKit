"""Normalize a WAV or ffmpeg-supported audio file to a PCM16 WAV."""

from __future__ import annotations

import argparse

from auralis_voicekit import normalize_pcm16, peak_pcm16, read_audio_as_chunk, rms_pcm16, write_wav
from auralis_voicekit.exceptions import AuralisError


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize audio volume to a PCM16 WAV file.")
    parser.add_argument("input", help="input audio path")
    parser.add_argument("output", help="output WAV path")
    parser.add_argument("--target-peak", type=float, default=0.95, help="target normalized peak")
    parser.add_argument("--max-gain", type=float, default=8.0, help="maximum gain multiplier")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable for MP3 input")
    args = parser.parse_args()

    try:
        chunk = read_audio_as_chunk(args.input, ffmpeg_executable=args.ffmpeg)
        normalized = normalize_pcm16(
            chunk,
            target_peak=args.target_peak,
            max_gain=args.max_gain,
        )
        write_wav(args.output, [normalized])
    except (AuralisError, ValueError) as exc:
        print(str(exc))
        return 1

    print(
        f"Wrote {args.output} "
        f"(gain={normalized.metadata['normalization_gain']:.3f}, "
        f"peak={peak_pcm16(normalized):.3f}, rms={rms_pcm16(normalized):.3f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
