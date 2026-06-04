"""System text-to-speech output backend."""

from __future__ import annotations

from collections.abc import Callable
import platform
import shutil
import subprocess

from ..config import VoiceKitConfig
from ..exceptions import BackendNotAvailable
from .base import BackendInfo


Runner = Callable[..., subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


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

    def _command(self, text: str, config: VoiceKitConfig) -> list[str]:
        executable = self._resolve_executable()
        if executable is None:
            raise BackendNotAvailable(self._missing_message())

        if self._system == "Windows":
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$speaker.Speak($args[0])"
            )
            return [executable, "-NoProfile", "-NonInteractive", "-Command", script, text]

        if self._system == "Darwin":
            command = [executable]
            if config.output_device is not None:
                command.extend(["-v", str(config.output_device)])
            command.append(text)
            return command

        if self._system == "Linux":
            name = self._executable_name(executable)
            if name == "espeak" and config.output_device is not None:
                return [executable, "-v", str(config.output_device), text]
            return [executable, text]

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

    def _missing_message(self) -> str:
        candidates = ", ".join(self._candidate_executables()) or "no known command"
        return (
            f"System speech output is not available on {self._system!r}. "
            f"Expected one of: {candidates}."
        )

    @staticmethod
    def _executable_name(path: str) -> str:
        normalized = path.replace("\\", "/").rstrip("/")
        return normalized.rsplit("/", 1)[-1].lower()
