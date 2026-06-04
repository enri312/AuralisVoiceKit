"""High-level voice sessions for segmenting and transcribing turns."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import threading
import time
from typing import Callable, Iterable

from .audio import (
    VoiceActivityConfig,
    VoiceSegment,
    normalize_pcm16,
    read_audio,
    read_wav,
    segment_voice_pcm16,
)
from .kit import AuralisVoiceKit
from .models import AudioChunk, TranscriptResult


TurnHandler = Callable[["VoiceTurn"], bool | None]
ChunkHandler = Callable[[AudioChunk], bool | None]


@dataclass(frozen=True, slots=True)
class VoiceSessionConfig:
    """Configuration for high-level listen/segment/transcribe workflows."""

    chunk_duration_ms: int = 50
    voice_activity: VoiceActivityConfig = field(default_factory=VoiceActivityConfig)
    max_turns: int | None = None
    ffmpeg_executable: str = "ffmpeg"
    normalize_segments: bool = False
    normalization_target_peak: float = 0.95
    normalization_max_gain: float = 8.0
    capture_poll_interval_ms: int = 50

    def __post_init__(self) -> None:
        if self.chunk_duration_ms <= 0:
            raise ValueError("chunk_duration_ms must be greater than zero")
        if self.max_turns is not None and self.max_turns <= 0:
            raise ValueError("max_turns must be greater than zero")
        if self.normalization_target_peak <= 0 or self.normalization_target_peak > 1:
            raise ValueError(
                "normalization_target_peak must be greater than zero and less than or equal to one"
            )
        if self.normalization_max_gain <= 0:
            raise ValueError("normalization_max_gain must be greater than zero")
        if self.capture_poll_interval_ms <= 0:
            raise ValueError("capture_poll_interval_ms must be greater than zero")


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
        self._cancel_event = threading.Event()
        self._lock = threading.RLock()
        self._capture_active = False
        self._closed = False

    def __enter__(self) -> "VoiceSession":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def is_cancelled(self) -> bool:
        """Return whether this session has been asked to stop."""

        return self._cancel_event.is_set()

    @property
    def is_closed(self) -> bool:
        """Return whether this session has been closed."""

        return self._closed

    def cancel(self) -> None:
        """Ask active capture/transcription loops to stop gracefully."""

        self._cancel_event.set()

    def reset_cancel(self) -> None:
        """Clear a previous cancellation so the session can be reused."""

        self._ensure_open()
        self._cancel_event.clear()

    def close(self) -> None:
        """Cancel the session and stop active capture if needed."""

        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._cancel_event.set()
        self._stop_capture_if_active()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("VoiceSession is closed")

    def _should_stop(self) -> bool:
        return self._closed or self._cancel_event.is_set()

    def _stop_capture_if_active(self) -> None:
        with self._lock:
            if not self._capture_active:
                return
            self._capture_active = False
        self.kit.stop_capture()

    def segment_chunks(self, chunks: Iterable[AudioChunk]) -> list[VoiceSegment]:
        self._ensure_open()
        if self._should_stop():
            return []
        return segment_voice_pcm16(chunks, config=self.config.voice_activity)

    def transcribe_segment(self, segment: VoiceSegment, index: int) -> VoiceTurn:
        self._ensure_open()
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
        if self.config.normalize_segments:
            chunk = normalize_pcm16(
                chunk,
                target_peak=self.config.normalization_target_peak,
                max_gain=self.config.normalization_max_gain,
            )
        result = self.kit.transcribe(chunk)
        merged_metadata = {**result.metadata, **chunk.metadata}
        result = replace(result, metadata=merged_metadata)
        return VoiceTurn(index=index, segment=segment, transcript=result)

    def transcribe_segments(
        self,
        segments: Iterable[VoiceSegment],
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        self._ensure_open()
        turns: list[VoiceTurn] = []
        for index, segment in enumerate(segments, start=1):
            if self._should_stop():
                break
            if self.config.max_turns is not None and index > self.config.max_turns:
                break
            turn = self.transcribe_segment(segment, index)
            turns.append(turn)
            if on_turn is not None:
                should_continue = on_turn(turn)
                if should_continue is False:
                    self.cancel()
                    break
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
        self._ensure_open()
        chunks = read_wav(path, chunk_duration_ms=self.config.chunk_duration_ms)
        return self.transcribe_chunks(chunks, on_turn=on_turn)

    def transcribe_file(
        self,
        path: str,
        on_turn: TurnHandler | None = None,
    ) -> list[VoiceTurn]:
        self._ensure_open()
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
        on_chunk: ChunkHandler | None = None,
    ) -> list[AudioChunk]:
        self._ensure_open()
        if self._should_stop():
            return []

        chunks: list[AudioChunk] = []

        def handle_chunk(chunk: AudioChunk) -> None:
            if self._should_stop():
                return
            chunks.append(chunk)
            if on_chunk is not None:
                should_continue = on_chunk(chunk)
                if should_continue is False:
                    self.cancel()

        started = False
        try:
            self.kit.start_capture(handle_chunk)
            started = True
            with self._lock:
                self._capture_active = True
            deadline = time.monotonic() + max(0.0, seconds)
            poll_interval = self.config.capture_poll_interval_ms / 1000
            while not self._should_stop():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._cancel_event.wait(min(poll_interval, remaining))
        finally:
            if started:
                self._stop_capture_if_active()
        return chunks

    def listen_once(
        self,
        seconds: float,
        on_turn: TurnHandler | None = None,
        on_chunk: ChunkHandler | None = None,
    ) -> list[VoiceTurn]:
        chunks = self.capture_for(seconds, on_chunk=on_chunk)
        return self.transcribe_chunks(chunks, on_turn=on_turn)
