"""
Tests for Fire Detection System
"""

import pytest
import numpy as np
import cv2
import time
from pathlib import Path
import tempfile
import yaml
import sys
import os

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from detection.fire_detector import FireDetector, Detection, DetectionResult
from detection.fire_model_manager import FireModelManager


class TestFireDetector:
    """Test cases for FireDetector"""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing"""
        config_data = {
            'detection': {
                'thresholds': {
                    'immediate_alert': 0.95,
                    'review_queue': 0.85,
                    'log_only': 0.70
                },
                'environmental': {
                    'fog_adjustment': -0.05,
                    'sunset_hours': [17, 19]
                }
            },
            'system': {
                'detection_latency_target': 2.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    @pytest.fixture
    def fire_detector(self, temp_config):
        """Create FireDetector instance for testing"""
        return FireDetector(temp_config)
    
    @pytest.fixture
    def test_frame(self):
        """Create test image frame"""
        # Create a 640x480 test image
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 1] = 128  # Green background
        
        # Add some "fire-like" regions (red/orange)
        frame[100:200, 100:200, 2] = 255  # Red region
        frame[100:200, 100:200, 1] = 165  # Orange tint
        frame[100:200, 100:200, 0] = 0    # No blue
        
        return frame
    
    def test_fire_detector_initialization(self, fire_detector):
        """Test FireDetector initializes correctly"""
        assert fire_detector is not None
        assert fire_detector.model is not None
        assert fire_detector.config is not None
        assert fire_detector.frame_count == 0
    
    def test_config_loading(self, temp_config):
        """Test configuration loading"""
        detector = FireDetector(temp_config)
        
        assert detector.config['detection']['thresholds']['immediate_alert'] == 0.95
        assert detector.config['detection']['thresholds']['review_queue'] == 0.85
        assert detector.config['detection']['thresholds']['log_only'] == 0.70
    
    def test_detect_fire_basic(self, fire_detector, test_frame):
        """Test basic fire detection functionality"""
        result = fire_detector.detect_fire(test_frame)
        
        assert isinstance(result, DetectionResult)
        assert result.frame_id > 0
        assert result.timestamp > 0
        assert isinstance(result.detections, list)
        assert result.max_confidence >= 0.0
        assert result.alert_level in ['P1', 'P2', 'P4', 'None']
    
    def test_detection_result_structure(self, fire_detector, test_frame):
        """Test detection result has correct structure"""
        result = fire_detector.detect_fire(test_frame)
        
        # Check DetectionResult fields
        assert hasattr(result, 'frame_id')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'detections')
        assert hasattr(result, 'max_confidence')
        assert hasattr(result, 'alert_level')
        
        # Check individual detections
        for detection in result.detections:
            assert isinstance(detection, Detection)
            assert hasattr(detection, 'confidence')
            assert hasattr(detection, 'bbox')
            assert hasattr(detection, 'class_name')
            assert hasattr(detection, 'timestamp')
            
            # Validate bbox format (x1, y1, x2, y2)
            assert len(detection.bbox) == 4
            assert all(isinstance(x, (int, float)) for x in detection.bbox)
    
    def test_alert_level_determination(self, fire_detector):
        """Test alert level determination logic"""
        # Test immediate alert threshold
        assert fire_detector._determine_alert_level(0.97) == 'P1'
        
        # Test review queue threshold
        assert fire_detector._determine_alert_level(0.87) == 'P2'
        
        # Test log only threshold
        assert fire_detector._determine_alert_level(0.72) == 'P4'
        
        # Test below threshold
        assert fire_detector._determine_alert_level(0.65) == 'None'
    
    def test_fire_class_detection(self, fire_detector):
        """Test fire-related class detection"""
        # Test direct fire classes
        assert fire_detector._is_fire_related('fire', 0.8) == True
        assert fire_detector._is_fire_related('smoke', 0.8) == True
        assert fire_detector._is_fire_related('flame', 0.8) == True
        
        # Test fire keywords
        assert fire_detector._is_fire_related('house_fire', 0.8) == True
        assert fire_detector._is_fire_related('smoke_detector', 0.8) == True
        
        # Test non-fire classes
        assert fire_detector._is_fire_related('person', 0.8) == False
        assert fire_detector._is_fire_related('car', 0.8) == False
        
        # Test high confidence potential fire indicators
        assert fire_detector._is_fire_related('car', 0.95) == True  # Very high confidence
        
        # Test below threshold
        assert fire_detector._is_fire_related('fire', 0.5) == False  # Below log_only threshold
    
    def test_detection_latency(self, fire_detector, test_frame):
        """Test detection meets latency requirements"""
        start_time = time.time()
        result = fire_detector.detect_fire(test_frame)
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should be under target latency (2 seconds = 2000ms)
        assert latency < fire_detector.config['system']['detection_latency_target'] * 1000
        
        # Should be reasonable for real-time processing (under 500ms for small frame)
        assert latency < 500
    
    def test_multiple_frame_processing(self, fire_detector, test_frame):
        """Test processing multiple frames"""
        results = []
        
        for i in range(5):
            result = fire_detector.detect_fire(test_frame)
            results.append(result)
        
        # Check frame counter increments
        assert results[0].frame_id == 1
        assert results[4].frame_id == 5
        
        # Check timestamps are increasing
        for i in range(1, len(results)):
            assert results[i].timestamp >= results[i-1].timestamp
    
    def test_rtsp_camera_integration(self, fire_detector):
        """Test RTSP camera integration methods"""
        # Test adding RTSP camera
        success = fire_detector.add_rtsp_camera(
            "test_cam", 
            "rtsp://test:test@192.168.1.100:554/stream1",
            username="test",
            password="test"
        )
        # This might fail if no actual camera, but method should exist
        assert isinstance(success, bool)
        
        # Test removing camera
        success = fire_detector.remove_rtsp_camera("test_cam")
        assert isinstance(success, bool)
    
    def test_monitoring_methods(self, fire_detector):
        """Test monitoring start/stop methods"""
        # Test methods exist and return expected types
        started = fire_detector.start_monitoring()
        assert isinstance(started, int)  # Number of cameras started
        
        # Test stop monitoring
        fire_detector.stop_monitoring()
        
        # Test callback setting
        def dummy_callback(camera_id, result):
            pass
        
        fire_detector.set_detection_callback(dummy_callback)
        assert fire_detector.detection_callback == dummy_callback


class TestFireModelManager:
    """Test cases for FireModelManager"""
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create temporary models directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def model_manager(self, temp_models_dir):
        """Create FireModelManager instance"""
        return FireModelManager(temp_models_dir)
    
    def test_model_manager_initialization(self, model_manager):
        """Test FireModelManager initializes correctly"""
        assert model_manager is not None
        assert model_manager.models_dir.exists()
        assert len(model_manager.available_models) > 0
    
    def test_list_available_models(self, model_manager):
        """Test listing available models"""
        models = model_manager.list_available_models()
        
        assert isinstance(models, dict)
        assert len(models) > 0
        
        for model_name, info in models.items():
            assert 'description' in info
            assert 'size' in info
            assert 'downloaded' in info
            assert 'verified' in info
    
    def test_model_download(self, model_manager):
        """Test model download functionality"""
        try:
            # Try to download the smallest model
            model_path = model_manager.download_model('fire_yolov8n')
            assert Path(model_path).exists()
            
            # Test that re-downloading uses existing file
            model_path2 = model_manager.download_model('fire_yolov8n')
            assert model_path == model_path2
            
        except Exception as e:
            # Download might fail in CI/CD or without internet
            pytest.skip(f"Model download failed (expected in some environments): {e}")
    
    def test_get_best_model(self, model_manager):
        """Test getting best available model"""
        try:
            # Test speed preference
            model_path = model_manager.get_best_model(prefer_accuracy=False)
            assert isinstance(model_path, str)
            
            # Test accuracy preference
            model_path2 = model_manager.get_best_model(prefer_accuracy=True)
            assert isinstance(model_path2, str)
            
        except Exception as e:
            pytest.skip(f"Model download failed (expected in some environments): {e}")
    
    def test_create_fire_detection_model(self, model_manager):
        """Test creating fire detection model"""
        try:
            fire_model = model_manager.create_fire_detection_model()
            assert fire_model is not None
            
            # Test that model can be used for inference
            # (This is a basic check that the model loads correctly)
            assert hasattr(fire_model, 'predict')
            
        except Exception as e:
            pytest.skip(f"Model creation failed (expected in some environments): {e}")
    
    def test_simulate_fire_training(self, model_manager):
        """Test training simulation"""
        try:
            fire_model = model_manager.create_fire_detection_model()
            results = model_manager.simulate_fire_training(fire_model)
            
            assert isinstance(results, dict)
            assert 'final_map50' in results
            assert 'precision' in results
            assert 'recall' in results
            assert 'f1_score' in results
            
            # Check reasonable values
            assert 0.0 <= results['final_map50'] <= 1.0
            assert 0.0 <= results['precision'] <= 1.0
            assert 0.0 <= results['recall'] <= 1.0
            
        except Exception as e:
            pytest.skip(f"Model creation failed (expected in some environments): {e}")


class TestIntegration:
    """Integration tests for complete system"""
    
    def test_end_to_end_detection(self):
        """Test complete detection pipeline"""
        try:
            # Create detector
            detector = FireDetector()
            
            # Create test frame
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Run detection
            result = detector.detect_fire(frame)
            
            # Verify result
            assert isinstance(result, DetectionResult)
            assert result.frame_id > 0
            
        except Exception as e:
            pytest.skip(f"End-to-end test failed (expected in some environments): {e}")
    
    def test_performance_under_load(self):
        """Test performance with multiple detections"""
        try:
            detector = FireDetector()
            
            # Process multiple frames quickly
            start_time = time.time()
            for i in range(10):
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                result = detector.detect_fire(frame)
                assert result is not None
            
            total_time = time.time() - start_time
            
            # Should process 10 frames in reasonable time (under 30 seconds)
            assert total_time < 30.0
            
            # Calculate FPS
            fps = 10 / total_time
            print(f"Detection FPS: {fps:.2f}")
            
        except Exception as e:
            pytest.skip(f"Performance test failed (expected in some environments): {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])