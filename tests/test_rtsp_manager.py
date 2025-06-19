"""
Tests for RTSP Camera Manager
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from detection.rtsp_manager import RTSPManager, CameraConfig, CameraStatus, RTSPCamera


class TestCameraConfig:
    """Test CameraConfig dataclass"""
    
    def test_camera_config_creation(self):
        """Test creating camera configuration"""
        config = CameraConfig(
            camera_id="test_cam",
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            username="admin",
            password="password"
        )
        
        assert config.camera_id == "test_cam"
        assert config.rtsp_url == "rtsp://192.168.1.100:554/stream1"
        assert config.username == "admin"
        assert config.password == "password"
        assert config.fps == 15  # Default
        assert config.enabled == True  # Default
    
    def test_camera_config_defaults(self):
        """Test default values in camera configuration"""
        config = CameraConfig("test", "rtsp://test")
        
        assert config.fps == 15
        assert config.resolution == (640, 480)
        assert config.timeout == 10
        assert config.retry_interval == 30
        assert config.enabled == True


class TestRTSPCamera:
    """Test RTSPCamera class"""
    
    @pytest.fixture
    def camera_config(self):
        """Create test camera configuration"""
        return CameraConfig(
            camera_id="test_cam",
            rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
            fps=10,
            timeout=5
        )
    
    @pytest.fixture
    def rtsp_camera(self, camera_config):
        """Create RTSPCamera instance"""
        return RTSPCamera(camera_config)
    
    def test_rtsp_camera_initialization(self, rtsp_camera):
        """Test RTSPCamera initializes correctly"""
        assert rtsp_camera.config.camera_id == "test_cam"
        assert rtsp_camera.is_running == False
        assert rtsp_camera.current_frame is None
        assert rtsp_camera.status.camera_id == "test_cam"
        assert rtsp_camera.status.connected == False
    
    def test_camera_status_structure(self, rtsp_camera):
        """Test camera status has correct structure"""
        status = rtsp_camera.status
        
        assert hasattr(status, 'camera_id')
        assert hasattr(status, 'connected')
        assert hasattr(status, 'last_frame_time')
        assert hasattr(status, 'frame_count')
        assert hasattr(status, 'error_count')
        assert hasattr(status, 'last_error')
        assert hasattr(status, 'resolution')
        assert hasattr(status, 'actual_fps')
    
    def test_build_rtsp_url(self, rtsp_camera):
        """Test RTSP URL building with authentication"""
        # Test URL with existing credentials
        url = rtsp_camera._build_rtsp_url()
        assert "test:test@" in url
        
        # Test URL building with config credentials
        rtsp_camera.config.username = "admin"
        rtsp_camera.config.password = "secret"
        rtsp_camera.config.rtsp_url = "rtsp://192.168.1.100:554/stream1"
        
        url = rtsp_camera._build_rtsp_url()
        assert "admin:secret@" in url
    
    def test_sanitize_url(self, rtsp_camera):
        """Test URL sanitization for logging"""
        test_url = "rtsp://admin:secret@192.168.1.100:554/stream1"
        sanitized = rtsp_camera._sanitize_url(test_url)
        
        assert "admin" not in sanitized
        assert "secret" not in sanitized
        assert "***:***@" in sanitized
    
    @patch('cv2.VideoCapture')
    def test_camera_start_stop(self, mock_video_capture, rtsp_camera):
        """Test camera start and stop functionality"""
        # Mock successful connection
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, Mock())
        mock_video_capture.return_value = mock_cap
        
        # Test start
        success = rtsp_camera.start()
        assert isinstance(success, bool)
        
        # Test stop
        rtsp_camera.stop()
        assert rtsp_camera.is_running == False


class TestRTSPManager:
    """Test RTSPManager class"""
    
    @pytest.fixture
    def rtsp_manager(self):
        """Create RTSPManager instance"""
        return RTSPManager()
    
    @pytest.fixture
    def test_camera_config(self):
        """Create test camera configuration"""
        return CameraConfig(
            camera_id="test_cam_1",
            rtsp_url="rtsp://test:test@192.168.1.100:554/stream1"
        )
    
    def test_rtsp_manager_initialization(self, rtsp_manager):
        """Test RTSPManager initializes correctly"""
        assert rtsp_manager is not None
        assert rtsp_manager.cameras == {}
        assert rtsp_manager.status_callback is None
    
    def test_add_camera(self, rtsp_manager, test_camera_config):
        """Test adding camera to manager"""
        success = rtsp_manager.add_camera(test_camera_config)
        assert success == True
        assert "test_cam_1" in rtsp_manager.cameras
        
        camera = rtsp_manager.cameras["test_cam_1"]
        assert camera.config.camera_id == "test_cam_1"
    
    def test_remove_camera(self, rtsp_manager, test_camera_config):
        """Test removing camera from manager"""
        # Add camera first
        rtsp_manager.add_camera(test_camera_config)
        assert "test_cam_1" in rtsp_manager.cameras
        
        # Remove camera
        success = rtsp_manager.remove_camera("test_cam_1")
        assert success == True
        assert "test_cam_1" not in rtsp_manager.cameras
        
        # Try removing non-existent camera
        success = rtsp_manager.remove_camera("non_existent")
        assert success == False
    
    def test_get_camera_status(self, rtsp_manager, test_camera_config):
        """Test getting camera status"""
        # Add camera
        rtsp_manager.add_camera(test_camera_config)
        
        # Get status
        status = rtsp_manager.get_camera_status("test_cam_1")
        assert status is not None
        assert isinstance(status, CameraStatus)
        assert status.camera_id == "test_cam_1"
        
        # Test non-existent camera
        status = rtsp_manager.get_camera_status("non_existent")
        assert status is None
    
    def test_get_all_status(self, rtsp_manager):
        """Test getting all camera statuses"""
        # Add multiple cameras
        configs = [
            CameraConfig("cam1", "rtsp://test1"),
            CameraConfig("cam2", "rtsp://test2"),
            CameraConfig("cam3", "rtsp://test3")
        ]
        
        for config in configs:
            rtsp_manager.add_camera(config)
        
        # Get all statuses
        all_status = rtsp_manager.get_all_status()
        assert len(all_status) == 3
        assert "cam1" in all_status
        assert "cam2" in all_status
        assert "cam3" in all_status
        
        for camera_id, status in all_status.items():
            assert isinstance(status, CameraStatus)
            assert status.camera_id == camera_id
    
    @patch('cv2.VideoCapture')
    def test_start_all_cameras(self, mock_video_capture, rtsp_manager):
        """Test starting all cameras"""
        # Mock successful connections
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, Mock())
        mock_video_capture.return_value = mock_cap
        
        # Add test cameras
        configs = [
            CameraConfig("cam1", "rtsp://test1"),
            CameraConfig("cam2", "rtsp://test2")
        ]
        
        for config in configs:
            rtsp_manager.add_camera(config)
        
        # Start all cameras
        started_count = rtsp_manager.start_all()
        assert isinstance(started_count, int)
        assert started_count >= 0
        
        # Stop all cameras
        rtsp_manager.stop_all()
    
    def test_get_frames(self, rtsp_manager, test_camera_config):
        """Test getting frames from cameras"""
        # Add camera
        rtsp_manager.add_camera(test_camera_config)
        
        # Get frames (will be empty since camera not actually connected)
        frames = rtsp_manager.get_frames()
        assert isinstance(frames, dict)
        # Should be empty since no real camera connection
        assert len(frames) == 0
    
    def test_test_rtsp_url(self, rtsp_manager):
        """Test RTSP URL testing functionality"""
        # Test with invalid URL
        success, message = rtsp_manager.test_rtsp_url("invalid_url")
        assert success == False
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Test with properly formatted but non-existent URL
        success, message = rtsp_manager.test_rtsp_url("rtsp://nonexistent:554/stream")
        assert success == False
        assert isinstance(message, str)


class TestONVIFDiscovery:
    """Test ONVIF discovery functionality"""
    
    def test_discover_cameras_structure(self):
        """Test ONVIF discovery returns correct structure"""
        from detection.rtsp_manager import ONVIFDiscovery
        
        # Discovery might not find cameras in test environment
        discovered = ONVIFDiscovery.discover_cameras(timeout=1)  # Short timeout
        
        assert isinstance(discovered, list)
        
        # If cameras found, check structure
        for camera in discovered:
            assert isinstance(camera, dict)
            if camera:  # If not empty
                assert 'ip' in camera
                assert 'type' in camera
                assert 'rtsp_url' in camera
    
    def test_parse_probe_response(self):
        """Test parsing ONVIF probe responses"""
        from detection.rtsp_manager import ONVIFDiscovery
        
        # Test with valid response
        valid_response = """<?xml version="1.0" encoding="UTF-8"?>
        <NetworkVideoTransmitter>test</NetworkVideoTransmitter>"""
        
        result = ONVIFDiscovery._parse_probe_response(valid_response, "192.168.1.100")
        
        if result:  # Might return None in some cases
            assert isinstance(result, dict)
            assert 'ip' in result
            assert result['ip'] == "192.168.1.100"
        
        # Test with invalid response
        invalid_response = "invalid xml"
        result = ONVIFDiscovery._parse_probe_response(invalid_response, "192.168.1.100")
        assert result is None


class TestIntegration:
    """Integration tests for RTSP system"""
    
    def test_rtsp_manager_lifecycle(self):
        """Test complete RTSP manager lifecycle"""
        manager = RTSPManager()
        
        # Add multiple cameras
        configs = [
            CameraConfig("cam1", "rtsp://test1:554/stream1"),
            CameraConfig("cam2", "rtsp://test2:554/stream2"),
            CameraConfig("cam3", "rtsp://test3:554/stream3")
        ]
        
        # Add cameras
        for config in configs:
            success = manager.add_camera(config)
            assert success == True
        
        # Verify all added
        assert len(manager.cameras) == 3
        
        # Get status of all
        all_status = manager.get_all_status()
        assert len(all_status) == 3
        
        # Test discovery (might not find cameras in test environment)
        discovered = manager.discover_cameras(timeout=1)
        assert isinstance(discovered, list)
        
        # Remove all cameras
        for config in configs:
            success = manager.remove_camera(config.camera_id)
            assert success == True
        
        # Verify all removed
        assert len(manager.cameras) == 0
    
    def test_camera_error_handling(self):
        """Test error handling in camera operations"""
        manager = RTSPManager()
        
        # Test adding invalid camera
        invalid_config = CameraConfig("invalid", "not_a_url")
        success = manager.add_camera(invalid_config)
        # Should still add to manager even if URL is invalid
        assert success == True
        
        # Test starting invalid camera (will fail gracefully)
        started = manager.start_camera("invalid")
        assert isinstance(started, bool)
        
        # Test stopping non-existent camera
        manager.stop_camera("non_existent")  # Should not raise exception


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])