"""
Raspberry Pi - Main Entry Point

This module orchestrates:
1. Human detection and tracking using YOLO11n
2. Gimbal control to follow targets
3. Annotated video streaming to PC
"""

import time
import sys
from yolo_tracker import YoloTracker
from gimbal_controller import GimbalController
from video_streamer import VideoStreamer

# Configuration
GIMBAL_IP = "192.168.144.25"  # Replace with Siyi A8 Mini IP
PC_HOST_IP = "192.168.2.28"  # Replace with PC IP
PC_PORT = 5000
SOURCE_URL = f"rtsp://{GIMBAL_IP}:554/stream1"
SOURCE_WIDTH = 1920
SOURCE_HEIGHT = 1080
MODEL_PATH = "models/yolo11n.pt"  # Path to YOLO11n model (relative to project root)

def main():
    print("RPi Gimbal Tracker Started")
    
    # Initialize Modules
    print("Initializing YOLO tracker...")
    tracker = YoloTracker(model_path=MODEL_PATH, conf_threshold=0.5)
    
    print("Initializing gimbal controller...")
    gimbal = GimbalController(gimbal_ip=GIMBAL_IP)
    gimbal.connect()
    
    print("Initializing video streamer...")
    streamer = VideoStreamer(host=PC_HOST_IP, port=PC_PORT)
    
    try:
        print("System running. Press Ctrl+C to stop")
        while True:
            # 1. Track targets
            target_list = tracker.track(SOURCE_URL)

            # 2. Get current primary target
            target = tracker.get_primary_target(target_list)

            # 3. Calculate gimbal commands
            pan, tilt = tracker.calculate_gimbal_command(target, SOURCE_WIDTH, SOURCE_HEIGHT)

            # 4. Set gimbal commands
            gimbal.set_pan_tilt(pan, tilt)

            # 5. Stream annotated video
            streamer.start_stream(host=PC_HOST_IP, port=PC_PORT)

            # Sleep to avoid high CPU usage
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStopping services...")

    finally:
        streamer.stop_stream()
        gimbal.disconnect()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()