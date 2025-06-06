"""
Sentinel Fire Detection Engine
Core YOLOv8-based fire and smoke detection system with RTSP integration
"""

import cv2
import torch
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import time
import logging
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import asyncio
import threading
from .rtsp_manager import RTSPManager, CameraConfig

@dataclass
class Detection:
    """Fire detection result"""
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_name: str
    timestamp: float

@dataclass
class DetectionResult:
    """Complete detection result for a frame"""
    frame_id: int
    timestamp: float
    detections: List[Detection]
    max_confidence: float
    alert_level: str  # P1, P2, P4, or None

class FireDetector:
    """Main fire detection engine using YOLOv8"""
    
    def __init__(self, config_path: str = "config/detection_config.yaml"):
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.frame_count = 0
        self.rtsp_manager = RTSPManager()
        self.detection_callback: Optional[Callable] = None
        self.is_running = False
        self.detection_thread = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load detection configuration"""
        import yaml
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration if file not found"""
        return {
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
    
    def _load_model(self) -> YOLO:
        """Load YOLOv8 model for fire detection"""
        try:
            # Try to load a fire-specific model first
            model_path = "models/fire_detection.pt"
            if Path(model_path).exists():
                self.logger.info(f"Loading fire detection model: {model_path}")
                return YOLO(model_path)
            else:
                # Fallback to general YOLOv8 model
                self.logger.info("Loading general YOLOv8n model (will need fire-specific training)")
                return YOLO('yolov8n.pt')  # This will download automatically
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def detect_fire(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect fire/smoke in a single frame
        
        Args:
            frame: BGR image array from OpenCV
            
        Returns:
            DetectionResult with detections and alert level
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Run YOLOv8 inference
        results = self.model(frame, verbose=False)
        
        # Process detections
        detections = []
        max_confidence = 0.0
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    
                    # Filter for fire-related classes (adjust based on your model)
                    if self._is_fire_related(class_name, confidence):
                        bbox = box.xyxy[0].cpu().numpy().astype(int)
                        
                        detection = Detection(
                            confidence=confidence,
                            bbox=tuple(bbox),
                            class_name=class_name,
                            timestamp=time.time()
                        )
                        detections.append(detection)
                        max_confidence = max(max_confidence, confidence)
        
        # Determine alert level
        alert_level = self._determine_alert_level(max_confidence)
        
        # Log detection time
        detection_time = time.time() - start_time
        if detection_time > self.config['system']['detection_latency_target']:
            self.logger.warning(f"Detection latency: {detection_time:.2f}s (target: {self.config['system']['detection_latency_target']}s)")
        
        return DetectionResult(
            frame_id=self.frame_count,
            timestamp=time.time(),
            detections=detections,
            max_confidence=max_confidence,
            alert_level=alert_level
        )
    
    def _is_fire_related(self, class_name: str, confidence: float) -> bool:
        """Check if detected class is fire-related"""
        # For general YOLOv8, we might detect fire as 'fire' or smoke-like objects
        # This will need adjustment based on the specific fire detection model
        fire_classes = ['fire', 'smoke', 'flame']
        
        # Minimum confidence threshold
        min_confidence = self.config['detection']['thresholds']['log_only']
        
        return (class_name.lower() in fire_classes or 
                'fire' in class_name.lower() or 
                'smoke' in class_name.lower()) and confidence >= min_confidence
    
    def _determine_alert_level(self, max_confidence: float) -> str:
        """Determine alert level based on confidence"""
        thresholds = self.config['detection']['thresholds']
        
        if max_confidence >= thresholds['immediate_alert']:
            return 'P1'
        elif max_confidence >= thresholds['review_queue']:
            return 'P2'
        elif max_confidence >= thresholds['log_only']:
            return 'P4'
        else:
            return 'None'
    
    def process_video_stream(self, video_source) -> None:
        """Process video stream (file or camera) for fire detection"""
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video source: {video_source}")
        
        self.logger.info(f"Started processing video stream: {video_source}")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    self.logger.info("End of video stream")
                    break
                
                # Detect fire in frame
                result = self.detect_fire(frame)
                
                # Handle detection result
                if result.alert_level != 'None':
                    self.logger.info(f"DETECTION: {result.alert_level} - Confidence: {result.max_confidence:.2f}")
                    # In full implementation, this would trigger alerts
                
                # Optional: Display frame with detections (for debugging)
                if self.config.get('debug', {}).get('show_video', False):
                    annotated_frame = self._annotate_frame(frame, result.detections)
                    cv2.imshow('Sentinel Fire Detection', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def _annotate_frame(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Annotate frame with detection boxes"""
        annotated = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            confidence = detection.confidence
            
            # Color based on confidence
            if confidence >= 0.95:
                color = (0, 0, 255)  # Red - immediate alert
            elif confidence >= 0.85:
                color = (0, 165, 255)  # Orange - review queue
            else:
                color = (0, 255, 255)  # Yellow - log only
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection.class_name}: {confidence:.2f}"
            cv2.putText(annotated, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
    
    def add_rtsp_camera(self, camera_id: str, rtsp_url: str, username: str = None, password: str = None, fps: int = 15) -> bool:
        """Add an RTSP camera for monitoring"""
        config = CameraConfig(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            username=username,
            password=password,
            fps=fps
        )
        return self.rtsp_manager.add_camera(config)
    
    def remove_rtsp_camera(self, camera_id: str) -> bool:
        """Remove an RTSP camera"""
        return self.rtsp_manager.remove_camera(camera_id)
    
    def start_monitoring(self) -> int:
        """Start monitoring all RTSP cameras"""
        if self.is_running:
            return 0
            
        started_cameras = self.rtsp_manager.start_all()
        if started_cameras > 0:
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.detection_thread.start()
            self.logger.info(f"Started monitoring {started_cameras} cameras")
        
        return started_cameras
    
    def stop_monitoring(self):
        """Stop monitoring all cameras"""
        self.is_running = False
        self.rtsp_manager.stop_all()
        if self.detection_thread:
            self.detection_thread.join(timeout=5)
        self.logger.info("Stopped camera monitoring")
    
    def set_detection_callback(self, callback: Callable[[str, DetectionResult], None]):
        """Set callback function for detection results"""
        self.detection_callback = callback
    
    def _monitoring_loop(self):
        """Main monitoring loop for all cameras"""
        while self.is_running:
            try:
                # Get frames from all cameras
                frames = self.rtsp_manager.get_frames()
                
                # Process each frame for fire detection
                for camera_id, frame in frames.items():
                    result = self.detect_fire(frame)
                    
                    # Call detection callback if set
                    if self.detection_callback and result.alert_level != 'None':
                        self.detection_callback(camera_id, result)
                    
                    # Log significant detections
                    if result.alert_level in ['P1', 'P2']:
                        self.logger.warning(f"Camera {camera_id} - {result.alert_level}: {result.max_confidence:.2f}")
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(1)
    
    def get_camera_status(self) -> Dict:
        """Get status of all cameras"""
        return self.rtsp_manager.get_all_status()
    
    def discover_cameras(self, timeout: int = 5) -> List[Dict]:
        """Discover ONVIF cameras on the network"""
        return self.rtsp_manager.discover_cameras(timeout)
    
    def test_rtsp_connection(self, rtsp_url: str, username: str = None, password: str = None) -> Tuple[bool, str]:
        """Test RTSP connection before adding camera"""
        return self.rtsp_manager.test_rtsp_url(rtsp_url, username, password)

if __name__ == "__main__":
    # Test the detector
    detector = FireDetector()
    
    # Process a test video file (you would provide this)
    test_video = "test_data/fire_test.mp4"
    if Path(test_video).exists():
        detector.process_video_stream(test_video)
    else:
        print(f"Test video not found: {test_video}")
        print("Place a test video file in test_data/ to test the detector")