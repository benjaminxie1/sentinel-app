"""
Field Testing and Calibration Suite
Comprehensive testing and threshold optimization for deployment
"""

import logging
import json
import csv
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import cv2
import yaml
from dataclasses import dataclass, asdict

# Import our detection system
import sys
sys.path.append(str(Path(__file__).parent.parent))

from backend.detection.fire_detector import FireDetector, DetectionResult
from backend.detection.rtsp_manager import RTSPManager, CameraConfig
from backend.config.camera_config import CameraConfigManager
from backend.utils.performance_optimizer import FrameProcessor, OptimizationConfig, benchmark_system

@dataclass
class TestScenario:
    """Test scenario definition"""
    name: str
    description: str
    duration_minutes: int
    expected_detections: int
    test_conditions: Dict
    validation_criteria: Dict

@dataclass
class TestResult:
    """Individual test result"""
    scenario_name: str
    camera_id: str
    timestamp: datetime
    detection_result: DetectionResult
    ground_truth: bool  # True if fire actually present
    test_conditions: Dict

@dataclass
class CalibrationReport:
    """Calibration and testing report"""
    test_date: datetime
    system_info: Dict
    scenarios_tested: List[str]
    total_detections: int
    true_positives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    recommended_thresholds: Dict
    performance_metrics: Dict

class FieldTestSuite:
    """Comprehensive field testing system"""
    
    def __init__(self, config_path: str = "config/field_test_config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config = self._load_test_config()
        
        # Testing components
        self.fire_detector = FireDetector()
        self.camera_manager = CameraConfigManager()
        self.test_results: List[TestResult] = []
        
        # Test scenarios
        self.test_scenarios = self._create_test_scenarios()
        
        # Results storage
        self.results_dir = Path("field_test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Testing state
        self.is_testing = False
        self.current_scenario: Optional[TestScenario] = None
        self.test_start_time: Optional[datetime] = None
    
    def _load_test_config(self) -> Dict:
        """Load field test configuration"""
        default_config = {
            'test_duration_hours': 24,
            'calibration_samples': 1000,
            'threshold_ranges': {
                'immediate_alert': [0.90, 0.95, 0.99],
                'review_queue': [0.80, 0.85, 0.90],
                'log_only': [0.65, 0.70, 0.75]
            },
            'environmental_conditions': [
                'normal', 'foggy', 'bright_sun', 'night', 'rain'
            ],
            'validation_cameras': [],
            'ground_truth_file': 'field_test_ground_truth.csv'
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded = yaml.safe_load(f)
                    default_config.update(loaded)
        except Exception as e:
            self.logger.warning(f"Could not load test config: {e}")
        
        return default_config
    
    def _create_test_scenarios(self) -> List[TestScenario]:
        """Create comprehensive test scenarios"""
        scenarios = [
            TestScenario(
                name="baseline_accuracy",
                description="Baseline accuracy test with known fire/no-fire samples",
                duration_minutes=60,
                expected_detections=50,
                test_conditions={'lighting': 'normal', 'weather': 'clear'},
                validation_criteria={'min_accuracy': 0.95, 'max_false_positives': 2}
            ),
            TestScenario(
                name="false_positive_test",
                description="Extended monitoring to detect false positives",
                duration_minutes=180,
                expected_detections=0,
                test_conditions={'lighting': 'variable', 'sources': 'no_fire'},
                validation_criteria={'max_false_positives': 1}
            ),
            TestScenario(
                name="environmental_stress",
                description="Test under challenging environmental conditions",
                duration_minutes=120,
                expected_detections=25,
                test_conditions={'lighting': 'challenging', 'weather': 'variable'},
                validation_criteria={'min_accuracy': 0.85}
            ),
            TestScenario(
                name="rapid_detection",
                description="Test detection speed and latency",
                duration_minutes=30,
                expected_detections=10,
                test_conditions={'fire_size': 'small_to_large', 'timing': 'critical'},
                validation_criteria={'max_detection_time_sec': 10, 'min_accuracy': 0.90}
            ),
            TestScenario(
                name="concurrent_cameras",
                description="Multi-camera performance test",
                duration_minutes=90,
                expected_detections=75,
                test_conditions={'cameras': 'multiple', 'load': 'high'},
                validation_criteria={'min_accuracy': 0.90, 'max_latency_ms': 2000}
            ),
            TestScenario(
                name="threshold_calibration",
                description="Systematic threshold optimization",
                duration_minutes=240,
                expected_detections=200,
                test_conditions={'thresholds': 'variable', 'samples': 'diverse'},
                validation_criteria={'optimal_f1_score': 0.95}
            )
        ]
        
        return scenarios
    
    def run_comprehensive_test_suite(self) -> CalibrationReport:
        """Run complete field testing suite"""
        self.logger.info("Starting comprehensive field testing suite")
        
        # System benchmark
        system_info = benchmark_system()
        self.logger.info(f"System benchmark: {system_info}")
        
        # Prepare cameras for testing
        cameras = self._prepare_test_cameras()
        if not cameras:
            raise ValueError("No cameras available for testing")
        
        # Clear previous results
        self.test_results.clear()
        test_start = datetime.now()
        
        try:
            # Run each test scenario
            for scenario in self.test_scenarios:
                self.logger.info(f"Running scenario: {scenario.name}")
                scenario_results = self._run_test_scenario(scenario, cameras)
                self.test_results.extend(scenario_results)
                
                # Brief pause between scenarios
                time.sleep(30)
            
            # Analyze results and generate report
            report = self._analyze_test_results(test_start, system_info)
            
            # Save detailed results
            self._save_test_results(report)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(report)
            self.logger.info(f"Generated {len(recommendations)} recommendations")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            raise
        finally:
            self._cleanup_test_environment()
    
    def _prepare_test_cameras(self) -> List[str]:
        """Prepare cameras for testing"""
        # Get available cameras
        cameras = self.camera_manager.get_enabled_cameras()
        
        if not cameras:
            self.logger.warning("No cameras configured, using simulation")
            # Setup test cameras with simulation
            test_cameras = [
                CameraConfig("test_cam_1", "simulation://fire_test_1"),
                CameraConfig("test_cam_2", "simulation://fire_test_2"),
                CameraConfig("test_cam_3", "simulation://fire_test_3")
            ]
            
            for cam_config in test_cameras:
                self.fire_detector.add_rtsp_camera(
                    cam_config.camera_id,
                    cam_config.rtsp_url
                )
            
            return [cam.camera_id for cam in test_cameras]
        
        return list(cameras.keys())
    
    def _run_test_scenario(self, scenario: TestScenario, cameras: List[str]) -> List[TestResult]:
        """Run a specific test scenario"""
        self.logger.info(f"Starting scenario: {scenario.name} ({scenario.duration_minutes} minutes)")
        
        # Load ground truth data for this scenario
        ground_truth = self._load_ground_truth(scenario.name)
        
        # Configure detection thresholds for testing
        original_thresholds = self._backup_thresholds()
        
        scenario_results = []
        scenario_start = datetime.now()
        scenario_end = scenario_start + timedelta(minutes=scenario.duration_minutes)
        
        # Set up detection callback
        def detection_callback(camera_id: str, detection_result: DetectionResult):
            # Determine ground truth for this detection
            gt = self._get_ground_truth(camera_id, detection_result.timestamp, ground_truth)
            
            result = TestResult(
                scenario_name=scenario.name,
                camera_id=camera_id,
                timestamp=datetime.fromtimestamp(detection_result.timestamp),
                detection_result=detection_result,
                ground_truth=gt,
                test_conditions=scenario.test_conditions.copy()
            )
            
            scenario_results.append(result)
            
            # Log significant detections
            if detection_result.alert_level in ['P1', 'P2']:
                self.logger.info(f"Scenario {scenario.name} - Detection: {camera_id} "
                               f"{detection_result.alert_level} (conf: {detection_result.max_confidence:.3f}, "
                               f"gt: {gt})")
        
        # Start monitoring
        self.fire_detector.set_detection_callback(detection_callback)
        
        try:
            # Run scenario for specified duration
            while datetime.now() < scenario_end:
                time.sleep(10)
                
                # Log progress
                elapsed = datetime.now() - scenario_start
                remaining = scenario_end - datetime.now()
                
                if elapsed.total_seconds() % 300 == 0:  # Every 5 minutes
                    self.logger.info(f"Scenario {scenario.name} - "
                                   f"Elapsed: {elapsed}, Remaining: {remaining}, "
                                   f"Detections: {len(scenario_results)}")
            
            self.logger.info(f"Completed scenario {scenario.name} - "
                           f"Total detections: {len(scenario_results)}")
            
        finally:
            # Restore original thresholds
            self._restore_thresholds(original_thresholds)
        
        return scenario_results
    
    def _load_ground_truth(self, scenario_name: str) -> Dict:
        """Load ground truth data for scenario"""
        ground_truth_file = self.results_dir / f"ground_truth_{scenario_name}.csv"
        
        if not ground_truth_file.exists():
            self.logger.warning(f"No ground truth file for {scenario_name}")
            return {}
        
        ground_truth = {}
        try:
            with open(ground_truth_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['camera_id']}_{row['timestamp']}"
                    ground_truth[key] = row['fire_present'].lower() == 'true'
        except Exception as e:
            self.logger.error(f"Failed to load ground truth: {e}")
        
        return ground_truth
    
    def _get_ground_truth(self, camera_id: str, timestamp: float, ground_truth: Dict) -> bool:
        """Get ground truth for specific detection"""
        # Look for exact match first
        key = f"{camera_id}_{int(timestamp)}"
        if key in ground_truth:
            return ground_truth[key]
        
        # Look for nearby timestamps (within 30 seconds)
        for gt_key, gt_value in ground_truth.items():
            if camera_id in gt_key:
                try:
                    gt_timestamp = int(gt_key.split('_')[-1])
                    if abs(timestamp - gt_timestamp) <= 30:
                        return gt_value
                except:
                    continue
        
        # Default assumption (no fire present)
        return False
    
    def _backup_thresholds(self) -> Dict:
        """Backup current detection thresholds"""
        return self.fire_detector.config['detection']['thresholds'].copy()
    
    def _restore_thresholds(self, thresholds: Dict):
        """Restore detection thresholds"""
        self.fire_detector.config['detection']['thresholds'].update(thresholds)
    
    def _analyze_test_results(self, test_start: datetime, system_info: Dict) -> CalibrationReport:
        """Analyze test results and generate calibration report"""
        self.logger.info("Analyzing test results...")
        
        # Calculate metrics
        total_detections = len(self.test_results)
        true_positives = sum(1 for r in self.test_results 
                           if r.ground_truth and r.detection_result.alert_level in ['P1', 'P2'])
        false_positives = sum(1 for r in self.test_results 
                            if not r.ground_truth and r.detection_result.alert_level in ['P1', 'P2'])
        false_negatives = sum(1 for r in self.test_results 
                            if r.ground_truth and r.detection_result.alert_level == 'None')
        
        # Calculate performance metrics
        accuracy = (true_positives + (total_detections - false_positives - false_negatives)) / max(total_detections, 1)
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        # Performance analysis
        performance_metrics = self._analyze_performance_metrics()
        
        # Optimal threshold recommendation
        recommended_thresholds = self._optimize_thresholds()
        
        report = CalibrationReport(
            test_date=test_start,
            system_info=system_info,
            scenarios_tested=[s.name for s in self.test_scenarios],
            total_detections=total_detections,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            recommended_thresholds=recommended_thresholds,
            performance_metrics=performance_metrics
        )
        
        self.logger.info(f"Analysis complete - Accuracy: {accuracy:.3f}, "
                        f"Precision: {precision:.3f}, Recall: {recall:.3f}, "
                        f"F1: {f1_score:.3f}")
        
        return report
    
    def _analyze_performance_metrics(self) -> Dict:
        """Analyze system performance metrics"""
        if not self.test_results:
            return {}
        
        # Detection latency analysis
        detection_times = []
        for result in self.test_results:
            if hasattr(result.detection_result, 'processing_time'):
                detection_times.append(result.detection_result.processing_time)
        
        performance = {
            'avg_detection_latency_ms': np.mean(detection_times) if detection_times else 0,
            'max_detection_latency_ms': np.max(detection_times) if detection_times else 0,
            'detection_rate_fps': len(self.test_results) / 3600,  # Assuming 1 hour test
            'total_test_duration_hours': 6  # Approximate total test time
        }
        
        return performance
    
    def _optimize_thresholds(self) -> Dict:
        """Optimize detection thresholds based on test results"""
        self.logger.info("Optimizing detection thresholds...")
        
        # Analyze confidence score distributions
        fire_confidences = [r.detection_result.max_confidence for r in self.test_results if r.ground_truth]
        no_fire_confidences = [r.detection_result.max_confidence for r in self.test_results if not r.ground_truth]
        
        if not fire_confidences or not no_fire_confidences:
            self.logger.warning("Insufficient data for threshold optimization")
            return self.fire_detector.config['detection']['thresholds']
        
        # Calculate optimal thresholds using ROC analysis
        optimal_thresholds = {}
        
        # For immediate alert (P1) - prioritize low false positives
        p1_threshold = np.percentile(fire_confidences, 95)  # Top 5% of fire detections
        optimal_thresholds['immediate_alert'] = min(0.99, max(0.90, p1_threshold))
        
        # For review queue (P2) - balance precision and recall
        p2_threshold = np.percentile(fire_confidences, 80)  # Top 20% of fire detections
        optimal_thresholds['review_queue'] = min(0.90, max(0.75, p2_threshold))
        
        # For logging (P4) - high sensitivity
        p4_threshold = np.percentile(fire_confidences, 60)  # Top 40% of fire detections
        optimal_thresholds['log_only'] = min(0.80, max(0.60, p4_threshold))
        
        self.logger.info(f"Optimized thresholds: {optimal_thresholds}")
        return optimal_thresholds
    
    def _save_test_results(self, report: CalibrationReport):
        """Save detailed test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save calibration report
        report_file = self.results_dir / f"calibration_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Save detailed results CSV
        results_file = self.results_dir / f"test_results_{timestamp}.csv"
        with open(results_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'scenario', 'camera_id', 'timestamp', 'confidence', 
                'alert_level', 'ground_truth', 'correct_detection'
            ])
            
            for result in self.test_results:
                correct = (result.ground_truth and result.detection_result.alert_level in ['P1', 'P2']) or \
                         (not result.ground_truth and result.detection_result.alert_level == 'None')
                
                writer.writerow([
                    result.scenario_name,
                    result.camera_id,
                    result.timestamp.isoformat(),
                    result.detection_result.max_confidence,
                    result.detection_result.alert_level,
                    result.ground_truth,
                    correct
                ])
        
        self.logger.info(f"Test results saved: {report_file}, {results_file}")
    
    def _generate_recommendations(self, report: CalibrationReport) -> List[str]:
        """Generate deployment recommendations"""
        recommendations = []
        
        # Performance recommendations
        if report.accuracy < 0.90:
            recommendations.append("Consider additional training data or model fine-tuning")
        
        if report.false_positives > report.true_positives * 0.1:
            recommendations.append("Increase detection thresholds to reduce false positives")
        
        if report.precision < 0.85:
            recommendations.append("Review camera positioning and environmental factors")
        
        # System recommendations
        if report.performance_metrics.get('avg_detection_latency_ms', 0) > 2000:
            recommendations.append("Consider GPU acceleration or system optimization")
        
        # Threshold recommendations
        if report.recommended_thresholds != self.fire_detector.config['detection']['thresholds']:
            recommendations.append("Update detection thresholds based on calibration results")
        
        return recommendations
    
    def _cleanup_test_environment(self):
        """Clean up testing environment"""
        try:
            self.fire_detector.stop_monitoring()
            self.logger.info("Test environment cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

def create_ground_truth_template():
    """Create template ground truth files for testing"""
    scenarios = ['baseline_accuracy', 'false_positive_test', 'environmental_stress', 
                'rapid_detection', 'concurrent_cameras', 'threshold_calibration']
    
    results_dir = Path("field_test_results")
    results_dir.mkdir(exist_ok=True)
    
    for scenario in scenarios:
        gt_file = results_dir / f"ground_truth_{scenario}.csv"
        
        if not gt_file.exists():
            with open(gt_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['camera_id', 'timestamp', 'fire_present', 'notes'])
                
                # Add some example entries
                base_time = int(time.time())
                for i in range(10):
                    writer.writerow([
                        f'test_cam_{i%3 + 1}',
                        base_time + i * 60,
                        'true' if i % 3 == 0 else 'false',
                        f'Example entry {i+1}'
                    ])
            
            print(f"Created ground truth template: {gt_file}")

if __name__ == "__main__":
    # Test the field testing suite
    logging.basicConfig(level=logging.INFO)
    
    print("Sentinel Fire Detection - Field Testing Suite")
    print("=" * 50)
    
    # Create ground truth templates
    print("Creating ground truth templates...")
    create_ground_truth_template()
    
    # Create test suite
    test_suite = FieldTestSuite()
    
    print(f"Configured {len(test_suite.test_scenarios)} test scenarios:")
    for scenario in test_suite.test_scenarios:
        print(f"  - {scenario.name}: {scenario.description}")
    
    print("\nTo run comprehensive testing:")
    print("  report = test_suite.run_comprehensive_test_suite()")
    print("\nReview and update ground truth files before running tests!")