import cv2

from yolo_tracker import YOLOTracker
from mqtt_client import MQTTClient
from utils import load_config

def main():
    print("Starting remote PC edge AI system...")
    
    config = load_config()
    if not config:
        return

    # Initialize video capture using OpenCV
    source = f"http://raspberrypi.local:{config['video']['port']}"
    cap = cv2.VideoCapture(source)

    tracker = YOLOTracker(config)
    mqtt = MQTTClient(config)

    ptz_state = {}

    def on_mqtt_message(topic, payload):
        nonlocal ptz_state
        if topic == config['mqtt']['topics']['ptz']:
            ptz_state = payload

    mqtt.set_callback(on_mqtt_message)

    try:
        mqtt.start()
        
        while cap.isOpened():
            # Read a frame from the video
            success, frame = cap.read()

            if success:
                # Track the objects in the frame
                results = tracker.track(frame)

                # Plot the results on the frame
                annotated_frame = results[0].plot()

                # Publish the inference results to MQTT
                mqtt.publish_inference(results)

                # Display the annotated frame
                cv2.imshow("YOLO Tracker", annotated_frame)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mqtt.stop()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
