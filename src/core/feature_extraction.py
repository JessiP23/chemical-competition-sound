"""Physical rates over a time window, independent of sample frequency."""
from collections import deque
import numpy as np

class FeatureExtractor:
    def __init__(self):
        self.samples = deque(maxlen=200)

    def update(self, sample):
        t, ph, temp = sample['timestamp'], sample['ph'], sample['temperature']
        if self.samples and t <= self.samples[-1][0]:
            raise ValueError('Measurement time must increase')
        self.samples.append((t, ph, temp))
        while len(self.samples)>1 and self.samples[0][0] < t-3:
            self.samples.popleft()
        a = np.array(self.samples)
        elapsed = t-a[0,0]
        ph_rate = (ph-a[0,1])/elapsed if elapsed else 0.0
        temp_rate = (temp-a[0,2])/elapsed if elapsed else 0.0
        variance = float(np.var(a[:,1]))
        return dict(timestamp=t, ready=bool(elapsed>=2), ph_value=ph, temp_value=temp,
                    ph_norm=ph/14, temp_norm=float(np.clip((temp-15)/85,0,1)),
                    dpH_dt=float(ph_rate), dT_dt=float(temp_rate), rolling_variance=variance,
                    volatility=min(1.,abs(ph_rate)+abs(temp_rate)*0.1+variance),
                    trend=float(np.clip(ph_rate,-1,1)), luminance=0.5)
