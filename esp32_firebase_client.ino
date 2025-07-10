/*
 * ESP32 Firebase Client for Irrigation Controller
 * This code connects your ESP32 to Firebase for cloud communication
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <FirebaseESP32.h>
#include <DHT.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Firebase configuration
#define FIREBASE_HOST "your-project-id-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH "your-database-secret-or-token"

// Device configuration
String deviceId = "ESP32_IRRIGATION_001";
String firmwareVersion = "1.0.0";

// Sensor pins
#define DHT_PIN 4
#define DHT_TYPE DHT22
#define SOIL_MOISTURE_PIN A0
#define LIGHT_SENSOR_PIN A1

// Relay pins for zones
#define ZONE1_RELAY_PIN 16
#define ZONE2_RELAY_PIN 17
#define ZONE3_RELAY_PIN 18
#define ZONE4_RELAY_PIN 19
#define PUMP_RELAY_PIN 21

// Initialize sensors
DHT dht(DHT_PIN, DHT_TYPE);

// Firebase objects
FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

// Timing variables
unsigned long lastSensorUpdate = 0;
unsigned long lastCommandCheck = 0;
unsigned long lastHeartbeat = 0;
const unsigned long SENSOR_INTERVAL = 30000;  // 30 seconds
const unsigned long COMMAND_INTERVAL = 10000; // 10 seconds
const unsigned long HEARTBEAT_INTERVAL = 60000; // 1 minute

// Device state
struct DeviceState {
  bool online = true;
  float temperature = 0.0;
  float humidity = 0.0;
  float soilMoisture = 0.0;
  float lightLevel = 0.0;
  
  bool zone1Active = false;
  bool zone2Active = false;
  bool zone3Active = false;
  bool zone4Active = false;
  bool pumpActive = false;
  
  unsigned long uptime = 0;
  int wifiStrength = 0;
  int freeMemory = 0;
} deviceState;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Firebase Irrigation Controller Starting...");
  
  // Initialize pins
  initializePins();
  
  // Initialize sensors
  dht.begin();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Initialize Firebase
  initializeFirebase();
  
  // Register device
  registerDevice();
  
  Serial.println("✅ ESP32 Firebase Client Ready!");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Update device uptime
  deviceState.uptime = currentTime;
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectToWiFi();
  }
  
  // Send sensor data periodically
  if (currentTime - lastSensorUpdate >= SENSOR_INTERVAL) {
    readSensors();
    sendSensorData();
    lastSensorUpdate = currentTime;
  }
  
  // Check for commands periodically
  if (currentTime - lastCommandCheck >= COMMAND_INTERVAL) {
    checkForCommands();
    lastCommandCheck = currentTime;
  }
  
  // Send heartbeat periodically
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  delay(1000); // Small delay to prevent overwhelming the system
}

void initializePins() {
  // Set relay pins as outputs
  pinMode(ZONE1_RELAY_PIN, OUTPUT);
  pinMode(ZONE2_RELAY_PIN, OUTPUT);
  pinMode(ZONE3_RELAY_PIN, OUTPUT);
  pinMode(ZONE4_RELAY_PIN, OUTPUT);
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  
  // Initialize all relays to OFF
  digitalWrite(ZONE1_RELAY_PIN, LOW);
  digitalWrite(ZONE2_RELAY_PIN, LOW);
  digitalWrite(ZONE3_RELAY_PIN, LOW);
  digitalWrite(ZONE4_RELAY_PIN, LOW);
  digitalWrite(PUMP_RELAY_PIN, LOW);
  
  Serial.println("✅ Pins initialized");
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    deviceState.wifiStrength = WiFi.RSSI();
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
  }
}

void initializeFirebase() {
  // Configure Firebase
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  
  // Initialize Firebase
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  // Set timeout
  firebaseData.setResponseSize(4096);
  
  Serial.println("✅ Firebase initialized");
}

void registerDevice() {
  Serial.println("📝 Registering device with Firebase...");
  
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceId;
  doc["firmware_version"] = firmwareVersion;
  doc["device_type"] = "ESP32_Irrigation_Controller";
  doc["ip_address"] = WiFi.localIP().toString();
  doc["mac_address"] = WiFi.macAddress();
  doc["registered_at"] = getCurrentTimestamp();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String path = "/devices/" + deviceId + "/device_info";
  
  if (Firebase.setJSON(firebaseData, path, doc)) {
    Serial.println("✅ Device registered successfully");
  } else {
    Serial.println("❌ Device registration failed: " + firebaseData.errorReason());
  }
}

void readSensors() {
  // Read DHT22 sensor
  deviceState.temperature = dht.readTemperature();
  deviceState.humidity = dht.readHumidity();
  
  // Read soil moisture (0-1023, convert to percentage)
  int soilRaw = analogRead(SOIL_MOISTURE_PIN);
  deviceState.soilMoisture = map(soilRaw, 0, 1023, 0, 100);
  
  // Read light sensor (0-1023, convert to lux approximation)
  int lightRaw = analogRead(LIGHT_SENSOR_PIN);
  deviceState.lightLevel = map(lightRaw, 0, 1023, 0, 1000);
  
  // Update system info
  deviceState.wifiStrength = WiFi.RSSI();
  deviceState.freeMemory = ESP.getFreeHeap() / 1024; // Convert to KB
  
  // Check for sensor errors
  if (isnan(deviceState.temperature) || isnan(deviceState.humidity)) {
    Serial.println("⚠️ DHT sensor read error");
    deviceState.temperature = 25.0; // Default value
    deviceState.humidity = 60.0;    // Default value
  }
  
  Serial.printf("📊 Sensors - Temp: %.1f°C, Humidity: %.1f%%, Soil: %.1f%%, Light: %.0f lux\n",
                deviceState.temperature, deviceState.humidity, deviceState.soilMoisture, deviceState.lightLevel);
}

void sendSensorData() {
  Serial.println("📤 Sending sensor data to Firebase...");
  
  DynamicJsonDocument doc(2048);
  
  // Sensor data
  doc["sensors"]["temperature"] = deviceState.temperature;
  doc["sensors"]["humidity"] = deviceState.humidity;
  doc["sensors"]["soil_moisture"] = deviceState.soilMoisture;
  doc["sensors"]["light_level"] = deviceState.lightLevel;
  
  // Zone states
  doc["zones"]["1"]["active"] = deviceState.zone1Active;
  doc["zones"]["1"]["valve_open"] = deviceState.zone1Active;
  doc["zones"]["2"]["active"] = deviceState.zone2Active;
  doc["zones"]["2"]["valve_open"] = deviceState.zone2Active;
  doc["zones"]["3"]["active"] = deviceState.zone3Active;
  doc["zones"]["3"]["valve_open"] = deviceState.zone3Active;
  doc["zones"]["4"]["active"] = deviceState.zone4Active;
  doc["zones"]["4"]["valve_open"] = deviceState.zone4Active;
  
  // Pump state
  doc["pump"]["active"] = deviceState.pumpActive;
  doc["pump"]["pressure"] = deviceState.pumpActive ? 2.5 : 0.0;
  doc["pump"]["flow_rate"] = deviceState.pumpActive ? 15.0 : 0.0;
  
  // Device info
  doc["device_info"]["uptime"] = formatUptime(deviceState.uptime);
  doc["device_info"]["wifi_strength"] = deviceState.wifiStrength;
  doc["device_info"]["free_memory"] = deviceState.freeMemory;
  doc["device_info"]["firmware_version"] = firmwareVersion;
  
  // System status
  doc["online"] = true;
  doc["irrigation_active"] = (deviceState.zone1Active || deviceState.zone2Active || 
                             deviceState.zone3Active || deviceState.zone4Active);
  doc["last_sync"] = getCurrentTimestamp();
  
  String path = "/devices/" + deviceId + "/state";
  
  if (Firebase.updateNode(firebaseData, path, doc)) {
    Serial.println("✅ Sensor data sent successfully");
  } else {
    Serial.println("❌ Failed to send sensor data: " + firebaseData.errorReason());
  }
}

void sendHeartbeat() {
  String path = "/devices/" + deviceId + "/last_heartbeat";
  String timestamp = getCurrentTimestamp();
  
  if (Firebase.setString(firebaseData, path, timestamp)) {
    Serial.println("💓 Heartbeat sent");
  } else {
    Serial.println("❌ Heartbeat failed: " + firebaseData.errorReason());
  }
  
  // Also update connection status
  path = "/devices/" + deviceId + "/connected";
  Firebase.setBool(firebaseData, path, true);
}

void checkForCommands() {
  String path = "/commands/" + deviceId;
  
  if (Firebase.getJSON(firebaseData, path)) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, firebaseData.jsonString());
    
    // Process each command
    for (JsonPair command : doc.as<JsonObject>()) {
      JsonObject cmdObj = command.value();
      
      if (cmdObj["status"] == "pending") {
        String cmdKey = command.key().c_str();
        executeCommand(cmdKey, cmdObj);
      }
    }
  }
}

void executeCommand(String cmdKey, JsonObject cmd) {
  String command = cmd["command"];
  String commandId = cmd["id"];
  
  Serial.println("🎯 Executing command: " + command);
  
  DynamicJsonDocument result(512);
  result["success"] = true;
  result["message"] = "Command executed successfully";
  result["timestamp"] = getCurrentTimestamp();
  
  if (command == "start_irrigation") {
    startAllZones();
    result["action"] = "All zones started";
    
  } else if (command == "stop_irrigation") {
    stopAllZones();
    result["action"] = "All zones stopped";
    
  } else if (command == "start_zone") {
    int zone = cmd["params"];
    startZone(zone);
    result["action"] = "Zone " + String(zone) + " started";
    
  } else if (command == "stop_zone") {
    int zone = cmd["params"];
    stopZone(zone);
    result["action"] = "Zone " + String(zone) + " stopped";
    
  } else if (command == "restart") {
    result["action"] = "Device restarting";
    markCommandCompleted(cmdKey, result);
    delay(1000);
    ESP.restart();
    
  } else if (command == "sync") {
    readSensors();
    sendSensorData();
    result["action"] = "Data synchronized";
    
  } else {
    result["success"] = false;
    result["message"] = "Unknown command: " + command;
  }
  
  markCommandCompleted(cmdKey, result);
}

void markCommandCompleted(String cmdKey, DynamicJsonDocument& result) {
  String path = "/commands/" + deviceId + "/" + cmdKey + "/status";
  Firebase.setString(firebaseData, path, "completed");
  
  path = "/commands/" + deviceId + "/" + cmdKey + "/result";
  Firebase.setJSON(firebaseData, path, result);
  
  path = "/commands/" + deviceId + "/" + cmdKey + "/completed_at";
  Firebase.setString(firebaseData, path, getCurrentTimestamp());
  
  Serial.println("✅ Command marked as completed");
}

void startZone(int zone) {
  switch (zone) {
    case 1:
      digitalWrite(ZONE1_RELAY_PIN, HIGH);
      deviceState.zone1Active = true;
      break;
    case 2:
      digitalWrite(ZONE2_RELAY_PIN, HIGH);
      deviceState.zone2Active = true;
      break;
    case 3:
      digitalWrite(ZONE3_RELAY_PIN, HIGH);
      deviceState.zone3Active = true;
      break;
    case 4:
      digitalWrite(ZONE4_RELAY_PIN, HIGH);
      deviceState.zone4Active = true;
      break;
  }
  
  // Start pump if any zone is active
  if (deviceState.zone1Active || deviceState.zone2Active || 
      deviceState.zone3Active || deviceState.zone4Active) {
    digitalWrite(PUMP_RELAY_PIN, HIGH);
    deviceState.pumpActive = true;
  }
  
  Serial.println("🚿 Zone " + String(zone) + " started");
}

void stopZone(int zone) {
  switch (zone) {
    case 1:
      digitalWrite(ZONE1_RELAY_PIN, LOW);
      deviceState.zone1Active = false;
      break;
    case 2:
      digitalWrite(ZONE2_RELAY_PIN, LOW);
      deviceState.zone2Active = false;
      break;
    case 3:
      digitalWrite(ZONE3_RELAY_PIN, LOW);
      deviceState.zone3Active = false;
      break;
    case 4:
      digitalWrite(ZONE4_RELAY_PIN, LOW);
      deviceState.zone4Active = false;
      break;
  }
  
  // Stop pump if no zones are active
  if (!deviceState.zone1Active && !deviceState.zone2Active && 
      !deviceState.zone3Active && !deviceState.zone4Active) {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    deviceState.pumpActive = false;
  }
  
  Serial.println("⏹️ Zone " + String(zone) + " stopped");
}

void startAllZones() {
  for (int i = 1; i <= 4; i++) {
    startZone(i);
  }
  Serial.println("🚿 All zones started");
}

void stopAllZones() {
  for (int i = 1; i <= 4; i++) {
    stopZone(i);
  }
  Serial.println("⏹️ All zones stopped");
}

String getCurrentTimestamp() {
  // In a real implementation, you might want to use NTP for accurate time
  // For now, we'll use millis() as a simple timestamp
  return String(millis());
}

String formatUptime(unsigned long uptime) {
  unsigned long seconds = uptime / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  unsigned long days = hours / 24;
  
  hours = hours % 24;
  minutes = minutes % 60;
  seconds = seconds % 60;
  
  return String(days) + "d " + String(hours) + "h " + String(minutes) + "m";
}