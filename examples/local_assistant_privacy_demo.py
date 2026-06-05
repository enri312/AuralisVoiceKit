"""Local assistant demo with sanitized privacy logs.

This example runs fully offline:

1. generate deterministic synthetic audio;
2. write it to a WAV file;
3. segment and transcribe it with the safe ``null`` backend;
4. answer with the safe ``null`` output backend;
5. write sanitized JSONL event logs with ``PrivacyEventLogger``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auralis_voicekit import (
    AuralisVoiceKit,
    PrivacyEventLogger,
    PrivacyLogConfig,
    VoiceActivityConfig,
    VoiceEventType,
    VoiceKitConfig,
    VoiceSession,
    VoiceSessionConfig,
    VoiceTurn,
    generate_synthetic_audio_chunks,
    write_wav,
)


DEMO_PRIVATE_COMMAND = "enciende la luz del estudio"
DEMO_PRIVATE_TOKEN = "demo-secret-token"


def run_demo(
    *,
    output_dir: str,
    log_path: str | None = None,
    duration_seconds: float = 0.8,
    chunk_duration_ms: int = 100,
    sample_rate: int = 16_000,
) -> dict[str, object]:
    """Run the offline assistant demo and return an inspectable summary."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    input_wav = output / "local_assistant_input.wav"
    event_log = Path(log_path) if log_path is not None else output / "auralis-events.jsonl"

    chunks = generate_synthetic_audio_chunks(
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=1,
        chunk_duration_ms=chunk_duration_ms,
    )
    write_wav(str(input_wav), chunks)

    kit = AuralisVoiceKit(
        VoiceKitConfig(
            transcription_backend="null",
            output_backend="null",
            sample_rate=sample_rate,
            channels=1,
            privacy_mode=True,
        )
    )
    session_config = VoiceSessionConfig(
        chunk_duration_ms=chunk_duration_ms,
        voice_activity=VoiceActivityConfig(
            threshold=0.01,
            min_voice_ms=chunk_duration_ms,
            max_silence_ms=chunk_duration_ms,
            pre_speech_ms=0,
        ),
    )
    responses: list[str] = []

    def handle_turn(turn: VoiceTurn) -> None:
        response = f"Turno {turn.index} detectado; respuesta local segura."
        responses.append(response)
        kit.events.emit(
            VoiceEventType.TRANSCRIPTION_COMPLETED,
            {
                "backend": kit.config.transcription_backend,
                "text": DEMO_PRIVATE_COMMAND,
                "token": DEMO_PRIVATE_TOKEN,
                "metadata": {
                    "path": str(input_wav),
                    "turn": turn.index,
                    "duration_seconds": turn.duration_seconds,
                },
            },
            source="assistant.demo",
        )
        kit.speak(response)

    with PrivacyEventLogger(
        event_log,
        PrivacyLogConfig(privacy_mode=True),
    ) as logger:
        unsubscribe = logger.subscribe(kit.events)
        try:
            with VoiceSession(kit, session_config) as session:
                turns = session.transcribe_wav(str(input_wav), on_turn=handle_turn)
        finally:
            unsubscribe()

    records = _read_jsonl(event_log)
    serialized_log = "\n".join(json.dumps(record, sort_keys=True) for record in records)
    privacy_checks = {
        "text_redacted": DEMO_PRIVATE_COMMAND not in serialized_log,
        "path_redacted": str(input_wav) not in serialized_log,
        "token_redacted": DEMO_PRIVATE_TOKEN not in serialized_log,
    }

    return {
        "input_wav": str(input_wav),
        "log_path": str(event_log),
        "chunks": len(chunks),
        "turns": [turn.to_dict() for turn in turns],
        "responses": responses,
        "utterances": list(getattr(kit.output, "utterances", [])),
        "log_records": len(records),
        "log_event_types": [record["type"] for record in records],
        "privacy_checks": privacy_checks,
        "sanitized_log_preview": records[:6],
        "message": "Offline assistant demo completed with sanitized JSONL logs.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local assistant demo with sanitized logs.")
    parser.add_argument("--output-dir", default="auralis_local_assistant_demo", help="output directory")
    parser.add_argument("--log", help="JSONL log path; defaults inside --output-dir")
    parser.add_argument("--duration", type=float, default=0.8, help="synthetic audio duration")
    parser.add_argument("--chunk-ms", type=int, default=100, help="chunk size in milliseconds")
    parser.add_argument("--sample-rate", type=int, default=16000, help="sample rate")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()

    payload = run_demo(
        output_dir=args.output_dir,
        log_path=args.log,
        duration_seconds=args.duration,
        chunk_duration_ms=args.chunk_ms,
        sample_rate=args.sample_rate,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(str(payload["message"]))
    print(f"Input WAV: {payload['input_wav']}")
    print(f"Log: {payload['log_path']}")
    print(f"Turns: {len(payload['turns'])}")
    print(f"Responses: {len(payload['responses'])}")
    print(f"Log records: {payload['log_records']}")
    print(f"Privacy checks: {payload['privacy_checks']}")
    return 0


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


if __name__ == "__main__":
    raise SystemExit(main())
