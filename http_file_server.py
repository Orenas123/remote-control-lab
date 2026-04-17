"""
Project: Remote Control System
Component: HTTP File Server
Description:
    Simple HTTP server that serves files from the current directory.
"""

# ========================
# Imports
# ========================
import http.server
import socketserver

# ========================
# Configuration
# ========================
PORT = 8000
HANDLER = http.server.SimpleHTTPRequestHandler

# ========================
# Server Logic
# ========================
def run_server():
    with socketserver.TCPServer(("", PORT), HANDLER) as httpd:
        print(f"[+] Serving at port {PORT}")
        httpd.serve_forever()

# ========================
# Entry Point
# ========================
if __name__ == "__main__":
    run_server()