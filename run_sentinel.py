#!/usr/bin/env python3
"""
Sentinel Fire Detection System - Production Entry Point
Main production launcher for fire detection system
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.main import SentinelSystem
from backend.config.config_manager import ConfigManager
from backend.utils.system_monitor import system_monitor


class SentinelProduction:
    """Production Sentinel Fire Detection System"""
    
    def __init__(self):
        self.sentinel_system: Optional[SentinelSystem] = None
        self.is_running = False
        self.logger = self._setup_logging()
        self.config_manager = ConfigManager()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup production logging"""
        # Create logs directory
        log_dir = Path("/var/log/sentinel") if Path("/var/log/sentinel").exists() else Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'sentinel.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    async def start(self):
        """Start the production system"""
        try:
            self.logger.info("🔥 Starting Sentinel Fire Detection System (Production Mode)")
            self.logger.info("=" * 60)
            
            # Load configuration
            config = self.config_manager.load_config()
            if not config:
                self.logger.error("Failed to load system configuration")
                return False
            
            # Check system health
            health_check = system_monitor.check_system_health()
            if not health_check['healthy']:
                self.logger.warning(f"System health issues detected: {health_check['issues']}")
            
            # Create and configure Sentinel system
            self.sentinel_system = SentinelSystem(config)
            
            # Start the detection system
            await self.sentinel_system.start()
            
            self.is_running = True
            self.logger.info("✅ Sentinel Fire Detection System started successfully")
            
            # Main monitoring loop
            await self._monitoring_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Sentinel system: {e}")
            return False
    
    async def _monitoring_loop(self):
        """Main system monitoring loop"""
        last_health_check = 0
        health_check_interval = 300  # 5 minutes
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Periodic health checks
                if current_time - last_health_check > health_check_interval:
                    health = system_monitor.check_system_health()
                    if not health['healthy']:
                        self.logger.warning(f"Health issues: {health['issues']}")
                    
                    # Log system status
                    if self.sentinel_system:
                        status = await self.sentinel_system.get_status()
                        self.logger.info(
                            f"Status: {status['active_cameras']} cameras, "
                            f"uptime: {status['uptime']:.1f}h, "
                            f"alerts: {status.get('alerts_today', 0)}"
                        )
                    
                    last_health_check = current_time
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """Stop the production system"""
        self.logger.info("🛑 Stopping Sentinel Fire Detection System...")
        self.is_running = False
        
        if self.sentinel_system:
            await self.sentinel_system.stop()
        
        self.logger.info("✅ Sentinel Fire Detection System stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point for production system"""
    # Setup signal handlers
    sentinel = SentinelProduction()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, sentinel._signal_handler)
    signal.signal(signal.SIGTERM, sentinel._signal_handler)
    
    # Ensure required directories exist
    required_dirs = [
        Path("logs"),
        Path("data"),
        Path("data/alert_frames"),
        Path("models")
    ]
    
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    
    try:
        # Start the system
        await sentinel.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        await sentinel.stop()
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        await sentinel.stop()
        sys.exit(1)


if __name__ == "__main__":
    print("🔥 Sentinel Fire Detection System - Production Mode")
    print("⚠️  SUPPLEMENTARY FIRE DETECTION ONLY - NOT A REPLACEMENT FOR CERTIFIED SYSTEMS")
    print()
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    
    # Run the production system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sentinel Fire Detection System shutdown complete")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        sys.exit(1)