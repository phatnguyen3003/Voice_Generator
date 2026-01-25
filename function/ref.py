import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pygame
import tempfile
from pydub import AudioSegment
import librosa
import soundfile as sf
import numpy as np
import shutil
from datetime import datetime

from function.master_player import load_to_master


# 1. Get absolute path to 'function' directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Determine full path to executable files
ffmpeg_exe = os.path.normpath(os.path.join(BASE_DIR, "ffmpeg.exe"))
ffprobe_exe = os.path.normpath(os.path.join(BASE_DIR, "ffprobe.exe"))

# 3. FORCE SYSTEM RECOGNITION (This is the most important step to fix your error)
# We add 'function' directory to PATH variable for this session
os.environ["PATH"] += os.pathsep + BASE_DIR

# 4. Configure Pydub with absolute paths
AudioSegment.converter = ffmpeg_exe
AudioSegment.ffprobe = ffprobe_exe

# 4. Configure Pydub (Important: Must assign both)
AudioSegment.converter = ffmpeg_exe
AudioSegment.ffprobe = ffprobe_exe

def select_file(self):
    # Open file selection dialog
    file_path = filedialog.askopenfilename(
        title="Select sample audio file",
        filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a")]
    )
    
    if file_path:
        # 1. Save path to Class variable for later use
        self.current_ref_path = file_path
        
        # 2. Update interface (Badge displays filename)
        file_name = os.path.basename(file_path)
        self.badge_ref.configure(
            text=f"Selected: {file_name}", 
            text_color="#2ecc71",
            fg_color="#1e272e"
        )
        
        print(f"File selected: {file_path}")

import librosa
import soundfile as sf
import numpy as np
import os
import tempfile

def play_ref_audio(self):
    try:
        # Get correct key names created from labels (lowercase)
        s_speed     = self.sliders_ref["speed"]["widget"].get()
        s_pitch     = self.sliders_ref["pitch"]["widget"].get()
        s_volume    = self.sliders_ref["volume"]["widget"].get()
        s_reverb    = self.sliders_ref["reverb"]["widget"].get()
        s_bass      = self.sliders_ref["bass"]["widget"].get()
        s_treble    = self.sliders_ref["treble"]["widget"].get()
        s_echo      = self.sliders_ref["echo"]["widget"].get()
        s_chorus    = self.sliders_ref["chorus"]["widget"].get()
        s_threshold = self.sliders_ref["thresh"]["widget"].get() 
        s_ratio     = self.sliders_ref["ratio"]["widget"].get()

        use_limiter   = self.ref_limiter_sw.get()
        use_normalize = self.ref_normalize_sw.get()
        use_gate      = self.ref_gate_sw.get()

    except KeyError as ke:
        print(f"Ref Logic KeyError: {ke}")
        return

    if hasattr(self, 'current_ref_path') and self.current_ref_path:
        try:
            # Load original file
            y, sr = librosa.load(self.current_ref_path, sr=None)

            # --- A. PITCH & SPEED (Librosa core) ---
            if s_pitch != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=s_pitch)
            if s_speed != 1.0:
                y = librosa.effects.time_stretch(y, rate=s_speed)

            # --- B. EQUALIZER (Bass/Treble) ---
            if s_bass != 0 or s_treble != 0:
                D = librosa.stft(y)
                if s_bass != 0:
                    D[:20, :] *= (10 ** (s_bass / 20)) 
                if s_treble != 0:
                    D[256:, :] *= (10 ** (s_treble / 20))
                y = librosa.istft(D)

            # --- C. DYNAMIC RANGE COMPRESSOR (Threshold/Ratio) ---
            # Helps balance loud/soft audio
            rms = np.sqrt(np.mean(y**2))
            thresh_linear = librosa.db_to_amplitude(s_threshold)
            if rms > thresh_linear:
                compression_gain = thresh_linear + (rms - thresh_linear) / s_ratio
                y = y * (compression_gain / rms)

            # --- D. ECHO & REVERB (Time-based effects) ---
            # Simple echo (large delay)
            if s_echo > 0:
                delay_samples = int(0.2 * sr)
                y_echo = np.zeros_like(y)
                y_echo[delay_samples:] = y[:-delay_samples]
                y = y + y_echo * s_echo

            # Simulated Reverb (multiple layers of microscopic delays overlapping)
            if s_reverb > 0:
                reverb_signal = np.zeros_like(y)
                for i in range(1, 5):
                    delay = int(0.03 * i * sr)
                    reverb_signal[delay:] += y[:-delay] * (s_reverb / (i * 2))
                y = y + reverb_signal

            # --- E. CHORUS (Phase effect) ---
            if s_chorus > 0:
                chorus_delay = int(0.025 * sr)
                y_chorus = np.zeros_like(y)
                y_chorus[chorus_delay:] = y[:-chorus_delay]
                y = (y + y_chorus * s_chorus) / (1 + s_chorus)



            # --- F. VOLUME & LIMITER ---
            y = y * s_volume
            # Prevent clipping (Clipping)
            max_val = np.max(np.abs(y))
            if max_val > 1.0:
                y = y / max_val


            # --- G. NOISE GATE & NORMALIZE ---
            if use_gate == 1:
                y[np.abs(y) < 0.005] = 0 # Block background noise

            if use_normalize == 1:
                max_peak = np.max(np.abs(y))
                if max_peak > 0: y = y / max_peak

            if use_limiter == 1:
                y = np.clip(y, -1.0, 1.0)

            # --- 3. EXPORT FILE AND LOAD MASTER ---
            # Get current file's directory path, then point to project root directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_folder = os.path.join(base_dir, "temp")

            # Create temp folder if it doesn't exist to avoid errors
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

            temp_path = os.path.join(temp_folder, "ref_master_output.wav")

            # Write file
            sf.write(temp_path, y, sr)
            
            duration = librosa.get_duration(y=y, sr=sr)
            self.load_to_master(temp_path, os.path.basename(self.current_ref_path), duration)

        except Exception as e:
            print(f"DSP Error: {e}")


def save_ref_audio(self):
    # 1. Determine temp file path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_path = os.path.join(base_dir, "temp", "ref_master_output.wav")

    # 2. Check if temp file exists
    if not os.path.exists(temp_path):
        messagebox.showwarning("Warning", "No processed data found! Please click Play first.")
        return

    # 3. CHECK FOR EDITS AND CONFIRMATION WARNING
    has_changes = False
    for key, item in self.sliders_ref.items():
        if abs(item["widget"].get() - item["default"]) > 0.01:
            has_changes = True
            break
            
    if not has_changes:
        # Instead of blocking, we ask the user
        confirm = messagebox.askyesno("Notice", "Parameters have not been changed (file is identical to original). Are you sure you want to continue saving?")
        if not confirm:
            return # User selects 'No', so stop

    # 4. CREATE FILENAME AND OPEN SAVE DIALOG
    now = datetime.now()
    time_str = now.strftime("save_%Hh%M_%d-%m-%Y")

    save_path = filedialog.asksaveasfilename(
        defaultextension=".wav",
        initialfile=f"{time_str}.wav",
        filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        title="Choose where to save result"
    )

    # 5. EXECUTE SAVE
    if save_path:
        try:
            shutil.copy2(temp_path, save_path)
            messagebox.showinfo("Success", f"File saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")