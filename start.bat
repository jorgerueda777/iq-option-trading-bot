@echo off
title IQ Option AI Scanner
color 0A

echo.
echo  ██╗ ██████╗      ██████╗ ██████╗ ████████╗██╗ ██████╗ ███╗   ██╗
echo  ██║██╔═══██╗    ██╔═══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
echo  ██║██║   ██║    ██║   ██║██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║
echo  ██║██║▄▄ ██║    ██║   ██║██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║
echo  ██║╚██████╔╝    ╚██████╔╝██║        ██║   ██║╚██████╔╝██║ ╚████║
echo  ╚═╝ ╚══▀▀═╝      ╚═════╝ ╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
echo.
echo                     AI SCANNER v1.0
echo.
echo ========================================================================
echo.

REM Verificar si existe .env
if not exist ".env" (
    echo ERROR: Archivo .env no encontrado
    echo Por favor ejecuta install.bat primero
    echo.
    pause
    exit /b 1
)

REM Verificar si node_modules existe
if not exist "node_modules" (
    echo ERROR: Dependencias no instaladas
    echo Por favor ejecuta install.bat primero
    echo.
    pause
    exit /b 1
)

echo [INFO] Iniciando IQ Option AI Scanner...
echo [INFO] Dashboard disponible en: http://localhost:3000
echo [INFO] Presiona Ctrl+C para detener
echo.
echo ========================================================================
echo.

REM Iniciar la aplicacion
node src/main.js

echo.
echo ========================================================================
echo Scanner detenido. Presiona cualquier tecla para salir...
pause >nul
