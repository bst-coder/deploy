import threading
import time
import random
from datetime import datetime, timedelta
import json

class ESPSimulator:
    """Simulates an ESP32 device for irrigation control"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Device state
        self.state = {
            'online': True,
            'device_info': {
                'device_id': 'ESP32_IRR_001',
                'firmware_version': '1.2.3',
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
        
        self.start_time = datetime.now()
        self.command_queue = []
    
    def start(self):
        """Start the ESP simulation thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the ESP simulation"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def get_state(self):
        """Get current device state (thread-safe)"""
        with self.lock:
            return json.loads(json.dumps(self.state))  # Deep copy
    
    def send_command(self, command, params=None):
        """Send command to ESP simulator"""
        with self.lock:
            result = self._process_command(command, params)
            return result
    
    def _process_command(self, command, params=None):
        """Process incoming commands"""
        try:
            if not self.state['online'] and command != 'set_online':
                return {'success': False, 'message': 'Device is offline'}
            
            if command == 'start_irrigation':
                return self._start_irrigation()
            elif command == 'stop_irrigation':
                return self._stop_irrigation()
            elif command == 'start_zone':
                return self._start_zone(params)
            elif command == 'stop_zone':
                return self._stop_zone(params)
            elif command == 'sync':
                return self._sync_data()
            elif command == 'restart':
                return self._restart_device()
            elif command == 'set_online':
                return self._set_online_status(params)
            else:
                return {'success': False, 'message': f'Unknown command: {command}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Command error: {str(e)}'}
    
    def _start_irrigation(self):
        """Start irrigation system"""
        if self.state['irrigation_active']:
            return {'success': False, 'message': 'Irrigation already active'}
        
        self.state['irrigation_active'] = True
        self.state['pump']['active'] = True
        self.state['pump']['pressure'] = random.uniform(25.0, 35.0)
        self.state['pump']['flow_rate'] = random.uniform(15.0, 25.0)
        
        # Start all zones
        for zone_id in self.state['zones']:
            self.state['zones'][zone_id]['active'] = True
            self.state['zones'][zone_id]['valve_open'] = True
            self.state['zones'][zone_id]['last_run'] = datetime.now().strftime('%H:%M:%S')
        
        return {'success': True, 'message': 'Irrigation started successfully'}
    
    def _stop_irrigation(self):
        """Stop irrigation system"""
        self.state['irrigation_active'] = False
        self.state['pump']['active'] = False
        self.state['pump']['pressure'] = 0.0
        self.state['pump']['flow_rate'] = 0.0
        
        # Stop all zones
        for zone_id in self.state['zones']:
            self.state['zones'][zone_id]['active'] = False
            self.state['zones'][zone_id]['valve_open'] = False
        
        return {'success': True, 'message': 'Irrigation stopped successfully'}
    
    def _start_zone(self, zone_id):
        """Start specific zone"""
        if zone_id not in self.state['zones']:
            return {'success': False, 'message': f'Zone {zone_id} not found'}
        
        zone = self.state['zones'][zone_id]
        if zone['active']:
            return {'success': False, 'message': f'Zone {zone_id} already active'}
        
        zone['active'] = True
        zone['valve_open'] = True
        zone['last_run'] = datetime.now().strftime('%H:%M:%S')
        
        # Start pump if not already running
        if not self.state['pump']['active']:
            self.state['pump']['active'] = True
            self.state['pump']['pressure'] = random.uniform(25.0, 35.0)
            self.state['pump']['flow_rate'] = random.uniform(8.0, 15.0)
        
        return {'success': True, 'message': f'Zone {zone_id} started successfully'}
    
    def _stop_zone(self, zone_id):
        """Stop specific zone"""
        if zone_id not in self.state['zones']:
            return {'success': False, 'message': f'Zone {zone_id} not found'}
        
        zone = self.state['zones'][zone_id]
        zone['active'] = False
        zone['valve_open'] = False
        
        # Check if any zones are still active
        active_zones = any(z['active'] for z in self.state['zones'].values())
        if not active_zones:
            self.state['pump']['active'] = False
            self.state['pump']['pressure'] = 0.0
            self.state['pump']['flow_rate'] = 0.0
            self.state['irrigation_active'] = False
        
        return {'success': True, 'message': f'Zone {zone_id} stopped successfully'}
    
    def _sync_data(self):
        """Sync device data"""
        self.state['last_sync'] = datetime.now().isoformat()
        return {'success': True, 'message': 'Data synchronized successfully'}
    
    def _restart_device(self):
        """Restart device simulation"""
        # Stop all irrigation
        self._stop_irrigation()
        
        # Reset some values
        self.start_time = datetime.now()
        self.state['device_info']['uptime'] = '0d 0h 0m'
        self.state['device_info']['free_memory'] = random.randint(200, 250)
        
        return {'success': True, 'message': 'Device restarted successfully'}
    
    def _set_online_status(self, online):
        """Set device online/offline status"""
        self.state['online'] = bool(online)
        status = 'online' if online else 'offline'
        
        if not online:
            # When going offline, stop irrigation
            self._stop_irrigation()
        
        return {'success': True, 'message': f'Device is now {status}'}
    
    def _simulation_loop(self):
        """Main simulation loop running in background thread"""
        while self.running:
            try:
                with self.lock:
                    self._update_sensors()
                    self._update_device_info()
                    self._simulate_irrigation_effects()
                
                time.sleep(5)  # Update every 5 seconds
            
            except Exception as e:
                print(f"Simulation error: {e}")
                time.sleep(1)
    
    def _update_sensors(self):
        """Update sensor readings with realistic variations"""
        if not self.state['online']:
            return
        
        sensors = self.state['sensors']
        
        # Temperature variation (20-35°C)
        sensors['temperature'] += random.uniform(-0.5, 0.5)
        sensors['temperature'] = max(20.0, min(35.0, sensors['temperature']))
        
        # Humidity variation (30-90%)
        sensors['humidity'] += random.uniform(-2.0, 2.0)
        sensors['humidity'] = max(30.0, min(90.0, sensors['humidity']))
        
        # Light level variation (0-1000 lux)
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Daytime
            base_light = 800 - abs(hour - 12) * 50
        else:  # Nighttime
            base_light = 50
        
        sensors['light_level'] = base_light + random.uniform(-100, 100)
        sensors['light_level'] = max(0, min(1000, sensors['light_level']))
        
        # Soil moisture - affected by irrigation
        for zone_id, zone in self.state['zones'].items():
            if zone['active']:
                # Increase moisture when irrigating
                zone['soil_moisture'] += random.uniform(0.5, 1.5)
                zone['soil_moisture'] = min(100.0, zone['soil_moisture'])
            else:
                # Gradual decrease when not irrigating
                zone['soil_moisture'] -= random.uniform(0.1, 0.3)
                zone['soil_moisture'] = max(0.0, zone['soil_moisture'])
        
        # Update main soil moisture sensor (average of zones)
        avg_moisture = sum(z['soil_moisture'] for z in self.state['zones'].values()) / len(self.state['zones'])
        sensors['soil_moisture'] = avg_moisture
    
    def _update_device_info(self):
        """Update device information"""
        if not self.state['online']:
            return
        
        # Update uptime
        uptime_delta = datetime.now() - self.start_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        self.state['device_info']['uptime'] = f"{days}d {hours}h {minutes}m"
        
        # Simulate WiFi strength variation
        self.state['device_info']['wifi_strength'] += random.randint(-5, 5)
        self.state['device_info']['wifi_strength'] = max(-80, min(-30, self.state['device_info']['wifi_strength']))
        
        # Simulate memory usage variation
        self.state['device_info']['free_memory'] += random.randint(-10, 10)
        self.state['device_info']['free_memory'] = max(100, min(300, self.state['device_info']['free_memory']))
    
    def _simulate_irrigation_effects(self):
        """Simulate effects of irrigation on pump and system"""
        if not self.state['online']:
            return
        
        if self.state['pump']['active']:
            # Simulate pressure and flow variations
            self.state['pump']['pressure'] += random.uniform(-1.0, 1.0)
            self.state['pump']['pressure'] = max(20.0, min(40.0, self.state['pump']['pressure']))
            
            self.state['pump']['flow_rate'] += random.uniform(-0.5, 0.5)
            self.state['pump']['flow_rate'] = max(5.0, min(30.0, self.state['pump']['flow_rate']))
        
        # Auto-stop zones after their duration (simplified simulation)
        current_time = datetime.now()
        for zone_id, zone in self.state['zones'].items():
            if zone['active'] and zone['last_run'] != 'Never':
                try:
                    last_run_time = datetime.strptime(zone['last_run'], '%H:%M:%S').time()
                    last_run_datetime = datetime.combine(current_time.date(), last_run_time)
                    
                    # If zone has been running for more than its duration, stop it
                    if (current_time - last_run_datetime).total_seconds() > zone['duration_minutes'] * 60:
                        self._stop_zone(zone_id)
                except:
                    pass  # Handle time parsing errors gracefully

# Test function for standalone testing
if __name__ == "__main__":
    simulator = ESPSimulator()
    simulator.start()
    
    print("ESP32 Simulator started. Testing commands...")
    
    # Test commands
    print(simulator.send_command("sync"))
    print(simulator.send_command("start_irrigation"))
    time.sleep(2)
    print(simulator.get_state()['pump'])
    print(simulator.send_command("stop_irrigation"))
    
    simulator.stop()
    print("Test completed.")