"""Waveform data must reflect the actual PCM WAV, not decorative fake bars."""
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from src.audio_analysis import wav_peaks


def write_wave(path, samples):
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(8000)
        file.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))


class AudioWaveTests(unittest.TestCase):
    def test_peaks_detect_audio_signal(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "demo.wav"
            frames = ([0] * 800) + ([16000] * 800) + ([0] * 800)
            write_wave(file, frames)
            peaks = wav_peaks(file, samples=60)
            self.assertIsNotNone(peaks)
            self.assertEqual(len(peaks), 60)
            self.assertLess(peaks[4], 0.02)
            self.assertGreater(peaks[24], 0.45)
            self.assertLess(peaks[-1], 0.02)
            self.assertEqual(wav_peaks(file, samples=60), peaks)

    def test_unsupported_formats_show_no_fake_waveform(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "audio.mp3"
            file.write_bytes(b"not actually an mp3")
            self.assertIsNone(wav_peaks(file))
            self.assertIsNone(wav_peaks(Path(folder) / "missing.wav"))

    def test_out_of_range_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "demo.wav"
            write_wave(file, [0] * 800)
            with self.assertRaises(ValueError):
                wav_peaks(file, samples=1000)

    def test_corrupt_wav_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "invalid.wav"
            file.write_bytes(b"bad WAV")
            self.assertIsNone(wav_peaks(file))


if __name__ == "__main__":
    unittest.main()
