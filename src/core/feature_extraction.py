"""
Feature extraction from chemical sensor data.

Extracts meaningful features from pH, temperature, and other sensor readings
for use in state classification and sonification mapping.
"""

import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.core.signal_tools import (
    calculate_derivative,
    calculate_rolling_variance,
    calculate_rolling_std,
    detect_spikes
)


@dataclass
class SensorFeatures:
    """Container for extracted sensor features."""
    # Raw values
    ph: float
    temperature: float
    color_r: Optional[float] = None
    color_g: Optional[float] = None
    color_b: Optional[float] = None
    
    # Rate of change features
    ph_rate: float = 0.0
    temp_rate: float = 0.0
    
    # Variance features
    ph_variance: float = 0.0
    temp_variance: float = 0.0
    
    # Volatility features
    ph_volatility: float = 0.0
    temp_volatility: float = 0.0
    
    # Spike detection
    ph_spike: bool = False
    temp_spike: bool = False
    
    # Trend features
    ph_trend: str = "stable"  # rising, falling, stable
    temp_trend: str = "stable"
    
    # Composite features
    instability_score: float = 0.0
    transition_intensity: float = 0.0


class FeatureExtractor:
    """
    Extracts features from sensor data streams.
    
    Maintains history buffers for calculating rolling statistics
    and rate-of-change metrics.
    """
    
    def __init__(
        self,
        variance_window: int = 20,
        rate_window: int = 5,
        spike_threshold: float = 3.0
    ):
        """
        Initialize feature extractor.
        
        Args:
            variance_window: Window size for variance calculation
            rate_window: Window size for rate-of-change calculation
            spike_threshold: Z-score threshold for spike detection
        """
        self.variance_window = variance_window
        self.rate_window = rate_window
        self.spike_threshold = spike_threshold
        
        # History buffers
        self.ph_history: deque = deque(maxlen=variance_window)
        self.temp_history: deque = deque(maxlen=variance_window)
        
        # Time tracking for rate calculation
        self.time_history: deque = deque(maxlen=rate_window)
        self.last_timestamp: Optional[float] = None
    
    def extract(
        self,
        ph: float,
        temperature: float,
        timestamp: Optional[float] = None,
        color_r: Optional[float] = None,
        color_g: Optional[float] = None,
        color_b: Optional[float] = None
    ) -> SensorFeatures:
        """
        Extract features from current sensor readings.
        
        Args:
            ph: Current pH value
            temperature: Current temperature value
            timestamp: Current timestamp (for rate calculation)
            color_r: Optional red color channel
            color_g: Optional green color channel
            color_b: Optional blue color channel
        
        Returns:
            SensorFeatures object with all extracted features
        """
        # Update history buffers
        self.ph_history.append(ph)
        self.temp_history.append(temperature)
        
        if timestamp is not None:
            self.time_history.append(timestamp)
            self.last_timestamp = timestamp
        
        # Calculate rate of change
        ph_rate = self._calculate_rate(list(self.ph_history))
        temp_rate = self._calculate_rate(list(self.temp_history))
        
        # Calculate variance
        ph_variance = self._calculate_variance(list(self.ph_history))
        temp_variance = self._calculate_variance(list(self.temp_history))
        
        # Calculate volatility (std dev)
        ph_volatility = np.sqrt(ph_variance) if ph_variance > 0 else 0.0
        temp_volatility = np.sqrt(temp_variance) if temp_variance > 0 else 0.0
        
        # Detect spikes
        ph_spike = self._detect_spike(list(self.ph_history))
        temp_spike = self._detect_spike(list(self.temp_history))
        
        # Determine trends
        ph_trend = self._determine_trend(ph_rate)
        temp_trend = self._determine_trend(temp_rate)
        
        # Calculate composite features
        instability_score = self._calculate_instability_score(
            ph_variance, temp_variance, ph_volatility, temp_volatility
        )
        transition_intensity = self._calculate_transition_intensity(
            ph_rate, temp_rate
        )
        
        return SensorFeatures(
            ph=ph,
            temperature=temperature,
            color_r=color_r,
            color_g=color_g,
            color_b=color_b,
            ph_rate=ph_rate,
            temp_rate=temp_rate,
            ph_variance=ph_variance,
            temp_variance=temp_variance,
            ph_volatility=ph_volatility,
            temp_volatility=temp_volatility,
            ph_spike=ph_spike,
            temp_spike=temp_spike,
            ph_trend=ph_trend,
            temp_trend=temp_trend,
            instability_score=instability_score,
            transition_intensity=transition_intensity
        )
    
    def _calculate_rate(self, data: List[float]) -> float:
        """Calculate rate of change from data buffer."""
        if len(data) < 2:
            return 0.0
        
        # Use simple difference between most recent points
        return data[-1] - data[-2]
    
    def _calculate_variance(self, data: List[float]) -> float:
        """Calculate variance from data buffer."""
        if len(data) < 2:
            return 0.0
        
        return float(np.var(data))
    
    def _detect_spike(self, data: List[float]) -> bool:
        """Detect if current value is a spike."""
        if len(data) < self.variance_window:
            return False
        
        spikes = detect_spikes(data, threshold=self.spike_threshold, window=5)
        return spikes[-1]
    
    def _determine_trend(self, rate: float, threshold: float = 0.01) -> str:
        """Determine trend direction from rate of change."""
        if rate > threshold:
            return "rising"
        elif rate < -threshold:
            return "falling"
        else:
            return "stable"
    
    def _calculate_instability_score(
        self,
        ph_var: float,
        temp_var: float,
        ph_vol: float,
        temp_vol: float
    ) -> float:
        """
        Calculate composite instability score.
        
        Combines variance and volatility metrics into a single
        instability indicator (0-1 normalized).
        """
        # Normalize components
        ph_norm = min(ph_var / 0.5, 1.0)  # Assume max variance of 0.5
        temp_norm = min(temp_var / 5.0, 1.0)  # Assume max variance of 5.0
        ph_vol_norm = min(ph_vol / 0.5, 1.0)
        temp_vol_norm = min(temp_vol / 2.0, 1.0)
        
        # Weighted combination
        instability = (
            0.3 * ph_norm +
            0.3 * temp_norm +
            0.2 * ph_vol_norm +
            0.2 * temp_vol_norm
        )
        
        return min(instability, 1.0)
    
    def _calculate_transition_intensity(
        self,
        ph_rate: float,
        temp_rate: float
    ) -> float:
        """
        Calculate transition intensity.
        
        Measures how rapidly the system is changing state.
        """
        # Normalize rates
        ph_rate_norm = min(abs(ph_rate) / 0.5, 1.0)  # Assume max rate of 0.5
        temp_rate_norm = min(abs(temp_rate) / 2.0, 1.0)  # Assume max rate of 2.0
        
        # Weighted combination
        intensity = 0.5 * ph_rate_norm + 0.5 * temp_rate_norm
        return min(intensity, 1.0)
    
    def reset(self) -> None:
        """Reset all history buffers."""
        self.ph_history.clear()
        self.temp_history.clear()
        self.time_history.clear()
        self.last_timestamp = None


class FeatureBuffer:
    """
    Maintains a buffer of feature history for analysis.
    """
    
    def __init__(self, max_length: int = 300):
        self.max_length = max_length
        self.ph_buffer: deque = deque(maxlen=max_length)
        self.temp_buffer: deque = deque(maxlen=max_length)
        self.instability_buffer: deque = deque(maxlen=max_length)
        self.state_buffer: deque = deque(maxlen=max_length)
    
    def add_features(self, features: SensorFeatures, state: str) -> None:
        """Add features to buffer."""
        self.ph_buffer.append(features.ph)
        self.temp_buffer.append(features.temperature)
        self.instability_buffer.append(features.instability_score)
        self.state_buffer.append(state)
    
    def get_ph_history(self) -> List[float]:
        """Get pH history."""
        return list(self.ph_buffer)
    
    def get_temp_history(self) -> List[float]:
        """Get temperature history."""
        return list(self.temp_buffer)
    
    def get_instability_history(self) -> List[float]:
        """Get instability history."""
        return list(self.instability_buffer)
    
    def get_state_history(self) -> List[str]:
        """Get state history."""
        return list(self.state_buffer)
    
    def reset(self) -> None:
        """Reset all buffers."""
        self.ph_buffer.clear()
        self.temp_buffer.clear()
        self.instability_buffer.clear()
        self.state_buffer.clear()
