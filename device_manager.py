import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid

class DeviceManager:
    """Manages ESP32 device connections and state"""
    
    def __init__(self):
        self.devices = {}  # device_id -> device_data
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
        
    def start(self):
        """Start the device manager"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
    
    def stop(self):
        """Stop the device manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def register_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """Register a new ESP32 device"""
        with self.lock:
            self.devices[device_id] = {
                'device_info': device_info,
                'last_heartbeat': datetime.now(),
                'connected': True,
                'state': self._get_default_state(device_id),
                'command_queue': [],
                'session_id': str(uuid.uuid4())
            }
            return True
    
    def update_device_state(self, device_id: str, state_update: Dict[str, Any]) -> bool:
        """Update device state from ESP32"""
        with self.lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            device['last_heartbeat'] = datetime.now()
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
            return True
    
    def send_command_to_device(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Send command to ESP32 device"""
        with self.lock:
            if device_id not in self.devices:
                return {'success': False, 'message': 'Device not found'}
            
            device = self.devices[device_id]
            if not device['connected']:
                return {'success': False, 'message': 'Device is offline'}
            
            # Add command to queue
            command_data = {
                'id': str(uuid.uuid4()),
                'command': command,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            device['command_queue'].append(command_data)
            
            # For simulation purposes, process command immediately
            # In real implementation, ESP32 would poll for commands
            return self._process_command_simulation(device_id, command, params)
    
    def get_device_commands(self, device_id: str) -> list:
        """Get pending commands for ESP32 device"""
        with self.lock:
            if device_id not in self.devices:
                return []
            
            device = self.devices[device_id]
            device['last_heartbeat'] = datetime.now()
            
            # Return pending commands
            pending_commands = [cmd for cmd in device['command_queue'] if cmd['status'] == 'pending']
            return pending_commands
    
    def mark_command_completed(self, device_id: str, command_id: str, result: Dict[str, Any]):
        """Mark command as completed by ESP32"""
        with self.lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            for cmd in device['command_queue']:
                if cmd['id'] == command_id:
                    cmd['status'] = 'completed'
                    cmd['result'] = result
                    cmd['completed_at'] = datetime.now().isoformat()
                    return True
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current device state"""
        with self.lock:
            if device_id not in self.devices:
                return None
            
            device = self.devices[device_id]
            return {
                'device_info': device['device_info'],
                'connected': device['connected'],
                'last_heartbeat': device['last_heartbeat'].isoformat(),
                'state': device['state'].copy()
            }
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all connected devices"""
        with self.lock:
            connected = {}
            for device_id, device in self.devices.items():
                if device['connected']:
                    connected[device_id] = {
                        'device_info': device['device_info'],
                        'last_heartbeat': device['last_heartbeat'].isoformat(),
                        'state': device['state'].copy()
                    }
            return connected
    
    def disconnect_device(self, device_id: str):
        """Manually disconnect a device"""
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id]['connected'] = False
    
    def _cleanup_loop(self):
        """Background thread to cleanup disconnected devices"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout = timedelta(minutes=2)  # 2 minutes timeout
                
                with self.lock:
                    for device_id, device in list(self.devices.items()):
                        if current_time - device['last_heartbeat'] > timeout:
                            device['connected'] = False
                            print(f"Device {device_id} marked as disconnected due to timeout")
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Cleanup error: {e}")
                time.sleep(5)
    
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
    
    def _process_command_simulation(self, device_id: str, command: str, params: Any = None) -> Dict[str, Any]:
        """Process command for simulation (will be removed when real ESP32 is used)"""
        device = self.devices[device_id]
        state = device['state']
        
        try:
            if command == 'set_sensor_value':
                sensor_type = params.get('sensor')
                value = params.get('value')
                if sensor_type in state['sensors']:
                    state['sensors'][sensor_type] = float(value)
                    return {'success': True, 'message': f'{sensor_type} set to {value}'}
                else:
                    return {'success': False, 'message': f'Unknown sensor: {sensor_type}'}
            
            elif command == 'start_irrigation':
                if state['irrigation_active']:
                    return {'success': False, 'message': 'Irrigation already active'}
                
                state['irrigation_active'] = True
                state['pump']['active'] = True
                state['pump']['pressure'] = 30.0
                state['pump']['flow_rate'] = 20.0
                
                for zone_id in state['zones']:
                    state['zones'][zone_id]['active'] = True
                    state['zones'][zone_id]['valve_open'] = True
                    state['zones'][zone_id]['last_run'] = datetime.now().strftime('%H:%M:%S')
                
                return {'success': True, 'message': 'Irrigation started successfully'}
            
            elif command == 'stop_irrigation':
                state['irrigation_active'] = False
                state['pump']['active'] = False
                state['pump']['pressure'] = 0.0
                state['pump']['flow_rate'] = 0.0
                
                for zone_id in state['zones']:
                    state['zones'][zone_id]['active'] = False
                    state['zones'][zone_id]['valve_open'] = False
                
                return {'success': True, 'message': 'Irrigation stopped successfully'}
            
            elif command == 'start_zone':
                zone_id = params
                if zone_id not in state['zones']:
                    return {'success': False, 'message': f'Zone {zone_id} not found'}
                
                zone = state['zones'][zone_id]
                if zone['active']:
                    return {'success': False, 'message': f'Zone {zone_id} already active'}
                
                zone['active'] = True
                zone['valve_open'] = True
                zone['last_run'] = datetime.now().strftime('%H:%M:%S')
                
                if not state['pump']['active']:
                    state['pump']['active'] = True
                    state['pump']['pressure'] = 30.0
                    state['pump']['flow_rate'] = 15.0
                
                return {'success': True, 'message': f'Zone {zone_id} started successfully'}
            
            elif command == 'stop_zone':
                zone_id = params
                if zone_id not in state['zones']:
                    return {'success': False, 'message': f'Zone {zone_id} not found'}
                
                zone = state['zones'][zone_id]
                zone['active'] = False
                zone['valve_open'] = False
                
                # Check if any zones are still active
                active_zones = any(z['active'] for z in state['zones'].values())
                if not active_zones:
                    state['pump']['active'] = False
                    state['pump']['pressure'] = 0.0
                    state['pump']['flow_rate'] = 0.0
                    state['irrigation_active'] = False
                
                return {'success': True, 'message': f'Zone {zone_id} stopped successfully'}
            
            else:
                return {'success': False, 'message': f'Unknown command: {command}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Command error: {str(e)}'}

# Global device manager instance
device_manager = DeviceManager()