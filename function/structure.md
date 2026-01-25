# 📁 `function` Directory Structure

The `function` directory contains core modules that handle the logic for the Voice Generator application. Below is a detailed description of each file and its functionality.

---

## 📋 File List

### 1. **cfg.py** - Configuration & Main Audio Processing
**Main Functions:**
- 🎤 **Edge TTS Integration**: Retrieve voice list from Microsoft Edge TTS with caching.
- 🎚️ **Slider Management (UI)**: Create and manage parameter adjustment sliders.
- 💾 **Preset Management**: Save/load/delete audio settings in `presets/` folder.
- 📊 **Advanced DSP Processing**: Audio effects (reverb, delay, chorus, compressor, EQ, noise gate) using `librosa` and `pedalboard`.
- 🧬 **OpenVoice Integration**: Use `ToneColorConverter` for voice cloning/tone conversion.
- 🏗️ **Queue Logic**: Handle text segmentation and batch processing items.

---

### 2. **main_func.py** - Intermediate Functions (Routing/Dispatcher)
**Main Functions:**
- 🔀 **Dispatcher Pattern**: Routes UI calls from `main.py` to specific logic in `ref.py`, `master_player.py`, or `cfg.py`.
- 🎛️ **Create UI Components**: Shared utility for creating standardized slider rows.
- 🔗 **Event Binding**: Connects filtering logic and parameter resets.

---

### 3. **ref.py** - Reference Audio File Processing
**Main Functions:**
- 📁 **File Management**: Logic for selecting and editing specific voice samples.
- 🎵 **Audio DSP Processing**: Custom `librosa` based pipeline for real-time sound adjustment.
- 💾 **File Export**: Exports processed samples to `temp/` for cloning usage.

---

### 4. **master_player.py** - Main Playback Control (VLC Player)
**Main Functions:**
- ▶️ **VLC Integration**: Manages a global VLC instance for audio playback.
- 📊 **State Sync**: Updates UI progress bars and timestamps 10 times per second.
- ⏱️ **Seeking**: Precise jumping to specific timestamps in audio files.

---

### 5. **download_models.py** - System & Model Bootstrap
**Main Functions:**
- 📥 **FFmpeg Suite**: Auto-downloads `ffmpeg`, `ffplay`, and `ffprobe` if missing.
- 📦 **VLC Checker**: Detects VLC installation and offers automated installer.
- 🧬 **OpenVoice V2**: Downloads model checkpoints (~2GB) from HuggingFace with existence checking to skip repeated downloads.

---

## 🏗️ Architecture Summary

```
main.py (GUI Setup)
   │
   └── main_func.py (Dispatcher)
          ├── cfg.py (TTS & Batch & Cloning)
          ├── ref.py (Voice Sample Editor)
          └── master_player.py (VLC Engine)
```

## 🛠️ Key External Tools (Bundled)
- **ffmpeg.exe**: Core converter for Pydub/OpenVoice.
- **ffplay.exe**: Auxiliary playback tool.
- **ffprobe.exe**: Metadata analysis for audio files.
