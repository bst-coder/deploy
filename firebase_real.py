"""
Real Firebase implementation for production use
Install: pip install firebase-admin
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase SDK not available. Install with: pip install firebase-admin")

class RealFirebaseManager:
    """Real Firebase-based device manager for production"""
    
    def __init__(self, firebase_config=None):
        self.firebase_config = firebase_config
        self.db_ref = None
        self.devices_ref = None
        self.commands_ref = None
        self.running = False
        self.cleanup_thread = None
        
        if FIREBASE_AVAILABLE and firebase_config:
            self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.firebase_config['service_account'])
                firebase_admin.initialize_app(cred, {
                    'databaseURL': self.firebase_config['database_url']
                })
            
            # Get database references
            self.db_ref = db.reference('/')
            self.devices_ref = db.reference('/devices')
            self.commands_ref = db.reference('/commands')
            
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            self.db_ref = None
    
    def start(self):
        """Start the Firebase device manager"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
    
    def stop(self):
        """Stop the Firebase device manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def register_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """Register a new ESP32 device in Firebase"""
        if not self.devices_ref:
            return False
        
        try:
            device_data = {
                'device_info': device_info,
                'last_heartbeat': datetime.now().isoformat(),
                'connected': True,
                'state': self._get_default_state(device_id),
                'session_id': str(uuid.uuid4())
            }
            
            self.devices_ref.child(device_id).set(device_data)
            
            # Initialize command queue
            self.commands_ref.child(device_id).set([])
            
            return True
            
        except Exception as e:
            print(f"Firebase register error: {e}")
            return False
    
    def update_device_state(self, device_id: str, state_update: Dict[str, Any]) -> bool:
        """Update device state in Firebase"""
        if not self.devices_ref:
            return False
        
        try:
            device_ref = self.devices_ref.child(device_id)
            
            # Update heartbeat and connection status
            device_ref.child('last_heartbeat').set(datetime.now().isoformat())
            device_ref.child('connected').set(True)
            
            # Update state fields
            state_ref = device_ref.child('state')
            
            if 'sensors' in state_update:
                for sensor, value in state_update['sensors'].items():
                    state_ref.child('sensors').child(sensor).set(value)
            
            if 'zones' in state_update:
                for zone_id, zone_data in state_update['zones'].items():
                    state_ref.child('zones').child(str(zone_id)).update(zone_data)
            
            if 'pump' in state_update:
                state_ref.child('pump').update(state_update['pump'])
            
            if 'irrigation_active' in state_update:
                state_ref.child('irrigation_active').set(state_update['irrigation_active'])
            
            state_ref.child('last_sync').set(datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            print(f"Firebase update error: {e}")
            return False
    
    def send_command_to_device(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Send command to ESP32 device via Firebase"""
        if not self.commands_ref:
            return {'success': False, 'message': 'Firebase not available'}
        
        try:
            # Check if device exists
            device_data = self.devices_ref.child(device_id).get()
            if not device_data or not device_data.get('connected'):
                return {'success': False, 'message': 'Device not found or offline'}
            
            # Create command
            command_data = {
                'id': str(uuid.uuid4()),
                'command': command,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # Add to command queue
            commands_ref = self.commands_ref.child(device_id)
            commands_ref.push(command_data)
            
            return {'success': True, 'message': 'Command queued', 'command_id': command_data['id']}
            
        except Exception as e:
            print(f"Firebase send command error: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_device_commands(self, device_id: str) -> list:
        """Get pending commands for ESP32 device from Firebase"""
        if not self.commands_ref:
            return []
        
        try:
            # Update device heartbeat
            self.devices_ref.child(device_id).child('last_heartbeat').set(datetime.now().isoformat())
            
            # Get commands
            commands_data = self.commands_ref.child(device_id).get()
            if not commands_data:
                return []
            
            # Filter pending commands
            pending_commands = []
            for cmd_key, cmd_data in commands_data.items():
                if cmd_data.get('status') == 'pending':
                    cmd_data['firebase_key'] = cmd_key
                    pending_commands.append(cmd_data)
            
            return pending_commands
            
        except Exception as e:
            print(f"Firebase get commands error: {e}")
            return []
    
    def mark_command_completed(self, device_id: str, command_id: str, result: Dict[str, Any]):
        """Mark command as completed in Firebase"""
        if not self.commands_ref:
            return False
        
        try:
            commands_data = self.commands_ref.child(device_id).get()
            if not commands_data:
                return False
            
            # Find and update command
            for cmd_key, cmd_data in commands_data.items():
                if cmd_data.get('id') == command_id:
                    self.commands_ref.child(device_id).child(cmd_key).update({
                        'status': 'completed',
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    })
                    return True
            
            return False
            
        except Exception as e:
            print(f"Firebase mark completed error: {e}")
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state from Firebase"""
        if not self.devices_ref:
            return None
        
        try:
            device_data = self.devices_ref.child(device_id).get()
            if not device_data:
                return None
            
            return {
                'device_info': device_data.get('device_info', {}),
                'connected': device_data.get('connected', False),
                'last_heartbeat': device_data.get('last_heartbeat', ''),
                'state': device_data.get('state', {})
            }
            
        except Exception as e:
            print(f"Firebase get state error: {e}")
            return None
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all connected devices from Firebase"""
        if not self.devices_ref:
            return {}
        
        try:
            all_devices = self.devices_ref.get()
            if not all_devices:
                return {}
            
            connected = {}
            current_time = datetime.now()
            timeout = timedelta(minutes=5)
            
            for device_id, device_data in all_devices.items():
                try:
                    last_heartbeat = datetime.fromisoformat(device_data.get('last_heartbeat', ''))
                    if current_time - last_heartbeat < timeout:
                        device_data['connected'] = True
                        connected[device_id] = {
                            'device_info': device_data.get('device_info', {}),
                            'last_heartbeat': device_data.get('last_heartbeat', ''),
                            'state': device_data.get('state', {})
                        }
                    else:
                        # Mark as disconnected
                        self.devices_ref.child(device_id).child('connected').set(False)
                except:
                    continue
            
            return connected
            
        except Exception as e:
            print(f"Firebase get connected devices error: {e}")
            return {}
    
    def _cleanup_loop(self):
        """Background cleanup for Firebase"""
        while self.running:
            try:
                if self.commands_ref:
                    # Clean up old completed commands
                    all_commands = self.commands_ref.get()
                    if all_commands:
                        for device_id, commands in all_commands.items():
                            if isinstance(commands, dict):
                                completed_count = sum(1 for cmd in commands.values() 
                                                    if cmd.get('status') == 'completed')
                                
                                if completed_count > 50:
                                    # Remove oldest completed commands
                                    completed_commands = [(k, v) for k, v in commands.items() 
                                                        if v.get('status') == 'completed']
                                    completed_commands.sort(key=lambda x: x[1].get('completed_at', ''))
                                    
                                    # Remove oldest 25 completed commands
                                    for cmd_key, _ in completed_commands[:25]:
                                        self.commands_ref.child(device_id).child(cmd_key).delete()
                
                time.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                print(f"Firebase cleanup error: {e}")
                time.sleep(60)
    
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

# Example Firebase configuration
FIREBASE_CONFIG_EXAMPLE = {
    "service_account": "path/to/serviceAccountKey.json",
    "database_url": "https://your-project-default-rtdb.firebaseio.com/"
}

# Create instance (will use file-based simulation if Firebase not available)
real_firebase_manager = RealFirebaseManager()