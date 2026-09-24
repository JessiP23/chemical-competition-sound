"""One process-wide monitoring service, independent of UI refreshes."""
import atexit
import json
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from src.io.sensor_manager import SensorManager
from src.core.feature_extraction import FeatureExtractor
from src.core.classifier import StateClassifier, DetectionProfile
from src.core.mapping import compute_audio_params
from src.audio.tone_engine import ToneEngine

class Pipeline:
    def __init__(self, profile=None):
        self.profile = profile or DetectionProfile()
        self.reset()

    def reset(self):
        self.extractor = FeatureExtractor()
        self.classifier = StateClassifier(self.profile)

    def process(self, sample):
        if not sample['valid']:
            self.reset()
            return dict(sample=sample, state='fault', reason=sample['error'], features={}, audio={'state':'fault'})
        features = self.extractor.update(sample)
        classification = self.classifier.classify(features)
        return dict(sample=sample, **classification, features=features,
                    audio=compute_audio_params(features,classification['state']))

class Monitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.control = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.audio = ToneEngine()
        self.current = dict(state='stopped',reason='Choose a mode and press Start',sample={})
        self.history = deque(maxlen=600)
        self.log_path = None
        atexit.register(self.stop)

    @property
    def running(self): return bool(self.thread and self.thread.is_alive())

    def start(self, mode, port='', scenario='Full demo', audio=False, profile=None, calibration_id=''):
        with self.control:
            if self.running: raise RuntimeError('Stop the current run first')
            if mode == 'hardware' and not calibration_id.strip():
                raise ValueError('Enter your completed calibration record ID before hardware monitoring')
            self.stop_event.clear()
            self.history.clear()
            self.current = dict(state='unknown',reason='Connecting / collecting baseline',sample={},mode=mode)
            self.audio.update_params({'state':'unknown'})
            self.thread = threading.Thread(target=self._run,args=(mode,port,scenario,audio,profile,calibration_id),daemon=True)
            self.thread.start()

    def _publish(self, record, log):
        record['received_at'] = datetime.now(timezone.utc).isoformat()
        log.write(json.dumps(record,allow_nan=False)+'\n')
        log.flush()
        self.audio.update_params(record.get('audio',{'state':'fault'}))
        with self.lock:
            self.current = record
            self.history.append(record)

    def _run(self, mode, port, scenario, audio, profile, calibration_id):
        source = None
        pipeline = Pipeline(profile)
        try:
            directory = Path(__file__).resolve().parents[2]/'recordings'
            directory.mkdir(exist_ok=True)
            self.log_path = directory/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.jsonl')
            with self.log_path.open('x') as log:
                log.write(json.dumps(dict(type='session',mode=mode,scenario=scenario,profile=vars(pipeline.profile),calibration_id=calibration_id))+'\n')
                if audio: self.audio.start()
                try:
                    source = SensorManager(mode,port,scenario)
                    while not self.stop_event.is_set():
                        started = time.monotonic()
                        sample = source.read()
                        if sample is not None:
                            record = pipeline.process(sample)
                            record['mode'] = mode
                            self._publish(record,log)
                        if mode == 'simulation': self.stop_event.wait(max(0,0.5-(time.monotonic()-started)))
                except Exception as exc:
                    self._publish(dict(state='fault',reason=str(exc),sample={},mode=mode,audio={'state':'fault'}),log)
                    # Keep fault audible until explicitly stopped; reconnect via Stop/Start.
                    self.stop_event.wait()
        except Exception as exc:
            with self.lock: self.current = dict(state='fault',reason=str(exc),sample={},mode=mode)
        finally:
            if source:
                try: source.close()
                except Exception: pass
            self.audio.stop()

    def stop(self):
        with self.control:
            self.stop_event.set()
            if self.thread: self.thread.join(timeout=3)
            if self.running: return
            self.audio.stop()
            with self.lock:
                self.current = dict(state='stopped',reason='Monitoring stopped',sample={})

    def snapshot(self):
        with self.lock: return dict(self.current), list(self.history)
