@echo off
REM ============================================
REM DIAGNÓSTICO SQL PROFUNDO - BASE DE DATOS
REM ============================================

echo.
echo ====================================================
echo  DIAGNÓSTICO SQL PROFUNDO - BASE DE DATOS
echo ====================================================
echo.
echo Este script revisa DIRECTAMENTE la base de datos
echo para ver por qué los nombres no se cargan.
echo.
pause

echo.
echo Ejecutando diagnóstico...
echo.
call venv\Scripts\activate.bat
python debug_database.py

echo.
echo.
echo ====================================================
echo  Diagnóstico completado
echo ====================================================
echo.
pause
