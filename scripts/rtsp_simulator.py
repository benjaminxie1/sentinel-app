#!/usr/bin/env python3
"""
Simple RTSP Simulator for testing Sentinel
Simulates fire/smoke scenarios without requiring actual RTSP server
"""

import cv2
import numpy as np
import time
import threading
import socket
from datetime import datetime

class RTSPSimulator:
    def __init__(self, port=8554):
        self.port = port
        self.running = False
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 10
        self.scenario = "normal"
        
    def generate_frame(self):
        """Generate a test frame based on current scenario"""
        # Create base frame
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if self.scenario == "normal":
            # Normal scene - just a room
            cv2.rectangle(frame, (50, 100), (590, 400), (100, 100, 100), -1)  # Room
            cv2.rectangle(frame, (200, 200), (300, 300), (150, 150, 150), -1)  # Object
            cv2.putText(frame, "Normal Scene", (250, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
        elif self.scenario == "smoke":
            # Simulate smoke
            cv2.rectangle(frame, (50, 100), (590, 400), (80, 80, 80), -1)  # Room
            
            # Add smoke effect
            smoke_layer = np.random.randint(100, 150, (self.frame_height, self.frame_width, 3), dtype=np.uint8)
            smoke_layer[:, :] = (120, 120, 130)  # Grayish smoke
            
            # Create smoke pattern
            x = np.random.randint(100, 500)
            y = np.random.randint(150, 350)
            cv2.circle(smoke_layer, (x, y), 100, (160, 160, 170), -1)
            
            frame = cv2.addWeighted(frame, 0.5, smoke_layer, 0.5, 0)
            cv2.putText(frame, "SMOKE DETECTED", (200, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        elif self.scenario == "fire":
            # Simulate fire
            cv2.rectangle(frame, (50, 100), (590, 400), (50, 50, 50), -1)  # Dark room
            
            # Add fire effect
            fire_x = np.random.randint(200, 400)
            fire_y = np.random.randint(250, 350)
            
            # Orange/red fire colors
            for i in range(5):
                radius = np.random.randint(20, 60)
                color = (0, np.random.randint(100, 200), np.random.randint(200, 255))
                cv2.circle(frame, (fire_x + np.random.randint(-30, 30), 
                                 fire_y + np.random.randint(-20, 20)), 
                          radius, color, -1)
            
            cv2.putText(frame, "FIRE DETECTED", (200, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
        return frame
    
    def simulate_rtsp_file(self, filename="test_stream.avi"):
        """Create a video file that can be streamed"""
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, self.fps, (self.frame_width, self.frame_height))
        
        print(f"Generating test video: {filename}")
        
        # Generate 30 seconds of video
        total_frames = self.fps * 30
        
        for i in range(total_frames):
            # Change scenarios
            if i < total_frames // 3:
                self.scenario = "normal"
            elif i < 2 * total_frames // 3:
                self.scenario = "smoke"
            else:
                self.scenario = "fire"
            
            frame = self.generate_frame()
            out.write(frame)
            
            if i % self.fps == 0:
                print(f"Generated {i}/{total_frames} frames...")
        
        out.release()
        print(f"✅ Test video created: {filename}")
        return filename

def create_mock_camera_feed():
    """Create a mock camera that Sentinel can connect to"""
    print("\n" + "="*60)
    print("Mock Camera Feed for Sentinel Testing")
    print("="*60 + "\n")
    
    # Create video file
    simulator = RTSPSimulator()
    video_file = simulator.simulate_rtsp_file("test_fire_scenarios.avi")
    
    print("\n✅ Mock camera feed created!")
    print("\nTo use with Sentinel:")
    print("1. The video file 'test_fire_scenarios.avi' simulates:")
    print("   - 0-10 seconds: Normal scene")
    print("   - 10-20 seconds: Smoke detection")
    print("   - 20-30 seconds: Fire detection")
    print("\n2. You can use this file path in cameras.yaml:")
    print(f"   url: 'file://{os.path.abspath(video_file)}'")
    
    return video_file

import os

if __name__ == "__main__":
    # Create mock feed
    video_file = create_mock_camera_feed()
    
    # Generate camera config
    config = f"""cameras:
  - id: "test_sim_1"
    name: "Fire Simulation Camera"
    url: "file://{os.path.abspath(video_file)}"
    username: ""
    password: ""
    enabled: true
    detection_enabled: true
    fps_limit: 10
    reconnect_interval: 30
    timeout: 10

last_updated: {datetime.now().isoformat()}Z
"""
    
    with open("config/cameras.yaml", "w") as f:
        f.write(config)
    
    print("\n✅ Camera configuration updated!")
    print("\nNow you can run Sentinel to test fire detection.")