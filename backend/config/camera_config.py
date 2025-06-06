"""
Camera Configuration Management
Handles RTSP camera setup, ONVIF discovery, and configuration persistence
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import ipaddress
import socket
import threading
import time

@dataclass
class CameraProfile:
    """Camera configuration profile"""
    camera_id: str
    name: str
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    fps: int = 15
    resolution: Tuple[int, int] = (1920, 1080)
    enabled: bool = True
    location: str = ""
    detection_zones: List[List[Tuple[int, int]]] = None
    
    def __post_init__(self):
        if self.detection_zones is None:
            self.detection_zones = []

@dataclass
class NetworkScan:
    """Network scanning configuration"""
    ip_ranges: List[str]
    common_ports: List[int]
    timeout: int = 3
    max_threads: int = 50

class CameraConfigManager:
    """Manages camera configurations and discovery"""
    
    def __init__(self, config_file: str = "config/cameras.yaml"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self.cameras: Dict[str, CameraProfile] = {}
        self.discovered_devices: List[Dict] = []
        self.load_config()
    
    def load_config(self):
        """Load camera configurations from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'cameras' in data:
                        for cam_data in data['cameras']:
                            profile = CameraProfile(**cam_data)
                            self.cameras[profile.camera_id] = profile
                        self.logger.info(f"Loaded {len(self.cameras)} camera configurations")
            else:
                self.logger.info("No camera config file found, starting with empty configuration")
        except Exception as e:
            self.logger.error(f"Failed to load camera config: {e}")
    
    def save_config(self):
        """Save camera configurations to file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            config_data = {
                'cameras': [asdict(camera) for camera in self.cameras.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Saved {len(self.cameras)} camera configurations")
        except Exception as e:
            self.logger.error(f"Failed to save camera config: {e}")
    
    def add_camera(self, profile: CameraProfile) -> bool:
        """Add a camera profile"""
        try:
            self.cameras[profile.camera_id] = profile
            self.save_config()
            self.logger.info(f"Added camera: {profile.camera_id} ({profile.name})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add camera {profile.camera_id}: {e}")
            return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera profile"""
        if camera_id in self.cameras:
            del self.cameras[camera_id]
            self.save_config()
            self.logger.info(f"Removed camera: {camera_id}")
            return True
        return False
    
    def get_camera(self, camera_id: str) -> Optional[CameraProfile]:
        """Get a camera profile by ID"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> Dict[str, CameraProfile]:
        """Get all camera profiles"""
        return self.cameras.copy()
    
    def get_enabled_cameras(self) -> Dict[str, CameraProfile]:
        """Get only enabled camera profiles"""
        return {cid: cam for cid, cam in self.cameras.items() if cam.enabled}
    
    def update_camera(self, camera_id: str, **kwargs) -> bool:
        """Update camera profile properties"""
        if camera_id not in self.cameras:
            return False
        
        try:
            camera = self.cameras[camera_id]
            for key, value in kwargs.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            
            self.save_config()
            self.logger.info(f"Updated camera {camera_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update camera {camera_id}: {e}")
            return False
    
    def discover_network_cameras(self, ip_ranges: List[str] = None, timeout: int = 5) -> List[Dict]:
        """Discover cameras on the network"""
        if ip_ranges is None:
            ip_ranges = self._get_local_networks()
        
        self.logger.info(f"Scanning for cameras on networks: {ip_ranges}")
        discovered = []
        
        # Common RTSP ports and paths
        common_ports = [554, 8554, 1935]
        common_paths = [
            '/stream1', '/stream', '/live', '/ch01/0', '/cam/realmonitor',
            '/h264Preview_01_main', '/video1', '/media', '/onvif1'
        ]
        
        # Scan each IP range
        for ip_range in ip_ranges:
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                for ip in network.hosts():
                    devices = self._scan_ip_for_cameras(str(ip), common_ports, common_paths, timeout)
                    discovered.extend(devices)
            except Exception as e:
                self.logger.error(f"Error scanning {ip_range}: {e}")
        
        self.discovered_devices = discovered
        self.logger.info(f"Discovered {len(discovered)} potential camera devices")
        return discovered
    
    def _get_local_networks(self) -> List[str]:
        """Get local network ranges"""
        networks = []
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        if 'addr' in addr_info and 'netmask' in addr_info:
                            ip = addr_info['addr']
                            netmask = addr_info['netmask']
                            if not ip.startswith('127.'):
                                networks.append(f"{ip}/{netmask}")
        except ImportError:
            # Fallback to common private networks
            networks = ['192.168.1.0/24', '192.168.0.0/24', '10.0.0.0/24']
        
        return networks
    
    def _scan_ip_for_cameras(self, ip: str, ports: List[int], paths: List[str], timeout: int) -> List[Dict]:
        """Scan a specific IP for camera services"""
        devices = []
        
        for port in ports:
            if self._is_port_open(ip, port, timeout):
                # Found open port, test for RTSP
                for path in paths:
                    rtsp_url = f"rtsp://{ip}:{port}{path}"
                    if self._test_rtsp_stream(rtsp_url, timeout):
                        device = {
                            'ip': ip,
                            'port': port,
                            'rtsp_url': rtsp_url,
                            'type': 'RTSP Camera',
                            'discovered_time': datetime.now().isoformat(),
                            'path': path
                        }
                        devices.append(device)
                        break  # Found working stream, move to next port
        
        return devices
    
    def _is_port_open(self, ip: str, port: int, timeout: int) -> bool:
        """Check if a port is open on the given IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _test_rtsp_stream(self, rtsp_url: str, timeout: int) -> bool:
        """Test if RTSP stream is accessible"""
        try:
            import cv2
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_TIMEOUT, timeout * 1000)  # OpenCV timeout in milliseconds
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret and frame is not None
            return False
        except:
            return False
    
    def create_profile_from_discovery(self, discovered_device: Dict, name: str, camera_id: str = None) -> CameraProfile:
        """Create a camera profile from discovered device"""
        if camera_id is None:
            camera_id = f"cam_{discovered_device['ip'].replace('.', '_')}"
        
        profile = CameraProfile(
            camera_id=camera_id,
            name=name,
            rtsp_url=discovered_device['rtsp_url'],
            location=f"IP: {discovered_device['ip']}"
        )
        
        return profile
    
    def test_camera_connection(self, profile: CameraProfile) -> Tuple[bool, str]:
        """Test camera connection"""
        try:
            import cv2
            
            # Build URL with auth if provided
            url = profile.rtsp_url
            if profile.username and profile.password:
                # Insert credentials into URL
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                netloc = f"{profile.username}:{profile.password}@{parsed.netloc}"
                url = urlunparse((parsed.scheme, netloc, parsed.path, 
                                parsed.params, parsed.query, parsed.fragment))
            
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_TIMEOUT, 10000)  # 10 second timeout
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    return True, f"Connection successful - Resolution: {width}x{height}"
                else:
                    return False, "Connected but failed to read frame"
            else:
                return False, "Failed to open stream"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def get_discovery_results(self) -> List[Dict]:
        """Get the last discovery results"""
        return self.discovered_devices.copy()
    
    def export_config(self, export_path: str = None) -> str:
        """Export configuration to file"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"camera_config_export_{timestamp}.yaml"
        
        try:
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'camera_count': len(self.cameras),
                    'system': 'Sentinel Fire Detection'
                },
                'cameras': [asdict(camera) for camera in self.cameras.values()]
            }
            
            with open(export_path, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Exported configuration to {export_path}")
            return export_path
        except Exception as e:
            self.logger.error(f"Failed to export config: {e}")
            raise
    
    def import_config(self, import_path: str, merge: bool = False) -> bool:
        """Import configuration from file"""
        try:
            with open(import_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not merge:
                self.cameras.clear()
            
            imported_count = 0
            for cam_data in data.get('cameras', []):
                try:
                    profile = CameraProfile(**cam_data)
                    self.cameras[profile.camera_id] = profile
                    imported_count += 1
                except Exception as e:
                    self.logger.warning(f"Skipped invalid camera config: {e}")
            
            self.save_config()
            self.logger.info(f"Imported {imported_count} camera configurations")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import config: {e}")
            return False

class CameraWizard:
    """Interactive camera setup wizard"""
    
    def __init__(self, config_manager: CameraConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def auto_discover_and_setup(self) -> List[CameraProfile]:
        """Automatically discover and set up cameras"""
        self.logger.info("Starting automatic camera discovery...")
        
        # Discover cameras
        discovered = self.config_manager.discover_network_cameras()
        
        profiles = []
        for i, device in enumerate(discovered):
            # Create basic profile
            camera_id = f"auto_cam_{i+1}"
            name = f"Camera {device['ip']}:{device['port']}"
            
            profile = self.config_manager.create_profile_from_discovery(
                device, name, camera_id
            )
            
            # Test connection
            success, message = self.config_manager.test_camera_connection(profile)
            if success:
                self.config_manager.add_camera(profile)
                profiles.append(profile)
                self.logger.info(f"Auto-configured camera: {profile.name}")
            else:
                self.logger.warning(f"Skipped {profile.name}: {message}")
        
        return profiles
    
    def guided_setup(self, rtsp_url: str, name: str) -> Optional[CameraProfile]:
        """Guided setup for a single camera"""
        camera_id = name.lower().replace(' ', '_').replace('-', '_')
        
        profile = CameraProfile(
            camera_id=camera_id,
            name=name,
            rtsp_url=rtsp_url
        )
        
        # Test basic connection
        success, message = self.config_manager.test_camera_connection(profile)
        if not success:
            self.logger.error(f"Camera connection failed: {message}")
            return None
        
        # Add to configuration
        if self.config_manager.add_camera(profile):
            self.logger.info(f"Successfully configured camera: {name}")
            return profile
        
        return None

if __name__ == "__main__":
    # Test camera configuration system
    logging.basicConfig(level=logging.INFO)
    
    # Create config manager
    config_manager = CameraConfigManager("test_cameras.yaml")
    
    # Test discovery
    print("Discovering cameras...")
    discovered = config_manager.discover_network_cameras(['192.168.1.0/24'])
    print(f"Found {len(discovered)} devices")
    
    # Test wizard
    wizard = CameraWizard(config_manager)
    profiles = wizard.auto_discover_and_setup()
    print(f"Auto-configured {len(profiles)} cameras")