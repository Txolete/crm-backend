@echo off
echo ================================================================
echo DEBUGGING COMPLETO DEL CRM
echo ================================================================
echo.

call venv\Scripts\activate.bat

echo.
echo ================================================================
echo PASO 1: Verificando base de datos...
echo ================================================================
python debug_01_database.py
echo.
pause

echo.
echo ================================================================
echo PASO 2: Verificando APIs...
echo ================================================================
echo IMPORTANTE: El servidor debe estar corriendo en otra ventana
echo Presiona cualquier tecla cuando el servidor este arrancado...
pause
python debug_02_apis.py
echo.
pause

echo.
echo ================================================================
echo PASO 3: Debug profundo del Kanban...
echo ================================================================
python debug_03_kanban_deep.py
echo.
pause

echo.
echo ================================================================
echo DEBUGGING COMPLETADO
echo ================================================================
echo.
echo Envia los resultados de los 3 pasos a Claude para diagnostico
echo.
pause
