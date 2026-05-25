"""
Serial communication with Arduino for sensor data acquisition.

Handles reading sensor data from Arduino via serial connection.
"""

import serial
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from src.config.settings import SerialConfig


@dataclass
class SensorReading:
    """Container for sensor reading from Arduino."""
    ph: float
    temperature: float
    color_r: Optional[float] = None
    color_g: Optional[float] = None
    color_b: Optional[float] = None
    timestamp: float = 0.0


class SerialReader:
    """
    Reads sensor data from Arduino via serial connection.
    
    Expected serial format:
    pH,temperature,color_r,color_g,color_b
    
    Example:
    7.2,25.5,100,150,200
    """
    
    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        config: Optional[SerialConfig] = None
    ):
        """
        Initialize serial reader.
        
        Args:
            port: Serial port path (e.g., /dev/ttyUSB0, COM3)
            config: Serial configuration
        """
        self.port = port
        self.config = config or SerialConfig()
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Establish serial connection to Arduino.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.config.BAUD_RATE,
                timeout=self.config.TIMEOUT
            )
            # Wait for connection to stabilize
            time.sleep(2)
            self.connected = True
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to serial port {self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Close serial connection."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.connected = False
    
    def read(self) -> Optional[SensorReading]:
        """
        Read sensor data from Arduino.
        
        Returns:
            SensorReading if successful, None otherwise
        """
        if not self.connected or not self.serial_connection:
            return None
        
        try:
            # Read line from serial
            line = self.serial_connection.readline().decode('utf-8').strip()
            
            if not line:
                return None
            
            # Parse comma-separated values
            values = line.split(self.config.DATA_DELIMITER)
            
            if len(values) < 2:
                return None
            
            # Extract pH and temperature (required)
            ph = float(values[0])
            temperature = float(values[1])
            
            # Extract color values (optional)
            color_r = None
            color_g = None
            color_b = None
            
            if len(values) >= 5:
                try:
                    color_r = float(values[2])
                    color_g = float(values[3])
                    color_b = float(values[4])
                except (ValueError, IndexError):
                    pass
            
            timestamp = time.time()
            
            return SensorReading(
                ph=ph,
                temperature=temperature,
                color_r=color_r,
                color_g=color_g,
                color_b=color_b,
                timestamp=timestamp
            )
        
        except (ValueError, IndexError, serial.SerialException) as e:
            print(f"Error reading serial data: {e}")
            return None
    
    def read_raw(self) -> Optional[str]:
        """
        Read raw string from serial.
        
        Returns:
            Raw string if successful, None otherwise
        """
        if not self.connected or not self.serial_connection:
            return None
        
        try:
            line = self.serial_connection.readline().decode('utf-8').strip()
            return line if line else None
        except serial.SerialException as e:
            print(f"Error reading raw serial data: {e}")
            return None
    
    def write(self, data: str) -> bool:
        """
        Write data to Arduino.
        
        Args:
            data: String to write
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected or not self.serial_connection:
            return False
        
        try:
            self.serial_connection.write(data.encode('utf-8'))
            return True
        except serial.SerialException as e:
            print(f"Error writing to serial: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.connected and self.serial_connection and self.serial_connection.is_open
    
    def flush(self) -> None:
        """Flush serial input and output buffers."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()


def list_available_ports() -> list[str]:
    """
    List available serial ports.
    
    Returns:
        List of available port names
    """
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def auto_detect_port() -> Optional[str]:
    """
    Auto-detect Arduino serial port.
    
    Returns:
        Port name if Arduino detected, None otherwise
    """
    ports = list_available_ports()
    
    for port in ports:
        try:
            # Try to open each port and check if it's an Arduino
            ser = serial.Serial(port, baudrate=115200, timeout=1)
            time.sleep(2)
            
            # Try to read a line
            line = ser.readline().decode('utf-8').strip()
            ser.close()
            
            # If we got data, assume it's our Arduino
            if line:
                return port
        
        except (serial.SerialException, UnicodeDecodeError):
            continue
    
    return None
