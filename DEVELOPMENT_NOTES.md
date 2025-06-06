# Development Notes

## Phase 1 Requirements (from user)
- **Camera Sources**: Test videos and simulated streams (no real RTSP initially)
- **YOLOv8 Model**: Pre-trained fire detection model
- **Alerts**: Local logging initially with notifications tab in GUI
- **GUI**: Must be Tauri - minimal/sleek like Docker Desktop/Claude Desktop
- **Branding**: Software name "Sentinel", domain sentinelfire.org
- **Test Data**: User will provide datasets later - note for future model training

## Architecture Decisions
- Tauri frontend with Python backend detection engine
- Video file processing with simulated RTSP capabilities
- Local SQLite logging with real-time GUI notifications
- Configurable thresholds via YAML
- Completely offline operation

## GUI Design Reference
- Docker Desktop style: minimal, clean, dark theme
- Claude Desktop style: professional, focused interface
- Key tabs: Live Feed, Alerts/Notifications, Configuration, System Status