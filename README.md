# Fire Detection System

**CRITICAL: This is a SUPPLEMENTARY early warning tool only. Does NOT replace certified fire detection systems.**

## Quick Start

### Requirements
- Python 3.10+
- NVIDIA GPU (RTX 3060 or better)
- RGB security cameras with RTSP/ONVIF support

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Download YOLOv8 model (first run)
python src/detection/setup_model.py

# Configure cameras and thresholds
cp config/detection_config.yaml config/local_config.yaml
# Edit config/local_config.yaml for your setup

# Run detection system
python src/main.py
```

### Configuration
Edit `config/local_config.yaml` to adjust:
- Detection confidence thresholds
- Camera RTSP stream URLs
- Alert notification settings
- Environmental adjustments

## Development Status
Core detection engine development:
- [x] Project structure setup
- [ ] Camera integration (RTSP/OpenCV)
- [ ] YOLOv8 fire detection implementation
- [ ] Configuration system
- [ ] Basic alerting
- [ ] Tauri GUI application

## Architecture
Single-algorithm approach using YOLOv8 for visual fire/smoke detection on RGB camera feeds. Completely offline operation with configurable thresholds via YAML configuration.

See `CLAUDE.md` for detailed development guide and `architecture.md` for technical specifications.

## Safety Notice
This system provides supplementary early warning only. Always maintain certified fire alarm systems as primary detection. Never rely solely on this system for fire safety.