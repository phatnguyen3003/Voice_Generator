@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo    Voice Generator - Automated Setup ^& Execution
echo ============================================================
echo.

cd /d "%~dp0"

:: 0. Check Python Installation
echo [0/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not added to your PATH.
    echo Please install Python 3.8 or higher from https://www.python.org
    pause
    exit /b 1
)
echo ✅ Python found.
echo.

:: 1. Create/Activate Virtual Environment
if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv || (
        echo ❌ Failed to create virtual environment.
        pause
        exit /b 1
    )
)
call "venv\Scripts\activate.bat"
echo ✅ Virtual environment activated.
echo.

:: 2. Upgrade Pip and Install Download Tools
echo [2/5] Installing download utilities...
python -m pip install --upgrade pip -q
python -m pip install huggingface_hub tqdm -q
echo ✅ Download utilities ready.
echo.

:: 3. Run the Model Downloader (download_models.py)
echo [3/5] Checking AI Model Checkpoints...
if not exist "checkpoints_v2\converter\checkpoint.pth" (
    echo ⚠️  Checkpoints missing. Starting automated download...
    python download_models.py
) else (
    echo ✅ OpenVoice V2 Checkpoints found.
)
echo.

:: 4. Install Project Dependencies
echo [4/5] Installing project dependencies...
python -m pip install -r requirements.txt --no-deps -q || (
    echo.
    echo ⚠️  Notice: Some minor version conflicts were detected and ignored.
)
echo ✅ Dependencies finalized.
echo.

:: 5. Ensure Web Directory Structure
echo [5/5] Organizing workspace folders...
for %%d in (processed used temp_edit temp_preview) do (
    if not exist "web\%%d" mkdir "web\%%d"
)
echo ✅ Directories verified.

echo.
echo ============================================================
echo    SETUP COMPLETE! Launching Voice Generator...
echo ============================================================
echo.

:: Run the Main Application immediately
python function.py

:: If the application crashes, keep the window open for debugging
if errorlevel 1 (
    echo.
    echo ❌ The application exited with an error.
    echo Check the logs above for details.
    pause
)

:: Optional: Remove the 'pause' below if you want the window to close 
:: automatically when you exit the app normally.
echo.
echo Application closed.
pause