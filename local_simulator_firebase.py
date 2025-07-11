#!/usr/bin/env python3
"""
Local ESP32 Simulator that stores data in Firebase
This simulates an ESP32 device but stores all data in Firebase Realtime Database
"""

import time
import threading
from datetime import datetime
import json
from firebase_manager_real import firebase_device_manager
from espsimulation import ESPSimulator

class FirebaseESPSimulator:
    """ESP32 Simulator that stores data in Firebase"""
    
    def __init__(self, device_id="ESP32_SIMULATOR_001"):
        self.device_id = device_id
        self.esp_simulator = ESPSimulator()
        self.running = False
        self.update_thread = None
        self.command_thread = None
        
        # Device info
        self.device_info = {
            "device_id": self.device_id,
            "firmware_version": "1.0.0-SIM",
            "device_type": "ESP32_Simulator",
            "ip_address": "127.0.0.1",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "location": "Local Simulation"
        }
        
        print(f"🔥 Firebase ESP32 Simulator initialized: {self.device_id}")
    
    def start(self):
        """Start the Firebase ESP32 simulator"""
        if self.running:
            print("⚠️ Simulator already running")
            return
        
        print(f"🚀 Starting Firebase ESP32 Simulator: {self.device_id}")
        
        # Start Firebase manager
        firebase_device_manager.start()
        
        # Start ESP simulator
        self.esp_simulator.start()
        
        # Register device in Firebase
        self.register_device()
        
        # Start background threads
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.command_thread = threading.Thread(target=self._command_loop, daemon=True)
        
        self.update_thread.start()
        self.command_thread.start()
        
        print(f"✅ Firebase ESP32 Simulator started successfully!")
        print(f"📊 Device will send data to Firebase every 10 seconds")
        print(f"🎯 Device will check for commands every 5 seconds")
    
    def stop(self):
        """Stop the Firebase ESP32 simulator"""
        print(f"⏹️ Stopping Firebase ESP32 Simulator: {self.device_id}")
        
        self.running = False
        self.esp_simulator.stop()
        
        # Disconnect from Firebase
        firebase_device_manager.disconnect_device(self.device_id)
        
        if self.update_thread:
            self.update_thread.join()
        if self.command_thread:
            self.command_thread.join()
        
        print(f"✅ Firebase ESP32 Simulator stopped")
    
    def register_device(self):
        """Register device in Firebase"""
        print(f"📝 Registering device {self.device_id} in Firebase...")
        
        result = firebase_device_manager.register_device(self.device_id, self.device_info)
        if result:
            print(f"✅ Device {self.device_id} registered successfully in Firebase")
        else:
            print(f"❌ Failed to register device {self.device_id} in Firebase")
        
        return result
    
    def _update_loop(self):
        """Background thread to send data to Firebase"""
        while self.running:
            try:
                # Get current ESP state
                esp_state = self.esp_simulator.get_state()
                
                # Prepare state update for Firebase
                state_update = {
                    "sensors": esp_state["sensors"],
                    "zones": esp_state["zones"],
                    "pump": esp_state["pump"],
                    "irrigation_active": esp_state["irrigation_active"]
                }
                
                # Send to Firebase
                result = firebase_device_manager.update_device_state(self.device_id, state_update)
                
                if result:
                    print(f"📤 Data sent to Firebase - Temp: {esp_state['sensors']['temperature']:.1f}°C, "
                          f"Humidity: {esp_state['sensors']['humidity']:.1f}%, "
                          f"Soil: {esp_state['sensors']['soil_moisture']:.1f}%")
                else:
                    print(f"❌ Failed to send data to Firebase")
                
                # Wait before next update
                time.sleep(10)  # Send data every 10 seconds
                
            except Exception as e:
                print(f"❌ Error in update loop: {e}")
                time.sleep(5)
    
    def _command_loop(self):
        """Background thread to check for commands from Firebase"""
        while self.running:
            try:
                # Get pending commands from Firebase
                commands = firebase_device_manager.get_device_commands(self.device_id)
                
                for command in commands:
                    self._execute_command(command)
                
                # Wait before checking again
                time.sleep(5)  # Check for commands every 5 seconds
                
            except Exception as e:
                print(f"❌ Error in command loop: {e}")
                time.sleep(5)
    
    def _execute_command(self, command):
        """Execute a command from Firebase"""
        cmd_name = command.get('command')
        cmd_id = command.get('id')
        cmd_params = command.get('params')
        
        print(f"🎯 Executing command: {cmd_name} (ID: {cmd_id})")
        
        try:
            # Execute command on ESP simulator
            if cmd_name == "start_irrigation":
                result = self.esp_simulator.process_command("start_irrigation")
            elif cmd_name == "stop_irrigation":
                result = self.esp_simulator.process_command("stop_irrigation")
            elif cmd_name == "start_zone":
                result = self.esp_simulator.process_command("start_zone", cmd_params)
            elif cmd_name == "stop_zone":
                result = self.esp_simulator.process_command("stop_zone", cmd_params)
            elif cmd_name == "restart":
                result = self.esp_simulator.process_command("restart")
            elif cmd_name == "sync":
                result = self.esp_simulator.process_command("sync")
            elif cmd_name == "set_sensor_value":
                sensor = cmd_params.get('sensor')
                value = cmd_params.get('value')
                result = self.esp_simulator.process_command("set_sensor_value", {"sensor": sensor, "value": value})
            else:
                result = {"success": False, "message": f"Unknown command: {cmd_name}"}
            
            # Mark command as completed in Firebase
            firebase_device_manager.mark_command_completed(self.device_id, cmd_id, result)
            
            print(f"✅ Command {cmd_name} completed: {result.get('message', 'Success')}")
            
        except Exception as e:
            error_result = {"success": False, "message": f"Command execution error: {str(e)}"}
            firebase_device_manager.mark_command_completed(self.device_id, cmd_id, error_result)
            print(f"❌ Command {cmd_name} failed: {e}")

def main():
    """Main function to run the Firebase ESP32 simulator"""
    print("🔥 Firebase ESP32 Simulator")
    print("=" * 50)
    
    # Create and start simulator
    simulator = FirebaseESPSimulator("ESP32_SIMULATOR_001")
    
    try:
        simulator.start()
        
        print("\n🎮 Simulator Controls:")
        print("- Press Ctrl+C to stop the simulator")
        print("- Use the Streamlit dashboard to send commands")
        print("- Data is being stored in Firebase Realtime Database")
        print("\n📊 Monitor your data at:")
        print("- Streamlit Dashboard: http://localhost:8501")
        print("- Firebase Console: https://console.firebase.google.com/")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        simulator.stop()
        print("\n👋 Firebase ESP32 Simulator stopped")

if __name__ == "__main__":
    main()