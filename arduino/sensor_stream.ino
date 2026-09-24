/* Uno R3 + SEN0161-V2 (A0) + DS18B20 (D2, 4.7k to 5V).
 * Libraries: OneWire, DallasTemperature. Serial: 115200, newline.
 * Protocol: CHEM1,sequence,millis,pH,tempC,rawADC,status
 * Calibration in Serial Monitor: CAL7, CAL4, SAVE (each newline).
 * Calibration is a two-point voltage fit at the calibration temperature.
 * No claim of automatic temperature compensation: verify at experiment temperature.
 */
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
#include <math.h>

OneWire wire(2);
DallasTemperature thermometer(&wire);
struct Calibration { unsigned long magic; float adc7; float adc4; } calibration;
const unsigned long MAGIC = 0x43484D31UL;
float point7 = 0, point4 = 0;
bool have7 = false, have4 = false;
unsigned long sequence = 0, lastSample = 0;
float raw = 0, temperature = 0;
bool haveSample = false;
char command[12];
byte commandLength = 0;
bool commandOverflow = false;

bool calibrated() {
  return calibration.magic == MAGIC && isfinite(calibration.adc7) && isfinite(calibration.adc4)
    && calibration.adc7 > 1 && calibration.adc4 < 1022
    && calibration.adc4 - calibration.adc7 > 10;
}

void setup() {
  Serial.begin(115200);
  thermometer.begin();
  thermometer.setResolution(10);
  EEPROM.get(0, calibration);
  Serial.println(F("# CHEM1 READY; calibrate CAL7, CAL4, SAVE"));
}

void handleCommand() {
  if (!haveSample || temperature < 5 || temperature > 60 || raw <= 1 || raw >= 1022) {
    Serial.println(F("# Calibration rejected: check sensors"));
    return;
  }
  if (!strcmp(command,"CAL7")) { point7=raw; have7=true; Serial.println(F("# pH7 point captured")); }
  else if (!strcmp(command,"CAL4")) { point4=raw; have4=true; Serial.println(F("# pH4 point captured")); }
  else if (!strcmp(command,"SAVE")) {
    if (have7 && have4 && point4-point7>10) {
      calibration.magic=MAGIC; calibration.adc7=point7; calibration.adc4=point4;
      EEPROM.put(0,calibration);
      have7=have4=false;
      Serial.println(F("# Calibration saved; verify with independent reference"));
    } else Serial.println(F("# Capture both stable buffer points before SAVE"));
  } else Serial.println(F("# Unknown command; use CAL7, CAL4, SAVE"));
}

void loop() {
  if (millis()-lastSample >= 500 || !haveSample) {
    thermometer.requestTemperatures(); // 10-bit conversion, up to 187.5 ms
    temperature=thermometer.getTempCByIndex(0);
    long sum=0;
    for (byte i=0;i<10;i++) sum+=analogRead(A0);
    raw=sum/10.0;
    lastSample=millis();
    haveSample=true;
    float ph=calibrated() ? 7.0+(raw-calibration.adc7)*(-3.0)/(calibration.adc4-calibration.adc7) : 0;
    const char* status="OK";
    if (!calibrated()) status="UNCALIBRATED";
    if (raw<=1 || raw>=1022 || ph<0 || ph>14) status="PH_FAULT";
    if (temperature<5 || temperature>60) status="TEMP_FAULT";
    Serial.print(F("CHEM1,")); Serial.print(sequence++); Serial.print(',');
    Serial.print(lastSample); Serial.print(','); Serial.print(ph,3); Serial.print(',');
    Serial.print(temperature,3); Serial.print(','); Serial.print((int)raw); Serial.print(',');
    Serial.println(status);
  }
  while (Serial.available()) {
    char c=Serial.read();
    if(c=='\r') continue;
    if(c=='\n') {
      command[commandLength]='\0';
      if(commandLength && !commandOverflow) handleCommand();
      commandLength=0; commandOverflow=false;
    } else if(commandLength<sizeof(command)-1) command[commandLength++]=c;
    else commandOverflow=true;
  }
}
