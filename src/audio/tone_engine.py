"""
tone_engine.py

Real-time multi-layer audio engine.
Runs in a dedicated thread, continuously generating audio output.

Architecture:
  - Background thread generates audio at AUDIO_UPDATE_HZ
  - sounddevice OutputStream consumes audio chunks
  - Audio parameters smoothly interpolate between updates (no clicks)
  - 3 independent layers: tone, rhythm, noise
"""

import numpy as np
import sounddevice as sd
import threading
import time
from src.config.settings import SAMPLE_RATE, BUFFER_SIZE, MASTER_VOLUME, AUDIO_UPDATE_HZ
from src.audio.synthesis import (
    additive_synthesis, fm_sine, noise_band, apply_envelope, apply_brightness
)


class ToneEngine:
    def __init__(self):
        self.params = {
            "fundamental_hz": 528.0,
            "harmonics": [1.0, 1.5, 2.0],
            "rhythm_bps": 1.0,
            "lfo_rate_hz": 1.0,
            "brightness": 0.8,
            "pan": 0.0,
            "noise_mix": 0.0,
            "vibrato_rate": 0.0,
            "vibrato_depth": 0.0,
            "state": "stable",
        }
        self._target_params = dict(self.params)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._audio_buffer = np.zeros(BUFFER_SIZE)
        self._phase = 0.0          # continuous phase tracker
        self._rhythm_timer = 0.0   # rhythm beat tracker
        self.waveform_buffer = np.zeros(1024)  # for dashboard display

    def update_params(self, new_params: dict):
        """Called by main loop to update audio targets. Thread-safe."""
        with self._lock:
            self._target_params.update(new_params)

    def _smooth_params(self, alpha=0.05):
        """Interpolate current params toward targets."""
        for key in ["fundamental_hz", "brightness", "noise_mix",
                    "vibrato_rate", "vibrato_depth", "rhythm_bps", "lfo_rate_hz", "pan"]:
            if key in self._target_params:
                current = self.params[key]
                target = self._target_params[key]
                self.params[key] = current + alpha * (target - current)
        # Non-numeric params: copy directly
        for key in ["harmonics", "state"]:
            if key in self._target_params:
                self.params[key] = self._target_params[key]

    def _generate_chunk(self, duration: float) -> np.ndarray:
        """Generate one audio chunk based on current params."""
        p = self.params
        freq = p["fundamental_hz"]
        harmonics = p["harmonics"]
        brightness = p["brightness"]
        noise_mix = p["noise_mix"]
        vib_rate = p["vibrato_rate"]
        vib_depth = p["vibrato_depth"]

        # Layer 1: Harmonic tone with vibrato
        if vib_rate > 0.1 and vib_depth > 0.001:
            tone = fm_sine(freq, vib_rate, vib_depth, duration, amplitude=0.7)
        else:
            tone = additive_synthesis(freq, harmonics, duration)

        tone = apply_brightness(tone, brightness)

        # Layer 2: Noise band (instability layer)
        if noise_mix > 0.01:
            noise = noise_band(freq, freq * 0.3, duration, amplitude=noise_mix)
            tone = tone * (1 - noise_mix) + noise * noise_mix

        # Layer 3: Rhythm pulse (temperature-driven)
        bps = p["rhythm_bps"]
        samples = len(tone)
        t = np.linspace(0, duration, samples)
        # Soft percussive pulse using raised cosine
        rhythm_phase = (t * bps) % 1.0
        pulse = np.exp(-rhythm_phase * 8.0) * 0.3  # exponential decay per beat
        tone = tone * (1.0 + pulse)

        # Apply envelope and master volume
        tone = apply_envelope(tone)
        tone = tone * MASTER_VOLUME

        # Stereo pan
        pan = float(np.clip(p["pan"], -1.0, 1.0))
        left = tone * np.clip(1.0 - pan, 0.0, 1.0)
        right = tone * np.clip(1.0 + pan, 0.0, 1.0)
        stereo = np.column_stack([left, right]).astype(np.float32)

        # Save waveform for dashboard
        display_size = min(1024, len(tone))
        self.waveform_buffer = tone[:display_size].copy()

        return stereo

    def _audio_loop(self):
        chunk_duration = 1.0 / AUDIO_UPDATE_HZ
        with sd.OutputStream(samplerate=SAMPLE_RATE, channels=2,
                             dtype='float32', blocksize=BUFFER_SIZE) as stream:
            while self._running:
                with self._lock:
                    self._smooth_params()
                chunk = self._generate_chunk(chunk_duration)
                stream.write(chunk)

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._audio_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_waveform(self) -> np.ndarray:
        return self.waveform_buffer.copy()
