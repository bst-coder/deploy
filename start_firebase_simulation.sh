#!/bin/bash

# Start Firebase ESP32 Simulation with Dashboard
# This script runs the local ESP32 simulator that stores data in Firebase
# and starts the Streamlit dashboard to view the data

echo "🔥 Starting Firebase ESP32 Irrigation Controller"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Please run ./deploy_firebase.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping services...${NC}"
    
    # Kill background processes
    if [ ! -z "$SIMULATOR_PID" ]; then
        kill $SIMULATOR_PID 2>/dev/null
        echo -e "${GREEN}✅ ESP32 simulator stopped${NC}"
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null
        echo -e "${GREEN}✅ Dashboard stopped${NC}"
    fi
    
    echo -e "${GREEN}👋 Firebase ESP32 Irrigation Controller stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}🚀 Starting ESP32 Firebase Simulator...${NC}"

# Start the ESP32 simulator in background
python3 local_simulator_firebase.py &
SIMULATOR_PID=$!

# Wait a moment for simulator to start
sleep 3

echo -e "${BLUE}🌐 Starting Streamlit Dashboard...${NC}"

# Start the Streamlit dashboard in background
streamlit run main.py --server.port 8501 --server.address 0.0.0.0 &
DASHBOARD_PID=$!

# Wait a moment for dashboard to start
sleep 5

echo -e "${GREEN}✅ Firebase ESP32 Irrigation Controller is running!${NC}"
echo
echo "📊 Access your dashboard at:"
echo "   Local:    http://localhost:8501"
echo "   Network:  http://0.0.0.0:8501"
echo
echo "🔥 Firebase Console:"
echo "   https://console.firebase.google.com/project/esp32-irrigation-control-c4ac6/database"
echo
echo "🎮 Features:"
echo "   ✅ Local ESP32 simulation running"
echo "   ✅ Data stored in Firebase Realtime Database"
echo "   ✅ Real-time dashboard with controls"
echo "   ✅ Multi-zone irrigation control"
echo "   ✅ Command history and monitoring"
echo
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for processes to finish
wait