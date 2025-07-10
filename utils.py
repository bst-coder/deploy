"""
Utility functions for the ESP32 Irrigation Controller
"""

import json
from datetime import datetime, timedelta
import random

def format_uptime(start_time):
    """Format uptime from start time to human readable string"""
    uptime_delta = datetime.now() - start_time
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

def generate_realistic_sensor_data(base_values=None, variation_ranges=None):
    """Generate realistic sensor data with variations"""
    if base_values is None:
        base_values = {
            'temperature': 25.0,
            'humidity': 60.0,
            'soil_moisture': 45.0,
            'light_level': 500.0
        }
    
    if variation_ranges is None:
        variation_ranges = {
            'temperature': (-0.5, 0.5),
            'humidity': (-2.0, 2.0),
            'soil_moisture': (-0.3, 0.3),
            'light_level': (-50, 50)
        }
    
    sensor_data = {}
    for sensor, base_value in base_values.items():
        min_var, max_var = variation_ranges[sensor]
        variation = random.uniform(min_var, max_var)
        sensor_data[sensor] = base_value + variation
    
    return sensor_data

def calculate_light_level_by_time():
    """Calculate realistic light level based on current time"""
    hour = datetime.now().hour
    
    if 6 <= hour <= 18:  # Daytime
        # Peak at noon (12), decrease towards morning/evening
        base_light = 800 - abs(hour - 12) * 50
    else:  # Nighttime
        base_light = 50
    
    # Add some random variation
    variation = random.uniform(-100, 100)
    light_level = base_light + variation
    
    return max(0, min(1000, light_level))

def validate_zone_id(zone_id, max_zones=4):
    """Validate zone ID is within acceptable range"""
    try:
        zone_num = int(zone_id)
        return 1 <= zone_num <= max_zones
    except (ValueError, TypeError):
        return False

def format_sensor_value(value, sensor_type):
    """Format sensor values for display"""
    formatters = {
        'temperature': lambda x: f"{x:.1f}°C",
        'humidity': lambda x: f"{x:.1f}%",
        'soil_moisture': lambda x: f"{x:.1f}%",
        'light_level': lambda x: f"{x:.0f} lux",
        'pressure': lambda x: f"{x:.1f} PSI",
        'flow_rate': lambda x: f"{x:.1f} L/min",
        'wifi_strength': lambda x: f"{x} dBm",
        'memory': lambda x: f"{x} KB"
    }
    
    formatter = formatters.get(sensor_type, lambda x: str(x))
    return formatter(value)

def get_status_icon(status, status_type='boolean'):
    """Get appropriate icon for different status types"""
    if status_type == 'boolean':
        return "🟢" if status else "🔴"
    elif status_type == 'online':
        return "🟢" if status else "🔴"
    elif status_type == 'valve':
        return "🔓" if status else "🔒"
    elif status_type == 'pump':
        return "🟢" if status else "⚪"
    else:
        return "❓"

def calculate_irrigation_efficiency(zones_data):
    """Calculate irrigation efficiency based on zone data"""
    if not zones_data:
        return 0.0
    
    total_moisture_increase = 0
    active_zones = 0
    
    for zone in zones_data.values():
        if zone.get('active', False):
            active_zones += 1
            # Simple efficiency calculation based on moisture level
            moisture = zone.get('soil_moisture', 0)
            if moisture > 70:
                total_moisture_increase += 1.0  # Excellent
            elif moisture > 50:
                total_moisture_increase += 0.8  # Good
            elif moisture > 30:
                total_moisture_increase += 0.6  # Fair
            else:
                total_moisture_increase += 0.3  # Poor
    
    if active_zones == 0:
        return 0.0
    
    return (total_moisture_increase / active_zones) * 100

def export_system_data(esp_state, format='json'):
    """Export system data in specified format"""
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'device_info': esp_state.get('device_info', {}),
        'sensors': esp_state.get('sensors', {}),
        'zones': esp_state.get('zones', {}),
        'pump': esp_state.get('pump', {}),
        'system_status': {
            'online': esp_state.get('online', False),
            'irrigation_active': esp_state.get('irrigation_active', False),
            'last_sync': esp_state.get('last_sync', '')
        }
    }
    
    if format.lower() == 'json':
        return json.dumps(export_data, indent=2)
    elif format.lower() == 'csv':
        # Simple CSV export for sensor data
        csv_lines = ['timestamp,sensor,value']
        timestamp = export_data['timestamp']
        
        for sensor, value in export_data['sensors'].items():
            csv_lines.append(f"{timestamp},{sensor},{value}")
        
        return '\n'.join(csv_lines)
    else:
        return str(export_data)

def check_system_alerts(esp_state):
    """Check for system alerts and warnings"""
    alerts = []
    
    if not esp_state.get('online', True):
        alerts.append({
            'level': 'error',
            'message': 'Device is offline',
            'icon': '🔴'
        })
    
    sensors = esp_state.get('sensors', {})
    
    # Temperature alerts
    temp = sensors.get('temperature', 25)
    if temp > 35:
        alerts.append({
            'level': 'warning',
            'message': f'High temperature: {temp:.1f}°C',
            'icon': '🌡️'
        })
    elif temp < 10:
        alerts.append({
            'level': 'warning',
            'message': f'Low temperature: {temp:.1f}°C',
            'icon': '🥶'
        })
    
    # Soil moisture alerts
    soil_moisture = sensors.get('soil_moisture', 50)
    if soil_moisture < 20:
        alerts.append({
            'level': 'warning',
            'message': f'Low soil moisture: {soil_moisture:.1f}%',
            'icon': '🏜️'
        })
    elif soil_moisture > 90:
        alerts.append({
            'level': 'info',
            'message': f'High soil moisture: {soil_moisture:.1f}%',
            'icon': '💧'
        })
    
    # Pump alerts
    pump = esp_state.get('pump', {})
    if pump.get('active', False):
        pressure = pump.get('pressure', 0)
        if pressure < 15:
            alerts.append({
                'level': 'error',
                'message': f'Low pump pressure: {pressure:.1f} PSI',
                'icon': '⚠️'
            })
        elif pressure > 45:
            alerts.append({
                'level': 'warning',
                'message': f'High pump pressure: {pressure:.1f} PSI',
                'icon': '⚠️'
            })
    
    # Memory alerts
    device_info = esp_state.get('device_info', {})
    free_memory = device_info.get('free_memory', 200)
    if free_memory < 50:
        alerts.append({
            'level': 'warning',
            'message': f'Low memory: {free_memory} KB',
            'icon': '💾'
        })
    
    return alerts

def get_system_recommendations(esp_state):
    """Get system optimization recommendations"""
    recommendations = []
    
    sensors = esp_state.get('sensors', {})
    zones = esp_state.get('zones', {})
    
    # Analyze soil moisture levels
    low_moisture_zones = []
    high_moisture_zones = []
    
    for zone_id, zone_data in zones.items():
        moisture = zone_data.get('soil_moisture', 50)
        if moisture < 30:
            low_moisture_zones.append(zone_id)
        elif moisture > 80:
            high_moisture_zones.append(zone_id)
    
    if low_moisture_zones:
        recommendations.append({
            'type': 'irrigation',
            'message': f"Consider watering zones: {', '.join(map(str, low_moisture_zones))}",
            'priority': 'high',
            'icon': '💧'
        })
    
    if high_moisture_zones:
        recommendations.append({
            'type': 'irrigation',
            'message': f"Zones {', '.join(map(str, high_moisture_zones))} may be overwatered",
            'priority': 'medium',
            'icon': '🚰'
        })
    
    # Weather-based recommendations
    temp = sensors.get('temperature', 25)
    humidity = sensors.get('humidity', 60)
    
    if temp > 30 and humidity < 40:
        recommendations.append({
            'type': 'schedule',
            'message': "Hot and dry conditions - consider increasing irrigation frequency",
            'priority': 'medium',
            'icon': '☀️'
        })
    
    if temp < 15:
        recommendations.append({
            'type': 'schedule',
            'message': "Cool weather - reduce irrigation frequency",
            'priority': 'low',
            'icon': '🌤️'
        })
    
    return recommendations

# Test functions
if __name__ == "__main__":
    # Test utility functions
    print("Testing utility functions...")
    
    # Test sensor data generation
    sensor_data = generate_realistic_sensor_data()
    print(f"Generated sensor data: {sensor_data}")
    
    # Test light level calculation
    light_level = calculate_light_level_by_time()
    print(f"Current light level: {light_level}")
    
    # Test formatting
    temp_formatted = format_sensor_value(25.7, 'temperature')
    print(f"Formatted temperature: {temp_formatted}")
    
    print("All tests completed successfully!")