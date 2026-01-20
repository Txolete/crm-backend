@echo off
echo ================================================================================
echo                REPARACION AUTOMATICA DE LA BASE DE DATOS
echo ================================================================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

echo [1/3] Diagnosticando base de datos...
echo.
python diagnose_database.py
echo.
echo ================================================================================
echo.

echo [2/3] Creando/verificando tablas...
echo.
python create_tables.py
echo.
echo ================================================================================
echo.

echo [3/3] Migrando campos de accounts...
echo.
python migrate_accounts_fields.py
echo.
echo ================================================================================
echo.

echo.
echo ================================================================================
echo                     REPARACION COMPLETADA
echo ================================================================================
echo.
echo Siguiente paso: Reiniciar el servidor
echo    START_CRM.bat
echo.
echo Presiona cualquier tecla para salir...
pause >nul
