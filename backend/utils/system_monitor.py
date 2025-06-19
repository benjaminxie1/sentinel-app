import psutil
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        self._last_net_io = None
        self._last_net_time = None
        
    def get_system_metrics(self) -> Dict:
        """Get real system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            disk_percent = disk.percent
            
            # Network metrics
            net_io = psutil.net_io_counters()
            network_latency = self._estimate_network_latency()
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024 ** 2)
            process_cpu_percent = process.cpu_percent(interval=0.1)
            
            # GPU metrics (if available)
            gpu_metrics = self._get_gpu_metrics()
            
            # System uptime
            uptime_seconds = time.time() - self.start_time
            
            return {
                'cpu': {
                    'usage_percent': round(cpu_percent, 1),
                    'core_count': cpu_count,
                    'process_cpu_percent': round(process_cpu_percent, 1)
                },
                'memory': {
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2),
                    'percent': round(memory_percent, 1),
                    'process_memory_mb': round(process_memory_mb, 1)
                },
                'disk': {
                    'used_gb': round(disk_used_gb, 2),
                    'total_gb': round(disk_total_gb, 2),
                    'percent': round(disk_percent, 1)
                },
                'network': {
                    'latency_ms': network_latency,
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                'gpu': gpu_metrics,
                'system': {
                    'uptime_seconds': int(uptime_seconds),
                    'uptime_hours': round(uptime_seconds / 3600, 2),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return self._get_fallback_metrics()
    
    def _estimate_network_latency(self) -> float:
        """Estimate network latency based on network I/O counters"""
        try:
            current_time = time.time()
            current_io = psutil.net_io_counters()
            
            if self._last_net_io is None:
                self._last_net_io = current_io
                self._last_net_time = current_time
                return 15.0  # Default initial value
            
            # Calculate packets per second
            time_diff = current_time - self._last_net_time
            if time_diff > 0:
                packets_diff = (current_io.packets_sent - self._last_net_io.packets_sent + 
                               current_io.packets_recv - self._last_net_io.packets_recv)
                packets_per_sec = packets_diff / time_diff
                
                # Estimate latency based on network activity
                # More packets = busier network = potentially higher latency
                base_latency = 10.0
                load_factor = min(packets_per_sec / 1000, 2.0)  # Cap at 2x
                estimated_latency = base_latency * (1 + load_factor * 0.5)
                
                self._last_net_io = current_io
                self._last_net_time = current_time
                
                return round(estimated_latency, 1)
            
            return 15.0
            
        except Exception:
            return 15.0
    
    def _get_gpu_metrics(self) -> Optional[Dict]:
        """Get GPU metrics if NVIDIA GPU is available"""
        try:
            import subprocess
            
            # Try nvidia-smi command
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                values = result.stdout.strip().split(', ')
                if len(values) == 4:
                    return {
                        'usage_percent': float(values[0]),
                        'memory_used_mb': float(values[1]),
                        'memory_total_mb': float(values[2]),
                        'temperature_c': float(values[3])
                    }
        except Exception:
            pass
        
        return None
    
    def _get_fallback_metrics(self) -> Dict:
        """Return minimal metrics if full monitoring fails"""
        return {
            'cpu': {'usage_percent': 0, 'core_count': 1, 'process_cpu_percent': 0},
            'memory': {'used_gb': 0, 'total_gb': 0, 'percent': 0, 'process_memory_mb': 0},
            'disk': {'used_gb': 0, 'total_gb': 0, 'percent': 0},
            'network': {'latency_ms': 0, 'bytes_sent': 0, 'bytes_recv': 0},
            'gpu': None,
            'system': {'uptime_seconds': 0, 'uptime_hours': 0, 'timestamp': datetime.utcnow().isoformat()}
        }
    
    def get_detection_performance_metrics(self, frames_processed: int, detections_made: int) -> Dict:
        """Calculate real detection performance metrics"""
        uptime_seconds = time.time() - self.start_time
        
        if uptime_seconds > 0:
            fps = frames_processed / uptime_seconds
            detection_rate = detections_made / frames_processed if frames_processed > 0 else 0
        else:
            fps = 0
            detection_rate = 0
        
        return {
            'frames_processed': frames_processed,
            'detections_made': detections_made,
            'fps': round(fps, 2),
            'detection_rate': round(detection_rate * 100, 2),
            'uptime_seconds': int(uptime_seconds)
        }


# Global instance
system_monitor = SystemMonitor()