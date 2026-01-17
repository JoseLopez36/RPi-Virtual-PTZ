import cv2

from ultralytics import YOLO

class YOLOTracker:
    def __init__(self, config):
        self.model_path = config['ai']['model_path']
        self.conf_threshold = config['ai']['conf_threshold']
        self.input_size = config['ai']['input_size']

        # Load the YOLO model
        print(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)

    def start(self, source):
        return self.model.track(source, stream=True, conf=self.conf_threshold, classes=[0], persist=True, imgsz=self.input_size, verbose=False)