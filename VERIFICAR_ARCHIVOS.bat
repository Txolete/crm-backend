@echo off
chcp 65001 >nul
echo =========================================
echo VERIFICADOR DE ARCHIVOS CRM
echo =========================================
echo.

setlocal enabledelayedexpansion
set errors=0

echo Verificando archivos críticos...
echo.

REM Verificar accounts.html
findstr /C:"taskModal" app\templates\accounts.html >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Modal de Tareas en accounts.html
    set /a errors+=1
) else (
    echo ✅ OK: Modal de Tareas en accounts.html
)

findstr /C:"taskForm" app\templates\accounts.html >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Formulario taskForm en modal
    set /a errors+=1
) else (
    echo ✅ OK: Formulario taskForm en modal
)

REM Verificar accounts.js
findstr /C:"loadAccountTasks" app\static\js\accounts.js >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Función loadAccountTasks en accounts.js
    set /a errors+=1
) else (
    echo ✅ OK: Función loadAccountTasks en accounts.js
)

findstr /C:"renderAccountTaskCard" app\static\js\accounts.js >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Función renderAccountTaskCard en accounts.js
    set /a errors+=1
) else (
    echo ✅ OK: Función renderAccountTaskCard en accounts.js
)

findstr /C:"opportunities_count" app\static\js\accounts.js >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Contador opportunities_count en accounts.js
    set /a errors+=1
) else (
    echo ✅ OK: Contador opportunities_count en accounts.js
)

REM Verificar tasks.js
findstr /C:"showCreateTaskModal" app\static\js\tasks.js >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Función showCreateTaskModal en tasks.js
    set /a errors+=1
) else (
    echo ✅ OK: Función showCreateTaskModal en tasks.js
)

REM Verificar backend
findstr /C:"opportunities_count" app\api\routes\accounts.py >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Contadores en accounts.py
    set /a errors+=1
) else (
    echo ✅ OK: Contadores en accounts.py
)

findstr /C:"opportunities_count" app\schemas\account.py >nul 2>&1
if errorlevel 1 (
    echo ❌ FALTA: Contadores en schema account.py
    set /a errors+=1
) else (
    echo ✅ OK: Contadores en schema account.py
)

echo.
echo =========================================
if !errors! equ 0 (
    echo ✅ TODOS LOS ARCHIVOS CORRECTOS
    echo.
    echo Si sigues teniendo problemas:
    echo 1. Detén el servidor ^(Ctrl+C^)
    echo 2. Reinicia: START_CRM.bat
    echo 3. Limpia caché del navegador:
    echo    - Ctrl+Shift+Delete
    echo    - Selecciona "Todo el tiempo"
    echo    - Marca "Caché e imágenes"
    echo    - Limpia
    echo 4. Cierra COMPLETAMENTE el navegador
    echo 5. Reabre el navegador
    echo 6. Vuelve a probar
) else (
    echo ⚠️ ENCONTRADOS !errors! PROBLEMAS
    echo.
    echo ACCIÓN REQUERIDA:
    echo 1. Los archivos con ❌ NO están actualizados
    echo 2. Reemplaza esos archivos desde la carpeta de descarga
    echo 3. Vuelve a ejecutar este script: VERIFICAR_ARCHIVOS.bat
)
echo =========================================
echo.
pause
