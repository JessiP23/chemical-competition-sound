import json
import math
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from src.io.serial_reader import parse_sample, SerialReader
from src.io.sensor_manager import SensorManager
from src.core.runtime import Pipeline, Monitor
from src.core.feature_extraction import FeatureExtractor
from src.core.classifier import DetectionProfile
from src.audio.tone_engine import ToneEngine

class PipelineTests(unittest.TestCase):
    def test_full_demo_wire_to_sound_and_recovery(self):
        source, pipeline, audio = SensorManager(), Pipeline(), ToneEngine()
        states=[]
        for _ in range(120):
            record=pipeline.process(source.read())
            states.append(record['state'])
            audio.update_params(record['audio'])
            chunk=audio.render()
            self.assertTrue(np.isfinite(chunk).all())
            self.assertLessEqual(np.max(np.abs(chunk)),0.5)
        self.assertTrue({'stable','transitional','critical','fault'}.issubset(states))
        self.assertEqual(states[-1],'stable')

    def test_absolute_limits_do_not_require_motion(self):
        for ph,temp in [(3,25),(7,45)]:
            record=Pipeline().process(parse_sample(f'CHEM1,0,0,{ph},{temp},300,OK'))
            self.assertEqual(record['state'],'critical')

    def test_rates_use_elapsed_time(self):
        for dt in [0.25,0.5,1]:
            extractor=FeatureExtractor()
            for i in range(int(3/dt)+1):
                t=i*dt
                f=extractor.update(dict(timestamp=t,ph=7+0.1*t,temperature=25+0.5*t))
            self.assertAlmostEqual(f['dpH_dt'],0.1)
            self.assertAlmostEqual(f['dT_dt'],0.5)

    def test_bad_records(self):
        for line in ['7,25','CHEM1,0,0,nan,25,300,OK','CHEM1,0,0,7,25,2048,OK']:
            with self.assertRaises(ValueError): parse_sample(line)
        self.assertFalse(parse_sample('CHEM1,0,0,7,-127,300,TEMP_FAULT')['valid'])

    def test_fault_discards_previous_baseline(self):
        source,pipeline=SensorManager(scenario='Stable'),Pipeline()
        for _ in range(10): record=pipeline.process(source.read())
        self.assertEqual(record['state'],'stable')
        self.assertEqual(pipeline.process(dict(valid=False,error='fault'))['state'],'fault')
        self.assertEqual(pipeline.process(source.read())['state'],'unknown')

    def test_partial_frames_and_repeated_samples(self):
        class Connection:
            def __init__(self,*a,**kw): self.chunks=iter([b'CHEM1,0,',b'0,7,25,300,OK\n',b'CHEM1,0,0,7,25,300,OK\n'])
            def read_until(self,*a,**kw): return next(self.chunks)
            def close(self): pass
        with patch('serial.Serial',Connection):
            reader=SerialReader('fake')
            self.assertIsNone(reader.read())
            self.assertEqual(reader.read()['ph'],7)
            with self.assertRaises(ValueError): reader.read()

    def test_no_hardware_fallback(self):
        with patch('serial.Serial',side_effect=OSError('unplugged')):
            with self.assertRaises(OSError): SensorManager('hardware','missing')

    def test_audio_continuity(self):
        a,b=ToneEngine(),ToneEngine()
        params=dict(state='stable',fundamental_hz=528.,rhythm_bps=2.,noise_mix=0.)
        for engine in (a,b):
            engine.update_params(params); engine.gain=0.2
        split=np.concatenate([a.render(1024),a.render(1024)])
        whole=b.render(2048)
        np.testing.assert_allclose(split,whole,atol=1e-6)

    def test_invalid_profile(self):
        with self.assertRaises(ValueError): DetectionProfile(ph_low=11,ph_high=4)

    def test_runtime_start_stop_recording(self):
        monitor=Monitor()
        try:
            monitor.start('simulation',scenario='Stable')
            deadline=time.monotonic()+3
            while not monitor.snapshot()[1] and time.monotonic()<deadline: time.sleep(0.02)
            self.assertTrue(monitor.snapshot()[1])
            monitor.stop()
            self.assertFalse(monitor.running)
            rows=[json.loads(line) for line in monitor.log_path.read_text().splitlines()]
            self.assertEqual(rows[0]['mode'],'simulation')
            self.assertEqual(rows[1]['sample']['ph'],7)
        finally: monitor.stop()

if __name__=='__main__': unittest.main()
