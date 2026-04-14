import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

import time

from src.core.plugin_base import SystemComponent
from src.core.processor import process_thermal_frame
from src.utils.constants import COLORMAPS

class ThermalViewFrame(ttk.Frame):
    """
    Main renderer component. Responsible for displaying the processed thermal image
    onto a scalable Tkinter Canvas. Maintains aspect ratio and coordinates overlay mounts.
    """
    def __init__(self, parent, context, **kwargs):
        super().__init__(parent, **kwargs)
        self.context = context
        
        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.context.register_service('renderer_canvas', self.canvas)
        self.canvas.bind("<Configure>", self.on_resize)
        
        self._image_id = None
        self._photo_image = None
        
        self.current_width = 1
        self.current_height = 1
        self.last_timestamp = 0.0
        
        self._fps_last_time = time.time()
        self._fps_frames = 0
        self._fps_current = 0.0

    def on_resize(self, event):
        self.current_width = max(event.width, 1)
        self.current_height = max(event.height, 1)

    def on_frame_ready(self, frame_data):
        if not frame_data:
            return
            
        timestamp = frame_data['timestamp']
        params = self.context.state.get('params', {})
        
        # Prepare parameters for processor
        params_processor = params.copy()
        idx = params.get('colormap_index', 0)
        params_processor['colormap_code'] = COLORMAPS[idx][0]
        
        # Avoid redundant redraws if nothing has changed
        current_state = (timestamp, str(params_processor), self.current_width, self.current_height)
        if getattr(self, '_last_render_state', None) == current_state:
            return
            
        self._last_render_state = current_state
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp

        heatmap, thermal_info, debug_info = process_thermal_frame(
            frame_data['frame'],
            frame_data['width'],
            frame_data['height'],
            frame_data['stride'],
            params_processor,
            event_bus=self.context.event_bus,
        )
        
        if heatmap is None:
            return
            
        # --- FPS Calculation ---
        current_time = time.time()
        self._fps_frames += 1
        elapsed = current_time - self._fps_last_time
        if elapsed >= 1.0:
            self._fps_current = self._fps_frames / elapsed
            self._fps_last_time = current_time
            self._fps_frames = 0

        # --- Consolidate all metadata into a single dict ---
        # This becomes the single source of truth for all UI consumers.
        infos = {
            # Thermal data from processor
            **thermal_info,
            # Processing diagnostics from processor
            **debug_info,
            # Renderer diagnostics
            'fps': self._fps_current,
            # Current display parameters
            'colormap_name':  COLORMAPS[idx][1],
            'colormap_code':  params_processor.get('colormap_code'),
            'scale':          params_processor.get('scale', 1),
            'blur':           params_processor.get('blur', 0),
            'alpha':          params_processor.get('alpha', 1.0),
            'manual_leveling': params_processor.get('manual_leveling', False),
            'gradient_step':  params.get('gradient_step', 0.0),
        }

        # Persist in global state so any module can read the latest snapshot
        self.context.state['infos'] = infos
        # Broadcast to all subscribers (HUD, gradient overlay, future plugins…)
        self.context.event_bus.publish('METADATA_READY', infos)
            
        if params.get('edge_detection', False):
            edge_threshold = params.get('edge_threshold', 100)
            gray = cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, edge_threshold, edge_threshold * 2)
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            edges_colored[:, :, 1] = edges
            heatmap = cv2.addWeighted(heatmap, 0.7, edges_colored, 0.3, 0)
            
        rgb_image = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        if self.current_width > 10 and self.current_height > 10:
            h, w = rgb_image.shape[:2]
            aspect = w / h
            new_w = self.current_width
            new_h = int(new_w / aspect)
            if new_h > self.current_height:
                new_h = self.current_height
                new_w = int(new_h * aspect)
            new_w = max(new_w, 1)
            new_h = max(new_h, 1)
            rgb_image = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            
        pil_img = Image.fromarray(rgb_image)
        self._photo_image = ImageTk.PhotoImage(image=pil_img)
        
        if self._image_id is None:
            self._image_id = self.canvas.create_image(
                self.current_width//2, self.current_height//2, 
                image=self._photo_image, 
                anchor=tk.CENTER
            )
        else:
            self.canvas.coords(self._image_id, self.current_width//2, self.current_height//2)
            self.canvas.itemconfig(self._image_id, image=self._photo_image)


class PluginClass(SystemComponent):
    """Core plugin for rendering the thermal feed."""
    
    def on_load(self, context):
        self.context = context
        self.view = None
        self.context.event_bus.subscribe('FRAME_READY', self._handle_frame)
        
    def _handle_frame(self, frame_data):
        if self.view:
            self.view.on_frame_ready(frame_data)
            
    def get_ui(self, parent_widget, zone):
        if zone == 'main_content':
            self.view = ThermalViewFrame(parent_widget, self.context)
            return self.view
        return None
