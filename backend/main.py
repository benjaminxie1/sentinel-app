#!/usr/bin/env python3
"""
Sentinel Fire Detection System - Main Application
Coordinates detection engine, video processing, and alert management
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any
import threading

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from detection.fire_detector import FireDetector
from config.config_manager import config_manager
from alerts.alert_manager import get_alert_manager
from utils.video_simulator import StreamProcessor

class SentinelSystem:
    """Main Sentinel Fire Detection System"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.config_manager = config_manager
        self.alert_manager = get_alert_manager()
        self.fire_detector = None
        self.stream_processor = None
        self.is_running = False
        
        self.logger.info("Sentinel System initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Configure system logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/sentinel.log', mode='a')
            ]
        )
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        return logging.getLogger(__name__)
    
    async def start(self):
        """Start the Sentinel system"""
        try:
            self.logger.info("Starting Sentinel Fire Detection System")
            
            # Initialize components
            await self._initialize_components()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start main processing loop
            self.is_running = True
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Failed to start Sentinel system: {e}")
            raise
    
    async def _initialize_components(self):
        """Initialize all system components"""
        # Load configuration
        detection_config = self.config_manager.get_detection_config()
        system_config = self.config_manager.get_system_config()
        
        self.logger.info(f"Detection thresholds: P1={detection_config.immediate_alert}, "
                        f"P2={detection_config.review_queue}, P4={detection_config.log_only}")
        
        # Initialize fire detector
        self.fire_detector = FireDetector()
        self.logger.info("Fire detector initialized")
        
        # Initialize stream processor with detection callback
        self.stream_processor = StreamProcessor(self._detection_callback)
        self.stream_processor.setup_test_cameras()
        self.logger.info("Video stream processor initialized")
        
        # Start stream processing
        self.stream_processor.start_processing()
        self.logger.info("Camera stream processing started")
    
    def _detection_callback(self, frames: Dict[str, Any]):
        """Process detection results from camera frames"""
        for camera_id, frame in frames.items():
            try:
                # Run fire detection on frame
                detection_result = self.fire_detector.detect_fire(frame)
                
                # Create alert if detection found
                if detection_result.alert_level != 'None':
                    alert = self.alert_manager.create_alert(camera_id, detection_result)
                    if alert:
                        self.logger.info(f"Alert created: {alert.id} ({alert.alert_level.value}) "
                                       f"Camera: {camera_id} Confidence: {alert.confidence:.2f}")
                
            except Exception as e:
                self.logger.error(f"Detection error for camera {camera_id}: {e}")
    
    async def _main_loop(self):
        """Main system processing loop"""
        self.logger.info("Sentinel system running - monitoring cameras for fire detection")
        
        # Performance monitoring
        last_stats_time = time.time()
        
        while self.is_running:
            try:
                # Periodic system health checks
                current_time = time.time()
                
                # Log system statistics every 60 seconds
                if current_time - last_stats_time >= 60:
                    await self._log_system_stats()
                    last_stats_time = current_time
                
                # Check for configuration updates
                if self.config_manager.reload_config():
                    self.logger.info("Configuration reloaded")
                
                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _log_system_stats(self):
        """Log system performance statistics"""
        try:
            # Get camera status
            camera_status = self.stream_processor.get_camera_status()
            active_cameras = len([c for c in camera_status.values() if c['running']])
            
            # Get alert statistics
            dashboard_data = self.alert_manager.get_dashboard_data()
            active_alerts = dashboard_data['system_status']['active_alerts']
            
            self.logger.info(f"System Stats - Cameras: {active_cameras}, "
                           f"Active Alerts: {active_alerts}, "
                           f"Total Alerts (24h): {len(dashboard_data['recent_alerts'])}")
            
            # Log to database for historical tracking
            self.alert_manager.database.log_system_event(
                "INFO", "System health check", "SentinelSystem", {
                    'active_cameras': active_cameras,
                    'active_alerts': active_alerts,
                    'uptime_seconds': time.time() - self.start_time
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log system stats: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.is_running = False
    
    async def stop(self):
        """Stop the Sentinel system gracefully"""
        self.logger.info("Stopping Sentinel Fire Detection System")
        
        self.is_running = False
        
        # Stop components
        if self.stream_processor:
            self.stream_processor.stop_processing()
        
        if self.alert_manager:
            self.alert_manager.stop()
        
        self.logger.info("Sentinel system stopped")

class APIServer:
    """Simple API server for Tauri frontend communication"""
    
    def __init__(self, sentinel_system: SentinelSystem):
        self.sentinel = sentinel_system
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for frontend"""
        try:
            dashboard_data = self.sentinel.alert_manager.get_dashboard_data()
            config_summary = self.sentinel.config_manager.get_config_summary()
            
            return {
                'alerts': dashboard_data,
                'config': config_summary,
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}
    
    def update_threshold(self, threshold_name: str, value: float) -> bool:
        """Update detection threshold"""
        try:
            return self.sentinel.config_manager.update_threshold(threshold_name, value)
        except Exception as e:
            self.logger.error(f"Failed to update threshold {threshold_name}: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            return self.sentinel.alert_manager.acknowledge_alert(alert_id)
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False

async def main():
    """Main entry point"""
    print("🔥 Starting Sentinel Fire Detection System")
    print("="*50)
    
    # Create main system
    sentinel = SentinelSystem()
    sentinel.start_time = time.time()
    
    try:
        await sentinel.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"System error: {e}")
    finally:
        await sentinel.stop()
        print("Sentinel system stopped")

if __name__ == "__main__":
    # Ensure required directories exist
    for directory in ['logs', 'data', 'test_data', 'models']:
        Path(directory).mkdir(exist_ok=True)
    
    # Run the system
    asyncio.run(main())