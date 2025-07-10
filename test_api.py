#!/usr/bin/env python3
"""
Test API endpoints directly
"""

import requests
import time

def test_api_endpoints():
    base_url = "https://deploy-esp-connection.streamlit.app"
    device_id = "TEST_API_DEVICE"
    
    print("🧪 Testing API endpoints...")
    
    # Test registration
    print("\n1. Testing device registration...")
    url = f"{base_url}/?api=register&device_id={device_id}&firmware=1.0.0"
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test heartbeat
    print("\n2. Testing heartbeat...")
    url = f"{base_url}/?api=heartbeat&device_id={device_id}&temperature=25.5&humidity=60.0&soil_moisture=45.0"
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test get commands
    print("\n3. Testing get commands...")
    url = f"{base_url}/?api=get_commands&device_id={device_id}"
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()