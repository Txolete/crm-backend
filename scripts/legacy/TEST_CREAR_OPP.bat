@echo off
echo ================================================================
echo TEST - CREAR OPORTUNIDAD
echo ================================================================
echo.
echo IMPORTANTE: El servidor debe estar corriendo
echo.
pause

call venv\Scripts\activate.bat
python test_crear_oportunidad.py

echo.
pause
