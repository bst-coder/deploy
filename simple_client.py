#!/usr/bin/env python3
"""
Simple ESP32 Client that works with Streamlit's limitations
This version simulates a device by directly connecting to the device manager
"""

import time
import random
import threading
from datetime import datetime

# Import the device manager directly
from device_manager import device_manager

class SimpleESP32Client:
    def __init__(self, device_id=None):
        self.device_id = device_id or f"SIMPLE_ESP32_{random.randint(1000, 9999)}"
        self.running = False
        self.heartbeat_thread = None
        
        # Simulated sensor values
        self.sensors = {
            'temperature': 25.0,
            'humidity': 60.0,
            'soil_moisture': 45.0,
            'light_level': 500.0
        }
        
        print(f"Simple ESP32 Client initialized with Device ID: {self.device_id}")
    
    def register_device(self):
        """Register this device with the device manager"""
        try:
            device_info = {
                'device_id': self.device_id,
                'firmware_version': '1.2.3',
                'registered_at': datetime.now().isoformat(),
                'ip_address': 'localhost'
            }
            
            success = device_manager.register_device(self.device_id, device_info)
            
            if success:
                print(f"✅ Device {self.device_id} registered successfully")
                return True
            else:
                print(f"❌ Registration failed")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat with current sensor data"""
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
            
            # Update device state
            state_update = {
                'sensors': self.sensors.copy()
            }
            
            success = device_manager.update_device_state(self.device_id, state_update)
            
            if success:
                print(f"💓 Heartbeat sent - T:{self.sensors['temperature']:.1f}°C H:{self.sensors['humidity']:.1f}% SM:{self.sensors['soil_moisture']:.1f}%")
                return True
            else:
                print(f"❌ Heartbeat failed")
                return False
                
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
            return False
    
    def check_commands(self):
        """Check for pending commands"""
        try:
            commands = device_manager.get_device_commands(self.device_id)
            
            for command_data in commands:
                self.execute_command(command_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Check commands error: {e}")
            return False
    
    def execute_command(self, command_data):
        """Execute a command"""
        command = command_data.get('command')
        params = command_data.get('params')
        command_id = command_data.get('id')
        
        print(f"🔧 Executing command: {command} with params: {params}")
        
        try:
            if command == 'set_sensor_value':
                sensor_type = params.get('sensor')
                value = float(params.get('value'))
                
                if sensor_type in self.sensors:
                    old_value = self.sensors[sensor_type]
                    self.sensors[sensor_type] = value
                    print(f"   📊 {sensor_type}: {old_value:.1f} → {value:.1f}")
                    
                    # Update the device state immediately
                    state_update = {'sensors': self.sensors.copy()}
                    device_manager.update_device_state(self.device_id, state_update)
                    
                    result = {'success': True, 'message': f'{sensor_type} set to {value}'}
                else:
                    result = {'success': False, 'message': f'Unknown sensor: {sensor_type}'}
            
            elif command == 'start_irrigation':
                print("   🚿 Starting irrigation system")
                result = {'success': True, 'message': 'Irrigation started'}
            
            elif command == 'stop_irrigation':
                print("   ⏹️ Stopping irrigation system")
                result = {'success': True, 'message': 'Irrigation stopped'}
            
            elif command == 'start_zone':
                zone_id = int(params)
                print(f"   🌊 Starting zone {zone_id}")
                result = {'success': True, 'message': f'Zone {zone_id} started'}
            
            elif command == 'stop_zone':
                zone_id = int(params)
                print(f"   ⏸️ Stopping zone {zone_id}")
                result = {'success': True, 'message': f'Zone {zone_id} stopped'}
            
            else:
                result = {'success': False, 'message': f'Unknown command: {command}'}
            
            # Mark command as completed
            device_manager.mark_command_completed(self.device_id, command_id, result)
            print(f"   ✅ Command completed: {result.get('message')}")
        
        except Exception as e:
            result = {'success': False, 'message': f'Command execution error: {str(e)}'}
            device_manager.mark_command_completed(self.device_id, command_id, result)
            print(f"   ❌ Command failed: {str(e)}")
    
    def heartbeat_loop(self):
        """Background thread for sending heartbeats"""
        while self.running:
            try:
                self.send_heartbeat()
                self.check_commands()
                time.sleep(5)  # Send heartbeat every 5 seconds
            except Exception as e:
                print(f"❌ Heartbeat loop error: {e}")
                time.sleep(2)
    
    def start(self):
        """Start the ESP32 client"""
        print(f"\n🚀 Starting Simple ESP32 Client...")
        
        # Start device manager if not already started
        device_manager.start()
        
        # Register device
        if not self.register_device():
            print("❌ Failed to register device. Exiting.")
            return False
        
        # Start background thread
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        print(f"✅ Simple ESP32 Client started successfully!")
        print(f"📱 Device ID: {self.device_id}")
        print(f"\n💡 This device is now connected to the local device manager!")
        print(f"   - Open the Streamlit dashboard to see this device")
        print(f"   - Use the dashboard controls to send commands")
        print(f"\n📊 Current sensor values:")
        for sensor, value in self.sensors.items():
            print(f"   {sensor}: {value}")
        
        return True
    
    def stop(self):
        """Stop the ESP32 client"""
        print("\n🛑 Stopping Simple ESP32 Client...")
        self.running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        
        print("✅ Simple ESP32 Client stopped")
    
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
                    print(f"Running: {self.running}")
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
                                # Update device state
                                state_update = {'sensors': self.sensors.copy()}
                                device_manager.update_device_state(self.device_id, state_update)
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple ESP32 Client')
    parser.add_argument('--device-id', help='Device ID (auto-generated if not provided)')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Create client
    client = SimpleESP32Client(args.device_id)
    
    try:
        # Start client
        if client.start():
            if args.interactive:
                client.interactive_mode()
            else:
                print("\n⏳ Running... Press Ctrl+C to stop")
                print("💡 Open the Streamlit dashboard in your browser to see this device!")
                print("🌐 Dashboard: http://localhost:8501 (if running locally)")
                while True:
                    time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Received interrupt signal")
    
    finally:
        client.stop()

if __name__ == "__main__":
    main()