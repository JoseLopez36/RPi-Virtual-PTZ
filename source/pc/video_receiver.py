import cv2
import threading

class VideoReceiver:
    def __init__(self, src=0):
        # Initialize capture with FFMPEG backend and request hardware acceleration
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        
        # Explicitly request NVIDIA CUDA hardware acceleration (NVDEC)
        # 7 = cv2.VIDEO_ACCELERATION_NVIDIA
        self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, 7)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        (self.grabbed, self.frame) = self.cap.read()
        self.stopped = False
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (grabbed, frame) = self.cap.read()
                with self.lock:
                    self.grabbed = grabbed
                    self.frame = frame

    def read(self):
        with self.lock:
            return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()
