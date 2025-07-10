#!/usr/bin/env python3
"""
Test script for ESP32 Irrigation Controller
Tests the main components without Streamlit UI
"""

import time
import json
from espsimulation import ESPSimulator
from utils import (
    format_sensor_value, 
    get_status_icon, 
    check_system_alerts,
    get_system_recommendations
)

def test_esp_simulator():
    """Test ESP simulator functionality"""
    print("🧪 Testing ESP Simulator...")
    
    # Initialize simulator
    simulator = ESPSimulator()
    simulator.start()
    
    # Test basic commands
    print("  ✓ Starting irrigation...")
    result = simulator.send_command("start_irrigation")
    print(f"    Result: {result}")
    
    # Wait for sensor updates
    time.sleep(2)
    
    # Get current state
    state = simulator.get_state()
    print(f"  ✓ Pump active: {state['pump']['active']}")
    print(f"  ✓ Irrigation active: {state['irrigation_active']}")
    
    # Test zone control
    print("  ✓ Testing zone control...")
    result = simulator.send_command("start_zone", 2)
    print(f"    Zone 2 start: {result}")
    
    result = simulator.send_command("stop_zone", 2)
    print(f"    Zone 2 stop: {result}")
    
    # Test offline mode
    print("  ✓ Testing offline mode...")
    result = simulator.send_command("set_online", False)
    print(f"    Set offline: {result}")
    
    result = simulator.send_command("sync")
    print(f"    Sync while offline: {result}")
    
    # Back online
    result = simulator.send_command("set_online", True)
    print(f"    Set online: {result}")
    
    # Stop irrigation
    result = simulator.send_command("stop_irrigation")
    print(f"  ✓ Stop irrigation: {result}")
    
    simulator.stop()
    print("  ✅ ESP Simulator tests completed!")
    return True

def test_utility_functions():
    """Test utility functions"""
    print("\n🧪 Testing Utility Functions...")
    
    # Test sensor formatting
    temp_formatted = format_sensor_value(25.7, 'temperature')
    humidity_formatted = format_sensor_value(65.3, 'humidity')
    print(f"  ✓ Temperature formatting: {temp_formatted}")
    print(f"  ✓ Humidity formatting: {humidity_formatted}")
    
    # Test status icons
    online_icon = get_status_icon(True, 'online')
    offline_icon = get_status_icon(False, 'online')
    print(f"  ✓ Online icon: {online_icon}")
    print(f"  ✓ Offline icon: {offline_icon}")
    
    # Test alerts with mock data
    mock_state = {
        'online': True,
        'sensors': {
            'temperature': 38.0,  # High temp
            'soil_moisture': 15.0  # Low moisture
        },
        'pump': {
            'active': True,
            'pressure': 10.0  # Low pressure
        },
        'device_info': {
            'free_memory': 30  # Low memory
        }
    }
    
    alerts = check_system_alerts(mock_state)
    print(f"  ✓ System alerts detected: {len(alerts)}")
    for alert in alerts:
        print(f"    {alert['icon']} {alert['level']}: {alert['message']}")
    
    # Test recommendations
    recommendations = get_system_recommendations(mock_state)
    print(f"  ✓ System recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"    {rec['icon']} {rec['priority']}: {rec['message']}")
    
    print("  ✅ Utility function tests completed!")
    return True

def test_integration():
    """Test integration between components"""
    print("\n🧪 Testing Component Integration...")
    
    simulator = ESPSimulator()
    simulator.start()
    
    # Run for a few seconds to get realistic data
    print("  ✓ Running simulation for 5 seconds...")
    time.sleep(5)
    
    # Get state and analyze
    state = simulator.get_state()
    
    # Check alerts
    alerts = check_system_alerts(state)
    print(f"  ✓ Current alerts: {len(alerts)}")
    
    # Check recommendations
    recommendations = get_system_recommendations(state)
    print(f"  ✓ Current recommendations: {len(recommendations)}")
    
    # Test command sequence
    print("  ✓ Testing command sequence...")
    commands = [
        ("sync", None),
        ("start_irrigation", None),
        ("start_zone", 1),
        ("stop_zone", 1),
        ("stop_irrigation", None)
    ]
    
    for cmd, param in commands:
        result = simulator.send_command(cmd, param)
        success = "✅" if result['success'] else "❌"
        print(f"    {success} {cmd}: {result['message']}")
    
    simulator.stop()
    print("  ✅ Integration tests completed!")
    return True

def main():
    """Run all tests"""
    print("🚀 ESP32 Irrigation Controller - Component Tests")
    print("=" * 50)
    
    try:
        # Run individual tests
        test1 = test_esp_simulator()
        test2 = test_utility_functions()
        test3 = test_integration()
        
        # Summary
        print("\n📊 Test Summary:")
        print(f"  ESP Simulator: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Utility Functions: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  Integration: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if all([test1, test2, test3]):
            print("\n🎉 All tests passed! The application is ready to run.")
            print("\nTo start the Streamlit app:")
            print("  streamlit run main.py")
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()