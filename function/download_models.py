import os
import shutil
from huggingface_hub import snapshot_download
import requests
import subprocess
import sys
import zipfile
import platform
from tkinter import messagebox


def check_and_setup_dependencies():
    # Get root directory containing current file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. CHECK AND DOWNLOAD FFmpeg Suite
    tools = ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]
    missing_tools = [t for t in tools if not os.path.exists(os.path.join(base_dir, t))]
    
    if missing_tools:
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(base_dir, "ffmpeg_temp.zip")
        try:
            print(f"📥 Downloading FFmpeg suite for tools: {missing_tools}...")
            r = requests.get(ffmpeg_url, stream=True, timeout=30)
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if filename in tools:
                        # Extract directly into base_dir
                        with zip_ref.open(member) as source, open(os.path.join(base_dir, filename), "wb") as target:
                            shutil.copyfileobj(source, target)
            
            if os.path.exists(zip_path): os.remove(zip_path)
            print("✅ FFmpeg suite ready.")
        except Exception as e:
            print(f"❌ FFmpeg processing error: {e}")

    # 2. CHECK AND INSTALL VLC
    vlc_paths = [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]
    if not any(os.path.exists(p) for p in vlc_paths):
        if messagebox.askyesno("System Requirement", "VLC is not installed. Install automatically?"):
            vlc_url = "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.exe"
            inst_path = os.path.join(base_dir, "vlc_installer.exe")
            try:
                print("📥 Downloading VLC...")
                r = requests.get(vlc_url, timeout=30)
                with open(inst_path, 'wb') as f: f.write(r.content)
                
                print("⚙️ Installing VLC (Please confirm Admin rights if requested)...")
                # Use shell=True and launch for user to confirm UAC
                subprocess.run([inst_path, "/S"], check=True, shell=True)
                
                if os.path.exists(inst_path): os.remove(inst_path)
                print("✅ VLC installation complete.")
            except Exception as e:
                print(f"❌ VLC installation error: {e}")

# Call check function immediately when file is loaded
check_and_setup_dependencies()


# 3. CHECK AND DOWNLOAD AI MODELS
checkpoint_dir = 'checkpoints_v2'
marker_file = os.path.join(checkpoint_dir, 'converter', 'checkpoint.pth')

if os.path.exists(marker_file):
    print(f"✅ AI Models already exist in {checkpoint_dir}. Skipping download.")
else:
    print("🔍 AI Models not found or incomplete. Starting download...")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    print("📥 Downloading model from HuggingFace (~1-2GB), please wait...")
    try:
        # Tải model OpenVoice V2
        snapshot_download(
            repo_id="myshell-ai/OpenVoiceV2",
            local_dir=checkpoint_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ Complete! Model has been saved to: {os.path.abspath(checkpoint_dir)}")
    except Exception as e:
        print(f"❌ Model download error: {e}")
