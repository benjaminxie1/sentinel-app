#!/usr/bin/env python3
"""
Sentinel Fire Detection System - Configuration Validator
Validates system configuration and dependencies
"""

import sys
import logging
import yaml
import json
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
from datetime import datetime
import socket
import urllib.parse

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

class ConfigValidator:
    """Validates Sentinel configuration and system setup"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.warnings = []
        self.info = []
        self.config_files = {}
        
    def validate_all(self) -> Dict:
        """Run complete validation suite"""
        print("🔥 Sentinel Fire Detection System - Configuration Validator")
        print("=" * 60)
        
        # Clear previous results
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Run validations
        print("📋 Validating system configuration...")
        self._validate_python_dependencies()
        self._validate_system_requirements()
        self._validate_config_files()
        self._validate_detection_config()
        self._validate_camera_config()
        self._validate_alert_config()
        self._validate_network_config()
        self._validate_model_setup()
        self._validate_directories()
        self._validate_permissions()
        
        # Generate report
        results = self._generate_report()
        self._print_validation_results()
        
        return results
    
    def _validate_python_dependencies(self):
        """Validate Python dependencies"""
        print("🐍 Checking Python dependencies...")
        
        required_packages = [
            ('torch', '2.0.0'),
            ('torchvision', '0.15.0'),
            ('ultralytics', '8.0.0'),
            ('cv2', '4.8.0'),
            ('numpy', '1.24.0'),
            ('yaml', '6.0'),
            ('requests', '2.31.0'),
            ('psutil', '5.9.0')
        ]
        
        for package_name, min_version in required_packages:
            try:
                if package_name == 'cv2':
                    import cv2 as pkg
                elif package_name == 'yaml':
                    import yaml as pkg
                else:
                    pkg = importlib.import_module(package_name)
                
                # Check version if available
                if hasattr(pkg, '__version__'):
                    version = pkg.__version__
                    self.info.append(f"✅ {package_name}: {version}")
                    
                    # Basic version check (simplified)
                    if self._compare_versions(version, min_version):
                        pass  # Version OK
                    else:
                        self.warnings.append(f"⚠️  {package_name} version {version} may be below recommended {min_version}")
                else:
                    self.info.append(f"✅ {package_name}: installed (version unknown)")
                    
            except ImportError:
                self.errors.append(f"❌ Missing required package: {package_name}")
            except Exception as e:
                self.warnings.append(f"⚠️  Could not check {package_name}: {e}")
    
    def _compare_versions(self, version: str, min_version: str) -> bool:
        """Simple version comparison"""
        try:
            v_parts = [int(x) for x in version.split('.')]
            min_parts = [int(x) for x in min_version.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v_parts), len(min_parts))
            v_parts.extend([0] * (max_len - len(v_parts)))
            min_parts.extend([0] * (max_len - len(min_parts)))
            
            return v_parts >= min_parts
        except:
            return True  # Assume OK if can't parse
    
    def _validate_system_requirements(self):
        """Validate system requirements"""
        print("💻 Checking system requirements...")
        
        try:
            import psutil
            import torch
            
            # Check RAM
            memory = psutil.virtual_memory()
            memory_gb = memory.total / 1024**3
            
            if memory_gb >= 16:
                self.info.append(f"✅ RAM: {memory_gb:.1f}GB (sufficient)")
            elif memory_gb >= 8:
                self.warnings.append(f"⚠️  RAM: {memory_gb:.1f}GB (minimum met, 16GB+ recommended)")
            else:
                self.errors.append(f"❌ RAM: {memory_gb:.1f}GB (insufficient, 8GB minimum)")
            
            # Check CPU
            cpu_count = psutil.cpu_count()
            if cpu_count >= 6:
                self.info.append(f"✅ CPU: {cpu_count} cores (good for multi-camera)")
            elif cpu_count >= 4:
                self.warnings.append(f"⚠️  CPU: {cpu_count} cores (sufficient, 6+ recommended)")
            else:
                self.errors.append(f"❌ CPU: {cpu_count} cores (may struggle with multiple cameras)")
            
            # Check GPU
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                
                self.info.append(f"✅ GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                
                if gpu_memory >= 6:
                    self.info.append("✅ GPU memory sufficient for high-quality detection")
                elif gpu_memory >= 4:
                    self.warnings.append("⚠️  GPU memory adequate (6GB+ recommended for best performance)")
                else:
                    self.warnings.append("⚠️  GPU memory limited (may need to reduce batch sizes)")
            else:
                self.warnings.append("⚠️  No GPU detected (CPU-only mode will be slower)")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / 1024**3
            
            if disk_free_gb >= 100:
                self.info.append(f"✅ Disk space: {disk_free_gb:.1f}GB free")
            elif disk_free_gb >= 50:
                self.warnings.append(f"⚠️  Disk space: {disk_free_gb:.1f}GB free (monitor usage)")
            else:
                self.errors.append(f"❌ Disk space: {disk_free_gb:.1f}GB free (insufficient for logs/models)")
                
        except Exception as e:
            self.errors.append(f"❌ Could not check system requirements: {e}")
    
    def _validate_config_files(self):
        """Validate configuration file structure"""
        print("📄 Checking configuration files...")
        
        config_files = {
            'detection_config.yaml': 'config/detection_config.yaml',
            'cameras.yaml': 'config/cameras.yaml',
            'alerts.yaml': 'config/alerts.yaml',
            'network_config.yaml': 'config/network_config.yaml'
        }
        
        for config_name, config_path in config_files.items():
            file_path = Path(config_path)
            
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    self.config_files[config_name] = config_data
                    self.info.append(f"✅ {config_name}: loaded successfully")
                    
                except yaml.YAMLError as e:
                    self.errors.append(f"❌ {config_name}: invalid YAML syntax - {e}")
                except Exception as e:
                    self.errors.append(f"❌ {config_name}: could not read - {e}")
            else:
                if config_name == 'detection_config.yaml':
                    self.errors.append(f"❌ {config_name}: missing (required)")
                else:
                    self.warnings.append(f"⚠️  {config_name}: missing (will use defaults)")
    
    def _validate_detection_config(self):
        """Validate detection configuration"""
        print("🔍 Checking detection configuration...")
        
        config = self.config_files.get('detection_config.yaml', {})
        
        if not config:
            self.errors.append("❌ Detection configuration missing")
            return
        
        # Check detection section
        detection = config.get('detection', {})
        if not detection:
            self.errors.append("❌ Detection section missing from config")
            return
        
        # Check thresholds
        thresholds = detection.get('thresholds', {})
        required_thresholds = ['immediate_alert', 'review_queue', 'log_only']
        
        for threshold in required_thresholds:
            if threshold not in thresholds:
                self.errors.append(f"❌ Missing threshold: {threshold}")
            else:
                value = thresholds[threshold]
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    self.errors.append(f"❌ Invalid threshold {threshold}: {value} (must be 0.0-1.0)")
                else:
                    self.info.append(f"✅ Threshold {threshold}: {value}")
        
        # Check threshold ordering
        if all(t in thresholds for t in required_thresholds):
            immediate = thresholds['immediate_alert']
            review = thresholds['review_queue']
            log = thresholds['log_only']
            
            if immediate >= review >= log:
                self.info.append("✅ Threshold ordering correct")
            else:
                self.errors.append("❌ Threshold ordering incorrect (should be: immediate ≥ review ≥ log)")
        
        # Check environmental settings
        environmental = detection.get('environmental', {})
        if environmental:
            self.info.append("✅ Environmental adjustments configured")
        else:
            self.warnings.append("⚠️  No environmental adjustments configured")
    
    def _validate_camera_config(self):
        """Validate camera configuration"""
        print("📹 Checking camera configuration...")
        
        config = self.config_files.get('cameras.yaml', {})
        cameras = config.get('cameras', [])
        
        if not cameras:
            self.warnings.append("⚠️  No cameras configured")
            return
        
        for i, camera in enumerate(cameras):
            camera_id = camera.get('camera_id', f'camera_{i}')
            
            # Check required fields
            required_fields = ['camera_id', 'rtsp_url']
            for field in required_fields:
                if field not in camera:
                    self.errors.append(f"❌ Camera {camera_id}: missing {field}")
                elif not camera[field]:
                    self.errors.append(f"❌ Camera {camera_id}: empty {field}")
            
            # Validate RTSP URL
            rtsp_url = camera.get('rtsp_url', '')
            if rtsp_url:
                if self._validate_rtsp_url(rtsp_url):
                    self.info.append(f"✅ Camera {camera_id}: RTSP URL format valid")
                else:
                    self.errors.append(f"❌ Camera {camera_id}: invalid RTSP URL format")
            
            # Check optional settings
            fps = camera.get('fps', 15)
            if not isinstance(fps, int) or fps < 1 or fps > 60:
                self.warnings.append(f"⚠️  Camera {camera_id}: unusual FPS setting {fps}")
            
            enabled = camera.get('enabled', True)
            if not enabled:
                self.info.append(f"ℹ️  Camera {camera_id}: disabled")
        
        self.info.append(f"✅ {len(cameras)} cameras configured")
    
    def _validate_rtsp_url(self, url: str) -> bool:
        """Validate RTSP URL format"""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme == 'rtsp' and parsed.netloc
        except:
            return False
    
    def _validate_alert_config(self):
        """Validate alert configuration"""
        print("📱 Checking alert configuration...")
        
        config = self.config_files.get('alerts.yaml', {})
        alert_config = config.get('alert_config', {})
        
        if not alert_config:
            self.warnings.append("⚠️  No alert configuration found")
            return
        
        # Check SMTP settings
        smtp_fields = ['smtp_server', 'smtp_port', 'smtp_username']
        smtp_configured = all(field in alert_config for field in smtp_fields)
        
        if smtp_configured:
            self.info.append("✅ SMTP email configuration present")
            
            # Validate SMTP port
            smtp_port = alert_config.get('smtp_port')
            if isinstance(smtp_port, int) and 1 <= smtp_port <= 65535:
                self.info.append(f"✅ SMTP port: {smtp_port}")
            else:
                self.errors.append(f"❌ Invalid SMTP port: {smtp_port}")
        else:
            self.warnings.append("⚠️  SMTP configuration incomplete")
        
        # Check SMS providers
        sms_providers = alert_config.get('sms_providers', [])
        if sms_providers:
            self.info.append(f"✅ {len(sms_providers)} SMS provider(s) configured")
            
            for provider in sms_providers:
                name = provider.get('name', 'unknown')
                if provider.get('api_url') and provider.get('account_sid'):
                    self.info.append(f"✅ SMS provider {name}: configured")
                else:
                    self.warnings.append(f"⚠️  SMS provider {name}: incomplete configuration")
        else:
            self.warnings.append("⚠️  No SMS providers configured")
        
        # Check recipients
        recipients = config.get('recipients', [])
        if recipients:
            email_count = sum(1 for r in recipients if r.get('email'))
            phone_count = sum(1 for r in recipients if r.get('phone'))
            
            self.info.append(f"✅ {len(recipients)} alert recipients configured")
            self.info.append(f"   📧 {email_count} with email, 📱 {phone_count} with SMS")
        else:
            self.errors.append("❌ No alert recipients configured")
    
    def _validate_network_config(self):
        """Validate network configuration"""
        print("🌐 Checking network configuration...")
        
        config = self.config_files.get('network_config.yaml', {})
        
        if not config:
            self.warnings.append("⚠️  No network configuration (will use defaults)")
            return
        
        # Check test targets
        test_targets = config.get('test_targets', [])
        if test_targets:
            valid_targets = []
            for target in test_targets:
                if self._validate_ip_or_hostname(target):
                    valid_targets.append(target)
                else:
                    self.warnings.append(f"⚠️  Invalid network test target: {target}")
            
            if valid_targets:
                self.info.append(f"✅ {len(valid_targets)} network test targets configured")
            else:
                self.errors.append("❌ No valid network test targets")
        
        # Check intervals
        monitor_interval = config.get('monitor_interval', 30)
        if isinstance(monitor_interval, int) and 10 <= monitor_interval <= 300:
            self.info.append(f"✅ Network monitor interval: {monitor_interval}s")
        else:
            self.warnings.append(f"⚠️  Unusual monitor interval: {monitor_interval}s")
    
    def _validate_ip_or_hostname(self, target: str) -> bool:
        """Validate IP address or hostname"""
        try:
            socket.inet_aton(target)  # IPv4
            return True
        except:
            try:
                socket.getaddrinfo(target, None)  # Hostname
                return True
            except:
                return False
    
    def _validate_model_setup(self):
        """Validate model setup"""
        print("🤖 Checking model setup...")
        
        try:
            # Check if models directory exists
            models_dir = Path("models")
            if models_dir.exists():
                self.info.append("✅ Models directory exists")
                
                # Check for existing models
                model_files = list(models_dir.glob("*.pt"))
                if model_files:
                    self.info.append(f"✅ Found {len(model_files)} model file(s)")
                    for model_file in model_files:
                        size_mb = model_file.stat().st_size / 1024**2
                        self.info.append(f"   📦 {model_file.name}: {size_mb:.1f}MB")
                else:
                    self.warnings.append("⚠️  No model files found (will download automatically)")
            else:
                self.warnings.append("⚠️  Models directory missing (will be created)")
            
            # Test model loading
            try:
                from detection.fire_model_manager import FireModelManager
                manager = FireModelManager()
                models = manager.list_available_models()
                
                self.info.append(f"✅ FireModelManager: {len(models)} models available")
                
                # Test model creation (without download)
                available_models = [name for name, info in models.items() if info['downloaded']]
                if available_models:
                    self.info.append(f"✅ {len(available_models)} models ready for use")
                else:
                    self.warnings.append("⚠️  No models downloaded yet")
                    
            except Exception as e:
                self.errors.append(f"❌ Model manager test failed: {e}")
                
        except Exception as e:
            self.errors.append(f"❌ Model validation failed: {e}")
    
    def _validate_directories(self):
        """Validate required directories"""
        print("📁 Checking directories...")
        
        required_dirs = [
            'config',
            'logs',
            'data',
            'models',
            'backend',
            'backend/detection',
            'backend/config',
            'backend/alerts',
            'backend/utils'
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                self.info.append(f"✅ Directory: {dir_path}")
            else:
                if dir_path in ['logs', 'data', 'models']:
                    self.warnings.append(f"⚠️  Directory missing: {dir_path} (will be created)")
                else:
                    self.errors.append(f"❌ Required directory missing: {dir_path}")
    
    def _validate_permissions(self):
        """Validate file permissions"""
        print("🔐 Checking permissions...")
        
        try:
            # Check if we can write to key directories
            test_dirs = ['logs', 'data', 'models', 'config']
            
            for dir_name in test_dirs:
                dir_path = Path(dir_name)
                
                if dir_path.exists():
                    # Test write permission
                    test_file = dir_path / ".permission_test"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                        self.info.append(f"✅ Write permission: {dir_name}")
                    except Exception as e:
                        self.errors.append(f"❌ No write permission: {dir_name} - {e}")
                else:
                    # Try to create directory
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.info.append(f"✅ Created directory: {dir_name}")
                    except Exception as e:
                        self.errors.append(f"❌ Cannot create directory: {dir_name} - {e}")
                        
        except Exception as e:
            self.warnings.append(f"⚠️  Could not fully check permissions: {e}")
    
    def _generate_report(self) -> Dict:
        """Generate validation report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_info': len(self.info),
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'config_files': list(self.config_files.keys()),
            'validation_passed': len(self.errors) == 0
        }
    
    def _print_validation_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)
        
        # Summary
        print(f"✅ Info: {len(self.info)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        # Print errors first (most important)
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        # Print warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Print info if verbose or no errors/warnings
        if not self.errors and not self.warnings:
            print(f"\n✅ ALL CHECKS PASSED ({len(self.info)}):")
            for info in self.info:
                print(f"   {info}")
        
        # Overall status
        print(f"\n🎯 Overall Status:")
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                print("   ✅ EXCELLENT - System fully configured and ready")
            else:
                print("   ⚠️  GOOD - System ready with minor recommendations")
        else:
            if len(self.errors) <= 2:
                print("   🔧 NEEDS ATTENTION - Fix errors before production use")
            else:
                print("   ❌ NOT READY - Significant configuration issues")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        if len(self.errors) > 0:
            print("   1. Fix configuration errors listed above")
            print("   2. Re-run validation: python scripts/validate_config.py")
            print("   3. Run tests: python -m pytest tests/")
        else:
            print("   1. Run performance benchmark: python scripts/benchmark.py")
            print("   2. Run tests: python -m pytest tests/")
            print("   3. Begin system deployment")


def main():
    """Main validation execution"""
    parser = argparse.ArgumentParser(description='Sentinel Configuration Validator')
    parser.add_argument('--verbose', action='store_true', help='Show all validation details')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--save', type=str, help='Save results to file')
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Run validation
    validator = ConfigValidator()
    results = validator.validate_all()
    
    # Handle output format
    if args.json:
        print(json.dumps(results, indent=2))
    
    # Save results if requested
    if args.save:
        try:
            with open(args.save, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.save}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    # Exit with appropriate code
    if results['validation_passed']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()