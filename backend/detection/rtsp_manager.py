"""
RTSP Camera Manager
Handles real RTSP camera connections, ONVIF discovery, and stream management
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Dict, List, Optional, Callable, Tuple
from pathlib import Path
from queue import Queue, Empty
from dataclasses import dataclass
from urllib.parse import urlparse
import socket
import requests
import xml.etree.ElementTree as ET

@dataclass
class CameraConfig:
    """Camera configuration settings"""
    camera_id: str
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    fps: int = 15
    resolution: Tuple[int, int] = (640, 480)
    timeout: int = 10
    retry_interval: int = 30
    enabled: bool = True

@dataclass
class CameraStatus:
    """Camera status information"""
    camera_id: str
    connected: bool
    last_frame_time: float
    frame_count: int
    error_count: int
    last_error: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = None
    actual_fps: float = 0.0

class RTSPCamera:
    """Manages a single RTSP camera connection"""
    
    def __init__(self, config: CameraConfig):
        self.config = config
        self.is_running = False
        self.cap = None
        self.current_frame = None
        self.frame_queue = Queue(maxsize=5)
        self.status = CameraStatus(
            camera_id=config.camera_id,
            connected=False,
            last_frame_time=0,
            frame_count=0,
            error_count=0
        )
        self.logger = logging.getLogger(f"RTSP-{config.camera_id}")
        self.thread = None
        self.last_fps_check = time.time()
        self.fps_frame_count = 0
        
    def start(self) -> bool:
        """Start the RTSP camera stream"""
        if self.is_running:
            return True
            
        if not self.config.enabled:
            self.logger.info(f"Camera {self.config.camera_id} is disabled")
            return False
            
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        # Wait a moment to check if connection succeeds
        time.sleep(2)
        return self.status.connected
    
    def stop(self):
        """Stop the RTSP camera stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.thread:
            self.thread.join(timeout=5)
        self.status.connected = False
        self.logger.info(f"Camera {self.config.camera_id} stopped")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        try:
            # Get the most recent frame, discard older ones
            frame = None
            while not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
            return frame
        except Empty:
            return self.current_frame
    
    def _capture_loop(self):
        """Main capture loop for RTSP stream"""
        while self.is_running:
            try:
                if not self._connect():
                    time.sleep(self.config.retry_interval)
                    continue
                
                self._read_frames()
                
            except Exception as e:
                self.logger.error(f"Camera {self.config.camera_id} error: {e}")
                self.status.error_count += 1
                self.status.last_error = str(e)
                self.status.connected = False
                
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                time.sleep(self.config.retry_interval)
    
    def _connect(self) -> bool:
        """Connect to RTSP stream"""
        if self.cap and self.status.connected:
            return True
        
        try:
            # Build RTSP URL with authentication if provided
            rtsp_url = self._build_rtsp_url()
            
            self.logger.info(f"Connecting to camera {self.config.camera_id}: {self._sanitize_url(rtsp_url)}")
            
            # Configure OpenCV capture
            self.cap = cv2.VideoCapture(rtsp_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            if self.config.resolution:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
            
            # Test connection
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.status.connected = True
                self.status.resolution = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                        int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                self.logger.info(f"Camera {self.config.camera_id} connected: {self.status.resolution}")
                return True
            else:
                raise Exception("Failed to read initial frame")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to camera {self.config.camera_id}: {e}")
            self.status.connected = False
            self.status.last_error = str(e)
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    def _read_frames(self):
        """Read frames from the RTSP stream"""
        while self.is_running and self.cap and self.status.connected:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.logger.warning(f"Camera {self.config.camera_id} lost connection")
                    self.status.connected = False
                    break
                
                # Update frame info
                self.current_frame = frame
                self.status.frame_count += 1
                self.status.last_frame_time = time.time()
                
                # Add to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    pass  # Queue full, skip frame
                
                # Calculate FPS
                self._update_fps()
                
                # Small delay to control frame rate
                time.sleep(1.0 / self.config.fps)
                
            except Exception as e:
                self.logger.error(f"Frame read error for {self.config.camera_id}: {e}")
                self.status.connected = False
                break
    
    def _build_rtsp_url(self) -> str:
        """Build RTSP URL with authentication"""
        url = self.config.rtsp_url
        
        if self.config.username and self.config.password:
            # Parse URL and add credentials
            parsed = urlparse(url)
            if not parsed.username:  # Only add if not already in URL
                auth_url = f"{parsed.scheme}://{self.config.username}:{self.config.password}@{parsed.netloc}{parsed.path}"
                if parsed.query:
                    auth_url += f"?{parsed.query}"
                return auth_url
        
        return url
    
    def _sanitize_url(self, url: str) -> str:
        """Remove credentials from URL for logging"""
        try:
            parsed = urlparse(url)
            if parsed.username:
                # Reconstruct URL without credentials
                netloc = parsed.hostname
                if parsed.port:
                    netloc += f":{parsed.port}"
                return f"{parsed.scheme}://***:***@{netloc}{parsed.path}"
            return url
        except:
            return url
    
    def _update_fps(self):
        """Update FPS calculation"""
        self.fps_frame_count += 1
        now = time.time()
        
        if now - self.last_fps_check >= 5.0:  # Update every 5 seconds
            elapsed = now - self.last_fps_check
            self.status.actual_fps = self.fps_frame_count / elapsed
            self.fps_frame_count = 0
            self.last_fps_check = now

class ONVIFDiscovery:
    """ONVIF camera discovery service"""
    
    @staticmethod
    def discover_cameras(timeout: int = 5) -> List[Dict]:
        """Discover ONVIF cameras on the network"""
        discovered_cameras = []
        
        try:
            # Send WS-Discovery probe
            probe_message = """<?xml version="1.0" encoding="UTF-8"?>
            <env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope"
                         xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
                <env:Header>
                    <wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
                        urn:uuid:1234567890
                    </wsa:MessageID>
                    <wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
                        urn:schemas-xmlsoap-org:ws:2005:04:discovery
                    </wsa:To>
                    <wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">
                        http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe
                    </wsa:Action>
                </env:Header>
                <env:Body>
                    <wsdd:Probe xmlns:wsdd="http://schemas.xmlsoap.org/ws/2005/04/discovery">
                        <wsdd:Types>dn:NetworkVideoTransmitter</wsdd:Types>
                    </wsdd:Probe>
                </env:Body>
            </env:Envelope>"""
            
            # Send multicast probe
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            
            multicast_addr = ('239.255.255.250', 3702)
            sock.sendto(probe_message.encode(), multicast_addr)
            
            # Collect responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode('utf-8', errors='ignore')
                    
                    # Parse response for camera info
                    camera_info = ONVIFDiscovery._parse_probe_response(response, addr[0])
                    if camera_info:
                        discovered_cameras.append(camera_info)
                        
                except socket.timeout:
                    break
                except Exception as e:
                    logging.error(f"ONVIF discovery error: {e}")
            
            sock.close()
            
        except Exception as e:
            logging.error(f"ONVIF discovery failed: {e}")
        
        return discovered_cameras
    
    @staticmethod
    def _parse_probe_response(response: str, ip: str) -> Optional[Dict]:
        """Parse ONVIF probe response"""
        try:
            # Basic XML parsing for camera info
            if 'NetworkVideoTransmitter' in response:
                return {
                    'ip': ip,
                    'type': 'ONVIF Camera',
                    'rtsp_url': f'rtsp://{ip}:554/stream1',  # Common default
                    'discovered_time': time.time()
                }
        except Exception:
            pass
        
        return None

class RTSPManager:
    """Manages multiple RTSP cameras"""
    
    def __init__(self):
        self.cameras: Dict[str, RTSPCamera] = {}
        self.logger = logging.getLogger(__name__)
        self.status_callback: Optional[Callable] = None
    
    def add_camera(self, config: CameraConfig) -> bool:
        """Add a camera to the manager"""
        try:
            camera = RTSPCamera(config)
            self.cameras[config.camera_id] = camera
            self.logger.info(f"Added camera {config.camera_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add camera {config.camera_id}: {e}")
            return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the manager"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            self.logger.info(f"Removed camera {camera_id}")
            return True
        return False
    
    def start_camera(self, camera_id: str) -> bool:
        """Start a specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].start()
        return False
    
    def stop_camera(self, camera_id: str):
        """Stop a specific camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
    
    def start_all(self) -> int:
        """Start all cameras"""
        started = 0
        for camera in self.cameras.values():
            if camera.start():
                started += 1
        self.logger.info(f"Started {started}/{len(self.cameras)} cameras")
        return started
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.logger.info("Stopped all cameras")
    
    def get_frames(self) -> Dict[str, np.ndarray]:
        """Get current frames from all connected cameras"""
        frames = {}
        for camera_id, camera in self.cameras.items():
            if camera.status.connected:
                frame = camera.get_frame()
                if frame is not None:
                    frames[camera_id] = frame
        return frames
    
    def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """Get status of a specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].status
        return None
    
    def get_all_status(self) -> Dict[str, CameraStatus]:
        """Get status of all cameras"""
        return {cid: camera.status for cid, camera in self.cameras.items()}
    
    def discover_cameras(self, timeout: int = 5) -> List[Dict]:
        """Discover ONVIF cameras on the network"""
        return ONVIFDiscovery.discover_cameras(timeout)
    
    def test_rtsp_url(self, rtsp_url: str, username: str = None, password: str = None) -> Tuple[bool, str]:
        """Test an RTSP URL connection"""
        try:
            config = CameraConfig(
                camera_id="test",
                rtsp_url=rtsp_url,
                username=username,
                password=password,
                timeout=5
            )
            
            test_camera = RTSPCamera(config)
            success = test_camera._connect()
            
            if success:
                test_camera.stop()
                return True, "Connection successful"
            else:
                error = test_camera.status.last_error or "Unknown connection error"
                return False, error
                
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    # Test RTSP manager
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    manager = RTSPManager()
    
    # Discover cameras
    print("Discovering ONVIF cameras...")
    discovered = manager.discover_cameras()
    print(f"Found {len(discovered)} cameras: {discovered}")
    
    # Test with common RTSP URLs (these would be real camera URLs in production)
    test_configs = [
        CameraConfig("cam1", "rtsp://192.168.1.100:554/stream1", "admin", "password"),
        CameraConfig("cam2", "rtsp://192.168.1.101:554/stream1", "admin", "password"),
    ]
    
    for config in test_configs:
        manager.add_camera(config)
    
    # Start cameras
    manager.start_all()
    
    try:
        # Run for a short test
        time.sleep(10)
        
        # Get frames
        frames = manager.get_frames()
        print(f"Retrieved frames from {len(frames)} cameras")
        
        # Show status
        status = manager.get_all_status()
        for camera_id, stat in status.items():
            print(f"{camera_id}: Connected={stat.connected}, Frames={stat.frame_count}, FPS={stat.actual_fps:.1f}")
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        manager.stop_all()