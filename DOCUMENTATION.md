# Hardware handoff and acceptance checklist

## Equipment

- Arduino Uno R3 and USB **data** cable (plus laptop adapter if necessary).
- DFRobot Gravity **SEN0161-V2**, including BNC probe and interface board.
- Encapsulated DS18B20, 4.7 kΩ resistor, connecting wires; breadboard recommended.
- Fresh pH 7 and pH 4 buffers, manufacturer-specified storage solution, rinse water.
- Suitable vessel and probe holders; reference thermometer and independent pH check.
- Existing laptop and its speakers suffice. Color sensor/Pi/external speaker are optional.

Confirm the solution is compatible with the probes. The SEN0161-V2 probe specifies
5–60°C and response time under two minutes. This is a sensor response limit, separate
from software latency. Do not assume an encapsulated temperature probe's cable or
seal has the same rating as its internal DS18B20 chip.

## Wiring (power disconnected while assembling)

| Connection | Uno R3 |
|---|---|
| pH interface A/signal | A0 |
| pH interface + | 5V |
| pH interface − | GND |
| DS18B20 data | D2 |
| DS18B20 supply | 5V |
| DS18B20 ground | GND |
| 4.7 kΩ resistor | Between D2/data and 5V |
| USB | Laptop |

Connect the pH electrode to the interface BNC. Verify the purchased probe's wire
labels; do not infer function from cable color alone. Keep interface electronics dry.

## Firmware and calibration

1. Install Arduino IDE and libraries **OneWire** and **DallasTemperature**.
2. Open `arduino/sensor_stream.ino`. If the IDE asks to create a matching
   `sensor_stream` sketch folder, accept and keep the supplied sketch in it.
3. Select **Arduino Uno**, select its port, and upload.
4. Open Serial Monitor at **115200 baud**, newline line ending.
5. Initially records indicate `UNCALIBRATED`; measurements are not accepted as valid.
6. Place the pH probe in pH 7 buffer. Allow a stable reading; send `CAL7`.
7. Rinse, move to pH 4 buffer, allow stabilization; send `CAL4`.
8. Send `SAVE`. Check the success message. Coefficients persist in EEPROM.
9. Verify both buffers and an independent reference; compare temperature against a
   reference thermometer. Record results, date, probe ID, and a calibration ID.
10. Close Serial Monitor so it releases the port. Start the dashboard, choose hardware,
    enter the port and calibration record ID, set experiment limits, and Start.

The sketch performs a two-point ADC fit. It does **not** implement automatic
pH temperature compensation; calibrate/verify at the intended measurement temperature.
The calibration ID is a user-entered record identifier, not automatic proof of accuracy.
Neither an ADC range check nor a flat reading can conclusively detect an unplugged
pH electrode at the BNC; inspect and verify probes before each experiment.

## Serial contract

One ASCII record per newline, 115200 baud:

```text
CHEM1,sequence,millis,pH,tempC,rawADC,status
CHEM1,12,6500,7.010,25.250,307,OK
```

- Device timestamp is in milliseconds; sequence increases per sample.
- `OK`, `UNCALIBRATED`, `PH_FAULT`, `TEMP_FAULT` are current firmware statuses.
- Diagnostic lines start with `#`; they do not count as measurements.
- Firmware samples approximately every 0.5 seconds, with a blocking temperature
  conversion before acquisition; host timing uses actual device timestamps.
- Host rejects malformed/non-finite records and repeated or reversed clocks/sequences.
- After 3 seconds without a completed measurement, host reports a fault.
- Device reset, long-term millis rollover, malformed data or USB failure requires
  Stop/Start to establish a fresh session. No silent simulation substitution.
- Faulted samples are excluded from feature windows; recovery starts a new baseline.

## End-to-end acceptance

1. **Simulation:** Full demo shows stable → change → critical → fault → recovery;
   sound enabled produces distinguishable pitch/rhythm and fault cues.
2. **Calibration:** reference readings meet the accuracy agreed for the experiment.
3. **Live pH:** move between known buffers; confirm changed measured pH and pitch
   after probe stabilization. Configure test limits intentionally for this test.
4. **Live temperature:** controlled temperature change within probe limits changes
   displayed temperature and pulse rate.
5. **Critical alert:** set a demo threshold near the current value; verify critical
   status, reason, audio, and log. Restore the actual experiment settings afterward.
6. **Fault:** unplug USB; confirm fault within approximately 3 seconds, no normal
   replacement readings, and a distinct fault tone. Stop, reconnect, Start.
7. **Sensor failure:** disconnect temperature data; verify TEMP_FAULT and recovery
   after reconnection. pH disconnection detection has the limitation noted above.
8. **Recording:** Stop, download JSONL, check source/calibration/profile and events.
9. **Duration:** run 30 minutes, confirm worker health, sound continuity and bounded memory.

Physical checks and Arduino compile/upload are pending until equipment/toolchain is available.
Software tests do not establish chemical accuracy or audible usability.

## References

- [SEN0161-V2 specifications and calibration guidance](https://wiki.dfrobot.com/sen0161-v2)
- [DS18B20 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf)
- [Arduino Uno R3](https://docs.arduino.cc/hardware/uno-rev3/)
