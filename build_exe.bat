@echo off
echo ========================================
echo   Vultrax Core - Executable Builder
echo ========================================
echo.
echo Cleaning old build artifacts...
if exist dist del /q dist\*
if exist build rd /s /q build
echo.
echo Starting PyInstaller build...
pyinstaller --clean VultraxCore.spec
echo.
echo Build process finished.
if exist dist\VultraxCore.exe (
    echo [SUCCESS] VultraxCore.exe generated in dist/
) else (
    echo [ERROR] Failed to generate VultraxCore.exe
)
pause
