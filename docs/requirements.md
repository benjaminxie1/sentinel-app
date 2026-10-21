# Sentinel System Requirements & Architecture Specifications

## 1. System Overview
Sentinel is a high-reliability, supplementary early-warning fire and smoke detection system that runs continuously on edge devices and local servers. It processes real-time camera streams (RTSP / ONVIF) using computer vision (YOLOv8) and local sensor fusion without requiring an internet connection for core detection loops.

---

## 2. Hardware Requirements

### Minimum Edge / Development Specs
- **Processor**: Intel Core i5 (8th Gen+) or AMD Ryzen 5 (3000 series+) / Apple Silicon M1+
- **Memory**: 8 GB RAM
- **Storage**: 20 GB available SSD storage (for OS, dependencies, and model weights)
- **Cameras**: 1–2 IP cameras (RTSP/ONVIF) or standard USB webcam for simulation
- **Power**: Standard power source

### Production Enterprise Deployment Specs (10+ Concurrent Cameras)
- **Processor**: Intel Core i7 / Xeon or AMD Ryzen 7 / EPYC (8+ cores recommended)
- **Memory**: 16 GB - 32 GB DDR4/DDR5 RAM
- **GPU Acceleration**: NVIDIA GeForce RTX 3060 (12GB VRAM) or RTX 40-series / Tesla T4 / A2000 (CUDA 11.8+ / 12.0+)
  - *Target Inference*: < 20ms per frame batch across active streams
- **Storage**: 512 GB+ NVMe SSD (high IOPS for continuous SQLite event logging and 48-hour video circular buffering)
- **Networking**:
  - Dual Gigabit Ethernet ports (Primary LAN for IP camera subnet + Uplink WAN)
  - Optional: 4G/LTE/5G cellular modem for emergency alert failover
- **Power**: Uninterruptible Power Supply (UPS) with at least 1–2 hours runtime battery capacity

---

## 3. Supported Operating Systems

- **Linux**: Ubuntu 20.04 LTS / 22.04 LTS / 24.04 LTS, Debian 11/12, Rocky Linux 9 (recommended for dedicated headless servers)
- **Windows**: Windows 10 Pro / Enterprise (64-bit), Windows 11, Windows Server 2022
- **macOS**: macOS 12+ (Monterey, Ventura, Sonoma, Sequoia) - x86_64 and arm64

---

## 4. Software Dependencies

### Backend & AI Runtime
- **Python**: 3.10, 3.11, or 3.12
- **PyTorch**: 2.0+ with CUDA support (where NVIDIA GPU is available)
- **Ultralytics**: YOLOv8 (v8.0+)
- **OpenCV**: 4.8.0+ (`opencv-python` / `opencv-python-headless`)
- **SQLite**: 3.35+ (bundled with standard Python distribution)

### Frontend & Desktop Client
- **Node.js**: 18.0.0+ (LTS) or Node.js 20+
- **Package Manager**: npm 9+ or pnpm / yarn
- **Rust Toolchain**: 1.75.0+ (for compiling Tauri v2 application wrapper)
- **Tauri Prerequisites**:
  - *Linux*: `libwebkit2gtk-4.1-dev`, `build-essential`, `curl`, `wget`, `file`, `libxdo-dev`, `libssl-dev`
  - *Windows*: Microsoft Visual Studio C++ Build Tools & WebView2
  - *macOS*: Xcode Command Line Tools

---

## 5. Network & Camera Protocols

- **Video Ingestion**: RTSP (`rtsp://[username]:[password]@[ip]:[port]/[path]`), ONVIF Profile S/T, HTTP MJPEG
- **Discovery**: ONVIF WS-Discovery (UDP 3702)
- **Internal API**: Local REST / WebSocket server (`127.0.0.1:8000` / configurable)
- **Outbound Notifications (Optional)**:
  - Twilio REST API (HTTPS port 443) for SMS alerts
  - SMTP / SMTPS (ports 587 / 465) for email alerts
