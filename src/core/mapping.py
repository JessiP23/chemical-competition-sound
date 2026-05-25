"""
mapping.py

Parameter Mapping Sonification (PMS) — Hermann, Hunt & Neuhoff, Chapter 15.

Maps 3 data channels to independent audio parameter spaces:
  Channel 1 (pH)         → pitch, harmonic complexity, vibrato
  Channel 2 (temperature) → rhythm density, LFO rate, reverb
  Channel 3 (color)      → timbre brightness, stereo pan, envelope

All mappings use smooth interpolation to prevent audio discontinuities.
"""

import numpy as np
from src.config.settings import (
    PH_FREQ_BASE, PH_FREQ_EXPONENT,
    TEMP_BPM_MIN, TEMP_BPM_MAX,
    PH_MIN, PH_MAX, TEMP_MIN, TEMP_MAX
)


def ph_to_frequency(ph: float) -> float:
    """
    Exponential mapping: pH → Hz
    Grounded in equal-temperament: each pH unit = one semitone.
    pH 7 (neutral) = 528 Hz (perceived as calm/stable).
    """
    # Center at pH 7 = 528 Hz, ±1 semitone per pH unit
    semitones_from_neutral = (ph - 7.0)
    freq = 528.0 * (2 ** (semitones_from_neutral / 12.0))
    return float(np.clip(freq, 80.0, 2000.0))


def state_to_harmonics(state: str) -> list:
    """
    Returns list of harmonic multipliers based on state.
    Consonance = stable perception; dissonance = instability.
    """
    return {
        "stable":       [1.0, 1.5, 2.0],               # root + fifth + octave
        "transitional": [1.0, 1.5, 1.778],              # adds minor 7th
        "critical":     [1.0, 1.414, 1.778, 2.0],       # tritone = max dissonance
        "chaotic":      [1.0, 1.333, 1.414, 1.587, 2.0], # dense dissonant cluster
    }.get(state, [1.0])


def temp_to_rhythm_density(temp: float) -> float:
    """Temperature → beats per second (rhythm density)."""
    t_norm = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
    return TEMP_BPM_MIN + t_norm * (TEMP_BPM_MAX - TEMP_BPM_MIN)


def temp_to_lfo_rate(temp: float) -> float:
    """Temperature → LFO modulation rate (0.1 to 8 Hz)."""
    t_norm = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
    return 0.1 + t_norm * 7.9


def luminance_to_brightness(luminance: float) -> float:
    """
    Color luminance → timbre brightness (filter cutoff multiplier).
    Higher luminance = brighter, more harmonics passed.
    """
    return 0.3 + luminance * 0.7  # 0.3 to 1.0


def luminance_to_pan(luminance: float) -> float:
    """Color luminance → stereo pan (-1 left, 0 center, +1 right)."""
    return (luminance - 0.5) * 2.0  # re-center around 0


def volatility_to_noise_mix(volatility: float) -> float:
    """Higher volatility = more noise mixed into the tone."""
    return min(1.0, volatility ** 0.5)  # square root for perceptual linearity


def dpH_to_vibrato(dpH_dt: float) -> tuple:
    """
    Rate of pH change → vibrato (pitch modulation).
    Returns (vibrato_rate_hz, vibrato_depth_semitones).
    """
    magnitude = abs(dpH_dt)
    rate = np.clip(magnitude * 10.0, 0.0, 12.0)   # 0–12 Hz
    depth = np.clip(magnitude * 5.0, 0.0, 2.0)    # 0–2 semitones
    return float(rate), float(depth)


def compute_audio_params(features: dict, state: str) -> dict:
    """
    Master mapping function.
    Takes feature dict + state string.
    Returns complete audio parameter dict.
    """
    ph = features["ph_value"]
    temp = features["temp_value"]
    lum = features["luminance"]
    vol = features["volatility"]
    dpH = features["dpH_dt"]

    freq = ph_to_frequency(ph)
    harmonics = state_to_harmonics(state)
    rhythm = temp_to_rhythm_density(temp)
    lfo = temp_to_lfo_rate(temp)
    brightness = luminance_to_brightness(lum)
    pan = luminance_to_pan(lum)
    noise_mix = volatility_to_noise_mix(vol)
    vib_rate, vib_depth = dpH_to_vibrato(dpH)

    return {
        "fundamental_hz": freq,
        "harmonics": harmonics,
        "rhythm_bps": rhythm,
        "lfo_rate_hz": lfo,
        "brightness": brightness,
        "pan": pan,
        "noise_mix": noise_mix,
        "vibrato_rate": vib_rate,
        "vibrato_depth": vib_depth,
        "state": state,
    }
