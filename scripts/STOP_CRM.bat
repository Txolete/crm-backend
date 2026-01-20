@echo off
REM ==================================================================
REM STOP_CRM.bat - CRM Application Stop Script
REM PASO 9 - Stop CRM server gracefully
REM ==================================================================

echo.
echo ==================================================================
echo STOPPING CRM APPLICATION
echo ==================================================================
echo.

REM Find and kill uvicorn/python processes running on port 8000
echo Looking for CRM process...

REM Find process using port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    set PID=%%a
)

if defined PID (
    echo Found CRM process (PID: %PID%)
    echo Stopping process...
    taskkill /PID %PID% /F >nul 2>&1
    
    if %errorlevel% equ 0 (
        echo.
        echo ==================================================================
        echo CRM APPLICATION STOPPED SUCCESSFULLY
        echo ==================================================================
    ) else (
        echo ERROR: Failed to stop process
    )
) else (
    echo No CRM process found on port 8000
    echo.
    echo The CRM may not be running, or it's using a different port.
)

echo.
pause
