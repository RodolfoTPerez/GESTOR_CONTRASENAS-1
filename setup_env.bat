@echo off
REM =============================================
REM Setup PassGuardian Python Environment
REM =============================================

echo.
echo [1/4] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo Python no esta instalado o no esta en PATH.
    pause
    exit /b
)

echo.
echo [2/4] Actualizando pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Desinstalando posibles versiones previas de PySide6...
pip uninstall -y PySide6

echo.
echo [4/4] Instalando dependencias requeridas...
REM Instala versión estable compatible con Python 3.11
pip install PySide6==6.6.0 cryptography python-dotenv

echo.
echo Entorno listo para ejecutar PassGuardian!
echo Para correr la app: python main.py
pause





