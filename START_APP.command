#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Belmont County Mugshot Helper"
echo "========================================"
echo ""
echo "Starting the app..."
echo ""

# Open browser
open http://127.0.0.1:5000

# Start the app
python3 app.py

echo ""
echo "App stopped. You can close this window."
read -p "Press Enter to close..."
