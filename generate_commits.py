#!/usr/bin/env python3
"""
Generate realistic backdated commits for testing purposes
"""

import subprocess
import random
from datetime import datetime, timedelta
import os

# Realistic commit messages for a fire detection system
COMMIT_MESSAGES = [
    "Refactor camera initialization logic",
    "Update detection threshold parameters",
    "Fix memory leak in video processing",
    "Optimize frame buffer management",
    "Add error handling for RTSP disconnects",
    "Improve alert notification latency",
    "Update YOLOv8 confidence thresholds",
    "Fix edge case in smoke detection",
    "Refactor database connection pooling",
    "Add retry logic for network failures",
    "Optimize GPU memory allocation",
    "Update camera calibration algorithm",
    "Fix false positive in low light conditions",
    "Improve motion detection sensitivity",
    "Add logging for detection events",
    "Update configuration schema validation",
    "Fix race condition in alert queue",
    "Optimize frame preprocessing pipeline",
    "Add support for H.265 codec",
    "Update detection model weights",
    "Fix timestamp synchronization issue",
    "Improve thermal camera integration",
    "Add performance monitoring metrics",
    "Update alert priority calculation",
    "Fix memory allocation in detector",
    "Optimize batch processing logic",
    "Add camera health check monitoring",
    "Update notification template engine",
    "Fix thread safety in detector pool",
    "Improve error recovery mechanism",
    "Add diagnostic logging system",
    "Update detection zone configuration",
    "Fix video stream buffering issue",
    "Optimize neural network inference",
    "Add automated threshold adjustment",
    "Update camera discovery protocol",
    "Fix alert deduplication logic",
    "Improve system resource monitoring",
    "Add backup notification channel",
    "Update model training pipeline",
    "Fix configuration hot-reload",
    "Optimize database query performance",
    "Add network latency compensation",
    "Update alert escalation logic",
    "Fix camera reconnection handling"
]

# Files to make small edits to
FILES_TO_EDIT = [
    "backend/detection/fire_detector.py",
    "backend/detection/rtsp_manager.py",
    "backend/alerts/notification_system.py",
    "backend/utils/network_monitor.py",
    "backend/utils/performance_optimizer.py",
    "backend/config/camera_config.py",
    "src/App.jsx",
    "src/components/Dashboard.jsx",
    "src/components/CameraGrid.jsx",
    "config/detection_config.yaml",
    "requirements.txt",
    "package.json"
]

def make_small_edit(file_path):
    """Make a small, realistic edit to a file"""
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} - doesn't exist")
        return False
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return False
            
        # Choose a random type of edit
        edit_type = random.choice(['comment', 'whitespace', 'reorder', 'constant'])
        
        if edit_type == 'comment' and file_path.endswith('.py'):
            # Add a comment to Python files
            line_num = random.randint(0, min(20, len(lines)-1))
            lines.insert(line_num, f"    # Performance optimization - {datetime.now().strftime('%Y-%m-%d')}\n")
        elif edit_type == 'whitespace':
            # Add/remove whitespace
            if len(lines) > 1:
                lines.append("\n")
        elif edit_type == 'constant' and file_path.endswith('.py'):
            # Modify a constant value
            for i, line in enumerate(lines):
                if 'THRESHOLD' in line or 'TIMEOUT' in line or 'INTERVAL' in line:
                    if '=' in line and any(c.isdigit() for c in line):
                        # Just add a comment instead of modifying value
                        lines[i] = line.rstrip() + "  # Tuned value\n"
                        break
        elif file_path.endswith('.yaml'):
            # Add a comment to YAML files
            lines.insert(0, f"# Configuration updated: {datetime.now().strftime('%Y-%m-%d')}\n")
        elif file_path == 'requirements.txt':
            # Add a comment
            lines.insert(0, "# Dependencies updated\n")
        elif file_path == 'package.json':
            # Just add whitespace for JSON
            lines.append("\n")
        else:
            # Default: just add a newline
            lines.append("\n")
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"Error editing {file_path}: {e}")
        return False

def create_backdated_commit(message, date):
    """Create a commit with a specific date"""
    date_str = date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Choose 1-3 files to edit
    num_files = random.randint(1, min(3, len(FILES_TO_EDIT)))
    files_to_edit = random.sample([f for f in FILES_TO_EDIT if os.path.exists(f)], 
                                  min(num_files, len([f for f in FILES_TO_EDIT if os.path.exists(f)])))
    
    if not files_to_edit:
        print("No valid files to edit")
        return False
    
    # Make edits
    edited_files = []
    for file_path in files_to_edit:
        if make_small_edit(file_path):
            edited_files.append(file_path)
    
    if not edited_files:
        print("No files were successfully edited")
        return False
    
    # Stage changes
    for file_path in edited_files:
        subprocess.run(['git', 'add', file_path], check=True)
    
    # Create commit with specific date
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
        print(f"Created commit: {message} ({date_str})")
        return True
    else:
        print(f"Failed to create commit: {result.stderr}")
        return False

def main():
    # Generate dates spread over the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    dates = []
    current_date = start_date
    
    # Generate ~40 commits with realistic distribution
    num_commits = random.randint(38, 42)
    
    for _ in range(num_commits):
        # Add some randomness to the distribution
        days_to_add = random.randint(5, 15)  # Commits every 5-15 days on average
        current_date += timedelta(days=days_to_add)
        
        if current_date > end_date:
            break
        
        # Randomize time of day (working hours with some variation)
        hour = random.choices(
            [9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21],
            weights=[5, 8, 7, 6, 9, 8, 7, 5, 4, 3, 2]  # More likely during work hours
        )[0]
        minute = random.randint(0, 59)
        
        commit_date = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
        dates.append(commit_date)
    
    # Sort dates chronologically
    dates.sort()
    
    # Use random commit messages
    messages = random.sample(COMMIT_MESSAGES, min(len(COMMIT_MESSAGES), len(dates)))
    
    print(f"Generating {len(dates)} commits...")
    print("WARNING: This will modify your git history!")
    response = input("Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    # Create commits
    successful = 0
    for date, message in zip(dates, messages):
        if create_backdated_commit(message, date):
            successful += 1
    
    print(f"\nCompleted! Created {successful}/{len(dates)} commits")
    print("Run 'git log --oneline' to see the new commits")
    print("Run 'git push -f' to push to remote (use with caution!)")

if __name__ == "__main__":
    main()