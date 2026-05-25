/*
 * sensor_stream.ino
 *
 * Arduino firmware for Chemical-to-Audio Intelligent Monitoring System.
 * Reads pH, temperature, and color sensors; streams via serial (CSV).
 *
 * Hardware:
 *   - pH sensor (analog A0)
 *   - DS18B20 temperature sensor (digital D2)
 *   - TCS34725 RGB color sensor (I2C - optional)
 *
 * Output format (CSV): pH,temperature,colorR,colorG,colorB
 * Update rate: 10 Hz (100ms)
 */

#include <OneWire.h>
#include <DallasTemperature.h>

// Pin definitions
#define PH_PIN A0
#define TEMP_PIN 2

// pH calibration offset (adjust after calibration)
#define PH_OFFSET 0.0

// Temperature sensor
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

// Timing
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 100;  // 10 Hz

// pH smoothing window
const int SMOOTH_WINDOW = 5;
float phBuffer[SMOOTH_WINDOW];
int phIndex = 0;

void setup() {
  Serial.begin(115200);
  
  tempSensor.begin();
  tempSensor.setResolution(10);  // 0.25°C resolution
  
  // Initialize pH buffer
  for (int i = 0; i < SMOOTH_WINDOW; i++) {
    phBuffer[i] = 7.0;
  }
  
  delay(2000);  // Sensor stabilization
  Serial.println("SENSOR_STREAM_READY");
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = now;
    
    float ph = readPH();
    float temp = readTemperature();
    
    // Color sensors (optional - return 0 if not connected)
    float r = 0, g = 0, b = 0;
    // readColor(&r, &g, &b);  // Uncomment if TCS34725 is connected
    
    // CSV output
    Serial.print(ph, 2);
    Serial.print(",");
    Serial.print(temp, 2);
    Serial.print(",");
    Serial.print(r, 0);
    Serial.print(",");
    Serial.print(g, 0);
    Serial.print(",");
    Serial.println(b, 0);
  }
}

float readPH() {
  int raw = analogRead(PH_PIN);
  float voltage = raw * (5.0 / 1023.0);
  
  // DFRobot pH sensor approximation
  float ph = 7.0 - (voltage - 2.5) / 0.18 + PH_OFFSET;
  
  // Moving average smoothing
  phBuffer[phIndex] = ph;
  phIndex = (phIndex + 1) % SMOOTH_WINDOW;
  
  float sum = 0.0;
  for (int i = 0; i < SMOOTH_WINDOW; i++) {
    sum += phBuffer[i];
  }
  float smoothed = sum / SMOOTH_WINDOW;
  
  // Clamp
  if (smoothed < 0.0) smoothed = 0.0;
  if (smoothed > 14.0) smoothed = 14.0;
  
  return smoothed;
}

float readTemperature() {
  tempSensor.requestTemperatures();
  float tempC = tempSensor.getTempCByIndex(0);
  
  if (tempC == -127.0) {
    return 25.0;  // Fallback on error
  }
  return tempC;
}

/*
 * Optional TCS34725 color sensor support.
 * Requires Adafruit_TCS34725 library.
 */
/*
#include <Wire.h>
#include <Adafruit_TCS34725.h>

Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

void initColor() {
  if (tcs.begin()) {
    Serial.println("Color sensor initialized");
  } else {
    Serial.println("No color sensor found");
  }
}

void readColor(float *r, float *g, float *b) {
  uint16_t red, green, blue, clear;
  tcs.getRawData(&red, &green, &blue, &clear);
  *r = (float)red;
  *g = (float)green;
  *b = (float)blue;
}
*/
