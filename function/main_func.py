import shutil
from tkinter import messagebox
import customtkinter as ctk
from tkinter import filedialog
import os
import pygame
import threading

import function.ref as ref_func
import function.master_player as master_logic
import function.cfg as cfg_func


# --- SLIDER CREATION FUNCTION WITH UPDATED DEFAULT VALUES ---
def create_slider_row_grid(self, parent, name1, min1, max1, def1, name2, min2, max2, def2, row_idx):
    # Determine storage based on "parent" of this slider row
    # If parent is ref_slider_container, store in sliders_ref, else sliders_cfg
    storage = self.sliders_ref if parent == self.ref_slider_container else self.sliders_cfg

    # --- Column 1 ---
    f1 = ctk.CTkFrame(parent, fg_color="transparent")
    f1.grid(row=row_idx, column=0, sticky="ew", padx=2, pady=2)
    f1.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(f1, text=f"{name1}:", font=ctk.CTkFont(size=14), width=50, anchor="w").grid(row=0, column=0, padx=2)
        
    lbl_val1 = ctk.CTkLabel(f1, text=f"{def1:.1f}" if isinstance(def1, float) else str(def1), 
                            font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b8ed0", width=35)
    lbl_val1.grid(row=0, column=2, padx=2)

    # Add n=name1 to lambda to avoid closure issues in loop
    slider1 = ctk.CTkSlider(f1, from_=min1, to=max1, height=14, 
                            command=lambda v: lbl_val1.configure(text=f"{v:.1f}"))
    slider1.set(def1)
    slider1.grid(row=0, column=1, sticky="ew")
        
    # SAVE TO MEMORY: Save slider, label, and default value
    storage[name1.lower()] = {"widget": slider1, "label": lbl_val1, "default": def1}

    # --- Column 2 ---
    f2 = ctk.CTkFrame(parent, fg_color="transparent")
    f2.grid(row=row_idx, column=1, sticky="ew", padx=2, pady=2)
    f2.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(f2, text=f"{name2}:", font=ctk.CTkFont(size=14), width=50, anchor="w").grid(row=0, column=0, padx=2)

    lbl_val2 = ctk.CTkLabel(f2, text=f"{def2:.1f}" if isinstance(def2, float) else str(def2), 
                            font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b8ed0", width=35)
    lbl_val2.grid(row=0, column=2, padx=2)

    # Handle integer display for large values (like Volume, Ratio)
    slider2 = ctk.CTkSlider(f2, from_=min2, to=max2, height=14, 
                            command=lambda v: lbl_val2.configure(text=f"{int(v)}" if max2 > 10 else f"{v:.1f}"))
    slider2.set(def2)
    slider2.grid(row=0, column=1, sticky="ew")

    # SAVE TO MEMORY
    storage[name2.lower()] = {"widget": slider2, "label": lbl_val2, "default": def2}


def on_closing(self):
    """
    Handles when the user clicks X to close the program.
    """
    import os
    import shutil
    from tkinter import messagebox

    # 1. Temp directory path
    # Assuming project structure: /project/function/cfg.py -> go back 2 levels for /project/temp
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "temp")

    # 2. Check if folder has files
    has_files = False
    if os.path.exists(temp_dir):
        # Get list of files and subdirectories (excluding hidden files if needed)
        content = os.listdir(temp_dir)
        if len(content) > 0:
            has_files = True

    # 3. If files exist, ask the user
    if has_files:
        msg = "Temporary folder (temp) still contains audio data.\n\n" \
              "Do you want to DELETE ALL of them before exiting?\n" \
              "(Select 'No' to keep them for the next session)"
        
        # Yes/No/Cancel dialog
        # Yes: Delete and exit | No: Keep and exit | Cancel: Stay in program
        ans = messagebox.askyesnocancel("Confirm Exit", msg)
        
        if ans is True: # User selects YES
            try:
                shutil.rmtree(temp_dir) # Clear temp folder
                os.makedirs(temp_dir)   # Recreate empty folder to avoid errors
                print("✨ Temp folder cleared and program exited.")
                self.destroy() # Close program
            except Exception as e:
                print(f"Error during clearing: {e}")
                self.destroy()
        elif ans is False: # User selects NO
            print("💾 Data kept and program exited.")
            self.destroy()
        else: # User selects CANCEL
            return # Do nothing, return to program
    else:
        # If temp is empty, close without asking
        self.destroy()


# --- FUNCTION TO CHECK AND LOAD DEPENDENCIES BEFORE RUNNING ---
def check_system_setup():
    """
    Check and install required components (FFmpeg, VLC, models).
    This function should be called at application startup.
    """
    from function.download_models import check_and_setup_dependencies
    
    print("🔍 Checking system...")
    check_and_setup_dependencies()
    print("✅ System check complete!")


#=================================== Ref ===================================

def reset_ref_parameters(self):
    for key, data in self.sliders_ref.items():
        data["widget"].set(data["default"])
        # Update display text
        val = data["default"]
        data["label"].configure(text=f"{int(val)}" if val > 10 else f"{val:.1f}")

def select_file(self):
    """Acts as a middleman for file selection"""
    ref_func.select_file(self) 

def play_ref_audio(self):
    """Calls play function from ref.py"""
    threading.Thread(target=ref_func.play_ref_audio, args=(self,), daemon=True).start()

def save_ref_audio(self):
    """Calls save function from ref.py"""
    ref_func.save_ref_audio(self)

#=================================== Master Player ===================================

# --- COORDINATE FROM MASTER_PLAYER.PY ---
def load_to_master(self, audio_path, display_name, duration):
    master_logic.load_to_master(self, audio_path, display_name, duration)

def start_master_playback(self):
    master_logic.start_master_playback(self)

def toggle_master_playback(self):
    master_logic.toggle_master_playback(self)

def stop_master_playback(self):
    master_logic.stop_master_playback(self)

def seek_audio(self, value):
    master_logic.seek_audio(self, value)

def update_progress_loop(self):
    master_logic.update_progress_loop(self)


def toggle_player(self):
    """Handles collapsing/expanding player bar"""
    if not self.is_collapsed:
        # Collapse: Hide components, reduce height
        self.controls_frame.grid_remove()
        self.info_frame.grid_remove()
        self.vol_frame.grid_remove()
        self.player_container.configure(height=35)
        self.btn_collapse.configure(text="▲")
        self.is_collapsed = True
    else:
        # Expand: Show components again
        self.controls_frame.grid()
        self.info_frame.grid()
        self.vol_frame.grid()
        self.player_container.configure(height=100)
        self.btn_collapse.configure(text="▼")
        self.is_collapsed = False


def toggle_log(self):
    """Handles collapsing/expanding log console"""
    if not self.is_log_collapsed:
        # Collapse: Hide textbox, keep header
        self.log_textbox.grid_remove()
        self.btn_toggle_log.configure(text="▲")
        self.is_log_collapsed = True
    else:
        # Expand: Show textbox again
        self.log_textbox.grid()
        self.btn_toggle_log.configure(text="▼")
        self.is_log_collapsed = False



#=================================== Cfg ===================================

def reset_cfg_parameters(self):
    for key, data in self.sliders_cfg.items():
        data["widget"].set(data["default"])
        # Update display text
        val = data["default"]
        data["label"].configure(text=f"{int(val)}" if val > 10 else f"{val:.1f}")


def get_edge_voices(self):
    """Intermediate function to fetch data from edgetts_func and store in App variable"""
    try:
        # Call the function from edgetts.py
        voices = cfg_func.get_all_edge_voices()
        
        # IMPORTANT: Store in self so filter_voices has data to filter
        self.all_voices = voices 
        
        return voices
    except Exception as e:
        print(f"Edge TTS connection error: {e}")
        self.all_voices = ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]
        return self.all_voices

def filter_voices(self, event):
    """Filter voices function: language code first, then name"""
    search_term = self.search_entry.get().lower().strip()
    
    if not search_term:
        # If search entry is empty, show original list
        self.edge_voice_dropdown.configure(values=self.all_voices)
        return

    # 1. Group 1: Priority for voices starting with language code (e.g., 'vi' -> 'vi-VN-...')
    starts_with_term = [v for v in self.all_voices if v.lower().startswith(search_term)]
    
    # 2. Group 2: Contains keyword elsewhere (in voice talent name)
    # Remove results already in Group 1 to avoid duplicates
    contains_term = [
        v for v in self.all_voices 
        if search_term in v.lower() and v not in starts_with_term
    ]
    
    # Merge 2 groups (Priority Group 1 first)
    filtered = starts_with_term + contains_term
    
    if not filtered:
        filtered = ["Not found"]
    
    # 3. Update interface
    self.edge_voice_dropdown.configure(values=filtered)
    
    # Automatically select first result so user doesn't have to click again
    if filtered:
        self.edge_voice_dropdown.set(filtered[0])




def save_preset(self):
    cfg_func.save_preset(self)
    cfg_func.render_presets(self)

def load_preset_file(self, filename):
    cfg_func.load_preset_file(self, filename)

def render_presets(self):
    cfg_func.render_presets(self)

def delete_preset(self, preset_name):
    cfg_func.delete_preset(self, preset_name)

def preview_voice(self):
    cfg_func.preview_voice(self)

def process_text_to_queue(self):
    cfg_func.process_text_to_queue(self)

def add_queue_item(self, text, preset_name):
    cfg_func.add_queue_item(self, text, preset_name)

def generate_all(self):
    cfg_func.generate_all(self)

def clone_all(self):
    cfg_func.clone_all(self)

def play_all(self):
    cfg_func.play_all(self)

def save_all(self):
    cfg_func.save_all(self)
