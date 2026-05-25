"""
Central configuration for Chemical-to-Audio Intelligent Monitoring System.

This module defines all system parameters, thresholds, and mapping rules
for both simulation and hardware modes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class SystemMode(Enum):
    """System operation modes."""
    SIMULATION = "simulation"
    HARDWARE = "hardware"


class ReactionState(Enum):
    """Chemical reaction states."""
    STABLE = "stable"
    TRANSITIONAL = "transitional"
    CRITICAL = "critical"
    CHAOTIC = "chaotic"


@dataclass
class SensorRanges:
    """Physical sensor ranges and calibration parameters."""
    PH_MIN: float = 0.0
    PH_MAX: float = 14.0
    PH_NEUTRAL: float = 7.0
    
    TEMP_MIN: float = 0.0
    TEMP_MAX: float = 100.0
    TEMP_OPTIMAL: float = 25.0
    
    COLOR_R_MIN: int = 0
    COLOR_R_MAX: int = 255
    COLOR_G_MIN: int = 0
    COLOR_G_MAX: int = 255
    COLOR_B_MIN: int = 0
    COLOR_B_MAX: int = 255


@dataclass
class ClassificationThresholds:
    """Thresholds for state classification."""
    # pH rate of change thresholds (pH units/second)
    PH_RATE_STABLE: float = 0.01
    PH_RATE_TRANSITIONAL: float = 0.05
    PH_RATE_CRITICAL: float = 0.15
    
    # Temperature rate of change thresholds (°C/second)
    TEMP_RATE_STABLE: float = 0.1
    TEMP_RATE_TRANSITIONAL: float = 0.5
    TEMP_RATE_CRITICAL: float = 1.0
    
    # Variance thresholds
    VARIANCE_STABLE: float = 0.01
    VARIANCE_TRANSITIONAL: float = 0.05
    VARIANCE_CRITICAL: float = 0.15
    
    # Volatility thresholds
    VOLATILITY_STABLE: float = 0.02
    VOLATILITY_TRANSITIONAL: float = 0.1
    VOLATILITY_CRITICAL: float = 0.3


@dataclass
class AudioParameters:
    """Audio synthesis parameters."""
    SAMPLE_RATE: int = 44100
    BLOCK_SIZE: int = 1024
    CHANNELS: int = 1
    
    # Pitch mapping (Hz)
    PITCH_MIN: float = 110.0  # A2
    PITCH_MAX: float = 880.0  # A5
    PITCH_NEUTRAL: float = 440.0  # A4
    
    # Rhythm density (events per second)
    RHYTHM_MIN: float = 0.5
    RHYTHM_MAX: float = 8.0
    RHYTHM_NEUTRAL: float = 2.0
    
    # Harmonic consistency (0-1)
    HARMONIC_MIN: float = 0.0
    HARMONIC_MAX: float = 1.0
    
    # Dissonance level (0-1)
    DISSONANCE_MIN: float = 0.0
    DISSONANCE_MAX: float = 1.0
    
    # Distortion level (0-1)
    DISTORTION_MIN: float = 0.0
    DISTORTION_MAX: float = 1.0


@dataclass
class SonificationMappings:
    """
    Research-driven sonification mappings based on:
    - Data sonification theory
    - Psychoacoustic principles
    - Auditory display best practices
    """
    
    # pH → Pitch Center
    # Rationale: pH represents the fundamental chemical property.
    # Lower pitch for acidic, higher pitch for basic.
    PH_TO_PITCH: Tuple[float, float] = (110.0, 880.0)  # A2 to A5
    
    # pH Movement → Pitch Glide
    # Rationale: Rate of change indicates reaction dynamics.
    # Faster changes produce more dramatic glides.
    PH_RATE_TO_GLIDE: Tuple[float, float] = (0.0, 2.0)  # semitones/second
    
    # Temperature → Rhythm Density
    # Rationale: Temperature correlates with reaction energy.
    # Higher temperature = more rhythmic activity.
    TEMP_TO_RHYTHM: Tuple[float, float] = (0.5, 8.0)  # events/second
    
    # Stability → Harmonic Consistency
    # Rationale: Stable reactions produce consonant harmonies.
    # Instability introduces dissonance.
    STABILITY_TO_HARMONIC: Tuple[float, float] = (0.0, 1.0)
    
    # Instability → Dissonance
    # Rationale: Direct mapping of instability to perceptual tension.
    INSTABILITY_TO_DISSONANCE: Tuple[float, float] = (0.0, 1.0)
    
    # Sudden Spikes → Percussive Events
    # Rationale: Abrupt changes should be marked percussively
    # to draw attention to anomalies.
    SPIKE_THRESHOLD: float = 0.3  # normalized change
    PERCUSSIVE_GAIN: float = 0.8
    
    # Critical States → Distortion
    # Rationale: Critical conditions require perceptual urgency.
    # Distortion creates alert-like quality.
    CRITICAL_DISTORTION: float = 0.7
    
    # Chaotic States → Noise Layers
    # Rationale: Chaos represented through broadband noise.
    CHAOTIC_NOISE_GAIN: float = 0.5


@dataclass
class SignalProcessingConfig:
    """Signal processing parameters."""
    # Moving average window size
    MA_WINDOW: int = 10
    
    # Low-pass filter cutoff frequency (Hz)
    LPF_CUTOFF: float = 5.0
    LPF_ORDER: int = 4
    
    # Rolling window for variance calculation
    VARIANCE_WINDOW: int = 20
    
    # Rate of change calculation window
    RATE_WINDOW: int = 5
    
    # Smoothing factor for exponential smoothing
    SMOOTHING_ALPHA: float = 0.3


@dataclass
class SerialConfig:
    """Serial communication configuration for Arduino."""
    BAUD_RATE: int = 115200
    TIMEOUT: float = 1.0
    DATA_DELIMITER: str = ","
    
    # Arduino pin assignments
    PH_PIN: int = 0  # Analog A0
    TEMP_PIN: int = 2  # Digital D2 (1-wire)
    COLOR_SDA_PIN: int = 20  # I2C SDA (if using Mega)
    COLOR_SCL_PIN: int = 21  # I2C SCL (if using Mega)


@dataclass
class VoiceConfig:
    """Voice engine configuration."""
    ENABLED: bool = True
    RATE: int = 150  # words per minute
    VOLUME: float = 0.8
    VOICE_INDEX: int = 0
    
    # Cooldown between voice alerts (seconds)
    ALERT_COOLDOWN: float = 10.0
    
    # State change announcements
    ANNOUNCE_STATE_CHANGES: bool = True


@dataclass
class DashboardConfig:
    """Streamlit dashboard configuration."""
    REFRESH_INTERVAL: int = 100  # milliseconds
    HISTORY_LENGTH: int = 300  # number of data points to display
    
    # Chart colors (dark theme)
    COLOR_PH: str = "#00ff88"
    COLOR_TEMP: str = "#ff6b6b"
    COLOR_VOLATILITY: str = "#ffd93d"
    COLOR_STABLE: str = "#00ff88"
    COLOR_TRANSITIONAL: str = "#ffd93d"
    COLOR_CRITICAL: str = "#ff6b6b"
    COLOR_CHAOTIC: str = "#ff0066"
    
    # Layout
    PAGE_TITLE: str = "Chemical-to-Audio Intelligent Monitoring System"
    PAGE_ICON: str = "🧪"


@dataclass
class SimulationConfig:
    """Simulation mode configuration."""
    # Base values
    BASE_PH: float = 7.0
    BASE_TEMP: float = 25.0
    
    # Noise levels
    PH_NOISE_STD: float = 0.05
    TEMP_NOISE_STD: float = 0.2
    
    # Disturbance parameters
    DISTURBANCE_PROBABILITY: float = 0.01  # per frame
    DISTURBANCE_MAGNITUDE: float = 2.0
    DISTURBANCE_DURATION: float = 5.0  # seconds
    
    # Simulation speed
    TIME_STEP: float = 0.1  # seconds per update


class Settings:
    """Main settings container."""
    
    def __init__(self, mode: SystemMode = SystemMode.SIMULATION):
        self.mode = mode
        self.sensor_ranges = SensorRanges()
        self.classification_thresholds = ClassificationThresholds()
        self.audio_parameters = AudioParameters()
        self.sonification_mappings = SonificationMappings()
        self.signal_processing = SignalProcessingConfig()
        self.serial = SerialConfig()
        self.voice = VoiceConfig()
        self.dashboard = DashboardConfig()
        self.simulation = SimulationConfig()
    
    def get_mode(self) -> SystemMode:
        """Get current system mode."""
        return self.mode
    
    def set_mode(self, mode: SystemMode) -> None:
        """Set system mode."""
        self.mode = mode


# Global settings instance
settings = Settings()
