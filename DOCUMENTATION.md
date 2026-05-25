# Chemical-to-Audio Intelligent Monitoring System
## Comprehensive Technical Documentation

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Hardware Setup](#hardware-setup)
3. [Wiring Diagram](#wiring-diagram)
4. [Sensor Calibration](#sensor-calibration)
5. [Software Installation](#software-installation)
6. [Configuration](#configuration)
7. [Demo Plan](#demo-plan)
8. [Troubleshooting](#troubleshooting)
9. [Research Foundation](#research-foundation)

---

## System Architecture

### Overview

The Chemical-to-Audio Intelligent Monitoring System transforms chemical reaction behavior into real-time sound and visual feedback through a multi-stage pipeline:

```
Chemical Reaction
    ↓
Sensor Acquisition (Arduino)
    ↓
Serial Communication
    ↓
Signal Processing (Python)
    ↓
Feature Extraction
    ↓
State Classification
    ↓
Parameter Mapping
    ↓
Sonification Engine
    ↓
Audio Output + Voice Feedback
    ↓
Visual Dashboard (Streamlit)
```

### Software Architecture

```
chemical_audio_project/
├── app.py                          # Main entry point
├── requirements.txt                # Python dependencies
│
├── src/
│   ├── core/
│   │   ├── classifier.py           # State classification logic
│   │   ├── mapping.py              # Sensor-to-audio parameter mapping
│   │   ├── signal_tools.py         # Filtering and signal processing
│   │   └── feature_extraction.py   # Feature extraction from sensors
│   │
│   ├── io/
│   │   ├── simulator.py            # Chemical reaction simulator
│   │   ├── serial_reader.py        # Arduino serial communication
│   │   └── sensor_manager.py       # Unified input source abstraction
│   │
│   ├── audio/
│   │   ├── tone_engine.py          # Real-time audio synthesis
│   │   ├── voice_engine.py        # Text-to-speech alerts
│   │   └── synthesis.py            # Advanced synthesis techniques
│   │
│   ├── ui/
│   │   ├── dashboard.py            # Main Streamlit dashboard
│   │   ├── charts.py               # Real-time chart generation
│   │   └── state_panels.py         # Status indicators
│   │
│   └── config/
│       └── settings.py             # Central configuration
│
└── arduino/
    └── sensor_stream.ino          # Arduino firmware
```

### Data Flow

1. **Sensor Layer**: Arduino reads pH, temperature, and optional color sensors at 10Hz
2. **Communication Layer**: Serial data transmitted at 115200 baud
3. **Processing Layer**: Python applies filtering, smoothing, and feature extraction
4. **Classification Layer**: Multi-factor analysis determines reaction state
5. **Mapping Layer**: Sensor features mapped to audio synthesis parameters
6. **Output Layer**: Real-time audio, voice alerts, and visual dashboard

---

## Hardware Setup

### Required Components

#### 1. Microcontroller
- **Arduino Uno** (recommended)
- Alternative: Arduino Mega (for I2C color sensor support)

#### 2. pH Sensor
- **DFRobot Gravity Analog pH Sensor Kit** (recommended)
- Includes: pH probe, BNC connector, analog pH meter
- Range: 0-14 pH
- Accuracy: ±0.1 pH

#### 3. Temperature Sensor
- **DS18B20 Waterproof Digital Temperature Sensor**
- Range: -55°C to +125°C
- Accuracy: ±0.5°C
- Protocol: 1-Wire digital

#### 4. Optional Color Sensor
- **TCS34725 RGB Color Sensor**
- I2C communication
- Requires Arduino Mega for dedicated I2C pins

#### 5. Main Processing Unit
- Laptop or Raspberry Pi 4+
- Minimum: 4GB RAM, dual-core CPU
- Recommended: 8GB RAM, quad-core CPU

---

## Wiring Diagram

### Arduino Uno Wiring

```
Arduino Uno              pH Sensor              Temperature Sensor
┌─────────────┐         ┌──────────┐          ┌──────────────┐
│             │         │          │          │              │
│         A0  ├─────────│ Signal   │          │              │
│             │         │          │          │              │
│         GND ├─────────│ GND      │          │              │
│             │         │          │          │              │
│        5V   ├─────────│ VCC      │          │              │
│             │         └──────────┘          │              │
│             │                                │              │
│         D2  ├───────────────────────────────│ Data         │
│             │                                │              │
│         GND ├───────────────────────────────│ GND          │
│             │                                │              │
│        5V   ├───────────────────────────────│ VCC          │
│             │                                │              │
│         GND ├───────────────────────────────│ (4.7kΩ pullup)│
│             │                                │   to VCC     │
└─────────────┘                                └──────────────┘

USB (Serial) → Computer
```

### Pin Assignments

| Arduino Pin | Component        | Connection Type |
|-------------|------------------|-----------------|
| A0          | pH Sensor Signal | Analog Input    |
| D2          | DS18B20 Data     | Digital 1-Wire  |
| GND         | pH Sensor GND    | Ground          |
| GND         | DS18B20 GND      | Ground          |
| 5V          | pH Sensor VCC    | Power           |
| 5V          | DS18B20 VCC      | Power           |

### DS18B20 Pull-up Resistor

**Critical**: The DS18B20 requires a 4.7kΩ pull-up resistor between the Data pin and VCC.

```
D2 ─────┬────── DS18B20 Data
        │
       4.7kΩ
        │
5V ─────┴
```

---

## Sensor Calibration

### pH Sensor Calibration

#### Required Materials
- pH 4.0 buffer solution
- pH 7.0 buffer solution
- pH 10.0 buffer solution (optional)

#### Calibration Procedure

1. **Initial Setup**
   - Connect pH sensor to Arduino
   - Upload sensor_stream.ino firmware
   - Open serial monitor (115200 baud)

2. **Calibrate pH 7.0 (Neutral)**
   - Rinse pH probe with distilled water
   - Immerse probe in pH 7.0 buffer
   - Wait 2 minutes for stabilization
   - Note the serial output value
   - Calculate offset: `offset = 7.0 - measured_value`
   - Update `PH_OFFSET` in Arduino code

3. **Calibrate pH 4.0 (Acidic)**
   - Rinse probe with distilled water
   - Immerse probe in pH 4.0 buffer
   - Wait 2 minutes for stabilization
   - Verify reading is within ±0.2 of 4.0
   - Adjust slope if necessary in Arduino code

4. **Calibrate pH 10.0 (Basic) - Optional**
   - Repeat process with pH 10.0 buffer
   - Verify linearity across range

5. **Save Calibration**
   - Update `PH_OFFSET` constant in sensor_stream.ino
   - Re-upload firmware to Arduino
   - Test with known solutions

#### pH Sensor Maintenance
- Always store probe in pH 4.0 or 7.0 storage solution
- Never let probe dry out completely
- Rinse with distilled water between measurements
- Recalibrate monthly for best accuracy

### Temperature Sensor Calibration

The DS18B20 is factory-calibrated and typically requires no additional calibration. However, you can verify accuracy:

1. **Ice Point Test**
   - Immerse sensor in ice-water mixture (0°C)
   - Verify reading is 0.0 ± 0.5°C

2. **Room Temperature Test**
   - Compare with reference thermometer
   - Note any systematic offset

3. **Software Adjustment**
   - If offset is consistent, add correction in Python code
   - Modify `src/io/serial_reader.py` if needed

---

## Software Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Arduino IDE (for hardware mode)
- Virtual audio device (for audio output on some systems)

### Python Environment Setup

#### 1. Create Virtual Environment

```bash
cd /Users/jessipavia/chemical
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Additional System Dependencies

**macOS:**
```bash
brew install portaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-pyaudio
sudo apt-get install espeak  # For voice engine
```

**Windows:**
- Download and install PortAudio from http://www.portaudio.com/
- Install Microsoft Visual C++ Redistributable

### Arduino Setup

#### 1. Install Arduino IDE
- Download from https://www.arduino.cc/en/software
- Install and launch Arduino IDE

#### 2. Install Required Libraries

In Arduino IDE:
- Go to Sketch → Include Library → Manage Libraries
- Install: "OneWire" by Paul Stoffregen
- Install: "DallasTemperature" by Miles Burton

#### 3. Upload Firmware

1. Open `arduino/sensor_stream.ino` in Arduino IDE
2. Select your board: Tools → Board → Arduino Uno
3. Select your port: Tools → Port → (your Arduino port)
4. Click Upload button

---

## Configuration

### System Mode Selection

The system supports two modes, configurable via the Streamlit dashboard:

#### Simulation Mode
- No hardware required
- Uses virtual chemical reaction simulator
- Ideal for testing and demonstrations
- Select "Simulation" in sidebar

#### Hardware Mode
- Requires Arduino with sensors
- Real-time sensor data acquisition
- Select "Hardware" in sidebar
- Configure serial port (e.g., /dev/ttyUSB0 or COM3)

### Audio Configuration

Audio parameters are configured in `src/config/settings.py`:

```python
class AudioParameters:
    SAMPLE_RATE: int = 44100
    BLOCK_SIZE: int = 1024
    CHANNELS: int = 1
    PITCH_MIN: float = 110.0  # A2
    PITCH_MAX: float = 880.0  # A5
```

### Classification Thresholds

Adjust state classification sensitivity in `src/config/settings.py`:

```python
class ClassificationThresholds:
    PH_RATE_STABLE: float = 0.01
    PH_RATE_CRITICAL: float = 0.15
    VARIANCE_CRITICAL: float = 0.15
```

### Sonification Mappings

Customize audio mappings in `src/config/settings.py`:

```python
class SonificationMappings:
    PH_TO_PITCH: Tuple[float, float] = (110.0, 880.0)
    TEMP_TO_RHYTHM: Tuple[float, float] = (0.5, 8.0)
```

---

## Demo Plan

### Competition Demo Script

#### Phase 1: Introduction (30 seconds)
1. Start system in Simulation Mode
2. Select "Stable Reaction" scenario
3. Explain system architecture briefly
4. Show dashboard overview

#### Phase 2: Stable State (45 seconds)
1. Click "Start/Stop" to begin monitoring
2. Observe calm, harmonic audio
3. Show real-time charts (pH, temperature)
4. Explain state classification (Stable)
5. Highlight sensor cards and values

#### Phase 3: Acid-Base Titration (60 seconds)
1. Switch to "Acid-Base Titration" scenario
2. Observe pH gradually increasing
3. Audio pitch rises accordingly
4. State transitions to Transitional
5. Voice engine announces: "Reaction transitioning"
6. Show volatility graph increasing

#### Phase 4: Critical Instability (45 seconds)
1. Manually trigger disturbance (if available)
2. Or switch to "Unstable Oscillation" scenario
3. Observe rapid pH swings
4. Audio becomes tense and dissonant
5. State transitions to Critical
6. Voice engine: "Warning. Critical instability detected"
7. Show severity meter at high level

#### Phase 5: Stabilization (30 seconds)
1. Return to "Stable Reaction" scenario
2. Observe system returning to stable state
3. Audio calms down
4. State returns to Stable
5. Voice engine: "Reaction stable"

#### Phase 6: Hardware Demonstration (Optional, 60 seconds)
1. Switch to Hardware Mode
2. Connect to Arduino
3. Show real sensor data
4. Demonstrate with actual chemical reaction
5. Explain calibration process

### Key Talking Points

**Architecture:**
- "The system uses a modular pipeline from sensors to sound"
- "Signal processing removes noise before classification"
- "State classification uses multi-factor analysis"

**Sonification:**
- "pH maps to pitch - acidic is low, basic is high"
- "Temperature controls rhythm density"
- "Instability creates dissonance and distortion"
- "Based on research in auditory display and psychoacoustics"

**Applications:**
- "Real-time monitoring of chemical processes"
- "Anomaly detection through auditory cues"
- "Accessible chemistry education"
- "Industrial process control"

---

## Troubleshooting

### Common Issues

#### Arduino Not Detected

**Symptoms:** "Failed to connect to serial port" error

**Solutions:**
1. Check USB cable (use data cable, not charge-only)
2. Verify Arduino is powered (LED on)
3. Check correct port in Arduino IDE
4. Try different USB port
5. Install Arduino drivers (CH340 for clone boards)

#### No Serial Data

**Symptoms:** Connected but no sensor readings

**Solutions:**
1. Verify firmware uploaded successfully
2. Check baud rate matches (115200)
3. Open Arduino Serial Monitor to test
4. Check sensor wiring connections
5. Verify pH probe is connected properly

#### Audio Not Playing

**Symptoms:** No sound output

**Solutions:**
1. Check system audio output device
2. Verify "Enable Audio" checkbox is checked
3. Install PortAudio system dependency
4. Check audio device permissions
5. Try different sample rate in settings

#### Voice Engine Not Working

**Symptoms:** No spoken alerts

**Solutions:**
1. Verify "Enable Voice" checkbox is checked
2. Install espeak (Linux) or ensure TTS available
3. Check voice engine initialization logs
4. Adjust cooldown time in settings

#### High CPU Usage

**Symptoms:** System sluggish, high CPU

**Solutions:**
1. Increase refresh rate in sidebar
2. Reduce chart history length in settings
3. Disable audio visualizer if not needed
4. Use lower sample rate (22050 Hz)

#### pH Readings Inaccurate

**Symptoms:** pH values don't match known solutions

**Solutions:**
1. Recalibrate pH sensor
2. Check pH probe condition (replace if old)
3. Verify probe is properly immersed
4. Allow 2 minutes for stabilization
5. Check Arduino analog reference voltage

---

## Research Foundation

### Data Sonification Theory

This system is grounded in established research on data sonification:

**Key Principles:**
1. **Parameter Mapping**: Direct, intuitive mappings between data dimensions and auditory parameters
2. **Perceptual Validity**: Mappings align with human auditory perception
3. **Redundancy**: Critical information conveyed through multiple auditory dimensions
4. **Alerting**: Anomalies marked through perceptual salience

### Psychoacoustic Considerations

**Pitch Mapping:**
- pH → Pitch: Lower pitch for acidic, higher for basic
- Rationale: Aligns with conceptual metaphors (low=bad, high=good)
- Range: 110-880 Hz (A2 to A5) - within optimal hearing range

**Rhythm Mapping:**
- Temperature → Rhythm density
- Rationale: Higher energy = more rhythmic activity
- Range: 0.5-8.0 events/second - perceptible but not overwhelming

**Dissonance Mapping:**
- Instability → Dissonance
- Rationale: Dissonance creates perceptual tension
- Implementation: Detuned oscillators, inharmonic spectra

### Auditory Display Best Practices

Based on guidelines from the International Community for Auditory Display (ICAD):

1. **Learnability**: Mappings should be intuitive and learnable
2. **Detectability**: Important changes should be perceptually salient
3. **Differentiability**: Different states should sound distinct
4. **Aesthetics**: Sound should be pleasant, not annoying
5. **Context**: Audio should complement, not replace, visual displays

### Chemical Process Monitoring

The system addresses challenges in chemical process monitoring:

**Traditional Limitations:**
- Visual monitoring requires constant attention
- Numerical data lacks immediate meaning
- Anomalies may be missed in complex displays

**Auditory Advantages:**
- Sound provides continuous monitoring without visual focus
- Pattern recognition in audio is intuitive
- Anomalies detected through perceptual changes
- Reduces cognitive load during multi-tasking

### Real-Time Systems Design

The system implements real-time design principles:

**Timing:**
- Sensor sampling: 10 Hz (Arduino)
- Audio block size: 1024 samples (~23ms latency)
- Dashboard refresh: 100ms (configurable)

**Reliability:**
- Graceful degradation if sensors fail
- Fallback to simulation mode
- Error handling in all critical paths

**Scalability:**
- Modular architecture allows component replacement
- Configuration-driven parameters
- Support for additional sensors

---

## References

### Academic Papers
- Hermann, T. (2008). "Taxonomy and definitions for sonification and auditory display"
- Kramer, G., et al. (1999). "Sonification Report: Status of the Field and Research Agenda"
- Barrass, S. (1997). "Auditory Information Design"

### Technical Resources
- Arduino Documentation: https://www.arduino.cc/en/reference/
- DFRobot pH Sensor: https://www.dfrobot.com/wiki/
- DS18B20 Datasheet: Maxim Integrated
- Streamlit Documentation: https://docs.streamlit.io/

### Standards
- IEC 60751: Temperature sensors
- ASTM D1293: Standard Test Method for pH

---

## Future Enhancements

### Planned Features
1. Machine learning-based state classification
2. Historical data logging and analysis
3. Mobile app companion
4. Additional sensor support (conductivity, turbidity)
5. Cloud-based monitoring and alerts
6. Multi-reaction simultaneous monitoring

### Research Directions
1. User studies on sonification effectiveness
2. Comparative studies with visual-only monitoring
3. Domain-specific calibration for different chemical processes
4. Integration with laboratory automation systems

---

## Contact and Support

For questions, issues, or contributions:
- Review troubleshooting section first
- Check GitHub issues (if applicable)
- Contact development team

---

**Document Version:** 1.0  
**Last Updated:** May 2026  
**System Version:** 1.0
