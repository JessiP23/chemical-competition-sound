# Chemical-to-Audio Monitoring System

Local pH and temperature monitoring with continuous sound, a Streamlit dashboard,
explicit sensor faults, and JSONL experiment recordings.

**Status:** software simulation and test harness implemented. Physical accuracy,
Arduino compilation/upload, and actual sensor-to-speaker behavior require hardware validation.
Default limits are demonstration settings, not experiment safety limits.

## Run now

Python 3.11+ recommended (development environment: Python 3.13).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Select **simulation → Full demo**, optionally enable sound, then **Start**.
The 60-second loop demonstrates stable readings, pH change, temperature change,
critical pH, a sensor fault, and recovery. Individual scenarios are also available.
Stop before changing mode/settings. Audio plays on the server laptop, not a remote browser.

## Verify without sensors

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m src.demo
```

The demo generates `recordings/demo.wav` and `recordings/demo.jsonl` using the same
parser, detector, and sound renderer as live monitoring. Play the WAV to hear it.

Replay a recorded run:

```sh
.venv/bin/python -m src.demo --replay recordings/demo.jsonl --output recordings/replayed
```

Replay recomputes decisions using the saved profile. It preserves sample intervals
(up to 3 seconds per gap); transport-only faults without samples are omitted.

## When hardware arrives

Follow [DOCUMENTATION.md](DOCUMENTATION.md) for wiring, firmware, calibration,
and the end-to-end checklist. Required setup: Uno R3, SEN0161-V2 kit, DS18B20 probe,
4.7 kΩ resistor, data cable, wires, calibration buffers, and probe storage solution.
A breadboard is convenient; an external speaker and Raspberry Pi are unnecessary.

## Architecture

`Arduino or simulator → CHEM1 parser → validity checks → time-based features → classifier → audio`

- `src/io/`: shared protocol, hardware connection, deterministic simulation.
- `src/core/`: demo profile, detector, mapping, service lifecycle and recording.
- `src/audio/tone_engine.py`: continuous phase synthesis, bounded output, visible device errors.
- `app.py`: shared start/stop controls, live values, charts, events and log download.
- `arduino/sensor_stream.ino`: Uno firmware with two-point calibration saved to EEPROM.
- `tests/`: parsing, timing, classification, fault/recovery, audio continuity, service and UI checks.

The dashboard uses one cached service per Python process. A serial connection is
owned by that service. Multiple browser sessions share controls. Run one server
process per physical device. Stop explicitly to release the serial port.

## Behavior

- No silent fallback from hardware to simulation and no fabricated normal readings.
- Sensor health faults override process classification.
- Absolute pH/temperature limits act immediately; trends require a 2-second window
  and 1-second persistence. These defaults are editable in `DetectionProfile`;
  absolute limits are also editable in the sidebar.
- pH maps to pitch; temperature to rhythm; changing values add noise; critical and
  sensor-fault sounds differ. Unknown/warmup is silent.
- Raw samples, features, decisions, audio parameters, source and calibration ID are
  logged. Memory history is bounded; recordings remain on disk until you remove them.
- Connection/protocol faults require **Stop → correct issue → Start**. A simulated
  sensor fault automatically recovers once valid measurements return.

The older voice and advanced chart/synthesis helpers remain optional modules;
spoken narration is not part of the supported monitoring path.
