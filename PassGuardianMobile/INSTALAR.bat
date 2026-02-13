@echo off
echo ========================================
echo   PASSGUARDIAN MOBILE - INSTALACION
echo ========================================
echo.

echo [1/3] Instalando dependencias...
call npm install

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se pudo instalar npm
    echo SOLUCION: Ejecuta PowerShell como Administrador y corre:
    echo   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
    pause
    exit /b 1
)

echo.
echo [2/3] Limpiando cache...
call npx expo start --clear

echo.
echo ========================================
echo   INSTALACION COMPLETA!
echo ========================================
echo.
echo PROXIMOS PASOS:
echo 1. Instala "Expo Go" en tu telefono (App Store / Play Store)
echo 2. Escanea el QR code que aparece arriba
echo 3. La app se abrira en tu telefono!
echo.
pause
