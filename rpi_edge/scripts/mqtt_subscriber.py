import time
from paho.mqtt import client
import random

class MQTTSubscriber:
    def __init__(self, broker_address, topic, callback):
        self.client = client.Client()
        self.broker_address = broker_address
        self.topic = topic
        self.callback = callback
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT Broker with result code {rc}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Received message on {msg.topic}: {msg.payload}")
        if self.callback:
            self.callback(msg.payload)

    def start(self):
        print(f"Connecting to MQTT Broker at {self.broker_address}...")
        self.client.connect(self.broker_address, 1883, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()