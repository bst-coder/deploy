import streamlit as st
import json
from datetime import datetime
from device_manager import device_manager

def handle_api_request():
    """Handle API requests from ESP32 devices"""
    
    # Check if this is an API request
    query_params = st.query_params
    
    if 'api' in query_params:
        api_endpoint = query_params.get('api')
        
        if api_endpoint == 'register':
            return handle_device_registration()
        elif api_endpoint == 'heartbeat':
            return handle_device_heartbeat()
        elif api_endpoint == 'get_commands':
            return handle_get_commands()
        elif api_endpoint == 'command_result':
            return handle_command_result()
        elif api_endpoint == 'update_state':
            return handle_state_update()
    
    return None

def handle_device_registration():
    """Handle ESP32 device registration"""
    try:
        # In a real implementation, you'd get this from POST data
        # For now, we'll use query parameters for simplicity
        query_params = st.query_params
        
        device_id = query_params.get('device_id', 'ESP32_DEFAULT')
        firmware_version = query_params.get('firmware', '1.0.0')
        
        device_info = {
            'device_id': device_id,
            'firmware_version': firmware_version,
            'registered_at': datetime.now().isoformat(),
            'ip_address': 'simulated'  # In real implementation, get from request
        }
        
        success = device_manager.register_device(device_id, device_info)
        
        response = {
            'success': success,
            'message': 'Device registered successfully' if success else 'Registration failed',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Return JSON response for API clients
        st.write(json.dumps(response))
        st.stop()
        
    except Exception as e:
        error_response = {
            'success': False,
            'message': f'Registration error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        st.write(json.dumps(error_response))
        st.stop()

def handle_device_heartbeat():
    """Handle ESP32 heartbeat/status update"""
    try:
        query_params = st.query_params
        device_id = query_params.get('device_id')
        
        if not device_id:
            raise ValueError("device_id is required")
        
        # Parse sensor data from query parameters
        state_update = {}
        
        if 'temperature' in query_params:
            state_update['sensors'] = state_update.get('sensors', {})
            state_update['sensors']['temperature'] = float(query_params.get('temperature'))
        
        if 'humidity' in query_params:
            state_update['sensors'] = state_update.get('sensors', {})
            state_update['sensors']['humidity'] = float(query_params.get('humidity'))
        
        if 'soil_moisture' in query_params:
            state_update['sensors'] = state_update.get('sensors', {})
            state_update['sensors']['soil_moisture'] = float(query_params.get('soil_moisture'))
        
        if 'light_level' in query_params:
            state_update['sensors'] = state_update.get('sensors', {})
            state_update['sensors']['light_level'] = float(query_params.get('light_level'))
        
        success = device_manager.update_device_state(device_id, state_update)
        
        response = {
            'success': success,
            'message': 'Heartbeat received' if success else 'Device not found',
            'timestamp': datetime.now().isoformat()
        }
        
        st.write(json.dumps(response))
        st.stop()
        
    except Exception as e:
        error_response = {
            'success': False,
            'message': f'Heartbeat error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        st.write(json.dumps(error_response))
        st.stop()

def handle_get_commands():
    """Handle ESP32 request for pending commands"""
    try:
        query_params = st.query_params
        device_id = query_params.get('device_id')
        
        if not device_id:
            raise ValueError("device_id is required")
        
        commands = device_manager.get_device_commands(device_id)
        
        response = {
            'success': True,
            'commands': commands,
            'count': len(commands),
            'timestamp': datetime.now().isoformat()
        }
        
        st.write(json.dumps(response))
        st.stop()
        
    except Exception as e:
        error_response = {
            'success': False,
            'message': f'Get commands error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        st.write(json.dumps(error_response))
        st.stop()

def handle_command_result():
    """Handle ESP32 command execution result"""
    try:
        query_params = st.query_params
        device_id = query_params.get('device_id')
        command_id = query_params.get('command_id')
        success = query_params.get('success', 'false').lower() == 'true'
        message = query_params.get('message', '')
        
        if not device_id or not command_id:
            raise ValueError("device_id and command_id are required")
        
        result = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        device_manager.mark_command_completed(device_id, command_id, result)
        
        response = {
            'success': True,
            'message': 'Command result recorded',
            'timestamp': datetime.now().isoformat()
        }
        
        st.write(json.dumps(response))
        st.stop()
        
    except Exception as e:
        error_response = {
            'success': False,
            'message': f'Command result error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        st.write(json.dumps(error_response))
        st.stop()

def handle_state_update():
    """Handle ESP32 state update"""
    try:
        query_params = st.query_params
        device_id = query_params.get('device_id')
        
        if not device_id:
            raise ValueError("device_id is required")
        
        # Parse state data from query parameters
        state_update = {}
        
        # Parse irrigation status
        if 'irrigation_active' in query_params:
            state_update['irrigation_active'] = query_params.get('irrigation_active').lower() == 'true'
        
        # Parse pump data
        if 'pump_active' in query_params:
            state_update['pump'] = state_update.get('pump', {})
            state_update['pump']['active'] = query_params.get('pump_active').lower() == 'true'
        
        if 'pump_pressure' in query_params:
            state_update['pump'] = state_update.get('pump', {})
            state_update['pump']['pressure'] = float(query_params.get('pump_pressure'))
        
        if 'pump_flow_rate' in query_params:
            state_update['pump'] = state_update.get('pump', {})
            state_update['pump']['flow_rate'] = float(query_params.get('pump_flow_rate'))
        
        success = device_manager.update_device_state(device_id, state_update)
        
        response = {
            'success': success,
            'message': 'State updated' if success else 'Device not found',
            'timestamp': datetime.now().isoformat()
        }
        
        st.write(json.dumps(response))
        st.stop()
        
    except Exception as e:
        error_response = {
            'success': False,
            'message': f'State update error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        st.write(json.dumps(error_response))
        st.stop()