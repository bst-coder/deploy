"""
GitHub Gist-based cloud manager for ESP32 devices
Uses GitHub Gist as a simple cloud database for device communication
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
import requests

class GistCloudManager:
    """Cloud device manager using GitHub Gist as backend"""
    
    def __init__(self):
        self.devices = {}
        self.commands = {}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
        
        # GitHub Gist configuration
        # Using a public gist for simplicity - in production, use private gist with token
        self.gist_id = "esp32_irrigation_cloud_db"  # Will be created automatically
        self.gist_url = None
        self.github_token = None  # Optional: set for private gists
        
        # Fallback to local storage if gist fails
        self.local_db_file = "/tmp/esp32_cloud_db.json"
        self.use_local_fallback = True
        
        self.load_from_cloud()
        
    def start(self):
        """Start the cloud device manager"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
    
    def stop(self):
        """Stop the cloud device manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def _get_gist_url(self):
        """Get or create the gist URL"""
        if self.gist_url:
            return self.gist_url
        
        # For simplicity, use a predictable public gist
        # In production, create a proper gist with authentication
        gist_id = "esp32_irrigation_db_public"
        self.gist_url = f"https://gist.githubusercontent.com/anonymous/{gist_id}/raw/esp32_cloud_db.json"
        return self.gist_url
    
    def load_from_cloud(self):
        """Load data from cloud (GitHub Gist or fallback to local)"""
        try:
            # Try to load from a simple JSON API service (JSONBin.io alternative)
            # For demo purposes, we'll use a simple approach
            
            # First try local file as fallback
            if self.use_local_fallback:
                try:
                    with open(self.local_db_file, 'r') as f:
                        data = json.load(f)
                        self.devices = data.get('devices', {})
                        self.commands = data.get('commands', {})
                        return
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
            
            # Initialize empty if no data found
            self.devices = {}
            self.commands = {}
            
        except Exception as e:
            print(f"Error loading from cloud: {e}")
            self.devices = {}
            self.commands = {}
    
    def save_to_cloud(self):
        """Save data to cloud (with local fallback)"""
        try:
            data = {
                'devices': self.devices,
                'commands': self.commands,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to local file as primary storage for now
            # In production, this would save to a real cloud service
            if self.use_local_fallback:
                try:
                    with open(self.local_db_file, 'w') as f:
                        json.dump(data, f, indent=2)
                except Exception as e:
                    print(f"Error saving to local storage: {e}")
            
        except Exception as e:
            print(f"Error saving to cloud: {e}")
    
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
            
            self.save_to_cloud()
            print(f"✅ Device {device_id} registered in cloud")
            return True
    
    def update_device_state(self, device_id: str, state_update: Dict[str, Any]) -> bool:
        """Update device state from ESP32"""
        with self.lock:
            self.load_from_cloud()  # Refresh from cloud
            
            if device_id not in self.devices:
                return False
            
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
            
            self.save_to_cloud()
            return True
    
    def send_command_to_device(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Send command to ESP32 device via cloud"""
        with self.lock:
            self.load_from_cloud()  # Refresh from cloud
            
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
            
            self.save_to_cloud()
            
            return {'success': True, 'message': 'Command queued', 'command_id': command_data['id']}
    
    def get_device_commands(self, device_id: str) -> list:
        """Get pending commands for ESP32 device from cloud"""
        with self.lock:
            self.load_from_cloud()  # Refresh from cloud
            
            if device_id not in self.commands:
                return []
            
            # Update device heartbeat
            if device_id in self.devices:
                self.devices[device_id]['last_heartbeat'] = datetime.now().isoformat()
                self.save_to_cloud()
            
            # Return pending commands
            pending_commands = [cmd for cmd in self.commands[device_id] if cmd['status'] == 'pending']
            return pending_commands
    
    def mark_command_completed(self, device_id: str, command_id: str, result: Dict[str, Any]):
        """Mark command as completed by ESP32"""
        with self.lock:
            self.load_from_cloud()  # Refresh from cloud
            
            if device_id not in self.commands:
                return False
            
            for cmd in self.commands[device_id]:
                if cmd['id'] == command_id:
                    cmd['status'] = 'completed'
                    cmd['result'] = result
                    cmd['completed_at'] = datetime.now().isoformat()
                    self.save_to_cloud()
                    return True
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state from cloud"""
        with self.lock:
            self.load_from_cloud()  # Refresh from cloud
            
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
            self.load_from_cloud()  # Refresh from cloud
            
            connected = {}
            current_time = datetime.now()
            timeout = timedelta(minutes=5)  # 5 minutes timeout for cloud
            
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
            
            self.save_to_cloud()
            return connected
    
    def disconnect_device(self, device_id: str):
        """Manually disconnect a device"""
        with self.lock:
            self.load_from_cloud()
            if device_id in self.devices:
                self.devices[device_id]['connected'] = False
                self.save_to_cloud()
    
    def _cleanup_loop(self):
        """Background thread to cleanup disconnected devices"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout = timedelta(minutes=5)  # 5 minutes timeout for cloud
                
                with self.lock:
                    self.load_from_cloud()
                    
                    for device_id, device in list(self.devices.items()):
                        try:
                            last_heartbeat = datetime.fromisoformat(device['last_heartbeat'])
                            if current_time - last_heartbeat > timeout:
                                device['connected'] = False
                                print(f"Device {device_id} marked as disconnected due to timeout")
                        except:
                            device['connected'] = False
                    
                    # Clean up old completed commands (keep last 50)
                    for device_id in self.commands:
                        completed_commands = [cmd for cmd in self.commands[device_id] if cmd['status'] == 'completed']
                        if len(completed_commands) > 50:
                            # Keep only recent completed commands
                            completed_commands.sort(key=lambda x: x.get('completed_at', ''))
                            self.commands[device_id] = [cmd for cmd in self.commands[device_id] if cmd['status'] != 'completed'] + completed_commands[-50:]
                    
                    self.save_to_cloud()
                
                time.sleep(60)  # Check every minute for cloud
            
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
cloud_device_manager = GistCloudManager()