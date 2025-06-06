"""
Performance Optimization System
Optimizes multi-camera detection processing and system performance
"""

import logging
import threading
import time
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Optional, Callable, Tuple
import psutil
import cv2
import numpy as np
import torch
from queue import Queue, Empty
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    camera_id: str
    fps_actual: float
    fps_target: float
    detection_latency_ms: float
    queue_depth: int
    cpu_usage: float
    gpu_usage: float
    memory_usage_mb: float
    dropped_frames: int
    timestamp: float

@dataclass
class OptimizationConfig:
    """Performance optimization configuration"""
    max_workers: int = 4
    frame_buffer_size: int = 3
    detection_batch_size: int = 4
    gpu_memory_fraction: float = 0.8
    enable_frame_skipping: bool = True
    quality_vs_speed_ratio: float = 0.7  # 0=speed, 1=quality
    adaptive_processing: bool = True

class FrameProcessor:
    """Optimized frame processing for multiple cameras"""
    
    def __init__(self, detection_model, config: OptimizationConfig):
        self.detection_model = detection_model
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Processing queues
        self.input_queue = Queue(maxsize=config.frame_buffer_size * 10)
        self.output_queue = Queue(maxsize=100)
        
        # Worker threads
        self.workers = []
        self.is_processing = False
        
        # Performance tracking
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.frame_counters: Dict[str, int] = {}
        self.last_fps_update = time.time()
        
        # GPU optimization
        self._optimize_gpu_settings()
    
    def _optimize_gpu_settings(self):
        """Optimize GPU settings for performance"""
        if torch.cuda.is_available():
            # Set memory fraction
            torch.cuda.set_per_process_memory_fraction(self.config.gpu_memory_fraction)
            
            # Enable cudNN benchmark for consistent input sizes
            torch.backends.cudnn.benchmark = True
            
            # Optimize for inference
            torch.backends.cudnn.deterministic = False
            
            self.logger.info(f"GPU optimization enabled - Memory fraction: {self.config.gpu_memory_fraction}")
        else:
            self.logger.warning("No GPU available - using CPU inference")
    
    def start_processing(self):
        """Start multi-threaded frame processing"""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        # Create worker threads
        for i in range(self.config.max_workers):
            worker = threading.Thread(target=self._processing_worker, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)
        
        # Start metrics collection
        metrics_thread = threading.Thread(target=self._metrics_collector, daemon=True)
        metrics_thread.start()
        self.workers.append(metrics_thread)
        
        self.logger.info(f"Started {self.config.max_workers} processing workers")
    
    def stop_processing(self):
        """Stop frame processing"""
        self.is_processing = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        self.logger.info("Stopped frame processing")
    
    def submit_frame(self, camera_id: str, frame: np.ndarray) -> bool:
        """Submit frame for processing"""
        try:
            # Check if queue is full (frame dropping)
            if self.input_queue.full():
                if self.config.enable_frame_skipping:
                    # Drop oldest frame
                    try:
                        self.input_queue.get_nowait()
                    except Empty:
                        pass
                else:
                    return False
            
            # Add frame to queue
            frame_data = {
                'camera_id': camera_id,
                'frame': frame,
                'timestamp': time.time()
            }
            
            self.input_queue.put(frame_data, timeout=0.1)
            
            # Update frame counter
            self.frame_counters[camera_id] = self.frame_counters.get(camera_id, 0) + 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit frame from {camera_id}: {e}")
            return False
    
    def get_result(self, timeout: float = 0.1) -> Optional[Dict]:
        """Get detection result"""
        try:
            return self.output_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def _processing_worker(self, worker_id: int):
        """Worker thread for frame processing"""
        self.logger.info(f"Started processing worker {worker_id}")
        
        batch_frames = []
        batch_metadata = []
        
        while self.is_processing:
            try:
                # Collect frames for batch processing
                while len(batch_frames) < self.config.detection_batch_size and self.is_processing:
                    try:
                        frame_data = self.input_queue.get(timeout=0.5)
                        batch_frames.append(frame_data['frame'])
                        batch_metadata.append({
                            'camera_id': frame_data['camera_id'],
                            'timestamp': frame_data['timestamp']
                        })
                    except Empty:
                        break
                
                if batch_frames:
                    # Process batch
                    start_time = time.time()
                    results = self._process_frame_batch(batch_frames)
                    processing_time = (time.time() - start_time) * 1000  # ms
                    
                    # Send results
                    for i, result in enumerate(results):
                        if i < len(batch_metadata):
                            output_data = {
                                'camera_id': batch_metadata[i]['camera_id'],
                                'timestamp': batch_metadata[i]['timestamp'],
                                'detection_result': result,
                                'processing_time_ms': processing_time / len(results)
                            }
                            
                            try:
                                self.output_queue.put(output_data, timeout=0.1)
                            except:
                                pass  # Queue full, drop result
                    
                    # Clear batch
                    batch_frames.clear()
                    batch_metadata.clear()
                
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Processing worker {worker_id} stopped")
    
    def _process_frame_batch(self, frames: List[np.ndarray]) -> List:
        """Process batch of frames for detection"""
        try:
            # Optimize frame sizes for faster processing
            processed_frames = []
            target_size = 640 if self.config.quality_vs_speed_ratio < 0.5 else 832
            
            for frame in frames:
                # Resize frame for faster processing if needed
                h, w = frame.shape[:2]
                if max(h, w) > target_size:
                    scale = target_size / max(h, w)
                    new_w, new_h = int(w * scale), int(h * scale)
                    frame = cv2.resize(frame, (new_w, new_h))
                
                processed_frames.append(frame)
            
            # Run detection on batch
            if len(processed_frames) == 1:
                # Single frame
                result = self.detection_model.detect_fire(processed_frames[0])
                return [result]
            else:
                # Batch processing
                results = []
                for frame in processed_frames:
                    result = self.detection_model.detect_fire(frame)
                    results.append(result)
                return results
                
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            return [None] * len(frames)
    
    def _metrics_collector(self):
        """Collect performance metrics"""
        while self.is_processing:
            try:
                current_time = time.time()
                
                # Update FPS metrics every 5 seconds
                if current_time - self.last_fps_update >= 5.0:
                    elapsed = current_time - self.last_fps_update
                    
                    for camera_id, frame_count in self.frame_counters.items():
                        fps = frame_count / elapsed
                        
                        # Get system metrics
                        cpu_percent = psutil.cpu_percent()
                        memory_info = psutil.virtual_memory()
                        gpu_usage = self._get_gpu_usage()
                        
                        # Create metrics object
                        metrics = PerformanceMetrics(
                            camera_id=camera_id,
                            fps_actual=fps,
                            fps_target=15.0,  # Default target
                            detection_latency_ms=0.0,  # Will be updated by results
                            queue_depth=self.input_queue.qsize(),
                            cpu_usage=cpu_percent,
                            gpu_usage=gpu_usage,
                            memory_usage_mb=memory_info.used / 1024 / 1024,
                            dropped_frames=0,  # TODO: Implement frame drop tracking
                            timestamp=current_time
                        )
                        
                        self.metrics[camera_id] = metrics
                    
                    # Reset counters
                    self.frame_counters.clear()
                    self.last_fps_update = current_time
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                time.sleep(5)
    
    def _get_gpu_usage(self) -> float:
        """Get GPU utilization percentage"""
        try:
            if torch.cuda.is_available():
                return torch.cuda.utilization()
            return 0.0
        except:
            return 0.0
    
    def get_performance_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get current performance metrics"""
        return self.metrics.copy()

class SystemOptimizer:
    """System-level performance optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_priority = None
    
    def optimize_system_settings(self):
        """Optimize system settings for real-time processing"""
        try:
            # Set high process priority
            process = psutil.Process()
            self.original_priority = process.nice()
            
            if psutil.WINDOWS:
                process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                process.nice(-10)  # Higher priority on Unix
            
            self.logger.info("Set high process priority")
            
            # Optimize thread settings
            if hasattr(threading, 'current_thread'):
                thread = threading.current_thread()
                if hasattr(thread, 'daemon'):
                    thread.daemon = False
            
            # GPU-specific optimizations
            if torch.cuda.is_available():
                # Clear GPU cache
                torch.cuda.empty_cache()
                
                # Set optimal GPU settings
                torch.cuda.set_device(0)  # Use first GPU
                
                self.logger.info("Applied GPU optimizations")
            
        except Exception as e:
            self.logger.warning(f"Could not apply all system optimizations: {e}")
    
    def restore_system_settings(self):
        """Restore original system settings"""
        try:
            if self.original_priority is not None:
                process = psutil.Process()
                process.nice(self.original_priority)
                self.logger.info("Restored original process priority")
        except Exception as e:
            self.logger.warning(f"Could not restore system settings: {e}")

class AdaptiveProcessor:
    """Adaptive processing that adjusts based on system load"""
    
    def __init__(self, frame_processor: FrameProcessor):
        self.frame_processor = frame_processor
        self.logger = logging.getLogger(__name__)
        
        # Adaptive settings
        self.max_cpu_usage = 80.0
        self.max_gpu_usage = 90.0
        self.target_latency_ms = 100.0
        
        # Monitoring
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """Start adaptive monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._adaptive_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Started adaptive processing monitor")
    
    def stop_monitoring(self):
        """Stop adaptive monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped adaptive processing monitor")
    
    def _adaptive_loop(self):
        """Adaptive monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self.frame_processor.get_performance_metrics()
                
                if metrics:
                    # Analyze system load
                    avg_cpu = sum(m.cpu_usage for m in metrics.values()) / len(metrics)
                    avg_gpu = sum(m.gpu_usage for m in metrics.values()) / len(metrics)
                    avg_latency = sum(m.detection_latency_ms for m in metrics.values()) / len(metrics)
                    
                    # Adjust processing parameters
                    if avg_cpu > self.max_cpu_usage or avg_gpu > self.max_gpu_usage:
                        self._reduce_processing_load()
                    elif avg_latency > self.target_latency_ms:
                        self._optimize_for_latency()
                    elif avg_cpu < 50 and avg_gpu < 50:
                        self._increase_processing_quality()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Adaptive monitoring error: {e}")
                time.sleep(30)
    
    def _reduce_processing_load(self):
        """Reduce processing load when system is overloaded"""
        config = self.frame_processor.config
        
        # Reduce batch size
        if config.detection_batch_size > 1:
            config.detection_batch_size = max(1, config.detection_batch_size - 1)
            self.logger.info(f"Reduced batch size to {config.detection_batch_size}")
        
        # Enable more aggressive frame skipping
        if not config.enable_frame_skipping:
            config.enable_frame_skipping = True
            self.logger.info("Enabled frame skipping")
        
        # Reduce quality for speed
        if config.quality_vs_speed_ratio > 0.3:
            config.quality_vs_speed_ratio = max(0.3, config.quality_vs_speed_ratio - 0.1)
            self.logger.info(f"Reduced quality ratio to {config.quality_vs_speed_ratio}")
    
    def _optimize_for_latency(self):
        """Optimize for lower latency"""
        config = self.frame_processor.config
        
        # Reduce buffer sizes
        if config.frame_buffer_size > 1:
            config.frame_buffer_size = max(1, config.frame_buffer_size - 1)
            self.logger.info(f"Reduced buffer size to {config.frame_buffer_size}")
        
        # Prioritize speed
        if config.quality_vs_speed_ratio > 0.5:
            config.quality_vs_speed_ratio = 0.5
            self.logger.info("Optimized for speed over quality")
    
    def _increase_processing_quality(self):
        """Increase quality when system has spare capacity"""
        config = self.frame_processor.config
        
        # Increase batch size for efficiency
        if config.detection_batch_size < 8:
            config.detection_batch_size = min(8, config.detection_batch_size + 1)
            self.logger.info(f"Increased batch size to {config.detection_batch_size}")
        
        # Improve quality
        if config.quality_vs_speed_ratio < 0.8:
            config.quality_vs_speed_ratio = min(0.8, config.quality_vs_speed_ratio + 0.1)
            self.logger.info(f"Improved quality ratio to {config.quality_vs_speed_ratio}")

def benchmark_system() -> Dict:
    """Benchmark system performance for optimal settings"""
    import tempfile
    
    logger = logging.getLogger(__name__)
    logger.info("Running system performance benchmark...")
    
    results = {
        'cpu_cores': psutil.cpu_count(),
        'memory_gb': psutil.virtual_memory().total / 1024**3,
        'gpu_available': torch.cuda.is_available(),
        'recommended_workers': 4,
        'recommended_batch_size': 4,
        'recommended_quality_ratio': 0.7
    }
    
    if torch.cuda.is_available():
        # GPU benchmark
        try:
            device = torch.device('cuda:0')
            
            # Test GPU memory
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            results['gpu_memory_gb'] = gpu_memory
            
            # Simple GPU performance test
            start_time = time.time()
            test_tensor = torch.randn(1000, 1000, device=device)
            torch.mm(test_tensor, test_tensor)
            torch.cuda.synchronize()
            gpu_time = time.time() - start_time
            
            results['gpu_performance_score'] = 1.0 / gpu_time
            
            # Adjust recommendations based on GPU
            if gpu_memory > 6:
                results['recommended_batch_size'] = 8
                results['recommended_quality_ratio'] = 0.8
            
        except Exception as e:
            logger.warning(f"GPU benchmark failed: {e}")
    
    # CPU benchmark
    try:
        start_time = time.time()
        # Simple CPU test
        test_array = np.random.rand(1000, 1000)
        np.dot(test_array, test_array)
        cpu_time = time.time() - start_time
        
        results['cpu_performance_score'] = 1.0 / cpu_time
        
        # Adjust worker count based on CPU
        cpu_cores = results['cpu_cores']
        if cpu_cores >= 8:
            results['recommended_workers'] = min(8, cpu_cores)
        else:
            results['recommended_workers'] = max(2, cpu_cores - 1)
        
    except Exception as e:
        logger.warning(f"CPU benchmark failed: {e}")
    
    logger.info(f"Benchmark completed: {results}")
    return results

if __name__ == "__main__":
    # Test performance optimization
    logging.basicConfig(level=logging.INFO)
    
    # Run benchmark
    benchmark_results = benchmark_system()
    print("Benchmark Results:")
    for key, value in benchmark_results.items():
        print(f"  {key}: {value}")
    
    print("\nRecommended settings:")
    print(f"  Workers: {benchmark_results['recommended_workers']}")
    print(f"  Batch size: {benchmark_results['recommended_batch_size']}")
    print(f"  Quality ratio: {benchmark_results['recommended_quality_ratio']}")