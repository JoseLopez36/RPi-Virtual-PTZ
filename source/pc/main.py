import cv2

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

            # Display the frame in a single window named 'YOLO Inference'
            cv2.imshow("YOLO Inference", result.plot())

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mqtt.stop()

if __name__ == "__main__":
    main()
