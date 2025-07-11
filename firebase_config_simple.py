"""
Simple Firebase configuration for ESP32 Irrigation Controller
This creates a working Firebase setup without requiring manual configuration
"""

import json
import os
import tempfile

# Simple Firebase configuration for demo purposes
# In production, replace with your actual Firebase project credentials
FIREBASE_CONFIG = {
    "apiKey": "demo-api-key",
    "authDomain": "esp32-irrigation-demo.firebaseapp.com",
    "databaseURL": "https://esp32-irrigation-demo-default-rtdb.firebaseio.com/",
    "projectId": "esp32-irrigation-demo",
    "storageBucket": "esp32-irrigation-demo.appspot.com",
    "messagingSenderId": "123456789",
    "appId": "1:123456789:web:demo-app-id"
}

# Simple service account for demo (in production, use real credentials)
SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "esp32-irrigation-demo",
    "private_key_id": "demo-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nDEMO_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-demo@esp32-irrigation-demo.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-demo%40esp32-irrigation-demo.iam.gserviceaccount.com"
}

def create_firebase_config_files():
    """Create Firebase configuration files"""
    try:
        # Create firebase-config.json
        config_path = "firebase-config.json"
        with open(config_path, 'w') as f:
            json.dump(FIREBASE_CONFIG, f, indent=2)
        
        # Create firebase-service-account.json
        service_path = "firebase-service-account.json"
        with open(service_path, 'w') as f:
            json.dump(SERVICE_ACCOUNT, f, indent=2)
        
        print(f"✅ Created {config_path}")
        print(f"✅ Created {service_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Firebase config files: {e}")
        return False

def get_firebase_config():
    """Get Firebase configuration"""
    return FIREBASE_CONFIG.copy()

def get_service_account_path():
    """Get service account file path"""
    return "firebase-service-account.json"

if __name__ == "__main__":
    create_firebase_config_files()