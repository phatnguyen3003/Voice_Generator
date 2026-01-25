# Voice Generator UI Widget Structure (Updated)

## Overall Layout
```
AiVoiceStudio (CTk Window)
├── Row 0: main_area (CTkScrollableFrame)
│   ├── Title: "Edge-TTS AI Generator Studio"
│   ├── Reference Audio Editor Frame (ref_frame)
│   └── Columns Frame (2-column layout)
│       ├── Left Column: Configuration & FX (config_col)
│       └── Right Column: Text Processing (text_col)
│
├── Row 1: log_container (Fixed & Collapsible System Log)
│   ├── Log Header (Title + Collapse Button)
│   └── log_textbox (Consolas font, redirected stdout/stderr)
│
└── Row 2: player_container (Fixed Bottom Master Player)
    ├── Collapse Button
    ├── Controls Frame (Play/Pause/Stop buttons)
    ├── Info Frame (Now Playing + Progress Slider + Time)
    └── Volume Control Frame
```

---

## 1. Main Window Configuration
- **Class**: `AiVoiceStudio(ctk.CTk)`
- **Title**: "Edge-TTS AI Generator Studio"
- **Size**: 1100x850 (min: 900x750)
- **Appearance**: Dark mode, Blue theme
- **Grid**: 1 column, 3 rows (main_area + log_container + player_container)

---

## 2. Default Values Dictionary
```python
self.d = {
    "speed": 1.0,      # Speed multiplier (0.5 - 2.0)
    "pitch": 0,        # Pitch shift (-50 to 50)
    "volume": 100,     # Volume level (0 - 250)
    "reverb": 0,       # Reverb effect (0 - 100)
    "bass": 0,         # Bass boost (0 - 15)
    "treble": 0,       # Treble boost (0 - 15)
    "echo": 0,         # Echo effect (0 - 100)
    "chorus": 0,       # Chorus effect (0 - 100)
    "threshold": -20.0, # Compressor Threshold (-60 to 0)
    "ratio": 4.0        # Compressor Ratio (1 to 20)
}
```

---

## 3. Reference Audio Editor (ref_frame) - Yellow Border (#f1c40f)
**Location**: row=1, column=0 in main_area

- **Features**: Select voice sample, adjust 10 parameters (Speed to Ratio), toggle switches (Limiter, Normalize, Noise Gate), Play/Save/Reset.
- **DSP**: Uses Librosa and custom signal processing for real-time preview.

---

## 4. Two-Column Layout (columns_frame)
**Location**: row=2, column=0 in main_area  
**Weight ratio**: Left 4 : Right 6

### 4.1 Left Column: Configuration & FX (config_col)
- **Voice Search**: Real-time filtering for Edge-TTS voices.
- **FX Sliders**: Identical parameters to Reference Editor for TTS generation.
- **Preset System**: Save/Load/Delete presets as JSON files.
- **Preview**: Generate a short sample of the selected voice with FX.

### 4.2 Right Column: Text Processing (text_col)
- **Text Input**: Multi-line textbox for script.
- **Queue System**: Segmented rendering with manual control over each segment.
- **Batch Actions**: Generate All, Clone All, Play All, Save All.

---

## 5. Fixed Bottom Master Player (player_container)
**Location**: row=2, column=0 (fixed at bottom of window)  
- **Logic**: Uses `python-vlc` for high-quality audio playback and seeking.
- **UI**: Large Play/Pause button, real-time progress slider, time display (Current/Total), and Volume slider (0-100%).

---

## 6. System Log Console
**Location**: row=1, column=0 (above player)
- **Feature**: Redirects `stdout` and `stderr` to a scrollable UI textbox.
- **Filtering**: Filters logs with specific emojis (🧬, 🚀, ✅, ❌) to show only operational activity to the user.

---

## 7. Dependencies & Tools
- **GUI**: `customtkinter`
- **Audio Engine**: `python-vlc`
- **Signal Processing**: `librosa`, `pedalboard`, `pydub`, `numpy`
- **AI Core**: `edge-tts`, `openvoice-cli` (ToneColorConverter), `torch`
- **Local Tools**: `ffmpeg.exe`, `ffprobe.exe` (bundled in `function/`)

---

## 8. Implementation Status
✅ **COMPLETED:**
- Full DSP pipeline (Reverb, Echo, Chorus, EQ, Compressor, Limiter)
- Edge-TTS integration with search & filter
- OpenVoice V2 Voice Cloning
- Batch segment processing queue
- Preset management system
- System log redirection and filtering
- Automated setup (`run.bat`, `requirements.txt`, `download_models.py`)
- VLC-based Master Player with seeking

⚠️ **IN PROGRESS:**
- Optimizing AI model loading speed
- Fine-tuning voice cloning quality for short segments
