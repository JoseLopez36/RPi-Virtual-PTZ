import paho.mqtt.client as mqtt
import json
import threading

class MQTTClient:
    def __init__(self, config):
        self.broker = config['mqtt']['broker']
        self.port = config['mqtt']['port']
        self.topics = config['mqtt']['topics']
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_callback = None
        self.running = False

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT Broker with result code {rc}")
        client.subscribe(self.topics['ptz'])

    def on_message(self, client, userdata, msg):
        if self.message_callback:
            try:
                payload = json.loads(msg.payload.decode())
                self.message_callback(msg.topic, payload)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from {msg.topic}")

    def set_callback(self, callback):
        self.message_callback = callback

    def publish_inference(self, results):
        if not self.running:
            return

        serializable_detections = []
        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                box = boxes[i]
                detection = {
                    "box": box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                    "conf": float(box.conf[0]),
                    "cls": int(box.cls[0]),
                }
                if box.id is not None:
                    detection["id"] = int(box.id[0])
                serializable_detections.append(detection)

        payload = {"detections": serializable_detections}
        try:
            self.client.publish(self.topics['inference'], json.dumps(payload))
        except Exception as e:
            print(f"Error publishing inference: {e}")

    def start(self):
        if not self.running:
            try:
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
                self.running = True
            except Exception as e:
                print(f"Failed to connect to MQTT broker: {e}")

    def stop(self):
        if self.running:
            self.client.loop_stop()
            self.client.disconnect()
            self.running = False
