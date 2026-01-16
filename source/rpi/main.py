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
SOURCE_URL = f"rtsp://{GIMBAL_IP}:8554/main.264"
STREAM_FPS = 30
MODEL_PATH = "models/yolo11n.pt"  # Path to YOLO11n model (relative to project root)

def _safe_close_results_gen(results_gen):
    if results_gen is None:
        return
    close_fn = getattr(results_gen, "close", None)
    if callable(close_fn):
        try:
            close_fn()
        except Exception as e:
            print(f"Warning: failed to close results generator: {e}")

def main():
    print("RPi Gimbal Tracker Started")
    
    tracker = None
    results_gen = None
    gimbal = None
    streamer = None

    # Initialize Modules
    try:
        print("Initializing YOLO tracker...")
        tracker = YoloTracker(model_path=MODEL_PATH, conf_threshold=0.5)
        results_gen = tracker.track(SOURCE_URL)

        print("Initializing gimbal controller...")
        gimbal = GimbalController(gimbal_ip=GIMBAL_IP)
        gimbal.connect()

        print("Initializing video streamer...")
        streamer = VideoStreamer()

    except Exception as e:
        print(f"Startup failed: {e}")
    
    try:
        print("System running. Press Ctrl+C to stop")

        if results_gen is None or tracker is None or gimbal is None or streamer is None:
            raise RuntimeError("System not initialized; cannot start processing loop")

        for result in results_gen:
            # 1. Render annotated frame and stream it to the PC
            annotated = None
            try:
                if result is not None:
                    annotated = result.plot()
            except Exception as e:
                print(f"Warning: failed to render YOLO annotations: {e}")

            if annotated is not None:
                try:
                    if streamer.pipeline is None:
                        h, w = annotated.shape[:2]
                        streamer.start_stream(
                            host=PC_HOST_IP, port=PC_PORT, width=w, height=h, fps=STREAM_FPS
                        )
                    streamer.push_frame(annotated)
                except Exception as e:
                    print(f"Warning: failed to stream annotated frame: {e}")

            # 2. Convert YOLO result to target list
            target_list = tracker.result_to_target_list(result)

            # 3. Get current primary target
            target = tracker.get_primary_target(target_list)

            # If no target, hold last gimbal position
            if target is None:
                continue

            # 4. Calculate gimbal commands based on target position
            if annotated is not None:
                frame_h, frame_w = annotated.shape[:2]
                pan, tilt = tracker.calculate_gimbal_command(target, frame_w, frame_h)

            # 5. Set gimbal commands
            gimbal.set_pan_tilt(pan, tilt)

    except KeyboardInterrupt:
        print("\nStopping services...")

    finally:
        _safe_close_results_gen(results_gen)
        if gimbal is not None:
            gimbal.disconnect()
        if streamer is not None:
            streamer.stop_stream()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()