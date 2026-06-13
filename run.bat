@echo off
chcp 65001 >nul 2>&1

if not exist ".venv" (
    echo [!] .venv bulunamadi. Once kurulumu yapin: setup.ps1
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

if "%1"=="--dev" (
    python dev.py
) else (
    pythonw main.py %*
    if errorlevel 1 python main.py %*
)
