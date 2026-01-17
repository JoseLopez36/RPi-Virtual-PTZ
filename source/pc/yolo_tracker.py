import cv2

from ultralytics import YOLO

class YOLOTracker:
    def __init__(self, config):
        self.model_path = config['ai']['model_path']
        self.conf_threshold = config['ai']['conf_threshold']

        # Load the YOLO model
        print(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)

    def track(self, frame):
        results = self.model.track(frame, persist=True)
        return results