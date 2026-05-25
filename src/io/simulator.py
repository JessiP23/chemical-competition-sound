"""
Real-time chemical reaction simulator.

Generates simulated pH, temperature, and color data for testing
the system without physical hardware.
"""

import numpy as np
import time
import random
from typing import Optional, Tuple
from dataclasses import dataclass

from src.config.settings import SimulationConfig


@dataclass
class SensorReading:
    """Container for simulated sensor reading."""
    ph: float
    temperature: float
    color_r: Optional[float] = None
    color_g: Optional[float] = None
    color_b: Optional[float] = None
    timestamp: float = 0.0


class ChemicalSimulator:
    """
    Real-time chemical reaction simulator.
    
    Simulates realistic chemical reaction behavior including:
    - pH curves (acid-base reactions)
    - Temperature changes (exothermic/endothermic)
    - Instability spikes
    - Reaction transitions
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize chemical simulator.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        
        # Current state
        self.current_ph = self.config.BASE_PH
        self.current_temp = self.config.BASE_TEMP
        self.current_time = 0.0
        
        # Disturbance state
        self.in_disturbance = False
        self.disturbance_start = 0.0
        self.disturbance_type = None
        
        # Reaction phase
        self.phase = "stable"  # stable, rising, falling, oscillating
        self.phase_start = 0.0
        
        # Color simulation
        self.color_r = 100.0
        self.color_g = 150.0
        self.color_b = 200.0
    
    def update(self, dt: Optional[float] = None) -> SensorReading:
        """
        Update simulation by one time step.
        
        Args:
            dt: Time step in seconds (uses config default if None)
        
        Returns:
            SensorReading with current simulated values
        """
        if dt is None:
            dt = self.config.TIME_STEP
        
        self.current_time += dt
        
        # Update pH
        self._update_ph(dt)
        
        # Update temperature
        self._update_temperature(dt)
        
        # Update color
        self._update_color(dt)
        
        # Handle disturbances
        self._handle_disturbances(dt)
        
        # Add noise
        ph_noisy = self.current_ph + np.random.normal(0, self.config.PH_NOISE_STD)
        temp_noisy = self.current_temp + np.random.normal(0, self.config.TEMP_NOISE_STD)
        
        # Clamp values to valid ranges
        ph_noisy = max(0.0, min(14.0, ph_noisy))
        temp_noisy = max(0.0, min(100.0, temp_noisy))
        
        return SensorReading(
            ph=ph_noisy,
            temperature=temp_noisy,
            color_r=self.color_r,
            color_g=self.color_g,
            color_b=self.color_b,
            timestamp=self.current_time
        )
    
    def _update_ph(self, dt: float) -> None:
        """Update pH based on reaction phase."""
        if self.in_disturbance:
            # During disturbance, pH changes rapidly
            if self.disturbance_type == "acid_spike":
                self.current_ph -= 2.0 * dt
            elif self.disturbance_type == "base_spike":
                self.current_ph += 2.0 * dt
            elif self.disturbance_type == "oscillation":
                self.current_ph += 3.0 * np.sin(self.current_time * 5.0) * dt
        else:
            # Normal reaction dynamics
            if self.phase == "stable":
                # Slow drift toward neutral
                if self.current_ph > 7.0:
                    self.current_ph -= 0.1 * dt
                elif self.current_ph < 7.0:
                    self.current_ph += 0.1 * dt
            
            elif self.phase == "rising":
                # Gradual pH increase
                self.current_ph += 0.3 * dt
                if self.current_ph > 10.0:
                    self.phase = "stable"
            
            elif self.phase == "falling":
                # Gradual pH decrease
                self.current_ph -= 0.3 * dt
                if self.current_ph < 4.0:
                    self.phase = "stable"
            
            elif self.phase == "oscillating":
                # Oscillating pH
                self.current_ph += 0.5 * np.sin(self.current_time * 2.0) * dt
        
        # Clamp pH
        self.current_ph = max(0.0, min(14.0, self.current_ph))
    
    def _update_temperature(self, dt: float) -> None:
        """Update temperature based on reaction state."""
        if self.in_disturbance:
            # During disturbance, temperature changes rapidly
            if self.disturbance_type == "heat_spike":
                self.current_temp += 5.0 * dt
            elif self.disturbance_type == "cool_spike":
                self.current_temp -= 5.0 * dt
        else:
            # Normal temperature dynamics
            # Temperature tends toward ambient (25°C)
            ambient = 25.0
            diff = ambient - self.current_temp
            self.current_temp += diff * 0.1 * dt
            
            # Add reaction heat based on pH deviation from neutral
            ph_deviation = abs(self.current_ph - 7.0)
            self.current_temp += ph_deviation * 0.05 * dt
        
        # Clamp temperature
        self.current_temp = max(0.0, min(100.0, self.current_temp))
    
    def _update_color(self, dt: float) -> None:
        """Update color based on pH (simulating indicator dye)."""
        # Simulate pH indicator color change
        # Acidic (low pH) → Red
        # Neutral (pH 7) → Green
        # Basic (high pH) → Blue
        
        if self.current_ph < 4.0:
            # Acidic - red dominant
            target_r, target_g, target_b = 255, 50, 50
        elif self.current_ph < 7.0:
            # Slightly acidic - orange/yellow
            target_r, target_g, target_b = 255, 200, 50
        elif self.current_ph < 10.0:
            # Neutral to slightly basic - green
            target_r, target_g, target_b = 50, 255, 100
        else:
            # Basic - blue
            target_r, target_g, target_b = 50, 100, 255
        
        # Smooth transition
        self.color_r += (target_r - self.color_r) * 0.1
        self.color_g += (target_g - self.color_g) * 0.1
        self.color_b += (target_b - self.color_b) * 0.1
    
    def _handle_disturbances(self, dt: float) -> None:
        """Handle disturbance generation and expiration."""
        # Check if disturbance should end
        if self.in_disturbance:
            if self.current_time - self.disturbance_start > self.config.DISTURBANCE_DURATION:
                self.in_disturbance = False
                self.disturbance_type = None
        else:
            # Randomly trigger disturbances
            if random.random() < self.config.DISTURBANCE_PROBABILITY:
                self._trigger_disturbance()
    
    def _trigger_disturbance(self) -> None:
        """Trigger a random disturbance."""
        self.in_disturbance = True
        self.disturbance_start = self.current_time
        
        # Random disturbance type
        disturbance_types = [
            "acid_spike",
            "base_spike",
            "heat_spike",
            "cool_spike",
            "oscillation"
        ]
        self.disturbance_type = random.choice(disturbance_types)
    
    def trigger_disturbance(self, disturbance_type: str) -> None:
        """
        Manually trigger a specific disturbance.
        
        Args:
            disturbance_type: Type of disturbance to trigger
        """
        self.in_disturbance = True
        self.disturbance_start = self.current_time
        self.disturbance_type = disturbance_type
    
    def set_phase(self, phase: str) -> None:
        """
        Set reaction phase.
        
        Args:
            phase: Phase name (stable, rising, falling, oscillating)
        """
        self.phase = phase
        self.phase_start = self.current_time
    
    def reset(self) -> None:
        """Reset simulator to initial state."""
        self.current_ph = self.config.BASE_PH
        self.current_temp = self.config.BASE_TEMP
        self.current_time = 0.0
        self.in_disturbance = False
        self.disturbance_type = None
        self.phase = "stable"
        self.color_r = 100.0
        self.color_g = 150.0
        self.color_b = 200.0
    
    def get_state(self) -> dict:
        """Get current simulator state."""
        return {
            "ph": self.current_ph,
            "temperature": self.current_temp,
            "phase": self.phase,
            "in_disturbance": self.in_disturbance,
            "disturbance_type": self.disturbance_type,
            "time": self.current_time
        }


class PresetScenario:
    """Predefined simulation scenarios for demo purposes."""
    
    @staticmethod
    def stable_reaction() -> ChemicalSimulator:
        """Create simulator in stable reaction mode."""
        sim = ChemicalSimulator()
        sim.set_phase("stable")
        return sim
    
    @staticmethod
    def acid_base_titration() -> ChemicalSimulator:
        """Create simulator simulating acid-base titration."""
        sim = ChemicalSimulator()
        sim.current_ph = 2.0  # Start acidic
        sim.set_phase("rising")
        return sim
    
    @staticmethod
    def exothermic_reaction() -> ChemicalSimulator:
        """Create simulator simulating exothermic reaction."""
        sim = ChemicalSimulator()
        sim.current_temp = 20.0
        sim.trigger_disturbance("heat_spike")
        return sim
    
    @staticmethod
    def unstable_oscillation() -> ChemicalSimulator:
        """Create simulator with unstable oscillating behavior."""
        sim = ChemicalSimulator()
        sim.set_phase("oscillating")
        return sim
