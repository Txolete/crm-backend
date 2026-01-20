@echo off
echo ================================================================
echo VERIFICACION DEL SISTEMA
echo ================================================================
echo.

call venv\Scripts\activate.bat
python verificar.py

echo.
pause
