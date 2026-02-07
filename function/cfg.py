import shutil
import sys
import edge_tts
import threading
import pygame
import asyncio
import json
import os
import librosa
import soundfile as sf
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
import numpy as np
from pydub import AudioSegment
from pedalboard import Pedalboard, Reverb, Delay, Chorus, LowShelfFilter, HighShelfFilter, Compressor, NoiseGate, Limiter
from pedalboard.io import AudioFile
import time
import torch
from openvoice_cli.api import ToneColorConverter
from openvoice_cli.api import ToneColorConverter
try:
    from openvoice_cli import se_extractor
    print("✅ ToneColorConverter and se_extractor loaded")
except ImportError:
    print("⚠️ Warning: se_extractor not found, you will not be able to extract sample voices.")
import unicodedata
import re



# --- SYSTEM CONFIGURATION ---

# 1. Ensure FFmpeg is executable (For pydub and openvoice)
os.environ["PATH"] += os.pathsep + os.getcwd()

# 2. Force Python to recognize modules in venv/site-packages if running from outside
site_pkg = os.path.join(os.getcwd(), "venv", "Lib", "site-packages")
if site_pkg not in sys.path:
    sys.path.insert(0, site_pkg)

# 3. Configure AI execution device (Priority GPU if available, else CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"


def get_all_edge_voices():
    """Get list of all current Edge TTS voices"""
    async def fetch():
        voices = await edge_tts.list_voices()
        # Get ShortName and sort alphabetically for easy search
        return sorted([v["ShortName"] for v in voices])
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(fetch())


def save_preset(self):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    preset_dir = os.path.join(base_dir, "presets")
    
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)

    # Logic to find automatic sequence number
    existing_files = os.listdir(preset_dir)
    counter = 1
    while True:
        proposed_name = f"preset_{counter}"
        if f"{proposed_name}.json" not in existing_files:
            default_name = proposed_name
            break
        counter += 1

    dialog = ctk.CTkInputDialog(text="Enter name for the voice preset:", title="Save Preset CFG")
    dialog.after(10, lambda: dialog._entry.insert(0, default_name)) 
    
    preset_name = dialog.get_input()

    if preset_name:
        if not preset_name.endswith(".json"):
            preset_name += ".json"
            
        file_path = os.path.join(preset_dir, preset_name)

        # ONLY COLLECT CFG AND VOICE DATA
        preset_data = {
            "sliders_cfg": {k: v["widget"].get() for k, v in self.sliders_cfg.items()},
            "voice": self.edge_voice_dropdown.get()
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Voice setting saved: {preset_name}")
            
            if hasattr(self, "render_presets"):
                self.render_presets()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not save: {e}")


def render_presets(self):
    """Scan presets folder and display preset boxes on UI"""
    # 1. Delete old widgets in preset_frame for new render
    for widget in self.preset_frame.winfo_children():
        widget.destroy()

    # 2. Determine presets folder path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    preset_dir = os.path.join(base_dir, "presets")
    
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)

    # 3. Get list of .json files
    presets = [f for f in os.listdir(preset_dir) if f.endswith(".json")]

    # 4. Render each preset in grid format (4 columns)
    for idx, filename in enumerate(presets):
        col = idx % 4
        row = idx // 4
        
        # Create container for each preset item
        item_container = ctk.CTkFrame(self.preset_frame, fg_color="#3d3d3d", corner_radius=8)
        item_container.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Delete (X) button in top right corner
        btn_delete = ctk.CTkButton(
            item_container, text="×", width=20, height=20, 
            fg_color="#c0392b", hover_color="#e74c3c",
            command=lambda f=filename: self.delete_preset(f)
        )
        btn_delete.place(relx=1.0, rely=0, anchor="ne", x=-2, y=2)

        # Main button (Display Preset name and for Loading)
        display_name = filename.replace(".json", "")
        # Truncate name if too long
        short_name = (display_name[:10] + '..') if len(display_name) > 12 else display_name
        
        btn_load = ctk.CTkButton(
            item_container, 
            text=short_name,
            fg_color="transparent",
            hover_color="#505050",
            height=60,
            font=ctk.CTkFont(size=11),
            command=lambda f=filename: self.load_preset_file(f)
        )
        btn_load.pack(expand=True, fill="both", padx=5, pady=(20, 5))


def delete_preset(self, filename):
    """Delete preset file after confirmation"""
    if messagebox.askyesno("Confirm", f"Are you sure you want to delete preset '{filename}'?"):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, "presets", filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                self.render_presets() # Redraw list after deletion
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file: {e}")

def load_preset_file(self, filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "presets", filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. Load Sliders Cfg (Speed, Pitch, etc.) only
        for k, val in data.get("sliders_cfg", {}).items():
            if k in self.sliders_cfg:
                self.sliders_cfg[k]["widget"].set(val)
                # Update displayed number next to slider
                # If integer (like Pitch), show int; if speed, show 1 decimal place
                label_text = f"{int(val)}" if val > 10 or val < -10 else f"{val:.1f}"
                self.sliders_cfg[k]["label"].configure(text=label_text)

        # 2. Load selected voice
        if "voice" in data:
            self.edge_voice_dropdown.set(data["voice"])

        # Show small notification in corner or console instead of messagebox to avoid interruption
        print(f"✅ Loaded preset: {filename}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Error loading preset: {e}")


def preview_voice(self):
    def run_preview():
        try:
            # 0. Release file
            if hasattr(self, 'player'):
                self.player.stop()
                self.player.set_media(None) 

            # 1. Collect data
            selected_voice = self.edge_voice_dropdown.get()
            raw_text = self.preview_textbox.get("1.0", "end-1c").strip()
            
            sample_texts = {
                "vi": "Chào bạn, đây là âm thanh mẫu tiếng Việt với cấu hình hiện tại.",
                "en": "Hello, this is a sample audio in English with the current configuration.",
                "ja": "こんにちは、これは現在の設定を適用した日本語 của mẫu âm thanh.",
                "fr": "Bonjour, ceci est un exemple audio avec la configuration actuelle.",
                "ru": "Здравствуйте! Это тестовая запись с примененными фильтрами."
            }
            
            # Get language code (e.g., 'vi', 'en', 'ko'...)
            lang_code = selected_voice.split('-')[0].lower()
            
            # If text is empty, get from dictionary.
            # If lang_code is not found in dictionary, use default English sentence.
            default_en = sample_texts["en"]
            text_to_read = raw_text if raw_text else sample_texts.get(lang_code, default_en)

            # 2. Get indices
            c_speed     = self.sliders_cfg["speed"]["widget"].get()
            c_pitch     = self.sliders_cfg["pitch"]["widget"].get()
            c_volume    = self.sliders_cfg["volume"]["widget"].get()
            c_reverb    = self.sliders_cfg["reverb"]["widget"].get()
            c_bass      = self.sliders_cfg["bass"]["widget"].get()
            c_treble    = self.sliders_cfg["treble"]["widget"].get()
            c_echo      = self.sliders_cfg["echo"]["widget"].get()
            c_chorus    = self.sliders_cfg["chorus"]["widget"].get()
            c_threshold = self.sliders_cfg["thresh"]["widget"].get() 
            c_ratio     = self.sliders_cfg["ratio"]["widget"].get()

            # 3. Edge-TTS formatting
            rate_str  = f"{int((c_speed - 1.0) * 100):+d}%"
            pitch_str = f"{int(c_pitch):+d}Hz"
            vol_str   = f"{int(c_volume - 100):+d}%"

            # 4. File paths
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_dir = os.path.join(base_dir, "temp")
            if not os.path.exists(temp_dir): os.makedirs(temp_dir)
            
            raw_path = os.path.join(temp_dir, "edge_raw.mp3")
            processed_path = os.path.join(temp_dir, "preview_processed.wav")

            # 5. Create raw audio
            import asyncio, edge_tts
            async def make_audio():
                communicate = edge_tts.Communicate(text_to_read, selected_voice, rate=rate_str, pitch=pitch_str, volume=vol_str)
                await communicate.save(raw_path)

            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(make_audio())
            new_loop.close()

            # 6. OPTIMIZED POST-PROCESSING
            import librosa, numpy as np, soundfile as sf
            y, sr = librosa.load(raw_path, sr=None)

            # --- A. NOISE GATE ---
            if self.cfg_gate_sw.get():
                y, _ = librosa.effects.trim(y, top_db=abs(c_threshold))

            # --- B. COMPRESSOR ---
            if c_ratio > 1.0:
                thresh_amp = librosa.db_to_amplitude(c_threshold)
                mask = np.abs(y) > thresh_amp
                y[mask] = np.sign(y[mask]) * (thresh_amp + (np.abs(y[mask]) - thresh_amp) / c_ratio)

            # --- C. EQ: BASS & TREBLE ---
            if c_bass > 0:
                y = librosa.effects.preemphasis(y, coef=0.2 + (c_bass/100))
            if c_treble > 0:
                y = y + (np.diff(y, prepend=y[0]) * (c_treble / 50))

            # --- D. ECHO ---
            if c_echo > 0:
                delay = int(0.15 * sr)
                if len(y) > delay:
                    echo_wet = np.zeros_like(y)
                    echo_wet[delay:] = y[:-delay] * (c_echo / 300)
                    y = y + echo_wet

            # --- E. REVERB/CHORUS ---
            if c_reverb > 0 or c_chorus > 0:
                shift = int(sr * 0.02)
                if len(y) > shift:
                    rev_wet = np.zeros_like(y)
                    rev_wet[shift:] = y[:-shift] * (max(c_reverb, c_chorus) / 400)
                    y = (y * 0.9) + rev_wet

            # --- F. NORMALIZE & VOLUME BOOST ---
            if self.cfg_normalize_sw.get():
                y = librosa.util.normalize(y)

            gain_factor = c_volume / 100.0
            if gain_factor != 1.0:
                y = y * gain_factor

            # --- G. LIMITER ---
            if self.cfg_limiter_sw.get() or gain_factor > 1.0:
                y = np.clip(y, -0.99, 0.99)

            # 7. Write file and push to Player
            sf.write(processed_path, y, sr)
            duration = librosa.get_duration(y=y, sr=sr)
            
            self.after(0, lambda: self.load_to_master(processed_path, f"Preview: {selected_voice}", duration))

        except Exception as e:
            print(f"Effect processing error: {e}")

    threading.Thread(target=run_preview, daemon=True).start()

def process_text_to_queue(self):
    raw_content = self.textbox.get("1.0", "end-1c").strip()
    
    if not raw_content:
        messagebox.showwarning("Notice", "Please enter text before splitting segments!")
        return

    paragraphs = [p.strip() for p in raw_content.split("\n") if p.strip()]

    for widget in self.queue_frame.winfo_children():
        widget.destroy()

    # --- UPDATE HERE: Get preset from actual folder ---
    available_presets = get_preset_list()

    self.queue_items_data = [] 
    
    for index, text in enumerate(paragraphs):
        # Pass the actual preset list in
        item_widget = self.add_queue_item(text, available_presets)
        
        self.queue_items_data.append({
            "id": index,
            "text": text,
            "widget": item_widget
        })

    try:
        self.queue_frame._parent_canvas.yview_moveto(0)
    except:
        pass


# Định nghĩa các hàm rỗng để test giao diện
def generate_one(self, text, widgets):
    try:
        # --- STEP 1: FIX INDEX (WHICH SEGMENT) ---
        # Get parent container of these widgets
        # widgets["sliders"]["speed"]["slider"] -> đi ngược lên tới item_container
        any_widget = list(widgets["sliders"].values())[0]["slider"]
        item_container = any_widget.master.master.master # Depending on nesting structure, we get the main container
        
        # Find index of the paragraph in queue_frame (starts from 1)
        all_items = self.queue_frame.winfo_children()
        try:
            item_index = all_items.index(item_container) + 1
        except:
            item_index = "unknown"

        # --- STEP 2: EXTRACT SPECIFIC PARAMETERS ---
        p = {k: v["slider"].get() for k, v in widgets["sliders"].items()}
        sw = {k: v.get() for k, v in widgets["switches"].items()}
        selected_voice = widgets["voice_dd"].get()

        # --- STEP 3: FILE PATHS (index + 1) ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(base_dir, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Raw file and final file named by sequence number
        raw_path = os.path.join(temp_dir, f"raw_{item_index}.mp3")
        final_path = os.path.join(temp_dir, f"{item_index}.wav")  # Lưu WAV để clone_one xử lý

        # --- STEP 4: SPEECH GENERATION (EDGE-TTS) ---
        async def run_tts():
            speed_str = f"{int((p['speed'] - 1.0) * 100):+}%"
            pitch_str = f"{int(p['pitch']):+}Hz"
            communicate = edge_tts.Communicate(text, selected_voice, rate=speed_str, pitch=pitch_str)
            await communicate.save(raw_path)

        asyncio.run(run_tts())

        # --- STEP 5: EFFECTS PROCESSING (PEDALBOARD) ---
        with AudioFile(raw_path) as f:
            audio_data = f.read(f.frames)
            sr = f.samplerate # Fixed samplerate error

        board = Pedalboard()

        if sw.get("gate"):
            board.append(NoiseGate(threshold_db=-40))

        # EQ: Bass & Treble
        board.append(LowShelfFilter(cutoff_frequency_hz=250, gain_db=p['bass']))
        board.append(HighShelfFilter(cutoff_frequency_hz=4000, gain_db=p['treble']))

        if p['chorus'] > 0:
            board.append(Chorus(mix=p['chorus']/100))
        
        if p['echo'] > 0:
            board.append(Delay(delay_seconds=0.25, feedback=0.3, mix=p['echo']/100))

        # Use correct key 'rev' from your create_local_slider
        if p.get('rev', 0) > 0:
            board.append(Reverb(room_size=p['rev']/100, wet_level=p['rev']/200))

        # Compressor (Thresh & Ratio)
        board.append(Compressor(threshold_db=p['thresh'], ratio=p['ratio']))

        if sw.get("limiter"):
            board.append(Limiter(threshold_db=-1.0))

        processed_audio = board(audio_data, sr)

        with AudioFile(final_path, 'w', sr, processed_audio.shape[0]) as f:
            f.write(processed_audio)

        # --- STEP 6: VOLUME & NORMALIZE (PYDUB) ---
        audio = AudioSegment.from_file(final_path)
        
        # p['vol'] taken from "Vol" slider (0-250)
        vol_db = (p['vol'] - 100) / 5
        audio = audio + vol_db

        if sw.get("normalize"):
            audio = audio.normalize()

        audio.export(final_path, format="wav")

        # Delete raw file
        if os.path.exists(raw_path):
            os.remove(raw_path)

        # --- CHANGE GEN BUTTON COLOR TO MARK DONE ---
        if "buttons" in widgets and "gen" in widgets["buttons"]:
            # Change to green (Success) or color you like
            widgets["buttons"]["gen"].configure(fg_color="#28a745", hover_color="#218838")
            # Optional: Change text to "Done"
            # widgets["buttons"]["gen"].configure(text="Done")

        print(f"✅ Created segment: {final_path}")
        return final_path

    except Exception as e:
        if "buttons" in widgets and "gen" in widgets["buttons"]:
            widgets["buttons"]["gen"].configure(fg_color="#dc3545", hover_color="#c82333")
        print(f"❌ Error: {e}")
        return None



def play_one(self, paragraph_text):
    """
    Function to play audio of a specific paragraph.
    Uses load_to_master to push to application's main player.
    """
    import os
    import librosa
    from tkinter import messagebox

    # 1. Determine Index of paragraph in queue list
    items = self.queue_frame.winfo_children()
    found_idx = -1
    
    for i, item in enumerate(items):
        # Check if paragraph_text was assigned to item_container in add_queue_item
        if hasattr(item, "paragraph_text") and item.paragraph_text == paragraph_text:
            found_idx = i + 1
            break
            
    if found_idx == -1:
        return

    # 2. Determine audio file path
    # Priority for .wav (result after Clone) then .mp3 (original Gen result)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "temp")
    
    file_path_wav = os.path.join(temp_dir, f"{found_idx}.wav")
    file_path_mp3 = os.path.join(temp_dir, f"{found_idx}.mp3")
    
    final_path = None
    if os.path.exists(file_path_wav):
        final_path = file_path_wav
    elif os.path.exists(file_path_mp3):
        final_path = file_path_mp3

    if not final_path:
        messagebox.showwarning("Notice", f"No audio file for segment {found_idx}. Please click 'Gen' first.")
        return

    # 3. Calculate duration and load into Master Player
    try:
        # Load file info to get duration (same as in preview_voice and play_ref_audio)
        y, sr = librosa.load(final_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Display name on Player
        display_name = f"Segment {found_idx}: {paragraph_text[:20]}..."
        
        # Call function to load into master player (imported in ref.py or main app)
        self.load_to_master(final_path, display_name, duration)
        
        print(f"🎵 Segment {found_idx} loaded into main player.")
        
    except Exception as e:
        print(f"Error loading file into player: {e}")
        messagebox.showerror("Error", f"Cannot load audio file: {e}")



def slugify_text(text, length=30):
    """
    Chuyển văn bản thành không dấu, loại bỏ ký tự đặc biệt để làm tên file.
    """
    if not text:
        return ""
    
    # 1. Chuyển Unicode dựng sẵn về dạng tổ hợp (NFD) để tách dấu
    # Ví dụ: "ế" sẽ thành "ê" + "ˊ"
    text = unicodedata.normalize('NFD', text)
    
    # 2. Loại bỏ các ký tự dấu (Non-spacing Mark)
    text = "".join([c for c in text if unicodedata.category(c) != 'Mn'])
    
    # 3. Chuyển chữ "đ" sang "d" (vì bước trên không xử lý được chữ đ/Đ)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    
    # 4. Loại bỏ ký tự đặc biệt, chỉ giữ lại chữ cái, số và khoảng trắng
    clean_text = re.sub(r'[\\/*?:"<>|]', "", text)
    
    # 5. Cắt 30 ký tự đầu và xóa khoảng trắng thừa ở 2 đầu
    return clean_text[:length].strip()




def save_one(self, paragraph_text):
    """Lưu file audio của đoạn văn bản cụ thể với tên không dấu (max 30 ký tự)"""
    # 1. Xác định Index (giữ nguyên logic cũ)
    items = self.queue_frame.winfo_children()
    found_idx = -1
    for i, item in enumerate(items):
        if hasattr(item, "paragraph_text") and item.paragraph_text == paragraph_text:
            found_idx = i + 1
            break
            
    if found_idx == -1:
        messagebox.showerror("Error", "Could not determine segment index.")
        return

    # 2. Xác định đường dẫn nguồn
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "temp")
    src_wav = os.path.join(temp_dir, f"{found_idx}.wav")
    src_mp3 = os.path.join(temp_dir, f"{found_idx}.mp3")
    src_path = src_wav if os.path.exists(src_wav) else src_mp3 if os.path.exists(src_mp3) else None

    if not src_path:
        messagebox.showwarning("Warning", f"Segment {found_idx} audio not created yet.")
        return

    # 3. Tạo tên file sạch (không dấu, max 30 ký tự)
    clean_name = slugify_text(paragraph_text, 30)
    if not clean_name:
        clean_name = f"segment_{found_idx}"
        
    ext = os.path.splitext(src_path)[1]

    # 4. Mở cửa sổ lưu file
    save_path = filedialog.asksaveasfilename(
        title="Save paragraph audio",
        initialfile=f"{clean_name}{ext}",
        defaultextension=ext,
        filetypes=[("Audio Files", f"*{ext}"), ("All Files", "*.*")]
    )

    # 5. Thực hiện copy
    if save_path:
        try:
            shutil.copy2(src_path, save_path)
            messagebox.showinfo("Success", f"Saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {str(e)}")


def clone_one(self, paragraph_text, widgets, is_all=False):
    # (Obtaining idx, source_path and ref_path remains the same...)
    any_slider = list(widgets["sliders"].values())[0]["slider"]
    item_container = any_slider.master.master.master
    all_items = self.queue_frame.winfo_children()
    try: idx = all_items.index(item_container) + 1
    except: return

    source_path = os.path.abspath(f"temp/{idx}.wav")
    if not os.path.exists(source_path):
        messagebox.showwarning("Error", "Please click Gen first!")
        return

    ref_path = ctk.filedialog.askopenfilename(title="Select voice sample", filetypes=[("Audio", "*.wav *.mp3 *.m4a")])
    if not ref_path: return

    output_path = os.path.abspath(f"temp/cloned_{idx}.wav")
    ckpt_dir = os.path.abspath("checkpoints_v2/converter")

    def process_cloning():
        try:
            print(f"🧬 [Segment {idx}] Preparing data...")
            
            # --- SOLUTION FOR "AUDIO TOO SHORT" ERROR ---
            # We will create a longer temp file to extract SE
            temp_se_path = os.path.abspath(f"temp/se_source_{idx}.wav")
            audio_src = AudioSegment.from_file(source_path)
            
            # If audio is under 15 seconds, we clone it multiple times for certainty
            # OpenVoice V2 is sometimes very strict with actual speech length
            loop_count = 5 
            extended_audio = audio_src * loop_count
            extended_audio.export(temp_se_path, format="wav")
            
            # Khởi tạo model
            print("📦 Initializing OpenVoice model...")
            model = ToneColorConverter(os.path.join(ckpt_dir, 'config.json'), device=device)
            model.load_ckpt(os.path.join(ckpt_dir, 'checkpoint.pth'))

            processed_dir = 'temp/processed'
            os.makedirs(processed_dir, exist_ok=True)

            # Phân tích SE (Sử dụng file đã kéo dài temp_se_path cho Source)
            print("🧬 Extracting target voice pattern...")
            target_se, _ = se_extractor.get_se(ref_path, vc_model=model, target_dir=processed_dir, vad=True)
            
            print("🧬 Extracting source voice pattern (extended)...")
            source_se, _ = se_extractor.get_se(temp_se_path, vc_model=model, target_dir=processed_dir, vad=True)

            # IMPORTANT CONVERT STEP:
            # - Use source_se (from long file) to get standard voice pattern
            # - Use source_path (original file) as input so results don't repeat sound
            # - convert() method automatically writes WAV file if output_path is provided
            print("🚀 Converting tone...")
            
            # source_path is already WAV from generate_one, use directly
            wav_source = source_path
            
            # Output will be WAV (ToneColorConverter only returns WAV)
            wav_output = os.path.abspath(f"temp/cloned_{idx}.wav")
            
            # Call convert with correct parameters - automatically writes WAV file
            model.convert(
                audio_src_path=wav_source, 
                src_se=source_se,
                tgt_se=target_se,
                output_path=wav_output,
                tau=0.3
            )
            # Clean up temp files (don't delete wav_source as it's source_path)
            # Complete: OpenVoice has created output WAV file
            if os.path.exists(wav_output):
                time.sleep(0.5)
                # Keep WAV output, don't convert to MP3
                # Delete original WAV file and replace with cloned_output (both are WAV)
                if os.path.exists(source_path): os.remove(source_path)
                
                # Rename cloned WAV file to original filename
                os.rename(wav_output, source_path)

            self.after(0, lambda: widgets["buttons"]["clone"].configure(fg_color="#6f42c1", text="Cloned"))
            print(f"✅ Segment {idx} success!")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            self.after(0, lambda m=error_msg: messagebox.showerror("Clone Error", m))

    threading.Thread(target=process_cloning, daemon=True).start()




def get_preset_list():
    """Scan presets folder and return list of filenames (without .json extension)"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    preset_dir = os.path.join(base_dir, "presets")
    
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)
        return ["Default"]

    # Get .json files and remove extension for display
    presets = [f.replace(".json", "") for f in os.listdir(preset_dir) if f.endswith(".json")]
    
    return presets if presets else ["Default"]





def add_queue_item(self, paragraph_text, available_presets):
    # --- STEP 0: Snapshot data from main table ---
    def get_main_cfg_snapshot():
        return {
            "speed": self.sliders_cfg["speed"]["widget"].get(),
            "pitch": self.sliders_cfg["pitch"]["widget"].get(),
            "volume": self.sliders_cfg["volume"]["widget"].get(),
            "reverb": self.sliders_cfg["reverb"]["widget"].get(),
            "bass": self.sliders_cfg["bass"]["widget"].get(),
            "treble": self.sliders_cfg["treble"]["widget"].get(),
            "echo": self.sliders_cfg["echo"]["widget"].get(),
            "chorus": self.sliders_cfg["chorus"]["widget"].get(),
            "threshold": self.sliders_cfg["thresh"]["widget"].get(),
            "ratio": self.sliders_cfg["ratio"]["widget"].get(),
            "limiter": self.cfg_limiter_sw.get() if hasattr(self, 'cfg_limiter_sw') else False,
            "normalize": self.cfg_normalize_sw.get() if hasattr(self, 'cfg_normalize_sw') else False,
            "gate": self.cfg_gate_sw.get() if hasattr(self, 'cfg_gate_sw') else False,
            "voice": self.edge_voice_dropdown.get()
        }

    current_defaults = get_main_cfg_snapshot()
    all_voices = self.edge_voice_dropdown.cget("values")

    # --- 1. Main Container (Configure horizontal expansion) ---
    item_container = ctk.CTkFrame(self.queue_frame, fg_color="#252525", corner_radius=8)
    item_container.pack(fill="x", padx=10, pady=5)
    item_container.grid_columnconfigure(0, weight=1) # Force content inside to expand

    # --- 2. Header Row ---
    header_frame = ctk.CTkFrame(item_container, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    header_frame.grid_columnconfigure(0, weight=1) # Text label takes up remaining space

    short_text = (paragraph_text[:40] + '...') if len(paragraph_text) > 40 else paragraph_text
    ctk.CTkLabel(header_frame, text=short_text, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")

    local_widgets = {"sliders": {}, "switches": {}, "voice_dd": None}

    # Logic Load Preset/Default (Keep your logic as is)
    def on_item_preset_change(choice):
        data = {}
        if choice == "Default":
            snapshot = get_main_cfg_snapshot()
            data = {
                "sliders_cfg": {k: v for k, v in snapshot.items() if k not in ["limiter", "normalize", "gate", "voice"]},
                "switches_cfg": {"limiter": snapshot["limiter"], "normalize": snapshot["normalize"], "gate": snapshot["gate"]},
                "voice": snapshot["voice"]
            }
        else:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_path = os.path.join(base_dir, "presets", f"{choice}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            except Exception as e: print(f"Error: {e}"); return

        if data:
            for k, val in data.get("sliders_cfg", {}).items():
                key = "thresh" if k == "threshold" else k
                if key in local_widgets["sliders"]:
                    local_widgets["sliders"][key]["slider"].set(val)
                    lbl_text = f"{int(val)}" if val > 10 or val < -10 else f"{val:.1f}"
                    local_widgets["sliders"][key]["label"].configure(text=lbl_text)
            for k, val in data.get("switches_cfg", {}).items():
                if k in local_widgets["switches"]:
                    if val: local_widgets["switches"][k].select()
                    else: local_widgets["switches"][k].deselect()
            if "voice" in data and local_widgets["voice_dd"]: local_widgets["voice_dd"].set(data["voice"])

    # Preset Dropdown
    preset_var = ctk.StringVar(value="Default")
    preset_values = ["Default"] + [p for p in available_presets if p != "Default"]
    preset_dd = ctk.CTkOptionMenu(header_frame, values=preset_values, variable=preset_var, 
                                  width=100, height=24, font=ctk.CTkFont(size=10), command=on_item_preset_change)
    preset_dd.grid(row=0, column=1, padx=5)

    # Button group: Gen, Play, Save
    btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    btn_frame.grid(row=0, column=2)
    
    # Initialize button list for later access
    # Initialize button list for later access
    local_widgets["buttons"] = {} 

    # Fix loop to pass 'local_widgets' to Clone function and store Button object
    for i, (text, key) in enumerate([
        ("Gen", "gen"), 
        ("▶", "play"), 
        ("Clone", "clone"), 
        ("💾", "save")
    ]):
        # Set corresponding command for each button
        if key == "gen":
            cmd = lambda t=paragraph_text, w=local_widgets: generate_one(self, t, w)
        elif key == "play":
            cmd = lambda t=paragraph_text: play_one(self, t)
        elif key == "clone":
            # IMPORTANT: Pass 'local_widgets' so clone function knows which button to recolor
            cmd = lambda t=paragraph_text, w=local_widgets: clone_one(self, t, w)
        else:
            cmd = lambda t=paragraph_text: save_one(self, t)

        # Create button
        btn = ctk.CTkButton(btn_frame, text=text, width=32, height=24, command=cmd)
        btn.grid(row=0, column=i, padx=1)
        
        # Save button to dict for later color/text changes
        local_widgets["buttons"][key] = btn

    # --- 3. Collapse Panel (Detail Frame) ---
    detail_frame = ctk.CTkFrame(item_container, fg_color="#1e1e1e", corner_radius=4)
    # Configure 2 columns for sliders, each takes 50%
    detail_frame.grid_columnconfigure((0, 1), weight=1)

    # Voice Row: force expansion to both sides
    voice_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
    voice_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    voice_frame.grid_columnconfigure(1, weight=1) # Dropdown will expand

    voice_dd = ctk.CTkOptionMenu(voice_frame, values=all_voices, height=22, font=ctk.CTkFont(size=10))
    voice_dd.set(current_defaults["voice"])
    voice_dd.grid(row=0, column=1, sticky="ew", padx=2)
    local_widgets["voice_dd"] = voice_dd

    search_entry = ctk.CTkEntry(voice_frame, placeholder_text="Find...", width=80, height=22, font=ctk.CTkFont(size=10))
    search_entry.grid(row=0, column=2, padx=5)
    search_entry.bind("<KeyRelease>", lambda e: [voice_dd.configure(values=[v for v in all_voices if search_entry.get().lower() in v.lower()]), 
                                                 voice_dd.set([v for v in all_voices if search_entry.get().lower() in v.lower()][0] if [v for v in all_voices if search_entry.get().lower() in v.lower()] else voice_dd.get())])

    # --- 4. Create Local Sliders ---
    def create_local_slider(parent, name1, min1, max1, def1, name2, min2, max2, def2, row_idx):
        for name, mi, ma, de, col in [(name1, min1, max1, def1, 0), (name2, min2, max2, def2, 1)]:
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row_idx, column=col, sticky="ew", padx=5, pady=2)
            f.grid_columnconfigure(1, weight=1) # Slider inside subframe will expand
            
            ctk.CTkLabel(f, text=f"{name}:", font=ctk.CTkFont(size=10), width=40, anchor="w").grid(row=0, column=0)
            lbl = ctk.CTkLabel(f, text=f"{de:.1f}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3b8ed0", width=30)
            lbl.grid(row=0, column=2, padx=2)
            
            s = ctk.CTkSlider(f, from_=mi, to=ma, height=12, command=lambda v, l=lbl: l.configure(text=f"{v:.1f}"))
            s.set(de)
            s.grid(row=0, column=1, sticky="ew")
            local_widgets["sliders"][name.lower()] = {"slider": s, "label": lbl}

    create_local_slider(detail_frame, "Speed", 0.5, 2.0, current_defaults["speed"], "Pitch", -50, 50, current_defaults["pitch"], 1)
    create_local_slider(detail_frame, "Vol", 0, 250, current_defaults["volume"], "Rev", 0, 100, current_defaults["reverb"], 2)
    create_local_slider(detail_frame, "Bass", 0, 15, current_defaults["bass"], "Treble", 0, 15, current_defaults["treble"], 3)
    create_local_slider(detail_frame, "Echo", 0, 100, current_defaults["echo"], "Chorus", 0, 100, current_defaults["chorus"], 4)
    create_local_slider(detail_frame, "Thresh", -60, 0, current_defaults["threshold"], "Ratio", 1, 20, current_defaults["ratio"], 5)

    # --- 5. Switches Row: Fixed sticky="center" error ---
    sw_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
    sw_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)
    
    # Divide 3 equal columns for switches to center themselves
    sw_frame.grid_columnconfigure((0, 1, 2), weight=1) 

    for i, (name, key) in enumerate([("Limiter", "limiter"), ("Normalize", "normalize"), ("Gate", "gate")]):
        sw = ctk.CTkSwitch(sw_frame, text=name, font=ctk.CTkFont(size=10), width=0)
        if current_defaults[key]: 
            sw.select()
        else: 
            sw.deselect()
            
        # REMOVE sticky="center" -> Widget will automatically center in grid cell
        sw.grid(row=0, column=i, padx=2) 
        local_widgets["switches"][key] = sw

    # Expand button ⚙
    def toggle():
        if detail_frame.winfo_viewable(): 
            detail_frame.grid_forget()
            exp.configure(text="⚙ ▼")
        else: 
            detail_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            exp.configure(text="⚙ ▲")
    
    exp = ctk.CTkButton(header_frame, text="⚙ ▼", width=40, height=24, fg_color="#333333", command=toggle)
    exp.grid(row=0, column=3, padx=(5, 0))

    item_container.paragraph_text = paragraph_text
    item_container.local_widgets = local_widgets

    return item_container

def generate_all(self):
    def run():
        items = self.queue_frame.winfo_children()
        if not items:
            return

        total = len(items)
        count = 0
        
        # Disable main "Generate All" button to avoid multiple clicks
        # (Assuming you have this button, if not skip)
        
        for index, item_container in enumerate(items):
            if hasattr(item_container, "paragraph_text") and hasattr(item_container, "local_widgets"):
                text = item_container.paragraph_text
                widgets = item_container.local_widgets
                
                # generate_one will run sequentially for each segment inside this sub-thread
                # prevents UI from freezing and updates button color immediately after each segment
                result = generate_one(self, text, widgets)
                
                if result:
                    count += 1
            
        # When complete, show notification back on main thread
        self.after(0, lambda: messagebox.showinfo("Notice", f"Completed generating {count}/{total} segments!"))

    # Start new thread
    threading.Thread(target=run, daemon=True).start()



def clone_all(self):
    """
    Function to Clone entire list in queue.
    Coordinates with clone_one logic but optimizes Model loading.
    """
    def run():
        # 1. Get list of segments
        items = self.queue_frame.winfo_children()
        if not items:
            self.after(0, lambda: messagebox.showwarning("Notice", "List is empty!"))
            return

        # 2. Request common voice sample
        ref_path = ctk.filedialog.askopenfilename(
            title="Choose common voice sample for the entire list", 
            filetypes=[("Audio", "*.wav *.mp3 *.m4a")]
        )
        if not ref_path: return

        # 3. Initialize Model once (Save time)
        print("📦 [Batch] Loading OpenVoice Model...")
        ckpt_dir = os.path.abspath("checkpoints_v2/converter")
        processed_dir = 'temp/processed'
        os.makedirs(processed_dir, exist_ok=True)
        
        try:
            # 'device' variable taken from config at top of cfg.py
            model = ToneColorConverter(os.path.join(ckpt_dir, 'config.json'), device=device)
            model.load_ckpt(os.path.join(ckpt_dir, 'checkpoint.pth'))
            
            # Extract sample voice SE once
            target_se, _ = se_extractor.get_se(ref_path, vc_model=model, target_dir=processed_dir, vad=True)
        except Exception as e:
            self.after(0, lambda m=str(e): messagebox.showerror("AI Error", f"Could not load model: {m}"))
            return

        # 4. Iterate through each segment
        for index, item_container in enumerate(items):
            idx = index + 1
            if hasattr(item_container, "paragraph_text") and hasattr(item_container, "local_widgets"):
                widgets = item_container.local_widgets
                source_path = os.path.abspath(f"temp/{idx}.wav")
                
                # Skip if no WAV file (Gen not clicked yet)
                if not os.path.exists(source_path):
                    print(f"⏩ Segment {idx} no source file, skipping.")
                    continue

                try:
                    print(f"🧬 [Batch] Processing segment {idx}...")
                    
                    # --- Coordination logic same as clone_one ---
                    # Fix too short audio error
                    temp_se_path = os.path.abspath(f"temp/se_batch_src_{idx}.wav")
                    audio_src = AudioSegment.from_file(source_path)
                    (audio_src * 5).export(temp_se_path, format="wav")
                    
                    # Extract source SE
                    source_se, _ = se_extractor.get_se(temp_se_path, vc_model=model, target_dir=processed_dir, vad=True)
                    
                    # Convert
                    wav_output = os.path.abspath(f"temp/cloned_batch_{idx}.wav")
                    model.convert(
                        audio_src_path=source_path, 
                        src_se=source_se,
                        tgt_se=target_se,
                        output_path=wav_output,
                        tau=0.3
                    )

                    # Overwrite old file with cloned file
                    if os.path.exists(wav_output):
                        time.sleep(0.2)
                        if os.path.exists(source_path): os.remove(source_path)
                        os.rename(wav_output, source_path)
                        
                        # Delete temp SE file
                        if os.path.exists(temp_se_path): os.remove(temp_se_path)

                        # Update UI immediately for each row
                        def update_ui(w=widgets):
                            if "clone" in w["buttons"]:
                                w["buttons"]["clone"].configure(fg_color="#6f42c1", text="Cloned")
                            if "gen" in w["buttons"]:
                                w["buttons"]["gen"].configure(fg_color="#28a745", text="AI-Gen")
                        self.after(0, update_ui)

                except Exception as e:
                    print(f"❌ Error processing segment {idx}: {str(e)}")
                    continue

        self.after(0, lambda: messagebox.showinfo("Complete", "Cloned entire list successfully!"))

    # Run in separate thread to prevent UI freezing
    threading.Thread(target=run, daemon=True).start()


def play_all(self):
    """
    Play entire segment list in queue in order.
    Uses VLC media list to play sequentially without user clicking.
    """
    import vlc
    
    # 1. Get list of all items
    items = self.queue_frame.winfo_children()
    if not items:
        messagebox.showwarning("Notice", "No segments in queue!")
        return

    # 2. Create list of files to play
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "temp")
    
    playlist = []  # Contains (file_path, display_name, duration)
    
    for idx, item in enumerate(items, 1):
        # Find WAV or MP3 file (WAV priority)
        file_path_wav = os.path.join(temp_dir, f"{idx}.wav")
        file_path_mp3 = os.path.join(temp_dir, f"{idx}.mp3")
        
        final_path = None
        if os.path.exists(file_path_wav):
            final_path = file_path_wav
        elif os.path.exists(file_path_mp3):
            final_path = file_path_mp3
        
        if final_path:
            # Get paragraph_text from item if available
            text = getattr(item, "paragraph_text", f"Segment {idx}")
            display_name = f"Segment {idx}: {text[:20]}..."
            
            # Calculate duration
            try:
                y, sr = librosa.load(final_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)
                playlist.append((final_path, display_name, duration))
            except Exception as e:
                print(f"⚠️ Error calculating duration for segment {idx}: {e}")
    
    if not playlist:
        messagebox.showwarning("Notice", "No audio files found!")
        return

    # 3. Create Media List and play
    print(f"🎵 Playing {len(playlist)} segments...")
    
    # Load first segment
    self.load_to_master(playlist[0][0], playlist[0][1], playlist[0][2])
    
    # Save playlist for auto-update (if needed for next track)
    self.playlist = playlist
    self.current_play_index = 0
    
    # Auto-play next segment when finished
    def on_playlist_end():
        """Called when current segment ends"""
        if hasattr(self, 'current_play_index') and self.current_play_index < len(self.playlist) - 1:
            self.current_play_index += 1
            file_path, display_name, duration = self.playlist[self.current_play_index]
            self.load_to_master(file_path, display_name, duration)
            print(f"🎵 Playing: {display_name}")
    
    # Save callback to update when track ends
    self.on_playlist_end = on_playlist_end


def save_all(self):
    """Lưu toàn bộ danh sách với tên file sạch (không dấu)"""
    items = self.queue_frame.winfo_children()
    if not items:
        messagebox.showwarning("Notice", "List is empty!")
        return

    msg = "Select save method:\n\n" \
          "- Automatic (Yes): Batch save to a folder.\n" \
          "- Manual (No): Confirm each file."
    
    choice = messagebox.askyesnocancel("Save All", msg)
    if choice is None: return

    if choice is True: # CHẾ ĐỘ TỰ ĐỘNG (Batch save)
        target_dir = filedialog.askdirectory(title="Select save folder")
        if not target_dir: return
        
        count = 0
        for i, item in enumerate(items):
            if hasattr(item, "paragraph_text"):
                idx = i + 1
                text_content = item.paragraph_text
                
                # Tìm file nguồn trong temp
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                temp_dir = os.path.join(base_dir, "temp")
                src_path = None
                for ext_type in [".wav", ".mp3"]:
                    p = os.path.join(temp_dir, f"{idx}{ext_type}")
                    if os.path.exists(p):
                        src_path = p
                        break
                
                if src_path:
                    ext = os.path.splitext(src_path)[1]
                    # Tạo tên file sạch: "SốTT_NoiDungKhongDau.wav"
                    clean_name = slugify_text(text_content, 30)
                    file_name = f"{idx:02d}_{clean_name}{ext}"
                    
                    dest = os.path.join(target_dir, file_name)
                    shutil.copy2(src_path, dest)
                    count += 1
        messagebox.showinfo("Success", f"Saved {count} files successfully.")

    elif choice is False: # CHẾ ĐỘ THỦ CÔNG
        for item in items:
            if hasattr(item, "paragraph_text"):
                # Gọi save_one sẽ tự động dùng logic tên không dấu mới
                self.save_one(item.paragraph_text)
