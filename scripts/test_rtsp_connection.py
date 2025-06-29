#!/usr/bin/env python3
"""
RTSP Connection Test Script
Tests RTSP stream connectivity for Sentinel Fire Detection System
"""

import cv2
import sys
import time
import argparse
from datetime import datetime

def test_rtsp_connection(rtsp_url, timeout=10):
    """
    Test RTSP stream connection and retrieve basic information
    """
    print(f"\n{'='*60}")
    print(f"RTSP Connection Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    print(f"Testing URL: {rtsp_url}")
    print(f"Timeout: {timeout} seconds\n")
    
    # Set capture properties
    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Wait for connection with timeout
    start_time = time.time()
    while not cap.isOpened() and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    if not cap.isOpened():
        print("❌ Failed to connect to RTSP stream")
        return False
    
    print("✅ Successfully connected to RTSP stream\n")
    
    # Get stream properties
    print("Stream Properties:")
    print(f"  - Width: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}")
    print(f"  - Height: {int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"  - FPS: {cap.get(cv2.CAP_PROP_FPS)}")
    print(f"  - Codec: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
    
    # Try to read frames
    print("\nTesting frame capture...")
    frames_read = 0
    start_time = time.time()
    
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            frames_read += 1
            if frames_read == 1:
                print(f"  - First frame received: {frame.shape}")
        else:
            print(f"  - Failed to read frame {i+1}")
    
    elapsed = time.time() - start_time
    print(f"\n✅ Read {frames_read}/10 frames in {elapsed:.2f} seconds")
    
    # Display a frame if requested
    if frames_read > 0 and '--show' in sys.argv:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('RTSP Test Frame', frame)
            print("\nDisplaying frame - Press any key to close")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    cap.release()
    
    # Test reconnection
    print("\nTesting reconnection...")
    cap2 = cv2.VideoCapture(rtsp_url)
    cap2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if cap2.isOpened():
        print("✅ Reconnection successful")
        cap2.release()
    else:
        print("❌ Reconnection failed")
    
    return True

def test_multiple_streams(urls):
    """
    Test multiple RTSP streams
    """
    print(f"\nTesting {len(urls)} RTSP streams...\n")
    
    results = []
    for i, url in enumerate(urls, 1):
        print(f"Stream {i}/{len(urls)}:")
        success = test_rtsp_connection(url, timeout=5)
        results.append((url, success))
        print("")
    
    # Summary
    print("\nSummary:")
    print("="*60)
    successful = sum(1 for _, success in results if success)
    print(f"Successful connections: {successful}/{len(results)}")
    
    for url, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {url}")

def create_test_config(rtsp_url):
    """
    Generate a sample camera configuration for Sentinel
    """
    config = f"""# Sample camera configuration for Sentinel
cameras:
  - id: "test_camera_1"
    name: "Test Camera"
    url: "{rtsp_url}"
    username: ""  # Add if authentication required
    password: ""  # Add if authentication required
    enabled: true
    detection_enabled: true
    fps_limit: 10
    reconnect_interval: 30
    timeout: 10
    
last_updated: {datetime.now().isoformat()}Z
"""
    
    print("\nSample cameras.yaml configuration:")
    print("-"*60)
    print(config)
    print("-"*60)
    
    # Save to file if requested
    if '--save-config' in sys.argv:
        with open('test_cameras.yaml', 'w') as f:
            f.write(config)
        print("\n✅ Configuration saved to test_cameras.yaml")

def main():
    parser = argparse.ArgumentParser(description='Test RTSP stream connectivity')
    parser.add_argument('url', nargs='?', default='rtsp://localhost:8554/webcam',
                        help='RTSP URL to test (default: rtsp://localhost:8554/webcam)')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Connection timeout in seconds (default: 10)')
    parser.add_argument('--show', action='store_true',
                        help='Display a frame from the stream')
    parser.add_argument('--save-config', action='store_true',
                        help='Save sample camera configuration')
    parser.add_argument('--test-common', action='store_true',
                        help='Test common RTSP URLs')
    
    args = parser.parse_args()
    
    if args.test_common:
        # Test common RTSP URLs
        common_urls = [
            'rtsp://localhost:8554/webcam',
            'rtsp://localhost:8554/stream',
            'rtsp://localhost:4554/live',
            'rtsp://127.0.0.1:8554/webcam',
        ]
        test_multiple_streams(common_urls)
    else:
        # Test single URL
        success = test_rtsp_connection(args.url, args.timeout)
        
        if success and args.save_config:
            create_test_config(args.url)
        
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)