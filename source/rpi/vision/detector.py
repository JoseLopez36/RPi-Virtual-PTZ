"""
YOLO Human Detection and Tracking Module

This module uses YOLO11n for human detection and YOLO's built-in tracker
for tracking detected humans across frames.
"""

import os
from ultralytics import YOLO

class YoloTracker:
    def __init__(self, model_path="models/yolo11n.pt", conf_threshold=0.5):
        """
        Initialize YOLO tracker
        
        Args:
            model_path: Path to YOLO11n model weights
            conf_threshold: Confidence threshold for detections (0.0, 1.0)
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self._model = None
        print(f"Initializing YOLO Tracker (model: {model_path})")
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            # Resolve model path relative to project root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            model_full_path = os.path.join(project_root, self.model_path)
            
            if not os.path.exists(model_full_path):
                raise FileNotFoundError(f"Model file not found: {model_full_path}")
            
            self._model = YOLO(model_full_path)
            print(f"YOLO model loaded successfully from {model_full_path}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise
    
    def track(self, source):
        """
        Detect humans and track them across frames
        
        Args:
            source: Input source (video file, stream url, etc.)
            
        Returns:
            List of tracked objects with bounding boxes and IDs
            Each object contains: id, bbox (x1, y1, x2, y2), confidence, class
        """
        if self._model is None:
            raise ValueError("YOLO model not loaded")
        
        # Run YOLO detection with tracking
        # Class 0 in COCO dataset is 'person'
        results = self._model.track(
            source,
            conf=self.conf_threshold,
            classes=[0],
            stream=True
        )
        
        return results

    def result_to_target_list(self, result):
        """
        Convert a single Ultralytics 'results' object into a list of target dicts

        Each dict contains: id, bbox (x1,y1,x2,y2), confidence, class
        """
        target_list = []
        if result is None:
            return target_list

        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return target_list

        for b in boxes:
            # xyxy: tensor([[x1, y1, x2, y2]])
            xyxy = getattr(b, "xyxy", None)
            if xyxy is None:
                continue
            try:
                bbox = xyxy.squeeze().tolist()
            except Exception:
                # Fallback: best-effort conversion
                bbox = list(xyxy[0])

            conf = getattr(b, "conf", None)
            try:
                confidence = float(conf.item()) if conf is not None else 0.0
            except Exception:
                confidence = float(conf) if conf is not None else 0.0

            cls = getattr(b, "cls", None)
            try:
                class_id = int(cls.item()) if cls is not None else -1
            except Exception:
                class_id = int(cls) if cls is not None else -1

            track_id = getattr(b, "id", None)
            if track_id is not None:
                try:
                    track_id = int(track_id.item())
                except Exception:
                    try:
                        track_id = int(track_id)
                    except Exception:
                        track_id = None

            target_list.append(
                {
                    "id": track_id,
                    "bbox": bbox,
                    "confidence": confidence,
                    "class": class_id,
                }
            )

        return target_list
    
    def get_primary_target(self, target_list):
        """
        Select primary target to track (e.g., largest or closest to center)
        
        Args:
            target_list: List of tracked objects from track
            
        Returns:
            Primary target object or None
        """
        if not target_list:
            return None
        
        # Simple strategy: select largest bounding box
        largest_area = 0
        primary_target = None
        
        for obj in target_list:
            bbox = obj['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            if area > largest_area:
                largest_area = area
                primary_target = obj
        
        return primary_target
    
    def calculate_gimbal_command(self, target, frame_width, frame_height):
        """
        Calculate gimbal pan/tilt commands based on target position
        
        Args:
            target: Target object with bbox
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            
        Returns:
            Tuple (pan, tilt) in degrees
            Positive pan = right, positive tilt = up
        """
        if target is None:
            return (0.0, 0.0)
        
        # Get bounding box coordinates
        bbox = target['bbox']

        # Calculate center of bounding box
        target_center_x = (bbox[0] + bbox[2]) / 2
        target_center_y = (bbox[1] + bbox[3]) / 2
        
        # Calculate offset from frame center
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        offset_x = target_center_x - frame_center_x
        offset_y = target_center_y - frame_center_y
        
        # Convert pixel offset to angular offset (degrees)
        pan_offset = (offset_x / frame_width) * 60.0  # degrees
        tilt_offset = -(offset_y / frame_height) * 45.0  # degrees (negative for up)
        
        return (pan_offset, tilt_offset)