# ESP32 Client Simulator

This Python script simulates an ESP32 device that connects to your Streamlit dashboard. You can run this on your laptop to test the system and send commands.

## Quick Start

1. **Download the client script:**
   ```bash
   # Download esp_client.py to your laptop
   wget https://raw.githubusercontent.com/your-repo/deploy/main/esp_client.py
   # OR copy the file manually
   ```

2. **Install requirements:**
   ```bash
   pip install requests
   ```

3. **Run the client:**
   ```bash
   python esp_client.py
   ```

## Usage Options

### Basic Usage
```bash
# Connect with auto-generated device ID
python esp_client.py

# Connect with custom device ID
python esp_client.py --device-id "MY_ESP32_001"

# Connect to different dashboard URL
python esp_client.py --url "https://your-custom-url.streamlit.app"
```

### Interactive Mode
```bash
# Run in interactive mode for manual control
python esp_client.py --interactive
```

In interactive mode, you can use these commands:
- `status` - Show current device status
- `set temperature 25.5` - Set temperature sensor value
- `set humidity 60.0` - Set humidity sensor value
- `set soil_moisture 45.0` - Set soil moisture value
- `set light_level 500` - Set light level value
- `quit` - Exit the program

## What the Client Does

1. **Registers** with the dashboard using a unique device ID
2. **Sends heartbeats** every 10 seconds with current sensor data
3. **Checks for commands** every 5 seconds from the dashboard
4. **Executes commands** like starting irrigation, setting sensor values, etc.
5. **Reports results** back to the dashboard

## Supported Commands from Dashboard

- **Set Sensor Values**: Change temperature, humidity, soil moisture, light level
- **Start/Stop Irrigation**: Control the entire irrigation system
- **Zone Control**: Start/stop individual irrigation zones
- **System Commands**: Sync, restart, etc.

## Dashboard Features

When your ESP32 client is connected, the dashboard will show:

- ✅ **Device connected** with real-time sensor data
- 🎛️ **Control panel** to send commands to your device
- 📊 **Live sensor charts** and metrics
- 🚿 **Zone status** and controls
- 📋 **Command history** showing all sent commands

When no devices are connected:
- 🔌 **"No ESP32 Devices Connected"** message
- 📋 **Connection instructions**
- 🔗 **API endpoint documentation**

## Example Session

```bash
$ python esp_client.py --device-id "LAPTOP_ESP32"

ESP32 Client initialized with Device ID: LAPTOP_ESP32
Target URL: https://deploy-esp-connection.streamlit.app

🚀 Starting ESP32 Client...
✅ Device LAPTOP_ESP32 registered successfully
✅ ESP32 Client started successfully!
📱 Device ID: LAPTOP_ESP32
🌐 Dashboard URL: https://deploy-esp-connection.streamlit.app

💡 You can now control this device from the dashboard!
   - Set sensor values
   - Start/stop irrigation
   - Control individual zones

📊 Current sensor values:
   temperature: 25.0
   humidity: 60.0
   soil_moisture: 45.0
   light_level: 500.0

⏳ Running... Press Ctrl+C to stop
💓 Heartbeat sent - T:25.2°C H:59.8% SM:45.1%
🔧 Executing command: set_sensor_value with params: {'sensor': 'temperature', 'value': 30.0}
   📊 temperature: 25.2 → 30.0
   ✅ Command result sent: temperature set to 30.0
💓 Heartbeat sent - T:30.0°C H:60.1% SM:44.9%
```

## Troubleshooting

### Connection Issues
- Make sure you have internet connection
- Check that the dashboard URL is correct
- Verify the dashboard is running and accessible

### Command Issues
- Commands are processed automatically
- Check the dashboard's command history for results
- Look at the client console output for execution details

### Sensor Value Issues
- Sensor values are automatically kept within realistic ranges
- Temperature: 15-40°C
- Humidity: 20-90%
- Soil Moisture: 0-100%
- Light Level: 0-1000 lux

## API Endpoints

The client uses these API endpoints to communicate with the dashboard:

```
# Device Registration
GET /?api=register&device_id=YOUR_DEVICE_ID&firmware=1.0.0

# Send Heartbeat with Sensor Data
GET /?api=heartbeat&device_id=YOUR_DEVICE_ID&temperature=25.5&humidity=60.0

# Get Pending Commands
GET /?api=get_commands&device_id=YOUR_DEVICE_ID

# Send Command Result
GET /?api=command_result&device_id=YOUR_DEVICE_ID&command_id=CMD_ID&success=true
```

## Real ESP32 Implementation

To implement this on a real ESP32:

1. Use the same API endpoints
2. Replace simulated sensors with real sensor readings
3. Replace simulated actuators with real GPIO controls
4. Add WiFi connection management
5. Add error handling and reconnection logic

Example ESP32 Arduino code structure:
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void setup() {
  // Initialize WiFi, sensors, actuators
  registerDevice();
}

void loop() {
  sendHeartbeat();
  checkCommands();
  delay(5000);
}
```