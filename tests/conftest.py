"""
Pytest configuration and shared fixtures for Sentinel test suite.
"""

import os
import sys
import time
from pathlib import Path
import pytest

# Ensure repository root and backend directory are in Python path
repo_root = Path(__file__).parent.parent
backend_dir = repo_root / "backend"

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture
def sample_detection_data():
    """Returns sample bounding box and confidence score data for fire detection."""
    return {
        "confidence": 0.96,
        "bbox": (100, 150, 300, 400),
        "class_name": "fire",
        "timestamp": time.time(),
    }
