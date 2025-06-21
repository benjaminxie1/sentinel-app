#!/usr/bin/env python3
"""
Sentinel Fire Detection API Server
HTTP API server for Tauri frontend communication
"""

import asyncio
import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from aiohttp import web, web_request
from aiohttp.web_response import Response
import aiohttp_cors

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from main import SentinelSystem, APIServer
from alerts.alert_manager import get_alert_manager
from utils.system_monitor import system_monitor
from config.camera_config import CameraConfigManager, CameraProfile

class SentinelAPIServer:
    """HTTP API Server for Tauri communication"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.app = web.Application()
        self.sentinel_system: Optional[SentinelSystem] = None
        self.api_handler: Optional[APIServer] = None
        self.camera_config = CameraConfigManager()
        self.logger = self._setup_logging()
        self.is_running = False
        
        # Setup CORS for Tauri communication
        self.cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        self._setup_routes()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure API server logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _setup_routes(self):
        """Setup API routes"""
        # Health check
        self.app.router.add_get('/api/health', self.health_check)
        
        # Dashboard data
        self.app.router.add_get('/api/dashboard', self.get_dashboard_data)
        
        # Threshold management
        self.app.router.add_post('/api/threshold', self.update_threshold)
        
        # Alert management
        self.app.router.add_post('/api/acknowledge', self.acknowledge_alert)
        self.app.router.add_get('/api/alerts/{alert_id}/frame', self.get_alert_frame)
        
        # Camera feeds
        self.app.router.add_get('/api/cameras', self.get_camera_feeds)
        self.app.router.add_get('/api/cameras/{camera_id}/frame', self.get_camera_frame)
        self.app.router.add_post('/api/cameras/discover', self.discover_cameras)
        self.app.router.add_post('/api/cameras/add', self.add_camera)
        self.app.router.add_post('/api/cameras/{camera_id}/test', self.test_camera)
        self.app.router.add_delete('/api/cameras/{camera_id}/remove', self.remove_camera)
        
        # System status
        self.app.router.add_get('/api/status', self.get_system_status)
        
        # System metrics (real performance data)
        self.app.router.add_get('/api/metrics', self.get_system_metrics)
        
        # Enable CORS for all routes
        for route in list(self.app.router.routes()):
            self.cors.add(route)
    
    async def health_check(self, request: web_request.BaseRequest) -> Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': time.time(),
            'backend_running': self.sentinel_system is not None and self.sentinel_system.is_running
        })
    
    async def get_dashboard_data(self, request: web_request.BaseRequest) -> Response:
        """Get dashboard data for frontend"""
        try:
            if not self.api_handler:
                return web.json_response({'error': 'Backend not initialized'}, status=500)
            
            data = self.api_handler.get_dashboard_data()
            return web.json_response(data)
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def update_threshold(self, request: web_request.BaseRequest) -> Response:
        """Update detection threshold"""
        try:
            if not self.api_handler:
                return web.json_response({'error': 'Backend not initialized'}, status=500)
            
            data = await request.json()
            threshold_name = data.get('threshold_name')
            value = data.get('value')
            
            if not threshold_name or value is None:
                return web.json_response({'error': 'Missing threshold_name or value'}, status=400)
            
            success = self.api_handler.update_threshold(threshold_name, float(value))
            return web.json_response({'success': success})
            
        except Exception as e:
            self.logger.error(f"Error updating threshold: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def acknowledge_alert(self, request: web_request.BaseRequest) -> Response:
        """Acknowledge an alert"""
        try:
            if not self.api_handler:
                return web.json_response({'error': 'Backend not initialized'}, status=500)
            
            data = await request.json()
            alert_id = data.get('alert_id')
            
            if not alert_id:
                return web.json_response({'error': 'Missing alert_id'}, status=400)
            
            success = self.api_handler.acknowledge_alert(alert_id)
            return web.json_response({'success': success})
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_alert_frame(self, request: web_request.BaseRequest) -> Response:
        """Get the saved frame for a specific alert"""
        try:
            alert_id = request.match_info['alert_id']
            
            if not self.api_handler:
                return web.json_response({'error': 'Backend not initialized'}, status=500)
            
            # Get alert from database
            alerts = self.api_handler.sentinel.alert_manager.database.get_recent_alerts(hours=24*7)
            alert = None
            
            for a in alerts:
                if a.id == alert_id:
                    alert = a
                    break
            
            if not alert:
                return web.json_response({'error': f'Alert {alert_id} not found'}, status=404)
            
            if not alert.frame_path or not Path(alert.frame_path).exists():
                return web.json_response({'error': 'No frame available for this alert'}, status=404)
            
            # Read the frame image
            with open(alert.frame_path, 'rb') as f:
                image_data = f.read()
            
            # Convert to base64 for JSON response
            import base64
            frame_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return web.json_response({
                'alert_id': alert_id,
                'frame': frame_base64,
                'timestamp': alert.timestamp,
                'camera_id': alert.camera_id,
                'confidence': alert.confidence,
                'detections': alert.detections,
                'format': 'jpeg'
            })
            
        except Exception as e:
            self.logger.error(f"Error getting alert frame: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_camera_feeds(self, request: web_request.BaseRequest) -> Response:
        """Get camera feed status and data"""
        try:
            if not self.sentinel_system or not self.sentinel_system.stream_processor:
                return web.json_response({'error': 'Camera system not initialized'}, status=500)
            
            # Get camera status from stream processor
            camera_status = self.sentinel_system.stream_processor.get_camera_status()
            
            # Format for frontend
            cameras = []
            for camera_id, status in camera_status.items():
                cameras.append({
                    'id': camera_id,
                    'name': status.get('name', f'Camera {camera_id}'),
                    'status': 'active' if status.get('running', False) else 'inactive',
                    'location': status.get('location', 'Unknown'),
                    'last_frame_time': status.get('last_frame_time', 0),
                    'fps': status.get('fps', 0),
                    'resolution': status.get('resolution', '1920x1080')
                })
            
            return web.json_response({
                'cameras': cameras,
                'total_cameras': len(cameras),
                'active_cameras': len([c for c in cameras if c['status'] == 'active'])
            })
            
        except Exception as e:
            self.logger.error(f"Error getting camera feeds: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_system_status(self, request: web_request.BaseRequest) -> Response:
        """Get system status"""
        try:
            backend_running = self.sentinel_system is not None and self.sentinel_system.is_running
            
            status = {
                'backend_running': backend_running,
                'api_server_running': True,
                'timestamp': time.time(),
                'uptime': time.time() - getattr(self.sentinel_system, 'start_time', time.time()) if backend_running else 0
            }
            
            if backend_running and self.sentinel_system.stream_processor:
                camera_status = self.sentinel_system.stream_processor.get_camera_status()
                status.update({
                    'active_cameras': len([c for c in camera_status.values() if c.get('running', False)]),
                    'total_cameras': len(camera_status)
                })
            
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_camera_frame(self, request: web_request.BaseRequest) -> Response:
        """Get current frame from specific camera as base64 JPEG"""
        try:
            camera_id = request.match_info['camera_id']
            
            if not self.sentinel_system or not self.sentinel_system.stream_processor:
                return web.json_response({'error': 'Camera system not initialized'}, status=500)
            
            # Get frame from stream processor
            frames = self.sentinel_system.stream_processor.simulator.get_camera_frames()
            
            if camera_id not in frames:
                return web.json_response({'error': f'Camera {camera_id} not found'}, status=404)
            
            frame = frames[camera_id]
            
            # Encode frame as JPEG
            import cv2
            import base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return web.json_response({
                'camera_id': camera_id,
                'frame': frame_base64,
                'timestamp': time.time(),
                'format': 'jpeg'
            })
            
        except Exception as e:
            self.logger.error(f"Error getting camera frame: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def discover_cameras(self, request: web_request.BaseRequest) -> Response:
        """Discover ONVIF cameras on the network"""
        try:
            from detection.rtsp_manager import ONVIFDiscovery
            
            data = await request.json() if request.content_length else {}
            timeout = data.get('timeout', 5)
            
            discovered_cameras = ONVIFDiscovery.discover_cameras(timeout)
            
            return web.json_response({
                'cameras': discovered_cameras,
                'count': len(discovered_cameras),
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Error discovering cameras: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def add_camera(self, request: web_request.BaseRequest) -> Response:
        """Add a new RTSP camera"""
        try:
            data = await request.json()
            
            required_fields = ['camera_id', 'rtsp_url']
            for field in required_fields:
                if field not in data:
                    return web.json_response({'error': f'Missing required field: {field}'}, status=400)
            
            if not self.sentinel_system or not self.sentinel_system.stream_processor:
                return web.json_response({'error': 'Camera system not initialized'}, status=500)
            
            camera_id = data['camera_id']
            rtsp_url = data['rtsp_url']
            
            # Check if camera already exists
            existing_cameras = [cam.camera_id for cam in self.sentinel_system.stream_processor.simulator.cameras]
            if camera_id in existing_cameras:
                return web.json_response({'error': f'Camera {camera_id} already exists'}, status=400)
            
            # Test the RTSP connection first (skip for synthetic sources)
            if rtsp_url not in ['synthetic', 'test']:
                from detection.rtsp_manager import RTSPManager
                manager = RTSPManager()
                test_success, test_message = manager.test_rtsp_url(
                    rtsp_url, 
                    data.get('username'), 
                    data.get('password')
                )
                
                if not test_success:
                    return web.json_response({
                        'success': False,
                        'error': f'Camera test failed: {test_message}'
                    }, status=400)
            
            # Create camera profile and save to config
            camera_profile = CameraProfile(
                camera_id=camera_id,
                name=data.get('name', f'Camera {camera_id}'),
                rtsp_url=rtsp_url,
                username=data.get('username'),
                password=data.get('password'),
                fps=data.get('fps', 30),
                enabled=data.get('enabled', True),
                location=data.get('location', 'Unknown')
            )
            
            # Save to configuration
            if not self.camera_config.add_camera(camera_profile):
                return web.json_response({'error': 'Failed to save camera configuration'}, status=500)
            
            # Add camera to the simulator (for now, until full RTSP integration)
            # Use the RTSP URL as the video source
            camera = self.sentinel_system.stream_processor.simulator.add_camera(
                camera_id, rtsp_url, fps=camera_profile.fps
            )
            
            # Start the camera
            camera.start()
            
            # Camera added successfully
            
            return web.json_response({
                'success': True,
                'camera_id': camera_id,
                'message': f'Camera {camera_id} added successfully'
            })
            
        except Exception as e:
            self.logger.error(f"Error adding camera: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def test_camera(self, request: web_request.BaseRequest) -> Response:
        """Test RTSP camera connection"""
        try:
            camera_id = request.match_info['camera_id']
            data = await request.json()
            
            rtsp_url = data.get('rtsp_url')
            username = data.get('username')
            password = data.get('password')
            
            if not rtsp_url:
                return web.json_response({'error': 'Missing rtsp_url'}, status=400)
            
            from detection.rtsp_manager import RTSPManager
            
            manager = RTSPManager()
            success, message = manager.test_rtsp_url(rtsp_url, username, password)
            
            return web.json_response({
                'camera_id': camera_id,
                'success': success,
                'message': message,
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Error testing camera: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def remove_camera(self, request: web_request.BaseRequest) -> Response:
        """Remove RTSP camera from system"""
        try:
            camera_id = request.match_info['camera_id']
            
            if not self.sentinel_system or not self.sentinel_system.stream_processor:
                return web.json_response({'error': 'Camera system not initialized'}, status=500)
            
            # Remove camera from simulator
            cameras_to_remove = []
            for camera in self.sentinel_system.stream_processor.simulator.cameras:
                if camera.camera_id == camera_id:
                    cameras_to_remove.append(camera)
            
            if not cameras_to_remove:
                return web.json_response({'error': f'Camera {camera_id} not found'}, status=404)
            
            # Stop and remove the camera
            for camera in cameras_to_remove:
                camera.stop()
                self.sentinel_system.stream_processor.simulator.cameras.remove(camera)
            
            # Remove from configuration
            self.camera_config.remove_camera(camera_id)
            
            # Camera removed successfully
            
            return web.json_response({
                'success': True,
                'camera_id': camera_id,
                'message': f'Camera {camera_id} removed successfully',
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Error removing camera: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_system_metrics(self, request: web_request.BaseRequest) -> Response:
        """Get real system performance metrics"""
        try:
            # Get real system metrics
            metrics = system_monitor.get_system_metrics()
            
            # Add detection performance metrics if backend is running
            if self.sentinel_system and hasattr(self.sentinel_system, 'frames_processed'):
                detection_metrics = system_monitor.get_detection_performance_metrics(
                    frames_processed=getattr(self.sentinel_system, 'frames_processed', 0),
                    detections_made=getattr(self.sentinel_system, 'detections_made', 0)
                )
                metrics['detection_performance'] = detection_metrics
            
            return web.json_response(metrics)
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def start_backend_system(self):
        """Start the Sentinel backend system"""
        try:
            # Starting Sentinel backend system
            
            # Create and start Sentinel system
            self.sentinel_system = SentinelSystem()
            self.sentinel_system.start_time = time.time()
            
            # Create API handler
            self.api_handler = APIServer(self.sentinel_system)
            
            # Start the backend in a separate task
            asyncio.create_task(self.sentinel_system.start())
            
            # Give it time to initialize
            await asyncio.sleep(2)
            
            # Load cameras from configuration
            await self._load_cameras_from_config()
            
            # Backend system started
            
        except Exception as e:
            self.logger.error(f"Failed to start backend system: {e}")
            raise
    
    async def _load_cameras_from_config(self):
        """Load cameras from configuration file on startup"""
        try:
            enabled_cameras = self.camera_config.get_enabled_cameras()
            
            if not enabled_cameras:
                # No enabled cameras in configuration
                return
            
            for camera_id, camera_profile in enabled_cameras.items():
                try:
                    # Add camera to simulator
                    camera = self.sentinel_system.stream_processor.simulator.add_camera(
                        camera_id, camera_profile.rtsp_url, fps=camera_profile.fps
                    )
                    camera.start()
                    
                    # Camera loaded from config
                    
                except Exception as e:
                    self.logger.error(f"Failed to load camera {camera_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to load cameras from config: {e}")
    
    async def start_server(self):
        """Start the API server"""
        try:
            # Starting API Server
            
            # Start backend system first
            await self.start_backend_system()
            
            # Start web server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()
            
            self.is_running = True
            print(f"API Server running on http://localhost:{self.port}")
            
            # Keep server running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise
    
    def stop_server(self):
        """Stop the API server"""
        # Stopping API server
        self.is_running = False
        
        if self.sentinel_system:
            asyncio.create_task(self.sentinel_system.stop())

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """Main entry point"""
    print("🔥 Starting Sentinel API Server")
    print("="*40)
    
    # Ensure required directories exist
    for directory in ['logs', 'data', 'test_data', 'models']:
        Path(directory).mkdir(exist_ok=True)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start API server
    api_server = SentinelAPIServer()
    
    try:
        await api_server.start_server()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"API Server error: {e}")
    finally:
        api_server.stop_server()
        print("API Server stopped")

if __name__ == "__main__":
    # Install aiohttp if not present
    try:
        import aiohttp
        import aiohttp_cors
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "aiohttp-cors"])
        import aiohttp
        import aiohttp_cors
    
    # Run the API server
    asyncio.run(main())