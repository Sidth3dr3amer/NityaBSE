#!/bin/bash

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r services/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# Start the Node.js server
echo "Starting Node.js server..."
node server.js
