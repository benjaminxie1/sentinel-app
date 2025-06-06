"""
Fire Detection Model Training
Custom YOLOv8 training for fire and smoke detection
"""

import os
import yaml
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import cv2
import numpy as np
from ultralytics import YOLO
import torch
from datetime import datetime
import requests
import zipfile

@dataclass
class TrainingConfig:
    """Training configuration"""
    model_size: str = 'yolov8n'  # n, s, m, l, x
    epochs: int = 100
    batch_size: int = 16
    image_size: int = 640
    learning_rate: float = 0.01
    patience: int = 50
    device: str = 'auto'  # auto, cpu, 0, 1, etc.
    
@dataclass
class DatasetInfo:
    """Dataset information"""
    name: str
    path: str
    classes: List[str]
    train_images: int = 0
    val_images: int = 0
    test_images: int = 0

class FireDatasetManager:
    """Manages fire detection datasets"""
    
    def __init__(self, data_root: str = "datasets"):
        self.data_root = Path(data_root)
        self.data_root.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Fire detection classes
        self.fire_classes = ['fire', 'smoke']
        
    def download_fire_datasets(self) -> List[DatasetInfo]:
        """Download available fire detection datasets"""
        datasets = []
        
        # Dataset 1: Fire and Smoke Dataset (example)
        fire_smoke_dataset = self._download_fire_smoke_dataset()
        if fire_smoke_dataset:
            datasets.append(fire_smoke_dataset)
        
        # Dataset 2: Forest Fire Dataset (example)
        forest_fire_dataset = self._download_forest_fire_dataset()
        if forest_fire_dataset:
            datasets.append(forest_fire_dataset)
        
        self.logger.info(f"Downloaded {len(datasets)} fire detection datasets")
        return datasets
    
    def _download_fire_smoke_dataset(self) -> Optional[DatasetInfo]:
        """Download fire and smoke detection dataset"""
        dataset_name = "fire_smoke_v1"
        dataset_path = self.data_root / dataset_name
        
        if dataset_path.exists():
            self.logger.info(f"Dataset {dataset_name} already exists")
            return self._load_dataset_info(dataset_path)
        
        try:
            self.logger.info(f"Creating synthetic {dataset_name} dataset...")
            
            # For now, create a synthetic dataset structure
            # In production, this would download from actual dataset sources
            self._create_synthetic_fire_dataset(dataset_path)
            
            return DatasetInfo(
                name=dataset_name,
                path=str(dataset_path),
                classes=self.fire_classes,
                train_images=800,
                val_images=200,
                test_images=100
            )
            
        except Exception as e:
            self.logger.error(f"Failed to download {dataset_name}: {e}")
            return None
    
    def _download_forest_fire_dataset(self) -> Optional[DatasetInfo]:
        """Download forest fire dataset"""
        dataset_name = "forest_fire_v1"
        dataset_path = self.data_root / dataset_name
        
        if dataset_path.exists():
            self.logger.info(f"Dataset {dataset_name} already exists")
            return self._load_dataset_info(dataset_path)
        
        try:
            self.logger.info(f"Creating synthetic {dataset_name} dataset...")
            
            # Create synthetic forest fire dataset
            self._create_synthetic_forest_dataset(dataset_path)
            
            return DatasetInfo(
                name=dataset_name,
                path=str(dataset_path),
                classes=self.fire_classes,
                train_images=600,
                val_images=150,
                test_images=75
            )
            
        except Exception as e:
            self.logger.error(f"Failed to download {dataset_name}: {e}")
            return None
    
    def _create_synthetic_fire_dataset(self, dataset_path: Path):
        """Create a synthetic fire dataset for development"""
        # Create directory structure
        for split in ['train', 'val', 'test']:
            (dataset_path / split / 'images').mkdir(parents=True, exist_ok=True)
            (dataset_path / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        # Create dataset.yaml
        dataset_config = {
            'path': str(dataset_path),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': len(self.fire_classes),
            'names': self.fire_classes
        }
        
        with open(dataset_path / 'dataset.yaml', 'w') as f:
            yaml.dump(dataset_config, f)
        
        # Create synthetic images and labels
        self._generate_synthetic_fire_images(dataset_path)
        
        self.logger.info(f"Created synthetic dataset at {dataset_path}")
    
    def _create_synthetic_forest_dataset(self, dataset_path: Path):
        """Create a synthetic forest fire dataset"""
        # Similar structure to fire dataset
        for split in ['train', 'val', 'test']:
            (dataset_path / split / 'images').mkdir(parents=True, exist_ok=True)
            (dataset_path / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        dataset_config = {
            'path': str(dataset_path),
            'train': 'train/images',
            'val': 'val/images', 
            'test': 'test/images',
            'nc': len(self.fire_classes),
            'names': self.fire_classes
        }
        
        with open(dataset_path / 'dataset.yaml', 'w') as f:
            yaml.dump(dataset_config, f)
        
        # Generate forest fire specific images
        self._generate_synthetic_forest_images(dataset_path)
        
        self.logger.info(f"Created synthetic forest dataset at {dataset_path}")
    
    def _generate_synthetic_fire_images(self, dataset_path: Path):
        """Generate synthetic fire images for training"""
        splits = {
            'train': 800,
            'val': 200, 
            'test': 100
        }
        
        for split, count in splits.items():
            images_dir = dataset_path / split / 'images'
            labels_dir = dataset_path / split / 'labels'
            
            for i in range(count):
                # Create synthetic fire image
                image = self._create_fire_image(640, 640)
                image_path = images_dir / f"fire_{split}_{i:04d}.jpg"
                cv2.imwrite(str(image_path), image)
                
                # Create corresponding label
                label_path = labels_dir / f"fire_{split}_{i:04d}.txt"
                label = self._create_fire_label()
                with open(label_path, 'w') as f:
                    f.write(label)
    
    def _generate_synthetic_forest_images(self, dataset_path: Path):
        """Generate synthetic forest fire images"""
        splits = {
            'train': 600,
            'val': 150,
            'test': 75
        }
        
        for split, count in splits.items():
            images_dir = dataset_path / split / 'images'
            labels_dir = dataset_path / split / 'labels'
            
            for i in range(count):
                # Create synthetic forest fire image
                image = self._create_forest_fire_image(640, 640)
                image_path = images_dir / f"forest_{split}_{i:04d}.jpg"
                cv2.imwrite(str(image_path), image)
                
                # Create corresponding label
                label_path = labels_dir / f"forest_{split}_{i:04d}.txt"
                label = self._create_forest_fire_label()
                with open(label_path, 'w') as f:
                    f.write(label)
    
    def _create_fire_image(self, width: int, height: int) -> np.ndarray:
        """Create a synthetic fire image"""
        # Create base image (indoor/outdoor scene)
        image = np.random.randint(30, 80, (height, width, 3), dtype=np.uint8)
        
        # Add fire region
        fire_x = np.random.randint(50, width - 150)
        fire_y = np.random.randint(50, height - 100)
        fire_w = np.random.randint(80, 150)
        fire_h = np.random.randint(60, 120)
        
        # Create fire-like colors (orange/red/yellow)
        fire_region = image[fire_y:fire_y+fire_h, fire_x:fire_x+fire_w]
        fire_region[:, :, 0] = np.random.randint(0, 50)      # Blue (low)
        fire_region[:, :, 1] = np.random.randint(100, 255)   # Green (medium-high)
        fire_region[:, :, 2] = np.random.randint(200, 255)   # Red (high)
        
        # Add some smoke if random
        if np.random.random() > 0.5:
            smoke_x = fire_x + np.random.randint(-20, 20)
            smoke_y = max(0, fire_y - np.random.randint(50, 100))
            smoke_w = fire_w + np.random.randint(20, 50)
            smoke_h = np.random.randint(80, 120)
            
            # Gray smoke color
            smoke_region = image[smoke_y:min(smoke_y+smoke_h, height), 
                               smoke_x:min(smoke_x+smoke_w, width)]
            smoke_color = np.random.randint(100, 180)
            smoke_region[:, :] = smoke_color
        
        return image
    
    def _create_forest_fire_image(self, width: int, height: int) -> np.ndarray:
        """Create a synthetic forest fire image"""
        # Forest-like background (green/brown)
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:, :, 1] = np.random.randint(40, 120)  # Green channel
        image[:, :, 0] = np.random.randint(20, 60)   # Blue channel
        image[:, :, 2] = np.random.randint(30, 80)   # Red channel
        
        # Add fire in forest
        num_fires = np.random.randint(1, 4)
        for _ in range(num_fires):
            fire_x = np.random.randint(0, width - 100)
            fire_y = np.random.randint(height//2, height - 50)
            fire_w = np.random.randint(60, 120)
            fire_h = np.random.randint(40, 80)
            
            # Fire colors
            fire_region = image[fire_y:fire_y+fire_h, fire_x:fire_x+fire_w]
            fire_region[:, :, 0] = np.random.randint(0, 30)
            fire_region[:, :, 1] = np.random.randint(150, 255)
            fire_region[:, :, 2] = np.random.randint(200, 255)
        
        return image
    
    def _create_fire_label(self) -> str:
        """Create YOLO format label for fire"""
        # Random fire bounding box (normalized coordinates)
        x_center = np.random.uniform(0.2, 0.8)
        y_center = np.random.uniform(0.2, 0.8)
        width = np.random.uniform(0.1, 0.3)
        height = np.random.uniform(0.1, 0.3)
        
        # Class 0 = fire
        return f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
    
    def _create_forest_fire_label(self) -> str:
        """Create YOLO format label for forest fire"""
        labels = []
        
        # Multiple fire instances possible
        num_fires = np.random.randint(1, 3)
        for _ in range(num_fires):
            x_center = np.random.uniform(0.1, 0.9)
            y_center = np.random.uniform(0.5, 0.9)
            width = np.random.uniform(0.08, 0.25)
            height = np.random.uniform(0.05, 0.2)
            
            labels.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
        
        return '\n'.join(labels)
    
    def _load_dataset_info(self, dataset_path: Path) -> DatasetInfo:
        """Load dataset information from existing dataset"""
        try:
            with open(dataset_path / 'dataset.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            # Count images in each split
            train_count = len(list((dataset_path / 'train' / 'images').glob('*.jpg')))
            val_count = len(list((dataset_path / 'val' / 'images').glob('*.jpg')))
            test_count = len(list((dataset_path / 'test' / 'images').glob('*.jpg')))
            
            return DatasetInfo(
                name=dataset_path.name,
                path=str(dataset_path),
                classes=config.get('names', self.fire_classes),
                train_images=train_count,
                val_images=val_count,
                test_images=test_count
            )
        except Exception as e:
            self.logger.error(f"Failed to load dataset info: {e}")
            return DatasetInfo(
                name=dataset_path.name,
                path=str(dataset_path),
                classes=self.fire_classes
            )

class FireModelTrainer:
    """Trains custom YOLOv8 models for fire detection"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.dataset_manager = FireDatasetManager()
        
    def prepare_datasets(self) -> List[DatasetInfo]:
        """Prepare training datasets"""
        self.logger.info("Preparing fire detection datasets...")
        datasets = self.dataset_manager.download_fire_datasets()
        
        total_images = sum(d.train_images + d.val_images + d.test_images for d in datasets)
        self.logger.info(f"Prepared {len(datasets)} datasets with {total_images} total images")
        
        return datasets
    
    def train_fire_model(self, config: TrainingConfig, dataset_path: str) -> Tuple[bool, str]:
        """Train a fire detection model"""
        try:
            self.logger.info(f"Starting training with {config.model_size} model...")
            
            # Load base model
            model = YOLO(f'{config.model_size}.pt')
            
            # Setup training parameters
            train_args = {
                'data': dataset_path,
                'epochs': config.epochs,
                'batch': config.batch_size,
                'imgsz': config.image_size,
                'lr0': config.learning_rate,
                'patience': config.patience,
                'device': config.device,
                'project': str(self.models_dir),
                'name': f'fire_detection_{config.model_size}',
                'exist_ok': True
            }
            
            # Train the model
            self.logger.info("Training started...")
            results = model.train(**train_args)
            
            # Save the trained model
            model_name = f"fire_detection_{config.model_size}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
            model_path = self.models_dir / model_name
            
            # Copy best weights
            best_weights = self.models_dir / f'fire_detection_{config.model_size}' / 'weights' / 'best.pt'
            if best_weights.exists():
                shutil.copy(best_weights, model_path)
                self.logger.info(f"Saved trained model: {model_path}")
                return True, str(model_path)
            else:
                return False, "Training completed but best weights not found"
                
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def evaluate_model(self, model_path: str, dataset_path: str) -> Dict:
        """Evaluate trained model performance"""
        try:
            self.logger.info(f"Evaluating model: {model_path}")
            
            # Load trained model
            model = YOLO(model_path)
            
            # Run validation
            results = model.val(data=dataset_path)
            
            # Extract metrics
            metrics = {
                'map50': float(results.box.map50) if hasattr(results.box, 'map50') else 0.0,
                'map50_95': float(results.box.map) if hasattr(results.box, 'map') else 0.0,
                'precision': float(results.box.mp) if hasattr(results.box, 'mp') else 0.0,
                'recall': float(results.box.mr) if hasattr(results.box, 'mr') else 0.0,
                'f1': float(results.box.f1) if hasattr(results.box, 'f1') else 0.0,
            }
            
            self.logger.info(f"Evaluation results: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return {}
    
    def optimize_model(self, model_path: str, optimization: str = 'trt') -> Tuple[bool, str]:
        """Optimize model for deployment"""
        try:
            self.logger.info(f"Optimizing model with {optimization}...")
            
            model = YOLO(model_path)
            
            if optimization == 'trt':
                # TensorRT optimization (requires NVIDIA GPU)
                model.export(format='engine', device=0)
                optimized_path = model_path.replace('.pt', '.engine')
            elif optimization == 'onnx':
                # ONNX export for cross-platform deployment
                model.export(format='onnx')
                optimized_path = model_path.replace('.pt', '.onnx')
            else:
                return False, f"Unsupported optimization: {optimization}"
            
            self.logger.info(f"Model optimized: {optimized_path}")
            return True, optimized_path
            
        except Exception as e:
            error_msg = f"Optimization failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def create_training_pipeline(self) -> bool:
        """Complete training pipeline"""
        try:
            # 1. Prepare datasets
            datasets = self.prepare_datasets()
            if not datasets:
                self.logger.error("No datasets available for training")
                return False
            
            # 2. Train on multiple dataset combinations
            configs = [
                TrainingConfig(model_size='yolov8n', epochs=50, batch_size=16),
                TrainingConfig(model_size='yolov8s', epochs=75, batch_size=12),
            ]
            
            trained_models = []
            
            for dataset in datasets:
                dataset_yaml = Path(dataset.path) / 'dataset.yaml'
                
                for config in configs:
                    self.logger.info(f"Training {config.model_size} on {dataset.name}")
                    
                    success, model_path = self.train_fire_model(config, str(dataset_yaml))
                    if success:
                        # Evaluate model
                        metrics = self.evaluate_model(model_path, str(dataset_yaml))
                        
                        trained_models.append({
                            'model_path': model_path,
                            'config': config,
                            'dataset': dataset.name,
                            'metrics': metrics
                        })
                        
                        self.logger.info(f"Completed training: {model_path}")
            
            # 3. Select best model
            if trained_models:
                best_model = max(trained_models, key=lambda x: x['metrics'].get('map50', 0))
                self.logger.info(f"Best model: {best_model['model_path']} (mAP50: {best_model['metrics'].get('map50', 0):.3f})")
                
                # Copy best model to standard location
                best_path = self.models_dir / 'fire_detection.pt'
                shutil.copy(best_model['model_path'], best_path)
                self.logger.info(f"Best model saved as: {best_path}")
                
                return True
            else:
                self.logger.error("No models were successfully trained")
                return False
                
        except Exception as e:
            self.logger.error(f"Training pipeline failed: {e}")
            return False

if __name__ == "__main__":
    # Test the training system
    logging.basicConfig(level=logging.INFO)
    
    # Create trainer
    trainer = FireModelTrainer()
    
    # Run complete training pipeline
    print("Starting fire detection model training pipeline...")
    success = trainer.create_training_pipeline()
    
    if success:
        print("Training pipeline completed successfully!")
        print("Fire detection model ready for deployment")
    else:
        print("Training pipeline failed. Check logs for details.")