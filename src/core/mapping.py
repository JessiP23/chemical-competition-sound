"""
Parameter mapping for sonification.

Maps sensor features and reaction states to audio synthesis parameters
using research-driven sonification principles.
"""

import numpy as np
from typing import Tuple, Dict
from dataclasses import dataclass

from src.core.feature_extraction import SensorFeatures
from src.core.classifier import ReactionState
from src.config.settings import (
    SonificationMappings,
    AudioParameters,
    SensorRanges
)


@dataclass
class AudioMapping:
    """Audio synthesis parameters derived from sensor data."""
    # Pitch parameters
    pitch_center: float  # Hz
    pitch_glide: float  # semitones/second
    
    # Rhythm parameters
    rhythm_density: float  # events/second
    
    # Timbre parameters
    harmonic_consistency: float  # 0-1
    dissonance: float  # 0-1
    distortion: float  # 0-1
    noise_gain: float  # 0-1
    
    # Dynamics
    overall_gain: float  # 0-1
    
    # Special events
    trigger_percussive: bool
    percussive_gain: float


class ParameterMapper:
    """
    Maps sensor features to audio synthesis parameters.
    
    Based on research in:
    - Data sonification theory
    - Psychoacoustic perception
    - Auditory display principles
    """
    
    def __init__(
        self,
        mappings: SonificationMappings = None,
        audio_params: AudioParameters = None,
        sensor_ranges: SensorRanges = None
    ):
        """
        Initialize parameter mapper.
        
        Args:
            mappings: Sonification mapping rules
            audio_params: Audio parameter constraints
            sensor_ranges: Physical sensor ranges
        """
        self.mappings = mappings or SonificationMappings()
        self.audio_params = audio_params or AudioParameters()
        self.sensor_ranges = sensor_ranges or SensorRanges()
    
    def map(
        self,
        features: SensorFeatures,
        state: ReactionState
    ) -> AudioMapping:
        """
        Map sensor features and state to audio parameters.
        
        Args:
            features: Extracted sensor features
            state: Current reaction state
        
        Returns:
            AudioMapping with all synthesis parameters
        """
        # Map pH to pitch center
        pitch_center = self._map_ph_to_pitch(features.ph)
        
        # Map pH rate to pitch glide
        pitch_glide = self._map_ph_rate_to_glide(features.ph_rate)
        
        # Map temperature to rhythm density
        rhythm_density = self._map_temp_to_rhythm(features.temperature)
        
        # Map stability to harmonic consistency
        harmonic_consistency = self._map_stability_to_harmonic(
            features.instability_score
        )
        
        # Map instability to dissonance
        dissonance = self._map_instability_to_dissonance(
            features.instability_score
        )
        
        # Map state to distortion
        distortion = self._map_state_to_distortion(state)
        
        # Map state to noise gain
        noise_gain = self._map_state_to_noise(state)
        
        # Map overall gain based on state
        overall_gain = self._map_state_to_gain(state)
        
        # Detect percussive trigger
        trigger_percussive, percussive_gain = self._detect_percussive_trigger(
            features.ph_spike,
            features.temp_spike,
            features.transition_intensity
        )
        
        return AudioMapping(
            pitch_center=pitch_center,
            pitch_glide=pitch_glide,
            rhythm_density=rhythm_density,
            harmonic_consistency=harmonic_consistency,
            dissonance=dissonance,
            distortion=distortion,
            noise_gain=noise_gain,
            overall_gain=overall_gain,
            trigger_percussive=trigger_percussive,
            percussive_gain=percussive_gain
        )
    
    def _map_ph_to_pitch(self, ph: float) -> float:
        """
        Map pH value to pitch center.
        
        Rationale: pH represents the fundamental chemical property.
        Lower pitch for acidic, higher pitch for basic.
        Neutral pH (7.0) maps to neutral pitch (A4 = 440Hz).
        
        Mapping: 0-14 pH → 110-880 Hz (A2 to A5)
        """
        # Normalize pH to 0-1 range
        norm_ph = (ph - self.sensor_ranges.PH_MIN) / (
            self.sensor_ranges.PH_MAX - self.sensor_ranges.PH_MIN
        )
        norm_ph = max(0.0, min(1.0, norm_ph))
        
        # Map to pitch range
        pitch_min, pitch_max = self.mappings.PH_TO_PITCH
        pitch = pitch_min + norm_ph * (pitch_max - pitch_min)
        
        return pitch
    
    def _map_ph_rate_to_glide(self, ph_rate: float) -> float:
        """
        Map pH rate of change to pitch glide.
        
        Rationale: Rate of change indicates reaction dynamics.
        Faster changes produce more dramatic glides.
        
        Mapping: Rate → 0-2 semitones/second
        """
        # Normalize rate (assume max rate of 0.5 pH/s)
        norm_rate = min(abs(ph_rate) / 0.5, 1.0)
        
        # Map to glide range
        glide_min, glide_max = self.mappings.PH_RATE_TO_GLIDE
        glide = glide_min + norm_rate * (glide_max - glide_min)
        
        # Apply direction
        if ph_rate < 0:
            glide = -glide
        
        return glide
    
    def _map_temp_to_rhythm(self, temperature: float) -> float:
        """
        Map temperature to rhythm density.
        
        Rationale: Temperature correlates with reaction energy.
        Higher temperature = more rhythmic activity.
        
        Mapping: 0-100°C → 0.5-8.0 events/second
        """
        # Normalize temperature
        norm_temp = (temperature - self.sensor_ranges.TEMP_MIN) / (
            self.sensor_ranges.TEMP_MAX - self.sensor_ranges.TEMP_MIN
        )
        norm_temp = max(0.0, min(1.0, norm_temp))
        
        # Map to rhythm range
        rhythm_min, rhythm_max = self.mappings.TEMP_TO_RHYTHM
        rhythm = rhythm_min + norm_temp * (rhythm_max - rhythm_min)
        
        return rhythm
    
    def _map_stability_to_harmonic(self, instability: float) -> float:
        """
        Map instability score to harmonic consistency.
        
        Rationale: Stable reactions produce consonant harmonies.
        Instability introduces dissonance.
        
        Mapping: 0-1 instability → 1-0 harmonic consistency
        """
        harmonic_min, harmonic_max = self.mappings.STABILITY_TO_HARMONIC
        harmonic = harmonic_max - instability * (harmonic_max - harmonic_min)
        return max(harmonic_min, min(harmonic_max, harmonic))
    
    def _map_instability_to_dissonance(self, instability: float) -> float:
        """
        Map instability score to dissonance level.
        
        Rationale: Direct mapping of instability to perceptual tension.
        
        Mapping: 0-1 instability → 0-1 dissonance
        """
        dissonance_min, dissonance_max = self.mappings.INSTABILITY_TO_DISSONANCE
        dissonance = dissonance_min + instability * (dissonance_max - dissonance_min)
        return max(dissonance_min, min(dissonance_max, dissonance))
    
    def _map_state_to_distortion(self, state: ReactionState) -> float:
        """
        Map reaction state to distortion level.
        
        Rationale: Critical conditions require perceptual urgency.
        Distortion creates alert-like quality.
        
        Mapping: State → 0-1 distortion
        """
        state_distortion = {
            ReactionState.STABLE: 0.0,
            ReactionState.TRANSITIONAL: 0.1,
            ReactionState.CRITICAL: self.mappings.CRITICAL_DISTORTION,
            ReactionState.CHAOTIC: 0.9
        }
        
        return state_distortion.get(state, 0.0)
    
    def _map_state_to_noise(self, state: ReactionState) -> float:
        """
        Map reaction state to noise layer gain.
        
        Rationale: Chaos represented through broadband noise.
        
        Mapping: State → 0-1 noise gain
        """
        state_noise = {
            ReactionState.STABLE: 0.0,
            ReactionState.TRANSITIONAL: 0.1,
            ReactionState.CRITICAL: 0.3,
            ReactionState.CHAOTIC: self.mappings.CHAOTIC_NOISE_GAIN
        }
        
        return state_noise.get(state, 0.0)
    
    def _map_state_to_gain(self, state: ReactionState) -> float:
        """
        Map reaction state to overall gain.
        
        Rationale: Critical states should be more prominent.
        """
        state_gain = {
            ReactionState.STABLE: 0.5,
            ReactionState.TRANSITIONAL: 0.6,
            ReactionState.CRITICAL: 0.8,
            ReactionState.CHAOTIC: 0.7
        }
        
        return state_gain.get(state, 0.5)
    
    def _detect_percussive_trigger(
        self,
        ph_spike: bool,
        temp_spike: bool,
        transition_intensity: float
    ) -> Tuple[bool, float]:
        """
        Detect if percussive event should be triggered.
        
        Rationale: Abrupt changes should be marked percussively
        to draw attention to anomalies.
        """
        trigger = ph_spike or temp_spike or transition_intensity > 0.7
        
        if trigger:
            gain = self.mappings.PERCUSSIVE_GAIN
            if transition_intensity > 0.7:
                gain = min(1.0, gain + transition_intensity * 0.2)
            return True, gain
        
        return False, 0.0


def normalize_audio_parameter(value: float, min_val: float, max_val: float) -> float:
    """Clamp audio parameter to valid range."""
    return max(min_val, min(max_val, value))


def get_state_audio_description(state: ReactionState) -> str:
    """Get audio description for state."""
    descriptions = {
        ReactionState.STABLE: "Calm, harmonic tones with steady rhythm",
        ReactionState.TRANSITIONAL: "Evolving pitch with moderate rhythmic activity",
        ReactionState.CRITICAL: "Tense, dissonant with distortion and urgency",
        ReactionState.CHAOTIC: "Unpredictable, noisy with extreme variation"
    }
    return descriptions.get(state, "Unknown")
