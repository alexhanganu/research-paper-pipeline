#!/bin/bash
# Cross-platform launcher script for Linux and macOS
# Usage: ./run_pipeline.sh [options]

set -e

echo "=========================================="
echo "Research Paper Processing Pipeline"
echo "Platform: $(uname -s)"
echo "=========================================="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "Warning: .env file not found"
    echo "Create a .env file with your API keys:"
    echo "  ANTHROPIC_API_KEY=your-key-here"
    echo "  OPENAI_API_KEY=your-key-here"
    echo ""
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check what to run
if [ "$1" == "gui" ]; then
    echo ""
    echo "Starting GUI application..."
    python3 project/scripts/windows_app.py
elif [ "$1" == "dashboard" ]; then
    echo ""
    echo "Starting monitoring dashboard..."
    streamlit run monitoring_dashboard.py
else
    echo ""
    echo "Starting command-line pipeline..."
    python3 project/scripts/process_papers.py "${@}"
fi