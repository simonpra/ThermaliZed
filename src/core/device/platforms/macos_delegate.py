import objc
from Foundation import NSObject
import CoreMedia as CM
from Quartz import CoreVideo as CV # Import via Quartz
import numpy as np
import ctypes
import traceback
import time

# Utility function to decode FourCC codes
def decode_fourcc(cc):
    """
    Decodes an integer FourCC pixel format code into its 4-character string representation.
    """
    try:
        int_cc = int(cc)
        return "".join([chr((int_cc >> 8 * i) & 0xFF) for i in range(4)])
    except Exception:
        return str(cc)

class FrameDelegate(NSObject):
    """
    AVFoundation delegate that receives raw video buffers on a separate thread.
    
    It copies the raw buffer and its metadata (dimensions, stride) into a
    shared dictionary protected by a lock for synchronization with the main thread.
    """
    # Custom initializer to inject the lock and shared data reference
    @objc.signature(b'@@:@@')
    def initWithLock_Data_(self, lock, shared_data):
        self = objc.super(FrameDelegate, self).init()
        if self is None: return None
        self.lock = lock
        self.shared_data = shared_data
        self.frame_count_delegate = 0
        print("[Delegate] FrameDelegate initialized.")
        return self

    # Method called automatically by AVFoundation for each frame received
    @objc.signature(b'v@:@@@')
    def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, sampleBuffer, connection):
        self.frame_count_delegate += 1
        pixelBuffer = None
        flags = 0 # Read-only lock

        try:
            # Get the CVPixelBuffer (contains the image data)
            pixelBuffer = CM.CMSampleBufferGetImageBuffer(sampleBuffer)
            if pixelBuffer is None: return

            # Lock the buffer memory to access it safely
            err = CV.CVPixelBufferLockBaseAddress(pixelBuffer, flags)
            if err != 0:
                # kCVReturnSuccess = 0
                print(f"[Delegate] Error: LockBaseAddress failed (code {err})")
                # Try to unlock even if the lock failed (safeguard)
                CV.CVPixelBufferUnlockBaseAddress(pixelBuffer, flags)
                return

            try:
                # Get essential buffer properties
                width = CV.CVPixelBufferGetWidth(pixelBuffer)       # Logical width (e.g., 256)
                height = CV.CVPixelBufferGetHeight(pixelBuffer)      # Logical height (e.g., 384)
                bytesPerRow = CV.CVPixelBufferGetBytesPerRow(pixelBuffer) # Actual width in bytes (stride, e.g., 512)
                is_planar = CV.CVPixelBufferIsPlanar(pixelBuffer)     # Check if planar (usually False here)
                pixelFormatCode = CV.CVPixelBufferGetPixelFormatType(pixelBuffer) # Actual format code

                # Display debug information for the first frame only
                if self.frame_count_delegate == 1:
                    print("-" * 30)
                    print(f"[Delegate] Info Frame 1:")
                    print(f"  Is Planar: {is_planar}")
                    print(f"  Dimensions (WxH): {width}x{height}")
                    print(f"  Pixel Format (Code): {pixelFormatCode}")
                    print(f"  Pixel Format (FourCC): '{decode_fourcc(pixelFormatCode)}'")
                    print(f"  Bytes Per Row (Stride): {bytesPerRow}")
                    print("-" * 30)

                # If planar, this logic is currently not meant to fully copy it
                if is_planar:
                     if self.frame_count_delegate % 100 == 1: # Log less frequently
                          print("[Delegate] WARNING: Planar format detected but not supported for complete copy.")
                     # Could copy the Y plane but defaulting to None for now
                     frame_to_pass = None
                # If packed (expected behavior)
                else:
                    # Access the memory buffer directly using the discovered .as_buffer() method
                    baseAddress_varlist = CV.CVPixelBufferGetBaseAddress(pixelBuffer)
                    if not baseAddress_varlist:
                        print("[Delegate] Error: GetBaseAddress returned None/empty.")
                        return # Unlocks in finally block

                    buffer_size = bytesPerRow * height # Total byte size
                    try:
                        # Extract content directly into Python bytes
                        buffer_bytes = baseAddress_varlist.as_buffer(buffer_size)
                        # Create a NumPy array from bytes (creates a hard copy)
                        frame_to_pass = np.frombuffer(buffer_bytes, dtype=np.uint8).copy()
                    except Exception as buffer_access_error:
                        print(f"[Delegate] Error: Access/Conversion via as_buffer failed: {buffer_access_error}")
                        frame_to_pass = None


                # Update shared data if the copy was successful
                if frame_to_pass is not None and frame_to_pass.size == buffer_size:
                    with self.lock:
                        self.shared_data['latest_frame'] = frame_to_pass # Provide the flat uint8 numpy copy
                        self.shared_data['width'] = width       # e.g.: 256
                        self.shared_data['height'] = height     # e.g.: 384
                        self.shared_data['stride'] = bytesPerRow # e.g.: 512
                        self.shared_data['is_planar'] = is_planar # e.g.: False
                        self.shared_data['timestamp'] = time.time() # Add a timestamp
                elif frame_to_pass is not None:
                    print(f"[Delegate] WARNING: Copied buffer size ({frame_to_pass.size}) != expected size ({buffer_size})")

            finally:
                # Always unlock the buffer!
                CV.CVPixelBufferUnlockBaseAddress(pixelBuffer, flags)

        except Exception as outer_err:
            print(f"[Delegate] Outer Error: {outer_err}")
            traceback.print_exc()