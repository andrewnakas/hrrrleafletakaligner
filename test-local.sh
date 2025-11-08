#!/bin/bash
# Quick local testing script

echo "Downloading and processing HRRR data..."
python scripts/download_hrrr.py

echo ""
echo "Starting local web server..."
echo "Open http://localhost:8000 in your browser"
echo "Press Ctrl+C to stop"
echo ""

cd public && python3 -m http.server 8000
