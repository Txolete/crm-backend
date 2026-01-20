@echo off
REM ==================================================================
REM BACKUP_DB.bat - CRM Database Backup Script
REM PASO 9 - Automated backup with retention policy
REM ==================================================================

setlocal EnableDelayedExpansion

echo.
echo ==================================================================
echo CRM DATABASE BACKUP
echo ==================================================================
echo.

REM Configuration
set "DB_FILE=crm.db"
set "BACKUP_DIR=data\backups"
set "MAX_BACKUPS=30"

REM Check if database exists
if not exist "%DB_FILE%" (
    echo ERROR: Database file not found: %DB_FILE%
    echo.
    echo Make sure you are running this script from the CRM directory.
    pause
    exit /b 1
)

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" (
    echo Creating backup directory: %BACKUP_DIR%
    mkdir "%BACKUP_DIR%"
)

REM Generate timestamp (YYYYMMDD_HHMMSS)
for /f "tokens=1-6 delims=/: " %%a in ("%date% %time%") do (
    set TIMESTAMP=%%c%%a%%b_%%d%%e%%f
)
set TIMESTAMP=%TIMESTAMP: =0%

REM Backup filename
set "BACKUP_FILE=%BACKUP_DIR%\crm_%TIMESTAMP%.db"

echo Backing up database...
echo Source: %DB_FILE%
echo Target: %BACKUP_FILE%
echo.

REM Copy database
copy "%DB_FILE%" "%BACKUP_FILE%" >nul 2>&1

if %errorlevel% equ 0 (
    echo SUCCESS: Database backed up successfully!
    
    REM Get backup file size
    for %%A in ("%BACKUP_FILE%") do set FILESIZE=%%~zA
    set /a FILESIZE_MB=%FILESIZE% / 1048576
    echo Backup size: %FILESIZE_MB% MB
    echo.
    
    REM Clean old backups (keep only last MAX_BACKUPS)
    echo Cleaning old backups (keeping last %MAX_BACKUPS%)...
    
    REM Count existing backups
    set BACKUP_COUNT=0
    for %%F in ("%BACKUP_DIR%\crm_*.db") do set /a BACKUP_COUNT+=1
    
    echo Found %BACKUP_COUNT% backup(s)
    
    if %BACKUP_COUNT% gtr %MAX_BACKUPS% (
        set /a TO_DELETE=%BACKUP_COUNT%-%MAX_BACKUPS%
        echo Deleting !TO_DELETE! oldest backup(s)...
        
        REM Delete oldest backups
        set COUNTER=0
        for /f "delims=" %%F in ('dir /b /o:d "%BACKUP_DIR%\crm_*.db"') do (
            set /a COUNTER+=1
            if !COUNTER! leq !TO_DELETE! (
                echo   Deleting: %%F
                del "%BACKUP_DIR%\%%F" >nul 2>&1
            )
        )
        echo Cleanup completed!
    ) else (
        echo No cleanup needed.
    )
    
    echo.
    echo ==================================================================
    echo BACKUP COMPLETED SUCCESSFULLY
    echo ==================================================================
    echo.
    echo Backup location: %BACKUP_FILE%
    echo.
    
) else (
    echo.
    echo ERROR: Backup failed!
    echo Please check if the database file is locked by another process.
    echo.
    pause
    exit /b 1
)

REM Pause if run manually (not from Task Scheduler)
if "%1" neq "auto" (
    pause
)

exit /b 0
