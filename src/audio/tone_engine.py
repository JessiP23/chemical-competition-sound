"""
Real-time tone engine for audio sonification.

Generates real-time audio based on sensor data using sounddevice
for low-latency audio output.
"""

import numpy as np
import sounddevice as sd
from threading import Thread, Lock
from typing import Optional, Callable
from dataclasses import dataclass

from src.core.mapping import AudioMapping
from src.config.settings import AudioParameters


@dataclass
class AudioState:
    """Current audio synthesis state."""
    pitch_center: float = 440.0
    pitch_glide: float = 0.0
    rhythm_density: float = 2.0
    harmonic_consistency: float = 1.0
    dissonance: float = 0.0
    distortion: float = 0.0
    noise_gain: float = 0.0
    overall_gain: float = 0.5
    trigger_percussive: bool = False
    percussive_gain: float = 0.0


class ToneEngine:
    """
    Real-time audio synthesis engine.
    
    Generates continuous audio based on sensor-derived parameters
    using additive synthesis with real-time parameter control.
    """
    
    def __init__(self, params: Optional[AudioParameters] = None):
        """
        Initialize tone engine.
        
        Args:
            params: Audio parameters
        """
        self.params = params or AudioParameters()
        
        # Audio state
        self.state = AudioState()
        self.state_lock = Lock()
        
        # Stream control
        self.stream: Optional[sd.OutputStream] = None
        self.running = False
        self.thread: Optional[Thread] = None
        
        # Time tracking
        self.phase = 0.0
        self.rhythm_phase = 0.0
        self.percussive_phase = 0.0
        self.percussive_active = False
        
        # Callback for state updates
        self.state_callback: Optional[Callable] = None
    
    def start(self) -> bool:
        """
        Start audio stream.
        
        Returns:
            True if successful, False otherwise
        """
        if self.running:
            return True
        
        try:
            self.stream = sd.OutputStream(
                samplerate=self.params.SAMPLE_RATE,
                channels=self.params.CHANNELS,
                blocksize=self.params.BLOCK_SIZE,
                callback=self._audio_callback
            )
            self.stream.start()
            self.running = True
            return True
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            return False
    
    def stop(self) -> None:
        """Stop audio stream."""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def update_mapping(self, mapping: AudioMapping) -> None:
        """
        Update audio parameters from mapping.
        
        Args:
            mapping: AudioMapping from parameter mapper
        """
        with self.state_lock:
            self.state.pitch_center = mapping.pitch_center
            self.state.pitch_glide = mapping.pitch_glide
            self.state.rhythm_density = mapping.rhythm_density
            self.state.harmonic_consistency = mapping.harmonic_consistency
            self.state.dissonance = mapping.dissonance
            self.state.distortion = mapping.distortion
            self.state.noise_gain = mapping.noise_gain
            self.state.overall_gain = mapping.overall_gain
            
            if mapping.trigger_percussive:
                self.state.trigger_percussive = True
                self.state.percussive_gain = mapping.percussive_gain
                self.percussive_active = True
                self.percussive_phase = 0.0
    
    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Audio callback for real-time synthesis.
        
        Called by sounddevice for each audio block.
        """
        if status:
            print(f"Audio callback status: {status}")
        
        with self.state_lock:
            state = AudioState(
                pitch_center=self.state.pitch_center,
                pitch_glide=self.state.pitch_glide,
                rhythm_density=self.state.rhythm_density,
                harmonic_consistency=self.state.harmonic_consistency,
                dissonance=self.state.dissonance,
                distortion=self.state.distortion,
                noise_gain=self.state.noise_gain,
                overall_gain=self.state.overall_gain,
                trigger_percussive=self.state.trigger_percussive,
                percussive_gain=self.state.percussive_gain
            )
            self.state.trigger_percussive = False
        
        # Generate audio block
        audio = self._generate_block(frames, state)
        
        # Write to output
        outdata[:] = audio.reshape(-1, 1)
    
    def _generate_block(self, frames: int, state: AudioState) -> np.ndarray:
        """
        Generate audio block based on current state.
        
        Args:
            frames: Number of frames to generate
            state: Current audio state
        
        Returns:
            Audio samples
        """
        t = np.arange(frames) / self.params.SAMPLE_RATE
        
        # Update phase
        self.phase += state.pitch_glide * t
        
        # Calculate current pitch with glide
        pitch = state.pitch_center * (2 ** (self.phase / 12.0))
        
        # Generate fundamental tone
        fundamental = np.sin(2 * np.pi * pitch * t)
        
        # Generate harmonics based on consistency
        harmonics = self._generate_harmonics(t, pitch, state.harmonic_consistency)
        
        # Generate dissonant components
        dissonance = self._generate_dissonance(t, pitch, state.dissonance)
        
        # Generate noise layer
        noise = self._generate_noise(frames, state.noise_gain)
        
        # Generate percussive event
        percussive = self._generate_percussive(frames, state)
        
        # Apply distortion
        signal = fundamental + harmonics + dissonance + noise + percussive
        signal = self._apply_distortion(signal, state.distortion)
        
        # Apply overall gain
        signal *= state.overall_gain
        
        # Clip to prevent distortion
        signal = np.clip(signal, -1.0, 1.0)
        
        return signal.astype(np.float32)
    
    def _generate_harmonics(self, t: np.ndarray, pitch: float, consistency: float) -> np.ndarray:
        """
        Generate harmonic components.
        
        Args:
            t: Time array
            pitch: Fundamental frequency
            consistency: Harmonic consistency (0-1)
        
        Returns:
            Harmonic signal
        """
        if consistency < 0.1:
            return np.zeros_like(t)
        
        harmonics = np.zeros_like(t)
        
        # Number of harmonics based on consistency
        num_harmonics = int(consistency * 8) + 1
        
        for i in range(2, num_harmonics + 1):
            # Harmonic amplitude decreases with harmonic number
            amplitude = (1.0 / i) * consistency
            harmonics += amplitude * np.sin(2 * np.pi * pitch * i * t)
        
        return harmonics
    
    def _generate_dissonance(self, t: np.ndarray, pitch: float, dissonance: float) -> np.ndarray:
        """
        Generate dissonant components.
        
        Args:
            t: Time array
            pitch: Fundamental frequency
            dissonance: Dissonance level (0-1)
        
        Returns:
            Dissonant signal
        """
        if dissonance < 0.1:
            return np.zeros_like(t)
        
        # Generate slightly detuned oscillators
        detune1 = pitch * 1.01
        detune2 = pitch * 0.99
        
        dissonant = (
            0.5 * np.sin(2 * np.pi * detune1 * t) +
            0.5 * np.sin(2 * np.pi * detune2 * t)
        )
        
        return dissonant * dissonance
    
    def _generate_noise(self, frames: int, gain: float) -> np.ndarray:
        """
        Generate noise layer.
        
        Args:
            frames: Number of frames
            gain: Noise gain (0-1)
        
        Returns:
            Noise signal
        """
        if gain < 0.01:
            return np.zeros(frames)
        
        noise = np.random.randn(frames) * gain
        return noise
    
    def _generate_percussive(self, frames: int, state: AudioState) -> np.ndarray:
        """
        Generate percussive event.
        
        Args:
            frames: Number of frames
            state: Current audio state
        
        Returns:
            Percussive signal
        """
        if not self.percussive_active:
            return np.zeros(frames)
        
        # Generate exponential decay
        decay_rate = 10.0
        t = np.arange(frames) / self.params.SAMPLE_RATE
        envelope = np.exp(-decay_rate * (t + self.percussive_phase))
        
        # Generate noise burst
        noise = np.random.randn(frames) * envelope * state.percussive_gain
        
        # Update percussive phase
        self.percussive_phase += frames / self.params.SAMPLE_RATE
        
        # Check if percussive event is complete
        if self.percussive_phase > 0.5:  # 0.5 second duration
            self.percussive_active = False
            self.percussive_phase = 0.0
        
        return noise
    
    def _apply_distortion(self, signal: np.ndarray, amount: float) -> np.ndarray:
        """
        Apply distortion to signal.
        
        Args:
            signal: Input signal
            amount: Distortion amount (0-1)
        
        Returns:
            Distorted signal
        """
        if amount < 0.01:
            return signal
        
        # Soft clipping distortion
        threshold = 1.0 - amount * 0.5
        distorted = np.tanh(signal / threshold) * threshold
        
        # Mix with original
        return signal * (1 - amount) + distorted * amount
    
    def is_running(self) -> bool:
        """Check if audio engine is running."""
        return self.running
    
    def get_sample_rate(self) -> int:
        """Get sample rate."""
        return self.params.SAMPLE_RATE
