import numpy as np
import cv2
import traceback
import time
from src.utils.functions import to_degrees_c


def process_thermal_frame(raw_flat_buffer, width, height, stride, params, event_bus=None):
    """
    Processes the raw buffer to extract, normalize, and visualize thermal data.

    Args:
        raw_flat_buffer (np.ndarray): Flat uint8 NumPy array containing the raw byte data from the camera.
        width (int): Logical width of the image (e.g., 256 pixels).
        height (int): Total height of the raw buffer (e.g., 384 pixels).
        stride (int): Number of bytes per row in the buffer (e.g., 512 bytes).
        params (dict): Dictionary with processing parameters:
            'colormap_code' (int): OpenCV colormap code to apply to the thermal image.
            'manual_leveling' (bool): True to use manual min/max levels instead of auto-scaling.
            'manual_min_raw' (int): Manual minimum raw thermal value (0-65535).
            'manual_max_raw' (int): Manual maximum raw thermal value (0-65535).
            'scale' (int): Scaling factor for the final display.
            (blur and alpha are now applied upstream by the image_enhancement plugin via RAW_FRAME_PIPELINE)
        event_bus (EventBus | None): Optional event bus. When provided, two pipeline events
            are fired:

            1. 'RAW_FRAME_PIPELINE'  — fired immediately after the 16-bit array is assembled,
               before normalisation or colormap.  Subscribers receive:
                 data : np.ndarray[uint16] — current (possibly modified) 16-bit array
                 raw  : np.ndarray[uint16] — original unmodified 16-bit array
               A non-None return replaces `data` for downstream steps.

            2. 'IMAGE_PIPELINE' — fired after the final 8-bit BGR heatmap is scaled.
               Subscribers receive:
                 data : np.ndarray[uint8, BGR] — current mutable 8-bit frame
                 raw  : dict with keys:
                          '8bit'         → np.ndarray[uint8, BGR] reference copy (unmodified)
                          '16bit'        → np.ndarray[uint16] original sensor data for math
                          'thermal_info' → dict of extracted thermal metadata
               A non-None ndarray return replaces `data` for downstream steps.

    Returns:
        tuple: (heatmap_scaled, thermal_info, debug_info)
            heatmap_scaled (np.ndarray): Final BGR image (resized and color-mapped) ready for display.
                                         Returns None if a processing error occurs.
            thermal_info (dict): Extracted thermal metadata (min/max raw values, normalization bounds, Celsius range).
                                 Empty dictionary if an error occurs.
            debug_info (dict): Processing diagnostics, e.g. {'proc_time_ms': float}.
                               Empty dictionary if an error occurs.
    """
    thermal_info = {} # Stores extracted thermal metadata
    debug_info   = {} # Stores processing diagnostics
    heatmap_scaled = None # Final processed image

    _t_start = time.perf_counter()

    try:
        # --- Validation and Pre-processing ---
        expected_size = height * stride
        if raw_flat_buffer is None or raw_flat_buffer.size != expected_size:
            size_found = raw_flat_buffer.size if raw_flat_buffer is not None else 'None'
            print(f"Processor Error: Buffer size ({size_found}) != expected ({expected_size})")
            return None, {}, {}

        bytes_per_pixel = 2 # Assuming YUYV format or 16-bit thermal data
        if stride < width * bytes_per_pixel:
             print(f"Processor Error: Stride ({stride}) < Width*BPP ({width*bytes_per_pixel})")
             return None, {}, {}

        # The thermal frame is usually packed with regular image data.
        # The fisrt half is the visual feed. It contains a standard 8-bit/pixel (or YUYV mapped)
        # auto-scaled grayscale image. The camera generates this top half so it can function
        # as a plug-and-play webcam recognized as a USB Video Class (UVC) device by the OS.
        # The bottom half contains the raw 16-bit per pixel data from the sensor.
        thermal_h = height // 2 # e.g., 192 for the TC001
        thermal_w = width       # e.g., 256 for the TC001

        # --- Reshaping and Splitting ---
        # Reshape the 1D buffer into a 2D array of bytes using the exact memory stride
        frame_raw_rows = raw_flat_buffer.reshape((height, stride))
        
        # Extract only the useful bytes per row, ignoring padding bytes at the end of each stride
        useful_width_bytes = width * bytes_per_pixel
        frame_raw_useful = frame_raw_rows[:, :useful_width_bytes]
        
        # Reshape into a 3D array: (Height, Width, BytesPerPixel)
        frame_packed_reshaped = frame_raw_useful.reshape((height, width, bytes_per_pixel))

        # Extract thermal data (the bottom half of the image)
        # Note: We ignore the visual data ('imdata' in the top half) for thermal processing
        thdata = frame_packed_reshaped[thermal_h:, :, :] # Shape: (192, 256, 2)

        # --- Interpretation as 16-bit Little Endian ---
        if not thdata.flags['C_CONTIGUOUS']:
            thdata = thdata.copy() # Ensure contiguous memory layout for .view() operation
        
        # Interpret the two 8-bit bytes as one 16-bit unsigned integer (little-endian)
        raw_thermal_16bit = thdata.view('<u2').reshape(thermal_h, thermal_w)

        # TC001/TS001 cameras emit an all-0x8000 placeholder while the sensor
        # performs its initial calibration. Rendering that value would show a
        # convincing but false 238.9 °C reading for the first few seconds.
        if np.all(raw_thermal_16bit == 0x8000):
            return None, {}, {'frame_status': 'calibrating'}

        original_raw_16bit = raw_thermal_16bit.copy()

        # --- Plugin Pipeline: RAW_FRAME_PIPELINE ---
        # Fired immediately after the 16-bit thermal array is assembled, before any
        # normalization or colormap is applied.  Subscribers receive:
        #   data : np.ndarray  – current 16-bit array (shape: thermal_h × thermal_w, dtype uint16)
        #   raw  : np.ndarray  – the original 16-bit array (never mutated)
        # A subscriber that returns a non-None ndarray replaces `raw_thermal_16bit` for every
        # subsequent visual step (colormap, scaling ...).
        if event_bus is not None:
            raw_thermal_16bit = event_bus.pipeline(
                'RAW_FRAME_PIPELINE',
                raw_thermal_16bit,
                raw=original_raw_16bit,
            )

        # Compute raw minimum and maximum thermal values using the UNMODIFIED data
        min_raw = int(np.min(original_raw_16bit)) # Cast to Python int to avoid numpy serialization errors
        max_raw = int(np.max(original_raw_16bit))
        thermal_info['min_raw'] = min_raw
        thermal_info['max_raw'] = max_raw

        # --- 16-bit to 8-bit Normalization ---
        norm_min, norm_max = 0, 0
        if params.get('manual_leveling', False): 
            # Use fixed normalization bounds based on user input
            norm_min = params.get('manual_min_raw', 0)
            norm_max = params.get('manual_max_raw', 65535)
        else:
            # Automatic normalization: calculate dynamic range discarding extreme 1% outliers (e.g. dead pixels)
            # CAUTION: Calculated on unmodified raw data to not be influenced by contrast plugins.
            p_low = np.percentile(original_raw_16bit, 1)
            p_high = np.percentile(original_raw_16bit, 99)
            if p_high <= p_low: 
                p_low, p_high = min_raw, max_raw
            norm_min = p_low
            norm_max = p_high

        # Store the actual normalization range applied
        thermal_info['norm_min'] = int(norm_min)
        thermal_info['norm_max'] = int(norm_max)

        # Map the 16-bit values into an 8-bit visual range (0-255)
        if norm_max > norm_min:
            scaled_data = (raw_thermal_16bit.astype(np.float32) - norm_min) / (norm_max - norm_min)
            scaled_data = np.clip(scaled_data, 0.0, 1.0)
            norm_image_8bit = (scaled_data * 255).astype(np.uint8)
        else:
            # Fallback to grey if min == max to prevent ZeroDivisionError
            norm_image_8bit = np.full(raw_thermal_16bit.shape, 128, dtype=np.uint8)

        # --- Apply Colormap ---
        cmap_code = params.get('colormap_code', cv2.COLORMAP_INFERNO)
        heatmap_8bit = cv2.applyColorMap(norm_image_8bit, cmap_code)

        # --- Resizing for Visual Output ---
        scale = params.get('scale', 1)
        if scale > 1:
            final_w = thermal_w * scale
            final_h = thermal_h * scale
            # Using INTER_NEAREST to preserve the sharp 'pixelated' thermography look instead of muddy blurring
            heatmap_scaled = cv2.resize(heatmap_8bit, (final_w, final_h), interpolation=cv2.INTER_NEAREST)
        else:
            heatmap_scaled = heatmap_8bit

        # --- Celsius Temperature Calculation ---
        # CAUTION: Calculated on unmodified raw data to not corrupt real thermal metrics.
        try:
             temps_celsius = to_degrees_c(original_raw_16bit)
             thermal_info['min_c'] = np.nanmin(temps_celsius)
             thermal_info['max_c'] = np.nanmax(temps_celsius)
        except Exception:
             thermal_info['min_c'] = float('nan')
             thermal_info['max_c'] = float('nan')

        # --- Plugin Pipeline: IMAGE_PIPELINE ---
        # Fired after the final 8-bit BGR heatmap is ready, giving plugins a chance to
        # draw or manipulate the rendered output before it reaches the display.
        # Subscribers receive:
        #   data : np.ndarray[uint8, BGR]  – current (mutable) 8-bit heatmap
        #   raw  : dict {
        #            '8bit'         : reference copy of the original 8-bit heatmap
        #            '16bit'        : original_raw_16bit for temperature math
        #            'thermal_info' : metadata like min/max temps
        #          }
        if event_bus is not None:
            raw_payload = {
                '8bit':  heatmap_scaled.copy(),
                '16bit': original_raw_16bit,
                'thermal_info': thermal_info.copy(),
            }
            # IMAGE_PIPELINE - Plugins can modify the final output image.
            heatmap_scaled = event_bus.pipeline(
                'IMAGE_PIPELINE',
                heatmap_scaled,
                raw=raw_payload,
            )

        debug_info['proc_time_ms'] = (time.perf_counter() - _t_start) * 1000.0
        return heatmap_scaled, thermal_info, debug_info

    except Exception as e:
        print(f"Error in process_thermal_frame: {e}")
        traceback.print_exc()
        return None, {}, {}
