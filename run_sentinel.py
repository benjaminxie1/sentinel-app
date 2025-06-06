#!/usr/bin/env python3
"""
Sentinel Fire Detection System - Launcher
Simple entry point to start the complete system
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import torch
        import cv2
        import ultralytics
        import yaml
        print("✅ All Python dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def main():
    print("🔥 Sentinel Fire Detection System")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the detection system
    backend_path = Path(__file__).parent / "backend" / "main.py"
    
    try:
        print("Starting detection engine...")
        subprocess.run([sys.executable, str(backend_path)], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutdown requested")
    except subprocess.CalledProcessError as e:
        print(f"❌ Detection engine failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()