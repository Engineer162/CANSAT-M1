import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import re
from datetime import datetime

# Configuration
ARDUINO_PORT = '/dev/ttyACM3'  # Change this to your Arduino port (COM3, COM4, etc. on Windows)
BAUD_RATE = 9600
MAX_POINTS = 100  # Number of data points to display

# Data storage
data = {
    'time': deque(maxlen=MAX_POINTS),
    'pressure': deque(maxlen=MAX_POINTS),
    'raw_altitude': deque(maxlen=MAX_POINTS),
    'filtered_altitude': deque(maxlen=MAX_POINTS),
    'mpu_temp': deque(maxlen=MAX_POINTS),
    'timestamp': 0
}

def parse_sensor_data(line):
    """Parse a single line of sensor data"""
    try:
        if 'Pressure:' in line:
            match = re.search(r'Pressure:\s*([\d.]+)\s*Pa', line)
            if match:
                return 'pressure', float(match.group(1))
        elif 'Raw altitude:' in line:
            match = re.search(r'Raw altitude:\s*([-\d.]+)\s*m', line)
            if match:
                return 'raw_altitude', float(match.group(1))
        elif 'Filtered altitude:' in line:
            match = re.search(r'Filtered altitude:\s*([-\d.]+)\s*m', line)
            if match:
                return 'filtered_altitude', float(match.group(1))
        elif 'MPU Temp:' in line:
            match = re.search(r'MPU Temp:\s*([\d.]+)\s*C', line)
            if match:
                return 'mpu_temp', float(match.group(1))
    except Exception as e:
        print(f"Error parsing line: {line} - {e}")
    return None, None

def read_serial_data(ser):
    """Read and parse data from Arduino"""
    if ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                key, value = parse_sensor_data(line)
                if key and value is not None:
                    data[key].append(value)
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"Serial read error: {e}")

def update_graphs(frame):
    """Update graph data"""
    try:
        # Read from serial
        read_serial_data(ser)
        
        # Clear previous plots
        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()
        
        # Get indices for x-axis
        x_indices = list(range(len(data['pressure'])))
        
        # Plot 1: Pressure
        if data['pressure']:
            ax1.plot(x_indices, list(data['pressure']), 'b-', linewidth=2, marker='o')
            ax1.set_ylabel('Pressure (Pa)', fontsize=10)
            ax1.set_title('Pressure over Time', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # Plot 2: Altitude (Raw vs Filtered)
        if data['raw_altitude'] and data['filtered_altitude']:
            ax2.plot(x_indices, list(data['raw_altitude']), 'r-', label='Raw', marker='o', alpha=0.7)
            ax2.plot(x_indices, list(data['filtered_altitude']), 'g-', label='Filtered', marker='s', alpha=0.7)
            ax2.set_ylabel('Altitude (m)', fontsize=10)
            ax2.set_title('Altitude over Time', fontsize=12, fontweight='bold')
            ax2.legend(loc='best')
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: MPU Temperature
        if data['mpu_temp']:
            ax3.plot(x_indices, list(data['mpu_temp']), 'orange', linewidth=2, marker='D')
            ax3.set_ylabel('Temperature (°C)', fontsize=10)
            ax3.set_title('MPU Temperature over Time', fontsize=12, fontweight='bold')
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: Combined view (normalized)
        if all([data['pressure'], data['raw_altitude'], data['mpu_temp']]):
            # Normalize data to 0-1 range for comparison
            norm_pressure = [(p - min(data['pressure'])) / (max(data['pressure']) - min(data['pressure']) + 1e-6) 
                           for p in data['pressure']]
            norm_altitude = [(a - min(data['filtered_altitude'])) / (max(data['filtered_altitude']) - min(data['filtered_altitude']) + 1e-6) 
                           for a in data['filtered_altitude']]
            norm_temp = [(t - min(data['mpu_temp'])) / (max(data['mpu_temp']) - min(data['mpu_temp']) + 1e-6) 
                        for t in data['mpu_temp']]
            
            ax4.plot(x_indices, norm_pressure, 'b-', label='Pressure (norm)', marker='o', alpha=0.7)
            ax4.plot(x_indices, norm_altitude, 'g-', label='Altitude (norm)', marker='s', alpha=0.7)
            ax4.plot(x_indices, norm_temp, 'orange', label='Temp (norm)', marker='D', alpha=0.7)
            ax4.set_ylabel('Normalized Value', fontsize=10)
            ax4.set_title('All Sensors (Normalized)', fontsize=12, fontweight='bold')
            ax4.legend(loc='best')
            ax4.grid(True, alpha=0.3)
        
        # Set common x-label
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_xlabel('Sample Number', fontsize=10)
    
    except Exception as e:
        print(f"Graph update error: {e}")

def main():
    global ser
    
    try:
        # Open serial connection
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {ARDUINO_PORT} at {BAUD_RATE} baud")
        print("Waiting for data from Arduino...")
        
        # Create figure with 4 subplots
        global fig, ax1, ax2, ax3, ax4
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('CANSAT Sensor Data Monitoring', fontsize=14, fontweight='bold')
        
        # Create animation
        ani = FuncAnimation(fig, update_graphs, interval=500, repeat=True)
        
        plt.tight_layout()
        plt.show()
        
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        print(f"Available ports: Check your Arduino connection")
    except KeyboardInterrupt:
        print("\nClosing connection...")
    finally:
        if 'ser' in globals() and ser.is_open:
            ser.close()
            print("Serial connection closed")

if __name__ == "__main__":
    main()

