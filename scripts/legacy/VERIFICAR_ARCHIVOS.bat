@echo off
echo ================================================================
echo VERIFICACIÓN DE ARCHIVOS
echo ================================================================
echo.

call venv\Scripts\activate.bat
python verificar_archivos.py

echo.
pause
