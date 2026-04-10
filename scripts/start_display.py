#!/usr/bin/env python3
"""
Start the Hobbit Journey Display
Starts a simple HTTP server and opens the display in a browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        # Enable CORS for development
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


def main():
    # First, make sure stream_scenes.json exists
    if not Path('../data/stream_scenes.json').exists():
        print("📖 stream_scenes.json not found. Running export...")
        os.system('python export_stream_data.py')
    
    # Start server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/display.html"
        print(f"\n🧙 The Hobbit Journey Stream")
        print(f"=" * 40)
        print(f"Server running at: {url}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 40 + "\n")
        
        # Open browser
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Safe travels!")


if __name__ == "__main__":
    main()
