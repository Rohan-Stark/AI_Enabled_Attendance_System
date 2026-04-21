@echo off
REM SmartAttend — Run Script for Windows CMD
REM Double-click this file OR run from terminal: start.bat

cd /d "%~dp0"

echo.
echo ============================================
echo   SmartAttend - Starting Server...
echo ============================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

echo [OK] Virtual environment found
echo [..] Starting Flask server...
echo.
echo   Open your browser at: http://127.0.0.1:5000
echo.
echo   Demo Credentials:
echo     Admin:   admin@university.edu  / admin123
echo     Teacher: sharma@university.edu / teacher123
echo     Student: rohan@student.edu     / student123
echo.
echo   Press CTRL+C to stop the server
echo --------------------------------------------
echo.

venv\Scripts\python.exe run.py
pause
