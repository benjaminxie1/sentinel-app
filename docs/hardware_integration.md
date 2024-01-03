# Sentinel Hardware Integration Guide

## Table of Contents
1. [Arduino Sensor Integration](#arduino-sensor-integration)
2. [RTSP Camera Configuration](#rtsp-camera-configuration)
3. [Network Topology](#network-topology)
4. [Troubleshooting](#troubleshooting)

## Arduino Sensor Integration

### Supported Hardware
- **Microcontrollers**: Arduino Mega 2560, Arduino Uno R3
- **Temperature/Humidity**: DHT22, DHT11, BME280
- **Smoke Detection**: MQ-2, MQ-135, MQ-7
- **Flame Detection**: IR Flame Sensor Module
- **Communication**: USB Serial, RS-485 (for long distances)

### Wiring Diagram
```
Arduino Mega 2560 Pin Assignments:
- Pin 2: DHT22 Data
- Pin A0: MQ-2 Analog Out
- Pin A1: MQ-135 Analog Out  
- Pin 3: Flame Sensor Digital
- Pin A2: Flame Sensor Analog
- Pin 13: Status LED
- Pin 9: Buzzer
- 5V: Sensor power
- GND: Common ground
```

### Serial Protocol
Communication uses binary packets at 115200 baud:

```
Packet Structure (24 bytes):
[SYNC_BYTE][TEMP_FLOAT][HUM_FLOAT][SMOKE_FLOAT][CO_FLOAT][RESERVED][FLAME_BOOL][IR_UINT16][END_BYTE]
```

Commands:
- `$INIT` - Initialize sensors
- `$CONFIG` - Get configuration
- `$CALIBRATE` - Start calibration
- `$HEARTBEAT` - Keep-alive
- `$STATS` - Get statistics

### Python Integration Example
```python
from backend.hardware.arduino_bridge import ArduinoBridge

# Initialize connection
bridge = ArduinoBridge(port='/dev/ttyACM0')
bridge.connect()
bridge.start_monitoring()

# Register callback for sensor data
def on_sensor_data(reading):
    print(f"Temperature: {reading.temperature}°C")
    print(f"Smoke: {reading.smoke_ppm} ppm")
    
bridge.callback = on_sensor_data
```

### Calibration Procedure
1. Place sensors in clean air environment
2. Power on system and wait 60 seconds for sensor warmup
3. Send `$CALIBRATE` command
4. Wait 20 seconds for calibration to complete
5. Verify with `$CAL_STATUS` command

## RTSP Camera Configuration

### Tested Camera Models

#### Hikvision
| Model | Resolution | Codec | Stream URLs | Notes |
|-------|------------|-------|------------|-------|
| DS-2CD2132F-I | 2048x1536 | H.264 | `/h264/ch1/main/av_stream` | Dome camera, IR |
| DS-2CD2T85FWD-I8 | 3840x2160 | H.265+ | `/Streaming/Channels/101` | 4K, WDR |
| DS-2DE5225IW-AE | 1920x1080 | H.265 | `/Streaming/Channels/101` | PTZ, 25x zoom |

#### Dahua
| Model | Resolution | Codec | Stream URLs | Notes |
|-------|------------|-------|------------|-------|
| IPC-HDW5231R-Z | 1920x1080 | H.265 | `/cam/realmonitor?channel=1&subtype=0` | Varifocal |
| IPC-HFW5241E-ZE | 1920x1080 | H.265+ | `/cam/realmonitor?channel=1&subtype=0` | AI features |

#### Axis
| Model | Resolution | Codec | Stream URLs | Notes |
|-------|------------|-------|------------|-------|
| M3065-V | 1920x1080 | H.264 | `/axis-media/media.amp` | Mini dome |
| P3245-LVE | 1920x1080 | H.265 | `/axis-media/media.amp?videocodec=h265` | Outdoor |

### RTSP URL Formats

**Hikvision:**
```
rtsp://[username]:[password]@[ip]:[port]/Streaming/Channels/[channel]
Main: channel=101, Sub: channel=102
```

**Dahua:**
```
rtsp://[username]:[password]@[ip]:[port]/cam/realmonitor?channel=1&subtype=[type]
Main: subtype=0, Sub: subtype=1
```

**Axis:**
```
rtsp://[username]:[password]@[ip]/axis-media/media.amp?[parameters]
Parameters: resolution=1920x1080&fps=15&compression=50
```

### Network Optimization

#### Bandwidth Requirements
- **4K Stream (H.265)**: 4-8 Mbps
- **1080p Stream (H.264)**: 2-4 Mbps
- **720p Stream (H.264)**: 1-2 Mbps
- **Sub Stream**: 256-512 Kbps

#### Recommended Settings
```yaml
# config/camera_settings.yaml
optimization:
  main_stream:
    resolution: 1920x1080
    fps: 15
    bitrate: 2048
    codec: H.265
    i_frame_interval: 30
    
  sub_stream:
    resolution: 640x360
    fps: 10
    bitrate: 256
    codec: H.264
    
  network:
    buffer_size: 1  # Reduce latency
    tcp_nodelay: true
    multicast: false  # Use unicast
    rtsp_transport: tcp  # More reliable than UDP
```

### Camera Discovery

The system supports automatic ONVIF camera discovery:

```python
from backend.cameras.rtsp_advanced import RTSPAdvanced

manager = RTSPAdvanced()

# Discover cameras on network
cameras = manager.discover_onvif_cameras(timeout=5)

for camera in cameras:
    print(f"Found: {camera['brand']} at {camera['ip']}")
    
    # Test connection
    result = manager.test_camera_connection(
        ip=camera['ip'],
        username='admin',
        password='password'
    )
    
    if result['rtsp_main']:
        print(f"Main stream available: {result['streams'][0]['resolution']}")
```

## Network Topology

### Recommended Architecture
```
Internet
    |
[Firewall]
    |
[Core Switch] --- [NVR/Storage]
    |
[PoE Switch] ---- [IP Cameras]
    |
[Sentinel Server]
    |
[Arduino Sensors via USB]
```

### VLAN Configuration
- **VLAN 10**: Management network
- **VLAN 20**: Camera network (isolated)
- **VLAN 30**: Sensor network
- **VLAN 40**: Alert/notification network

### Firewall Rules
```
# Allow RTSP from Sentinel to Cameras
permit tcp 192.168.1.100 192.168.20.0/24 eq 554

# Allow ONVIF discovery
permit udp 192.168.1.100 192.168.20.0/24 eq 3702

# Allow HTTP for camera configuration
permit tcp 192.168.1.100 192.168.20.0/24 eq 80

# Block camera internet access
deny ip 192.168.20.0/24 0.0.0.0/0
```

## Troubleshooting

### Arduino Connection Issues

**Problem**: "Arduino not detected"
```bash
# Check USB devices
ls /dev/ttyACM* /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER

# Monitor serial output
screen /dev/ttyACM0 115200
```

**Problem**: "Sensor readings invalid"
- Check wiring connections
- Verify 5V power supply
- Run calibration: `$CALIBRATE`
- Check pull-up resistors on I2C sensors

### Camera Stream Issues

**Problem**: "Cannot connect to camera"
```bash
# Test RTSP connectivity
ffmpeg -i rtsp://admin:password@192.168.1.64:554/stream1 -frames:v 1 test.jpg

# Check network route
ping 192.168.1.64

# Verify credentials with curl
curl -u admin:password http://192.168.1.64/ISAPI/System/deviceInfo
```

**Problem**: "High latency/dropped frames"
- Switch from UDP to TCP transport
- Reduce stream resolution/framerate
- Check network congestion with iperf3
- Increase receive buffer size

**Problem**: "H.265 codec not working"
```bash
# Install NVIDIA codec SDK
sudo apt install nvidia-cuda-toolkit

# Verify GPU acceleration
nvidia-smi

# Check codec support
ffmpeg -decoders | grep h265
```

### Performance Optimization

#### CPU Usage High
- Enable GPU decoding for H.265
- Reduce number of concurrent streams
- Use sub-streams for monitoring
- Implement frame skipping

#### Memory Leaks
- Monitor with: `watch -n 1 'ps aux | grep sentinel'`
- Check camera reconnection logic
- Verify frame buffer cleanup
- Review sensor data queue management

#### Network Bandwidth
- Enable multicast if supported
- Use VBR instead of CBR
- Implement adaptive bitrate
- Configure QoS on switches

## Best Practices

### Sensor Placement
- Mount smoke sensors on ceiling
- Position flame sensors with clear line of sight
- Avoid HVAC vents for temperature sensors
- Use multiple sensors for redundancy

### Camera Positioning
- Cover all exits and high-risk areas
- Avoid backlighting and glare
- Mount at 8-10 feet height
- Overlap coverage zones by 20%

### System Maintenance
- Monthly sensor calibration
- Quarterly camera lens cleaning
- Annual cable inspection
- Regular firmware updates

### Data Management
- Retain alerts for 90 days minimum
- Archive critical events permanently
- Implement automated backups
- Test recovery procedures monthly

## Compliance Considerations

### NFPA Standards
- NFPA 72: National Fire Alarm Code
- NFPA 1221: Emergency Communications
- Maintain supplementary role designation
- Document all system modifications

### Privacy Regulations
- Limit camera coverage to public areas
- Implement data retention policies
- Secure all network communications
- Maintain access logs

### Installation Records
- Document all hardware serial numbers
- Record calibration dates and values
- Maintain network topology diagrams
- Keep firmware version inventory
