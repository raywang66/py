@echo off
echo ============================================
echo ChromaCloud v1.1 - Folder Auto-Scan
echo ============================================
echo.
echo Starting ChromaCloud with folder monitoring...
echo.

cd /d "%~dp0"
python CC_Main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start ChromaCloud
    echo.
    echo Possible issues:
    echo 1. Python not installed or not in PATH
    echo 2. Dependencies missing - run: pip install -r requirements_cc.txt
    echo 3. Check error messages above
    echo.
    pause
)
