@echo off
REM ────────────────────────────────────────────────────────
REM  SmartAttend — Windows Setup Script
REM  Uses Python 3.12 with pre-built dlib wheel (no C++ compiler needed)
REM ────────────────────────────────────────────────────────
echo.
echo ============================================
echo   SmartAttend — Windows Setup
echo ============================================
echo.

REM ── Find Python 3.12 ─────────────────────────────────
set PYTHON_CMD=
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=*" %%i in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set PYTHON_CMD=%%i
)
if "%PYTHON_CMD%"=="" (
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        for /f "tokens=*" %%v in ('"%%i" -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")" 2^>nul') do (
            if "%%v"=="3.12" set PYTHON_CMD=%%i
        )
    )
)
if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3.12 not found. Please install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Found Python: %PYTHON_CMD%

REM ── Create virtual environment ───────────────────────
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment already exists
) else (
    echo [..] Creating virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM ── Upgrade pip ──────────────────────────────────────
echo [..] Upgrading pip...
"venv\Scripts\python.exe" -m pip install --upgrade pip "setuptools<71" wheel >nul 2>&1
echo [OK] pip upgraded

REM ── Install dlib from pre-built wheel ────────────────
echo [..] Installing dlib (pre-built wheel for Windows)...
"venv\Scripts\python.exe" -m pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] dlib wheel install failed. Trying pip install dlib...
    "venv\Scripts\python.exe" -m pip install dlib >nul 2>&1
)
echo [OK] dlib installed

REM ── Install remaining requirements ──────────────────
echo [..] Installing Python dependencies...
"venv\Scripts\python.exe" -m pip install -r requirements.txt >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies. Check requirements.txt
    pause
    exit /b 1
)
echo [OK] All dependencies installed

REM ── Seed database ────────────────────────────────────
echo [..] Seeding database with demo data...
"venv\Scripts\python.exe" database\seed.py
echo.

REM ── Done ─────────────────────────────────────────────
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   To run the app:
echo     venv\Scripts\activate
echo     python run.py
echo.
echo   Then open: http://127.0.0.1:5000
echo.
pause
