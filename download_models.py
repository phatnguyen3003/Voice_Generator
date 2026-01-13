import os
from huggingface_hub import snapshot_download

# Tạo thư mục checkpoints nếu chưa có
checkpoint_dir = 'checkpoints_v2'
os.makedirs(checkpoint_dir, exist_ok=True)

print("Đang tải model từ HuggingFace (khoảng 1-2GB), vui lòng đợi...")

# Tải model OpenVoice V2
snapshot_download(
    repo_id="myshell-ai/OpenVoiceV2",
    local_dir=checkpoint_dir,
    local_dir_use_symlinks=False
)

print(f"Hoàn tất! Model đã được lưu vào: {os.path.abspath(checkpoint_dir)}")