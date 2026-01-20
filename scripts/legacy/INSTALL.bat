@echo off
cls
echo ================================================================================
echo                   INSTALACION Y SETUP COMPLETO DEL CRM
echo ================================================================================
echo.
echo Este script hara:
echo   1. Crear entorno virtual (si no existe)
echo   2. Instalar dependencias de Python
echo   3. Crear base de datos
echo   4. Inicializar todos los datos
echo.
echo EJECUTAR SOLO LA PRIMERA VEZ
echo.
echo ================================================================================
pause

echo.
echo ================================================================================
echo PASO 1: Verificando entorno virtual...
echo ================================================================================

REM Verificar si existe venv
if exist venv\ (
    echo    Entorno virtual encontrado
) else (
    echo    Creando entorno virtual...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: No se pudo crear el entorno virtual
        echo Verifica que Python este instalado: python --version
        pause
        exit /b 1
    )
    echo    Entorno virtual creado correctamente
)

echo.
echo ================================================================================
echo PASO 2: Activando entorno virtual...
echo ================================================================================
call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo    Entorno virtual activado

echo.
echo ================================================================================
echo PASO 3: Instalando dependencias de Python...
echo ================================================================================
echo.
echo Esto puede tardar 1-2 minutos...
echo.

python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se pudieron instalar las dependencias
    echo Verifica el archivo requirements.txt
    pause
    exit /b 1
)

echo    Dependencias instaladas correctamente

echo.
echo ================================================================================
echo PASO 4: Inicializando base de datos y datos maestros...
echo ================================================================================
echo.

python setup.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Fallo la inicializacion
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo.
echo   ███████ ██   ██ ██ ████████  ██████  
echo   ██       ██ ██  ██    ██    ██    ██ 
echo   █████     ███   ██    ██    ██    ██ 
echo   ██       ██ ██  ██    ██    ██    ██ 
echo   ███████ ██   ██ ██    ██     ██████  
echo.
echo ================================================================================
echo.
echo Siguiente paso: Ejecuta START_CRM.bat para arrancar el servidor
echo.
echo ================================================================================
pause
