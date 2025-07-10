#!/bin/bash

# ESP32 Irrigation Controller - Deployment Script
# This script helps with local setup and GitHub deployment preparation

set -e  # Exit on any error

echo "🌱 ESP32 Irrigation Controller - Deployment Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_status "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed. Please install Python 3.7 or higher."
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    print_status "Virtual environment created"
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    print_status "Pip upgraded"
    
    # Install dependencies
    print_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
}

# Run tests
run_tests() {
    print_info "Running application tests..."
    
    # Test ESP simulation
    python3 espsimulation.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "ESP simulation test passed"
    else
        print_error "ESP simulation test failed"
        exit 1
    fi
    
    # Test utilities
    python3 utils.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "Utilities test passed"
    else
        print_error "Utilities test failed"
        exit 1
    fi
    
    # Run comprehensive tests
    python3 test_app.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "All component tests passed"
    else
        print_error "Component tests failed"
        exit 1
    fi
}

# Check Git setup
check_git() {
    if command -v git &> /dev/null; then
        print_status "Git is available"
        
        if [ -d ".git" ]; then
            print_status "Git repository already initialized"
        else
            print_warning "Git repository not initialized"
            print_info "Run 'git init' to initialize repository"
        fi
    else
        print_warning "Git is not installed. Install Git for version control and deployment."
    fi
}

# Create .gitignore if it doesn't exist
create_gitignore() {
    if [ ! -f ".gitignore" ]; then
        print_info "Creating .gitignore file..."
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
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/secrets.toml

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
EOF
        print_status ".gitignore created"
    else
        print_status ".gitignore already exists"
    fi
}

# Display project structure
show_structure() {
    print_info "Project structure:"
    echo ""
    tree -I 'venv|__pycache__|*.pyc' . 2>/dev/null || find . -type f -not -path "./venv/*" -not -name "*.pyc" | sort
    echo ""
}

# Display deployment instructions
show_deployment_info() {
    echo ""
    echo "🚀 Deployment Instructions"
    echo "========================="
    echo ""
    echo "📁 Local Development:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run the app: streamlit run main.py"
    echo "  3. Open browser to: http://localhost:8501"
    echo ""
    echo "☁️  Streamlit Cloud Deployment:"
    echo "  1. Push code to GitHub:"
    echo "     git init"
    echo "     git add ."
    echo "     git commit -m 'Initial commit: ESP32 Irrigation Simulator'"
    echo "     git branch -M main"
    echo "     git remote add origin <your-github-repo-url>"
    echo "     git push -u origin main"
    echo ""
    echo "  2. Deploy on Streamlit Cloud:"
    echo "     - Go to https://share.streamlit.io"
    echo "     - Click 'New app'"
    echo "     - Connect your GitHub repository"
    echo "     - Set main file: main.py"
    echo "     - Click 'Deploy'"
    echo ""
    echo "📋 Files included:"
    echo "  ✓ main.py - Streamlit dashboard"
    echo "  ✓ espsimulation.py - ESP32 simulator"
    echo "  ✓ utils.py - Utility functions"
    echo "  ✓ requirements.txt - Dependencies"
    echo "  ✓ README.md - Documentation"
    echo "  ✓ test_app.py - Test suite"
    echo "  ✓ .streamlit/config.toml - Streamlit config"
    echo ""
}

# Main execution
main() {
    echo ""
    
    # Check prerequisites
    check_python
    check_git
    
    echo ""
    print_info "Setting up project..."
    
    # Setup environment
    setup_venv
    
    # Create additional files
    create_gitignore
    
    # Run tests
    echo ""
    run_tests
    
    # Show project info
    echo ""
    show_structure
    show_deployment_info
    
    echo ""
    print_status "Setup completed successfully! 🎉"
    echo ""
    print_info "To start the application:"
    echo "  source venv/bin/activate && streamlit run main.py"
    echo ""
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "test")
        print_info "Running tests only..."
        run_tests
        print_status "All tests passed!"
        ;;
    "clean")
        print_info "Cleaning up..."
        rm -rf venv __pycache__ *.pyc
        print_status "Cleanup completed"
        ;;
    "help")
        echo "Usage: $0 [setup|test|clean|help]"
        echo ""
        echo "Commands:"
        echo "  setup (default) - Full setup with virtual environment and tests"
        echo "  test           - Run tests only"
        echo "  clean          - Clean up generated files"
        echo "  help           - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac