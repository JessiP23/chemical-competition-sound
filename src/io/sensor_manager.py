"""
Sensor manager for unified input source abstraction.

Provides a unified interface for both simulation and hardware modes,
allowing seamless switching between simulated and real sensor data.
"""

from typing import Optional
from abc import ABC, abstractmethod

from src.io.simulator import ChemicalSimulator, SensorReading as SimReading
from src.io.serial_reader import SerialReader, SensorReading as SerialReading
from src.config.settings import SystemMode


class SensorSource(ABC):
    """Abstract base class for sensor data sources."""
    
    @abstractmethod
    def read(self) -> Optional['SensorReading']:
        """Read sensor data."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if source is connected/active."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from source."""
        pass


class SimulatorSource(SensorSource):
    """Simulator-based sensor source."""
    
    def __init__(self, simulator: ChemicalSimulator):
        self.simulator = simulator
    
    def read(self) -> Optional['SensorReading']:
        """Read simulated sensor data."""
        reading = self.simulator.update()
        return SensorReading(
            ph=reading.ph,
            temperature=reading.temperature,
            color_r=reading.color_r,
            color_g=reading.color_g,
            color_b=reading.color_b,
            timestamp=reading.timestamp
        )
    
    def is_connected(self) -> bool:
        """Simulator is always connected."""
        return True
    
    def disconnect(self) -> None:
        """No-op for simulator."""
        pass
    
    def get_simulator(self) -> ChemicalSimulator:
        """Get underlying simulator instance."""
        return self.simulator


class HardwareSource(SensorSource):
    """Hardware-based sensor source via serial."""
    
    def __init__(self, serial_reader: SerialReader):
        self.serial_reader = serial_reader
    
    def read(self) -> Optional['SensorReading']:
        """Read hardware sensor data."""
        reading = self.serial_reader.read()
        if reading:
            return SensorReading(
                ph=reading.ph,
                temperature=reading.temperature,
                color_r=reading.color_r,
                color_g=reading.color_g,
                color_b=reading.color_b,
                timestamp=reading.timestamp
            )
        return None
    
    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.serial_reader.is_connected()
    
    def disconnect(self) -> None:
        """Disconnect from serial."""
        self.serial_reader.disconnect()
    
    def get_serial_reader(self) -> SerialReader:
        """Get underlying serial reader instance."""
        return self.serial_reader


class SensorManager:
    """
    Unified sensor data manager.
    
    Provides a single interface for both simulation and hardware modes,
    allowing runtime switching between data sources.
    """
    
    def __init__(self):
        self.current_source: Optional[SensorSource] = None
        self.mode: Optional[SystemMode] = None
        self.simulator_source: Optional[SimulatorSource] = None
        self.hardware_source: Optional[HardwareSource] = None
    
    def set_simulation_mode(self, simulator: ChemicalSimulator) -> None:
        """
        Switch to simulation mode.
        
        Args:
            simulator: ChemicalSimulator instance
        """
        # Disconnect current source if hardware
        if self.current_source and self.mode == SystemMode.HARDWARE:
            self.current_source.disconnect()
        
        self.simulator_source = SimulatorSource(simulator)
        self.current_source = self.simulator_source
        self.mode = SystemMode.SIMULATION
    
    def set_hardware_mode(self, serial_reader: SerialReader) -> bool:
        """
        Switch to hardware mode.
        
        Args:
            serial_reader: SerialReader instance
        
        Returns:
            True if successful, False otherwise
        """
        # Try to connect
        if not serial_reader.connect():
            return False
        
        # Disconnect current source if hardware
        if self.current_source and self.mode == SystemMode.HARDWARE:
            self.current_source.disconnect()
        
        self.hardware_source = HardwareSource(serial_reader)
        self.current_source = self.hardware_source
        self.mode = SystemMode.HARDWARE
        return True
    
    def read(self) -> Optional['SensorReading']:
        """
        Read sensor data from current source.
        
        Returns:
            SensorReading if successful, None otherwise
        """
        if self.current_source is None:
            return None
        
        return self.current_source.read()
    
    def is_connected(self) -> bool:
        """Check if current source is connected."""
        if self.current_source is None:
            return False
        return self.current_source.is_connected()
    
    def get_mode(self) -> Optional[SystemMode]:
        """Get current mode."""
        return self.mode
    
    def disconnect(self) -> None:
        """Disconnect from current source."""
        if self.current_source:
            self.current_source.disconnect()
    
    def get_simulator(self) -> Optional[ChemicalSimulator]:
        """Get simulator instance if in simulation mode."""
        if self.mode == SystemMode.SIMULATION and self.simulator_source:
            return self.simulator_source.get_simulator()
        return None
    
    def get_serial_reader(self) -> Optional[SerialReader]:
        """Get serial reader instance if in hardware mode."""
        if self.mode == SystemMode.HARDWARE and self.hardware_source:
            return self.hardware_source.get_serial_reader()
        return None


# Unified SensorReading class
class SensorReading:
    """Unified sensor reading container."""
    
    def __init__(
        self,
        ph: float,
        temperature: float,
        color_r: Optional[float] = None,
        color_g: Optional[float] = None,
        color_b: Optional[float] = None,
        timestamp: float = 0.0
    ):
        self.ph = ph
        self.temperature = temperature
        self.color_r = color_r
        self.color_g = color_g
        self.color_b = color_b
        self.timestamp = timestamp
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ph": self.ph,
            "temperature": self.temperature,
            "color_r": self.color_r,
            "color_g": self.color_g,
            "color_b": self.color_b,
            "timestamp": self.timestamp
        }
