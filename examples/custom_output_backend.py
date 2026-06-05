"""Custom speech output backend example without playing real audio."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json

from auralis_voicekit import AuralisVoiceKit, VoiceEventType, VoiceKitConfig
from auralis_voicekit.backends import BackendInfo, create_default_registry


@dataclass(slots=True)
class MemorySpeechOutputBackend:
    """Collect spoken text in memory instead of playing audio."""

    name: str = "memory"
    utterances: list[str] = field(default_factory=list)

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="output")

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        if not text.strip():
            return
        self.utterances.append(text)


def create_memory_voice_kit() -> tuple[AuralisVoiceKit, MemorySpeechOutputBackend]:
    """Create a kit wired to one inspectable memory output backend."""

    backend = MemorySpeechOutputBackend()
    registry = create_default_registry()
    registry.register_output(backend.name, lambda: backend)
    kit = AuralisVoiceKit(
        VoiceKitConfig(output_backend=backend.name, privacy_mode=True),
        registry=registry,
    )
    return kit, backend


def run_demo(text: str = "Hola desde un backend de salida personalizado") -> dict[str, object]:
    kit, backend = create_memory_voice_kit()
    events: list[dict[str, object]] = []
    unsubscribe = kit.events.subscribe(
        VoiceEventType.ANY,
        lambda event: events.append(
            {
                "type": event.type.value,
                "payload": dict(event.payload),
            }
        ),
    )
    try:
        kit.speak(text)
    finally:
        unsubscribe()

    return {
        "backend": backend.name,
        "utterances": list(backend.utterances),
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a custom output backend demo.")
    parser.add_argument(
        "--text",
        default="Hola desde un backend de salida personalizado",
        help="text to send to the custom output backend",
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()

    payload = run_demo(args.text)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Backend: {payload['backend']}")
    print(f"Utterances: {len(payload['utterances'])}")
    print(f"Events: {len(payload['events'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

