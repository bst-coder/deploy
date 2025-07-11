"""
API-based cloud manager for ESP32 devices
Uses a simple REST API for cloud communication that works with Streamlit Cloud
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
import requests
import os

class APICloudManager:
    """Cloud device manager using REST API backend"""
    
    def __init__(self):
        self.devices = {}
        self.commands = {}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
        
        # Use a simple JSON storage API (JSONBin.io free tier)
        self.api_url = "https://api.jsonbin.io/v3/b/67a0f8e5e41b4d34e4749b8e"
        self.api_key = "$2a$10$YourAPIKeyHere"  # Replace with actual key
        
        # Headers for API requests
        self.headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': self.api_key
        } if self.api_key != "$2a$10$YourAPIKeyHere" else {'Content-Type': 'application/json'}
        
        # Use local fallback for demo
        self.use_local_fallback = True
        self.local_file = "/tmp/esp32_api_db.json"
        
        self.load_from_api()
        
    def start(self):
        """Start the cloud device manager"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            print("🌐 API Cloud Manager started")
    
    def stop(self):
        """Stop the cloud device manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def load_from_api(self):
        """Load data from API or local fallback"""
        try:
            # Try API first (if configured)
            if not self.use_local_fallback and self.api_key != "$2a$10$YourAPIKeyHere":
                response = requests.get(f"{self.api_url}/latest", headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'record' in data:
                        record = data['record']
                        self.devices = record.get('devices', {})
                        self.commands = record.get('commands', {})
                        return
            
            # Use local file as fallback
            try:
                with open(self.local_file, 'r') as f:
                    data = json.load(f)
                    self.devices = data.get('devices', {})
                    self.commands = data.get('commands', {})
                    return
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Initialize empty if no data found
            self.devices = {}
            self.commands = {}
            print("📡 API storage initialized (empty)")
            
        except Exception as e:
            print(f"Error loading from API: {e}")
            self.devices = {}
            self.commands = {}
    
    def save_to_api(self):
        """Save data to API or local fallback"""
        try:
            data = {
                'devices': self.devices,
                'commands': self.commands,
                'last_updated': datetime.now().isoformat()
            }
            
            # Try API first (if configured)
            if not self.use_local_fallback and self.api_key != "$2a$10$YourAPIKeyHere":
                response = requests.put(self.api_url, json=data, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    return
            
            # Save to local file as fallback
            try:
                with open(self.local_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving to local file: {e}")
            
        except Exception as e:
            print(f"Error saving to API: {e}")
    
    def register_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """Register a new ESP32 device"""
        with self.lock:
            self.devices[device_id] = {
                'device_info': device_info,
                'last_heartbeat': datetime.now().isoformat(),
                'connected': True,
                'state': self._get_default_state(device_id),
                'session_id': str(uuid.uuid4())
            }
            
            # Initialize command queue for this device
            if device_id not in self.commands:
                self.commands[device_id] = []
            
            self.save_to_api()
            print(f"✅ Device {device_id} registered in API cloud")
            return True
    
    def update_device_state(self, device_id: str, state_update: Dict[str, Any]) -> bool:
        """Update device state from ESP32"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            if device_id not in self.devices:
                # Auto-register device if not found
                self.register_device(device_id, {
                    'device_id': device_id,
                    'auto_registered': True,
                    'registered_at': datetime.now().isoformat()
                })
            
            device = self.devices[device_id]
            device['last_heartbeat'] = datetime.now().isoformat()
            device['connected'] = True
            
            # Update state
            if 'sensors' in state_update:
                device['state']['sensors'].update(state_update['sensors'])
            if 'zones' in state_update:
                device['state']['zones'].update(state_update['zones'])
            if 'pump' in state_update:
                device['state']['pump'].update(state_update['pump'])
            if 'irrigation_active' in state_update:
                device['state']['irrigation_active'] = state_update['irrigation_active']
            
            device['state']['last_sync'] = datetime.now().isoformat()
            
            self.save_to_api()
            return True
    
    def send_command_to_device(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Send command to ESP32 device via cloud"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            if device_id not in self.devices:
                return {'success': False, 'message': 'Device not found'}
            
            device = self.devices[device_id]
            if not device['connected']:
                return {'success': False, 'message': 'Device is offline'}
            
            # Add command to cloud queue
            command_data = {
                'id': str(uuid.uuid4()),
                'command': command,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            if device_id not in self.commands:
                self.commands[device_id] = []
            
            self.commands[device_id].append(command_data)
            
            self.save_to_api()
            
            return {'success': True, 'message': 'Command queued', 'command_id': command_data['id']}
    
    def get_device_commands(self, device_id: str) -> list:
        """Get pending commands for ESP32 device from cloud"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            if device_id not in self.commands:
                return []
            
            # Update device heartbeat
            if device_id in self.devices:
                self.devices[device_id]['last_heartbeat'] = datetime.now().isoformat()
                self.save_to_api()
            
            # Return pending commands
            pending_commands = [cmd for cmd in self.commands[device_id] if cmd['status'] == 'pending']
            return pending_commands
    
    def mark_command_completed(self, device_id: str, command_id: str, result: Dict[str, Any]):
        """Mark command as completed by ESP32"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            if device_id not in self.commands:
                return False
            
            for cmd in self.commands[device_id]:
                if cmd['id'] == command_id:
                    cmd['status'] = 'completed'
                    cmd['result'] = result
                    cmd['completed_at'] = datetime.now().isoformat()
                    self.save_to_api()
                    return True
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state from cloud"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            if device_id not in self.devices:
                return None
            
            device = self.devices[device_id]
            return {
                'device_info': device['device_info'],
                'connected': device['connected'],
                'last_heartbeat': device['last_heartbeat'],
                'state': device['state'].copy()
            }
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all connected devices from cloud"""
        with self.lock:
            self.load_from_api()  # Refresh from cloud
            
            connected = {}
            current_time = datetime.now()
            timeout = timedelta(minutes=2)  # 2 minutes timeout
            
            for device_id, device in self.devices.items():
                try:
                    last_heartbeat = datetime.fromisoformat(device['last_heartbeat'])
                    if current_time - last_heartbeat < timeout:
                        device['connected'] = True
                        connected[device_id] = {
                            'device_info': device['device_info'],
                            'last_heartbeat': device['last_heartbeat'],
                            'state': device['state'].copy()
                        }
                    else:
                        device['connected'] = False
                except:
                    # Handle invalid datetime format
                    device['connected'] = False
            
            self.save_to_api()
            return connected
    
    def disconnect_device(self, device_id: str):
        """Manually disconnect a device"""
        with self.lock:
            self.load_from_api()
            if device_id in self.devices:
                self.devices[device_id]['connected'] = False
                self.save_to_api()
    
    def _cleanup_loop(self):
        """Background thread to cleanup disconnected devices"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout = timedelta(minutes=2)  # 2 minutes timeout
                
                with self.lock:
                    self.load_from_api()
                    
                    for device_id, device in list(self.devices.items()):
                        try:
                            last_heartbeat = datetime.fromisoformat(device['last_heartbeat'])
                            if current_time - last_heartbeat > timeout:
                                device['connected'] = False
                                print(f"Device {device_id} marked as disconnected due to timeout")
                        except:
                            device['connected'] = False
                    
                    # Clean up old completed commands (keep last 20)
                    for device_id in self.commands:
                        completed_commands = [cmd for cmd in self.commands[device_id] if cmd['status'] == 'completed']
                        if len(completed_commands) > 20:
                            # Keep only recent completed commands
                            completed_commands.sort(key=lambda x: x.get('completed_at', ''))
                            self.commands[device_id] = [cmd for cmd in self.commands[device_id] if cmd['status'] != 'completed'] + completed_commands[-20:]
                    
                    self.save_to_api()
                
                time.sleep(30)  # Check every 30 seconds
            
            except Exception as e:
                print(f"Cleanup error: {e}")
                time.sleep(30)
    
    def _get_default_state(self, device_id: str) -> Dict[str, Any]:
        """Get default state for a new device"""
        return {
            'online': True,
            'device_info': {
                'device_id': device_id,
                'firmware_version': '1.0.0',
                'uptime': '0d 0h 0m',
                'wifi_strength': -45,
                'free_memory': 234
            },
            'sensors': {
                'temperature': 25.0,
                'humidity': 60.0,
                'soil_moisture': 45.0,
                'light_level': 500.0
            },
            'zones': {
                1: {
                    'active': False,
                    'valve_open': False,
                    'duration_minutes': 15,
                    'soil_moisture': 45.0,
                    'last_run': 'Never'
                },
                2: {
                    'active': False,
                    'valve_open': False,
                    'duration_minutes': 20,
                    'soil_moisture': 38.0,
                    'last_run': 'Never'
                },
                3: {
                    'active': False,
                    'valve_open': False,
                    'duration_minutes': 10,
                    'soil_moisture': 52.0,
                    'last_run': 'Never'
                },
                4: {
                    'active': False,
                    'valve_open': False,
                    'duration_minutes': 25,
                    'soil_moisture': 41.0,
                    'last_run': 'Never'
                }
            },
            'pump': {
                'active': False,
                'pressure': 0.0,
                'flow_rate': 0.0
            },
            'irrigation_active': False,
            'last_sync': datetime.now().isoformat()
        }

# Global cloud device manager instance
cloud_device_manager = APICloudManager()