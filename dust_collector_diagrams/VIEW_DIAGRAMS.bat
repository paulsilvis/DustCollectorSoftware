@echo off
REM Simple launcher for the diagram viewer on Windows
REM This starts a local web server and opens the viewer in your browser

echo Starting local web server...
echo Press Ctrl+C to stop the server when done
echo.

REM Try to find Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Opening diagrams viewer at http://localhost:8000/diagrams_viewer_simple.html
    echo.
    
    REM Start browser after a delay
    start /min cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000/diagrams_viewer_simple.html"
    
    REM Start server
    python -m http.server 8000
    
) else (
    echo Error: Python not found!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Or just open the PNG files directly in your image viewer:
    echo   - system_diagram_enhanced.png
    echo   - dataflow_diagram.png
    echo   - state_machine.png
    pause
    exit /b 1
)
