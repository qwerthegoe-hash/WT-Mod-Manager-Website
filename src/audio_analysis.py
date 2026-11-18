"""Bounded, format-aware waveform samples for local WAV previews.

Uncompressed PCM WAV only. Other formats remain playable via QMediaPlayer,
but we must not present decorative random bars as if they were actual audio.
"""
from __future__ import annotations

import sys
import wave
from functools import lru_cache
from pathlib import Path


def _level(buffer: bytes, width: int) -> float:
    if not buffer or width not in (1, 2, 3, 4):
        return 0.0
    total = len(buffer) // width
    stride = max(1, total // 300)
    peak = 0.0
    for i in range(0, total, stride):
        part = buffer[i * width:(i + 1) * width]
        if width == 1:
            sample = (part[0] - 128) / 128.0
        elif width == 2:
            sample = int.from_bytes(part, "little", signed=True) / 32768.0
        elif width == 3:
            sample = int.from_bytes(part, "little", signed=True) / 8388608.0
        else:
            sample = int.from_bytes(part, "little", signed=True) / 2147483648.0
        peak = max(peak, abs(sample))
    return min(1.0, peak)


@lru_cache(maxsize=48)
def _wav_peaks_cached(filename: str, size: int, mtime_ns: int, samples: int) -> tuple[float, ...]:
    del size, mtime_ns
    with wave.open(filename, "rb") as stream:
        if stream.getcomptype() != "NONE":
            raise ValueError("Compressed WAV is not supported for waveform display.")
        count = stream.getnframes()
        width = stream.getsampwidth()
        channels = stream.getnchannels()
        if not count or width not in (1, 2, 3, 4) or not (1 <= channels <= 8):
            raise ValueError("Unsupported WAV sample format.")
        readings = []
        for column in range(samples):
            start = min(count - 1, (column * count) // samples)
            stream.setpos(start)
            frames = stream.readframes(min(300, count - start))
            readings.append(_level(frames, width))
        return tuple(readings)


def wav_peaks(path: Path | str, samples: int = 140) -> list[float] | None:
    """Returns real audio peaks for PCM WAV; None if unsupported/invalid."""
    path = Path(path)
    if path.suffix.lower() != ".wav" or not path.is_file() or path.is_symlink():
        return None
    if not 16 <= samples <= 240:
        raise ValueError("Invalid waveform resolution.")
    try:
        stat = path.stat()
        if stat.st_size > 120 * 1024 * 1024:
            return None
        return list(_wav_peaks_cached(str(path.resolve()), stat.st_size, stat.st_mtime_ns, samples))
    except (OSError, EOFError, wave.Error, ValueError):
        return None
