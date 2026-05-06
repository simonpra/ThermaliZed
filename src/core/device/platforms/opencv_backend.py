import os
import sys

# Suppress OpenCV warnings (must be set before cv2 import)
os.environ.setdefault('OPENCV_LOG_LEVEL', 'FATAL')

import cv2
import threading
import time
import numpy as np

from src.core.device.base import BaseDeviceBackend

class OpenCVDeviceBackend(BaseDeviceBackend):
    """
    Generic OpenCV-based basic capture backend.
    Used as a fallback for platforms without native implementations like Linux and Windows.
    """
    
    def __init__(self):
        self.frame_lock = threading.Lock()
        self.shared_frame_data = {
            'latest_frame': None,
            'width': 0,
            'height': 0,
            'stride': 0,
            'is_planar': False,
            'timestamp': 0.0
        }
        self.capture_thread = None
        self.session_active = False
        self.devices = []
        self.device_indices = []

    def get_device_names(self) -> list:
        """
        Request a list of available video devices using OpenCV.
        Note: OpenCV doesn't easily provide device names, so this might return indices or generic names.
        """
        self.devices = []
        self.device_indices = []
        
        backend = cv2.CAP_MSMF if sys.platform == 'win32' else cv2.CAP_ANY

        # Basic scanning up to 5 devices to check if they can be opened.
        # This is a stub/basic implementation.
        for i in range(5):
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                self.devices.append(f"OpenCV Camera {i}")
                self.device_indices.append(i)
                cap.release()
        return self.devices

    def start(self, device_index: int):
        if not self.session_active:
            self.session_active = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(device_index,),
                daemon=True
            )
            self.capture_thread.start()

    def stop(self):
        self.session_active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

    def _capture_loop(self, device_index: int):
        real_index = self.device_indices[device_index] if hasattr(self, 'device_indices') and device_index < len(self.device_indices) else device_index
        # Stub loop logic
        backend = cv2.CAP_MSMF if sys.platform == 'win32' else cv2.CAP_ANY
        cap = cv2.VideoCapture(real_index, backend)
        
        # Try to set resolution (TC001 is 256x384 standard format is NV12 or YUY2 but wrapped)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
        cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        
        try:
            while self.session_active and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # In real implementation we need to process this raw buffer correctly
                    # For now just update with raw shape bytes
                    with self.frame_lock:
                        # Dummy raw byte extraction logic that needs tweaking depending on backend
                        raw_bytes = frame.tobytes()
                        self.shared_frame_data['latest_frame'] = np.frombuffer(raw_bytes, dtype=np.uint8)
                        self.shared_frame_data['width'] = 256
                        self.shared_frame_data['height'] = 384
                        self.shared_frame_data['stride'] = 512 # Dummy
                        self.shared_frame_data['timestamp'] = time.time()
                time.sleep(1/30) # 30fps
        finally:
            cap.release()

    def get_latest_frame(self) -> dict | None:
        with self.frame_lock:
            if self.shared_frame_data['latest_frame'] is None:
                return None
            return {
                'frame': self.shared_frame_data['latest_frame'],
                'width': self.shared_frame_data['width'],
                'height': self.shared_frame_data['height'],
                'stride': self.shared_frame_data['stride'],
                'timestamp': self.shared_frame_data['timestamp']
            }
