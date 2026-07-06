#!/usr/bin/env python3
"""
qgis2web - Local HTTP Server for PBF Vector Tiles

Starts a local HTTP server in the current directory and opens the
specified HTML file (default: index.html) in the default browser.

This is necessary because browsers block CORS requests when opening
HTML files via file:// protocol, which prevents loading PBF tiles.

Usage:
    python start_server.py [index_file]

Press Ctrl+C to stop the server or close the terminal window.
"""

import http.server
import socketserver
import socket
import webbrowser
import threading
import os
import sys


def find_free_port():
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def open_browser(url, delay=0.5):
    """Open the browser after a short delay (to let the server start)."""
    timer = threading.Timer(delay, lambda: webbrowser.open(url))
    timer.start()


def main():
    # Determine the directory where this script is located
    server_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_dir)

    # Determine which HTML file to open
    index_file = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    index_path = os.path.join(server_dir, index_file)

    if not os.path.exists(index_path):
        print("Warning: {} not found in this directory.".format(index_file))
        print("Open http://localhost:{}/ manually.".format(
            find_free_port()))
        return 1

    # Find a free port
    port = find_free_port()
    url = "http://localhost:{}/{}".format(port, index_file)

    print("=" * 60)
    print("qgis2web - Local HTTP Server")
    print("=" * 60)
    print("Serving directory: {}".format(server_dir))
    print("Server URL:       http://localhost:{}".format(port))
    print("Map URL:          {}".format(url))
    print("Press Ctrl+C to stop the server or close the terminal window.")
    print("=" * 60)

    # Start the HTTP server
    Handler = http.server.SimpleHTTPRequestHandler

    # Suppress default HTTP server logs
    class QuietHandler(Handler):
        def log_message(self, format, *args):
            pass

    try:
        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            # Open the browser
            open_browser(url)
            # Serve until interrupted
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except OSError as e:
        print("Error starting server: {}".format(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())