"""
State classification for chemical reaction monitoring.

Classifies chemical reaction states based on sensor features
using threshold-based and pattern-based classification logic.
"""

from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

from src.core.feature_extraction import SensorFeatures
from src.config.settings import (
    ClassificationThresholds,
    ReactionState
)


class ReactionState(Enum):
    """Chemical reaction states."""
    STABLE = "stable"
    TRANSITIONAL = "transitional"
    CRITICAL = "critical"
    CHAOTIC = "chaotic"


@dataclass
class ClassificationResult:
    """Result of state classification."""
    state: ReactionState
    confidence: float
    triggers: list[str]
    severity: float  # 0-1, higher = more severe


class StateClassifier:
    """
    Classifies chemical reaction states based on sensor features.
    
    Uses multi-factor analysis including:
    - Rate of change (pH, temperature)
    - Variance and volatility
    - Spike detection
    - Pattern recognition
    """
    
    def __init__(self, thresholds: Optional[ClassificationThresholds] = None):
        """
        Initialize state classifier.
        
        Args:
            thresholds: Classification thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or ClassificationThresholds()
        self.previous_state: Optional[ReactionState] = None
        self.state_duration: int = 0
        self.state_history: list[ReactionState] = []
    
    def classify(self, features: SensorFeatures) -> ClassificationResult:
        """
        Classify current reaction state from sensor features.
        
        Args:
            features: Extracted sensor features
        
        Returns:
            ClassificationResult with state and metadata
        """
        # Calculate individual factor scores
        ph_rate_score = self._classify_ph_rate(features.ph_rate)
        temp_rate_score = self._classify_temp_rate(features.temp_rate)
        variance_score = self._classify_variance(
            features.ph_variance,
            features.temp_variance
        )
        volatility_score = self._classify_volatility(
            features.ph_volatility,
            features.temp_volatility
        )
        spike_score = self._classify_spikes(features.ph_spike, features.temp_spike)
        
        # Combine scores
        combined_score = self._combine_scores(
            ph_rate_score,
            temp_rate_score,
            variance_score,
            volatility_score,
            spike_score
        )
        
        # Determine state from combined score
        state = self._score_to_state(combined_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(combined_score, state)
        
        # Identify triggers
        triggers = self._identify_triggers(
            ph_rate_score,
            temp_rate_score,
            variance_score,
            volatility_score,
            spike_score
        )
        
        # Calculate severity
        severity = self._calculate_severity(state, combined_score)
        
        # Update state tracking
        self._update_state_tracking(state)
        
        return ClassificationResult(
            state=state,
            confidence=confidence,
            triggers=triggers,
            severity=severity
        )
    
    def _classify_ph_rate(self, ph_rate: float) -> float:
        """
        Classify pH rate of change.
        
        Returns score 0-3 where:
        0 = stable, 1 = transitional, 2 = critical, 3 = chaotic
        """
        abs_rate = abs(ph_rate)
        
        if abs_rate <= self.thresholds.PH_RATE_STABLE:
            return 0.0
        elif abs_rate <= self.thresholds.PH_RATE_TRANSITIONAL:
            return 1.0
        elif abs_rate <= self.thresholds.PH_RATE_CRITICAL:
            return 2.0
        else:
            return 3.0
    
    def _classify_temp_rate(self, temp_rate: float) -> float:
        """
        Classify temperature rate of change.
        
        Returns score 0-3 where:
        0 = stable, 1 = transitional, 2 = critical, 3 = chaotic
        """
        abs_rate = abs(temp_rate)
        
        if abs_rate <= self.thresholds.TEMP_RATE_STABLE:
            return 0.0
        elif abs_rate <= self.thresholds.TEMP_RATE_TRANSITIONAL:
            return 1.0
        elif abs_rate <= self.thresholds.TEMP_RATE_CRITICAL:
            return 2.0
        else:
            return 3.0
    
    def _classify_variance(self, ph_var: float, temp_var: float) -> float:
        """
        Classify variance metrics.
        
        Returns score 0-3.
        """
        # Normalize variance scores
        ph_score = min(ph_var / self.thresholds.VARIANCE_CRITICAL, 3.0)
        temp_score = min(temp_var / self.thresholds.VARIANCE_CRITICAL, 3.0)
        
        # Average the two
        return (ph_score + temp_score) / 2.0
    
    def _classify_volatility(self, ph_vol: float, temp_vol: float) -> float:
        """
        Classify volatility metrics.
        
        Returns score 0-3.
        """
        # Normalize volatility scores
        ph_score = min(ph_vol / self.thresholds.VOLATILITY_CRITICAL, 3.0)
        temp_score = min(temp_vol / self.thresholds.VOLATILITY_CRITICAL, 3.0)
        
        # Average the two
        return (ph_score + temp_score) / 2.0
    
    def _classify_spikes(self, ph_spike: bool, temp_spike: bool) -> float:
        """
        Classify spike detection.
        
        Returns score 0-3.
        """
        if ph_spike and temp_spike:
            return 3.0
        elif ph_spike or temp_spike:
            return 2.0
        else:
            return 0.0
    
    def _combine_scores(
        self,
        ph_rate: float,
        temp_rate: float,
        variance: float,
        volatility: float,
        spikes: float
    ) -> float:
        """
        Combine individual scores into overall state score.
        
        Weighted combination emphasizing rate of change and volatility.
        """
        combined = (
            0.25 * ph_rate +
            0.25 * temp_rate +
            0.15 * variance +
            0.25 * volatility +
            0.10 * spikes
        )
        return combined
    
    def _score_to_state(self, score: float) -> ReactionState:
        """
        Convert combined score to reaction state.
        
        Score ranges:
        0.0 - 0.5: Stable
        0.5 - 1.5: Transitional
        1.5 - 2.5: Critical
        2.5 - 3.0: Chaotic
        """
        if score < 0.5:
            return ReactionState.STABLE
        elif score < 1.5:
            return ReactionState.TRANSITIONAL
        elif score < 2.5:
            return ReactionState.CRITICAL
        else:
            return ReactionState.CHAOTIC
    
    def _calculate_confidence(self, score: float, state: ReactionState) -> float:
        """
        Calculate classification confidence.
        
        Higher confidence when score is clearly within state boundaries.
        """
        # Define state boundaries
        boundaries = {
            ReactionState.STABLE: (0.0, 0.5),
            ReactionState.TRANSITIONAL: (0.5, 1.5),
            ReactionState.CRITICAL: (1.5, 2.5),
            ReactionState.CHAOTIC: (2.5, 3.0)
        }
        
        lower, upper = boundaries[state]
        midpoint = (lower + upper) / 2.0
        range_width = upper - lower
        
        # Distance from midpoint (normalized)
        distance = abs(score - midpoint) / (range_width / 2.0)
        
        # Confidence decreases with distance from midpoint
        confidence = max(0.0, 1.0 - distance)
        
        return confidence
    
    def _identify_triggers(
        self,
        ph_rate: float,
        temp_rate: float,
        variance: float,
        volatility: float,
        spikes: float
    ) -> list[str]:
        """
        Identify which factors triggered the current state.
        """
        triggers = []
        
        if ph_rate >= 1.0:
            triggers.append("pH rate change")
        if temp_rate >= 1.0:
            triggers.append("temperature rate change")
        if variance >= 1.0:
            triggers.append("high variance")
        if volatility >= 1.0:
            triggers.append("high volatility")
        if spikes >= 2.0:
            triggers.append("sensor spike detected")
        
        return triggers
    
    def _calculate_severity(self, state: ReactionState, score: float) -> float:
        """
        Calculate severity level (0-1).
        """
        severity_map = {
            ReactionState.STABLE: 0.0,
            ReactionState.TRANSITIONAL: 0.33,
            ReactionState.CRITICAL: 0.67,
            ReactionState.CHAOTIC: 1.0
        }
        
        base_severity = severity_map[state]
        
        # Adjust based on score within state
        if state != ReactionState.STABLE:
            # Add some variation based on exact score
            severity = base_severity + (score % 1.0) * 0.1
            return min(severity, 1.0)
        
        return base_severity
    
    def _update_state_tracking(self, state: ReactionState) -> None:
        """Update state tracking for hysteresis and duration."""
        if self.previous_state == state:
            self.state_duration += 1
        else:
            self.state_duration = 1
            self.previous_state = state
        
        self.state_history.append(state)
        
        # Keep history manageable
        if len(self.state_history) > 100:
            self.state_history.pop(0)
    
    def get_state_duration(self) -> int:
        """Get duration of current state in samples."""
        return self.state_duration
    
    def get_previous_state(self) -> Optional[ReactionState]:
        """Get previous state."""
        return self.previous_state
    
    def reset(self) -> None:
        """Reset classifier state."""
        self.previous_state = None
        self.state_duration = 0
        self.state_history.clear()


def get_state_color(state: ReactionState) -> str:
    """Get color associated with state for visualization."""
    colors = {
        ReactionState.STABLE: "#00ff88",
        ReactionState.TRANSITIONAL: "#ffd93d",
        ReactionState.CRITICAL: "#ff6b6b",
        ReactionState.CHAOTIC: "#ff0066"
    }
    return colors.get(state, "#ffffff")


def get_state_description(state: ReactionState) -> str:
    """Get human-readable description of state."""
    descriptions = {
        ReactionState.STABLE: "Reaction is stable and within normal parameters.",
        ReactionState.TRANSITIONAL: "Reaction is undergoing transition or change.",
        ReactionState.CRITICAL: "Reaction has reached critical instability.",
        ReactionState.CHAOTIC: "Reaction is chaotic and unpredictable."
    }
    return descriptions.get(state, "Unknown state")
