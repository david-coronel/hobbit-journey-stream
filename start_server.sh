#!/bin/bash

# The Hobbit Journey Stream - Unified Server Launcher
# Serves both the main stream client and the timeline/prototypes from Flask on :5000

cd "$(dirname "$0")"

echo "=================================="
echo "  The Hobbit Journey Stream"
echo "  Unified Server Launcher"
echo "=================================="
echo ""

# Check Python dependencies
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask flask-cors --quiet
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install pyyaml --quiet
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing requests..."
    pip3 install requests --quiet
fi

if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "Installing python-dotenv..."
    pip3 install python-dotenv --quiet
fi

echo "Starting unified server..."
echo ""
echo "Available endpoints:"
echo "  Stream client:        http://localhost:5000"
echo "  Timeline (gaps):      http://localhost:5000/prototypes/timeline_canon_gaps.html"
echo "  API (events):         http://localhost:5000/api/events/range"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

python3 scripts/stream_server.py
