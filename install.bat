@echo off
echo ========================================
echo  IQ Option AI Scanner - Instalacion
echo ========================================
echo.

echo [1/4] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no encontrado. Por favor instala Node.js v16 o superior.
    echo Descarga desde: https://nodejs.org/
    pause
    exit /b 1
)
echo ✓ Node.js detectado

echo.
echo [2/4] Instalando dependencias...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Fallo en la instalacion de dependencias
    pause
    exit /b 1
)
echo ✓ Dependencias instaladas

echo.
echo [3/4] Creando directorios necesarios...
if not exist "data" mkdir data
if not exist "data\candles" mkdir data\candles
if not exist "data\predictions" mkdir data\predictions
if not exist "data\performance" mkdir data\performance
if not exist "data\backups" mkdir data\backups
if not exist "logs" mkdir logs
if not exist "models" mkdir models
echo ✓ Directorios creados

echo.
echo [4/4] Configuracion inicial...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo ✓ Archivo .env creado desde plantilla
    echo.
    echo IMPORTANTE: Edita el archivo .env con tus credenciales de IQ Option
    echo.
) else (
    echo ✓ Archivo .env ya existe
)

echo.
echo ========================================
echo  INSTALACION COMPLETADA
echo ========================================
echo.
echo Proximos pasos:
echo 1. Editar .env con tus credenciales de IQ Option
echo 2. Ejecutar: npm start
echo 3. Abrir navegador en: http://localhost:3000
echo.
echo Para iniciar en modo desarrollo: npm run dev
echo.
pause
