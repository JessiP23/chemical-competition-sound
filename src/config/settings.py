# settings.py — All configurable parameters in one place

MODE = "simulation"  # "simulation" | "hardware"

# Serial port (hardware mode only)
SERIAL_PORT = "/dev/ttyUSB0"  # Linux: /dev/ttyUSB0 | Windows: COM3 | Mac: /dev/cu.usbmodem*
BAUD_RATE = 9600

# Sensor ranges
PH_MIN = 0.0
PH_MAX = 14.0
TEMP_MIN = 15.0
TEMP_MAX = 100.0
COLOR_LUMINANCE_MIN = 0.0
COLOR_LUMINANCE_MAX = 255.0

# State classification thresholds
THRESHOLDS = {
    "stable":       {"variance": 0.01,  "rate": 0.02},
    "transitional": {"variance": 0.05,  "rate": 0.10},
    "critical":     {"variance": 0.15,  "rate": 0.30},
    "chaotic":      {"variance": 0.30,  "rate": 0.60},
}

# Audio parameters
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
AUDIO_UPDATE_HZ = 20       # How often to recompute audio parameters
MASTER_VOLUME = 0.4

# Frequency map (pH → Hz) — psychoacoustic exponential mapping
PH_FREQ_BASE = 220.0       # Hz at pH=0
PH_FREQ_EXPONENT = 1/12    # Semitone per pH unit

# Rhythm (temperature → beats per second)
TEMP_BPM_MIN = 0.5         # BPS at min temperature
TEMP_BPM_MAX = 4.0         # BPS at max temperature

# Signal processing
MOVING_AVG_WINDOW = 10     # samples
LOWPASS_CUTOFF = 0.1       # normalized frequency for Butterworth
LOWPASS_ORDER = 4
VARIANCE_WINDOW = 30       # samples for rolling variance
RATE_WINDOW = 5            # samples for dpH/dt

# Voice engine
VOICE_COOLDOWN = {
    "stable":       30.0,   # seconds between repeat announcements
    "transitional": 15.0,
    "critical":     8.0,
    "chaotic":      5.0,
}

# Dashboard refresh
DASHBOARD_REFRESH_MS = 200  # milliseconds
HISTORY_LENGTH = 300        # data points kept in display buffer

# Simulator scenario durations (seconds)
SCENARIO_PHASE_DURATIONS = [15, 10, 12, 8, 10, 15]  # 6 phases
