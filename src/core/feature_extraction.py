"""
feature_extraction.py

Extracts meaningful features from the rolling sensor buffer.
All features are normalized to [0, 1] for use in the sonification engine.

Features extracted:
  - ph_value          : current pH (normalized)
  - temp_value        : current temperature (normalized)
  - luminance         : RGB luminance (normalized)
  - dpH_dt            : rate of change of pH (signed, normalized)
  - rolling_variance  : rolling variance of pH window
  - volatility        : combined instability metric
  - trend             : longer-term pH direction
"""

import numpy as np
from collections import deque
from src.config.settings import (
    PH_MIN, PH_MAX, TEMP_MIN, TEMP_MAX,
    VARIANCE_WINDOW, RATE_WINDOW
)


class FeatureExtractor:
    def __init__(self):
        self.ph_buffer = deque(maxlen=VARIANCE_WINDOW)
        self.temp_buffer = deque(maxlen=VARIANCE_WINDOW)

    def update(self, sensor_data: dict) -> dict:
        ph = sensor_data["ph"]
        temp = sensor_data["temperature"]
        r = sensor_data.get("color_r", 128)
        g = sensor_data.get("color_g", 128)
        b = sensor_data.get("color_b", 128)

        self.ph_buffer.append(ph)
        self.temp_buffer.append(temp)

        ph_arr = np.array(self.ph_buffer)
        temp_arr = np.array(self.temp_buffer)

        # Normalized values
        ph_norm = (ph - PH_MIN) / (PH_MAX - PH_MIN)
        temp_norm = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)

        # Luminance (perceptual)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

        # Rate of change (dpH/dt) — over last RATE_WINDOW samples
        if len(ph_arr) >= RATE_WINDOW:
            dpH_dt = (ph_arr[-1] - ph_arr[-RATE_WINDOW]) / RATE_WINDOW
        else:
            dpH_dt = 0.0

        # Rolling variance
        if len(ph_arr) >= 2:
            rolling_var = float(np.var(ph_arr))
        else:
            rolling_var = 0.0

        # Volatility — combination of variance and rate
        volatility = min(1.0, (abs(dpH_dt) * 3.0 + rolling_var * 5.0))

        # Trend — linear regression slope over full buffer
        if len(ph_arr) >= 5:
            x = np.arange(len(ph_arr))
            coeffs = np.polyfit(x, ph_arr, 1)
            trend = float(np.clip(coeffs[0] * 10, -1.0, 1.0))  # normalized slope
        else:
            trend = 0.0

        return {
            "ph_value": ph,
            "ph_norm": ph_norm,
            "temp_value": temp,
            "temp_norm": temp_norm,
            "luminance": luminance,
            "dpH_dt": dpH_dt,
            "rolling_variance": rolling_var,
            "volatility": volatility,
            "trend": trend,
        }
