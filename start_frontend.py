#!/usr/bin/env python3
"""
Simple HTTP server for serving the frontend on port 3000
This separates the frontend from the backend for better development workflow
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import time
from pathlib import Path

# Change to the frontend directory
frontend_dir = Path(__file__).parent / "frontend"
if not frontend_dir.exists():
    print("Error: frontend directory not found!")
    sys.exit(1)

os.chdir(frontend_dir)

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to set proper MIME types and CORS headers"""
    
    def end_headers(self):
        # Add CORS headers for API requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(200)
        self.end_headers()
    
    def guess_type(self, path):
        """Override to set correct MIME types"""
        if path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.css'):
            return 'text/css'
        elif path.endswith('.html'):
            return 'text/html'
        return super().guess_type(path)
    
    def log_message(self, format, *args):
        """Override to customize log messages"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def start_frontend_server():
    """Start the frontend development server"""
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 TikTok Aging App Frontend Server")
            print(f"📁 Serving files from: {frontend_dir}")
            print(f"🌐 Frontend URL: http://localhost:{PORT}")
            print(f"🔗 Backend API: http://localhost:8000")
            print(f"📋 Make sure the backend is running on port 8000")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print("-" * 50)
            
            # Optionally open browser after a short delay
            def open_browser():
                time.sleep(2)  # Wait for server to start
                try:
                    webbrowser.open(f'http://localhost:{PORT}')
                    print(f"🌐 Opened browser at http://localhost:{PORT}")
                except Exception as e:
                    print(f"Could not open browser: {e}")
            
            import threading
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Error: Port {PORT} is already in use!")
            print(f"💡 Try stopping any existing servers or change the port")
            print(f"🔍 Check what's using port {PORT}: netstat -ano | findstr :{PORT}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Frontend server stopped")
        sys.exit(0)

if __name__ == "__main__":
    start_frontend_server()
