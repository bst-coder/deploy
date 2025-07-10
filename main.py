import streamlit as st
import time
import threading
from datetime import datetime
import json
from firebase_manager import cloud_device_manager

# Configure Streamlit page
st.set_page_config(
    page_title="ESP32 Irrigation Controller",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize cloud device manager
if 'cloud_device_manager_started' not in st.session_state:
    cloud_device_manager.start()
    st.session_state.cloud_device_manager_started = True

# Initialize other session state variables
if 'command_history' not in st.session_state:
    st.session_state.command_history = []

if 'selected_device' not in st.session_state:
    st.session_state.selected_device = None

def send_command(device_id, command, params=None):
    """Send command to ESP device via cloud and log it"""
    result = cloud_device_manager.send_command_to_device(device_id, command, params)
    st.session_state.command_history.append({
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'device_id': device_id,
        'command': command,
        'params': params,
        'result': result
    })
    return result

def show_no_devices_connected():
    """Show message when no ESP devices are connected"""
    st.title("🌱 ESP32 Irrigation Controller Dashboard - Cloud")
    st.markdown("---")
    
    # Large centered message
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h2>🔌 No ESP32 Devices Connected</h2>
            <p style="font-size: 18px; color: #666;">
                Waiting for ESP32 devices to connect to the cloud system...
            </p>
            <p style="font-size: 14px; color: #888;">
                Make sure your ESP32 device is powered on and connected to the internet.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Connection instructions
    st.markdown("---")
    st.subheader("📋 Cloud Connection Instructions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **For ESP32 Device:**
        1. Power on your ESP32 device
        2. Ensure it's connected to WiFi
        3. Configure it to use the cloud endpoints
        4. The device should automatically register
        """)
    
    with col2:
        st.markdown("""
        **For Python Script:**
        1. Download the `cloud_client.py` script
        2. Install required packages: `pip install requests`
        3. Run: `python cloud_client.py`
        4. The script will connect via cloud database
        """)
    
    # Cloud endpoints info
    st.markdown("---")
    st.subheader("☁️ Cloud Communication")
    
    st.markdown("""
    **How it works:**
    - ESP32 devices communicate through a cloud database (Firebase/similar)
    - Dashboard reads/writes to the same database
    - Real-time synchronization between devices and dashboard
    - No direct HTTP API calls needed
    """)
    
    st.code("""
# ESP32 Cloud Communication Pattern:
1. Device registers in cloud database
2. Device sends sensor data to cloud
3. Device polls cloud for commands
4. Dashboard reads device data from cloud
5. Dashboard writes commands to cloud
6. Device executes commands and reports results
    """)
    
    # Auto-refresh to check for new devices
    time.sleep(5)
    st.rerun()

def main():
    # Get connected devices from cloud
    connected_devices = cloud_device_manager.get_connected_devices()
    
    # If no devices connected, show the no devices page
    if not connected_devices:
        show_no_devices_connected()
        return
    
    st.title("🌱 ESP32 Irrigation Controller Dashboard - Cloud")
    st.markdown("---")
    
    # Device selection
    device_ids = list(connected_devices.keys())
    
    # Auto-select first device if none selected or selected device is not available
    if st.session_state.selected_device not in device_ids:
        st.session_state.selected_device = device_ids[0]
    
    # Device selector in sidebar
    with st.sidebar:
        st.header("☁️ Cloud Device Selection")
        selected_device = st.selectbox(
            "Select ESP32 Device",
            device_ids,
            index=device_ids.index(st.session_state.selected_device),
            key="device_selector"
        )
        st.session_state.selected_device = selected_device
        
        # Show device info
        device_data = connected_devices[selected_device]
        st.markdown(f"**Device ID:** {selected_device}")
        st.markdown(f"**Last Heartbeat:** {device_data['last_heartbeat'][:19]}")
        st.markdown(f"**Connection:** ☁️ Cloud")
        st.markdown(f"**Connection:** ☁️ Cloud")
        st.markdown("---")
    
    # Get current ESP state for selected device
    device_data = connected_devices[st.session_state.selected_device]
    esp_state = device_data['state']
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Connection status
        status_color = "🟢" if esp_state['online'] else "🔴"
        st.markdown(f"**Status:** {status_color} {'Online' if esp_state['online'] else 'Offline'}")
        
        # Network toggle
        if st.button("Toggle Network Status"):
            current_status = esp_state['online']
            send_command("set_online", not current_status)
            st.rerun()
        
        st.markdown("---")
        
        # Manual Commands
        st.subheader("Manual Commands")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start Irrigation", use_container_width=True):
                send_command(st.session_state.selected_device, "start_irrigation")
                st.rerun()
            
            if st.button("⏹️ Stop Irrigation", use_container_width=True):
                send_command(st.session_state.selected_device, "stop_irrigation")
                st.rerun()
        
        with col2:
            if st.button("🔄 Sync Data", use_container_width=True):
                send_command(st.session_state.selected_device, "sync")
                st.rerun()
            
            if st.button("🔃 Restart ESP", use_container_width=True):
                send_command(st.session_state.selected_device, "restart")
                st.rerun()
        
        # Zone-specific controls
        st.subheader("Zone Controls")
        selected_zone = st.selectbox("Select Zone", [1, 2, 3, 4])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Start Zone {selected_zone}"):
                send_command(st.session_state.selected_device, "start_zone", selected_zone)
                st.rerun()
        
        with col2:
            if st.button(f"Stop Zone {selected_zone}"):
                send_command(st.session_state.selected_device, "stop_zone", selected_zone)
                st.rerun()
        
        # Sensor value controls
        st.subheader("Set Sensor Values")
        
        sensor_type = st.selectbox("Sensor Type", ["temperature", "humidity", "soil_moisture", "light_level"])
        sensor_value = st.number_input(f"Set {sensor_type.replace('_', ' ').title()}", 
                                     min_value=0.0, max_value=100.0, value=25.0, step=0.1)
        
        if st.button(f"Set {sensor_type.replace('_', ' ').title()}"):
            send_command(st.session_state.selected_device, "set_sensor_value", 
                        {"sensor": sensor_type, "value": sensor_value})
            st.rerun()
        
        # Auto-refresh toggle
        st.markdown("---")
        auto_refresh = st.checkbox("Auto Refresh (10s)", value=True)
        
        if st.button("🔄 Manual Refresh"):
            st.rerun()
    
    # Main dashboard content
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("📊 Sensor Data")
        
        # Sensor metrics
        sensors = esp_state['sensors']
        
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(
                label="🌡️ Temperature",
                value=f"{sensors['temperature']:.1f}°C",
                delta=f"{sensors['temperature'] - 25:.1f}"
            )
            st.metric(
                label="💧 Soil Moisture",
                value=f"{sensors['soil_moisture']:.1f}%",
                delta=f"{sensors['soil_moisture'] - 50:.1f}"
            )
        
        with metric_col2:
            st.metric(
                label="💨 Humidity",
                value=f"{sensors['humidity']:.1f}%",
                delta=f"{sensors['humidity'] - 60:.1f}"
            )
            st.metric(
                label="🌞 Light Level",
                value=f"{sensors['light_level']:.0f} lux",
                delta=f"{sensors['light_level'] - 500:.0f}"
            )
        
        # Sensor chart
        if 'sensor_history' not in st.session_state:
            st.session_state.sensor_history = []
        
        # Add current reading to history
        current_time = datetime.now()
        st.session_state.sensor_history.append({
            'time': current_time,
            'temperature': sensors['temperature'],
            'humidity': sensors['humidity'],
            'soil_moisture': sensors['soil_moisture']
        })
        
        # Keep only last 20 readings
        if len(st.session_state.sensor_history) > 20:
            st.session_state.sensor_history = st.session_state.sensor_history[-20:]
        
        if len(st.session_state.sensor_history) > 1:
            st.line_chart(
                data={
                    'Temperature': [h['temperature'] for h in st.session_state.sensor_history],
                    'Humidity': [h['humidity'] for h in st.session_state.sensor_history],
                    'Soil Moisture': [h['soil_moisture'] for h in st.session_state.sensor_history]
                }
            )
    
    with col2:
        st.subheader("🚿 Zone Status")
        
        zones = esp_state['zones']
        for zone_id, zone_data in zones.items():
            status_icon = "🟢" if zone_data['active'] else "⚪"
            valve_icon = "🔓" if zone_data['valve_open'] else "🔒"
            
            with st.container():
                st.markdown(f"**Zone {zone_id}** {status_icon}")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"Valve: {valve_icon}")
                    st.write(f"Duration: {zone_data['duration_minutes']}min")
                with col_b:
                    st.write(f"Moisture: {zone_data['soil_moisture']:.1f}%")
                    st.write(f"Last Run: {zone_data['last_run']}")
                st.markdown("---")
        
        # Pump status
        st.subheader("⚙️ System Status")
        pump_icon = "🟢" if esp_state['pump']['active'] else "🔴"
        st.markdown(f"**Main Pump:** {pump_icon} {'Running' if esp_state['pump']['active'] else 'Stopped'}")
        st.write(f"Pressure: {esp_state['pump']['pressure']:.1f} PSI")
        st.write(f"Flow Rate: {esp_state['pump']['flow_rate']:.1f} L/min")
    
    with col3:
        st.subheader("📝 System Info")
        
        # Device info
        device_info = esp_state['device_info']
        st.write(f"**Device ID:** {device_info['device_id']}")
        st.write(f"**Firmware:** {device_info['firmware_version']}")
        st.write(f"**Uptime:** {device_info['uptime']}")
        st.write(f"**WiFi:** {device_info['wifi_strength']} dBm")
        st.write(f"**Memory:** {device_info['free_memory']} KB")
        
        # Last update
        st.markdown("---")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"**Connection:** ☁️ Cloud")
        st.write(f"**Connection:** ☁️ Cloud")
    
    # Command History
    st.subheader("📋 Command History")
    if st.session_state.command_history:
        # Show last 10 commands
        recent_commands = st.session_state.command_history[-10:]
        for cmd in reversed(recent_commands):
            device_info = f" [{cmd.get('device_id', 'Unknown')}]" if 'device_id' in cmd else ""
            with st.expander(f"{cmd['timestamp']} - {cmd['command']}{device_info}", expanded=False):
                st.json({
                    'device_id': cmd.get('device_id', 'Unknown'),
                    'command': cmd['command'],
                    'parameters': cmd['params'],
                    'result': cmd['result']
                })
    else:
        st.info("No commands sent yet.")
    
    # Auto-refresh logic for cloud (slower refresh) for cloud (slower refresh)
    if auto_refresh:
        time.sleep(2)  # Slower refresh for cloud
        st.rerun()

if __name__ == "__main__":
    main()