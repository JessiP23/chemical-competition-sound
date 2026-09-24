"""Generate a reproducible demo or replay a recorded session, without audio hardware."""
import argparse
import json
import wave
from pathlib import Path
import numpy as np
from src.io.sensor_manager import SensorManager
from src.core.runtime import Pipeline
from src.core.classifier import DetectionProfile
from src.audio.tone_engine import ToneEngine
from src.config.settings import SAMPLE_RATE

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,help='Replay valid/invalid samples from a saved JSONL run')
    parser.add_argument('--output',type=Path,default=Path('recordings/demo'))
    args=parser.parse_args()
    profile=DetectionProfile()
    if args.replay:
        records=[json.loads(line) for line in args.replay.read_text().splitlines()]
        profile=DetectionProfile(**records[0]['profile'])
        samples=[r['sample'] for r in records[1:] if r.get('sample')]
    else:
        source=SensorManager()
        samples=[source.read() for _ in range(120)]
    pipeline,audio=Pipeline(profile),ToneEngine()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    wav_path=args.output.with_suffix('.wav')
    log_path=args.output.with_suffix('.jsonl')
    if args.replay and log_path.resolve()==args.replay.resolve():
        parser.error('Output must differ from input recording')
    states=set()
    with wave.open(str(wav_path),'wb') as wav, log_path.open('w') as log:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(SAMPLE_RATE)
        log.write(json.dumps(dict(type='session',mode='replay' if args.replay else 'simulation',profile=vars(profile)))+'\n')
        for i,sample in enumerate(samples):
            record=pipeline.process(sample)
            states.add(record['state'])
            log.write(json.dumps(record,allow_nan=False)+'\n')
            audio.update_params(record['audio'])
            # Preserve recorded intervals, cap gaps at 3s; transport-only faults
            # lack samples and are not replayed (use live fault tests for these).
            duration=samples[i+1]['timestamp']-sample['timestamp'] if i+1<len(samples) else 0.5
            frames=max(1,int(min(3,max(0.01,duration))*SAMPLE_RATE))
            while frames:
                count=min(1024,frames)
                chunk=audio.render(count)
                wav.writeframes((chunk*32767).astype('<i2').tobytes())
                frames-=count
    print('States:',', '.join(sorted(states)))
    print('Audio:',wav_path)
    print('Decisions:',log_path)

if __name__=='__main__': main()
