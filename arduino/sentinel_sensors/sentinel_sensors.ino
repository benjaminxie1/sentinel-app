/*
 * Sentinel Fire Detection System - Arduino Sensor Array
 * Supports: DHT22, MQ-2, MQ-135, Flame Sensor
 * Communication: Serial @ 115200 baud
 */

#include <DHT.h>
#include <Wire.h>

// Pin definitions
#define DHT_PIN 2
#define MQ2_PIN A0
#define MQ135_PIN A1
#define FLAME_PIN 3
#define FLAME_ANALOG A2
#define LED_STATUS 13
#define BUZZER_PIN 9

// Sensor configuration
#define DHT_TYPE DHT22
#define SAMPLE_INTERVAL 100  // ms
#define CALIBRATION_TIME 20000  // 20 seconds

// Communication protocol
#define SYNC_BYTE 0xAA
#define END_BYTE 0x55

// Sensor objects
DHT dht(DHT_PIN, DHT_TYPE);

// Sensor data structure (24 bytes)
struct SensorData {
  uint8_t sync;           // Sync byte
  float temperature;      // DHT22
  float humidity;         // DHT22
  float smoke_ppm;        // MQ-2
  float co_ppm;           // MQ-135
  float reserved;         // Future use
  uint8_t flame_detected; // Digital flame sensor
  uint16_t ir_value;      // Analog flame reading
  uint8_t end;            // End byte
} __attribute__((packed));

// Calibration values
float R0_MQ2 = 10.0;    // Calibrated in clean air
float R0_MQ135 = 10.0;  // Calibrated in clean air
float RL_VALUE = 10.0;  // Load resistance in kOhms

// State variables
unsigned long lastSample = 0;
unsigned long startTime = 0;
bool calibrated = false;
int sampleCount = 0;
float tempSum = 0, humSum = 0, smokeSum = 0, coSum = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LED_STATUS, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(FLAME_PIN, INPUT);
  
  // Initialize sensors
  dht.begin();
  
  // Status indicator
  digitalWrite(LED_STATUS, HIGH);
  delay(1000);
  digitalWrite(LED_STATUS, LOW);
  
  // Initial calibration
  Serial.println("SENTINEL_READY");
  performCalibration();
  
  startTime = millis();
}

void loop() {
  // Handle serial commands
  if (Serial.available()) {
    handleCommand();
  }
  
  // Sample sensors at defined interval
  if (millis() - lastSample >= SAMPLE_INTERVAL) {
    lastSample = millis();
    
    SensorData data = readSensors();
    sendSensorData(data);
    
    // Check for critical conditions
    checkAlerts(data);
    
    // Update running averages
    updateAverages(data);
  }
}

SensorData readSensors() {
  SensorData data;
  
  // Protocol bytes
  data.sync = SYNC_BYTE;
  data.end = END_BYTE;
  
  // DHT22 readings
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Validate DHT readings
  if (isnan(data.temperature)) data.temperature = -999;
  if (isnan(data.humidity)) data.humidity = -999;
  
  // MQ-2 Smoke sensor
  int mq2_raw = analogRead(MQ2_PIN);
  data.smoke_ppm = calculatePPM_MQ2(mq2_raw);
  
  // MQ-135 CO sensor  
  int mq135_raw = analogRead(MQ135_PIN);
  data.co_ppm = calculatePPM_MQ135(mq135_raw);
  
  // Flame sensor
  data.flame_detected = !digitalRead(FLAME_PIN);  // Active low
  data.ir_value = analogRead(FLAME_ANALOG);
  
  data.reserved = 0.0;
  
  return data;
}

float calculatePPM_MQ2(int raw_adc) {
  float resistance = calculateResistance(raw_adc);
  float ratio = resistance / R0_MQ2;
  
  // MQ-2 smoke curve approximation
  // PPM = a * ratio^b (from datasheet curve)
  float ppm = 613.9 * pow(ratio, -2.074);
  
  return constrain(ppm, 0, 10000);
}

float calculatePPM_MQ135(int raw_adc) {
  float resistance = calculateResistance(raw_adc);
  float ratio = resistance / R0_MQ135;
  
  // MQ-135 CO curve approximation
  float ppm = 116.6 * pow(ratio, -2.769);
  
  return constrain(ppm, 0, 1000);
}

float calculateResistance(int raw_adc) {
  float voltage = raw_adc * (5.0 / 1023.0);
  float rs_gas = ((5.0 * RL_VALUE) / voltage) - RL_VALUE;
  return rs_gas;
}

void sendSensorData(SensorData &data) {
  // Send as binary packet
  Serial.write((uint8_t*)&data, sizeof(SensorData));
}

void checkAlerts(SensorData &data) {
  bool alert = false;
  
  // Temperature threshold
  if (data.temperature > 60) {
    alert = true;
  }
  
  // Smoke threshold
  if (data.smoke_ppm > 300) {
    alert = true;
  }
  
  // CO threshold
  if (data.co_ppm > 50) {
    alert = true;
  }
  
  // Flame detected
  if (data.flame_detected) {
    alert = true;
  }
  
  // Visual/audio alert
  if (alert) {
    digitalWrite(LED_STATUS, HIGH);
    tone(BUZZER_PIN, 2000, 100);
  } else {
    digitalWrite(LED_STATUS, LOW);
  }
}

void updateAverages(SensorData &data) {
  if (data.temperature != -999) {
    tempSum += data.temperature;
    humSum += data.humidity;
    smokeSum += data.smoke_ppm;
    coSum += data.co_ppm;
    sampleCount++;
  }
}

void handleCommand() {
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  
  if (cmd == "$INIT") {
    Serial.println("ACK:INIT");
    performCalibration();
  }
  else if (cmd == "$CONFIG") {
    sendConfiguration();
  }
  else if (cmd == "$CALIBRATE") {
    performCalibration();
  }
  else if (cmd == "$CAL_STATUS") {
    sendCalibrationStatus();
  }
  else if (cmd == "$HEARTBEAT") {
    Serial.println("ACK:HEARTBEAT");
  }
  else if (cmd == "$STATS") {
    sendStatistics();
  }
  else if (cmd == "$RESET") {
    resetSystem();
  }
}

void performCalibration() {
  Serial.println("CAL:START");
  
  float mq2_sum = 0, mq135_sum = 0;
  int samples = 100;
  
  for (int i = 0; i < samples; i++) {
    mq2_sum += calculateResistance(analogRead(MQ2_PIN));
    mq135_sum += calculateResistance(analogRead(MQ135_PIN));
    delay(50);
    
    // Blink LED during calibration
    digitalWrite(LED_STATUS, i % 2);
  }
  
  R0_MQ2 = mq2_sum / samples;
  R0_MQ135 = mq135_sum / samples;
  
  calibrated = true;
  digitalWrite(LED_STATUS, LOW);
  
  Serial.println("CAL:COMPLETE");
}

void sendConfiguration() {
  Serial.print("CONFIG:");
  Serial.print("DHT22,MQ2,MQ135,FLAME;");
  Serial.print("INTERVAL:");
  Serial.print(SAMPLE_INTERVAL);
  Serial.print(";VERSION:2.0");
  Serial.println();
}

void sendCalibrationStatus() {
  Serial.print("CAL_STATUS:");
  Serial.print(calibrated ? "OK" : "PENDING");
  Serial.print(";R0_MQ2:");
  Serial.print(R0_MQ2);
  Serial.print(";R0_MQ135:");
  Serial.println(R0_MQ135);
}

void sendStatistics() {
  Serial.print("STATS:");
  Serial.print("UPTIME:");
  Serial.print(millis() - startTime);
  Serial.print(";SAMPLES:");
  Serial.print(sampleCount);
  
  if (sampleCount > 0) {
    Serial.print(";AVG_TEMP:");
    Serial.print(tempSum / sampleCount);
    Serial.print(";AVG_HUM:");
    Serial.print(humSum / sampleCount);
    Serial.print(";AVG_SMOKE:");
    Serial.print(smokeSum / sampleCount);
    Serial.print(";AVG_CO:");
    Serial.print(coSum / sampleCount);
  }
  Serial.println();
}

void resetSystem() {
  Serial.println("ACK:RESET");
  delay(100);
  
  // Reset statistics
  sampleCount = 0;
  tempSum = humSum = smokeSum = coSum = 0;
  
  // Recalibrate
  performCalibration();
}
