#!/bin/bash

# Firebase Deployment Script for ESP32 Irrigation Controller
# This script helps you deploy your application with Firebase integration

set -e  # Exit on any error

echo "🔥 Firebase Deployment Script for ESP32 Irrigation Controller"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running in correct directory
if [ ! -f "main.py" ]; then
    print_error "main.py not found. Please run this script from the project directory."
    exit 1
fi

print_info "Starting Firebase deployment process..."

# Step 1: Check Python version
echo
echo "📋 Step 1: Checking Python environment..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_info "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

print_status "Python 3 is available"

# Step 2: Create virtual environment
echo
echo "🐍 Step 2: Setting up virtual environment..."

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_status "Virtual environment created"

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Step 3: Install dependencies
echo
echo "📦 Step 3: Installing dependencies..."

pip install --upgrade pip
pip install -r requirements.txt

print_status "Dependencies installed successfully"

# Step 4: Check Firebase configuration
echo
echo "🔥 Step 4: Checking Firebase configuration..."

if [ ! -f "firebase-config.json" ]; then
    print_warning "firebase-config.json not found"
    print_info "Creating template configuration file..."
    
    if [ -f "firebase-config-template.json" ]; then
        cp firebase-config-template.json firebase-config.json
        print_info "Please edit firebase-config.json with your Firebase project details"
    else
        print_error "firebase-config-template.json not found"
        exit 1
    fi
else
    print_status "Firebase configuration file found"
fi

if [ ! -f "firebase-service-account.json" ]; then
    print_warning "firebase-service-account.json not found"
    print_info "Please download your Firebase service account key and save it as firebase-service-account.json"
    print_info "You can download it from: Firebase Console > Project Settings > Service Accounts"
else
    print_status "Firebase service account file found"
fi

# Step 5: Test Firebase connection
echo
echo "🧪 Step 5: Testing Firebase connection..."

if [ -f "firebase-service-account.json" ] && [ -f "firebase-config.json" ]; then
    print_info "Running Firebase connection test..."
    
    if python3 test_firebase.py; then
        print_status "Firebase connection test passed"
    else
        print_warning "Firebase connection test failed. Check your configuration."
        print_info "You can still continue with local simulation mode."
    fi
else
    print_warning "Skipping Firebase test - configuration files missing"
    print_info "The application will run in local simulation mode"
fi

# Step 6: Create .gitignore
echo
echo "📝 Step 6: Setting up Git configuration..."

if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Firebase
firebase-service-account.json
firebase-config.json
.env

# Streamlit
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
/tmp/
EOF
    print_status ".gitignore created"
else
    print_status ".gitignore already exists"
fi

# Step 7: Test application
echo
echo "🚀 Step 7: Testing application..."

print_info "Running application tests..."
if python3 test_app.py; then
    print_status "Application tests passed"
else
    print_warning "Some application tests failed, but continuing..."
fi

# Step 8: Deployment options
echo
echo "🌐 Step 8: Deployment Options"
echo "=============================="

print_info "Your application is ready for deployment! Choose an option:"
echo
echo "Option 1: Local Development"
echo "  Run: streamlit run main.py"
echo
echo "Option 2: Streamlit Cloud"
echo "  1. Push your code to GitHub (excluding firebase-service-account.json)"
echo "  2. Go to https://streamlit.io/cloud"
echo "  3. Connect your repository"
echo "  4. Add secrets in Streamlit Cloud settings:"
echo "     - FIREBASE_CONFIG: (paste firebase-config.json content)"
echo "     - FIREBASE_SERVICE_ACCOUNT: (paste service account JSON content)"
echo
echo "Option 3: Google Cloud Run"
echo "  1. Build Docker image: docker build -t esp32-irrigation ."
echo "  2. Deploy: gcloud run deploy esp32-irrigation --source ."
echo
echo "Option 4: Firebase Hosting (Static)"
echo "  1. Install Firebase CLI: npm install -g firebase-tools"
echo "  2. Initialize: firebase init hosting"
echo "  3. Build static version of your app"
echo

# Step 9: Create startup script
echo
echo "📜 Step 9: Creating startup scripts..."

# Local development script
cat > start_local.sh << 'EOF'
#!/bin/bash
echo "🌱 Starting ESP32 Irrigation Controller (Local Mode)"
source venv/bin/activate
streamlit run main.py --server.port 8501 --server.address 0.0.0.0
EOF

chmod +x start_local.sh
print_status "Local startup script created: start_local.sh"

# Production script
cat > start_production.sh << 'EOF'
#!/bin/bash
echo "🌱 Starting ESP32 Irrigation Controller (Production Mode)"
source venv/bin/activate

# Set production environment variables
export STREAMLIT_SERVER_PORT=${PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

streamlit run main.py \
  --server.port $STREAMLIT_SERVER_PORT \
  --server.address $STREAMLIT_SERVER_ADDRESS \
  --server.headless true \
  --browser.gatherUsageStats false
EOF

chmod +x start_production.sh
print_status "Production startup script created: start_production.sh"

# Step 10: Create Dockerfile for containerized deployment
echo
echo "🐳 Step 10: Creating Docker configuration..."

cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
EOF

print_status "Dockerfile created"

# Create docker-compose for local development
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  esp32-irrigation:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    volumes:
      - ./firebase-config.json:/app/firebase-config.json:ro
      - ./firebase-service-account.json:/app/firebase-service-account.json:ro
    restart: unless-stopped
EOF

print_status "docker-compose.yml created"

# Step 11: Final instructions
echo
echo "🎉 Deployment Setup Complete!"
echo "=============================="

print_status "Your ESP32 Irrigation Controller is ready for Firebase deployment!"
echo
print_info "Next steps:"
echo "1. Configure Firebase (if not done already):"
echo "   - Edit firebase-config.json with your project details"
echo "   - Download firebase-service-account.json from Firebase Console"
echo
echo "2. Test locally:"
echo "   ./start_local.sh"
echo
echo "3. Deploy to your preferred platform:"
echo "   - Streamlit Cloud: Push to GitHub and connect"
echo "   - Google Cloud Run: gcloud run deploy --source ."
echo "   - Docker: docker-compose up"
echo
echo "4. Program your ESP32 with the provided Arduino code:"
echo "   - Use esp32_firebase_client.ino"
echo "   - Update WiFi and Firebase credentials"
echo
print_info "For detailed instructions, see FIREBASE_DEPLOYMENT_GUIDE.md"

# Deactivate virtual environment
deactivate

echo
print_status "Firebase deployment setup completed successfully! 🔥"