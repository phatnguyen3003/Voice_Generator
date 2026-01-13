# Voice Generator - Advanced Text-to-Speech Application

A sophisticated voice generation application that combines multiple state-of-the-art technologies to convert text into natural-sounding speech with voice cloning and tone color customization capabilities.

## 🎯 Project Overview

Voice Generator is a powerful desktop and web-based application that leverages:
- **OpenVoice** - Advanced voice conversion and tone color preservation
- **Edge TTS** - High-quality text-to-speech synthesis from Microsoft Edge
- **Advanced Audio Processing** - Real-time audio effects and filtering using Pedalboard
- **Voice Presets** - Pre-configured voice profiles for quick voice generation
- **Web Interface** - User-friendly Bootstrap-based interface for easy interaction

### Key Features

- **Text-to-Speech Conversion**: Convert written text to natural-sounding audio
- **Voice Cloning**: Clone speaker characteristics using base speaker models
- **Tone Color Preservation**: Maintain emotional tone and voice characteristics during conversion
- **Audio Effects**: Apply professional audio processing effects including:
  - Noise gating and compression
  - EQ filtering (Low-shelf and High-shelf)
  - Distortion, chorus, delay, and reverb effects
  - Pitch shifting and limiting
- **Multi-Language Support**: Support for multiple languages including English (AU, BR, India, US), Spanish, French, Japanese, Korean, and Chinese
- **Voice Presets**: Save and load custom voice configurations
- **Web UI**: Intuitive web interface built with Bootstrap
- **Batch Processing**: Process multiple files efficiently

## 📋 System Requirements

- **OS**: Windows 7 or later (Python-based, may work on other OS with proper setup)
- **Python**: Version 3.10 or higher
- **RAM**: Minimum 8GB (16GB recommended for smooth operation)
- **GPU**: NVIDIA GPU with CUDA support recommended for faster processing (optional)
- **Storage**: At least 5GB free space for models

### Python Dependencies

Core dependencies include:
- **torch** - Deep learning framework
- **torchaudio** - Audio processing with PyTorch
- **librosa** - Audio analysis and feature extraction
- **soundfile** - WAV file reading/writing
- **edge-tts** - Microsoft Edge text-to-speech API
- **openvoice** - Voice conversion library
- **eel** - Python-JavaScript bridge for web interface
- **pedalboard** - Audio effects and processing
- **aiortc** - WebRTC support
- **accelerate** - Distributed training support

## 🚀 Installation Guide

### Prerequisites

Ensure you have **Python 3.10 or higher** installed on your system.

- Download Python from https://www.python.org/downloads/
- During installation, **check "Add Python to PATH"**
- Verify installation by opening Command Prompt and typing:
  ```bash
  python --version
  ```

### Quick Start - Run Setup Script

The installation process is automated. Simply execute the setup script:

**Option 1: Double-click (Easiest)**
1. Navigate to the project folder
2. Double-click `run.bat`
3. Wait for the setup to complete (may take 10-15 minutes)
4. Your default browser will automatically open the application

**Option 2: Command Prompt**
```bash
cd path\to\voice_generator
run.bat
```

### What the Setup Script Does

The `run.bat` script automatically handles:
- ✓ Verifying Python installation
- ✓ Creating virtual environment
- ✓ Installing all Python dependencies from `requirements.txt`
- ✓ Downloading pre-trained models and checkpoints
- ✓ Launching the web application
- ✓ Opening the interface in your browser

No manual configuration needed!

## 📖 Usage Guide

### Method 1: Using Batch Script (Windows)

The easiest way to start the application:

```bash
# Simply double-click or run:
run.bat

# Or from command line:
run.bat
```

The script will automatically:
1. Check Python installation
2. Verify dependencies
3. Download missing models if needed
4. Launch the web interface
5. Open your default browser

### Method 2: Manual Python Execution

```bash
# Activate virtual environment (if using one)
venv\Scripts\activate

# Run the application
python function.py
```

The application will start a local web server, typically at `http://localhost:8000`

### Method 3: Docker (Optional)

If you have Docker installed:

```bash
# Build Docker image
docker build -t voice-generator .

# Run container
docker run -p 8000:8000 voice-generator
```

## 🎛️ Using the Web Interface

### Basic Text-to-Speech
1. Navigate to the web interface (http://localhost:8000)
2. Enter text in the input field
3. Select language and voice style
4. Click "Generate" to create audio
5. Preview and download the generated audio

### Voice Customization
1. Select a base speaker model
2. Apply audio effects using the effects panel:
   - Adjust compression, EQ, and reverb
   - Modify pitch and tone
3. Save custom presets for future use

### Loading Voice Presets
```
# Presets are stored in the presets/ directory as JSON files
# Example: presets/test1.json

# To load a preset:
1. Click "Load Preset"
2. Select your custom preset file
3. Apply to generation
```

## 📁 Project Structure

```
voice_generator/
├── checkpoints_v2/              # Pre-trained model checkpoints
│   ├── base_speakers/           # Language-specific voice models
│   │   └── ses/                 # Base speaker models (.pth files)
│   └── converter/               # Main converter model
├── web/                         # Web interface files
│   ├── index.html              # Main HTML interface
│   ├── style.css               # Custom styling
│   ├── bootstrap.css           # Bootstrap framework
│   ├── bootstrap.bundle.min.js # Bootstrap JavaScript
│   ├── processed/              # Generated audio files
│   ├── temp_edit/              # Temporary editing files
│   ├── temp_preview/           # Preview audio files
│   └── used/                   # Archive of used files
├── presets/                     # Voice configuration presets
│   ├── test1.json
│   ├── test2.json
│   ├── test4.json
│   └── test5.json
├── function.py                  # Main application logic
├── download_models.py          # Model download utility
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
└── run.bat                     # Batch script for easy startup
```

## ⚙️ Configuration

### Voice Presets

Voice presets are JSON files that store voice configuration:

```json
test.json
{
    "speed": "0.9",
    "pitch": "11",
    "vol": "100",
    "reverb": "0",
    "bass": "0",
    "treble": "0",
    "useComp": false,
    "echo": "0",
    "chorus": "0",
    "useLimiter": true,
    "ps": "11",
    "wide": 0,
    "drive": "0",
    "hp_freq": "20",
    "useDesser": false,
    "voiceId": "en-US-RogerNeural"
}
```

Create custom presets in the `presets/` directory and load them in the web interface.

### Supported Languages and Voices

**Available Base Speakers** (in `checkpoints_v2/base_speakers/ses/`):
- English (Australian): `en-au.pth`
- English (Brazilian): `en-br.pth`
- English (Default): `en-default.pth`
- English (Indian): `en-india.pth`
- English (Latest): `en-newest.pth`
- English (US): `en-us.pth`
- Spanish: `es.pth`
- French: `fr.pth`
- Japanese: `jp.pth`
- Korean: `kr.pth`
- Chinese: `zh.pth`

## 🔧 Troubleshooting

### Common Issues and Solutions

**Issue: "Python is not installed or not added to PATH"**
- Solution: Reinstall Python and ensure "Add Python to PATH" is checked during installation
- Verify: Open Command Prompt and type `python --version`

**Issue: "ModuleNotFoundError: No module named 'torch'"**
- Solution: Reinstall dependencies
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

**Issue: "CUDA out of memory"**
- Solution: Use CPU instead
  - Edit `function.py` and set `device = 'cpu'`
  - Or reduce batch size in processing

**Issue: Models not downloading**
- Solution: Manually download from checkpoint sources
  ```bash
  python download_models.py --verbose
  ```
- Ensure sufficient disk space (5GB+) and stable internet connection

**Issue: Web interface not loading**
- Solution: Check if port 8000 is available
  - Windows: `netstat -ano | findstr :8000`
  - Close conflicting applications or change port in `function.py`

**Issue: Audio quality is poor**
- Solution: 
  - Adjust audio effects settings
  - Use higher quality base speaker model
  - Check input text quality (proper punctuation helps)

## 📊 Performance Tips

1. **GPU Acceleration**: Ensure CUDA is installed for NVIDIA GPUs
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Memory Optimization**:
   - Close other applications while processing
   - Process shorter texts for faster generation
   - Use batch processing for multiple files

3. **Quality Settings**:
   - Higher bitrate audio for better quality (trade-off with file size)
   - Multiple synthesis attempts for optimal results

## 🤝 Contributing

To improve the Voice Generator:

1. Test and report bugs
2. Suggest new features or voice effects
3. Optimize code for better performance
4. Create language-specific voice models


## 🔗 References and Credits

- **OpenVoice**: Advanced voice conversion technology
- **Microsoft Edge TTS**: High-quality speech synthesis
- **PyTorch**: Deep learning framework
- **Librosa**: Audio analysis library
- **Pedalboard**: Professional audio effects processing

## 📞 Support

For issues, questions, or suggestions:
- Check existing issues in the project repository
- Create detailed bug reports with steps to reproduce
- Include system information and error messages
- Provide sample audio or text that causes issues

## ✨ Future Enhancements

- Real-time voice synthesis with low latency
- Multi-speaker mixing and blending
- Advanced voice emotion control
- Cloud-based processing support
- Mobile application version
- Enhanced multi-language support
- Voice activity detection and processing
- Custom neural voice training

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Status**: Active Development


