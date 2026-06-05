"""Safe system speech output example.

The default mode is a dry run: it exercises the real ``system`` backend shape
with an injected runner, records the command that would be executed and emits
normal output events without playing audio. Pass ``--speak`` to use the real
operating system speech command.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import platform
import subprocess

from auralis_voicekit import (
    AuralisVoiceKit,
    BackendNotAvailable,
    VoiceEventType,
    VoiceKitConfig,
)
from auralis_voicekit.backends import SystemSpeechOutputBackend, create_default_registry


@dataclass(slots=True)
class DryRunSystemRunner:
    """Record system speech commands instead of running them."""

    system: str
    commands: list[list[str]] = field(default_factory=list)

    def __call__(self, command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        argv = [str(item) for item in command]
        self.commands.append(argv)
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=self._stdout_for(argv),
            stderr="",
        )

    def _stdout_for(self, argv: list[str]) -> str:
        if self.system == "Windows" and any("GetInstalledVoices" in item for item in argv):
            return "Microsoft Helena\tes-ES\tFemale\tAdult\nMicrosoft David\ten-US\tMale\tAdult\n"
        if self.system == "Darwin" and argv[-2:] == ["-v", "?"]:
            return "Monica              es_ES    # Hola soy Monica\nAlex                en_US    # Hello\n"
        if self.system == "Linux" and argv[-1:] == ["--voices"]:
            return (
                "Pty Language Age/Gender VoiceName File Other Languages\n"
                " 5  es             M  spanish  europe/es\n"
                " 5  en-us          F  english-us  en/en-us\n"
            )
        return ""


def run_demo(
    text: str = "Hola desde AuralisVoiceKit",
    *,
    voice: str | None = None,
    rate: int | None = None,
    volume: int | None = None,
    system: str | None = None,
    dry_run: bool = True,
    include_voices: bool = True,
) -> dict[str, object]:
    """Run a safe system output demo and return an inspectable payload."""

    system_name = system or platform.system()
    registry = create_default_registry()
    dry_runner: DryRunSystemRunner | None = None

    if dry_run:
        dry_runner = DryRunSystemRunner(system_name)
        backend = SystemSpeechOutputBackend(
            system=system_name,
            runner=dry_runner,
            which=_dry_run_which(system_name),
        )
        registry.register_output("system", lambda: backend)

    kit = AuralisVoiceKit(
        VoiceKitConfig(
            output_backend="system",
            output_voice=voice,
            output_rate=rate,
            output_volume=volume,
            privacy_mode=True,
        ),
        registry=registry,
    )
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

    voices = []
    voice_error = None
    if include_voices:
        try:
            list_voices = getattr(kit.output, "list_voices")
            voices = [voice_item.to_dict() for voice_item in list_voices()]
        except BackendNotAvailable as exc:
            voice_error = str(exc)

    output_error = None
    spoken = False
    try:
        kit.speak(text)
        spoken = True
    except BackendNotAvailable as exc:
        output_error = str(exc)
    finally:
        unsubscribe()

    commands = dry_runner.commands if dry_runner is not None else []
    return {
        "backend": "system",
        "dry_run": dry_run,
        "system": system_name,
        "text_characters": len(text),
        "voice": voice,
        "rate": rate,
        "volume": volume,
        "spoken": spoken,
        "error": output_error,
        "voice_error": voice_error,
        "voices": voices,
        "events": events,
        "commands": [{"argv": command} for command in commands],
        "message": "Dry run only. Pass --speak to play audio with the real system backend."
        if dry_run
        else "Real system speech backend was requested.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe system output backend demo.")
    parser.add_argument("--text", default="Hola desde AuralisVoiceKit", help="text to speak or simulate")
    parser.add_argument("--voice", help="system voice selector when supported")
    parser.add_argument("--rate", type=int, help="system speech rate when supported")
    parser.add_argument("--volume", type=int, help="system speech volume when supported")
    parser.add_argument(
        "--system",
        help="override platform name for dry-run command examples",
    )
    parser.add_argument(
        "--speak",
        action="store_true",
        help="play audio with the real system backend; default is dry-run",
    )
    parser.add_argument("--no-voices", action="store_true", help="skip voice listing")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()

    payload = run_demo(
        args.text,
        voice=args.voice,
        rate=args.rate,
        volume=args.volume,
        system=args.system,
        dry_run=not args.speak,
        include_voices=not args.no_voices,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Backend: {payload['backend']}")
        print(f"System: {payload['system']}")
        print(f"Dry run: {payload['dry_run']}")
        print(f"Spoken: {payload['spoken']}")
        print(f"Voices: {len(payload['voices'])}")
        print(f"Commands: {len(payload['commands'])}")
        if payload["error"]:
            print(f"Error: {payload['error']}")
        else:
            print(str(payload["message"]))
    return 1 if payload["error"] else 0


def _dry_run_which(system_name: str):
    def which(name: str) -> str | None:
        if system_name == "Windows" and name == "powershell.exe":
            return "C:\\Windows\\System32\\powershell.exe"
        if system_name == "Darwin" and name == "say":
            return "/usr/bin/say"
        if system_name == "Linux" and name == "espeak":
            return "/usr/bin/espeak"
        return None

    return which


if __name__ == "__main__":
    raise SystemExit(main())
