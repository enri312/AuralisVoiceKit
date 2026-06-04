"""High-level voice sessions for segmenting and transcribing turns."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import time
from typing import Callable, Iterable

from .audio import VoiceActivityConfig, VoiceSegment, read_audio, read_wav, segment_voice_pcm16
from .kit import AuralisVoiceKit
from .models import AudioChunk, TranscriptResult


TurnHandler = Callable[["VoiceTurn"], None]


@dataclass(frozen=True, slots=True)
class VoiceSessionConfig:
    """Configuration for high-level listen/segment/transcribe workflows."""

    chunk_duration_ms: int = 50
    voice_activity: VoiceActivityConfig = field(default_factory=VoiceActivityConfig)
    max_turns: int | None = None
    ffmpeg_executable: str = "ffmpeg"

    def __post_init__(self) -> None:
        if self.chunk_duration_ms <= 0:
            raise ValueError("chunk_duration_ms must be greater than zero")
        if self.max_turns is not None and self.max_turns <= 0:
            raise ValueError("max_turns must be greater than zero")


@dataclass(frozen=True, slots=True)
class VoiceTurn:
    """One speech-like segment and its transcription result."""

    index: int
    segment: VoiceSegment
    transcript: TranscriptResult

    @property
    def text(self) -> str:
        return self.transcript.text

    @property
    def duration_seconds(self) -> float:
        return self.segment.duration_seconds

    @property
    def rms(self) -> float:
        return self.segment.rms

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "text": self.transcript.text,
            "language": self.transcript.language,
            "confidence": self.transcript.confidence,
            "is_final": self.transcript.is_final,
            "source": self.transcript.source,
            "duration_seconds": self.duration_seconds,
            "rms": self.rms,
            "metadata": dict(self.transcript.metadata),
        }


class VoiceSession:
    """Reusable helper for turning captured audio into transcribed voice turns."""

    def __init__(
        self,
        kit: AuralisVoiceKit | None = None,
        config: VoiceSessionConfig | None = None,
    ) -> None:
        self.kit = kit or AuralisVoiceKit()
        self.config = config or VoiceSessionConfig()

    def segment_chunks(self, chunks: Iterable[AudioChunk]) -> list[VoiceSegment]:
        return segment_voice_pcm16(chunks, config=self.config.voice_activity)

    def transcribe_segment(self, segment: VoiceSegment, index: int) -> VoiceTurn:
        metadata = {
            "segment_index": index,
            "segment_chunks": len(segment.chunks),
            "segment_duration_seconds": segment.duration_seconds,
            "segment_rms": segment.rms,
        }
        source_path = segment.chunks[0].metadata.get("path")
        if source_path is not None:
            metadata["path"] = source_path

        chunk = AudioChunk(
            data=segment.data,
            format=segment.chunks[0].format,
            metadata=metadata,
        )
        result = self.kit.transcribe(chunk)
        merged_metadata = {**result.metadata, **metadata}
        result = replace(result, metadata=merged_metadata)
        return VoiceTurn(index=index, segment=segment, transcript=result)

    def transcribe_segments(
        self,
        segments: Iterable[VoiceSegment],
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        turns: list[VoiceTurn] = []
        for index, segment in enumerate(segments, start=1):
            if self.config.max_turns is not None and index > self.config.max_turns:
                break
            turn = self.transcribe_segment(segment, index)
            turns.append(turn)
            if on_turn is not None:
                on_turn(turn)
        return turns

    def transcribe_chunks(
        self,
        chunks: Iterable[AudioChunk],
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        return self.transcribe_segments(self.segment_chunks(chunks), on_turn=on_turn)

    def transcribe_wav(
        self,
        path: str,
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        chunks = read_wav(path, chunk_duration_ms=self.config.chunk_duration_ms)
        return self.transcribe_chunks(chunks, on_turn=on_turn)

    def transcribe_file(
        self,
        path: str,
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        chunks = read_audio(
            path,
            chunk_duration_ms=self.config.chunk_duration_ms,
            sample_rate=self.kit.config.sample_rate,
            channels=self.kit.config.channels,
            ffmpeg_executable=self.config.ffmpeg_executable,
        )
        return self.transcribe_chunks(chunks, on_turn=on_turn)

    def capture_for(
        self,
        seconds: float,
        on_chunk: Callable[[AudioChunk], None] | None = None,
    ) -> list[AudioChunk]:
        chunks: list[AudioChunk] = []

        def handle_chunk(chunk: AudioChunk) -> None:
            chunks.append(chunk)
            if on_chunk is not None:
                on_chunk(chunk)

        started = False
        try:
            self.kit.start_capture(handle_chunk)
            started = True
            time.sleep(max(0.0, seconds))
        finally:
            if started:
                self.kit.stop_capture()
        return chunks

    def listen_once(
        self,
        seconds: float,
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        return self.transcribe_chunks(self.capture_for(seconds), on_turn=on_turn)
