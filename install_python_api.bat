@echo off
echo Instalando IQ Option API para Python...
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python desde https://python.org
    pause
    exit /b 1
)

echo Python encontrado. Instalando dependencias...
echo.

REM Instalar pip si no está disponible
python -m ensurepip --upgrade >nul 2>&1

REM Instalar la API de IQ Option
echo Instalando iqoptionapi...
pip install iqoptionapi

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo instalar iqoptionapi
    echo Intentando con método alternativo...
    pip install git+https://github.com/iqoptionapi/iqoptionapi.git
)

echo.
echo Instalación completada!
echo.
echo IMPORTANTE: 
echo 1. Edita el archivo src/connectors/iqOptionPython.py
echo 2. Cambia "tu_password" por tu contraseña real de IQ Option
echo 3. Asegúrate de que el email sea correcto
echo.
pause
