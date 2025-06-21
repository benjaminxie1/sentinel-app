"""
Video Stream Simulator
Creates simulated RTSP-like streams from video files for testing
"""

import cv2
import numpy as np
import time
import threading
from pathlib import Path
from typing import List, Optional, Callable
import logging
from queue import Queue

class CameraSimulator:
    """Simulates a single camera feed"""
    
    def __init__(self, camera_id: str, video_source: str, fps: int = 30):
        self.camera_id = camera_id
        self.video_source = video_source
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.is_running = False
        self.current_frame = None
        self.frame_count = 0
        self.logger = logging.getLogger(f"Camera-{camera_id}")
        
    def start(self):
        """Start the camera simulation"""
        self.is_running = True
        self.thread = threading.Thread(target=self._run_simulation, daemon=True)
        self.thread.start()
        # Camera started
    
    def stop(self):
        """Stop the camera simulation"""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)
        # Camera stopped
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current frame"""
        return self.current_frame
    
    def _run_simulation(self):
        """Run the camera simulation loop"""
        if Path(self.video_source).exists():
            self._simulate_from_video()
        else:
            self._simulate_generated_frames()
    
    def _simulate_from_video(self):
        """Simulate camera from video file"""
        cap = cv2.VideoCapture(self.video_source)
        
        if not cap.isOpened():
            self.logger.error(f"Could not open video: {self.video_source}")
            return
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                # Loop the video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            self.current_frame = frame
            self.frame_count += 1
            time.sleep(self.frame_interval)
        
        cap.release()
    
    def _simulate_generated_frames(self):
        """Generate synthetic frames for testing"""
        width, height = 640, 480
        
        while self.is_running:
            # Create a synthetic frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add some pattern
            frame[:, :, 0] = (self.frame_count % 255)  # Blue channel
            frame[:, :, 1] = 50  # Green channel
            frame[:, :, 2] = 100  # Red channel
            
            # Add camera ID text
            cv2.putText(frame, f"Camera {self.camera_id}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(frame, timestamp, (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # No fake fire simulation in production
            
            self.current_frame = frame
            self.frame_count += 1
            time.sleep(self.frame_interval)
    

class MultiCameraSimulator:
    """Manages multiple simulated cameras"""
    
    def __init__(self):
        self.cameras: List[CameraSimulator] = []
        self.logger = logging.getLogger(__name__)
    
    def add_camera(self, camera_id: str, video_source: str, fps: int = 30):
        """Add a camera to the simulation"""
        camera = CameraSimulator(camera_id, video_source, fps)
        self.cameras.append(camera)
        # Camera added
        return camera
    
    def start_all(self):
        """Start all camera simulations"""
        for camera in self.cameras:
            camera.start()
        # Started camera simulations
    
    def stop_all(self):
        """Stop all camera simulations"""
        for camera in self.cameras:
            camera.stop()
        # Stopped all camera simulations
    
    def get_camera_frames(self) -> dict:
        """Get current frames from all cameras"""
        frames = {}
        for camera in self.cameras:
            frame = camera.get_frame()
            if frame is not None:
                frames[camera.camera_id] = frame
        return frames
    
    def create_default_setup(self) -> None:
        """Create a default multi-camera setup for testing"""
        # Create test data directory
        test_dir = Path("test_data")
        test_dir.mkdir(exist_ok=True)
        
        # No default cameras - start with clean slate
        # Cameras should be added via configuration or discovery
        
        # Camera setup initialized

class StreamProcessor:
    """Processes multiple camera streams with detection"""
    
    def __init__(self, detection_callback: Optional[Callable] = None):
        self.simulator = MultiCameraSimulator()
        self.detection_callback = detection_callback
        self.is_processing = False
        self.process_thread = None
        self.logger = logging.getLogger(__name__)
        
    def setup_test_cameras(self):
        """Setup test camera configuration"""
        self.simulator.create_default_setup()
    
    def start_processing(self):
        """Start processing camera streams"""
        self.simulator.start_all()
        self.is_processing = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        # Started stream processing
    
    def stop_processing(self):
        """Stop processing camera streams"""
        self.is_processing = False
        self.simulator.stop_all()
        if self.process_thread:
            self.process_thread.join(timeout=3)
        # Stopped stream processing
    
    def _process_loop(self):
        """Main processing loop"""
        while self.is_processing:
            frames = self.simulator.get_camera_frames()
            
            if self.detection_callback and frames:
                # Send frames to detection callback
                try:
                    self.detection_callback(frames)
                except Exception as e:
                    self.logger.error(f"Detection callback error: {e}")
            
            time.sleep(0.1)  # Process at ~10 FPS
    
    def get_camera_status(self) -> dict:
        """Get status of all cameras"""
        status = {}
        for camera in self.simulator.cameras:
            status[camera.camera_id] = {
                'running': camera.is_running,
                'frame_count': camera.frame_count,
                'fps': camera.fps,
                'source': camera.video_source
            }
        return status

if __name__ == "__main__":
    # Test the video simulator
    logging.basicConfig(level=logging.INFO)
    
    def test_detection_callback(frames):
        """Test callback for frame processing"""
        print(f"Processing {len(frames)} camera frames")
        for camera_id, frame in frames.items():
            print(f"  {camera_id}: {frame.shape}")
    
    # Create and run processor
    processor = StreamProcessor(test_detection_callback)
    processor.setup_test_cameras()
    
    try:
        processor.start_processing()
        print("Running simulation... Press Ctrl+C to stop")
        time.sleep(30)  # Run for 30 seconds
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        processor.stop_processing()