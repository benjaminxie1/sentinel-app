#!/usr/bin/env python3
"""
Sentinel Fire Detection System - Performance Benchmark
Comprehensive performance testing and optimization recommendations
"""

import time
import logging
import statistics
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import cv2
import psutil
import torch
from datetime import datetime
import argparse

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from detection.fire_detector import FireDetector
from detection.fire_model_manager import FireModelManager
from utils.performance_optimizer import benchmark_system, FrameProcessor, OptimizationConfig

class SentinelBenchmark:
    """Comprehensive benchmark suite for Sentinel Fire Detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results = {}
        self.system_info = {}
        
    def run_full_benchmark(self) -> Dict:
        """Run complete benchmark suite"""
        print("🔥 Sentinel Fire Detection System - Performance Benchmark")
        print("=" * 60)
        
        try:
            # System information
            self.system_info = self._collect_system_info()
            self._print_system_info()
            
            # Core benchmarks
            print("\n📊 Running Performance Benchmarks...")
            self.results['system_benchmark'] = self._run_system_benchmark()
            self.results['model_benchmark'] = self._run_model_benchmark()
            self.results['detection_benchmark'] = self._run_detection_benchmark()
            self.results['memory_benchmark'] = self._run_memory_benchmark()
            self.results['multi_camera_benchmark'] = self._run_multi_camera_benchmark()
            
            # Analysis and recommendations
            self.results['analysis'] = self._analyze_results()
            self.results['recommendations'] = self._generate_recommendations()
            
            # Save results
            self._save_results()
            
            # Print summary
            self._print_summary()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"Benchmark failed: {e}")
            traceback.print_exc()
            return {'error': str(e)}
    
    def _collect_system_info(self) -> Dict:
        """Collect system information"""
        info = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'percent': psutil.cpu_percent(interval=1)
            },
            'memory': {
                'total_gb': psutil.virtual_memory().total / 1024**3,
                'available_gb': psutil.virtual_memory().available / 1024**3,
                'percent': psutil.virtual_memory().percent
            },
            'gpu': {
                'available': torch.cuda.is_available(),
                'count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'current_device': torch.cuda.current_device() if torch.cuda.is_available() else None,
                'memory_gb': torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0,
                'name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            },
            'python_version': sys.version,
            'torch_version': torch.__version__,
            'opencv_version': cv2.__version__
        }
        
        return info
    
    def _print_system_info(self):
        """Print system information"""
        print("\n💻 System Information:")
        print(f"  CPU: {self.system_info['cpu']['count']} cores @ {self.system_info['cpu']['percent']:.1f}% usage")
        print(f"  Memory: {self.system_info['memory']['total_gb']:.1f}GB total, {self.system_info['memory']['available_gb']:.1f}GB available")
        
        if self.system_info['gpu']['available']:
            print(f"  GPU: {self.system_info['gpu']['name']} ({self.system_info['gpu']['memory_gb']:.1f}GB)")
        else:
            print("  GPU: Not available (CPU-only mode)")
        
        print(f"  PyTorch: {self.system_info['torch_version']}, OpenCV: {self.system_info['opencv_version']}")
    
    def _run_system_benchmark(self) -> Dict:
        """Run system-level benchmark"""
        print("\n🔧 System Benchmark...")
        
        # Use the existing benchmark function
        system_bench = benchmark_system()
        
        # Add our own tests
        results = system_bench.copy()
        
        # CPU benchmark
        print("  Testing CPU performance...")
        cpu_times = []
        for i in range(5):
            start_time = time.time()
            # CPU-intensive task
            arr = np.random.rand(1000, 1000)
            np.linalg.inv(arr @ arr.T + np.eye(1000))
            cpu_times.append((time.time() - start_time) * 1000)
        
        results['cpu_benchmark_ms'] = {
            'min': min(cpu_times),
            'max': max(cpu_times),
            'mean': statistics.mean(cpu_times),
            'median': statistics.median(cpu_times)
        }
        
        # Memory benchmark
        print("  Testing memory performance...")
        memory_start = psutil.virtual_memory().available
        
        # Allocate and free memory
        big_array = np.zeros((1000, 1000, 10), dtype=np.float32)
        memory_after_alloc = psutil.virtual_memory().available
        del big_array
        memory_after_free = psutil.virtual_memory().available
        
        results['memory_benchmark'] = {
            'allocation_impact_mb': (memory_start - memory_after_alloc) / 1024**2,
            'deallocation_recovery_mb': (memory_after_free - memory_after_alloc) / 1024**2
        }
        
        print(f"    CPU Performance: {results['cpu_benchmark_ms']['mean']:.1f}ms avg")
        print(f"    Memory Impact: {results['memory_benchmark']['allocation_impact_mb']:.1f}MB")
        
        return results
    
    def _run_model_benchmark(self) -> Dict:
        """Benchmark model loading and inference"""
        print("\n🤖 Model Benchmark...")
        
        results = {}
        
        try:
            # Test model manager
            print("  Testing FireModelManager...")
            manager = FireModelManager()
            
            model_load_start = time.time()
            fire_model = manager.create_fire_detection_model('fire_yolov8n')
            model_load_time = time.time() - model_load_start
            
            results['model_loading'] = {
                'load_time_seconds': model_load_time,
                'model_type': 'fire_yolov8n',
                'success': True
            }
            
            # Test inference speed
            print("  Testing inference speed...")
            test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
            
            # Warm-up
            for _ in range(3):
                _ = fire_model(test_frame, verbose=False)
            
            # Timed inference
            inference_times = []
            for i in range(10):
                start_time = time.time()
                results_pred = fire_model(test_frame, verbose=False)
                inference_time = (time.time() - start_time) * 1000
                inference_times.append(inference_time)
            
            results['inference_performance'] = {
                'min_ms': min(inference_times),
                'max_ms': max(inference_times),
                'mean_ms': statistics.mean(inference_times),
                'median_ms': statistics.median(inference_times),
                'fps_theoretical': 1000 / statistics.mean(inference_times)
            }
            
            print(f"    Model Load Time: {model_load_time:.2f}s")
            print(f"    Inference Speed: {statistics.mean(inference_times):.1f}ms avg ({1000/statistics.mean(inference_times):.1f} FPS)")
            
        except Exception as e:
            results['error'] = str(e)
            print(f"    ❌ Model benchmark failed: {e}")
        
        return results
    
    def _run_detection_benchmark(self) -> Dict:
        """Benchmark fire detection system"""
        print("\n🔥 Fire Detection Benchmark...")
        
        results = {}
        
        try:
            # Initialize detector
            print("  Initializing FireDetector...")
            detector_init_start = time.time()
            detector = FireDetector()
            detector_init_time = time.time() - detector_init_start
            
            results['detector_initialization'] = {
                'init_time_seconds': detector_init_time,
                'success': True
            }
            
            # Test detection on various frame sizes
            frame_sizes = [(320, 240), (640, 480), (1280, 720), (1920, 1080)]
            detection_results = {}
            
            for width, height in frame_sizes:
                print(f"  Testing {width}x{height} frames...")
                
                # Create test frame
                test_frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
                
                # Add some fire-like regions for more realistic testing
                fire_region_h = min(100, height // 4)
                fire_region_w = min(100, width // 4)
                test_frame[50:50+fire_region_h, 50:50+fire_region_w, 2] = 255  # Red
                test_frame[50:50+fire_region_h, 50:50+fire_region_w, 1] = 165  # Orange
                test_frame[50:50+fire_region_h, 50:50+fire_region_w, 0] = 0    # No blue
                
                # Time detection
                detection_times = []
                for i in range(5):
                    start_time = time.time()
                    result = detector.detect_fire(test_frame)
                    detection_time = (time.time() - start_time) * 1000
                    detection_times.append(detection_time)
                
                detection_results[f"{width}x{height}"] = {
                    'min_ms': min(detection_times),
                    'max_ms': max(detection_times),
                    'mean_ms': statistics.mean(detection_times),
                    'fps_theoretical': 1000 / statistics.mean(detection_times),
                    'meets_target': statistics.mean(detection_times) < 2000  # 2 second target
                }
                
                print(f"    {width}x{height}: {statistics.mean(detection_times):.1f}ms avg")
            
            results['detection_performance'] = detection_results
            
            # Test detection accuracy with known patterns
            print("  Testing detection accuracy...")
            accuracy_results = self._test_detection_accuracy(detector)
            results['detection_accuracy'] = accuracy_results
            
        except Exception as e:
            results['error'] = str(e)
            print(f"    ❌ Detection benchmark failed: {e}")
        
        return results
    
    def _test_detection_accuracy(self, detector) -> Dict:
        """Test detection accuracy with synthetic fire patterns"""
        # Create frames with known fire/no-fire patterns
        test_cases = []
        
        # Fire-like frame
        fire_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        fire_frame[100:200, 100:200, 2] = 255  # Red region
        fire_frame[100:200, 100:200, 1] = 165  # Orange
        fire_frame[100:200, 100:200, 0] = 0
        test_cases.append(('fire', fire_frame))
        
        # Normal frame
        normal_frame = np.random.randint(50, 150, (480, 640, 3), dtype=np.uint8)
        test_cases.append(('normal', normal_frame))
        
        # Bright light frame (potential false positive)
        bright_frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        bright_frame[200:300, 200:300] = 255  # Very bright region
        test_cases.append(('bright', bright_frame))
        
        results = {}
        for case_name, frame in test_cases:
            detection_result = detector.detect_fire(frame)
            results[case_name] = {
                'max_confidence': detection_result.max_confidence,
                'alert_level': detection_result.alert_level,
                'detection_count': len(detection_result.detections)
            }
        
        return results
    
    def _run_memory_benchmark(self) -> Dict:
        """Benchmark memory usage"""
        print("\n💾 Memory Benchmark...")
        
        results = {}
        
        try:
            # Baseline memory
            baseline_memory = psutil.virtual_memory().used / 1024**2
            
            # Test memory usage during detection
            detector = FireDetector()
            after_init_memory = psutil.virtual_memory().used / 1024**2
            
            # Process multiple frames
            frames = [np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8) for _ in range(10)]
            
            memory_usage = []
            for frame in frames:
                result = detector.detect_fire(frame)
                current_memory = psutil.virtual_memory().used / 1024**2
                memory_usage.append(current_memory)
            
            results = {
                'baseline_memory_mb': baseline_memory,
                'after_init_mb': after_init_memory,
                'init_overhead_mb': after_init_memory - baseline_memory,
                'peak_memory_mb': max(memory_usage),
                'memory_growth_mb': max(memory_usage) - after_init_memory,
                'memory_stable': max(memory_usage) - min(memory_usage[-5:]) < 50  # Stable if < 50MB variation
            }
            
            print(f"    Initialization Overhead: {results['init_overhead_mb']:.1f}MB")
            print(f"    Peak Memory Usage: {results['peak_memory_mb']:.1f}MB")
            print(f"    Memory Growth: {results['memory_growth_mb']:.1f}MB")
            
        except Exception as e:
            results['error'] = str(e)
            print(f"    ❌ Memory benchmark failed: {e}")
        
        return results
    
    def _run_multi_camera_benchmark(self) -> Dict:
        """Benchmark multi-camera performance"""
        print("\n📹 Multi-Camera Benchmark...")
        
        results = {}
        
        try:
            # Test different camera counts
            camera_counts = [1, 2, 4, 6, 8, 10]
            
            for cam_count in camera_counts:
                print(f"  Testing {cam_count} cameras...")
                
                # Create multiple test frames
                frames = []
                for i in range(cam_count):
                    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                    frames.append(frame)
                
                # Time processing all frames
                detector = FireDetector()
                
                start_time = time.time()
                detection_results = []
                for frame in frames:
                    result = detector.detect_fire(frame)
                    detection_results.append(result)
                
                total_time = time.time() - start_time
                
                results[f"{cam_count}_cameras"] = {
                    'total_time_seconds': total_time,
                    'time_per_camera_ms': (total_time / cam_count) * 1000,
                    'fps_per_camera': cam_count / total_time,
                    'meets_realtime': total_time < cam_count * 0.1  # 10 FPS per camera target
                }
                
                print(f"    {cam_count} cameras: {total_time:.2f}s total, {(total_time/cam_count)*1000:.1f}ms per camera")
        
        except Exception as e:
            results['error'] = str(e)
            print(f"    ❌ Multi-camera benchmark failed: {e}")
        
        return results
    
    def _analyze_results(self) -> Dict:
        """Analyze benchmark results"""
        analysis = {
            'overall_performance': 'unknown',
            'bottlenecks': [],
            'strengths': [],
            'readiness_score': 0.0
        }
        
        try:
            scores = []
            
            # Analyze system performance
            if 'system_benchmark' in self.results:
                sys_bench = self.results['system_benchmark']
                if sys_bench.get('recommended_workers', 0) >= 4:
                    analysis['strengths'].append('Good CPU for multi-threading')
                    scores.append(0.8)
                else:
                    analysis['bottlenecks'].append('Limited CPU cores')
                    scores.append(0.4)
            
            # Analyze GPU availability
            if self.system_info['gpu']['available']:
                analysis['strengths'].append('GPU acceleration available')
                scores.append(0.9)
            else:
                analysis['bottlenecks'].append('No GPU - CPU-only processing')
                scores.append(0.3)
            
            # Analyze detection performance
            if 'detection_benchmark' in self.results and 'detection_performance' in self.results['detection_benchmark']:
                det_perf = self.results['detection_benchmark']['detection_performance']
                
                # Check if meets 2-second target for common resolutions
                hd_performance = det_perf.get('1280x720', {})
                if hd_performance.get('meets_target', False):
                    analysis['strengths'].append('Meets detection latency targets')
                    scores.append(0.8)
                else:
                    analysis['bottlenecks'].append('Detection latency too high')
                    scores.append(0.4)
            
            # Analyze memory usage
            if 'memory_benchmark' in self.results:
                mem_bench = self.results['memory_benchmark']
                if mem_bench.get('memory_stable', False) and mem_bench.get('memory_growth_mb', 0) < 100:
                    analysis['strengths'].append('Stable memory usage')
                    scores.append(0.7)
                else:
                    analysis['bottlenecks'].append('High or unstable memory usage')
                    scores.append(0.3)
            
            # Calculate overall score
            if scores:
                analysis['readiness_score'] = statistics.mean(scores)
            
            # Determine overall performance
            if analysis['readiness_score'] >= 0.8:
                analysis['overall_performance'] = 'excellent'
            elif analysis['readiness_score'] >= 0.6:
                analysis['overall_performance'] = 'good'
            elif analysis['readiness_score'] >= 0.4:
                analysis['overall_performance'] = 'fair'
            else:
                analysis['overall_performance'] = 'poor'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            # GPU recommendations
            if not self.system_info['gpu']['available']:
                recommendations.append("🚨 CRITICAL: Install NVIDIA GPU (RTX 3060+) for real-time processing")
            elif self.system_info['gpu']['memory_gb'] < 4:
                recommendations.append("⚠️  Consider GPU with more VRAM (8GB+) for better performance")
            
            # Memory recommendations
            if self.system_info['memory']['total_gb'] < 16:
                recommendations.append("⚠️  Upgrade to 16GB+ RAM for stable multi-camera operation")
            
            # CPU recommendations
            if self.system_info['cpu']['count'] < 6:
                recommendations.append("💡 Consider CPU with more cores for multi-camera processing")
            
            # Detection performance recommendations
            if 'detection_benchmark' in self.results:
                det_results = self.results['detection_benchmark']
                if 'detection_performance' in det_results:
                    hd_perf = det_results['detection_performance'].get('1280x720', {})
                    if hd_perf.get('mean_ms', 0) > 1000:
                        recommendations.append("🔧 Enable GPU acceleration or reduce camera resolution")
            
            # Multi-camera recommendations
            if 'multi_camera_benchmark' in self.results:
                multi_cam = self.results['multi_camera_benchmark']
                poor_performance_counts = [
                    count for count, data in multi_cam.items() 
                    if isinstance(data, dict) and not data.get('meets_realtime', True)
                ]
                
                if poor_performance_counts:
                    recommendations.append(f"📹 System may struggle with {max([int(c.split('_')[0]) for c in poor_performance_counts])}+ cameras")
            
            # Memory recommendations
            if 'memory_benchmark' in self.results:
                mem_results = self.results['memory_benchmark']
                if mem_results.get('memory_growth_mb', 0) > 200:
                    recommendations.append("💾 Monitor memory usage - possible memory leak detected")
            
            # General recommendations
            if len(recommendations) == 0:
                recommendations.append("✅ System appears well-configured for fire detection")
            
            recommendations.append("🔧 Run 'python scripts/validate_config.py' to check configuration")
            recommendations.append("🧪 Run 'python -m pytest tests/' to verify system functionality")
        
        except Exception as e:
            recommendations.append(f"❌ Could not generate recommendations: {e}")
        
        return recommendations
    
    def _save_results(self):
        """Save benchmark results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = Path(f"benchmark_results_{timestamp}.json")
            
            # Combine system info and results
            full_results = {
                'system_info': self.system_info,
                'benchmark_results': self.results,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(results_file, 'w') as f:
                json.dump(full_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    def _print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        # Overall assessment
        analysis = self.results.get('analysis', {})
        score = analysis.get('readiness_score', 0)
        performance = analysis.get('overall_performance', 'unknown')
        
        print(f"🎯 Overall Performance: {performance.upper()}")
        print(f"📈 Readiness Score: {score:.1%}")
        
        # Strengths
        strengths = analysis.get('strengths', [])
        if strengths:
            print(f"\n✅ Strengths:")
            for strength in strengths:
                print(f"   • {strength}")
        
        # Bottlenecks
        bottlenecks = analysis.get('bottlenecks', [])
        if bottlenecks:
            print(f"\n⚠️  Bottlenecks:")
            for bottleneck in bottlenecks:
                print(f"   • {bottleneck}")
        
        # Recommendations
        recommendations = self.results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Production readiness
        print(f"\n🏭 Production Readiness:")
        if score >= 0.8:
            print("   ✅ READY - System meets production requirements")
        elif score >= 0.6:
            print("   ⚠️  MOSTLY READY - Minor optimizations recommended")
        elif score >= 0.4:
            print("   🔧 NEEDS WORK - Significant improvements required")
        else:
            print("   ❌ NOT READY - Major hardware/software upgrades needed")


def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(description='Sentinel Fire Detection Benchmark')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark (reduced test iterations)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run benchmark
    benchmark = SentinelBenchmark()
    
    if args.quick:
        print("🏃 Running quick benchmark mode...")
        # Could implement reduced iterations here
    
    results = benchmark.run_full_benchmark()
    
    # Exit with appropriate code
    if 'error' in results:
        sys.exit(1)
    
    analysis = results.get('analysis', {})
    score = analysis.get('readiness_score', 0)
    
    if score >= 0.6:
        sys.exit(0)  # Success
    else:
        sys.exit(2)  # Performance issues


if __name__ == "__main__":
    main()