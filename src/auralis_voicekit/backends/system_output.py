"""System text-to-speech output backend."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import platform
import re
import shutil
import subprocess
from typing import Any

from ..config import VoiceKitConfig
from ..exceptions import BackendNotAvailable
from .base import BackendInfo


Runner = Callable[..., subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class SystemVoice:
    """Voice reported by the local operating system speech command."""

    id: str
    name: str
    language: str | None = None
    gender: str | None = None
    age: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "gender": self.gender,
            "age": self.age,
            "metadata": dict(self.metadata),
        }


class SystemSpeechOutputBackend:
    """Speak text through a lightweight OS-provided command when available."""

    name = "system"

    def __init__(
        self,
        *,
        system: str | None = None,
        runner: Runner = subprocess.run,
        which: Which = shutil.which,
    ) -> None:
        self._system = system or platform.system()
        self._runner = runner
        self._which = which

    def info(self) -> BackendInfo:
        executable = self._resolve_executable()
        if executable is None:
            return BackendInfo(
                name=self.name,
                kind="output",
                available=False,
                reason=self._missing_message(),
                dependencies=self._candidate_executables(),
            )
        return BackendInfo(
            name=self.name,
            kind="output",
            dependencies=(executable,),
        )

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        if not text.strip():
            return

        command = self._command(text, config)
        completed = self._runner(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "").strip()
            if not message:
                message = f"command exited with code {completed.returncode}"
            raise BackendNotAvailable(f"System speech command failed: {message}")

    def list_voices(self) -> tuple[SystemVoice, ...]:
        executable = self._voice_list_executable()
        if executable is None:
            raise BackendNotAvailable(self._missing_message())

        command = self._voice_list_command(executable)
        if command is None:
            return ()

        completed = self._runner(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "").strip()
            if not message:
                message = f"command exited with code {completed.returncode}"
            raise BackendNotAvailable(f"System voice listing failed: {message}")
        return self._parse_voice_list(completed.stdout)

    def _command(self, text: str, config: VoiceKitConfig) -> list[str]:
        executable = self._resolve_executable()
        if executable is None:
            raise BackendNotAvailable(self._missing_message())

        voice = self._selected_voice(config)
        rate = "" if config.output_rate is None else str(config.output_rate)
        volume = "" if config.output_volume is None else str(config.output_volume)

        if self._system == "Windows":
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$voice = $args[1]; "
                "if ($voice) { $speaker.SelectVoice($voice) }; "
                "$rate = $args[2]; "
                "if ($rate -ne '') { $speaker.Rate = [int]$rate }; "
                "$volume = $args[3]; "
                "if ($volume -ne '') { $speaker.Volume = [int]$volume }; "
                "$speaker.Speak($args[0])"
            )
            return [
                executable,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
                text,
                voice or "",
                rate,
                volume,
            ]

        if self._system == "Darwin":
            command = [executable]
            if voice is not None:
                command.extend(["-v", voice])
            if config.output_rate is not None:
                command.extend(["-r", str(config.output_rate)])
            command.append(text)
            return command

        if self._system == "Linux":
            name = self._executable_name(executable)
            command = [executable]
            if name == "espeak":
                if voice is not None:
                    command.extend(["-v", voice])
                if config.output_rate is not None:
                    command.extend(["-s", str(config.output_rate)])
                if config.output_volume is not None:
                    command.extend(["-a", str(config.output_volume)])
            elif name == "spd-say":
                if config.output_rate is not None:
                    command.extend(["-r", str(config.output_rate)])
                if config.output_volume is not None:
                    command.extend(["-i", str(config.output_volume)])
            command.append(text)
            return command

        raise BackendNotAvailable(self._missing_message())

    def _resolve_executable(self) -> str | None:
        for candidate in self._candidate_executables():
            path = self._which(candidate)
            if path is not None:
                return path
        return None

    def _candidate_executables(self) -> tuple[str, ...]:
        if self._system == "Windows":
            return ("powershell.exe", "powershell")
        if self._system == "Darwin":
            return ("say",)
        if self._system == "Linux":
            return ("spd-say", "espeak")
        return ()

    def _voice_list_executable(self) -> str | None:
        if self._system == "Linux":
            return self._which("espeak")
        return self._resolve_executable()

    def _voice_list_command(self, executable: str) -> list[str] | None:
        if self._system == "Windows":
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$speaker.GetInstalledVoices() | ForEach-Object { "
                "$info = $_.VoiceInfo; "
                "[string]::Join(\"`t\", @($info.Name, $info.Culture.Name, $info.Gender, $info.Age)) "
                "}"
            )
            return [executable, "-NoProfile", "-NonInteractive", "-Command", script]
        if self._system == "Darwin":
            return [executable, "-v", "?"]
        if self._system == "Linux" and self._executable_name(executable) == "espeak":
            return [executable, "--voices"]
        return None

    def _parse_voice_list(self, output: str) -> tuple[SystemVoice, ...]:
        if self._system == "Windows":
            return self._parse_windows_voices(output)
        if self._system == "Darwin":
            return self._parse_macos_voices(output)
        if self._system == "Linux":
            return self._parse_espeak_voices(output)
        return ()

    @staticmethod
    def _parse_windows_voices(output: str) -> tuple[SystemVoice, ...]:
        voices = []
        for line in output.splitlines():
            parts = [part.strip() for part in line.split("\t")]
            if not parts or not parts[0]:
                continue
            voices.append(
                SystemVoice(
                    id=parts[0],
                    name=parts[0],
                    language=parts[1] if len(parts) > 1 and parts[1] else None,
                    gender=parts[2] if len(parts) > 2 and parts[2] else None,
                    age=parts[3] if len(parts) > 3 and parts[3] else None,
                )
            )
        return tuple(voices)

    @staticmethod
    def _parse_macos_voices(output: str) -> tuple[SystemVoice, ...]:
        voices = []
        pattern = re.compile(r"^(.+?)\s+([a-z]{2}_[A-Z]{2})\s+#\s*(.*)$")
        for line in output.splitlines():
            match = pattern.match(line.strip())
            if match is None:
                continue
            name = match.group(1).strip()
            language = match.group(2).strip()
            sample = match.group(3).strip()
            voices.append(
                SystemVoice(
                    id=name,
                    name=name,
                    language=language,
                    metadata={"sample": sample} if sample else {},
                )
            )
        return tuple(voices)

    @staticmethod
    def _parse_espeak_voices(output: str) -> tuple[SystemVoice, ...]:
        voices = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 4 or parts[0].lower() == "pty":
                continue
            gender = parts[2][-1:] or None
            voices.append(
                SystemVoice(
                    id=parts[3],
                    name=parts[3],
                    language=parts[1],
                    gender=gender,
                    metadata={"priority": parts[0], "age_gender": parts[2]},
                )
            )
        return tuple(voices)

    def _missing_message(self) -> str:
        candidates = ", ".join(self._candidate_executables()) or "no known command"
        return (
            f"System speech output is not available on {self._system!r}. "
            f"Expected one of: {candidates}."
        )

    @staticmethod
    def _selected_voice(config: VoiceKitConfig) -> str | None:
        if config.output_voice:
            return config.output_voice
        if config.output_device is not None:
            return str(config.output_device)
        return None

    @staticmethod
    def _executable_name(path: str) -> str:
        normalized = path.replace("\\", "/").rstrip("/")
        return normalized.rsplit("/", 1)[-1].lower()
