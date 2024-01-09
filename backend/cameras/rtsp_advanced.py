"""
Advanced RTSP camera integration with brand-specific optimizations
Supports Hikvision, Dahua, Axis, and generic ONVIF cameras
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET

@dataclass
class CameraProfile:
    """Camera-specific configuration profile"""
    brand: str
    model: str
    main_stream: str
    sub_stream: str
    snapshot_url: str
    ptz_support: bool
    audio_support: bool
    h265_support: bool
    onvif_port: int
    
class RTSPAdvanced:
    """Advanced RTSP camera manager with brand-specific optimizations"""
    
    # Camera profile database
    CAMERA_PROFILES = {
        'hikvision': {
            'default': CameraProfile(
                brand='Hikvision',
                model='Generic',
                main_stream='/Streaming/Channels/101',
                sub_stream='/Streaming/Channels/102',
                snapshot_url='/ISAPI/Streaming/channels/101/picture',
                ptz_support=True,
                audio_support=True,
                h265_support=True,
                onvif_port=80
            ),
            'DS-2CD2132F-I': CameraProfile(
                brand='Hikvision',
                model='DS-2CD2132F-I',
                main_stream='/h264/ch1/main/av_stream',
                sub_stream='/h264/ch1/sub/av_stream',
                snapshot_url='/ISAPI/Streaming/channels/101/picture',
                ptz_support=False,
                audio_support=True,
                h265_support=False,
                onvif_port=80
            )
        },
        'dahua': {
            'default': CameraProfile(
                brand='Dahua',
                model='Generic',
                main_stream='/cam/realmonitor?channel=1&subtype=0',
                sub_stream='/cam/realmonitor?channel=1&subtype=1',
                snapshot_url='/cgi-bin/snapshot.cgi',
                ptz_support=True,
                audio_support=True,
                h265_support=True,
                onvif_port=80
            ),
            'IPC-HDW5231R-Z': CameraProfile(
                brand='Dahua',
                model='IPC-HDW5231R-Z',
                main_stream='/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif',
                sub_stream='/cam/realmonitor?channel=1&subtype=1&unicast=true&proto=Onvif',
                snapshot_url='/cgi-bin/snapshot.cgi?channel=1',
                ptz_support=True,
                audio_support=True,
                h265_support=True,
                onvif_port=80
            )
        },
        'axis': {
            'default': CameraProfile(
                brand='Axis',
                model='Generic',
                main_stream='/axis-media/media.amp',
                sub_stream='/axis-media/media.amp?resolution=640x480',
                snapshot_url='/axis-cgi/jpg/image.cgi',
                ptz_support=True,
                audio_support=True,
                h265_support=True,
                onvif_port=80
            ),
            'M3065-V': CameraProfile(
                brand='Axis',
                model='M3065-V',
                main_stream='/axis-media/media.amp?videocodec=h264',
                sub_stream='/axis-media/media.amp?videocodec=h264&resolution=640x360',
                snapshot_url='/axis-cgi/jpg/image.cgi?resolution=1920x1080',
                ptz_support=False,
                audio_support=True,
                h265_support=False,
                onvif_port=80
            )
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cameras: Dict[str, 'CameraConnection'] = {}
        self.discovery_results: List[Dict] = []
        
    def detect_camera_brand(self, ip: str, username: str, password: str) -> Tuple[str, str]:
        """Detect camera brand and model via HTTP headers and responses"""
        brands_endpoints = [
            ('hikvision', f'http://{ip}/ISAPI/System/deviceInfo'),
            ('dahua', f'http://{ip}/cgi-bin/magicBox.cgi?action=getDeviceType'),
            ('axis', f'http://{ip}/axis-cgi/basicdeviceinfo.cgi')
        ]
        
        for brand, endpoint in brands_endpoints:
            try:
                response = requests.get(
                    endpoint,
                    auth=HTTPDigestAuth(username, password),
                    timeout=3
                )
                
                if response.status_code == 200:
                    # Parse response to get model
                    if brand == 'hikvision' and '<model>' in response.text:
                        model = response.text.split('<model>')[1].split('</model>')[0]
                        return brand, model
                    elif brand == 'dahua' and 'type=' in response.text:
                        model = response.text.split('type=')[1].split('\n')[0]
                        return brand, model
                    elif brand == 'axis' and 'ProdNbr' in response.text:
                        model = response.text.split('ProdNbr>')[1].split('<')[0]
                        return brand, model
                    
                    return brand, 'Generic'
                    
            except Exception as e:
                self.logger.debug(f"Failed to detect {brand}: {e}")
                
        return 'generic', 'Unknown'
    
    def get_camera_profile(self, brand: str, model: str) -> CameraProfile:
        """Get optimized profile for specific camera"""
        brand_profiles = self.CAMERA_PROFILES.get(brand.lower(), {})
        
        # Try specific model first
        for key in brand_profiles:
            if model and key in model:
                return brand_profiles[key]
        
        # Fall back to default for brand
        if 'default' in brand_profiles:
            return brand_profiles['default']
        
        # Generic profile
        return CameraProfile(
            brand='Generic',
            model='Unknown',
            main_stream='/stream1',
            sub_stream='/stream2',
            snapshot_url='/snapshot.jpg',
            ptz_support=False,
            audio_support=False,
            h265_support=False,
            onvif_port=8899
        )
    
    def optimize_stream_url(self, base_url: str, profile: CameraProfile, 
                           use_sub_stream: bool = False) -> str:
        """Build optimized RTSP URL based on camera profile"""
        parsed = urlparse(base_url)
        
        # Select appropriate stream path
        if use_sub_stream:
            path = profile.sub_stream
        else:
            path = profile.main_stream
        
        # Build complete URL
        if not parsed.path or parsed.path == '/':
            new_parsed = parsed._replace(path=path)
        else:
            # Keep existing path if specified
            new_parsed = parsed
        
        optimized_url = urlunparse(new_parsed)
        
        # Add H.265 parameters if supported
        if profile.h265_support and 'h265' not in optimized_url.lower():
            if '?' in optimized_url:
                optimized_url += '&codec=h265'
            else:
                optimized_url += '?codec=h265'
        
        return optimized_url
    
    def test_camera_connection(self, ip: str, username: str, password: str,
                              port: int = 554) -> Dict:
        """Comprehensive camera connection test"""
        results = {
            'ip': ip,
            'rtsp_main': False,
            'rtsp_sub': False,
            'snapshot': False,
            'onvif': False,
            'brand': 'unknown',
            'model': 'unknown',
            'streams': []
        }
        
        # Detect brand and model
        brand, model = self.detect_camera_brand(ip, username, password)
        results['brand'] = brand
        results['model'] = model
        
        # Get camera profile
        profile = self.get_camera_profile(brand, model)
        
        # Test main stream
        main_url = f"rtsp://{username}:{password}@{ip}:{port}{profile.main_stream}"
        if self.test_single_stream(main_url):
            results['rtsp_main'] = True
            results['streams'].append({
                'name': 'Main Stream',
                'url': main_url,
                'resolution': self.get_stream_resolution(main_url)
            })
        
        # Test sub stream
        sub_url = f"rtsp://{username}:{password}@{ip}:{port}{profile.sub_stream}"
        if self.test_single_stream(sub_url):
            results['rtsp_sub'] = True
            results['streams'].append({
                'name': 'Sub Stream',
                'url': sub_url,
                'resolution': self.get_stream_resolution(sub_url)
            })
        
        # Test snapshot
        snapshot_url = f"http://{username}:{password}@{ip}{profile.snapshot_url}"
        try:
            response = requests.get(snapshot_url, timeout=3)
            if response.status_code == 200:
                results['snapshot'] = True
        except:
            pass
        
        # Test ONVIF
        results['onvif'] = self.test_onvif(ip, username, password, profile.onvif_port)
        
        return results
    
    def test_single_stream(self, url: str) -> bool:
        """Test individual RTSP stream"""
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret
        except:
            pass
        return False
    
    def get_stream_resolution(self, url: str) -> Tuple[int, int]:
        """Get resolution of RTSP stream"""
        try:
            cap = cv2.VideoCapture(url)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            return (width, height)
        except:
            return (0, 0)
    
    def test_onvif(self, ip: str, username: str, password: str, port: int = 80) -> bool:
        """Test ONVIF compatibility"""
        try:
            # Simple ONVIF device management test
            url = f"http://{ip}:{port}/onvif/device_service"
            
            # ONVIF GetCapabilities SOAP request
            soap_request = """<?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
                <soap:Body>
                    <tds:GetCapabilities xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
                        <tds:Category>All</tds:Category>
                    </tds:GetCapabilities>
                </soap:Body>
            </soap:Envelope>"""
            
            response = requests.post(
                url,
                data=soap_request,
                auth=HTTPDigestAuth(username, password),
                headers={'Content-Type': 'application/soap+xml'},
                timeout=3
            )
            
            return response.status_code == 200
        except:
            return False
    
    def configure_camera_optimization(self, camera_id: str, profile: CameraProfile) -> None:
        """Apply camera-specific optimizations"""
        if camera_id not in self.cameras:
            return
        
        camera = self.cameras[camera_id]
        
        # Set buffer size based on brand
        if profile.brand.lower() == 'hikvision':
            camera.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        elif profile.brand.lower() == 'dahua':
            camera.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        
        # Set codec preferences
        if profile.h265_support:
            camera.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '5'))
        
        # Configure frame rate
        camera.cap.set(cv2.CAP_PROP_FPS, 15)
        
        self.logger.info(f"Applied optimizations for {profile.brand} {profile.model}")
    
    def perform_latency_test(self, url: str, duration: int = 10) -> Dict:
        """Test stream latency and performance"""
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            return {'error': 'Cannot open stream'}
        
        latencies = []
        frame_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            frame_start = time.time()
            ret, frame = cap.read()
            
            if ret:
                latency = (time.time() - frame_start) * 1000  # ms
                latencies.append(latency)
                frame_count += 1
        
        cap.release()
        
        if latencies:
            return {
                'avg_latency_ms': np.mean(latencies),
                'min_latency_ms': np.min(latencies),
                'max_latency_ms': np.max(latencies),
                'std_latency_ms': np.std(latencies),
                'frame_count': frame_count,
                'fps': frame_count / duration
            }
        
        return {'error': 'No frames captured'}

class CameraConnection:
    """Individual camera connection handler"""
    
    def __init__(self, camera_id: str, url: str, profile: CameraProfile):
        self.camera_id = camera_id
        self.url = url
        self.profile = profile
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        self.reconnect_count = 0
        self.last_frame_time = 0
        self.frame_count = 0
        self.error_count = 0
        
    def connect(self) -> bool:
        """Establish connection to camera"""
        try:
            self.cap = cv2.VideoCapture(self.url)
            
            # Set connection timeout
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            
            if self.cap.isOpened():
                self.is_connected = True
                self.last_frame_time = time.time()
                return True
                
        except Exception as e:
            logging.error(f"Failed to connect to {self.camera_id}: {e}")
        
        self.is_connected = False
        return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame from camera"""
        if not self.is_connected or not self.cap:
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if ret:
                self.last_frame_time = time.time()
                self.frame_count += 1
                return frame
            else:
                self.error_count += 1
                if self.error_count > 10:
                    self.reconnect()
                    
        except Exception as e:
            logging.error(f"Error reading frame from {self.camera_id}: {e}")
            self.error_count += 1
        
        return None
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to camera"""
        self.disconnect()
        self.reconnect_count += 1
        
        # Exponential backoff
        time.sleep(min(2 ** self.reconnect_count, 30))
        
        if self.connect():
            self.reconnect_count = 0
            return True
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from camera"""
        if self.cap:
            self.cap.release()
        self.is_connected = False
        self.cap = None
