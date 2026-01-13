import eel
import os
import asyncio
import edge_tts
import librosa
import soundfile as sf
import shutil
import numpy as np
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import unidecode
import re
import torch
import json
from pedalboard import (
    Pedalboard, NoiseGate, Compressor, LowShelfFilter, 
    HighShelfFilter, Distortion, Chorus, Delay, Reverb, Limiter, PitchShift
)

# --- CẤU HÌNH HỆ THỐNG ---
try:
    from pedalboard import HighPassFilter
except ImportError:
    HighPassFilter = None

# --- CẬP NHẬT ĐOẠN ĐẦU FILE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'web')

# QUAN TRỌNG: Tất cả phải nằm trong WEB_DIR
PROCESSED_DIR = os.path.join(WEB_DIR, 'processed')
USED_DIR = os.path.join(WEB_DIR, 'used')
TEMP_EDIT_DIR = os.path.join(WEB_DIR, 'temp_edit')
PRESET_DIR = os.path.join(BASE_DIR, 'presets') # Preset có thể để ngoài vì JS không cần gọi trực tiếp

# Tự động tạo thư mục nếu chưa có
for d in [PROCESSED_DIR, USED_DIR, TEMP_EDIT_DIR, PRESET_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

PREVIEW_PATH = os.path.join(TEMP_EDIT_DIR, "preview.wav")





# --- CẤU HÌNH OPENVOICE ---
from openvoice import se_extractor
from openvoice.api import ToneColorConverter

CKPT_CONVERTER = os.path.join(BASE_DIR, 'checkpoints_v2', 'converter')
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Khởi tạo converter (nên khởi tạo một lần để tránh tốn tài nguyên)
tone_color_converter = ToneColorConverter(f'{CKPT_CONVERTER}/config.json', device=DEVICE)
tone_color_converter.load_ckpt(f'{CKPT_CONVERTER}/checkpoint.pth')






def cleanup_on_close(page, sockets):
    """Hàm này sẽ chạy khi cửa sổ trình duyệt bị đóng"""
    print(f"Đang đóng ứng dụng và dọn dẹp hệ thống...")
    
    # Danh sách các thư mục cần làm sạch (Chỉ dọn file tạm, KHÔNG dọn USED_DIR)
    # Lưu ý: TEMP_PREVIEW_DIR nếu bạn có biến riêng, hãy thêm vào đây. 
    # Nếu file preview nằm trong TEMP_EDIT_DIR thì nó sẽ tự động bị xóa.
    directories_to_clean = [TEMP_EDIT_DIR, PROCESSED_DIR]
    
    try:
        for folder in directories_to_clean:
            if os.path.exists(folder):
                print(f"--- Cleaning: {os.path.basename(folder)} ---")
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f'Error While Cleaning {filename}: {e}')
                        
        print("Cleaned up temporary files.")
    except Exception as e:
        print(f"Error While Cleaning: {e}")
    os._exit(0)

# --- HÀM XỬ LÝ PRESET ---

@eel.expose
def save_preset_to_file(name, data):
    try:
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).rstrip()
        file_path = os.path.join(PRESET_DIR, f"{safe_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error Saving Preset: {e}")
        return False

@eel.expose
def get_all_presets():
    presets = {}
    try:
        if os.path.exists(PRESET_DIR):
            for filename in os.listdir(PRESET_DIR):
                if filename.endswith(".json"):
                    name = filename.replace(".json", "")
                    with open(os.path.join(PRESET_DIR, filename), 'r', encoding='utf-8') as f:
                        presets[name] = json.load(f)
    except Exception as e:
        print(f"Error Reading Presets: {e}")
    return presets

@eel.expose
def delete_preset_file(name):
    try:
        file_path = os.path.join(PRESET_DIR, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error Deleting Preset: {e}")
    return False

# --- AUDIO FILTERS & PROCESSING ---

def apply_audio_filters(file_path, vol, reverb, bass, treble, use_comp, echo, chorus, use_limiter, ps, wide, drive, hp_freq, use_desser):
    try:
        y, sr = librosa.load(file_path, sr=None)
        if len(y.shape) == 1:
            y = np.stack([y, y])

        effects = []
        if HighPassFilter is not None:
            effects.append(HighPassFilter(cutoff_frequency_hz=float(hp_freq)))
        else:
            effects.append(LowShelfFilter(cutoff_frequency_hz=float(hp_freq), gain_db=-30.0))

        effects.append(NoiseGate(threshold_db=-45))
        if use_desser:
            effects.append(HighShelfFilter(cutoff_frequency_hz=5000, gain_db=-8))

        if float(drive) > 0:
            effects.append(Distortion(drive_db=float(drive)))
        
        if float(ps) != 0:
            semitones = float(ps) / 10 
            effects.append(PitchShift(semitones=semitones))

        if float(bass) > 0:
            effects.append(LowShelfFilter(cutoff_frequency_hz=400, gain_db=float(bass)))
        if float(treble) > 0:
            effects.append(HighShelfFilter(cutoff_frequency_hz=3000, gain_db=float(treble)))

        if use_comp:
            effects.append(Compressor(threshold_db=-18, ratio=3.5))

        if float(chorus) > 0:
            effects.append(Chorus(depth=float(chorus)/100))
        if float(echo) > 0:
            effects.append(Delay(delay_seconds=0.25, mix=float(echo)/300))
        if float(reverb) > 0:
            effects.append(Reverb(room_size=float(reverb)/100, wet_level=0.15))

        if use_limiter:
            effects.append(Limiter(threshold_db=-1.0))

        board = Pedalboard(effects)
        y = board(y, sr)
        y = y * (float(vol) / 100.0)
        
        sf.write(file_path, y.T, sr)
        return True
    except Exception as e:
        print(f"Error Processing Audio: {e}")
        return False

@eel.expose
def get_all_voices():
    async def fetch_voices():
        v = await edge_tts.VoicesManager.create()
        return v.voices
    return asyncio.run(fetch_voices())

@eel.expose
def process_preview(text, voice_id, speed, pitch, vol, reverb, bass, treble, use_comp, echo, chorus, use_limiter, ps, wide, drive, hp_freq, use_desser):
    if not voice_id: voice_id = "vi-VN-HoaiNinhNeural"
    try:
        rate_str = f"{int((float(speed) - 1) * 100):+d}%"
        pitch_str = f"{int(pitch):+d}Hz"
        
        async def generate():
            await edge_tts.Communicate(text, voice_id, rate=rate_str, pitch=pitch_str).save(PREVIEW_PATH)
        async def run_gen():
            await generate()
        asyncio.run(run_gen())
        
        if os.path.exists(PREVIEW_PATH):
            apply_audio_filters(PREVIEW_PATH, vol, reverb, bass, treble, use_comp, echo, chorus, use_limiter, ps, wide, drive, hp_freq, use_desser)
            return "temp_edit/preview.wav"
    except Exception as e:
        print(f"Error Processing Preview: {e}")
    return None

@eel.expose
def process_ai_generate_with_fx(text, voice_id, index, speed, pitch, vol, reverb, bass, treble, use_comp, echo, chorus, use_limiter, ps, wide, drive, hp_freq, use_desser):
    output_path = os.path.join(TEMP_EDIT_DIR, f"gen_{index}.wav")
    try:
        rate_str = f"{int((float(speed) - 1) * 100):+d}%"
        pitch_str = f"{int(pitch):+d}Hz"
        
        async def generate():
            await edge_tts.Communicate(text, voice_id, rate=rate_str, pitch=pitch_str).save(output_path)
        asyncio.run(generate())
        
        success = apply_audio_filters(output_path, vol, reverb, bass, treble, use_comp, echo, chorus, use_limiter, ps, wide, drive, hp_freq, use_desser)
        return success
    except Exception as e:
        print(f"Error Generating (Index {index}): {e}")
    return False

@eel.expose
def save_single_audio(index, current_preset_name):
    """Mở hộp thoại lưu file với tên mặc định là TênPreset_ThoiGian"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        source_path = os.path.join(TEMP_EDIT_DIR, f"gen_{index}.wav")
        
        if not os.path.exists(source_path):
            return {"status": "error", "message": "File Isn't Created Right!"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        preset_label = current_preset_name if current_preset_name else "Default"
        default_filename = f"{preset_label}_{timestamp}.wav"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            initialfile=default_filename,
            title="Chọn nơi lưu file audio"
        )
        
        root.destroy()

        if file_path:
            shutil.copy(source_path, file_path)
            return {"status": "success", "message": f"Saved: {os.path.basename(file_path)}"}
        return {"status": "cancel"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    


@eel.expose
def save_all_audio(paragraph_list, preset_names):
    """
    Lưu tất cả các đoạn audio đã generate vào một thư mục do người dùng chọn.
    paragraph_list: Danh sách các đoạn văn bản (để biết số lượng file).
    preset_names: Danh sách tên preset tương ứng từng dòng để đặt tên file.
    """
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        # Chọn thư mục lưu trữ
        target_dir = filedialog.askdirectory(title="Select Folder to Save All Audio Files")
        root.destroy()

        if not target_dir:
            return {"status": "cancel"}

        count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for index, text in enumerate(paragraph_list):
            source_path = os.path.join(TEMP_EDIT_DIR, f"gen_{index}.wav")
            
            if os.path.exists(source_path):
                # Đặt tên file theo định dạng: 01_TenPreset_ThoiGian.wav
                preset_label = preset_names[index] if index < len(preset_names) else "Custom"
                file_name = f"{index+1:02d}_{preset_label}_{timestamp}.wav"
                dest_path = os.path.join(target_dir, file_name)
                
                shutil.copy(source_path, dest_path)
                count += 1

        if count > 0:
            return {"status": "success", "message": f"Saved {count} files to folder."}
        else:
            return {"status": "error", "message": "No generated files found to save."}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    


target_se = None 

def clean_filename(filename):
    # Tách tên và đuôi file
    name, ext = os.path.splitext(filename)
    # Khử dấu tiếng Việt: "Thoại" -> "Thoai"
    name = unidecode.unidecode(name)
    # Thay khoảng trắng và ký tự lạ bằng dấu gạch dưới
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return f"{name}{ext}"

@eel.expose
def select_reference_audio():
    global target_se
    try:
        # Xác định đường dẫn: main.py -> web -> used
        # os.path.dirname(__file__) lấy thư mục chứa file main.py hiện tại
        base_path = os.path.dirname(os.path.abspath(__file__))
        used_dir = os.path.join(base_path, "web", "used")
        
        # Tạo thư mục 'web/used' nếu chưa có để tránh lỗi mở folder mặc định của Win
        if not os.path.exists(used_dir):
            os.makedirs(used_dir, exist_ok=True)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        # Mở hộp thoại chọn file tại thư mục web/used
        file_path = filedialog.askopenfilename(
            initialdir=used_dir,
            title="Select Reference Audio",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.flac")]
        )
        root.destroy()

        if not file_path: return {"status": "cancel"}

        # 1. Chuẩn hóa tên file và ĐỔI ĐUÔI SANG .WAV
        original_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(original_name)[0]
        file_name = clean_filename(name_without_ext) + ".wav" 
        
        dest_path = os.path.join(PROCESSED_DIR, file_name)

        # 2. Dùng librosa để đọc và soundfile để ghi
        y, sr = librosa.load(file_path, sr=None)
        sf.write(dest_path, y, sr)

        # 3. Trích xuất SE
        se, _ = se_extractor.get_se(dest_path, tone_color_converter, target_dir=PROCESSED_DIR, vad=True)
        target_se = se
        
        # 4. Kiểm tra lại lần cuối
        if not os.path.exists(dest_path):
            sf.write(dest_path, y, sr)
            
        print(f"✅ Reference audio prepared: {dest_path}")
        return {"status": "success", "file_name": file_name}
        
    except Exception as e:
        print(f"❌ Error in select_reference_audio: {e}")
        return {"status": "error", "message": str(e)}



@eel.expose
def convert_to_clone_voice(input_relative_path):
    """Chuyển đổi giọng nói dựa trên cấu trúc audio_src_path"""
    global target_se
    try:
        # 1. Xử lý đường dẫn đồng nhất (Dùng os.path.normpath để tránh lỗi dấu gạch chéo trên Windows)
        clean_path = input_relative_path.split('?')[0] # Loại bỏ param ?t= nếu có
        input_full_path = os.path.normpath(os.path.join(WEB_DIR, clean_path))
        output_full_path = input_full_path.replace(".wav", "_cloned.wav")
        
        if not os.path.exists(input_full_path):
            return {"status": "error", "message": f"Can't Find Source File At: {input_full_path}"}

        # 2. Kiểm tra/Tự động nạp lại SE (Sửa lỗi mất biến global)
        if target_se is None:
            # Sửa đường dẫn nạp SE chuẩn với thư mục processed của bạn
            se_path = os.path.join(PROCESSED_DIR, "current_target_se.pth") 
            if os.path.exists(se_path):
                target_se = torch.load(se_path, map_location=DEVICE)
            else:
                return {"status": "error", "message": "Please 'Learn Voice' sample file first!"}

        # 3. Load Source SE (Dùng map_location để tránh lỗi nếu chạy trên máy không có CUDA)
        source_se_path = os.path.join(BASE_DIR, 'checkpoints_v2', 'base_speakers', 'ses', 'en-default.pth')
        source_se = torch.load(source_se_path, map_location=DEVICE)

        # 4. THỰC HIỆN CONVERT
        # Chạy trong luồng xử lý của OpenVoice
        tone_color_converter.convert(
            audio_src_path=input_full_path, 
            src_se=source_se, 
            tgt_se=target_se, 
            output_path=output_full_path,
            tau=0.3
        )

        # Giải phóng bộ nhớ GPU sau mỗi câu (Rất quan trọng cho hàm All)
        if DEVICE == "cuda":
            torch.cuda.empty_cache()

        # 5. Trả về đường dẫn tương đối chuẩn cho JS
        # Thay thế dấu gạch chéo ngược Windows sang gạch chéo Web
        web_path = clean_path.replace(".wav", "_cloned.wav").replace("\\", "/")
        
        print(f"Clone Succeed: {web_path}")
        return {"status": "success", "output_file": web_path}

    except Exception as e:
        print(f"Error OpenVoice At {input_relative_path}: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def apply_fx_to_reference(file_name, data):
    target_path = os.path.join(BASE_DIR, "processed", file_name)
    # Gọi hàm apply_audio_filters có sẵn của bạn
    # Lưu ý: Truyền đúng thứ tự tham số mà hàm apply_audio_filters yêu cầu
    return apply_audio_filters(
        target_path, 
        data['vol'], data['reverb'], data['bass'], data['treble'], 
        data['use_comp'], data['echo'], data['chorus'], data['use_limiter'], 
        data['ps'], 0, data['drive'], data['hp_freq'], data['use_desser']
    )


@eel.expose
def process_and_save_to_used(data):
    try:
        # 1. Khởi tạo giao diện chọn file để người dùng đặt tên
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        # Mặc định mở ở thư mục USED_DIR
        save_path = filedialog.asksaveasfilename(
            initialdir=USED_DIR,
            title="Rename And Save Processed Audio",
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            initialfile=data['file_name'] # Đề xuất tên file hiện tại
        )
        root.destroy()

        if not save_path:
            return {"status": "cancel", "message": "User cancelled."}

        # 2. Đường dẫn nguồn và đích
        source_path = os.path.join(PROCESSED_DIR, data['file_name'])
        destination_path = save_path
        new_filename = os.path.basename(save_path)

        # Copy file gốc sang đường dẫn mới đã chọn
        shutil.copy2(source_path, destination_path)

        # 3. Áp dụng hiệu ứng âm thanh
        success = apply_audio_filters(
            destination_path,
            vol=float(data['vol']),
            reverb=float(data['reverb']),
            bass=float(data['bass']),
            treble=float(data['treble']),
            use_comp=bool(data['comp']),
            echo=float(data['echo']),
            chorus=float(data['chorus']),
            use_limiter=bool(data['limit']),
            ps=float(data['pitch']),
            wide=0,
            drive=float(data['drive']),
            hp_freq=float(data['hp']),
            use_desser=bool(data['desser'])
        )

        if success:
            global target_se
            # Học lại giọng từ file đã lưu (file đã có hiệu ứng)
            se, _ = se_extractor.get_se(destination_path, tone_color_converter, target_dir=USED_DIR, vad=True)
            target_se = se
            return {"status": "success", "file_name": new_filename}

        return {"status": "error", "message": "Can't Apply The Filters."}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}







# --- KHỞI CHẠY ---
if __name__ == "__main__":
    eel.init(WEB_DIR)
    print("Studio Is Starting At http://localhost:8888")
    eel.start('index.html', port=8888, size=(1100, 850),mode="default",close_callback=cleanup_on_close)