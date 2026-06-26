#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if .venv directory exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "Checking and installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting NexSupport Chatbot..."
python app.py
