"""
Alert Management System
Handles detection alerts, logging, and notifications
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging
from enum import Enum
import threading
from queue import Queue

class AlertLevel(Enum):
    P1 = "P1"  # Immediate alert
    P2 = "P2"  # Review queue
    P4 = "P4"  # Log only

@dataclass
class Alert:
    """Fire detection alert"""
    id: str
    timestamp: float
    camera_id: str
    alert_level: AlertLevel
    confidence: float
    detections: List[Dict]  # Detection details
    status: str = "active"  # active, acknowledged, resolved
    notes: str = ""
    frame_path: Optional[str] = None  # Path to saved frame with bounding boxes
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['alert_level'] = self.alert_level.value
        data['detections'] = json.dumps(self.detections)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Alert':
        """Create from dictionary"""
        # Create a copy to avoid modifying the original
        clean_data = data.copy()
        
        # Remove database-specific fields that aren't part of the Alert dataclass
        clean_data.pop('created_at', None)
        
        # Convert field types
        clean_data['alert_level'] = AlertLevel(clean_data['alert_level'])
        clean_data['detections'] = json.loads(clean_data['detections'])
        
        # Handle optional frame_path
        if 'frame_path' not in clean_data:
            clean_data['frame_path'] = None
        
        return cls(**clean_data)

class AlertDatabase:
    """SQLite database for storing alerts and system logs"""
    
    def __init__(self, db_path: str = "data/alerts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    camera_id TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    detections TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    notes TEXT DEFAULT '',
                    frame_path TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    component TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    camera_id TEXT NOT NULL,
                    fps REAL,
                    detection_latency REAL,
                    total_detections INTEGER,
                    false_positives INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_alert(self, alert: Alert) -> bool:
        """Save alert to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = alert.to_dict()
                conn.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (id, timestamp, camera_id, alert_level, confidence, detections, status, notes, frame_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['id'], data['timestamp'], data['camera_id'], 
                    data['alert_level'], data['confidence'], data['detections'],
                    data['status'], data['notes'], data.get('frame_path')
                ))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
            return False
    
    def get_recent_alerts(self, hours: int = 24, limit: int = 100) -> List[Alert]:
        """Get recent alerts"""
        cutoff = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM alerts 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (cutoff, limit))
            
            alerts = []
            for row in cursor:
                alert_data = dict(row)
                alerts.append(Alert.from_dict(alert_data))
            
            return alerts
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        cutoff = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    alert_level,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM alerts 
                WHERE timestamp > ? 
                GROUP BY alert_level
            """, (cutoff,))
            
            stats = {}
            for row in cursor:
                level, count, avg_conf = row
                stats[level] = {
                    'count': count,
                    'avg_confidence': round(avg_conf, 3)
                }
            
            # Get total count
            cursor = conn.execute("""
                SELECT COUNT(*) FROM alerts WHERE timestamp > ?
            """, (cutoff,))
            total = cursor.fetchone()[0]
            
            stats['total'] = total
            stats['time_range_hours'] = hours
            
            return stats
    
    def log_system_event(self, level: str, message: str, component: str = None, data: Dict = None):
        """Log system event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_logs (timestamp, level, message, component, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    time.time(), level, message, component,
                    json.dumps(data) if data else None
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log system event: {e}")
    
    def cleanup_old_records(self, retention_days: int = 30):
        """Clean up old records"""
        cutoff = time.time() - (retention_days * 24 * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clean alerts
                cursor = conn.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff,))
                alerts_deleted = cursor.rowcount
                
                # Clean logs
                cursor = conn.execute("DELETE FROM system_logs WHERE timestamp < ?", (cutoff,))
                logs_deleted = cursor.rowcount
                
                # Clean metrics
                cursor = conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff,))
                metrics_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Cleanup: {alerts_deleted} alerts, {logs_deleted} logs, {metrics_deleted} metrics")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")

class AlertManager:
    """Main alert management system"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.database = AlertDatabase()
        self.logger = logging.getLogger(__name__)
        
        # Alert queue for processing
        self.alert_queue = Queue()
        self.notification_queue = Queue()
        
        # Start processing threads
        self.is_running = True
        self.alert_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.notification_thread = threading.Thread(target=self._process_notifications, daemon=True)
        
        self.alert_thread.start()
        self.notification_thread.start()
        
        self.logger.info("Alert Manager initialized")
    
    def create_alert(self, camera_id: str, detection_result) -> Optional[Alert]:
        """Create alert from detection result"""
        if detection_result.alert_level == 'None':
            return None
        
        # Generate unique alert ID
        alert_id = f"{camera_id}_{int(time.time() * 1000)}"
        
        # Convert detections to serializable format
        detections = []
        for detection in detection_result.detections:
            detections.append({
                'confidence': detection.confidence,
                'bbox': detection.bbox,
                'class_name': detection.class_name,
                'timestamp': detection.timestamp
            })
        
        alert = Alert(
            id=alert_id,
            timestamp=detection_result.timestamp,
            camera_id=camera_id,
            alert_level=AlertLevel(detection_result.alert_level),
            confidence=detection_result.max_confidence,
            detections=detections
        )
        
        # Queue alert for processing
        self.alert_queue.put(alert)
        
        return alert
    
    def _process_alerts(self):
        """Process alerts in background thread"""
        while self.is_running:
            try:
                alert = self.alert_queue.get(timeout=1)
                
                # Save to database
                if self.database.save_alert(alert):
                    self.logger.info(f"Alert saved: {alert.id} ({alert.alert_level.value})")
                    
                    # Queue for notifications
                    self.notification_queue.put(alert)
                
                self.alert_queue.task_done()
                
            except Exception as e:
                import queue
                if not isinstance(e, queue.Empty):
                    self.logger.error(f"Error processing alert: {e}")
    
    def _process_notifications(self):
        """Process notifications in background thread"""
        while self.is_running:
            try:
                alert = self.notification_queue.get(timeout=1)
                
                # Send notifications based on alert level
                if alert.alert_level == AlertLevel.P1:
                    self._send_immediate_notification(alert)
                elif alert.alert_level == AlertLevel.P2:
                    self._send_review_notification(alert)
                # P4 alerts are just logged
                
                self.notification_queue.task_done()
                
            except Exception as e:
                import queue
                if not isinstance(e, queue.Empty):
                    self.logger.error(f"Error processing notification: {e}")
    
    def _send_immediate_notification(self, alert: Alert):
        """Send immediate notification for P1 alerts"""
        message = f"🔥 FIRE DETECTED - Camera {alert.camera_id} - Confidence: {alert.confidence:.2f}"
        self.logger.critical(message)
        
        # In full implementation, this would:
        # - Send SMS alerts
        # - Send email notifications
        # - Trigger desktop notifications
        # - Update GUI in real-time
        
        self.database.log_system_event("CRITICAL", message, "AlertManager", {
            'alert_id': alert.id,
            'camera_id': alert.camera_id,
            'confidence': alert.confidence
        })
    
    def _send_review_notification(self, alert: Alert):
        """Send review notification for P2 alerts"""
        message = f"🔍 Fire Detection Review - Camera {alert.camera_id} - Confidence: {alert.confidence:.2f}"
        self.logger.warning(message)
        
        self.database.log_system_event("WARNING", message, "AlertManager", {
            'alert_id': alert.id,
            'camera_id': alert.camera_id,
            'confidence': alert.confidence
        })
    
    def get_dashboard_data(self, total_cameras: int = 0) -> Dict[str, Any]:
        """Get data for dashboard display"""
        recent_alerts = self.database.get_recent_alerts(hours=24, limit=50)
        alert_stats = self.database.get_alert_statistics(hours=24)
        
        return {
            'recent_alerts': [
                {
                    'id': alert.id,
                    'timestamp': alert.timestamp,
                    'camera_id': alert.camera_id,
                    'alert_level': alert.alert_level.value,
                    'confidence': alert.confidence,
                    'status': alert.status,
                    'has_frame': alert.frame_path is not None
                }
                for alert in recent_alerts
            ],
            'statistics': alert_stats,
            'system_status': {
                'total_cameras': total_cameras,
                'active_alerts': len([a for a in recent_alerts if a.status == 'active']),
                'last_detection': recent_alerts[0].timestamp if recent_alerts else None
            }
        }
    
    def acknowledge_alert(self, alert_id: str, notes: str = "") -> bool:
        """Acknowledge an alert"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE alerts 
                    SET status = 'acknowledged', notes = ?
                    WHERE id = ?
                """, (notes, alert_id))
                rows_affected = cursor.rowcount
                conn.commit()
            
            if rows_affected > 0:
                self.logger.info(f"Alert acknowledged: {alert_id}")
                return True
            else:
                self.logger.warning(f"Alert not found for acknowledgment: {alert_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def stop(self):
        """Stop the alert manager"""
        self.is_running = False
        self.logger.info("Alert Manager stopped")

# Global alert manager instance
alert_manager = None

def get_alert_manager():
    """Get global alert manager instance"""
    global alert_manager
    if alert_manager is None:
        alert_manager = AlertManager()
    return alert_manager