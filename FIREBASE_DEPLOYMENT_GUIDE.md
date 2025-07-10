# 🔥 Firebase Deployment Guide for ESP32 Irrigation Controller

## 📋 Overview

This guide will help you deploy your ESP32 Irrigation Controller to Firebase, enabling real-time cloud communication between your ESP32 devices and the Streamlit dashboard.

## 🎯 What You'll Achieve

- **Real-time cloud synchronization** between ESP32 devices and dashboard
- **Scalable device management** supporting multiple ESP32 controllers
- **Persistent data storage** with Firebase Realtime Database
- **Secure authentication** and device management
- **Global accessibility** from anywhere with internet

## 🏗️ Architecture Overview

```
ESP32 Device(s) ←→ Firebase Realtime Database ←→ Streamlit Dashboard
                           ↓
                    Firebase Hosting (Optional)
```

## 📦 Prerequisites

### 1. Firebase Account Setup
- Google account
- Firebase project created
- Firebase CLI installed

### 2. Required Dependencies
```bash
pip install firebase-admin
pip install pyrebase4
pip install streamlit
pip install requests
```

## 🚀 Step-by-Step Deployment

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name: `esp32-irrigation-controller`
4. Enable Google Analytics (optional)
5. Create project

### Step 2: Enable Firebase Services

#### Enable Realtime Database
1. In Firebase Console, go to "Realtime Database"
2. Click "Create Database"
3. Choose location (closest to your devices)
4. Start in **test mode** (we'll secure it later)

#### Enable Authentication (Optional but Recommended)
1. Go to "Authentication" → "Sign-in method"
2. Enable "Email/Password"
3. Enable "Anonymous" for device authentication

### Step 3: Get Firebase Configuration

1. Go to Project Settings (gear icon)
2. Scroll to "Your apps"
3. Click "Add app" → Web app
4. Register app name: `irrigation-dashboard`
5. Copy the configuration object

### Step 4: Set Up Service Account

1. Go to Project Settings → "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file
4. Rename it to `firebase-service-account.json`
5. Place it in your project directory (add to .gitignore!)

## 🔧 Implementation

### Step 1: Update Firebase Manager

Replace your current `firebase_manager.py` with the real Firebase implementation:

```python
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
```

### Step 2: Create Firebase Configuration Files

Create `firebase-config.json`:
```json
{
  "apiKey": "your-api-key",
  "authDomain": "your-project.firebaseapp.com",
  "databaseURL": "https://your-project-default-rtdb.firebaseio.com/",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "your-app-id"
}
```

### Step 3: Update Requirements

Add Firebase dependencies to `requirements.txt`:
```
streamlit>=1.28.0
requests>=2.31.0
firebase-admin>=6.2.0
pyrebase4>=4.7.1
```

### Step 4: Update Main Application

Modify the import in `main.py`:
```python
# Replace this line:
from firebase_manager import cloud_device_manager

# With this:
from firebase_manager_real import firebase_device_manager as cloud_device_manager
```

## 🔒 Security Configuration

### Step 1: Database Rules

In Firebase Console → Realtime Database → Rules:

```json
{
  "rules": {
    "devices": {
      "$device_id": {
        ".read": true,
        ".write": true,
        ".validate": "newData.hasChildren(['device_info', 'last_heartbeat', 'connected', 'state'])"
      }
    },
    "commands": {
      "$device_id": {
        ".read": true,
        ".write": true
      }
    }
  }
}
```

### Step 2: Environment Variables

Create `.env` file (add to .gitignore):
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com/
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

## 🚀 Deployment Options

### Option 1: Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your repository
4. Add secrets in Streamlit Cloud:
   - `FIREBASE_CONFIG` (paste your firebase-config.json content)
   - `FIREBASE_SERVICE_ACCOUNT` (paste your service account JSON)

### Option 2: Firebase Hosting

1. Install Firebase CLI:
```bash
npm install -g firebase-tools
```

2. Initialize Firebase hosting:
```bash
firebase init hosting
```

3. Build your Streamlit app as static files (advanced)

### Option 3: Google Cloud Run

1. Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy esp32-irrigation --source .
```

## 📱 ESP32 Integration

### Arduino Code Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <FirebaseESP32.h>

// Firebase configuration
#define FIREBASE_HOST "your-project-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH "your-database-secret"

FirebaseData firebaseData;
String deviceId = "ESP32_001";

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin("your-wifi", "your-password");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  // Initialize Firebase
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);
  Firebase.reconnectWiFi(true);
  
  // Register device
  registerDevice();
}

void loop() {
  // Send sensor data every 30 seconds
  sendSensorData();
  
  // Check for commands every 10 seconds
  checkCommands();
  
  delay(10000);
}

void registerDevice() {
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceId;
  doc["firmware_version"] = "1.0.0";
  doc["device_type"] = "ESP32_Irrigation";
  
  String path = "/devices/" + deviceId + "/device_info";
  Firebase.setJSON(firebaseData, path, doc);
}

void sendSensorData() {
  DynamicJsonDocument doc(1024);
  
  // Read sensors (replace with actual sensor code)
  doc["sensors"]["temperature"] = 25.5;
  doc["sensors"]["humidity"] = 60.0;
  doc["sensors"]["soil_moisture"] = 45.0;
  doc["sensors"]["light_level"] = 500.0;
  
  doc["last_heartbeat"] = "2024-01-01T12:00:00";
  doc["connected"] = true;
  
  String path = "/devices/" + deviceId + "/state";
  Firebase.updateNode(firebaseData, path, doc);
}

void checkCommands() {
  String path = "/commands/" + deviceId;
  if (Firebase.getJSON(firebaseData, path)) {
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, firebaseData.jsonString());
    
    // Process commands
    for (JsonPair command : doc.as<JsonObject>()) {
      if (command.value()["status"] == "pending") {
        executeCommand(command.key().c_str(), command.value());
      }
    }
  }
}

void executeCommand(const char* cmdKey, JsonObject cmd) {
  String command = cmd["command"];
  
  if (command == "start_irrigation") {
    // Start irrigation logic
    Serial.println("Starting irrigation...");
  } else if (command == "stop_irrigation") {
    // Stop irrigation logic
    Serial.println("Stopping irrigation...");
  }
  
  // Mark command as completed
  String path = "/commands/" + deviceId + "/" + cmdKey + "/status";
  Firebase.setString(firebaseData, path, "completed");
}
```

## 🧪 Testing

### Test Firebase Connection

Create `test_firebase.py`:
```python
from firebase_manager_real import firebase_device_manager

# Test device registration
device_id = "TEST_ESP32_001"
device_info = {
    "device_id": device_id,
    "firmware_version": "1.0.0",
    "device_type": "ESP32_Test"
}

# Start manager
firebase_device_manager.start()

# Register device
result = firebase_device_manager.register_device(device_id, device_info)
print(f"Registration result: {result}")

# Send test command
cmd_result = firebase_device_manager.send_command_to_device(device_id, "test_command", {"param": "value"})
print(f"Command result: {cmd_result}")

# Get device state
state = firebase_device_manager.get_device_state(device_id)
print(f"Device state: {state}")
```

## 📊 Monitoring

### Firebase Console Monitoring

1. **Realtime Database**: Monitor data flow in real-time
2. **Usage**: Track read/write operations
3. **Performance**: Monitor response times

### Application Monitoring

Add logging to your application:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add to your Firebase operations
logger.info(f"Device {device_id} registered successfully")
logger.error(f"Failed to send command: {error}")
```

## 🔧 Troubleshooting

### Common Issues

1. **Firebase Connection Failed**
   - Check service account file path
   - Verify database URL
   - Ensure Firebase project is active

2. **Permission Denied**
   - Update database rules
   - Check authentication settings

3. **Device Not Appearing**
   - Verify ESP32 WiFi connection
   - Check Firebase configuration in ESP32 code
   - Monitor Firebase console for incoming data

### Debug Mode

Enable debug logging:
```python
import os
os.environ['FIREBASE_DEBUG'] = '1'
```

## 🎯 Next Steps

1. **Deploy to Streamlit Cloud** with Firebase integration
2. **Program your ESP32** with Firebase communication
3. **Set up monitoring** and alerts
4. **Scale to multiple devices**
5. **Add authentication** for production use

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-cloud)
- [ESP32 Firebase Library](https://github.com/mobizt/Firebase-ESP32)

---

🌱 **Happy Deploying!** Your ESP32 Irrigation Controller is now ready for global cloud deployment! 🔥