"""
Advanced audio synthesis module.

Provides sophisticated synthesis techniques for creating
expressive and perceptually meaningful sonification.
"""

import numpy as np
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class SynthesisParameters:
    """Parameters for synthesis."""
    fundamental: float
    harmonics: List[float]
    harmonic_amplitudes: List[float]
    detune_amount: float
    modulation_index: float
    modulation_rate: float
    filter_cutoff: float
    filter_resonance: float
    envelope_attack: float
    envelope_decay: float
    envelope_sustain: float
    envelope_release: float


class Oscillator:
    """Base oscillator class."""
    
    @staticmethod
    def sine(frequency: float, phase: float = 0.0) -> float:
        """Generate sine wave sample."""
        return np.sin(2 * np.pi * frequency + phase)
    
    @staticmethod
    def sawtooth(frequency: float, phase: float = 0.0) -> float:
        """Generate sawtooth wave sample."""
        return 2.0 * (frequency + phase - np.floor(frequency + phase + 0.5))
    
    @staticmethod
    def square(frequency: float, phase: float = 0.0, duty: float = 0.5) -> float:
        """Generate square wave sample."""
        return 1.0 if (frequency + phase) % 1.0 < duty else -1.0
    
    @staticmethod
    def triangle(frequency: float, phase: float = 0.0) -> float:
        """Generate triangle wave sample."""
        return 2.0 * abs(2.0 * (frequency + phase - np.floor(frequency + phase + 0.5))) - 1.0


class AdditiveSynthesizer:
    """
    Additive synthesis using multiple oscillators.
    
    Builds complex timbres by summing sinusoidal components
    with precise control over harmonic content.
    """
    
    def __init__(self, sample_rate: float = 44100.0):
        self.sample_rate = sample_rate
        self.phase = 0.0
    
    def synthesize(
        self,
        frequency: float,
        harmonics: List[int],
        amplitudes: List[float],
        duration: float,
        phase_offset: float = 0.0
    ) -> np.ndarray:
        """
        Synthesize tone using additive synthesis.
        
        Args:
            frequency: Fundamental frequency
            harmonics: List of harmonic numbers (e.g., [1, 2, 3])
            amplitudes: List of amplitudes for each harmonic
            duration: Duration in seconds
            phase_offset: Initial phase offset
        
        Returns:
            Audio samples
        """
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        signal = np.zeros(num_samples)
        
        for harmonic, amplitude in zip(harmonics, amplitudes):
            freq = frequency * harmonic
            signal += amplitude * np.sin(2 * np.pi * freq * t + phase_offset)
        
        # Normalize
        if np.max(np.abs(signal)) > 0:
            signal = signal / np.max(np.abs(signal))
        
        return signal
    
    def synthesize_chord(
        self,
        frequencies: List[float],
        amplitudes: List[float],
        duration: float
    ) -> np.ndarray:
        """
        Synthesize chord from multiple frequencies.
        
        Args:
            frequencies: List of frequencies
            amplitudes: List of amplitudes
            duration: Duration in seconds
        
        Returns:
            Audio samples
        """
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        signal = np.zeros(num_samples)
        
        for freq, amp in zip(frequencies, amplitudes):
            signal += amp * np.sin(2 * np.pi * freq * t)
        
        # Normalize
        if np.max(np.abs(signal)) > 0:
            signal = signal / np.max(np.abs(signal))
        
        return signal


class FMSynthesizer:
    """
    Frequency modulation synthesis.
    
    Creates rich, evolving timbres through frequency modulation,
    useful for representing dynamic chemical processes.
    """
    
    def __init__(self, sample_rate: float = 44100.0):
        self.sample_rate = sample_rate
    
    def synthesize(
        self,
        carrier_freq: float,
        modulator_freq: float,
        modulation_index: float,
        duration: float
    ) -> np.ndarray:
        """
        Synthesize using FM synthesis.
        
        Args:
            carrier_freq: Carrier frequency
            modulator_freq: Modulator frequency
            modulation_index: Modulation index (depth)
            duration: Duration in seconds
        
        Returns:
            Audio samples
        """
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        # FM synthesis equation
        signal = np.sin(
            2 * np.pi * carrier_freq * t +
            modulation_index * np.sin(2 * np.pi * modulator_freq * t)
        )
        
        return signal


class EnvelopeGenerator:
    """ADSR envelope generator."""
    
    @staticmethod
    def generate(
        num_samples: int,
        attack: float,
        decay: float,
        sustain: float,
        release: float
    ) -> np.ndarray:
        """
        Generate ADSR envelope.
        
        Args:
            num_samples: Total number of samples
            attack: Attack time (0-1, fraction of total)
            decay: Decay time (0-1, fraction of total)
            sustain: Sustain level (0-1)
            release: Release time (0-1, fraction of total)
        
        Returns:
            Envelope values
        """
        envelope = np.zeros(num_samples)
        
        attack_samples = int(num_samples * attack)
        decay_samples = int(num_samples * decay)
        release_samples = int(num_samples * release)
        sustain_samples = num_samples - attack_samples - decay_samples - release_samples
        
        # Attack phase
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay phase
        if decay_samples > 0:
            start = attack_samples
            end = attack_samples + decay_samples
            envelope[start:end] = np.linspace(1, sustain, decay_samples)
        
        # Sustain phase
        if sustain_samples > 0:
            start = attack_samples + decay_samples
            end = start + sustain_samples
            envelope[start:end] = sustain
        
        # Release phase
        if release_samples > 0:
            start = attack_samples + decay_samples + sustain_samples
            envelope[start:] = np.linspace(sustain, 0, release_samples)
        
        return envelope


class Filter:
    """Audio filter implementations."""
    
    @staticmethod
    def low_pass(signal: np.ndarray, cutoff: float, sample_rate: float, order: int = 4) -> np.ndarray:
        """
        Apply low-pass filter.
        
        Args:
            signal: Input signal
            cutoff: Cutoff frequency
            sample_rate: Sample rate
            order: Filter order
        
        Returns:
            Filtered signal
        """
        from scipy import signal as scipy_signal
        
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        b, a = scipy_signal.butter(order, normal_cutoff, btype='low', analog=False)
        filtered = scipy_signal.filtfilt(b, a, signal)
        
        return filtered
    
    @staticmethod
    def high_pass(signal: np.ndarray, cutoff: float, sample_rate: float, order: int = 4) -> np.ndarray:
        """
        Apply high-pass filter.
        
        Args:
            signal: Input signal
            cutoff: Cutoff frequency
            sample_rate: Sample rate
            order: Filter order
        
        Returns:
            Filtered signal
        """
        from scipy import signal as scipy_signal
        
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        b, a = scipy_signal.butter(order, normal_cutoff, btype='high', analog=False)
        filtered = scipy_signal.filtfilt(b, a, signal)
        
        return filtered


class SpectralProcessor:
    """Spectral processing for advanced effects."""
    
    @staticmethod
    def add_harmonics(signal: np.ndarray, amount: float) -> np.ndarray:
        """
        Add harmonics to signal.
        
        Args:
            signal: Input signal
            amount: Harmonic amount (0-1)
        
        Returns:
            Signal with added harmonics
        """
        if amount < 0.01:
            return signal
        
        # Simple harmonic addition using soft clipping
        harmonics = np.tanh(signal * (1 + amount * 3))
        return signal * (1 - amount) + harmonics * amount
    
    @staticmethod
    def add_dissonance(signal: np.ndarray, amount: float) -> np.ndarray:
        """
        Add dissonance to signal.
        
        Args:
            signal: Input signal
            amount: Dissonance amount (0-1)
        
        Returns:
            Signal with added dissonance
        """
        if amount < 0.01:
            return signal
        
        # Add slightly detuned copy
        detuned = np.roll(signal, 1) * amount
        return signal + detuned
    
    @staticmethod
    def apply_spectral_enhancement(signal: np.ndarray, enhancement: float) -> np.ndarray:
        """
        Apply spectral enhancement.
        
        Args:
            signal: Input signal
            enhancement: Enhancement amount (0-1)
        
        Returns:
            Enhanced signal
        """
        if enhancement < 0.01:
            return signal
        
        # Simple enhancement using dynamic range compression
        enhanced = np.tanh(signal * (1 + enhancement))
        return enhanced
