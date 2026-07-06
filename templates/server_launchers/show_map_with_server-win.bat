@echo off
REM qgis2web - HTTP Server Launcher for Windows
REM This script starts a local HTTP server to serve vector tiles (PBF)
REM and opens the map in the default browser.
REM This is needed because browsers block CORS requests when opening
REM HTML files directly (file:// protocol) with PBF tiles.

set SERVER_DIR=%~dp0
echo Starting HTTP server on directory: %SERVER_DIR%
python "%SERVER_DIR%start_server.py" index.html
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Python not found. Please install Python and try again.
    pause
)