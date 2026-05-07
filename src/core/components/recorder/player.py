import threading
import time
import struct
import zlib
import os
import numpy as np

class RecordingPlayer(threading.Thread):
    """
    Reads a .trv file and pushes frames to the application context state
    to simulate a live camera feed. Supports pause and stepping.
    """
    def __init__(self, filepath, context):
        super().__init__(daemon=True)
        self.filepath = filepath
        self.context = context
        self._stop_event = threading.Event()
        
        self.is_playing = False
        self.is_paused = False
        self._step_request = 0  # 1 for forward, -1 for backward
        
        self.width = 0
        self.height = 0
        self.fps = 30.0
        
        self.frame_offsets = []
        self.current_frame_idx = 0
        
        self._scan_file()

    def _scan_file(self):
        """Pre-scan the file to build an index of frame offsets."""
        try:
            with open(self.filepath, 'rb') as f:
                header_data = f.read(16)
                if len(header_data) < 16:
                    return
                magic, self.width, self.height, self.fps = struct.unpack('<4sIIf', header_data)
                if magic != b'TRV1':
                    return
                
                while True:
                    offset = f.tell()
                    block_header_data = f.read(16)
                    if len(block_header_data) < 16:
                        break
                        
                    marker, timestamp, payload_size = struct.unpack('<4sdI', block_header_data)
                    if marker != b'FRME':
                        break
                        
                    self.frame_offsets.append(offset)
                    f.seek(payload_size, os.SEEK_CUR) # Skip payload
        except Exception as e:
            self.context.event_bus.publish('LOG_MESSAGE', f"Error indexing recording: {e}")

    def stop_playback(self):
        self._stop_event.set()
        self.is_playing = False

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def step_frame(self, direction):
        """Request a step by `direction` frames (e.g., 1 or -1)."""
        if self.is_paused:
            self._step_request = direction

    def seek_frame(self, frame_idx):
        """Seek to a specific frame index."""
        if 0 <= frame_idx < len(self.frame_offsets):
            self.current_frame_idx = frame_idx
            # If paused, we need to trigger a read of the new frame.
            if self.is_paused:
                self._step_request = 0 # reset any pending step
                self._force_read = True

    def run(self):
        self.is_playing = True
        
        if not self.frame_offsets:
            self.context.event_bus.publish('LOG_MESSAGE', "Error: No frames found in recording.")
            self.is_playing = False
            return
            
        frame_delay = 1.0 / self.fps if self.fps > 0 else 1.0 / 30.0
        
        try:
            with open(self.filepath, 'rb') as f:
                while not self._stop_event.is_set():
                    
                    if self.current_frame_idx >= len(self.frame_offsets):
                        self.is_paused = True # Auto-pause at end
                        self.current_frame_idx = len(self.frame_offsets) - 1
                        
                    if self.is_paused:
                        if self._step_request != 0:
                            self.current_frame_idx += self._step_request
                            # Clamp index
                            self.current_frame_idx = max(0, min(self.current_frame_idx, len(self.frame_offsets) - 1))
                            self._step_request = 0
                        elif getattr(self, '_force_read', False):
                            self._force_read = False
                        else:
                            time.sleep(0.05)
                            continue

                    # Read current frame
                    offset = self.frame_offsets[self.current_frame_idx]
                    f.seek(offset)
                    
                    block_header_data = f.read(16)
                    if len(block_header_data) < 16:
                         break
                         
                    marker, timestamp, payload_size = struct.unpack('<4sdI', block_header_data)
                    compressed_payload = f.read(payload_size)
                    
                    try:
                        raw_buffer = zlib.decompress(compressed_payload)
                        frozen_data = {
                            'frame': np.frombuffer(raw_buffer, dtype=np.uint8),
                            'width': self.width,
                            'height': self.height,
                            'stride': self.width * 2,
                            'timestamp': time.time()
                        }
                        self.context.state['frozen_frame_data'] = frozen_data
                    except zlib.error as e:
                        self.context.event_bus.publish('LOG_MESSAGE', f"Error decompressing frame: {e}")
                    
                    if not self.is_paused:
                        self.current_frame_idx += 1
                        time.sleep(frame_delay)
                    
            if not self._stop_event.is_set():
                 self.context.event_bus.publish('LOG_MESSAGE', "Recording playback finished.")
                 
        except Exception as e:
             self.context.event_bus.publish('LOG_MESSAGE', f"Error playing recording: {e}")
        finally:
             self.is_playing = False
