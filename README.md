# Chemical-to-Audio Intelligent Monitoring System

A real-time auditory interpretation engine for chemistry that transforms chemical process behavior into meaningful sound patterns and live visual feedback.

![System Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Project Overview

This system monitors chemical reactions through physical sensors and converts chemical behavior into real-time sound, auditory intelligence, and interactive visualization. The objective is to allow users to:

- **Hear** chemical stability and anomalies
- **Perceive** reaction dynamics intuitively
- **Understand** process states through sound
- **Detect** anomalies through auditory cues

The system acts as an intelligent agent that perceives chemical signals, interprets behavior, classifies states, generates adaptive responses, and communicates process conditions through sound.

## ✨ Key Features

### Dual Mode Operation
- **Simulation Mode**: Fully virtual chemical reaction simulation for testing and demonstrations
- **Hardware Mode**: Real sensor data acquisition via Arduino

### Intelligent State Classification
- **Stable**: Reaction within normal parameters
- **Transitional**: Reaction undergoing change
- **Critical**: High instability detected
- **Chaotic**: Unpredictable behavior

### Research-Driven Sonification
- pH level → Pitch center
- pH movement → Pitch glide
- Temperature → Rhythm density
- Stability → Harmonic consistency
- Instability → Dissonance
- Critical states → Distortion/noise layers

### Real-Time Dashboard
- Live sensor cards (pH, temperature, instability)
- Real-time charts (pH, temperature, volatility)
- State timeline visualization
- Audio parameter monitoring
- Event logging

### Voice Feedback
- Spoken state change announcements
- Contextual alerts for important transitions
- Configurable cooldown periods

## 🏗️ System Architecture

```
Chemical Reaction → Sensor Acquisition → Signal Processing → 
Feature Extraction → State Classification → Sonification Engine → 
Voice Feedback → Visual Dashboard
```

## 📁 Project Structure

```
chemical_audio_project/
├── app.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── DOCUMENTATION.md                # Comprehensive technical docs
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

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Arduino IDE (for hardware mode)
- Arduino Uno with sensors (for hardware mode)

### Installation

1. **Clone or navigate to project directory**
```bash
cd /Users/jessipavia/chemical
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install system dependencies**

**macOS:**
```bash
brew install portaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-pyaudio
sudo apt-get install espeak
```

**Windows:**
- Download and install PortAudio from http://www.portaudio.com/

### Running the System

#### Simulation Mode (No Hardware Required)

```bash
streamlit run app.py
```

1. Open browser to `http://localhost:8501`
2. Select "Simulation" mode in sidebar
3. Choose a scenario (e.g., "Stable Reaction")
4. Click "Start/Stop" to begin monitoring
5. Observe real-time audio and visualizations

#### Hardware Mode (Requires Arduino)

1. **Upload Arduino firmware**
   - Open `arduino/sensor_stream.ino` in Arduino IDE
   - Select Arduino Uno board
   - Select correct port
   - Upload firmware

2. **Connect sensors** (see DOCUMENTATION.md for wiring diagram)
   - pH sensor to A0
   - DS18B20 temperature sensor to D2
   - Include 4.7kΩ pull-up resistor for DS18B20

3. **Run the system**
```bash
streamlit run app.py
```

4. **Configure in dashboard**
   - Select "Hardware" mode in sidebar
   - Enter serial port (e.g., /dev/ttyUSB0 or COM3)
   - Click "Connect"
   - Click "Start/Stop" to begin monitoring

## 🔧 Hardware Requirements

### Required Components
- **Arduino Uno**
- **DFRobot Gravity Analog pH Sensor Kit**
- **DS18B20 Waterproof Temperature Sensor**
- **4.7kΩ resistor** (for DS18B20 pull-up)
- **USB cable** (data cable, not charge-only)

### Optional Components
- **TCS34725 RGB Color Sensor** (requires Arduino Mega)
- **Raspberry Pi 4+** (alternative to laptop)

### Wiring Summary

| Arduino Pin | Component        | Connection |
|-------------|------------------|------------|
| A0          | pH Sensor Signal | Analog     |
| D2          | DS18B20 Data     | Digital    |
| GND         | Both sensors     | Ground     |
| 5V          | Both sensors     | Power      |

**Critical**: DS18B20 requires 4.7kΩ pull-up between Data pin and VCC.

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed wiring diagram.

## 🎛️ Configuration

### System Settings

Edit `src/config/settings.py` to customize:

- **Audio parameters**: Sample rate, pitch ranges, rhythm density
- **Classification thresholds**: State classification sensitivity
- **Sonification mappings**: Sensor-to-audio parameter relationships
- **Signal processing**: Filter parameters, smoothing factors

### Dashboard Settings

Configure via Streamlit sidebar:
- System mode (Simulation/Hardware)
- Refresh rate
- Audio enable/disable
- Voice enable/disable
- Simulation scenarios

## 📊 Demo Scenarios

The system includes preset simulation scenarios:

1. **Stable Reaction**: Calm, stable chemical process
2. **Acid-Base Titration**: Gradual pH increase
3. **Exothermic Reaction**: Temperature spike
4. **Unstable Oscillation**: Chaotic pH swings

Select these from the sidebar in Simulation Mode.

## 🔬 Calibration

### pH Sensor Calibration

Required materials:
- pH 4.0 buffer solution
- pH 7.0 buffer solution
- pH 10.0 buffer solution (optional)

Procedure:
1. Immerse probe in pH 7.0 buffer
2. Wait 2 minutes for stabilization
3. Note reading and calculate offset
4. Update `PH_OFFSET` in Arduino code
5. Repeat with pH 4.0 buffer
6. Re-upload firmware

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed calibration procedure.

### Temperature Sensor

DS18B20 is factory-calibrated. Verify with ice-water (0°C) test.

## 🐛 Troubleshooting

### Common Issues

**Arduino not detected:**
- Check USB cable (use data cable)
- Verify Arduino is powered
- Install drivers (CH340 for clones)
- Try different USB port

**No serial data:**
- Verify firmware uploaded
- Check baud rate (115200)
- Test with Arduino Serial Monitor
- Check sensor wiring

**Audio not playing:**
- Check system audio output
- Install PortAudio dependency
- Verify "Enable Audio" checkbox
- Check audio device permissions

**Voice not working:**
- Verify "Enable Voice" checkbox
- Install espeak (Linux)
- Check voice engine logs

See [DOCUMENTATION.md](DOCUMENTATION.md) for comprehensive troubleshooting guide.

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Comprehensive technical documentation including:
  - System architecture details
  - Hardware setup and wiring diagrams
  - Sensor calibration procedures
  - Demo plan and talking points
  - Research foundation
  - Troubleshooting guide

## 🎓 Research Foundation

This system is grounded in established research:

- **Data Sonification Theory**: Parameter mapping, perceptual validity
- **Psychoacoustics**: Pitch, rhythm, and dissonance perception
- **Auditory Display**: ICAD best practices
- **Chemical Process Monitoring**: Real-time anomaly detection

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed research references.

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional sensor support
- Machine learning classification
- Mobile app companion
- Cloud integration
- User studies and validation

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- International Community for Auditory Display (ICAD)
- Arduino open-source hardware community
- Streamlit framework
- Scientific Python ecosystem (NumPy, SciPy)

## 📞 Support

For questions or issues:
1. Review troubleshooting section in DOCUMENTATION.md
2. Check GitHub issues
3. Contact development team

---

**Version**: 1.0  
**Last Updated**: May 2026  
**Status**: Competition-Ready ✅
