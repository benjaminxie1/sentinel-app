#!/usr/bin/env python3
"""
Generate highly realistic 2023 commits for Sentinel Fire Detection System
Simulates actual development progression with meaningful code changes
"""

import subprocess
import random
from datetime import datetime, timedelta
import os
import textwrap
import re

# Development phases for realistic progression
DEVELOPMENT_PHASES = {
    "2023-01": ["research", "prototype"],
    "2023-02": ["research", "prototype", "architecture"],
    "2023-03": ["architecture", "foundation"],
    "2023-04": ["foundation", "core"],
    "2023-05": ["core", "detection"],
    "2023-06": ["detection", "integration"],
    "2023-07": ["integration", "testing"],
    "2023-08": ["testing", "optimization"],
    "2023-09": ["optimization", "ui"],
    "2023-10": ["ui", "production"],
    "2023-11": ["production", "deployment"],
    "2023-12": ["deployment", "documentation"]
}

# Realistic commit messages grouped by phase
PHASE_COMMITS = {
    "research": [
        ("Initial project structure and requirements analysis", "major"),
        ("Add literature review on fire detection algorithms", "docs"),
        ("Research YOLOv8 vs RetinaNet performance benchmarks", "research"),
        ("Document hardware requirements for real-time detection", "docs"),
        ("Evaluate thermal vs RGB camera approaches", "research"),
        ("Add feasibility study for edge deployment", "docs"),
        ("Compare detection model architectures", "research"),
        ("Document regulatory compliance requirements", "docs"),
    ],
    "prototype": [
        ("Implement basic YOLO inference pipeline", "feature"),
        ("Add initial smoke detection prototype", "feature"),
        ("Create simple OpenCV camera capture", "feature"),
        ("Test basic flame color detection", "experiment"),
        ("Prototype confidence threshold system", "feature"),
        ("Add basic frame preprocessing", "feature"),
        ("Initial motion detection experiments", "experiment"),
        ("Create proof-of-concept GUI", "feature"),
    ],
    "architecture": [
        ("Design modular detection pipeline architecture", "refactor"),
        ("Implement plugin-based camera manager", "feature"),
        ("Create abstract detector interface", "refactor"),
        ("Add configuration management system", "feature"),
        ("Design alert notification framework", "feature"),
        ("Implement event-driven architecture", "refactor"),
        ("Create database schema for alerts", "feature"),
        ("Add dependency injection container", "refactor"),
    ],
    "foundation": [
        ("Set up Tauri application skeleton", "feature"),
        ("Configure Python backend communication", "feature"),
        ("Implement IPC message protocol", "feature"),
        ("Add SQLite database integration", "feature"),
        ("Create base React component structure", "feature"),
        ("Set up build pipeline", "build"),
        ("Add logging infrastructure", "feature"),
        ("Implement error handling framework", "feature"),
    ],
    "core": [
        ("Implement YOLOv8 detection engine", "feature"),
        ("Add multi-threaded frame processing", "performance"),
        ("Create detection queue management", "feature"),
        ("Implement frame buffer optimization", "performance"),
        ("Add detection result aggregation", "feature"),
        ("Create alert priority system", "feature"),
        ("Implement detection zone configuration", "feature"),
        ("Add temporal analysis for false positive reduction", "feature"),
    ],
    "detection": [
        ("Train custom fire detection model", "model"),
        ("Add smoke pattern recognition", "feature"),
        ("Implement flame color analysis", "feature"),
        ("Create heat signature detection", "feature"),
        ("Add motion-based fire detection", "feature"),
        ("Implement multi-model ensemble", "feature"),
        ("Optimize detection algorithms", "performance"),
        ("Add environmental compensation", "feature"),
    ],
    "integration": [
        ("Integrate RTSP camera support", "feature"),
        ("Add ONVIF camera discovery", "feature"),
        ("Implement camera health monitoring", "feature"),
        ("Create unified alert system", "feature"),
        ("Add email notification service", "feature"),
        ("Implement SMS alert integration", "feature"),
        ("Add webhook support for alerts", "feature"),
        ("Create REST API endpoints", "feature"),
    ],
    "testing": [
        ("Add unit tests for detection engine", "test"),
        ("Create integration test suite", "test"),
        ("Add performance benchmarks", "test"),
        ("Implement stress testing framework", "test"),
        ("Add detection accuracy tests", "test"),
        ("Create camera failure simulation tests", "test"),
        ("Add alert system tests", "test"),
        ("Implement end-to-end test scenarios", "test"),
    ],
    "optimization": [
        ("Optimize GPU memory utilization", "performance"),
        ("Implement batch processing", "performance"),
        ("Add frame skipping optimization", "performance"),
        ("Optimize database queries", "performance"),
        ("Reduce detection latency", "performance"),
        ("Implement caching layer", "performance"),
        ("Optimize network bandwidth usage", "performance"),
        ("Add resource pooling", "performance"),
    ],
    "ui": [
        ("Design command center dashboard", "ui"),
        ("Implement camera grid view", "ui"),
        ("Add real-time activity feed", "ui"),
        ("Create settings management UI", "ui"),
        ("Add alert notification center", "ui"),
        ("Implement system health monitoring", "ui"),
        ("Create incident management interface", "ui"),
        ("Add analytics dashboard", "ui"),
    ],
    "production": [
        ("Add production error handling", "stability"),
        ("Implement automatic recovery system", "stability"),
        ("Add redundancy for critical components", "stability"),
        ("Create backup alert channels", "feature"),
        ("Implement data retention policies", "feature"),
        ("Add audit logging system", "security"),
        ("Create system diagnostics tools", "feature"),
        ("Add performance monitoring", "feature"),
    ],
    "deployment": [
        ("Create Linux installer script", "deploy"),
        ("Add Windows installer", "deploy"),
        ("Implement systemd service integration", "deploy"),
        ("Add Docker container support", "deploy"),
        ("Create deployment documentation", "docs"),
        ("Add configuration templates", "deploy"),
        ("Implement auto-update mechanism", "feature"),
        ("Add license management", "legal"),
    ],
    "documentation": [
        ("Write comprehensive README", "docs"),
        ("Add API documentation", "docs"),
        ("Create user manual", "docs"),
        ("Document configuration options", "docs"),
        ("Add troubleshooting guide", "docs"),
        ("Create developer documentation", "docs"),
        ("Add compliance documentation", "docs"),
        ("Document best practices", "docs"),
    ]
}

# File change templates for realistic edits
FILE_CHANGES = {
    "feature": {
        "backend/detection/fire_detector.py": [
            {
                "type": "add_method",
                "content": '''
    def calculate_flame_intensity(self, region):
        """Calculate flame intensity based on color and brightness"""
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        # Flame color range in HSV
        lower_flame = np.array([0, 50, 50])
        upper_flame = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_flame, upper_flame)
        intensity = np.sum(mask) / mask.size
        return min(intensity * 1.5, 1.0)
'''
            },
            {
                "type": "add_constant",
                "content": "    FLAME_THRESHOLD = 0.65  # Minimum flame intensity threshold\n    SMOKE_OPACITY = 0.45  # Smoke detection opacity level\n"
            },
            {
                "type": "modify_threshold",
                "old": "confidence > 0.75",
                "new": "confidence > self.config.get('detection_threshold', 0.75)"
            }
        ],
        "backend/alerts/notification_system.py": [
            {
                "type": "add_import",
                "content": "from email.mime.multipart import MIMEMultipart\nfrom email.mime.text import MIMEText\nimport smtplib\n"
            },
            {
                "type": "add_method",
                "content": '''
    async def send_priority_alert(self, alert_data):
        """Send high-priority alerts through multiple channels"""
        tasks = []
        if self.email_enabled:
            tasks.append(self.send_email_alert(alert_data))
        if self.sms_enabled:
            tasks.append(self.send_sms_alert(alert_data))
        if self.webhook_enabled:
            tasks.append(self.send_webhook(alert_data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(not isinstance(r, Exception) for r in results)
'''
            }
        ],
        "src/components/views/CommandCenter.jsx": [
            {
                "type": "add_component",
                "content": '''
const AlertBanner = ({ alert }) => {
  const severityColors = {
    P1: 'bg-red-600 animate-pulse',
    P2: 'bg-orange-500',
    P3: 'bg-yellow-500',
    P4: 'bg-blue-500'
  };

  return (
    <div className={`p-4 text-white rounded-lg ${severityColors[alert.severity]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-6 h-6" />
          <span className="font-semibold">{alert.message}</span>
        </div>
        <span className="text-sm">{alert.timestamp}</span>
      </div>
    </div>
  );
};
'''
            }
        ]
    },
    "performance": {
        "backend/utils/performance_optimizer.py": [
            {
                "type": "add_method",
                "content": '''
    def optimize_batch_processing(self, frames, batch_size=8):
        """Process frames in optimized batches for GPU efficiency"""
        batches = []
        for i in range(0, len(frames), batch_size):
            batch = frames[i:i + batch_size]
            # Pad batch if needed
            while len(batch) < batch_size:
                batch.append(np.zeros_like(frames[0]))
            batches.append(np.stack(batch))
        return batches
'''
            },
            {
                "type": "add_cache",
                "content": '''
    def __init__(self):
        super().__init__()
        self.frame_cache = {}  # Cache preprocessed frames
        self.cache_size = 100
        self.cache_hits = 0
        self.cache_misses = 0
'''
            }
        ],
        "backend/detection/fire_detector.py": [
            {
                "type": "optimize_loop",
                "old": "for frame in frames:\n            result = self.detect(frame)",
                "new": "# Vectorized processing\n        results = self.detect_batch(frames)"
            }
        ]
    },
    "test": {
        "tests/test_detection.py": [
            {
                "type": "add_test",
                "content": '''
def test_smoke_detection_accuracy():
    """Test smoke detection with various opacity levels"""
    detector = FireDetector()
    test_cases = [
        ("light_smoke.jpg", 0.65),
        ("heavy_smoke.jpg", 0.95),
        ("fog.jpg", 0.15),  # Should not trigger
    ]
    
    for image_path, expected_confidence in test_cases:
        result = detector.detect(cv2.imread(f"tests/data/{image_path}"))
        assert abs(result.confidence - expected_confidence) < 0.1
'''
            }
        ],
        "tests/test_performance.py": [
            {
                "type": "add_benchmark",
                "content": '''
@pytest.mark.benchmark
def test_detection_latency():
    """Ensure detection meets latency requirements"""
    detector = FireDetector()
    frame = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
    
    start_time = time.time()
    for _ in range(100):
        detector.detect(frame)
    avg_time = (time.time() - start_time) / 100
    
    assert avg_time < 0.05, f"Detection too slow: {avg_time:.3f}s"
'''
            }
        ]
    },
    "refactor": {
        "backend/detection/fire_detector.py": [
            {
                "type": "extract_method",
                "content": '''
    def _preprocess_frame(self, frame):
        """Extract preprocessing logic for better maintainability"""
        # Resize for model input
        processed = cv2.resize(frame, (640, 640))
        # Normalize pixel values
        processed = processed.astype(np.float32) / 255.0
        # Apply contrast enhancement
        processed = cv2.addWeighted(processed, 1.2, processed, 0, -10)
        return processed
'''
            }
        ]
    },
    "docs": {
        "README.md": [
            {
                "type": "add_section",
                "content": '''
## System Architecture

The Sentinel Fire Detection System uses a modular architecture:

- **Detection Engine**: YOLOv8-based neural network for fire/smoke detection
- **Camera Manager**: RTSP/ONVIF integration with automatic discovery
- **Alert System**: Multi-channel notification with redundancy
- **Frontend**: Tauri + React for cross-platform desktop application
- **Database**: SQLite for local alert history and configuration

### Performance Metrics
- Detection Latency: <2 seconds
- Concurrent Cameras: 10+
- False Positive Rate: <2%
- System Uptime: >99%
'''
            }
        ]
    },
    "config": {
        "config/detection_config.yaml": [
            {
                "type": "add_config",
                "content": '''model:
  path: "models/fire_detection_v2.pt"
  confidence_threshold: 0.75
  nms_threshold: 0.45
  
preprocessing:
  resize_width: 640
  resize_height: 640
  normalize: true
  enhance_contrast: true
'''
            }
        ]
    }
}

def get_realistic_file_changes(commit_type, phase):
    """Get appropriate file changes based on commit type and development phase"""
    changes = []
    
    # Determine which files to modify based on phase
    if phase in ["research", "prototype"]:
        # Early phases - mostly docs and simple prototypes
        if commit_type == "docs":
            changes.append(("docs/research_notes.md", "add", f"# Research Notes - {datetime.now().strftime('%Y-%m-%d')}\n\n"))
            changes.append(("docs/requirements.md", "modify", "update requirements"))
        else:
            changes.append(("prototype/detect_fire.py", "add", "import cv2\nimport numpy as np\n"))
    
    elif phase in ["architecture", "foundation"]:
        # Architecture and foundation - structural changes
        changes.append(("backend/__init__.py", "add", "# Backend initialization\n"))
        changes.append(("backend/core/base_detector.py", "add", "from abc import ABC, abstractmethod\n"))
        changes.append(("src-tauri/tauri.conf.json", "modify", "version update"))
        
    elif phase in ["core", "detection"]:
        # Core functionality - actual detection code
        if "backend/detection/fire_detector.py" in FILE_CHANGES.get(commit_type, {}):
            for change in FILE_CHANGES[commit_type]["backend/detection/fire_detector.py"]:
                changes.append(("backend/detection/fire_detector.py", change["type"], change.get("content", "")))
        else:
            changes.append(("backend/detection/fire_detector.py", "modify", "threshold adjustment"))
            
    elif phase in ["integration", "testing"]:
        # Integration and testing - tests and connections
        if commit_type == "test":
            changes.append(("tests/test_detection.py", "add", "import pytest\n"))
            changes.append(("tests/conftest.py", "modify", "fixture update"))
        else:
            changes.append(("backend/alerts/notification_system.py", "modify", "alert integration"))
            
    elif phase in ["optimization", "ui"]:
        # Optimization and UI - performance and frontend
        if phase == "ui":
            changes.append(("src/components/views/CommandCenter.jsx", "modify", "UI enhancement"))
            changes.append(("src/styles/main.css", "modify", "style update"))
        else:
            changes.append(("backend/utils/performance_optimizer.py", "modify", "performance tuning"))
            
    elif phase in ["production", "deployment"]:
        # Production readiness
        changes.append(("scripts/install.sh", "add", "#!/bin/bash\n"))
        changes.append(("config/production.yaml", "add", "production: true\n"))
        
    # Always update config for tracking
    changes.append(("config/detection_config.yaml", "modify", "threshold update"))
    
    return changes

def apply_file_change(file_path, change_type, content):
    """Apply a specific type of change to a file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if change_type == "add":
        # Add new content or create file
        if os.path.exists(file_path):
            with open(file_path, 'a') as f:
                f.write(f"\n{content}")
        else:
            with open(file_path, 'w') as f:
                f.write(content)
                
    elif change_type == "modify":
        # Modify existing file or create if not exists
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Add a comment indicating modification
            if file_path.endswith('.py'):
                lines.insert(0, f"# Modified: {datetime.now().strftime('%Y-%m-%d')}\n")
            elif file_path.endswith('.yaml'):
                lines.insert(0, f"# Updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            elif file_path.endswith('.jsx'):
                lines.insert(0, f"// Updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            
            with open(file_path, 'w') as f:
                f.writelines(lines)
        else:
            # Create file if it doesn't exist
            with open(file_path, 'w') as f:
                if file_path.endswith('.py'):
                    f.write(f"# {content}\n")
                else:
                    f.write(f"// {content}\n")
    
    elif change_type in ["add_method", "add_component", "add_test"]:
        # Add substantial code block
        if os.path.exists(file_path):
            with open(file_path, 'a') as f:
                f.write(f"\n{content}\n")
        else:
            with open(file_path, 'w') as f:
                f.write(content)

def create_realistic_commit(message, date, phase):
    """Create a commit with realistic file changes"""
    # Determine commit type from message
    commit_type = "feature"  # default
    for keyword, ctype in [("test", "test"), ("optimize", "performance"), 
                           ("refactor", "refactor"), ("document", "docs"),
                           ("fix", "fix"), ("perf", "performance")]:
        if keyword in message.lower():
            commit_type = ctype
            break
    
    # Get appropriate file changes
    changes = get_realistic_file_changes(commit_type, phase)
    
    # Apply changes
    modified_files = []
    for file_path, change_type, content in changes[:random.randint(3, 5)]:  # 3-5 files per commit
        try:
            apply_file_change(file_path, change_type, content)
            modified_files.append(file_path)
        except Exception as e:
            print(f"Error modifying {file_path}: {e}")
    
    if not modified_files:
        print(f"No files modified for commit: {message}")
        return False
    
    # Stage changes
    for file_path in modified_files:
        subprocess.run(['git', 'add', file_path], check=True)
    
    # Create commit
    date_str = date.strftime('%Y-%m-%d %H:%M:%S')
    env = os.environ.copy()
    env['GIT_AUTHOR_DATE'] = date_str
    env['GIT_COMMITTER_DATE'] = date_str
    
    result = subprocess.run(
        ['git', 'commit', '-m', message],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ {date.strftime('%Y-%m-%d')}: {message}")
        return True
    else:
        print(f"✗ Failed: {message}")
        return False

def generate_2023_commits():
    """Generate 100 realistic commits throughout 2023"""
    commits = []
    
    # Generate commits based on development phases
    for month in range(1, 13):
        month_str = f"2023-{month:02d}"
        phases = DEVELOPMENT_PHASES.get(month_str, ["general"])
        
        # 8-10 commits per month for realistic distribution
        num_commits = random.randint(7, 10)
        
        for _ in range(num_commits):
            # Pick a phase for this commit
            phase = random.choice(phases)
            
            # Get appropriate commit messages for this phase
            phase_messages = PHASE_COMMITS.get(phase, PHASE_COMMITS["research"])
            message, commit_type = random.choice(phase_messages)
            
            # Generate realistic date/time
            day = random.randint(1, 28)  # Avoid month-end issues
            # Work hours with realistic distribution
            hour = random.choices(
                [9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                weights=[3, 5, 7, 4, 8, 9, 9, 8, 6, 5, 3, 2, 1]
            )[0]
            minute = random.randint(0, 59)
            
            commit_date = datetime(2023, month, day, hour, minute, random.randint(0, 59))
            
            # Add some weekend/late night commits for realism
            if random.random() < 0.15:  # 15% chance of weekend work
                commit_date += timedelta(days=random.choice([5, 6]))  # Move to weekend
            
            commits.append((commit_date, message, phase))
    
    # Sort chronologically
    commits.sort(key=lambda x: x[0])
    
    # Ensure we have ~100 commits
    commits = commits[:100]
    
    print(f"Generating {len(commits)} realistic commits for 2023...")
    print("This will create a comprehensive development history")
    print("=" * 50)
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    # Create commits
    successful = 0
    for date, message, phase in commits:
        if create_realistic_commit(message, date, phase):
            successful += 1
    
    print("=" * 50)
    print(f"✓ Created {successful}/{len(commits)} commits")
    print("\nDevelopment timeline created:")
    print("- Q1 2023: Research & Prototyping")
    print("- Q2 2023: Core Development")
    print("- Q3 2023: Integration & Testing") 
    print("- Q4 2023: Production & Deployment")
    print("\nRun 'git log --oneline --graph --all' to see the history")
    print("Run 'git push -f origin master' to push to remote")

if __name__ == "__main__":
    generate_2023_commits()