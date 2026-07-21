@echo off
title Sharky Checker - by SharkySolvers
color 0A

echo.
echo  ================================================
echo   Sharky Checker - by SharkySolvers
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

if not exist "venv" (
    echo  [*] Setting up virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo  [*] Installing dependencies...
    pip install -r scripts\requirements.txt --quiet
) else (
    call venv\Scripts\activate.bat
)

echo  [*] Launching...
echo.
python main.py

pause
