"""
ringbuffer.py

Thread-safe shared state container.
Used to pass data between the processing thread and the Streamlit dashboard.

Contains:
  - Sensor history (pH, temperature, color)
  - Feature history (for charts)
  - State history (for event timeline)
  - Spectrogram buffer (for real-time spectrogram display)
"""

import numpy as np
from collections import deque
from threading import Lock
from src.config.settings import HISTORY_LENGTH


class SharedState:
    def __init__(self):
        self._lock = Lock()
        self.ph_history = deque(maxlen=HISTORY_LENGTH)
        self.temp_history = deque(maxlen=HISTORY_LENGTH)
        self.state_history = deque(maxlen=HISTORY_LENGTH)
        self.timestamp_history = deque(maxlen=HISTORY_LENGTH)
        self.spectrogram_buffer = np.zeros((64, 80))  # freq_bins x time_steps
        self.waveform_buffer = np.zeros(1024)
        self.current_state = "stable"
        self.current_features = {}

    def update(self, sensor_data: dict, features: dict, state: str):
        """Thread-safe update of all buffers."""
        with self._lock:
            self.ph_history.append(sensor_data["ph"])
            self.temp_history.append(sensor_data["temperature"])
            self.state_history.append(state)
            self.timestamp_history.append(sensor_data["timestamp"])
            self.current_state = state
            self.current_features = features

    def update_spectrogram(self, audio_chunk: np.ndarray):
        """Compute and update spectrogram from audio chunk."""
        with self._lock:
            # Compute FFT
            fft = np.abs(np.fft.rfft(audio_chunk))
            # Shift buffer left
            self.spectrogram_buffer = np.roll(self.spectrogram_buffer, -1, axis=1)
            # Insert new column (normalized)
            col = fft[:64] / (np.max(fft) + 1e-6)
            self.spectrogram_buffer[:, -1] = col

    def update_waveform(self, waveform: np.ndarray):
        """Update waveform buffer for display."""
        with self._lock:
            self.waveform_buffer = waveform

    def get_history(self):
        """Thread-safe read of all history buffers."""
        with self._lock:
            return {
                "ph": list(self.ph_history),
                "temp": list(self.temp_history),
                "state": list(self.state_history),
                "timestamp": list(self.timestamp_history),
            }

    def get_spectrogram(self):
        """Thread-safe read of spectrogram buffer."""
        with self._lock:
            return self.spectrogram_buffer.copy()

    def get_waveform(self):
        """Thread-safe read of waveform buffer."""
        with self._lock:
            return self.waveform_buffer.copy()

    def get_current(self):
        """Thread-safe read of current state and features."""
        with self._lock:
            return {
                "state": self.current_state,
                "features": dict(self.current_features),
            }
