#!/bin/bash
# qgis2web - HTTP Server Launcher for Linux
# This script starts a local HTTP server to serve vector tiles (PBF)
# and opens the map in the default browser.
# This is needed because browsers block CORS requests when opening
# HTML files directly (file:// protocol) with PBF tiles.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "qgis2web - Local HTTP Server"
echo "============================================================"

python3 start_server.py index.html