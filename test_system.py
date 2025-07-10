#!/usr/bin/env python3
"""
Test script to verify the ESP32 connection system works
"""

import time
import threading
from device_manager import device_manager

def test_device_manager():
    """Test the device manager functionality"""
    print("🧪 Testing Device Manager...")
    
    # Start device manager
    device_manager.start()
    
    # Test device registration
    device_id = "TEST_ESP32_001"
    device_info = {
        'device_id': device_id,
        'firmware_version': '1.0.0',
        'ip_address': '192.168.1.100'
    }
    
    success = device_manager.register_device(device_id, device_info)
    print(f"✅ Device registration: {'SUCCESS' if success else 'FAILED'}")
    
    # Test state update
    state_update = {
        'sensors': {
            'temperature': 26.5,
            'humidity': 65.0
        }
    }
    
    success = device_manager.update_device_state(device_id, state_update)
    print(f"✅ State update: {'SUCCESS' if success else 'FAILED'}")
    
    # Test command sending
    result = device_manager.send_command_to_device(device_id, "start_irrigation")
    print(f"✅ Command sending: {'SUCCESS' if result.get('success') else 'FAILED'}")
    print(f"   Result: {result.get('message')}")
    
    # Test getting connected devices
    devices = device_manager.get_connected_devices()
    print(f"✅ Connected devices: {len(devices)} device(s)")
    
    if device_id in devices:
        device_data = devices[device_id]
        print(f"   Device {device_id}:")
        print(f"   - Temperature: {device_data['state']['sensors']['temperature']}°C")
        print(f"   - Humidity: {device_data['state']['sensors']['humidity']}%")
        print(f"   - Irrigation: {device_data['state']['irrigation_active']}")
    
    # Test sensor value command
    result = device_manager.send_command_to_device(device_id, "set_sensor_value", 
                                                  {"sensor": "temperature", "value": 30.0})
    print(f"✅ Sensor value command: {'SUCCESS' if result.get('success') else 'FAILED'}")
    
    # Get updated state
    device_state = device_manager.get_device_state(device_id)
    if device_state:
        temp = device_state['state']['sensors']['temperature']
        print(f"   Updated temperature: {temp}°C")
    
    # Stop device manager
    device_manager.stop()
    print("✅ Device manager test completed")

if __name__ == "__main__":
    print("🚀 Starting ESP32 System Test\n")
    test_device_manager()
    print("\n✅ All tests completed!")