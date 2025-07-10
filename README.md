# 🌱 ESP32 Irrigation Controller Simulator

A comprehensive Streamlit web application that simulates an ESP32-based irrigation control system. This app provides real-time monitoring, manual control, and system management for a smart irrigation system.

## 🚀 Features

### Real-Time Dashboard
- **Live Sensor Data**: Temperature, humidity, soil moisture, and light levels
- **Zone Management**: Control up to 4 irrigation zones independently
- **Pump Monitoring**: Real-time pressure and flow rate tracking
- **System Status**: Device connectivity, uptime, and performance metrics

### Manual Controls
- Start/Stop irrigation system
- Individual zone control
- Manual data synchronization
- Device restart simulation
- Network connectivity toggle (online/offline simulation)

### Data Visualization
- Real-time sensor data charts
- Historical data tracking
- Command history logging
- System performance metrics

## 📁 Project Structure

```
esp-simulator-app/
├── main.py               # Streamlit dashboard application
├── espsimulation.py      # ESP32 device simulation logic
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .streamlit/          # Streamlit configuration (optional)
    └── config.toml
```

## 🛠️ Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd esp-simulator-app
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

5. **Access the dashboard**
   - Open your browser to `http://localhost:8501`
   - The ESP32 simulator will start automatically

## ☁️ Deployment on Streamlit Cloud

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: ESP32 Irrigation Simulator"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set the main file path: `main.py`
   - Click "Deploy"

3. **Configuration** (if needed)
   - The app will automatically install dependencies from `requirements.txt`
   - No additional configuration required for basic deployment

## 🎮 How to Use

### Dashboard Overview
- **Left Sidebar**: Control panel with manual commands and zone controls
- **Main Area**: Real-time sensor data, zone status, and system information
- **Bottom Section**: Command history and logs

### Basic Operations

1. **Start Irrigation**
   - Click "🚀 Start Irrigation" in the sidebar
   - All zones will activate and the pump will start
   - Monitor real-time data changes

2. **Zone Control**
   - Select individual zones from the dropdown
   - Start/stop specific zones as needed
   - Each zone has configurable duration settings

3. **System Monitoring**
   - View real-time sensor readings
   - Monitor pump pressure and flow rates
   - Check device connectivity and performance

4. **Simulation Features**
   - Toggle "Network Status" to simulate offline conditions
   - Use "Restart ESP" to simulate device reboot
   - "Sync Data" to refresh all readings

### Advanced Features

- **Auto-refresh**: Enable automatic dashboard updates every 5 seconds
- **Historical Data**: View sensor data trends over time
- **Command Logging**: Track all commands sent to the device
- **Offline Simulation**: Test system behavior during network outages

## 🔧 Technical Details

### Architecture
- **Frontend**: Streamlit web framework
- **Backend**: Python threading for real-time simulation
- **Data Flow**: Shared state management with thread-safe operations
- **Simulation**: Realistic sensor data with environmental variations

### ESP32 Simulation Features
- **Realistic Sensor Data**: Temperature, humidity, soil moisture, light levels
- **Time-based Variations**: Day/night cycles, weather patterns
- **Irrigation Effects**: Soil moisture increases during watering
- **System Responses**: Pump pressure, flow rates, valve operations
- **Device Metrics**: Uptime, memory usage, WiFi strength

### Data Models

#### Sensor Data
```python
{
    'temperature': float,      # °C (20-35)
    'humidity': float,         # % (30-90)
    'soil_moisture': float,    # % (0-100)
    'light_level': float       # lux (0-1000)
}
```

#### Zone Configuration
```python
{
    'active': bool,           # Zone running status
    'valve_open': bool,       # Valve position
    'duration_minutes': int,  # Irrigation duration
    'soil_moisture': float,   # Zone-specific moisture
    'last_run': str          # Last activation time
}
```

## 🐛 Troubleshooting

### Common Issues

1. **App won't start**
   - Check Python version (3.7+ required)
   - Verify all dependencies are installed
   - Run `pip install -r requirements.txt`

2. **Real-time updates not working**
   - Ensure auto-refresh is enabled
   - Check browser console for errors
   - Try manual refresh button

3. **Deployment issues**
   - Verify `requirements.txt` is in root directory
   - Check Streamlit Cloud logs for errors
   - Ensure GitHub repository is public or properly connected

### Performance Tips
- Disable auto-refresh for better performance on slower connections
- Use manual refresh when needed
- Monitor browser memory usage for extended sessions

## 🔮 Future Enhancements

- **Weather Integration**: Real weather data API integration
- **Scheduling**: Automated irrigation schedules
- **Alerts**: Email/SMS notifications for system events
- **Data Export**: CSV/JSON export functionality
- **Multi-device**: Support for multiple ESP32 devices
- **User Authentication**: Login system for multi-user access

## 📝 Development Notes

### Code Structure
- `main.py`: Streamlit UI and application logic
- `espsimulation.py`: ESP32 device simulation with threading
- Thread-safe operations using locks
- Session state management for real-time updates

### Customization
- Modify sensor ranges in `espsimulation.py`
- Adjust update intervals (currently 5 seconds)
- Add new zones or sensors as needed
- Customize UI layout and styling

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Create a GitHub issue
- Check the troubleshooting section
- Review Streamlit documentation

---

**Happy Irrigating! 🌱💧**