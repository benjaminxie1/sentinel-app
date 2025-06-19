"""
Fire Detection Model Manager
Downloads and manages pre-trained fire detection YOLOv8 models
"""

import os
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple
import torch
from ultralytics import YOLO
import hashlib

class FireModelManager:
    """Manages fire detection models with automatic downloading"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Base YOLOv8 models (NOT fire-specific - need training!)
        self.available_models = {
            'yolov8n_base': {
                'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
                'description': '⚠️  YOLOv8 Nano - GENERAL PURPOSE (needs fire training)',
                'size': '6.2MB',
                'fire_trained': False,
                'coco_classes': True
            },
            'yolov8s_base': {
                'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt', 
                'description': '⚠️  YOLOv8 Small - GENERAL PURPOSE (needs fire training)',
                'size': '21.5MB',
                'fire_trained': False,
                'coco_classes': True
            },
            'yolov8m_base': {
                'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt',
                'description': '⚠️  YOLOv8 Medium - GENERAL PURPOSE (needs fire training)',
                'size': '49.7MB',
                'fire_trained': False,
                'coco_classes': True
            }
        }
        
        # Fire-specific classes we'll retrain for
        self.fire_classes = ['fire', 'smoke']
        
    def download_model(self, model_name: str = 'fire_yolov8n') -> str:
        """Download a fire detection model"""
        if model_name not in self.available_models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.available_models.keys())}")
        
        model_info = self.available_models[model_name]
        model_path = self.models_dir / f"{model_name}.pt"
        
        # Check if already downloaded and valid
        if model_path.exists():
            if self._verify_model(model_path, model_info.get('sha256')):
                self.logger.info(f"Model {model_name} already exists and verified")
                return str(model_path)
            else:
                self.logger.warning(f"Model {model_name} exists but verification failed, re-downloading")
        
        # Download model
        self.logger.info(f"Downloading {model_name} ({model_info['size']})...")
        try:
            response = requests.get(model_info['url'], stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify download (skip SHA256 check for now since we don't have real hashes)
            if self._verify_model(model_path, None):  # Skip SHA256 verification
                self.logger.info(f"Successfully downloaded and verified {model_name}")
                return str(model_path)
            else:
                raise ValueError("Downloaded model failed verification")
                
        except Exception as e:
            if model_path.exists():
                model_path.unlink()  # Remove corrupted file
            raise RuntimeError(f"Failed to download {model_name}: {e}")
    
    def _verify_model(self, model_path: Path, expected_sha256: Optional[str] = None) -> bool:
        """Verify model file integrity"""
        try:
            # Check if file is a valid PyTorch model
            torch.load(model_path, map_location='cpu')
            
            # Check file size (should be reasonable)
            size_mb = model_path.stat().st_size / (1024 * 1024)
            if size_mb < 1 or size_mb > 1000:  # 1MB to 1GB range
                return False
            
            # Optional SHA256 verification
            if expected_sha256:
                with open(model_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                return file_hash == expected_sha256
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model verification failed: {e}")
            return False
    
    def get_best_model(self, prefer_accuracy: bool = False) -> str:
        """Get the best available base model (WARNING: needs fire training!)"""
        self.logger.warning("⚠️  Loading BASE YOLOv8 model - NOT fire-trained!")
        self.logger.warning("⚠️  This model detects COCO objects, not fire/smoke!")
        self.logger.warning("⚠️  You need to provide fire training data and retrain!")
        
        if prefer_accuracy:
            # Try medium, then small, then nano
            for model_name in ['yolov8m_base', 'yolov8s_base', 'yolov8n_base']:
                try:
                    return self.download_model(model_name)
                except Exception as e:
                    self.logger.warning(f"Failed to get {model_name}: {e}")
        else:
            # Try nano first for speed, then others
            for model_name in ['yolov8n_base', 'yolov8s_base', 'yolov8m_base']:
                try:
                    return self.download_model(model_name)
                except Exception as e:
                    self.logger.warning(f"Failed to get {model_name}: {e}")
        
        raise RuntimeError("Failed to download any base YOLOv8 model")
    
    def list_available_models(self) -> dict:
        """List all available models with their status"""
        status = {}
        for model_name, info in self.available_models.items():
            model_path = self.models_dir / f"{model_name}.pt"
            status[model_name] = {
                'description': info['description'],
                'size': info['size'],
                'downloaded': model_path.exists(),
                'verified': model_path.exists() and self._verify_model(model_path),
                'path': str(model_path) if model_path.exists() else None
            }
        return status
    
    def create_fire_detection_model(self, base_model: str = 'yolov8n_base') -> YOLO:
        """Create a fire detection model ready for training or inference"""
        model_path = self.download_model(base_model)
        
        # Load the model
        model = YOLO(model_path)
        
        # Modify for fire detection classes
        # Note: For now we use the base model, but this is where we'd load
        # a fire-specific trained model in production
        
        self.logger.info(f"Created fire detection model from {base_model}")
        return model
    
    def simulate_fire_training(self, model: YOLO) -> dict:
        """Simulate training results for testing (until real training data available)"""
        # This simulates what training results would look like
        training_results = {
            'epochs': 100,
            'final_map50': 0.892,
            'final_map50_95': 0.654,
            'precision': 0.876,
            'recall': 0.843,
            'f1_score': 0.859,
            'loss': 0.234,
            'training_time_hours': 2.5,
            'model_size_mb': 6.2,
            'inference_speed_ms': 12.3
        }
        
        self.logger.info("Simulated fire detection training completed")
        return training_results

def create_fire_model_config() -> dict:
    """Create configuration for fire detection model"""
    return {
        'classes': ['fire', 'smoke'],
        'num_classes': 2,
        'model_architecture': 'yolov8n',
        'image_size': 640,
        'confidence_threshold': 0.25,
        'iou_threshold': 0.45,
        'max_detections': 100,
        'fire_detection_thresholds': {
            'immediate_alert': 0.95,
            'review_queue': 0.85, 
            'log_only': 0.70
        }
    }

if __name__ == "__main__":
    # Test the fire model manager
    logging.basicConfig(level=logging.INFO)
    
    manager = FireModelManager()
    
    print("Available fire detection models:")
    models = manager.list_available_models()
    for name, info in models.items():
        status = "✓ Downloaded" if info['downloaded'] else "○ Available"
        print(f"  {status} {name}: {info['description']} ({info['size']})")
    
    print("\nTesting model download...")
    try:
        model_path = manager.get_best_model(prefer_accuracy=False)
        print(f"Successfully downloaded: {model_path}")
        
        # Test creating fire detection model
        fire_model = manager.create_fire_detection_model()
        print(f"Fire detection model created: {type(fire_model)}")
        
        # Simulate training results
        results = manager.simulate_fire_training(fire_model)
        print(f"Simulated training results: mAP50={results['final_map50']:.3f}")
        
    except Exception as e:
        print(f"Error: {e}")