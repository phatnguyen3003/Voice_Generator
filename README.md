# 🎙️ Edge-TTS AI Generator Studio

A professional-grade, all-in-one Text-To-Speech (TTS) and Voice Cloning studio built with Python. This application combines the power of Microsoft's **Edge-TTS** with the advanced **OpenVoice V2** cloning engine and a rich **DSP (Digital Signal Processing)** suite.

![UI Preview](https://img.shields.io/badge/UI-CustomTkinter-blue)
![AI-Powered](https://img.shields.io/badge/AI-OpenVoiceV2-orange)
![Audio Engine](https://img.shields.io/badge/Audio-VLC%20%2F%20Librosa-green)

---

## ✨ Key Features

### 1. 🎤 Advanced TTS Generation
*   **Edge-TTS Integration**: Access 100+ high-quality voices from Microsoft Edge.
*   **Search & Filter**: Find the perfect voice and language in seconds.
*   **Real-time Preview**: Listen to your configuration before generating long scripts.

### 2. 🧬 AI Voice Cloning
*   **OpenVoice V2 Core**: Clone any voice sample with high fidelity.
*   **Tone Color Converter**: Transform standard TTS output into your custom voice sample.

### 3. 🎚️ Pro DSP Effects Suite
Fine-tune your audio with 10+ professional parameters available in both the Reference Editor and TTS Config:
*   **Time/Pitch**: Speed (0.5x - 2.0x) and Pitch adjustment.
*   **Dynamics**: Compressor (Threshold/Ratio), Limiter, and Noise Gate.
*   **Acoustics**: Reverb, Delay/Echo, and Chorus.
*   **EQ**: Bass and Treble boost.
*   **Normalization**: Automatic volume leveling.

### 4. 📦 Batch Processing Queue
*   **Smart Split**: Automatically split long texts into segments by paragraphs.
*   **Segment Control**: Assign different presets/voices to each paragraph.
*   **One-Click Actions**: Generate All, Clone All, and Save All segments at once.

### 5. 🔊 Master Player & UI
*   **VLC Engine**: Support for all audio formats with precise seeking.
*   **Collapsible Design**: Minimize the player and logs for a focused workspace.
*   **Live Metrics**: Real-time progress tracking and console activity logs.

---

## 🚀 Quick Start (Windows)

### 1. Requirements
*   **Python 3.10+**
*   **VLC Media Player** (Installer provided automatically if missing)
*   **Internet Connection** (For first-time model download ~2GB)

### 2. Installation & Launch
Simply download the project folder and run:
```batch
run.bat
```
This script will automatically:
1.  Create a Virtual Environment (`venv`).
2.  Install all required libraries via `pip`.
3.  Check/Download missing tools (`FFmpeg`, `VLC`).
4.  Check/Download AI Models (`OpenVoice V2`).
5.  Launch the application.

---

## 📂 Project Structure

*   `main.py`: Main GUI Application.
*   `function/`: Core logic modules (DSP, TTS, Cloning, Player).
*   `presets/`: Saved voice and effect configurations.
*   `checkpoints_v2/`: AI Model storage.
*   `temp/`: Workspace for processed audio segments.
*   `run.bat`: Simplified launcher.

---

## 🛠️ Tech Stack
*   **GUI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
*   **TTS**: [edge-tts](https://github.com/rany2/edge-tts)
*   **Cloning**: [OpenVoice V2](https://github.com/myshell-ai/OpenVoice)
*   **Signal Processing**: `Librosa`, `Pedalboard`, `Pydub`, `Soundfile`
*   **Audio Backend**: `python-vlc`
*   **AI Framework**: `PyTorch`

---

## 📝 License
This project is for educational and creative purposes. Please ensure you have the rights to the voice samples you use for cloning.

---
*Created with ❤️ for AI Voice Enthusiasts.*
