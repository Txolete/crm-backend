@echo off
REM ============================================
REM DEBUGGER AUTOMÁTICO - ENDPOINTS DE TAREAS
REM ============================================

echo.
echo ====================================================
echo  DEBUGGER AUTOMÁTICO - ENDPOINTS DE TAREAS
echo ====================================================
echo.
echo Este script probará todos los endpoints de tareas
echo y generará un diagnóstico completo.
echo.
echo Requisitos:
echo   - Servidor CRM corriendo (START_CRM.bat)
echo   - Usuario admin con password admin123
echo.
pause

echo.
echo Instalando dependencias...
call venv\Scripts\activate.bat
pip install requests colorama --quiet

echo.
echo Ejecutando tests...
echo.
python test_tasks_api.py

echo.
echo.
echo ====================================================
echo  Test completado
echo ====================================================
echo.
pause
