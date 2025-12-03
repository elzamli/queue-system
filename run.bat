@echo off
REM Windows Batch Script for Queue Management System

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or newer
    pause
    exit /b 1
)

echo OK: Python found

echo.
echo Installing requirements...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

echo OK: Requirements installed

echo.
echo Starting Queue Management System...
echo Navigate to: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
pause
