@echo off
echo ============================================================
echo Cleaning Python Cache...
echo ============================================================
cd /d "%~dp0"

REM Remove all __pycache__ directories
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

REM Remove all .pyc files
del /s /q *.pyc 2>nul

echo.
echo ============================================================
echo Cache Cleaned!
echo ============================================================
echo.
echo Starting CC_MainApp_v2_simple.py...
echo.
echo IMPORTANT: Watch for these log lines during batch analysis:
echo   INFO: Saturation: vl=X.X, l=X.X, n=X.X, h=X.X, vh=X.X
echo.
echo If saturation values are NON-ZERO, it's working correctly!
echo ============================================================
echo.

python CC_MainApp_v2_simple.py

pause
