import cv2
import numpy as np

from yolo_tracker import YOLOTracker
from mqtt_client import MQTTClient
from utils import load_config

def main():
    print("Starting remote PC edge AI system...")
    
    config = load_config()
    if not config:
        return

    # Initialize video capture
    source = f"tcp://raspberrypi.local:{config['video']['port']}"

    tracker = YOLOTracker(config)
    mqtt = MQTTClient(config)

    ptz_state = {}

    def on_mqtt_message(topic, payload):
        nonlocal ptz_state
        if topic == config['mqtt']['topics']['ptz']:
            ptz_state = payload

    mqtt.set_callback(on_mqtt_message)

    try:
        results = tracker.start(source)
        mqtt.start()
        
        for result in results:
            # Publish the inference results to MQTT
            mqtt.publish_inference(result)

            # Get the annotated frame (YOLO detections)
            full_frame = result.plot()
            H, W = full_frame.shape[:2]
            
            # Initialize PTZ view with a placeholder (using 9:16 aspect ratio)
            target_ratio = 9 / 16
            ptz_W = int(H * target_ratio)
            ptz_view = np.zeros((H, ptz_W, 3), dtype=np.uint8)
            cv2.putText(ptz_view, "WAITING", (ptz_W//10, H//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

            # Process PTZ if state is available
            if ptz_state:
                try:
                    x, y, w, h = ptz_state.get('x'), ptz_state.get('y'), ptz_state.get('w'), ptz_state.get('h')
                    if all(v is not None for v in [x, y, w, h]):
                        # Calculate coordinates and ensure they are within frame boundaries
                        x1, y1 = max(0, int(x)), max(0, int(y))
                        x2, y2 = min(W, int(x + w)), min(H, int(y + h))
                        
                        if x2 > x1 and y2 > y1:
                            # Draw PTZ region rectangle on full frame (YOLO style)
                            color = (0, 0, 255)
                            thickness = 3
                            cv2.rectangle(full_frame, (x1, y1), (x2, y2), color, thickness)
                            
                            label = "PTZ VIEWPORT"
                            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            # Draw filled background for label
                            cv2.rectangle(full_frame, (x1 - 1, y1 - lh - 12), (x1 + lw + 10, y1), color, -1)
                            # Draw label text
                            cv2.putText(full_frame, label, (x1 + 4, y1 - 7), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                            
                            # Extract and resize crop, maintaining vertical aspect ratio
                            crop = result.orig_img[y1:y2, x1:x2]
                            if crop.size > 0:
                                ptz_view = cv2.resize(crop, (ptz_W, H))
                except Exception as e:
                    print(f"Error processing PTZ crop: {e}")

            # Add HUD elements / Design
            # Add semi-transparent overlays for labels
            for img, label in [(full_frame, "SYSTEM VIEW"), (ptz_view, "PTZ VIEW")]:
                cur_H, cur_W = img.shape[:2]
                overlay = img.copy()
                cv2.rectangle(overlay, (0, 0), (cur_W, 40), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)
                cv2.putText(img, label, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Combine both views side-by-side
            dashboard = np.hstack((full_frame, ptz_view))
            
            # Display the final composed window
            cv2.imshow("RPi Virtual PTZ - Dashboard", dashboard)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mqtt.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
