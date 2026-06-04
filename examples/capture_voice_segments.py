"""Capture microphone audio, calibrate noise and save speech-like segments."""

from __future__ import annotations

import argparse
import os
import time

from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceActivityConfig,
    VoiceActivityDetector,
    VoiceKitConfig,
    calibrate_noise_pcm16,
    write_wav,
)


def _record(config: VoiceKitConfig, seconds: float):
    chunks = []
    kit = AuralisVoiceKit(config)
    try:
        kit.start_capture(chunks.append)
        time.sleep(max(0.0, seconds))
    finally:
        kit.stop_capture()
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture and segment microphone speech.")
    parser.add_argument("--calibrate-seconds", type=float, default=1.0)
    parser.add_argument("--record-seconds", type=float, default=5.0)
    parser.add_argument("--device", default=None, help="input device id, name or 'default'")
    parser.add_argument("--output-dir", default="segments")
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--min-voice-ms", type=int, default=120)
    parser.add_argument("--max-silence-ms", type=int, default=350)
    args = parser.parse_args()

    config = VoiceKitConfig(
        capture_backend="sounddevice",
        input_device=args.device,
        sample_rate=args.sample_rate,
        channels=args.channels,
    )

    print(f"Calibrating ambient noise for {args.calibrate_seconds:.1f}s...")
    noise_chunks = _record(config, args.calibrate_seconds)
    profile = calibrate_noise_pcm16(noise_chunks)
    print(
        "Noise floor={:.4f}, threshold={:.4f}, duration={:.2f}s".format(
            profile.noise_floor,
            profile.threshold,
            profile.duration_seconds,
        )
    )

    print(f"Recording speech for {args.record_seconds:.1f}s...")
    speech_chunks = _record(config, args.record_seconds)
    detector = VoiceActivityDetector(
        VoiceActivityConfig(
            min_voice_ms=args.min_voice_ms,
            max_silence_ms=args.max_silence_ms,
        ),
        noise_profile=profile,
    )
    segments = detector.segment(speech_chunks)

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
