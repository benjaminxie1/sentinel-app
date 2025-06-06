# SENTINEL Fire Detection System

**🔥 PHASE 1 COMPLETE** - Professional fire safety command center with YOLOv8 detection engine

**CRITICAL: This is a SUPPLEMENTARY early warning tool only. Does NOT replace certified fire detection systems.**

## 🚀 Quick Start

### Requirements
- **Rust** (for Tauri desktop app)
- **Python 3.10+** with virtual environment
- **Node.js 18+** (for frontend build)
- **Modern desktop OS** (Windows 10+, macOS 10.15+, Ubuntu 18+)

### Installation
```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Install Node dependencies
npm install

# 4. Run the application
npm run tauri dev
```

### 🖥️ Application Features
- **Fire Safety Command Center** - Professional dark-themed dashboard
- **Real-time Monitoring** - Live camera feed surveillance grid
- **Alert Management** - P1/P2/P4 priority alert system with acknowledge/clear
- **System Health** - Performance metrics and diagnostic monitoring
- **Detection Settings** - Live threshold adjustment (95%/85%/70%)
- **Analytics Dashboard** - Performance graphs and system metrics

## ✅ Development Status - PHASE 1 COMPLETE
- ✅ **Professional Tauri Desktop App** - Fire command center UI
- ✅ **YOLOv8 Detection Engine** - Python backend with asyncio
- ✅ **YAML Configuration System** - Hot-reload threshold management
- ✅ **SQLite Alert Management** - Local logging with UI notifications
- ✅ **Multi-Camera Simulation** - Demo feeds for development/testing
- ✅ **Real-time Dashboard** - Live activity monitoring and status
- ✅ **TailwindCSS Interface** - Professional fire safety color scheme

## 🎯 Next Phase Goals
- **Real RTSP Integration** - Connect to actual security cameras
- **Fire Model Training** - Custom YOLOv8 model for fire detection
- **Network Redundancy** - Failover and offline operation
- **Field Testing** - Real-world validation and threshold optimization

## Architecture
Single-algorithm approach using YOLOv8 for visual fire/smoke detection on RGB camera feeds. Completely offline operation with configurable thresholds via YAML configuration.

See `CLAUDE.md` for detailed development guide and `architecture.md` for technical specifications.

## Safety Notice
This system provides supplementary early warning only. Always maintain certified fire alarm systems as primary detection. Never rely solely on this system for fire safety.