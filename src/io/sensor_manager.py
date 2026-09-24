"""No hardware failure ever silently becomes simulation."""
from src.io.serial_reader import SerialReader, parse_sample
from src.io.simulator import ChemicalSimulator

class SensorManager:
    def __init__(self, mode='simulation', port='', scenario='Full demo'):
        if mode not in ('simulation','hardware'): raise ValueError('Unknown mode')
        self.mode = mode
        self.source = ChemicalSimulator(scenario) if mode == 'simulation' else SerialReader(port)

    def read(self):
        return parse_sample(self.source.tick()) if self.mode == 'simulation' else self.source.read()

    def close(self):
        if self.mode == 'hardware': self.source.close()
