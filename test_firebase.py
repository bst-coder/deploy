#!/usr/bin/env python3
"""
Test script for Firebase integration
Run this to test your Firebase setup before deploying
"""

import json
import time
from datetime import datetime
from firebase_manager_real import firebase_device_manager

def test_firebase_connection():
    """Test basic Firebase connection"""
    print("🔥 Testing Firebase Connection...")
    
    try:
        # Start the manager
        firebase_device_manager.start()
        print("✅ Firebase manager started successfully")
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

def test_device_registration():
    """Test device registration"""
    print("\n📝 Testing Device Registration...")
    
    device_id = "TEST_ESP32_001"
    device_info = {
        "device_id": device_id,
        "firmware_version": "1.0.0",
        "device_type": "ESP32_Test",
        "ip_address": "192.168.1.100",
        "mac_address": "AA:BB:CC:DD:EE:FF"
    }
    
    try:
        result = firebase_device_manager.register_device(device_id, device_info)
        if result:
            print(f"✅ Device {device_id} registered successfully")
            return device_id
        else:
            print(f"❌ Device registration failed")
            return None
    except Exception as e:
        print(f"❌ Device registration error: {e}")
        return None

def test_state_update(device_id):
    """Test device state updates"""
    print(f"\n📊 Testing State Update for {device_id}...")
    
    state_update = {
        "sensors": {
            "temperature": 26.5,
            "humidity": 65.0,
            "soil_moisture": 42.0,
            "light_level": 750.0
        },
        "zones": {
            1: {"active": True, "valve_open": True},
            2: {"active": False, "valve_open": False}
        },
        "pump": {
            "active": True,
            "pressure": 2.5,
            "flow_rate": 15.0
        },
        "irrigation_active": True
    }
    
    try:
        result = firebase_device_manager.update_device_state(device_id, state_update)
        if result:
            print("✅ State update successful")
            return True
        else:
            print("❌ State update failed")
            return False
    except Exception as e:
        print(f"❌ State update error: {e}")
        return False

def test_command_sending(device_id):
    """Test sending commands to device"""
    print(f"\n🎯 Testing Command Sending to {device_id}...")
    
    commands_to_test = [
        ("start_irrigation", None),
        ("start_zone", 1),
        ("stop_zone", 1),
        ("sync", None),
        ("stop_irrigation", None)
    ]
    
    for command, params in commands_to_test:
        try:
            result = firebase_device_manager.send_command_to_device(device_id, command, params)
            if result.get('success'):
                print(f"✅ Command '{command}' sent successfully")
            else:
                print(f"❌ Command '{command}' failed: {result.get('message')}")
        except Exception as e:
            print(f"❌ Command '{command}' error: {e}")
        
        time.sleep(1)  # Small delay between commands

def test_device_retrieval(device_id):
    """Test retrieving device data"""
    print(f"\n📖 Testing Device Data Retrieval for {device_id}...")
    
    try:
        # Test getting specific device state
        device_state = firebase_device_manager.get_device_state(device_id)
        if device_state:
            print("✅ Device state retrieved successfully")
            print(f"   Connected: {device_state.get('connected')}")
            print(f"   Last Heartbeat: {device_state.get('last_heartbeat')}")
            print(f"   Temperature: {device_state.get('state', {}).get('sensors', {}).get('temperature')}°C")
        else:
            print("❌ Failed to retrieve device state")
        
        # Test getting all connected devices
        connected_devices = firebase_device_manager.get_connected_devices()
        print(f"✅ Found {len(connected_devices)} connected devices")
        for dev_id in connected_devices.keys():
            print(f"   - {dev_id}")
        
        return True
    except Exception as e:
        print(f"❌ Device retrieval error: {e}")
        return False

def test_command_retrieval(device_id):
    """Test retrieving commands for device"""
    print(f"\n📥 Testing Command Retrieval for {device_id}...")
    
    try:
        commands = firebase_device_manager.get_device_commands(device_id)
        print(f"✅ Retrieved {len(commands)} pending commands")
        
        for cmd in commands:
            print(f"   - {cmd.get('command')} (ID: {cmd.get('id')})")
            
            # Mark command as completed (simulate ESP32 response)
            result = {
                "success": True,
                "message": "Test command executed",
                "timestamp": datetime.now().isoformat()
            }
            firebase_device_manager.mark_command_completed(device_id, cmd.get('id'), result)
            print(f"     ✅ Marked as completed")
        
        return True
    except Exception as e:
        print(f"❌ Command retrieval error: {e}")
        return False

def test_cleanup(device_id):
    """Test cleanup operations"""
    print(f"\n🧹 Testing Cleanup for {device_id}...")
    
    try:
        # Disconnect device
        firebase_device_manager.disconnect_device(device_id)
        print("✅ Device disconnected")
        
        # Verify disconnection
        time.sleep(2)
        device_state = firebase_device_manager.get_device_state(device_id)
        if device_state and not device_state.get('connected'):
            print("✅ Device marked as disconnected")
        
        return True
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

def main():
    """Run all Firebase tests"""
    print("🔥 Firebase Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Connection
    if not test_firebase_connection():
        print("\n❌ Firebase connection failed. Check your configuration.")
        return
    
    # Test 2: Device Registration
    device_id = test_device_registration()
    if not device_id:
        print("\n❌ Device registration failed. Cannot continue tests.")
        return
    
    # Test 3: State Updates
    if not test_state_update(device_id):
        print("\n⚠️ State update failed, but continuing tests...")
    
    # Test 4: Command Sending
    test_command_sending(device_id)
    
    # Wait a moment for commands to be processed
    time.sleep(2)
    
    # Test 5: Data Retrieval
    if not test_device_retrieval(device_id):
        print("\n⚠️ Data retrieval failed, but continuing tests...")
    
    # Test 6: Command Retrieval
    if not test_command_retrieval(device_id):
        print("\n⚠️ Command retrieval failed, but continuing tests...")
    
    # Test 7: Cleanup
    test_cleanup(device_id)
    
    print("\n" + "=" * 50)
    print("🎉 Firebase test suite completed!")
    print("\nIf all tests passed, your Firebase setup is ready for deployment.")
    print("If some tests failed, check your Firebase configuration and try again.")

if __name__ == "__main__":
    main()