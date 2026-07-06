# README – Vector Tile Export

This project has been exported using Vector Tiles.

Unlike the standard qgis2web export, this version must be served through
a web server and cannot be opened directly by double-clicking "index.html".

To make it easy to preview the map locally, three launcher scripts are provided:

* Windows: "show_map_with_server-win.bat"
* macOS:   "show_map_with_server-mac.command"
* Linux:   "show_map_with_server-linux.sh"

Double-click the script corresponding to your operating system.
The script will execute "start_server.py", which starts a local Python
web server and open the browser with the local address

*** Python must be installed on your system *** for the server to start correctly.


## Publishing on a Website

If you upload the entire folder to a web server, the map will be immediately
available by opening the "index.html" file and the three script are unnecessary

Example:

"https://www.example.com/my-map/index.html"