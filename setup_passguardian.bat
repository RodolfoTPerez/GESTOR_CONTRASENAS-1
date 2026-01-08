@echo off
REM ===================================================
REM Setup completo PassGuardian - Python 3.10 + Entorno
REM ===================================================

echo.
echo ============================================
echo 1/6 - Verificando Python 3.10...
echo ============================================

REM Chequear si python 3.10 esta disponible
where python
python --version | findstr "3.10"
if %errorlevel% neq 0 (
    echo.
    echo Python 3.10 no encontrado. Debes instalarlo primero desde:
    echo https://www.python.org/downloads/release/python-31012/
    pause
    exit /b
)

echo.
echo ============================================
echo 2/6 - Creando entorno virtual PassGuardian
echo ============================================
cd /d C:\PassGuardian
python -m venv venv

echo.
echo ============================================
echo 3/6 - Activando entorno virtual
echo ============================================
call venv\Scripts\activate

echo.
echo ============================================
echo 4/6 - Actualizando pip
echo ============================================
python -m pip install --upgrade pip

echo.
echo ============================================
echo 5/6 - Instalando dependencias
echo ============================================
pip install PySide6==6.6.0 cryptography python-dotenv

echo.
echo ============================================
echo 6/6 - Entorno listo
echo ============================================
echo Para ejecutar PassGuardian:
echo 1. Activar entorno: call C:\PassGuardian\venv\Scripts\activate
echo 2. Ejecutar: python main.py
pause
