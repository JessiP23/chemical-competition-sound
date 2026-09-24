"""Continuous phase synthesis; device errors are visible to the controller."""
import threading
import numpy as np
from src.config.settings import SAMPLE_RATE, BUFFER_SIZE

class ToneEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.error = ''
        self.params = dict(fundamental_hz=528., rhythm_bps=1., noise_mix=0., state='unknown')
        self.phase = 0.
        self.beat = 0.
        self.freq = 528.
        self.gain = 0.
        self.waveform = np.zeros(BUFFER_SIZE)
        self.rng = np.random.default_rng(1)

    def update_params(self, params):
        with self._lock: self.params = dict(params)

    def render(self, frames=BUFFER_SIZE):
        with self._lock: p = dict(self.params)
        state = p.get('state','unknown')
        target = 220. if state == 'fault' else p.get('fundamental_hz',528.)
        frequencies = np.linspace(self.freq, target, frames)
        self.freq = target
        phases = self.phase + np.cumsum(2*np.pi*frequencies/SAMPLE_RATE)
        self.phase = float(phases[-1] % (2*np.pi))
        bps = 2. if state == 'fault' else float(np.clip(p.get('rhythm_bps',1.),0.5,8))
        beats = self.beat + np.arange(frames)*bps/SAMPLE_RATE
        self.beat = float((self.beat+frames*bps/SAMPLE_RATE)%1)
        pulse = 0.35+0.65*np.exp(-8*(beats%1))
        tone = np.sin(phases)*pulse
        if state == 'critical': tone += 0.25*np.sin(2*phases)
        if state == 'fault': tone *= (beats%1 < 0.35)
        noise = min(0.15, p.get('noise_mix',0.)*0.15)
        tone += self.rng.normal(0,noise,frames)
        target_gain = 0. if state == 'unknown' else 0.2
        tone *= np.linspace(self.gain,target_gain,frames)
        self.gain = target_gain
        tone = np.clip(tone,-0.5,0.5).astype(np.float32)
        with self._lock: self.waveform = tone.copy()
        return np.column_stack([tone,tone])

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self.error = ''
        self._stop.clear()
        self._thread = threading.Thread(target=self._run,daemon=True)
        self._thread.start()

    def _run(self):
        try:
            import sounddevice as sd
            with sd.OutputStream(samplerate=SAMPLE_RATE,channels=2,dtype='float32',blocksize=BUFFER_SIZE) as stream:
                while not self._stop.is_set():
                    if stream.write(self.render()): self.error = 'Audio underflow: output could not keep up'
        except Exception as exc:
            self.error = str(exc)

    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=2)

    def get_waveform(self):
        with self._lock: return self.waveform.copy()
