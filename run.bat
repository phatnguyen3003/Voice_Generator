@echo off
title Edge-TTS AI Generator Studio Launcher

echo ======================================================
echo    Edge-TTS AI Generator Studio - Launcher
echo ======================================================

REM 1. Kiem tra Python
echo [*] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher.
    pause
    exit /b
)

REM 2. Tao moi truong ao neu chua co
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment found.
)

REM 3. Kich hoat va cai dat thu vien
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat

REM Cap nhat pip
python -m pip install --upgrade pip

REM Cai dat tu requirements.txt
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

REM 4. Tai Models va Cong cu
echo [3/4] Checking FFmpeg and AI Models...
python function/download_models.py
if errorlevel 1 (
    echo [ERROR] Model download failed.
    pause
    exit /b
)

REM 5. Chay ung dung
echo [4/4] Launching App...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed.
    pause
)

echo.
echo Launching finished.
pause
