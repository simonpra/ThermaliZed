import threading
import time
import struct
import zlib
import os
import numpy as np

class RecordingPlayer(threading.Thread):
    """
    Reads a .trv file and pushes frames to the application context state
    to simulate a live camera feed.
    """
    def __init__(self, filepath, context):
        super().__init__(daemon=True)
        self.filepath = filepath
        self.context = context
        self._stop_event = threading.Event()
        self.is_playing = False
        
        self.width = 0
        self.height = 0
        self.fps = 30.0
        self.total_frames = 0
        
        # Pre-scan the file to get metadata and frame offsets if needed
        # For a simple player, we just read sequentially.

    def stop_playback(self):
        self._stop_event.set()
        self.is_playing = False

    def run(self):
        self.is_playing = True
        
        try:
            with open(self.filepath, 'rb') as f:
                # Read Header
                header_data = f.read(16)
                if len(header_data) < 16:
                    self.context.event_bus.publish('LOG_MESSAGE', "Error: Invalid .trv file (too short).")
                    return
                    
                magic, self.width, self.height, self.fps = struct.unpack('<4sIIf', header_data)
                if magic != b'TRV1':
                    self.context.event_bus.publish('LOG_MESSAGE', "Error: Not a valid .trv file.")
                    return
                
                frame_delay = 1.0 / self.fps if self.fps > 0 else 1.0 / 30.0
                
                while not self._stop_event.is_set():
                    # Read Frame Block Header
                    block_header_data = f.read(16)
                    if len(block_header_data) < 16:
                        break # EOF
                        
                    marker, timestamp, payload_size = struct.unpack('<4sdI', block_header_data)
                    if marker != b'FRME':
                        self.context.event_bus.publish('LOG_MESSAGE', "Error: Corrupted .trv file (missing frame marker).")
                        break
                        
                    # Read Payload
                    compressed_payload = f.read(payload_size)
                    if len(compressed_payload) < payload_size:
                        break # Unexpected EOF
                        
                    try:
                        raw_buffer = zlib.decompress(compressed_payload)
                    except zlib.error as e:
                        self.context.event_bus.publish('LOG_MESSAGE', f"Error decompressing frame: {e}")
                        continue
                        
                    # Push to context state
                    # The raw buffer is a flat uint8 array
                    # We format it exactly as the camera backend does
                    frozen_data = {
                        'frame': np.frombuffer(raw_buffer, dtype=np.uint8),
                        'width': self.width,
                        'height': self.height,
                        'stride': self.width * 2, # Assuming 16-bit / 2 bytes per pixel
                        'timestamp': time.time() # Use current time to keep the renderer happy
                    }
                    
                    self.context.state['frozen_frame_data'] = frozen_data
                    
                    # Sleep to match FPS
                    time.sleep(frame_delay)
                    
            if not self._stop_event.is_set():
                 self.context.event_bus.publish('LOG_MESSAGE', "Recording playback finished.")
                 
        except Exception as e:
             self.context.event_bus.publish('LOG_MESSAGE', f"Error playing recording: {e}")
        finally:
             self.is_playing = False
             # We do NOT clear frozen_frame_data here so the last frame stays visible
