/*
 * Chemical-to-Audio Intelligent Monitoring System
 * Arduino Sensor Stream Firmware
 * 
 * Reads pH, temperature, and optional color sensors
 * and streams data via serial for processing by Python application.
 * 
 * Hardware:
 * - Arduino Uno
 * - DFRobot Gravity Analog pH Sensor (Analog A0)
 * - DS18B20 Waterproof Temperature Sensor (Digital D2)
 * - TCS34725 RGB Color Sensor (I2C - optional, requires Arduino Mega)
 */

#include <OneWire.h>
#include <DallasTemperature.h>

// Pin definitions
#define PH_PIN A0
#define TEMP_PIN 2

// pH sensor calibration
#define PH_OFFSET 0.0  // Adjust after calibration

// Temperature sensor setup
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

// Timing
unsigned long lastUpdateTime = 0;
const unsigned long updateInterval = 100;  // 10 Hz update rate

// Smoothing
const int smoothingWindow = 5;
float phReadings[smoothingWindow];
int phIndex = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize temperature sensor
  tempSensor.begin();
  tempSensor.setResolution(10);  // 10-bit resolution (0.25°C)
  
  // Initialize pH readings array
  for (int i = 0; i < smoothingWindow; i++) {
    phReadings[i] = 7.0;
  }
  
  // Allow sensors to stabilize
  delay(2000);
  
  Serial.println("Chemical Sensor Stream Initialized");
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastUpdateTime >= updateInterval) {
    lastUpdateTime = currentTime;
    
    // Read sensors
    float ph = readPH();
    float temperature = readTemperature();
    
    // Optional: Read color sensor (if connected)
    // float colorR = readColorR();
    // float colorG = readColorG();
    // float colorB = readColorB();
    
    // Stream data via serial
    // Format: pH,temperature,colorR,colorG,colorB
    // Color values are optional (0 if not available)
    Serial.print(ph, 2);
    Serial.print(",");
    Serial.print(temperature, 2);
    Serial.print(",");
    Serial.print("0");  // colorR placeholder
    Serial.print(",");
    Serial.print("0");  // colorG placeholder
    Serial.print(",");
    Serial.println("0");  // colorB placeholder
  }
}

float readPH() {
  // Read analog pH sensor
  int rawValue = analogRead(PH_PIN);
  
  // Convert to voltage (0-5V)
  float voltage = rawValue * (5.0 / 1023.0);
  
  // Convert voltage to pH (DFRobot pH sensor formula)
  // pH = 7.0 - (voltage - 2.5) / 0.18  (approximate)
  // Adjust based on your specific sensor calibration
  float ph = 7.0 - (voltage - 2.5) / 0.18 + PH_OFFSET;
  
  // Apply smoothing
  phReadings[phIndex] = ph;
  phIndex = (phIndex + 1) % smoothingWindow;
  
  // Calculate moving average
  float sum = 0.0;
  for (int i = 0; i < smoothingWindow; i++) {
    sum += phReadings[i];
  }
  float smoothedPH = sum / smoothingWindow;
  
  // Clamp to valid range
  if (smoothedPH < 0.0) smoothedPH = 0.0;
  if (smoothedPH > 14.0) smoothedPH = 14.0;
  
  return smoothedPH;
}

float readTemperature() {
  // Request temperature from DS18B20
  tempSensor.requestTemperatures();
  
  // Read temperature in Celsius
  float tempC = tempSensor.getTempCByIndex(0);
  
  // Handle sensor error
  if (tempC == -127.0) {
    return 25.0;  // Return default value on error
  }
  
  return tempC;
}

/*
 * Optional color sensor functions
 * Requires TCS34725 library and I2C pins (SDA/SCL)
 * Only works on Arduino Mega or boards with dedicated I2C pins
 */

/*
#include <Wire.h>
#include <Adafruit_TCS34725.h>

Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

void initColorSensor() {
  if (tcs.begin()) {
    Serial.println("Color sensor initialized");
  } else {
    Serial.println("No color sensor found");
  }
}

float readColorR() {
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  return (float)r;
}

float readColorG() {
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  return (float)g;
}

float readColorB() {
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  return (float)b;
}
*/
