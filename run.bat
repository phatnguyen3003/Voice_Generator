@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo      VOICE GENERATOR - FULL SETUP (MODELS + DEPENDENCIES)
echo ============================================================

:: 1. Kiểm tra và Kích hoạt môi trường ảo
if not exist "venv" (
    echo [1/6] Đang tạo môi trường ảo mới...
    python -m venv venv
)
call "venv\Scripts\activate.bat"
echo ✅ Đã kích hoạt môi trường ảo.

:: 2. Cài đặt Torch CPU (Bắt buộc phải cài đúng bản này trước)
echo [2/6] Đang cài đặt PyTorch (Bản CPU)...
python -m pip install torch==2.5.1 torchaudio==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu --quiet
echo ✅ Hoàn thành cài đặt Torch.

:: 3. Cài đặt các thư viện lõi để chạy script tải model và giao diện
echo [3/6] Cài đặt thư viện hỗ trợ tải và giao diện...
python -m pip install eel edge-tts librosa unidecode huggingface_hub tqdm --quiet
echo ✅ Thư viện hỗ trợ sẵn sàng.

:: 4. Kiểm tra và tải Checkpoint OpenVoice V2
echo [4/6] Kiểm tra AI Model Checkpoints...
:: Kiểm tra sự tồn tại của model chính, nếu thiếu sẽ chạy script tải
if not exist "checkpoints_v2\converter\checkpoint.pth" (
    echo ⚠️ Checkpoint missing. Đang chạy download_models.py...
    python download_models.py
    if errorlevel 1 (
        echo ❌ Lỗi khi tải Model. Kiểm tra kết nối mạng hoặc Git!
        pause
        exit /b 1
    )
    echo ✅ Đã tải xong Model Checkpoints.
) else (
    echo ✅ OpenVoice V2 Checkpoints đã tồn tại.
)

:: 5. Cài đặt cưỡng chế từng dòng từ requirements.txt
echo [5/6] Đang cài đặt toàn bộ danh sách thư viện (Bỏ qua xung đột)...
for /f "tokens=*" %%i in (requirements.txt) do (
    set "line=%%i"
    if not "!line!"=="" (
        echo !line! | findstr /i "torch" >nul
        if errorlevel 1 (
            python -m pip install "!line!" --no-deps --quiet --prefer-binary
        )
    )
)
echo ✅ Cấu trúc thư viện đã hoàn tất.

:: 6. Khởi chạy ứng dụng
echo [6/6] Đang khởi chạy Voice Generator...
echo ------------------------------------------------------------
python function.py

if errorlevel 1 (
    echo.
    echo ❌ Ứng dụng gặp lỗi. Vui lòng kiểm tra log phía trên.
    pause
)