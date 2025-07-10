"""
Real Firebase-based device manager for cloud deployment
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
import os

try:
    import firebase_admin
    from firebase_admin import credentials, db
    import pyrebase
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase libraries not installed. Using local simulation.")

class FirebaseDeviceManager:
    """Real Firebase-based device manager"""
    
    def __init__(self, config_file="firebase-config.json", service_account_file="firebase-service-account.json"):
        self.firebase_available = FIREBASE_AVAILABLE
        self.running = False
        self.cleanup_thread = None
        
        if self.firebase_available:
            self._initialize_firebase(config_file, service_account_file)
        else:
            # Fallback to local simulation
            from firebase_manager import CloudDeviceManager
            self.fallback_manager = CloudDeviceManager()
    
    def _initialize_firebase(self, config_file, service_account_file):
        """Initialize Firebase connection"""
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_file)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': self._get_database_url(config_file)
                })
            
            # Initialize Pyrebase for real-time features
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.firebase = pyrebase.initialize_app(config)
            self.db_ref = db.reference()
            self.realtime_db = self.firebase.database()
            
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            self.firebase_available = False
            from firebase_manager import CloudDeviceManager
            self.fallback_manager = CloudDeviceManager()
    
    def _get_database_url(self, config_file):
        """Extract database URL from config"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return config.get('databaseURL', '')
        except:
            return ''
    
    def start(self):
        """Start the Firebase device manager"""
        if not self.firebase_available:
            return self.fallback_manager.start()
        
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            print("🚀 Firebase Device Manager started")
    
    def stop(self):
        """Stop the Firebase device manager"""
        if not self.firebase_available:
            return self.fallback_manager.stop()
        
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def register_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """Register a new ESP32 device in Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.register_device(device_id, device_info)
        
        try:
            device_data = {
                'device_info': device_info,
                'last_heartbeat': datetime.now().isoformat(),
                'connected': True,
                'state': self._get_default_state(device_id),
                'session_id': str(uuid.uuid4()),
                'registered_at': datetime.now().isoformat()
            }
            
            # Write to Firebase
            self.db_ref.child('devices').child(device_id).set(device_data)
            
            # Initialize command queue
            self.db_ref.child('commands').child(device_id).set([])
            
            print(f"✅ Device {device_id} registered in Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error registering device {device_id}: {e}")
            return False
    
    def update_device_state(self, device_id: str, state_update: Dict[str, Any]) -> bool:
        """Update device state in Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.update_device_state(device_id, state_update)
        
        try:
            # Update heartbeat and connection status
            updates = {
                f'devices/{device_id}/last_heartbeat': datetime.now().isoformat(),
                f'devices/{device_id}/connected': True,
                f'devices/{device_id}/state/last_sync': datetime.now().isoformat()
            }
            
            # Update specific state fields
            if 'sensors' in state_update:
                for sensor, value in state_update['sensors'].items():
                    updates[f'devices/{device_id}/state/sensors/{sensor}'] = value
            
            if 'zones' in state_update:
                for zone_id, zone_data in state_update['zones'].items():
                    for key, value in zone_data.items():
                        updates[f'devices/{device_id}/state/zones/{zone_id}/{key}'] = value
            
            if 'pump' in state_update:
                for key, value in state_update['pump'].items():
                    updates[f'devices/{device_id}/state/pump/{key}'] = value
            
            if 'irrigation_active' in state_update:
                updates[f'devices/{device_id}/state/irrigation_active'] = state_update['irrigation_active']
            
            # Batch update to Firebase
            self.db_ref.update(updates)
            return True
            
        except Exception as e:
            print(f"❌ Error updating device state for {device_id}: {e}")
            return False
    
    def send_command_to_device(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Send command to ESP32 device via Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.send_command_to_device(device_id, command, params)
        
        try:
            # Check if device exists and is connected
            device_ref = self.db_ref.child('devices').child(device_id)
            device_data = device_ref.get()
            
            if not device_data:
                return {'success': False, 'message': 'Device not found'}
            
            if not device_data.get('connected', False):
                return {'success': False, 'message': 'Device is offline'}
            
            # Create command
            command_data = {
                'id': str(uuid.uuid4()),
                'command': command,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # Add command to Firebase queue
            commands_ref = self.db_ref.child('commands').child(device_id)
            commands_ref.push(command_data)
            
            print(f"📤 Command '{command}' sent to device {device_id}")
            return {'success': True, 'message': 'Command queued', 'command_id': command_data['id']}
            
        except Exception as e:
            print(f"❌ Error sending command to {device_id}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_device_commands(self, device_id: str) -> list:
        """Get pending commands for ESP32 device from Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.get_device_commands(device_id)
        
        try:
            # Update device heartbeat
            self.db_ref.child('devices').child(device_id).child('last_heartbeat').set(
                datetime.now().isoformat()
            )
            
            # Get pending commands
            commands_ref = self.db_ref.child('commands').child(device_id)
            commands_data = commands_ref.get() or {}
            
            pending_commands = []
            for cmd_key, cmd_data in commands_data.items():
                if cmd_data.get('status') == 'pending':
                    cmd_data['firebase_key'] = cmd_key
                    pending_commands.append(cmd_data)
            
            return pending_commands
            
        except Exception as e:
            print(f"❌ Error getting commands for {device_id}: {e}")
            return []
    
    def mark_command_completed(self, device_id: str, command_id: str, result: Dict[str, Any]):
        """Mark command as completed in Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.mark_command_completed(device_id, command_id, result)
        
        try:
            commands_ref = self.db_ref.child('commands').child(device_id)
            commands_data = commands_ref.get() or {}
            
            for cmd_key, cmd_data in commands_data.items():
                if cmd_data.get('id') == command_id:
                    # Update command status
                    commands_ref.child(cmd_key).update({
                        'status': 'completed',
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    })
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error marking command completed for {device_id}: {e}")
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state from Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.get_device_state(device_id)
        
        try:
            device_ref = self.db_ref.child('devices').child(device_id)
            device_data = device_ref.get()
            
            if not device_data:
                return None
            
            return {
                'device_info': device_data.get('device_info', {}),
                'connected': device_data.get('connected', False),
                'last_heartbeat': device_data.get('last_heartbeat', ''),
                'state': device_data.get('state', {})
            }
            
        except Exception as e:
            print(f"❌ Error getting device state for {device_id}: {e}")
            return None
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all connected devices from Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.get_connected_devices()
        
        try:
            devices_ref = self.db_ref.child('devices')
            devices_data = devices_ref.get() or {}
            
            connected = {}
            current_time = datetime.now()
            timeout = timedelta(minutes=5)
            
            for device_id, device_data in devices_data.items():
                try:
                    last_heartbeat = datetime.fromisoformat(device_data.get('last_heartbeat', ''))
                    is_connected = current_time - last_heartbeat < timeout
                    
                    # Update connection status in Firebase
                    if device_data.get('connected') != is_connected:
                        devices_ref.child(device_id).child('connected').set(is_connected)
                    
                    if is_connected:
                        connected[device_id] = {
                            'device_info': device_data.get('device_info', {}),
                            'last_heartbeat': device_data.get('last_heartbeat', ''),
                            'state': device_data.get('state', {})
                        }
                except:
                    continue
            
            return connected
            
        except Exception as e:
            print(f"❌ Error getting connected devices: {e}")
            return {}
    
    def disconnect_device(self, device_id: str):
        """Manually disconnect a device in Firebase"""
        if not self.firebase_available:
            return self.fallback_manager.disconnect_device(device_id)
        
        try:
            self.db_ref.child('devices').child(device_id).child('connected').set(False)
            print(f"🔌 Device {device_id} disconnected")
        except Exception as e:
            print(f"❌ Error disconnecting device {device_id}: {e}")
    
    def _cleanup_loop(self):
        """Background thread to cleanup disconnected devices and old commands"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout = timedelta(minutes=5)
                
                # Get all devices
                devices_data = self.db_ref.child('devices').get() or {}
                
                for device_id, device_data in devices_data.items():
                    try:
                        last_heartbeat = datetime.fromisoformat(device_data.get('last_heartbeat', ''))
                        if current_time - last_heartbeat > timeout:
                            # Mark as disconnected
                            self.db_ref.child('devices').child(device_id).child('connected').set(False)
                            print(f"🔌 Device {device_id} marked as disconnected due to timeout")
                    except:
                        continue
                
                # Clean up old completed commands (keep last 50 per device)
                commands_data = self.db_ref.child('commands').get() or {}
                for device_id, device_commands in commands_data.items():
                    if isinstance(device_commands, dict):
                        completed_commands = []
                        for cmd_key, cmd_data in device_commands.items():
                            if cmd_data.get('status') == 'completed':
                                completed_commands.append((cmd_key, cmd_data.get('completed_at', '')))
                        
                        if len(completed_commands) > 50:
                            # Sort by completion time and remove oldest
                            completed_commands.sort(key=lambda x: x[1])
                            for cmd_key, _ in completed_commands[:-50]:
                                self.db_ref.child('commands').child(device_id).child(cmd_key).delete()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
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
                1: {'active': False, 'valve_open': False, 'duration_minutes': 15, 'soil_moisture': 45.0, 'last_run': 'Never'},
                2: {'active': False, 'valve_open': False, 'duration_minutes': 20, 'soil_moisture': 38.0, 'last_run': 'Never'},
                3: {'active': False, 'valve_open': False, 'duration_minutes': 10, 'soil_moisture': 52.0, 'last_run': 'Never'},
                4: {'active': False, 'valve_open': False, 'duration_minutes': 25, 'soil_moisture': 41.0, 'last_run': 'Never'}
            },
            'pump': {
                'active': False,
                'pressure': 0.0,
                'flow_rate': 0.0
            },
            'irrigation_active': False,
            'last_sync': datetime.now().isoformat()
        }

# Global Firebase device manager instance
firebase_device_manager = FirebaseDeviceManager()