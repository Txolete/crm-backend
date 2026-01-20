@echo off
REM ============================================
REM VERIFICADOR DE ARCHIVOS - FASE 2 PASO 3
REM ============================================

echo.
echo ====================================================
echo  VERIFICADOR DE ARCHIVOS
echo ====================================================
echo.

echo Verificando archivos...
echo.

REM Verificar dashboard.js
echo 1. Verificando dashboard.js...
findstr /C:"DESACTIVADO - Ahora se maneja en tasks.js" app\static\js\dashboard.js >nul
if %errorlevel%==0 (
    echo    [OK] dashboard.js esta actualizado
) else (
    echo    [ERROR] dashboard.js NO esta actualizado
    echo    Necesitas reemplazar: dashboard.js -^> app\static\js\dashboard.js
)

echo.

REM Verificar tasks.js
echo 2. Verificando tasks.js...
findstr /C:"function getCurrentUser" app\static\js\tasks.js >nul
if %errorlevel%==0 (
    echo    [OK] tasks.js esta actualizado
) else (
    echo    [ERROR] tasks.js NO esta actualizado
    echo    Necesitas reemplazar: tasks.js -^> app\static\js\tasks.js
)

echo.

REM Verificar dashboard.html
echo 3. Verificando dashboard.html...
findstr /C:"tasks.js" app\templates\dashboard.html >nul
if %errorlevel%==0 (
    echo    [OK] dashboard.html incluye tasks.js
) else (
    echo    [ERROR] dashboard.html NO incluye tasks.js
    echo    Necesitas reemplazar: dashboard.html -^> app\templates\dashboard.html
)

echo.
echo ====================================================
echo.
echo Si todos los archivos estan OK pero sigues viendo errores:
echo.
echo 1. LIMPIA LA CACHE DEL NAVEGADOR:
echo    - Presiona Ctrl+Shift+R en el dashboard
echo    - O presiona Ctrl+Shift+Delete y limpia cache
echo.
echo 2. REINICIA EL SERVIDOR:
echo    - Ctrl+C para detener
echo    - START_CRM.bat para iniciar
echo.
echo 3. ABRE EN MODO INCOGNITO:
echo    - Ctrl+Shift+N (Chrome)
echo    - Ctrl+Shift+P (Firefox)
echo.
echo ====================================================
echo.
pause
