import time
import sys
from video_receiver import VideoReceiver
from model_inference import ModelInference
from mqtt_publisher import MQTTPublisher

# Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "/control/action"
LISTEN_PORT = 5000
MODEL_PATH = "models/my_model.tflite"

def on_frame_received(frame):
    """Callback when a video frame is received"""
    # TODO: Run Inference
    # 1. Run Inference
    # result = inference_engine.predict(frame)
    
    # 2. Logic to determine action
    # if result == "some_condition":
    #     mqtt_pub.send_command("ACTIVATE")

def main():
    print("PC Server Node Started")
    
    global inference_engine, mqtt_pub
    
    # Initialize Modules
    inference_engine = ModelInference(MODEL_PATH)
    inference_engine.load_model()
    
    mqtt_pub = MQTTPublisher(MQTT_BROKER, MQTT_TOPIC)
    mqtt_pub.connect()
    
    receiver = VideoReceiver(on_frame_received)
    
    try:
        # Start Receiver
        receiver.start_receiving(LISTEN_PORT)
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping services...")
        receiver.stop_receiving()
        mqtt_pub.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()

