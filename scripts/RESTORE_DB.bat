@echo off
REM ==================================================================
REM RESTORE_DB.bat - CRM Database Restore Script
REM PASO 9 - Restore database from backup with safety checks
REM ==================================================================

setlocal EnableDelayedExpansion

echo.
echo ==================================================================
echo CRM DATABASE RESTORE
echo ==================================================================
echo.

REM Configuration
set "DB_FILE=crm.db"
set "BACKUP_DIR=data\backups"

REM Check if backup directory exists
if not exist "%BACKUP_DIR%" (
    echo ERROR: Backup directory not found: %BACKUP_DIR%
    echo.
    echo No backups available to restore.
    pause
    exit /b 1
)

REM List available backups
echo Available backups:
echo.
set BACKUP_COUNT=0
for /f "delims=" %%F in ('dir /b /o:-d "%BACKUP_DIR%\crm_*.db" 2^>nul') do (
    set /a BACKUP_COUNT+=1
    echo [!BACKUP_COUNT!] %%F
    set "BACKUP_!BACKUP_COUNT!=%%F"
)

if %BACKUP_COUNT% equ 0 (
    echo No backup files found in %BACKUP_DIR%
    pause
    exit /b 1
)

echo.
echo ==================================================================
echo.

REM Ask user to select backup
set /p SELECTION="Enter backup number to restore (or Q to quit): "

if /i "%SELECTION%"=="Q" (
    echo Restore cancelled.
    exit /b 0
)

REM Validate selection
if "%SELECTION%"=="" goto :invalid_selection
set /a TEST=%SELECTION% 2>nul
if %TEST% lss 1 goto :invalid_selection
if %TEST% gtr %BACKUP_COUNT% goto :invalid_selection

REM Get selected backup
set BACKUP_FILE=!BACKUP_%SELECTION%!
set FULL_BACKUP_PATH=%BACKUP_DIR%\%BACKUP_FILE%

echo.
echo Selected backup: %BACKUP_FILE%
echo.

REM Final confirmation
echo ==================================================================
echo WARNING: This will replace your current database!
echo ==================================================================
echo.
echo Current database: %DB_FILE%
echo Backup to restore: %FULL_BACKUP_PATH%
echo.
set /p CONFIRM="Are you SURE you want to continue? (YES/no): "

if /i not "%CONFIRM%"=="YES" (
    echo.
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo ==================================================================
echo STARTING RESTORE PROCESS
echo ==================================================================
echo.

REM Step 1: Create safety backup of current database
if exist "%DB_FILE%" (
    echo Step 1: Creating safety backup of current database...
    
    for /f "tokens=1-6 delims=/: " %%a in ("%date% %time%") do (
        set TIMESTAMP=%%c%%a%%b_%%d%%e%%f
    )
    set TIMESTAMP=%TIMESTAMP: =0%
    
    set SAFETY_BACKUP=%BACKUP_DIR%\crm_before_restore_%TIMESTAMP%.db
    
    copy "%DB_FILE%" "!SAFETY_BACKUP!" >nul 2>&1
    
    if %errorlevel% equ 0 (
        echo   SUCCESS: Safety backup created
        echo   Location: !SAFETY_BACKUP!
    ) else (
        echo   ERROR: Failed to create safety backup!
        echo   Restore aborted for safety.
        pause
        exit /b 1
    )
) else (
    echo Step 1: No existing database found, skipping safety backup.
)

echo.
echo Step 2: Restoring database from backup...

REM Step 2: Restore from backup
copy "%FULL_BACKUP_PATH%" "%DB_FILE%" >nul 2>&1

if %errorlevel% equ 0 (
    echo   SUCCESS: Database restored successfully!
    echo.
    echo ==================================================================
    echo RESTORE COMPLETED SUCCESSFULLY
    echo ==================================================================
    echo.
    echo Database has been restored from: %BACKUP_FILE%
    
    if defined SAFETY_BACKUP (
        echo.
        echo Safety backup of previous database saved to:
        echo !SAFETY_BACKUP!
        echo.
        echo You can delete this safety backup once you verify the restore.
    )
    
    echo.
    echo IMPORTANT: Restart the CRM application for changes to take effect.
    echo.
    
) else (
    echo   ERROR: Restore failed!
    echo.
    echo The current database was NOT modified.
    
    if defined SAFETY_BACKUP (
        echo Safety backup remains at: !SAFETY_BACKUP!
    )
    
    pause
    exit /b 1
)

pause
exit /b 0

:invalid_selection
echo.
echo ERROR: Invalid selection. Please enter a number between 1 and %BACKUP_COUNT%
echo.
pause
exit /b 1
