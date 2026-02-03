#include <Adafruit_MPU6050.h>
#include <Adafruit_BMP085.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
Adafruit_BMP085 bmp;

float knownAltitude = 0.0;   // meters (altitude at power-on)
float seaLevelPressure = 101325.0;

float filteredAltitude = 0.0;
float alpha = 0.95;   // smoothing factor

void setup() {
  Serial.begin(9600);
  while (!Serial) delay(10);

  Serial.println("Initializing sensors...");

  if (!bmp.begin()) {
    Serial.println("BMP085 not found!");
    while (1);
  }

  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    while (1);
  }

  Serial.println("Sensors OK");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  calibrateBarometer();

  filteredAltitude = bmp.readAltitude(seaLevelPressure);
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float pressure = bmp.readPressure();
  float rawAltitude = bmp.readAltitude(seaLevelPressure);

  // Exponential low-pass filter
  filteredAltitude = alpha * filteredAltitude + (1.0 - alpha) * rawAltitude;

  Serial.println("=================================");
  Serial.print("Pressure: ");
  Serial.print(pressure);
  Serial.println(" Pa");

  Serial.print("Raw altitude: ");
  Serial.print(rawAltitude);
  Serial.println(" m");

  Serial.print("Filtered altitude: ");
  Serial.print(filteredAltitude);
  Serial.println(" m");

  Serial.print("MPU Temp: ");
  Serial.print(temp.temperature);
  Serial.println(" C");

  Serial.println();
  delay(1000);
}

void calibrateBarometer() {
  Serial.println("Calibrating barometer...");

  float pressure = bmp.readPressure();

  // Calculate sea-level pressure from known altitude
  seaLevelPressure = pressure / pow(
    1.0 - (knownAltitude / 44330.0),
    5.255
  );

  Serial.print("Measured pressure: ");
  Serial.print(pressure);
  Serial.println(" Pa");

  Serial.print("Calculated sea-level pressure: ");
  Serial.print(seaLevelPressure);
  Serial.println(" Pa");

  Serial.println("Calibration complete.");
}
