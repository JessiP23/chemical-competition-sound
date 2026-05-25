"""
sensor_manager.py

The critical abstraction layer that lets you swap:
  Simulator ↔ Hardware Arduino

Without changing anything else in the system.

Usage:
  sensor_manager = SensorManager(mode="simulation")  # or "hardware"
  data = sensor_manager.read()  # returns same dict format either way
"""

import time
from src.config.settings import MODE, SERIAL_PORT, BAUD_RATE


class SensorManager:
    def __init__(self, mode: str = None):
        self.mode = mode or MODE
        self._sim = None
        self._serial = None

        if self.mode == "simulation":
            from src.io.simulator import ChemicalSimulator
            self._sim = ChemicalSimulator()
        elif self.mode == "hardware":
            self._init_hardware()

    def _init_hardware(self):
        try:
            import serial
            self._serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)  # Arduino reset
            print(f"[HW] Connected to {SERIAL_PORT}")
        except Exception as e:
            print(f"[HW] ERROR: {e}. Falling back to simulation.")
            self.mode = "simulation"
            from src.io.simulator import ChemicalSimulator
            self._sim = ChemicalSimulator()

    def read(self) -> dict:
        """Read one sensor sample. Returns standardized dict."""
        if self.mode == "simulation":
            return self._sim.tick()
        else:
            return self._read_hardware()

    def _read_hardware(self) -> dict:
        """Parse Arduino serial line: pH,temperature,R,G,B"""
        try:
            line = self._serial.readline().decode('utf-8').strip()
            parts = line.split(',')
            return {
                "timestamp": time.time(),
                "ph": float(parts[0]),
                "temperature": float(parts[1]),
                "color_r": int(parts[2]) if len(parts) > 2 else 128,
                "color_g": int(parts[3]) if len(parts) > 3 else 128,
                "color_b": int(parts[4]) if len(parts) > 4 else 128,
                "phase": -1,
                "phase_name": "Hardware",
            }
        except Exception as e:
            print(f"[HW] Parse error: {e}")
            return {"timestamp": time.time(), "ph": 7.0, "temperature": 25.0,
                    "color_r": 128, "color_g": 128, "color_b": 128, "phase": -1, "phase_name": "Error"}

    def inject_disturbance(self, magnitude=0.5):
        """Only available in simulation mode."""
        if self.mode == "simulation" and self._sim:
            self._sim.inject_disturbance(magnitude)

    def reset(self):
        if self.mode == "simulation" and self._sim:
            self._sim.reset()
