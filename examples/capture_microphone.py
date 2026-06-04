"""Record microphone audio with the optional sounddevice backend."""

from __future__ import annotations

import argparse
import time

from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, write_wav


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture microphone audio to a WAV file.")
    parser.add_argument("--seconds", type=float, default=3.0, help="recording duration")
    parser.add_argument("--device", default=None, help="input device id, name or 'default'")
    parser.add_argument("--output", default="capture.wav", help="WAV output path")
    parser.add_argument("--sample-rate", type=int, default=16000, help="capture sample rate")
    parser.add_argument("--channels", type=int, default=1, help="number of input channels")
    args = parser.parse_args()

    chunks = []
    config = VoiceKitConfig(
        capture_backend="sounddevice",
        input_device=args.device,
        sample_rate=args.sample_rate,
        channels=args.channels,
    )
    kit = AuralisVoiceKit(config)

    print(f"Recording {args.seconds:.1f}s from {args.device or 'default input'}...")
    try:
        kit.start_capture(chunks.append)
        time.sleep(max(0.0, args.seconds))
    finally:
        kit.stop_capture()

    write_wav(args.output, chunks)
    print(f"Wrote {args.output} ({len(chunks)} chunks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
