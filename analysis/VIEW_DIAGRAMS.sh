#!/bin/bash
# Simple launcher for the diagram viewer
# This starts a local web server and opens the viewer in your browser

echo "Starting local web server..."
echo "Press Ctrl+C to stop the server when done"
echo ""

# Try to find Python
if command -v python3 &> /dev/null; then
    echo "Opening diagrams viewer at http://localhost:8000/diagrams_viewer.html"
    echo ""
    
    # Try to open browser (works on most systems)
    sleep 2 && (xdg-open http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                open http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                start http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                echo "Please open http://localhost:8000/diagrams_viewer.html in your browser") &
    
    # Start server
    python3 -m http.server 8000
    
elif command -v python &> /dev/null; then
    echo "Opening diagrams viewer at http://localhost:8000/diagrams_viewer.html"
    echo ""
    
    sleep 2 && (xdg-open http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                open http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                start http://localhost:8000/diagrams_viewer.html 2>/dev/null || \
                echo "Please open http://localhost:8000/diagrams_viewer.html in your browser") &
    
    python -m SimpleHTTPServer 8000
    
else
    echo "Error: Python not found!"
    echo ""
    echo "Please install Python, or just open the PNG files directly:"
    echo "  - system_diagram_enhanced.png"
    echo "  - dataflow_diagram.png"
    echo "  - state_machine.png"
    exit 1
fi
