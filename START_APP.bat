@echo off
title Belmont County Mugshot Helper
cd /d "%~dp0"

echo ========================================
echo   Belmont County Mugshot Helper
echo ========================================
echo.
echo Starting the app...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b
)

REM Start the app in the background and open the browser
start "" http://127.0.0.1:5000
python app.py

pause
