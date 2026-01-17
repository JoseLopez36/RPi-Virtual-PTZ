class VirtualPTZ:
    def __init__(self, config):
        self.config = config
        self.resolution = config['video']['resolution']  # [W, H]
        self.current_zoom = 1.0
        self.target_id = None
        self.last_detections = []
        self.max_zoom = 4.0
        self.zoom_step = 0.2

    def update(self, detections):
        """Calculate PTZ based on detections and current target"""
        self.last_detections = detections
        W, H = self.resolution

        # Human-like aspect ratio (vertical)
        # target_ratio = width / height
        target_ratio = 9 / 16
        
        # Default: centered view based on current zoom
        target_center_x, target_center_y = W / 2, H / 2

        # If we have a target ID, try to find it in current detections
        if self.target_id is not None:
            target = next((d for d in detections if d.get('id') == self.target_id), None)
            if target:
                # Use target's bounding box center
                x1, y1, x2, y2 = target['box']
                target_center_x = (x1 + x2) / 2
                target_center_y = (y1 + y2) / 2

        # Calculate crop dimensions using the human-like aspect ratio
        # We base the size on the height and the current zoom
        crop_h = H / self.current_zoom
        crop_w = crop_h * target_ratio

        # Ensure crop width doesn't exceed frame width (unlikely for vertical on landscape)
        if crop_w > W:
            crop_w = W
            crop_h = crop_w / target_ratio

        # Calculate top-left corner
        crop_x = target_center_x - crop_w / 2
        crop_y = target_center_y - crop_h / 2

        # Clamp to frame boundaries
        crop_x = max(0, min(crop_x, W - crop_w))
        crop_y = max(0, min(crop_y, H - crop_h))

        return {
            "x": int(crop_x),
            "y": int(crop_y),
            "w": int(crop_w),
            "h": int(crop_h),
            "zoom": self.current_zoom,
            "target_id": self.target_id
        }

    def set_target(self, target_id):
        self.target_id = target_id

    def handle_input(self, event):
        """
        Handle joystick events from Sense HAT.
        """
        # event is expected to have 'direction' and 'action'
        if event.action in ['pressed', 'held']:
            if event.direction == 'up':
                self.current_zoom = min(self.max_zoom, self.current_zoom + self.zoom_step)
            elif event.direction == 'down':
                self.current_zoom = max(1.0, self.current_zoom - self.zoom_step)
            elif event.direction == 'middle':
                self.current_zoom = 1.0
                self.target_id = None
            elif event.direction == 'left':
                self._cycle_target(reverse=True)
            elif event.direction == 'right':
                self._cycle_target(reverse=False)

    def _cycle_target(self, reverse=False):
        """
        Cycle through available target IDs from last detections.
        """
        if not self.last_detections:
            self.target_id = None
            return

        # Get all unique IDs from detections
        ids = sorted(list(set(d['id'] for d in self.last_detections if 'id' in d)))
        
        if not ids:
            self.target_id = None
            return

        if self.target_id is None:
            self.target_id = ids[0]
        else:
            try:
                current_idx = ids.index(self.target_id)
                if reverse:
                    new_idx = (current_idx - 1) % len(ids)
                else:
                    new_idx = (current_idx + 1) % len(ids)
                self.target_id = ids[new_idx]
            except ValueError:
                # Current target_id not in latest detections
                self.target_id = ids[0]
