import streamlit as st
import time
import threading
from datetime import datetime
import json
from espsimulation import ESPSimulator

# Configure Streamlit page
st.set_page_config(
    page_title="ESP32 Irrigation Controller",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ESP simulator in session state
if 'esp_simulator' not in st.session_state:
    st.session_state.esp_simulator = ESPSimulator()
    st.session_state.esp_simulator.start()

# Initialize other session state variables
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

if 'command_history' not in st.session_state:
    st.session_state.command_history = []

def send_command(command, params=None):
    """Send command to ESP simulator and log it"""
    result = st.session_state.esp_simulator.send_command(command, params)
    st.session_state.command_history.append({
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'command': command,
        'params': params,
        'result': result
    })
    return result

def main():
    st.title("🌱 ESP32 Irrigation Controller Dashboard")
    st.markdown("---")
    
    # Get current ESP state
    esp_state = st.session_state.esp_simulator.get_state()
    
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
                send_command("start_irrigation")
                st.rerun()
            
            if st.button("⏹️ Stop Irrigation", use_container_width=True):
                send_command("stop_irrigation")
                st.rerun()
        
        with col2:
            if st.button("🔄 Sync Data", use_container_width=True):
                send_command("sync")
                st.rerun()
            
            if st.button("🔃 Restart ESP", use_container_width=True):
                send_command("restart")
                st.rerun()
        
        # Zone-specific controls
        st.subheader("Zone Controls")
        selected_zone = st.selectbox("Select Zone", [1, 2, 3, 4])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Start Zone {selected_zone}"):
                send_command("start_zone", selected_zone)
                st.rerun()
        
        with col2:
            if st.button(f"Stop Zone {selected_zone}"):
                send_command("stop_zone", selected_zone)
                st.rerun()
        
        # Auto-refresh toggle
        st.markdown("---")
        auto_refresh = st.checkbox("Auto Refresh (5s)", value=True)
        
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
    
    # Command History
    st.subheader("📋 Command History")
    if st.session_state.command_history:
        # Show last 10 commands
        recent_commands = st.session_state.command_history[-10:]
        for cmd in reversed(recent_commands):
            with st.expander(f"{cmd['timestamp']} - {cmd['command']}", expanded=False):
                st.json({
                    'command': cmd['command'],
                    'parameters': cmd['params'],
                    'result': cmd['result']
                })
    else:
        st.info("No commands sent yet.")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent too frequent updates
        st.rerun()

if __name__ == "__main__":
    main()