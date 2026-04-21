# SmartAttend — Run Script for Windows PowerShell
# Double-click this file OR run it from any terminal:
#   powershell -ExecutionPolicy Bypass -File start.ps1

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   SmartAttend - Starting Server..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check venv exists
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    Write-Host "Please run setup_windows.bat first." -ForegroundColor Yellow
    Pause
    exit 1
}

Write-Host "[OK] Virtual environment found" -ForegroundColor Green
Write-Host "[..] Starting Flask server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Open your browser at: http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "  Demo Credentials:" -ForegroundColor White
Write-Host "    Admin:   admin@university.edu  / admin123" -ForegroundColor Gray
Write-Host "    Teacher: sharma@university.edu / teacher123" -ForegroundColor Gray
Write-Host "    Student: rohan@student.edu     / student123" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press CTRL+C to stop the server" -ForegroundColor DarkGray
Write-Host "--------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

& ".\venv\Scripts\python.exe" run.py
