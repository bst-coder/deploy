#!/usr/bin/env python3
"""
Cloud ESP32 Client
This script simulates an ESP32 device connecting through cloud database
Works with any cloud deployment (Firebase, etc.)
"""

import time
import random
import threading
from datetime import datetime
import argparse
import sys
import json
import os

# Import the cloud device manager directly
from firebase_manager import cloud_device_manager

class CloudESP32Client:
    def __init__(self, device_id=None):
        self.device_id = device_id or f"CLOUD_ESP32_{random.randint(1000, 9999)}"
        self.running = False
        self.heartbeat_thread = None
        self.command_thread = None
        
        # Simulated sensor values
        self.sensors = {
            'temperature': 25.0,
            'humidity': 60.0,
            'soil_moisture': 45.0,
            'light_level': 500.0
        }
        
        # Device state
        self.state = {
            'irrigation_active': False,
            'pump_active': False,
            'pump_pressure': 0.0,
            'pump_flow_rate': 0.0,
            'zones': {
                1: {'active': False, 'valve_open': False},
                2: {'active': False, 'valve_open': False},
                3: {'active': False, 'valve_open': False},
                4: {'active': False, 'valve_open': False}
            }
        }
        
        print(f"Cloud ESP32 Client initialized with Device ID: {self.device_id}")
        print(f"Communication: ☁️ Cloud Database")
    
    def register_device(self):
        """Register this device with the cloud"""
        try:
            device_info = {
                'device_id': self.device_id,
                'firmware_version': '1.2.3-cloud',
                'registered_at': datetime.now().isoformat(),
                'ip_address': 'cloud-connected',
                'connection_type': 'cloud'
            }
            
            success = cloud_device_manager.register_device(self.device_id, device_info)
            
            if success:
                print(f"✅ Device {self.device_id} registered successfully in cloud")
                return True
            else:
                print(f"❌ Cloud registration failed")
                return False
                
        except Exception as e:
            print(f"❌ Cloud registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat with current sensor data to cloud"""
        try:
            # Add some random variation to sensors
            self.sensors['temperature'] += random.uniform(-0.5, 0.5)
            self.sensors['humidity'] += random.uniform(-1.0, 1.0)
            self.sensors['soil_moisture'] += random.uniform(-0.3, 0.3)
            self.sensors['light_level'] += random.uniform(-50, 50)
            
            # Keep values in realistic ranges
            self.sensors['temperature'] = max(15.0, min(40.0, self.sensors['temperature']))
            self.sensors['humidity'] = max(20.0, min(90.0, self.sensors['humidity']))
            self.sensors['soil_moisture'] = max(0.0, min(100.0, self.sensors['soil_moisture']))
            self.sensors['light_level'] = max(0.0, min(1000.0, self.sensors['light_level']))
            
            # Update cloud with sensor data
            state_update = {
                'sensors': self.sensors.copy(),
                'pump': {
                    'active': self.state['pump_active'],
                    'pressure': self.state['pump_pressure'],
                    'flow_rate': self.state['pump_flow_rate']
                },
                'irrigation_active': self.state['irrigation_active'],
                'zones': self.state['zones'].copy()
            }
            
            success = cloud_device_manager.update_device_state(self.device_id, state_update)
            
            if success:
                print(f"☁️ Cloud heartbeat sent - T:{self.sensors['temperature']:.1f}°C H:{self.sensors['humidity']:.1f}% SM:{self.sensors['soil_moisture']:.1f}%")
                return True
            else:
                print(f"❌ Cloud heartbeat failed")
                return False
                
        except Exception as e:
            print(f"❌ Cloud heartbeat error: {e}")
            return False
    
    def get_commands(self):
        """Get pending commands from cloud"""
        try:
            commands = cloud_device_manager.get_device_commands(self.device_id)
            return commands
            
        except Exception as e:
            print(f"❌ Get cloud commands error: {e}")
            return []
    
    def execute_command(self, command_data):
        """Execute a command and return result"""
        command = command_data.get('command')
        params = command_data.get('params')
        command_id = command_data.get('id')
        
        print(f"☁️ Executing cloud command: {command} with params: {params}")
        
        try:
            if command == 'set_sensor_value':
                sensor_type = params.get('sensor')
                value = float(params.get('value'))
                
                if sensor_type in self.sensors:
                    old_value = self.sensors[sensor_type]
                    self.sensors[sensor_type] = value
                    print(f"   📊 {sensor_type}: {old_value:.1f} → {value:.1f}")
                    return {'success': True, 'message': f'{sensor_type} set to {value}'}
                else:
                    return {'success': False, 'message': f'Unknown sensor: {sensor_type}'}
            
            elif command == 'start_irrigation':
                self.state['irrigation_active'] = True
                self.state['pump_active'] = True
                self.state['pump_pressure'] = 30.0
                self.state['pump_flow_rate'] = 20.0
                
                for zone_id in self.state['zones']:
                    self.state['zones'][zone_id]['active'] = True
                    self.state['zones'][zone_id]['valve_open'] = True
                
                print("   🚿 Irrigation system started")
                return {'success': True, 'message': 'Irrigation started'}
            
            elif command == 'stop_irrigation':
                self.state['irrigation_active'] = False
                self.state['pump_active'] = False
                self.state['pump_pressure'] = 0.0
                self.state['pump_flow_rate'] = 0.0
                
                for zone_id in self.state['zones']:
                    self.state['zones'][zone_id]['active'] = False
                    self.state['zones'][zone_id]['valve_open'] = False
                
                print("   ⏹️ Irrigation system stopped")
                return {'success': True, 'message': 'Irrigation stopped'}
            
            elif command == 'start_zone':
                zone_id = int(params)
                if zone_id in self.state['zones']:
                    self.state['zones'][zone_id]['active'] = True
                    self.state['zones'][zone_id]['valve_open'] = True
                    
                    if not self.state['pump_active']:
                        self.state['pump_active'] = True
                        self.state['pump_pressure'] = 25.0
                        self.state['pump_flow_rate'] = 15.0
                    
                    print(f"   🌊 Zone {zone_id} started")
                    return {'success': True, 'message': f'Zone {zone_id} started'}
                else:
                    return {'success': False, 'message': f'Zone {zone_id} not found'}
            
            elif command == 'stop_zone':
                zone_id = int(params)
                if zone_id in self.state['zones']:
                    self.state['zones'][zone_id]['active'] = False
                    self.state['zones'][zone_id]['valve_open'] = False
                    
                    # Check if any zones are still active
                    active_zones = any(z['active'] for z in self.state['zones'].values())
                    if not active_zones:
                        self.state['pump_active'] = False
                        self.state['pump_pressure'] = 0.0
                        self.state['pump_flow_rate'] = 0.0
                        self.state['irrigation_active'] = False
                    
                    print(f"   ⏸️ Zone {zone_id} stopped")
                    return {'success': True, 'message': f'Zone {zone_id} stopped'}
                else:
                    return {'success': False, 'message': f'Zone {zone_id} not found'}
            
            else:
                return {'success': False, 'message': f'Unknown command: {command}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Command execution error: {str(e)}'}
    
    def send_command_result(self, command_id, result):
        """Send command execution result back to cloud"""
        try:
            cloud_device_manager.mark_command_completed(self.device_id, command_id, result)
            print(f"   ✅ Cloud command result sent: {result.get('message')}")
            return True
                
        except Exception as e:
            print(f"   ❌ Cloud command result error: {e}")
            return False
    
    def heartbeat_loop(self):
        """Background thread for sending heartbeats to cloud"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(10)  # Send heartbeat every 10 seconds for cloud
            except Exception as e:
                print(f"❌ Cloud heartbeat loop error: {e}")
                time.sleep(5)
    
    def command_loop(self):
        """Background thread for checking and executing commands from cloud"""
        while self.running:
            try:
                commands = self.get_commands()
                
                for command_data in commands:
                    result = self.execute_command(command_data)
                    self.send_command_result(command_data['id'], result)
                
                time.sleep(5)  # Check for commands every 5 seconds
            except Exception as e:
                print(f"❌ Cloud command loop error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the cloud ESP32 client"""
        print(f"\n🚀 Starting Cloud ESP32 Client...")
        
        # Start cloud device manager
        cloud_device_manager.start()
        
        # Register device
        if not self.register_device():
            print("❌ Failed to register device in cloud. Exiting.")
            return False
        
        # Start background threads
        self.running = True
        
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        self.command_thread = threading.Thread(target=self.command_loop, daemon=True)
        self.command_thread.start()
        
        print(f"✅ Cloud ESP32 Client started successfully!")
        print(f"📱 Device ID: {self.device_id}")
        print(f"☁️ Communication: Cloud Database")
        print(f"\n💡 You can now control this device from the cloud dashboard!")
        print(f"   - Set sensor values")
        print(f"   - Start/stop irrigation")
        print(f"   - Control individual zones")
        print(f"\n📊 Current sensor values:")
        for sensor, value in self.sensors.items():
            print(f"   {sensor}: {value}")
        
        return True
    
    def stop(self):
        """Stop the cloud ESP32 client"""
        print("\n🛑 Stopping Cloud ESP32 Client...")
        self.running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        
        if self.command_thread:
            self.command_thread.join(timeout=2)
        
        print("✅ Cloud ESP32 Client stopped")
    
    def interactive_mode(self):
        """Interactive mode for manual control"""
        print(f"\n🎮 Interactive Mode - Device: {self.device_id}")
        print("Commands:")
        print("  status - Show current status")
        print("  set <sensor> <value> - Set sensor value")
        print("  quit - Exit")
        
        while self.running:
            try:
                command = input("\n> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'status':
                    print(f"\n📊 Current Status:")
                    print(f"Device ID: {self.device_id}")
                    print(f"Irrigation Active: {self.state['irrigation_active']}")
                    print(f"Pump Active: {self.state['pump_active']}")
                    print(f"Sensors:")
                    for sensor, value in self.sensors.items():
                        print(f"  {sensor}: {value:.1f}")
                elif command.startswith('set '):
                    parts = command.split()
                    if len(parts) == 3:
                        sensor = parts[1]
                        try:
                            value = float(parts[2])
                            if sensor in self.sensors:
                                self.sensors[sensor] = value
                                print(f"✅ {sensor} set to {value}")
                            else:
                                print(f"❌ Unknown sensor: {sensor}")
                        except ValueError:
                            print("❌ Invalid value. Use a number.")
                    else:
                        print("❌ Usage: set <sensor> <value>")
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break

def main():
    parser = argparse.ArgumentParser(description='Cloud ESP32 Client')
    parser.add_argument('--device-id', help='Device ID (auto-generated if not provided)')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Create client
    client = CloudESP32Client(args.device_id)
    
    try:
        # Start client
        if client.start():
            if args.interactive:
                client.interactive_mode()
            else:
                print("\n⏳ Running... Press Ctrl+C to stop")
                print("💡 Open the cloud dashboard to see this device!")
                print("☁️ Dashboard: https://esp32-irrigation-controller.streamlit.app/")
                while True:
                    time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Received interrupt signal")
    
    finally:
        client.stop()

if __name__ == "__main__":
    main()