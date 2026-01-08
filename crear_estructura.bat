@echo off
REM =====================================================
REM Script para crear la estructura de carpetas de PassGuardian
REM =====================================================

SET ROOT=C:\PassGuardian

REM Crear carpetas principales
mkdir "%ROOT%"
mkdir "%ROOT%\src"
mkdir "%ROOT%\tests"
mkdir "%ROOT%\docs"
mkdir "%ROOT%\config"
mkdir "%ROOT%\scripts"

REM Crear subcarpetas dentro de src
mkdir "%ROOT%\src\domain"
mkdir "%ROOT%\src\application"
mkdir "%ROOT%\src\infrastructure"
mkdir "%ROOT%\src\presentation"

echo.
echo ========================================
echo Estructura de carpetas creada correctamente
echo ========================================
pause
