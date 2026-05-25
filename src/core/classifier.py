"""
classifier.py

State machine with hysteresis to prevent rapid oscillation between states.
States: stable → transitional → critical → chaotic (and back)

Hysteresis: Must exceed threshold for N consecutive samples before transition.
"""

from src.config.settings import THRESHOLDS


class StateClassifier:
    STATES = ["stable", "transitional", "critical", "chaotic"]

    def __init__(self):
        self.current_state = "stable"
        self.consecutive_counts = {s: 0 for s in self.STATES}
        self.HYSTERESIS = 3  # consecutive samples needed to change state
        self.history = []

    def classify(self, features: dict) -> dict:
        var = features["rolling_variance"]
        rate = abs(features["dpH_dt"])

        # Determine candidate state
        if var >= THRESHOLDS["chaotic"]["variance"] or rate >= THRESHOLDS["chaotic"]["rate"]:
            candidate = "chaotic"
        elif var >= THRESHOLDS["critical"]["variance"] or rate >= THRESHOLDS["critical"]["rate"]:
            candidate = "critical"
        elif var >= THRESHOLDS["transitional"]["variance"] or rate >= THRESHOLDS["transitional"]["rate"]:
            candidate = "transitional"
        else:
            candidate = "stable"

        # Hysteresis
        for s in self.STATES:
            self.consecutive_counts[s] = self.consecutive_counts[s] + 1 if s == candidate else 0

        if self.consecutive_counts[candidate] >= self.HYSTERESIS:
            prev = self.current_state
            self.current_state = candidate
            changed = prev != candidate
        else:
            changed = False

        result = {
            "state": self.current_state,
            "changed": changed,
            "candidate": candidate,
            "instability_score": min(1.0, features["volatility"]),
        }

        self.history.append(result)
        return result
