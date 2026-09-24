"""Deterministic scenarios, encoded through the actual serial protocol."""
import math

SCENARIOS = ['Full demo', 'Stable', 'pH transition', 'Temperature rise', 'Critical pH', 'Sensor fault']

class ChemicalSimulator:
    def __init__(self, scenario='Full demo'):
        self.scenario = scenario
        self.sequence = 0

    def tick(self):
        t = self.sequence * 0.5
        phase = self.scenario
        if phase == 'Full demo':
            phase = ['Stable','pH transition','Temperature rise','Critical pH','Sensor fault','Stable'][int(t//10)%6]
        local = t % 10
        ph, temp, status = 7 + 0.005*math.sin(t), 25.0, 'OK'
        if phase == 'pH transition': ph = 7-local*0.15
        if phase == 'Temperature rise': temp = 25+local*1.5
        if phase == 'Critical pH': ph = 3.0
        if phase == 'Sensor fault': status = 'TEMP_FAULT'
        line = f'CHEM1,{self.sequence},{int(t*1000)},{ph:.3f},{temp:.3f},307,{status}'
        self.sequence += 1
        return line
