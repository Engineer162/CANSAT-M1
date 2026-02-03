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


void setup(void) {
  Serial.begin(9600);
  while (!Serial)
    delay(10); // will pause Zero, Leonardo, etc until serial console opens

  Serial.println("Initializing sensors...");

  if (!bmp.begin()) {
    Serial.println("BMP180 not found!");
    while (1);
  }
  Serial.println("BMP180 Found!");

  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    while (1);
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

  calibrateBarometer();

  filteredAltitude = bmp.readAltitude(seaLevelPressure);

  Serial.println("");
  delay(100);
}

void loop() {

  /* Get new sensor events with the readings */
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);


  float pressure = bmp.readPressure();
  float rawAltitude = bmp.readAltitude(seaLevelPressure);

  // Exponential low-pass filter
  filteredAltitude = alpha * filteredAltitude + (1.0 - alpha) * rawAltitude;

  /* Print out the values */
  Serial.print("Acceleration X: ");
  Serial.print(a.acceleration.x);
  Serial.print(", Y: ");
  Serial.print(a.acceleration.y);
  Serial.print(", Z: ");
  Serial.print(a.acceleration.z);
  Serial.println(" m/s^2");

  Serial.print("Rotation X: ");
  Serial.print(g.gyro.x);
  Serial.print(", Y: ");
  Serial.print(g.gyro.y);
  Serial.print(", Z: ");
  Serial.print(g.gyro.z);
  Serial.println(" rad/s");

  Serial.print("Pressure: ");
  Serial.print(pressure);
  Serial.println(" Pa");

  Serial.print("Raw altitude: ");
  Serial.print(rawAltitude);
  Serial.println(" m");

  Serial.print("Filtered altitude: ");
  Serial.print(filteredAltitude);
  Serial.println(" m");

  Serial.print("MPU Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" degC");

  Serial.print("BMP Temperature: ");
  Serial.print(bmp.readTemperature());
  Serial.println(" degC");

  Serial.println("");
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