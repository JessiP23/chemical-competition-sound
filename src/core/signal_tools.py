"""
Signal processing tools for chemical sensor data.

Implements filtering, smoothing, and noise reduction techniques
to prepare raw sensor readings for feature extraction and classification.
"""

import numpy as np
from scipy import signal
from collections import deque
from typing import Deque, List, Tuple


class MovingAverageFilter:
    """Moving average filter for noise reduction."""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.buffer: Deque[float] = deque(maxlen=window_size)
    
    def filter(self, value: float) -> float:
        """Apply moving average filter to input value."""
        self.buffer.append(value)
        if len(self.buffer) < self.window_size:
            return value
        return sum(self.buffer) / len(self.buffer)
    
    def reset(self) -> None:
        """Reset filter buffer."""
        self.buffer.clear()


class LowPassFilter:
    """Butterworth low-pass filter for high-frequency noise removal."""
    
    def __init__(self, cutoff: float = 5.0, order: int = 4, sample_rate: float = 10.0):
        """
        Initialize low-pass filter.
        
        Args:
            cutoff: Cutoff frequency in Hz
            order: Filter order
            sample_rate: Sampling rate in Hz
        """
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        self.b, self.a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        self.zi = signal.lfilter_zi(self.b, self.a)
        self.initialized = False
    
    def filter(self, value: float) -> float:
        """Apply low-pass filter to input value."""
        if not self.initialized:
            self.zi = self.zi * value
            self.initialized = True
        
        filtered, self.zi = signal.lfilter(self.b, self.a, [value], zi=self.zi)
        return filtered[0]
    
    def reset(self) -> None:
        """Reset filter state."""
        self.initialized = False


class ExponentialSmoothing:
    """Exponential smoothing for real-time signal smoothing."""
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize exponential smoothing.
        
        Args:
            alpha: Smoothing factor (0-1). Higher = less smoothing.
        """
        self.alpha = alpha
        self.prev_value: float = 0.0
        self.initialized = False
    
    def filter(self, value: float) -> float:
        """Apply exponential smoothing to input value."""
        if not self.initialized:
            self.prev_value = value
            self.initialized = True
            return value
        
        smoothed = self.alpha * value + (1 - self.alpha) * self.prev_value
        self.prev_value = smoothed
        return smoothed
    
    def reset(self) -> None:
        """Reset smoothing state."""
        self.initialized = False


class MedianFilter:
    """Median filter for spike removal."""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.buffer: Deque[float] = deque(maxlen=window_size)
    
    def filter(self, value: float) -> float:
        """Apply median filter to input value."""
        self.buffer.append(value)
        if len(self.buffer) < self.window_size:
            return value
        return float(np.median(list(self.buffer)))
    
    def reset(self) -> None:
        """Reset filter buffer."""
        self.buffer.clear()


class SignalProcessor:
    """
    Comprehensive signal processing pipeline.
    
    Combines multiple filtering techniques for optimal noise reduction
    while preserving signal dynamics important for chemical monitoring.
    """
    
    def __init__(
        self,
        ma_window: int = 10,
        lpf_cutoff: float = 2.0,
        lpf_order: int = 4,
        sample_rate: float = 10.0,
        smoothing_alpha: float = 0.3,
        median_window: int = 5
    ):
        self.ma_filter = MovingAverageFilter(ma_window)
        self.lpf = LowPassFilter(lpf_cutoff, lpf_order, sample_rate)
        self.exp_smooth = ExponentialSmoothing(smoothing_alpha)
        self.median_filter = MedianFilter(median_window)
    
    def process(self, value: float, use_median: bool = False) -> float:
        """
        Apply full processing pipeline to input value.
        
        Args:
            value: Raw sensor reading
            use_median: Whether to apply median filter (for spike removal)
        
        Returns:
            Processed and filtered signal value
        """
        # Apply median filter first if enabled (removes spikes)
        if use_median:
            value = self.median_filter.filter(value)
        
        # Apply moving average
        value = self.ma_filter.filter(value)
        
        # Apply low-pass filter
        value = self.lpf.filter(value)
        
        # Apply exponential smoothing
        value = self.exp_smooth.filter(value)
        
        return value
    
    def reset(self) -> None:
        """Reset all filters."""
        self.ma_filter.reset()
        self.lpf.reset()
        self.exp_smooth.reset()
        self.median_filter.reset()


def calculate_derivative(signal_data: List[float], dt: float = 1.0) -> List[float]:
    """
    Calculate numerical derivative (rate of change) of signal.
    
    Args:
        signal_data: List of signal values
        dt: Time step between samples
    
    Returns:
        List of derivative values
    """
    if len(signal_data) < 2:
        return [0.0]
    
    derivatives = []
    for i in range(1, len(signal_data)):
        derivative = (signal_data[i] - signal_data[i-1]) / dt
        derivatives.append(derivative)
    
    # Pad with last value for same length
    derivatives.append(derivatives[-1] if derivatives else 0.0)
    return derivatives


def calculate_rolling_variance(signal_data: List[float], window: int = 20) -> List[float]:
    """
    Calculate rolling variance of signal.
    
    Args:
        signal_data: List of signal values
        window: Window size for variance calculation
    
    Returns:
        List of variance values
    """
    if len(signal_data) < window:
        return [0.0] * len(signal_data)
    
    variances = []
    for i in range(len(signal_data)):
        start = max(0, i - window + 1)
        window_data = signal_data[start:i+1]
        if len(window_data) > 1:
            variances.append(np.var(window_data))
        else:
            variances.append(0.0)
    
    return variances


def calculate_rolling_std(signal_data: List[float], window: int = 20) -> List[float]:
    """
    Calculate rolling standard deviation of signal.
    
    Args:
        signal_data: List of signal values
        window: Window size for std calculation
    
    Returns:
        List of std values
    """
    variances = calculate_rolling_variance(signal_data, window)
    return [np.sqrt(v) if v >= 0 else 0.0 for v in variances]


def detect_spikes(
    signal_data: List[float],
    threshold: float = 3.0,
    window: int = 5
) -> List[bool]:
    """
    Detect sudden spikes in signal using z-score method.
    
    Args:
        signal_data: List of signal values
        threshold: Z-score threshold for spike detection
        window: Window size for mean/std calculation
    
    Returns:
        List of boolean values indicating spike detection
    """
    if len(signal_data) < window:
        return [False] * len(signal_data)
    
    spikes = []
    for i in range(len(signal_data)):
        start = max(0, i - window + 1)
        window_data = signal_data[start:i+1]
        
        if len(window_data) < 2:
            spikes.append(False)
            continue
        
        mean = np.mean(window_data[:-1])  # Exclude current point
        std = np.std(window_data[:-1])
        
        if std == 0:
            spikes.append(False)
        else:
            z_score = abs(signal_data[i] - mean) / std
            spikes.append(z_score > threshold)
    
    return spikes


def normalize_signal(signal_data: List[float], min_val: float = 0.0, max_val: float = 1.0) -> List[float]:
    """
    Normalize signal to specified range.
    
    Args:
        signal_data: List of signal values
        min_val: Target minimum value
        max_val: Target maximum value
    
    Returns:
        Normalized signal values
    """
    if len(signal_data) == 0:
        return []
    
    data_min = min(signal_data)
    data_max = max(signal_data)
    
    if data_max == data_min:
        return [min_val] * len(signal_data)
    
    normalized = []
    for value in signal_data:
        norm = (value - data_min) / (data_max - data_min)
        norm = norm * (max_val - min_val) + min_val
        normalized.append(norm)
    
    return normalized
