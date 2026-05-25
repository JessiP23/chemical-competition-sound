"""
synthesis.py

Low-level waveform generation primitives.
Used by tone_engine.py to build the complete audio scene.

Key techniques:
  - Additive synthesis: sum of harmonically related sine waves
  - Frequency modulation (FM): vibrato implementation
  - Noise band: filtered white noise for instability
  - Amplitude envelope: smooth fade in/out to prevent clicks
"""

import numpy as np
from src.config.settings import SAMPLE_RATE


def sine_wave(freq: float, duration: float, amplitude: float = 1.0,
              phase: float = 0.0) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t + phase)


def fm_sine(carrier_freq: float, mod_rate: float, mod_depth_semitones: float,
            duration: float, amplitude: float = 1.0) -> np.ndarray:
    """FM synthesis for vibrato effect."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    mod_depth_hz = carrier_freq * (2 ** (mod_depth_semitones / 12) - 1)
    modulator = mod_depth_hz * np.sin(2 * np.pi * mod_rate * t)
    return amplitude * np.sin(2 * np.pi * carrier_freq * t + modulator)


def additive_synthesis(fundamental: float, harmonics: list,
                       duration: float, amplitudes: list = None) -> np.ndarray:
    """
    Additive synthesis: sum of harmonics.
    harmonics: list of multipliers [1.0, 1.5, 2.0, ...]
    amplitudes: per-harmonic amplitudes (defaults to 1/n rolloff)
    """
    n = len(harmonics)
    if amplitudes is None:
        amplitudes = [1.0 / (i + 1) for i in range(n)]

    output = np.zeros(int(SAMPLE_RATE * duration))
    for mult, amp in zip(harmonics, amplitudes):
        output += sine_wave(fundamental * mult, duration, amp)

    # Normalize
    if np.max(np.abs(output)) > 0:
        output /= np.max(np.abs(output))
    return output


def noise_band(center_freq: float, bandwidth: float,
               duration: float, amplitude: float = 1.0) -> np.ndarray:
    """Band-pass filtered white noise centered at center_freq."""
    from scipy.signal import butter, sosfilt
    samples = int(SAMPLE_RATE * duration)
    noise = np.random.randn(samples)
    nyq = SAMPLE_RATE / 2.0
    low = max(0.001, (center_freq - bandwidth / 2) / nyq)
    high = min(0.999, (center_freq + bandwidth / 2) / nyq)
    sos = butter(4, [low, high], btype='band', output='sos')
    filtered = sosfilt(sos, noise)
    if np.max(np.abs(filtered)) > 0:
        filtered = filtered / np.max(np.abs(filtered)) * amplitude
    return filtered


def apply_envelope(signal: np.ndarray, attack_ms: float = 10.0,
                   release_ms: float = 10.0) -> np.ndarray:
    """Apply fade-in/fade-out to prevent clicks."""
    attack_samples = int(SAMPLE_RATE * attack_ms / 1000)
    release_samples = int(SAMPLE_RATE * release_ms / 1000)
    n = len(signal)

    envelope = np.ones(n)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    if release_samples > 0:
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)

    return signal * envelope


def apply_brightness(signal: np.ndarray, brightness: float) -> np.ndarray:
    """Low-pass filter to control timbre brightness (0.0=dark, 1.0=full)."""
    from scipy.signal import butter, sosfilt
    cutoff = 0.05 + brightness * 0.9  # 0.05 to 0.95 of Nyquist
    cutoff = np.clip(cutoff, 0.01, 0.99)
    sos = butter(2, cutoff, btype='low', output='sos')
    return sosfilt(sos, signal)
