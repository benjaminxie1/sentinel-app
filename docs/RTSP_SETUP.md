# RTSP Stream Setup Guide

This guide will help you set up RTSP (Real Time Streaming Protocol) streams for testing the Sentinel Fire Detection System. You can use your desktop/laptop camera, IP cameras, or video files as RTSP sources.

## Table of Contents
- [Desktop as RTSP Stream (Windows)](#desktop-as-rtsp-stream-windows)
- [Desktop as RTSP Stream (macOS)](#desktop-as-rtsp-stream-macos)
- [Desktop as RTSP Stream (Linux)](#desktop-as-rtsp-stream-linux)
- [Testing RTSP Connectivity](#testing-rtsp-connectivity)
- [Common RTSP URLs](#common-rtsp-urls)
- [Troubleshooting](#troubleshooting)

## Desktop as RTSP Stream (Windows)

### Method 1: Using OBS Studio + RTSP Plugin

1. **Install OBS Studio**:
   ```powershell
   # Using Chocolatey
   choco install obs-studio -y
   
   # Or download from: https://obsproject.com/
   ```

2. **Install OBS RTSP Server Plugin**:
   - Download from: https://github.com/iamscottxu/obs-rtspserver/releases
   - Extract to OBS plugins folder: `C:\Program Files\obs-studio\obs-plugins\64bit\`

3. **Configure OBS**:
   - Open OBS Studio
   - Add Source → Video Capture Device → Select your webcam
   - Tools → RTSP Server → Start Server
   - Default URL: `rtsp://localhost:4554/live`

### Method 2: Using VLC Media Player

1. **Install VLC**:
   ```powershell
   choco install vlc -y
   ```

2. **Start RTSP Stream**:
   ```powershell
   # Stream webcam
   "C:\Program Files\VideoLAN\VLC\vlc.exe" -vvv dshow:// :dshow-vdev="Your Camera Name" :dshow-adev="none" --sout "#transcode{vcodec=h264,vb=800,acodec=none}:rtp{sdp=rtsp://:8554/stream}" --no-sout-all --sout-keep
   
   # Stream desktop
   "C:\Program Files\VideoLAN\VLC\vlc.exe" -vvv screen:// --screen-fps=10 --sout "#transcode{vcodec=h264,vb=800,acodec=none}:rtp{sdp=rtsp://:8554/desktop}" --no-sout-all --sout-keep
   ```

3. **Access stream**: `rtsp://localhost:8554/stream`

### Method 3: Using FFmpeg

1. **Install FFmpeg**:
   ```powershell
   choco install ffmpeg -y
   ```

2. **List available devices**:
   ```powershell
   ffmpeg -list_devices true -f dshow -i dummy
   ```

3. **Start RTSP server with webcam**:
   ```powershell
   # Create a simple RTSP server using ffmpeg
   ffmpeg -f dshow -i video="Your Camera Name" -rtsp_transport tcp -f rtsp rtsp://localhost:8554/webcam
   ```

## Desktop as RTSP Stream (macOS)

### Method 1: Using FFmpeg

1. **Install FFmpeg**:
   ```bash
   brew install ffmpeg
   ```

2. **List available devices**:
   ```bash
   ffmpeg -f avfoundation -list_devices true -i ""
   ```

3. **Stream webcam**:
   ```bash
   # Replace "0" with your camera index from the list
   ffmpeg -f avfoundation -framerate 30 -i "0" -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/webcam
   ```

### Method 2: Using OBS Studio

1. **Install OBS**:
   ```bash
   brew install --cask obs
   ```

2. **Install RTSP plugin** (follow Windows instructions, adapted for macOS)

3. **Configure** as in Windows method

## Desktop as RTSP Stream (Linux)

### Method 1: Using GStreamer

1. **Install GStreamer**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
   
   # Fedora/RHEL
   sudo dnf install gstreamer1-tools gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly
   ```

2. **Start RTSP server**:
   ```bash
   # Install gst-rtsp-server
   sudo apt-get install libgstrtspserver-1.0-dev
   
   # Create simple RTSP server script
   cat > rtsp_server.py << 'EOF'
   #!/usr/bin/env python3
   import gi
   gi.require_version('Gst', '1.0')
   gi.require_version('GstRtspServer', '1.0')
   from gi.repository import Gst, GstRtspServer, GLib
   
   Gst.init(None)
   
   class RTSPServer:
       def __init__(self):
           self.server = GstRtspServer.RTSPServer()
           self.server.set_service("8554")
           
           factory = GstRtspServer.RTSPMediaFactory()
           factory.set_launch('v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=30/1 ! x264enc tune=zerolatency ! rtph264pay name=pay0 pt=96')
           factory.set_shared(True)
           
           mount_points = self.server.get_mount_points()
           mount_points.add_factory("/webcam", factory)
           
           self.server.attach(None)
           print("RTSP server started at rtsp://localhost:8554/webcam")
   
   if __name__ == '__main__':
       server = RTSPServer()
       loop = GLib.MainLoop()
       loop.run()
   EOF
   
   chmod +x rtsp_server.py
   ./rtsp_server.py
   ```

### Method 2: Using FFmpeg

```bash
# Stream webcam
ffmpeg -f v4l2 -i /dev/video0 -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/webcam

# Stream desktop
ffmpeg -f x11grab -s 1920x1080 -i :0.0 -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/desktop
```

## Testing RTSP Connectivity

### 1. Test with VLC

```bash
# Open VLC and go to Media → Open Network Stream
# Enter: rtsp://localhost:8554/webcam
```

### 2. Test with FFplay

```bash
ffplay -rtsp_transport tcp rtsp://localhost:8554/webcam
```

### 3. Test with Python

```python
import cv2

# Test RTSP stream
cap = cv2.VideoCapture("rtsp://localhost:8554/webcam")

if not cap.isOpened():
    print("Cannot open RTSP stream")
else:
    print("RTSP stream connected successfully")
    
    # Read a frame
    ret, frame = cap.read()
    if ret:
        print(f"Frame received: {frame.shape}")
        cv2.imshow("RTSP Test", frame)
        cv2.waitKey(0)
    
cap.release()
cv2.destroyAllWindows()
```

### 4. Configure Sentinel

Add the RTSP stream to your `cameras.yaml`:

```yaml
cameras:
  - id: "desktop_cam"
    name: "Desktop Camera"
    url: "rtsp://localhost:8554/webcam"
    username: ""  # Leave empty if no auth
    password: ""
    enabled: true
    detection_enabled: true
    fps_limit: 10
    reconnect_interval: 30
    timeout: 10

last_updated: 2024-01-15T10:00:00Z
```

## Common RTSP URLs

### IP Camera Brands

**Hikvision**:
```
rtsp://[username]:[password]@[ip_address]:554/Streaming/Channels/101
rtsp://[username]:[password]@[ip_address]:554/h264/ch1/main/av_stream
```

**Dahua**:
```
rtsp://[username]:[password]@[ip_address]:554/cam/realmonitor?channel=1&subtype=0
```

**Axis**:
```
rtsp://[username]:[password]@[ip_address]/axis-media/media.amp
```

**Foscam**:
```
rtsp://[username]:[password]@[ip_address]:88/videoMain
```

**Generic ONVIF**:
```
rtsp://[username]:[password]@[ip_address]:554/stream1
```

### Public Test Streams

```yaml
# Big Buck Bunny (test video)
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4

# Live example (may not always be available)
rtsp://demo:demo@ipvmdemo.dyndns.org:5541/onvif-media/media.amp
```

## Troubleshooting

### Windows Issues

1. **Firewall blocking RTSP**:
   ```powershell
   # Allow RTSP port
   New-NetFirewallRule -DisplayName "RTSP Server" -Direction Inbound -Protocol TCP -LocalPort 8554 -Action Allow
   ```

2. **Camera access denied**:
   - Go to Settings → Privacy → Camera
   - Allow apps to access camera

### macOS Issues

1. **Camera permissions**:
   - System Preferences → Security & Privacy → Camera
   - Allow Terminal/FFmpeg access

2. **Port already in use**:
   ```bash
   # Find process using port
   lsof -i :8554
   # Kill process
   kill -9 [PID]
   ```

### Linux Issues

1. **Camera device permissions**:
   ```bash
   # Add user to video group
   sudo usermod -a -G video $USER
   # Logout and login again
   ```

2. **V4L2 device not found**:
   ```bash
   # List video devices
   ls -la /dev/video*
   # Check device capabilities
   v4l2-ctl --list-devices
   ```

### General RTSP Issues

1. **Connection refused**:
   - Check if RTSP server is running
   - Verify firewall settings
   - Test with localhost first, then network IP

2. **Stream lag or choppy**:
   - Reduce resolution/framerate
   - Use hardware encoding if available
   - Check network bandwidth

3. **Authentication failures**:
   - Verify username/password
   - Try without authentication first
   - Check camera's RTSP settings

## Security Considerations

1. **Local Testing Only**:
   - Keep RTSP streams on local network
   - Use VPN for remote access
   - Don't expose RTSP ports to internet

2. **Authentication**:
   - Always use strong passwords
   - Change default camera credentials
   - Use RTSP over TLS when possible

3. **Network Isolation**:
   - Put cameras on separate VLAN
   - Use firewall rules to restrict access
   - Monitor for unauthorized access

## Integration with Sentinel

Once your RTSP stream is running:

1. **Update cameras.yaml** with your stream URL
2. **Restart Sentinel service**
3. **Check logs** for connection status
4. **Monitor dashboard** for detection results

For production deployments, always use proper IP cameras with reliable RTSP support rather than desktop streaming solutions.