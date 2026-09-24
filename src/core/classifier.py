"""Demo thresholds are configurable, not validated chemical safety limits."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DetectionProfile:
    ph_low: float = 4.0
    ph_high: float = 10.0
    temp_high: float = 40.0
    ph_rate: float = 0.08
    temp_rate: float = 0.3
    persistence: float = 1.0

    def __post_init__(self):
        import math
        if not all(math.isfinite(v) for v in vars(self).values()):
            raise ValueError('Thresholds must be finite')
        if not 0 <= self.ph_low < self.ph_high <= 14 or not 5 <= self.temp_high <= 60:
            raise ValueError('Thresholds must fit the probe range')
        if min(self.ph_rate,self.temp_rate,self.persistence) <= 0:
            raise ValueError('Rates and persistence must be positive')

class StateClassifier:
    def __init__(self, profile=None):
        self.profile = profile or DetectionProfile()
        self.current_state = 'unknown'
        self.candidate = None
        self.since = 0

    def classify(self, f):
        p = self.profile
        reasons = []
        # Absolute limits bypass warmup and smoothing.
        if f['ph_value'] <= p.ph_low or f['ph_value'] >= p.ph_high: reasons.append('pH outside demo limits')
        if f['temp_value'] >= p.temp_high: reasons.append('Temperature above demo limit')
        if reasons: candidate = 'critical'
        elif not f['ready']: candidate, reasons = 'unknown', ['Collecting baseline (2 seconds)']
        else:
            if abs(f['dpH_dt']) >= p.ph_rate: reasons.append('pH changing')
            if abs(f['dT_dt']) >= p.temp_rate: reasons.append('Temperature changing')
            candidate = 'transitional' if reasons else 'stable'
        now = f['timestamp']
        if candidate != self.candidate:
            self.candidate, self.since = candidate, now
        previous = self.current_state
        if candidate in ('critical','unknown') or now-self.since >= p.persistence:
            self.current_state = candidate
        pending = candidate != self.current_state
        return dict(state=self.current_state, changed=previous != self.current_state,
                    reason=('Confirming recovery/change: ' if pending else '') + (', '.join(reasons) or 'Within demo limits; low change'),
                    candidate=candidate)
