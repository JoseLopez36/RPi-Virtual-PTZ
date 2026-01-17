import time

from camera_stream import CameraStream
from ptz_logic import PTZController
from sense_hat_interface import SenseHatInterface
from mqtt_client import MQTTClient
from utils import load_config

def main():
    print("Starting RPi Virtual PTZ system...")
    
    config = load_config()
    if not config:
        return

    # Initialize components
    camera = CameraStream(config)
    mqtt = MQTTClient(config)
    ptz = PTZController(config)
    sense_hat = SenseHatInterface()

    def on_mqtt_message(topic, payload):
        if topic == config['mqtt']['topics']['inference']:
            # Process inference results
            detections = payload.get('detections', [])
            ptz_cmd = ptz.update(detections)
            mqtt.publish_ptz(ptz_cmd)
            sense_hat.update_display(detections, ptz.target_id)

    mqtt.set_callback(on_mqtt_message)

    try:
        camera.start()
        mqtt.start()
        
        while True:
            # Main loop tasks (e.g., check joystick)
            # event = sense_hat.get_joystick_event()
            # if event:
            #     ptz.handle_input(event)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        camera.stop()
        mqtt.stop()

if __name__ == "__main__":
    main()
