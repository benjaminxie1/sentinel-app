"""
App-Only Notification System
Handles in-application alerts without external SMS/email dependencies
"""

import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import cv2
import numpy as np
from queue import Queue, Empty
import sqlite3
import base64

@dataclass
class AlertMessage:
    """Alert message structure"""
    alert_id: str
    alert_type: str  # P1, P2, P4
    camera_id: str
    message: str
    confidence: float
    timestamp: datetime
    image_data: Optional[bytes] = None
    location: str = ""
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.image_data:
            # Convert image data to base64 for JSON serialization
            data['image_data'] = base64.b64encode(self.image_data).decode('utf-8')
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AlertMessage':
        """Create AlertMessage from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('acknowledged_at'):
            data['acknowledged_at'] = datetime.fromisoformat(data['acknowledged_at'])
        if data.get('image_data'):
            # Decode base64 image data
            data['image_data'] = base64.b64decode(data['image_data'])
        return cls(**data)

@dataclass
class AppAlertConfig:
    """In-app alert configuration"""
    # Alert storage
    max_alerts_stored: int = 1000
    alert_retention_days: int = 30
    
    # Rate limiting
    max_alerts_per_hour: int = 50
    max_alerts_per_day: int = 200
    
    # UI behavior
    auto_popup_p1: bool = True  # Auto-show P1 alerts
    auto_popup_p2: bool = True  # Auto-show P2 alerts
    sound_enabled: bool = True
    
    # Persistence
    database_path: str = "data/alerts.db"
    alert_frames_dir: str = "data/alert_frames"

class AlertDatabase:
    """Local alert storage and management"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for alert storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Main alerts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE NOT NULL,
                        alert_type TEXT NOT NULL,
                        camera_id TEXT NOT NULL,
                        message TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        location TEXT,
                        frame_path TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        acknowledged_by TEXT,
                        acknowledged_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data JSON
                    )
                """)
                
                # Indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_camera ON alerts(camera_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)")
                
                # Alert statistics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hour_key TEXT NOT NULL,
                        day_key TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        count INTEGER DEFAULT 1,
                        UNIQUE(hour_key, day_key, alert_type)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize alert database: {e}")
    
    def save_alert(self, alert: AlertMessage, frame_path: Optional[str] = None) -> bool:
        """Save alert to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts (
                        alert_id, alert_type, camera_id, message, confidence,
                        timestamp, location, frame_path, acknowledged,
                        acknowledged_by, acknowledged_at, data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id,
                    alert.alert_type,
                    alert.camera_id,
                    alert.message,
                    alert.confidence,
                    alert.timestamp.isoformat(),
                    alert.location,
                    frame_path,
                    alert.acknowledged,
                    alert.acknowledged_by,
                    alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    json.dumps(alert.to_dict())
                ))
                
                # Update statistics
                hour_key = alert.timestamp.strftime('%Y-%m-%d-%H')
                day_key = alert.timestamp.strftime('%Y-%m-%d')
                
                conn.execute("""
                    INSERT OR REPLACE INTO alert_stats (hour_key, day_key, alert_type, count)
                    VALUES (?, ?, ?, 
                        COALESCE((SELECT count + 1 FROM alert_stats 
                                  WHERE hour_key = ? AND day_key = ? AND alert_type = ?), 1)
                    )
                """, (hour_key, day_key, alert.alert_type, hour_key, day_key, alert.alert_type))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
            return False
    
    def get_recent_alerts(self, hours: int = 24, limit: int = 100) -> List[AlertMessage]:
        """Get recent alerts from database"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT data FROM alerts 
                    WHERE timestamp > ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (cutoff_time, limit))
                
                alerts = []
                for row in cursor.fetchall():
                    try:
                        data = json.loads(row['data'])
                        alerts.append(AlertMessage.from_dict(data))
                    except Exception as e:
                        self.logger.warning(f"Failed to parse alert data: {e}")
                
                return alerts
                
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "operator", notes: str = "") -> bool:
        """Mark alert as acknowledged"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET acknowledged = TRUE,
                        acknowledged_by = ?,
                        acknowledged_at = CURRENT_TIMESTAMP
                    WHERE alert_id = ?
                """, (acknowledged_by, alert_id))
                
                affected = conn.execute("SELECT changes()").fetchone()[0]
                conn.commit()
                
                return affected > 0
                
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def get_unacknowledged_count(self) -> Dict[str, int]:
        """Get count of unacknowledged alerts by type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT alert_type, COUNT(*) as count
                    FROM alerts
                    WHERE acknowledged = FALSE
                    GROUP BY alert_type
                """)
                
                counts = {'P1': 0, 'P2': 0, 'P4': 0}
                for row in cursor.fetchall():
                    counts[row[0]] = row[1]
                
                return counts
                
        except Exception as e:
            self.logger.error(f"Failed to get unacknowledged count: {e}")
            return {'P1': 0, 'P2': 0, 'P4': 0}
    
    def cleanup_old_alerts(self, retention_days: int):
        """Remove alerts older than retention period"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Get frame paths to delete
                cursor = conn.execute("""
                    SELECT frame_path FROM alerts 
                    WHERE timestamp < ? AND frame_path IS NOT NULL
                """, (cutoff_date,))
                
                frame_paths = [row[0] for row in cursor.fetchall()]
                
                # Delete old alerts
                conn.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff_date,))
                
                # Cleanup old stats
                old_day_key = (datetime.now() - timedelta(days=retention_days + 1)).strftime('%Y-%m-%d')
                conn.execute("DELETE FROM alert_stats WHERE day_key < ?", (old_day_key,))
                
                conn.commit()
                
                # Delete associated frame files
                for frame_path in frame_paths:
                    try:
                        Path(frame_path).unlink(missing_ok=True)
                    except Exception as e:
                        self.logger.warning(f"Failed to delete frame file {frame_path}: {e}")
                
                self.logger.info(f"Cleaned up {len(frame_paths)} old alerts")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old alerts: {e}")

class AppNotificationManager:
    """Application-only notification manager"""
    
    def __init__(self, config: Optional[AppAlertConfig] = None):
        self.config = config or AppAlertConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.database = AlertDatabase(self.config.database_path)
        self.alert_queue = Queue()
        self.alert_callbacks: List[Callable[[AlertMessage], None]] = []
        
        # Rate limiting
        self.alert_counts = {'hourly': {}, 'daily': {}}
        self.last_cleanup = datetime.now()
        
        # Processing state
        self.is_processing = False
        self.processor_thread: Optional[threading.Thread] = None
        
        # Create alert frames directory
        Path(self.config.alert_frames_dir).mkdir(parents=True, exist_ok=True)
        
        # Start processing
        self.start_processing()
    
    def register_callback(self, callback: Callable[[AlertMessage], None]):
        """Register callback for new alerts (for UI updates)"""
        self.alert_callbacks.append(callback)
    
    def send_fire_alert(self, alert: AlertMessage, image_frame: Optional[np.ndarray] = None):
        """Send fire detection alert to application"""
        try:
            # Check rate limits
            if not self._check_rate_limits(alert.alert_type):
                self.logger.warning(f"Rate limit exceeded for {alert.alert_type} alerts")
                return
            
            # Save frame if provided
            frame_path = None
            if image_frame is not None:
                frame_path = self._save_alert_frame(alert.alert_id, image_frame)
            
            # Save to database
            if self.database.save_alert(alert, frame_path):
                # Queue for processing
                self.alert_queue.put(alert)
                self.logger.info(f"Alert {alert.alert_id} queued for processing")
            else:
                self.logger.error(f"Failed to save alert {alert.alert_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to send fire alert: {e}")
    
    def _save_alert_frame(self, alert_id: str, frame: np.ndarray) -> Optional[str]:
        """Save alert frame to disk"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{alert_id}_{timestamp}.jpg"
            filepath = Path(self.config.alert_frames_dir) / filename
            
            # Encode and save frame
            cv2.imwrite(str(filepath), frame)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save alert frame: {e}")
            return None
    
    def _check_rate_limits(self, alert_type: str) -> bool:
        """Check if alert is within rate limits"""
        now = datetime.now()
        
        # Cleanup old counts
        if now - self.last_cleanup > timedelta(hours=1):
            self._cleanup_rate_limits()
        
        # Check hourly limit
        hour_key = now.strftime('%Y-%m-%d-%H')
        hourly_count = self.alert_counts['hourly'].get(hour_key, 0)
        
        if hourly_count >= self.config.max_alerts_per_hour:
            return False
        
        # Check daily limit
        day_key = now.strftime('%Y-%m-%d')
        daily_count = self.alert_counts['daily'].get(day_key, 0)
        
        if daily_count >= self.config.max_alerts_per_day:
            return False
        
        # Update counts
        self.alert_counts['hourly'][hour_key] = hourly_count + 1
        self.alert_counts['daily'][day_key] = daily_count + 1
        
        return True
    
    def _cleanup_rate_limits(self):
        """Cleanup old rate limit counts"""
        now = datetime.now()
        
        # Remove old hourly counts
        cutoff_hour = (now - timedelta(hours=24)).strftime('%Y-%m-%d-%H')
        self.alert_counts['hourly'] = {
            k: v for k, v in self.alert_counts['hourly'].items() if k >= cutoff_hour
        }
        
        # Remove old daily counts
        cutoff_day = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        self.alert_counts['daily'] = {
            k: v for k, v in self.alert_counts['daily'].items() if k >= cutoff_day
        }
        
        self.last_cleanup = now
    
    def start_processing(self):
        """Start alert processing thread"""
        self.is_processing = True
        self.processor_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.processor_thread.start()
        self.logger.info("Started alert processing")
    
    def stop_processing(self):
        """Stop alert processing"""
        self.is_processing = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        self.logger.info("Stopped alert processing")
    
    def _process_alerts(self):
        """Process alert queue"""
        while self.is_processing:
            try:
                # Get alert from queue
                alert = self.alert_queue.get(timeout=1)
                
                # Notify all registered callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        self.logger.error(f"Alert callback error: {e}")
                
                # Cleanup old alerts periodically
                if hasattr(self, '_last_cleanup_check'):
                    if datetime.now() - self._last_cleanup_check > timedelta(hours=24):
                        self.database.cleanup_old_alerts(self.config.alert_retention_days)
                        self._last_cleanup_check = datetime.now()
                else:
                    self._last_cleanup_check = datetime.now()
                
                self.alert_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[AlertMessage]:
        """Get recent alerts"""
        return self.database.get_recent_alerts(hours)
    
    def get_unacknowledged_count(self) -> Dict[str, int]:
        """Get unacknowledged alert counts"""
        return self.database.get_unacknowledged_count()
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "operator") -> bool:
        """Acknowledge an alert"""
        return self.database.acknowledge_alert(alert_id, acknowledged_by)
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                # Get today's stats
                today = datetime.now().strftime('%Y-%m-%d')
                cursor = conn.execute("""
                    SELECT alert_type, SUM(count) as total
                    FROM alert_stats
                    WHERE day_key = ?
                    GROUP BY alert_type
                """, (today,))
                
                today_stats = {'P1': 0, 'P2': 0, 'P4': 0}
                for row in cursor.fetchall():
                    today_stats[row[0]] = row[1]
                
                # Get last 7 days stats
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                cursor = conn.execute("""
                    SELECT alert_type, SUM(count) as total
                    FROM alert_stats
                    WHERE day_key >= ?
                    GROUP BY alert_type
                """, (week_ago,))
                
                week_stats = {'P1': 0, 'P2': 0, 'P4': 0}
                for row in cursor.fetchall():
                    week_stats[row[0]] = row[1]
                
                # Get unacknowledged counts
                unacknowledged = self.get_unacknowledged_count()
                
                return {
                    'today': today_stats,
                    'last_7_days': week_stats,
                    'unacknowledged': unacknowledged,
                    'total_stored': conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get alert stats: {e}")
            return {
                'today': {'P1': 0, 'P2': 0, 'P4': 0},
                'last_7_days': {'P1': 0, 'P2': 0, 'P4': 0},
                'unacknowledged': {'P1': 0, 'P2': 0, 'P4': 0},
                'total_stored': 0
            }