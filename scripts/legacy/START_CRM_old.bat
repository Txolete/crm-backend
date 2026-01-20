@echo off
REM ==================================================================
REM START_CRM.bat - CRM Application Startup Script
REM PASO 9 - Production-ready startup with auto-setup
REM ==================================================================

setlocal EnableDelayedExpansion

echo.
echo ==================================================================
echo CRM SEGUIMIENTO CLIENTES - STARTUP
echo Version 0.7.0
echo ==================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/5] Python detected
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo [2/5] Virtual environment found
)

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements need to be installed
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [4/5] Installing dependencies...
    echo This may take a few minutes on first run...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo [4/5] Dependencies already installed
)

REM Create necessary directories
if not exist "data" mkdir data
if not exist "data\backups" mkdir data\backups
if not exist "data\uploads" mkdir data\uploads
if not exist "logs" mkdir logs

echo [5/5] Starting CRM application...
echo.
echo ==================================================================
echo CRM IS STARTING
echo ==================================================================
echo.
echo Access the CRM at: http://localhost:8000
echo.
echo The browser will open automatically in 5 seconds...
echo.
echo Press Ctrl+C to stop the server
echo ==================================================================
echo.

REM Wait 5 seconds then open browser
start /b cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8000"

REM Start uvicorn in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info

REM Cleanup on exit
echo.
echo CRM application stopped.
pause
