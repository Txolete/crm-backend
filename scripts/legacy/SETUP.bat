@echo off
cls
echo ================================================================================
echo                          SETUP INICIAL DEL CRM
echo ================================================================================
echo.
echo ATENCION: Si es la PRIMERA VEZ que instalas el CRM, debes ejecutar:
echo.
echo    INSTALL.bat
echo.
echo Este archivo (SETUP.bat) solo se usa si ya tienes las dependencias instaladas.
echo.
echo ================================================================================
echo.
echo Si ya ejecutaste INSTALL.bat antes, presiona una tecla para continuar
echo Si NO, cierra esta ventana y ejecuta INSTALL.bat
echo.
pause

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se encontro el entorno virtual
    echo Por favor ejecuta INSTALL.bat primero
    pause
    exit /b 1
)

echo.
python setup.py

echo.
echo ================================================================================
echo PRESIONA UNA TECLA PARA CERRAR
echo ================================================================================
pause
