"""signal_tools.py — Filtering and smoothing."""

import numpy as np
from scipy.signal import butter, sosfilt_zi, sosfilt
from collections import deque
from src.config.settings import MOVING_AVG_WINDOW, LOWPASS_CUTOFF, LOWPASS_ORDER


def moving_average(data: list, window: int = MOVING_AVG_WINDOW) -> float:
    arr = np.array(data[-window:])
    return float(np.mean(arr))


class LowPassFilter:
    """Online (sample-by-sample) Butterworth low-pass filter."""
    def __init__(self, cutoff: float = LOWPASS_CUTOFF, order: int = LOWPASS_ORDER):
        self.sos = butter(order, cutoff, btype='low', output='sos')
        self.zi = sosfilt_zi(self.sos)[:, :, np.newaxis]  # shape for 1-channel

    def filter(self, sample: float) -> float:
        x = np.array([[sample]])
        out, self.zi = sosfilt(self.sos, x.T, zi=self.zi)
        return float(out[0])
