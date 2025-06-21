# Sentinel Fire Detection System

A supplementary fire detection system using computer vision. **Does NOT replace certified fire alarm systems.**

## Requirements

- **Python 3.10+**
- **Node.js 18+** 
- **Rust** (latest stable)
- **NVIDIA GPU** (recommended for real-time detection)
- **Operating System**: Windows 10+, macOS 10.15+, or Linux

## Quick Start - Development

```bash
# Clone the repository
git clone https://github.com/benjaminxie1/sentinel-app.git
cd sentinel-app

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Node dependencies
npm install

# Run in development mode
npm run tauri dev
```

## Production Build

```bash
# Build for production
npm run tauri build

# Output will be in:
# - Windows: src-tauri/target/release/bundle/msi/
# - macOS: src-tauri/target/release/bundle/dmg/
# - Linux: src-tauri/target/release/bundle/appimage/
```

## Installation - Production

### Linux
```bash
sudo ./scripts/install.sh
```

### Windows (Run as Administrator)
```powershell
.\scripts\install.ps1
```

## Camera Setup

1. **Launch the application**
2. **Navigate to Settings → Camera Management**
3. **Add cameras using:**
   - RTSP URL: `rtsp://username:password@camera-ip:554/stream`
   - HTTP URL: `http://camera-ip/video.mjpeg`
4. **Test connection before saving**
5. **Adjust detection thresholds in Settings → Detection Config**

## Configuration Files

After installation, configuration files are located in:
- Linux: `/etc/sentinel/`
- Windows: `C:\ProgramData\Sentinel\`

Key configuration files:
- `cameras.yaml` - Camera connection settings
- `detection_config.yaml` - Detection thresholds
- `alerts.yaml` - Alert notification settings

## Basic Usage

1. **Start the application**
2. **Monitor the surveillance grid for fire detection**
3. **Respond to alerts in the Activity Feed**
4. **Adjust thresholds if needed (Settings → Detection)**

## Troubleshooting

- **No cameras showing**: Check camera URLs and network connectivity
- **High CPU usage**: Reduce number of active cameras or lower frame rate
- **False alerts**: Increase detection thresholds in settings
- **App won't start**: Check Python/Node versions and GPU drivers

## Support

For issues or questions, please check the [project documentation](https://github.com/benjaminxie1/sentinel-app/wiki) or create an issue on GitHub.

## Contributors

- [Benjamin Xie](https://github.com/benjaminxie1)
- [Kevin Fei](https://github.com/Fairhain)
- [Mihir Bamdhamvamvuri](https://github.com/Phenixrigh)