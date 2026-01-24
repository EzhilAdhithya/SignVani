# SignVani Raspberry Pi 4 Setup - COMPLETED ✓

**Setup Date**: 2 January 2026  
**Branch**: overhaul

## Setup Summary

SignVani has been successfully initialized on Raspberry Pi 4 with all required components installed and verified.

---

## Installation Details

### ✅ 1. Python Virtual Environment
- **Created**: `.venv/` directory
- **Python Version**: 3.13.5
- **Status**: Active

### ✅ 2. Dependencies Installed
```
vosk==0.3.45              # Offline Speech Recognition
PyAudio==0.2.14           # Audio I/O
numpy>=1.26.0             # Numerical Computing
scipy>=1.11.0             # Scientific Computing
nltk>=3.8.1               # Natural Language Processing
```

**Installation Command**:
```bash
pip install -r requirements.txt
```

### ✅ 3. Models Downloaded
| Model | Size | Path |
|-------|------|------|
| **Vosk ASR** (vosk-model-small-en-in-0.4) | 54.1 MB | `models/vosk/` |
| **NLTK Data** (punkt, wordnet, stopwords, averaged_perceptron_tagger) | ~24 MB | `models/nltk_data/` |

**Download Command**:
```bash
python scripts/setup_models.py
```

### ✅ 4. System Dependencies
Pre-installed on the system:
- `portaudio19-dev` - Audio capture support
- `python3-dev` - Python development headers
- `libasound2-dev` - ALSA sound library

---

## Test Results

All unit and integration tests **PASSED** ✓

### Audio Subsystem Tests
```
python -m tests.unit.test_audio
✓ 6 tests passed
```
- Voice Activity Detection (VAD)
- Spectral Subtraction (Noise Filtering)
- Circular Buffer Operations

### ASR Subsystem Tests
```
python -m tests.unit.test_asr
✓ 2 tests passed
```
- ASRWorker thread processing
- VoskEngine singleton initialization

### Integration Tests (Phase 1 & 2)
```
python -m tests.integration.test_pipeline_phase1_2
✓ 2 tests passed
```
- End-to-end audio capture to transcript generation
- Real Vosk model loading verification

---

## Project Structure

```
/home/labs/Desktop/SignVani/
├── .venv/                    # Python virtual environment
├── config/                   # Configuration settings
│   └── settings.py          # Frozen dataclass configs
├── src/                      # Source code
│   ├── audio/               # Audio capture, VAD, noise filtering
│   ├── asr/                 # Speech recognition
│   └── nlp/                 # NLP pipeline (pending)
├── models/                   # Downloaded models
│   ├── vosk/                # Vosk ASR model
│   └── nltk_data/           # NLTK corpus data
├── scripts/                 # Utility scripts
│   └── setup_models.py      # Model downloader
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docs/                    # Documentation
├── main.py                  # Entry point (pending)
└── requirements.txt         # Python dependencies
```

---

## Architecture Overview

**Pipeline**: Audio Capture → VAD → Noise Filter → Buffer → ASR Worker → NLP (pending) → Database (pending) → SiGML (pending)

### Completed Phases

✅ **Phase 0**: Scaffolding & Configuration
✅ **Phase 1**: Audio Subsystem (Capture, VAD, Noise Filter, Buffering)
✅ **Phase 2**: ASR Integration (Vosk Engine, Worker Thread)

### Pending Phases

⏳ **Phase 3**: Database Layer (SQLite schema, Gloss mapping, FTS5)
⏳ **Phase 4**: NLP Engine (Text preprocessing, Grammar transformation)
⏳ **Phase 5**: SiGML Generation (HamNoSys to XML conversion)
⏳ **Phase 6**: Pipeline Integration (Main orchestrator, end-to-end app)

---

## Running the Application

### Activate Virtual Environment
```bash
cd /home/labs/Desktop/SignVani
source .venv/bin/activate
```

### Run Unit Tests
```bash
python -m tests.unit.test_audio
python -m tests.unit.test_asr
```

### Run Integration Tests
```bash
python -m tests.integration.test_pipeline_phase1_2
```

### Run Main Application (when ready)
```bash
python main.py
```

---

## Configuration

All settings are centralized in `config/settings.py`:

- **Audio Config**: Sample rate (16kHz), channels, buffer size
- **Vosk Config**: Model path, optimization settings
- **NLP Config**: NLTK data path, lemmatization options
- **Database Config**: SQLite path, cache settings
- **Pipeline Config**: Queue sizes, memory optimization

Modify settings as needed for your Raspberry Pi 4 hardware specs.

---

## Next Steps

1. Implement **Phase 3 (Database Layer)**:
   - Design SQLite schema for gloss mappings
   - Set up FTS5 for fuzzy matching
   - Implement LRU caching

2. Implement **Phase 4 (NLP Engine)**:
   - Text preprocessing pipeline
   - Grammar transformation (SVO → SOV)
   - Gloss mapping and lookup

3. Implement **Phase 5 (SiGML Generation)**:
   - Convert HamNoSys to SiGML XML

4. Implement **Phase 6 (Pipeline Integration)**:
   - Build main orchestrator
   - Create end-to-end application entry point

---

## Memory & Performance Notes

- **Vosk Model**: 54.1 MB (optimized for Raspberry Pi)
- **NumPy/SciPy**: Pre-compiled wheels from `piwheels.org` for ARM architecture
- **Audio Processing**: Uses `float32` and `__slots__` for memory efficiency
- **Thread Safety**: All inter-component communication uses `queue.Queue`

---

## Troubleshooting

### If imports fail:
```bash
# Verify virtual environment is active
source .venv/bin/activate

# Verify all packages installed
pip list
```

### If models fail to download:
```bash
# Re-run setup script
python scripts/setup_models.py

# Or download manually:
python -m nltk.downloader -d models/nltk_data wordnet averaged_perceptron_tagger
```

### If audio tests fail:
- Ensure a microphone is connected
- Check ALSA is properly configured
- Verify PyAudio installation: `python -c "import pyaudio; print(pyaudio.PyAudio().get_device_count())"`

---

**Setup Status**: ✅ READY FOR DEVELOPMENT

For detailed architecture documentation, see: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
