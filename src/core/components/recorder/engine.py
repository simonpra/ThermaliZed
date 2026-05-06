import threading
import queue
import time
import struct
import zlib
import os

class RecordingEngine(threading.Thread):
    """
    Background engine that compresses and writes thermal frames to a .trv file.
    Runs in its own thread to prevent UI blocking during compression/IO.
    """
    def __init__(self, filepath, width, height, fps=30.0):
        super().__init__(daemon=True)
        self.filepath = filepath
        self.width = width
        self.height = height
        self.fps = float(fps)
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self.is_recording = False
        
        self.frames_written = 0
        self.bytes_written = 0
        self.start_time = 0.0

    def start_recording(self):
        """Starts the background thread."""
        self.is_recording = True
        self.start_time = time.time()
        self.start()

    def stop_recording(self):
        """Signals the thread to stop and waits for it to finish."""
        self._stop_event.set()
        self.is_recording = False
        if self.is_alive():
            self.join(timeout=2.0)

    def enqueue_frame(self, frame_data_dict):
        """
        Adds a frame to the recording queue.
        frame_data_dict should contain 'frame' (the packed raw buffer) and 'timestamp'.
        """
        if self.is_recording:
            # We copy the buffer to avoid it being mutated by the main thread
            # before it gets compressed.
            payload = {
                'frame': frame_data_dict['frame'].copy(),
                'timestamp': frame_data_dict.get('timestamp', time.time())
            }
            self.queue.put(payload)

    def run(self):
        try:
            with open(self.filepath, 'wb') as f:
                # Write Header
                # Magic 'TRV1' (4 bytes), Width (uint32), Height (uint32), FPS (float32)
                header = struct.pack('<4sIIf', b'TRV1', self.width, self.height, self.fps)
                f.write(header)
                self.bytes_written += len(header)
                
                while not self._stop_event.is_set() or not self.queue.empty():
                    try:
                        # Timeout allows checking the stop_event regularly
                        item = self.queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                        
                    raw_buffer = item['frame']
                    timestamp = float(item['timestamp'])
                    
                    # Compress the raw buffer
                    compressed_payload = zlib.compress(raw_buffer, level=1) # Level 1 is fast, good enough for raw bytes
                    
                    # Write Frame Block
                    # Marker 'FRME' (4 bytes), Timestamp (float64), Payload Size (uint32)
                    payload_size = len(compressed_payload)
                    block_header = struct.pack('<4sdI', b'FRME', timestamp, payload_size)
                    
                    f.write(block_header)
                    f.write(compressed_payload)
                    
                    # Flush to make it readable externally in real-time
                    f.flush()
                    
                    self.bytes_written += len(block_header) + payload_size
                    self.frames_written += 1
                    self.queue.task_done()
                    
        except Exception as e:
            print(f"[RecordingEngine] Error writing to {self.filepath}: {e}")
        finally:
            self.is_recording = False
