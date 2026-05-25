"""
simulator.py

6-phase chemical reaction simulation engine.
Each phase models a realistic chemical scenario with continuous noise.

Phases:
  0 → Stable equilibrium (buffer solution, pH ~7, T ~25°C)
  1 → Acid addition begins (pH drops 7→4, temperature rises)
  2 → Reaction peak (pH oscillates around 4, high T, variance spikes)
  3 → Neutralization (pH climbs 4→7, temperature stabilizes)
  4 → Overshoot (pH exceeds 7→9, slight instability)
  5 → Return to equilibrium (pH settles to 7, T drops)
"""

import numpy as np
import time
from src.config.settings import SCENARIO_PHASE_DURATIONS


class ChemicalSimulator:
    def __init__(self):
        self.phase = 0
        self.phase_start = time.time()
        self.phase_durations = SCENARIO_PHASE_DURATIONS
        self.t = 0.0  # internal time counter
        self.dt = 0.05  # 50ms steps = 20Hz

        # State
        self.ph = 7.0
        self.temperature = 25.0
        self.color_r = 128
        self.color_g = 128
        self.color_b = 128

        # Noise
        self.rng = np.random.default_rng()

    def _phase_targets(self):
        """Define target values per phase."""
        return [
            # phase: (pH, temp, R, G, B)
            (7.0,  25.0, 200, 200, 100),  # 0: stable
            (4.0,  45.0, 220,  80,  60),  # 1: acid addition
            (4.2,  55.0, 255,  40,  20),  # 2: reaction peak
            (7.0,  40.0, 180, 160,  80),  # 3: neutralization
            (9.0,  35.0,  80, 200, 180),  # 4: overshoot
            (7.0,  26.0, 200, 200, 100),  # 5: equilibrium
        ]

    def _noise_scale(self):
        """Noise magnitude per phase — higher during instability."""
        scales = [0.02, 0.08, 0.25, 0.12, 0.10, 0.03]
        return scales[self.phase]

    def tick(self) -> dict:
        """Advance simulation by one step. Returns current sensor readings."""
        now = time.time()
        elapsed = now - self.phase_start

        # Advance phase
        if elapsed > self.phase_durations[self.phase]:
            self.phase = (self.phase + 1) % len(self.phase_durations)
            self.phase_start = now

        targets = self._phase_targets()[self.phase]
        ph_target, temp_target, r_target, g_target, b_target = targets

        # Smooth approach to target with noise
        noise = self.rng.normal(0, self._noise_scale())
        alpha = 0.05  # smoothing factor

        self.ph = self.ph + alpha * (ph_target - self.ph) + noise
        self.ph = float(np.clip(self.ph, 0.0, 14.0))

        self.temperature = self.temperature + alpha * (temp_target - self.temperature) + \
                           self.rng.normal(0, self._noise_scale() * 0.3)
        self.temperature = float(np.clip(self.temperature, 15.0, 100.0))

        self.color_r = int(np.clip(self.color_r + alpha * (r_target - self.color_r), 0, 255))
        self.color_g = int(np.clip(self.color_g + alpha * (g_target - self.color_g), 0, 255))
        self.color_b = int(np.clip(self.color_b + alpha * (b_target - self.color_b), 0, 255))

        self.t += self.dt

        return {
            "timestamp": now,
            "ph": self.ph,
            "temperature": self.temperature,
            "color_r": self.color_r,
            "color_g": self.color_g,
            "color_b": self.color_b,
            "phase": self.phase,
            "phase_name": ["Stable", "Acid Addition", "Reaction Peak",
                           "Neutralization", "Overshoot", "Equilibrium"][self.phase],
        }

    def reset(self):
        self.__init__()

    def inject_disturbance(self, magnitude=0.5):
        """Manually inject a spike — for live demo."""
        self.ph += self.rng.uniform(-magnitude * 2, magnitude * 2)
        self.temperature += self.rng.uniform(0, magnitude * 10)
        self.ph = float(np.clip(self.ph, 0.0, 14.0))
