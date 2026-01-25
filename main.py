import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
import os
import sys
import vlc
import threading
from function.main_func import *

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ConsoleRedirector:
    def __init__(self, textbox, original_stream):
        self.textbox = textbox
        self.original_stream = original_stream

    def write(self, text):
        # 1. ALWAYS print to terminal (for debugging)
        self.original_stream.write(text)
        
        # 2. FILTER for UI Log (Operational Activity only)
        # We only show logs that start with our activity markers (emojis)
        activity_markers = ["🧬", "🚀", "✅", "❌", "🎵", "📦", "✨", "🔍", "⏩", "💻", "⚠️", "🔍"]
        stripped_text = text.strip()
        if any(stripped_text.startswith(m) for m in activity_markers):
            self.textbox.after(0, lambda: self._insert_text(text))

    def _insert_text(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def flush(self):
        self.original_stream.flush()

class AiVoiceStudio(ctk.CTk):

    # --- REGISTER FUNCTIONS FROM EXTERNAL FILES ---
    # This assignment helps functions recognize 'self' when running
    create_slider_row_grid = create_slider_row_grid
    on_closing = on_closing
    check_system_setup = check_system_setup
    toggle_log = toggle_log

    # ref
    select_file = select_file
    play_ref_audio = play_ref_audio
    reset_ref_parameters = reset_ref_parameters
    save_ref_audio = save_ref_audio

    # cfg
    toggle_player = toggle_player
    seek_audio = seek_audio
    reset_cfg_parameters = reset_cfg_parameters
    get_edge_voices = get_edge_voices
    filter_voices = filter_voices
    save_preset = save_preset
    load_preset_file = load_preset_file
    render_presets = render_presets
    delete_preset = delete_preset
    preview_voice = preview_voice
    process_text_to_queue = process_text_to_queue
    add_queue_item = add_queue_item
    generate_all = generate_all
    clone_all = clone_all
    play_all = play_all
    save_all = save_all



    #master player
    load_to_master = load_to_master
    start_master_playback = start_master_playback
    toggle_master_playback = toggle_master_playback
    stop_master_playback = stop_master_playback
    seek_audio = seek_audio
    update_progress_loop = update_progress_loop

    
    
    



    def __init__(self):
        super().__init__()
        
        # --- INITIALIZE VARIABLES ---
        self.instance = vlc.Instance('--no-video', '--quiet')
        self.player = self.instance.media_player_new()
        
        self.d = {
            "speed": 1.0, "pitch": 0, "volume": 100,
            "reverb": 0, "room_size": 0.5, "width": 0.5, # Add Reverb details
            "bass": 0, "treble": 0,
            "echo": 0, "chorus": 0,
            "threshold": -20.0, "ratio": 4.0 # Add Compressor
        }
        self.sliders_ref = {}
        self.sliders_cfg = {}

        self.is_dragging = False
        self.is_paused = False

        # --- GUI SETUP ---
        self.title("Edge-TTS AI Generator Studio")
        self.geometry("1100x850") # Increased height for Log section
        self.minsize(900, 750)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        self.main_area.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.main_area, text="Edge-TTS AI Generator Studio", 
                      font=ctk.CTkFont(size=26, weight="bold"), text_color="#3b8ed0").grid(row=0, column=0, pady=20)
        
        # ================= 3. LOG CONSOLE (Fixed & Collapsible) =================
        self.log_container = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#333333")
        self.log_container.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.log_container.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(self.log_container, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=5)
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_header, text="💻 System Log", 
                      font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa").grid(row=0, column=0, sticky="w", padx=10)
        
        self.is_log_collapsed = False
        self.btn_toggle_log = ctk.CTkButton(log_header, text="▼", width=25, height=20, 
                                            fg_color="#333333", hover_color="#444444", command=self.toggle_log)
        self.btn_toggle_log.grid(row=0, column=1, padx=5, pady=2)

        self.log_textbox = ctk.CTkTextbox(self.log_container, height=120, font=("Consolas", 12), state="disabled", fg_color="#000000")
        self.log_textbox.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        # REDIRECT PRINT TO TEXTBOX (Mirroring Terminal)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        # Redirection will be enabled after heavy initial checks below

        # --- RUN INITIAL SYSTEM CHECKS (Prints to terminal only) ---
        print("🔍 Starting initial system check...")
        check_system_setup()
        print("✅ System initial check complete!")

        # NOW enable redirection for runtime operational logs
        sys.stdout = ConsoleRedirector(self.log_textbox, self.original_stdout)
        sys.stderr = ConsoleRedirector(self.log_textbox, self.original_stderr)

        print("💻 Log system initialized. Operational logs will appear here.")


        # ================= 1. REFERENCE AUDIO EDITOR =================
        self.ref_frame = ctk.CTkFrame(self.main_area, border_width=2, border_color="#f1c40f")
        self.ref_frame.grid(row=1, column=0, sticky="ew", pady=10)
        self.ref_frame.grid_columnconfigure(0, weight=1)

        header_ref = ctk.CTkFrame(self.ref_frame, fg_color="transparent")
        header_ref.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        header_ref.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(header_ref, text="🛠️ Reference Audio Editor", 
                      font=ctk.CTkFont(weight="bold"), text_color="#f1c40f").grid(row=0, column=0, sticky="w")
        
        self.badge_ref = ctk.CTkLabel(header_ref, text="File Not Selected", fg_color="#1a1a1a", corner_radius=5, padx=10)
        self.badge_ref.grid(row=0, column=1, sticky="e", padx=10)
        ctk.CTkButton(header_ref, text="📁 Select Reference Voice File", width=80, command=self.select_file).grid(row=0, column=2, sticky="e")

        
        # Slider Container (Cập nhật với giá trị mặc định)
        self.ref_slider_container = ctk.CTkFrame(self.ref_frame, fg_color="transparent")
        self.ref_slider_container.grid(row=2, column=0, sticky="ew", padx=15)
        self.ref_slider_container.grid_columnconfigure((0, 1), weight=1)

        self.create_slider_row_grid(self.ref_slider_container, "Speed", 0.5, 2.0, self.d["speed"], "Pitch", -50, 50, self.d["pitch"], 0)
        self.create_slider_row_grid(self.ref_slider_container, "Volume", 0, 250, self.d["volume"], "Reverb", 0, 100, self.d["reverb"], 1)
        self.create_slider_row_grid(self.ref_slider_container, "Bass", 0, 15, self.d["bass"], "Treble", 0, 15, self.d["treble"], 2)
        self.create_slider_row_grid(self.ref_slider_container, "Echo", 0, 100, self.d["echo"], "Chorus", 0, 100, self.d["chorus"], 3)
        self.create_slider_row_grid(self.ref_slider_container, "Thresh", -60, 0, self.d["threshold"], "Ratio", 1, 20, self.d["ratio"], 4)

        # --- SWITCHES CONTAINER ---
        self.ref_switch_frame = ctk.CTkFrame(self.ref_slider_container, fg_color="transparent")
        self.ref_switch_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Evenly divide 3 columns for switches
        self.ref_switch_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. Limiter Switch (On by default to protect speakers)
        self.ref_limiter_sw = ctk.CTkSwitch(self.ref_switch_frame, text="Limiter", 
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            progress_color="#2ecc71") # Green when on
        #self.ref_limiter_sw.select() # Default on
        self.ref_limiter_sw.grid(row=0, column=0, padx=5, sticky="w")

        # 2. Công tắc Normalize
        self.ref_normalize_sw = ctk.CTkSwitch(self.ref_switch_frame, text="Normalize", 
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            progress_color="#2ecc71")
        self.ref_normalize_sw.grid(row=0, column=1, padx=5, sticky="w")

        # 3. Công tắc Noise Gate
        self.ref_gate_sw = ctk.CTkSwitch(self.ref_switch_frame, text="Noise Gate", 
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        progress_color="#2ecc71")
        self.ref_gate_sw.grid(row=0, column=2, padx=5, sticky="w")


        self.play_ref_voice_btn = ctk.CTkButton(self.ref_frame, text="▶ Play Reference Voice", fg_color="#28FF53", text_color="black")
        self.play_ref_voice_btn.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        self.play_ref_voice_btn.configure(command=self.play_ref_audio)

        self.save_ref_voice_btn = ctk.CTkButton(self.ref_frame, text="💾 Save Reference Voice Setting", fg_color="#a86700")
        self.save_ref_voice_btn.grid(row=4, column=0, sticky="ew", padx=15, pady=10)
        self.save_ref_voice_btn.configure(command=self.save_ref_audio)

        self.reset_ref_voice_btn = ctk.CTkButton(self.ref_frame, text="🔄️ Reset Reference Voice Setting", fg_color="#e74c3c",command=self.reset_ref_parameters)
        self.reset_ref_voice_btn.grid(row=5, column=0, sticky="ew", padx=15, pady=10)









        # ================= 2. CONFIGURATION COLUMN (LEFT) =================
        self.columns_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.columns_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        self.columns_frame.grid_columnconfigure(0, weight=4) 
        self.columns_frame.grid_columnconfigure(1, weight=6)

        self.config_col = ctk.CTkFrame(self.columns_frame)
        self.config_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.config_col.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.config_col, text="Configuration & FX", font=ctk.CTkFont(weight="bold"), text_color="#3b8ed0").grid(row=0, column=0, pady=10)


        ctk.CTkLabel(self.config_col, text="Preset", font=ctk.CTkFont(weight="bold"), text_color="#ef4646").grid(row=1, column=0, pady=10)

        self.preset_frame = ctk.CTkFrame(self.config_col, fg_color="#2b2b2b", border_width=1, border_color="#444444")
        self.preset_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        self.preset_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) # Divide into 4 columns for buttons


        # 1. Get voice list first
        all_voices = self.get_edge_voices() 

        # Find your Search Entry and assign event
        self.search_entry = ctk.CTkEntry(self.config_col, placeholder_text="Search voice...")
        self.search_entry.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_voices)

        # Use OptionMenu instead of ComboBox
        self.edge_voice_dropdown = ctk.CTkOptionMenu(
            self.config_col, 
            values=all_voices,
            width=200,
            dynamic_resizing=False # Keep fixed size to prevent interface jumping
        )
        self.edge_voice_dropdown.grid(row=4, column=0, sticky="ew", padx=15, pady=5)

        self.edge_voice_dropdown.set(all_voices[0] if all_voices else "")
        self.cfg_slider_container = ctk.CTkFrame(self.config_col, fg_color="transparent")
        self.cfg_slider_container.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.cfg_slider_container.grid_columnconfigure((0, 1), weight=1)



        self.create_slider_row_grid(self.cfg_slider_container, "Speed", 0.5, 2.0, self.d["speed"], "Pitch", -50, 50, self.d["pitch"], 0)
        self.create_slider_row_grid(self.cfg_slider_container, "Volume", 0, 250, self.d["volume"], "Reverb", 0, 100, self.d["reverb"], 1)
        self.create_slider_row_grid(self.cfg_slider_container, "Bass", 0, 15, self.d["bass"], "Treble", 0, 15, self.d["treble"], 2)
        self.create_slider_row_grid(self.cfg_slider_container, "Echo", 0, 100, self.d["echo"], "Chorus", 0, 100, self.d["chorus"], 3)
        self.create_slider_row_grid(self.cfg_slider_container, "Thresh", -60, 0, self.d["threshold"], "Ratio", 1, 20, self.d["ratio"], 4)

        # --- SWITCHES CONTAINER ---
        self.cfg_switch_frame = ctk.CTkFrame(self.cfg_slider_container, fg_color="transparent")
        self.cfg_switch_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Evenly divide 3 columns for switches
        self.cfg_switch_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. Limiter Switch (On by default to protect speakers)
        self.cfg_limiter_sw = ctk.CTkSwitch(self.cfg_switch_frame, text="Limiter", 
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            progress_color="#2ecc71") # Green when on
        #self.cfg_limiter_sw.select() # Default on
        self.cfg_limiter_sw.grid(row=0, column=0, padx=5, sticky="w")

        # 2. Công tắc Normalize
        self.cfg_normalize_sw = ctk.CTkSwitch(self.cfg_switch_frame, text="Normalize", 
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            progress_color="#2ecc71")
        self.cfg_normalize_sw.grid(row=0, column=1, padx=5, sticky="w")

        # 3. Công tắc Noise Gate
        self.cfg_gate_sw = ctk.CTkSwitch(self.cfg_switch_frame, text="Noise Gate", 
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        progress_color="#2ecc71")
        self.cfg_gate_sw.grid(row=0, column=2, padx=5, sticky="w")


        self.lbl_preview_tip = ctk.CTkLabel(
            self.config_col, 
            text="📝 Preview Text (Blank for Default):", 
            font=ctk.CTkFont(size=14, family="Arial", weight="bold"),
            text_color="#aaaaaa"
        )
        self.lbl_preview_tip.grid(row=7, column=0, sticky="w", padx=17, pady=(5, 0))

        self.preview_textbox = ctk.CTkTextbox(self.config_col, height=60, border_width=1, border_color="#444444")
        self.preview_textbox.grid(row=8, column=0, sticky="ew", padx=15, pady=5)

        self.preview_voice_btn = ctk.CTkButton(self.config_col, text="▶ Preview Voice", fg_color="transparent", border_width=2, command=self.preview_voice)
        self.preview_voice_btn.grid(row=9, column=0, sticky="ew", padx=15, pady=5)

        self.btn_save_preset = ctk.CTkButton(
            self.config_col, 
            text="💾 Save current as preset", 
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.save_preset
        )
        self.btn_save_preset.grid(row=10, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkButton(self.config_col, text="🔄 Reset Parameters", 
              fg_color="#c0392b", hover_color="#e74c3c", 
              command=self.reset_cfg_parameters).grid(row=11, column=0, sticky="ew", padx=15, pady=(10, 20))
        


        # --- RIGHT COLUMN: TEXT PROCESSING ---
        self.text_col = ctk.CTkFrame(self.columns_frame)
        self.text_col.grid(row=0, column=1, sticky="nsew")
        self.text_col.grid_columnconfigure(0, weight=1)
        
        self.text_col.grid_rowconfigure(5, weight=1) 

        # 1
        ctk.CTkLabel(self.text_col, text="Text Processing & Batch Queue", 
                     font=ctk.CTkFont(weight="bold"), text_color="#2ecc71").grid(row=0, column=0, pady=(10, 5))
        
        # 2. Raw Input Label & Textbox
        self.input_label = ctk.CTkLabel(self.text_col, text="Raw Script Input:", font=ctk.CTkFont(size=11))
        self.input_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.textbox = ctk.CTkTextbox(self.text_col, height=250) 
        self.textbox.grid(row=2, column=0, sticky="ew", padx=15, pady=(2, 5))

        self.btn_split = ctk.CTkButton(self.text_col, text="✂️ Split Text to Queue", 
                                       fg_color="#34495e", hover_color="#2ecc71", 
                                       height=28, font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_split.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        self.btn_split.configure(command=self.process_text_to_queue)

        # 3. Queue Label & Scrollable Frame
        self.queue_label = ctk.CTkLabel(self.text_col, text="Processing Queue:", font=ctk.CTkFont(size=11))
        self.queue_label.grid(row=4, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.queue_frame = ctk.CTkScrollableFrame(self.text_col, fg_color="#1a1a1a")
        self.queue_frame.grid(row=5, column=0, sticky="nsew", padx=15, pady=(2, 5))
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # 4. Batch Controls
        self.batch_frame = ctk.CTkFrame(self.text_col, fg_color="transparent")
        self.batch_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.batch_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_gen_all = ctk.CTkButton(self.batch_frame, text="⚡ Generate All", fg_color="#2ecc71", text_color="black", height=32)
        self.btn_gen_all.grid(row=0, column=0, padx=2)
        self.btn_gen_all.configure(command=lambda: threading.Thread(target=self.generate_all, daemon=True).start())

        self.btn_clone_all = ctk.CTkButton(self.batch_frame, text="👥 Clone All", fg_color="#e67e22", height=32)
        self.btn_clone_all.grid(row=0, column=1, padx=2)
        self.btn_clone_all.configure(command=lambda: threading.Thread(target=self.clone_all, daemon=True).start())

        self.btn_play_all = ctk.CTkButton(self.batch_frame, text="▶ Play All", fg_color="#3498db", height=32)
        self.btn_play_all.grid(row=0, column=2, padx=2)
        self.btn_play_all.configure(command=self.play_all)

        self.btn_save_all = ctk.CTkButton(self.batch_frame, text="💾 Save All", fg_color="#9b59b6", height=32)
        self.btn_save_all.grid(row=0, column=3, padx=2)
        self.btn_save_all.configure(command=self.save_all)











        # ================= 4. BOTTOM MASTER PLAYER =================
        # Main container for player bar
        self.player_container = ctk.CTkFrame(self, height=100, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333333")
        self.player_container.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.player_container.grid_columnconfigure(1, weight=1) 

        # Collapse/Expand button
        self.is_collapsed = False
        self.btn_collapse = ctk.CTkButton(self.player_container, text="▼", width=25, height=25, 
                                        fg_color="#333333", hover_color="#444444", command=self.toggle_player)
        self.btn_collapse.place(relx=1.0, rely=0, anchor="ne", x=-10, y=5)

        # --- Control components (Play/Pause only) ---
        self.controls_frame = ctk.CTkFrame(self.player_container, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, padx=20, pady=15)

        self.master_play_btn = ctk.CTkButton(
            self.controls_frame, text="▶", width=55, height=55, corner_radius=28, 
            font=("Arial", 22),
            command=self.toggle_master_playback 
        )
        self.master_play_btn.grid(row=0, column=0, padx=5)

        # --- File info & Progress ---
        self.info_frame = ctk.CTkFrame(self.player_container, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="ew", padx=10)
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.lbl_now_playing = ctk.CTkLabel(self.info_frame, text="Master Output: Ready", 
                                            font=("Arial", 12, "bold"), text_color="#2ecc71")
        self.lbl_now_playing.grid(row=0, column=0, sticky="w")

        # Function to update virtual time label when dragging
        def on_slider_dragging(val):
            if hasattr(self, 'master_duration'):
                curr_min, curr_sec = divmod(int(val), 60)
                max_min, max_sec = divmod(int(self.master_duration), 60)
                self.lbl_time.configure(text=f"{curr_min:02d}:{curr_sec:02d} / {max_min:02d}:{max_sec:02d}")

        # Progress Slider (Increase button_length for easier dragging)
        self.master_progress = ctk.CTkSlider(
            self.info_frame, from_=0, to=100, height=14,
            button_length=12,  # <--- Modified: Easier to click
            button_color="#ffffff",
            progress_color="#3b8ed0",
            command=on_slider_dragging # <--- Update time when dragging
        )

        # Ràng buộc sự kiện kéo/thả
        self.master_progress.bind("<Button-1>", lambda e: setattr(self, 'is_dragging', True))
        self.master_progress.bind("<ButtonRelease-1>", self.seek_audio)

        self.master_progress.set(0) 
        self.master_progress.grid(row=1, column=0, sticky="ew", pady=5)

        self.lbl_time = ctk.CTkLabel(self.info_frame, text="00:00 / 00:00", font=("Arial", 11))
        self.lbl_time.grid(row=1, column=1, padx=10)

        # --- Master Volume ---
        self.vol_frame = ctk.CTkFrame(self.player_container, fg_color="transparent")
        self.vol_frame.grid(row=0, column=2, padx=20)

        ctk.CTkLabel(self.vol_frame, text="🔊", width=20).grid(row=0, column=0)
        self.lbl_vol_percent = ctk.CTkLabel(self.vol_frame, text="80%", font=("Arial", 11, "bold"), width=35)
        self.lbl_vol_percent.grid(row=0, column=2, padx=(5, 0))

        self.master_vol = ctk.CTkSlider(
            self.vol_frame, from_=0, to=100, width=100,
            command=lambda v: self.lbl_vol_percent.configure(text=f"{int(v)}%")
        )
        self.master_vol.set(80)
        self.master_vol.grid(row=0, column=1)

        # Run update loop
        self.update_progress_loop()


        self.render_presets()



if __name__ == "__main__":
    app = AiVoiceStudio()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()