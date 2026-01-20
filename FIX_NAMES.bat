@echo off
REM ============================================
REM REPARAR NOMBRES DE OPORTUNIDADES
REM ============================================

echo.
echo ====================================================
echo  REPARAR NOMBRES DE OPORTUNIDADES
echo ====================================================
echo.
echo Este script asignara nombres automaticamente a todas
echo las oportunidades que tienen name = NULL
echo.
echo Formato: [Nombre Cuenta] - Oportunidad
echo.
echo IMPORTANTE:
echo   - Se creara un backup automatico de la BD
echo   - Podras revisar los cambios antes de confirmar
echo.
pause

echo.
echo Ejecutando reparacion...
echo.
call venv\Scripts\activate.bat
python fix_opportunity_names.py

echo.
echo.
echo ====================================================
echo  Proceso completado
echo ====================================================
echo.
echo Ahora ejecuta:
echo   1. START_CRM.bat  (reiniciar servidor)
echo   2. TEST_TASKS.bat (verificar que funciona)
echo.
pause
